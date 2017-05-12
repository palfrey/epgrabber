from codecs import open
from re import compile, MULTILINE, DOTALL
import os.path

class TorrentDay:
	row = compile("<td class=\"torrentNameInfo\"><div class='torrentTableNameDiv'><a class='torrentName' href='details.php\?id=\d+'><b>(?P<name>[^<]+)</b></a>.*?<a class=\"index\" href=\"(?P<download>download.php/\d+/[^\"]+)\"><img src=\"/images/browse/uTorrent.png\" alt=\"Download as .torrent file\" border=0></a></td>.*?<td class=\"ac seedersInfo\">(?P<seeds>[\d,]+)</td>.*?<td class=\"ac leechersInfo\">(?P<peers>[\d,]+)</td>", MULTILINE|DOTALL)
	rowcount = compile("<div align='center' class='paging'><span>1-(\d+)</span>")

	cookie = open(os.path.join(os.path.dirname(__file__), "td-cookie")).read()

	def __init__(self, cache):
		self.cache = cache

	def rows(self, terms, numbers):
		# TorrentDay doesn't like exclusion terms :(
		s = terms.split(" ")
		terms = "+".join([x for x in s if x[0] != "-"])
		url = "https://torrentday.it/browse.php?search=%s&cata=yes&sort=7&type=desc" % (terms.replace(" ", "+"))
		print url
		torr = self.cache.get(url, max_age=60*60, headers={"Cookie": self.cookie}).read()
		rows = list(self.row.finditer(torr))
		expected = int(self.rowcount.findall(torr)[0])
		if len(rows) != expected:
		    for row in rows:
			print row.groups()
		    raise Exception, (len(rows), expected)
		if rows == []:
			print terms
			open("dump",mode = "wb", encoding="utf-8").write(torr)
			return []
		return rows

	def torrent(self, row):
		return [{"url":"https://torrentday.it/" + row["download"], "headers":{"Cookie":self.cookie}}]
