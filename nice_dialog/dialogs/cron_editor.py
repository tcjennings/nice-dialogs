from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import islice
from typing import TYPE_CHECKING

from nicegui import ui
from nicegui.events import ValueChangeEventArguments
from pydantic import ValidationError
from pydantic_extra_types.cron import CronStr

MINUTE_OPTIONS = {
    "*": "Every (*)",
    "0": "HH:00",
    "*/15": "Every 15 minutes",
    "*/30": "Every 30 minutes",
}
"""Default set of cron-minute options."""

HOUR_OPTIONS = {
    "*": "Every (*)",
    "*/4": "Every 4 hours",
    "*/8": "Every 8 hours",
    "*/12": "Every 12 hours",
    "0": "Midnight",
    "12": "Noon",
}
"""Default set of cron-hour options."""

# January 1, 2023 was a Sunday
WEEKDAY_OPTIONS = {
    "*": "Every (*)",
    "1-5": "Weekdays",
    "0,6": "Weekends",
} | {str(i): datetime(2023, 1, i + 8, tzinfo=UTC).strftime("%A") for i in range(7)}
"""Default set of cron-day-of-week options."""

DAY_OPTIONS = {"*": "Every (*)"}
"""Default set of cron-day-of-month options."""

MONTH_OPTIONS = {"*": "Every (*)"} | {
    str(n): datetime(1970, n, 1, tzinfo=UTC).strftime("%B") for n in range(1, 13)
}
"""Default set of cron-month options (12 months)"""


@dataclass
class CronEditorModel:
    minute: str = "*"
    hour: str = "*"
    dom: str = "*"
    month: str = "*"
    dow: str = "*"
    cron: CronStr = field(init=False)
    is_valid: bool = field(init=False, default=True)

    def __post_init__(self) -> None:
        try:
            self.cron = CronStr(str(self))
        except (ValueError, ValidationError):
            self.is_valid = False

    def __repr__(self) -> str:
        return f"{self.minute} {self.hour} {self.dom} {self.month} {self.dow}"


class CronEditorDialog(ui.dialog):
    """NiceGUI Dialog displaying a Cron Expression Editor.

    Two action buttons are available: "Done" returns the current cron expression string;
    "Cancel" returns None.

    This dialog is created with the initial cron expression of "* * * * *". This
    expression can be replaced by calling the `reset` method with a new cron expression
    string.

    If an invalid cron expression is used to create or reset the dialog, a notification
    will alert the user, but the dialog will remain open in order to allow the user to
    correct the expression.

    The dialog cannot be closed with a positive action if the cron expression is
    invalid.

    The dialog's `reset` button can be used to set the cron expression back to an
    initial expression, which is whatever value was first used to create or set the
    dialog, which will be `* * * * *` in the default case.

    Attributes
    ----------
    dialog_title: str
        The title displayed at the top of the dialog.

    model: CronEditorModel
        A data model of the current cron expression, which includes string fields
        for each cron part and a `CronStr` object for validation and scheduling.

    initial_expression: str
        The initial cron expression used with the dialog when it is first opened.
    """

    dialog_title: str
    model: CronEditorModel
    initial_expression: str

    def __init__(
        self,
        *,
        dialog_title: str = "Cron Expression Editor",
    ) -> None:
        super().__init__()
        self.dialog_title = dialog_title
        self.initial_expression = ""
        self.reset()
        self.dialog_layout()

    if TYPE_CHECKING:

        def __await__(self) -> Generator[None, None, str | None]: ...

    def reset(self, cron: str | None = None) -> None:
        """Set the dialog to its initial state or to a provided cron expression by
        establishing or replacing the dialog's data model.

        If the provided cron expression is valid and contains novel tokens, those
        tokens will be added to the options of the relevant select components.

        This method is called when the dialog is first created, and can be called
        at any time to set the dialog to a specific new cron expression.
        """
        # Set the dialog's initial or fallback expression on first method call
        self.initial_expression = self.initial_expression or cron or "* * * * *"

        # Set the data model using the provided cron expression or the fallback
        cron = cron or self.initial_expression
        self.model = CronEditorModel(*cron.split())

        if self.model.is_valid:
            self.update_input_options()
        else:
            ui.notify(f"Invalid cron expression: {cron}", type="negative")

    def update_input_options(self) -> None:
        """Add novel cron expression tokens to the options of the select components.

        When used interactively, users may input arbitrary cron expression tokens,
        and the select element will accept them as new options.

        When the dialog is set programatically, as with the `reset` method, we have to
        manually add any novel tokens to those select options.
        """
        if TYPE_CHECKING:
            # all select options in this implementation are dicts
            assert isinstance(self.minute_select.options, dict)
            assert isinstance(self.hour_select.options, dict)
            assert isinstance(self.dom_select.options, dict)
            assert isinstance(self.month_select.options, dict)
            assert isinstance(self.dow_select.options, dict)

        # The module constants providing default options for each component are
        # never mutated, so are merged with the existing and novel options.
        try:
            if self.model.minute not in self.minute_select.options:
                self.minute_select.set_options(
                    {self.model.minute: self.model.minute}
                    | self.minute_select.options
                    | MINUTE_OPTIONS
                )

            if self.model.hour not in self.hour_select.options:
                self.hour_select.set_options(
                    {self.model.hour: self.model.hour}
                    | self.hour_select.options
                    | HOUR_OPTIONS
                )

            if self.model.dom not in self.dom_select.options:
                self.dom_select.set_options(
                    {self.model.dom: self.model.dom}
                    | self.dom_select.options
                    | DAY_OPTIONS
                )

            if self.model.month not in self.month_select.options:
                self.month_select.set_options(
                    {self.model.month: self.model.month}
                    | self.month_select.options
                    | MONTH_OPTIONS
                )

            if self.model.dow not in self.dow_select.options:
                self.dow_select.set_options(
                    {self.model.dow: self.model.dow}
                    | self.dow_select.options
                    | WEEKDAY_OPTIONS
                )
        except AttributeError:
            # When called before the dialog fully is rendered, some select components
            # may not yet be created.
            pass

    def dialog_layout(self) -> None:
        with self, ui.card():
            ui.label(self.dialog_title).classes("font-bold text-3xl")
            with ui.row().classes("flex w-full"):
                # cron expression display with copy button
                ui.code().classes(
                    "text-2xl/8 text-center",
                ).bind_content_from(
                    target_object=self,
                    target_name="model",
                    backward=lambda x: str(x),
                ).classes("flex-1").mark("cron-expression-display")
            with ui.row().classes("flex w-full"):
                # 5 x dropdown selectors
                self.minute_select = (
                    ui.select(
                        MINUTE_OPTIONS,
                        label="Minute",
                        with_input=True,
                        new_value_mode="add-unique",
                        on_change=self.handle_cron_change,
                    )
                    .classes("w-1/6 flex-1")
                    .bind_value(self, ("model", "minute"))
                    .mark(
                        "minute",
                    )
                )
                self.hour_select = (
                    ui.select(
                        HOUR_OPTIONS,
                        label="Hour",
                        with_input=True,
                        new_value_mode="add-unique",
                        on_change=self.handle_cron_change,
                    )
                    .classes("w-1/6 flex-1")
                    .bind_value(self, ("model", "hour"))
                    .mark(
                        "hour",
                    )
                )
                self.dom_select = (
                    ui.select(
                        DAY_OPTIONS,
                        label="Day",
                        with_input=True,
                        new_value_mode="add-unique",
                        on_change=self.handle_cron_change,
                    )
                    .classes("w-1/6 flex-1")
                    .bind_value(self, ("model", "dom"))
                    .mark("dom")
                )
                self.month_select = (
                    ui.select(
                        MONTH_OPTIONS,
                        label="Month",
                        with_input=True,
                        new_value_mode="add-unique",
                        on_change=self.handle_cron_change,
                    )
                    .classes("w-1/6 flex-1")
                    .bind_value(self, ("model", "month"))
                    .mark(
                        "month",
                    )
                )
                self.dow_select = (
                    ui.select(
                        WEEKDAY_OPTIONS,
                        label="Weekday",
                        with_input=True,
                        new_value_mode="add-unique",
                        on_change=self.handle_cron_change,
                    )
                    .classes("w-1/6 flex-1")
                    .bind_value(self, ("model", "dow"))
                    .mark("dow")
                )

            with ui.column().classes("w-full"):
                ui.label("Next 5 Runs").classes("text-sm text-gray-400 font-medium")
                self.show_next_runs()

            with ui.card_actions().classes("w-full align-left"):
                with ui.row().classes("flex w-full items-end"):
                    ui.button(
                        "Done",
                        color="positive",
                        on_click=lambda: self.submit(str(self.model)),
                    ).bind_enabled_from(self, ("model", "is_valid")).mark("done")
                    ui.button(
                        "Cancel",
                        color="negative",
                        on_click=lambda: self.submit(None),
                    ).mark("cancel")
                    ui.space()
                    ui.label("Reset").classes(
                        "text-sm text-negative font-medium cursor-pointer"
                    ).on("click", self.reset).tooltip(
                        f"{self.initial_expression}"
                    ).mark("reset")

    def handle_cron_change(self, event: ValueChangeEventArguments) -> None:
        """Callback handler from cron expression selectors"""
        try:
            self.model.cron = CronStr(str(self.model))
            self.model.is_valid = True
            self.show_next_runs.refresh()
        except (ValueError, ValidationError) as e:
            self.model.is_valid = False
            ui.notify(e, type="negative")

    @ui.refreshable_method
    def show_next_runs(self) -> None:
        """Refreshable method to display the next five events according to the
        current cron schedule.
        """
        now = datetime.now(tz=UTC)
        for i, run in enumerate(islice(self.model.cron.schedule(), 5)):
            until_run = run - now
            with ui.row().classes("w-full items-center"):
                ui.label(str(i + 1)).classes(
                    "text-xs bg-accent text-white px-2 py-1 rounded",
                )
                ui.label(f"{run:%a, %d-%b %Y at %I:%M %p %z}")
                ui.space()
                ui.label(
                    f"in {until_run.days} days, {until_run.seconds // 3600} hours",
                ).classes("text-sm text-gray-400")
