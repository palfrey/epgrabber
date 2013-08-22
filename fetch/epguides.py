# vim: set fileencoding=utf-8
from re import compile,split
from enum import Enum
from time import strptime

class EpType(Enum):
	TVRage = 1
	TVcom = 2

class epguides:
	args = {"name":"Epguides page name e.g. http://epguides.com/NAME"}

	def run(self,inf,name,listp=None):
		url = "http://epguides.com/%s/"%name
		if listp:
			data= {"list":listp}
		else:
			data = None
		#print url
		data = inf["cache"].get(url,max_age=60*60*24*2,data=data).read()
		if data.find("TVRage present")!=-1:
			kind = EpType.TVRage
			matcher = compile("www.tvrage.com/.+?/episodes/\d+")
			lines = []
			tagstrip = compile(r'<.*?>')
			for line in data.split("\n"):
				if matcher.search(line)!=None:
					bits = list(split("\s+",line,3))
					#print "bits",bits
					assert bits[-1].find("href=")!=-1,bits
					bits[-1] = tagstrip.sub('',bits[-1]).strip()
					if bits[1].find("-")==-1:
						print "bits invalid",bits
						continue
					(season,ident) = bits[1].split("-",1)
					del bits[0]
					bits[0:1] = (ident, season)
					lines.append(bits)
					#print "rev", bits
			eps = lines
		elif data.find("TV.com")!=-1:
			patt = compile("(\d+).\s+(\d+)-(.+?)\s+(?:[\dA-Z\-]+)?\s+(\d+ [A-Z][a-z]+ \d+)?\s+<a target=\"(?:visit|_blank)\" href=\"[^\"]+\">([^<]+)</a>")
			kind = EpType.TVcom
			eps = patt.findall(data)
		else:
			file('dump','w').write(data)
			raise Exception
		if len(eps) ==0:
			file('dump','w').write(data)
			raise Exception
		neweps = []
		for e in eps:
			print "e", e
			(epnum, season, date, title) = e
			#print epnum, season, title
			epnum = int(epnum)
			try:
				if kind == EpType.TVRage:
					date = strptime(date,"%d/%b/%y")
				else:
					date = strptime(date,"%d %b %y")
			except ValueError:
				if date.find(" ")!=-1 or date.find(" ")!=-1:
					print e
					raise
				date = None
			title = title.replace("[Recap]","").replace("[Trailer]","").strip()
			neweps.append((int(season), epnum, date,title))
			#print neweps[-1]
		return inf["core"](inf,neweps)
