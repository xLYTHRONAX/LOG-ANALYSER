import json
import logging
from pathlib import Path

"""
    Save IP country lookups in a json file, so the ipinfo API
    is only called once per IP 
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
file = logging.FileHandler(Path(__file__).parent / 'country_cache.log')
file.setFormatter(logger_format)
logger.addHandler(file)

CACHE_FILE = Path(__file__).parent / 'countries.json'


def load_cache(path=CACHE_FILE):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.error('Cannot read cache %s: %s', path, e)
        return {}


def save_cache(cache, path=CACHE_FILE):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=1)
    except Exception as e:
        logger.error('Cannot save cache %s: %s', path, e)


def cached_country(ip, cache, get_country):
    if ip not in cache:
        country = get_country(ip)
        if country == 'Unknown':
            return country      # lookup failed (network, limit...): do not remember it, retry next run
        cache[ip] = country
        if len(cache) % 100 == 0:
            print(len(cache), 'IPs located')
    return cache[ip]


if __name__ == '__main__':
    test_path = Path(__file__).parent / 'test_countries.json'
    cache = load_cache(test_path)
    print('loaded:', cache)
    fake = lambda ip: 'Unknown' if ip == '9.9.9.9' else 'FR'
    print(cached_country('1.2.3.4', cache, fake), cached_country('9.9.9.9', cache, fake))
    save_cache(cache, test_path)
    print('saved:', load_cache(test_path))
    test_path.unlink()