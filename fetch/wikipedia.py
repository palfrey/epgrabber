from re import compile,IGNORECASE,MULTILINE,DOTALL
from time import strptime, struct_time

trs = compile("<tr[^>]*>(.*?)</tr>",MULTILINE|DOTALL)
tds = compile("<t(?:d|h)[^>]*>(.*?)</t(?:d|h)>",MULTILINE|DOTALL)
bold = compile("<b>(.*?)</b>",MULTILINE|DOTALL)
dm = compile("<a href=\"/wiki/\w+\" title=\"\w+ \w+\">(\w+[- ]\w+)</a>")
year = compile("<a href=\"/wiki/\d+\" title=\"\d+\">(\d+)</a>")
title = compile(">([^<]+)</a>")
tags = compile(r'<[^<]*?/?>')

class wikipedia:
	args = {
			"name":"Wikipedia page name e.g. http://en.wikipedia.org/NAME. Should be a 'List of' page",
			"anime":"Is this an anime series? i.e. no seasons, just episode numbers"
			}
	def run(self,inf,page,anime=False):
		data = inf["cache"].get("https://en.wikipedia.org/wiki/%s"%page,max_age=60*60*24,ignore_move=True).read()
		if data.find("List of")==-1: # dodgy page
			return None

		blocks = trs.findall(data)
		items = []
		#file("dump","wb").write(data)
		for b in blocks:
			if b.find("<td")==-1:
				continue
			bits = tds.findall(b)
			if len(bits)<3:
				continue
			blob = {}
			#print "bits",bits
			for bi in bits:
				if bi.find("List of")!=-1:
					continue
				try:
					try:
						blob["number"] = str(int(bi))
					except ValueError:
						blob["number"] = str(float(bi))
					continue
				except ValueError:
					pass
				if "title" not in blob:
					if bi.find("<b>")!=-1: # assume title
						m = bold.findall(bi)[0]
						if m.find("<")!=-1:
							m = m[:m.find("<")]
						if len(m)>0 and m[0] in ["\"","\'"]:
							m = m[1:]
						if len(m) == 0:
							continue
						if m[-1] in ["\"","\'"]:
							m = m[:-1]
						blob["title"] = m
						continue
					elif bi == bits[0]:
						st = title.findall(bi)
						if len(st)>0:
							blob["title"] = st[0]
							continue
						elif len(blob)>0:
							raise Exception, (bi, blob)
				try:
					blob["year"] = year.findall(bi)[0]
					#print "year",blob["year"]
				except IndexError:
					pass
				try:
					if bi.find("20")!=-1: # first bit of 20xx?
						blob["date"] = dm.findall(bi)[0]
				except IndexError:
					try:
						if bi.find("<")!=-1:
							bi = bi[:bi.find("<")]
						blob["date"] = strptime(bi,"%B %d, %Y")
					except ValueError:
						#print "not date",bi
						pass
			if len(blob.keys())>0:
			        #print "blob", blob
			        if bits[0] == "Total TD":
				    continue
				if not blob.has_key("title"): # guess that first is title
					#print "title?",bits[0], blob
					pass
				items.append(blob)
		#raise Exception,items
		if len(items)==0:
			print type(data)
			open("dump","wb").write(data)
			raise Exception
		eps = []
		#print [ms for ms in items]
		for ma in items:
			#print "ma",ma
			if "date" not in ma:
				continue
			if type(ma["date"]) == struct_time:
				date = ma["date"]
			else:
				try:
					cmb = (ma["date"]+" "+ma["year"]).replace("-"," ")
				except KeyError:
					print ma
					raise
				try:
					date = strptime(cmb,"%B %d %Y")
				except ValueError,e: # alternate format?
					try:
						date = strptime(cmb,"%m %d %Y")
					except ValueError: # no matches
						print "date doesn't match for",cmb,"discarding"
						continue

			try:
				number = ma["number"]
			except KeyError:
				print "no valid number. keys are",ma
				continue
				
			if len(number)<3 or anime:
				season = 0
				epnum = number
			elif number.find("x")!=-1:
				(season,epnum) = number.split("x")
			else:
				epnum = number[-2:]
				season = number[:-2]

			if "title" in ma:
				ti = ma["title"]
			else:
				ti = ""

			try:
				eps.append((int(season),int(epnum),date, ti))
			except ValueError:
				print "non-integer season or epnum?",season,epnum
			except KeyError:
				print "no valid title. keys are",ma
		if len(eps) == 0:
			raise Exception
		#print eps
		return inf["core"](inf,eps)
