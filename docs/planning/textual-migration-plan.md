# Textual Migration Plan: 0.46.0 → 8.2.8

## Repositories Affected

| Repository | Current Version | Constraint |
|---|---|---|
| `flows_clis` | pinned `== 0.46.0` | hard pin |
| `textual-jsonschema-form` | `>= 0.40.0` | lower bound only |

**Strategy**: Migrate `textual-jsonschema-form` first, then update `flows_clis` to point at the updated dependency + new textual version.

---

## Breaking Changes Audit Checklist

Scan source for each pattern below. Check off when resolved.

### 1. `Static.renderable` → `Static.content`

- [ ] `flows_clis` — grep for `.renderable` on Static/Label instances
- [ ] `textual-jsonschema-form` — grep for `.renderable`

### 2. `Label` constructor arg `renderable` → `content`

- [ ] `flows_clis` — grep for `Label(renderable=`
- [ ] `textual-jsonschema-form` — grep for `Label(renderable=`

### 3. `HeaderTitle` is now a static (no `text`/`sub_text` reactives)

- [ ] `flows_clis` — grep for `HeaderTitle`, `.text`, `.sub_text`
- [ ] `textual-jsonschema-form` — grep for `HeaderTitle`

### 4. `Select.BLANK` → `Select.NULL`

- [ ] `flows_clis` — grep for `Select.BLANK`
- [ ] `textual-jsonschema-form` — grep for `Select.BLANK`

### 5. `Widget.anchor` semantics changed (v4.0)

- [ ] `flows_clis` — grep for `Widget.anchor`, `.anchor`
- [ ] `textual-jsonschema-form` — grep for `.anchor`

### 6. `App.query` queries default screen, not active screen (v3.0)

- [ ] `flows_clis` — audit all `self.query`, `app.query` calls for assumptions about active screen
- [ ] `textual-jsonschema-form` — same audit

### 7. `OptionList` — `Separator` removed, `wrap`/`tooltip` args removed (v2.0)

- [ ] `flows_clis` — grep for `Separator` in OptionList context, `OptionList(wrap=`, `OptionList(tooltip=`
- [ ] `textual-jsonschema-form` — same

### 8. Default quit key is now `ctrl+q` (v1.0)

- [ ] `flows_clis` — check if any custom keybindings rely on `ctrl+c` quit behavior
- [ ] `textual-jsonschema-form` — same

### 9. `App.dark` reactive removed (v0.86)

- [ ] `flows_clis` — grep for `app.dark`, `self.dark`
- [ ] `textual-jsonschema-form` — same

### 10. `Input.view_position` / `Input.cursor_position` reactives removed (v0.89)

- [ ] `flows_clis` — grep for `view_position`, `cursor_position` on Input
- [ ] `textual-jsonschema-form` — same

### 11. Markdown component classes moved to `MarkdownBlock` (v5.0)

- [ ] `flows_clis` — grep for Markdown CSS targeting component classes
- [ ] `textual-jsonschema-form` — same

### 12. `Visual.render_strips` signature changed (v5.0)

- [ ] `flows_clis` — grep for `render_strips`
- [ ] `textual-jsonschema-form` — grep for `render_strips`

### 13. Markdown removed attrs: `code_dark_theme`, `code_light_theme`, `code_indent_guides` (v5.0)

- [ ] `flows_clis` — grep for these attributes
- [ ] `textual-jsonschema-form` — same

### 14. `Content()` now defaults to empty string (v3.0)

- [ ] Low risk — verify no code relies on `Content()` raising or behaving differently

### 15. Line API no longer auto-applies background to blank Segments (v6.0)

- [ ] `flows_clis` — check for custom widget rendering that relies on blank Segment backgrounds
- [ ] `textual-jsonschema-form` — same

---

## API Additions to Adopt (Optional but Recommended)

These are new features that may simplify existing code:

| Feature | Version | Notes |
|---|---|---|
| Textual markup (`Content.from_markup`) | v2.0 | Replaces Rich markup |
| `text-wrap` / `text-overflow` CSS | v2.0 | May replace manual truncation |
| Theming system (`App.theme`) | v0.86 | Built-in themes, dynamic switching |
| `Widget.BLANK` | v7.1 | Optimize rendering of large containers |
| `DOMNode.trap_focus` | v6.5 | Focus management |
| `empty` pseudo-class | v5.1 | CSS for empty containers |
| `scrollbar-visibility` rule | v6.3 | Fine-grained scrollbar control |
| `pointer` CSS rule | v7.4 | Cursor styling |
| `textual.getters` | v3.7 | Convenience getters |
| `textual.highlight` module | v5.0 | Syntax highlighting |
| Smooth scrolling | v2.0 | Pixel-perfect scrolling |
| Multi-mode screens (`push_screen` mode arg) | v8.0 | Screen management |

---

## Migration Steps

### Phase 1: `textual-jsonschema-form`

1. Update `textual` dependency to `>=8.2.0` (or pin `==8.2.8`)
2. Run `uv run ruff check --fix` and `uv run ruff format`
3. Run `uv run pytest` — note failures
4. Fix each failing test against the checklist above
5. Update snapshot tests if applicable
6. Verify CLI entrypoint works manually

### Phase 2: `flows_clis`

1. Update `textual` pin to `==8.2.8`
2. Update `textual-jsonschema-form` git ref to migrated version
3. Update `textual-dev` if needed (`^1.3.0` → latest)
4. Run `uv run ruff check --fix` and `uv run ruff format`
5. Run `uv run pytest` — note failures
6. Fix each failing test against the checklist above
7. Update snapshot tests if applicable
8. Manual smoke test of `flows-tui`

### Phase 3: Verify

- [ ] `uv run pytest` passes in both repos
- [ ] `uv run ty check` passes (or known acceptable diffs)
- [ ] `make docker-test` passes
- [ ] `uv run textual` demo app launches correctly
- [ ] No visual regressions in TUI (manual check)

---

## Reference Links

- [Textual CHANGELOG.md](https://github.com/Textualize/textual/blob/main/CHANGELOG.md)
- [PyPI textual releases](https://pypi.org/project/textual/#history)
- Current pin: `flows_clis/pyproject.toml` line `textual == 0.46.0`
- Dependency pin: `textual-jsonschema-form/pyproject.toml` line `textual = ">=0.40.0"`
