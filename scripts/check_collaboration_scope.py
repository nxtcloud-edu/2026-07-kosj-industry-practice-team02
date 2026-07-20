from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass

if __package__:
    from . import check_collaboration_note_append as note_append
else:
    import check_collaboration_note_append as note_append


FRONTEND_SELF_MERGE_ELIGIBLE = "FRONTEND_SELF_MERGE_ELIGIBLE"
OWNER_REVIEW_REQUIRED = "OWNER_REVIEW_REQUIRED"
OPERATIONAL_ERROR = "OPERATIONAL_ERROR"

FULL_SHA_PATTERN = re.compile(r"\A(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\Z")
RENAME_STATUS_PATTERN = re.compile(r"\AR(\d{1,3})\Z")
ALLOWED_PREFIXES = ("apps/web/src/", "tools/web-e2e/e2e/")
GLOBAL_DENY_PREFIXES = (
    ".github/",
    "apps/api/",
    "contracts/",
    "database/",
    "supabase/",
    "data/official/",
    "data/staging/",
    "docs/adr/",
    "docs/source-of-truth/",
    "packages/shared-contracts/src/generated/",
)
PROTECTED_SEGMENTS = {
    ".git",
    "adr",
    "contract",
    "contracts",
    "database",
    "db",
    "generated",
    "migration",
    "migrations",
    "official",
    "policies",
    "policy",
    "staging",
}
LOCKFILE_NAMES = {
    "bun.lock",
    "bun.lockb",
    "cargo.lock",
    "composer.lock",
    "npm-shrinkwrap.json",
    "package-lock.json",
    "pipfile.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "yarn.lock",
}
PACKAGE_METADATA_NAMES = {
    "package.json",
    "package.yaml",
    "package.yml",
}


class OperationalError(RuntimeError):
    """Input or Git state does not permit a trustworthy classification."""


@dataclass(frozen=True)
class Change:
    status: str
    paths: tuple[str, ...]


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        raise OperationalError


def is_full_commit_sha(value: str | None) -> bool:
    return isinstance(value, str) and FULL_SHA_PATTERN.fullmatch(value) is not None


def _valid_login(value: str | None) -> bool:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 256:
        return False
    return not any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value)


def _execute_git(
    arguments: list[str],
    *,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    execute = runner or subprocess.run
    try:
        result = execute(
            arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise OperationalError from error
    if not isinstance(result.stdout, bytes) or not isinstance(result.stderr, bytes):
        raise OperationalError
    return result


def require_commit(
    sha: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] | None = None,
) -> None:
    if not is_full_commit_sha(sha):
        raise OperationalError
    result = _execute_git(["git", "cat-file", "-t", sha], runner=runner)
    if result.returncode != 0 or result.stdout.strip() != b"commit":
        raise OperationalError


def _decode_path(raw_path: bytes) -> str:
    if not raw_path:
        raise OperationalError
    return raw_path.decode("utf-8", errors="surrogateescape")


def parse_name_status(raw_diff: bytes) -> list[Change]:
    if not isinstance(raw_diff, bytes):
        raise OperationalError
    if not raw_diff:
        return []
    if not raw_diff.endswith(b"\0"):
        raise OperationalError
    tokens = raw_diff[:-1].split(b"\0")
    changes: list[Change] = []
    index = 0
    while index < len(tokens):
        raw_status = tokens[index]
        index += 1
        if not raw_status:
            raise OperationalError
        try:
            status = raw_status.decode("ascii", errors="strict")
        except UnicodeDecodeError as error:
            raise OperationalError from error
        path_count = 2 if status[:1] in {"R", "C"} else 1
        if index + path_count > len(tokens):
            raise OperationalError
        paths = tuple(_decode_path(token) for token in tokens[index : index + path_count])
        index += path_count
        changes.append(Change(status=status, paths=paths))
    return changes


def read_name_status(
    base_sha: str,
    head_sha: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] | None = None,
) -> list[Change]:
    command = ["git", "diff", "--name-status", "-z", base_sha, head_sha, "--"]
    result = _execute_git(command, runner=runner)
    if result.returncode != 0:
        raise OperationalError
    return parse_name_status(result.stdout)


def normalize_repository_path(path: str) -> str | None:
    if not path or "\0" in path or "\\" in path or path.startswith("/"):
        return None
    if re.match(r"\A[A-Za-z]:", path):
        return None
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return "/".join(parts)


def _is_protected_path(path: str) -> bool:
    lowered = path.casefold()
    if any(lowered.startswith(prefix) for prefix in GLOBAL_DENY_PREFIXES):
        return True
    parts = lowered.split("/")
    basename = parts[-1]
    if any(part in PROTECTED_SEGMENTS for part in parts):
        return True
    if basename == "agents.md" or basename == "readme" or basename.startswith("readme."):
        return True
    if basename in {".env", ".envrc"} or basename.startswith(".env."):
        return True
    if basename in LOCKFILE_NAMES or basename.endswith(".lock"):
        return True
    if basename in PACKAGE_METADATA_NAMES:
        return True
    if basename.endswith(".example") or ".example." in basename:
        return True
    if (
        basename.startswith("generated-")
        or basename.startswith("generated.")
        or ".generated." in basename
    ):
        return True
    if basename.startswith("contract.") or ".contract." in basename:
        return True
    if basename.startswith("policy.") or ".policy." in basename:
        return True
    return False


def _is_allowed_regular_path(path: str) -> bool:
    normalized = normalize_repository_path(path)
    if normalized is None or _is_protected_path(normalized):
        return False
    return any(normalized.startswith(prefix) and len(normalized) > len(prefix) for prefix in ALLOWED_PREFIXES)


def _note_path_for_append(changes: Sequence[Change]) -> str | None:
    notes: list[str] = []
    indexes = 0
    for change in changes:
        if change.status == "A" and len(change.paths) == 1:
            path = normalize_repository_path(change.paths[0])
            if path is not None and note_append.web_note_identity(path) is not None:
                notes.append(path)
        if change.status == "M" and change.paths == (note_append.INDEX_PATH,):
            indexes += 1
    if len(notes) == 1 and indexes == 1:
        return notes[0]
    return None


def classify_changes(
    changes: Sequence[Change],
    *,
    pr_author: str,
    frontend_login: str,
    note_append_valid: bool,
) -> str:
    if not changes or pr_author.casefold() != frontend_login.casefold():
        return OWNER_REVIEW_REQUIRED

    note_count = 0
    index_count = 0
    for change in changes:
        if change.status in {"A", "M"} and len(change.paths) == 1:
            path = normalize_repository_path(change.paths[0])
            if path is None:
                return OWNER_REVIEW_REQUIRED
            if path == note_append.INDEX_PATH:
                if change.status != "M":
                    return OWNER_REVIEW_REQUIRED
                index_count += 1
                continue
            if path.startswith("docs/implementation-notes/"):
                if change.status != "A" or note_append.web_note_identity(path) is None:
                    return OWNER_REVIEW_REQUIRED
                note_count += 1
                continue
            if not _is_allowed_regular_path(path):
                return OWNER_REVIEW_REQUIRED
            continue

        rename_match = RENAME_STATUS_PATTERN.fullmatch(change.status)
        if (
            rename_match is None
            or int(rename_match.group(1)) > 100
            or len(change.paths) != 2
            or not all(_is_allowed_regular_path(path) for path in change.paths)
        ):
            return OWNER_REVIEW_REQUIRED

    if note_count or index_count:
        if note_count != 1 or index_count != 1 or not note_append_valid:
            return OWNER_REVIEW_REQUIRED
    return FRONTEND_SELF_MERGE_ELIGIBLE


def render_result(classification: str, change_count: int, paths: Sequence[str]) -> str:
    sorted_paths = sorted(paths)
    payload = {
        "classification": classification,
        "counts": {"changes": change_count, "paths": len(sorted_paths)},
        "paths": sorted_paths,
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _parse_arguments(arguments: Sequence[str] | None) -> argparse.Namespace:
    parser = SafeArgumentParser(add_help=False)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    parser.add_argument("--pr-author")
    parser.add_argument("--frontend-login")
    return parser.parse_args(arguments)


def _classify(arguments: Sequence[str] | None) -> tuple[str, int, list[str]]:
    parsed = _parse_arguments(arguments)
    if not is_full_commit_sha(parsed.base_sha) or not is_full_commit_sha(parsed.head_sha):
        raise OperationalError
    if not _valid_login(parsed.pr_author) or not _valid_login(parsed.frontend_login):
        raise OperationalError

    require_commit(parsed.base_sha)
    require_commit(parsed.head_sha)
    changes = read_name_status(parsed.base_sha, parsed.head_sha)
    paths = [path for change in changes for path in change.paths]
    note_path = _note_path_for_append(changes)
    append_valid = False
    if note_path is not None:
        try:
            append_valid = note_append.validate_note_and_index_append(
                parsed.base_sha,
                parsed.head_sha,
                note_path,
            )
        except note_append.AppendValidationOperationalError as error:
            raise OperationalError from error
    classification = classify_changes(
        changes,
        pr_author=parsed.pr_author,
        frontend_login=parsed.frontend_login,
        note_append_valid=append_valid,
    )
    return classification, len(changes), paths


def main(arguments: Sequence[str] | None = None) -> int:
    try:
        classification, change_count, paths = _classify(arguments)
    except Exception:
        print(render_result(OPERATIONAL_ERROR, 0, []))
        return 2
    print(render_result(classification, change_count, paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
