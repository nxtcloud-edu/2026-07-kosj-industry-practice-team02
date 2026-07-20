from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
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
FENCE_PATTERN = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})")
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


def is_active(relative_path: Path) -> bool:
    return not any(part.lower() in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts)


def git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name in GIT_ENVIRONMENT_NAMES or name.startswith(GIT_ENVIRONMENT_PREFIXES):
            environment.pop(name)
    return environment


def tracked_active_files(repository: Path) -> list[Path]:
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
            ["git", "-C", os.fspath(repository), "ls-files", "-z"],
            check=True,
            capture_output=True,
            env=git_environment(),
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise RepositoryCheckError("unable to list tracked files") from error

    files = []
    for raw_path in completed.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative_path = Path(os.fsdecode(raw_path))
        if is_active(relative_path):
            files.append(relative_path)
    return files


def repository_local_target(destination: str) -> str | None:
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc:
        return None
    return unquote(parsed.path)


def markdown_targets(contents: str) -> list[str]:
    targets = []
    active_fence: str | None = None
    for line in contents.splitlines():
        fence = FENCE_PATTERN.match(line)
        if fence:
            marker = fence.group("fence")
            if active_fence is None:
                active_fence = marker[0]
            elif active_fence == marker[0]:
                active_fence = None
            continue
        if active_fence is not None:
            continue
        for match in MARKDOWN_TARGET_PATTERN.finditer(line):
            destination = match.group("target").strip()
            if destination.startswith("<") and ">" in destination:
                destination = destination[1 : destination.index(">")]
            else:
                title = re.search(r"\s+(?=[\"'][^\"']*[\"']\s*$)", destination)
                if title:
                    destination = destination[: title.start()]
            target = repository_local_target(destination)
            if target is not None:
                targets.append(target)
    return targets


def resolve_target(repository: Path, source: Path, target: str) -> Path:
    if not target:
        return source.resolve()
    if target.startswith("/"):
        candidate = repository / target.lstrip("/")
    else:
        candidate = source.parent / target
        target_path = Path(target)
        if (
            not candidate.exists()
            and target_path.parts
            and target_path.parts[0] not in {".", ".."}
            and (repository / target_path.parts[0]).is_dir()
        ):
            candidate = repository / target_path
    return candidate.resolve()


def check_repository(repository: Path) -> list[str]:
    repository = repository.resolve()
    errors: list[str] = []

    for relative_path in tracked_active_files(repository):
        path = repository / relative_path
        try:
            if relative_path.suffix.lower() == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            if relative_path.suffix.lower() in MARKDOWN_SUFFIXES:
                contents = path.read_text(encoding="utf-8")
                for target in markdown_targets(contents):
                    resolved = resolve_target(repository, path, target)
                    if resolved.is_relative_to(repository) and not is_active(
                        resolved.relative_to(repository)
                    ):
                        continue
                    if not resolved.is_relative_to(repository) or not resolved.exists():
                        displayed_target = (
                            resolved.relative_to(repository).as_posix()
                            if resolved.is_relative_to(repository)
                            else target
                        )
                        errors.append(
                            "missing Markdown target: "
                            f"{relative_path.as_posix()} -> {displayed_target}"
                        )
        except json.JSONDecodeError as error:
            errors.append(
                f"invalid JSON: {relative_path.as_posix()} at line {error.lineno}, column {error.colno}"
            )
        except (OSError, UnicodeError) as error:
            raise RepositoryCheckError(
                f"unable to inspect tracked file: {relative_path.as_posix()}"
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
