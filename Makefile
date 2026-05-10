.PHONY: install dev test lint format type-check clean build

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short

test-e2e:
	pytest tests/e2e/ -v --tb=short --slow

coverage:
	pytest tests/ --cov=galaxy --cov-report=html --cov-report=term-missing

lint:
	ruff check src/galaxy/ tests/

format:
	ruff format src/galaxy/ tests/

type-check:
	mypy src/galaxy/ --strict

check: lint type-check test

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build:
	python -m build

publish-test:
	twine upload --repository testpypi dist/*
