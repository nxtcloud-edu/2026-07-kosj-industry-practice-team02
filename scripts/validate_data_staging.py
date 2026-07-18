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

from scripts.data_staging_validation import build_pending_manifest, validate_staging


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPOSITORY_ROOT / "data" / "schemas" / "data-001" / "v1"
DEFAULT_SOURCE_REGISTRY = REPOSITORY_ROOT / "data" / "official" / "kb_source_registry.csv"


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
            _write_json_atomic(Path(arguments.draft_dir) / "approval_manifest.json", manifest)
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
    print("[FAIL] step=VALIDATE-DATA-001 reason=usage")
    return 2


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as temporary:
        temporary.write(serialized)
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


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
