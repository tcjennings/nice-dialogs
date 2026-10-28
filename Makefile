PY_VENV := .venv/
UV_LOCKFILE := uv.lock
BUILD_DIST := dist/

# Use uv.lock as it is; only the lockfile target may change it.
export UV_FROZEN := 1

$(UV_LOCKFILE):
	env -u UV_FROZEN uv lock --build-isolation

$(PY_VENV): $(UV_LOCKFILE)
	uv sync

$(BUILD_DIST): $(PY_VENV)
	uv build

.PHONY: init
init: $(PY_VENV)
	uv run prek install -f
	uv run prek prepare-hooks

.PHONY: clean
clean:
	uv run prek cache clean
	rm -rf $(PY_VENV)
	find . -type f -name '.DS_Store' | xargs rm -rf
	find . -type d -name '__pycache__' | xargs rm -rf
	rm -rf ./mypy_cache
	rm -rf ./ruff_cache
	rm -rf ./dist

.PHONY: examples
examples:
	uv run python3 -m examples.main

.PHONY: lint
lint:
	uv run prek run --all-files --show-diff-on-failure --fail-fast

.PHONY: typing
typing:
	uv run mypy -p nice_dialogs -p examples -p tests

.PHONY: release-dry-run
release-dry-run:
	uv run semantic-release --noop version --no-commit --no-changelog

# On a maintenance branch (release/X.Y.x) only patch releases are allowed.
# The tag is made as the git user, so GitHub can verify its signature.
.PHONY: release
release: export GIT_COMMIT_AUTHOR = $(shell git config user.name) <$(shell git config user.email)>
release:
	@branch=$$(git branch --show-current); \
	next=$$(uv run semantic-release --noop version --no-commit --no-changelog --print 2>/dev/null | tail -n 1); \
	case "$$branch" in \
	  release/*) series=$${branch#release/}; series=$${series%.x}; \
	    case "$$next" in "$$series".*) ;; \
	      *) echo "Next version $$next is outside the $$series series of $$branch; cherry-pick only fixes."; exit 1;; \
	    esac;; \
	esac; \
	uv run semantic-release version --no-commit --no-changelog
