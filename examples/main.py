#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nice-dialog",
#   "pywebview",
# ]
# [tool.uv.sources]
# nice-dialog = { path = ".." }
# ///

import os

from nicegui import ui

from .pages.index import NiceIndexPage


@ui.page("/")
async def nice_index() -> None:
    await ui.context.client.connected()
    if page := await NiceIndexPage().setup():
        await page.render()


if __name__ in {"__main__", "__mp_main__"}:
    native = os.getenv("NATIVE", "1") == "1"
    ui.run(title="Nice Dialogs", native=native, reload=True)
