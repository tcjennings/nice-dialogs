from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from faker import Faker
from nicegui import ui
from nicegui.testing import User

pytestmark = pytest.mark.asyncio(loop_scope="function")
"""Sets the default asyncio loop scope."""


@pytest.mark.skip(reason="Not yet implemented")
async def test_upload_wrong_file_type(user: User, faker: Faker) -> None:
    await user.open("/")
    await user.should_see("Upload File Dialog")

    # Click the button and ensure the dialog opens with the correct contents
    user.find("Upload File Dialog").click()
    await user.should_see("Single File Upload")
    await user.should_see("Cancel")

    # "upload" a file
    upload: ui.upload = cast(ui.upload, user.find("file_upload").elements.pop())
    await upload.handle_uploads(
        [
            ui.upload.SmallFileUpload(
                "data.csv", "text/csv", faker.text(max_nb_chars=8_192).encode("utf-8")
            )
        ]
    )


@pytest.mark.skip(reason="Not yet implemented")
async def test_upload_file_too_big(user: User) -> None: ...


@patch("nice_dialog.dialogs.upload_file.UploadFileDialog.handle_file_upload")
async def test_upload_file(
    mock_upload_handler: MagicMock, user: User, faker: Faker
) -> None:
    await user.open("/")
    await user.should_see("Upload File Dialog")

    # Click the button and ensure the dialog opens with the correct contents
    user.find("Upload File Dialog").click()
    await user.should_see("Single File Upload")
    await user.should_see("Cancel")

    # "upload" a file
    upload: ui.upload = cast(ui.upload, user.find("file_upload").elements.pop())
    await upload.handle_uploads(
        [
            ui.upload.SmallFileUpload(
                "data.txt", "text/plain", faker.text(max_nb_chars=8_192).encode("utf-8")
            )
        ]
    )

    # TODO this testing pattern for the uploader bypasses any file validity
    # checks otherwise performed by the upload component
    mock_upload_handler.assert_called_once()
