from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from sejong_ai_api.chat.classification import SafeQuestion, classify_question
from sejong_ai_api.db.models import FallbackReason, Intent
from sejong_ai_api.privacy.redaction import redact_question


def safe_question(text: str) -> SafeQuestion:
    return SafeQuestion(redact_question(text))


@pytest.mark.parametrize(
    ("question", "expected_intent"),
    [
        ("전입신고 절차가 궁금해요.", Intent.MOVE_IN_RESIDENT_REGISTRATION),
        ("주민등록등본 발급 방법을 알려주세요.", Intent.CERTIFICATE_ISSUANCE),
        ("대형폐기물 소파 배출 방법을 알려주세요.", Intent.BULKY_WASTE),
        ("자동차세 납부 방법을 알려주세요.", Intent.LOCAL_TAX_GENERAL),
    ],
)
def test_classifies_the_four_supported_intents(
    question: str,
    expected_intent: Intent,
) -> None:
    outcome = classify_question(safe_question(question))

    assert outcome.intent is expected_intent
    assert outcome.followup_required is False
    assert outcome.fallback_reason is None


def test_clear_out_of_scope_question_uses_the_policy_fallback() -> None:
    outcome = classify_question(safe_question("오늘 세종시 날씨를 알려주세요."))

    assert outcome.intent is Intent.OUT_OF_SCOPE
    assert outcome.followup_required is False
    assert outcome.fallback_reason is FallbackReason.OUT_OF_SCOPE


def test_unsupported_pet_registration_is_out_of_scope() -> None:
    outcome = classify_question(safe_question("반려동물 등록 어디서 해요?"))

    assert outcome.intent is Intent.OUT_OF_SCOPE
    assert outcome.followup_required is False
    assert outcome.fallback_reason is FallbackReason.OUT_OF_SCOPE


@pytest.mark.parametrize(
    "question",
    [
        "신고하고 싶어요.",
        "전입신고 후 주민등록등본도 발급하고 싶어요.",
    ],
)
def test_ambiguous_supported_question_requests_followup(question: str) -> None:
    outcome = classify_question(safe_question(question))

    assert outcome.intent is Intent.UNKNOWN
    assert outcome.followup_required is True
    assert outcome.fallback_reason is None


def test_personal_lookup_is_decided_before_retrieval() -> None:
    outcome = classify_question(safe_question("내 자동차세 체납액을 조회해줘."))

    assert outcome.intent is Intent.LOCAL_TAX_GENERAL
    assert outcome.followup_required is False
    assert outcome.fallback_reason is FallbackReason.PERSONAL_LOOKUP


def test_legal_judgment_is_decided_before_retrieval() -> None:
    outcome = classify_question(
        safe_question("대형폐기물 신고를 안 하면 법적으로 처벌받는지 판단해줘.")
    )

    assert outcome.intent is Intent.BULKY_WASTE
    assert outcome.followup_required is False
    assert outcome.fallback_reason is FallbackReason.LEGAL_JUDGMENT


def test_classifier_rejects_raw_or_unresolved_text_at_its_boundary() -> None:
    with pytest.raises(TypeError, match="^SAFE_QUESTION_REQUIRED$"):
        classify_question("raw citizen text")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="^SAFE_QUESTION_REQUIRED$"):
        SafeQuestion(redact_question(""))


def test_safe_question_cannot_be_replaced_after_redaction() -> None:
    question = safe_question("자동차세 납부 방법")

    with pytest.raises(FrozenInstanceError):
        question._text = "raw replacement"  # type: ignore[misc]


def test_general_tax_arrears_guidance_is_not_mistaken_for_personal_lookup() -> None:
    outcome = classify_question(safe_question("자동차세 체납액 기준을 안내해줘."))

    assert outcome.intent is Intent.LOCAL_TAX_GENERAL
    assert outcome.fallback_reason is None


@pytest.mark.parametrize("question", ["졸업증명서 발급 방법", "건강진단서 발급 방법"])
def test_unsupported_certificate_domains_are_out_of_scope(question: str) -> None:
    outcome = classify_question(safe_question(question))

    assert outcome.intent is Intent.OUT_OF_SCOPE
    assert outcome.fallback_reason is FallbackReason.OUT_OF_SCOPE


def test_canonical_bed_frame_question_is_supported_bulky_waste() -> None:
    outcome = classify_question(safe_question("침대 2인용 프레임 수수료가 얼마예요?"))

    assert outcome.intent is Intent.BULKY_WASTE
    assert outcome.fallback_reason is None


def test_legal_wording_is_not_grounded_as_general_move_in_guidance() -> None:
    outcome = classify_question(safe_question("전입신고 벌금이 합법인가요?"))

    assert outcome.intent is Intent.MOVE_IN_RESIDENT_REGISTRATION
    assert outcome.fallback_reason is FallbackReason.LEGAL_JUDGMENT
