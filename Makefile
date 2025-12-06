.PHONY: help install migrate run test lint format worker docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make migrate     - Run database migrations"
	@echo "  make run         - Run Django development server"
	@echo "  make worker      - Run Celery worker"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code with black"
	@echo "  make docker-up   - Start all services with docker-compose"
	@echo "  make docker-down - Stop all services"

install:
	poetry install

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

run:
	python manage.py runserver

worker:
	celery -A config worker --loglevel=info

test:
	pytest

lint:
	flake8 .
	mypy .

format:
	black .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

shell:
	python manage.py shell

superuser:
	python manage.py createsuperuser

