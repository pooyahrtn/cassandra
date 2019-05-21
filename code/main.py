

from cassandra.query import SimpleStatement
from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
import logging
from datetime import datetime, timedelta

log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)


def get_dummy():
    posts = []
    for i in range(40):
        posts.append({
            "user_id": "{}".format(i % 10 + 1),
            "time": datetime.now() + timedelta(minutes=i),
            "content": "comment {}".format(i),
        })
    return posts


def main():
    cluster = Cluster()
    session = cluster.connect()
    # session.execute("DROP KEYSPACE tagdb")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS tagdb
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': 2 }
        """)

    log.info("setting keyspace...")
    session.set_keyspace('tagdb')

    log.info("creating table...")

    session.execute("""
        CREATE TABLE IF NOT EXISTS sometag (
            user_id text,
            date timestamp,
            content text,
            PRIMARY KEY ((user_id), date)
        ) WITH CLUSTERING ORDER BY (date DESC)
        """)

    prepared = session.prepare("""
        INSERT INTO sometag (user_id, date, content)
        VALUES (?, ?, ?)
        """)
    prepared.consistency_level = ConsistencyLevel.ONE
    posts = get_dummy()
    for post in posts:
        log.info("inserting {}".format(str(post["time"])))
        session.execute(
            prepared, (post["user_id"], post["time"], post["content"]))

    future = session.execute_async(
        """SELECT * FROM sometag LIMIT 10"""
    )
    log.info("user_id\ttime\tcontent")
    log.info("---\t----\t----")

    try:
        rows = future.result()
        for row in rows:
            log.info('\t'.join([row.user_id, str(row.date), row.content]))
    except Exception:
        log.exception("Error reading rows:")
        return

    session.execute("DROP KEYSPACE tagdb")


if __name__ == '__main__':
    main()
