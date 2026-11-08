import re
import logging
from pathlib import Path
from datetime import datetime
"""
    in: list of rows
    out:dateTime, ip, success, failed, invalid user
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
file = logging.FileHandler(Path(__file__).parent / 'extract_transforme.log')
file.setFormatter(logger_format)
logger.addHandler(file)

YEAR = 2026

pattern=re.compile(r'(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<server>\S+)\s+(?P<service>[\w-]+)(?:\[\d+\])?:\s+(?P<message>.+)')
pattern_success = re.compile(r'Accepted (?P<method>\w+) for (?P<user>\S+) from (?P<ip>\S+) port \d+')
pattern_failed = re.compile(r'Failed password for (?P<invalid>invalid user )?(?P<user>\S+) from (?P<ip>\S+) port \d+')
pattern_repeated = re.compile(r'message repeated (?P<n>\d+) times: \[ (?P<inner>.+)\]')

def make_event(date_time, ip, user, success, failed, invalid_user, count):
    return {
        'datetime': date_time,
        'ip': ip,
        'user': user,
        'success': success,
        'failed': failed,
        'invalid_user': invalid_user,
        'count': count,
    }

def extract_from_row(row):
    match=re.search(pattern,row)
    if not match:
        logger.warning('Row not recognized: %s', row.strip())
        return None
    
    data=match.groupdict()
    if data['service'] != 'sshd':
            return None
    try:
            date_time=datetime.strptime(
                f"{YEAR} {data['month']} {data['day']} {data['time']}",
                '%Y %b %d %H:%M:%S'
            )
    except ValueError as e:
            logger.error('Invalid date in row %s: %s', row.strip(), e)
            return None
    
    message=data['message']
    count=1
    repeated=re.search(pattern_repeated, message)
    if repeated:
        rep=repeated.groupdict()
        count=int(rep['n'])
        message=rep['inner']

    ok=re.search(pattern_success, message)
    if ok:
        d=ok.groupdict()
        return make_event(date_time, d['ip'], d['user'], True, False, False, count)
    
    ko = re.search(pattern_failed, message)
    if ko:
        d=ko.groupdict()
        return make_event(date_time, d['ip'], d['user'], False, True, d['invalid'] is not None, count)
    return None

def extract(rows):
        #keep only the login attempts.
        events = []
        for row in rows:
            try:
                event = extract_from_row(row)
            except Exception as e:
                logger.error('Unexpected error on row %r: %s', row, e)
                continue
            if event:
                events.append(event)
        return events

def test_errors():
    bad_rows = [
        'this is not a log line',               # row not recognized
        '',                                     #empty row
        'Foo 12 10:00:00 ns sshd[1]: ...',      #invalid month
        'Feb 30 10:00:00 ns sshd[1]: ...',      #invalid day
        None,                                   #unexpected (not a string)
    ]
    events = extract(bad_rows)
    print('bad rows -> events:', len(events), '(expected 0)')

if __name__ == '__main__':
    from ingestion.raw import to_rows
    path = './data'
    print('looking in:', Path(path).resolve())
    rows = to_rows(path)
    print('rows read:', len(rows))
    events = extract(rows)
    print('events:', len(events))
    print('failed (weighted):', sum(e['count'] for e in events if e['failed']))
    print('invalid user:', sum(e['count'] for e in events if e['invalid_user']))
    print('success:', sum(e['count'] for e in events if e['success']))
    test_errors()