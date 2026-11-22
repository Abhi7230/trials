.PHONY: install test lint demo clean

install:
	pip install -e .[dev]

test:
	pytest

lint:
	python -m py_compile src/chunk_bench/*.py src/chunk_bench/chunkers/*.py src/chunk_bench/retrieve/*.py src/chunk_bench/report/*.py

demo:
	python scripts/make_demo.py

clean:
	rm -rf build/ dist/ *.egg-info htmlcov/ .pytest_cache/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
