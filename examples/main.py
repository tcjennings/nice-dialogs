#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nice-dialogs",
#   "pywebview",
# ]
# [tool.uv.sources]
# nice-dialogs = { path = "..", editable = true }
# ///

import os

from nicegui import ui

from examples.pages.index import NiceIndexPage


@ui.page("/")
async def nice_index() -> None:
    await ui.context.client.connected()
    if page := await NiceIndexPage().setup():
        await page.render()


native = os.getenv("NATIVE", "1") == "1"
ui.run(title="Nice Dialogs", native=native, reload=True)
