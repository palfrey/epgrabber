# http://www.tvrage.com/DoctorWho_2005/episode_guide/all

import re
from time import strptime

class tvrage:
	args = {"name":"Tvrage page name e.g. http://www.tvrage.com/NAME"}

	epPattern = re.compile("<h1 class=\"content_title hover_blue\">(.*?)<br />")
	titlePattern = re.compile("<a [^>]+>(.*?)</a>")
	datePattern = re.compile("<i>(.*?)</i>")

	def run(self,inf,name):
		url = "http://www.tvrage.com/%s/episode_guide/all/"%name
		data = inf["cache"].get(url,max_age=60*60*24*2).read()
		open("dump","wb").write(data)
		eps = tvrage.epPattern.findall(data)
		neweps = []
		for ep in eps:
			title = tvrage.titlePattern.search(ep)
			title = title.groups()[0]
			date = tvrage.datePattern.search(ep)
			if date == None:
				print "no date for", title
				continue
			date = date.groups()[0]
			if date.find("/")==-1:
				print "no full date for", title, date
				continue
			date = strptime(date,"%b/%d/%Y")
			title = title[title.find(":")+1:]
			if title.find("-") == -1 or title.find("x") ==-1:
				print "not a proper episode", title
				continue
			epdata, title = title.split("-", 2)
			title = title.strip()
			season, epnum = epdata.split("x")
			print title, date, season, epnum
			neweps.append((int(season), int(epnum), date,title))
		#print eps
		return inf["core"](inf,neweps)

