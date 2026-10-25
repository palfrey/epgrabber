all: episodes_pb2.py

episodes_pb2.py: episodes.proto .tool-versions
	protoc --python_out=. episodes.proto

load::
	python loader.py watch.txt watch.list

dump::
	python dumper.py watch.list watch.txt

.PHONY: load dump

.venv/bin/activate:
	uv venv --python=3.11

.PHONY: sync
sync: uv.lock pyproject.toml .venv/bin/activate
	uv sync

install-pre-commit: sync
	uv run pre-commit install

pre-commit: sync
	uv run pre-commit run -a