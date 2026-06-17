.PHONY: install-dev lint format precommit-install precommit-run test

install-dev:
	pip install -r requirements-dev.txt

# Run the test suite inside an ephemeral container (installs dev deps, needs the db service).
test:
	docker compose run --rm --entrypoint sh web -c "pip install -q -r requirements-dev.txt && pytest"

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
