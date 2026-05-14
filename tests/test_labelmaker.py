import asyncio

import pytest
from nicegui import ElementFilter, ui
from nicegui.elements.mixins.disableable_element import DisableableElement
from nicegui.testing import User, UserInteraction

pytestmark = pytest.mark.asyncio(loop_scope="function")
"""Sets the default asyncio loop scope."""


async def wait_until_enabled(element: DisableableElement) -> None:
    """Utility fixture to wait until a given element is enabled.

    This should only be used along with `asyncio.wait_for`.
    """
    while not element.enabled:  # noqa: ASYNC110
        await asyncio.sleep(0.1)


async def test_labelmaker_dialog(user: User) -> None:
    """Tests the label maker dialog by opening, interacting the custom elements,
    and adding a custom label to the list.
    """
    await user.open("/")
    await user.should_see("LabelMaker Dialog")

    # Click the button and ensure the dialog opens with the correct contents
    user.find(kind=ui.button, marker="labelmaker").click()
    await user.should_see("Testing Label Constructor")
    await user.should_see("Submit")

    # Click to open the select dropdowns and ensure the options are visible
    user.find(kind=ui.select, marker="input_1").click()
    await user.should_see("OPTION_B", retries=50)
    user.find("OPTION_B").click()

    user.find(kind=ui.select, marker="input_2").click()
    await user.should_see("Option C", retries=50)
    user.find("Option C").click()

    user.find(kind=ui.select, marker="input_3").click()
    await user.should_see("Option X", retries=50)
    user.find("Option X").click()

    user.find(kind=ui.input, marker="input_0").type("abcd").trigger("keydown.tab")
    await user.should_see("abcd", retries=50)
    await user.should_not_see("Input must not be empty", retries=50)

    # The element bindings are not instantaneous, so we give it a moment to update
    add_button = user.find(kind=ui.button, marker="add").elements.pop()
    await asyncio.wait_for(wait_until_enabled(add_button), timeout=5)
    assert add_button.enabled is True

    user.find(kind=ui.button, marker="add").click()
    await user.should_see(
        kind=ui.chip, content="abcd : OPTION_B : Option C : Option X", retries=50
    )


async def test_labelmaker_dialog_remove_item(user: User) -> None:
    """Tests the label maker dialog by opening and removing an item from the custom
    list of labels.
    """
    await user.open("/")
    await user.should_see("LabelMaker Dialog")

    # Click the button and ensure the dialog opens with the correct contents
    user.find(kind=ui.button, marker="labelmaker").click()
    await user.should_see("Testing Label Constructor")
    await user.should_see("Submit")

    # Remove one of the default labels
    with user:
        for item in ElementFilter(kind=ui.icon, marker="delete").within(
            marker="label_1"
        ):
            UserInteraction(user, {item}, target=None).click()

    await user.should_not_see("1 : 2 : 3 : 4", retries=50)
