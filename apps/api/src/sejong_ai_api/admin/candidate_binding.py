"""Server-owned identity for the one reserved MVP candidate activation."""

from __future__ import annotations

from datetime import date

from sejong_ai_api.contracts.admin import KBCandidateSummary

RESERVED_KB_PUBLIC_ID = "KB-WASTE-03"

_TITLE = "침대 프레임 배출 수수료"
_REPRESENTATIVE_QUESTION = "침대 2인용 프레임 수수료가 얼마예요?"
_ANSWER_SUMMARY = (
    "공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다."
)
_PROCEDURE_STEPS = (
    "공식 품목표에서 침대 프레임의 1인용침대 또는 2인용침대 항목을 확인합니다.",
    "해당 수수료로 공식 배출 절차를 진행합니다.",
)
_FEE = "1인용침대 8,000원; 2인용침대 10,000원"
_DEPARTMENT = "세종특별자치시시설관리공단"
_SOURCE_TITLE = "배출항목선택"
_SOURCE_URL = "https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305"
_LAST_VERIFIED_AT = date(2026, 7, 18)
_CAUTION = (
    "공식 품목표의 1인용침대·2인용침대 항목을 그대로 따릅니다. "
    "매트리스 포함 가격이나 실제 규격을 단정하지 않습니다."
)


def claims_reserved_binding(candidate: KBCandidateSummary) -> bool:
    """Return whether the three immutable routing fields claim the reserved binding."""

    return (
        candidate.title == _TITLE
        and candidate.source_title == _SOURCE_TITLE
        and str(candidate.source_url) == _SOURCE_URL
    )


def is_exact_reserved_candidate(candidate: KBCandidateSummary) -> bool:
    """Match every approved and sanitized canonical content field exactly."""

    return claims_reserved_binding(candidate) and (
        candidate.representative_question == _REPRESENTATIVE_QUESTION
        and candidate.data_origin == "OFFICIAL"
        and candidate.category == "BULKY_WASTE"
        and candidate.answer_summary == _ANSWER_SUMMARY
        and tuple(candidate.procedure_steps) == _PROCEDURE_STEPS
        and candidate.required_documents == []
        and candidate.processing_time is None
        and candidate.fee == _FEE
        and candidate.department == _DEPARTMENT
        and candidate.last_verified_at == _LAST_VERIFIED_AT
        and candidate.caution == _CAUTION
    )


__all__ = [
    "RESERVED_KB_PUBLIC_ID",
    "claims_reserved_binding",
    "is_exact_reserved_candidate",
]
