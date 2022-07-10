try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite

from episodes_pb2 import All
from sys import argv

con = sqlite.connect(argv[1])

cur = con.cursor()
cur.execute(
    "select name,search,season,episode,command,last,checked from series order by last desc"
)

all = All()

for row in cur.fetchall():
    series = all.series.add()
    print(row)
    (
        series.name,
        series.search,
        series.season,
        series.episode,
        series.listing,
        series.last,
        series.checked,
    ) = row

f = open(argv[2], "wb")
f.write(all.SerializeToString())
f.close()
