"""This module implements a simple Yes/No confirmation dialog with a few useful
extra options.
"""

from collections.abc import Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from nicegui import ui


@dataclass
class ConfirmationDialogModel:
    icon: str = "warning"
    icon_color: str = "warning"
    yes_button_label: str = "Yes"
    yes_button_color: str = "positive"
    no_button_label: str = "No"
    no_button_color: str = "negative"
    remember: bool = False
    yes_return_value: Any = True
    no_return_value: Any = False
    show_remember_checkbox: bool = True
    remember_checkbox_color: str = "accent"


class ConfirmationDialog(ui.dialog):
    """A NiceGUI dialog box presenting a simple yes/no confirmation.

    Other than the required `dialog_title` and `message`, any keyword arguments are
    passed along to the dialog's data model, which can control the wording and
    color of the Yes/No options, as well as the displayed icon, and whether the
    "remember my choice" checkbox is enabled.

    When awaited, the dialog will always return a tuple of the configured return value
    of the selected button and the state of the "remember" checkbox, irrespective
    of whether it was displayed.

    By default, the "yes"/"no" buttons return a bool `True`/`False` respectively,
    but these values can be customized via the data model.
    """

    dialog_title: str
    message: str
    model: ConfirmationDialogModel

    def __init__(
        self,
        *,
        dialog_title: str = "Confirmation",
        message: str = "Are you sure?",
        **kwargs: Any,
    ) -> None:
        """Initialize the dialog and its components."""
        super().__init__()
        self.dialog_title = dialog_title
        self.message = message
        self.model = ConfirmationDialogModel(**kwargs)
        self.dialog_layout()

    if TYPE_CHECKING:

        def __await__(self) -> Generator[None, None, tuple[Any, bool]]: ...

    def dialog_layout(self) -> None:
        with self, ui.card():
            ui.label(self.dialog_title).classes("font-bold text-3xl")
            with ui.row().classes("w-full"):
                ui.icon(self.model.icon, size="4rem", color=self.model.icon_color)
                ui.label(self.message)
            with ui.card_actions().classes("w-full align-left"):
                with ui.row().classes("flex w-full"):
                    ui.button(
                        self.model.yes_button_label,
                        color=self.model.yes_button_color,
                        on_click=lambda: self.submit(
                            (self.model.yes_return_value, self.model.remember)
                        ),
                    ).mark("confirm_yes")
                    ui.button(
                        self.model.no_button_label,
                        color=self.model.no_button_color,
                        on_click=lambda: self.submit(
                            (self.model.no_return_value, self.model.remember)
                        ),
                    ).mark("confirm_no")
                with ui.row().classes("flex w-full justify-end"):
                    ui.checkbox("Don't ask me again").classes("scale-75").props(
                        f"color={self.model.remember_checkbox_color}"
                    ).bind_value_to(self, ("model", "remember")).bind_visibility_from(
                        self, ("model", "show_remember_checkbox")
                    ).tooltip("Remember my preference for this confirmation.")
