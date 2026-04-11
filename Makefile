PY_VENV := .venv/
UV_LOCKFILE := uv.lock
BUILD_DIST := dist/

$(UV_LOCKFILE):
	uv lock --build-isolation

$(PY_VENV): $(UV_LOCKFILE)
	uv sync --frozen

$(BUILD_DIST): $(PY_VENV)
	uv build

.PHONY: init
init: $(PY_VENV)
	uv run pre-commit install

.PHONY: clean
clean:
	rm -rf $(PY_VENV)
	find . -type f -name '.DS_Store' | xargs rm -rf
	find . -type d -name '__pycache__' | xargs rm -rf
	rm -rf ./mypy_cache
	rm -rf ./ruff_cache
	rm -rf ./dist

.PHONY: examples
examples:
	uv run python3 -m examples.main

.PHONY: typing
typing:
	uv run mypy -p nice_dialog -p examples -p tests
