"""Dialog for managing the upload of a single file.

This dialog is designed to be simple and straightforward for the upload of one
file at a time to a NiceGUI application. For more robust uploading needs,
especially the handling of larger files, consult the NiceGUI docuementation for
the `ui.upload` component, particularly the advice regarding adjusting the
Starlette Multiparser's `spool_max_size`.

The default spool size of 1MiB is sufficient for many use cases, especially for
the small files this dialog supports in its default configuration. With this
limit, the NiceGUI uploader uses buffer during the upload but then passes the
actual bytes of the uploaded file to the `on_upload` callback. If the file
is larger than Starlette's spool size, the upload is spilled to a temp file
instead.
"""

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from nicegui import ui
from nicegui.elements.upload_files import FileUpload
from nicegui.events import UiEventArguments, UploadEventArguments


@dataclass
class UploadFileModel:
    """Data model for the upload file dialog.

    Attributes
    ----------
    max_file_size: int
        The maximum allowed file size in bytes. This defaults to 1 MiB.

    allowed_file_types: list[str]
        A list of allowed file types for upload. These file types are not
        documented by NiceGUI but are passed directly to the `accept` property
        of the underlying Quasar `<q-uploader>` component.
    """

    allowed_file_types: list[str] = field(default_factory=list)
    max_file_size: int = 1_048_576  # 1 MiB


class UploadFileDialog(ui.dialog):
    """NiceGUI Dialog for uploading a single file.

    With a maximum file size of around 1MB, this dialog is intended for small
    files that will fit in RAM (within the default spool size of the underlying
    Starlette MultipartParser).

    When a file is successfully uploaded, the dialog automatically closes and
    returns the FileUpload object. A "Cancel" button allows users to dismiss the
    dialog without uploading, returning None.

    Params
    ------
    dialog_title: str
        The title displayed at the top of the dialog.

    allowed_file_types: list[str]
        A list of allowed file types for upload, e.g. `[".jpg", ".png"]` to only
        allow JPEG and PNG images, or `["image/*"]` to allow all image types.
        See NiceGUI's `ui.upload` component for more details.

    max_file_size: int
        The maximum allowed file size in bytes. Defaults to 1,000,000 bytes (1 MB).

    Returns
    -------
    nicegui.elements.upload_files.FileUpload | None
        The uploaded file object when the upload completes, or `None` if the user
        clicks "Cancel".
    """

    def __init__(
        self,
        *,
        dialog_title: str = "Single File Upload",
        allowed_file_types: list[str] = [".*"],
        max_file_size: int = 1_000_000,
    ) -> None:
        """Initialize the dialog and its components."""
        super().__init__()
        self.dialog_title = dialog_title
        self.model = UploadFileModel(
            allowed_file_types=allowed_file_types,
            max_file_size=max_file_size,
        )
        self.dialog_layout()

    if TYPE_CHECKING:

        def __await__(self) -> Generator[None, None, FileUpload | None]: ...

    def dialog_layout(self) -> None:
        with self, ui.card():
            ui.label(self.dialog_title).classes("font-bold text-3xl")
            with ui.row().classes("flex w-full"):
                self.uploader = (
                    ui.upload(
                        label="Upload File",
                        on_begin_upload=self.handle_begin_upload,
                        on_upload=self.handle_file_upload,
                        on_rejected=self.handle_rejected_upload,
                        max_file_size=self.model.max_file_size,
                        max_files=1,
                    )
                    .classes("flex-1")
                    .props(f'accept="{",".join(self.model.allowed_file_types)}"')
                    .mark("file_upload")
                )

            with ui.card_actions().classes("w-full align-left"):
                with ui.row().classes("flex w-full"):
                    ui.button(
                        "Cancel",
                        color="negative",
                        on_click=lambda: self.submit(None),
                    ).mark("cancel")

    async def handle_begin_upload(self, e: UiEventArguments) -> None:
        """Callback handler for the beginning of a file upload."""
        ...

    async def handle_file_upload(self, e: UploadEventArguments) -> None:
        """Callback handler for successful file upload.

        Displays a notification with the file size and immediately submits the
        dialog with the uploaded file object.
        """
        size_k = e.file.size() / 1024
        ui.notify(
            f"Upload complete: {e.file.name} ({size_k:.1f} KiB)", color="positive"
        )
        self.submit(e.file)

    async def handle_rejected_upload(self, e: UiEventArguments) -> None:
        """Callback handler for rejected file upload (e.g. due to file type or size
        restrictions).
        """
        ui.notify(
            "File upload rejected. Please ensure the file meets the type and size "
            "requirements.",
            color="negative",
        )
