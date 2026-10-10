.PHONY: test seed migrate up down lint

test:
	cd backend && python -m pytest -q

seed:
	cd backend && python -m app.db.seed

migrate:
	cd backend && alembic upgrade head

up:
	docker compose up --build

down:
	docker compose down -v
