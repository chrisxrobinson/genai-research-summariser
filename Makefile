.PHONY: build up down fastapi frontend test db-shell db-backup db-restore db-query db-stats docker-clean docker-image-prune lint fmt check fix install-backend install-frontend install-all local-init logs restart-localstack clean-all

build:
	# Build all services
	docker-compose build

up:
	# Start all services
	docker-compose up -d

down:
	# Stop and remove containers
	docker-compose down

logs:
	# View logs from all containers
	docker-compose logs -f

local-init:
	# Initialize local development environment
	chmod +x ./init-localstack.sh
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Local environment is ready!"

restart-localstack:
	# Restart LocalStack container
	docker-compose rm -sf localstack
	docker-compose up -d localstack
	@echo "Waiting for LocalStack to initialize..."
	@sleep 10
	@echo "LocalStack restarted"

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

fix: fix-lint fmt
	# Fix all code style issues
	cd backend && poetry run autoflake --in-place --remove-all-unused-imports --recursive app tests
	cd backend && poetry run black --line-length 79 app tests
	cd backend && poetry run isort app tests

fix-lint:
	# Fix specific flake8 issues
	cd backend && find app -type f -name "*.py" -exec sed -i '' -e 's/[[:space:]]*$$//' {} \;
	cd backend && find app -type f -name "*.py" -exec sed -i '' -e '/^[[:space:]]*$$/d' {} \;
	cd backend && find app -type f -name "*.py" -exec sed -i '' -e 's/except:/except Exception:/' {} \;

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

setup: install-all build local-init
	@echo "Project setup complete!"

clean-all: down
	# Stop containers and remove volumes, networks, etc.
	docker-compose down -v
	@echo "Removing any leftover localstack volumes..."
	-docker volume ls -q | grep localstack | xargs docker volume rm 2>/dev/null || true
	@docker container ls -a | grep localstack | awk '{print $$1}' | xargs docker container rm -f 2>/dev/null || true
	@echo "Environment cleanup complete!"
