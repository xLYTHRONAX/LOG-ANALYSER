from pathlib import Path
from ingestion.raw import to_rows
from processing.extract_transforme import extract
from processing.geo_location import get_country
from serving.aggregate import failed_by_country, success_by_user, failed_invalid_user
from serving.dashboard import build_dashboard
from storage.country_cache import load_cache, save_cache, cached_country
from storage.postgres_store import get_connection, save_events, success_by_user_sql, failed_invalid_user_sql

if __name__ == '__main__':
    events = extract(to_rows('./data'))

    cache = load_cache()
    try:
        by_country = failed_by_country(events, lambda ip: cached_country(ip, cache, get_country))
    finally:
        save_cache(cache)

    by_user = success_by_user(events)
    invalid_user = failed_invalid_user(events)

    conn = get_connection()             
    if conn and save_events(events, conn):
        print('PostgreSQL: events saved, tables read with SQL')
        by_user = success_by_user_sql(conn) or by_user
        invalid_user = failed_invalid_user_sql(conn) or invalid_user
    else:
        print('PostgreSQL not available, using the Python tables (see storage/postgres_store.log)')
    if conn:
        conn.close()

    build_dashboard(by_country, by_user, invalid_user, save_path=Path('serving') / 'dashboard.png')