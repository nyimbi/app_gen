# Makefile for Python project management

.PHONY: setup test lint format clean docs migrate

# Installation and setup
setup:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

venv:
	python -m venv venv
	@echo "Run 'source venv/bin/activate' to activate the virtual environment"

# Testing
test:
	pytest tests/ --cov=app

test-verbose:
	pytest tests/ -v --cov=app --cov-report=term-missing

# Code quality
lint:
	flake8 app/ tests/
	mypy app/ tests/

format:
	isort app/ tests/
	black app/ tests/

# Cleaning
clean:
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info __pycache__ *.pyc
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Documentation
docs:
	mkdocs build

docs-serve:
	mkdocs serve

# Database
migrate:
	flask db migrate -m "Auto-generated migration"

upgrade:
	flask db upgrade

# Docker
docker-build:
	docker build -t $(project_name) .

docker-run:
	docker run -p 5000:5000 $(project_name)

# Default target
all: format lint test
