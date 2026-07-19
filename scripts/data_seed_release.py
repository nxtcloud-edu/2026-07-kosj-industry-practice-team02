"""Pure, dependency-free trust checks for the DATA-SEED initial release.

This module deliberately validates only approved DATA-001 input.  It neither
publishes an official release nor writes a database or dispatcher artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Mapping, Sequence

from scripts.data_staging_validation import validate_staging


CANONICAL_DRAFT_RELATIVE_PATH = Path("data/staging/data-001/0.1.0-draft.1")
CANONICAL_STAGE_SCHEMA_RELATIVE_PATH = Path("data/schemas/data-001/v1")
CANONICAL_SOURCE_REGISTRY_RELATIVE_PATH = Path("data/official/kb_source_registry.csv")
CONTENT_ARTIFACTS = (
    "kb_records.json",
    "offices.json",
    "office_service_mappings.json",
)
APPROVAL_ARTIFACT = "approval_manifest.json"
CANONICAL_CONTENT_HASHES = {
    "kb_records.json": "38d0c801b3dab3962b5cd01fe15a43a60121963b53e8b1f7ac65304d07267365",
    "offices.json": "fe942ce476c7d78f5b17deb10fd3b53e5b673f3ae36cf67a042823ccd51a7af0",
    "office_service_mappings.json": "a0fb8f3c423c0b0b199ed27cdb35cf40efa9011e7ae3d6736f420fc175ee4e1b",
}
CANONICAL_APPROVAL_SHA256 = "466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a"
CANONICAL_CONTENT_COUNTS = {
    "kb_records.json": 20,
    "offices.json": 3,
    "office_service_mappings.json": 12,
}
AUTHOR = "AI-DATA-BACKEND"
REVIEWER = "PM-LOCAL-001"
REVIEWED_AT = "2026-07-19T02:06:19+09:00"
OFFICE_IDS = ("OFFICE-AREUM", "OFFICE-DODAM", "OFFICE-JOCHIWON")
INTENTS = (
    "BULKY_WASTE",
    "CERTIFICATE_ISSUANCE",
    "LOCAL_TAX_GENERAL",
    "MOVE_IN_RESIDENT_REGISTRATION",
)
KB_IDS = tuple(
    f"KB-{category}-{number:02d}"
    for category in ("CERT", "MOVE", "TAX", "WASTE")
    for number in range(1, 6)
)
EXCLUDED_RECORD_IDS = frozenset({
    "KB-WASTE-03",
    "OFFICE-AREUM:LOCAL_TAX_GENERAL",
    "OFFICE-DODAM:BULKY_WASTE",
})


@dataclass(frozen=True, order=True)
class ReleaseIssue:
    """A stable, value-free rejected-input finding."""

    code: str
    artifact: str
    record_id: str | None = None
    field: str | None = None


def load_json_object_strict(path: Path) -> dict[str, object]:
    """Load a UTF-8 JSON object while rejecting duplicate object members."""

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("JSON_DUPLICATE_MEMBER")
            result[key] = value
        return result

    try:
        payload = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("JSON_UTF8_INVALID") from error
    try:
        value = json.loads(payload, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as error:
        raise ValueError("JSON_INVALID") from error
    if not isinstance(value, dict):
        raise ValueError("JSON_ROOT_MUST_BE_OBJECT")
    return value


def validate_approved_input(
    repository_root: Path, draft_dir: Path,
) -> Sequence[ReleaseIssue]:
    """Fail closed unless ``draft_dir`` is the exact approved DATA-001 input.

    Findings intentionally carry only stable codes and structural locations so
    callers cannot accidentally emit approval comments or authored content.
    """
    issues: list[ReleaseIssue] = []
    root = Path(repository_root)
    draft = Path(draft_dir)
    expected_draft = root / CANONICAL_DRAFT_RELATIVE_PATH
    if not _is_trusted_directory(root):
        _issue(issues, "REPOSITORY_ROOT_INVALID", "repository", None, None)
        return _normalized(issues)
    if not _is_exact_path(draft, expected_draft) or not _is_trusted_directory(draft):
        _issue(issues, "CANONICAL_DRAFT_PATH_INVALID", "approval_manifest.json", None, None)
        return _normalized(issues)

    stage_schema_dir = root / CANONICAL_STAGE_SCHEMA_RELATIVE_PATH
    source_registry = root / CANONICAL_SOURCE_REGISTRY_RELATIVE_PATH
    if not _is_trusted_directory(stage_schema_dir) or not _is_trusted_file(source_registry):
        _issue(issues, "CANONICAL_VALIDATION_INPUT_INVALID", "repository", None, None)
        return _normalized(issues)

    artifacts: dict[str, dict[str, object]] = {}
    for artifact in (*CONTENT_ARTIFACTS, APPROVAL_ARTIFACT):
        path = draft / artifact
        if not _is_trusted_file(path):
            _issue(issues, "APPROVED_ARTIFACT_INVALID", artifact, None, None)
            continue
        try:
            artifacts[artifact] = load_json_object_strict(path)
        except (OSError, ValueError):
            _issue(issues, "APPROVED_ARTIFACT_INVALID", artifact, None, None)

    if len(artifacts) != len(CONTENT_ARTIFACTS) + 1:
        return _normalized(issues)

    _validate_current_staging(draft, stage_schema_dir, source_registry, issues)
    _validate_content_bytes(draft, issues)
    _validate_approval_manifest(artifacts[APPROVAL_ARTIFACT], draft, issues)
    return _normalized(issues)


def _validate_current_staging(
    draft: Path, stage_schema_dir: Path, source_registry: Path, issues: list[ReleaseIssue],
) -> None:
    try:
        report = validate_staging(draft, stage_schema_dir, source_registry)
    except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        _issue(issues, "DATA_STAGING_VALIDATION_ERROR", "approval_manifest.json", None, None)
        return
    if report.get("valid") is not True:
        _issue(issues, "DATA_STAGING_INVALID", "approval_manifest.json", None, None)


def _validate_content_bytes(draft: Path, issues: list[ReleaseIssue]) -> None:
    for artifact in CONTENT_ARTIFACTS:
        try:
            actual = _sha256_file(draft / artifact)
        except OSError:
            _issue(issues, "CANONICAL_CONTENT_HASH_INVALID", artifact, None, "sha256")
            continue
        if actual != CANONICAL_CONTENT_HASHES[artifact]:
            _issue(issues, "CANONICAL_CONTENT_HASH_INVALID", artifact, None, "sha256")


def _validate_approval_manifest(
    manifest: Mapping[str, object], draft: Path, issues: list[ReleaseIssue],
) -> None:
    artifact = APPROVAL_ARTIFACT
    if manifest.get("state") != "APPROVED_FOR_INITIAL_RELEASE":
        _issue(issues, "APPROVAL_STATE_INVALID", artifact, None, "state")
    if manifest.get("created_by") != AUTHOR:
        _issue(issues, "APPROVAL_AUTHOR_INVALID", artifact, None, "created_by")
    if manifest.get("reviewed_by") != REVIEWER:
        _issue(issues, "APPROVAL_REVIEWER_INVALID", artifact, None, "reviewed_by")
    if manifest.get("reviewed_at") != REVIEWED_AT or not _is_timezone_aware_datetime(
        manifest.get("reviewed_at")
    ):
        _issue(issues, "APPROVAL_TIMESTAMP_INVALID", artifact, None, "reviewed_at")
    if not _nonempty_string(manifest.get("review_comment")):
        _issue(issues, "APPROVAL_COMMENT_INVALID", artifact, None, "review_comment")

    try:
        manifest_hash = _sha256_file(draft / APPROVAL_ARTIFACT)
    except OSError:
        manifest_hash = ""
    if manifest_hash != CANONICAL_APPROVAL_SHA256:
        _issue(issues, "APPROVAL_MANIFEST_HASH_INVALID", artifact, None, "sha256")

    _validate_manifest_artifacts(manifest.get("artifacts"), draft, issues)
    _validate_decisions(manifest.get("decisions"), issues)


def _validate_manifest_artifacts(
    entries: object, draft: Path, issues: list[ReleaseIssue],
) -> None:
    artifact = APPROVAL_ARTIFACT
    if not isinstance(entries, list) or len(entries) != len(CONTENT_ARTIFACTS):
        _issue(issues, "APPROVAL_ARTIFACTS_INVALID", artifact, None, "artifacts")
        return
    by_path: dict[str, Mapping[str, object]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            _issue(issues, "APPROVAL_ARTIFACTS_INVALID", artifact, None, "artifacts")
            return
        path = entry["path"]
        if path in by_path:
            _issue(issues, "APPROVAL_ARTIFACTS_INVALID", artifact, None, "artifacts")
            return
        by_path[path] = entry
    if set(by_path) != set(CONTENT_ARTIFACTS):
        _issue(issues, "APPROVAL_ARTIFACTS_INVALID", artifact, None, "artifacts")
        return
    for path in CONTENT_ARTIFACTS:
        entry = by_path[path]
        if (
            entry.get("record_count") != CANONICAL_CONTENT_COUNTS[path]
            or entry.get("sha256") != CANONICAL_CONTENT_HASHES[path]
        ):
            _issue(issues, "APPROVAL_ARTIFACTS_INVALID", artifact, None, "artifacts")
            return
        try:
            current_hash = _sha256_file(draft / path)
        except OSError:
            current_hash = ""
        if current_hash != entry.get("sha256"):
            _issue(issues, "APPROVAL_ARTIFACTS_INVALID", artifact, None, "artifacts")
            return


def _validate_decisions(decisions: object, issues: list[ReleaseIssue]) -> None:
    artifact = APPROVAL_ARTIFACT
    expected = _expected_decisions()
    if not isinstance(decisions, list) or len(decisions) != len(expected):
        _issue(issues, "APPROVAL_DECISIONS_INVALID", artifact, None, "decisions")
        _issue(issues, "APPROVED_PROJECTION_INVALID", artifact, None, "decisions")
        return

    actual_pairs: list[tuple[object, object]] = []
    projection = {"KB": 0, "OFFICE": 0, "MAPPING": 0}
    withheld_kb = 0
    rejected_mapping = 0
    structurally_valid = True
    for decision, expected_entry in zip(decisions, expected, strict=True):
        if not isinstance(decision, dict):
            structurally_valid = False
            continue
        record_type, record_id, expected_disposition = expected_entry
        actual_pairs.append((decision.get("record_type"), decision.get("record_id")))
        if (
            decision.get("record_type") != record_type
            or decision.get("record_id") != record_id
            or decision.get("recommended_decision") != expected_disposition
            or decision.get("decision") != expected_disposition
            or not _nonempty_string(decision.get("comment"))
        ):
            structurally_valid = False
        disposition = decision.get("decision")
        if record_type in projection and disposition == "APPROVE_INITIAL_RELEASE":
            projection[record_type] += 1
        elif record_type == "KB" and disposition == "WITHHOLD_FOR_REGRESSION":
            withheld_kb += 1
        elif record_type == "MAPPING" and disposition == "REJECT":
            rejected_mapping += 1

    expected_pairs = [(record_type, record_id) for record_type, record_id, _ in expected]
    if actual_pairs != expected_pairs or len(set(actual_pairs)) != len(expected_pairs):
        structurally_valid = False
    if not structurally_valid:
        _issue(issues, "APPROVAL_DECISIONS_INVALID", artifact, None, "decisions")
    if (
        projection != {"KB": 19, "OFFICE": 3, "MAPPING": 10}
        or withheld_kb != 1
        or rejected_mapping != 2
    ):
        _issue(issues, "APPROVED_PROJECTION_INVALID", artifact, None, "decisions")


def _expected_decisions() -> tuple[tuple[str, str, str], ...]:
    expected: list[tuple[str, str, str]] = [
        (
            "KB",
            record_id,
            "WITHHOLD_FOR_REGRESSION"
            if record_id == "KB-WASTE-03"
            else "APPROVE_INITIAL_RELEASE",
        )
        for record_id in KB_IDS
    ]
    expected.extend(
        (
            "MAPPING",
            f"{office_id}:{intent}",
            "REJECT"
            if f"{office_id}:{intent}" in EXCLUDED_RECORD_IDS
            else "APPROVE_INITIAL_RELEASE",
        )
        for office_id in OFFICE_IDS
        for intent in INTENTS
    )
    expected.extend(
        ("OFFICE", office_id, "APPROVE_INITIAL_RELEASE") for office_id in OFFICE_IDS
    )
    return tuple(expected)


def _is_exact_path(candidate: Path, expected: Path) -> bool:
    try:
        candidate_absolute = candidate.absolute()
        expected_absolute = expected.absolute()
    except OSError:
        return False
    if os.path.normcase(str(candidate_absolute)) != os.path.normcase(str(expected_absolute)):
        return False
    if _has_reparse_component(candidate):
        return False
    try:
        return os.path.normcase(str(candidate.resolve(strict=True))) == os.path.normcase(
            str(expected.resolve(strict=True))
        )
    except OSError:
        return False


def _is_trusted_directory(path: Path) -> bool:
    try:
        return path.is_dir() and not _has_reparse_component(path)
    except OSError:
        return False


def _is_trusted_file(path: Path) -> bool:
    try:
        return path.is_file() and not _has_reparse_component(path)
    except OSError:
        return False


def _has_reparse_component(path: Path) -> bool:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if not current.exists():
            continue
        try:
            if _is_link_or_reparse_point(current):
                return True
        except OSError:
            return True
    return False


def _is_link_or_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_timezone_aware_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _issue(
    issues: list[ReleaseIssue], code: str, artifact: str,
    record_id: str | None, field: str | None,
) -> None:
    issues.append(ReleaseIssue(code, artifact, record_id, field))


def _normalized(issues: list[ReleaseIssue]) -> tuple[ReleaseIssue, ...]:
    return tuple(sorted(set(issues), key=lambda issue: (
        issue.artifact, issue.record_id or "", issue.field or "", issue.code,
    )))
