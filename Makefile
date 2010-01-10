all: episodes_pb2.py

episodes_pb2.py:
	protoc --python_out=. episodes.proto
