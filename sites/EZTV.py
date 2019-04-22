from re import compile,findall,IGNORECASE,MULTILINE,DOTALL,split,UNICODE,sub
from codecs import open

class EZTV:
	def __init__(self, cache):
		self.cache = cache

	row = compile("class=\"epinfo\">(?P<name>[^<]+)</a>\s+</td>\s+<td align=\"center\" class=\"forum_thread_post\">(?P<allpath>.+?</td>)",MULTILINE|DOTALL|UNICODE)

	def rows(self, terms, numbers):
		url = "https://eztv.wf/search/"

		# EZTV doesnt' like exclusion terms :(
		s = terms.split(" ")
		terms = "-".join([x for x in s if x[0] != "-"])

		torr = self.cache.get(url + terms, max_age=60*60).read()

		rows = list(self.row.finditer(torr))
		if rows == []:
			print(terms)
			open("dump",mode = "wb", encoding="utf-8").write(torr)
			return []
			#assert rows!=[],rows


		terms = terms.split("-")
		goodterms = [x.lower() for x in terms if x[0]!="-"]
		badterms = [x[1:].lower() for x in terms if x[0] == "-"]

		print("good", goodterms)
		print("bad", badterms)

		ret = []
		for nr in rows:
			r = nr.groupdict()
			r['name'] = sub('<[^<]+?>', '', r['name'])
			for x in goodterms:
				if r['name'].lower().find(x)==-1:
					print("bad name", r['name'])
					break
			else:
				for x in badterms:
					if r['name'].lower().find(x)!=-1:
						print("bad name", r['name'])
						break
				else:
					print("good name", r['name'])
					ret.append(nr)
		return ret

	def torrent(self,r):
		httppat = compile("<a href=\"(https?://[^\"]+)")
		ret = [x for x in httppat.findall(r["allpath"]) if x.endswith(".torrent")]
		#raise Exception, ret
		return ret
