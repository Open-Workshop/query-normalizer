.PHONY: install install-dev test test-cov lint format typecheck check clean run-server build help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "Available targets:"
	@echo "  install        - Install base dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo "  test           - Run tests"
	@echo "  test-cov       - Run tests with coverage"
	@echo "  lint           - Run ruff linter"
	@echo "  format         - Format code with ruff"
	@echo "  typecheck      - Run mypy type checker"
	@echo "  check          - Run all checks (lint, format, typecheck)"
	@echo "  clean          - Remove temporary files"
	@echo "  run-server     - Run FastAPI server"
	@echo "  build          - Build distribution packages"
	@echo "  help           - Show this help message"

install:
	$(PIP) install -e .
	@echo "Dependencies installed successfully!"

install-dev:
	$(PIP) install -e ".[dev,server]"
	@echo "Development dependencies installed successfully!"

test:
	$(PYTHON) -m pytest tests/ -v

test-cov:
	$(PYTHON) -m pytest tests/ --cov=query_normalizer --cov-report=term-missing

lint:
	$(PYTHON) -m ruff check . || (echo "Error: Ruff not found. Run 'make install-dev' first." && exit 1)

format:
	$(PYTHON) -m ruff format . || (echo "Error: Ruff not found. Run 'make install-dev' first." && exit 1)

typecheck:
	$(PYTHON) -m mypy query_normalizer/ || (echo "Error: MyPy not found. Run 'make install-dev' first." && exit 1)

check: lint format typecheck

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Clean completed successfully!"

run-server:
	$(PYTHON) -m uvicorn query_normalizer.server:app --reload --host 0.0.0.0 --port 8000

build:
	$(PYTHON) -m build || (echo "Error: Build tool not found. Run 'pip install build' first." && exit 1)