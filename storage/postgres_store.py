import os
import logging
from pathlib import Path
import psycopg2

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger_format = logging.Formatter(
    fmt='%(asctime)s|%(levelname)s|%(name)s|%(message)s',
    datefmt='%d-%b-%Y %H:%M:%S %p'
)
console = logging.StreamHandler()
console.setFormatter(logger_format)
logger.addHandler(console)
file = logging.FileHandler(Path(__file__).parent / 'postgres_store.log')
file.setFormatter(logger_format)
logger.addHandler(file)

CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        datetime TIMESTAMP,
        ip TEXT,
        username TEXT,
        success BOOLEAN,
        failed BOOLEAN,
        invalid_user BOOLEAN,
        count INTEGER
    )
"""

INSERT = """
    INSERT INTO events (datetime, ip, username, success, failed, invalid_user, count)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


def get_connection():
    try:
        return psycopg2.connect(
            host=os.environ.get('PGHOST', 'localhost'),
            port=os.environ.get('PGPORT', '5432'),
            dbname=os.environ.get('PGDATABASE', 'logs'),
            user=os.environ.get('PGUSER', 'postgres'),
            password=os.environ.get('PGPASSWORD'),
            connect_timeout=5,
        )
    except psycopg2.Error as e:
        logger.error('Cannot connect to PostgreSQL: %s', e)
        return None


def save_events(events, conn):
    rows = [(e['datetime'], e['ip'], e['user'], e['success'], e['failed'],
             e['invalid_user'], e['count']) for e in events]
    try:
        with conn:                          # commit at the end, rollback if there is an error
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE)
                cur.execute('TRUNCATE events RESTART IDENTITY')
                cur.executemany(INSERT, rows)
        return True
    except psycopg2.Error as e:
        logger.error('Cannot save events: %s', e)
        return False


def query_table(conn, sql):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return {name: int(total) for name, total in cur.fetchall()}
    except psycopg2.Error as e:
        conn.rollback()
        logger.error('Query failed: %s', e)
        return {}


def success_by_user_sql(conn):
    return query_table(conn, """
        SELECT username, SUM(count) FROM events
        WHERE success GROUP BY username ORDER BY 2 DESC, 1""")


def failed_invalid_user_sql(conn):
    return query_table(conn, """
        SELECT username, SUM(count) FROM events
        WHERE failed AND invalid_user GROUP BY username ORDER BY 2 DESC, 1""")


def failed_by_ip_sql(conn):
    return query_table(conn, """
        SELECT ip, SUM(count) FROM events
        WHERE failed GROUP BY ip ORDER BY 2 DESC, 1""")


if __name__ == '__main__':
    from ingestion.raw import to_rows
    from processing.extract_transforme import extract

    events = extract(to_rows('./data'))
    conn = get_connection()
    if not conn:
        print('No connection to PostgreSQL, see storage/postgres_store.log')
    elif not save_events(events, conn):
        print('Events not saved, see storage/postgres_store.log')
    else:
        print('saved: True')
        print('success by user :', success_by_user_sql(conn))
        invalid = failed_invalid_user_sql(conn)
        print('invalid user    : total', sum(invalid.values()), '| top 3', dict(list(invalid.items())[:3]))
        print('failed IPs      :', len(failed_by_ip_sql(conn)))
    if conn:
        conn.close()