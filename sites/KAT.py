class KAT:
	row = compile("<a href=\"(?P<path>[^\"]+)\" class=\"cellMainLink\">(?P<name>.*?)</a>")

	def rows(self, terms, numbers):
		numbers = [int(x.strip()) for x in numbers.split()]
		numbers = " S%02de%02d"% tuple(numbers)
		url = "http://kattorrent.us/usearch/%s/?field=seeders&sorder=desc" % ((terms+numbers).replace(" ", "%20"))
		print url
		torr = cache.get(url, max_age=60).read()
		rows = list(self.row.finditer(torr))
		if rows == []:
			open("dump","wb", encoding="utf-8").write(torr)
			assert rows!=[],rows
		return checkterms(terms, rows)

	def torrent(self, r):
		url = "https://kattorrent.us" + r['path']
		page = cache.get(url, max_age = -1).read()
		links = findall("title=\"Download (?:verified )?torrent file\" href=\"(//(?:torcache.kattorrent.(?:us|co)/torrent|torcache.net)/[^\"]+)", page)
		try:
			return "http:" + links[0]
		except:
			open("dump","wb", encoding="utf-8").write(page)
			raise
