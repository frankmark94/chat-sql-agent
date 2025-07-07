.PHONY: install run test clean lint format setup-dev help

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  run        - Run the Streamlit application"
	@echo "  test       - Run all tests"
	@echo "  test-unit  - Run unit tests only"
	@echo "  lint       - Run linting checks"
	@echo "  format     - Format code with black"
	@echo "  setup-dev  - Setup development environment"
	@echo "  clean      - Clean temporary files"
	@echo "  sample-db  - Create sample database"

# Install dependencies
install:
	pip install -r requirements.txt

# Run the application
run:
	streamlit run app/main.py

# Run all tests
test:
	python -m pytest tests/ -v

# Run unit tests only
test-unit:
	python -m pytest tests/unit/ -v

# Run integration tests only
test-integration:
	python -m pytest tests/integration/ -v

# Run linting
lint:
	flake8 src/ app/ tests/
	black --check src/ app/ tests/
	isort --check-only src/ app/ tests/

# Format code
format:
	black src/ app/ tests/
	isort src/ app/ tests/

# Setup development environment
setup-dev:
	pip install -e .
	pip install -r requirements.txt

# Clean temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/

# Create sample database
sample-db:
	python scripts/create_sample_db.py

# Run GitHub webhook server
webhook-server:
	python -m src.github_webhooks

# Security scan
security-scan:
	bandit -r src/ -ll
	safety check