# Nice Dialogs

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![prek](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json)](https://github.com/j178/prek)

A collection of opinionated [NiceGUI](https://nicegui.io) dialogs.

## Dialogs

### Cron Expression Editor

Using `cron_converter` via `CronStr` from `pydantic-extra-types`, this dialog allows one to build a cron expression by populating the cron schedule parts from selectors.

### Datetime Picker

A dialog, on which one may pick an arbitrary date and time using the appropriate NiceGUI picker elements.
A timezone field is optional and allows the user to set an IANA timezone while using the dialog.
The returned datetime object is always timezone-aware and converted to UTC.

### File Uploader

A simple single-file uploader component dialog with options for restricting file types and max size.
The dialog returns a NiceGUI `FileUpload` object for the consumer to dereference after the dialog returns.

## Requirements

- uv. This project is managed by [uv](https://astral.sh/uv)
- Python >= 3.13.
- NiceGUI >= 3.16.

## Examples

A NiceGUI application can be started to demonstrate the dialogs by running `make examples`.
Note this uses NiceGUI's native mode by default. You may set the `NATIVE=0` environment variable to disable native mode.
The example application is also used by the NiceGUI `User` test fixture.

## Development Setup

To prepare for development, run `make init`.
The contents of the `.vscode/` directory may be useful for IDE-based testing and debugging.

## Releasing

The package version is derived from git tags (`hatch-vcs`), and releases are made with [python-semantic-release](https://python-semantic-release.readthedocs.io/) from the conventional commits on `main`.
There is no version commit; the tag is placed on the merged commit, so nothing needs to be pushed to the protected `main` branch.

1. Merge the changes to `main` and `git pull`.
2. Run `make release-dry-run` to see the next version PSR would choose.
3. Export a `GH_TOKEN` with `repo` scope and run `make release`.
   This tags the commit and creates the GitHub Release, which triggers the publish workflow (subject to approval of the `pypi` environment).

Commits that are only `chore`, `docs`, etc. do not produce a release.

### Point releases

To release a fix for an older version, cut a maintenance branch from the release tag, e.g. `git switch -c release/1.4.x 1.4.0`, cherry-pick the fix commits (`git cherry-pick -x ...`), and push the branch.
Run `make release-dry-run` and then `make release` from that branch to publish `1.4.1`, `1.4.2`, and so on.
`make release` refuses to run on a `release/X.Y.x` branch if the next version falls outside the `X.Y` series, for example because a `feat:` commit was cherry-picked.
The branch must be cut from a tag that already contains the `[tool.semantic_release]` configuration.

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
