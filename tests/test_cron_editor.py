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


async def open_cron_editor(user: User) -> None:
    """Open the example page and its Cron Editor Dialog."""
    await user.open("/")
    await user.should_see("Cron Expression Editor")
    user.find("Cron Expression Editor").click()
    await user.should_see(marker="cron-expression-display", content="* * * * *")


@pytest.mark.parametrize(
    ("marker", "typed", "expected"),
    [
        ("dom", "12", "* * 12 * *"),
        ("minute", "*/5", "*/5 * * * *"),
        ("hour", "Midnight", "* 0 * * *"),  # the label of an existing option
    ],
)
async def test_cron_editor_commits_typed_text_on_blur(
    user: User,
    marker: str,
    typed: str,
    expected: str,
) -> None:
    """Text typed into a select is kept when the select loses focus.

    Quasar only commits typed text on Enter or Tab and discards it on blur, so
    the dialog commits the last typed text itself when the select is blurred.
    """
    await open_cron_editor(user)

    select = user.find(kind=ui.select, marker=marker)
    select.trigger("focus")
    select.trigger("inputValue", typed)
    select.trigger("blur")

    await user.should_see(
        marker="cron-expression-display", content=expected, retries=50
    )


async def test_cron_editor_blur_keeps_selected_option(user: User) -> None:
    """Blurring after choosing an option keeps the option, not stale input text.

    Quasar reports the label of the current value as input text when a select is
    focused, but not after an option is chosen from the dropdown.
    """
    await open_cron_editor(user)

    select = user.find(kind=ui.select, marker="dow")
    select.click()
    select.trigger("focus")
    select.trigger("inputValue", "Every (*)")
    await user.should_see("Weekdays", retries=50)
    user.find("Weekdays").click()
    await user.should_see(
        marker="cron-expression-display", content="* * * * 1-5", retries=50
    )

    select.trigger("blur")

    await user.should_see(
        marker="cron-expression-display", content="* * * * 1-5", retries=50
    )


async def test_cron_editor_blur_without_typing_changes_nothing(user: User) -> None:
    """Focusing and blurring a select without typing leaves the expression as is."""
    await open_cron_editor(user)

    select = user.find(kind=ui.select, marker="dom")
    select.trigger("focus")
    select.trigger("inputValue", "Every (*)")
    select.trigger("blur")

    await user.should_see(
        marker="cron-expression-display", content="* * * * *", retries=50
    )
