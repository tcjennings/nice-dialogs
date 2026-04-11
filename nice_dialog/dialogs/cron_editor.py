from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime, UTC
from itertools import islice
from typing import TYPE_CHECKING

from nicegui import ui
from nicegui.events import ValueChangeEventArguments

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

    def __repr__(self) -> str:
        return f"{self.minute} {self.hour} {self.dom} {self.month} {self.dow}"


class CronEditorDialog(ui.dialog):
    """NiceGUI Dialog displaying a Cron Expression Editor.

    Two action buttons are available: "Done" returns the current cron expression string;
    "Cancel" returns None.
    """

    dialog_title: str
    cron: CronStr
    model: CronEditorModel

    def __init__(
        self,
        *,
        dialog_title: str = "Cron Expression Editor",
        initial_expression: str = "* * * * *",
    ) -> None:
        super().__init__()
        self.dialog_title = dialog_title
        self.model = CronEditorModel(*initial_expression.split())
        self.dialog_layout()

    if TYPE_CHECKING:

        def __await__(self) -> Generator[None, None, str | None]: ...

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
                with ui.row():
                    ui.button(
                        "Done",
                        on_click=lambda: self.submit(str(self.model)),
                    ).mark("done")
                    ui.button(
                        "Cancel",
                        color="negative",
                        on_click=lambda: self.submit(None),
                    ).mark("cancel")

    def handle_cron_change(self, e: ValueChangeEventArguments) -> None:
        """Callback handler from cron expression selectors"""
        self.cron = CronStr(str(self.model))
        self.show_next_runs.refresh()

    @ui.refreshable_method
    def show_next_runs(self) -> None:
        """Refreshable method to display the next five events according to the
        current cron schedule.
        """
        now = datetime.now(tz=UTC)
        for i, run in enumerate(islice(self.cron.schedule(), 5)):
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
