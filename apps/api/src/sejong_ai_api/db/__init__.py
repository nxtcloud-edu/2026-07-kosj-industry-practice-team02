"""Safe typed database boundary values."""

from sejong_ai_api.db.errors import (
    DatabaseRuleCode,
    DatabaseRuleError,
    DatabaseUnavailableError,
)
from sejong_ai_api.db.models import (
    Actor,
    AdminRole,
    AnswerStatus,
    CandidateDraft,
    DataOrigin,
    FailureReasonConfirmation,
    FallbackReason,
    Intent,
    InteractionWrite,
    InteractionWriteResult,
    KnowledgeRecord,
    OfficeRecord,
    PurgeResult,
    Region,
)

__all__ = [
    "Actor",
    "AdminRole",
    "AnswerStatus",
    "CandidateDraft",
    "DataOrigin",
    "DatabaseRuleCode",
    "DatabaseRuleError",
    "DatabaseUnavailableError",
    "FailureReasonConfirmation",
    "FallbackReason",
    "InteractionWrite",
    "InteractionWriteResult",
    "Intent",
    "KnowledgeRecord",
    "OfficeRecord",
    "PurgeResult",
    "Region",
]
