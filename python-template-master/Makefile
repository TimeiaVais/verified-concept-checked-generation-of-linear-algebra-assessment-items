-include Makefile.local

.PHONY: bootstrap lint test build clean lock

# The .venv with the dev and test groups, and both git hooks.
bootstrap:
	@poetry sync --with dev --with tests
	@poetry run pre-commit install --config .githooks.yml --hook-type pre-commit --hook-type commit-msg

lint:
	@poetry run pre-commit run --all-files --config .githooks.yml

test:
	@poetry run pytest --cov

# The sdist and the wheel, in dist/.
build:
	@poetry build

# The .venv, build output and tool caches. `make bootstrap` brings the environment back.
clean:
	@rm -rf .venv dist build .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache
	@find . -name __pycache__ -not -path './.git/*' -prune -exec rm -rf {} +

lock:
	@poetry lock
