from functools import lru_cache
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, DirectoryPath, Field, FilePath
from textual import on
from textual.app import App, ComposeResult
from textual.validation import Integer
from textual.widgets import Button

from examples.user_app import UserApp, UserModel, user_data
from textual_jsonschema_form import FormContainer
from textual_jsonschema_form.converter import TextualObjectParams
from textual_jsonschema_form.validators import NumberRange


class TBaseModel(BaseModel):
    _test_data: ClassVar[dict] = {}

    @classmethod
    def expected(cls) -> dict:
        return cls.model_validate(cls._test_data).model_dump()


class FormApp(App):
    def __init__(self, model: type[TBaseModel]):
        super().__init__()
        self.model = model
        self.converter = TextualObjectParams.from_jsonschema(model.model_json_schema())
        self.form_data = None

    def compose(self) -> ComposeResult:
        yield FormContainer(model=self.converter)

    @property
    def form(self):
        return self.query_one(FormContainer)

    @property
    def submit_btn(self):
        return self.query_one("#submit", Button)

    def load_data(self):
        self.query_one(FormContainer).form_data = self.model._test_data

    @on(FormContainer.FormSubmitted)
    def on_submit_form(self, event: FormContainer.FormSubmitted):
        self.form_data = event.form_data


async def load_and_check(pilot, valid_as_is: bool = False):
    submit: Button = pilot.app.submit_btn
    submit.press()
    await pilot.pause()
    if not valid_as_is:
        assert submit.variant == "error"
        assert pilot.app.form_data is None
    else:
        assert submit.variant == "success"
        assert pilot.app.form_data

    pilot.app.load_data()
    submit.press()
    await pilot.pause()
    try:
        assert submit.variant == "success"
    except AssertionError:
        for v_id, errors in pilot.app.form.validation_errors():
            print(f"{v_id}: {errors}")
        raise
    assert pilot.app.form_data == pilot.app.model.expected()


class StringModel(TBaseModel):

    _test_data: ClassVar = {"s": "Anderson Paak is great", "c": "B"}

    s: str
    s_d: str = "Foobar"
    s_d_n: str | None = None
    c: Literal["A", "B", "C"]
    c_d: Literal["C", "D"] | None = None


async def test_string_form():
    async with FormApp(model=StringModel).run_test() as pilot:
        form = pilot.app.form
        inp = form.get_input("s")
        assert inp.form_data is None
        assert not inp.is_valid
        inp = form.get_input("s_d")
        assert inp.form_data == "Foobar"
        assert inp.is_valid
        inp = form.get_input("s_d_n")
        assert inp.form_data is None
        assert inp.is_valid
        inp = form.get_input("c")

        assert pilot.app.converter.fields["c"].required
        assert not inp._allow_blank, "Select widget is required"
        assert (
            inp.form_data == "A"
        ), "The widget has no blank option and uses the first choice as default"
        assert inp.is_valid

        inp = form.get_input("c_d")
        assert not pilot.app.converter.fields["c_d"].required
        assert inp._allow_blank
        assert inp.form_data is None
        assert inp.is_valid
        await load_and_check(pilot)


@lru_cache
def existing_path():
    for path in (Path("/usr/bin"), Path("C:/Windows/System32")):
        if path.exists():
            return path


class StringWithFormatModel(TBaseModel):
    _test_data: ClassVar = {"p": existing_path(), "d": existing_path()}

    p: Path
    d: DirectoryPath
    p_o: Path | None = None
    f_p_o: FilePath | None = None
    d_o: DirectoryPath | None = None


async def test_string_format_form(temporary_directory):
    """Test all supported string formats including validators and submitting"""
    async with FormApp(model=StringWithFormatModel).run_test() as pilot:
        form = pilot.app.form

        inp = form.get_input("p")
        assert pilot.app.converter.fields["p"].required
        assert inp.form_data is None
        assert not inp.is_valid
        assert inp.format == "path"
        inp.form_data = Path(".")
        assert not inp.is_valid, "Only absolute paths are allowed"
        inp.form_data = Path("~/")
        assert inp.is_valid, "the validator should allow ~ and expand the user"

        inp = form.get_input("p_o")
        assert inp.form_data is None
        assert inp.is_valid

        inp = form.get_input("f_p_o")
        assert inp.form_data is None
        assert inp.valid_empty
        assert len(inp.validators) == 1, "file path validator"
        assert inp.validators[-1].function.__name__ == "valid_file_path"
        assert inp.is_valid
        fp = temporary_directory / "foo"
        inp.form_data = fp
        assert not inp.is_valid
        fp.write_text("foo")
        assert inp.is_valid, "The file foo exists and the validator should run again"
        # Reset the value so the rest passes
        inp.form_data = None
        assert inp.value == ""

        inp = form.get_input("d")
        assert inp.form_data is None
        assert not inp.valid_empty
        assert len(inp.validators) == 2, "Empty + directory validator"
        assert pilot.app.converter.fields["d"].attrs["format"] == "directory-path"
        assert inp.validators[-1].function.__name__ == "valid_folder"
        assert not inp.is_valid
        await load_and_check(pilot)


class NumberModel(TBaseModel):

    _test_data: ClassVar = {"i": 5, "f": 0.1, "c": 15}

    i: int
    i_f: int = 0
    f: float
    c: int = Field(ge=10, le=115)


async def test_number_form():
    async with FormApp(model=NumberModel).run_test() as pilot:
        form = pilot.app.form
        inp = form.get_input("i")
        assert inp.form_data is None
        assert not inp.is_valid
        inp = form.get_input("i_f")
        assert inp.form_data == 0
        assert inp.is_valid
        inp = form.get_input("f")
        assert inp.form_data is None
        assert not inp.is_valid
        inp = form.get_input("c")
        assert not inp.is_valid
        inp.form_data = 9
        assert not inp.is_valid
        await load_and_check(pilot)


class BooleanModel(TBaseModel):
    _test_data: ClassVar = {"a": True, "a_n": False}

    a: bool
    # Quite an edge case...
    a_n: bool | None = None


async def test_bool_form():
    async with FormApp(model=BooleanModel).run_test() as pilot:
        form = pilot.app.form
        inp = form.get_input("a")
        assert pilot.app.converter.fields["a"].required
        assert inp.form_data is False
        assert inp.is_valid

        inp = form.get_input("a_n")
        assert not pilot.app.converter.fields["a_n"].required
        assert (
            inp.form_data is False
        ), "If the user does not touch the field, fallback to default"
        assert inp.is_valid
        await load_and_check(pilot, valid_as_is=True)


class ArrayStringModel(TBaseModel):
    _test_data: ClassVar = {"i": ["A", "B"]}

    # We do not load data for the tuple to check values since jsonschema
    # just knows the array type, but pydantic generates the same schema as for using list

    # i: tuple[Literal["A", "B"], ...]
    i: list[Literal["A", "B"]]


async def test_array_string_form():
    async with FormApp(model=ArrayStringModel).run_test() as pilot:
        form = pilot.app.form
        inp = form.get_input("i")
        assert pilot.app.converter.fields["i"].required
        assert inp.form_data == []
        assert inp.is_valid
        await load_and_check(pilot, valid_as_is=True)


class NestedModel(TBaseModel):
    _test_data: ClassVar = {
        "bools": BooleanModel._test_data,
        "strings": StringModel._test_data,
        "array_str": ArrayStringModel._test_data,
        "nums": NumberModel._test_data,
    }
    bools: BooleanModel
    strings: StringModel
    array_str: ArrayStringModel
    nums: NumberModel


async def test_nested_model():
    """Test all previous models as a nested one"""
    async with FormApp(model=NestedModel).run_test() as pilot:
        assert pilot.app.converter.fields["bools"].field_label == "BooleanModel"
        await load_and_check(pilot)


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

        # Load data into form
        for attr in ("first_name", "age"):
            assert form.get_input(attr).form_data is None
        await pilot.press("ctrl+l")

        for attr in ("first_name", "age", "country"):
            assert form.get_input(attr).form_data == user_data[attr]
        assert form.get_input("interests").form_data == user_data["interests"]
