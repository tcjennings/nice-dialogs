from typing import Self

from nicegui import ui

from nice_dialog.dialogs.cron_editor import CronEditorDialog


class NiceIndexPage:
    """An index page for a NiceGUI application.

    Page models or other components can be created during the `setup` phase and stored as instance variables.
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

    def __init__(self) -> None:
        """Creates the basic layout of the page.

        This method should only be used for creating the static layout of the page, such as headers, footers, and content areas.

        Page specific components can be created using the `self.content` column as a context manager (see the `render` method).
        """
        with ui.header(elevated=True).classes(
            "h-[4rem] min-h-[4rem] items-center justify-between px-4 p-4"
        ):
            ui.label("Nice Dialogs").classes("text-[2rem]")

        with ui.column().classes(
            "h-[calc(100vh-4rem)] min-h-[4rem] overflow-hidden p-0 m-0 w-full"
        ) as self.content:
            pass

    async def show_cron_dialog(self) -> None:
        """Button callback to display and await the result of a cron expression editor dialog."""
        result = await self.cron_dialog
        ui.notify(result)

    async def setup(self) -> Self:
        """Method for creating page models or other components. This method can also be used to fetch data or perform other asynchronous setup tasks."""
        self.cron_dialog = CronEditorDialog()
        return self

    async def render(self) -> None:
        """Method for building the UI of the page. This method can use any components created during the `setup` phase."""
        with self.content:
            ui.button("Cron Expression Editor", on_click=self.show_cron_dialog)
