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
    build_pending_manifest,
    load_json_object,
    validate_staging,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPOSITORY_ROOT / "data" / "schemas" / "data-001" / "v1"
DEFAULT_SOURCE_REGISTRY = REPOSITORY_ROOT / "data" / "official" / "kb_source_registry.csv"
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
    if arguments.command == "prepare":
        try:
            draft_dir = Path(arguments.draft_dir)
            manifest = build_pending_manifest(draft_dir, arguments.submitted_at)
            report = validate_staging(
                draft_dir, SCHEMA_DIR, Path(arguments.source_registry), manifest
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
            draft_dir = Path(arguments.draft_dir)
            if arguments.report and not _is_safe_report_destination(
                Path(arguments.report), draft_dir
            ):
                print("[FAIL] step=VALIDATE-DATA-001 issues=REPORT_DESTINATION_INVALID:1")
                return 1
            report = validate_staging(
                draft_dir, SCHEMA_DIR, Path(arguments.source_registry)
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
            draft_dir = Path(arguments.draft_dir)
            manifest_path = draft_dir / "approval_manifest.json"
            existing = manifest_path.read_bytes()
            candidate = build_pending_manifest(draft_dir, arguments.submitted_at)
            if not _is_legacy_pending_manifest(existing, candidate):
                print("[FAIL] step=MIGRATE-DATA-001 issues=MIGRATE_PENDING_REFUSED:1")
                return 1
            report = validate_staging(
                draft_dir, SCHEMA_DIR, Path(arguments.source_registry), candidate
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
    processed_root = (REPOSITORY_ROOT / "data" / "processed").resolve()
    candidate = report if report.is_absolute() else (REPOSITORY_ROOT / report)
    candidate = candidate.absolute()
    if not _is_within(candidate.resolve(), processed_root):
        return False
    resolved_draft = draft_dir.resolve()
    resolved_candidate = candidate.resolve()
    if _is_within(resolved_candidate, resolved_draft) or _is_within(resolved_draft, resolved_candidate):
        return False
    current = candidate.anchor and Path(candidate.anchor)
    if not isinstance(current, Path):
        return False
    for part in candidate.parts[1:]:
        current = current / part
        if current.exists() and _is_link_or_reparse_point(current):
            return False
    return True


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        return os.path.commonpath((os.path.normcase(str(candidate)), os.path.normcase(str(parent)))) == os.path.normcase(str(parent))
    except ValueError:
        return False


def _is_link_or_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


if __name__ == "__main__":
    raise SystemExit(main())
