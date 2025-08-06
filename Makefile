# Makefile for IRIS API Integration System
# Provides convenient commands for testing, development, and deployment

.PHONY: help install install-dev test test-unit test-integration test-security test-performance test-all
.PHONY: test-containers test-coverage test-watch lint format security-scan clean docker-test setup-test-env
.PHONY: docs serve-docs build-docs migrate-test migrate-prod start-services stop-services

# Default target
help:
	@echo "IRIS API Integration System - Available Commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install           Install production dependencies"
	@echo "  install-dev       Install development dependencies"
	@echo "  setup-test-env    Setup test environment"
	@echo ""
	@echo "Testing:"
	@echo "  test              Run all tests"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-security     Run security tests only"
	@echo "  test-performance  Run performance tests only"
	@echo "  test-containers   Run tests with real containers"
	@echo "  test-coverage     Run tests with coverage report"
	@echo "  test-watch        Run tests in watch mode"
	@echo "  test-parallel     Run tests in parallel"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint              Run all linters"
	@echo "  format            Format code with black and isort"
	@echo "  security-scan     Run security scans"
	@echo "  type-check        Run mypy type checking"
	@echo ""
	@echo "Services:"
	@echo "  start-services    Start test services (Docker Compose)"
	@echo "  stop-services     Stop test services"
	@echo "  docker-test       Run tests in Docker"
	@echo ""
	@echo "Database:"
	@echo "  migrate-test      Run database migrations for test"
	@echo "  migrate-prod      Run database migrations for production"
	@echo ""
	@echo "Documentation:"
	@echo "  docs              Build documentation"
	@echo "  serve-docs        Serve documentation locally"
	@echo ""
	@echo "Utilities:"
	@echo "  clean             Clean build artifacts and cache"
	@echo "  clean-containers  Clean Docker containers and volumes"

# ==================== Installation ====================

install:
	@echo "Installing production dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "Installing development dependencies..."
	pip install -e ".[test,dev,security,performance]"

setup-test-env:
	@echo "Setting up test environment..."
	cp .env.example .env.test || echo "No .env.example found"
	docker-compose -f docker-compose.test.yml pull
	@echo "Test environment setup complete"

# ==================== Testing ====================

test:
	@echo "Running all tests..."
	pytest -v

test-unit:
	@echo "Running unit tests..."
	pytest -v -m "unit and not slow"

test-integration:
	@echo "Running integration tests..."
	pytest -v -m "integration and not slow"

test-security:
	@echo "Running security tests..."
	pytest -v -m "security"

test-performance:
	@echo "Running performance tests..."
	pytest -v -m "performance" --benchmark-only

test-containers:
	@echo "Running tests with containers..."
	docker-compose -f docker-compose.test.yml up -d
	sleep 10  # Wait for services to be ready
	pytest -v -m "requires_containers" || true
	docker-compose -f docker-compose.test.yml down

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80

test-watch:
	@echo "Running tests in watch mode..."
	pytest-watch -- -v

test-parallel:
	@echo "Running tests in parallel..."
	pytest -v -n auto

test-all:
	@echo "Running comprehensive test suite..."
	pytest -v --cov=app --cov-report=html --cov-report=term-missing

# ==================== Code Quality ====================

lint:
	@echo "Running linters..."
	flake8 app/
	ruff check app/
	bandit -r app/ -x app/tests/

format:
	@echo "Formatting code..."
	black app/
	isort app/

type-check:
	@echo "Running type checks..."
	mypy app/

security-scan:
	@echo "Running security scans..."
	bandit -r app/ -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true
	@echo "Security scan complete. Check bandit-report.json and safety-report.json"

# ==================== Services ====================

start-services:
	@echo "Starting test services..."
	docker-compose -f docker-compose.test.yml up -d
	@echo "Waiting for services to be ready..."
	sleep 15
	@echo "Services started. Check logs with: docker-compose -f docker-compose.test.yml logs"

stop-services:
	@echo "Stopping test services..."
	docker-compose -f docker-compose.test.yml down

docker-test:
	@echo "Running tests in Docker..."
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit test-runner

# ==================== Database ====================

migrate-test:
	@echo "Running test database migrations..."
	export ENVIRONMENT=test && alembic upgrade head

migrate-prod:
	@echo "Running production database migrations..."
	export ENVIRONMENT=production && alembic upgrade head

seed-test-data:
	@echo "Seeding test data..."
	docker-compose -f docker-compose.test.yml up --profile seeder test-data-seeder

# ==================== Documentation ====================

docs:
	@echo "Building documentation..."
	mkdocs build

serve-docs:
	@echo "Serving documentation locally..."
	mkdocs serve

build-docs:
	@echo "Building documentation for deployment..."
	mkdocs build --clean

# ==================== Utilities ====================

clean:
	@echo "Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/
	rm -rf coverage.xml coverage.json bandit-report.json safety-report.json

clean-containers:
	@echo "Cleaning Docker containers and volumes..."
	docker-compose -f docker-compose.test.yml down -v --remove-orphans
	docker system prune -f

# ==================== Advanced Testing Scenarios ====================

test-smoke:
	@echo "Running smoke tests..."
	pytest -v -m "smoke" --tb=short

test-regression:
	@echo "Running regression tests..."
	pytest -v -m "regression"

test-e2e:
	@echo "Running end-to-end tests..."
	pytest -v -m "e2e" --tb=short

test-load:
	@echo "Running load tests..."
	docker-compose -f docker-compose.test.yml up --profile load-testing -d
	sleep 10
	locust -f app/tests/load_tests.py --headless -u 10 -r 2 -t 30s --host http://localhost:8080
	docker-compose -f docker-compose.test.yml down --profile load-testing

test-memory:
	@echo "Running memory profiling tests..."
	pytest -v -m "performance" --memory-profile

# ==================== CI/CD Helpers ====================

ci-install:
	@echo "Installing dependencies for CI..."
	pip install --upgrade pip
	pip install -e ".[test,dev]"

ci-test:
	@echo "Running CI test suite..."
	pytest -v --junitxml=test-results.xml --cov=app --cov-report=xml --cov-report=term

ci-lint:
	@echo "Running CI linting..."
	flake8 app/ --format=junit-xml --output-file=flake8-results.xml || true
	black --check app/
	isort --check-only app/

ci-security:
	@echo "Running CI security checks..."
	bandit -r app/ -f json -o bandit-results.json || true
	safety check --json --output safety-results.json || true

# ==================== Development Helpers ====================

dev-setup:
	@echo "Setting up development environment..."
	make install-dev
	make setup-test-env
	pre-commit install
	@echo "Development environment ready!"

dev-test:
	@echo "Running development test cycle..."
	make format
	make lint
	make test-unit
	@echo "Development test cycle complete!"

quick-test:
	@echo "Running quick tests (unit only, no slow tests)..."
	pytest -v -m "unit and not slow" --tb=short

# ==================== Monitoring and Observability ====================

test-with-monitoring:
	@echo "Running tests with monitoring..."
	docker-compose -f docker-compose.test.yml up --profile observability -d
	sleep 15
	pytest -v --tb=short
	@echo "View traces at: http://localhost:16686"
	docker-compose -f docker-compose.test.yml down --profile observability

# ==================== Performance Benchmarking ====================

benchmark:
	@echo "Running performance benchmarks..."
	pytest -v -m "performance" --benchmark-json=benchmark-results.json

benchmark-compare:
	@echo "Comparing benchmarks..."
	pytest -v -m "performance" --benchmark-compare --benchmark-compare-fail=min:5%

# ==================== Environment Variables ====================

# Export test environment variables
export ENVIRONMENT=test
export DEBUG=true
export DATABASE_URL=postgresql://test_user:test_password@localhost:5433/test_iris_db
export REDIS_URL=redis://localhost:6380/0
export SECRET_KEY=test_secret_key_32_characters_long
export ENCRYPTION_KEY=test_encryption_key_32_chars_long