"""Stable, dependency-free CLI for the DATA-001 staging boundary."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
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
            manifest = build_pending_manifest(Path(arguments.draft_dir), arguments.submitted_at)
            _write_json_atomic(Path(arguments.draft_dir) / "approval_manifest.json", manifest)
        except (OSError, ValueError, json.JSONDecodeError):
            print("[FAIL] step=PREPARE-DATA-001 reason=validation")
            return 1
        print("[PASS] step=PREPARE-DATA-001")
        return 0
    if arguments.command == "validate":
        try:
            report = validate_staging(
                Path(arguments.draft_dir), SCHEMA_DIR, Path(arguments.source_registry)
            )
            if arguments.report:
                _write_json_atomic(Path(arguments.report), report)
        except (OSError, ValueError, json.JSONDecodeError):
            print("[FAIL] step=VALIDATE-DATA-001 issues=VALIDATION_RUNTIME_ERROR:1")
            return 1
        if report["valid"]:
            print("[PASS] step=VALIDATE-DATA-001")
            return 0
        counts = Counter(
            issue["code"] for issue in report["issues"] if isinstance(issue, dict)
        )
        summary = ",".join(f"{code}:{counts[code]}" for code in sorted(counts))
        print(f"[FAIL] step=VALIDATE-DATA-001 issues={summary}")
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


if __name__ == "__main__":
    raise SystemExit(main())
