from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import islice
from typing import TYPE_CHECKING, Self

from nicegui import ui
from pydantic import ValidationError
from pydantic_extra_types.cron import CronStr

if TYPE_CHECKING:
    from nicegui.events import GenericEventArguments

    from .types import ValueChangeEventArguments


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

UPCOMING_RUNS = 5
"""Number of upcoming runs to find and show for a cron expression."""


@dataclass
class CronEditorModel:
    """Data model of a cron expression and its validity.

    The expression is held as one string per cron part so that each part can be
    edited on its own. An expression is only valid if it parses *and* has at least
    one upcoming run. The second condition rejects expressions that can never fire,
    such as February 30th, without any date logic of our own: those are simply the
    expressions for which the schedule is empty.

    Use `from_expression` to create a model from a whole expression string. The
    model is validated when it is created, and `validate` must be called again
    after any part is changed.

    Parameters
    ----------
    minute : str, default "*"
        The minute part of the expression.
    hour : str, default "*"
        The hour part of the expression.
    dom : str, default "*"
        The day-of-month part of the expression.
    month : str, default "*"
        The month part of the expression.
    dow : str, default "*"
        The day-of-week part of the expression.
    cron : CronStr, optional
        An expression that has already been parsed from these parts. If given, the
        parts are not parsed again, and only the upcoming runs are found.

    Attributes
    ----------
    minute, hour, dom, month, dow : str
        The parts of the expression, as given or as most recently edited.
    cron : CronStr or None
        The most recent expression that parsed, with or without any runs. It is
        `None` until the parts have parsed.
    upcoming : list of datetime
        Up to `UPCOMING_RUNS` upcoming runs of the expression. Empty if the
        expression is malformed or never runs.
    is_valid : bool
        Whether the expression parses and has at least one upcoming run.
    error : str
        The reason the expression is not valid, or an empty string if it is.

    Notes
    -----
    `str()` and `repr()` of the model give the expression as space separated parts,
    exactly as they are held, which is not necessarily in the canonical form of
    `cron`.
    """

    minute: str = "*"
    hour: str = "*"
    dom: str = "*"
    month: str = "*"
    dow: str = "*"
    cron: CronStr | None = field(default=None, kw_only=True)
    upcoming: list[datetime] = field(init=False, default_factory=list)
    is_valid: bool = field(init=False, default=True)
    error: str = field(init=False, default="")

    def __post_init__(self) -> None:
        # An expression that is already parsed does not need parsing again
        if self.cron is None:
            self.validate()
        else:
            self._find_runs(self.cron)

    def __repr__(self) -> str:
        return f"{self.minute} {self.hour} {self.dom} {self.month} {self.dow}"

    @classmethod
    def from_expression(cls, expression: str) -> Self:
        """Create a model from a cron expression string.

        The expression is validated by `CronStr`, which raises a `ValueError` if it
        is malformed or out of range. An expression that is well formed but never
        runs does not raise: the model is returned with `is_valid` false.
        """
        return cls(*expression.split(), cron=CronStr(expression))

    def validate(self) -> bool:
        """Validate the current cron parts and find the upcoming runs.

        Sets `is_valid`, `error`, and `upcoming`, and returns `is_valid`. The
        `cron` attribute is only replaced by an expression that parses.
        """
        self.upcoming = []
        try:
            cron = CronStr(str(self))
        except (ValueError, ValidationError) as e:
            self.is_valid, self.error = False, str(e)
            return False
        return self._find_runs(cron)

    def _find_runs(self, cron: CronStr) -> bool:
        """Find the upcoming runs of a parsed expression and set the model's state."""
        self.cron = cron
        try:
            self.upcoming = list(islice(cron.schedule(), UPCOMING_RUNS))
        except Exception:
            # cron_converter raises a bare Exception when it finds no run at all
            self.upcoming = []

        if not self.upcoming:
            self.is_valid, self.error = False, "This expression never runs"
            return False

        self.is_valid, self.error = True, ""
        return True


class CronEditorDialog(ui.dialog):
    """NiceGUI Dialog displaying a Cron Expression Editor.

    Two action buttons are available: "Done" returns the current cron expression string;
    "Cancel" returns None.

    This dialog is created with the initial cron expression of "* * * * *". This
    expression can be replaced by calling the `reset` method with a new cron expression
    string.

    If a cron expression that is malformed, or has a value out of range, is used to
    reset the dialog, a notification will alert the user and the dialog keeps its
    current expression. If the expression is well formed but can never run, such as
    February 30th, a notification will alert the user, but the dialog will show the
    expression and remain open in order to allow the user to correct it.

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
    _drafts: dict[str, str]
    """Text most recently typed into each cron part's select, by part name."""

    def __init__(
        self,
        *,
        dialog_title: str = "Cron Expression Editor",
    ) -> None:
        super().__init__()
        self.dialog_title = dialog_title
        self.initial_expression = ""
        self._drafts = {}
        self.reset()
        self.dialog_layout()

    if TYPE_CHECKING:

        def __await__(self) -> Generator[None, None, str | None]: ...

    def reset(self, cron: str | None = None) -> None:
        """Set the dialog to its initial state or to a provided cron expression by
        establishing or replacing the dialog's data model.

        If the provided cron expression contains novel tokens, those tokens will be
        added to the options of the relevant select components.

        This method is called when the dialog is first created, and can be called
        at any time to set the dialog to a specific new cron expression.

        The expression is validated by `CronStr` when the model is created. One that
        does not validate is rejected with a notification and leaves the dialog
        unchanged.
        """
        # Set the dialog's initial or fallback expression on first method call
        self.initial_expression = self.initial_expression or cron or "* * * * *"

        # Set the data model using the provided cron expression or the fallback
        cron = cron or self.initial_expression
        try:
            model = CronEditorModel.from_expression(cron)
        except (ValueError, ValidationError) as e:
            ui.notify(f"Invalid cron expression: {cron!r} ({e})", type="negative")
            return

        self._drafts.clear()
        self.model = model

        # Every token must be an option of its select to be shown, valid or not
        self.update_input_options()
        if not self.model.is_valid:
            ui.notify(
                f"Invalid cron expression: {cron} ({self.model.error})",
                type="negative",
            )

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

            for select, part in (
                (self.minute_select, "minute"),
                (self.hour_select, "hour"),
                (self.dom_select, "dom"),
                (self.month_select, "month"),
                (self.dow_select, "dow"),
            ):
                self.commit_on_blur(select, part)

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

    def commit_on_blur(self, select: ui.select, part: str) -> None:
        """Keep text typed into a select when the user clicks away.

        Quasar only converts typed text into a value on Enter or Tab and discards
        it on blur. This remembers the latest text typed into the select and
        commits it when the select loses focus, as if the user had pressed Tab.

        Quasar also reports the label of the current selection as input text when
        the select is focused, so the remembered text is dropped whenever the
        select gains focus or a value is chosen, and ignored if it only repeats
        the label of the current value.
        """

        def remember(event: GenericEventArguments) -> None:
            self._drafts[part] = (event.args or "").strip()

        def forget() -> None:
            self._drafts.pop(part, None)

        def commit() -> None:
            text = self._drafts.pop(part, "")
            if TYPE_CHECKING:
                assert isinstance(select.options, dict)
            current = getattr(self.model, part)
            if not text or text == select.options.get(current):
                return
            if text in select.options:
                value = text
            elif text in select.options.values():
                value = next(k for k, v in select.options.items() if v == text)
            else:
                value = text
            if value != current:
                setattr(self.model, part, value)
                self.update_input_options()

        select.on("focus", forget)
        select.on("update:model-value", forget)
        select.on("input-value", remember)
        select.on("blur", commit)

    def handle_cron_change(self, event: ValueChangeEventArguments) -> None:
        """Callback handler from cron expression selectors"""
        if not self.model.validate():
            ui.notify(self.model.error, type="negative")
        self.show_next_runs.refresh()

    @ui.refreshable_method
    def show_next_runs(self) -> None:
        """Refreshable method to display the next five events according to the
        current cron schedule, or to say that there are none.
        """
        if not self.model.is_valid:
            ui.label("No upcoming runs for this expression").classes(
                "text-sm text-gray-400",
            )
            return

        now = datetime.now(tz=UTC)
        for i, run in enumerate(self.model.upcoming):
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
