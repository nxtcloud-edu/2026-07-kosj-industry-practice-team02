"""Safe database error mapping without database-message inspection."""

from __future__ import annotations

from enum import Enum


class DatabaseRuleCode(str, Enum):  # noqa: UP042 - approved str/Enum contract
    FORBIDDEN_ACTOR_ROLE = "FORBIDDEN_ACTOR_ROLE"
    SELF_APPROVAL = "SELF_APPROVAL"
    INVALID_CANDIDATE_STATE = "INVALID_CANDIDATE_STATE"
    INCOMPLETE_CANDIDATE = "INCOMPLETE_CANDIDATE"
    DISALLOWED_ORIGIN = "DISALLOWED_ORIGIN"
    INVALID_INTERACTION = "INVALID_INTERACTION"


_SQLSTATE_TO_RULE_CODE = {
    "P1001": DatabaseRuleCode.FORBIDDEN_ACTOR_ROLE,
    "P1002": DatabaseRuleCode.SELF_APPROVAL,
    "P1003": DatabaseRuleCode.INVALID_CANDIDATE_STATE,
    "P1004": DatabaseRuleCode.INCOMPLETE_CANDIDATE,
    "P1005": DatabaseRuleCode.DISALLOWED_ORIGIN,
    "P1010": DatabaseRuleCode.INVALID_INTERACTION,
}


class DatabaseRuleError(Exception):
    """Expose a stable rule code and no database-provided content."""

    def __init__(self, code: DatabaseRuleCode) -> None:
        self.code = code
        super().__init__(code.value)


class DatabaseUnavailableError(Exception):
    """Represent every unavailable, native, or malformed database outcome safely."""

    def __init__(self) -> None:
        super().__init__("DATABASE_OPERATION_FAILED")


def map_database_error(exc: BaseException) -> DatabaseRuleError | DatabaseUnavailableError:
    """Map only an allowlisted SQLSTATE, without reading any exception message."""
    sqlstate = getattr(exc, "sqlstate", None)
    code = _SQLSTATE_TO_RULE_CODE.get(sqlstate) if type(sqlstate) is str else None
    if code is None:
        return DatabaseUnavailableError()
    return DatabaseRuleError(code)
