.PHONY: test lint format-check gates

test:
	uv run pytest

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

gates: lint format-check test
