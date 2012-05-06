#!/usr/bin/python

import sys
try:
	from urlgrab import Cache, URLTimeoutError
except:
	print "You need to install urlgrab. Get it using 'git clone git://github.com/palfrey/urlgrab.git urlgrab'"
	sys.exit(1)
from re import compile,IGNORECASE,MULTILINE,DOTALL,split,UNICODE
from time import strptime,strftime,localtime,time
from os.path import exists,getsize,basename,join
from os import remove
from urlparse import urljoin
from datetime import datetime, timedelta,date
from optparse import OptionParser
from types import ListType
try:
	import vobject
except ImportError:
	vobject = None
from shutil import move
try:
	from BitTorrent.bencode import bdecode
except ImportError:
	bdecode = None

import fetch

from codecs import getdecoder

import urllib
class AppURLopener(urllib.FancyURLopener):
    version = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11"

urllib._urlopener = AppURLopener()

options = None
cache = None
db = None

idnum = compile("(?:S(\d+)E(\d+))|(?:(\d+)x(\d+))|(?: (\d)(\d{2}) - )|(?: (\d+)X(\d+) )|(?:\.(\d+)(\d{2}).)|(?: (\d{2}))|(?:Season (\d+) Episode (\d+))",IGNORECASE)

def saferetrieve(url,fname):
	badurls = ["http://torrent.zoink.it"]

	for b in badurls:
		if url.find(b)!=-1:
			print "bad url", url, b
			return False

	global bdecode
	try:
		print "Trying",url
		tmpname = join("/tmp",basename(fname))
		cache.urlretrieve(url,tmpname)
		if exists(tmpname) and getsize(tmpname)>1000:
			print "Retrieved!",url
			if bdecode:
				try:
					torr = bdecode(open(tmpname).read())
				except ValueError:
					print "can't decode"
					return False
				bd = torr['info']

				try:
					length = bd['length']
					if length in ([364904448,365431575,183500806,183500808,183656487]+list(range(367001600,367001600+50))):
						print "Bad torrent!"
						return False
				except KeyError:
					assert "files" in bd,bd.keys()

				if 'files' in bd: # folder torrent
					for path in bd['files']:
						path = path['path'][-1]
						if path.find(".wmv")!=-1:
							print "Found %s, bad torrent!"%path
							return False
			trackers = []
			if "announce-list" in torr:
				for x in torr['announce-list']:
					trackers.extend(x)
			if "announce" in torr:
				trackers.append(torr["announce"])
			badtrackers = ["http://tracker.hexagon.cc:2710/announce", "http://tracker.thepiratebay.org/announce"]
			good = [x for x in trackers if x not in badtrackers]
			if len(good) == 0:
				print "no good trackers", trackers, torr
				return False
			move(tmpname, fname)
			return True
		else:
			if exists(tmpname):
				remove(tmpname)
			print "Too small!"
			return False
	except IOError:
		print "IOError!"
		return False

def info(name):
	global cache,yesterday,options,db
	#print "options",options
	keys = ["name","search","season","episode","last","checked"]
	ret = {}
	data = [s for s in db.series if s.name == name][0]
	for k in range(len(keys)):
		if hasattr(options,keys[k]) and getattr(options,keys[k])!=-1:
			ret[keys[k]] = getattr(options,keys[k])
		elif keys[k] == "search" and data.search == "":
			ret[keys[k]] = data.name
		else:
			ret[keys[k]] = getattr(data,keys[k])
	ret["cache"] = cache
	ret["yesterday"] = yesterday
	ret["core"] = core
	ret["options"] = options
	return ret

def core(inf,eps):
	if eps == []:
		raise Exception, "NO EPISODES FOUND"
	seas = inf["season"]
	num = inf["episode"]
	has_prev = False

	eps.sort(lambda a,b:cmp(int(a[0])*100+int(a[1]),int(b[0])*100+int(b[1])))
		
	prev = (0,0)
	last = None
	for e in eps:
		(season,epnum,date,title) = e
		season = int(season)
		epnum = int(epnum)
		if (season,epnum) == prev:
			continue
		prev = (season,epnum)
		if season<seas or (season==seas and num>epnum):
			last = (season,epnum,date)
			continue
		print season,epnum,date,has_prev
		if not has_prev and (season>seas or (season==seas and num!=epnum)):
			has_prev= True
		print "%02d-%02d"%(season,epnum),
		if date !=None:
			print strftime("%Y-%m-%d",date),
		else:
			print "TBA"
			continue
		print title
		if not has_prev:
			print "has_prev"
			has_prev = True
			last = (season,epnum,date)
			continue
		else:
			print "last",last
		return {"name":inf["name"],"season":season,"epnum":epnum,"date":date, "title":title}
	else:
		print "ran out of episodes!"
		return None

def	torrent(name,season,epnum):
	fname = "%s - %02d-%02d.torrent"%(name,season,epnum)
	print "fname:",fname
	return fname
	
def update(name,season,epnum,force=False):
	global curr
	fname = torrent(name,season,epnum)
	if exists(fname) or force:
		seas = info(name)["season"]
		num  = info(name)["episode"]
		print "season,epnum",season,epnum,seas,num
		if (season == seas and epnum == num) and not force:
			print "Duplicate numbers!"
			return
		
		s = get_series(name)
		if season !=0:
			s.season = season
		s.episode = epnum
		s.last = curr
		store_values()
	return fname
		
class Isohunt:
	#row = compile("<tr class=\"hlRow\" onClick=\"servOC\(\d+,\\'/torrent_details/(?P<path>[^']+)'.*?<td class=\"row3\" id=name\d+>(?P<name>.*?)(?=</td>)</td><td class=\"row3\" title='\d+ file(?:s)?'>\d+.\d+ (?:M|G|K)B</td><td class=\"row1\">(?P<seeds>\d*)</td><td class=\"row3\">(?P<peers>\d*)</td>")
	row = compile("<a onClick=\"servOC\(\d+,\\'/torrent_details/(?P<path>[^']+)'.*?\?tab=summary'>(?P<name>.*?)(?=</a>)</a></td><td class=\"row3\" title='\d+ file(?:s)?'>\d+.\d+ (?:M|G|K)B</td><td class=\"row\d\">(?P<seeds>\d*)</td><td class=\"row\d\">(?P<peers>\d*)</td>")

	def rows(self,terms, numbers):
		url ="http://isohunt.com/torrents/%s?iht=-1&ihp=1&ihs1=1&iho1=d"%(numbers+" "+terms).replace(" ","+")
		print "url",url
		torr = cache.get(url,max_age=60*60).read()
		rows = self.row.finditer(torr)
		#raise Exception, [x.groups() for x in rows][:5]
		return rows

	def torrent(self,r):
		return "http://isohunt.com/download/"+r["path"]

class NyaaTorrents:
#<td class="tlistname"><a href="http://www.nyaa.eu/?page=torrentinfo&amp;tid=294294">[narutoverse]_naruto_shippuden_253.avi</a></td><td class="tlistdownload"><a href="http://www.nyaa.eu/?page=download&amp;tid=294294" title="download" rel="nofollow"><img src="http://files.nyaa.eu/www-dl.png" alt="dl" /></a></td><td class="tlistsize">178.2 mib</td><td class="tlistsn">163</td><td class="tlistln">484</td><td class="tlistdn">4266</td><td class="tlistmn">0</td></tr>
#<td class="tlistname"><a href="http://www.nyaa.eu/?page=torrentinfo&#38;tid=310959">[Narutoverse]_NARUTO_Shippuden_261.avi</a></td><td class="tlistdownload"><a href="http://www.nyaa.eu/?page=download&#38;tid=310959" title="Download" rel="nofollow"><img src="http://files.nyaa.eu/www-dl.png" alt="DL" /></a></td><td class="tlistsize">179.5 MiB</td><td class="tlistfailed" colspan="2">Status unknown</td><td class="tlistdn">17838</td><td class="tlistmn">0</td></tr>
	row = compile("""<td class="tlistname"><a href="http://[^/]+/\?page=torrentinfo&#38;tid=\d+">(?P<name>[^<]+)</a></td>\S*<td class="tlistdownload">.*?<a href="(?P<path>http://[^/]+/\?page=download&#38;tid=\d+)" title="Download"[^>]*><img src="[^\"]+" alt="DL" /></a>.*?</td>\S*<td class="tlistsize">\d+.\d+ (?:G|M)iB</td>(?P<items>.+?)</tr>""", IGNORECASE|DOTALL)
	item = compile("<td class=\"([^\"]+)\"[^>]*>([^<]+)</td>")

	def rows(self,terms,numbers):
		terms = " ".join([x for x in (terms + " " +numbers).split(" ") if len(x)>0 and x[0]!="-"])
		url = "http://www.nyaatorrents.org/?page=search&term=%s&sort=1"%(terms.replace(" ","+"))
		print url
		torr = cache.get(url,max_age=60*60).read()
		torr = torr.replace("<div><!-- --></div>","")
		rows = list(self.row.finditer(torr))
		if rows == []:
			file("dump","wb").write(torr)
			assert rows!=[],rows

		for r in rows:
			items = dict(self.item.findall(r.group('items')))
			if 'tlistsn' in items:
				r['seeds'] = items['tlistsn']
			if 'tlistln' in items:
				r['peers'] = items['tlistln']
		return rows
	
	def torrent(self,r):
		return r["path"].replace("&amp;","&").replace("&#38;", "&")

class EZTV:
	row = compile("class=\"epinfo\">(?P<name>[^<]+)</a>\s+</td>\s+<td align=\"center\" class=\"forum_thread_post\">(?P<allpath>(?:<a href=\"(?P<path>[^\"]+)\" class=\"[^\"]+\" title=\"[^\"]+\"></a>)+)",MULTILINE|DOTALL|UNICODE)

	def rows(self,terms, numbers):
		url = "http://eztv.it/search/"
		torr = cache.get(url, max_age=60*60, data={"SearchString1":terms}).read()

		rows = list(self.row.finditer(torr))
		if rows == []:
			file("dump","wb").write(torr)
			assert rows!=[],rows

		terms = terms.split(" ")
		goodterms = [x.lower() for x in terms if x[0]!="-"]
		badterms = [x[1:].lower() for x in terms if x[0] == "-"]

		print "good", goodterms
		print "bad", badterms

		ret = []
		for nr in rows:
			r = nr.groupdict()
			if r['name'].find("720p") !=-1:
				continue
			for x in goodterms:
				if r['name'].lower().find(x)==-1:
					break
			else:
				for x in badterms:
					if r['name'].lower().find(x)!=-1:
						break
				else:
					print "good name", r['name']
					ret.append(nr)
		return ret

	def torrent(self,r):
		httppat = compile("<a href=\"(http://[^\"]+)")
		ret = httppat.findall(r["allpath"])
		#raise Exception, ret
		return ret

def store_values():
	global db,options
	open(options.database,"wb").write(db.SerializeToString())

def get_series(key):
	global db
	for s in db.series:
		if s.name == key:
			return s
	raise IndexError

def setup(options):
	from episodes_pb2 import All

	db = All()
	db.ParseFromString(open(options.database,"rb").read())
	yesterday = date.fromtimestamp(time())-timedelta(days=1)
	yesterday = yesterday.timetuple()

	cache = Cache(debug=options.debug)
	cache.user_agent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.3) Gecko/20070309 Firefox/2.0.0.3"

	items = {"yesterday":yesterday, "cache":cache, "db": db}
	for x in items:
		globals()[x] = items[x]
	return items

def run(options, parser):
	got = 0
	globals()["options"] = options

	setup(options)

	now = list(localtime())
	for x in range(3,len(now)):
		now[x] = 0
	now = tuple(now)

	if options.series:
		series = []
		for s in db.series:
			if s.name in options.series:
				series.append(s.name)
	else:
		series = [s.name for s in sorted(db.series,key=lambda x:x.last,reverse=True)]
	
	if options.series != []:
		missing = [x for x in options.series if x not in series]
		if len(missing)>0:
			series = sorted([s.name for s in db.series])
			parser.error("Can't find series called: "+(", ".join(missing))+"\nWe have: "+(", ".join(series)))

	if series == []:
		print "Don't have any selected series!"
		series = sorted([s.name for s in db.series])
		print "We have:",(", ".join(series))
		sys.exit(1)
	
	print "Selected series:",(", ".join(sorted(series))),"\n"

	main_sites = [Isohunt(),EZTV()]

	shorttd = timedelta(0,0,0,0,0,6,0)
	longtd = timedelta(7)
	limit = timedelta(21)

	globals()['curr'] = time()

	if vobject:
		calendar = vobject.iCalendar()

	for name in series:
		print "Running: %s"%name
		if options.save:
			if len(series)>1:
				raise Exception
			inf = info(name)
			if options.season!=-1:
				inf["season"] = options.season
			if options.episode!=-1:
				inf["episode"] = options.episode
			update(name,inf["season"],inf["episode"],force=True)
			get_series(name).checked = curr
			store_values()
			#raise Exception,inf

		s = get_series(name)
		(last,checked,command) = s.last,s.checked,s.listing
		if last == None:
			get_series(name).last = curr
			store_values()
			last = curr
		if checked == None:
			get_series(name).checked = curr
			store_values()
			checked = curr

		#print "since",curr-last
		td = timedelta(0,curr-last)
		
		if td>limit:
			mingap = longtd
		else:
			mingap = timedelta()#shorttd
		print "time since last new",td
		gap = timedelta(0,curr-checked)
		if not options.override and gap<mingap:
			print "not enough time has passed. gap is",gap," mingap is",mingap,"\n"
			continue

		print "command '%s'"%command
		if command in ["",None]:
			raise Exception
		next = None
		success = False
		for c in command.split(";"):
			if c.find("(")!=-1:
				args = [x.strip() for x in c[c.find("(")+1:c.rfind(")")].split(",")]
				#print "brk",c[c.find("(")+1:c.find(")")],c.find(")")
				c = c[:c.find("(")]
			else:
				args = []
			print "cmd: '%s' args: "%c,args
			try:
				cmd = getattr(fetch,c)
			except ImportError:
				raise Exception, "can't find command %s"%c
			args = [info(name)]+args
			try:
				next = cmd().run(*args)
			except URLTimeoutError,e:
				print "URL TIMEOUT!",e.url
				continue
			success = True
			if next!=None:
				print "found",next
				#raise Exception
				break

		if success or options.save:
			get_series(name).checked = curr
			store_values()
		if next!=None:
			season = next["season"]
			epnum = next["epnum"]
			date = next["date"]
			title = next["title"]
			if vobject:
				encoder = getdecoder("ascii")
				utc = vobject.icalendar.utc
				event = calendar.add('vevent')
				if "title" in next:
					event.add('summary').value = "%s - %02dx%02d: %s"%(name, season, epnum, encoder(title,'ignore')[0])
				else:
					event.add('summary').value = str("%s - %02dx%02d"%(name, season, epnum))
				event.add('dtstart').value = datetime(date[0],date[1],date[2],tzinfo=utc)
				event.add('dtend').value = datetime(date[0],date[1],date[2],tzinfo=utc)
			delta = None
			if date!=None:
				delta = datetime(date[0],date[1],date[2])-datetime(now[0],now[1],now[2])
				print "delta",delta

			if (date == None or now[:3]<=date[:3]) and not options.fast:
				print "too early",
				if date!=None:
					print now[:3],date[:3],
					if delta<longtd and td>longtd:
						get_series(name).last = curr
						store_values()
				else:
					print "(don't know next date)",
				print "\n"
				continue

			if options.download:
				if next.has_key("url"):
					if not hasattr(locals(),"season"):
						season = 0
					fname = torrent(name,season,epnum)
					if not saferetrieve(next["url"],fname):
						continue
					update(name,season,epnum)
					store_values()
					print ""
					continue
				gotit = False
				try:
					sites = [globals()[x]() for x in get_series(name).search_sites.split(",") if x!=""]
					if sites == []:
						sites = main_sites
					print "sites", sites
				except KeyError:
					raise
				for site in sites:
					try:
						patt = ""
						if season!=0:
							patt += " %d"%season
						if epnum!=0:
							patt +=" %d"%epnum
						rows = site.rows(info(name)["search"]+ " -zip -rar -ita -crimson -raw -psp -ipod",patt)
						print site
						newrows = []
						for nr in rows:
							r = nr.groupdict()
							try:
								r["seeds"] = int(r["seeds"])
							except (KeyError,ValueError):
								r["seeds"] = 0
							try:
								r["peers"] = int(r["peers"])
							except (KeyError,ValueError):
								r["peers"] = 0
							#print "r",r
							newrows.append(r)

						rows = newrows
						#assert(rows!=[])
						rows.sort(lambda x,y:cmp(y["seeds"],x["seeds"]))
							
						for r in rows:
							sp = "<span title=\""
							if r["name"].find(sp)!=-1:
								first = r["name"][r["name"].find(sp)+len(sp):]
								r["name"] = first[:first.find("\"")]
							r["name"] = r["name"].replace("<b>","").replace("</b>","")
							ok = False
							print "row",r["name"]
							if next.has_key("idnum"):
								print "options",options
								globals()["options"] = options
								try:
									ok = next["idnum"](r["name"],name,season,epnum)
								except TypeError:
									ok = globals()[next["idnum"]](r["name"],name,season,epnum)
							else:
								if season == 0: # assume no proper season numbers
									num = compile("[^a-zA-Z](\d+)[^a-zA-Z]").search(r["name"])
								else:
									num = idnum.search(r["name"])
								if num!=None:
									print num.groups()
									try:
										which = [int(x) for x in num.groups() if x!=None]
									except TypeError:
										print r["name"],num.groups()
										raise
									if len(which) == 1:
										which = [0]+which
									if which == [season,epnum]:
										ok = True
									else:
										print "wrong ep, want",(season,epnum),"got",which

									print r,which
									if not ok:
										continue
							if ok:
								fname = torrent(name,season,epnum)
								items = site.torrent(r)
								if type(items)!=ListType:
									items = [items]
								for url in items:
									if saferetrieve(url,fname):
										break
								else:
									continue
								update(name,season,epnum)
								got +=1
								store_values()
								gotit = True
								break
							else:
								print "not an ep",r
								print
								
					except URLTimeoutError:
						print "URLTimeout for",site
						continue
					if gotit:
						break
				else:
					print "can't get %d-%d for %s"%(season,epnum,name)
					raise Exception, "can't get %d-%d for %s"%(season,epnum,name)
		print ""
	if vobject:
		open("episodes.ics","w").write(calendar.serialize())
	return got
	
if __name__ == "__main__":

	parser = OptionParser(description="Episode grabber by Tom Parker <palfrey@tevp.net>")
	parser.add_option("--database",dest="database", type="string", default="watch.list",help="Series database (Default: watch.list)")
	parser.add_option("-n","--series",dest="series",action="append",type="string",default=[])
	parser.add_option("-o","--override",dest="override",action="store_true",help="Override normal date values",default=False)
	parser.add_option("-s","--season",dest="season",type="int",default=-1)
	parser.add_option("-e","--episode",dest="episode",type="int",default=-1)
	parser.add_option("-d","--no-download",dest="download",action="store_false",help="Don't download anything",default=True)
	parser.add_option("-m","--set",dest="save",action="store_true",default=False,help="Store overriden values")
	parser.add_option("-f","--fast",dest="fast",action="store_true",default=False,help="Find now (ignoring dates)")
	parser.add_option("--debug",dest="debug",action="store_true",default=False)

	(options,args) = parser.parse_args()

	if len(args)!=0:
		parser.print_help()
		parser.error("args after main text")

	run(options, parser)

