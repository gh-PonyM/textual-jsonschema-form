from collections.abc import Callable, Iterable
from datetime import date, datetime
from functools import partial
from pathlib import Path
from typing import Any, ClassVar, Generator, Protocol

from rich.highlighter import Highlighter
from textual import on
from textual.containers import Container, Horizontal
from textual.reactive import Reactive, var
from textual.suggester import Suggester
from textual.validation import Function, Validator
from textual.widget import Widget
from textual.widgets import (
    Button,
    Input,
    Label,
    Pretty,
    Select,
    SelectionList,
    Switch,
)
from textual.widgets._input import InputType, InputValidationOn
from textual.widgets._select import NoSelection

from .validators import (
    NumberRange,
    empty_value,
    example_date,
    is_absolute_path,
    valid_date_by_format,
    valid_file_path,
    valid_folder,
)


def date_to_string(value: date | datetime, fmt: str) -> str:
    return value.strftime(fmt)


class WithHiddenClass(Widget):
    """A base for items that can be hidden by a class using a reactive attribute"""

    HIDDEN_CLASS: str = "hidden"
    show: Reactive[bool] = var(True)

    def watch_show(self, show: bool):
        self.set_class(not show, self.HIDDEN_CLASS)

    def toggle_show(self):
        self.show = not self.show

    def hide(self):
        self.show = False

    def unhide(self):
        self.show = True


class ValidationInfo(Pretty, WithHiddenClass):
    """Widget to be used for to show validation info near a field"""

    pass


# TODO: Use the Protocol rather than this class inheriting from Widget
class Field(Protocol):
    """Field to use for custom widgets to be used by the form"""

    @property
    def form_data(self) -> Any: ...

    @form_data.setter
    def form_data(self, value): ...

    @property
    def is_valid(self) -> bool:
        """Runs internal validation function if not yet validated and returns the result"""
        ...

    def validated(self) -> bool:
        """Flag to indicate whether the field ever was touched and validated"""
        ...


class FormField(Container):
    """Structural container to hold label, input and eventual validation info field"""

    DEFAULT_CSS = """
    FormField {
      height: auto;
      padding: 0 1;
    }
    FormField Label {
      padding: 1 1 1 1;
    }

    FormField ValidationInfo {
      padding: 1 1 1 1;
    }
    """

    pass


class FieldLabel(Label):
    """A label for an input field"""

    pass


class ActionBtn(Button):
    """An icon like Button to add to a form field"""

    DEFAULT_CSS = """
    ActionBtn {
      padding: 0;
      min-width: 0;
      border: none;
      color: $text;
    }

    ActionBtn:hover {
      background: $panel-darken-2;
      color: $secondary;
      border: none;
    }
    """


class BaseForm(Container):
    """Structural container to hold a subform."""

    DEFAULT_CSS = """
    BaseForm {
      height: auto;
    }
    """

    FORM_INPUTS_CLASS: ClassVar[str] = "jsonform-input"
    FORM_INPUTS_CONTAINER_CLASS: ClassVar[str] = "jsonform-input-container"
    SUB_FORM_CONTAINER_CLASS: ClassVar[str] = "jsonform-subform"
    FORM_SUBMIT_CONTAINER_ID: ClassVar[str] = "jsonform-submit"
    ID_JOIN_SYMBOL: ClassVar[str] = "-"
    FIELD_CONTAINER_WIDGET = FormField
    FORM_LABEL_WIDGET = FieldLabel

    @property
    def form_input_query(self) -> str:
        """Query string for all inputs fields that are immediate children"""
        return (
            f"#{self.id} > .{self.FORM_INPUTS_CONTAINER_CLASS} >"
            f" .{self.FORM_INPUTS_CLASS}, #{self.id} > .{self.SUB_FORM_CONTAINER_CLASS}"
        )

    @classmethod
    def data_key(cls, input_id: str) -> str:
        """Converts the field_id back to the original jsonschema key"""
        return input_id.split(cls.ID_JOIN_SYMBOL)[-1]

    @classmethod
    def join_labels(cls, *labels):
        return " > ".join(la for la in labels if la)

    @classmethod
    def container_id(cls, field_id: str):
        return cls.join_ids(field_id, "container")

    @classmethod
    def field_id(cls, name: str, parent_id: str | None = None):
        """Constructs the field id using the parent id"""
        return cls.join_ids(parent_id, name)

    @classmethod
    def join_ids(cls, *ids) -> str:
        """Joins all valid id's together"""
        return cls.ID_JOIN_SYMBOL.join(id_ for id_ in ids if id_)

    @property
    def form_input_fields(self):
        """Returns a dom query of all immediate children, that follow the protocol of a Field"""
        # TODO: Don't know how to type-annotate this
        return self.query(self.form_input_query)

    @property
    def form_data(self):
        """Returns the data from all fields and sub-forms"""
        return {self.data_key(d.id): d.form_data for d in self.form_input_fields}

    @form_data.setter
    def form_data(self, data: dict):
        """Converts and populates data into the form"""
        for field in self.form_input_fields:
            key = self.data_key(field.id)
            if key not in data:
                continue
            field.form_data = data[key]

    @property
    def is_valid(self) -> bool:
        """Returns in all fields are valid. Using the tuple here to makes sure all fields are called. The field
        should be validated if it wasn't already when calling this property."""
        return all(tuple(d.is_valid for d in self.form_input_fields))

    def validated(self) -> bool:
        return True

    def _validation_id(self, input_id):
        """Returns the id of the validation field for a given input field id"""
        return f"validate-{input_id}"

    def _validation_info(self, input_id, hidden: bool = True):
        """Returns an instance of the validation field"""
        o = ValidationInfo([], id=self._validation_id(input_id))
        # Class to hide is handled by reactive attribute
        o.show = not hidden
        return o

    def validation_fields(self):
        """A DOM query that returns all validation info fields that are currently shown"""
        for f in self.query(ValidationInfo):
            if f.show:
                yield f

    def validation_errors(self) -> Generator[tuple[str, list[str]], None, None]:
        """Returns the validation errors as list for each field with a shown validation field"""
        for f in self.validation_fields():
            yield f.id, f._renderable._object

    def info_field(self, input_id: str) -> ValidationInfo:
        """Returns the validation info field for a given input field id"""
        return self.query_one(f"#{self._validation_id(input_id)}", ValidationInfo)

    def update_info_field(self, failures: list[str], input_id: str):
        """Update the validation info field using a list of failure messages"""
        if not failures:
            self.info_field(input_id).hide()
            return
        field = self.info_field(input_id)
        field.update(failures)
        field.unhide()

    @classmethod
    def _label_text(cls, label: str, required: bool = True):
        """Constructs a label for a optional or required field"""
        return f"{label}[red]^[/red]" if required else label

    @classmethod
    def _label(cls, label: str, required: bool = True):
        """Returns an instance of a label field"""
        return cls.FORM_LABEL_WIDGET(cls._label_text(label, required))


class FormInput(Input):
    """The base input class"""

    INPUT_DATE_FORMAT: ClassVar[str] = "%d.%m.%Y"
    INPUT_DATETIME_FORMAT: ClassVar[str] = "%d.%m.%Y %H:%M"
    INPUT_VALIDATE_ON: ClassVar[Iterable[InputValidationOn] | None] = ("changed",)
    ALWAYS_REVALIDATE_FORMATS: ClassVar[set[str]] = {
        "path",
        "directory-path",
        "file-path",
    }

    def __init__(
        self,
        value: str | None = None,
        placeholder: str = "",
        highlighter: Highlighter | None = None,
        password: bool = False,
        *,
        restrict: str | None = None,
        type: InputType = "text",
        max_length: int = 0,
        suggester: Suggester | None = None,
        validators: Validator | Iterable[Validator] | None = None,
        validate_on: Iterable[InputValidationOn] | None = None,
        valid_empty: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        format: str | None = None,
        minimum: int | None = None,
        maximum: int | None = None,
        exclusive_minimum: int | None = None,
        exclusive_maximum: int | None = None,
    ) -> None:
        # If no validators are given and the valid_empty is False, no validation occurs
        # Subsequent validator can pass when an empty value is given, e.g. for path validation
        if not validators and not valid_empty:
            validators = [Function(empty_value, "Field can not be empty")]
        super().__init__(
            value,
            placeholder,
            highlighter,
            password,
            restrict=restrict,
            type=type,
            max_length=max_length,
            suggester=suggester,
            validate_on=validate_on or self.INPUT_VALIDATE_ON,
            validators=validators,
            valid_empty=valid_empty,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        if format:
            validator = self.get_validator_for_format(format)
            if not validator:
                raise NotImplementedError(f"format {format} not supported")
            self.validators.append(validator)
        if any(
            f is not None
            for f in (exclusive_minimum, exclusive_maximum, minimum, maximum)
        ):
            self.validators.append(
                NumberRange(minimum, maximum, exclusive_minimum, exclusive_maximum)
            )
        self.format = format

    @classmethod
    def get_validator_for_format(cls, fmt: str) -> Validator | None:
        """Returns the validator for a specific format. If the field is optional, use a validator that
        returns True on empty values"""
        return {
            "date": Function(
                partial(valid_date_by_format, date_fmt=cls.INPUT_DATE_FORMAT),
                "Is not a valid date of format"
                f" '{example_date(cls.INPUT_DATE_FORMAT)}'",
            ),
            "date-time": Function(
                partial(valid_date_by_format, date_fmt=cls.INPUT_DATETIME_FORMAT),
                "Is not a valid date of format"
                f" '{example_date(cls.INPUT_DATETIME_FORMAT)}'",
            ),
            "file-path": Function(
                valid_file_path,
                "File does not exist",
            ),
            "directory-path": Function(
                valid_folder,
                "Directory does not exist",
            ),
            "path": Function(
                is_absolute_path,
                "Use absolute paths or '~' to expand the current user",
            ),
        }.get(fmt)

    @classmethod
    def _getter_formatter(cls, fmt: str | None, default: Callable[[str], Any]):
        """Formatters for conversion from field value to the correct jsonschema type and format."""
        return {
            "number": float,
            "integer": int,
            "path": Path,
            "file-path": Path,
            "directory-path": Path,
            "date": lambda x: datetime.strptime(x, cls.INPUT_DATETIME_FORMAT).date(),
            "date-time": lambda x: datetime.strptime(x, cls.INPUT_DATETIME_FORMAT),
            None: default,
        }.get(fmt, default)

    @classmethod
    def _setter_formatter(cls, fmt: str | None, default: Callable[[Any], str]):
        """Returns a special setter function that is responsible to populate the field value with
        the string representation of this data. The representation must be compatible with validators if any.
        """
        return {
            "date": partial(date_to_string, fmt=cls.INPUT_DATE_FORMAT),
            "date-time": partial(date_to_string, fmt=cls.INPUT_DATETIME_FORMAT),
            "path": lambda p: str(p),
            "file-path": lambda p: str(p),
            "directory-path": lambda p: str(p),
            None: lambda x: str(x),
        }.get(fmt, default)

    def validated(self) -> bool:
        """Checks if the field has any validators. Some formats are always re-validated on submit,
        e.g. for a file path"""
        if not self.validate_on and not self.validators:
            return True
        if self.format in self.ALWAYS_REVALIDATE_FORMATS:
            return False
        classes = self.classes
        if "-valid" in classes or "-invalid" in classes:
            return True
        return False

    @property
    def is_valid(self) -> bool:
        """Checks if the field is valid, calling the 'validate' if the field needs to be re-validated"""
        if not self.validated():
            self.validate(self.value)
        return super().is_valid

    @property
    def form_data(self):
        return (
            self._getter_formatter(self.format or self.type, lambda x: x)(self.value)
            if self.value != ""
            else None
        )

    @form_data.setter
    def form_data(self, data):
        if data is None:
            self.value = ""
            return
        self.value = self._setter_formatter(self.format, lambda x: str(x))(data)


class FormSwitch(Switch):
    """A Switch Widget implementation"""

    @property
    def form_data(self) -> bool:
        return self.value

    @form_data.setter
    def form_data(self, data):
        self.value = bool(data)

    @property
    def is_valid(self) -> bool:
        return True

    def validated(self) -> bool:
        return True


class FormStrSelect(Select[str]):
    """A Select Widget implementation for strings"""

    @property
    def form_data(self) -> str | None:
        if isinstance(self.value, NoSelection) or self.value == Select.BLANK:
            return None
        return self.value

    @form_data.setter
    def form_data(self, data):
        self.value = data

    @property
    def is_valid(self) -> bool:
        return True

    def validated(self) -> bool:
        return True


class FormStrMultiSelect(SelectionList[str]):
    """A SelectionList implementation for strings"""

    @property
    def is_valid(self) -> bool:
        return True

    def validated(self) -> bool:
        return True

    @classmethod
    def from_obj(
        cls, data: Iterable[str], options: Iterable[str], **kwargs
    ) -> "FormStrMultiSelect":
        choices: tuple[tuple[str, str] | tuple[str, str, bool], ...] = tuple(
            (t, t, True) if t in (data or []) else (t, t) for t in options
        )
        return cls(*choices, **kwargs)

    @property
    def form_data(self) -> list[str]:
        return self.selected

    @form_data.setter
    def form_data(self, data):
        self.deselect_all()
        for item in data:
            self.select(item)


class ArrayField(FormField):
    # TODO: How to annotate the callable using the protocol, but complains it needs a widget

    ACTION_BTN_CLASS_ADD: ClassVar[str] = "jsonform-action-btn-add"
    ACTION_BTN_CLASS_REMOVE: ClassVar[str] = "jsonform-action-btn-remove"

    def __init__(
        self,
        id: str,
        subfield_factory: Callable,
        label: str,
        required: bool,
        data: Iterable | None = None,
        parent_id: str | None = None,
        parent_label: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(
            id=id,
            classes=classes or BaseForm.FORM_INPUTS_CONTAINER_CLASS,
        )
        self.subfield_factory = subfield_factory
        self.label = label
        self.data = data
        self.parent_id = parent_id
        self.parent_label = parent_label
        self.required = required

    @property
    def form_input_query(self) -> str:
        """Query string for all inputs fields that are immediate children"""
        return f"#{self.id} > .{BaseForm.FORM_INPUTS_CLASS}"

    @property
    def form_input_fields(self):
        """Returns a dom query of all immediate children, that follow the protocol of a Field"""
        return self.query(self.form_input_query)

    def on_mount(self):
        if self.data:
            self.add_input_fields(self.data)

    @property
    def form_data(self):
        """Returns the data from all fields and sub-forms"""
        return {BaseForm.data_key(d.id): d.form_data for d in self.form_input_fields}

    @form_data.setter
    def form_data(self, data: Iterable):
        self.remove_children()
        self.add_input_fields(data)

    def add_input_field(self, field_data: Any):
        field = self.subfield_factory(classes=BaseForm.FORM_INPUTS_CLASS)
        if field_data:
            field.form_data = field_data
        self.mount(
            Horizontal(field, ActionBtn("-", classes=self.ACTION_BTN_CLASS_REMOVE))
        )

    def add_input_fields(self, data: Iterable):
        for item in data:
            self.add_input_field(item)

    @classmethod
    def action_add_btn_id(cls, field_id: str):
        return f"{field_id}-add-field"

    def compose(self):
        with Horizontal():
            yield BaseForm._label(
                BaseForm.join_labels(self.parent_label, self.label), self.required
            )
            yield ActionBtn(
                "+",
                id=self.action_add_btn_id(self.id),  # type: ignore
                classes=self.ACTION_BTN_CLASS_ADD,
            )
        yield self.subfield_factory(classes=BaseForm.FORM_INPUTS_CLASS)

    @on(ActionBtn.Pressed)
    def handle_action_buttons(self, event: ActionBtn.Pressed):
        if self.ACTION_BTN_CLASS_ADD in event.button.classes:
            self.add_input_field(None)
        elif self.ACTION_BTN_CLASS_REMOVE in event.button.classes:
            event.button.parent.query_one(f".{BaseForm.FORM_INPUTS_CLASS}").remove()  # type: ignore

    @property
    def is_valid(self) -> bool:
        """Returns in all fields are valid. The field should be validated if it wasn't already when
        calling this property."""
        return all(tuple(d.is_valid for d in self.form_input_fields))

    def validated(self) -> bool:
        return True
