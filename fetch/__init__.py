from os import listdir
from os.path import dirname
keep = []
for f in listdir(dirname(__file__)):
	if f[-3:] == ".py" and f[0] != "_":
		s = f[:-3]
		#print s
		locals()[s] = __import__("fetch.%s"%s,globals(),locals(),s)
		keep.append(s)

toremove = ["keep"]
l = None
for l in locals():
	if l[0]!="_" and l!="keep" and l not in keep:
		toremove.append(l)

for r in toremove:
	del locals()[r]
del r
