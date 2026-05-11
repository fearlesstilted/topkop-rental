.PHONY: install migrate seed dev check

PYTHON := .venv/bin/python

install:
	python3.12 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

migrate:
	$(PYTHON) -m alembic upgrade head

seed:
	$(PYTHON) -m app.cli seed

dev:
	$(PYTHON) -m uvicorn app.main:app --reload --port 8000

check:
	$(PYTHON) -m ruff check app tests
	$(PYTHON) -m pytest
