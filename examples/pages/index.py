from dataclasses import dataclass, field
from enum import Enum, StrEnum, auto
from typing import Literal, Self

from nicegui import ui
from nicegui.elements.upload_files import FileUpload
from nicegui.version import __version__ as nicegui_version

from nice_dialogs.dialogs.cron_editor import CronEditorDialog


@dataclass
class NiceIndexModel:
    """Data model for the index page."""

    cron: str = "* * * * *"
    dt_tz_frozen: bool = False
    dt_tz_hidden: bool = False
    upload_types: list[str] = field(default_factory=list)
    confirmation_icon_color: str = "warning"
    confirmation_icon_name: str = "warning"
    confirmation_message: str = "Are you sure?"


class EnumValueOptions(StrEnum):
    OPTION_A = "Option A"
    OPTION_B = "Option B"
    OPTION_C = "Option C"
    OPTION_D = "Option D"


class EnumOptions(Enum):
    OPTION_A = auto()
    OPTION_B = auto()
    OPTION_C = auto()
    OPTION_D = auto()


class NiceIndexPage:
    """An index page for a NiceGUI application.

    Page models or other components can be created during the `setup` phase and
    stored as instance variables.
    The `render` method can then use these components to build the UI.

    This page uses asynchronous methods for setup and rendering.
    A pattern for using this page with a NiceGUI app is:

    ```
    @ui.page("/")
    async def nice_index() -> None:
        if page := await NiceIndexPage().setup():
            await page.render()
    ```
    """

    content: ui.column
    model: NiceIndexModel

    def __init__(self) -> None:
        """Creates the basic layout of the page.

        This method should only be used for creating the static layout of the page,
        such as headers, footers, and content areas.

        Page specific components can be created using the `self.content` column as a
        context manager (see the `render` method).
        """
        with ui.header(elevated=True).classes(
            "w-full h-[4rem] min-h-[4rem] items-center justify-between px-4 p-4",
        ):
            ui.label("Nice Dialogs").classes("text-[2rem]")
            ui.space()
            ui.label(nicegui_version).classes("text-sm text-white")

        with ui.column().classes(
            "h-[calc(100vh-4rem)] min-h-[4rem] overflow-hidden p-0 m-0 w-full",
        ) as self.content:
            pass

    async def show_cron_dialog(self) -> None:
        """Callback to display and await the result of a cron editor dialog."""
        cron_dialog = CronEditorDialog()
        cron_dialog.reset(self.model.cron)
        result: str | None = await cron_dialog
        cron_dialog.clear()
        ui.notify(result)

    async def show_dt_dialog(self) -> None:
        """Callback to display and await the result of a datetime picker dialog."""
        from nice_dialogs.dialogs.datetime_picker import DatetimePickerDialog

        dtpicker = DatetimePickerDialog(
            hide_timezone=self.model.dt_tz_hidden,
            freeze_timezone=self.model.dt_tz_frozen,
        )
        result = await dtpicker
        dtpicker.clear()
        ui.notify(result)

    async def show_upload_dialog(self) -> None:
        """Button callback to display and await the result of an upload file dialog."""
        from nice_dialogs.dialogs.upload_file import UploadFileDialog

        _: FileUpload | None = await UploadFileDialog(
            allowed_file_types=self.model.upload_types,
        )

    async def show_confirmation_dialog(self) -> None:
        """Button callback to display and await the result of a confirmation dialog."""
        from nice_dialogs.dialogs.confirmation import ConfirmationDialog

        confirm_dialog = ConfirmationDialog(
            icon_color=self.model.confirmation_icon_color,
            icon=self.model.confirmation_icon_name,
            message=self.model.confirmation_message,
        )
        result, remember = await confirm_dialog
        ui.notify(f"{result} [remembered: {remember}]", color="accent")
        confirm_dialog.clear()

    async def show_labelmaker_dialog(self) -> None:
        """Button callback to display and await the result of a label maker dialog."""
        from nice_dialogs.dialogs.labelmaker import LabelMakerDialog

        labelmaker_dialog = LabelMakerDialog(
            "Testing Label Constructor",
            num_inputs=4,
            input_labels=["First", "Second"],
            values=[
                ("One", "Two", "Three", "Four"),
                ("1", "2", "3", "4"),
                ("uno", "dos", "tres", "cuatro"),
            ],
            validators=[{"Input must be less than 5 characters": lambda v: len(v) < 5}],
            value_types=[
                str,
                EnumOptions,
                EnumValueOptions,
                Literal["Option Z", "Option Y", "Option X", "Option W"],
            ],
        )
        result = await labelmaker_dialog
        if result is not None:
            display_result = result[0]
            ui.notify(display_result, color="accent")
        labelmaker_dialog.clear()

    async def setup(self) -> Self:
        """Method for creating page models or other components. This method can also be
        used to fetch data or perform other asynchronous setup tasks.
        """
        self.model = NiceIndexModel()
        return self

    async def render(self) -> None:
        """Method for building the UI of the page. This method can use any components
        created during the `setup` phase.
        """
        with self.content:
            with ui.row().classes("w-full items-center justify-start gap-4"):
                ui.button("Cron Expression Editor", on_click=self.show_cron_dialog)
                ui.input(label="Initial Cron Expression").bind_value(
                    self, ("model", "cron")
                )
            with ui.row().classes("w-full items-center justify-start gap-4"):
                ui.button("Datetime Picker", on_click=self.show_dt_dialog)
                ui.switch("Freeze Timezone Input").bind_value(
                    self,
                    ("model", "dt_tz_frozen"),
                )
                ui.switch("Hide Timezone Input").bind_value(
                    self,
                    ("model", "dt_tz_hidden"),
                )
            with ui.row().classes("w-full items-center justify-start gap-4"):
                ui.button("Upload File Dialog", on_click=self.show_upload_dialog)
                ui.input_chips(
                    "Allow file types",
                    new_value_mode="add-unique",
                    value=[".txt"],
                ).bind_value_to(self, ("model", "upload_types"))
            with ui.row().classes("w-full items-center justify-start gap-4"):
                ui.button("Confirmation Dialog", on_click=self.show_confirmation_dialog)
                ui.color_input(label="Icon Color").bind_value(
                    self, ("model", "confirmation_icon_color")
                )
                ui.input(label="Icon Name").bind_value(
                    self, ("model", "confirmation_icon_name")
                )
                ui.textarea(label="Message").bind_value(
                    self, ("model", "confirmation_message")
                )

            with ui.row().classes("w-full items-center justify-start gap-4"):
                ui.button(
                    "LabelMaker Dialog", on_click=self.show_labelmaker_dialog
                ).mark("labelmaker")
