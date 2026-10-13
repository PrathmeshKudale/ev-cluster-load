.PHONY: setup up demo results test seed migrate migrate-down migrate-check ingest train simulate down lint

setup:
	python -m pip install -r backend/requirements.txt
	cd frontend && npm install

up:
	docker compose up --build

demo:
	cd frontend && npm run demo

results:
	python scripts/generate_results_md.py

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

train:
	cd backend && python -m app.ml.train

simulate:
	cd backend && python -m app.sim

down:
	docker compose down -v
