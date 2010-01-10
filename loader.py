from google.protobuf import text_format
from sys import argv

from episodes_pb2 import All

db = All()
text_format.Merge(open(argv[1],"rb").read(),db)
open(argv[2],"wb").write(db.SerializeToString())

