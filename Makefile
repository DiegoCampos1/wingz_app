.PHONY: install-dev lint format precommit-install precommit-run test seed

install-dev:
	pip install -r requirements-dev.txt

# Run the test suite inside an ephemeral container (installs dev deps, needs the db service).
# Silk is forced off so its middleware never perturbs the query-count assertions.
test:
	docker compose run --rm -e DJANGO_ENABLE_SILK=0 --entrypoint sh web -c "pip install -q -r requirements-dev.txt && pytest"

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

# Load demo data (idempotent). Use `make seed ARGS="--flush --rides 1000"` to customize.
seed:
	docker compose exec web python manage.py seed_demo $(ARGS)
