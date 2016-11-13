from re import compile,findall,IGNORECASE,MULTILINE,DOTALL,split,UNICODE,sub

class NyaaTorrents:
	def __init__(self, cache):
		self.cache = cache

	row = compile("""<td class="tlistname"><a href="(?:http:)?//[^/]+/\?page=view&#38;tid=\d+">(?P<name>[^<]+)</a></td>\S*<td class="tlistdownload">.*?<a href="(?P<path>(?:http:)?//[^/]+/\?page=download&#38;tid=\d+)" title="Download"[^>]*><img src="[^\"]+" alt="DL"></a>.*?</td>\S*<td class="tlistsize">\d+.\d+ (?:G|M)iB</td>(?P<items>.+?)</tr>""", IGNORECASE|DOTALL)
	item = compile("<td class=\"([^\"]+)\"[^>]*>([^<]+)</td>")
	singleitem = compile("<span class=\"([^\"]+)\">([^<]+)</span>")
	downloadlink = compile("<div class=\"viewdownloadbutton\"><a href=\"(//[^/]+/\?page=download&#38;tid=\d+)")

	def rows(self,terms,numbers):
		terms = " ".join([x for x in (terms + " " +numbers).split(" ") if len(x)>0 and x[0]!="-"])
		url = "http://www.nyaatorrents.org/?page=search&term=%s&sort=1"%(terms.replace(" ","+"))
		print url
		torr = self.cache.get(url,max_age=60*60).read()
		torr = torr.replace("<div><!-- --></div>","")
		if torr.find("Torrent description:")!=-1: # single item redirect
			rows = []
			items = dict(self.singleitem.findall(torr))
			otheritems = dict(self.item.findall(torr))
			link = self.downloadlink.findall(torr)
			rows.append({"seeds":items["viewsn"], "peers" :items["viewln"], "name":otheritems["viewtorrentname"], "path": "http:" + link[0]})
		else:
			rows = [x.groupdict() for x in list(self.row.finditer(torr))]
			if rows == [] and torr.find("No torrents found") == -1:
				file("dump","wb").write(torr)
				assert rows!=[],rows

			for r in rows:
				items = dict(self.item.findall(r['items']))
				if 'tlistsn' in items:
					r['seeds'] = items['tlistsn']
				if 'tlistln' in items:
					r['peers'] = items['tlistln']
		return rows

	def torrent(self,r):
		return r["path"].replace("&amp;","&").replace("&#38;", "&")
