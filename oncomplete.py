from os import listdir,popen,system,rmdir,remove,walk
from os.path import isfile,join,dirname, splitext,basename
from shutil import move

from episodes_pb2 import All

from optparse import OptionParser
import transmissionrpc

parser = OptionParser()
parser.add_option("-w","--write",help="Actually do the actions!", action="store_true",default=False,dest="execute")
parser.add_option("-i","--ignore-torrent",help="Do action irregardless of torrent existing",action="store_false",default=True,dest="check_torrent")
parser.add_option("-c","--check-dir",default=".",type="string",dest="check_dir",help="Directory to check")
parser.add_option("-d","--dest-dir",default="output",type="string",dest="dest_dir",help="Directory to move files to")
(opts,args) = parser.parse_args()

db = All()
db.ParseFromString(open("watch.list","rb").read())
series = [(x.name,x.search) for x in db.series]

if opts.check_torrent:
	trans = transmissionrpc.Client("localhost",6886,"palfrey","epsilon")
	torrents = trans.list()
	ids = {}
	for k in torrents.keys():
		ids[trans.info(k)[k].files()[0]['name']] = k

def remove_dir(top):
	print "remove dir",top
	return
	for root,dirs,files in walk(top, topdown=False):
		for name in files:
			remove(join(root,name))
		for name in dirs:
			rmdir(join(root,name))
	rmdir(top)

if len(args) == 0:
	files = sorted(listdir(opts.check_dir))
	docheck = True
else:
	files = args
	docheck = False

for f in files:
	found = False
	if docheck:
		small = f.lower().decode("utf-8")
		for (name,search) in series:
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
		found = True
		name = ""
	if found:
		print "Found for %s - %s"%(name,f.decode("utf-8"))
		if opts.check_torrent:
			if f in ids:
				print "torrent id", ids[f]
				details = trans.info(ids[f])[ids[f]]
				done = details.progress
				if done == 100.0:
					if opts.execute:
						trans.remove(ids[f])
					f = join(opts.check_dir,f)
				else:
					print "Only %.2f%% complete"%done
					continue
			else:
				continue
		if not isfile(f):
			for nf in listdir(f):
				ext = splitext(nf)[1].lower()
				if ext not in (".avi",):
					print "not",nf
					continue
				found = False
				if docheck:
					small = nf.lower().decode("utf-8")
					for b in bits:
						if b[0] == "-": # an ignore
							continue
						if small.find(b)==-1:
							print "failed with",b,nf
							break
					else:
						found = True
						break
				else:
					found = True
					break
			if found:
				f = join(f,nf)
				print f
		data = popen("~/bin/renamer '%s'"%f).readlines()
		if len(data) == 1:
			destname = basename("".join(data).split("=>")[1].strip()[1:-1])
		else:
			destname = basename(f)
			assert len(data)==0,data
		dest = join(opts.dest_dir,destname)
		if opts.execute:
			move(f, dest)
			if "/" in f[opts.check_dir:]:
				remove_dir(dirname(f))
		else:
			print "Would have moved %s to %s"%(f, dest)

