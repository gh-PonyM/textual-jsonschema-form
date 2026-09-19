# Migration Plan: Poetry to uv

## Context

- **uv version**: 0.12.17
- **Default build backend**: `uv_build` (not hatchling)
- **Default layout**: `src/<package_name>/` (src-layout)
- **Current project layout**: flat (`textual_jsonschema_form/` at root)

## Key Decision: Layout

Two options:

### Option A: Move to src-layout (uv default)
Move `textual_jsonschema_form/` to `src/textual_jsonschema_form/` and keep default `uv_build` config.
- Pro: Aligns with uv conventions, zero build-backend config needed
- Con: Changes import paths in tests/examples, more files to update

### Option B: Keep flat layout, configure uv_build
Keep `textual_jsonschema_form/` at root, configure:
```toml
[tool.uv.build-backend]
module-root = ""
module-name = "textual_jsonschema_form"
```
- Pro: Minimal file moves, less risk
- Con: One extra config section, non-default

**Recommendation**: Option A (src-layout). It is the uv default, recommended for libraries, and prevents accidental working-directory imports. The project is small enough that the move is low-risk.

---

## Phase 1: Branch Setup

1. `git checkout -b migrate-to-uv`

## Phase 2: Restructure to src-layout

1. `mkdir src`
2. `git mv textual_jsonschema_form/ src/textual_jsonschema_form/`
3. Keep `tests/` at root (uv/pytest convention)

Target structure:
```
src/
  textual_jsonschema_form/
    __init__.py
    base.py
    converter.py
    core.py
    fields.py
    py.typed
    registry.py
    validators.py
tests/
  conftest.py
  test_form.py
examples/
  __init__.py
  user_app.py
```

## Phase 3: Rewrite pyproject.toml

Convert from Poetry format to PEP 621 + uv format.

### Remove:
- `[tool.poetry]` section
- `[tool.poetry.dependencies]`
- `[tool.poetry.group.dev.dependencies]`
- `[tool.poetry.group.docs.dependencies]`
- `[build-system]` with poetry-core

### Add:
- `[project]` (PEP 621 metadata)
- `[dependency-groups]` for dev/docs deps
- `[build-system]` with uv_build

### Keep unchanged:
- `[tool.pytest.ini_options]`
- `[tool.mypy]`
- `[tool.ruff]`
- `[tool.coverage.report]`
- `[tool.coverage.run]`
- `[tool.ruff.per-file-ignores]`

### New pyproject.toml content:

```toml
[build-system]
requires = ["uv_build>=0.12.17,<0.13"]
build-backend = "uv_build"

[project]
name = "textual_jsonschema_form"
version = "0.1.0"
description = "Textual forms based on jsonschema"
authors = [{ name = "Lukas Burkhard", email = "dev@lksch.ch" }]
requires-python = ">=3.10,<4.0"
dependencies = [
    "textual>=0.40.0",
]

[project.urls]
Repository = "https://github.com/gh-PonyM/textual-jsonschema-form"
Documentation = "https://gh-PonyM.github.io/textual-jsonschema-form/"

[dependency-groups]
dev = [
    "pytest-cov>=4.0.0",
    "mypy>=1.5.1",
    "pre-commit>=3.4.0",
    "tox>=4.11.1",
    "bump2version>=1.0.1",
    "pydantic>=2.5.3",
    "textual-dev>=1.3.0",
    "ruff>=0.1.9",
    "pytest-asyncio>=0.23.2",
    "pytest>=7.4.3",
]
docs = [
    "mkdocs>=1.4.2",
    "mkdocs-material>=9.2.7",
    "mkdocstrings[python]>=0.23.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.mypy]
files = ["src/textual_jsonschema_form"]
disallow_untyped_defs = "False"
disallow_any_unimported = "True"
no_implicit_optional = "True"
check_untyped_defs = "True"
warn_return_any = "True"
warn_unused_ignores = "True"
show_error_codes = "True"
exclude = [
  'tests'
]

[tool.ruff]
target-version = "py38"
line-length = 88
fix = true
select = [
    "YTT", "S", "B", "A", "C4", "T10", "SIM", "I", "C90",
    "E", "W", "F", "PGH", "UP", "RUF", "TRY",
]
ignore = [
    "E501", "E731", "A002", "A003", "RUF012", "C408",
    "RUF015", "C901", "TRY003", "PGH003"
]

[tool.coverage.report]
skip_empty = true

[tool.coverage.run]
branch = true
source = ["textual_jsonschema_form"]

[tool.ruff.per-file-ignores]
"tests/*" = ["S101"]
```

## Phase 4: Delete Poetry-specific files

1. `git rm poetry.toml`

## Phase 5: Update Makefile

Replace all `poetry` commands with `uv` equivalents:

| Old Command | New Command |
|-------------|-------------|
| `poetry install` | `uv sync` |
| `poetry run <cmd>` | `uv run <cmd>` |
| `poetry build` | `uv build` |
| `poetry check --lock` | `uv lock --check` |
| `poetry publish` | `uv publish` |
| `poetry shell` | *(remove, not needed)* |
| `poetry config pypi-token.pypi $(PYPI_TOKEN)` | *(use UV_PUBLISH_TOKEN env var)* |

### Updated Makefile:

```makefile
.PHONY: install
install: ## Install the uv environment and install the pre-commit hooks
	@echo "Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "Checking uv lock file consistency with pyproject.toml"
	@uv lock --check
	@echo "Linting code: Running ruff"
	@uv run ruff check .
	@echo "Static type checking: Running mypy"
	@uv run mypy .

.PHONY: test
test: ## Test the code with pytest
	@echo "Testing code: Running pytest"
	@uv run pytest --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: build
build: clean-build ## Build wheel file using uv
	@echo "Creating wheel file"
	@uv build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@rm -rf dist

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "Publishing: Dry run."
	@UV_PUBLISH_TOKEN=$(PYPI_TOKEN) uv publish --dry-run
	@echo "Publishing."
	@UV_PUBLISH_TOKEN=$(PYPI_TOKEN) uv publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run mkdocs serve --livereload

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
```

## Phase 6: Update CI/CD (.github/)

### 6a. Replace setup-poetry-env with setup-uv-env

Delete `.github/actions/setup-poetry-env/action.yml` and create `.github/actions/setup-uv-env/action.yml`:

```yaml
name: "setup-uv-env"
description: "Composite action to setup Python and uv environment."

inputs:
  python-version:
    required: false
    description: "The python version to use"
    default: "3.11"

runs:
  using: "composite"
  steps:
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ inputs.python-version }}

    - name: Install uv
      uses: astral-sh/setup-uv@v4

    - name: Install dependencies
      run: uv sync
      shell: bash
```

### 6b. Update .github/workflows/main.yml

```yaml
name: Main

on:
  push:
    branches:
      - main
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Check out
        uses: actions/checkout@v3

      - uses: actions/cache@v3
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}

      - name: Set up the environment
        uses: ./.github/actions/setup-uv-env

      - name: Run checks
        run: make check

  tox:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
      fail-fast: false
    steps:
      - name: Check out
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install tox
        run: |
          python -m pip install --upgrade pip
          python -m pip install tox tox-gh-actions

      - name: Test with tox
        run: tox

      - name: Upload coverage reports to Codecov with GitHub Action on Python 3.11
        uses: codecov/codecov-action@v3
        if: ${{ matrix.python-version == '3.11' }}

  check-docs:
    runs-on: ubuntu-latest
    steps:
      - name: Check out
        uses: actions/checkout@v3

      - name: Set up the environment
        uses: ./.github/actions/setup-uv-env

      - name: Check if documentation can be built
        run: uv run mkdocs build -s
```

### 6c. Update .github/workflows/on-release-main.yml

```yaml
name: release-main

on:
  release:
    types: [published]
    branches: [main]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: Check out
        uses: actions/checkout@v3

      - name: Set up the environment
        uses: ./.github/actions/setup-uv-env

      - name: Export tag
        id: vars
        run: echo tag=${GITHUB_REF#refs/*/} >> $GITHUB_OUTPUT

      - name: Set version
        run: uv version $RELEASE_VERSION
        env:
          RELEASE_VERSION: ${{ steps.vars.outputs.tag }}

      - name: Build
        run: uv build

      - name: Publish
        run: uv publish
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}

  deploy-docs:
    needs: publish
    runs-on: ubuntu-latest
    steps:
      - name: Check out
        uses: actions/checkout@v3

      - name: Set up the environment
        uses: ./.github/actions/setup-uv-env

      - name: Deploy documentation
        run: uv run mkdocs gh-deploy --force
```

## Phase 7: Update tox.ini

Update tox to work with uv:

```ini
[tox]
skipsdist = true
envlist = py310, py311

[gh-actions]
python =
    3.10: py310
    3.11: py311

[testenv]
passenv = PYTHON_VERSION
allowlist_externals = uv
commands =
    uv sync
    pytest --doctest-modules tests --cov --cov-config=pyproject.toml --cov-report=xml
    mypy
```

## Phase 8: Update .gitignore

- Remove the `#poetry.lock` commented section (lines 101-106)
- `uv.lock` should NOT be in .gitignore (it should be committed)

## Phase 9: Update mypy config

The `files` path in `[tool.mypy]` needs updating since the package moved to `src/`:

```toml
[tool.mypy]
files = ["src/textual_jsonschema_form"]
```

## Phase 10: Generate lock file and verify

1. `uv lock` -- generates `uv.lock`
2. `uv sync` -- installs all dependencies
3. `uv run pytest` -- verify tests pass
4. `uv build` -- verify the package builds correctly
5. `uv run ruff check .` -- verify linting works
6. `uv run mypy .` -- verify type checking works

## Phase 11: Create AGENTS.md

Write a compact AGENTS.md with:
- Python managed by uv. Use `uv run` for every python command.
- Key commands: `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv build`
- Layout: src-layout, package at `src/textual_jsonschema_form/`
- Dependencies: lock file is `uv.lock`, dependency groups in `[dependency-groups]`
- CI: GitHub Actions, uses `astral-sh/setup-uv@v4`

---

## Risk Assessment

- **Low risk**: Makefile, CI/CD, .gitignore changes (mechanical replacements)
- **Medium risk**: pyproject.toml rewrite (must preserve all tool configs correctly)
- **Medium risk**: src-layout move (must update mypy config, verify imports work)
- **Low risk**: tox.ini update (simple command replacement)

## Rollback Plan

If something breaks:
1. `git checkout main` to go back
2. The `migrate-to-uv` branch preserves all changes for review
