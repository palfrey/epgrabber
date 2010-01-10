from google.protobuf import text_format
from sys import argv

from episodes_pb2 import All

db = All()
db.ParseFromString(open(argv[1],"rb").read())
print text_format.MessageToString(db)

