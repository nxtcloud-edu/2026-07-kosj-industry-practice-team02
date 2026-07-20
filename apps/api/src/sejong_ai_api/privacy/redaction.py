from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Final


class PiiCategory(str, Enum):  # noqa: UP042 - approved wire-independent value contract
    NAME = "NAME"
    RESIDENT_REGISTRATION_NUMBER = "RESIDENT_REGISTRATION_NUMBER"
    PASSPORT_OR_LICENSE = "PASSPORT_OR_LICENSE"
    PHONE_NUMBER = "PHONE_NUMBER"
    EMAIL = "EMAIL"
    DETAILED_ADDRESS = "DETAILED_ADDRESS"
    FINANCIAL_ACCOUNT = "FINANCIAL_ACCOUNT"
    PAYMENT_CARD = "PAYMENT_CARD"
    AUTH_SECRET = "AUTH_SECRET"
    VEHICLE_PLATE = "VEHICLE_PLATE"
    CASE_REFERENCE = "CASE_REFERENCE"
    SENSITIVE_HEALTH_WELFARE = "SENSITIVE_HEALTH_WELFARE"
    PRECISE_LOCATION = "PRECISE_LOCATION"


class UnresolvedReason(str, Enum):  # noqa: UP042 - approved value contract
    INPUT_INVALID = "INPUT_INVALID"
    UNSAFE_UNICODE = "UNSAFE_UNICODE"
    AMBIGUOUS_PERSON_NAME = "AMBIGUOUS_PERSON_NAME"
    AMBIGUOUS_DETAILED_ADDRESS = "AMBIGUOUS_DETAILED_ADDRESS"
    RESIDUAL_HIGH_RISK_PATTERN = "RESIDUAL_HIGH_RISK_PATTERN"


def _replacement(category: PiiCategory) -> str:
    return {
        PiiCategory.RESIDENT_REGISTRATION_NUMBER: "[주민등록번호]",
        PiiCategory.PAYMENT_CARD: "[카드번호]",
        PiiCategory.FINANCIAL_ACCOUNT: "[계좌번호]",
        PiiCategory.AUTH_SECRET: "[인증정보]",
        PiiCategory.PASSPORT_OR_LICENSE: "[여권·면허번호]",
        PiiCategory.PHONE_NUMBER: "[전화번호]",
        PiiCategory.EMAIL: "[이메일]",
        PiiCategory.PRECISE_LOCATION: "[정밀위치]",
        PiiCategory.VEHICLE_PLATE: "[차량번호]",
        PiiCategory.CASE_REFERENCE: "[접수번호]",
        PiiCategory.DETAILED_ADDRESS: "[상세주소]",
        PiiCategory.NAME: "[이름]",
        PiiCategory.SENSITIVE_HEALTH_WELFARE: "[건강·복지정보]",
    }[category]


@dataclass(frozen=True, slots=True)
class RedactionFinding:
    category: PiiCategory
    start: int
    end: int
    replacement: str

    def __post_init__(self) -> None:
        if (
            type(self.category) is not PiiCategory
            or type(self.start) is not int
            or type(self.end) is not int
            or self.start < 0
            or self.end <= self.start
            or self.replacement != _replacement(self.category)
        ):
            raise ValueError("REDACTION_FINDING_INVALID")


@dataclass(frozen=True, slots=True)
class RedactionResult:
    masked_text: str | None
    findings: tuple[RedactionFinding, ...]
    safe_for_failure_storage: bool
    safe_for_synthetic_provider: bool
    unresolved_reason: UnresolvedReason | None

    def __post_init__(self) -> None:
        findings_are_valid = type(self.findings) is tuple and all(
            type(item) is RedactionFinding for item in self.findings
        )
        if not findings_are_valid:
            raise ValueError("REDACTION_RESULT_INVALID")
        if self.masked_text is None:
            if (
                self.safe_for_failure_storage is not False
                or self.safe_for_synthetic_provider is not False
                or type(self.unresolved_reason) is not UnresolvedReason
            ):
                raise ValueError("REDACTION_RESULT_INVALID")
            return
        if (
            type(self.masked_text) is not str
            or not self.masked_text
            or self.safe_for_failure_storage is not True
            or self.safe_for_synthetic_provider is not True
            or self.unresolved_reason is not None
        ):
            raise ValueError("REDACTION_RESULT_INVALID")


_MAX_QUESTION_LENGTH: Final = 1000
_REMOVED_FORMAT_CHARACTERS: Final = (
    "\u200b",
    "\u200c",
    "\u200d",
    "\u2060",
    "\ufeff",
)
_UNSAFE_BIDI_CLASSES: Final = frozenset(
    {"LRE", "RLE", "LRO", "RLO", "PDF", "LRI", "RLI", "FSI", "PDI"}
)


def _closed(
    reason: UnresolvedReason,
    findings: tuple[RedactionFinding, ...] = (),
) -> RedactionResult:
    return RedactionResult(None, findings, False, False, reason)


def _normalize(raw_question: object) -> tuple[str | None, UnresolvedReason | None]:
    if type(raw_question) is not str:
        return None, UnresolvedReason.INPUT_INVALID
    if not raw_question or len(raw_question) > _MAX_QUESTION_LENGTH or not raw_question.strip():
        return None, UnresolvedReason.INPUT_INVALID
    normalized = unicodedata.normalize(
        "NFKC",
        raw_question.replace("\r\n", "\n").replace("\r", "\n"),
    )
    for character in _REMOVED_FORMAT_CHARACTERS:
        normalized = normalized.replace(character, "")
    if not normalized or len(normalized) > _MAX_QUESTION_LENGTH or not normalized.strip():
        return None, UnresolvedReason.INPUT_INVALID
    for character in normalized:
        category = unicodedata.category(character)
        if category == "Cs":
            return None, UnresolvedReason.UNSAFE_UNICODE
        if category == "Cc" and character not in {"\t", "\n"}:
            return None, UnresolvedReason.UNSAFE_UNICODE
        if category == "Cf" or unicodedata.bidirectional(character) in _UNSAFE_BIDI_CLASSES:
            return None, UnresolvedReason.UNSAFE_UNICODE
    return normalized, None


@dataclass(frozen=True, slots=True)
class _Rule:
    category: PiiCategory
    pattern: re.Pattern[str]


_CATEGORY_PRIORITY: Final = (
    PiiCategory.RESIDENT_REGISTRATION_NUMBER,
    PiiCategory.PAYMENT_CARD,
    PiiCategory.FINANCIAL_ACCOUNT,
    PiiCategory.AUTH_SECRET,
    PiiCategory.PASSPORT_OR_LICENSE,
    PiiCategory.PHONE_NUMBER,
    PiiCategory.EMAIL,
    PiiCategory.PRECISE_LOCATION,
    PiiCategory.VEHICLE_PLATE,
    PiiCategory.CASE_REFERENCE,
    PiiCategory.DETAILED_ADDRESS,
    PiiCategory.NAME,
    PiiCategory.SENSITIVE_HEALTH_WELFARE,
)
_RULES: Final = (
    _Rule(
        PiiCategory.RESIDENT_REGISTRATION_NUMBER,
        re.compile(r"(?<!\d)(?P<value>\d{6}\s*[- ]?\s*[1-8]\d{6})(?!\d)"),
    ),
    _Rule(
        PiiCategory.PAYMENT_CARD,
        re.compile(
            r"(?<!\d)(?P<value>(?:\d{4}(?:[- .]?\d{4}){3}|"
            r"\d{4}[- .]?\d{6}[- .]?\d{5}))(?!\d)"
        ),
    ),
    _Rule(
        PiiCategory.FINANCIAL_ACCOUNT,
        re.compile(
            r"(?:계좌(?:번호)?|입금계좌|통장)\s*[:：]?\s*"
            r"(?P<value>\d{2,6}(?:[- ]\d{2,6}){1,4})"
        ),
    ),
    _Rule(
        PiiCategory.AUTH_SECRET,
        re.compile(
            r"(?:비밀번호|인증번호|OTP|PIN)\s*[:：]?\s*(?!\[)"
            r"(?P<value>[A-Z0-9!#$%&()*+,\-./:;<=>?@\^_`{|}~]{3,63}"
            r"[A-Z0-9!#$%&()*+\-/:;<=>?@\^_`{|}~])"
            r"(?=$|[\s,.!?]|입니다|이에요|예요|이고|라고)",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        PiiCategory.PASSPORT_OR_LICENSE,
        re.compile(
            r"(?:여권번호|운전면허번호|면허번호)\s*[:：]?\s*"
            r"(?P<value>(?:[A-Z]\d{8}|(?:[가-힣]{2,4}\s*)?"
            r"\d{2}(?:-\d{2})?-\d{6}-\d{2}))",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        PiiCategory.PHONE_NUMBER,
        re.compile(
            r"(?<!\d)(?P<value>(?:01[016789]|070)(?:[- .]?\d{3,4})"
            r"[- .]?\d{4})(?!\d)"
        ),
    ),
    _Rule(
        PiiCategory.PHONE_NUMBER,
        re.compile(
            r"(?<!\d)(?P<value>0(?:2|[3-6][1-5])[- .]?\d{3,4}"
            r"[- .]?\d{4})(?!\d)"
        ),
    ),
    _Rule(
        PiiCategory.EMAIL,
        re.compile(
            r"(?<![\w.+-])(?P<value>[A-Z0-9._%+\-]+@[A-Z0-9.\-]+"
            r"\.[A-Z]{2,})(?![\w.-])",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        PiiCategory.PRECISE_LOCATION,
        re.compile(
            r"(?:(?<![\d.])(?P<value>-?\d{1,2}\.\d+\s*,\s*-?\d{1,3}\.\d+)"
            r"(?![\d.])|(?:위도\s*(?P<value_lat>-?\d{1,2}(?:\.\d+)?)\s*"
            r"경도\s*(?P<value_lng>-?\d{1,3}(?:\.\d+)?)))",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        PiiCategory.VEHICLE_PLATE,
        re.compile(r"(?<!\d)(?P<value>\d{2,3}[가-힣]\s?\d{4})(?!\d)"),
    ),
    _Rule(
        PiiCategory.CASE_REFERENCE,
        re.compile(
            r"(?:접수번호|민원번호)\s*[:：]?\s*"
            r"(?P<value>(?:[A-Z]+-)?\d{4}-\d{6}|[A-Z]+-\d{6}|\d{6}-\d{7})",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        PiiCategory.DETAILED_ADDRESS,
        re.compile(
            r"(?:(?:주소(?:는)?|사는\s*곳|거주지|상세주소)\s*[:：]?\s*)?"
            r"(?P<value>(?:(?:세종특별자치시|세종시)\s*)?(?:[가-힣]+(?:읍|면|동)\s+)?"
            r"[가-힣0-9]+(?:대로|로|길)\s+\d+(?:-\d+)?"
            r"(?:\s+\d+동\s+\d+호|\s+\d+층)?)"
        ),
    ),
    _Rule(
        PiiCategory.NAME,
        re.compile(
            r"(?:이름(?:은|이)?|성명|신청인\s*성명|신청인(?!\s*성명))"
            r"\s*[:：]?\s*"
            r"(?P<value>[가-힣]{2,4})(?=입니다|이에요|예요|이고|라고|[\s,.!?]|$)"
        ),
    ),
    _Rule(
        PiiCategory.NAME,
        re.compile(r"저는\s*(?P<value>[가-힣]{2,4})(?=입니다|이에요|예요|이고|라고)"),
    ),
    _Rule(
        PiiCategory.SENSITIVE_HEALTH_WELFARE,
        re.compile(
            r"(?P<value>(?:당뇨|암|고혈압|우울증)\s*(?:진단|치료|환자)|"
            r"장애등급\s*\d+급|기초생활수급자)"
        ),
    ),
    _Rule(
        PiiCategory.SENSITIVE_HEALTH_WELFARE,
        re.compile(r"(?:진단명|복지대상)\s*[:：]?\s*(?!\[)(?P<value>[^\s,.!?]{2,40})"),
    ),
)

_AMBIGUOUS_NAME: Final = re.compile(
    r"(?:(?<![가-힣])(?P<value>[가-힣]{2,4})(?:씨|님)"
    r"(?=이라고|라고|입니다|이에요|예요|[\s,.!?]|$)|"
    r"(?:민원인|신청인)(?:은|는)\s*(?P<labeled_value>[가-힣]{2,4})"
    r"(?=입니다|이에요|예요|[\s,.!?]|$)|"
    r"(?<![가-힣])(?P<standalone_value>[가-힣]{3})"
    r"(?=입니다(?:[\s,.!?]|$)|이에요(?:[\s,.!?]|$)|예요(?:[\s,.!?]|$)))"
)
_SAFE_STANDALONE_NAME_TERMS: Final = frozenset({"이메일", "신청서", "민원인"})
_AMBIGUOUS_ADDRESS: Final = re.compile(
    r"(?P<value>(?:[가-힣0-9]+(?:아파트|빌라)\s*\d+동\s*\d+호|"
    r"(?:[가-힣]+(?:읍|면|동)\s*)?\d+(?:-\d+)?번지(?:\s*\d+(?:동|호))*))"
)
_AMBIGUOUS_EXPLICIT_PII: Final = re.compile(
    r"(?:주민(?:등록)?번호|여권번호|면허번호|연락처|전화번호|휴대폰|이메일|메일|"
    r"주소|거주지|계좌번호|카드번호|비밀번호|인증번호|OTP|PIN|차량번호|번호판|"
    r"접수번호|민원번호|진단명|복지대상|GPS|위치)"
    r"(?:은|는|이|가|을|를)?(?:\s*[:：]\s*|\s+)"
    r"(?!\[(?:이름|주민등록번호|여권·면허번호|전화번호|이메일|상세주소|계좌번호|"
    r"카드번호|인증정보|차량번호|접수번호|건강·복지정보|정밀위치)\]"
    r"(?=$|[\s,.!?]))"
    r"(?P<unclassified_value>(?=[^\n]*(?:@|\d|[A-Z]))[^\n]{2,})",
    re.IGNORECASE,
)
_HIGH_RISK_SPAN_PATTERNS: Final = (
    re.compile(r"(?<!\d)(?:\d[- ./]?){9,}\d(?!\d)"),
    re.compile(r"(?<!\S)[^\s@]+@[^\s@,.!?]+(?=$|[\s,.!?])"),
    re.compile(
        r"(?<![\w.+-])[A-Z0-9._%+\-]+@[A-Z0-9.\-]+"
        r"\.[A-Z]{2,}(?![\w.-])",
        re.IGNORECASE,
    ),
)


def _match_bounds(match: re.Match[str]) -> tuple[int, int]:
    if match.groupdict().get("value") is not None:
        return match.span("value")
    return match.start("value_lat"), match.end("value_lng")


def _collect_findings(text: str) -> tuple[RedactionFinding, ...]:
    findings: list[RedactionFinding] = []
    for rule in _RULES:
        for match in rule.pattern.finditer(text):
            start, end = _match_bounds(match)
            findings.append(
                RedactionFinding(rule.category, start, end, _replacement(rule.category))
            )
    return tuple(findings)


def _overlaps(left: RedactionFinding, right: RedactionFinding) -> bool:
    return left.start < right.end and right.start < left.end


def _select_findings(
    candidates: tuple[RedactionFinding, ...],
) -> tuple[RedactionFinding, ...]:
    ranked = sorted(
        candidates,
        key=lambda item: (
            _CATEGORY_PRIORITY.index(item.category),
            -(item.end - item.start),
            item.start,
        ),
    )
    selected: list[RedactionFinding] = []
    for candidate in ranked:
        if not any(_overlaps(candidate, existing) for existing in selected):
            selected.append(candidate)
    return tuple(
        sorted(
            selected,
            key=lambda item: (
                item.start,
                item.end,
                _CATEGORY_PRIORITY.index(item.category),
            ),
        )
    )


def _apply_findings(text: str, findings: tuple[RedactionFinding, ...]) -> str:
    masked = text
    for finding in reversed(findings):
        masked = masked[: finding.start] + finding.replacement + masked[finding.end :]
    return masked


def _has_uncovered_high_risk_span(
    text: str,
    findings: tuple[RedactionFinding, ...],
) -> bool:
    for pattern in _HIGH_RISK_SPAN_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            if not any(finding.start <= start and finding.end >= end for finding in findings):
                return True
    return False


def _has_ambiguous_name(text: str) -> bool:
    for match in _AMBIGUOUS_NAME.finditer(text):
        standalone = match.groupdict().get("standalone_value")
        if standalone is not None and (
            standalone in _SAFE_STANDALONE_NAME_TERMS or standalone.endswith(("읍", "면", "동"))
        ):
            continue
        return True
    return False


def redact_question(raw_question: str) -> RedactionResult:
    normalized, reason = _normalize(raw_question)
    if reason is not None:
        return _closed(reason)
    assert normalized is not None
    findings = _select_findings(_collect_findings(normalized))
    if _has_uncovered_high_risk_span(normalized, findings):
        return _closed(UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN, findings)
    masked = _apply_findings(normalized, findings)
    if _has_ambiguous_name(masked):
        return _closed(UnresolvedReason.AMBIGUOUS_PERSON_NAME, findings)
    if _AMBIGUOUS_ADDRESS.search(masked):
        return _closed(UnresolvedReason.AMBIGUOUS_DETAILED_ADDRESS, findings)
    if (
        _AMBIGUOUS_EXPLICIT_PII.search(masked)
        or _select_findings(_collect_findings(masked))
        or _has_uncovered_high_risk_span(masked, ())
    ):
        return _closed(UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN, findings)
    return RedactionResult(masked, findings, True, True, None)
