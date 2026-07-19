"""Secret-free verification of the initial official seed in disposable local DBs.

This is an initial-release-only verification tool.  It reads release SQL into
memory, uses only the existing psycopg dependency, and never persists or emits a
DSN.  The PowerShell runner is the supported orchestration boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Protocol, Sequence, cast

import psycopg
from psycopg.conninfo import conninfo_to_dict

from scripts.data_seed_release import (
    CANONICAL_DRAFT_RELATIVE_PATH,
    CANONICAL_RELEASE_RELATIVE_PATH,
    KB_DOCUMENT_FIELDS,
    KB_QUESTION_EXAMPLE_FIELDS,
    OFFICE_FIELDS,
    OFFICE_SERVICE_MAPPING_FIELDS,
    RELEASE_VERSION,
    ReleaseVerificationError,
    build_seed_projection,
    canonical_json_bytes,
    semantic_sha256,
    verify_release_directory,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ADMIN_DSN_ENVIRONMENT = "SEJONG_ADMIN_DATABASE_URL"
EXPECTED_ADMIN_IDENTITY = ("postgres", "127.0.0.1", 54322, "postgres")
LOCK_TABLES = (
    "kb_documents",
    "kb_question_examples",
    "offices",
    "office_service_mappings",
    "interaction_events",
    "failed_questions",
    "kb_candidates",
    "audit_logs",
)
OPERATIONAL_TABLES = (
    "interaction_events",
    "failed_questions",
    "kb_candidates",
    "audit_logs",
)
SUPPORTED_INTENTS = (
    "MOVE_IN_RESIDENT_REGISTRATION",
    "CERTIFICATE_ISSUANCE",
    "BULKY_WASTE",
    "LOCAL_TAX_GENERAL",
)

PROJECTION_FIELDS: Mapping[str, tuple[str, ...]] = {
    "kb_documents": KB_DOCUMENT_FIELDS,
    "kb_question_examples": KB_QUESTION_EXAMPLE_FIELDS,
    "offices": OFFICE_FIELDS,
    "office_service_mappings": OFFICE_SERVICE_MAPPING_FIELDS,
}

PROJECTION_QUERIES: Mapping[str, str] = {
    "kb_documents": """
SELECT
  kb.public_id, kb.data_origin::text, kb.category::text, kb.service_name,
  kb.answer_summary, kb.procedure_steps, kb.required_documents,
  kb.processing_time, kb.fee, kb.department, kb.source_title, kb.source_url,
  kb.last_verified_at, kb.caution, kb.status::text, kb.created_by,
  kb.approved_by, kb.approved_at
FROM app_private.kb_documents AS kb
ORDER BY kb.public_id COLLATE pg_catalog."C"
""".strip(),
    "kb_question_examples": """
SELECT kb.public_id, question.question_example, question.normalized_text
FROM app_private.kb_question_examples AS question
JOIN app_private.kb_documents AS kb ON kb.id = question.kb_document_id
ORDER BY
  kb.public_id COLLATE pg_catalog."C",
  question.question_example COLLATE pg_catalog."C"
""".strip(),
    "offices": """
SELECT
  office.public_id, office.data_origin::text, office.region,
  office.office_name, office.address, office.phone, office.opening_hours,
  office.map_url, office.source_title, office.source_url,
  office.last_verified_at
FROM app_private.offices AS office
ORDER BY office.public_id COLLATE pg_catalog."C"
""".strip(),
    "office_service_mappings": """
SELECT office.public_id, mapping.intent::text, mapping.department_label
FROM app_private.office_service_mappings AS mapping
JOIN app_private.offices AS office ON office.id = mapping.office_id
ORDER BY
  office.public_id COLLATE pg_catalog."C",
  mapping.intent::text COLLATE pg_catalog."C"
""".strip(),
}

_ORDER_FIELDS: Mapping[str, tuple[str, ...]] = {
    "kb_documents": ("public_id",),
    "kb_question_examples": ("kb_public_id", "question_example"),
    "offices": ("public_id",),
    "office_service_mappings": ("office_public_id", "intent"),
}
_COMMAND_STEPS = {
    "identity": "VERIFY-DATA-SEED-IDENTITY",
    "failure-rollback": "VERIFY-DATA-SEED-FAILURE-ROLLBACK",
    "seed-cycle": "VERIFY-DATA-SEED-SEED-CYCLE",
    "verify-final": "VERIFY-DATA-SEED-FINAL",
}
_STABLE_REASON = re.compile(r"^[A-Z][A-Z0-9_]+$")


class _Result(Protocol):
    def fetchall(self) -> list[tuple[object, ...]]: ...

    def fetchone(self) -> tuple[object, ...] | None: ...


class _Connection(Protocol):
    def execute(
        self,
        statement: str,
        params: Sequence[object] | None = None,
    ) -> _Result: ...


@dataclass(frozen=True)
class AdminDsn:
    """Validated identity only; the secret-bearing DSN is intentionally absent."""

    identity: tuple[str, str, int, str]


@dataclass(frozen=True)
class VerifiedRelease:
    """One verified release snapshot used for a single verifier invocation."""

    version: str
    counts: Mapping[str, int]
    semantic_sha256: str
    seed_sql: bytes
    compensation_sql: bytes
    projection: Mapping[str, object]


def parse_and_validate_dsn(value: str) -> AdminDsn:
    """Parse libpq conninfo and retain only the exact approved local identity."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError("ADMIN_DSN_IDENTITY_INVALID")
    try:
        values = conninfo_to_dict(value)
        port_value = values.get("port")
        if isinstance(port_value, str):
            if not port_value.isascii() or not port_value.isdecimal():
                raise ValueError
            port = int(port_value)
        elif type(port_value) is int:
            port = port_value
        else:
            raise ValueError
        identity = (
            values.get("user", ""),
            values.get("host", ""),
            port,
            values.get("dbname", ""),
        )
    except (TypeError, ValueError, psycopg.Error):
        raise ValueError("ADMIN_DSN_IDENTITY_INVALID") from None

    # service/servicefile and hostaddr can silently redirect a libpq connection
    # while leaving the display identity looking acceptable.
    if (
        identity != EXPECTED_ADMIN_IDENTITY
        or values.get("hostaddr") not in (None, "")
        or values.get("service") not in (None, "")
        or values.get("servicefile") not in (None, "")
    ):
        raise ValueError("ADMIN_DSN_IDENTITY_INVALID")
    return AdminDsn(identity=identity)


def load_verified_release(
    repository_root: Path, release_version: str
) -> VerifiedRelease:
    """Reverify exact release bytes and bind them to the semantic projection."""

    if release_version != RELEASE_VERSION:
        raise ValueError("RELEASE_VERSION_INVALID")
    root = Path(repository_root).absolute()
    release = (root / CANONICAL_RELEASE_RELATIVE_PATH).absolute()
    summary = verify_release_directory(root, release)
    counts_value = summary.get("counts")
    if not isinstance(counts_value, dict):
        raise ValueError("RELEASE_SUMMARY_INVALID")
    counts = {name: counts_value.get(name) for name in ("kb", "office", "mapping")}
    if counts != {"kb": 19, "office": 3, "mapping": 10}:
        raise ValueError("RELEASE_SUMMARY_INVALID")

    release_hash = summary.get("seed_semantic_sha256")
    seed_sql = summary.get("seed_sql_bytes")
    compensation_sql = summary.get("compensation_sql_bytes")
    if (
        not isinstance(release_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", release_hash) is None
        or not isinstance(seed_sql, bytes)
        or not isinstance(compensation_sql, bytes)
    ):
        raise ValueError("RELEASE_SUMMARY_INVALID")

    projection = build_seed_projection(
        root / CANONICAL_DRAFT_RELATIVE_PATH,
        release_version,
    )
    if semantic_sha256(projection) != release_hash:
        raise ValueError("RELEASE_SEMANTIC_HASH_INVALID")
    return VerifiedRelease(
        version=release_version,
        counts=cast(Mapping[str, int], counts),
        semantic_sha256=release_hash,
        seed_sql=seed_sql,
        compensation_sql=compensation_sql,
        projection=projection,
    )


def canonicalize_database_projection(
    projection: Mapping[str, object],
) -> dict[str, object]:
    """Normalize psycopg date/timestamp/JSON values to release hash values."""

    normalized: dict[str, object] = {}
    for table in PROJECTION_FIELDS:
        value = projection.get(table)
        if not isinstance(value, list) or not all(
            isinstance(row, dict) for row in value
        ):
            raise ValueError("DATABASE_PROJECTION_INVALID")
        rows: list[dict[str, object]] = []
        for row in value:
            rows.append(
                {str(key): _canonical_database_value(item) for key, item in row.items()}
            )
        order_fields = _ORDER_FIELDS[table]
        rows.sort(
            key=lambda row: tuple(_order_text(row.get(field)) for field in order_fields)
        )
        normalized[table] = rows
    return normalized


def _canonical_database_value(value: object) -> object:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("DATABASE_TIMESTAMP_INVALID")
        return (
            value.astimezone(timezone.utc)
            .replace(microsecond=0)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {
            str(key): _canonical_database_value(item) for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_database_value(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    raise ValueError("DATABASE_VALUE_INVALID")


def _order_text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("DATABASE_ORDER_KEY_INVALID")
    return value


def query_database_projection(connection: _Connection) -> dict[str, object]:
    """Query only seed-owned columns and return the canonical four-array object."""

    projection: dict[str, object] = {}
    for table, fields in PROJECTION_FIELDS.items():
        rows = connection.execute(PROJECTION_QUERIES[table]).fetchall()
        if any(len(row) != len(fields) for row in rows):
            raise ValueError("DATABASE_PROJECTION_INVALID")
        projection[table] = [dict(zip(fields, row, strict=True)) for row in rows]
    return canonicalize_database_projection(projection)


def database_semantic_sha256(connection: _Connection) -> str:
    projection = query_database_projection(connection)
    return hashlib.sha256(
        canonical_json_bytes(projection, trailing_newline=False)
    ).hexdigest()


def require_expected_database_error(error: BaseException, message: str) -> None:
    """Accept only the planned P0001 error without exposing database detail."""

    sqlstate = getattr(error, "sqlstate", None)
    diagnostic = getattr(error, "diag", None)
    primary = getattr(diagnostic, "message_primary", None)
    if sqlstate != "P0001" or primary != message:
        raise ValueError("EXPECTED_DATABASE_ERROR_MISSING")


def _assert_session_identity(connection: _Connection) -> None:
    row = connection.execute(
        """
SELECT
  session_user,
  current_user,
  current_database(),
  pg_catalog.count(*)::integer,
  pg_catalog.coalesce(
    pg_catalog.bool_and(
      memberships.admin_option
      AND memberships.inherit_option
      AND memberships.set_option
    ),
    false
  )
FROM pg_catalog.pg_auth_members AS memberships
JOIN pg_catalog.pg_roles AS granted_role ON granted_role.oid = memberships.roleid
JOIN pg_catalog.pg_roles AS member_role ON member_role.oid = memberships.member
WHERE granted_role.rolname = 'sejong_schema_owner'
  AND member_role.rolname = 'postgres'
GROUP BY session_user, current_user, current_database()
""".strip()
    ).fetchone()
    if row != ("postgres", "postgres", "postgres", 1, True):
        raise ValueError("DATABASE_SESSION_IDENTITY_INVALID")


def _table_counts(connection: _Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in LOCK_TABLES:
        row = connection.execute(
            f"SELECT pg_catalog.count(*)::integer FROM app_private.{table}"
        ).fetchone()
        if row is None or len(row) != 1 or not isinstance(row[0], int):
            raise ValueError("DATABASE_COUNT_INVALID")
        counts[table] = row[0]
    return counts


def _assert_exact_projection(connection: _Connection, release: VerifiedRelease) -> None:
    actual = query_database_projection(connection)
    if actual != release.projection:
        raise ValueError("DATABASE_PROJECTION_MISMATCH")
    if database_semantic_sha256(connection) != release.semantic_sha256:
        raise ValueError("DATABASE_SEMANTIC_HASH_MISMATCH")


def _assert_all_tables_empty(connection: _Connection) -> None:
    if any(_table_counts(connection).values()):
        raise ValueError("DATABASE_PARTIAL_MUTATION")


def _rollback_quietly(connection: _Connection) -> None:
    try:
        connection.execute("ROLLBACK")
    except Exception:
        pass


def _execute_sql(connection: _Connection, payload: bytes) -> None:
    try:
        statement = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ValueError("RELEASE_SQL_INVALID") from None
    connection.execute(statement)


def _expect_sql_failure(
    connection: _Connection,
    payload: bytes,
    message: str,
) -> None:
    try:
        _execute_sql(connection, payload)
    except Exception as error:
        _rollback_quietly(connection)
        require_expected_database_error(error, message)
        return
    raise ValueError("EXPECTED_DATABASE_ERROR_MISSING")


def _inject_before(
    payload: bytes,
    marker: bytes,
    statement: bytes,
    *,
    expected_markers: int = 1,
) -> bytes:
    if payload.count(marker) != expected_markers:
        raise ValueError("RELEASE_SQL_MARKER_INVALID")
    return payload.replace(marker, statement + marker, 1)


def _forced_failure_sql(seed_sql: bytes) -> bytes:
    return _inject_before(
        seed_sql,
        b"\n\nDO $data_seed_projection_guard$",
        b"\n\nDO $data_seed_forced_failure$\nBEGIN\n"
        b"  RAISE EXCEPTION USING ERRCODE = 'P0001', "
        b"MESSAGE = 'DATA_SEED_FORCED_FAILURE';\n"
        b"END;\n$data_seed_forced_failure$;",
    )


def _blocked_compensation_sql(compensation_sql: bytes) -> bytes:
    return _inject_before(
        compensation_sql,
        b"\n\nDO $data_seed_empty_guard$",
        b"\n\nINSERT INTO app_private.interaction_events (\n"
        b"  intent, answer_status, source_count, used_source_ids,\n"
        b"  response_time_ms, is_test, request_id\n"
        b") VALUES (\n"
        b"  'MOVE_IN_RESIDENT_REGISTRATION', 'FOLLOWUP', 0, '[]'::jsonb,\n"
        b"  0, true, '45000000-0000-4000-8000-000000000901'::uuid\n"
        b");",
        expected_markers=2,
    )


def _run_failure_rollback(connection: _Connection, release: VerifiedRelease) -> None:
    _assert_session_identity(connection)
    _assert_all_tables_empty(connection)
    _expect_sql_failure(
        connection,
        _forced_failure_sql(release.seed_sql),
        "DATA_SEED_FORCED_FAILURE",
    )
    _assert_all_tables_empty(connection)


def _run_seed_cycle(connection: _Connection, release: VerifiedRelease) -> None:
    _assert_session_identity(connection)
    _assert_all_tables_empty(connection)
    _execute_sql(connection, release.seed_sql)
    _assert_exact_projection(connection, release)

    before_second = database_semantic_sha256(connection)
    _expect_sql_failure(connection, release.seed_sql, "DATA_SEED_DATABASE_NOT_EMPTY")
    if database_semantic_sha256(connection) != before_second:
        raise ValueError("SECOND_SEED_MUTATED_DATABASE")

    _expect_sql_failure(
        connection,
        _blocked_compensation_sql(release.compensation_sql),
        "DATA_SEED_COMPENSATION_OPERATIONAL_ROWS_PRESENT",
    )
    _assert_exact_projection(connection, release)
    if any(_table_counts(connection)[table] for table in OPERATIONAL_TABLES):
        raise ValueError("COMPENSATION_GUARD_PARTIAL_MUTATION")

    _execute_sql(connection, release.compensation_sql)
    _assert_all_tables_empty(connection)
    _execute_sql(connection, release.seed_sql)
    _assert_exact_projection(connection, release)


def _assert_final_evidence(connection: _Connection, release: VerifiedRelease) -> None:
    _assert_session_identity(connection)
    _assert_exact_projection(connection, release)
    counts = _table_counts(connection)
    if counts["kb_documents"] != 19 or counts["offices"] != 3:
        raise ValueError("DATABASE_COUNT_INVALID")
    if counts["office_service_mappings"] != 10:
        raise ValueError("DATABASE_COUNT_INVALID")
    if any(counts[table] for table in OPERATIONAL_TABLES):
        raise ValueError("DATABASE_OPERATIONAL_ROWS_PRESENT")

    excluded = connection.execute(
        """
SELECT
  (SELECT pg_catalog.count(*) FROM app_private.kb_documents
   WHERE public_id = 'KB-WASTE-03'),
  (SELECT pg_catalog.count(*)
   FROM app_private.office_service_mappings AS mapping
   JOIN app_private.offices AS office ON office.id = mapping.office_id
   WHERE (office.public_id, mapping.intent::text) IN (
     ('OFFICE-AREUM', 'LOCAL_TAX_GENERAL'),
     ('OFFICE-DODAM', 'BULKY_WASTE')
   )),
  (SELECT pg_catalog.count(*) FROM app_private.kb_documents
   WHERE data_origin::text = 'MOCK'),
  (SELECT pg_catalog.count(*) FROM app_private.offices
   WHERE data_origin::text = 'MOCK')
""".strip()
    ).fetchone()
    if excluded != (0, 0, 0, 0):
        raise ValueError("DATABASE_EXCLUSION_FAILED")

    expected_by_intent: dict[str, list[str]] = {
        intent: [] for intent in SUPPORTED_INTENTS
    }
    kb_rows = release.projection.get("kb_documents")
    if not isinstance(kb_rows, list):
        raise ValueError("RELEASE_PROJECTION_INVALID")
    for row in kb_rows:
        if not isinstance(row, dict):
            raise ValueError("RELEASE_PROJECTION_INVALID")
        category = row.get("category")
        public_id = row.get("public_id")
        if not isinstance(category, str) or not isinstance(public_id, str):
            raise ValueError("RELEASE_PROJECTION_INVALID")
        if category not in expected_by_intent:
            raise ValueError("RELEASE_PROJECTION_INVALID")
        expected_by_intent[category].append(public_id)

    actual_ids: list[str] = []
    for intent in SUPPORTED_INTENTS:
        rows = connection.execute(
            "SELECT public_id FROM app_api.list_active_kb(%s)",
            (intent,),
        ).fetchall()
        if any(len(row) != 1 or not isinstance(row[0], str) for row in rows):
            raise ValueError("CITIZEN_READ_INVALID")
        ids = [cast(str, row[0]) for row in rows]
        if ids != sorted(expected_by_intent[intent]):
            raise ValueError("CITIZEN_READ_INVALID")
        actual_ids.extend(ids)
    if len(actual_ids) != 19 or len(set(actual_ids)) != 19:
        raise ValueError("CITIZEN_READ_INVALID")


def _open_connection(dsn: str) -> psycopg.Connection[Any]:
    return psycopg.connect(dsn, autocommit=True)


def _parse_cli(argv: Sequence[str]) -> tuple[str, str]:
    if (
        isinstance(argv, (str, bytes))
        or len(argv) != 3
        or argv[0] not in _COMMAND_STEPS
        or argv[1] != "--release-version"
        or argv[2] != RELEASE_VERSION
    ):
        raise ValueError("CLI_ARGUMENTS_INVALID")
    return argv[0], argv[2]


def _stable_reason(error: BaseException) -> str:
    if isinstance(error, ReleaseVerificationError):
        return (
            error.reason
            if _STABLE_REASON.fullmatch(error.reason)
            else "RELEASE_INVALID"
        )
    if isinstance(error, ValueError) and error.args and isinstance(error.args[0], str):
        reason = error.args[0]
        if _STABLE_REASON.fullmatch(reason):
            return reason
    return "OPERATION_FAILED"


def cli(argv: Sequence[str]) -> int:
    """Run one exact command and emit a single content-free evidence line."""

    command = argv[0] if argv and isinstance(argv[0], str) else ""
    step = _COMMAND_STEPS.get(command, "VERIFY-DATA-SEED-CLI")
    try:
        command, release_version = _parse_cli(argv)
        release = load_verified_release(REPOSITORY_ROOT, release_version)
        dsn = os.environ.get(ADMIN_DSN_ENVIRONMENT, "")
        parse_and_validate_dsn(dsn)
        with _open_connection(dsn) as connection:
            if command == "identity":
                _assert_session_identity(connection)
                detail = "identity=exact"
            elif command == "failure-rollback":
                _run_failure_rollback(connection, release)
                detail = "tables=8 partial=0"
            elif command == "seed-cycle":
                _run_seed_cycle(connection, release)
                detail = (
                    "kb=19 office=3 mapping=10 replay=1 second_seed=blocked "
                    "compensation_guard=blocked "
                    f"semantic_sha256={release.semantic_sha256}"
                )
            else:
                _assert_final_evidence(connection, release)
                detail = (
                    "kb=19 office=3 mapping=10 citizen=19 exclusions=0 operational=0 "
                    f"semantic_sha256={release.semantic_sha256}"
                )
        print(f"[PASS] step={step} release={RELEASE_VERSION} {detail}")
        return 0
    except Exception as error:
        print(f"[FAIL] step={step} reason={_stable_reason(error)} issues=1")
        return 2


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
