import logging
from pathlib import Path
from ingestion.raw import to_rows
from processing.extract_transforme import extract

"""
    in: list of events (from extract_transforme.extract)
    out: the three dashboard tables, dicts sorted from biggest to smallest
         - failed attempts per country
         - successful attempts per user
         - failed attempts with invalid user 
"""

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger_format = logging.Formatter(
    fmt='%(asctime)s|%(levelname)s|%(name)s|%(message)s',
    datefmt='%d-%b-%Y %H:%M:%S %p'
)
console = logging.StreamHandler()
console.setFormatter(logger_format)
logger.addHandler(console)
file = logging.FileHandler(Path(__file__).parent / 'aggregate.log')
file.setFormatter(logger_format)
logger.addHandler(file)


def sort_desc(table):
    """by value, biggest first"""
    return dict(sorted(table.items(), key=lambda item: item[1], reverse=True))


def failed_by_ip(events):
    per_ip = {}
    for event in events:
        try:
            if event['failed']:
                per_ip[event['ip']] = per_ip.get(event['ip'], 0) + event['count']
        except KeyError as e:
            logger.error('Event without key %s: %r', e, event)
    return per_ip


def failed_by_country(events, get_country):
    """
    geo_location.get_country, passed as a parameter.
    Count per IP first, then ask the country once per IP 
    """
    table = {}
    for ip, total in failed_by_ip(events).items():
        try:
            country = get_country(ip)
        except Exception as e:
            logger.error('Country lookup failed for %s: %s', ip, e)
            country = 'Unknown'
        table[country] = table.get(country,0)+total
    return sort_desc(table)


def success_by_user(events):
    table = {}
    for event in events:
        try:
            if event['success']:
                table[event['user']] = table.get(event['user'],0) + event['count']
        except KeyError as e:
            logger.error('Event without key %s: %r', e, event)
    return sort_desc(table)


def failed_invalid_user(events):
    table = {}
    for event in events:
        try:
            if event['failed'] and event['invalid_user']:
                table[event['user']] = table.get(event['user'], 0) + event['count']
        except KeyError as e:
            logger.error('Event without key %s: %r', e, event)
    return sort_desc(table)


if __name__ == '__main__':

    events = extract(to_rows('./data'))
    def fake_country(ip):
        return 'Private' if ip.startswith('10.') else 'FR' if int(ip.split('.')[0]) < 100 else 'US'

    by_country = failed_by_country(events, fake_country)
    print('failed by country:', by_country, '| total', sum(by_country.values()))
    print('countries        :', len(by_country), '| distinct failing IPs:', len(failed_by_ip(events)))
    print('success by user  :', success_by_user(events))
    invalid = failed_invalid_user(events)
    print('invalid user     : total', sum(invalid.values()), '| distinct usernames', len(invalid),
          '| top 5', dict(list(invalid.items())[:5]))