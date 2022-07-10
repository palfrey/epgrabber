from google.protobuf import text_format
from sys import argv
from codecs import open

from episodes_pb2 import All

db = All()
db.ParseFromString(open(argv[1], "rb").read())
out = text_format.MessageToString(db)
open(argv[2], "w").write(out)
