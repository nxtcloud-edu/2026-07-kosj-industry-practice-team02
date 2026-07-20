from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path

OBJECT_ID = re.compile(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})")
SECRET_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
MAX_LOCAL_SECRET_FILE_BYTES = 1024 * 1024

PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    (
        "GITHUB_TOKEN",
        re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    ),
    (
        "PROVIDER_BEARER_KEY",
        re.compile(rb"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_-])"),
    ),
    (
        "PRIVATE_KEY_HEADER",
        re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    ),
    (
        "CREDENTIAL_DATABASE_URL",
        re.compile(
            rb"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|redis|rediss|mongodb(?:\+srv)?)"
            rb"://(?P<username>[^/\s:@]+):(?P<password>[^/\s@]+)@"
            rb"(?P<host>\[[^]]+\]|[^/\s:]+)"
        ),
    ),
    (
        "JWT_LIKE_TOKEN",
        re.compile(
            rb"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{7,}"
            rb"\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(?![A-Za-z0-9_-])"
        ),
    ),
    (
        "ACTUAL_QUESTION_SENTINEL",
        re.compile(rb"(?i)\b(?:SEJONG_)?(?:ACTUAL|CITIZEN|RAW)_QUESTION_SENTINEL\s*[:=]"),
    ),
)


class ScannerOperationalError(Exception):
    """A deliberately detail-free operational failure."""


def _secret_in_bytes(value: bytes, exact_secrets: Sequence[bytes]) -> bool:
    return any(secret and secret in value for secret in exact_secrets)


def _safe_environment(exact_secrets: Sequence[bytes]) -> dict[str, str]:
    environment: dict[str, str] = {}
    for name, value in os.environ.items():
        if name.upper().startswith("GIT_"):
            continue
        encoded = f"{name}={value}".encode("utf-8", errors="replace")
        if _secret_in_bytes(encoded, exact_secrets):
            continue
        environment[name] = value
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        }
    )
    return environment


def _run_git(
    repository: Path,
    arguments: Sequence[str],
    *,
    environment: dict[str, str],
    input_bytes: bytes = b"",
    accepted_returncodes: Iterable[int] = (0,),
) -> bytes:
    command = ["git", "-c", "core.quotepath=false", *arguments]
    try:
        result = subprocess.run(
            command,
            cwd=str(repository),
            input=input_bytes,
            capture_output=True,
            env=environment,
            shell=False,
            check=False,
        )
    except (OSError, ValueError):
        raise ScannerOperationalError from None
    if result.returncode not in set(accepted_returncodes):
        raise ScannerOperationalError
    if not isinstance(result.stdout, bytes) or not isinstance(result.stderr, bytes):
        raise ScannerOperationalError
    return result.stdout


def _resolve_repository(value: str) -> Path:
    try:
        repository = Path(value).resolve(strict=True)
    except (OSError, RuntimeError):
        raise ScannerOperationalError from None
    if not repository.is_dir():
        raise ScannerOperationalError
    return repository


def _extract_named_secret(content: bytes, name: str) -> bytes:
    encoded_name = name.encode("ascii")
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith(b"export "):
            line = line[7:].lstrip()
        assignment_name, separator, value = line.partition(b"=")
        if not separator or assignment_name.strip() != encoded_name:
            continue
        secret = value.strip()
        if len(secret) >= 2 and secret[:1] in (b"'", b'"') and secret[-1:] == secret[:1]:
            secret = secret[1:-1]
        if not secret:
            raise ScannerOperationalError
        return secret
    raise ScannerOperationalError


def _load_local_secret(repository: Path, file_value: str, name: str) -> tuple[str, bytes]:
    if SECRET_NAME.fullmatch(name) is None:
        raise ScannerOperationalError
    candidate = Path(file_value)
    if not candidate.is_absolute():
        candidate = repository / candidate
    try:
        path = candidate.resolve(strict=True)
        relative_path = path.relative_to(repository)
        if not path.is_file() or path.stat().st_size > MAX_LOCAL_SECRET_FILE_BYTES:
            raise ScannerOperationalError
        content = path.read_bytes()
    except (OSError, RuntimeError, ValueError):
        raise ScannerOperationalError from None
    secret = _extract_named_secret(content, name)
    relative = relative_path.as_posix()
    if _secret_in_bytes(os.fsencode(relative), (secret,)):
        raise ScannerOperationalError
    return relative, secret


def _verify_ignored(
    repository: Path,
    relative_path: str,
    *,
    environment: dict[str, str],
) -> None:
    _run_git(
        repository,
        ["check-ignore", "-q", "--", relative_path],
        environment=environment,
    )


def _parse_object_ids(output: bytes) -> list[bytes]:
    object_ids: list[bytes] = []
    seen: set[bytes] = set()
    for line in output.splitlines():
        if not line:
            continue
        object_id = line.split(b" ", 1)[0]
        if OBJECT_ID.fullmatch(object_id) is None:
            raise ScannerOperationalError
        if object_id not in seen:
            seen.add(object_id)
            object_ids.append(object_id)
    return object_ids


def _object_types(
    repository: Path,
    object_ids: Sequence[bytes],
    *,
    environment: dict[str, str],
) -> dict[bytes, bytes]:
    if not object_ids:
        return {}
    output = _run_git(
        repository,
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"],
        environment=environment,
        input_bytes=b"\n".join(object_ids) + b"\n",
    )
    result: dict[bytes, bytes] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 2 or OBJECT_ID.fullmatch(parts[0]) is None:
            raise ScannerOperationalError
        result[parts[0]] = parts[1]
    if set(result) != set(object_ids):
        raise ScannerOperationalError
    return result


def _batch_contents(
    repository: Path,
    object_ids: Sequence[bytes],
    object_types: dict[bytes, bytes],
    *,
    environment: dict[str, str],
) -> list[tuple[bytes, bytes]]:
    if not object_ids:
        return []
    output = _run_git(
        repository,
        ["cat-file", "--batch"],
        environment=environment,
        input_bytes=b"\n".join(object_ids) + b"\n",
    )
    offset = 0
    contents: list[tuple[bytes, bytes]] = []
    for expected_id in object_ids:
        header_end = output.find(b"\n", offset)
        if header_end < 0:
            raise ScannerOperationalError
        header = output[offset:header_end].split()
        if len(header) != 3 or header[0] != expected_id:
            raise ScannerOperationalError
        if header[1] != object_types.get(expected_id):
            raise ScannerOperationalError
        try:
            size = int(header[2])
        except ValueError:
            raise ScannerOperationalError from None
        if size < 0:
            raise ScannerOperationalError
        content_start = header_end + 1
        content_end = content_start + size
        if content_end >= len(output) or output[content_end : content_end + 1] != b"\n":
            raise ScannerOperationalError
        contents.append((expected_id, output[content_start:content_end]))
        offset = content_end + 1
    if offset != len(output):
        raise ScannerOperationalError
    return contents


def _categories(content: bytes, exact_secrets: Sequence[bytes]) -> set[str]:
    categories: set[str] = set()
    for category, pattern in PATTERNS:
        matches = pattern.finditer(content)
        if category == "CREDENTIAL_DATABASE_URL":
            if any(not _is_local_placeholder_database_url(match) for match in matches):
                categories.add(category)
        elif next(matches, None) is not None:
            categories.add(category)
    if _secret_in_bytes(content, exact_secrets):
        categories.add("LOCAL_SECRET_EXACT")
    return categories


def _is_local_placeholder_database_url(match: re.Match[bytes]) -> bool:
    placeholder_users = {
        b"demo",
        b"example",
        b"postgres",
        b"synthetic",
        b"test",
        b"user",
        b"username",
    }
    placeholder_passwords = {
        b"changeme",
        b"demo",
        b"example",
        b"pass",
        b"password",
        b"postgres",
        b"synthetic",
        b"test",
    }
    username = match.group("username").lower()
    password = match.group("password").lower()
    host = match.group("host").lower().strip(b"[]")
    reserved_host = host in {
        b"127.0.0.1",
        b"::1",
        b"example.com",
        b"example.net",
        b"example.org",
        b"localhost",
    } or host.endswith(b".invalid")
    return username in placeholder_users and password in placeholder_passwords and reserved_host


def _decode_path(path: bytes, exact_secrets: Sequence[bytes]) -> str:
    if _categories(path, exact_secrets):
        return "<redacted-path>"
    return path.decode("utf-8", errors="surrogateescape")


def _blob_contexts(
    repository: Path,
    blob_ids: set[bytes],
    *,
    environment: dict[str, str],
    exact_secrets: Sequence[bytes],
) -> dict[bytes, set[tuple[str, str]]]:
    contexts: dict[bytes, set[tuple[str, str]]] = defaultdict(set)
    if not blob_ids:
        return contexts
    commit_output = _run_git(
        repository,
        ["rev-list", "--all"],
        environment=environment,
    )
    commits = _parse_object_ids(commit_output)
    for commit_id in commits:
        tree = _run_git(
            repository,
            ["ls-tree", "-r", "-z", "--full-tree", commit_id.decode("ascii")],
            environment=environment,
        )
        for entry in tree.split(b"\0"):
            if not entry:
                continue
            metadata, separator, path = entry.partition(b"\t")
            fields = metadata.split()
            if not separator or len(fields) != 3 or fields[1] != b"blob":
                raise ScannerOperationalError
            blob_id = fields[2]
            if blob_id in blob_ids:
                contexts[blob_id].add(
                    (commit_id.decode("ascii"), _decode_path(path, exact_secrets))
                )
    return contexts


def scan_repository(
    repository: Path,
    *,
    environment: dict[str, str],
    exact_secrets: Sequence[bytes] = (),
) -> list[dict[str, str]]:
    object_output = _run_git(
        repository,
        ["rev-list", "--objects", "--all"],
        environment=environment,
    )
    object_ids = _parse_object_ids(object_output)
    object_types = _object_types(repository, object_ids, environment=environment)
    scannable_ids = [
        object_id for object_id in object_ids if object_types[object_id] in (b"blob", b"commit")
    ]
    findings_by_object: dict[bytes, set[str]] = {}
    for object_id, content in _batch_contents(
        repository,
        scannable_ids,
        object_types,
        environment=environment,
    ):
        categories = _categories(content, exact_secrets)
        if categories:
            findings_by_object[object_id] = categories

    finding_blobs = {
        object_id for object_id in findings_by_object if object_types[object_id] == b"blob"
    }
    contexts = _blob_contexts(
        repository,
        finding_blobs,
        environment=environment,
        exact_secrets=exact_secrets,
    )
    findings: list[dict[str, str]] = []
    for object_id, categories in findings_by_object.items():
        object_text = object_id.decode("ascii")
        if object_types[object_id] == b"commit":
            object_contexts = {(object_text, "<commit-object>")}
        else:
            object_contexts = contexts.get(object_id, {("<unresolved>", "<unresolved>")})
        for commit, path in object_contexts:
            for category in categories:
                findings.append(
                    {
                        "blob": object_text,
                        "category": category,
                        "commit": commit,
                        "path": path,
                    }
                )
    return sorted(
        findings,
        key=lambda item: (
            item["category"],
            item["commit"],
            item["blob"],
            item["path"],
        ),
    )


def _write_record(record: dict[str, str]) -> None:
    sys.stdout.write(
        json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    )


def _write_operational_error() -> None:
    _write_record(
        {
            "blob": "<unavailable>",
            "category": "SCANNER_OPERATIONAL_ERROR",
            "commit": "<unavailable>",
            "path": "<unavailable>",
        }
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan every reachable Git commit and blob without reporting matched values."
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument("--local-secret-file")
    parser.add_argument("--local-secret-name")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        repository = _resolve_repository(arguments.repo)
        if bool(arguments.local_secret_file) != bool(arguments.local_secret_name):
            raise ScannerOperationalError
        exact_secrets: tuple[bytes, ...] = ()
        relative_secret_path: str | None = None
        if arguments.local_secret_file:
            relative_secret_path, exact_secret = _load_local_secret(
                repository,
                arguments.local_secret_file,
                arguments.local_secret_name,
            )
            exact_secrets = (exact_secret,)
        environment = _safe_environment(exact_secrets)
        if relative_secret_path is not None:
            _verify_ignored(
                repository,
                relative_secret_path,
                environment=environment,
            )
        findings = scan_repository(
            repository,
            environment=environment,
            exact_secrets=exact_secrets,
        )
    except ScannerOperationalError:
        _write_operational_error()
        return 2
    except Exception:
        _write_operational_error()
        return 2

    for finding in findings:
        _write_record(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
