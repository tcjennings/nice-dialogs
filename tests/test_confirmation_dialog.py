import pytest
from nicegui import ui
from nicegui.testing import User

pytestmark = pytest.mark.asyncio(loop_scope="function")
"""Sets the default asyncio loop scope."""


async def test_confirmation_dialog(user: User) -> None:
    """Tests the confirmation dialog."""
    await user.open("/")
    await user.should_see("Confirmation Dialog")

    # Click the button and ensure the dialog opens with the correct contents
    user.find("Confirmation Dialog").click()
    await user.should_see(marker="confirm_no")
    await user.should_see("Are you sure?")
    user.find(kind=ui.button, marker="confirm_yes").click()
