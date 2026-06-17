.PHONY: install-dev lint format precommit-install precommit-run

install-dev:
	pip install -r requirements-dev.txt

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

precommit-install:
	pre-commit install

precommit-run:
	pre-commit run --all-files
