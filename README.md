# textual-jsonschema-form

[![Release](https://img.shields.io/github/v/release/gh-PonyM/textual-jsonschema-form)](https://img.shields.io/github/v/release/gh-PonyM/textual-jsonschema-form)
[![Build status](https://img.shields.io/github/actions/workflow/status/gh-PonyM/textual-jsonschema-form/main.yml?branch=main)](https://github.com/gh-PonyM/textual-jsonschema-form/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/gh-PonyM/textual-jsonschema-form/branch/main/graph/badge.svg)](https://codecov.io/gh/gh-PonyM/textual-jsonschema-form)
[![Commit activity](https://img.shields.io/github/commit-activity/m/gh-PonyM/textual-jsonschema-form)](https://img.shields.io/github/commit-activity/m/gh-PonyM/textual-jsonschema-form)
[![License](https://img.shields.io/github/license/gh-PonyM/textual-jsonschema-form)](https://img.shields.io/github/license/gh-PonyM/textual-jsonschema-form)

Textual forms based on jsonschema

- **Github repository**: <https://github.com/gh-PonyM/textual-jsonschema-form/>
- **Documentation** <https://gh-PonyM.github.io/textual-jsonschema-form/>

## Usage

Please take a look into the provided [user app](examples/user_app.py) example.

## Development

Install the environment with

```bash
make install
```

Run `make` to see all the options.

## Releasing a new version

- Create an API Token on [Pypi](https://pypi.org/).
- Add the API Token to your projects secrets with the name `PYPI_TOKEN` by visiting
[this page](https://github.com/gh-PonyM/textual-jsonschema-form/settings/secrets/actions/new).
- Create a [new release](https://github.com/gh-PonyM/textual-jsonschema-form/releases/new) on Github.
Create a new tag in the form ``*.*.*``.
