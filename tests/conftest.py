from collections.abc import Generator
import pytest


@pytest.fixture(scope='session')
def monkeypatch_session() -> Generator[pytest.MonkeyPatch]:
    """A session-scoped monkeypatch fixture that can be used across multiple test modules."""
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope='session', autouse=True)
def setup_nicegui_env(monkeypatch_session: pytest.MonkeyPatch) -> None:
    """Set up environment before NiceGUI test app loads"""
    monkeypatch_session.setenv("NATIVE", "0")
