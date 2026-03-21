.PHONY: run install test coverage lint migrate downgrade postgres

run:
	uv run uvicorn \
		--app-dir src api:app \
		--port 8000 \
		--reload \
		--reload-dir src \
		--reload-include .env

install:
	uv sync
	uv run pre-commit install

test:
	uv run pytest

coverage:
	uv run pytest --cov --cov-report=html && echo "See htmlcov/index.html"

lint:
	uv run ruff check src
	uv run pyright src

migrate:
	uv run alembic upgrade head

downgrade:
	uv run alembic downgrade -1

postgres:
	docker compose run --service-ports database
