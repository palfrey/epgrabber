from codecs import open
from re import compile
import os.path

class TorrentDay:
	row = compile("<tr><td class=t_label><a href=\"\?\d+\"><img src=\"/images/categories/[^\"]+\"></a></td><td class=torrentNameInfo><a class=\"\" href=\"(?P<path>/details.php\?id=\d+)\">(?P<name>[^<]+)</a>.*?<td class=ac><a href=\"(?P<download>/download.php/\d+/[^\"]+)\">.*?<td class=\"ac seedersInfo\">(?P<seeds>\d+)</td><td class=\"ac leechersInfo\">(?P<peers>\d+)</td></tr>")

	cookie = open(os.path.join(os.path.dirname(__file__), "td-cookie")).read()

	def __init__(self, cache):
		self.cache = cache

	def rows(self, terms, numbers):
		# TorrentDay doesn't like exclusion terms :(
		s = terms.split(" ")
		terms = "-".join([x for x in s if x[0] != "-"])
		url = "https://torrentday.it/t?32=&33=&14=&26=&7=&34=&2=&q=%s" % (terms.replace(" ", "%20"))
		print url
		torr = self.cache.get(url, max_age=60*60, headers={"Cookie": self.cookie}).read()
		rows = list(self.row.finditer(torr))
		if rows == []:
			print terms
			open("dump",mode = "wb", encoding="utf-8").write(torr)
			return []
		return rows

	def torrent(self, row):
		return [{"url":"https://torrentday.it" + row["download"], "headers":{"Cookie":self.cookie}}]
