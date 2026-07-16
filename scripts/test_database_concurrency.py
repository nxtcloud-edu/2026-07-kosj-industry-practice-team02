from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import psycopg
from psycopg import Connection


LINEAGE_ERROR = "LINEAGE_WRITE_REQUIRES_READ_COMMITTED"
QUESTION_ERROR = "KB_QUESTION_WRITE_REQUIRES_READ_COMMITTED"
ACTIVE_ERROR = "KB_ACTIVE_TRANSITION_REQUIRES_READ_COMMITTED"

KB_ID = "45000000-0000-4000-8000-000000000101"
QUESTION_ID = "45000000-0000-4000-8000-000000000121"
SECOND_QUESTION_ID = "45000000-0000-4000-8000-000000000122"
EVENT_ID = "45000000-0000-4000-8000-000000000201"
REQUEST_ID = "45000000-0000-4000-8000-000000000211"
FAILURE_ID = "45000000-0000-4000-8000-000000000301"
CANDIDATE_ID = "45000000-0000-4000-8000-000000000401"


def rollback_quietly(connection: Connection[Any]) -> None:
    try:
        connection.execute("ROLLBACK")
    except psycopg.Error:
        pass


def run_transaction(
    connection: Connection[Any], operation: Callable[[Connection[Any]], object]
) -> None:
    connection.execute("BEGIN")
    try:
        operation(connection)
        connection.execute("COMMIT")
    except Exception:
        rollback_quietly(connection)
        raise


def expect_p0001(
    connection: Connection[Any], operation: Callable[[], object], message: str
) -> None:
    try:
        operation()
    except psycopg.Error as error:
        primary_message = error.diag.message_primary
        rollback_quietly(connection)
        if error.sqlstate != "P0001" or primary_message != message:
            raise AssertionError("UNEXPECTED_DATABASE_ERROR") from None
        return
    rollback_quietly(connection)
    raise AssertionError("EXPECTED_DATABASE_ERROR_MISSING")


def fetch_count(connection: Connection[Any], statement: str) -> int:
    row = connection.execute(statement).fetchone()
    if row is None:
        raise AssertionError("COUNT_RESULT_MISSING")
    return int(row[0])


def cleanup(connection: Connection[Any]) -> None:
    def remove_fixtures(active: Connection[Any]) -> None:
        active.execute(
            "DELETE FROM app_private.audit_logs WHERE target_id = %s", (CANDIDATE_ID,)
        )
        active.execute(
            "DELETE FROM app_private.kb_candidates WHERE id = %s", (CANDIDATE_ID,)
        )
        active.execute(
            "DELETE FROM app_private.failed_questions WHERE id = %s", (FAILURE_ID,)
        )
        active.execute(
            "DELETE FROM app_private.interaction_events WHERE id = %s", (EVENT_ID,)
        )
        active.execute("DELETE FROM app_private.kb_documents WHERE id = %s", (KB_ID,))

    run_transaction(connection, remove_fixtures)


def setup_draft_kb(connection: Connection[Any]) -> None:
    def insert_fixtures(active: Connection[Any]) -> None:
        active.execute(
            """
            INSERT INTO app_private.kb_documents (
              id, public_id, data_origin, category, service_name, answer_summary,
              department, source_title, source_url, last_verified_at, status, created_by
            ) VALUES (
              %s, 'T4-MIXED-ISOLATION-KB', 'OFFICIAL', 'BULKY_WASTE',
              'MOCK isolation service', 'MOCK isolation summary', 'MOCK department',
              'MOCK official source', 'https://example.invalid/t4/isolation-kb',
              DATE '2026-07-16', 'DRAFT', 'MOCK-T4-OPERATOR'
            )
            """,
            (KB_ID,),
        )
        active.execute(
            """
            INSERT INTO app_private.kb_question_examples (
              id, kb_document_id, question_example
            ) VALUES (%s, %s, 'MOCK stale snapshot question')
            """,
            (QUESTION_ID, KB_ID),
        )

    run_transaction(connection, insert_fixtures)


def setup_event(connection: Connection[Any], *, with_failure: bool) -> None:
    def insert_fixtures(active: Connection[Any]) -> None:
        active.execute(
            """
            INSERT INTO app_private.interaction_events (
              id, intent, answer_status, fallback_reason, source_count, used_source_ids,
              response_time_ms, is_test, request_id
            ) VALUES (
              %s, 'BULKY_WASTE', 'FALLBACK', 'INSUFFICIENT_GROUNDING',
              0, '[]'::jsonb, 1, true, %s
            )
            """,
            (EVENT_ID, REQUEST_ID),
        )
        if with_failure:
            insert_failure(active)

    run_transaction(connection, insert_fixtures)


def insert_failure(connection: Connection[Any]) -> None:
    connection.execute(
        """
        INSERT INTO app_private.failed_questions (
          id, interaction_event_id, masked_question, intent, fallback_reason,
          candidate_eligible, status
        ) VALUES (
          %s, %s, '[MASKED] MOCK isolation failure', 'BULKY_WASTE',
          'INSUFFICIENT_GROUNDING', true, 'REASON_CONFIRMED'
        )
        """,
        (FAILURE_ID, EVENT_ID),
    )


def insert_candidate(connection: Connection[Any]) -> None:
    connection.execute(
        """
        INSERT INTO app_private.kb_candidates (
          id, failed_question_id, title, representative_question, data_origin,
          category, answer_summary, department, source_title, source_url,
          last_verified_at, created_by
        ) VALUES (
          %s, %s, 'MOCK isolation candidate', 'MOCK generalized isolation question',
          'MOCK', 'BULKY_WASTE', 'MOCK candidate summary', 'MOCK department',
          'MOCK source', 'https://example.invalid/t4/isolation-candidate',
          DATE '2026-07-16', 'MOCK-T4-OPERATOR'
        )
        """,
        (CANDIDATE_ID, FAILURE_ID),
    )


def probe_question_and_active(
    read_committed: Connection[Any], repeatable_read: Connection[Any]
) -> None:
    cleanup(read_committed)
    setup_draft_kb(read_committed)

    repeatable_read.execute("BEGIN ISOLATION LEVEL REPEATABLE READ")
    expect_p0001(
        repeatable_read,
        lambda: repeatable_read.execute(
            """
            INSERT INTO app_private.kb_question_examples (
              id, kb_document_id, question_example
            ) VALUES (%s, %s, 'MOCK blocked RR question')
            """,
            (SECOND_QUESTION_ID, KB_ID),
        ),
        QUESTION_ERROR,
    )

    repeatable_read.execute("BEGIN ISOLATION LEVEL REPEATABLE READ")
    question_count = fetch_count(
        repeatable_read,
        f"SELECT count(*) FROM app_private.kb_question_examples "
        f"WHERE kb_document_id = '{KB_ID}'::uuid",
    )
    if question_count != 1:
        raise AssertionError("QUESTION_FIXTURE_COUNT_INVALID")

    run_transaction(
        read_committed,
        lambda active: active.execute(
            "DELETE FROM app_private.kb_question_examples WHERE id = %s", (QUESTION_ID,)
        ),
    )
    repeatable_read.execute(
        """
        UPDATE app_private.kb_documents
        SET status = 'ACTIVE', approved_by = 'MOCK-T4-APPROVER', approved_at = now()
        WHERE id = %s
        """,
        (KB_ID,),
    )
    expect_p0001(
        repeatable_read,
        lambda: repeatable_read.execute("COMMIT"),
        ACTIVE_ERROR,
    )


def probe_event_failure(
    read_committed: Connection[Any], repeatable_read: Connection[Any]
) -> None:
    cleanup(read_committed)
    setup_event(read_committed, with_failure=False)

    repeatable_read.execute("BEGIN ISOLATION LEVEL REPEATABLE READ")
    failure_count = fetch_count(
        repeatable_read,
        f"SELECT count(*) FROM app_private.failed_questions "
        f"WHERE interaction_event_id = '{EVENT_ID}'::uuid",
    )
    if failure_count != 0:
        raise AssertionError("FAILURE_FIXTURE_COUNT_INVALID")

    run_transaction(read_committed, insert_failure)
    expect_p0001(
        repeatable_read,
        lambda: repeatable_read.execute(
            """
            UPDATE app_private.interaction_events
            SET answer_status = 'FOLLOWUP', fallback_reason = NULL
            WHERE id = %s
            """,
            (EVENT_ID,),
        ),
        LINEAGE_ERROR,
    )


def probe_failure_candidate(
    read_committed: Connection[Any], repeatable_read: Connection[Any]
) -> None:
    cleanup(read_committed)
    setup_event(read_committed, with_failure=True)

    repeatable_read.execute("BEGIN ISOLATION LEVEL REPEATABLE READ")
    candidate_count = fetch_count(
        repeatable_read,
        f"SELECT count(*) FROM app_private.kb_candidates "
        f"WHERE failed_question_id = '{FAILURE_ID}'::uuid",
    )
    if candidate_count != 0:
        raise AssertionError("CANDIDATE_FIXTURE_COUNT_INVALID")

    run_transaction(read_committed, insert_candidate)
    expect_p0001(
        repeatable_read,
        lambda: repeatable_read.execute(
            """
            UPDATE app_private.failed_questions
            SET candidate_eligible = candidate_eligible
            WHERE id = %s
            """,
            (FAILURE_ID,),
        ),
        LINEAGE_ERROR,
    )


def run_probes(admin_dsn: str) -> None:
    if not admin_dsn.strip():
        raise ValueError("ADMIN_DATABASE_URL_REQUIRED")

    with (
        psycopg.connect(admin_dsn, autocommit=True) as read_committed,
        psycopg.connect(admin_dsn, autocommit=True) as repeatable_read,
    ):
        try:
            probe_question_and_active(read_committed, repeatable_read)
            probe_event_failure(read_committed, repeatable_read)
            probe_failure_candidate(read_committed, repeatable_read)
        finally:
            rollback_quietly(repeatable_read)
            cleanup(read_committed)


def main() -> int:
    admin_dsn = os.environ.get("SEJONG_ADMIN_DATABASE_URL", "")
    if not admin_dsn.strip():
        print("[FAIL] step=DATABASE-CONCURRENCY reason=missing-admin-dsn code=2")
        return 2

    try:
        run_probes(admin_dsn)
    except psycopg.Error:
        print("[FAIL] step=DATABASE-CONCURRENCY reason=database code=1")
        return 1
    except (AssertionError, OSError, ValueError):
        print("[FAIL] step=DATABASE-CONCURRENCY reason=invariant code=1")
        return 1

    print("[PASS] step=DATABASE-CONCURRENCY scenarios=3 connections=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
