# Variables
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
BLACK := $(VENV)/bin/black
FLAKE8 := $(VENV)/bin/flake8
MYPY := $(VENV)/bin/mypy
PACKAGE := macro_hunter

.PHONY: all venv clean install dev-install test lint format type-check coverage docs

# Default target
all: install test lint

# Create virtual environment
venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

# Clean up generated files and cache
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Install base requirements
install: venv
	$(PIP) install -r requirements/base.txt
	$(PIP) install -e .

# Install development requirements
dev-install: venv
	$(PIP) install -r requirements/dev.txt
	$(PIP) install -r requirements/test.txt
	$(PIP) install -e .

# Run tests
test:
	$(PYTEST) tests/ -v --cov=$(PACKAGE)

# Run linting
lint:
	$(FLAKE8) $(PACKAGE)
	$(BLACK) --check $(PACKAGE)

# Format code
format:
	$(BLACK) $(PACKAGE)

# Type checking
type-check:
	$(MYPY) $(PACKAGE)

# Generate coverage report
coverage:
	$(PYTEST) tests/ -v --cov=$(PACKAGE) --cov-report=html

# Build documentation
docs:
	cd docs && make html
