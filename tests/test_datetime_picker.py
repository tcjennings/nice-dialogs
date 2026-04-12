from asyncio import sleep
from typing import cast

import pytest
from nicegui import ui
from nicegui.testing import User

pytestmark = pytest.mark.asyncio(loop_scope="function")
"""Sets the default asyncio loop scope."""


async def test_datetime_picker_24h_option(user: User) -> None:
    """Tests the datetime picker dialog's option switch to display time in
    24H or 12H format.
    """
    await user.open("/")
    await user.should_see("Datetime Picker")

    # Click the button and ensure the dialog opens with the correct contents
    user.find("Datetime Picker").click()
    await user.should_see(marker="date")
    await user.should_see(marker="time")
    await user.should_see(marker="timezone")

    time_input: ui.time_input = cast(
        ui.time_input, user.find(marker="time").elements.pop()
    )
    time_input.set_value("20:00")
    user.find("Options").click()
    user.find("24h").click()
    await sleep(0.5)
    assert time_input.value == "08:00 PM"


async def test_datetime_picker_hide_tz(user: User) -> None:
    """Test the hide-tz option for the datetime picker"""
    await user.open("/")
    await user.should_see("Datetime Picker")
    user.find("Hide Timezone Input").click()

    # Click the button and ensure the dialog opens with the correct contents
    user.find("Datetime Picker").click()
    await user.should_see(marker="date")
    await user.should_see(marker="time")
    await user.should_not_see(marker="timezone")


async def test_datetime_picker_disable_tz(user: User) -> None:
    """Test the freeze-tz option for the datetime picker"""
    await user.open("/")
    await user.should_see("Datetime Picker")
    user.find("Freeze Timezone Input").click()

    # Click the button and ensure the dialog opens with the correct contents
    user.find("Datetime Picker").click()
    await user.should_see(marker="date")
    await user.should_see(marker="time")
    await user.should_see(marker="timezone")

    tz_input: ui.input = cast(ui.input, user.find(marker="timezone").elements.pop())
    assert not tz_input.enabled
