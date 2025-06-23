# Makefile – convenience tasks

.PHONY: install lint format test precommit

install:
	poetry install --no-root

lint:
	poetry run ruff check .

format:
	poetry run black .

mypy:
	poetry run mypy .

test:
	poetry run pytest -q

precommit:
	poetry run pre-commit run --all-files 