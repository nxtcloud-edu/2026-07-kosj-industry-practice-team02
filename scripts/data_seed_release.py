"""Pure, dependency-free generation for immutable DATA-SEED releases.

This module validates approved DATA-001 input and deterministically projects
release bytes.  It never publishes a release or writes a database/dispatcher.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
from typing import Mapping, Sequence

from scripts.data_staging_validation import validate_schema, validate_staging


CANONICAL_DRAFT_TOKEN = "data/staging/data-001/0.1.0-draft.1"
CANONICAL_DRAFT_RELATIVE_PATH = Path(CANONICAL_DRAFT_TOKEN)
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
CANONICAL_APPROVAL_SHA256 = (
    "466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a"
)
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
EXCLUDED_RECORD_IDS = frozenset(
    {
        "KB-WASTE-03",
        "OFFICE-AREUM:LOCAL_TAX_GENERAL",
        "OFFICE-DODAM:BULKY_WASTE",
    }
)
SOURCE_DRAFT_VERSION = "0.1.0-draft.1"


@dataclass(frozen=True)
class ReleaseProfile:
    """Trusted generation and verification configuration for one release."""

    version: str
    release_id: str
    released_at: str
    released_at_utc: str
    canonical_token: str
    schema_token: str
    generator_id: str
    manifest_schema_version: int
    membership_guard: str
    predecessor_version: str | None = None
    predecessor_manifest_sha256: str | None = None
    decision_id: str | None = None
    correction_reason: str | None = None


INITIAL_RELEASE_PROFILE = ReleaseProfile(
    version="0.1.0-initial.1",
    release_id="sejong-official-0.1.0-initial.1",
    released_at="2026-07-19T09:20:31+09:00",
    released_at_utc="2026-07-19T00:20:31Z",
    canonical_token="data/official/releases/0.1.0-initial.1",
    schema_token="data/schemas/data-seed/v1",
    generator_id="data-seed-release-v1",
    manifest_schema_version=1,
    membership_guard="legacy-single-row",
)
SUCCESSOR_RELEASE_PROFILE = ReleaseProfile(
    version="0.1.0-initial.2",
    release_id="sejong-official-0.1.0-initial.2",
    released_at="2026-07-20T20:41:24+09:00",
    released_at_utc="2026-07-20T11:41:24Z",
    canonical_token="data/official/releases/0.1.0-initial.2",
    schema_token="data/schemas/data-seed/v2",
    generator_id="data-seed-release-v2",
    manifest_schema_version=2,
    membership_guard="effective-option-union",
    predecessor_version="0.1.0-initial.1",
    predecessor_manifest_sha256=(
        "e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2"
    ),
    decision_id="D-044",
    correction_reason="POSTGRES17_EFFECTIVE_MEMBERSHIP_OPTION_UNION",
)
RELEASE_PROFILES = {
    profile.version: profile
    for profile in (INITIAL_RELEASE_PROFILE, SUCCESSOR_RELEASE_PROFILE)
}


def release_profile(version: str) -> ReleaseProfile:
    """Return one closed, code-owned release profile or fail closed."""

    if not isinstance(version, str):
        raise ValueError("RELEASE_VERSION_INVALID")
    try:
        return RELEASE_PROFILES[version]
    except KeyError:
        raise ValueError("RELEASE_VERSION_INVALID") from None


RELEASE_VERSION = SUCCESSOR_RELEASE_PROFILE.version
RELEASE_ID = SUCCESSOR_RELEASE_PROFILE.release_id
GENERATOR_ID = SUCCESSOR_RELEASE_PROFILE.generator_id
GOVERNANCE_RELEASED_AT_UTC = SUCCESSOR_RELEASE_PROFILE.released_at_utc
GOVERNANCE_RELEASED_AT = SUCCESSOR_RELEASE_PROFILE.released_at
CANONICAL_RELEASE_TOKEN = SUCCESSOR_RELEASE_PROFILE.canonical_token
CANONICAL_RELEASE_RELATIVE_PATH = Path(CANONICAL_RELEASE_TOKEN)
CANONICAL_RELEASE_SCHEMA_RELATIVE_PATH = Path(SUCCESSOR_RELEASE_PROFILE.schema_token)
RELEASE_ARTIFACTS = (
    "approval_manifest.json",
    "compensation.sql",
    "kb_records.json",
    "office_service_mappings.json",
    "offices.json",
    "release_manifest.json",
    "seed.sql",
)
RELEASE_JSON_SCHEMAS = {
    "release_manifest.json": "release-manifest.schema.json",
    "kb_records.json": "kb-records.schema.json",
    "offices.json": "offices.schema.json",
    "office_service_mappings.json": "office-service-mappings.schema.json",
}

KB_RELEASE_FIELDS = (
    "id",
    "data_origin",
    "category",
    "service_name",
    "question_examples",
    "answer_summary",
    "procedure_steps",
    "required_documents",
    "processing_time",
    "fee",
    "department",
    "provider",
    "source_title",
    "source_url",
    "source_service_id",
    "last_verified_at",
    "caution",
    "status",
    "created_by",
    "approved_by",
    "approved_at",
)
KB_DOCUMENT_FIELDS = (
    "public_id",
    "data_origin",
    "category",
    "service_name",
    "answer_summary",
    "procedure_steps",
    "required_documents",
    "processing_time",
    "fee",
    "department",
    "source_title",
    "source_url",
    "last_verified_at",
    "caution",
    "status",
    "created_by",
    "approved_by",
    "approved_at",
)
KB_QUESTION_EXAMPLE_FIELDS = (
    "kb_public_id",
    "question_example",
    "normalized_text",
)
OFFICE_RELEASE_FIELDS = (
    "public_id",
    "data_origin",
    "region",
    "office_name",
    "address",
    "phone",
    "opening_hours",
    "map_url",
    "provider",
    "source_title",
    "source_url",
    "last_verified_at",
    "created_by",
    "approved_by",
    "approved_at",
)
OFFICE_FIELDS = (
    "public_id",
    "data_origin",
    "region",
    "office_name",
    "address",
    "phone",
    "opening_hours",
    "map_url",
    "source_title",
    "source_url",
    "last_verified_at",
)
MAPPING_RELEASE_FIELDS = (
    "office_public_id",
    "intent",
    "department_label",
    "evidence_source_url",
    "last_verified_at",
    "created_by",
    "approved_by",
    "approved_at",
)
OFFICE_SERVICE_MAPPING_FIELDS = (
    "office_public_id",
    "intent",
    "department_label",
)


@dataclass(frozen=True, order=True)
class ReleaseIssue:
    """A stable, value-free rejected-input finding."""

    code: str
    artifact: str
    record_id: str | None = None
    field: str | None = None


@dataclass(frozen=True)
class ReleaseBundle:
    """All deterministic bytes needed by the later publication task."""

    profile: ReleaseProfile
    manifest: dict[str, object]
    approval_manifest_bytes: bytes
    kb_records_bytes: bytes
    offices_bytes: bytes
    office_service_mappings_bytes: bytes
    seed_sql_bytes: bytes
    compensation_sql_bytes: bytes
    seed_semantic_sha256: str


class ReleaseVerificationError(ValueError):
    """A content-free release verification failure for the publication CLI."""

    def __init__(self, issues: Sequence[ReleaseIssue]) -> None:
        normalized = _normalized(list(issues))
        if not normalized:
            normalized = (
                ReleaseIssue("RELEASE_VERIFICATION_FAILED", "release", None, None),
            )
        self.issues = normalized
        self.reason = normalized[0].code
        super().__init__(self.reason)


@dataclass(frozen=True)
class _ApprovedInputSnapshot:
    """The exact staging bytes and strict-parsed objects used for generation."""

    approval_manifest_bytes: bytes
    kb_records_bytes: bytes
    offices_bytes: bytes
    office_service_mappings_bytes: bytes
    approval_manifest: dict[str, object]
    kb_records: dict[str, object]
    offices: dict[str, object]
    office_service_mappings: dict[str, object]


def load_json_object_strict(path: Path) -> dict[str, object]:
    """Load a UTF-8 JSON object while rejecting duplicate object members."""

    return _load_json_object_strict_bytes(path.read_bytes())


def _load_json_object_strict_bytes(payload: bytes) -> dict[str, object]:
    """Strict-parse one already captured artifact byte string."""

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("JSON_DUPLICATE_MEMBER")
            result[key] = value
        return result

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("JSON_UTF8_INVALID") from error
    try:
        value = json.loads(text, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as error:
        raise ValueError("JSON_INVALID") from error
    if not isinstance(value, dict):
        raise ValueError("JSON_ROOT_MUST_BE_OBJECT")
    return value


def validate_approved_input(
    repository_root: Path,
    draft_token: str,
) -> Sequence[ReleaseIssue]:
    """Fail closed unless ``draft_token`` is the exact approved DATA-001 input.

    Findings intentionally carry only stable codes and structural locations so
    callers cannot accidentally emit approval comments or authored content.
    """
    issues: list[ReleaseIssue] = []
    root = Path(repository_root)
    if not isinstance(draft_token, str) or draft_token != CANONICAL_DRAFT_TOKEN:
        _issue(
            issues, "CANONICAL_DRAFT_PATH_INVALID", "approval_manifest.json", None, None
        )
        return _normalized(issues)
    draft = root / CANONICAL_DRAFT_RELATIVE_PATH
    if not _is_trusted_directory(root):
        _issue(issues, "REPOSITORY_ROOT_INVALID", "repository", None, None)
        return _normalized(issues)
    if not _is_trusted_directory(draft):
        _issue(
            issues, "CANONICAL_DRAFT_PATH_INVALID", "approval_manifest.json", None, None
        )
        return _normalized(issues)

    stage_schema_dir = root / CANONICAL_STAGE_SCHEMA_RELATIVE_PATH
    source_registry = root / CANONICAL_SOURCE_REGISTRY_RELATIVE_PATH
    if not _is_trusted_directory(stage_schema_dir) or not _is_trusted_file(
        source_registry
    ):
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


def canonical_json_bytes(value: object, trailing_newline: bool) -> bytes:
    """Serialize canonical semantic JSON without ASCII escaping or ambient state."""

    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if trailing_newline:
        text += "\n"
    return text.encode("utf-8")


def semantic_sha256(projection: Mapping[str, object]) -> str:
    """Hash the exact canonical seed-owned projection bytes."""

    return hashlib.sha256(
        canonical_json_bytes(projection, trailing_newline=False)
    ).hexdigest()


def build_seed_projection(draft_dir: Path, release_version: str) -> dict[str, object]:
    """Build the exact approved DB-owned projection in canonical row order."""

    repository_root = _repository_root_for_canonical_draft(draft_dir)
    _require_release_version(release_version)
    snapshot = _capture_approved_snapshot(
        repository_root,
        Path(draft_dir),
    )
    _, _, _, projection = _build_projected_records(snapshot, release_version)
    return projection


def build_release_bundle(
    repository_root: Path,
    draft_dir: Path,
    release_version: str,
    released_at: str,
) -> ReleaseBundle:
    """Build a deterministic in-memory release bundle without filesystem writes."""

    root = Path(repository_root).absolute()
    derived_root = _repository_root_for_canonical_draft(draft_dir)
    if root != derived_root:
        raise ValueError("REPOSITORY_ROOT_MISMATCH")
    profile = release_profile(release_version)
    snapshot = _capture_approved_snapshot(root, Path(draft_dir))

    normalized_released_at = _normalize_timestamp(released_at)
    if normalized_released_at != profile.released_at_utc:
        raise ValueError("RELEASE_TIMESTAMP_INVALID")
    kb_records, offices, mappings, projection = _build_projected_records(
        snapshot, release_version
    )
    approval_bytes = snapshot.approval_manifest_bytes
    kb_bytes = _release_json_bytes(
        {
            "schema_version": profile.manifest_schema_version,
            "release_version": release_version,
            "records": kb_records,
        }
    )
    office_bytes = _release_json_bytes(
        {
            "schema_version": profile.manifest_schema_version,
            "release_version": release_version,
            "records": offices,
        }
    )
    mapping_bytes = _release_json_bytes(
        {
            "schema_version": profile.manifest_schema_version,
            "release_version": release_version,
            "records": mappings,
        }
    )

    from scripts.data_seed_sql import render_compensation_sql, render_seed_sql

    seed_bytes = render_seed_sql(
        projection,
        membership_guard=profile.membership_guard,
    )
    compensation_bytes = render_compensation_sql(
        projection,
        membership_guard=profile.membership_guard,
    )
    semantic_hash = semantic_sha256(projection)
    artifact_payloads = {
        "kb_records.json": (len(kb_records), kb_bytes),
        "offices.json": (len(offices), office_bytes),
        "office_service_mappings.json": (len(mappings), mapping_bytes),
        "seed.sql": (0, seed_bytes),
        "compensation.sql": (0, compensation_bytes),
    }
    manifest: dict[str, object] = {
        "schema_version": profile.manifest_schema_version,
        "release_id": profile.release_id,
        "release_version": release_version,
        "source_draft_version": SOURCE_DRAFT_VERSION,
        "released_at": normalized_released_at,
        "approval": {
            "path": APPROVAL_ARTIFACT,
            "sha256": hashlib.sha256(approval_bytes).hexdigest(),
            "reviewed_by": REVIEWER,
            "reviewed_at": _normalize_timestamp(REVIEWED_AT),
        },
        "artifacts": [
            {
                "path": path,
                "record_count": artifact_payloads[path][0],
                "sha256": hashlib.sha256(artifact_payloads[path][1]).hexdigest(),
            }
            for path in sorted(artifact_payloads)
        ],
        "projection": {
            "kb": 19,
            "office": 3,
            "mapping": 10,
            "withheld_kb": 1,
            "rejected_mapping": 2,
            "mock": 0,
        },
        "seed_semantic_sha256": semantic_hash,
        "excluded_record_ids": sorted(EXCLUDED_RECORD_IDS),
        "generator": profile.generator_id,
    }
    if profile.predecessor_version is not None:
        manifest["correction"] = {
            "predecessor_release_version": profile.predecessor_version,
            "predecessor_manifest_sha256": profile.predecessor_manifest_sha256,
            "decision_id": profile.decision_id,
            "reason": profile.correction_reason,
        }
    return ReleaseBundle(
        profile=profile,
        manifest=manifest,
        approval_manifest_bytes=approval_bytes,
        kb_records_bytes=kb_bytes,
        offices_bytes=office_bytes,
        office_service_mappings_bytes=mapping_bytes,
        seed_sql_bytes=seed_bytes,
        compensation_sql_bytes=compensation_bytes,
        seed_semantic_sha256=semantic_hash,
    )


def release_bundle_files(bundle: ReleaseBundle) -> dict[str, bytes]:
    """Return the exact seven immutable release artifact byte strings."""

    return {
        "approval_manifest.json": bundle.approval_manifest_bytes,
        "compensation.sql": bundle.compensation_sql_bytes,
        "kb_records.json": bundle.kb_records_bytes,
        "office_service_mappings.json": bundle.office_service_mappings_bytes,
        "offices.json": bundle.offices_bytes,
        "release_manifest.json": _release_json_bytes(bundle.manifest),
        "seed.sql": bundle.seed_sql_bytes,
    }


def verify_release_directory(
    repository_root: Path,
    release_dir: Path,
) -> dict[str, object]:
    """Verify an exact canonical known release or raise a stable failure."""

    root = Path(repository_root).absolute()
    candidate = Path(release_dir).absolute()
    profile = _release_profile_for_canonical_path(root, candidate)
    if profile is None or not _is_trusted_directory(root):
        raise ReleaseVerificationError(
            (ReleaseIssue("RELEASE_PATH_INVALID", "release", None, None),)
        )
    return _verify_release_contents(root, candidate, profile=profile)


def _verify_release_contents(
    repository_root: Path,
    release_dir: Path,
    expected_bundle: ReleaseBundle | None = None,
    *,
    profile: ReleaseProfile | None = None,
) -> dict[str, object]:
    """Verify one trusted release directory from a single captured byte snapshot."""

    root = Path(repository_root).absolute()
    directory = Path(release_dir).absolute()
    selected_profile = profile
    if expected_bundle is not None:
        if selected_profile is not None and selected_profile != expected_bundle.profile:
            raise ReleaseVerificationError(
                (ReleaseIssue("RELEASE_PROFILE_INVALID", "release", None, None),)
            )
        selected_profile = expected_bundle.profile
    if selected_profile is None:
        selected_profile = _release_profile_for_canonical_path(root, directory)
    if not _is_trusted_directory(root) or not _is_trusted_directory(directory):
        raise ReleaseVerificationError(
            (ReleaseIssue("RELEASE_PATH_INVALID", "release", None, None),)
        )

    try:
        entries = tuple(directory.iterdir())
    except OSError as error:
        raise ReleaseVerificationError(
            (ReleaseIssue("RELEASE_FILE_SET_INVALID", "release", None, None),)
        ) from error
    by_name = {entry.name: entry for entry in entries}
    if set(by_name) != set(RELEASE_ARTIFACTS) or len(entries) != len(RELEASE_ARTIFACTS):
        raise ReleaseVerificationError(
            (ReleaseIssue("RELEASE_FILE_SET_INVALID", "release", None, None),)
        )

    payloads: dict[str, bytes] = {}
    issues: list[ReleaseIssue] = []
    for artifact in RELEASE_ARTIFACTS:
        path = by_name[artifact]
        if not _is_trusted_file(path):
            _issue(issues, "RELEASE_ARTIFACT_INVALID", artifact, None, None)
            continue
        try:
            payloads[artifact] = _read_artifact_bytes_once(path)
        except OSError:
            _issue(issues, "RELEASE_ARTIFACT_INVALID", artifact, None, None)

    if issues:
        raise ReleaseVerificationError(issues)

    parsed: dict[str, dict[str, object]] = {}
    for artifact in (*RELEASE_JSON_SCHEMAS, APPROVAL_ARTIFACT):
        try:
            parsed[artifact] = _load_json_object_strict_bytes(payloads[artifact])
        except ValueError:
            _issue(issues, "RELEASE_JSON_INVALID", artifact, None, None)

    if selected_profile is None:
        _issue(issues, "RELEASE_PATH_INVALID", "release", None, None)
        schema_dir = root / CANONICAL_RELEASE_SCHEMA_RELATIVE_PATH
    else:
        schema_dir = root / Path(selected_profile.schema_token)
    if not _is_trusted_directory(schema_dir):
        _issue(issues, "RELEASE_SCHEMA_INVALID", "release-schema", None, None)
    else:
        for artifact, schema_name in RELEASE_JSON_SCHEMAS.items():
            schema_path = schema_dir / schema_name
            if not _is_trusted_file(schema_path):
                _issue(issues, "RELEASE_SCHEMA_INVALID", artifact, None, None)
                continue
            try:
                schema = _load_json_object_strict_bytes(
                    _read_artifact_bytes_once(schema_path)
                )
            except (OSError, ValueError):
                _issue(issues, "RELEASE_SCHEMA_INVALID", artifact, None, None)
                continue
            instance = parsed.get(artifact)
            if instance is None:
                continue
            schema_issues = validate_schema(instance, schema, artifact)
            for schema_issue in schema_issues:
                _issue(
                    issues,
                    "RELEASE_SCHEMA_INVALID",
                    artifact,
                    schema_issue.record_id,
                    schema_issue.field,
                )

    bundle = expected_bundle
    if bundle is None:
        try:
            if selected_profile is None:
                raise ValueError("RELEASE_VERSION_INVALID")
            bundle = build_release_bundle(
                root,
                root / CANONICAL_DRAFT_RELATIVE_PATH,
                selected_profile.version,
                selected_profile.released_at,
            )
        except (OSError, ValueError):
            _issue(
                issues,
                "RELEASE_REGENERATION_INVALID",
                "release",
                None,
                None,
            )

    expected_payloads = release_bundle_files(bundle) if bundle is not None else {}
    for artifact in RELEASE_ARTIFACTS:
        if payloads.get(artifact) != expected_payloads.get(artifact):
            _issue(issues, "RELEASE_BYTES_INVALID", artifact, None, None)

    if issues:
        raise ReleaseVerificationError(issues)
    assert bundle is not None
    projection = bundle.manifest.get("projection")
    if not isinstance(projection, dict):
        raise ReleaseVerificationError(
            (
                ReleaseIssue(
                    "RELEASE_MANIFEST_INVALID",
                    "release_manifest.json",
                    None,
                    "projection",
                ),
            )
        )
    return {
        "release_version": bundle.profile.version,
        "release_id": bundle.profile.release_id,
        "counts": {
            "kb": projection.get("kb"),
            "office": projection.get("office"),
            "mapping": projection.get("mapping"),
        },
        "seed_semantic_sha256": bundle.seed_semantic_sha256,
        "seed_sql_bytes": payloads["seed.sql"],
        "compensation_sql_bytes": payloads["compensation.sql"],
    }


def _capture_approved_snapshot(
    repository_root: Path,
    draft: Path,
) -> _ApprovedInputSnapshot:
    """Read each approved artifact once, then validate and retain those exact bytes."""

    issues: list[ReleaseIssue] = []
    root = Path(repository_root).absolute()
    canonical_draft = root / CANONICAL_DRAFT_RELATIVE_PATH
    if draft.absolute() != canonical_draft or not _is_trusted_directory(root):
        raise ValueError("APPROVED_INPUT_INVALID")
    if not _is_trusted_directory(canonical_draft):
        raise ValueError("APPROVED_INPUT_INVALID")

    stage_schema_dir = root / CANONICAL_STAGE_SCHEMA_RELATIVE_PATH
    source_registry = root / CANONICAL_SOURCE_REGISTRY_RELATIVE_PATH
    if not _is_trusted_directory(stage_schema_dir) or not _is_trusted_file(
        source_registry
    ):
        raise ValueError("APPROVED_INPUT_INVALID")

    captured_bytes: dict[str, bytes] = {}
    captured_objects: dict[str, dict[str, object]] = {}
    for artifact in (*CONTENT_ARTIFACTS, APPROVAL_ARTIFACT):
        path = canonical_draft / artifact
        if not _is_trusted_file(path):
            raise ValueError("APPROVED_INPUT_INVALID")
        try:
            payload = _read_artifact_bytes_once(path)
            parsed = _load_json_object_strict_bytes(payload)
        except (OSError, ValueError):
            raise ValueError("APPROVED_INPUT_INVALID") from None
        captured_bytes[artifact] = payload
        captured_objects[artifact] = parsed

    snapshot = _ApprovedInputSnapshot(
        approval_manifest_bytes=captured_bytes[APPROVAL_ARTIFACT],
        kb_records_bytes=captured_bytes["kb_records.json"],
        offices_bytes=captured_bytes["offices.json"],
        office_service_mappings_bytes=captured_bytes["office_service_mappings.json"],
        approval_manifest=captured_objects[APPROVAL_ARTIFACT],
        kb_records=captured_objects["kb_records.json"],
        offices=captured_objects["offices.json"],
        office_service_mappings=captured_objects["office_service_mappings.json"],
    )
    _validate_approved_snapshot(snapshot, issues)

    # The DATA-001 business/schema/privacy validator still gates the current
    # repository.  It may observe a concurrent path change after capture and
    # fail closed; generation below never reopens the captured artifacts.
    _validate_current_staging(
        canonical_draft,
        stage_schema_dir,
        source_registry,
        issues,
    )
    if issues:
        raise ValueError("APPROVED_INPUT_INVALID")
    return snapshot


def _read_artifact_bytes_once(path: Path) -> bytes:
    """Single source read seam used by the snapshot race regression."""

    return path.read_bytes()


def _validate_approved_snapshot(
    snapshot: _ApprovedInputSnapshot,
    issues: list[ReleaseIssue],
) -> None:
    content_bytes = {
        "kb_records.json": snapshot.kb_records_bytes,
        "offices.json": snapshot.offices_bytes,
        "office_service_mappings.json": snapshot.office_service_mappings_bytes,
    }
    content_hashes = {
        artifact: hashlib.sha256(payload).hexdigest()
        for artifact, payload in content_bytes.items()
    }
    for artifact in CONTENT_ARTIFACTS:
        if content_hashes[artifact] != CANONICAL_CONTENT_HASHES[artifact]:
            _issue(
                issues,
                "CANONICAL_CONTENT_HASH_INVALID",
                artifact,
                None,
                "sha256",
            )

    manifest = snapshot.approval_manifest
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
    if (
        hashlib.sha256(snapshot.approval_manifest_bytes).hexdigest()
        != CANONICAL_APPROVAL_SHA256
    ):
        _issue(issues, "APPROVAL_MANIFEST_HASH_INVALID", artifact, None, "sha256")
    _validate_snapshot_manifest_artifacts(
        manifest.get("artifacts"),
        content_hashes,
        issues,
    )
    _validate_decisions(manifest.get("decisions"), issues)


def _validate_snapshot_manifest_artifacts(
    entries: object,
    content_hashes: Mapping[str, str],
    issues: list[ReleaseIssue],
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
            or content_hashes[path] != entry.get("sha256")
        ):
            _issue(issues, "APPROVAL_ARTIFACTS_INVALID", artifact, None, "artifacts")
            return


def _build_projected_records(
    snapshot: _ApprovedInputSnapshot,
    release_version: str,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, object],
]:
    manifest = snapshot.approval_manifest
    approved = {
        (decision["record_type"], decision["record_id"])
        for decision in _mapping_list(
            manifest.get("decisions"), "APPROVAL_DECISIONS_INVALID"
        )
        if decision.get("decision") == "APPROVE_INITIAL_RELEASE"
    }
    approved_at = _normalize_timestamp(_required_string(manifest, "reviewed_at"))

    kb_source = _snapshot_records(snapshot.kb_records)
    kb_release: list[dict[str, object]] = []
    kb_projection: list[dict[str, object]] = []
    question_projection: list[dict[str, object]] = []
    for source in kb_source:
        public_id = _required_string(source, "id")
        if ("KB", public_id) not in approved:
            continue
        record = dict(source)
        record.update(
            {
                "status": "ACTIVE",
                "data_origin": "OFFICIAL",
                "approved_by": REVIEWER,
                "approved_at": approved_at,
            }
        )
        projected_release = _allowlisted(record, KB_RELEASE_FIELDS)
        kb_release.append(projected_release)
        db_record: dict[str, object] = {"public_id": public_id}
        db_record.update(
            {
                field: _copy_authored_value(projected_release[field])
                for field in KB_DOCUMENT_FIELDS
                if field != "public_id"
            }
        )
        kb_projection.append(db_record)
        examples = projected_release["question_examples"]
        if not isinstance(examples, list):
            raise ValueError("KB_QUESTION_EXAMPLES_INVALID")
        question_projection.extend(
            {
                "kb_public_id": public_id,
                "question_example": example,
                "normalized_text": None,
            }
            for example in examples
        )

    office_source = _snapshot_records(snapshot.offices)
    office_release: list[dict[str, object]] = []
    office_projection: list[dict[str, object]] = []
    for source in office_source:
        public_id = _required_string(source, "public_id")
        if ("OFFICE", public_id) not in approved:
            continue
        record = dict(source)
        record.update(
            {
                "data_origin": "OFFICIAL",
                "approved_by": REVIEWER,
                "approved_at": approved_at,
            }
        )
        projected_release = _allowlisted(record, OFFICE_RELEASE_FIELDS)
        office_release.append(projected_release)
        office_projection.append(_allowlisted(projected_release, OFFICE_FIELDS))

    mapping_source = _snapshot_records(snapshot.office_service_mappings)
    mapping_release: list[dict[str, object]] = []
    mapping_projection: list[dict[str, object]] = []
    for source in mapping_source:
        mapping_id = (
            f"{_required_string(source, 'office_public_id')}:"
            f"{_required_string(source, 'intent')}"
        )
        if ("MAPPING", mapping_id) not in approved:
            continue
        record = dict(source)
        record.update({"approved_by": REVIEWER, "approved_at": approved_at})
        projected_release = _allowlisted(record, MAPPING_RELEASE_FIELDS)
        mapping_release.append(projected_release)
        mapping_projection.append(
            _allowlisted(projected_release, OFFICE_SERVICE_MAPPING_FIELDS)
        )

    kb_release.sort(key=lambda row: str(row["id"]))
    kb_projection.sort(key=lambda row: str(row["public_id"]))
    question_projection.sort(
        key=lambda row: (str(row["kb_public_id"]), str(row["question_example"]))
    )
    office_release.sort(key=lambda row: str(row["public_id"]))
    office_projection.sort(key=lambda row: str(row["public_id"]))
    mapping_release.sort(
        key=lambda row: (str(row["office_public_id"]), str(row["intent"]))
    )
    mapping_projection.sort(
        key=lambda row: (str(row["office_public_id"]), str(row["intent"]))
    )
    projection: dict[str, object] = {
        "kb_documents": kb_projection,
        "kb_question_examples": question_projection,
        "offices": office_projection,
        "office_service_mappings": mapping_projection,
    }
    if (len(kb_release), len(office_release), len(mapping_release)) != (19, 3, 10):
        raise ValueError("APPROVED_PROJECTION_INVALID")
    return kb_release, office_release, mapping_release, projection


def _repository_root_for_canonical_draft(draft_dir: Path) -> Path:
    draft = Path(draft_dir).absolute()
    try:
        root = draft.parents[3]
    except IndexError as error:
        raise ValueError("CANONICAL_DRAFT_PATH_INVALID") from error
    if draft != root / CANONICAL_DRAFT_RELATIVE_PATH:
        raise ValueError("CANONICAL_DRAFT_PATH_INVALID")
    return root


def _require_release_version(release_version: str) -> None:
    release_profile(release_version)


def _release_profile_for_canonical_path(
    repository_root: Path,
    release_dir: Path,
) -> ReleaseProfile | None:
    root = Path(repository_root).absolute()
    candidate = Path(release_dir).absolute()
    for profile in RELEASE_PROFILES.values():
        if candidate == (root / Path(profile.canonical_token)).absolute():
            return profile
    return None


def _normalize_timestamp(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("TIMESTAMP_INVALID")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("TIMESTAMP_INVALID") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("TIMESTAMP_TIMEZONE_REQUIRED")
    if parsed.microsecond != 0:
        raise ValueError("TIMESTAMP_PRECISION_INVALID")
    normalized = parsed.astimezone(timezone.utc)
    return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")


def _release_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _snapshot_records(artifact: Mapping[str, object]) -> list[Mapping[str, object]]:
    return _mapping_list(artifact.get("records"), "RECORDS_INVALID")


def _mapping_list(value: object, error_code: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(error_code)
    return value


def _allowlisted(
    source: Mapping[str, object],
    fields: tuple[str, ...],
) -> dict[str, object]:
    missing = [field for field in fields if field not in source]
    if missing:
        raise ValueError("PROJECTED_FIELD_MISSING")
    return {field: _copy_authored_value(source[field]) for field in fields}


def _copy_authored_value(value: object) -> object:
    if isinstance(value, list):
        return [_copy_authored_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _copy_authored_value(item) for key, item in value.items()}
    return value


def _required_string(source: Mapping[str, object], field: str) -> str:
    value = source.get(field)
    if not isinstance(value, str):
        raise ValueError("PROJECTED_FIELD_INVALID")
    return value


def _validate_current_staging(
    draft: Path,
    stage_schema_dir: Path,
    source_registry: Path,
    issues: list[ReleaseIssue],
) -> None:
    try:
        report = validate_staging(draft, stage_schema_dir, source_registry)
    except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        _issue(
            issues,
            "DATA_STAGING_VALIDATION_ERROR",
            "approval_manifest.json",
            None,
            None,
        )
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
    manifest: Mapping[str, object],
    draft: Path,
    issues: list[ReleaseIssue],
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
    entries: object,
    draft: Path,
    issues: list[ReleaseIssue],
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

    expected_pairs = [
        (record_type, record_id) for record_type, record_id, _ in expected
    ]
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
    issues: list[ReleaseIssue],
    code: str,
    artifact: str,
    record_id: str | None,
    field: str | None,
) -> None:
    issues.append(ReleaseIssue(code, artifact, record_id, field))


def _normalized(issues: list[ReleaseIssue]) -> tuple[ReleaseIssue, ...]:
    return tuple(
        sorted(
            set(issues),
            key=lambda issue: (
                issue.artifact,
                issue.record_id or "",
                issue.field or "",
                issue.code,
            ),
        )
    )
