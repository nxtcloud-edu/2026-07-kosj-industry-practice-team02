"""Deterministic policy and intent classification for redacted chat questions.

This module accepts only :class:`SafeQuestion`, which can only be constructed
from a successful privacy-redaction result.  It performs no logging, storage,
network, repository, or provider I/O.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from sejong_ai_api.db.models import FallbackReason, Intent
from sejong_ai_api.privacy.redaction import RedactionResult

_SUPPORTED_INTENTS = frozenset(
    {
        Intent.MOVE_IN_RESIDENT_REGISTRATION,
        Intent.CERTIFICATE_ISSUANCE,
        Intent.BULKY_WASTE,
        Intent.LOCAL_TAX_GENERAL,
    }
)
_TOKEN_WORD_PATTERN = re.compile(r"[0-9a-z가-힣]+")

_INTENT_TERMS: dict[Intent, tuple[tuple[str, int], ...]] = {
    Intent.MOVE_IN_RESIDENT_REGISTRATION: (
        ("전입신고", 4),
        ("주소이전", 4),
        ("주소변경", 4),
        ("이사신고", 4),
        ("통보서비스", 4),
        ("전입", 3),
        ("세대주변경", 3),
    ),
    Intent.CERTIFICATE_ISSUANCE: (
        ("주민등록등본", 4),
        ("주민등록초본", 4),
        ("주민등록표", 4),
        ("무인민원발급", 4),
        ("무인발급기", 4),
        ("인감증명", 4),
        ("등본", 3),
        ("초본", 3),
        ("주민등록열람", 3),
    ),
    Intent.BULKY_WASTE: (
        ("대형폐기물", 4),
        ("배출신고", 4),
        ("폐기물", 3),
        ("침대프레임", 3),
        ("침대", 3),
        ("프레임", 3),
        ("매트리스", 3),
        ("가구배출", 3),
        ("폐기물스티커", 3),
        ("소파배출", 3),
    ),
    Intent.LOCAL_TAX_GENERAL: (
        ("지방세", 4),
        ("자동차세", 4),
        ("재산세", 4),
        ("주민세", 4),
        ("취득세", 4),
        ("납세증명", 4),
        ("전자납부번호", 4),
        ("과세증명서", 4),
        ("납부확인서", 4),
        ("체납액", 3),
        ("세금", 2),
    ),
}

_OUT_OF_SCOPE_TERMS = (
    "날씨",
    "맛집",
    "버스",
    "교통",
    "병원",
    "여권",
    "운전면허",
    "출생신고",
    "복지급여",
    "졸업증명서",
    "재학증명서",
    "성적증명서",
    "건강진단서",
    "진단서",
    "반려동물",
    "동물등록",
)
_FIRST_PERSON_TERMS = frozenset({"내", "내가", "나의", "저의", "제", "제가", "본인"})
_PERSONAL_LOOKUP_TERMS = (
    "체납액",
    "납부내역",
    "신청상태",
    "처리상태",
    "발급상태",
    "신고상태",
    "민원번호",
)
_LOOKUP_ACTIONS = ("조회", "알려", "확인", "보여", "됐", "완료")
_LEGAL_TERMS = (
    "법적으로",
    "법률판단",
    "위법",
    "불법",
    "처벌",
    "유죄",
    "소송",
    "법적책임",
    "합법",
    "벌금",
    "과태료",
)


@dataclass(frozen=True, slots=True, init=False)
class SafeQuestion:
    """Masked text proven safe by the privacy core."""

    _text: str

    def __init__(self, redaction: RedactionResult) -> None:
        if type(redaction) is not RedactionResult:
            raise TypeError("SAFE_QUESTION_REQUIRED")
        if (
            redaction.masked_text is None
            or redaction.safe_for_failure_storage is not True
            or redaction.safe_for_synthetic_provider is not True
            or redaction.unresolved_reason is not None
        ):
            raise ValueError("SAFE_QUESTION_REQUIRED")
        object.__setattr__(self, "_text", redaction.masked_text)

    @property
    def text(self) -> str:
        return self._text


@dataclass(frozen=True, slots=True)
class ClassificationOutcome:
    intent: Intent
    followup_required: bool
    fallback_reason: FallbackReason | None

    def __post_init__(self) -> None:
        if type(self.intent) is not Intent or type(self.followup_required) is not bool:
            raise ValueError("CLASSIFICATION_OUTCOME_INVALID")
        if self.fallback_reason is not None and type(self.fallback_reason) is not FallbackReason:
            raise ValueError("CLASSIFICATION_OUTCOME_INVALID")
        if self.followup_required:
            if self.intent is not Intent.UNKNOWN or self.fallback_reason is not None:
                raise ValueError("CLASSIFICATION_OUTCOME_INVALID")
            return
        if self.intent is Intent.OUT_OF_SCOPE:
            if self.fallback_reason is not FallbackReason.OUT_OF_SCOPE:
                raise ValueError("CLASSIFICATION_OUTCOME_INVALID")
            return
        if self.intent not in _SUPPORTED_INTENTS:
            raise ValueError("CLASSIFICATION_OUTCOME_INVALID")
        if self.fallback_reason not in {
            None,
            FallbackReason.PERSONAL_LOOKUP,
            FallbackReason.LEGAL_JUDGMENT,
        }:
            raise ValueError("CLASSIFICATION_OUTCOME_INVALID")


def classify_question(question: SafeQuestion) -> ClassificationOutcome:
    """Classify a privacy-safe question without any external side effects."""

    if type(question) is not SafeQuestion:
        raise TypeError("SAFE_QUESTION_REQUIRED")
    compact = _compact(question.text)

    scores = {
        intent: max((weight for term, weight in terms if term in compact), default=0)
        for intent, terms in _INTENT_TERMS.items()
    }
    highest_score = max(scores.values())
    if highest_score == 0 and any(term in compact for term in _OUT_OF_SCOPE_TERMS):
        return ClassificationOutcome(
            Intent.OUT_OF_SCOPE,
            followup_required=False,
            fallback_reason=FallbackReason.OUT_OF_SCOPE,
        )
    best_intents = tuple(
        intent for intent, score in scores.items() if score == highest_score and score
    )
    if len(best_intents) != 1:
        return ClassificationOutcome(Intent.UNKNOWN, followup_required=True, fallback_reason=None)

    intent = best_intents[0]
    if _is_personal_lookup(question.text, compact):
        return ClassificationOutcome(intent, False, FallbackReason.PERSONAL_LOOKUP)
    if any(term in compact for term in _LEGAL_TERMS):
        return ClassificationOutcome(intent, False, FallbackReason.LEGAL_JUDGMENT)
    return ClassificationOutcome(intent, False, None)


def _compact(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^0-9a-z가-힣]", "", normalized)


def _is_personal_lookup(value: str, compact: str) -> bool:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    words = _TOKEN_WORD_PATTERN.findall(normalized)
    has_subject = any(word in _FIRST_PERSON_TERMS for word in words)
    has_subject = has_subject or any(
        word.startswith(("내자동차세", "내재산세", "내주민세", "제자동차세", "제재산세"))
        for word in words
    )
    has_personal_target = any(term in compact for term in _PERSONAL_LOOKUP_TERMS)
    has_lookup_action = any(term in compact for term in _LOOKUP_ACTIONS)
    intrinsically_personal = any(
        term in compact for term in _PERSONAL_LOOKUP_TERMS if term not in {"체납액", "납부내역"}
    )
    return (has_subject and has_personal_target) or (intrinsically_personal and has_lookup_action)


__all__ = ["ClassificationOutcome", "SafeQuestion", "classify_question"]
