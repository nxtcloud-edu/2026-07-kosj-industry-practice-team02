from __future__ import annotations

from sejong_ai_api.db.errors import (
    DatabaseRuleCode,
    DatabaseRuleError,
    DatabaseUnavailableError,
    map_database_error,
)


class FakePsycopgError(Exception):
    def __init__(self, sqlstate: str | None, message: str) -> None:
        super().__init__(message)
        self.sqlstate = sqlstate


def test_sqlstate_maps_to_stable_rule_code_without_parsing_message() -> None:
    expected_codes = {
        "P1001": DatabaseRuleCode.FORBIDDEN_ACTOR_ROLE,
        "P1002": DatabaseRuleCode.SELF_APPROVAL,
        "P1003": DatabaseRuleCode.INVALID_CANDIDATE_STATE,
        "P1004": DatabaseRuleCode.INCOMPLETE_CANDIDATE,
        "P1005": DatabaseRuleCode.DISALLOWED_ORIGIN,
        "P1010": DatabaseRuleCode.INVALID_INTERACTION,
    }

    for sqlstate, expected_code in expected_codes.items():
        sentinel = f"synthetic-private-{sqlstate}"
        error = map_database_error(FakePsycopgError(sqlstate, sentinel))

        assert isinstance(error, DatabaseRuleError)
        assert error.code is expected_code
        assert str(error) == expected_code.value
        assert sentinel not in str(error)


def test_unknown_or_missing_sqlstate_maps_to_exact_unavailable_error() -> None:
    for sqlstate in (None, "23505", "08006", "unexpected"):
        sentinel = f"synthetic-private-{sqlstate}"
        error = map_database_error(FakePsycopgError(sqlstate, sentinel))

        assert type(error) is DatabaseUnavailableError
        assert str(error) == "DATABASE_OPERATION_FAILED"
        assert sentinel not in str(error)


def test_rule_error_uses_only_the_code_selected_safe_message() -> None:
    error = DatabaseRuleError(DatabaseRuleCode.SELF_APPROVAL)

    assert error.code is DatabaseRuleCode.SELF_APPROVAL
    assert str(error) == "SELF_APPROVAL"
    assert error.args == ("SELF_APPROVAL",)


def test_database_unavailable_error_ignores_caller_values() -> None:
    error = DatabaseUnavailableError()

    assert str(error) == "DATABASE_OPERATION_FAILED"
    assert error.args == ("DATABASE_OPERATION_FAILED",)
