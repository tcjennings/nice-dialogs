from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from enum import Enum, EnumType, IntFlag, StrEnum, auto
from functools import partial
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any, Literal, get_args, get_origin

from nicegui import ui

# SortableJS support is added in NiceGUI 3.11
if TYPE_CHECKING:
    if find_spec("nicegui.elements.sortable") is not None:
        from nicegui.events import (  # type: ignore[attr-defined, unused-ignore]
            SortableEventArguments,
        )
    else:
        type SortableEventArguments = Any  # type: ignore[no-redef]


SORTABLE_AVAILABLE = find_spec("nicegui.elements.sortable") is not None
"""Module-level constant for whether the sortable component is available, which
dependson NiceGUI >= 3.11.
"""


class DialogOptions(IntFlag):
    """Dialog option flags."""

    ALLOW_SORTABLE = auto()
    """Whether the label list can be sorted by dragging and dropping."""

    USE_DEFAULT_VALIDATOR = auto()
    """Whether to use the default validator, which checks that fields are not empty."""


@dataclass
class LabelMakerModel:
    """Data model for the label maker dialog."""

    num_inputs: int = 2
    inputs: list[ui.input | ui.select] = field(default_factory=list)
    input_labels: list[str] = field(default_factory=list)
    values: list[tuple[str, ...]] = field(default_factory=list)
    validators: list[dict[str, Any]] = field(default_factory=list)
    value_types: list[type | StrEnum | list[str]] = field(default_factory=list)
    options: DialogOptions = field(default_factory=lambda: DialogOptions(0))
    default_validator: dict[str, Any] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        """For fields that are expected to be the same length as the number of
        inputs, fill in any missing values with defaults.
        """
        if len(self.input_labels) < self.num_inputs:
            # fill in any missing input labels with empty label
            for _ in range(len(self.input_labels), self.num_inputs):
                self.input_labels.append("")
        if len(self.value_types) < self.num_inputs:
            # fill in any missing value types with str
            for _ in range(len(self.value_types), self.num_inputs):
                self.value_types.append(str)

    @property
    def all_valid(self) -> bool:
        """Returns whether all input fields currently have valid values."""
        return all([_input.validate() for _input in self.inputs])


class LabelMakerDialog(ui.dialog):
    """The labelmaker dialog is an interface for applying label-based metadata
    to an arbitrary object. The default type of "label" is a key-value pair, but
    the dialog can be initialized with any number of input fields, and the return
    value is a list of tuples. This leaves the formatting of the labels up to the
    caller.

    Labels are displayed in a list, can be reordered by dragging and dropping, and
    can be removed by clicking a delete button.
    """

    dialog_title: str
    model: LabelMakerModel

    def __init__(
        self,
        dialog_title: str = "List Editor",
        *,
        allow_sorting: bool = True,
        use_default_validator: bool = True,
        **kwargs: Any,
    ) -> None:
        """Dialog class for creating and editing sets of labels.

        Other than `dialog_title`, all parameters are passed to the `LabelMakerModel`
        dataclass, including seed values for the label list and input field validators.

        By default, the input fields are simple text inputs for string values,
        but if the `value_types` parameter is set to a list of types and the type
        at position *n* is a `Literal`, the input at position *n* will be a select
        component with options generated from the matching `Literal`. Likewise,
        if this type is an `Enum`, then the input will be a select with options
        generated from the enum names (or values, in the case of a `StrEnum`).
        Finally if the type is a list of strings, these will be used as options
        for a select input.

        Once populated, the dialog handles all values as strings, and results
        are not cast back to the original types.
        """
        super().__init__()
        self.dialog_title = dialog_title
        self.model = LabelMakerModel(**kwargs)

        if SORTABLE_AVAILABLE and allow_sorting:
            self.model.options |= DialogOptions.ALLOW_SORTABLE

        if use_default_validator:
            self.model.options |= DialogOptions.USE_DEFAULT_VALIDATOR
            self.model.default_validator["Input must not be empty"] = lambda v: (
                len(v) > 0 if v is not None else False
            )

        self.dialog_layout()

    if TYPE_CHECKING:

        def __await__(self) -> Generator[None, None, list[tuple[str, ...]] | None]: ...

    def dialog_layout(self) -> None:
        with self, ui.card().classes("w-[96vw] max-w-[96vw]"):
            ui.label(self.dialog_title).classes("font-bold text-3xl")

            with ui.row().classes("flex w-full items-start"):
                # an input or select field for each label component
                for i in range(0, self.model.num_inputs):
                    input_element: ui.input | ui.select | None = None
                    value_type = self.model.value_types[i]
                    input_label = self.model.input_labels[i]

                    if get_origin(value_type) is Literal:
                        input_element = ui.select(
                            options=list(get_args(value_type)),
                        )
                    elif isinstance(value_type, EnumType) and issubclass(
                        value_type, StrEnum
                    ):
                        input_element = ui.select(
                            options=[option for option in value_type],
                        )
                    elif isinstance(value_type, EnumType) and issubclass(
                        value_type, Enum
                    ):
                        input_element = ui.select(
                            options=[option.name for option in value_type],
                        )
                    elif isinstance(value_type, list):
                        input_element = ui.select(options=value_type)
                    else:
                        # All other cases result in an ordinary text input
                        input_element = ui.input()

                    if TYPE_CHECKING:
                        assert input_element is not None

                    input_element.classes(add="flex-1").props("clearable").set_label(
                        input_label
                    )

                    # Create a non-mutating copy of the provided validator for
                    # the input and optionally apply the default validators.
                    validators: dict[str, Any]
                    try:
                        validators = {**self.model.validators[i]}
                    except IndexError:
                        validators = {}

                    if DialogOptions.USE_DEFAULT_VALIDATOR in self.model.options:
                        validators |= self.model.default_validator

                    input_element.validation = validators

                    input_element.mark(f"input_{i}")
                    self.model.inputs.append(input_element)

                ui.button(
                    icon="add", on_click=self.handle_add_label, color="accent"
                ).props("fab-mini").tooltip("Add").bind_enabled_from(
                    self, ("model", "all_valid")
                ).mark("add")

            ui.separator()

            with ui.column().classes("w-full overflow-y-auto") as self.labels_column:
                self.labels_container()

            ui.separator()

            with ui.card_actions().classes("w-full"):
                ui.button(
                    "Submit",
                    on_click=lambda: self.submit(self.model.values),
                    color="positive",
                ).mark("submit")
                ui.button(
                    "Cancel", on_click=lambda: self.submit(None), color="negative"
                ).mark("cancel")

    async def handle_add_label(self) -> None:
        label_value_tuple = tuple(str(_input.value) for _input in self.model.inputs)
        self.model.values.append(label_value_tuple)
        for _input in self.model.inputs:
            _input.value = ""
        self.labels_container.refresh()

    @ui.refreshable_method
    def labels_container(self) -> None:
        """Creates the content of the label list container. Each list element
        has a delete button.
        """
        with ui.list().classes("w-full") as list_container:
            for i, label_tuple in enumerate(self.model.values):
                delete_callback = partial(self.handle_delete_label, i)
                click_callback = partial(self.handle_item_click, i)
                with ui.item().classes("w-full").mark(f"label_{i}"):
                    with ui.item_section().props("side"):
                        ui.icon("drag_indicator").classes(
                            "handle cursor-grab active:cursor-grabbing"
                        ).bind_visibility_from(
                            self,
                            ("model", "options"),
                            backward=lambda o: DialogOptions.ALLOW_SORTABLE in o,
                        )
                    with ui.item_section().props():
                        ui.chip(
                            " : ".join(label_tuple), on_click=click_callback
                        ).classes("w-full flex-1 secondary text-white")
                    with ui.item_section().props("side"):
                        ui.icon(
                            name="delete",
                            color="warning",
                        ).on("click", delete_callback).props("flat").tooltip(
                            "Delete"
                        ).mark("delete")

        # We only make the list sortable if the option is enabled, which is
        # possible only when nicegui supports it, but for type checking
        # we also assert that the make_sortable method is present anyway
        if TYPE_CHECKING:
            assert hasattr(list_container, "make_sortable")

        if DialogOptions.ALLOW_SORTABLE in self.model.options:
            list_container.make_sortable(handle=".handle", on_end=self.handle_sortable)

    def handle_delete_label(self, index: int) -> None:
        """Removes the label set at the specified index from the model."""
        self.model.values.pop(index)
        self.labels_container.refresh()

    def handle_item_click(self, index: int) -> None:
        """Repopulates the input fields with the values of the clicked label set."""
        try:
            for i, _input in enumerate(self.model.inputs):
                _input.value = self.model.values[index][i]
        except IndexError:
            ui.notify(
                "An error occurred while updating the input fields.", color="negative"
            )

    def handle_sortable(self, e: SortableEventArguments) -> None:
        """Updates the model when the label list is sorted on the client side."""
        # If the event doesn't support the necessary attributes, make this a no-op.
        if not hasattr(e, "old_index") or not hasattr(e, "new_index"):
            return

        try:
            shifting_item = self.model.values.pop(e.old_index)
            self.model.values.insert(e.new_index, shifting_item)
        except IndexError:
            ui.notify("An error occurred while sorting the list.", color="negative")
