class Strike:
    def rows(self, terms, numbers):
	url = "https://getstrike.net/api/v2/torrents/search/?phrase=%s" % (terms.replace(" ","%20"))
	print url
	torr = cache.get(url, max_age=60).read()
	data = json.loads(torr)["torrents"]
	for d in data:
	    d["name"] = d["torrent_title"]
	return data

    def torrent(self, row):
	return "https://getstrike.net/torrents/api/download/%s.torrent"%row["torrent_hash"]
