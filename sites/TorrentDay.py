from codecs import open
from re import compile, MULTILINE, DOTALL
import os.path
import html

class TorrentDay:
	#<td class=torrentNameInfo><a class="b hv" href="/t/4104213">Game of Thrones S08E04 480p x264-mSD</a> <a href="/download.php/4104213/Game.of.Thrones.S08E04.480p.x264-mSD.torrent"> <td class="ac seedersInfo">235</td><td class="ac leechersInfo">22</td>
	row = compile("<td class=torrentNameInfo><a class=\"b? hv\" href=\"\/t\/\d+\">(?P<name>[^<]+)</a>.*?<a href=\"(?P<download>/download.php/\d+/[^\"]+)\">.*?<td class=\"ac seedersInfo\">(?P<seeds>[\d,]+)</td><td class=\"ac leechersInfo\">(?P<peers>[\d,]+)</td>", MULTILINE|DOTALL)
	#rowcount = compile("<div align='center' class='paging'><span>1-(\d+)</span>")

	cookie = open(os.path.join(os.path.dirname(__file__), "td-cookie")).read()

	def __init__(self, cache):
		self.cache = cache

	def rows(self, terms, numbers):
		# TorrentDay doesn't like exclusion terms :(
		s = terms.split(" ")
		terms = "+".join([x for x in s if x[0] != "-"])
		url = "https://torrentday.it/t?q=%s;o=seeders" % (terms.replace(" ", "+"))
		print(url)
		torr = self.cache.get(url, max_age=60, headers={"Cookie": self.cookie})
		print(torr)
		torr = torr.read()
		rows = list(self.row.finditer(torr))
		if torr.find("Nothing found!")==-1:
			open("dump",mode = "wb", encoding="utf-8").write(torr)
		else:
			print(torr.find("Nothing found"))
		print("row count", len(rows))
		if rows == []:
			print(terms)
			open("dump",mode = "wb", encoding="utf-8").write(torr)
			return []
		return [x for x in rows if x.groupdict()["name"].find("Leaked")==-1 and x.groupdict()["name"].find("SUBFRENCH") == -1]

	def torrent(self, row):
		return [{"url":"https://torrentday.it" + html.unescape(row["download"]), "headers":{"Cookie":self.cookie}}]
