from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit


EXCLUDED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".next",
        ".pnpm-store",
        ".pytest_cache",
        ".superpowers",
        ".tools",
        ".venv",
        ".worktrees",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "generated",
        "legacy",
        "node_modules",
        "runtime",
    }
)
MARKDOWN_SUFFIXES = frozenset({".markdown", ".md"})
MARKDOWN_TARGET_PATTERN = re.compile(r"\]\(\s*(?P<target>[^)\n]+)\)")
FENCE_PATTERN = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
GIT_ENVIRONMENT_PREFIXES = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
GIT_ENVIRONMENT_NAMES = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_WORK_TREE",
    }
)


class RepositoryCheckError(RuntimeError):
    """Raised when tracked-file inspection cannot be completed safely."""


@dataclass(frozen=True)
class TrackedBlob:
    mode: str
    object_id: str
    relative_path: str


@dataclass(frozen=True)
class MarkdownTarget:
    destination: str
    line: int
    ordinal: int


def escape_source_path(source_path: str) -> str:
    return json.dumps(source_path, ensure_ascii=True)


def is_active(relative_path: PurePosixPath) -> bool:
    return not any(part.lower() in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts)


def git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name in GIT_ENVIRONMENT_NAMES or name.startswith(GIT_ENVIRONMENT_PREFIXES):
            environment.pop(name)
    return environment


def tracked_active_blobs(repository: Path) -> tuple[list[TrackedBlob], set[str]]:
    try:
        repository_check = subprocess.run(
            ["git", "-C", os.fspath(repository), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            env=git_environment(),
        )
        if Path(os.fsdecode(repository_check.stdout.strip())).resolve() != repository:
            raise RepositoryCheckError("inspection root is not a Git work tree")
        completed = subprocess.run(
            ["git", "-C", os.fspath(repository), "ls-files", "--stage", "-z"],
            check=True,
            capture_output=True,
            env=git_environment(),
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise RepositoryCheckError("unable to list tracked files") from error

    blobs: list[TrackedBlob] = []
    tracked_paths: set[str] = set()
    for raw_entry in completed.stdout.split(b"\0"):
        if not raw_entry:
            continue
        metadata, separator, raw_path = raw_entry.partition(b"\t")
        fields = metadata.split()
        if separator != b"\t" or len(fields) != 3:
            raise RepositoryCheckError("REPO_DOCS_INVALID_GIT_INDEX")
        try:
            mode = fields[0].decode("ascii")
            object_id = fields[1].decode("ascii")
            stage = fields[2].decode("ascii")
            source_path = os.fsdecode(raw_path)
        except UnicodeError as error:
            raise RepositoryCheckError("REPO_DOCS_INVALID_GIT_INDEX") from error

        relative_path = PurePosixPath(source_path)
        if relative_path.is_absolute() or ".." in relative_path.parts or stage != "0":
            raise RepositoryCheckError("REPO_DOCS_INVALID_GIT_INDEX")
        tracked_paths.add(source_path)
        if not is_active(relative_path):
            continue
        if mode not in {"100644", "100755"}:
            raise RepositoryCheckError(
                "REPO_DOCS_UNSUPPORTED_TRACKED_ENTRY "
                f"source={escape_source_path(source_path)} mode={json.dumps(mode)}"
            )
        blobs.append(TrackedBlob(mode=mode, object_id=object_id, relative_path=source_path))
    return blobs, tracked_paths


def read_git_blobs(repository: Path, records: list[TrackedBlob]) -> dict[str, bytes]:
    object_ids = list(dict.fromkeys(record.object_id for record in records))
    if not object_ids:
        return {}
    try:
        completed = subprocess.run(
            ["git", "-C", os.fspath(repository), "cat-file", "--batch"],
            input="".join(f"{object_id}\n" for object_id in object_ids).encode("ascii"),
            check=True,
            capture_output=True,
            env=git_environment(),
        )
    except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
        raise RepositoryCheckError("REPO_DOCS_GIT_BLOB_READ_FAILED") from error

    blobs: dict[str, bytes] = {}
    cursor = 0
    output = completed.stdout
    try:
        for expected_object_id in object_ids:
            header_end = output.index(b"\n", cursor)
            header = output[cursor:header_end].split()
            if len(header) != 3 or header[1] != b"blob":
                raise ValueError
            actual_object_id = header[0].decode("ascii")
            size = int(header[2])
            content_start = header_end + 1
            content_end = content_start + size
            if actual_object_id != expected_object_id or output[content_end : content_end + 1] != b"\n":
                raise ValueError
            blobs[expected_object_id] = output[content_start:content_end]
            cursor = content_end + 1
        if cursor != len(output):
            raise ValueError
    except (IndexError, UnicodeError, ValueError) as error:
        raise RepositoryCheckError("REPO_DOCS_GIT_BLOB_READ_FAILED") from error
    return blobs


def repository_local_target(destination: str) -> str | None:
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc:
        return None
    return unquote(parsed.path)


def markdown_targets(contents: str) -> list[MarkdownTarget]:
    targets: list[MarkdownTarget] = []
    active_fence: tuple[str, int] | None = None
    for line_number, line in enumerate(contents.splitlines(), start=1):
        fence = FENCE_PATTERN.match(line)
        if active_fence is not None:
            if fence:
                marker = fence.group("fence")
                if (
                    marker[0] == active_fence[0]
                    and len(marker) >= active_fence[1]
                    and not fence.group("rest").strip()
                ):
                    active_fence = None
            continue
        if fence:
            marker = fence.group("fence")
            active_fence = (marker[0], len(marker))
            continue
        for ordinal, match in enumerate(MARKDOWN_TARGET_PATTERN.finditer(line), start=1):
            destination = match.group("target").strip()
            if destination.startswith("<") and ">" in destination:
                destination = destination[1 : destination.index(">")]
            else:
                title = re.search(r"\s+(?=[\"'][^\"']*[\"']\s*$)", destination)
                if title:
                    destination = destination[: title.start()]
            target = repository_local_target(destination)
            if target is not None:
                targets.append(
                    MarkdownTarget(destination=target, line=line_number, ordinal=ordinal)
                )
    return targets


def tracked_target_exists(target: str, tracked_paths: set[str]) -> bool:
    if target in tracked_paths:
        return True
    prefix = f"{target.rstrip('/')}/"
    return any(path.startswith(prefix) for path in tracked_paths)


def resolve_target(source_path: str, target: str, tracked_paths: set[str]) -> str:
    if not target:
        return source_path
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))

    relative_candidate = posixpath.normpath(
        posixpath.join(posixpath.dirname(source_path), target)
    )
    target_path = PurePosixPath(target)
    if (
        not tracked_target_exists(relative_candidate, tracked_paths)
        and target_path.parts
        and target_path.parts[0] not in {".", ".."}
        and any(path == target_path.parts[0] or path.startswith(f"{target_path.parts[0]}/") for path in tracked_paths)
    ):
        return posixpath.normpath(target)
    return relative_candidate


def check_repository(repository: Path) -> list[str]:
    repository = repository.resolve()
    errors: list[str] = []

    records, tracked_paths = tracked_active_blobs(repository)
    inspected_records = [
        record
        for record in records
        if PurePosixPath(record.relative_path).suffix.lower() == ".json"
        or PurePosixPath(record.relative_path).suffix.lower() in MARKDOWN_SUFFIXES
    ]
    blobs = read_git_blobs(repository, inspected_records)
    for record in inspected_records:
        relative_path = PurePosixPath(record.relative_path)
        try:
            contents = blobs[record.object_id].decode("utf-8")
            if relative_path.suffix.lower() == ".json":
                json.loads(contents)
            if relative_path.suffix.lower() in MARKDOWN_SUFFIXES:
                for target in markdown_targets(contents):
                    resolved = resolve_target(
                        record.relative_path,
                        target.destination,
                        tracked_paths,
                    )
                    if resolved != ".." and not resolved.startswith("../") and not is_active(
                        PurePosixPath(resolved)
                    ):
                        continue
                    if (
                        resolved == ".."
                        or resolved.startswith("../")
                        or not tracked_target_exists(resolved, tracked_paths)
                    ):
                        errors.append(
                            "REPO_DOCS_MISSING_MARKDOWN_TARGET "
                            f"source={escape_source_path(record.relative_path)} "
                            f"line={target.line} ordinal={target.ordinal}"
                        )
        except json.JSONDecodeError as error:
            errors.append(
                "REPO_DOCS_INVALID_JSON "
                f"source={escape_source_path(record.relative_path)} "
                f"line={error.lineno} column={error.colno}"
            )
        except (KeyError, UnicodeError) as error:
            raise RepositoryCheckError(
                "REPO_DOCS_TRACKED_BLOB_DECODE_FAILED "
                f"source={escape_source_path(record.relative_path)}"
            ) from error

    return errors


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate tracked active Markdown links and JSON files.")
    parser.add_argument(
        "--repository-root",
        "--repository",
        dest="repository",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root to inspect",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        errors = check_repository(arguments.repository)
    except RepositoryCheckError as error:
        print(f"repository documentation check failed: {error}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("repository documentation check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
