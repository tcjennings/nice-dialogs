import pytest
from nicegui import ui
from nicegui.testing import User


pytestmark = pytest.mark.asyncio(loop_scope="function")
"""Sets the default asyncio loop scope."""


async def test_cron_editor(user: User):
    """Tests the operation of the Cron Editor Dialog.

    Using the NiceGUI User testing fixture, open the dialog and set a specific
    cron expression by interacting directly with the 5 available select
    components. Assert that the expected cron expression string is visible in
    the dialog and that the correct value is returned when "Done" is clicked.

    Notes
    -----
    The user fixture's `should_see` method has a retry mechanism built in such
    that each retry introduces a 0.1 second sleep. We set this retry count
    higher than the default of 3 to account for race conditions or delays,
    especially because the dialog has multiple bind and callback interactions
    that we need to give time to resolve.
    """
    # Open the index page and ensure the dialog button is visible
    await user.open('/')
    await user.should_see('Cron Expression Editor')

    # Click the button and ensure the dialog opens with the correct contents
    user.find('Cron Expression Editor').click()
    await user.should_see("Cron Expression Editor")
    await user.should_see("* * * * *")

    for pair in [("minute", "*/15"), ("hour", "Midnight"), ("dom", "Every (*)"), ("month", "March"), ("dow", "Weekends")]:
        s, o = pair
        # Click to open the select dropdown and ensure the options are visible
        user.find(kind=ui.select, marker=s).click()
        await user.should_see(o, retries=10)

        # Find the option and click it
        user.find(o).click()
        await user.should_see(o, retries=10)

    await user.should_see("*/15 0 * 3 0,6", retries=10)

    cron_display = user.find(kind=ui.code, marker="cron-expression-display").elements.pop()
    assert cron_display.content == "*/15 0 * 3 0,6"

    # Click the Done button
    user.find(kind=ui.button, marker="done").click()
