.DEFAULT_GOAL := install

.PHONY: install
install:
	pip install -r requirements.txt
	pip install -r test_requirements.txt

.PHONY: format
format:
	ruff check --fix .
	ruff format .

.PHONY: lint
lint:
	ruff check .
	ruff format --check .

.PHONY: test
test:
	pytest SalsaVerde --cov=SalsaVerde

.PHONY: reset-db
reset-db:
	psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS salsaverde"
	psql -h localhost -U postgres -c "CREATE DATABASE salsaverde"
