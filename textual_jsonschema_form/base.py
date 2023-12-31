from __future__ import annotations
from dataclasses import dataclass

from rich.text import Text, TextType
from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import Reactive, var
from textual.widgets import Button, Input, Rule, Static, Tree
from textual.widgets._tree import TreeNode

from .converter import TextualArrayParams, TextualObjectParams
from .core import JSONFieldParametersBase
from .fields import BaseForm, WithHiddenClass


class FormContainer(BaseForm):
    """This widget contains the actual form using the widgets of the converter. How to display the field is partly
    delegated to this class in terms of adding a label field and a field that shows errors of validators.
    This widget must also implement all event listeners for all form-field widgets."""

    SUBFORM_CONTAINER_WIDGET = BaseForm
    INPUT_VALIDATE_ON = ("changed", "submitted")

    DEFAULT_CSS = """
    FormContainer {
      max-width: 100;
    }
    FormContainer Input.-valid:focus {
      border: tall $success;
    }
    FormContainer #jsonform-submit {
      dock: bottom;
    }
    .hidden {
      display: none;
    }
    """

    @dataclass
    class FormSubmitted(Message):
        form_data: dict

    # TODO: Don't know how to refresh the whole thing when the model changes
    # model: Reactive[TextualObjectParams | None] = var(None)

    def __init__(
        self,
        model: TextualObjectParams,
        form_data: dict | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        # The id can not be None, otherwise the query of the immediate children does not work
        id_ = id or self.__class__.__name__
        super().__init__(name=name, id=id_, classes=classes, disabled=disabled)
        self.model = model
        self._form_data = form_data

    def compose(self):
        if not self.model or not self.model.fields:
            yield Static("This form is emtpy")
            return
        yield from self._compose(self.model)

    def watch_model(self):
        pass

    def get_field_label(self, field_id: str):
        return self.query_one(f"#{FormContainer.container_id(field_id)}").query_one(
            FormContainer.FORM_LABEL_WIDGET
        )

    def get_input(self, input_id):
        def iter_fields(fields):
            for field in fields:
                if field.id == input_id:
                    return field
                elif hasattr(field, "form_input_fields"):
                    iter_fields(field.form_input_fields)

        return iter_fields(self.form_input_fields)

    def compose_container_widgets(
        self,
        name: str,
        field,
        parent_id: str | None = None,
        parent_label: str | None = None,
    ):
        id_ = self.field_id(name, parent_id)
        yield self._label(
            self.join_labels(parent_label, field.field_label), field.required
        )
        opts = field.get_options()
        opts["id"] = id_
        opts["classes"] = self.FORM_INPUTS_CLASS
        widget = field.get_factory()
        yield widget(**opts)
        if field.type not in {"boolean"}:
            yield self._validation_info(id_)

    def _compose(
        self, model, parent_id: str | None = None, parent_label: str | None = None
    ) -> ComposeResult:
        for name, field in model.fields.items():
            id_ = self.field_id(name, parent_id)
            if field.type == "object":
                with self.SUBFORM_CONTAINER_WIDGET(
                    id=id_, classes=self.SUB_FORM_CONTAINER_CLASS
                ):
                    yield from self._compose(
                        model=field,
                        parent_id=id_,
                        parent_label=self._label_text(
                            field.field_label, field.required
                        ),
                    )
                continue
            if field.type == "array" and not field.choices:
                yield field.get_factory()(
                    id=self.container_id(id_),
                    parent_id=parent_label,
                    parent_label=parent_label,
                    classes=self.FORM_INPUTS_CLASS,
                    **field.get_options(),
                )
                continue
            with self.FIELD_CONTAINER_WIDGET(
                id=self.container_id(id_), classes=self.FORM_INPUTS_CONTAINER_CLASS
            ):
                yield from self.compose_container_widgets(
                    name, field, parent_id, parent_label
                )
        if parent_id:
            return
        with self.FIELD_CONTAINER_WIDGET(id=self.FORM_SUBMIT_CONTAINER_ID):
            yield Rule()
            yield Button("Submit", id="submit", variant="success")

    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        if not event.validation_result or not event.input.id:
            return
        if not event.validation_result.is_valid:
            failures = event.validation_result.failure_descriptions
        else:
            failures = []
        self.update_info_field(failures, event.input.id)

    @on(Button.Pressed, "#submit")
    def submit_form(self, event: Button.Pressed):
        if not self.is_valid:
            event.button.variant = "error"
            return
        event.button.variant = "success"
        self.post_message(self.FormSubmitted(self.form_data))


class JsonSchemaTree(Tree[JSONFieldParametersBase], WithHiddenClass):
    """A jsonschema navigator tree to toggle on and off sub-forms for very large schemas"""

    OBJECT_SYM: str = ""
    ARRAY_SYM: str = "[] "
    ARRAY_INDEX: bool = False

    data: Reactive[TextualObjectParams | None] = var(None)

    def __init__(
        self,
        label: TextType,
        data: TextualObjectParams | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(
            label=label, data=None, name=name, id=id, classes=classes, disabled=disabled
        )
        self._data = data

    def on_mount(self):
        if self._data:
            self.add_schema(self.root, self._data, root_name=self._data.field_name)

    def watch_data(self):
        if not self.data:
            return
        self.clear()
        self.add_schema(self.root, self.data, root_name=self.data.field_name)

    @classmethod
    def add_schema(
        cls, node: TreeNode, model: TextualObjectParams, root_name: str = "Form"
    ) -> None:
        def assemble_label(*labels):
            return Text.assemble(*(Text.from_markup(la) for la in labels if la))

        def add_node(name: str, node: TreeNode, model: JSONFieldParametersBase) -> None:
            label = f"{name}[red]^[/red]" if model.required else name
            if isinstance(model, TextualObjectParams):
                if not model.fields:
                    return
                node.set_label(assemble_label(cls.OBJECT_SYM, label))
                for name, field in model.fields.items():
                    new_node = node.add("")
                    add_node(name, new_node, field)
            elif isinstance(model, TextualArrayParams):
                if isinstance(model.subfield, TextualObjectParams):
                    raise NotImplementedError("Arrays of objects not supported yet")
                node.set_label(assemble_label(cls.ARRAY_SYM, label))
                node.allow_expand = False
            else:
                node.allow_expand = False
                node.set_label(label)

        add_node(root_name, node, model)
