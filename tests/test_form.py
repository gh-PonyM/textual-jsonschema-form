import json
from datetime import date
from enum import Enum
from typing import Literal

import pytest
from pydantic import BaseModel, Field
from textual import on
from textual.app import App, ComposeResult
from textual.validation import Function, Integer
from textual.widgets import Footer

from textual_jsonschema_form import FormContainer
from textual_jsonschema_form.converter import TextualObjectParams
from textual_jsonschema_form.fields import FormInput
from textual_jsonschema_form.validators import NumberRange


class TestModel(BaseModel):
    payload: str
    d: date = Field(description="Required date")
    d_d: date = Field(
        date.today(),
        description="Required with default date means empty string is not allowed",
    )
    opt_d: date | None = Field(None, description="Optional with default")


test_model_schema = TestModel.model_json_schema()


class Interests(str, Enum):
    SPORTS = "Sports"
    TV = "TV"
    MATH = "Math"
    LIT = "Literature"


class Address(BaseModel):
    street: str = Field(title="Street Name")
    street_num: str = Field(title="Street Number")
    postal_code: int
    city: str = Field(description="City")


class UserModel(BaseModel):
    first_name: str = Field(description="Name of User")
    age: int = Field(description="Your age", ge=10, le=115)
    country: Literal["CH", "DE", "AT"]
    interests: tuple[Interests, ...] = Field(
        (Interests.LIT,), description="Your interests"
    )
    vegetarian: bool = Field(False, description="Are you a veggie?")
    date_of_birth: date = Field(description="Your date of birth")
    address: Address


user_data = dict(
    first_name="Hans",
    age=11,
    country="CH",
    date_of_birth=date.today(),
    address=dict(street="A", street_num="55", postal_code=8000, city="Bobo"),
    interests=["TV"],
)


class UserApp(App):
    BINDINGS = [("l", "load_data", "Load Data")]

    def compose(self) -> ComposeResult:
        schema = UserModel.model_json_schema()
        yield FormContainer(model=TextualObjectParams.from_jsonschema(schema))
        yield Footer()

    def action_load_data(self):
        self.query_one(FormContainer).form_data = user_data

    @on(FormContainer.FormSubmitted)
    def on_submit_form(self, event: FormContainer.FormSubmitted):
        self.notify(json.dumps(event.form_data, indent=2), timeout=7)


@pytest.mark.parametrize(
    "name,schema_required,required,input_validators,valid_empty",
    (
        ("d", True, True, [Function], False),
        ("d_d", False, False, [Function], False),
        ("opt_d", False, False, [Function], True),
        ("payload", True, True, [Function], False),
    ),
)
def test_fields(name, schema_required, required, input_validators, valid_empty):
    converter = TextualObjectParams.from_jsonschema(test_model_schema)
    field_conv = converter.fields[name]
    assert (name in test_model_schema["required"]) == schema_required
    assert field_conv.required == required
    input_field = field_conv.get_factory()(**field_conv.get_options())
    assert isinstance(input_field, FormInput)

    if hasattr(input_field, "validators"):
        validator_types = [type(v) for v in input_field.validators]
        assert validator_types == input_validators
    assert input_field.valid_empty == valid_empty
    if valid_empty:
        return
    input_field.value = ""
    assert not input_field.is_valid, f"{name} should not be valid for an empty string"


async def test_user_form_app():
    schema = UserModel.model_json_schema()
    model = TextualObjectParams.from_json_field(schema["title"], True, schema)
    first_name = model.fields["first_name"]
    assert first_name.required

    age = model.fields["age"]
    assert isinstance(age.validators[0], Integer)
    assert isinstance(age.validators[1], NumberRange)
    validator = age.validators[1]
    assert validator.minimum == 10
    assert validator.maximum == 115

    veggie = model.fields["vegetarian"]
    assert not veggie.required

    country = model.fields["country"]
    assert country.required
    assert country.attrs["choices"]

    d_o_b = model.fields["date_of_birth"]
    assert not d_o_b.validators, (
        "The input field implements the validators in the __init__"
        " due value getters and setters that use same data as validators"
    )

    interests = model.fields["interests"]
    assert interests.attrs["default"]
    assert not interests.required, "A default is given, the field is not required"

    app = UserApp()

    async with app.run_test() as pilot:
        form = app.query_one(FormContainer)
        field_id = "first_name"
        label = form.get_field_label(field_id)
        assert str(label.renderable) == f"{first_name.label}^"

        field_id = "vegetarian"
        label = form.get_field_label(field_id)
        assert (
            str(label.renderable) == f"{veggie.description}"
        ), "Switch should use description by default if it's not too long"

        await pilot.press("l")


if __name__ == "__main__":
    app = UserApp()
    app.run()
