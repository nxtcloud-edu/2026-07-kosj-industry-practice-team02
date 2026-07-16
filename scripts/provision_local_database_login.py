from __future__ import annotations

import os
import secrets
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo


ROLE_NAME = "sejong_local_login"
TARGET_ENV_KEY = "DATABASE_URL"
CAPABILITY_ROLE_NAME = "sejong_backend"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = REPOSITORY_ROOT / "apps" / "api" / ".env"


def update_env_assignment(path: Path, key: str, value: str) -> None:
    if not key or any(character in key for character in "=\r\n"):
        raise ValueError("INVALID_ENV_KEY")
    if any(character in value for character in "\r\n"):
        raise ValueError("INVALID_ENV_VALUE")

    original = path.read_bytes() if path.exists() else b""
    key_prefix = key.encode("utf-8") + b"="
    replacement = key_prefix + value.encode("utf-8")
    updated_lines: list[bytes] = []
    found = False

    for line in original.splitlines(keepends=True):
        content = line.rstrip(b"\r\n")
        line_ending = line[len(content) :]
        if content.startswith(key_prefix):
            updated_lines.append(replacement + line_ending)
            found = True
        else:
            updated_lines.append(line)

    updated = b"".join(updated_lines)
    if not found:
        line_ending = b"\r\n" if b"\r\n" in original else b"\n"
        if updated and not updated.endswith((b"\r", b"\n")):
            updated += line_ending
        updated += replacement + line_ending

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(updated)


def provision(admin_dsn: str, env_path: Path) -> None:
    if not admin_dsn.strip():
        raise ValueError("ADMIN_DATABASE_URL_REQUIRED")

    password = secrets.token_urlsafe(32)
    with psycopg.connect(admin_dsn, autocommit=False) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (ROLE_NAME,))
            role_exists = cursor.fetchone() is not None
            role_options = sql.SQL(
                " LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE "
                "NOREPLICATION NOBYPASSRLS PASSWORD {}"
            ).format(sql.Literal(password))
            if role_exists:
                cursor.execute(
                    sql.SQL("ALTER ROLE {} WITH").format(sql.Identifier(ROLE_NAME))
                    + role_options
                )
            else:
                cursor.execute(
                    sql.SQL("CREATE ROLE {} WITH").format(sql.Identifier(ROLE_NAME))
                    + role_options
                )
            cursor.execute(
                sql.SQL("GRANT {} TO {}").format(
                    sql.Identifier(CAPABILITY_ROLE_NAME),
                    sql.Identifier(ROLE_NAME),
                )
            )
        connection.commit()

    backend_dsn = make_conninfo(admin_dsn, user=ROLE_NAME, password=password)
    update_env_assignment(env_path, TARGET_ENV_KEY, backend_dsn)


def main() -> int:
    admin_dsn = os.environ.get("SEJONG_ADMIN_DATABASE_URL", "")
    if not admin_dsn.strip():
        print("[FAIL] step=PROVISION-LOCAL-DB-LOGIN reason=missing-admin-dsn code=2")
        return 2

    try:
        provision(admin_dsn, DEFAULT_ENV_PATH)
    except psycopg.Error:
        print("[FAIL] step=PROVISION-LOCAL-DB-LOGIN reason=database code=1")
        return 1
    except (OSError, UnicodeError, ValueError):
        print("[FAIL] step=PROVISION-LOCAL-DB-LOGIN reason=operational code=1")
        return 1

    print("[PASS] step=PROVISION-LOCAL-DB-LOGIN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
