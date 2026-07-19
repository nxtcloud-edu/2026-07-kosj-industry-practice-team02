"""Deterministic SQL serialization for the DATA-SEED initial release."""

from __future__ import annotations

from datetime import date, datetime, timezone
import json
from typing import Mapping, Sequence

from scripts.data_seed_release import (
    KB_DOCUMENT_FIELDS,
    KB_QUESTION_EXAMPLE_FIELDS,
    OFFICE_FIELDS,
    OFFICE_SERVICE_MAPPING_FIELDS,
)


ADVISORY_LOCK_KEY = 20260719001
LOCK_TIMEOUT = "5s"
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

_TABLE_FIELDS = {
    "kb_documents": KB_DOCUMENT_FIELDS,
    "kb_question_examples": KB_QUESTION_EXAMPLE_FIELDS,
    "offices": OFFICE_FIELDS,
    "office_service_mappings": OFFICE_SERVICE_MAPPING_FIELDS,
}

_EXPECTED_FIELD_TYPES = {
    "kb_documents": {
        "procedure_steps": "jsonb",
        "required_documents": "jsonb",
        "last_verified_at": "date",
        "approved_at": "timestamptz",
    },
    "kb_question_examples": {},
    "offices": {"last_verified_at": "date"},
    "office_service_mappings": {},
}

_INSERT_FIELD_TYPES = {
    "kb_documents": {
        "data_origin": "app_private.data_origin",
        "category": "app_private.intent_code",
        "procedure_steps": "jsonb",
        "required_documents": "jsonb",
        "last_verified_at": "date",
        "status": "app_private.kb_status",
        "approved_at": "timestamptz",
    },
    "kb_question_examples": {},
    "offices": {
        "data_origin": "app_private.data_origin",
        "last_verified_at": "date",
    },
    "office_service_mappings": {},
}


def sql_literal(value: object) -> str:
    """Return a fixed PostgreSQL literal with an explicit non-null type."""

    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return f"{'TRUE' if value else 'FALSE'}::boolean"
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("SQL_TIMESTAMP_TIMEZONE_REQUIRED")
        normalized = value.astimezone(timezone.utc).replace(microsecond=0)
        text = normalized.isoformat(timespec="seconds").replace("+00:00", "Z")
        return f"{_quoted(text)}::timestamptz"
    if isinstance(value, date):
        return f"{_quoted(value.isoformat())}::date"
    if isinstance(value, str):
        return f"{_quoted(value)}::text"
    if isinstance(value, (list, dict)):
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return f"{_quoted(text)}::jsonb"
    raise TypeError("SQL_LITERAL_TYPE_UNSUPPORTED")


def render_expected_rows(projection: Mapping[str, object]) -> str:
    """Render the four fixed expected-row CTE definitions."""

    definitions = []
    for table, fields in _TABLE_FIELDS.items():
        rows = _projection_rows(projection, table, fields)
        values = _render_values(rows, fields, _EXPECTED_FIELD_TYPES[table])
        definitions.append(
            f"expected_{table} ({', '.join(fields)}) AS (\n  VALUES\n{values}\n)"
        )
    return ",\n".join(definitions)


def render_seed_sql(projection: Mapping[str, object]) -> bytes:
    """Render deterministic fail-closed initial seed SQL."""

    rows = {
        table: _projection_rows(projection, table, fields)
        for table, fields in _TABLE_FIELDS.items()
    }
    sections = [
        _transaction_prefix(),
        _empty_preflight("DATA_SEED_DATABASE_NOT_EMPTY", LOCK_TABLES),
        _insert_values_statement(
            "kb_documents",
            KB_DOCUMENT_FIELDS,
            rows["kb_documents"],
        ),
        _insert_question_examples(rows["kb_question_examples"]),
        _insert_values_statement("offices", OFFICE_FIELDS, rows["offices"]),
        _insert_office_mappings(rows["office_service_mappings"]),
        _projection_guard(projection, "DATA_SEED_PROJECTION_MISMATCH"),
        _excluded_row_guard(),
    ]
    return (
        "\n\n".join(section.rstrip("\n") for section in sections).encode("utf-8")
        + b"\n\nCOMMIT;\n"
    )


def render_compensation_sql(projection: Mapping[str, object]) -> bytes:
    """Render deterministic disposable-local compensation SQL."""

    rows = {
        table: _projection_rows(projection, table, fields)
        for table, fields in _TABLE_FIELDS.items()
    }
    mapping_pairs = ",\n".join(
        "    ("
        + ", ".join(
            (
                _typed_literal(row["office_public_id"], "text"),
                _typed_literal(row["intent"], "text"),
            )
        )
        + ")"
        for row in rows["office_service_mappings"]
    )
    kb_ids = ",\n".join(
        f"    ({_typed_literal(row['public_id'], 'text')})"
        for row in rows["kb_documents"]
    )
    office_ids = ",\n".join(
        f"    ({_typed_literal(row['public_id'], 'text')})" for row in rows["offices"]
    )
    deletes = f"""DELETE FROM app_private.office_service_mappings AS mapping
USING app_private.offices AS office
WHERE mapping.office_id = office.id
  AND (office.public_id, mapping.intent::text) IN (
    VALUES
{mapping_pairs}
  );

DELETE FROM app_private.kb_documents AS kb
WHERE kb.public_id IN (
  SELECT expected.public_id
  FROM (VALUES
{kb_ids}
  ) AS expected(public_id)
);

DELETE FROM app_private.offices AS office
WHERE office.public_id IN (
  SELECT expected.public_id
  FROM (VALUES
{office_ids}
  ) AS expected(public_id)
);"""
    sections = [
        _transaction_prefix(),
        _empty_preflight(
            "DATA_SEED_COMPENSATION_OPERATIONAL_ROWS_PRESENT",
            OPERATIONAL_TABLES,
        ),
        _projection_guard(
            projection,
            "DATA_SEED_COMPENSATION_PROJECTION_MISMATCH",
        ),
        deletes,
        _empty_preflight("DATA_SEED_COMPENSATION_ABSENCE_FAILED", LOCK_TABLES),
    ]
    return (
        "\n\n".join(section.rstrip("\n") for section in sections).encode("utf-8")
        + b"\n\nCOMMIT;\n"
    )


def _transaction_prefix() -> str:
    locks = "\n".join(
        f"LOCK TABLE app_private.{table} IN ACCESS EXCLUSIVE MODE;"
        for table in LOCK_TABLES
    )
    return f"""BEGIN;
SET LOCAL standard_conforming_strings = on;
SET LOCAL lock_timeout = '{LOCK_TIMEOUT}';
SELECT pg_catalog.pg_advisory_xact_lock({ADVISORY_LOCK_KEY});

DO $data_seed_assert_principal$
DECLARE
  v_exact_memberships integer;
BEGIN
  IF NOT (
    session_user = 'postgres'
    AND current_user = 'postgres'
    AND current_database() = 'postgres'
  ) THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_PRINCIPAL_INVALID';
  END IF;

  SELECT pg_catalog.count(*)
  INTO v_exact_memberships
  FROM pg_catalog.pg_auth_members AS memberships
  JOIN pg_catalog.pg_roles AS granted_role
    ON granted_role.oid = memberships.roleid
  JOIN pg_catalog.pg_roles AS member_role
    ON member_role.oid = memberships.member
  WHERE granted_role.rolname = 'sejong_schema_owner'
    AND member_role.rolname = 'postgres'
    AND memberships.admin_option
    AND memberships.inherit_option
    AND memberships.set_option;

  IF v_exact_memberships <> 1 THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_MEMBERSHIP_INVALID';
  END IF;
END;
$data_seed_assert_principal$;

SET LOCAL ROLE sejong_schema_owner;

DO $data_seed_assert_role_switch$
BEGIN
  IF NOT (
    session_user = 'postgres'
    AND current_user = 'sejong_schema_owner'
    AND current_database() = 'postgres'
  ) THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_ROLE_SWITCH_INVALID';
  END IF;
END;
$data_seed_assert_role_switch$;

{locks}"""


def _empty_preflight(message: str, tables: Sequence[str]) -> str:
    conditions = "\n     OR ".join(
        f"EXISTS (SELECT 1 FROM app_private.{table})" for table in tables
    )
    return f"""DO $data_seed_empty_guard$
BEGIN
  IF {conditions} THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = '{message}';
  END IF;
END;
$data_seed_empty_guard$;"""


def _insert_values_statement(
    table: str,
    fields: tuple[str, ...],
    rows: Sequence[Mapping[str, object]],
) -> str:
    values = _render_values(rows, fields, _INSERT_FIELD_TYPES[table])
    return f"INSERT INTO app_private.{table} ({', '.join(fields)})\nVALUES\n{values};"


def _insert_question_examples(rows: Sequence[Mapping[str, object]]) -> str:
    fields = KB_QUESTION_EXAMPLE_FIELDS
    values = _render_values(rows, fields, _INSERT_FIELD_TYPES["kb_question_examples"])
    return f"""INSERT INTO app_private.kb_question_examples (
  kb_document_id, question_example, normalized_text
)
SELECT kb.id, expected.question_example, expected.normalized_text
FROM (VALUES
{values}
) AS expected(kb_public_id, question_example, normalized_text)
JOIN app_private.kb_documents AS kb
  ON kb.public_id = expected.kb_public_id
ORDER BY expected.kb_public_id, expected.question_example;"""


def _insert_office_mappings(rows: Sequence[Mapping[str, object]]) -> str:
    fields = OFFICE_SERVICE_MAPPING_FIELDS
    values = _render_values(
        rows, fields, _INSERT_FIELD_TYPES["office_service_mappings"]
    )
    return f"""INSERT INTO app_private.office_service_mappings (
  office_id, intent, department_label
)
SELECT office.id, expected.intent::app_private.intent_code, expected.department_label
FROM (VALUES
{values}
) AS expected(office_public_id, intent, department_label)
JOIN app_private.offices AS office
  ON office.public_id = expected.office_public_id
ORDER BY expected.office_public_id, expected.intent;"""


def _projection_guard(projection: Mapping[str, object], message: str) -> str:
    comparisons: list[str] = []
    for table in _TABLE_FIELDS:
        comparisons.extend(
            (
                f"EXISTS (SELECT * FROM expected_{table} EXCEPT ALL SELECT * FROM actual_{table})",
                f"EXISTS (SELECT * FROM actual_{table} EXCEPT ALL SELECT * FROM expected_{table})",
            )
        )
    mismatch = "\n    OR ".join(comparisons)
    return f"""DO $data_seed_projection_guard$
DECLARE
  v_mismatch boolean;
BEGIN
  WITH
{_indent(render_expected_rows(projection), 4)},
{_indent(_actual_row_ctes(), 4)}
  SELECT
    {mismatch}
  INTO v_mismatch;

  IF v_mismatch THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = '{message}';
  END IF;
END;
$data_seed_projection_guard$;"""


def _actual_row_ctes() -> str:
    return """actual_kb_documents AS (
  SELECT
    kb.public_id,
    kb.data_origin::text AS data_origin,
    kb.category::text AS category,
    kb.service_name,
    kb.answer_summary,
    kb.procedure_steps,
    kb.required_documents,
    kb.processing_time,
    kb.fee,
    kb.department,
    kb.source_title,
    kb.source_url,
    kb.last_verified_at,
    kb.caution,
    kb.status::text AS status,
    kb.created_by,
    kb.approved_by,
    kb.approved_at
  FROM app_private.kb_documents AS kb
),
actual_kb_question_examples AS (
  SELECT
    kb.public_id AS kb_public_id,
    question.question_example,
    question.normalized_text
  FROM app_private.kb_question_examples AS question
  JOIN app_private.kb_documents AS kb ON kb.id = question.kb_document_id
),
actual_offices AS (
  SELECT
    office.public_id,
    office.data_origin::text AS data_origin,
    office.region,
    office.office_name,
    office.address,
    office.phone,
    office.opening_hours,
    office.map_url,
    office.source_title,
    office.source_url,
    office.last_verified_at
  FROM app_private.offices AS office
),
actual_office_service_mappings AS (
  SELECT
    office.public_id AS office_public_id,
    mapping.intent::text AS intent,
    mapping.department_label
  FROM app_private.office_service_mappings AS mapping
  JOIN app_private.offices AS office ON office.id = mapping.office_id
)"""


def _excluded_row_guard() -> str:
    return """DO $data_seed_exclusion_guard$
BEGIN
  IF EXISTS (
       SELECT 1 FROM app_private.kb_documents
       WHERE public_id = 'KB-WASTE-03'
     )
     OR EXISTS (
       SELECT 1
       FROM app_private.office_service_mappings AS mapping
       JOIN app_private.offices AS office ON office.id = mapping.office_id
       WHERE (office.public_id, mapping.intent::text) IN (
         ('OFFICE-AREUM', 'LOCAL_TAX_GENERAL'),
         ('OFFICE-DODAM', 'BULKY_WASTE')
       )
     )
     OR EXISTS (
       SELECT 1 FROM app_private.kb_documents WHERE data_origin::text = 'MOCK'
     )
     OR EXISTS (
       SELECT 1 FROM app_private.offices WHERE data_origin::text = 'MOCK'
     ) THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_EXCLUSION_FAILED';
  END IF;
END;
$data_seed_exclusion_guard$;"""


def _render_values(
    rows: Sequence[Mapping[str, object]],
    fields: tuple[str, ...],
    field_types: Mapping[str, str],
) -> str:
    if not rows:
        raise ValueError("SQL_EXPECTED_ROWS_EMPTY")
    return ",\n".join(
        "    ("
        + ", ".join(
            _typed_literal(row[field], field_types.get(field, "text"))
            for field in fields
        )
        + ")"
        for row in rows
    )


def _typed_literal(value: object, sql_type: str) -> str:
    if value is None:
        return f"NULL::{sql_type}"
    if sql_type == "jsonb":
        if not isinstance(value, (list, dict)):
            raise ValueError("SQL_JSON_VALUE_INVALID")
        return sql_literal(value)
    if sql_type == "date":
        if not isinstance(value, str):
            raise ValueError("SQL_DATE_VALUE_INVALID")
        try:
            parsed = date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("SQL_DATE_VALUE_INVALID") from error
        return sql_literal(parsed)
    if sql_type == "timestamptz":
        if not isinstance(value, str):
            raise ValueError("SQL_TIMESTAMP_VALUE_INVALID")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("SQL_TIMESTAMP_VALUE_INVALID") from error
        return sql_literal(parsed)
    if not isinstance(value, str):
        raise ValueError("SQL_TEXT_VALUE_INVALID")
    return f"{_quoted(value)}::{sql_type}"


def _projection_rows(
    projection: Mapping[str, object],
    table: str,
    fields: tuple[str, ...],
) -> list[Mapping[str, object]]:
    value = projection.get(table)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(row, dict) for row in value)
    ):
        raise ValueError("SQL_PROJECTION_INVALID")
    for row in value:
        if set(row) != set(fields):
            raise ValueError("SQL_PROJECTION_FIELDS_INVALID")
    return value


def _quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _indent(value: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line for line in value.splitlines())
