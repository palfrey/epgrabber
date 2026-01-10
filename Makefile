all: episodes_pb2.py

episodes_pb2.py: episodes.proto
	protoc --python_out=. episodes.proto

load::
	python loader.py watch.txt watch.list

dump::
	python dumper.py watch.list watch.txt

.PHONY: load dump

requirements.txt: requirements.in
	uv pip compile --python-version 3.11 --no-strip-extras requirements.in -o requirements.txt

.venv/bin/activate:
	uv venv --python=3.11

.PHONY: sync
sync: requirements.txt .venv/bin/activate
	uv pip sync requirements.txt

install-pre-commit: sync
	uv run pre-commit install

pre-commit: sync
	uv run pre-commit run -a