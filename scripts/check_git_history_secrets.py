from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import threading
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

OBJECT_ID = re.compile(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})")
SECRET_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
MAX_LOCAL_SECRET_FILE_BYTES = 1024 * 1024
MAX_REACHABLE_OBJECTS = 100_000
MAX_OBJECT_BYTES = 16 * 1024 * 1024
MAX_AGGREGATE_OBJECT_BYTES = 256 * 1024 * 1024
MAX_GIT_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_BATCH_HEADER_BYTES = 256
MAX_UNIQUE_TREES = 20_000
MAX_TREE_ENTRIES = 1_000_000
MAX_PATH_BYTES = 4096
MAX_AGGREGATE_PATH_BYTES = 128 * 1024 * 1024
GIT_TIMEOUT_SECONDS = 60
GIT_STREAM_CHUNK_BYTES = 64 * 1024
GIT_THREAD_JOIN_SECONDS = 5
VALID_OBJECT_TYPES = frozenset({b"blob", b"commit", b"tag", b"tree"})
LOCAL_PLACEHOLDER_DATABASE_URL = "_LOCAL_PLACEHOLDER_DATABASE_URL"
SAFE_PLACEHOLDER_DATABASE_PATHS = frozenset(
    {".env.example", "apps/api/.env.example", "apps/web/.env.example"}
)

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
        encoded_name = name.encode("utf-8", errors="replace")
        encoded_value = value.encode("utf-8", errors="replace")
        if _secret_in_bytes(encoded_name, exact_secrets) or _secret_in_bytes(
            encoded_value, exact_secrets
        ):
            continue
        environment[name] = value
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        }
    )
    for name, value in environment.items():
        encoded_name = name.encode("utf-8", errors="replace")
        encoded_value = value.encode("utf-8", errors="replace")
        if _secret_in_bytes(encoded_name, exact_secrets) or _secret_in_bytes(
            encoded_value, exact_secrets
        ):
            raise ScannerOperationalError
    return environment


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    try:
        if process.poll() is None:
            process.terminate()
    except OSError:
        pass


def _write_process_input(
    process: subprocess.Popen[bytes],
    stream: object,
    content: bytes,
    failed: threading.Event,
) -> None:
    try:
        offset = 0
        while offset < len(content):
            written = stream.write(content[offset : offset + GIT_STREAM_CHUNK_BYTES])
            if not isinstance(written, int) or written <= 0:
                raise ScannerOperationalError
            offset += written
        stream.flush()
    except BaseException:
        failed.set()
        _terminate_process(process)
    finally:
        with contextlib.suppress(OSError):
            stream.close()


def _read_bounded_stream(
    process: subprocess.Popen[bytes],
    stream: object,
    chunks: list[bytes] | None,
    failed: threading.Event,
) -> None:
    total = 0
    try:
        while True:
            remaining = MAX_GIT_OUTPUT_BYTES - total
            if remaining < 0:
                raise ScannerOperationalError
            chunk = stream.read(min(GIT_STREAM_CHUNK_BYTES, remaining + 1))
            if not isinstance(chunk, bytes):
                raise ScannerOperationalError
            if not chunk:
                return
            if len(chunk) > remaining:
                raise ScannerOperationalError
            if chunks is not None:
                chunks.append(chunk)
            total += len(chunk)
    except BaseException:
        failed.set()
        _terminate_process(process)


def _run_git(
    repository: Path,
    arguments: Sequence[str],
    *,
    environment: dict[str, str],
    input_bytes: bytes = b"",
    accepted_returncodes: Iterable[int] = (0,),
) -> bytes:
    command = ["git", "-c", "core.quotepath=false", *arguments]
    process: subprocess.Popen[bytes] | None = None
    threads: list[threading.Thread] = []
    stdout_chunks: list[bytes] = []
    failed = threading.Event()
    try:
        process = subprocess.Popen(
            command,
            cwd=str(repository),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            shell=False,
            bufsize=0,
        )
        if process.stdin is None or process.stdout is None or process.stderr is None:
            raise ScannerOperationalError
        threads = [
            threading.Thread(
                target=_write_process_input,
                args=(process, process.stdin, input_bytes, failed),
                daemon=True,
            ),
            threading.Thread(
                target=_read_bounded_stream,
                args=(process, process.stdout, stdout_chunks, failed),
                daemon=True,
            ),
            threading.Thread(
                target=_read_bounded_stream,
                args=(process, process.stderr, None, failed),
                daemon=True,
            ),
        ]
        for thread in threads:
            thread.start()
        returncode = process.wait(timeout=GIT_TIMEOUT_SECONDS)
        for thread in threads:
            thread.join(timeout=GIT_THREAD_JOIN_SECONDS)
        if failed.is_set() or any(thread.is_alive() for thread in threads):
            raise ScannerOperationalError
    except ScannerOperationalError:
        raise
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError):
        raise ScannerOperationalError from None
    finally:
        if process is not None:
            _stop_process(process)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    with contextlib.suppress(OSError):
                        stream.close()
            for thread in threads:
                thread.join(timeout=GIT_THREAD_JOIN_SECONDS)
    if returncode not in set(accepted_returncodes):
        raise ScannerOperationalError
    return b"".join(stdout_chunks)


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
            if len(object_ids) > MAX_REACHABLE_OBJECTS:
                raise ScannerOperationalError
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
        if (
            len(parts) != 2
            or OBJECT_ID.fullmatch(parts[0]) is None
            or parts[1] not in VALID_OBJECT_TYPES
            or parts[0] in result
        ):
            raise ScannerOperationalError
        result[parts[0]] = parts[1]
    if len(result) != len(object_ids) or set(result) != set(object_ids):
        raise ScannerOperationalError
    return result


def _read_exact(stream: object, size: int) -> bytes:
    content = bytearray()
    while len(content) < size:
        chunk = stream.read(min(64 * 1024, size - len(content)))
        if not isinstance(chunk, bytes) or not chunk:
            raise ScannerOperationalError
        content.extend(chunk)
    return bytes(content)


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    try:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _batch_contents(
    repository: Path,
    object_ids: Sequence[bytes],
    object_types: dict[bytes, bytes],
    *,
    environment: dict[str, str],
) -> Iterator[tuple[bytes, bytes]]:
    if not object_ids:
        return
    command = ["git", "-c", "core.quotepath=false", "cat-file", "--batch"]
    process: subprocess.Popen[bytes] | None = None
    stderr_thread: threading.Thread | None = None
    failed = threading.Event()
    try:
        process = subprocess.Popen(
            command,
            cwd=str(repository),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            shell=False,
            bufsize=0,
        )
        if process.stdin is None or process.stdout is None or process.stderr is None:
            raise ScannerOperationalError
        stderr_thread = threading.Thread(
            target=_read_bounded_stream,
            args=(process, process.stderr, None, failed),
            daemon=True,
        )
        stderr_thread.start()
        aggregate_size = 0
        for expected_id in object_ids:
            process.stdin.write(expected_id + b"\n")
            process.stdin.flush()
            header_line = process.stdout.readline(MAX_BATCH_HEADER_BYTES + 1)
            if (
                not isinstance(header_line, bytes)
                or not header_line.endswith(b"\n")
                or len(header_line) > MAX_BATCH_HEADER_BYTES
            ):
                raise ScannerOperationalError
            header = header_line[:-1].split()
            if (
                len(header) != 3
                or header[0] != expected_id
                or header[1] != object_types.get(expected_id)
            ):
                raise ScannerOperationalError
            try:
                size = int(header[2])
            except ValueError:
                raise ScannerOperationalError from None
            if size < 0 or size > MAX_OBJECT_BYTES:
                raise ScannerOperationalError
            aggregate_size += size
            if aggregate_size > MAX_AGGREGATE_OBJECT_BYTES:
                raise ScannerOperationalError
            content = _read_exact(process.stdout, size)
            if process.stdout.read(1) != b"\n":
                raise ScannerOperationalError
            yield expected_id, content
        process.stdin.close()
        if process.stdout.read(1) != b"":
            raise ScannerOperationalError
        if process.wait(timeout=GIT_TIMEOUT_SECONDS) != 0:
            raise ScannerOperationalError
        stderr_thread.join(timeout=GIT_THREAD_JOIN_SECONDS)
        if failed.is_set() or stderr_thread.is_alive():
            raise ScannerOperationalError
    except ScannerOperationalError:
        raise
    except (BrokenPipeError, OSError, subprocess.TimeoutExpired, ValueError):
        raise ScannerOperationalError from None
    finally:
        if process is not None:
            _stop_process(process)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    with contextlib.suppress(OSError):
                        stream.close()
            if stderr_thread is not None:
                stderr_thread.join(timeout=GIT_THREAD_JOIN_SECONDS)


def _categories(content: bytes, exact_secrets: Sequence[bytes]) -> set[str]:
    categories: set[str] = set()
    for category, pattern in PATTERNS:
        matches = pattern.finditer(content)
        if category == "CREDENTIAL_DATABASE_URL":
            for match in matches:
                if _is_local_placeholder_database_url(match):
                    categories.add(LOCAL_PLACEHOLDER_DATABASE_URL)
                else:
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


def _commit_tree_id(content: bytes) -> bytes:
    first_line = content.split(b"\n", 1)[0]
    prefix, separator, tree_id = first_line.partition(b" ")
    if prefix != b"tree" or not separator or OBJECT_ID.fullmatch(tree_id) is None:
        raise ScannerOperationalError
    return tree_id


def _history_contexts(
    repository: Path,
    blob_ids: set[bytes],
    tree_contexts: dict[bytes, bytes],
    *,
    environment: dict[str, str],
    exact_secrets: Sequence[bytes],
) -> tuple[dict[bytes, set[tuple[str, str]]], list[dict[str, str]]]:
    contexts: dict[bytes, set[tuple[str, str]]] = defaultdict(set)
    path_findings: list[dict[str, str]] = []
    total_entries = 0
    total_path_bytes = 0
    for tree_id, commit_id in sorted(tree_contexts.items()):
        tree = _run_git(
            repository,
            ["ls-tree", "-r", "-z", "--full-tree", tree_id.decode("ascii")],
            environment=environment,
        )
        for entry in tree.split(b"\0"):
            if not entry:
                continue
            total_entries += 1
            if total_entries > MAX_TREE_ENTRIES:
                raise ScannerOperationalError
            metadata, separator, path = entry.partition(b"\t")
            fields = metadata.split()
            if not separator or len(fields) != 3:
                raise ScannerOperationalError
            if fields[1] == b"commit":
                continue
            if fields[1] != b"blob" or OBJECT_ID.fullmatch(fields[2]) is None:
                raise ScannerOperationalError
            if len(path) > MAX_PATH_BYTES:
                raise ScannerOperationalError
            total_path_bytes += len(path)
            if total_path_bytes > MAX_AGGREGATE_PATH_BYTES:
                raise ScannerOperationalError
            blob_id = fields[2]
            display_path = _decode_path(path, exact_secrets)
            for category in _categories(path, exact_secrets):
                public_category = (
                    "CREDENTIAL_DATABASE_URL"
                    if category == LOCAL_PLACEHOLDER_DATABASE_URL
                    else category
                )
                path_findings.append(
                    {
                        "blob": blob_id.decode("ascii"),
                        "category": public_category,
                        "commit": commit_id.decode("ascii"),
                        "path": display_path,
                    }
                )
            if blob_id in blob_ids:
                contexts[blob_id].add((commit_id.decode("ascii"), display_path))
    return contexts, path_findings


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
    scannable_ids = list(object_ids)
    findings_by_object: dict[bytes, set[str]] = {}
    tree_contexts: dict[bytes, bytes] = {}
    for object_id, content in _batch_contents(
        repository,
        scannable_ids,
        object_types,
        environment=environment,
    ):
        if object_types[object_id] == b"commit":
            tree_id = _commit_tree_id(content)
            tree_contexts.setdefault(tree_id, object_id)
            if len(tree_contexts) > MAX_UNIQUE_TREES:
                raise ScannerOperationalError
        categories = _categories(content, exact_secrets)
        if categories:
            findings_by_object[object_id] = categories

    all_blobs = {object_id for object_id in object_ids if object_types[object_id] == b"blob"}
    contexts, path_findings = _history_contexts(
        repository,
        all_blobs,
        tree_contexts,
        environment=environment,
        exact_secrets=exact_secrets,
    )
    findings: list[dict[str, str]] = list(path_findings)
    for object_id, categories in findings_by_object.items():
        object_text = object_id.decode("ascii")
        object_type = object_types[object_id]
        if object_type == b"blob":
            object_contexts = contexts.get(object_id, {("<unresolved>", "<unresolved>")})
        elif object_type == b"commit":
            object_contexts = {(object_text, "<commit-object>")}
        else:
            object_contexts = {("<unresolved>", f"<{object_type.decode('ascii')}-object>")}
        for commit, path in object_contexts:
            for category in categories:
                if category == LOCAL_PLACEHOLDER_DATABASE_URL:
                    if object_type == b"blob" and path in SAFE_PLACEHOLDER_DATABASE_PATHS:
                        continue
                    category = "CREDENTIAL_DATABASE_URL"
                findings.append(
                    {
                        "blob": object_text,
                        "category": category,
                        "commit": commit,
                        "path": path,
                    }
                )
    unique_findings = {
        (item["category"], item["commit"], item["blob"], item["path"]): item for item in findings
    }
    return sorted(
        unique_findings.values(),
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
