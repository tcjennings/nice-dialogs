# Nice Dialogs

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A collection of opinionated [NiceGUI](https://nicegui.io) dialogs.

## Cron Expression Editor

Using `cron_converter` via `CronStr` from `pydantic-extra-types`, this dialog allows one to build a cron expression by populating the cron schedule parts from selectors.

## Datetime Picker

A dialog, on which one may pick an arbitrary date and time using the appropriate NiceGUI picker elements.
A timezone field is optional and allows the user to set an IANA timezone while using the dialog.
The returned datetime object is always timezone-aware and converted to UTC.

## File Uploader

A simple single-file uploader component dialog with options for restricting file types and max size.
The dialog returns a NiceGUI `FileUpload` object for the consumer to dereference after the dialog returns.

## Requirements

- uv. This project is managed by [uv](https://astral.sh/uv)
- Python >= 3.13[^1].
- NiceGUI >= 3.10[^2].

## Examples

A NiceGUI application can be started to demonstrate the dialogs by running `make examples`.
Note this uses NiceGUI's native mode by default. You may set the `NATIVE=0` environment variable to disable native mode.
The example application is also used by the NiceGUI `User` test fixture.

## Development Setup

To prepare for development, run `make init`.
The contents of the `.vscode/` directory may be useful for IDE-based testing and debugging.

## Usage in Projects

To use these dialogs in a NiceGUI application, set a dependency; example for `uv` and `pyproject.toml` shown:

```
dependencies = [
    ...,
    "nice-dialog",
]

[tool.uv.sources]
nice-dialog = { git = "https://github.com/tcjennings/nice-dialogs", rev = "..." }
```

> [!TIP]
> Consider pinning a `git` dependency source to a specific commit revision for maximum security.

[^1]: This project uses modern Python syntax, including `datetime` format strings, structural pattern matching, and walrus operators.

[^2]: This project uses NiceGUI features introduced in version 3.10 (e.g., nested dictionary binding) and is not compatible with older versions.
