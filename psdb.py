import psycopg2
import psycopg2.extras
from credentials import db_password
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
            user="sean", password=db_password, host="localhost", port="5432", database="sean"
        )
        return conn

    def create_dict(self, conn, item_type):
        # This function creates a dictionary based on the returned results.
        # This is much easier to parse in table.html than the tuples
        # that it was originally returning.
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(f"SELECT * FROM {item_type};")
            results = [dict(row) for row in cur.fetchall()]
        return results

    def query(self):
        # Started playing some code golf, because I was getting bored with this project.
        with self.create_con() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            data_dict = {table[0]: self.create_dict(conn, table[0]) for table in cur.fetchall()}
        return data_dict

    def insert(self, key, values):
        with self.create_con() as conn, conn.cursor() as cur:
            for thread in values:
                insert_query = (
                    f"INSERT INTO {key} (reddit_id, tag, url, image, name, "
                    "text, ytid, ups, time_posted, reddit_url) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    " ON CONFLICT (reddit_id) DO UPDATE SET"
                    f" (ups) = ROW(EXCLUDED.ups)"
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
                        thread["time_posted"],
                        thread["reddit_url"],
                    ),
                )
            conn.commit()
