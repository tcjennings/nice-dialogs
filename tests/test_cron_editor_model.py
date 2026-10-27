import pytest

from nice_dialogs.dialogs.cron_editor import UPCOMING_RUNS, CronEditorModel


@pytest.mark.parametrize(
    "parts",
    [
        ("*", "*", "*", "*", "*"),
        ("0", "0", "29", "2", "*"),  # February 29th exists in leap years
        ("*/15", "0", "*", "5", "2"),
        ("0", "0", "31", "*", "*"),  # only some months have a 31st
    ],
)
def test_expression_with_upcoming_runs_is_valid(parts: tuple[str, ...]) -> None:
    model = CronEditorModel(*parts)

    assert model.is_valid
    assert model.error == ""
    assert len(model.upcoming) == UPCOMING_RUNS


@pytest.mark.parametrize(
    "parts",
    [
        ("0", "0", "30", "2", "*"),  # February 30th
        ("0", "0", "31", "4", "*"),  # April 31st
        ("0", "0", "31", "6", "*"),  # June 31st
    ],
)
def test_expression_that_never_runs_is_invalid(parts: tuple[str, ...]) -> None:
    model = CronEditorModel(*parts)

    assert not model.is_valid
    assert model.error == "This expression never runs"
    assert model.upcoming == []


def test_unparseable_expression_is_invalid() -> None:
    model = CronEditorModel("99", "*", "*", "*", "*")

    assert not model.is_valid
    assert model.error
    assert model.upcoming == []


def test_validate_recovers_when_the_expression_is_fixed() -> None:
    model = CronEditorModel("0", "0", "30", "2", "*")
    assert not model.is_valid

    model.dom = "28"

    assert model.validate()
    assert model.is_valid
    assert model.error == ""
    assert len(model.upcoming) == UPCOMING_RUNS


def test_from_expression() -> None:
    model = CronEditorModel.from_expression("30 4 1 * *")

    assert model.is_valid
    assert repr(model) == "30 4 1 * *"
    assert len(model.upcoming) == UPCOMING_RUNS


def test_from_expression_that_never_runs() -> None:
    model = CronEditorModel.from_expression("0 0 30 2 *")

    assert not model.is_valid
    assert model.error == "This expression never runs"
    assert repr(model) == "0 0 30 2 *"


@pytest.mark.parametrize("expression", ["* * *", "* * * * * *", "99 * * * *", ""])
def test_from_expression_rejects_a_malformed_expression(expression: str) -> None:
    with pytest.raises(ValueError):
        CronEditorModel.from_expression(expression)
