# Makefile for pydantic-ai investment research system

.PHONY: help install test test-unit test-integration test-e2e test-cov lint format clean

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -e .
	pip install -r requirements-dev.txt

test:  ## Run all tests
	pytest

test-unit:  ## Run unit tests only
	pytest -m unit

test-integration:  ## Run integration tests only
	pytest -m integration

test-e2e:  ## Run end-to-end tests only
	pytest -m e2e

test-cov:  ## Run tests with coverage report
	pytest --cov=agents --cov=tools --cov=models --cov-report=term-missing --cov-report=html

test-fast:  ## Run fast tests only (exclude slow tests)
	pytest -m "not slow"

test-watch:  ## Run tests in watch mode
	pytest-watch

lint:  ## Run linting (if ruff is available)
	@which ruff > /dev/null && ruff check . || echo "ruff not installed, skipping lint"
	@which mypy > /dev/null && mypy agents tools models || echo "mypy not installed, skipping type check"

format:  ## Format code (if ruff is available)
	@which ruff > /dev/null && ruff format . || echo "ruff not installed, skipping format"
	@which ruff > /dev/null && ruff check --fix . || echo "ruff not installed, skipping fixes"

clean:  ## Clean up generated files
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

setup-dev:  ## Set up development environment
	pip install -e .
	pip install -r requirements-dev.txt
	@which pre-commit > /dev/null && pre-commit install || echo "pre-commit not installed, skipping"

run-example:  ## Run example investment research
	python main.py

run-tests-ci:  ## Run tests suitable for CI
	pytest --cov=agents --cov=tools --cov=models --cov-report=xml --junitxml=pytest.xml

benchmark:  ## Run performance benchmarks
	pytest --benchmark-only

profile:  ## Profile test performance
	pytest --profile

docs:  ## Generate documentation
	@echo "Documentation is in tests/README.md"
	@echo "Architecture docs are in ARCHITECTURE.md"

check-env:  ## Check environment variables
	@echo "Checking environment variables..."
	@python -c "import os; print('OPENROUTER_API_KEY:', 'SET' if os.getenv('OPENROUTER_API_KEY') else 'NOT SET')"
	@python -c "import os; print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
	@python -c "import os; print('SEARXNG_URL:', os.getenv('SEARXNG_URL', 'NOT SET'))"

debug-test:  ## Run tests with debugging
	poetry run pytest -s -vvv --tb=long

test-specific:  ## Run specific test (usage: make test-specific TEST=test_file.py::test_function)
	poetry run pytest $(TEST) -v