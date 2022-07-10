from os import listdir
from os.path import dirname

keep = []
for f in listdir(dirname(__file__)):
    if f[-3:] == ".py" and f[0] != "_":
        s = f[:-3]
        locals()[s] = getattr(__import__("sites.%s" % s, globals(), locals(), [s]), s)
        keep.append(s)

for l in list(locals()):
    if l[0] != "_" and l != "keep" and l not in keep:
        del locals()[l]

del l
del keep
