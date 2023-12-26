# textual-jsonschema-form

[![Release](https://img.shields.io/github/v/release/gh-PonyM/textual-jsonschema-form)](https://img.shields.io/github/v/release/gh-PonyM/textual-jsonschema-form)
[![Build status](https://img.shields.io/github/actions/workflow/status/gh-PonyM/textual-jsonschema-form/main.yml?branch=main)](https://github.com/gh-PonyM/textual-jsonschema-form/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/gh-PonyM/textual-jsonschema-form)](https://img.shields.io/github/commit-activity/m/gh-PonyM/textual-jsonschema-form)
[![License](https://img.shields.io/github/license/gh-PonyM/textual-jsonschema-form)](https://img.shields.io/github/license/gh-PonyM/textual-jsonschema-form)

The idea was to create a widget that supports converting a json schema (from pydantic models) into a TUI Form.

## Form Features

- `integer/number`
  - check if valid number
  - min, max, exclusive min and max validation
- `str`
    - `enum`: Converter supports **suggester** or `Select` widget
    - `format: path`: validates resolved path
    - `format: directory-path`: validates existing directory
    - `format: file-path`: validates existing file
    - `format: date`: validates correct date format with example using `Input` as default
    - `format: date-time`: validates correct date and time format with example using `Input` as default
    - `format: ipv4`: TODO
    - `format: ipv6`: TODO
- `boolean`:
  - `Switch` field
- `array`:
  - `enum`: Supported using MultiSelect
  - `integer/number`: TODO Any number as list
  - `str`: TODO Any string as list
  - `object`: TODO
- `object`: Sub-Forms are supported
- Tooltip Support for description: TODO
- Jumping to the field on selection of the jsonschema overview tree: TODO
