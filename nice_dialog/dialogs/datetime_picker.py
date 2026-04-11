from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import date, time, datetime, tzinfo, UTC
from enum import IntFlag, auto
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from nicegui import ui
from nicegui.events import ValueChangeEventArguments


class DialogOptions(IntFlag):
    """Dialog option flags."""

    DISPLAY_12H = auto()
    """Whether to display time in 12h format. This option does not affect the returned
    datetime value, which is always timezone-aware in UTC.
    """

    FREEZE_TZ = auto()
    """Whether to disallow changes to the timezone input. The timezone input may be
    visible but not editable.
    """

    HIDE_TZ = auto()
    """Whether to hide the timezone input. The timezone input is shown by default."""


@dataclass
class DatetimePickerModel:
    """Data model for the datetime picker dialog.

    Private (`init=False`) fields are used for binding with the dialog input components.

    The dialog's callbacks will manage the model's fields, and the `dt` property will
    always return a timezone-aware datetime in UTC.
    """

    ts: float
    tz: tzinfo = UTC
    options: DialogOptions = DialogOptions(0)
    _date: str = field(init=False, default="")
    _time: str = field(init=False, default="")

    @property
    def dt(self) -> datetime:
        """Returns a timezone-aware datetime in UTC."""
        return datetime.fromtimestamp(self.ts, tz=UTC)

    @property
    def localdt(self) -> datetime:
        """Returns a timezone-aware datetime in the specified timezone."""
        return datetime.fromtimestamp(self.ts, tz=self.tz)


class DatetimePickerDialog(ui.dialog):
    """NiceGUI Dialog displaying a Datetime Picker.

    Two action buttons are available: "Done" returns the selected datetime;
    "Cancel" returns None.

    The user may select any timezone they wish when using the dialog, but the returned
    value is always timezone-aware in UTC.

    Notes
    -----
    - The timezone input is a freeform input field, but we check that its value is
      matched to a known timezone before updating the model.
    - The model stores the datetime as a UTC POSIX timestamp.
    """

    dialog_title: str
    model: DatetimePickerModel

    def __init__(
        self,
        *,
        dialog_title: str = "Datetime Picker",
        hide_timezone: bool = False,
        freeze_timezone: bool = False,
    ) -> None:
        super().__init__()
        self.dialog_title = dialog_title
        now = datetime.now(UTC).timestamp()
        self.model = DatetimePickerModel(ts=now, tz=UTC)

        if hide_timezone:
            self.model.options ^= DialogOptions.HIDE_TZ
        if freeze_timezone:
            self.model.options ^= DialogOptions.FREEZE_TZ

        self.dialog_layout()

    if TYPE_CHECKING:

        def __await__(self) -> Generator[None, None, datetime | None]: ...

    def dialog_layout(self) -> None:
        with self, ui.card():
            ui.label(self.dialog_title).classes("font-bold text-3xl")
            with ui.row().classes("flex w-full"):
                ui.date_input("Date").classes("flex-1 w-2/5").bind_value(
                    self,
                    ("model", "_date"),
                    strict=False,
                ).on_value_change(self.handle_datetime_change).mark("date")

                ui.time_input("Time").classes("flex-1 w-2/5").bind_value(
                    self,
                    ("model", "_time"),
                    strict=False,
                ).on_value_change(self.handle_datetime_change).mark("time")

                # The tz input is not bound the model; instead, updates are
                # handled through the validation callback
                self.tz_input = (
                    ui.input(
                        "Timezone",
                        value=str(self.model.tz),
                    )
                    .classes("flex-1 w-1/5")
                    .props("debounce=1000")
                    .bind_enabled_from(
                        self,
                        ("model", "options"),
                        backward=lambda o: not o & DialogOptions.FREEZE_TZ,
                    )
                    .bind_visibility_from(
                        self,
                        ("model", "options"),
                        backward=lambda o: not o & DialogOptions.HIDE_TZ,
                    )
                    .mark("timezone")
                )
                self.tz_input.validation = self.validate_timezone

            with ui.card_actions().classes("w-full align-left"):
                with ui.row().classes("flex w-full"):
                    ui.button("Done", on_click=lambda: self.submit(self.model.dt)).mark(
                        "done",
                    )
                    ui.button(
                        "Cancel",
                        color="negative",
                        on_click=lambda: self.submit(None),
                    ).mark("cancel")
                    ui.space()
                    with ui.dropdown_button("Options", color="accent"):
                        ui.switch(text="24h").on_value_change(
                            self.handle_24h_option_change,
                        ).bind_value_from(
                            self,
                            ("model", "options"),
                            backward=lambda o: not o & DialogOptions.DISPLAY_12H,
                        )

    def handle_24h_option_change(self, e: ValueChangeEventArguments) -> None:
        """Callback handler for 24h display option toggle."""
        # Instead of an XOR toggle, we are explicit in setting or clearing the
        # flag in order to keep the model consistent with the state of the UI.
        if e.value:
            # Clear the 12h display option flag
            self.model.options &= ~DialogOptions.DISPLAY_12H
        else:
            # Set the 12h display option flag
            self.model.options |= DialogOptions.DISPLAY_12H

        # propagate the option change to the model's string fields
        self.tz_input.validate()

    def handle_datetime_change(
        self,
        e: ValueChangeEventArguments | None = None,
    ) -> None:
        """Callback handler from datetime selectors.

        The model's timestamp is updated based on the date and time input values in UTC.
        """
        # the date and time inputs are bound to the model
        try:
            d = date.fromisoformat(self.model._date)
            t = time.fromisoformat(self.model._time)
        except ValueError:
            # case if either input is not yet populated
            return None

        # update the model timestamp based on the date and time input values
        local_dt = datetime.combine(d, t, tzinfo=self.model.tz)
        self.model.ts = local_dt.astimezone(UTC).timestamp()

    def validate_timezone(self, value: str) -> str | None:
        """Validation and update handler for timezone input.

        The timezone input is a freeform input field, but we check that its
        value is matched to a known timezone before updating the model.
        """
        try:
            # validate and update the model
            self.model.tz = ZoneInfo(value)

            time_format = (
                "%I:%M %p"
                if self.model.options & DialogOptions.DISPLAY_12H
                else "%H:%M"
            )

            # propagate the timezone change to the model's string fields
            # these bound properties will update the UI inputs
            self.model._date = f"{self.model.localdt.date()}"
            self.model._time = self.model.localdt.timetz().strftime(time_format)
        except ZoneInfoNotFoundError as e:
            return f"Invalid timezone: {e}"
        except Exception as e:
            return f"Error processing timezone: {e}"

        return None
