.DEFAULT_GOAL := install
black = black -S -l 120 --target-version py38

.PHONY: install
install:
	pip install -r requirements.txt
	pip install -r test_requirements.txt

.PHONY: format
format:
	isort SalsaVerde
	$(black) SalsaVerde

.PHONY: lint
lint:
	flake8 SalsaVerde
	isort --check-only SalsaVerde
	$(black) --check SalsaVerde

.PHONY: test
test:
	pytest SalsaVerde --cov=SalsaVerde

.PHONY: reset-db
reset-db:
	psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS salsaverde"
	psql -h localhost -U postgres -c "CREATE DATABASE salsaverde"
