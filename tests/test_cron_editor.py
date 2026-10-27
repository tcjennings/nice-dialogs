import asyncio
import calendar
import re

import pytest
from nicegui import ui
from nicegui.testing import User

pytestmark = pytest.mark.asyncio(loop_scope="function")
"""Sets the default asyncio loop scope."""

PATIENCE = 30
"""Retries (0.1 seconds each) to wait for something the user should see.

The example page renders only after the client connects, and the dialog's bound
display catches up with a select on the next binding refresh, so what the user
sees is always slightly behind what they just did. `should_see` defaults to only
3 retries, which is too tight for that.
"""


async def open_cron_editor(user: User) -> None:
    """Open the example page and its Cron Expression Editor Dialog."""
    await user.open("/")
    await user.should_see("Cron Expression Editor", retries=PATIENCE)
    user.find("Cron Expression Editor").click()
    await user.should_see(kind=ui.button, marker="done", retries=PATIENCE)
    await should_see_cron(user, "* * * * *")


async def should_see_cron(user: User, expression: str) -> None:
    """Wait until the dialog displays the given cron expression.

    The display shows exactly one expression, so matching its content is as good
    as comparing it for equality.
    """
    await user.should_see(
        marker="cron-expression-display",
        content=expression,
        retries=PATIENCE,
    )


def next_runs(user: User) -> list[str]:
    """The upcoming runs the dialog currently shows, as the user reads them."""
    try:
        labels = user.find(kind=ui.label).elements
    except AssertionError:
        return []
    return [
        label.text
        for label in labels
        if re.fullmatch(r"\w{3}, \d{2}-\w{3} \d{4} at .*", label.text)
    ]


async def type_into(user: User, marker: str, text: str) -> None:
    """Type text into a select and click away, as a user would."""
    select = user.find(kind=ui.select, marker=marker)
    select.trigger("focus")
    select.trigger("inputValue", text)
    select.trigger("blur")


async def settle() -> None:
    """Give the dialog's bindings time to catch up with the last interaction.

    Positive checks can just wait for what the user should see. Checking that
    something did *not* change needs a quiet period instead, because a stale
    display would otherwise pass before a regression becomes visible.
    """
    await asyncio.sleep(0.5)


def month_number(month: str) -> int:
    """The cron number of a month name, as listed in the month select."""
    return list(calendar.month_name).index(month)


async def choose_option(user: User, marker: str, option: str, expression: str) -> None:
    """Choose an option from a select's dropdown, as a user would.

    The user opens the dropdown and sees the option, clicks it, and then sees the
    resulting cron expression. The options are only visible while the dropdown is
    open, so seeing the option also proves that the dropdown opened.
    """
    user.find(kind=ui.select, marker=marker).click()
    await user.should_see(option, retries=PATIENCE)
    user.find(option).click()
    await should_see_cron(user, expression)


async def test_cron_editor(user: User) -> None:
    """Tests the operation of the Cron Editor Dialog.

    Using the NiceGUI User testing fixture, open the dialog and set a specific
    cron expression by choosing options from each of the 5 select components.
    Assert after every step that the dialog displays the expected cron expression.

    Notes
    -----
    The test only does what a user can do and only checks what a user can see.
    In particular it does not inspect the state of the select components, such as
    whether their dropdowns are showing.
    """
    await open_cron_editor(user)

    # the triple is the marker for the select, the option text to click, and the
    # expected cron expression after clicking that option
    for marker, option, expression in [
        ("dow", "Tuesday", "* * * * 2"),
        ("month", "May", "* * * 5 2"),
        ("hour", "Midnight", "* 0 * 5 2"),
        ("minute", "Every 15 minutes", "*/15 0 * 5 2"),
    ]:
        await choose_option(user, marker, option, expression)


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

    await should_see_cron(user, expected)


async def test_cron_editor_blur_keeps_selected_option(user: User) -> None:
    """Blurring after choosing an option keeps the option, not stale input text.

    Quasar reports the label of the current value as input text when a select is
    focused, but not after an option is chosen from the dropdown. The user
    simulation sets a select's value directly when an option is clicked, so this
    test sends the same events as a browser instead: the input text, followed by
    the selection of an option by its index.
    """
    await open_cron_editor(user)

    select = user.find(kind=ui.select, marker="dow")
    select.trigger("focus")
    select.trigger("inputValue", "Every (*)")
    weekdays = list(next(iter(select.elements)).options).index("1-5")
    select.trigger("update:modelValue", {"value": weekdays, "label": "Weekdays"})
    await should_see_cron(user, "* * * * 1-5")

    select.trigger("blur")
    await settle()

    await should_see_cron(user, "* * * * 1-5")


async def test_cron_editor_blur_without_typing_changes_nothing(user: User) -> None:
    """Focusing and blurring a select without typing leaves the expression as is."""
    await open_cron_editor(user)

    select = user.find(kind=ui.select, marker="dom")
    select.trigger("focus")
    select.trigger("inputValue", "Every (*)")
    select.trigger("blur")
    await settle()

    await should_see_cron(user, "* * * * *")


@pytest.mark.parametrize(
    ("day", "month"),
    [("30", "February"), ("31", "April"), ("31", "June")],
)
async def test_cron_editor_rejects_a_date_that_never_happens(
    user: User,
    day: str,
    month: str,
) -> None:
    """The dialog warns about and refuses expressions that can never run.

    Day and month are separate selects, so a user can easily combine them into a
    date that does not exist. No next runs can be found for such an expression.
    """
    await open_cron_editor(user)
    await type_into(user, "dom", day)
    await should_see_cron(user, f"* * {day} * *")
    assert next_runs(user)

    await choose_option(user, "month", month, f"* * {day} {month_number(month)} *")

    await user.should_see("This expression never runs", retries=PATIENCE)
    await user.should_see("No upcoming runs for this expression", retries=PATIENCE)
    assert next_runs(user) == []
    done = next(iter(user.find(kind=ui.button, marker="done").elements))
    assert not done.enabled


async def test_cron_editor_accepts_a_leap_day(user: User) -> None:
    """February 29th exists in leap years, so the dialog accepts it."""
    await open_cron_editor(user)
    await type_into(user, "dom", "29")
    await choose_option(user, "month", "February", "* * 29 2 *")
    await settle()

    assert len(next_runs(user)) == 5
    assert all("29-Feb" in run for run in next_runs(user))
    done = next(iter(user.find(kind=ui.button, marker="done").elements))
    assert done.enabled


async def test_cron_editor_clears_next_runs_for_an_invalid_expression(
    user: User,
) -> None:
    """An invalid expression must not leave the previous expression's runs showing."""
    await open_cron_editor(user)
    await type_into(user, "dom", "12")
    await should_see_cron(user, "* * 12 * *")
    assert all("12-" in run for run in next_runs(user))
    assert next_runs(user)

    await type_into(user, "dom", "99")

    await user.should_see("No upcoming runs for this expression", retries=PATIENCE)
    assert next_runs(user) == []
    done = next(iter(user.find(kind=ui.button, marker="done").elements))
    assert not done.enabled


async def test_cron_editor_recovers_after_an_invalid_expression(user: User) -> None:
    """Fixing an invalid expression brings back the next runs and enables Done."""
    await open_cron_editor(user)
    await type_into(user, "dom", "99")
    await user.should_see("No upcoming runs for this expression", retries=PATIENCE)

    await type_into(user, "dom", "12")
    await should_see_cron(user, "* * 12 * *")
    await settle()

    assert len(next_runs(user)) == 5
    done = next(iter(user.find(kind=ui.button, marker="done").elements))
    assert done.enabled
