import psycopg2
import psycopg2.extras
from datetime import datetime
import datetime as dt
from operator import itemgetter
import logging
import os
CLIENT_ID = os.environ['CLIENT_ID']
SECRET_TOKEN = os.environ["SECRET_TOKEN"]
db_password = os.environ["db_password"]


class DB:
    def __init__(self):
        pass

    def create_con(self):
        conn = psycopg2.connect(
            user="sean",
            password=db_password,
            host="localhost",
            port="5432",
            database="sean",
        )
        return conn

    def create_dict(self, conn, item_type):
        # This function creates a dictionary based on the returned results.
        # This is much easier to parse in table.html than the tuples
        # that it was originally returning.
        now = datetime.now()
        num_days = 7
        if num_days > 30:
            num_days = 7
        week_ago = now - dt.timedelta(days=num_days)
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {item_type} WHERE ts BETWEEN %s and %s;",
                (week_ago, now),
            )
            results = [dict(row) for row in cur.fetchall()]
        return results

    def query(self):
        with self.create_con() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';",
            )
            results = [query[0] for query in cur.fetchall()]
            data_dict = {}
            for result in results:
                table = self.create_dict(conn, result)
                # Sort data according to the number of "ups" aka upvotes
                # Then append it to the data_dict
                data_dict[result] = sorted(table, key=itemgetter("ups"))[::-1]
        return data_dict

    def insert(self, key, values):
        with self.create_con() as conn, conn.cursor() as cur:
            for thread in values:
                insert_query = (
                    f"INSERT INTO {key} (reddit_id, tag, url, image, name, "
                    "text, ytid, ups, ts, reddit_url) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    " ON CONFLICT (reddit_id) DO UPDATE SET"
                    " (ups) = ROW(EXCLUDED.ups)"
                )
                cur.execute(
                    insert_query,
                    (
                        thread["reddit_id"],
                        thread["tag"],
                        thread["url"],
                        thread["image"],
                        thread["name"],
                        thread["text"],
                        thread["ytid"],
                        thread["ups"],
                        datetime.fromtimestamp(thread["ts"]),
                        thread["reddit_url"],
                    ),
                )
            conn.commit()

    @staticmethod
    def create_database(key):
        conn = psycopg2.connect(
            user="sean",
            password=db_password,
            host="localhost",
            port="5432",
            database="sean",
        )
        with conn, conn.cursor() as cur:
            conn.cursor()
            cur.execute(
                f"CREATE TABLE {key} (reddit_id TEXT UNIQUE, tag TEXT, url TEXT, image "
                f"TEXT, name TEXT, text TEXT, ytid TEXT, ups SMALLINT, ts TIMESTAMP, reddit_url TEXT);"
            )
            conn.commit()

    def db_insert_response(self, response):
        logging.debug("Inserting new data into database")
        for key, value in response.items():
            self.insert(key, value)

    def db_create_database(self, response):
        for key, value in response.items():
            self.create_database(key)
            self.insert(key, value)
