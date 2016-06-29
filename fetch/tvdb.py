from re import compile
from time import strptime

class tvdb:
	args = {"sid":"Tvdb id"}

	row = compile("<tr><td class=\"(?:odd|even)\"><a href=\"/\?tab=episode&seriesid=\d+&seasonid=\d+&id=\d+&amp;lid=\d+\">(?P<season>\d+) x (?P<episode>\d+)</a></td><td class=\"(?:odd|even)\"><a href=\"/\?tab=episode&seriesid=\d+&seasonid=\d+&id=\d+&amp;lid=\d+\">(?P<name>[^<]*)</a></td><td class=\"(?:odd|even)\">(?P<date>\d+-\d+-\d+)</td>")

	def run(self,inf,sid):
		url = "http://thetvdb.com/?tab=seasonall&id=%s"%sid
		data = inf["cache"].get(url,max_age=60*60*12).read()
		data = data.encode('utf-8')
		open("dump","wb").write(data)
		rows = tvdb.row.findall(data)
		#print rows
		neweps = []
		for (season, epnum, title, date) in rows:
			neweps.append((int(season), int(epnum), strptime(date,"%Y-%m-%d"), title))
		return inf["core"](inf,neweps)
