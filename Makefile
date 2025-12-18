.PHONY: help build up down logs shell clean test

help:
	@echo "E-Ink Art Gallery - Development Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make build       - Build Docker image"
	@echo "  make up          - Start containers with Docker Compose"
	@echo "  make down        - Stop containers"
	@echo "  make logs        - View container logs"
	@echo "  make shell       - Open shell in running container"
	@echo "  make clean       - Remove containers, volumes, and build artifacts"
	@echo "  make dev         - Setup local development environment"
	@echo "  make run-local   - Run application locally (requires dependencies installed)"
	@echo ""

build:
	docker build -t eink-art-gallery .

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec eink-art-gallery /bin/bash

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/

dev:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	mkdir -p /data/eink_art/images

run-local:
	@if [ -d "venv" ]; then \
		. venv/bin/activate; \
	fi
	mkdir -p /data/eink_art/images
	export PYTHONUNBUFFERED=1 && python3 app/app.py

restart: down up

ps:
	docker-compose ps
