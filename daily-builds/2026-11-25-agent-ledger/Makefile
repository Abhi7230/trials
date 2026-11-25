.PHONY: install test coverage demo serve check clean

install:
	pip install -e .[dev]

test:
	pytest

coverage:
	pytest --cov=agent_ledger --cov-report=html --cov-report=term --cov-fail-under=85

demo:
	python scripts/make_demo.py

serve:
	agent-ledger serve

check:
	agent-ledger check --db ledger.db

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov *.db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
