all: episodes_pb2.py

episodes_pb2.py: episodes.proto
	protoc --python_out=. episodes.proto

load::
	python loader.py watch.txt watch.list

dump::
	python dumper.py watch.list watch.txt

.PHONY: load dump
