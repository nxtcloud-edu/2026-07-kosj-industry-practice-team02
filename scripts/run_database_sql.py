from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from pathlib import Path

import psycopg


DATABASE_ROOT = Path(__file__).resolve().parents[1] / "database"


def resolve_database_files(arguments: Sequence[str]) -> tuple[Path, ...]:
    if not arguments:
        raise ValueError("DATABASE_SQL_FILES_REQUIRED")

    database_root = DATABASE_ROOT.resolve(strict=True)
    resolved_files: list[Path] = []
    for argument in arguments:
        candidate = Path(argument)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file() or not resolved.is_relative_to(database_root):
            raise ValueError("DATABASE_SQL_FILE_INVALID")
        resolved_files.append(resolved)
    return tuple(resolved_files)


def run_files(admin_dsn: str, paths: Sequence[Path]) -> None:
    if not admin_dsn.strip():
        raise ValueError("ADMIN_DATABASE_URL_REQUIRED")

    with psycopg.connect(admin_dsn, autocommit=False) as connection:
        for path in paths:
            statement = path.read_text(encoding="utf-8")
            with connection.transaction():
                connection.execute(statement)


def main(arguments: Sequence[str] | None = None) -> int:
    raw_arguments = tuple(sys.argv[1:] if arguments is None else arguments)
    try:
        paths = resolve_database_files(raw_arguments)
    except (OSError, ValueError):
        print("[FAIL] step=RUN-DATABASE-SQL reason=invalid-files code=2")
        return 2

    admin_dsn = os.environ.get("SEJONG_ADMIN_DATABASE_URL", "")
    if not admin_dsn.strip():
        print("[FAIL] step=RUN-DATABASE-SQL reason=missing-admin-dsn code=2")
        return 2

    try:
        run_files(admin_dsn, paths)
    except psycopg.Error:
        print("[FAIL] step=RUN-DATABASE-SQL reason=database code=1")
        return 1
    except (OSError, UnicodeError, ValueError):
        print("[FAIL] step=RUN-DATABASE-SQL reason=operational code=2")
        return 2

    print(f"[PASS] step=RUN-DATABASE-SQL files={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
