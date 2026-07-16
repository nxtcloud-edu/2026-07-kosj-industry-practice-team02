from __future__ import annotations

import contextlib
import os
import queue
import threading
import time
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
REPLAY_EVENT_ID = "45000000-0000-4000-8000-000000000202"
REPLAY_REQUEST_ID = "45000000-0000-4000-8000-000000000212"
REPLAY_FAILURE_ID = "45000000-0000-4000-8000-000000000302"


def rollback_quietly(connection: Connection[Any]) -> None:
    with contextlib.suppress(psycopg.Error):
        connection.execute("ROLLBACK")


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
        active.execute("DELETE FROM app_private.audit_logs WHERE target_id = %s", (CANDIDATE_ID,))
        active.execute(
            "DELETE FROM app_private.audit_logs WHERE target_id = %s",
            (REPLAY_FAILURE_ID,),
        )
        active.execute("DELETE FROM app_private.kb_candidates WHERE id = %s", (CANDIDATE_ID,))
        active.execute("DELETE FROM app_private.failed_questions WHERE id = %s", (FAILURE_ID,))
        active.execute("DELETE FROM app_private.interaction_events WHERE id = %s", (EVENT_ID,))
        active.execute(
            "DELETE FROM app_private.failed_questions WHERE id = %s",
            (REPLAY_FAILURE_ID,),
        )
        active.execute(
            "DELETE FROM app_private.interaction_events WHERE id = %s",
            (REPLAY_EVENT_ID,),
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


def probe_event_failure(read_committed: Connection[Any], repeatable_read: Connection[Any]) -> None:
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


def setup_replay_confirm(connection: Connection[Any]) -> None:
    def insert_fixtures(active: Connection[Any]) -> None:
        active.execute(
            """
            INSERT INTO app_private.interaction_events (
              id, intent, answer_status, fallback_reason, source_count,
              used_source_ids, response_time_ms, is_test, request_id
            ) VALUES (
              %s, 'BULKY_WASTE', 'FALLBACK', 'INSUFFICIENT_GROUNDING',
              0, '[]'::jsonb, 1, true, %s
            )
            """,
            (REPLAY_EVENT_ID, REPLAY_REQUEST_ID),
        )
        active.execute(
            """
            INSERT INTO app_private.failed_questions (
              id, interaction_event_id, masked_question, intent, fallback_reason,
              candidate_eligible, status
            ) VALUES (
              %s, %s, '[MASKED] MOCK replay-confirm failure', 'BULKY_WASTE',
              'INSUFFICIENT_GROUNDING', true, 'NEW'
            )
            """,
            (REPLAY_FAILURE_ID, REPLAY_EVENT_ID),
        )

    run_transaction(connection, insert_fixtures)


def probe_replay_confirm_lock_order(admin_dsn: str) -> None:
    worker_pid: queue.Queue[int] = queue.Queue(maxsize=1)
    worker_result: queue.Queue[BaseException | None] = queue.Queue(maxsize=1)
    worker_done = threading.Event()

    def confirm_reason() -> None:
        try:
            with psycopg.connect(admin_dsn, autocommit=True) as connection:
                worker_pid.put(connection.info.backend_pid)
                connection.execute("BEGIN")
                connection.execute("SET LOCAL deadlock_timeout = '100ms'")
                connection.execute("SET LOCAL lock_timeout = '5s'")
                connection.execute("SET LOCAL statement_timeout = '10s'")
                try:
                    connection.execute(
                        "SELECT app_api.confirm_failed_question_reason(%s, %s, %s, %s)",
                        (
                            REPLAY_FAILURE_ID,
                            "MOCK-T4-OPERATOR",
                            "OPERATOR",
                            "INSUFFICIENT_GROUNDING",
                        ),
                    )
                    connection.execute("COMMIT")
                    worker_result.put(None)
                except BaseException as error:
                    rollback_quietly(connection)
                    worker_result.put(error)
        except BaseException as error:
            if worker_pid.empty():
                worker_pid.put(-1)
            if worker_result.empty():
                worker_result.put(error)
        finally:
            worker_done.set()

    with psycopg.connect(admin_dsn, autocommit=True) as replay:
        cleanup(replay)
        setup_replay_confirm(replay)
        replay.execute("BEGIN")
        replay.execute("SET LOCAL deadlock_timeout = '100ms'")
        replay.execute("SET LOCAL lock_timeout = '5s'")
        replay.execute("SET LOCAL statement_timeout = '10s'")
        replay.execute(
            "SELECT 1 FROM app_private.interaction_events WHERE id = %s FOR SHARE",
            (REPLAY_EVENT_ID,),
        )

        worker = threading.Thread(target=confirm_reason, daemon=True)
        worker.start()
        pid = worker_pid.get(timeout=3)
        if pid < 0:
            worker.join(timeout=3)
            error = worker_result.get_nowait()
            if error is not None:
                raise error
            raise AssertionError("CONFIRM_WORKER_START_FAILED")

        deadline = time.monotonic() + 3
        while not worker_done.is_set() and time.monotonic() < deadline:
            waiting = replay.execute(
                """
                SELECT wait_event_type = 'Lock'
                FROM pg_catalog.pg_stat_activity
                WHERE pid = %s
                """,
                (pid,),
            ).fetchone()
            if waiting is not None and bool(waiting[0]):
                break
            time.sleep(0.02)

        replay_error: BaseException | None = None
        replay_row: tuple[object, ...] | None = None
        try:
            replay_row = replay.execute(
                """
                SELECT * FROM app_api.record_interaction(
                  %s, 'BULKY_WASTE', 'FALLBACK', 'INSUFFICIENT_GROUNDING',
                  ARRAY[]::text[], 1, NULL, NULL, true,
                  '[MASKED] MOCK replay-confirm failure'
                )
                """,
                (REPLAY_REQUEST_ID,),
            ).fetchone()
            replay.execute("COMMIT")
        except BaseException as error:
            replay_error = error
            rollback_quietly(replay)

        worker.join(timeout=10)
        if worker.is_alive():
            raise AssertionError("REPLAY_CONFIRM_WORKER_TIMEOUT")
        confirm_error = worker_result.get_nowait()

        for operation_error in (replay_error, confirm_error):
            if isinstance(operation_error, psycopg.Error) and operation_error.sqlstate == "40P01":
                raise AssertionError("REPLAY_CONFIRM_DEADLOCK") from None
            if operation_error is not None:
                raise operation_error

        if replay_row is None or tuple(str(value) for value in replay_row) != (
            REPLAY_EVENT_ID,
            REPLAY_FAILURE_ID,
        ):
            raise AssertionError("REPLAY_RETURNED_DIFFERENT_LINEAGE")
        lineage = replay.execute(
            """
            SELECT events.fallback_reason::text, failures.status::text,
                   failures.fallback_reason::text
            FROM app_private.interaction_events AS events
            JOIN app_private.failed_questions AS failures
              ON failures.interaction_event_id = events.id
            WHERE events.id = %s AND failures.id = %s
            """,
            (REPLAY_EVENT_ID, REPLAY_FAILURE_ID),
        ).fetchone()
        if lineage != (
            "INSUFFICIENT_GROUNDING",
            "REASON_CONFIRMED",
            "INSUFFICIENT_GROUNDING",
        ):
            raise AssertionError("REPLAY_CONFIRM_LINEAGE_INVALID")
        audit_count = fetch_count(
            replay,
            f"SELECT count(*) FROM app_private.audit_logs "
            f"WHERE target_id = '{REPLAY_FAILURE_ID}'::uuid "
            f"AND action = 'FAILED_QUESTION_REASON_CONFIRMED'",
        )
        if audit_count != 1:
            raise AssertionError("REPLAY_CONFIRM_AUDIT_COUNT_INVALID")

        cleanup(replay)


def run_probes(admin_dsn: str) -> int:
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
            workflow_available = fetch_count(
                read_committed,
                """
                SELECT (
                  pg_catalog.to_regprocedure(
                    'app_api.confirm_failed_question_reason(uuid,text,text,text)'
                  ) IS NOT NULL
                )::integer
                """,
            )
        finally:
            rollback_quietly(repeatable_read)
            cleanup(read_committed)

    if workflow_available:
        try:
            probe_replay_confirm_lock_order(admin_dsn)
        finally:
            with psycopg.connect(admin_dsn, autocommit=True) as cleanup_connection:
                cleanup(cleanup_connection)
    return 3 + workflow_available


def main() -> int:
    admin_dsn = os.environ.get("SEJONG_ADMIN_DATABASE_URL", "")
    if not admin_dsn.strip():
        print("[FAIL] step=DATABASE-CONCURRENCY reason=missing-admin-dsn code=2")
        return 2

    try:
        scenario_count = run_probes(admin_dsn)
    except psycopg.Error:
        print("[FAIL] step=DATABASE-CONCURRENCY reason=database code=1")
        return 1
    except (AssertionError, OSError, ValueError):
        print("[FAIL] step=DATABASE-CONCURRENCY reason=invariant code=1")
        return 1

    print(f"[PASS] step=DATABASE-CONCURRENCY scenarios={scenario_count} connections=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
