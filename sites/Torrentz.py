class Torrentz:
	#<dl><dt><a href="/f0e1c5ba695ec3071ce2390a7466138adf9a4455"><b>Arrow</b> S02E04 HDTV x264 LOL ettv</a> &#187; sdtv tv divx xvid video shows</dt><dd><span class="v" style="color:#fff;background-color:#79CC53">5&#10003;</span><span class="a"><span title="Thu, 31 Oct 2013 01:04:29">10 days</span></span><span class="s">279 MB</span> <span class="u">7,855</span><span class="d">530</span></dd></dl>
	#row = compile("<dl><dt><a href=\"?(?P<path>/[a-z0-9]+)\"?>(?P<name>.*?)</a>.*?</dt><dd>.*?<span class=\"u\">(?P<seeds>[\d,]+)</span><span class=\"d\">(?P<peers>[\d,]+)</span>", MULTILINE|DOTALL|UNICODE)
	#row = compile("<dl><dt><a href=(?P<path>/[a-z0-9]+)>(?P<name>.*?)</a>.*?</dt><dd><span>✓</span><span title=\d+>([^<]+)</span><span>(\d+ (?:M|G)B)</span><span>(?P<peers>\d+)</span>", MULTILINE|DOTALL|UNICODE)
	row = compile("<dl><dt><a href=(?P<path>/[a-z0-9]+)>(?P<name>.*?)</a>", MULTILINE|DOTALL|UNICODE)
	#row = compile("class=\"epinfo\">(?P<name>[^<]+)</a>\s+</td>\s+<td align=\"center\" class=\"forum_thread_post\">(?P<allpath>(?:<a href=\"(?P<path>[^\"]+)\" class=\"[^\"]+\" title=\"[^\"]+\"></a>)+)",MULTILINE|DOTALL|UNICODE)

	def rows(self,terms, numbers):
		url = "https://torrentz2.eu/search?f=%s" % terms
		print url
		torr = cache.get(url, max_age=60*60).read()

		rows = list(self.row.finditer(torr))
		if rows == []:
			open("dump","wb", encoding="utf-8").write(torr)
			assert rows!=[],rows

			return checkterms(terms, rows)

	def torrent(self,r):
		url = "https://torrentz2.eu" + r['path']
		page = cache.get(url, max_age = -1).read()
		links = findall("<a href=\"([^\"]+?)\" rel=\"e\">", page)

		for l in links:
			if l.startswith("http://torcache.net"):
				print l
				raise Exception

			if l.startswith("http://www.newtorrents.info"):
				print l
				otherpage = cache.get(l, max_age = -1).read()
				patt = compile("<a href='(/down.php\?id=\d+)'><b>download this torrent!</b></a>")
				torrent = patt.search(otherpage)
				return urljoin(l, torrent.groups()[0])

			if l.startswith("http://publichd.se"):
				print l
				otherpage = cache.get(l, max_age = -1).read()
				patt = compile("<a href=\"(download.php\?id=[a-z0-9]+&f=[^\"]+)\">")
				torrent = patt.search(otherpage)
				return urljoin(l.replace("http", "https"), torrent.groups()[0])

			if l.startswith("https://kickass.so"):
				print l
				url = "http://kasssto.come.in/" + l.split("/")[-1]
				print url
				otherpage = cache.get(url, max_age = -1).read()
				patt = compile("href=\"(http://torcache.[^/]+/torrent/[^\"]+)\"><span>Download torrent</span>")
				torrent = patt.search(otherpage)
				return torrent.groups()[0]

			#if l.startswith("http://www.bt-chat.com"):
			#	print l
			#	otherpage = cache.get(l, max_age = -1).read()
			#	patt = compile("<a href=\"(download.php\?id=[a-z0-9]+)\">")
			#	torrent = patt.search(otherpage)
			#	return urljoin(l, torrent.groups()[0].replace("download","download1")) + "&type=torrent"

			if l.startswith("https://www.monova.org"):
				continue
				print l
				otherpage = cache.get(l, max_age = -1).read()
				patt = compile("<a id=\"download-file\" href=\"((?:https:)?//www.monova.org/torrent/download[^\"]+)\"")
				torrent = patt.search(otherpage)
				if torrent == None:
					if otherpage.find("Download via magnet")!=-1:
					print "Magnet-only page"
					else:
					raise Exception, "Bad Regex"
				else:
					return {"url" : urljoin(l, torrent.groups()[0]), "ref" : l}

			if l.startswith("https://rarbg.com"):
				print l
				otherpage = cache.get(l, max_age = -1).read()
				patt = compile("href=\"(/download.php\?id=[a-z0-9]+&f=.*?\.torrent)")
				torrent = patt.search(otherpage)
				return {"url" : urljoin(l, torrent.groups()[0]), "ref" : l}


		print links
		#raise Exception
		return []
