.PHONY: test seed migrate migrate-down migrate-check ingest up down lint

test:
	cd backend && python -m pytest -q

seed:
	cd backend && python -m app.db.seed

migrate:
	cd backend && alembic upgrade head

migrate-down:
	cd backend && alembic downgrade base

migrate-check:
	cd backend && alembic check

ingest:
	cd backend && python -m app.ml.data.ingest

up:
	docker compose up --build

down:
	docker compose down -v
