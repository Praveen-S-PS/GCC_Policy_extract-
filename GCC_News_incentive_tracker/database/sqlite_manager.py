import sqlite3


class SQLiteManager:

    def __init__(self):

        self.conn = sqlite3.connect(
            "data/gcc_news.db"
        )

        self.create_table()

    def create_table(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gcc_news(

            title TEXT UNIQUE,

            country TEXT,

            state TEXT,

            category TEXT,

            policy_type TEXT,

            incentive_type TEXT,

            jobs TEXT,

            investment TEXT,

            source TEXT,

            site TEXT,

            published_date TEXT
        )
        """)

        self.conn.commit()

    def article_exists(self, title):

        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT 1 FROM gcc_news WHERE title=?",
            (title,)
        )

        return cursor.fetchone() is not None

    def insert(self, record):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO gcc_news
        VALUES(
            ?,?,?,?,?,?,?,?,?,?,?
        )
        """,

        (
            record["title"],
            record["country"],
            record["state"],
            record["category"],
            record["policy_type"],
            record["incentive_type"],
            record["jobs"],
            record["investment"],
            record["source"],
            record["site"],
            record["date"]
        ))

        self.conn.commit()

    def get_all(self):

        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM gcc_news"
        )

        return cursor.fetchall()