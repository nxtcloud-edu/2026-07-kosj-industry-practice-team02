"""Guarded publication CLI for the initial DATA-SEED official release."""

from __future__ import annotations

import ctypes
import errno
import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Mapping, Sequence

from scripts.data_seed_release import (
    CANONICAL_DRAFT_RELATIVE_PATH,
    CANONICAL_DRAFT_TOKEN,
    CANONICAL_RELEASE_RELATIVE_PATH,
    CANONICAL_RELEASE_TOKEN,
    GOVERNANCE_RELEASED_AT,
    RELEASE_ARTIFACTS,
    RELEASE_VERSION,
    ReleaseBundle,
    ReleaseVerificationError,
    _verify_release_contents,
    build_release_bundle,
    release_bundle_files,
    verify_release_directory,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PREPARE_STEP = "PREPARE-DATA-SEED"
VERIFY_RELEASE_STEP = "VERIFY-DATA-SEED-RELEASE"
ACTIVATE_STEP = "ACTIVATE-LOCAL-SEED"
VERIFY_LOCAL_STEP = "VERIFY-LOCAL-SEED"
CLI_STEP = "DATA-SEED-CLI"
INITIAL_DISPATCHER_BYTES = (
    b"-- DB-001 deliberately contains no official or mock seed.\n"
    b"-- DATA-001 and DATA-SEED-001 own PM-approved data and versioned lineage.\n"
    b"-- An empty approved-data set must keep /ready at HTTP 503.\n"
)
_COMMAND_STEPS = {
    "prepare": PREPARE_STEP,
    "verify-release": VERIFY_RELEASE_STEP,
    "activate-local-seed": ACTIVATE_STEP,
    "verify-local-seed": VERIFY_LOCAL_STEP,
}
_COMMAND_FLAGS = {
    "prepare": frozenset({"--draft-dir", "--release-version", "--released-at"}),
    "verify-release": frozenset({"--release-dir"}),
    "activate-local-seed": frozenset({"--release-dir"}),
    "verify-local-seed": frozenset({"--release-dir"}),
}


class _CliFailure(Exception):
    def __init__(self, reason: str, issues: int = 1) -> None:
        self.reason = reason
        self.issues = max(1, issues)
        super().__init__(reason)


def cli(argv: Sequence[str]) -> int:
    """Run one exact publication command with content-free stable output."""

    step = _step_for(argv)
    try:
        command, values = _parse_arguments(argv)
        root = Path(REPOSITORY_ROOT).absolute()
        if not _is_trusted_directory(root):
            raise _CliFailure("REPOSITORY_ROOT_INVALID")

        if command == "prepare":
            _require_exact_prepare_values(values)
            _prepare(root)
            print(
                "[PASS] step=PREPARE-DATA-SEED release=0.1.0-initial.1 "
                "kb=19 office=3 mapping=10"
            )
        else:
            _require_exact_release_value(values)
            if command == "verify-release":
                verify_release_directory(root, root / CANONICAL_RELEASE_RELATIVE_PATH)
                print(
                    "[PASS] step=VERIFY-DATA-SEED-RELEASE "
                    "release=0.1.0-initial.1 issues=0"
                )
            elif command == "activate-local-seed":
                changed = _activate_local_seed(root)
                print(
                    "[PASS] step=ACTIVATE-LOCAL-SEED "
                    f"release=0.1.0-initial.1 changed={changed}"
                )
            else:
                _verify_local_seed(root)
                print("[PASS] step=VERIFY-LOCAL-SEED release=0.1.0-initial.1 active=1")
        return 0
    except ReleaseVerificationError as error:
        _print_failure(step, error.reason, len(error.issues))
        return 2
    except _CliFailure as error:
        _print_failure(step, error.reason, error.issues)
        return 2
    except Exception:
        _print_failure(step, "OPERATION_FAILED", 1)
        return 2


def _step_for(argv: Sequence[str]) -> str:
    if (
        isinstance(argv, Sequence)
        and not isinstance(argv, (str, bytes))
        and argv
        and isinstance(argv[0], str)
    ):
        return _COMMAND_STEPS.get(argv[0], CLI_STEP)
    return CLI_STEP


def _parse_arguments(argv: Sequence[str]) -> tuple[str, dict[str, str]]:
    if isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence) or not argv:
        raise _CliFailure("CLI_ARGUMENTS_INVALID")
    if not all(isinstance(token, str) for token in argv):
        raise _CliFailure("CLI_ARGUMENTS_INVALID")
    command = argv[0]
    allowed = _COMMAND_FLAGS.get(command)
    if allowed is None:
        raise _CliFailure("CLI_ARGUMENTS_INVALID")
    remainder = argv[1:]
    if len(remainder) != len(allowed) * 2:
        raise _CliFailure("CLI_ARGUMENTS_INVALID")
    values: dict[str, str] = {}
    for index in range(0, len(remainder), 2):
        flag = remainder[index]
        value = remainder[index + 1]
        if flag not in allowed or flag in values:
            raise _CliFailure("CLI_ARGUMENTS_INVALID")
        values[flag] = value
    if set(values) != set(allowed):
        raise _CliFailure("CLI_ARGUMENTS_INVALID")
    return command, values


def _require_exact_prepare_values(values: Mapping[str, str]) -> None:
    if values.get("--draft-dir") != CANONICAL_DRAFT_TOKEN:
        raise _CliFailure("DRAFT_PATH_INVALID")
    if values.get("--release-version") != RELEASE_VERSION:
        raise _CliFailure("RELEASE_VERSION_INVALID")
    if values.get("--released-at") != GOVERNANCE_RELEASED_AT:
        raise _CliFailure("RELEASE_TIMESTAMP_INVALID")


def _require_exact_release_value(values: Mapping[str, str]) -> None:
    if values.get("--release-dir") != CANONICAL_RELEASE_TOKEN:
        raise _CliFailure("RELEASE_PATH_INVALID")


def _prepare(root: Path) -> None:
    try:
        bundle = build_release_bundle(
            root,
            root / CANONICAL_DRAFT_RELATIVE_PATH,
            RELEASE_VERSION,
            GOVERNANCE_RELEASED_AT,
        )
    except (OSError, ValueError) as error:
        raise _CliFailure("APPROVED_INPUT_INVALID") from error

    releases = _ensure_release_parent(root)
    release = releases / RELEASE_VERSION
    temporary = releases / f".{RELEASE_VERSION}.prepare"
    if _path_entry_exists(release):
        raise _CliFailure("RELEASE_ALREADY_EXISTS")
    if _path_entry_exists(temporary):
        raise _CliFailure("PREPARE_TEMP_EXISTS")
    try:
        temporary.mkdir()
    except (FileExistsError, OSError) as error:
        raise _CliFailure("PREPARE_TEMP_CREATE_FAILED") from error
    identity = _path_identity(temporary)
    if identity is None or not _is_trusted_directory(temporary):
        raise _CliFailure("PREPARE_TEMP_INVALID")

    try:
        _write_bundle(temporary, bundle)
        _verify_release_contents(root, temporary, bundle)
        if _path_entry_exists(release):
            raise _CliFailure("RELEASE_ALREADY_EXISTS")
        _rename_create_once(temporary, release)
    except Exception as error:
        cleaned = _cleanup_owned_directory(temporary, identity)
        if not cleaned:
            raise _CliFailure("PREPARE_TEMP_OWNERSHIP_LOST") from error
        if isinstance(error, ReleaseVerificationError):
            raise error
        if isinstance(error, _CliFailure):
            raise error
        raise _CliFailure("PREPARE_PUBLICATION_FAILED") from error


def _ensure_release_parent(root: Path) -> Path:
    official = root / "data" / "official"
    if not _is_trusted_directory(official):
        raise _CliFailure("RELEASE_PARENT_INVALID")
    releases = official / "releases"
    if not _path_entry_exists(releases):
        try:
            releases.mkdir()
        except FileExistsError:
            pass
        except OSError as error:
            raise _CliFailure("RELEASE_PARENT_INVALID") from error
    if not _is_trusted_directory(releases):
        raise _CliFailure("RELEASE_PARENT_INVALID")
    return releases


def _rename_create_once(source: Path, target: Path) -> None:
    """Atomically rename without replacing an entry created by another process."""

    if os.name == "nt":
        os.rename(source, target)
        return

    library = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    target_bytes = os.fsencode(target)
    result = -1
    if sys.platform.startswith("linux"):
        rename = getattr(library, "renameat2", None)
        if rename is None:
            raise OSError(errno.ENOTSUP, "atomic no-replace rename unavailable")
        rename.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        rename.restype = ctypes.c_int
        result = rename(-100, source_bytes, -100, target_bytes, 1)
    elif sys.platform == "darwin":
        rename = getattr(library, "renamex_np", None)
        if rename is None:
            raise OSError(errno.ENOTSUP, "atomic no-replace rename unavailable")
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        rename.restype = ctypes.c_int
        result = rename(source_bytes, target_bytes, 4)
    else:
        raise OSError(errno.ENOTSUP, "atomic no-replace rename unavailable")
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))


def _write_bundle(directory: Path, bundle: ReleaseBundle) -> None:
    payloads = release_bundle_files(bundle)
    if set(payloads) != set(RELEASE_ARTIFACTS):
        raise OSError("release artifact set mismatch")
    for artifact in RELEASE_ARTIFACTS:
        _write_exclusive_fsynced(directory / artifact, payloads[artifact])
    _flush_directory_if_supported(directory)


def _write_exclusive_fsynced(path: Path, payload: bytes) -> None:
    with path.open("xb") as target:
        target.write(payload)
        target.flush()
        os.fsync(target.fileno())


def _flush_directory_if_supported(directory: Path) -> None:
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if directory_flag is None:
        return
    descriptor: int | None = None
    try:
        descriptor = os.open(directory, os.O_RDONLY | directory_flag)
        os.fsync(descriptor)
    except OSError:
        return
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _activate_local_seed(root: Path) -> int:
    summary = verify_release_directory(root, root / CANONICAL_RELEASE_RELATIVE_PATH)
    desired = summary.get("seed_sql_bytes")
    if not isinstance(desired, bytes):
        raise _CliFailure("VERIFIED_RELEASE_SEED_INVALID")
    dispatcher = root / "supabase" / "seed.sql"
    previous = _read_trusted_bytes(dispatcher, "DISPATCHER_PATH_INVALID")
    if previous == desired:
        return 0
    if previous != INITIAL_DISPATCHER_BYTES:
        raise _CliFailure("DISPATCHER_DRIFT")

    temporary = _write_dispatcher_temp(dispatcher, desired, "activate")
    identity = _path_identity(temporary)
    try:
        os.replace(temporary, dispatcher)
    except OSError as error:
        _remove_owned_file(temporary, identity)
        if not _dispatcher_matches(dispatcher, previous):
            _restore_dispatcher(dispatcher, previous)
        raise _CliFailure("DISPATCHER_REPLACE_FAILED") from error

    if not _dispatcher_matches(dispatcher, desired):
        _restore_dispatcher(dispatcher, previous)
        raise _CliFailure("DISPATCHER_POSTCHECK_FAILED")
    return 1


def _verify_local_seed(root: Path) -> None:
    summary = verify_release_directory(root, root / CANONICAL_RELEASE_RELATIVE_PATH)
    expected = summary.get("seed_sql_bytes")
    if not isinstance(expected, bytes):
        raise _CliFailure("VERIFIED_RELEASE_SEED_INVALID")
    dispatcher = root / "supabase" / "seed.sql"
    if not _dispatcher_matches(dispatcher, expected):
        raise _CliFailure("LOCAL_SEED_INACTIVE")


def _write_dispatcher_temp(dispatcher: Path, payload: bytes, tag: str) -> Path:
    parent = dispatcher.parent
    if not _is_trusted_directory(parent):
        raise OSError("untrusted dispatcher parent")
    descriptor, raw_path = tempfile.mkstemp(
        prefix=f".{dispatcher.name}.{tag}.", suffix=".tmp", dir=parent
    )
    path = Path(raw_path)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(payload)
            target.flush()
            os.fsync(target.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    return path


def _restore_dispatcher(dispatcher: Path, previous: bytes) -> None:
    temporary: Path | None = None
    identity: tuple[int, int, int] | None = None
    try:
        temporary = _write_dispatcher_temp(dispatcher, previous, "restore")
        identity = _path_identity(temporary)
        os.replace(temporary, dispatcher)
        if not _dispatcher_matches(dispatcher, previous):
            raise OSError("dispatcher restore verification failed")
    except OSError as error:
        if temporary is not None:
            _remove_owned_file(temporary, identity)
        raise _CliFailure("DISPATCHER_RESTORE_FAILED") from error


def _read_trusted_bytes(path: Path, reason: str) -> bytes:
    if not _is_trusted_file(path):
        raise _CliFailure(reason)
    try:
        return path.read_bytes()
    except OSError as error:
        raise _CliFailure(reason) from error


def _dispatcher_matches(dispatcher: Path, expected: bytes) -> bool:
    try:
        if not _is_trusted_file(dispatcher):
            return False
        actual = dispatcher.read_bytes()
        return (
            hashlib.sha256(actual).digest() == hashlib.sha256(expected).digest()
            and actual == expected
        )
    except OSError:
        return False


def _cleanup_owned_directory(
    directory: Path, identity: tuple[int, int, int] | None
) -> bool:
    if identity is None or _path_identity(directory) != identity:
        return False
    if not _is_trusted_directory(directory):
        return False
    try:
        entries = tuple(directory.iterdir())
    except OSError:
        return False
    if any(entry.name not in RELEASE_ARTIFACTS for entry in entries):
        return False
    if any(not _is_trusted_file(entry) for entry in entries):
        return False
    try:
        for entry in entries:
            entry.unlink()
        directory.rmdir()
    except OSError:
        return False
    return True


def _remove_owned_file(path: Path, identity: tuple[int, int, int] | None) -> bool:
    if identity is None or _path_identity(path) != identity:
        return not _path_entry_exists(path)
    if not _is_trusted_file(path):
        return False
    try:
        path.unlink()
    except OSError:
        return False
    return True


def _path_identity(path: Path) -> tuple[int, int, int] | None:
    try:
        metadata = path.lstat()
    except OSError:
        return None
    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)


def _path_entry_exists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


def _is_trusted_directory(path: Path) -> bool:
    try:
        return path.is_dir() and not _has_reparse_component(path)
    except OSError:
        return False


def _is_trusted_file(path: Path) -> bool:
    try:
        return path.is_file() and not _has_reparse_component(path)
    except OSError:
        return False


def _has_reparse_component(path: Path) -> bool:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if not _path_entry_exists(current):
            continue
        try:
            metadata = current.lstat()
            attributes = getattr(metadata, "st_file_attributes", 0)
            reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            if current.is_symlink() or bool(attributes & reparse_flag):
                return True
        except OSError:
            return True
    return False


def _print_failure(step: str, reason: str, issues: int) -> None:
    print(f"[FAIL] step={step} reason={reason} issues={max(1, issues)}")


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
