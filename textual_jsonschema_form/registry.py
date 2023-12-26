from dataclasses import dataclass, field

from .core import JSONFieldParametersBase


@dataclass
class Converter:
    """Registry for typer cli type conversion from jsonschema"""

    converters: dict[str, type[JSONFieldParametersBase]] = field(
        default_factory=lambda: {}
    )

    def register(self, type_: str):
        def type_registration(converter: type[JSONFieldParametersBase]):
            self.converters[type_] = converter
            return converter

        return type_registration

    def lookup(
        self, type_: str, defs: dict | None = None
    ) -> type[JSONFieldParametersBase]:
        return self.converters[type_]


@dataclass
class TextualConverter(Converter):
    """Registry for typer cli type conversion from jsonschema"""

    converters: dict[str, type[JSONFieldParametersBase]] = field(
        default_factory=lambda: {}
    )

    def __get_key(self, type_: str, fmt: str | None) -> str:
        return type_ if not fmt else f"{type_}.{fmt}"

    def register(self, type_: str, format: str | None = None):
        def type_format_registration(converter: type[JSONFieldParametersBase]):
            self.converters[self.__get_key(type_, format)] = converter
            return converter

        return type_format_registration

    def lookup(
        self, type_: str, defs: dict | None = None
    ) -> type[JSONFieldParametersBase]:
        key_with_fmt = self.__get_key(type_, (defs or {}).get("format"))
        return self.converters.get(key_with_fmt, self.converters[type_])


textual_converter = TextualConverter()