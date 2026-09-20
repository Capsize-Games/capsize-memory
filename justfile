set shell := ["bash", "-euo", "pipefail", "-c"]

default: ci

setup:
    uv sync --all-extras

build:
    uv build

test:
    uv run pytest

lint:
    uv run ruff check .

format:
    uv run ruff format .

typecheck:
    uv run mypy src

run:
    @echo "capsize-memory is a library; run it through a host service."

clean:
    find src tests -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
    rm -rf dist build

docs:
    @echo "See README.md for the host integration contract."

ci: lint typecheck test build
