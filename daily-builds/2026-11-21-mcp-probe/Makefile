.PHONY: install test lint demo clean

install:
	pip install -e .[dev]

test:
	pytest

lint:
	python -m py_compile src/mcp_probe/*.py src/mcp_probe/rules/*.py src/mcp_probe/report/*.py

demo:
	python scripts/make_demo.py

clean:
	rm -rf build/ dist/ *.egg-info htmlcov/ .pytest_cache/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
