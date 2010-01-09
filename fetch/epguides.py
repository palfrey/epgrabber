# vim: set fileencoding=utf-8
from re import compile,split
from enum import Enum
from time import strptime

class EpType(Enum):
	TVRage = 1
	TVcom = 2

class epguides:
	args = {"name":"Epguides page name e.g. http://epguides.com/NAME"}

	def run(self,inf,name):
		data = inf["cache"].get("http://epguides.com/%s/"%name,max_age=60*60*24*2).read()
		if data.find("TVRage present")!=-1:
			kind = EpType.TVRage
			matcher = compile("www.tvrage.com/.+?/episodes/\d+")
			lines = []
			tagstrip = compile(r'<.*?>')
			for line in data.split("\n"):
				if matcher.search(line)!=None:
					bits = list(split("\s+",line,3))
					#print "bits",bits
					if bits[-1].find("<a href=")!=0:
						bits = list(split("\s+",line,4))
						del bits[2] # remove the ident
					assert bits[-1].find("<a href=")==0,bits
					bits[-1] = tagstrip.sub('',bits[-1])
					assert bits[1].find("-")!=-1,bits
					(season,ident) = bits[1].split("-",1)
					del bits[1]
					bits[1:1] = (season,ident)
					lines.append(bits)
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
			(epnum, season, identifier, date, title) = e
			try:
				epnum = str(int(identifier))
			except ValueError,e:
				valid = ""
				for x in identifier.strip():
					if x.isdigit():
						valid += x
					else:
						break
				if valid !="":
					epnum = valid
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
			neweps.append((season, epnum, date,title))
		return inf["core"](inf,neweps)
