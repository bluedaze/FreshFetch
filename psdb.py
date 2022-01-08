import psycopg2
import psycopg2.extras
from credentials import db_password
from datetime import datetime
import datetime as DT

# I'm using postgres, because everyone seems to think it's the best
# I think I still prefer sqlite. This is great for like website stuff
# but I think I prefer most of the things I make to be self encapsulated.
# Like, you don't need to setup a database, and you can just run it
# without thinking about the overhead.


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
        week_ago = now - DT.timedelta(days=7)
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {item_type} WHERE ts BETWEEN %s and %s;",
                (week_ago, now),
            )
            results = [dict(row) for row in cur.fetchall()]
        return results

    def query(self):
        # Started playing some code golf, because I was getting bored with this project.
        # In retrospect this was stupid, and I need to make this more readable.
        # TODO: Make more readable
        with self.create_con() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';",
            )
            data_dict = {
                table[0]: self.create_dict(conn, table[0]) for table in cur.fetchall()
            }
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
    def createDatabase(key):
        print("Creating database")
        conn = psycopg2.connect(
            user="sean",
            password=db_password,
            host="localhost",
            port="5432",
            database="sean",
        )
        with conn, conn.cursor() as cur:
            cur = conn.cursor()
            cur.execute(
                f"CREATE TABLE {key} (reddit_id TEXT UNIQUE, tag TEXT, url TEXT, image TEXT, name TEXT, text TEXT, ytid TEXT, ups SMALLINT, ts TIMESTAMP, reddit_url TEXT);"
            )
            conn.commit()

    def db_insert_response(self, response):
        print("Inserting new data into database")
        for key, value in response.items():
            self.insert(key, value)

    def db_create_database(self, response):
        for key, value in response.items():
            self.createDatabase(key)
            self.insert(key, value)