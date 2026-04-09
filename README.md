# Nice Dialogs

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A collection of [NiceGUI](https://nicegui.io) dialogs for use with NiceGUI >= 3.10.

## Cron Expression Editor

Using `cron_converter` via `CronStr` from `pydantic-extra-types`, this dialog allows one to build a cron expression by populating the cron schedule parts from selectors.

## Requirements

- uv. This project is managed by [uv](https://astral.sh/uv)
- Python >= 3.13. This project uses modern Python syntax, including `datetime` format strings, structural pattern matching, and walrus operators.

## Examples

A NiceGUI application can be started to demonstrate the dialogs by running `make examples`.
Note this uses NiceGUI's native mode by default. You may set the `NATIVE=0` environment variable to disable native mode.
