import os
import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger_format = logging.Formatter(
    fmt='%(asctime)s|%(levelname)s|%(name)s|%(message)s',
    datefmt='%d-%b-%Y %H:%M:%S %p'
)
console = logging.StreamHandler()
console.setFormatter(logger_format)
logger.addHandler(console)
file = logging.FileHandler(Path(__file__).parent / 'geo_location.log')
file.setFormatter(logger_format)
logger.addHandler(file)

URL_IPINFO = 'https://ipinfo.io'

def get_location(ip):
    try:
        response=requests.get(URL_IPINFO+'/'+ip+'/json', params={'token': os.environ.get('IPINFO_TOKEN')})
    except Exception as e:
        logger.error('Request failed for %s: %s', ip, e)
        return None  
    if response.status_code==200:
        return response.json()
    logger.error('Error for %s: status %s', ip, response.status_code)
    return None

cache = {}

def get_country(ip):
    if ip not in cache:
        info=get_location(ip)
        cache[ip]=info.get('country', 'Unknown') if info else 'Unknown'
    return cache[ip]

if __name__=='__main__':
    print(get_location('138.199.39.186'))
    print(get_country('138.199.39.186'))
    print(get_country('138.199.39.186'))