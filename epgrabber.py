#!/usr/bin/python

import sys
try:
	from urlgrab.GetURL import GetURL
	from urlgrab.URLTimeout import URLTimeoutError
except:
	print "You need to install urlgrab. Get it using 'git clone git://github.com/palfrey/urlgrab.git urlgrab'"
	sys.exit(1)
from re import compile,IGNORECASE,MULTILINE,DOTALL,split
from time import strptime,strftime,localtime,time
from os.path import exists,getsize,basename,join
from os import remove
from urlparse import urljoin
from datetime import datetime, timedelta,date
from optparse import OptionParser
import vobject
from shutil import move
from BitTorrent.bencode import bdecode

import fetch

import urllib
class AppURLopener(urllib.FancyURLopener):
    version = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11"

urllib._urlopener = AppURLopener()

options = None
cur = None
con = None
cache = None

def saferetrieve(url,fname):
	try:
		print "Trying",url
		tmpname = join("/tmp",basename(fname))
		urllib.urlretrieve(url,tmpname)
		if exists(tmpname) and getsize(tmpname)>1000:
			print "Retrieved!",url
			bd = bdecode(open(tmpname).read())['info']

			try:
				length = bd['length']
				if length in ([364904448,183500806,183500808,183656487]+list(range(367001600,367001600+50))):
					print "Bad torrent!"
					return False
			except KeyError:
				assert "files" in bd,bd.keys()
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

def geass(inf):
	ret = wikipedia(inf,"List_of_Code_Geass_episodes")
	if ret!=None:
		ret["idnum"] = animeep
	return ret

def multisplit(text,items):
	out = [text]
	while len(items)>0:
		for x in out:
			sp = x.split(items[0])
			if len(sp)>1:
				out.remove(x)
				out.extend(sp)
		items = items[1:]
	print "out",out,text
	return out

def animeep(title,name,season,epnum):
	bits = [x.strip() for x in multisplit(title,[" ","."]) if x!="" and x!="-"]
	print "bits",bits
	num = -1
	for x in bits:
		if x[0] == "[":
			continue
		if x.find("-")!=-1:
			nums = x.split("-")
			try:
				while len(nums)>1:
					val = int(nums[0])
					if val>season:
						update(name,int(nums[0]),epnum,force=True)
						print "updating with",val
					nums = nums[1:]
				x = nums[0]
				if int(nums[0])>season:
					season = int(nums[0])
			except ValueError:
				continue
		try:
			num = int(x)
		except ValueError:
			continue
	
	print "num",num
	return num == season

def info(name):
	global cache,yesterday,cur,options
	#print "options",options
	keys = ["name","search","season","episode","last","checked"]
	cur.execute("select %s from series where name=\"%s\""%(",".join(keys),name))
	ret = {}
	data = cur.fetchone()
	for k in range(len(keys)):
		if hasattr(options,keys[k]) and getattr(options,keys[k])!=-1:
			ret[keys[k]] = getattr(options,keys[k])
		else:
			ret[keys[k]] = data[k]
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
		cur.execute("update series set season=%d, episode=%d, last=%d where name=\"%s\""%(season,epnum,curr,name))
		con.commit()
		if cur.rowcount!=1:
			cur.execute("select name,search,season,episode,last from series where name=\"%s\""%ep)
			print cur.fetchall()
			raise Exception
	return fname
		
class Isohunt:
	#row = compile("<tr class=\"hlRow\" onClick=\"servOC\(\d+,\\'/torrent_details/(?P<path>[^']+)'.*?<td class=\"row3\" id=name\d+>(?P<name>.*?)(?=</td>)</td><td class=\"row3\" title='\d+ file(?:s)?'>\d+.\d+ (?:M|G|K)B</td><td class=\"row1\">(?P<seeds>\d*)</td><td class=\"row3\">(?P<peers>\d*)</td>")
	row = compile("<a onClick=\"servOC\(\d+,\\'/torrent_details/(?P<path>[^']+)'.*?<td class=\"row3\" id=name\d+>.+?tab=summary'>(?P<name>.*?)(?=</td>)</td><td class=\"row3\" title='\d+ file(?:s)?'>\d+.\d+ (?:M|G|K)B</td><td class=\"row1\">(?P<seeds>\d*)</td><td class=\"row3\">(?P<peers>\d*)</td>")

	def rows(self,terms, numbers):
		url ="http://isohunt.com/torrents/%s?ihp=1&iht=-1&ihs1=2&iho1=d"%terms.replace(" ","+")
		print "url",url
		torr = cache.get(url,max_age=60*60).read()
		rows = self.row.finditer(torr)
		return rows

	def torrent(self,r):
		return "http://isohunt.com/download/"+r["path"]

class PirateBay:
	row = compile("<a href=\"[^\"]+\" class=\"detLink\" title=\"[^\"]+\">(?P<name>[^<]+)</a>.*?(?P<path>http://torrents.thepiratebay.org/\d+/[^\"]+)\" title=\"Download this torrent\">.*?<td align=\"right\">\d+\.\d+&nbsp;(?:G|M|K)iB</td>.*?<td align=\"right\">(?P<seeds>\d+)</td>.*?<td align=\"right\">(?P<peers>\d+)</td>",MULTILINE|DOTALL)

	def rows(self,terms,numbers):
		url = "http://thepiratebay.org/search/%s/0/7/0"%(terms+numbers).replace(" ","+")
		print "url",url
		torr = cache.get(url,max_age=60*60).read()
		rows = self.row.finditer(torr)
		return rows

	def torrent(self,r):
		return r["path"]

def setup(options):
	try:
		from pysqlite2 import dbapi2 as sqlite
	except ImportError,e:
		print e
		import sqlite

	con = sqlite.connect(options.database)
	cur = con.cursor()

	yesterday = date.fromtimestamp(time())-timedelta(days=1)
	yesterday = yesterday.timetuple()

	cache = GetURL(debug=options.debug)
	cache.user_agent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.3) Gecko/20070309 Firefox/2.0.0.3"

	items = {"cur": cur, "yesterday":yesterday, "cache":cache, "con":con}
	for x in items:
		globals()[x] = items[x]
	return items
	
if __name__ == "__main__":
	idnum = compile("(?:S(\d+)E(\d+))|(?:\[(\d+)x(\d+)\])|(?: (\d)(\d{2}) - )|(?: (\d+)X(\d+) )|(?:\.(\d+)(\d{2}).)|(?: (\d{2}))",IGNORECASE)

	now = list(localtime())
	for x in range(3,len(now)):
		now[x] = 0
	now = tuple(now)

	parser = OptionParser(description="Episode grabber by Tom Parker <palfrey@tevp.net>")
	parser.add_option("--database",dest="database", type="string", default="watch.db",help="Series database (Default: watch.db)")
	parser.add_option("-n","--series",dest="series",action="append",type="string",default=[])
	parser.add_option("-o","--override",dest="override",action="store_true",help="Override normal date values",default=False)
	parser.add_option("-s","--season",dest="season",type="int",default=-1)
	parser.add_option("-e","--episode",dest="episode",type="int",default=-1)
	parser.add_option("-d","--no-download",dest="download",action="store_false",help="Don't download anything",default=True)
	parser.add_option("-m","--set",dest="save",action="store_true",default=False,help="Store overriden values")
	parser.add_option("-f","--fast",dest="fast",action="store_true",default=False,help="Find now (ignoring dates)")
	parser.add_option("--debug",dest="debug",action="store_true",default=False)

	(options,args) = parser.parse_args()

	globals()["options"] =  options
	if len(args)!=0:
		parser.print_help()
		parser.error("args after main text")

	setup(options)

	cur.execute("select name from sqlite_master where type='table' and name='series'")
	if len(cur.fetchall())==0:
		cur.execute("create table series (name varchar(30) primary key,search varchar(100),season integer, episode integer, last datetime, command varchar(100), checked datetime);")
		con.commit()
	if options.series:
		query = "select name from series where name='"+("' or name='".join(options.series))+"'"
		cur.execute(query)
	else:
		cur.execute("select name from series order by last desc")
	
	series = [x[0] for x in cur.fetchall()]
	if options.series != []:
		missing = [x for x in options.series if x not in series]
		if len(missing)>0:
			cur.execute("select name from series order by name")
			series = [x[0] for x in cur.fetchall()]
			parser.error("Can't find series called: "+(", ".join(missing))+"\nWe have: "+(", ".join(series)))

	if series == []:
		print "Don't have any selected series!"
		cur.execute("select name from series order by name")
		series = [x[0] for x in cur.fetchall()]
		print "We have:",(", ".join(series))
		sys.exit(1)
	
	print "Selected series:",(", ".join(series)),"\n"

	sites = [Isohunt(),PirateBay()]

	shorttd = timedelta(0,0,0,0,0,6,0)
	longtd = timedelta(7)
	limit = timedelta(21)

	curr = time()

	calendar = vobject.iCalendar()

	for name in series:
		print name
		if options.save:
			if len(series)>1:
				raise Exception
			inf = info(name)
			if options.season!=-1:
				inf["season"] = options.season
			if options.episode!=-1:
				inf["episode"] = options.episode
			update(name,inf["season"],inf["episode"],force=True)
			cur.execute("update series set checked=? where name=?",(curr,name))
			con.commit()
			#raise Exception,inf

		cur.execute("select last,checked,command from series where name=?",(name,))
		((last,checked,command),) = cur.fetchall()
		if last == None:
			cur.execute("update series set last=? where name=?",(curr,name))
			con.commit()
			last = curr
		if checked == None:
			cur.execute("update series set checked=? where name=?",(curr,name))
			con.commit()
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
			cur.execute("update series set checked=? where name=?",(curr,name))
			con.commit()
		if next!=None:
			for x in ["season","epnum","date", "title"]:
				if x in next:
					locals()[x] = next[x]
			utc = vobject.icalendar.utc
			event = calendar.add('vevent')
			if "title" in next:
				event.add('summary').value = str("%s - %02dx%02d: %s"%(name, season, epnum, title))
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
						cur.execute("update series set last=? where name=?",(curr,name))
						con.commit()
				else:
					print "(don't know next date)",
				print "\n"
				continue

			if options.download:
				if next.has_key("url"):
					fname = torrent(name,season,epnum)
					if not saferetrieve(next["url"],fname):
						continue
					update(name,season,epnum)
					con.commit()
					print ""
					continue
				gotit = False
				for site in sites:
					try:
						patt = ""
						if season!=0:
							patt += " %d"%season
						if epnum!=0:
							patt +=" %d"%epnum
						rows = site.rows(info(name)["search"]+ " -zip -rar -ita -crimson -raw -mkv -psp -wmv -ipod",patt)
						print site
						newrows = []
						for nr in rows:
							r = nr.groupdict()
							#print "r",r
							try:
								r["seeds"] = int(r["seeds"])
							except ValueError:
								r["seeds"] = 0
							try:
								r["peers"] = int(r["peers"])
							except ValueError:
								r["peers"] = 0
							newrows.append(r)

						rows = newrows
						#assert(rows!=[])
						rows.sort(lambda x,y:cmp(y["seeds"],x["seeds"]))
							
						for r in rows:
							sp = "<span title=\""
							if r["name"].find(sp)!=-1:
								r["name"] = r["name"][r["name"].find(sp)+len(sp):r["name"][len(sp)+1:].find("\"")+len(sp)+1]
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
							if ok:
								fname = torrent(name,season,epnum)
								if not saferetrieve(site.torrent(r),fname):
									continue
								update(name,season,epnum)
								con.commit()
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
		print ""
	open("episodes.ics","w").write(calendar.serialize())
