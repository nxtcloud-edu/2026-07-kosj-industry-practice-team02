from __future__ import annotations

import json
import logging
import time
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import TypedDict, cast

import pytest

from sejong_ai_api.privacy import (
    PiiCategory,
    RedactionFinding,
    RedactionResult,
    UnresolvedReason,
    redact_question,
)


class FixtureCase(TypedDict):
    id: str
    input: str
    outcome: str
    categories: list[str]
    tokens: list[str]
    expected_masked_text: str | None
    unresolved_reason: str | None


class FixtureDocument(TypedDict):
    fixture_version: int
    synthetic_only: bool
    cases: list[FixtureCase]


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pii_masking_cases.v1.json"
CASES = cast(
    FixtureDocument,
    json.loads(FIXTURE_PATH.read_text(encoding="utf-8")),
)
EXPECTED_TOKENS = {
    "[이름]", "[주민등록번호]", "[여권·면허번호]", "[전화번호]", "[이메일]",
    "[상세주소]", "[계좌번호]", "[카드번호]", "[인증정보]", "[차량번호]",
    "[접수번호]", "[건강·복지정보]", "[정밀위치]",
}


def test_fixture_contract_is_frozen_synthetic_and_complete() -> None:
    assert CASES["fixture_version"] == 1
    assert CASES["synthetic_only"] is True
    cases = CASES["cases"]
    assert len(cases) == 74
    positive_prefixes = (
        "name", "rrn", "identity", "phone", "email", "address", "account",
        "card", "auth", "vehicle", "case", "sensitive", "location",
    )
    expected_ids = {
        *(f"{prefix}-{number:02d}" for prefix in positive_prefixes for number in range(1, 4)),
        *(f"unicode-{number:02d}" for number in range(1, 11)),
        *(f"overlap-{number:02d}" for number in range(1, 6)),
        *(f"negative-{number:02d}" for number in range(1, 21)),
    }
    assert {case["id"] for case in cases} == expected_ids
    assert [case["outcome"] for case in cases].count("MASKED") == 50
    assert [case["outcome"] for case in cases].count("SAFE_UNCHANGED") == 20
    assert [case["outcome"] for case in cases].count("UNRESOLVED") == 4
    exact_keys = {
        "id", "input", "outcome", "categories", "tokens",
        "expected_masked_text", "unresolved_reason",
    }
    expected_key_order = (
        "id", "input", "outcome", "categories", "tokens",
        "expected_masked_text", "unresolved_reason",
    )
    for case in cases:
        assert set(case) == exact_keys
        assert tuple(case) == expected_key_order
        assert case["outcome"] in {"MASKED", "SAFE_UNCHANGED", "UNRESOLVED"}
        assert set(case["categories"]) <= {category.value for category in PiiCategory}
        assert set(case["tokens"]) <= EXPECTED_TOKENS
        reason = case["unresolved_reason"]
        assert reason is None or reason in {item.value for item in UnresolvedReason}
        assert (case["outcome"] == "UNRESOLVED") is (reason is not None)
        assert (case["outcome"] == "UNRESOLVED") is (
            case["expected_masked_text"] is None
        )
    for prefix in positive_prefixes:
        assert sum(case["id"].startswith(f"{prefix}-") for case in cases) == 3


def _case_id(case: FixtureCase) -> str:
    return case["id"]


@pytest.mark.parametrize("case", CASES["cases"], ids=_case_id)
def test_frozen_v1_case(case: FixtureCase) -> None:
    raw = case["input"]
    assert type(raw) is str
    result = redact_question(raw)
    assert isinstance(result, RedactionResult)
    assert [finding.category.value for finding in result.findings] == case["categories"]
    assert result.masked_text == case["expected_masked_text"]
    if case["outcome"] == "SAFE_UNCHANGED":
        assert result.safe_for_failure_storage is True
        assert result.safe_for_synthetic_provider is True
        assert result.unresolved_reason is None
    elif case["outcome"] == "MASKED":
        assert result.masked_text is not None
        assert result.masked_text != raw
        assert all(token in result.masked_text for token in case["tokens"])
        assert result.safe_for_failure_storage is True
        assert result.safe_for_synthetic_provider is True
        assert result.unresolved_reason is None
    else:
        reason = case["unresolved_reason"]
        assert reason is not None
        assert result.masked_text is None
        assert result.safe_for_failure_storage is False
        assert result.safe_for_synthetic_provider is False
        assert result.unresolved_reason is UnresolvedReason(reason)


def test_enum_values_are_closed_and_exact() -> None:
    assert [item.value for item in PiiCategory] == [
        "NAME", "RESIDENT_REGISTRATION_NUMBER", "PASSPORT_OR_LICENSE",
        "PHONE_NUMBER", "EMAIL", "DETAILED_ADDRESS", "FINANCIAL_ACCOUNT",
        "PAYMENT_CARD", "AUTH_SECRET", "VEHICLE_PLATE", "CASE_REFERENCE",
        "SENSITIVE_HEALTH_WELFARE", "PRECISE_LOCATION",
    ]


def test_value_objects_are_frozen_slotted_and_value_free() -> None:
    finding = RedactionFinding(PiiCategory.EMAIL, 3, 10, "[이메일]")
    result = RedactionResult("메일 [이메일]", (finding,), True, True, None)
    assert not hasattr(finding, "__dict__")
    assert not hasattr(result, "__dict__")
    assert not hasattr(finding, "matched_value")
    with pytest.raises(FrozenInstanceError):
        finding.start = 0  # type: ignore[misc]
    with pytest.raises(ValueError, match="^REDACTION_FINDING_INVALID$"):
        RedactionFinding(PiiCategory.EMAIL, 3, 10, "raw@example.invalid")
    with pytest.raises(ValueError, match="^REDACTION_RESULT_INVALID$"):
        RedactionResult("raw", (), False, True, None)
    assert [item.value for item in UnresolvedReason] == [
        "INPUT_INVALID", "UNSAFE_UNICODE", "AMBIGUOUS_PERSON_NAME",
        "AMBIGUOUS_DETAILED_ADDRESS", "RESIDUAL_HIGH_RISK_PATTERN",
    ]


@pytest.mark.parametrize("raw", [None, 1, b"question", "", " ", "x" * 1001])
def test_invalid_input_is_closed_without_text(raw: object) -> None:
    result = redact_question(raw)  # type: ignore[arg-type]
    assert result == RedactionResult(None, (), False, False, UnresolvedReason.INPUT_INVALID)


@pytest.mark.parametrize("raw", ["x\x00y", "x\u202ey", "x\u2063y", "x\ud800y"])
def test_unsafe_unicode_is_closed_without_findings(raw: str) -> None:
    result = redact_question(raw)
    assert result == RedactionResult(None, (), False, False, UnresolvedReason.UNSAFE_UNICODE)


def test_exact_replacement_and_normalized_offsets() -> None:
    result = redact_question("연락처 010\u200b-0000-0000")
    assert result.masked_text == "연락처 [전화번호]"
    assert result.findings == (
        RedactionFinding(PiiCategory.PHONE_NUMBER, 4, 17, "[전화번호]"),
    )


def test_input_is_not_mutated_and_repeated_results_are_identical() -> None:
    raw = "제 이름은 김가상이고 주소는 세종시 테스트길 34-5입니다."
    first = redact_question(raw)
    second = redact_question(raw)
    assert raw == "제 이름은 김가상이고 주소는 세종시 테스트길 34-5입니다."
    assert first == second


def test_raw_identifier_never_appears_in_value_objects_exception_or_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    sentinel = "unique.secret@example.invalid"
    with caplog.at_level(logging.DEBUG):
        result = redact_question(f"이메일 {sentinel}")
    assert sentinel not in repr(result)
    assert sentinel not in repr(result.findings)
    assert all(sentinel not in record.getMessage() for record in caplog.records)


def test_pathological_1000_character_inputs_finish_within_two_seconds() -> None:
    inputs = (
        ("0-" * 499) + "0x",
        ("가" * 970) + "아파트 999동 999호?",
        ("a." * 490) + "@invalid",
        ("저는 " * 200) + "가가가가라",
        ("면허번호 " * 100) + "00-00-000000-x",
    )
    assert all(len(raw) <= 1000 for raw in inputs)
    started = time.perf_counter()
    for raw in inputs:
        for _ in range(20):
            redact_question(raw)
    assert time.perf_counter() - started < 2.0
