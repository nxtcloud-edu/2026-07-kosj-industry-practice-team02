"""Dependency-free helpers for validating DATA-001 staging JSON contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Mapping, Sequence
from urllib.parse import urlparse


CONTENT_ARTIFACTS = (
    "kb_records.json",
    "offices.json",
    "office_service_mappings.json",
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DRAFT_DIR = REPOSITORY_ROOT / "data" / "staging" / "data-001" / "0.1.0-draft.1"
CANONICAL_SOURCE_MATRIX = (
    REPOSITORY_ROOT / "data" / "schemas" / "data-001" / "v1" / "approved-source-matrix.json"
)
APPROVED_SOURCE_MATRIX_SHA256 = (
    "19952d1ead2cb3878de7e3f80c7c5bde28b351781d8bf8d4947494f1ccfe29de"
)
CANONICAL_SOURCE_AUDIT_RELATIVE_PATHS = (
    "docs/data-lineage/source-audits/data-001-move-cert-source-audit.md",
    "docs/data-lineage/source-audits/data-001-office-mapping-audit.md",
    "docs/data-lineage/source-audits/data-001-tax-source-audit.md",
    "docs/data-lineage/source-audits/data-001-waste-source-audit.md",
)
CANONICAL_SOURCE_AUDIT_PATHS = tuple(
    REPOSITORY_ROOT / path for path in CANONICAL_SOURCE_AUDIT_RELATIVE_PATHS
)
CANONICAL_KB_IDS = tuple(
    f"KB-{category}-{number:02d}"
    for category in ("CERT", "MOVE", "TAX", "WASTE")
    for number in range(1, 6)
)
CANONICAL_KB_CATEGORIES = {
    "CERT": "CERTIFICATE_ISSUANCE",
    "MOVE": "MOVE_IN_RESIDENT_REGISTRATION",
    "TAX": "LOCAL_TAX_GENERAL",
    "WASTE": "BULKY_WASTE",
}
SOURCE_REGISTRY_COLUMNS = (
    "kb_id", "분야", "세부 주제", "공식 출처명", "제공기관", "URL", "확인일",
    "사용 필드", "작성 상태", "작성자", "검수자", "한계·주의",
)
SOURCE_REGISTRY_REQUIRED_METADATA = tuple(
    column for column in SOURCE_REGISTRY_COLUMNS if column != "검수자"
)
_SAFE_REPORT_FIELD_COMPONENTS = frozenset({
    "address", "answer_summary", "approved_at", "approved_by", "artifacts",
    "category", "caution", "comment", "created_by", "data_origin", "dataset_id",
    "decision", "decisions", "department", "department_label", "draft_version",
    "evidence_source_url", "fee", "headers", "id", "intent", "last_verified_at",
    "map_url", "office_name", "office_public_id", "opening_hours", "path", "phone",
    "procedure_steps", "provider", "public_id", "question_examples", "record_count",
    "record_id", "record_type", "recommended_decision", "records", "region",
    "required_documents", "review_comment", "reviewed_at", "reviewed_by", "rows",
    "schema_version", "service_name", "sha256", "source_service_id", "source_title",
    "source_url", "state", "status", "submitted_at", "processing_time",
}) | frozenset(SOURCE_REGISTRY_COLUMNS)
ALLOWED_SOURCE_HOSTS = frozenset({
    "plus.gov.kr",
    "www.law.go.kr",
    "law.go.kr",
    "www.sjwaste.kr",
    "www.wetax.go.kr",
    "www.gov.kr",
    "www.sejong.go.kr",
})
SUPPORTED_INTENTS = frozenset({
    "MOVE_IN_RESIDENT_REGISTRATION",
    "CERTIFICATE_ISSUANCE",
    "BULKY_WASTE",
    "LOCAL_TAX_GENERAL",
})
_PII_PATTERNS = (
    re.compile(r"\b\d{6}[- ]?[1-8]\d{6}\b"),
    re.compile(r"\b01[016789][ -]?\d{3,4}[ -]?\d{4}\b"),
    re.compile(r"\b0(?:2|[3-8][0-9])[ -]?\d{3,4}[ -]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b\d{2,3}[가-힣]\d{4}\b"),
    re.compile(r"\b\d{1,4}동\s*\d{1,4}호\b"),
    re.compile(r"\b\d{2}-\d{2}-\d{6}-\d{2}\b"),
    re.compile(r"\b[A-Z]{1,2}\d{7,8}\b"),
    re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"),
    re.compile(r"(?i)(?:계좌|account)\s*(?:번호|no\.?|[:=])?\s*\d[\d -]{8,18}\d"),
    re.compile(r"(?:인증번호|인증\s*코드)\s*[:=]?\s*\d{4,8}"),
    re.compile(r"(?i)(?:접수|민원|receipt|case)\s*(?:번호|no\.?)?\s*[:=]?\s*[A-Z]{0,4}[- ]?\d[\d-]{5,}"),
    re.compile(r"\b[A-Z]{2,4}-\d{4}-\d{4,8}\b"),
    re.compile(r"(?:저는|제\s*이름은|이름은|성명은)\s*[가-힣]{2,4}\b"),
    re.compile(r"(?:이름|성명)\s*[:=]\s*[가-힣]{2,4}\b"),
    re.compile(r"(?:제|나의)\s*(?:질환|병력|장애|수급자격|건강정보)\s*[:=]?\s*\S+"),
    re.compile(r"(?i)(?:lat(?:itude)?|위도)\s*[:=]\s*3[3-9]\.\d{4,}.{0,80}(?:lon(?:gitude)?|경도)\s*[:=]\s*12[4-8]\.\d{4,}"),
)
_SECRET_PATTERN = re.compile(
    r"(?i)(?:\b(?:api[_-]?key|secret|token|password)\s*[:=]|\bsk-[A-Za-z0-9_-]+)"
)
_AUTH_SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(?:비밀번호|암호|\b(?:password|passcode|pin)\b|인증\s*(?:번호|코드))"
    r"\s*(?:[:=]|은|는)?\s*[A-Za-z0-9!@#$%^&*_.-]{4,}"
)
_MOCK_PATTERN = re.compile(r"(?i)(?:\bmock\b|시연용\s*샘플)")
_KB_ID_PATTERN = r"KB-(?:MOVE|CERT|WASTE|TAX)-[0-9]{2}"
_OFFICE_ID_PATTERN = r"OFFICE-(?:AREUM|DODAM|JOCHIWON)"
_SUPPORTED_SCHEMA_KEYWORDS = frozenset({
    "$schema", "additionalProperties", "const", "enum", "format", "items",
    "maxItems", "maxLength", "minimum", "minItems", "minLength", "pattern",
    "properties", "required", "title", "type", "uniqueItems",
})
_RUNTIME_ALLOWLIST = frozenset({
    "scripts/data_staging_validation.py",
    "scripts/tests/test_data_staging_validation.py",
    "scripts/validate_data_staging.py",
    "scripts/verify.ps1",
})
_RUNTIME_SUFFIXES = frozenset({
    ".bat", ".cjs", ".cmd", ".env", ".js", ".json", ".mjs", ".ps1",
    ".psd1", ".psm1", ".py", ".sh", ".sql", ".toml", ".ts", ".tsx",
    ".yaml", ".yml",
})
_OPERATIONS_CONFIG_ROOTS = frozenset({
    ".config", "config", "deploy", "deployment", "infra", "infrastructure",
    "operations", "ops",
})
_OPERATIONS_CONFIG_SUFFIXES = frozenset({
    ".json", ".ps1", ".psd1", ".psm1", ".toml", ".yaml", ".yml",
})


@dataclass(frozen=True, order=True)
class ValidationIssue:
    """A stable, value-free schema validation failure."""

    code: str
    artifact: str
    record_id: str | None
    field: str | None


def load_json_object(path: Path) -> dict[str, object]:
    """Load a JSON object without accepting arrays or scalar roots."""
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("JSON_DUPLICATE_MEMBER")
            result[key] = item
        return result

    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
    )
    if not isinstance(value, dict):
        raise ValueError("JSON_ROOT_MUST_BE_OBJECT")
    return value


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for the exact bytes of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    """Write canonical UTF-8 JSON used by DATA-001 staging artifacts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json_bytes(value))


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def build_pending_manifest(draft_dir: Path, submitted_at: str) -> dict[str, object]:
    """Build an unapproved manifest bound only to the three content artifacts."""
    if not _is_iso_datetime(submitted_at):
        raise ValueError("SUBMITTED_AT_INVALID")
    counts = _content_counts(draft_dir)
    decisions = _recommended_decisions(draft_dir)
    return {
        "schema_version": 1,
        "dataset_id": "sejong-data-001",
        "draft_version": "0.1.0-draft.1",
        "state": "PENDING_PM_REVIEW",
        "created_by": "AI-DATA-BACKEND",
        "submitted_at": submitted_at,
        "reviewed_by": None,
        "reviewed_at": None,
        "review_comment": None,
        "artifacts": [
            {
                "path": artifact,
                "record_count": counts[artifact],
                "sha256": sha256_file(draft_dir / artifact),
            }
            for artifact in CONTENT_ARTIFACTS
        ],
        "decisions": decisions,
    }


def validate_staging(
    draft_dir: Path, schema_dir: Path, source_registry: Path,
    manifest_override: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return a value-free deterministic validation report for one DATA-001 draft."""
    issues: list[ValidationIssue] = []
    artifacts: dict[str, dict[str, object]] = {}
    canonical_run = _same_resolved_path(draft_dir, CANONICAL_DRAFT_DIR)
    approved_matrix: dict[str, object] | None = None
    if canonical_run:
        try:
            matrix_hash = _sha256_trusted_file(CANONICAL_SOURCE_MATRIX)
        except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
            matrix_hash = None
        if matrix_hash != APPROVED_SOURCE_MATRIX_SHA256:
            _issue(issues, "SOURCE_MATRIX_HASH_MISMATCH", "approved-source-matrix.json", None, None)
        else:
            try:
                approved_matrix = load_json_object(CANONICAL_SOURCE_MATRIX)
                if CANONICAL_SOURCE_MATRIX.read_bytes() != _canonical_json_bytes(approved_matrix):
                    _issue(issues, "SOURCE_MATRIX_NOT_CANONICAL", "approved-source-matrix.json", None, None)
            except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
                _issue(issues, "SOURCE_MATRIX_LOAD_ERROR", "approved-source-matrix.json", None, None)
    schemas = {
        "kb_records.json": "kb-records.schema.json",
        "offices.json": "offices.schema.json",
        "office_service_mappings.json": "office-service-mappings.schema.json",
        "approval_manifest.json": "approval-manifest.schema.json",
    }
    for artifact, schema_name in schemas.items():
        if artifact == "approval_manifest.json" and manifest_override is not None:
            artifacts[artifact] = manifest_override
            try:
                schema = load_json_object(schema_dir / schema_name)
            except (OSError, ValueError, json.JSONDecodeError):
                _issue(issues, "SCHEMA_LOAD_ERROR", artifact, None, None)
            else:
                issues.extend(validate_schema(manifest_override, schema, artifact))
            continue
        try:
            artifacts[artifact] = load_json_object(draft_dir / artifact)
        except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
            _issue(issues, "ARTIFACT_MISSING", artifact, None, None)
            continue
        if (draft_dir / artifact).read_bytes() != _canonical_json_bytes(artifacts[artifact]):
            _issue(issues, "JSON_NOT_CANONICAL", artifact, None, None)
        try:
            schema = load_json_object(schema_dir / schema_name)
        except (OSError, ValueError, json.JSONDecodeError):
            _issue(issues, "SCHEMA_LOAD_ERROR", artifact, None, None)
            continue
        issues.extend(validate_schema(artifacts[artifact], schema, artifact))

    kb_records = _records(artifacts.get("kb_records.json"))
    office_records = _records(artifacts.get("offices.json"))
    mapping_records = _records(artifacts.get("office_service_mappings.json"))
    counts = {"kb": len(kb_records), "office": len(office_records), "mapping": len(mapping_records)}
    for key, expected, artifact in (
        ("kb", 20, "kb_records.json"),
        ("office", 3, "offices.json"),
        ("mapping", 12, "office_service_mappings.json"),
    ):
        if counts[key] != expected:
            _issue(issues, f"COUNT_{key.upper()}", artifact, None, "records")

    _validate_records(kb_records, "kb_records.json", "id", issues)
    _validate_canonical_kb_records(kb_records, issues)
    _validate_records(office_records, "offices.json", "public_id", issues)
    _validate_mappings(mapping_records, office_records, issues)
    _validate_kb_draft_metadata(kb_records, issues)
    registry, registry_fieldnames = _validate_sources(
        kb_records, office_records, mapping_records, source_registry, issues
    )
    _validate_text_safety(kb_records, "kb_records.json", issues)
    if approved_matrix is None:
        _validate_text_safety(
            office_records, "offices.json", issues,
            fixture_allowed_fields={"phone", "address"},
        )
    else:
        _validate_text_safety(
            office_records,
            "offices.json",
            issues,
            office_public_contacts=_approved_office_public_contacts(approved_matrix),
        )
    _validate_text_safety(mapping_records, "office_service_mappings.json", issues)
    manifest = artifacts.get("approval_manifest.json")
    if isinstance(manifest, dict):
        _validate_text_safety([manifest], "approval_manifest.json", issues)
    _validate_text_safety(
        [{"headers": list(registry_fieldnames), "rows": list(registry.values())}],
        "kb_source_registry.csv",
        issues,
    )
    if approved_matrix is not None:
        _validate_approved_source_matrix(
            kb_records, office_records, mapping_records, list(registry.values()),
            approved_matrix, issues,
        )
        _validate_source_registry_hash(source_registry, approved_matrix, issues)
        _validate_source_audit_hashes(approved_matrix, issues)
        _validate_content_artifact_hashes(draft_dir, approved_matrix, issues)
    _validate_manifest(
        artifacts.get("approval_manifest.json"), draft_dir, kb_records, office_records,
        mapping_records, issues,
    )
    _validate_runtime_staging_references(issues)

    artifact_hashes = {
        artifact: sha256_file(draft_dir / artifact)
        for artifact in CONTENT_ARTIFACTS
        if (draft_dir / artifact).is_file()
    }
    normalized_issues = sorted(issues, key=lambda issue: (
        issue.artifact, issue.record_id or "", issue.field or "", issue.code,
    ))
    manifest = artifacts.get("approval_manifest.json")
    state = manifest.get("state") if isinstance(manifest, dict) else None
    valid = not normalized_issues
    return {
        "schema_version": 1,
        "draft_version": "0.1.0-draft.1",
        "valid": valid,
        "counts": counts,
        "approval_projection": (
            _approval_projection(manifest)
            if valid and state == "APPROVED_FOR_INITIAL_RELEASE"
            else None
        ),
        "recommendation_projection": (
            _recommendation_projection(manifest)
            if valid and state == "PENDING_PM_REVIEW"
            else None
        ),
        "artifact_hashes": artifact_hashes,
        "issues": [
            {
                "code": issue.code,
                "artifact": issue.artifact,
                "record_id": issue.record_id,
                "field": issue.field,
            }
            for issue in normalized_issues
        ],
        "warnings": (
            ["PM_REVIEW_REQUIRED"]
            if valid and state == "PENDING_PM_REVIEW"
            else []
        ),
    }


def _content_counts(draft_dir: Path) -> dict[str, int]:
    return {
        artifact: len(_records(load_json_object(draft_dir / artifact)))
        for artifact in CONTENT_ARTIFACTS
    }


def _records(root: object | None) -> list[dict[str, object]]:
    if not isinstance(root, dict):
        return []
    records = root.get("records")
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def _recommended_decisions(draft_dir: Path) -> list[dict[str, object]]:
    decisions: list[dict[str, object]] = []
    for record in _records(load_json_object(draft_dir / "kb_records.json")):
        record_id = record.get("id")
        if isinstance(record_id, str):
            decisions.append({
                "record_type": "KB",
                "record_id": record_id,
                "recommended_decision": (
                    "WITHHOLD_FOR_REGRESSION" if record_id == "KB-WASTE-03"
                    else "APPROVE_INITIAL_RELEASE"
                ),
                "decision": None,
                "comment": None,
            })
    for record in _records(load_json_object(draft_dir / "offices.json")):
        record_id = record.get("public_id")
        if isinstance(record_id, str):
            decisions.append({
                "record_type": "OFFICE",
                "record_id": record_id,
                "recommended_decision": "APPROVE_INITIAL_RELEASE",
                "decision": None,
                "comment": None,
            })
    for record in _records(load_json_object(draft_dir / "office_service_mappings.json")):
        office_id = record.get("office_public_id")
        intent = record.get("intent")
        if isinstance(office_id, str) and isinstance(intent, str):
            record_id = f"{office_id}:{intent}"
            decisions.append({
                "record_type": "MAPPING",
                "record_id": record_id,
                "recommended_decision": (
                    "REJECT" if record_id in {
                        "OFFICE-AREUM:LOCAL_TAX_GENERAL",
                        "OFFICE-DODAM:BULKY_WASTE",
                    } else "APPROVE_INITIAL_RELEASE"
                ),
                "decision": None,
                "comment": None,
            })
    return sorted(decisions, key=lambda decision: (
        str(decision["record_type"]), str(decision["record_id"])
    ))


def _safe_id(value: object, pattern: str) -> str | None:
    return value if isinstance(value, str) and re.fullmatch(pattern, value) else None


def _validate_records(
    records: list[dict[str, object]], artifact: str, id_field: str,
    issues: list[ValidationIssue],
) -> None:
    identifiers = [record.get(id_field) for record in records]
    pattern = _KB_ID_PATTERN if id_field == "id" else _OFFICE_ID_PATTERN
    safe_ids = [
        identifier for identifier in identifiers
        if _safe_id(identifier, pattern) is not None
    ]
    for identifier in sorted(set(safe_ids)):
        if safe_ids.count(identifier) > 1:
            _issue(issues, "DUPLICATE_RECORD_ID", artifact, identifier, id_field)
    if safe_ids != sorted(safe_ids):
        _issue(issues, "RECORD_ORDER", artifact, None, "records")


def _validate_canonical_kb_records(
    records: list[dict[str, object]], issues: list[ValidationIssue]
) -> None:
    identifiers = [record.get("id") for record in records]
    if identifiers != list(CANONICAL_KB_IDS):
        _issue(issues, "KB_CANONICAL_ID_SET", "kb_records.json", None, "records")
    for record in records:
        record_id = _safe_id(record.get("id"), _KB_ID_PATTERN)
        if record_id is None:
            continue
        category_prefix = record_id.split("-")[1]
        if record.get("category") != CANONICAL_KB_CATEGORIES.get(category_prefix):
            _issue(issues, "KB_CATEGORY_MISMATCH", "kb_records.json", record_id, "category")


def _validate_mappings(
    mappings: list[dict[str, object]], offices: list[dict[str, object]],
    issues: list[ValidationIssue],
) -> None:
    artifact = "office_service_mappings.json"
    office_ids = {
        public_id for record in offices
        if isinstance((public_id := record.get("public_id")), str)
    }
    keys: list[str] = []
    for record in mappings:
        office_id = record.get("office_public_id")
        intent = record.get("intent")
        mapping_key = (
            f"{office_id}:{intent}"
            if isinstance(office_id, str) and isinstance(intent, str) else None
        )
        record_id = _safe_mapping_key(mapping_key)
        if isinstance(office_id, str) and office_id not in office_ids:
            _issue(issues, "ORPHAN_OFFICE_MAPPING", artifact, record_id, "office_public_id")
        if not isinstance(intent, str) or intent not in SUPPORTED_INTENTS:
            _issue(issues, "UNSUPPORTED_INTENT", artifact, record_id, "intent")
        if mapping_key is not None:
            keys.append(mapping_key)
    for key in sorted(set(keys)):
        if keys.count(key) > 1:
            _issue(issues, "DUPLICATE_MAPPING_KEY", artifact, _safe_mapping_key(key), None)
    if keys != sorted(keys):
        _issue(issues, "RECORD_ORDER", artifact, None, "records")


def _validate_kb_draft_metadata(
    records: list[dict[str, object]], issues: list[ValidationIssue]
) -> None:
    for record in records:
        record_id = _safe_id(record.get("id"), _KB_ID_PATTERN)
        if record.get("status") != "DRAFT":
            _issue(issues, "KB_NOT_DRAFT", "kb_records.json", record_id, "status")
        if record.get("approved_by") is not None or record.get("approved_at") is not None:
            _issue(
                issues, "APPROVAL_METADATA_IN_DRAFT", "kb_records.json", record_id,
                "approved_by" if record.get("approved_by") is not None else "approved_at",
            )


def _validate_sources(
    kb_records: list[dict[str, object]], offices: list[dict[str, object]],
    mappings: list[dict[str, object]], source_registry: Path,
    issues: list[ValidationIssue],
) -> tuple[dict[str, dict[str, str]], tuple[str, ...]]:
    for artifact, records, id_field, url_field in (
        ("kb_records.json", kb_records, "id", "source_url"),
        ("offices.json", offices, "public_id", "source_url"),
        ("office_service_mappings.json", mappings, "office_public_id", "evidence_source_url"),
    ):
        for record in records:
            value = record.get(url_field)
            record_id = _record_identifier(record)
            if not _has_allowed_source_host(value):
                _issue(issues, "SOURCE_DOMAIN_NOT_ALLOWED", artifact, record_id, url_field)
            map_url = record.get("map_url")
            if map_url is not None and not _has_allowed_map_host(map_url):
                _issue(issues, "SOURCE_DOMAIN_NOT_ALLOWED", artifact, record_id, "map_url")
    registry, fieldnames = _load_source_registry(source_registry, issues)
    for record in kb_records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or record_id not in registry:
            continue
        source = registry[record_id]
        matches = (
            record.get("source_title") == source.get("공식 출처명")
            and record.get("provider") == source.get("제공기관")
            and record.get("source_url") == source.get("URL")
            and record.get("last_verified_at") == source.get("확인일")
        )
        if not matches:
            _issue(issues, "SOURCE_METADATA_MISMATCH", "kb_records.json", record_id, "source_url")
    return registry, fieldnames


def _load_source_registry_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def _load_source_registry(
    path: Path, issues: list[ValidationIssue]
) -> tuple[dict[str, dict[str, str]], tuple[str, ...]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            fieldnames = tuple(reader.fieldnames or ())
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error):
        _issue(issues, "SOURCE_REGISTRY_ID_SET", "kb_source_registry.csv", None, "kb_id")
        return {}, ()
    if fieldnames != SOURCE_REGISTRY_COLUMNS:
        _issue(issues, "SOURCE_REGISTRY_COLUMN_SET", "kb_source_registry.csv", None, None)
    registry: dict[str, dict[str, str]] = {}
    identifiers: list[str] = []
    for row in rows:
        record_id = row.get("kb_id")
        if not isinstance(record_id, str) or _safe_id(record_id, _KB_ID_PATTERN) is None:
            _issue(issues, "SOURCE_REGISTRY_MALFORMED_ID", "kb_source_registry.csv", None, "kb_id")
            continue
        identifiers.append(record_id)
        if record_id in registry:
            _issue(issues, "SOURCE_REGISTRY_DUPLICATE_ID", "kb_source_registry.csv", record_id, "kb_id")
            continue
        if any(
            not isinstance(row.get(column), str) or not row[column].strip()
            for column in SOURCE_REGISTRY_REQUIRED_METADATA
        ):
            _issue(issues, "SOURCE_REGISTRY_METADATA_REQUIRED", "kb_source_registry.csv", record_id, None)
        if (
            row.get("확인일") != "2026-07-18"
            or row.get("작성 상태") != "검수 대기"
            or row.get("작성자") != "AI-DATA-BACKEND"
            or row.get("검수자") != ""
        ):
            _issue(issues, "SOURCE_REGISTRY_PENDING_METADATA", "kb_source_registry.csv", record_id, None)
        registry[record_id] = row
    if identifiers != list(CANONICAL_KB_IDS):
        _issue(issues, "SOURCE_REGISTRY_ID_SET", "kb_source_registry.csv", None, "kb_id")
    if identifiers != sorted(identifiers):
        _issue(issues, "SOURCE_REGISTRY_ROW_ORDER", "kb_source_registry.csv", None, "kb_id")
    return registry, fieldnames


def _has_allowed_source_host(value: object) -> bool:
    return isinstance(value, str) and urlparse(value).hostname in ALLOWED_SOURCE_HOSTS


def _has_allowed_map_host(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return urlparse(value).hostname in (ALLOWED_SOURCE_HOSTS | {"place.map.kakao.com"})


def _validate_text_safety(
    records: list[dict[str, object]], artifact: str, issues: list[ValidationIssue],
    fixture_allowed_fields: set[str] | None = None,
    office_public_contacts: set[tuple[str, str, str]] | None = None,
) -> None:
    fixture_allowed_fields = fixture_allowed_fields or set()
    office_public_contacts = office_public_contacts or set()
    for record in records:
        record_id = _record_identifier(record)
        for field, value in _text_fields(record):
            top_level = field.split(".", 1)[0]
            if _SECRET_PATTERN.search(value) or _AUTH_SECRET_VALUE_PATTERN.search(value):
                _issue(issues, "SECRET_DETECTED", artifact, record_id, field)
            if _MOCK_PATTERN.search(value):
                _issue(issues, "MOCK_REFERENCE", artifact, record_id, field)
            public_contact = (
                record_id is not None
                and (record_id, top_level, value) in office_public_contacts
            )
            if (
                top_level not in fixture_allowed_fields
                and not public_contact
                and any(pattern.search(value) for pattern in _PII_PATTERNS)
            ):
                _issue(issues, "PII_DETECTED", artifact, record_id, field)


def _text_fields(value: object, prefix: str | None = None) -> Sequence[tuple[str, str]]:
    if isinstance(value, str):
        return [(prefix or "", value)]
    if isinstance(value, list):
        return [
            pair for index, item in enumerate(value)
            for pair in _text_fields(item, _join(prefix, str(index)))
        ]
    if isinstance(value, dict):
        key_pairs = [
            (_join(prefix, "<object-key>"), key)
            for key in value if isinstance(key, str)
        ]
        value_pairs = [
            pair for key, item in value.items() if isinstance(key, str)
            for pair in _text_fields(item, _join(prefix, _safe_field_component(key)))
        ]
        return key_pairs + value_pairs
    return []


def _safe_field_component(value: str) -> str:
    return value if value in _SAFE_REPORT_FIELD_COMPONENTS else "<unknown-property>"


def _record_identifier(record: Mapping[str, object]) -> str | None:
    record_id = _safe_id(record.get("id"), _KB_ID_PATTERN)
    if record_id is not None:
        return record_id
    office_id = _safe_id(record.get("public_id"), _OFFICE_ID_PATTERN)
    if office_id is not None:
        return office_id
    mapping_key = record.get("office_public_id")
    intent = record.get("intent")
    if isinstance(mapping_key, str) and isinstance(intent, str):
        return _safe_mapping_key(f"{mapping_key}:{intent}")
    return None


def _safe_mapping_key(value: str | None) -> str | None:
    if value is None:
        return None
    return _safe_id(value, rf"{_OFFICE_ID_PATTERN}:(?:{'|'.join(sorted(SUPPORTED_INTENTS))})")


def _validate_manifest(
    manifest: object | None, draft_dir: Path, kb_records: list[dict[str, object]],
    office_records: list[dict[str, object]], mapping_records: list[dict[str, object]],
    issues: list[ValidationIssue],
) -> None:
    artifact = "approval_manifest.json"
    if not isinstance(manifest, dict):
        return
    state = manifest.get("state")
    if state not in {"PENDING_PM_REVIEW", "APPROVED_FOR_INITIAL_RELEASE", "REJECTED"}:
        _issue(issues, "MANIFEST_STATE", artifact, None, "state")
    reviewed_by = manifest.get("reviewed_by")
    if reviewed_by == manifest.get("created_by") and reviewed_by is not None:
        _issue(issues, "SELF_APPROVAL", artifact, None, "reviewed_by")
    if state == "PENDING_PM_REVIEW":
        if any(manifest.get(field) is not None for field in (
            "reviewed_by", "reviewed_at", "review_comment"
        )):
            _issue(issues, "PENDING_REVIEW_METADATA", artifact, None, "reviewed_by")
    elif state in {"APPROVED_FOR_INITIAL_RELEASE", "REJECTED"}:
        if (
            not isinstance(reviewed_by, str) or not reviewed_by.strip()
            or not isinstance(manifest.get("reviewed_at"), str)
            or not _is_iso_datetime(str(manifest.get("reviewed_at")))
            or not isinstance(manifest.get("review_comment"), str)
            or not str(manifest.get("review_comment")).strip()
        ):
            _issue(issues, "REVIEW_METADATA_REQUIRED", artifact, None, "reviewed_by")

    entries = manifest.get("artifacts")
    if not isinstance(entries, list):
        entries = []
    by_path = {
        entry.get("path"): entry for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }
    if set(by_path) != set(CONTENT_ARTIFACTS) or len(entries) != len(CONTENT_ARTIFACTS):
        _issue(issues, "MANIFEST_CONTENT_PATH_SET", artifact, None, "artifacts")
    for path in CONTENT_ARTIFACTS:
        entry = by_path.get(path)
        if not isinstance(entry, dict):
            continue
        actual_count = len(_records(_load_artifact_or_empty(draft_dir / path)))
        if entry.get("record_count") != actual_count:
            _issue(issues, "MANIFEST_COUNT_MISMATCH", artifact, None, f"artifacts.{path}.record_count")
        if (draft_dir / path).is_file() and entry.get("sha256") != sha256_file(draft_dir / path):
            _issue(issues, "MANIFEST_HASH_MISMATCH", artifact, None, f"artifacts.{path}.sha256")

    expected = _expected_decisions(kb_records, office_records, mapping_records)
    decisions = manifest.get("decisions")
    if not isinstance(decisions, list):
        decisions = []
    pairs = [
        (decision.get("record_type"), decision.get("record_id"))
        for decision in decisions if isinstance(decision, dict)
    ]
    expected_pairs = [(record_type, record_id) for record_type, record_id, _ in expected]
    if len(pairs) != len(set(pairs)):
        _issue(issues, "DECISION_DUPLICATE", artifact, None, "decisions")
    expected_type_by_id = {record_id: record_type for record_type, record_id, _ in expected}
    if any(expected_type_by_id.get(record_id) != record_type for record_type, record_id in pairs):
        _issue(issues, "DECISION_TYPE_ID_MISMATCH", artifact, None, "decisions")
    if set(pairs) != set(expected_pairs) or len(pairs) != len(expected_pairs):
        _issue(issues, "DECISION_COVERAGE", artifact, None, "decisions")
    if pairs != expected_pairs:
        _issue(issues, "DECISION_ORDER", artifact, None, "decisions")
    recommendations = {
        (decision.get("record_type"), decision.get("record_id")): decision.get("recommended_decision")
        for decision in decisions if isinstance(decision, dict)
    }
    for record_type, record_id, recommendation in expected:
        if recommendations.get((record_type, record_id)) != recommendation:
            _issue(issues, "RECOMMENDATION_POLICY_MISMATCH", artifact, record_id, "recommended_decision")

    structurally_valid = pairs == expected_pairs and len(pairs) == len(expected_pairs)
    if state == "PENDING_PM_REVIEW":
        if recommendations.get(("KB", "KB-WASTE-03")) != "WITHHOLD_FOR_REGRESSION":
            _issue(issues, "WASTE_03_DECISION", artifact, "KB-WASTE-03", "recommended_decision")
        if any(
            isinstance(decision, dict)
            and (decision.get("decision") is not None or decision.get("comment") is not None)
            for decision in decisions
        ):
            _issue(issues, "PENDING_DECISION_EVIDENCE", artifact, None, "decisions")
        if _recommendation_projection(manifest) != {
            "initial_kb": 19,
            "initial_office": 3,
            "initial_mapping": 10,
            "withheld_kb": 1,
            "rejected_mapping": 2,
        }:
            _issue(issues, "INITIAL_PROJECTION_MISMATCH", artifact, None, "decisions")
    elif state in {"APPROVED_FOR_INITIAL_RELEASE", "REJECTED"}:
        for decision in decisions:
            if not isinstance(decision, dict):
                continue
            if not isinstance(decision.get("comment"), str) or not str(decision.get("comment")).strip():
                _issue(issues, "DECISION_COMMENT_REQUIRED", artifact, _manifest_record_id(decision), "comment")
            if decision.get("decision") is None:
                _issue(issues, "DECISION_REQUIRED", artifact, _manifest_record_id(decision), "decision")
            if decision.get("record_type") in {"OFFICE", "MAPPING"} and decision.get("decision") == "WITHHOLD_FOR_REGRESSION":
                _issue(issues, "DECISION_DISPOSITION_MISMATCH", artifact, _manifest_record_id(decision), "decision")
        if state == "APPROVED_FOR_INITIAL_RELEASE" and structurally_valid:
            _validate_approved_projection(decisions, issues)


def _load_artifact_or_empty(path: Path) -> dict[str, object]:
    try:
        return load_json_object(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def _expected_decisions(
    kb_records: list[dict[str, object]], offices: list[dict[str, object]],
    mappings: list[dict[str, object]],
) -> list[tuple[str, str, str]]:
    expected: list[tuple[str, str, str]] = []
    for record in kb_records:
        record_id = _safe_id(record.get("id"), _KB_ID_PATTERN)
        if record_id is not None:
            expected.append(("KB", record_id, (
                "WITHHOLD_FOR_REGRESSION" if record_id == "KB-WASTE-03"
                else "APPROVE_INITIAL_RELEASE"
            )))
    for record in offices:
        record_id = _safe_id(record.get("public_id"), _OFFICE_ID_PATTERN)
        if record_id is not None:
            expected.append(("OFFICE", record_id, "APPROVE_INITIAL_RELEASE"))
    for record in mappings:
        office_id = record.get("office_public_id")
        intent = record.get("intent")
        if isinstance(office_id, str) and isinstance(intent, str):
            record_id = _safe_mapping_key(f"{office_id}:{intent}")
            if record_id is None:
                continue
            expected.append(("MAPPING", record_id, (
                "REJECT" if record_id in {
                    "OFFICE-AREUM:LOCAL_TAX_GENERAL",
                    "OFFICE-DODAM:BULKY_WASTE",
                } else "APPROVE_INITIAL_RELEASE"
            )))
    return sorted(expected, key=lambda entry: (entry[0], entry[1]))


def _recommendation_projection(manifest: object | None) -> dict[str, int] | None:
    return _manifest_projection(manifest, "PENDING_PM_REVIEW", "recommended_decision")


def _approval_projection(manifest: object | None) -> dict[str, int] | None:
    return _manifest_projection(manifest, "APPROVED_FOR_INITIAL_RELEASE", "decision")


def _manifest_projection(
    manifest: object | None, expected_state: str, field: str,
) -> dict[str, int] | None:
    if not isinstance(manifest, dict) or manifest.get("state") != expected_state:
        return None
    decisions = manifest.get("decisions")
    if not isinstance(decisions, list):
        return None
    specs = _static_decision_specs()
    expected_pairs = [(record_type, record_id) for record_type, record_id, _ in specs]
    pairs = [
        (entry.get("record_type"), entry.get("record_id"))
        for entry in decisions if isinstance(entry, dict)
    ]
    if pairs != expected_pairs:
        return None
    if any(
        entry.get("recommended_decision") != recommendation
        for entry, (_, _, recommendation) in zip(decisions, specs, strict=True)
        if isinstance(entry, dict)
    ):
        return None
    if expected_state == "PENDING_PM_REVIEW" and any(
        isinstance(entry, dict)
        and (entry.get("decision") is not None or entry.get("comment") is not None)
        for entry in decisions
    ):
        return None
    if expected_state == "APPROVED_FOR_INITIAL_RELEASE" and any(
        not isinstance(entry, dict)
        or entry.get("decision") not in {"APPROVE_INITIAL_RELEASE", "WITHHOLD_FOR_REGRESSION", "REJECT"}
        or (
            entry.get("record_type") in {"OFFICE", "MAPPING"}
            and entry.get("decision") == "WITHHOLD_FOR_REGRESSION"
        )
        for entry in decisions
    ):
        return None
    if expected_state == "APPROVED_FOR_INITIAL_RELEASE":
        reviewed_by_pair = {
            (entry.get("record_type"), entry.get("record_id")): entry.get("decision")
            for entry in decisions if isinstance(entry, dict)
        }
        if not all(_approved_policy_flags(reviewed_by_pair)):
            return None
    approved = {"KB": 0, "OFFICE": 0, "MAPPING": 0}
    withheld_kb = 0
    rejected_mapping = 0
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        record_type = decision.get("record_type")
        disposition = decision.get(field)
        if record_type in approved and disposition == "APPROVE_INITIAL_RELEASE":
            approved[record_type] += 1
        elif record_type == "KB" and disposition == "WITHHOLD_FOR_REGRESSION":
            withheld_kb += 1
        elif record_type == "MAPPING" and disposition == "REJECT":
            rejected_mapping += 1
    return {
        "initial_kb": approved["KB"],
        "initial_office": approved["OFFICE"],
        "initial_mapping": approved["MAPPING"],
        "withheld_kb": withheld_kb,
        "rejected_mapping": rejected_mapping,
    }


def _static_decision_specs() -> list[tuple[str, str, str]]:
    office_ids = ("OFFICE-AREUM", "OFFICE-DODAM", "OFFICE-JOCHIWON")
    mappings = [f"{office_id}:{intent}" for office_id in office_ids for intent in sorted(SUPPORTED_INTENTS)]
    specs = [
        ("KB", record_id, "WITHHOLD_FOR_REGRESSION" if record_id == "KB-WASTE-03" else "APPROVE_INITIAL_RELEASE")
        for record_id in CANONICAL_KB_IDS
    ]
    specs.extend(("MAPPING", record_id, "REJECT" if record_id in {
        "OFFICE-AREUM:LOCAL_TAX_GENERAL", "OFFICE-DODAM:BULKY_WASTE",
    } else "APPROVE_INITIAL_RELEASE") for record_id in mappings)
    specs.extend(("OFFICE", record_id, "APPROVE_INITIAL_RELEASE") for record_id in office_ids)
    return specs


def _manifest_record_id(decision: Mapping[str, object]) -> str | None:
    value = decision.get("record_id")
    return value if isinstance(value, str) and re.fullmatch(
        rf"(?:{_KB_ID_PATTERN}|{_OFFICE_ID_PATTERN}(?::(?:{'|'.join(sorted(SUPPORTED_INTENTS))}))?)", value
    ) else None


def _validate_approved_projection(
    decisions: list[object], issues: list[ValidationIssue]
) -> None:
    by_pair = {
        (entry.get("record_type"), entry.get("record_id")): entry.get("decision")
        for entry in decisions if isinstance(entry, dict)
    }
    kb_valid, office_valid, mapping_valid = _approved_policy_flags(by_pair)
    if not kb_valid:
        _issue(issues, "WASTE_03_DECISION", "approval_manifest.json", "KB-WASTE-03", "decision")
    if not (kb_valid and office_valid and mapping_valid):
        _issue(issues, "INITIAL_PROJECTION_MISMATCH", "approval_manifest.json", None, "decisions")


def _approved_policy_flags(
    by_pair: Mapping[tuple[object, object], object]
) -> tuple[bool, bool, bool]:
    kb_valid = all(
        by_pair.get(("KB", record_id)) == (
            "WITHHOLD_FOR_REGRESSION" if record_id == "KB-WASTE-03" else "APPROVE_INITIAL_RELEASE"
        ) for record_id in CANONICAL_KB_IDS
    )
    office_valid = all(
        by_pair.get(("OFFICE", record_id)) == "APPROVE_INITIAL_RELEASE"
        for record_id in ("OFFICE-AREUM", "OFFICE-DODAM", "OFFICE-JOCHIWON")
    )
    mapping_values = [value for (record_type, _), value in by_pair.items() if record_type == "MAPPING"]
    mapping_valid = (
        all(value in {"APPROVE_INITIAL_RELEASE", "REJECT"} for value in mapping_values)
        and 10 <= mapping_values.count("APPROVE_INITIAL_RELEASE") <= 12
    )
    return kb_valid, office_valid, mapping_valid


def _approved_office_public_contacts(
    matrix: Mapping[str, object],
) -> set[tuple[str, str, str]]:
    contacts: set[tuple[str, str, str]] = set()
    offices = matrix.get("offices")
    if not isinstance(offices, list):
        return contacts
    for office in offices:
        if not isinstance(office, dict) or not isinstance(office.get("public_id"), str):
            continue
        for field in ("address", "phone"):
            value = office.get(field)
            if isinstance(value, str):
                contacts.add((office["public_id"], field, value))
    return contacts


def _validate_approved_source_matrix(
    kb_records: list[dict[str, object]],
    office_records: list[dict[str, object]],
    mapping_records: list[dict[str, object]],
    registry_rows: list[dict[str, str]],
    matrix: Mapping[str, object],
    issues: list[ValidationIssue],
) -> None:
    artifact = "approved-source-matrix.json"
    if set(matrix) != {
        "content_artifacts", "draft_version", "kb_records", "mappings", "offices",
        "schema_version", "source_audits", "source_registry", "verified_at",
    }:
        _issue(issues, "SOURCE_MATRIX_MISMATCH", artifact, None, "<matrix-shape>")
    if (
        matrix.get("schema_version") != 1
        or matrix.get("draft_version") != "0.1.0-draft.1"
        or matrix.get("verified_at") != "2026-07-18"
    ):
        _issue(issues, "SOURCE_MATRIX_MISMATCH", artifact, None, None)

    kb_fields = (
        "category", "id", "last_verified_at", "provider", "source_title", "source_url",
    )
    office_fields = (
        "address", "last_verified_at", "map_url", "office_name", "opening_hours",
        "phone", "provider", "public_id", "region", "source_title", "source_url",
    )
    mapping_fields = (
        "department_label", "evidence_source_url", "intent", "last_verified_at",
        "office_public_id",
    )
    expected_kb = matrix.get("kb_records")
    expected_offices = matrix.get("offices")
    expected_mappings = matrix.get("mappings")
    actual_kb = [{field: record.get(field) for field in kb_fields} for record in kb_records]
    actual_offices = [
        {field: record.get(field) for field in office_fields} for record in office_records
    ]
    recommendations = {
        (record_type, record_id): recommendation
        for record_type, record_id, recommendation in _static_decision_specs()
    }
    actual_mappings = []
    for record in mapping_records:
        projected = {field: record.get(field) for field in mapping_fields}
        key = f"{record.get('office_public_id')}:{record.get('intent')}"
        projected["recommended_decision"] = recommendations.get(("MAPPING", key))
        actual_mappings.append(projected)

    registry_projection = [
        {
            "category": CANONICAL_KB_CATEGORIES.get(row.get("kb_id", "").split("-")[1])
            if len(row.get("kb_id", "").split("-")) > 1 else None,
            "id": row.get("kb_id"),
            "last_verified_at": row.get("확인일"),
            "provider": row.get("제공기관"),
            "source_title": row.get("공식 출처명"),
            "source_url": row.get("URL"),
        }
        for row in registry_rows
    ]
    for actual, expected, field in (
        (actual_kb, expected_kb, "kb_records"),
        (registry_projection, expected_kb, "source_registry"),
        (actual_offices, expected_offices, "offices"),
        (actual_mappings, expected_mappings, "mappings"),
    ):
        if not _json_equal(actual, expected):
            _issue(issues, "SOURCE_MATRIX_MISMATCH", artifact, None, field)


def _validate_source_registry_hash(
    source_registry: Path,
    matrix: Mapping[str, object],
    issues: list[ValidationIssue],
) -> None:
    expected = matrix.get("source_registry")
    if not isinstance(expected, dict) or expected != {
        "path": "data/official/kb_source_registry.csv",
        "sha256": expected.get("sha256") if isinstance(expected.get("sha256"), str) else None,
    }:
        _issue(issues, "SOURCE_REGISTRY_HASH_MISMATCH", "approved-source-matrix.json", None, "source_registry")
        return
    if not _same_resolved_path(source_registry, REPOSITORY_ROOT / expected["path"]):
        _issue(issues, "SOURCE_REGISTRY_HASH_MISMATCH", "kb_source_registry.csv", None, None)
        return
    try:
        actual = sha256_file(source_registry)
    except OSError:
        actual = None
    if actual != expected["sha256"]:
        _issue(issues, "SOURCE_REGISTRY_HASH_MISMATCH", "kb_source_registry.csv", None, None)


def _validate_source_audit_hashes(
    matrix: Mapping[str, object], issues: list[ValidationIssue]
) -> None:
    expected_paths = CANONICAL_SOURCE_AUDIT_RELATIVE_PATHS
    entries = matrix.get("source_audits")
    if not isinstance(entries, list) or [
        entry.get("path") if isinstance(entry, dict) else None for entry in entries
    ] != list(expected_paths):
        _issue(issues, "SOURCE_AUDIT_HASH_MISMATCH", "approved-source-matrix.json", None, "source_audits")
        return
    for entry in entries:
        assert isinstance(entry, dict)
        if set(entry) != {"path", "sha256"}:
            _issue(issues, "SOURCE_AUDIT_HASH_MISMATCH", "approved-source-matrix.json", None, "source_audits")
            continue
        path = REPOSITORY_ROOT / entry["path"]
        try:
            actual = _sha256_trusted_file(path)
        except OSError:
            actual = None
        if actual != entry.get("sha256"):
            _issue(issues, "SOURCE_AUDIT_HASH_MISMATCH", "approved-source-matrix.json", None, "source_audits")


def _validate_content_artifact_hashes(
    draft_dir: Path, matrix: Mapping[str, object], issues: list[ValidationIssue]
) -> None:
    entries = matrix.get("content_artifacts")
    if not isinstance(entries, list) or [
        entry.get("path") if isinstance(entry, dict) else None for entry in entries
    ] != list(CONTENT_ARTIFACTS):
        _issue(issues, "SOURCE_MATRIX_MISMATCH", "approved-source-matrix.json", None, "content_artifacts")
        return
    for entry in entries:
        assert isinstance(entry, dict)
        if set(entry) != {"path", "sha256"}:
            _issue(issues, "SOURCE_MATRIX_MISMATCH", "approved-source-matrix.json", None, "content_artifacts")
            continue
        try:
            actual = sha256_file(draft_dir / entry["path"])
        except OSError:
            actual = None
        if actual != entry.get("sha256"):
            _issue(issues, "SOURCE_MATRIX_MISMATCH", "approved-source-matrix.json", None, "content_artifacts")


def _same_resolved_path(left: Path, right: Path) -> bool:
    try:
        return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))
    except OSError:
        return False


def _validate_runtime_staging_references(issues: list[ValidationIssue]) -> None:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        )
        names = completed.stdout.decode("utf-8").split("\0")
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        _issue(issues, "RUNTIME_SCAN_FAILED", "<runtime-scan>", None, None)
        return
    paths = [
        REPOSITORY_ROOT / name for name in names
        if name and _is_runtime_or_operations_file(name)
    ]
    _scan_runtime_files(paths, REPOSITORY_ROOT, issues, _RUNTIME_ALLOWLIST)


def _is_runtime_or_operations_file(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = Path(normalized)
    parts = tuple(part.lower() for part in path.parts)
    suffix = path.suffix.lower()
    executable_or_config = (
        suffix in _RUNTIME_SUFFIXES
        or path.name.lower() in {
            ".env.example", "dockerfile", "makefile", "package.json",
            "pnpm-workspace.yaml",
        }
    )
    in_runtime_tree = (
        normalized.lower().startswith(("apps/", "packages/", "database/", "scripts/"))
        or normalized.lower().startswith(".github/workflows/")
        or normalized.lower() == "supabase/config.toml"
        or normalized.lower() == "supabase/seed.sql"
        or normalized.lower().startswith("supabase/migrations/")
        or suffix in {".ps1", ".psd1", ".psm1"}
    )
    excluded_artifact_tree = bool(parts) and parts[0] in {"data", "docs"}
    in_operations_config_tree = (
        not excluded_artifact_tree
        and suffix in _OPERATIONS_CONFIG_SUFFIXES
        and any(part in _OPERATIONS_CONFIG_ROOTS for part in parts[:-1])
    )
    root_config = "/" not in normalized and executable_or_config
    return (
        (in_runtime_tree and executable_or_config)
        or in_operations_config_tree
        or root_config
    )


def _scan_runtime_files(
    paths: Sequence[Path],
    repository_root: Path,
    issues: list[ValidationIssue],
    allowlist: frozenset[str] = frozenset(),
) -> None:
    for candidate in paths:
        try:
            relative = candidate.relative_to(repository_root).as_posix()
        except ValueError:
            relative = candidate.name
        if relative in allowlist:
            continue
        try:
            if _has_reparse_component(candidate) or not candidate.is_file():
                raise OSError("untrusted runtime path")
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            _issue(issues, "RUNTIME_FILE_UNTRUSTED", relative, None, None)
            continue
        if _is_runtime_staging_reference(text):
            _issue(issues, "RUNTIME_STAGING_REFERENCE", relative, None, None)


def _is_runtime_staging_reference(text: str) -> bool:
    normalized = _collapse_literal_concatenations(text).lower().replace("\\", "/")
    normalized = re.sub(r"/+", "/", normalized)
    if re.search(r"data\s*/\s*staging(?:\s*/|\b)", normalized):
        return True
    compact = re.sub(r"[\s\"'`+(){}\[\],]", "", normalized)
    if "data/staging" in compact:
        return True
    if re.search(
        r"[\"']data[\"'].{0,200}[\"']/?staging[\"']",
        normalized,
        flags=re.DOTALL,
    ) is not None:
        return True
    return re.search(
        r"(?:root|path|dir)\w*\s*[:=]\s*[\"']?data[\"']?.{0,200}"
        r"(?:stage|staging)\w*\s*[:=]\s*[\"']?staging[\"']?",
        normalized,
        flags=re.DOTALL,
    ) is not None


def _collapse_literal_concatenations(text: str) -> str:
    pattern = re.compile(
        r"(?P<left_quote>[\"'])(?P<left>[A-Za-z0-9_./\\-]*)"
        r"(?P=left_quote)\s*\+\s*"
        r"(?P<right_quote>[\"'])(?P<right>[A-Za-z0-9_./\\-]*)"
        r"(?P=right_quote)"
    )
    while True:
        collapsed = pattern.sub(
            lambda match: f'"{match.group("left")}{match.group("right")}"',
            text,
        )
        if collapsed == text:
            return text
        text = collapsed


def _sha256_trusted_file(path: Path) -> str:
    if _has_reparse_component(path) or not path.is_file():
        raise OSError("untrusted linked path")
    return sha256_file(path)


def _has_reparse_component(path: Path) -> bool:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if not current.exists():
            continue
        try:
            attributes = getattr(current.lstat(), "st_file_attributes", 0)
        except OSError:
            return True
        if current.is_symlink() or bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            return True
    return False


def validate_schema(
    instance: object, schema: dict[str, object], artifact: str
) -> Sequence[ValidationIssue]:
    """Validate the small JSON Schema subset used by DATA-001 contracts."""
    issues: list[ValidationIssue] = []
    _validate_schema_meta(schema, artifact, issues)
    _validate(instance, schema, artifact, None, None, issues)
    return sorted(issues, key=lambda issue: (
        issue.artifact,
        issue.record_id or "",
        issue.field or "",
        issue.code,
    ))


def _validate_schema_meta(
    schema: Mapping[str, object], artifact: str, issues: list[ValidationIssue]
) -> None:
    for keyword, value in schema.items():
        if keyword not in _SUPPORTED_SCHEMA_KEYWORDS:
            _issue(
                issues, "SCHEMA_UNSUPPORTED_KEYWORD", artifact, None,
                "<schema-keyword>",
            )
            continue
        if not _schema_keyword_value_is_supported(keyword, value):
            _issue(
                issues, "SCHEMA_KEYWORD_VALUE_INVALID", artifact, None,
                "<schema-keyword>",
            )
            continue
        if keyword == "properties" and isinstance(value, Mapping):
            for child in value.values():
                if isinstance(child, Mapping):
                    _validate_schema_meta(child, artifact, issues)
                else:
                    _issue(
                        issues, "SCHEMA_KEYWORD_VALUE_INVALID", artifact, None,
                        "<schema-keyword>",
                    )
        elif keyword == "items" and isinstance(value, Mapping):
            _validate_schema_meta(value, artifact, issues)
        elif keyword == "format" and value not in {
            "date", "date-time", "https-url", "uri",
        }:
            _issue(
                issues, "SCHEMA_UNSUPPORTED_FORMAT", artifact, None,
                "<schema-format>",
            )


def _schema_keyword_value_is_supported(keyword: str, value: object) -> bool:
    if keyword in {"$schema", "pattern", "title"}:
        return isinstance(value, str)
    if keyword == "type":
        names = [value] if isinstance(value, str) else value
        return isinstance(names, list) and bool(names) and all(
            isinstance(name, str)
            and name in {"array", "boolean", "integer", "null", "object", "string"}
            for name in names
        )
    if keyword in {"additionalProperties", "uniqueItems"}:
        return isinstance(value, bool)
    if keyword in {"properties", "items"}:
        return isinstance(value, Mapping)
    if keyword == "required":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    if keyword == "enum":
        return isinstance(value, list)
    if keyword in {"maxItems", "maxLength", "minItems", "minLength"}:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0
    if keyword == "minimum":
        return _is_json_number(value)
    if keyword == "format":
        return isinstance(value, str)
    return keyword == "const"


def _validate(
    value: object,
    schema: Mapping[str, object],
    artifact: str,
    record_id: str | None,
    field: str | None,
    issues: list[ValidationIssue],
) -> None:
    current_record_id = _record_id(value, schema, record_id)
    if "const" in schema and not _json_equal(value, schema["const"]):
        _issue(issues, "SCHEMA_CONST", artifact, current_record_id, field)

    allowed_types = schema.get("type")
    if allowed_types is not None and not _matches_type(value, allowed_types):
        _issue(issues, "SCHEMA_TYPE", artifact, current_record_id, field)
        return

    enum = schema.get("enum")
    if isinstance(enum, list) and not any(_json_equal(value, item) for item in enum):
        _issue(issues, "SCHEMA_ENUM", artifact, current_record_id, field)

    minimum = schema.get("minimum")
    if _is_json_number(value) and _is_json_number(minimum) and value < minimum:
        _issue(issues, "SCHEMA_MINIMUM", artifact, current_record_id, field)

    if isinstance(value, dict):
        _validate_object(value, schema, artifact, current_record_id, field, issues)
    elif isinstance(value, list):
        _validate_array(value, schema, artifact, current_record_id, field, issues)
    elif isinstance(value, str):
        _validate_string(value, schema, artifact, current_record_id, field, issues)


def _validate_object(
    value: dict[object, object],
    schema: Mapping[str, object],
    artifact: str,
    record_id: str | None,
    field: str | None,
    issues: list[ValidationIssue],
) -> None:
    properties = schema.get("properties", {})
    if not isinstance(properties, Mapping):
        properties = {}
    required = schema.get("required", [])
    if isinstance(required, list):
        for name in required:
            if isinstance(name, str) and name not in value:
                _issue(issues, "SCHEMA_REQUIRED", artifact, record_id, _join(field, name))
    if schema.get("additionalProperties") is False:
        for name in value:
            if isinstance(name, str) and name not in properties:
                _issue(
                    issues,
                    "SCHEMA_ADDITIONAL_PROPERTY",
                    artifact,
                    record_id,
                    _join(field, "<unknown-property>"),
                )
    for name, child_schema in properties.items():
        if name in value and isinstance(name, str) and isinstance(child_schema, Mapping):
            _validate(
                value[name],
                child_schema,
                artifact,
                record_id,
                _join(field, name),
                issues,
            )


def _validate_array(
    value: list[object],
    schema: Mapping[str, object],
    artifact: str,
    record_id: str | None,
    field: str | None,
    issues: list[ValidationIssue],
) -> None:
    minimum = schema.get("minItems")
    maximum = schema.get("maxItems")
    if isinstance(minimum, int) and len(value) < minimum:
        _issue(issues, "SCHEMA_MIN_ITEMS", artifact, record_id, field)
    if isinstance(maximum, int) and len(value) > maximum:
        _issue(issues, "SCHEMA_MAX_ITEMS", artifact, record_id, field)
    if schema.get("uniqueItems") is True and len({_canonical(item) for item in value}) != len(value):
        _issue(issues, "SCHEMA_UNIQUE_ITEMS", artifact, record_id, field)
    child_schema = schema.get("items")
    if isinstance(child_schema, Mapping):
        for index, item in enumerate(value):
            _validate(
                item,
                child_schema,
                artifact,
                record_id,
                _join(field, str(index)),
                issues,
            )


def _validate_string(
    value: str,
    schema: Mapping[str, object],
    artifact: str,
    record_id: str | None,
    field: str | None,
    issues: list[ValidationIssue],
) -> None:
    minimum = schema.get("minLength")
    maximum = schema.get("maxLength")
    if isinstance(minimum, int) and len(value) < minimum:
        _issue(issues, "SCHEMA_MIN_LENGTH", artifact, record_id, field)
    if isinstance(maximum, int) and len(value) > maximum:
        _issue(issues, "SCHEMA_MAX_LENGTH", artifact, record_id, field)
    pattern = schema.get("pattern")
    if isinstance(pattern, str) and re.search(pattern, value) is None:
        _issue(issues, "SCHEMA_PATTERN", artifact, record_id, field)
    format_name = schema.get("format")
    if format_name == "date" and not _is_iso_date(value):
        _issue(issues, "SCHEMA_DATE", artifact, record_id, field)
    elif format_name == "date-time" and not _is_iso_datetime(value):
        _issue(issues, "SCHEMA_DATETIME", artifact, record_id, field)
    elif format_name in {"https-url", "uri"} and not _is_https_url(value):
        _issue(issues, "SCHEMA_HTTPS_URL", artifact, record_id, field)


def _matches_type(value: object, allowed_types: object) -> bool:
    names = [allowed_types] if isinstance(allowed_types, str) else allowed_types
    if not isinstance(names, list):
        return False
    checks = {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "boolean": lambda: isinstance(value, bool),
        "null": lambda: value is None,
    }
    return any(isinstance(name, str) and name in checks and checks[name]() for name in names)


def _is_iso_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _is_iso_datetime(value: str) -> bool:
    if "T" not in value:
        return False
    try:
        normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _record_id(
    value: object, schema: Mapping[str, object], previous: str | None
) -> str | None:
    if not isinstance(value, dict):
        return previous
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return previous
    for key in ("id", "public_id", "record_id", "office_public_id"):
        candidate = value.get(key)
        candidate_schema = properties.get(key)
        pattern = (
            candidate_schema.get("pattern")
            if isinstance(candidate_schema, Mapping)
            else None
        )
        if (
            isinstance(candidate, str)
            and isinstance(pattern, str)
            and re.fullmatch(pattern, candidate) is not None
        ):
            return candidate
    return previous


def _json_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        return (
            left.keys() == right.keys()
            and all(_json_equal(left[key], right[key]) for key in left)
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _json_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def _is_json_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _join(parent: str | None, child: str) -> str:
    return child if parent is None else f"{parent}.{child}"


def _issue(
    issues: list[ValidationIssue],
    code: str,
    artifact: str,
    record_id: str | None,
    field: str | None,
) -> None:
    issues.append(ValidationIssue(code, artifact, record_id, field))
