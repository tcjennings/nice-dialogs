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
    "*/15": "*/15",
    "*/30": "*/30",
    0: "0",
}
"""Default set of cron-minute options."""

HOUR_OPTIONS = {
    "*": "Every (*)",
    "*/2": "*/2",
    "*/8": "*/8",
    "*/12": "*/12",
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
        initial_expression: str = "* * * * *",
    ) -> None:
        super().__init__()
        self.dialog_title = dialog_title
        self.initial_expression = initial_expression
        self.reset()
        self.dialog_layout()

    if TYPE_CHECKING:

        def __await__(self) -> Generator[None, None, str | None]: ...

    def reset(self, cron: str | None = None) -> None:
        """Set the dialog to its initial state."""
        cron = cron or self.initial_expression
        self.model = CronEditorModel(*cron.split())

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
                ui.select(
                    MINUTE_OPTIONS,
                    label="Minute",
                    with_input=True,
                    new_value_mode="add-unique",
                    on_change=self.handle_cron_change,
                ).classes("w-1/6 flex-1").bind_value(self, ("model", "minute")).mark(
                    "minute",
                )
                ui.select(
                    HOUR_OPTIONS,
                    label="Hour",
                    with_input=True,
                    new_value_mode="add-unique",
                    on_change=self.handle_cron_change,
                ).classes("w-1/6 flex-1").bind_value(self, ("model", "hour")).mark(
                    "hour",
                )
                ui.select(
                    DAY_OPTIONS,
                    label="Day",
                    with_input=True,
                    new_value_mode="add-unique",
                    on_change=self.handle_cron_change,
                ).classes("w-1/6 flex-1").bind_value(self, ("model", "dom")).mark("dom")
                ui.select(
                    MONTH_OPTIONS,
                    label="Month",
                    with_input=True,
                    new_value_mode="add-unique",
                    on_change=self.handle_cron_change,
                ).classes("w-1/6 flex-1").bind_value(self, ("model", "month")).mark(
                    "month",
                )
                ui.select(
                    WEEKDAY_OPTIONS,
                    label="Weekday",
                    with_input=True,
                    new_value_mode="add-unique",
                    on_change=self.handle_cron_change,
                ).classes("w-1/6 flex-1").bind_value(self, ("model", "dow")).mark("dow")

            with ui.column().classes("w-full"):
                ui.label("Next 5 Runs").classes("text-sm text-gray-400 font-medium")
                self.show_next_runs()

            with ui.card_actions().classes("w-full align-left"):
                with ui.row().classes("flex w-full items-end"):
                    ui.button(
                        "Done",
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
