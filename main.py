from pathlib import Path
from ingestion.raw import to_rows
from processing.extract_transforme import extract
from processing.geo_location import get_country
from serving.aggregate import failed_by_country, success_by_user, failed_invalid_user
from serving.dashboard import build_dashboard
from storage.country_cache import load_cache, save_cache, cached_country

if __name__ == '__main__':
    events = extract(to_rows('./data'))
    cache = load_cache()
    try:
        by_country = failed_by_country(events, lambda ip: cached_country(ip, cache, get_country))
    finally:
        save_cache(cache)
    build_dashboard(by_country, success_by_user(events), failed_invalid_user(events),
                    save_path=Path('serving') / 'dashboard.png')