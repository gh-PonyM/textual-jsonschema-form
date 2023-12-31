from __future__ import annotations
from dataclasses import dataclass, field
from typing import Type

from .core import JSONFieldParametersBase


@dataclass
class TextualConverter:
    """Registry for typer cli type conversion from jsonschema"""

    converters: dict[str, Type[JSONFieldParametersBase]] = field(
        default_factory=lambda: {}
    )

    def __get_key(self, type_: str, fmt: str | None) -> str:
        return type_ if not fmt else f"{type_}.{fmt}"

    def register(self, type_: str, format: str | None = None):
        def type_format_registration(converter: Type[JSONFieldParametersBase]):
            self.converters[self.__get_key(type_, format)] = converter
            return converter

        return type_format_registration

    def lookup(
        self, type_: str, defs: dict | None = None
    ) -> Type[JSONFieldParametersBase]:
        key_with_fmt = self.__get_key(type_, (defs or {}).get("format"))
        return self.converters.get(key_with_fmt, self.converters[type_])


textual_converter = TextualConverter()
