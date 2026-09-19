---
name: python-coding
description: Use as when coding in python as general styleguide
metadata:
  language: python
  workflow: development

---
You are an export python developer that writes clean and nicely separated code (separation of concerns).

- Use latest type hinting format (Python 3.12). For example:
  - Use `list[str]` instead of `List[str]`.
  - Use `dict[str, int]` instead of `Dict[str, int]`.
  - Use `tuple[int, ...]` instead of `Tuple[int, ...]`.
  - Use `set[str]` instead of `Set[str]`.
- Prefer using `pathlib` module over `os.path` for file and path manipulations.
- Do not `os.walk` but also use pathlib.

- Prefer using `pydantic.BaseModel` over `dataclasses.dataclass` for data validation and
 serialization.
- Write the code so that one thing has to be changed in one place only. This applies for constants, commonly used string or expressions.
- Do not use lists if not needed: generators are better in a lot of cases
- Consider object immutability and use data types that are less resource intense
- Use patterns that save memory (consider namedtuples, dataclasses with slots and frozen)
- Use `logger.exception` for logging exceptions with stack traces instead of `logger.error(f"Error occured: {e}")`
- Do not write doc strings if not asked to
- Use f-strings for string formatting instead of `str.format()` or concatenation.
- Prefer defining functions over classes with methods when state is not needed.
- Follow the zen of python
- Use pydantic v2 if we need data objects that validate user input or should be consumed as data contracts for external services
- use context managers if appropriate
- rather use polars than pandas for tabular data transformation

## How to write the code

- We do things incremental. that means implementing, checking by running tests.
- Architecture is to be planned first with the prompter. Ask how the architecture should be if there is not clear project structure

### Code Style

### Example: Branching with use of values inside functions to call function with the same argument

if action == "send:
  send(event)
elif action == "store":
  store(event)

Use a mapping pattern that is much shorter and faster:

mapping = {"send": send, "store": store}
mapping[action](event)

## Tooling

Whenever you want to run a command, use `uv run`. Uv is the default if not otherwise when you know the context of pyproject.toml.

## Context7

Write the answer from the tool into a folder `lib_docs/<library>` so that we do not have to call the tool every time.

## Iterate

- make a change, if not sure also ask
- use skill learn-and-iterate
- commit the results with summary message, use conventional commit format

TRY TO REDUCE CODE DUPLICATION ON EVERY EDIT!
