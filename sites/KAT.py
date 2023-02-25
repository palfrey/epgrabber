from re import compile, MULTILINE, DOTALL, findall
from codecs import open


class KAT:
    row = compile('<a href="(?P<path>[^"]+)" class="cellMainLink">\s+(?P<name>.+?)</a>')
    # row = compile("<a href=\"(?P<path>[^\"]+)\" title=\"(?P<name>[^\"]+)\" class=\"cellMainLink\">")

    def __init__(self, cache, checkterms):
        self.cache = cache
        self.checkterms = checkterms

    def rows(self, terms, numbers):
        s = terms.split(" ")
        terms = " ".join([x for x in s if x[0] != "-"])
        print(numbers.split(" "))
        numbers = "S%02dE%02d" % tuple([int(x) for x in numbers.split(" ") if x != ""])
        url = "https://kat.am/usearch/%s%%20%s/?sortby=seeders&sort=desc" % (
            terms,
            numbers,
        )
        print(url)
        torr = self.cache.get(url, max_age=60).read()
        rows = list(self.row.finditer(torr))
        if rows == []:
            open("dump", "wb", encoding="utf-8").write(torr)
            assert rows != [], rows
        return self.checkterms(terms, rows)

    def torrent(self, r):
        url = "https://kat.am" + r["path"]
        print(url)
        page = self.cache.get(url, max_age=-1).read()
        links = findall(
            'title="Download (?:verified )?torrent file" href="(//itorrents.org/torrent/[^"]+)',
            page,
        )
        try:
            return list(set(["http:" + x for x in links]))
        except:
            open("dump", "wb", encoding="utf-8").write(page)
            print("No torrent link")
            raise
            return []
