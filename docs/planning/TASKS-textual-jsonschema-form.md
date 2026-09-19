# Implementation Tasks — textual-jsonschema-form Migration (textual 0.46.0 → 8.2.8)

## Project Overview

Migrate the `textual-jsonschema-form` repo (`/home/pony_m/Repos/textual-jsonschema-form`) from textual `0.46.0` to `8.2.8`. This is Phase 1 of the migration plan in `docs/planning/textual-migration-plan.md`; `flows_clis` (Phase 2) is out of scope here.

**Current state**: `uv.lock` already resolves textual `8.2.8` and `textual-dev 1.8.0`. The venv has textual `8.2.8` installed. All 7 tests currently fail with a single root cause (`FormContainer._compose` name collision).

**Validation performed**: The proposed fixes were applied to a throwaway copy in `/tmp/opencode/migcheck2` and run against the repo venv — **7/7 tests pass**. The plan below is therefore verified, not speculative.

## Progress Summary

- Total Tasks: 8
- Completed: 8
- In Progress: 0
- Not Started: 0
- Blocked: 0

## Breaking Changes Audit Results (textual-jsonschema-form)

Full checklist from the requirements doc, resolved against textual 8.2.8:

| # | Item | Verdict |
|---|---|---|
| 1 | `Static.renderable` → `Static.content` | N/A — no `.renderable` on Static/Label instances in src. Tests use `label.renderable` (see #2). |
| 2 | `Label` arg `renderable` → `content` | **APPLIES (tests only)** — `tests/test_form.py:307,312`. `Label.content` exists but returns **raw markup** (`First Name[red]^[/red]`); `Label.render()` returns rendered text (`First Name^`) matching the old assertion semantics. Use `.render()`, not `.content`. |
| 3 | `HeaderTitle` static | N/A — not used. |
| 4 | `Select.BLANK` → `Select.NULL` | **APPLIES** — `converter.py:94`, `fields.py:443`. In 8.2.8 `Select.BLANK` still exists but is literally `False` (broken shim); `Select.NULL` is the sentinel (`NoSelection()`). |
| 5 | `Widget.anchor` semantics | N/A — not used. |
| 6 | `App.query` default screen | N/A — all queries are widget-scoped (`self.query`, `query_one`), not app-level. |
| 7 | `OptionList` changes | N/A — not used. |
| 8 | Default quit key `ctrl+q` | N/A — no custom quit bindings; example app only binds `ctrl+l`. |
| 9 | `App.dark` removed | N/A — not used. |
| 10 | `Input.view_position`/`cursor_position` | N/A — not used. |
| 11 | Markdown component classes | N/A — no Markdown usage. |
| 12 | `render_strips` signature | N/A — not used. |
| 13 | Markdown removed attrs | N/A — not used. |
| 14 | `Content()` default | N/A — not used. |
| 15 | Line API blank Segments | N/A — no custom line rendering. |
| — | **`Widget._compose` collision (NOT in checklist)** | **CRITICAL** — `FormContainer._compose(self, model, ...)` at `base.py:111` shadows textual 8.x's internal `Widget._compose()` (called by `_on_compose`). Causes `TypeError: FormContainer._compose() missing 1 required positional argument: 'model'` — the root cause of all 7 test failures. |

**Verified still working in 8.2.8 (no change needed)**: `Input.validators`, `Input.validate_on`, `Input.valid_empty`, `Input.restrict`, `Input.max_length`, `Input.validate()`, `Input.is_valid`, `Input.Changed` (`validation_result`), `Select._allow_blank` (instance attr), `NoSelection`, `TreeNode`, `InputType`, `InputValidationOn`, `textual.validation.{Function,Validator,Integer,Number,Failure}`, `Number.NotInRange`, `Pretty.update()`, `Tree` instance API (`root`, `add`, `set_label`, `allow_expand`, `clear`), `Switch.value`, `SelectionList.{selected,select,deselect_all}`, `Button.variant`, `Button.Pressed`, `Reactive`/`var`.

## Task Categories

### Infrastructure & Setup

#### TASK-001: Update textual dependency constraint
- **Status**: [x] Done
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: None
- **Description**: In `pyproject.toml:12` change `textual>=0.40.0` → `textual>=8.2.0` (or pin `==8.2.8` to match the plan). `uv.lock` already resolves 8.2.8; run `uv lock` to sync the constraint. Verify `textual-dev` (locked 1.8.0) stays compatible.
- **Acceptance Criteria**:
  - [ ] `pyproject.toml` constraint updated
  - [ ] `uv lock --check` passes
  - [ ] `uv run python -c "import textual; print(textual.__version__)"` prints `8.2.8`
- **Test First**: No (config change; verified by TASK-006)

### Core Functionality

#### TASK-002: Rename `FormContainer._compose` → `_compose_form` (CRITICAL)
- **Status**: [x] Done
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: None
- **Description**: In `src/textual_jsonschema_form/base.py`:
  - Rename `def _compose(self, model, parent_id=None, parent_label=None)` (line 111) → `def _compose_form(...)`.
  - Update caller in `compose()` (line 67): `yield from self._compose(self.model)` → `yield from self._compose_form(self.model)`.
  - Update recursive call (line 121): `yield from self._compose(model=field, ...)` → `yield from self._compose_form(model=field, ...)`.
  - Remove the dead commented-out `_on_compose` block (lines 106–109) which references the old name.
  - Rationale: textual 8.x `Widget._on_compose` calls `self._compose()` internally; the class method shadows it and breaks composition.
- **Acceptance Criteria**:
  - [ ] No method named `_compose` remains on `FormContainer`
  - [ ] `compose()` and recursion use `_compose_form`
  - [ ] `test_string_form` no longer raises `TypeError: FormContainer._compose() missing 1 required positional argument`
- **Test First**: Yes (existing tests are the failing spec)

#### TASK-003: Replace `Select.BLANK` with `Select.NULL`
- **Status**: [x] Done
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: None
- **Description**:
  - `src/textual_jsonschema_form/converter.py:94`: `"value": self.attrs.get("default", FormStrSelect.BLANK)` → `FormStrSelect.NULL`.
  - `src/textual_jsonschema_form/fields.py:443`: `if isinstance(self.value, NoSelection) or self.value == Select.BLANK:` → `if isinstance(self.value, NoSelection) or self.value is Select.NULL:`.
  - Rationale: in 8.2.8 `Select.BLANK` is `False` (a leftover shim), so it can never match the unselected state and is wrong as a default value. `Select.NULL` is the sentinel.
- **Acceptance Criteria**:
  - [ ] No `Select.BLANK` / `FormStrSelect.BLANK` references remain in `src/`
  - [ ] Unselected `FormStrSelect.form_data` returns `None`
  - [ ] `test_string_form` select assertions pass
- **Test First**: Yes

#### TASK-004: Fix `Pretty` object accessor
- **Status**: [x] Done
- **Priority**: Medium
- **Complexity**: Low
- **Dependencies**: None
- **Description**: `src/textual_jsonschema_form/fields.py:230` in `validation_errors()`: `f._renderable._object` → `f._pretty_renderable._object`. In 8.2.8 `Pretty` stores the object as `self._pretty_renderable` (a `rich.pretty.Pretty` instance exposing `_object`); `_renderable` no longer exists.
- **Acceptance Criteria**:
  - [ ] `validation_errors()` yields `(field_id, object)` tuples without AttributeError
  - [ ] `test_user_form_app` error-reporting path works
- **Test First**: Yes

### Testing & Validation

#### TASK-005: Update label assertions in tests
- **Status**: [x] Done
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: None
- **Description**: `tests/test_form.py:307,312`: `str(label.renderable)` → `str(label.render())`. Do **not** use `.content` — it returns raw markup (`First Name[red]^[/red]`), while `.render()` returns the rendered text (`First Name^`) that the assertions expect.
- **Acceptance Criteria**:
  - [ ] No `.renderable` references remain in `tests/`
  - [ ] `test_user_form_app` label assertions pass
- **Test First**: Yes (this IS the test update)

#### TASK-006: Run full test suite
- **Status**: [x] Done
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: TASK-001, TASK-002, TASK-003, TASK-004, TASK-005
- **Description**: `uv run pytest` — expect **7 passed** (verified against a copy in `/tmp/opencode/migcheck2`).
- **Acceptance Criteria**:
  - [ ] `uv run pytest` → 7 passed, 0 failed
- **Test First**: No (validation task)

#### TASK-007: Lint, format, type-check
- **Status**: [x] Done
- **Priority**: Medium
- **Complexity**: Low
- **Dependencies**: TASK-002, TASK-003, TASK-004, TASK-005
- **Description**: `uv run ruff check --fix`, `uv run ruff format`, `uv run mypy .`. Fix any new violations introduced by the migration.
- **Acceptance Criteria**:
  - [ ] `uv run ruff check .` clean
  - [ ] `uv run mypy .` clean (or documented acceptable diffs)
- **Test First**: No

#### TASK-008: Manual smoke test of example app
- **Status**: [x] Done
- **Priority**: Medium
- **Complexity**: Low
- **Dependencies**: TASK-006
- **Description**: Launch `uv run textual run examples/user_app.py` (or `uv run python examples/user_app.py`). Verify: form renders, tree navigator works, `ctrl+l` loads data, submit shows the notify payload, no visual regressions.
- **Acceptance Criteria**:
  - [ ] App launches without exceptions
  - [ ] Form fields, tree, load-data, and submit all function
- **Test First**: No

### Optional Hardening (post-migration, non-blocking)

#### TASK-009: Migrate private imports to public paths
- **Status**: [x] Done (partial — `InputType`/`InputValidationOn` have no public path)
- **Priority**: Low
- **Complexity**: Low
- **Dependencies**: TASK-006
- **Description**: Private module imports still resolve in 8.2.8 but are fragile. Public modules exist: `textual.widgets.tree` (`TreeNode`), `textual.widgets.input` (`InputType`, `InputValidationOn`), `textual.widgets.select` (`NoSelection`). Update `base.py:11` and `fields.py:25-26`.
- **Acceptance Criteria**:
  - [ ] No `textual.widgets._*` imports remain in `src/`
  - [ ] Tests still pass
- **Test First**: Yes

## Blocked Tasks

None.

## Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-19 | Rename `_compose` → `_compose_form` rather than overriding `_on_compose` | textual 8.x owns `_compose` internally; a custom name avoids the collision entirely. |
| 2026-09-19 | Use `label.render()` in tests, not `label.content` | `.content` returns raw markup; `.render()` returns rendered text matching the original assertion semantics. |
| 2026-09-19 | Use `Select.NULL` (not `Select.BLANK`) | `Select.BLANK` is `False` in 8.2.8 — semantically broken. |
| 2026-09-19 | Keep `Input._allow_blank` test assertions as-is | Verified it still exists as an instance attribute in 8.2.8. |
| 2026-09-19 | Pin textual `>=8.2.0` (or `==8.2.8`) | Matches the requirements doc; lock already resolves 8.2.8. |

## Questions & Assumptions

- **Assumption**: `textual-dev 1.8.0` (already locked) is compatible with textual 8.2.8 — verify during TASK-001.
- **Assumption**: No snapshot tests exist in this repo (none found in `tests/`), so no snapshot regeneration is needed.
- **Open question**: Should the dependency be `>=8.2.0` (lower bound, consistent with repo style) or pinned `==8.2.8` (matches `flows_clis` hard pin)? Default: `>=8.2.0` per the requirements doc's primary suggestion.
- **Out of scope**: `flows_clis` migration (Phase 2) and the `MIGRATION_PLAN.md` Poetry→uv content (already executed).

## Iteration Workflow

1. Work tasks in dependency order: TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-005 → TASK-006 → TASK-007 → TASK-008.
2. After completing each task, update its status in this file (`[ ]` open, `[/]` in-progress, `[x]` done) and update the Progress Summary.
3. Run `uv run pytest` after each source change; do not proceed past a red suite unless the failure is the task being worked on.
4. If a task is blocked, move it to Blocked Tasks with the reason and recommend an alternative; do not silently skip.
5. Re-run the breaking-changes audit grep (`renderable`, `BLANK`, `_compose`, `_renderable`) after all fixes to confirm zero stragglers.
6. When TASK-008 passes, report back to the orchestrator for Phase 2 (`flows_clis`).

## Best Practices Block

- Test-first: the existing suite is the spec — fix tests only where the textual API changed (TASK-005), then make source conform.
- Small, incremental changes with frequent validation (`uv run pytest` after each task).
- Document decisions and rationale in the Decisions Log as you go.
- Keep the working tree clean: tests that generate files must write to temp dirs.
- Do not hand-edit generated output; prefer changing the pydantic models / widgets.
- Flag blockers and risks early; this migration is verified end-to-end, so deviations from the plan are unexpected and worth surfacing.
