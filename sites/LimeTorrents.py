from re import compile
from codecs import open

class LimeTorrents:
    def __init__(self, cache):
        self.cache = cache

    row = compile("<a href=\"(?P<path>http://itorrents.org/torrent/[0-9A-Z]+.torrent\?title=[^\"]+)\" rel=\"nofollow\" class=\"csprite_dl14\".*></a><a href=\"[^\"]+\"><(?P<name>[^<]+)/a>")

    def rows(self, terms, numbers):
        split_numbers = [int(x.strip()) for x in numbers.split()]
        if len(split_numbers) == 2:
            numbers = " S%02de%02d"% tuple(split_numbers)
        # LimeTorrents doesnt' like exclusion terms :(
        s = terms.split(" ")
        terms = "-".join([x for x in s if x[0] != "-"])

        url = "http://0torrents.com/search/all/%s/" % ((terms+numbers).replace(" ", "-"))
        print(url)
        torr = self.cache.get(url, max_age=60).read()
        rows = list(self.row.finditer(torr))
        if rows == [] and torr.find("Search Results for")!=-1:
            open("dump","wb", encoding="utf-8").write(torr)
            #assert rows!=[],rows
        return rows

    def torrent(self, r):
        return r["path"]
