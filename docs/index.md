# textual-jsonschema-form

[![Release](https://img.shields.io/github/v/release/gh-PonyM/textual-jsonschema-form)](https://img.shields.io/github/v/release/gh-PonyM/textual-jsonschema-form)
[![Build status](https://img.shields.io/github/actions/workflow/status/gh-PonyM/textual-jsonschema-form/main.yml?branch=main)](https://github.com/gh-PonyM/textual-jsonschema-form/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/gh-PonyM/textual-jsonschema-form)](https://img.shields.io/github/commit-activity/m/gh-PonyM/textual-jsonschema-form)
[![License](https://img.shields.io/github/license/gh-PonyM/textual-jsonschema-form)](https://img.shields.io/github/license/gh-PonyM/textual-jsonschema-form)

This library provides form fields for jsonschema definitions (from pydantic).

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
- Tooltip Support for jsonschema description: TODO
- Jumping to the field on selection in `JsonSchemaTree`: TODO

## Customization

You can subclass any converter e.g. `TextualNumberParams` and register them with `@textual_converter.register("array")`.
Furthermore, you can register dedicated converters for string formats: `@textual_converter.register("string", format="path")`
to skip the default `string` converter for this format.

## RoadMap

- Fields for `list[str | int | float]`
- Navigation of very large forms using a `Tree` widget to jump to certain fields
