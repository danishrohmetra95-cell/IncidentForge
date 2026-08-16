.PHONY: dev dev-db api web migrate seed test test-unit test-e2e clean

dev:
	docker compose up --build

dev-db:
	docker compose up db redis

api:
	uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

migrate:
	cd apps/api && alembic upgrade head

seed:
	cd apps/api && python -m seed

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-e2e:
	pytest tests/end_to_end/ -v

clean:
	docker compose down -v
