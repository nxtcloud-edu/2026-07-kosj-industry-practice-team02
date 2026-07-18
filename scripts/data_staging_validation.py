"""Dependency-free helpers for validating DATA-001 staging JSON contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping, Sequence
from urllib.parse import urlparse


CONTENT_ARTIFACTS = (
    "kb_records.json",
    "offices.json",
    "office_service_mappings.json",
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
    re.compile(r"\b\d{6}-?[1-4]\d{6}\b"),
    re.compile(r"\b01[016789]-?\d{3,4}-?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b\d{2,3}[가-힣]\d{4}\b"),
    re.compile(r"\b\d{1,4}동\s*\d{1,4}호\b"),
)
_SECRET_PATTERN = re.compile(
    r"(?i)(?:\b(?:api[_-]?key|secret|token|password)\s*[:=]|\bsk-[A-Za-z0-9_-]+)"
)
_MOCK_PATTERN = re.compile(r"(?i)(?:\bmock\b|시연용\s*샘플)")
_KB_ID_PATTERN = r"KB-(?:MOVE|CERT|WASTE|TAX)-[0-9]{2}"
_OFFICE_ID_PATTERN = r"OFFICE-(?:AREUM|DODAM|JOCHIWON)"


@dataclass(frozen=True, order=True)
class ValidationIssue:
    """A stable, value-free schema validation failure."""

    code: str
    artifact: str
    record_id: str | None
    field: str | None


def load_json_object(path: Path) -> dict[str, object]:
    """Load a JSON object without accepting arrays or scalar roots."""
    value = json.loads(path.read_text(encoding="utf-8"))
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
    serialized = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(f"{serialized}\n", encoding="utf-8", newline="\n")


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
        except (OSError, ValueError, json.JSONDecodeError):
            _issue(issues, "ARTIFACT_MISSING", artifact, None, None)
            continue
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
    _validate_sources(kb_records, office_records, mapping_records, source_registry, issues)
    _validate_text_safety(kb_records, "kb_records.json", issues)
    _validate_text_safety(office_records, "offices.json", issues, {"phone", "address"})
    _validate_text_safety(mapping_records, "office_service_mappings.json", issues)
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
    return {
        "schema_version": 1,
        "draft_version": "0.1.0-draft.1",
        "valid": not normalized_issues,
        "counts": counts,
        "approval_projection": _approval_projection(artifacts.get("approval_manifest.json")),
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
            if artifacts.get("approval_manifest.json", {}).get("state") == "PENDING_PM_REVIEW"
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
) -> None:
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
    registry = _load_source_registry(source_registry, issues)
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


def _load_source_registry(path: Path, issues: list[ValidationIssue]) -> dict[str, dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            fieldnames = tuple(reader.fieldnames or ())
            rows = list(reader)
    except OSError:
        _issue(issues, "SOURCE_REGISTRY_ID_SET", "kb_source_registry.csv", None, "kb_id")
        return {}
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
    return registry


def _has_allowed_source_host(value: object) -> bool:
    return isinstance(value, str) and urlparse(value).hostname in ALLOWED_SOURCE_HOSTS


def _has_allowed_map_host(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return urlparse(value).hostname in (ALLOWED_SOURCE_HOSTS | {"place.map.kakao.com"})


def _validate_text_safety(
    records: list[dict[str, object]], artifact: str, issues: list[ValidationIssue],
    allowed_fields: set[str] | None = None,
) -> None:
    allowed_fields = allowed_fields or set()
    for record in records:
        record_id = _record_identifier(record)
        for field, value in _text_fields(record):
            top_level = field.split(".", 1)[0]
            if _SECRET_PATTERN.search(value):
                _issue(issues, "SECRET_DETECTED", artifact, record_id, field)
            if _MOCK_PATTERN.search(value):
                _issue(issues, "MOCK_REFERENCE", artifact, record_id, field)
            if top_level not in allowed_fields and any(pattern.search(value) for pattern in _PII_PATTERNS):
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
        return [
            pair for key, item in value.items() if isinstance(key, str)
            for pair in _text_fields(item, _join(prefix, key))
        ]
    return []


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
        if _approval_projection(manifest) != {
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


def _approval_projection(manifest: object | None) -> dict[str, int]:
    decisions = manifest.get("decisions") if isinstance(manifest, dict) else []
    if not isinstance(decisions, list):
        decisions = []
    specs = _static_decision_specs()
    expected_pairs = [(record_type, record_id) for record_type, record_id, _ in specs]
    pairs = [
        (entry.get("record_type"), entry.get("record_id"))
        for entry in decisions if isinstance(entry, dict)
    ]
    if pairs != expected_pairs:
        return _empty_projection()
    state = manifest.get("state") if isinstance(manifest, dict) else None
    if any(
        entry.get("recommended_decision") != recommendation
        for entry, (_, _, recommendation) in zip(decisions, specs, strict=True)
        if isinstance(entry, dict)
    ):
        return _empty_projection()
    field = "recommended_decision" if state == "PENDING_PM_REVIEW" else "decision"
    if state == "PENDING_PM_REVIEW" and any(
        isinstance(entry, dict)
        and (entry.get("decision") is not None or entry.get("comment") is not None)
        for entry in decisions
    ):
        return _empty_projection()
    if state in {"APPROVED_FOR_INITIAL_RELEASE", "REJECTED"} and any(
        not isinstance(entry, dict)
        or entry.get("decision") not in {"APPROVE_INITIAL_RELEASE", "WITHHOLD_FOR_REGRESSION", "REJECT"}
        or (
            entry.get("record_type") in {"OFFICE", "MAPPING"}
            and entry.get("decision") == "WITHHOLD_FOR_REGRESSION"
        )
        for entry in decisions
    ):
        return _empty_projection()
    if state == "APPROVED_FOR_INITIAL_RELEASE":
        reviewed_by_pair = {
            (entry.get("record_type"), entry.get("record_id")): entry.get("decision")
            for entry in decisions if isinstance(entry, dict)
        }
        if not all(_approved_policy_flags(reviewed_by_pair)):
            return _empty_projection()
    if state not in {"PENDING_PM_REVIEW", "APPROVED_FOR_INITIAL_RELEASE", "REJECTED"}:
        return _empty_projection()
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


def _empty_projection() -> dict[str, int]:
    return {"initial_kb": 0, "initial_office": 0, "initial_mapping": 0, "withheld_kb": 0, "rejected_mapping": 0}


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


def _validate_runtime_staging_references(issues: list[ValidationIssue]) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    paths = [
        repository_root / "apps",
        repository_root / "packages",
        repository_root / "database",
        repository_root / "supabase" / "seed.sql",
        repository_root / "supabase" / "migrations",
    ]
    for path in paths:
        candidates = path.rglob("*") if path.is_dir() else (path,)
        for candidate in candidates:
            if {".next", "node_modules", ".venv", "__pycache__"} & set(candidate.parts):
                continue
            if not candidate.is_file() or candidate.suffix.lower() not in {
                ".py", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".sql", ".json", ".toml",
            }:
                continue
            try:
                lines = candidate.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            if any(_is_runtime_staging_reference(line) for line in lines):
                relative = candidate.relative_to(repository_root).as_posix()
                _issue(issues, "RUNTIME_STAGING_REFERENCE", relative, None, None)


def _is_runtime_staging_reference(line: str) -> bool:
    stripped = line.lstrip()
    if stripped.startswith(("#", "//", "--", "/*", "*")):
        return False
    return "data/staging/" in line.replace("\\", "/")


def validate_schema(
    instance: object, schema: dict[str, object], artifact: str
) -> Sequence[ValidationIssue]:
    """Validate the small JSON Schema subset used by DATA-001 contracts."""
    issues: list[ValidationIssue] = []
    _validate(instance, schema, artifact, None, None, issues)
    return sorted(issues, key=lambda issue: (
        issue.artifact,
        issue.record_id or "",
        issue.field or "",
        issue.code,
    ))


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
                    _join(field, name),
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
