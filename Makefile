.SILENT:
.ONESHELL:
.PHONY: \
	setup_uv setup_dev \
	lint autofix check_types test test_cov retest validate \
	clean help
.DEFAULT_GOAL := help

VERBOSE ?=
ifndef VERBOSE
  RUFF_QUIET := --quiet
  PYTEST_QUIET := -q --tb=short --no-header
  PYRIGHT_QUIET := > /dev/null
endif


# MARK: SETUP


setup_uv:  ## Install uv (if missing)
	if command -v uv > /dev/null 2>&1; then
		echo "uv already installed: $$(uv --version)"
	else
		curl --proto '=https' --tlsv1.2 -LsSf https://astral.sh/uv/install.sh | sh
		echo "NOTE: restart your shell or run 'source $$HOME/.local/bin/env'"
	fi

setup_dev: setup_uv  ## uv sync (default groups: dev + test)
	uv sync


# MARK: QUALITY


lint:  ## ruff check
	echo "--- lint"
	uv run ruff check $(RUFF_QUIET) .

autofix:  ## ruff format + ruff check --fix
	uv run ruff format $(RUFF_QUIET) . && uv run ruff check --fix $(RUFF_QUIET) .

check_types:  ## pyright type check
	echo "--- check_types"
	uv run pyright app $(PYRIGHT_QUIET)

test:  ## pytest
	echo "--- test"
	uv run pytest $(PYTEST_QUIET)

test_cov:  ## pytest with coverage (--cov-fail-under=0; raise once tests exist)
	echo "--- test_cov"
	uv run pytest --cov=app --cov-fail-under=0 $(PYTEST_QUIET)

retest:  ## rerun last failed tests only
	uv run pytest --lf -x

validate:  ## CI gate: lint + test_cov (check_types added once existing 22 errors clear)
	set -e
	$(MAKE) -s lint
	$(MAKE) -s test_cov


# MARK: CLEAN


clean:  ## remove caches
	rm -rf .pytest_cache .ruff_cache .pyright_cache .coverage htmlcov
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete


# MARK: HELP


help:  ## show available recipes grouped by section
	echo "Usage: make [recipe] [VERBOSE=1]"
	echo ""
	awk '/^# MARK:/ { \
		section = substr($$0, index($$0, ":")+2); \
		printf "\n\033[1m%s\033[0m\n", section \
	} \
	/^[a-zA-Z0-9_-]+:.*?##/ { \
		helpMessage = match($$0, /## (.*)/); \
		if (helpMessage) { \
			recipe = $$1; \
			sub(/:/, "", recipe); \
			printf "  \033[36m%-14s\033[0m %s\n", recipe, substr($$0, RSTART + 3, RLENGTH) \
		} \
	}' $(MAKEFILE_LIST)
