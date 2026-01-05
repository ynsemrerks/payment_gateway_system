.PHONY: help up down build migrate test lint logs shell clean seed

help:
	@echo "Available commands:"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make build      - Build Docker images"
	@echo "  make migrate    - Run database migrations"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters (black, isort, ruff)"
	@echo "  make logs       - Show logs from all services"
	@echo "  make shell      - Access application shell"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make seed       - Seed database with test data"

up:
	docker compose up -d
	@echo "Services started. API: http://localhost:8000, Flower: http://localhost:5555"

down:
	docker-compose down

build:
	docker compose build

migrate:
	docker compose exec api alembic upgrade head

test:
	docker compose exec api pytest -v --cov=app --cov-report=term-missing

lint:
	docker-compose exec api black app tests
	docker-compose exec api isort app tests
	docker-compose exec api ruff check app tests

logs:
	docker-compose logs -f

shell:
	docker-compose exec api /bin/bash

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

seed:
	docker compose exec api python -m app.scripts.seed_data
