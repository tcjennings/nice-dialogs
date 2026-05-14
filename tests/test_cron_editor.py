import pytest
from nicegui import ui
from nicegui.testing import User

pytestmark = pytest.mark.asyncio(loop_scope="function")
"""Sets the default asyncio loop scope."""


@pytest.mark.xfail(reason="Test is sometimes flaky")
async def test_cron_editor(user: User) -> None:
    """Tests the operation of the Cron Editor Dialog.

    Using the NiceGUI User testing fixture, open the dialog and set a specific
    cron expression by interacting directly with the 5 available select
    components. Assert that the expected cron expression string is visible in
    the dialog.

    Notes
    -----
    The user fixture's `should_see` method has a retry mechanism built in such
    that each retry introduces a 0.1 second sleep. We set this retry count
    higher than the default of 3 to account for race conditions or delays,
    especially because the dialog has multiple bind and callback interactions
    that we need to give time to resolve.
    """
    # Open the index page and ensure the dialog button is visible
    await user.open("/")
    await user.should_see("Cron Expression Editor")

    # Click the button and ensure the dialog opens with the correct contents
    user.find("Cron Expression Editor").click()
    await user.should_see(kind=ui.button, marker="done")
    await user.should_see(marker="cron-expression-display", content="* * * * *")

    # the triple is the marker for the select, the option text to click, and the
    # expected cron value after clicking that option
    for triple in [
        ("dow", "Tuesday", "* * * * 2"),
        ("month", "May", "* * * 5 2"),
        ("hour", "Midnight", "* 0 * 5 2"),
        ("minute", "Every 15 minutes", "*/15 0 * 5 2"),
    ]:
        m, o, c = triple
        # Click to open the select dropdown and ensure the options are visible
        user.find(kind=ui.select, marker=m).click()

        select_dropdown = user.find(
            kind=ui.select,
            marker=m,
        ).elements.pop()
        assert select_dropdown.is_showing_popup
        await user.should_see(o, retries=50)

        # Find the option and click it
        user.find(o).click()
        await user.should_see(c, retries=50)

    cron_display = user.find(
        kind=ui.code,
        marker="cron-expression-display",
    ).elements.pop()
    assert cron_display.content == "*/15 0 * 5 2"
