from codecs import open
from re import compile, MULTILINE, DOTALL
import os.path

class TorrentDay:
	# <a class="b" href="/t/3412606">My Hero Academia S03E13 AAC MP4-Mobile</a> <span style="background: #ffba25 none repeat scroll 0 0;border-radius: 3px;font-size: 11px;font-weight: bold;padding: 0px 5px; color:#000">New!</span><div class="ar t_ctime">8.4 2016 Animation Action Comedy | 3.5 days ago</div></td><td class=ac><a href="/download.php/3412606/My.Hero.Academia.S03E13.AAC.MP4-Mobile.torrent"><img src="/images/browse/uTorrent.png" alt="Download" title="Download"></a></td><td class=ac><a href="/t/3412606?bookmark"><i class="fa fa-bookmark-o" title="Bookmark"></i></a></td><td class=ac><a href="/details.php?id=3412606&amp;page=0#startcomments" alt="Comments" title="Comments">0</a></td><td class=ac style="white-space: nowrap">94.4 MB</td><td class="ac seedersInfo">3</td><td class="ac leechersInfo">0</td>
	row = compile("<a class=\"b\" href=\"/t/\d+\">(?P<name>[^<]+)</a>.*?<a href=\"(?P<download>/download.php/\d+/[^\"]+)\">.*?<td class=\"ac seedersInfo\">(?P<seeds>[\d,]+)</td><td class=\"ac leechersInfo\">(?P<peers>[\d,]+)</td>", MULTILINE|DOTALL)
	#rowcount = compile("<div align='center' class='paging'><span>1-(\d+)</span>")

	cookie = open(os.path.join(os.path.dirname(__file__), "td-cookie")).read()

	def __init__(self, cache):
		self.cache = cache

	def rows(self, terms, numbers):
		# TorrentDay doesn't like exclusion terms :(
		s = terms.split(" ")
		terms = "+".join([x for x in s if x[0] != "-"])
		url = "https://torrentday.it/t?q=%s&qf=" % (terms.replace(" ", "+"))
		print(url)
		torr = self.cache.get(url, max_age=60, headers={"Cookie": self.cookie})
		print(torr)
		torr = torr.read()
		rows = list(self.row.finditer(torr))
		if torr.find("Nothing found!")==-1:
			open("dump",mode = "wb", encoding="utf-8").write(torr)
		else:
			print torr.find("Nothing found")
		print "row count", len(rows)
		if rows == []:
			print(terms)
			open("dump",mode = "wb", encoding="utf-8").write(torr)
			return []
		return [x for x in rows if x.groupdict()["name"].find("Leaked")==-1]

	def torrent(self, row):
		return [{"url":"https://torrentday.it/" + row["download"], "headers":{"Cookie":self.cookie}}]
