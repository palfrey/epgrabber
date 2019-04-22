from re import compile, MULTILINE, DOTALL, findall
from codecs import open

class KAT:
	row = compile("<a href=\"(?P<path>[^\"]+)\" title=\"(?P<name>[^\"]+)\" class=\"cellMainLink\">")

	def __init__(self, cache, checkterms):
		self.cache = cache
		self.checkterms = checkterms

	def rows(self, terms, numbers):
		numbers = [int(x.strip()) for x in numbers.split()]
		numbers = " S%02de%02d"% tuple(numbers)
		url = "https://katcrs.bid/search/%s/?field=seeders&sorder=desc" % ((terms+numbers).replace(" ", "%20"))
		print(url)
		torr = self.cache.get(url, max_age=60).read()
		rows = list(self.row.finditer(torr))
		if rows == []:
			open("dump","wb", encoding="utf-8").write(torr)
			assert rows!=[],rows
		return self.checkterms(terms, rows)

	def torrent(self, r):
		url = "https://katcrs.bid/" + r['path']
		print url
		page = self.cache.get(url, max_age = -1).read()
		links = findall("title=\"Download (?:verified )?torrent file\" href=\"(//itorrents.org/torrent/[^\"]+)", page)
		try:
			return list(set(["http:" + x for x in links]))
		except:
			open("dump","wb", encoding="utf-8").write(page)
			print "No torrent link"
			raise
			return []
