"""Stable, dependency-free CLI for the DATA-001 staging boundary."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.data_staging_validation import (
    CANONICAL_SOURCE_AUDIT_PATHS,
    CANONICAL_SOURCE_MATRIX,
    CONTENT_ARTIFACTS,
    build_pending_manifest,
    load_json_object,
    validate_staging,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPOSITORY_ROOT / "data" / "schemas" / "data-001" / "v1"
DEFAULT_SOURCE_REGISTRY = REPOSITORY_ROOT / "data" / "official" / "kb_source_registry.csv"
CANONICAL_DRAFT_DIR = (
    REPOSITORY_ROOT / "data" / "staging" / "data-001" / "0.1.0-draft.1"
)
CANONICAL_REPORT_PATH = (
    REPOSITORY_ROOT / "data" / "processed" / "data-001" / "0.1.0-draft.1"
    / "validation-report.json"
)
LEGACY_PENDING_SUBMITTED_AT = "2026-07-18T19:32:04+09:00"


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def main(argv: list[str] | None = None) -> int:
    parser = _SafeArgumentParser(add_help=False)
    subcommands = parser.add_subparsers(dest="command")
    prepare = subcommands.add_parser("prepare", add_help=False)
    prepare.add_argument("--draft-dir", required=True)
    prepare.add_argument("--submitted-at", required=True)
    prepare.add_argument("--source-registry", default=str(DEFAULT_SOURCE_REGISTRY))
    migrate = subcommands.add_parser("migrate-pending", add_help=False)
    migrate.add_argument("--draft-dir", required=True)
    migrate.add_argument("--submitted-at", required=True)
    migrate.add_argument("--source-registry", default=str(DEFAULT_SOURCE_REGISTRY))
    validate = subcommands.add_parser("validate", add_help=False)
    validate.add_argument("--draft-dir", required=True)
    validate.add_argument("--report")
    validate.add_argument("--source-registry", default=str(DEFAULT_SOURCE_REGISTRY))
    try:
        arguments = parser.parse_args(argv)
    except (SystemExit, ValueError):
        print("[FAIL] step=VALIDATE-DATA-001 reason=usage")
        return 2
    if arguments.command in {"prepare", "validate", "migrate-pending"}:
        draft_dir = Path(arguments.draft_dir)
        source_registry = Path(arguments.source_registry)
        if not _canonical_inputs_are_trusted(
            draft_dir,
            source_registry,
            require_manifest=arguments.command != "prepare",
        ):
            step = {
                "prepare": "PREPARE-DATA-001",
                "validate": "VALIDATE-DATA-001",
                "migrate-pending": "MIGRATE-DATA-001",
            }[arguments.command]
            print(f"[FAIL] step={step} issues=PATH_BOUNDARY_INVALID:1")
            return 1
    if arguments.command == "prepare":
        try:
            manifest = build_pending_manifest(draft_dir, arguments.submitted_at)
            report = validate_staging(
                draft_dir, SCHEMA_DIR, source_registry, manifest
            )
            if not report["valid"]:
                _print_issue_failure("PREPARE-DATA-001", report)
                return 1
            manifest_path = draft_dir / "approval_manifest.json"
            candidate_bytes = _json_bytes(manifest)
            if manifest_path.exists():
                existing = load_json_object(manifest_path)
                if _has_review_evidence(existing):
                    print("[FAIL] step=PREPARE-DATA-001 issues=PREPARE_REVIEW_EVIDENCE:1")
                    return 1
                if manifest_path.read_bytes() != candidate_bytes:
                    print("[FAIL] step=PREPARE-DATA-001 issues=PREPARE_MANIFEST_IMMUTABLE:1")
                    return 1
                print("[PASS] step=PREPARE-DATA-001")
                return 0
            _write_json_atomic(manifest_path, manifest)
        except (OSError, ValueError, json.JSONDecodeError):
            print("[FAIL] step=PREPARE-DATA-001 reason=validation")
            return 1
        print("[PASS] step=PREPARE-DATA-001")
        return 0
    if arguments.command == "validate":
        try:
            if arguments.report and not _is_safe_report_destination(
                Path(arguments.report), draft_dir
            ):
                print("[FAIL] step=VALIDATE-DATA-001 issues=REPORT_DESTINATION_INVALID:1")
                return 1
            report = validate_staging(
                draft_dir, SCHEMA_DIR, source_registry
            )
            if arguments.report:
                _write_json_atomic(Path(arguments.report), report)
        except (OSError, ValueError, json.JSONDecodeError):
            print("[FAIL] step=VALIDATE-DATA-001 issues=VALIDATION_RUNTIME_ERROR:1")
            return 1
        if report["valid"]:
            print("[PASS] step=VALIDATE-DATA-001")
            return 0
        _print_issue_failure("VALIDATE-DATA-001", report)
        return 1
    if arguments.command == "migrate-pending":
        try:
            manifest_path = draft_dir / "approval_manifest.json"
            existing = manifest_path.read_bytes()
            candidate = build_pending_manifest(draft_dir, arguments.submitted_at)
            if not _is_legacy_pending_manifest(existing, candidate):
                print("[FAIL] step=MIGRATE-DATA-001 issues=MIGRATE_PENDING_REFUSED:1")
                return 1
            report = validate_staging(
                draft_dir, SCHEMA_DIR, source_registry, candidate
            )
            if not report["valid"]:
                _print_issue_failure("MIGRATE-DATA-001", report)
                return 1
            _write_json_atomic(manifest_path, candidate)
        except (OSError, ValueError, json.JSONDecodeError):
            print("[FAIL] step=MIGRATE-DATA-001 issues=MIGRATE_PENDING_REFUSED:1")
            return 1
        print("[PASS] step=MIGRATE-DATA-001")
        return 0
    print("[FAIL] step=VALIDATE-DATA-001 reason=usage")
    return 2


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = _json_bytes(value).decode("utf-8")
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as temporary:
        temporary.write(serialized)
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _has_review_evidence(manifest: dict[str, object]) -> bool:
    if manifest.get("state") in {"APPROVED_FOR_INITIAL_RELEASE", "REJECTED"}:
        return True
    if any(manifest.get(field) is not None for field in ("reviewed_by", "reviewed_at", "review_comment")):
        return True
    decisions = manifest.get("decisions")
    return isinstance(decisions, list) and any(
        isinstance(entry, dict)
        and (entry.get("decision") is not None or entry.get("comment") is not None)
        for entry in decisions
    )


def _is_legacy_pending_manifest(
    existing: bytes, candidate: dict[str, object]
) -> bool:
    new_decisions = candidate.get("decisions")
    if not isinstance(new_decisions, list):
        return False
    legacy_decisions: list[dict[str, object]] = []
    for entry in new_decisions:
        if not isinstance(entry, dict):
            return False
        legacy_decisions.append({
            "record_type": entry.get("record_type"),
            "record_id": entry.get("record_id"),
            "decision": entry.get("recommended_decision"),
            "comment": None,
        })
    expected = dict(candidate)
    expected["submitted_at"] = LEGACY_PENDING_SUBMITTED_AT
    expected["decisions"] = legacy_decisions
    return existing == _json_bytes(expected)


def _print_issue_failure(step: str, report: dict[str, object]) -> None:
    issues = report.get("issues")
    counts = Counter(
        issue.get("code") for issue in issues
        if isinstance(issues, list) and isinstance(issue, dict) and isinstance(issue.get("code"), str)
    )
    summary = ",".join(f"{code}:{counts[code]}" for code in sorted(counts))
    print(f"[FAIL] step={step} issues={summary}")


def _is_safe_report_destination(report: Path, draft_dir: Path) -> bool:
    candidate = report if report.is_absolute() else (REPOSITORY_ROOT / report)
    candidate = candidate.absolute()
    if _has_reparse_component(candidate):
        return False
    try:
        if os.path.normcase(str(candidate.resolve())) != os.path.normcase(
            str(CANONICAL_REPORT_PATH.resolve())
        ):
            return False
    except OSError:
        return False
    return True


def _canonical_inputs_are_trusted(
    draft_dir: Path, source_registry: Path, require_manifest: bool
) -> bool:
    if not _is_exact_resolved_path(draft_dir, CANONICAL_DRAFT_DIR):
        return False
    if not _is_exact_resolved_path(source_registry, DEFAULT_SOURCE_REGISTRY):
        return False
    required_files = [
        DEFAULT_SOURCE_REGISTRY,
        CANONICAL_SOURCE_MATRIX,
        *CANONICAL_SOURCE_AUDIT_PATHS,
        *(SCHEMA_DIR / name for name in (
            "approval-manifest.schema.json",
            "kb-records.schema.json",
            "office-service-mappings.schema.json",
            "offices.schema.json",
        )),
        *(CANONICAL_DRAFT_DIR / name for name in CONTENT_ARTIFACTS),
    ]
    if require_manifest:
        required_files.append(CANONICAL_DRAFT_DIR / "approval_manifest.json")
    required_directories = [REPOSITORY_ROOT, SCHEMA_DIR, CANONICAL_DRAFT_DIR]
    for path in required_directories:
        if not path.is_dir() or _has_reparse_component(path):
            return False
    for path in required_files:
        if not path.is_file() or _has_reparse_component(path):
            return False
    manifest = CANONICAL_DRAFT_DIR / "approval_manifest.json"
    return not manifest.exists() or not _has_reparse_component(manifest)


def _is_exact_resolved_path(candidate: Path, expected: Path) -> bool:
    if _has_reparse_component(candidate):
        return False
    try:
        return os.path.normcase(str(candidate.resolve(strict=True))) == os.path.normcase(
            str(expected.resolve(strict=True))
        )
    except OSError:
        return False


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        return os.path.commonpath((os.path.normcase(str(candidate)), os.path.normcase(str(parent)))) == os.path.normcase(str(parent))
    except ValueError:
        return False


def _is_link_or_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


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


if __name__ == "__main__":
    raise SystemExit(main())
