from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass


INDEX_PATH = "docs/implementation-notes/INDEX.md"
UNIFIED_CONTEXT_LINES = 1_000_000
NOTE_PATH_PATTERN = re.compile(
    r"\Adocs/implementation-notes/"
    r"(IMP-(\d{8})-(\d{3})-web-[a-z0-9]+(?:-[a-z0-9]+)*\.md)\Z"
)
HUNK_HEADER_PATTERN = re.compile(
    rb"\A@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?\Z"
)
INDEX_ROW_PATTERN = re.compile(
    r"\A\| \[IMP-(\d{8})-(\d{3})\]\(([^)]+)\) \|.*\|\Z"
)


class AppendValidationOperationalError(RuntimeError):
    """The validator could not obtain a trustworthy Git diff."""


@dataclass(frozen=True)
class ParsedHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    prefixes: tuple[bytes, ...]
    added_lines: tuple[bytes, ...]
    context_lines: tuple[bytes, ...]
    context_count: int
    deletion_count: int


def web_note_identity(note_path: str) -> tuple[str, str, str] | None:
    match = NOTE_PATH_PATTERN.fullmatch(note_path)
    if match is None:
        return None
    return match.group(1), match.group(2), match.group(3)


def _split_patch_sections(unified_diff: bytes) -> dict[str, list[bytes]] | None:
    if not unified_diff:
        return None
    lines = unified_diff.split(b"\n")
    if lines[-1] == b"":
        lines.pop()

    sections: dict[str, list[bytes]] = {}
    current_path: str | None = None
    expected_headers = {
        f"diff --git a/{path} b/{path}".encode("ascii"): path
        for path in (INDEX_PATH,)
    }

    for line in lines:
        if line.startswith(b"diff --git "):
            path = expected_headers.get(line)
            if path is None:
                try:
                    decoded = line.decode("ascii")
                except UnicodeDecodeError:
                    return None
                prefix = "diff --git a/"
                separator = " b/"
                if not decoded.startswith(prefix) or separator not in decoded:
                    return None
                old_path, new_path = decoded[len(prefix) :].split(separator, 1)
                if old_path != new_path or web_note_identity(old_path) is None:
                    return None
                path = old_path
            if path in sections:
                return None
            current_path = path
            sections[path] = []
            continue
        if current_path is None:
            return None
        sections[current_path].append(line)

    return sections


def _parse_single_hunk(lines: list[bytes]) -> tuple[list[bytes], ParsedHunk] | None:
    hunk_indexes = [index for index, line in enumerate(lines) if line.startswith(b"@@ ")]
    if len(hunk_indexes) != 1:
        return None
    hunk_index = hunk_indexes[0]
    header_match = HUNK_HEADER_PATTERN.fullmatch(lines[hunk_index])
    if header_match is None:
        return None

    old_start = int(header_match.group(1))
    old_count = int(header_match.group(2) or b"1")
    new_start = int(header_match.group(3))
    new_count = int(header_match.group(4) or b"1")
    prefixes: list[bytes] = []
    added_lines: list[bytes] = []
    context_lines: list[bytes] = []
    context_count = 0
    deletion_count = 0
    previous_was_content = False

    for line in lines[hunk_index + 1 :]:
        if line.startswith(b"@@ "):
            return None
        if line == rb"\ No newline at end of file":
            if not previous_was_content:
                return None
            previous_was_content = False
            continue
        if not line or line[:1] not in (b" ", b"+", b"-"):
            return None
        prefix = line[:1]
        content = line[1:]
        if content.endswith(b"\r"):
            content = content[:-1]
        prefixes.append(prefix)
        previous_was_content = True
        if prefix == b" ":
            context_count += 1
            context_lines.append(content)
        elif prefix == b"+":
            added_lines.append(content)
        else:
            deletion_count += 1

    parsed = ParsedHunk(
        old_start=old_start,
        old_count=old_count,
        new_start=new_start,
        new_count=new_count,
        prefixes=tuple(prefixes),
        added_lines=tuple(added_lines),
        context_lines=tuple(context_lines),
        context_count=context_count,
        deletion_count=deletion_count,
    )
    return lines[:hunk_index], parsed


def _valid_new_note_patch(note_path: str, lines: list[bytes]) -> bool:
    parsed_patch = _parse_single_hunk(lines)
    if parsed_patch is None:
        return False
    metadata, hunk = parsed_patch
    allowed_metadata = {
        b"new file mode 100644",
        b"--- /dev/null",
        f"+++ b/{note_path}".encode("ascii"),
    }
    if not allowed_metadata.issubset(metadata):
        return False
    if any(
        line not in allowed_metadata and not line.startswith(b"index 0000000")
        for line in metadata
    ):
        return False
    if not any(line.startswith(b"index 0000000") for line in metadata):
        return False
    return (
        hunk.old_start == 0
        and hunk.old_count == 0
        and hunk.new_start == 1
        and hunk.new_count == len(hunk.added_lines)
        and hunk.new_count > 0
        and hunk.context_count == 0
        and hunk.deletion_count == 0
        and all(prefix == b"+" for prefix in hunk.prefixes)
    )


def _valid_index_append_patch(note_path: str, lines: list[bytes]) -> bool:
    identity = web_note_identity(note_path)
    if identity is None:
        return False
    note_name, note_date, note_number = identity
    parsed_patch = _parse_single_hunk(lines)
    if parsed_patch is None:
        return False
    metadata, hunk = parsed_patch
    required_metadata = {
        f"--- a/{INDEX_PATH}".encode("ascii"),
        f"+++ b/{INDEX_PATH}".encode("ascii"),
    }
    if not required_metadata.issubset(metadata):
        return False
    if any(
        line not in required_metadata and not line.startswith(b"index ")
        for line in metadata
    ):
        return False
    if not any(line.startswith(b"index ") for line in metadata):
        return False
    if (
        hunk.old_start != 1
        or hunk.old_count != hunk.context_count
        or hunk.deletion_count != 0
        or hunk.new_start != 1
        or hunk.new_count != hunk.context_count + 1
        or len(hunk.added_lines) != 1
        or hunk.prefixes != (b" ",) * hunk.context_count + (b"+",)
    ):
        return False

    try:
        added_row = hunk.added_lines[0].decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    row_match = INDEX_ROW_PATTERN.fullmatch(added_row)
    if row_match is None:
        return False
    row_date, row_number, linked_note = row_match.groups()
    for raw_context_line in hunk.context_lines:
        try:
            context_line = raw_context_line.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return False
        context_match = INDEX_ROW_PATTERN.fullmatch(context_line)
        if (
            context_match is not None
            and context_match.group(1) == note_date
            and context_match.group(2) == note_number
        ):
            return False
    return (
        row_date == note_date
        and row_number == note_number
        and linked_note == note_name
    )


def validate_unified_diff(unified_diff: bytes, note_path: str) -> bool:
    if web_note_identity(note_path) is None:
        return False
    sections = _split_patch_sections(unified_diff)
    if sections is None or set(sections) != {note_path, INDEX_PATH}:
        return False
    return _valid_new_note_patch(note_path, sections[note_path]) and _valid_index_append_patch(
        note_path,
        sections[INDEX_PATH],
    )


def validate_note_and_index_append(
    base_sha: str,
    head_sha: str,
    note_path: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] | None = None,
) -> bool:
    command = [
        "git",
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--no-color",
        f"--unified={UNIFIED_CONTEXT_LINES}",
        base_sha,
        head_sha,
        "--",
        note_path,
        INDEX_PATH,
    ]
    execute = runner or subprocess.run
    try:
        result = execute(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise AppendValidationOperationalError from error
    if result.returncode != 0 or not isinstance(result.stdout, bytes):
        raise AppendValidationOperationalError
    return validate_unified_diff(result.stdout, note_path)
