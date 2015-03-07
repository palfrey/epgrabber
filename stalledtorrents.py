from os import sep
from robustclient import RobustClient
from episodes_pb2 import All
from datetime import datetime
from epgrabber import idnum, run
from re import compile

db = All()
db.ParseFromString(open("watch.list","rb").read())
series = [(x.name,x.search) for x in db.series]

trans = RobustClient("localhost",6886,"palfrey","epsilon")
torrents = trans.list()
ids = {}
for k in torrents.keys():
	details = trans.info(k)
	for val in details.files():
		f = details.files()[val]['name']

		small = f.lower().encode("ascii", "replace")
		for (name,search) in series:
			if search == "":
				search = name
			bits = search.replace("eztv","").strip().lower().decode("utf-8","replace").split(" ")
			for b in bits:
				if b == "":
					continue
				if b[0] == "-": # an ignore
					continue
				if small.find(b)==-1:
					#print "failed with",b,f
					break
			else:
				found = True
				break
		else:
			continue
		done = details.progress
		
		if done == 100.0:
			break

		delta = datetime.now() - details.date_started
		print delta, f, done, details.eta
		time = (delta.days*24*60*60) + delta.seconds
		if details.eta == None and ((done == 0.0 and time > 60*60) or time > 6*60*60):
			print "Stalled torrent", f
			number = compile("(\d+)").findall(f)
			if number == None:
				print "Can't get id for", name
				continue
			which = [int(x) for x in number if x!=None]
			print which
			if len(which)!=2:
				if len(which)>2:
					for i in range(len(which)-2):
						if which[i]>2000:
							continue
						which = which[i:i+2]
						break
					else:
						continue
			class opt:
				pass

			class FakeParser:
				def error(self, msg):
					print msg
					import sys
					sys.exit(-1)

			options = opt()
			options.database = "watch.list"
			options.debug = True
			options.series = [name]
			options.save = False
			options.override = False
			options.fast = False
			options.season = which[0]
			options.episode = which[1]-1
			options.download = True

			got = run(options, FakeParser())
			if got == 1:
				trans.remove(k)
			continue
		break

