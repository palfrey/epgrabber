def scarywater(*args):
	if len(args)==3:
		(inf,group,name) = args
		exclude = ""
	else:
		(inf,group,name,exclude) = args
	global yesterday
	base = "http://a.scarywater.net/%s/"%group
	data = inf["cache"].get(base,max_age=60*60).read()
	href = compile("<a href=\"([^\"]+)\"[^>]+>([^<]+)</a>")
	eps = []
	added = []
	crossref = {}
	for (url,text) in href.findall(data):
		#print url,text
		if name not in text or (exclude!="" and exclude in text):
			continue
		for x in text.replace("_"," ").replace("-"," ").replace("["," ").split():
			try:
				season = int(x)
				break
			except ValueError:
				continue
		try:
			if season in added:
				continue
		except UnboundLocalError:
			print url,text
			raise
		added.append(season)
		eps.append((season,0,yesterday,text))
		crossref[season] = url
	if eps == []:
		print "NO SCARYWATER EPISODES"
		return None
	ret = core(inf,eps)
	if ret!=None and crossref.has_key(ret["season"]):
		ret["url"] = base+crossref[ret["season"]]
	#print "ret",ret
	return ret

