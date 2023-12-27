import abc
from collections.abc import Generator
from dataclasses import dataclass
from typing import ClassVar, Generic, TypeVar

FactoryType = TypeVar("FactoryType")
ValidatorType = TypeVar("ValidatorType")


def strip_cmp_path(ref: str) -> str:
    # TODO: can't handle all sorts of jsonschema, the standard by jsonschema would be '$definitions' instead of
    # $defs
    return ref.replace("#/components/schemas/", "").replace("#/$defs/", "")


@dataclass
class JSONFieldParametersBase(Generic[FactoryType, ValidatorType], abc.ABC):
    """The Base Adapter to convert a json-schema using different converters to end up with
    different object adapters or to generate code out of those converters"""

    supported: ClassVar[set[str]]
    ignore: ClassVar[set[str]] = {
        "additionalProperties",
        "name",
        "type",
        "title",
        "description",
        "if",
        "then",
    }
    allowed: ClassVar[set[str]] = {"default"}
    defs_key: ClassVar[str] = "$defs"
    factory: ClassVar = None

    type: str
    field_name: str
    label: str
    description: str
    required: bool
    attrs: dict
    validators: list[ValidatorType] | None = None

    # TODO: how to type annotate the return value?
    def get_factory(self):
        if self.factory:
            return self.factory
        raise NotImplementedError(
            f"class {self.__class__.__name__} must implement this"
        )

    @property
    def field_label(self):
        return self.label

    def get_options(self):
        """Returns the keyword arguments for the factory model to initialize"""
        return {}

    @property
    def used_imports(self) -> Generator[str, None, None]:
        """Returns the imports as full import statements for the types used that have to be imported"""
        yield from ()

    @property
    def default(self) -> str | None:
        return self.attrs.get("default")

    @property
    def format(self) -> str | None:
        return self.attrs.get("format")

    def __post_init__(self):
        if self.type not in self.supported:
            raise TypeError(f"{self.__class__} does not support the {type} type.")

    @classmethod
    def validate_params(cls, params: dict) -> set[str]:
        available = set(params.keys())
        if illegal := ((available - cls.ignore) - cls.allowed):
            raise NotImplementedError(f"Unsupported attributes: {illegal} for {cls}.")
        return available

    @classmethod
    def extract(
        cls, params: dict, available: set[str]
    ) -> tuple[list[ValidatorType], dict]:
        """Extracts attributes such as default"""
        return [], {}

    @classmethod
    def from_json_field(cls, field_name: str, required: bool, params: dict):
        available = cls.validate_params(params)
        validators, attrs = cls.extract(params, available)
        return cls(
            type=params["type"],
            field_name=field_name,
            required=required,
            label=params.get("title", ""),
            description=params.get("description", ""),
            attrs=attrs,
            validators=validators,
        )
