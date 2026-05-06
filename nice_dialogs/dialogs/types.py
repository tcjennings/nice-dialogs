"""Module for generic NiceGUI event argument types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import nicegui.events

    type ValueChangeEventArguments = nicegui.events.ValueChangeEventArguments[Any]
    """A generic ValueChangeEventArguments for indeterminate or dynamic value
    change events"""

    type ValueChangeEventArgumentsBool = nicegui.events.ValueChangeEventArguments[
        bool | None
    ]
    """A ValueChangeEventArguments for events that use a boolean value when a
    value is present."""

    type ValueChangeEventArgumentsStr = nicegui.events.ValueChangeEventArguments[
        str | None
    ]
    """A ValueChangeEventArguments for events that use a string value when a
    value is present."""

__all__ = ["ValueChangeEventArguments", "ValueChangeEventArgumentsBool"]
