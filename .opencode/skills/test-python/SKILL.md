---
name: test-python
description: Use skill test-python when asked to write tests
metadata:
  library: pytest
  workflow: development

---
You follow test driven development when implementing changes. You are most happy if
you found a good way to verify results. Sometimes when you are blind, you admit it, and we will find a solution to help gettings feedback from consistent validation from code execution.

- when asked for tests, use pytest,
- Do never use class based tests with pytest, always functions
- if needed, add fixtures to `contest.py` when a setup might be used multiple times in tests
- you can always run `uv run ruff format && uv ruff check --fix` before running test to lint and format first
- run required tests with `uv run pytest ...`

EVEN WHEN TESTING IS MENTIONED IN PLANNING LATER, YOU WANT TO HAVE CONCTEXT OF EXISTING TESTS. YOU WANT TO VERIFY IF YOU ARE RIGHT USING SOME SORT OF TEST.
