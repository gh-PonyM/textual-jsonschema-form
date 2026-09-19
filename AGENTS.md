# AGENTS.md

## Project: textual-jsonschema-form

Textual forms based on JSON Schema. Generates Textual UI forms from Pydantic models.

## Quick Reference

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Type check
uv run ty check

# Build package
uv build
```

## Layout

- **Package**: `src/textual_jsonschema_form/` (src-layout, uv_build backend)
- **Tests**: `tests/`
- **Examples**: `examples/`
- **Lock file**: `uv.lock` (committed)

## Dependencies

- **Runtime**: `textual>=0.40.0`
- **Python**: `>=3.12,<4.0`
- **Dev group**: pytest, ty, ruff, pre-commit, tox, bump2version, pydantic, textual-dev
- **Docs group**: mkdocs, mkdocs-material, mkdocstrings[python]

Dependency groups are in `[dependency-groups]` in `pyproject.toml`.

## Commands

- `uv run pytest` -- run tests
- `uv run ruff check .` -- lint
- `uv run ruff format .` -- format
- `uv run ty check` -- type check
- `uv build` -- build wheel/sdist
- `uv lock --check` -- verify lock file consistency
- `uv sync` -- install/sync dependencies

## Code Style

- **Linter/formatter**: ruff
- **Type checker**: ty
- **Target Python**: 3.12
- Line length: 88
- Use `from __future__ import annotations` in test files

## CI/CD

GitHub Actions (`.github/workflows/`):
- `main.yml`: quality checks + tox tests on push/PR
- `on-release-main.yml`: build, publish to PyPI, deploy docs on release

Uses `astral-sh/setup-uv@v4` action.
