from __future__ import annotations
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar, Type

from textual.suggester import SuggestFromList
from textual.validation import Integer, Number, Validator

from .core import JSONFieldParametersBase, ValidatorType, strip_cmp_path
from .fields import ArrayField, FormInput, FormStrMultiSelect, FormStrSelect, FormSwitch
from .registry import textual_converter
from .validators import NumberRange


class InputBase(JSONFieldParametersBase[FormInput, Validator]):
    factory: ClassVar[Type[FormInput]] = FormInput

    @classmethod
    def extract(cls, params: dict, available: set[str]) -> tuple[list[Validator], dict]:
        attrs = {}
        if "default" in available:
            attrs["default"] = params.get("default")
        return [], attrs

    def get_options(self):
        """These are all kwargs that the default input field takes"""
        value = self.attrs.get("default", "")
        return {
            "valid_empty": not (self.required or value),
            "value": str(value),
            "name": self.field_name,
            "placeholder": self.description,
            "restrict": self.attrs.get("restrict"),
            "validate_on": ("changed", "submitted"),
            "password": self.attrs.get("password", False),
            "max_length": self.attrs.get("max_length", 0),
            "suggester": self.attrs.get("suggester"),
            "validators": self.validators,
            "type": {"string": "text"}.get(self.type, self.type),
        }

    def get_factory(self) -> Type[FormInput]:
        return self.factory


@textual_converter.register("string")
@dataclass
class TextualStringParam(InputBase):
    supported = {"string"}
    allowed = {
        "format",
        "pattern",
        "enum",
        "default",
    }
    ignore = JSONFieldParametersBase.ignore | {"minLength", "maxLength", "writeOnly"}
    SUGGESTER_FOR_ENUM: ClassVar[bool] = False

    @classmethod
    def extract(cls, params: dict, available: set[str]):
        validators, attrs = InputBase.extract(params, available)
        if "enum" in available:
            if cls.SUGGESTER_FOR_ENUM:
                attrs["suggester"] = SuggestFromList(
                    params["enum"], case_sensitive=False
                )
            attrs["choices"] = params["enum"]
        if "maxLength" in available:
            attrs["max_length"] = int(params["maxLength"])
        if "pattern" in available:
            attrs["restrict"] = params["pattern"]
        if "format" in available:
            fmt = attrs["format"] = params["format"]
            if fmt == "password":
                attrs["password"] = True
        return validators, attrs

    def get_factory(self):
        return (
            FormStrSelect
            if (not self.SUGGESTER_FOR_ENUM and self.attrs.get("choices"))
            else FormInput
        )

    def get_options(self):
        choices = self.attrs.get("choices")
        return (
            {
                "name": self.field_name,
                "options": ((opt, opt) for opt in choices),
                "prompt": f"Select {self.label}",
                "allow_blank": not self.required,
                "value": self.attrs.get("default", FormStrSelect.BLANK),
            }
            if (not self.SUGGESTER_FOR_ENUM and choices)
            else {
                "type": "text",
                "format": self.attrs.get("format"),
                **super().get_options(),
            }
        )


@textual_converter.register("boolean")
@dataclass
class TextualBoolParam(JSONFieldParametersBase[FormSwitch, None]):
    supported = {"boolean"}
    factory = FormSwitch

    @classmethod
    def extract(
        cls, params: dict, available: set[str]
    ) -> tuple[list[ValidatorType], dict]:
        _, attrs = InputBase.extract(params, available)
        return [], attrs

    def get_options(self):
        return {
            "value": self.attrs.get("default"),
            "name": self.field_name,
        }

    @property
    def field_label(self):
        if self.description and len(self.description) < 100:
            return self.description
        return self.label


@textual_converter.register("integer")
@textual_converter.register("number")
@dataclass
class TextualNumberParam(InputBase):
    supported = {"integer", "number"}
    allowed = {
        "enum",
        "format",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "default",
    }

    @classmethod
    def number_validator(cls, params: dict):
        return {"integer": Integer(), "number": Number()}[params["type"]]

    @classmethod
    def extract(cls, params: dict, available: set[str]):
        vals, attrs = InputBase.extract(params, available)
        vals.append(cls.number_validator(params))
        if {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"} & available:
            vals.append(
                NumberRange(
                    minimum=params.get("minimum"),
                    maximum=params.get("maximum"),
                    exclusive_maximum=params.get("exclusiveMaximum"),
                    exclusive_minimum=params.get("exclusiveMinimum"),
                )
            )
        if "enum" in available:
            raise NotImplementedError("Choices for numbers not implemented")
        return vals, attrs

    def get_options(self):
        return {
            "minimum": self.attrs.get("minimum"),
            "exclusive_minimum": self.attrs.get("minimum"),
            "exclusive_maximum": self.attrs.get("minimum"),
            "maximum": self.attrs.get("maximum"),
            **super().get_options(),
        }


@textual_converter.register("array")
@dataclass
class TextualArrayParams(JSONFieldParametersBase):
    supported = {"array"}
    defs_key: ClassVar[str] = "$defs"
    allowed: ClassVar[set] = {"items", "minItems", "maxItems", "default", defs_key}
    converter: ClassVar = textual_converter

    subfield: TextualStringParam | TextualNumberParam | TextualBoolParam | None = None

    @classmethod
    def extract(cls, params: dict, available: set[str]):
        validators, attrs = InputBase.extract(params, available)
        return validators, attrs

    def get_options(self):
        if self.choices:
            return {"name": self.field_name}

        def subfield_factory(**kwargs):
            f = self.subfield
            if not f:
                raise NotImplementedError()
            opts_ = f.get_options()
            opts_.update(kwargs)
            return f.get_factory()(**opts_)

        return {
            "required": self.required,
            "data": self.attrs.get("default", []),
            "label": self.field_label,
            "subfield_factory": subfield_factory,
        }

    @property
    def choices(self):
        return self.subfield.attrs.get("choices") if self.subfield else None

    def get_factory(self):
        choices = self.choices
        if choices:

            def with_options(**kwargs) -> FormStrMultiSelect:
                return FormStrMultiSelect.from_obj(
                    options=choices,
                    id=kwargs.get("id"),
                    classes=kwargs.get("classes"),
                    data=kwargs.get("data", []),
                )

            return with_options

        def with_no_options(**kwargs) -> ArrayField:
            return ArrayField(**kwargs)

        return with_no_options

    @classmethod
    def from_json_field(cls, field_name: str, required: bool, params: dict):
        available = cls.validate_params(params)
        validators, attrs = cls.extract(params, available)
        if "items" in available and (items := params["items"]):
            if ref := items.get("$ref"):
                definitions = params.get(cls.defs_key)
                if not definitions:
                    raise NotImplementedError(f"Missing {cls.defs_key}: {params}")
                items = definitions[strip_cmp_path(ref)]
                subtype = items["type"]
            else:
                subtype = items.get("type")
            subfield = cls.converter.lookup(subtype, items).from_json_field(
                field_name, True, items
            )
        else:
            raise NotImplementedError("subfield can't be None")
        return cls(
            subfield=subfield,
            type=params["type"],
            field_name=field_name,
            required=required,
            label=params.get("title", ""),
            description=params.get("description", ""),
            attrs=attrs,
            validators=validators,
        )


@textual_converter.register("object")
@dataclass
class TextualObjectParams(JSONFieldParametersBase):
    supported = {"object"}
    fields: (
        dict[
            str,
            TextualArrayParams
            | TextualNumberParam
            | TextualStringParam
            | TextualBoolParam,
        ]
        | None
    ) = None
    defs_key: ClassVar[str] = "$defs"
    ignore = JSONFieldParametersBase.ignore | {
        "properties",
        "required",
    }
    allowed = {"required", "properties", defs_key}
    converter = textual_converter

    @classmethod
    def extract(cls, params: dict, available: set[str]):
        return [], {}

    def get_options(self):
        return {
            "field_name": self.field_name,
            "required": self.required,
            "params": self.attrs,
        }

    @classmethod
    def preferred_all_of_schema(
        cls, item_schema: dict, params: dict
    ) -> tuple[str, dict]:
        all_of = item_schema["allOf"]
        if len(all_of) > 1:
            raise NotImplementedError(all_of)

        schema = all_of[0]
        ref = schema.get("$ref")
        if not ref:
            schema.setdefault("description", item_schema.get("description", ""))
            return schema["type"], schema

        s = params[cls.defs_key][strip_cmp_path(ref)]
        if "default" in params:
            s["default"] = params["default"]
        return s["type"], s

    @staticmethod
    def sorted_any_of(any_of: Iterable[dict]):
        return sorted(any_of, key=lambda x: len(x), reverse=True)

    @classmethod
    def preferred_any_of_schema(
        cls, item_schema: dict, params: dict
    ) -> tuple[str, dict]:
        inferred_types: dict[str, dict] = {}
        any_of = item_schema["anyOf"]
        types = tuple(i for i in any_of if i.get("type") != "null")
        if len(types) > 2:
            raise ValueError(
                "typer can not handle different types besides one and None:"
                f" {item_schema}"
            )

        # getting the object with most keys
        for item in cls.sorted_any_of(types):
            ref = item.get("$ref")
            if ref:
                s = params[cls.defs_key][strip_cmp_path(ref)]
                choices = s.get("enum")
                # only support for definition of enums that can be converted
                if not choices:
                    continue
                    # raise NotImplementedError(item)
                item_type = s["type"]
                inferred_types.setdefault(item_type, s)
                continue
            ti = item["type"]
            if ti == "object":
                continue
                # raise ValueError("A oneOf type can not be another object/dict")
            if ti == "array":
                item_type = item["items"]["type"]
                if item_type == "object":
                    continue
                    # raise ValueError("A oneOf type can not be another object/dict")
                # raise NotImplementedError("Must implements the Array converter")
                inferred_types.setdefault(ti, item)
                continue
            else:
                inferred_types.setdefault(ti, item)
        if len(inferred_types) > 1:
            raise NotImplementedError(f"Multiple inferred types: {inferred_types}")
        if not inferred_types:
            raise NotImplementedError(f"Could not infer any types: {types}")
        type_, schema = tuple(inferred_types.items())[0]
        schema.setdefault("description", item_schema.get("description", ""))
        schema.setdefault("title", item_schema.get("title", ""))
        return type_, schema

    @classmethod
    def from_jsonschema(cls, schema: dict):
        instance = cls.from_json_field(
            schema.get("title", "Form"),
            False,
            schema,
        )
        return instance

    @classmethod
    def from_json_field(cls, field_name: str, required: bool, params: dict):
        available = cls.validate_params(params)
        properties = params.get("properties", None)
        if properties is None:
            raise NotImplementedError("Missing properties.")
        fields = {}
        defs = params.get(cls.defs_key, {})
        required_f = params.get("required", [])
        for property_name, item_schema in properties.items():
            if "allOf" in item_schema:
                type_, schema_ = cls.preferred_all_of_schema(item_schema, params)
                field = cls.converter.lookup(type_, schema_)
                if "default" in item_schema:
                    schema_["default"] = item_schema["default"]
                if cls.defs_key in field.allowed:
                    schema_[cls.defs_key] = defs
                fields[property_name] = field.from_json_field(
                    property_name, property_name in required_f, schema_
                )
                continue
            if item_schema.get("anyOf"):
                type_, schema_ = cls.preferred_any_of_schema(item_schema, params)
                field = cls.converter.lookup(type_, schema_)
                if cls.defs_key in field.allowed:
                    schema_[cls.defs_key] = defs
                # If a default is given
                fields[property_name] = field.from_json_field(
                    property_name, property_name in required_f, schema_
                )
                continue
            if ref := item_schema.get("$ref"):
                if not defs:
                    raise NotImplementedError("Missing $defs.")
                item_schema = defs[strip_cmp_path(ref)]

            if "enum" in item_schema and "type" not in item_schema:
                item_schema["type"] = "enum"
            if type_ := item_schema.get("type", None):
                field = cls.converter.lookup(type_, item_schema)
                if cls.defs_key in field.allowed:
                    item_schema[cls.defs_key] = defs
                fields[property_name] = field.from_json_field(
                    property_name, property_name in required_f, item_schema
                )

            else:
                raise NotImplementedError(
                    f"Undefined type for property {property_name}: {item_schema}"
                )
        validators, attrs = cls.extract(params, available)
        return cls(
            fields=fields,
            type=params["type"],
            field_name=field_name,
            required=required,
            label=params.get("title", ""),
            description=params.get("description", ""),
            attrs=attrs,
            validators=validators,
        )
