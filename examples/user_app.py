from __future__ import annotations

import json
from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer

from textual_jsonschema_form import FormContainer, JsonSchemaTree
from textual_jsonschema_form.converter import TextualObjectParams


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

schema = UserModel.model_json_schema()
converter = TextualObjectParams.from_jsonschema(UserModel.model_json_schema())


class UserApp(App):
    BINDINGS = [("ctrl+l", "load_data", "Load Data")]

    FORM_CONTAINER_ID = "form-container"
    FORM_TREE_ID = "form-tree"

    def compose(self) -> ComposeResult:
        with Horizontal():
            with VerticalScroll():
                tree = JsonSchemaTree("Form Navigator")
                tree.root.expand()
                yield tree
            with VerticalScroll(id=self.FORM_CONTAINER_ID):
                yield FormContainer(model=converter)
        yield Footer()

    def on_mount(self):
        self.query_one(JsonSchemaTree).data = converter

    def action_load_data(self):
        self.query_one(FormContainer).form_data = user_data

    @on(FormContainer.FormSubmitted)
    def on_submit_form(self, event: FormContainer.FormSubmitted):
        self.notify(json.dumps(event.form_data, indent=2), timeout=7)


if __name__ == "__main__":
    app = UserApp()
    app.run()
