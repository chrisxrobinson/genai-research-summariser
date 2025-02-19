.PHONY: build up down fastapi frontend test db-shell db-backup db-restore db-query db-stats docker-clean docker-image-prune lint fmt check install-backend install-frontend install-all

build:
	# Build all services
	docker-compose build

up:
	# Start all services
	docker-compose up

down:
	# Stop and remove containers
	docker-compose down

fastapi:
	# Run the FastAPI service
	docker-compose run backend

frontend:
	# Run the frontend service
	docker-compose run frontend

test:
	@cd backend && poetry run pytest
	@cd frontend && npm test -- --watchAll=false

docker-clean:
	# Remove unused containers, networks, images and build cache
	docker system prune -f

docker-image-prune:
	# Remove dangling images only
	docker image prune -f

lint: fmt
	# Run all linting checks
	cd backend && poetry run flake8 app tests

fmt:
	# Format all code
	cd backend && poetry run black --line-length 79 app tests
	cd backend && poetry run isort app tests

check:
	# Run all checks
	make lint
	make test

install-backend:
	@cd backend && \
	if [ ! -f poetry.lock ]; then \
		poetry lock && poetry install; \
	else \
		poetry install; \
	fi

install-frontend:
	@cd frontend && npm install

install-all: install-backend install-frontend
	@echo "All dependencies installed successfully"
