from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Awaitable
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

import psycopg
import pytest
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from sejong_ai_api.db.errors import (
    DatabaseRuleCode,
    DatabaseRuleError,
    DatabaseUnavailableError,
)
from sejong_ai_api.db.models import (
    Actor,
    AdminRole,
    AnswerStatus,
    CandidateDraft,
    DataOrigin,
    FallbackReason,
    Intent,
    InteractionWrite,
    Region,
)
from sejong_ai_api.db.pool import create_pool
from sejong_ai_api.db.repository import PsycopgSejongRepository, SejongRepository

pytestmark = pytest.mark.skipif(
    not os.getenv("SEJONG_DB_TEST_URL"),
    reason="local DB gate only",
)

_RepositoryPool = AsyncConnectionPool[AsyncConnection[dict[str, Any]]]

if os.name == "nt":
    _windows_selector_policy = cast(
        type[asyncio.AbstractEventLoopPolicy],
        asyncio.WindowsSelectorEventLoopPolicy,
    )
    asyncio.set_event_loop_policy(_windows_selector_policy())


@dataclass(slots=True)
class _OwnedRows:
    request_ids: set[UUID] = field(default_factory=set)
    failure_ids: set[UUID] = field(default_factory=set)
    candidate_ids: set[UUID] = field(default_factory=set)
    kb_public_ids: set[str] = field(default_factory=set)
    office_public_ids: set[str] = field(default_factory=set)


def _database_urls() -> tuple[str, str]:
    backend_url = os.getenv("SEJONG_DB_TEST_URL")
    admin_url = os.getenv("SEJONG_ADMIN_DATABASE_URL")
    if not backend_url:
        pytest.fail("BACKEND_DATABASE_URL_REQUIRED")
    if not admin_url:
        pytest.fail("ADMIN_DATABASE_URL_REQUIRED")
    return backend_url, admin_url


async def _open_pool(database_url: str, *, one_connection: bool = False) -> _RepositoryPool:
    pool = cast(_RepositoryPool, create_pool(database_url))
    pool_logger = logging.getLogger("psycopg.pool")
    logger_was_disabled = pool_logger.disabled
    pool_logger.disabled = True
    try:
        await pool.open(wait=True)
    except Exception:
        await pool.close()
        raise RuntimeError("BACKEND_POOL_OPEN_FAILED") from None
    finally:
        pool_logger.disabled = logger_was_disabled
    if one_connection:
        await pool.resize(1, 1)
    return pool


async def _admin_rows(
    database_url: str,
    statement: str,
    parameters: tuple[object, ...] = (),
) -> list[dict[str, Any]]:
    connection: AsyncConnection[dict[str, Any]] | None = None
    try:
        connection = await AsyncConnection.connect(
            database_url,
            autocommit=False,
            row_factory=dict_row,
        )
        async with connection.transaction(), connection.cursor() as cursor:
            await cursor.execute(statement, parameters)
            if cursor.description is None:
                return []
            return await cursor.fetchall()
    except psycopg.Error:
        raise RuntimeError("ADMIN_FIXTURE_OPERATION_FAILED") from None
    finally:
        if connection is not None:
            await connection.close()


async def _admin_transaction(
    database_url: str,
    operations: list[tuple[str, tuple[object, ...]]],
) -> None:
    connection: AsyncConnection[dict[str, Any]] | None = None
    try:
        connection = await AsyncConnection.connect(
            database_url,
            autocommit=False,
            row_factory=dict_row,
        )
        async with connection.transaction(), connection.cursor() as cursor:
            for statement, parameters in operations:
                await cursor.execute(statement, parameters)
    except psycopg.Error:
        raise RuntimeError("ADMIN_FIXTURE_OPERATION_FAILED") from None
    finally:
        if connection is not None:
            await connection.close()


async def _backend[Result](operation: Awaitable[Result]) -> Result:
    try:
        return await operation
    except DatabaseUnavailableError:
        raise RuntimeError("BACKEND_DATABASE_OPERATION_FAILED") from None


async def _cleanup(database_url: str, owned: _OwnedRows) -> None:
    request_ids = list(owned.request_ids)
    failure_ids = list(owned.failure_ids)
    candidate_ids = list(owned.candidate_ids)
    kb_public_ids = list(owned.kb_public_ids)
    office_public_ids = list(owned.office_public_ids)

    if request_ids:
        rows = await _admin_rows(
            database_url,
            """
            SELECT failures.id
            FROM app_private.failed_questions AS failures
            JOIN app_private.interaction_events AS events
              ON events.id = failures.interaction_event_id
            WHERE events.request_id = ANY(%s)
            """,
            (request_ids,),
        )
        failure_ids.extend(
            cast(UUID, row["id"]) for row in rows if cast(UUID, row["id"]) not in failure_ids
        )

    if failure_ids:
        rows = await _admin_rows(
            database_url,
            """
            SELECT candidates.id, candidates.activated_kb_id
            FROM app_private.kb_candidates AS candidates
            WHERE candidates.failed_question_id = ANY(%s)
            """,
            (failure_ids,),
        )
        candidate_ids.extend(
            cast(UUID, row["id"]) for row in rows if cast(UUID, row["id"]) not in candidate_ids
        )
        activated_kb_ids = [
            cast(UUID, row["activated_kb_id"]) for row in rows if row["activated_kb_id"] is not None
        ]
    else:
        activated_kb_ids = []

    operations: list[tuple[str, tuple[object, ...]]] = []
    target_ids = [*failure_ids, *candidate_ids]
    if target_ids:
        operations.append(
            (
                "DELETE FROM app_private.audit_logs WHERE target_id = ANY(%s)",
                (target_ids,),
            )
        )
    if activated_kb_ids or kb_public_ids:
        operations.append(
            (
                """
                DELETE FROM app_private.kb_question_examples
                WHERE kb_document_id = ANY(%s)
                   OR kb_document_id IN (
                     SELECT id FROM app_private.kb_documents WHERE public_id = ANY(%s)
                   )
                """,
                (activated_kb_ids, kb_public_ids),
            )
        )
    if candidate_ids:
        operations.append(
            (
                "DELETE FROM app_private.kb_candidates WHERE id = ANY(%s)",
                (candidate_ids,),
            )
        )
    if activated_kb_ids or kb_public_ids:
        operations.append(
            (
                """
                DELETE FROM app_private.kb_documents
                WHERE id = ANY(%s) OR public_id = ANY(%s)
                """,
                (activated_kb_ids, kb_public_ids),
            )
        )
    if failure_ids:
        operations.append(
            (
                "DELETE FROM app_private.failed_questions WHERE id = ANY(%s)",
                (failure_ids,),
            )
        )
    if request_ids:
        operations.append(
            (
                "DELETE FROM app_private.interaction_events WHERE request_id = ANY(%s)",
                (request_ids,),
            )
        )
    if office_public_ids:
        operations.append(
            (
                """
                DELETE FROM app_private.office_service_mappings
                WHERE office_id IN (
                  SELECT id FROM app_private.offices WHERE public_id = ANY(%s)
                )
                """,
                (office_public_ids,),
            )
        )
        operations.append(
            (
                "DELETE FROM app_private.offices WHERE public_id = ANY(%s)",
                (office_public_ids,),
            )
        )
    if operations:
        await _admin_transaction(database_url, operations)


def _interaction(request_id: UUID, *, response_time_ms: int = 37) -> InteractionWrite:
    return InteractionWrite(
        request_id=request_id,
        intent=Intent.MOVE_IN_RESIDENT_REGISTRATION,
        answer_status=AnswerStatus.FALLBACK,
        fallback_reason=FallbackReason.INSUFFICIENT_GROUNDING,
        used_source_ids=(),
        response_time_ms=response_time_ms,
        selected_region=None,
        routed_office_public_id=None,
        is_test=True,
        masked_question="[MASKED] 시연용 샘플 전입 절차 근거 부족 질문",
    )


def _operator(prefix: str) -> Actor:
    return Actor(f"operator-{prefix}-{uuid4().hex}", AdminRole.OPERATOR)


def _approver(prefix: str) -> Actor:
    return Actor(f"approver-{prefix}-{uuid4().hex}", AdminRole.APPROVER)


def _candidate(failure_id: UUID, actor: Actor, prefix: str) -> CandidateDraft:
    return CandidateDraft(
        failed_question_id=failure_id,
        actor=actor,
        title=f"시연용 샘플 전입 안내 {prefix}",
        representative_question=f"시연용 샘플 전입 절차는 무엇인가요 {prefix}",
        category=Intent.MOVE_IN_RESIDENT_REGISTRATION,
        answer_summary="시연용 샘플 공식 절차 안내입니다.",
        procedure_steps=("시연용 샘플 신청서 작성", "시연용 샘플 제출"),
        required_documents=("시연용 샘플 신분증",),
        processing_time="시연용 샘플 즉시",
        fee="시연용 샘플 무료",
        department="시연용 샘플 민원행정팀",
        source_title="시연용 샘플 공식 안내",
        source_url="https://example.invalid/sejong-task-9",
        last_verified_at=date(2026, 7, 17),
        caution=None,
        data_origin=DataOrigin.OFFICIAL,
    )


def _rule_errors(results: list[object]) -> list[DatabaseRuleError]:
    return [result for result in results if isinstance(result, DatabaseRuleError)]


@pytest.mark.asyncio
async def test_identical_request_replay_writes_one_event() -> None:
    backend_url, admin_url = _database_urls()
    owned = _OwnedRows()
    request_id = uuid4()
    owned.request_ids.add(request_id)
    pool = await _open_pool(backend_url)
    try:
        repository = PsycopgSejongRepository(pool)
        event = _interaction(request_id)

        first = await _backend(repository.record_interaction(event))
        second = await _backend(repository.record_interaction(event))

        assert first.interaction_id == second.interaction_id
        assert first.failed_question_id == second.failed_question_id
        assert first.failed_question_id is not None
        rows = await _admin_rows(
            admin_url,
            """
            SELECT
              count(DISTINCT events.id)::integer AS event_count,
              count(failures.id)::integer AS failure_count
            FROM app_private.interaction_events AS events
            LEFT JOIN app_private.failed_questions AS failures
              ON failures.interaction_event_id = events.id
            WHERE events.request_id = %s
            """,
            (request_id,),
        )
        assert rows[0]["event_count"] == 1
        assert rows[0]["failure_count"] == 1
    finally:
        await pool.close()
        await _cleanup(admin_url, owned)


@pytest.mark.asyncio
async def test_conflicting_request_replay_maps_p1010() -> None:
    backend_url, admin_url = _database_urls()
    owned = _OwnedRows()
    request_id = uuid4()
    owned.request_ids.add(request_id)
    pool = await _open_pool(backend_url)
    try:
        repository = PsycopgSejongRepository(pool)
        event = _interaction(request_id)
        await _backend(repository.record_interaction(event))

        with pytest.raises(DatabaseRuleError) as captured:
            await _backend(repository.record_interaction(replace(event, response_time_ms=38)))

        assert captured.value.code is DatabaseRuleCode.INVALID_INTERACTION
        assert str(captured.value) == DatabaseRuleCode.INVALID_INTERACTION.value
        rows = await _admin_rows(
            admin_url,
            """
            SELECT
              count(DISTINCT events.id)::integer AS event_count,
              count(failures.id)::integer AS failure_count
            FROM app_private.interaction_events AS events
            LEFT JOIN app_private.failed_questions AS failures
              ON failures.interaction_event_id = events.id
            WHERE events.request_id = %s
            """,
            (request_id,),
        )
        assert rows[0]["event_count"] == 1
        assert rows[0]["failure_count"] == 1
    finally:
        await pool.close()
        await _cleanup(admin_url, owned)


@pytest.mark.asyncio
async def test_two_concurrent_reason_confirmations_write_one_audit() -> None:
    backend_url, admin_url = _database_urls()
    owned = _OwnedRows()
    request_id = uuid4()
    owned.request_ids.add(request_id)
    setup_pool = await _open_pool(backend_url)
    first_pool: _RepositoryPool | None = None
    second_pool: _RepositoryPool | None = None
    try:
        created = await _backend(
            PsycopgSejongRepository(setup_pool).record_interaction(_interaction(request_id))
        )
        assert created.failed_question_id is not None
        failure_id = created.failed_question_id
        actor = _operator("confirm")
        first_pool = await _open_pool(backend_url, one_connection=True)
        second_pool = await _open_pool(backend_url, one_connection=True)
        release = asyncio.Event()

        async def confirm(pool: _RepositoryPool) -> None:
            await asyncio.wait_for(release.wait(), timeout=5)
            await _backend(
                PsycopgSejongRepository(pool).confirm_failed_question_reason(
                    failure_id,
                    actor,
                    FallbackReason.INSUFFICIENT_GROUNDING,
                )
            )

        tasks = [
            asyncio.create_task(confirm(first_pool)),
            asyncio.create_task(confirm(second_pool)),
        ]
        release.set()
        results = cast(list[object], await asyncio.gather(*tasks, return_exceptions=True))

        errors = _rule_errors(results)
        if any(
            isinstance(result, BaseException) and not isinstance(result, DatabaseRuleError)
            for result in results
        ):
            raise RuntimeError("BACKEND_CONFIRMATION_FAILED") from None
        assert sum(result is None for result in results) == 1
        assert len(errors) == 1
        assert errors[0].code is DatabaseRuleCode.INVALID_CANDIDATE_STATE
        assert str(errors[0]) == DatabaseRuleCode.INVALID_CANDIDATE_STATE.value
        rows = await _admin_rows(
            admin_url,
            """
            SELECT
              failures.status::text AS status,
              failures.fallback_reason::text AS confirmed_reason,
              failures.candidate_eligible,
              events.fallback_reason::text AS event_reason,
              count(audits.id)::integer AS audit_count
            FROM app_private.failed_questions AS failures
            JOIN app_private.interaction_events AS events
              ON events.id = failures.interaction_event_id
            LEFT JOIN app_private.audit_logs AS audits
              ON audits.target_id = failures.id
             AND audits.action = 'FAILED_QUESTION_REASON_CONFIRMED'
            WHERE failures.id = %s
            GROUP BY failures.id, events.id
            """,
            (failure_id,),
        )
        assert rows[0]["status"] == "REASON_CONFIRMED"
        assert rows[0]["confirmed_reason"] == "INSUFFICIENT_GROUNDING"
        assert rows[0]["candidate_eligible"] is True
        assert rows[0]["event_reason"] == "INSUFFICIENT_GROUNDING"
        assert rows[0]["audit_count"] == 1
    finally:
        if first_pool is not None:
            await first_pool.close()
        if second_pool is not None:
            await second_pool.close()
        await setup_pool.close()
        await _cleanup(admin_url, owned)


@pytest.mark.asyncio
async def test_candidate_creation_requires_confirmed_reason() -> None:
    backend_url, admin_url = _database_urls()
    owned = _OwnedRows()
    request_id = uuid4()
    owned.request_ids.add(request_id)
    pool = await _open_pool(backend_url)
    try:
        repository = PsycopgSejongRepository(pool)
        created = await _backend(repository.record_interaction(_interaction(request_id)))
        assert created.failed_question_id is not None
        failure_id = created.failed_question_id
        actor = _operator("candidate")
        draft = _candidate(failure_id, actor, uuid4().hex)

        with pytest.raises(DatabaseRuleError) as captured:
            await _backend(repository.create_kb_candidate(draft))
        assert captured.value.code is DatabaseRuleCode.INVALID_CANDIDATE_STATE
        assert str(captured.value) == DatabaseRuleCode.INVALID_CANDIDATE_STATE.value

        await _backend(
            repository.confirm_failed_question_reason(
                failure_id,
                actor,
                FallbackReason.INSUFFICIENT_GROUNDING,
            )
        )
        candidate_id = await _backend(repository.create_kb_candidate(draft))
        owned.candidate_ids.add(candidate_id)
        rows = await _admin_rows(
            admin_url,
            """
            SELECT
              count(DISTINCT candidates.id)::integer AS candidate_count,
              count(audits.id) FILTER (
                WHERE audits.action = 'FAILED_QUESTION_REASON_CONFIRMED'
              )::integer AS confirmation_audits,
              count(audits.id) FILTER (
                WHERE audits.action = 'CANDIDATE_CREATED'
              )::integer AS creation_audits
            FROM app_private.failed_questions AS failures
            LEFT JOIN app_private.kb_candidates AS candidates
              ON candidates.failed_question_id = failures.id
            LEFT JOIN app_private.audit_logs AS audits
              ON audits.target_id IN (failures.id, candidates.id)
            WHERE failures.id = %s
            """,
            (failure_id,),
        )
        assert rows[0]["candidate_count"] == 1
        assert rows[0]["confirmation_audits"] == 1
        assert rows[0]["creation_audits"] == 1
    finally:
        await pool.close()
        await _cleanup(admin_url, owned)


@pytest.mark.asyncio
async def test_two_concurrent_approvals_create_one_active_kb_and_audit() -> None:
    backend_url, admin_url = _database_urls()
    owned = _OwnedRows()
    request_id = uuid4()
    owned.request_ids.add(request_id)
    setup_pool = await _open_pool(backend_url)
    first_pool: _RepositoryPool | None = None
    second_pool: _RepositoryPool | None = None
    try:
        repository = PsycopgSejongRepository(setup_pool)
        created = await _backend(repository.record_interaction(_interaction(request_id)))
        assert created.failed_question_id is not None
        failure_id = created.failed_question_id
        author = _operator("approval")
        await _backend(
            repository.confirm_failed_question_reason(
                failure_id,
                author,
                FallbackReason.INSUFFICIENT_GROUNDING,
            )
        )
        candidate_id = await _backend(
            repository.create_kb_candidate(_candidate(failure_id, author, uuid4().hex))
        )
        owned.candidate_ids.add(candidate_id)
        await _backend(repository.submit_kb_candidate(candidate_id, author))

        first_pool = await _open_pool(backend_url, one_connection=True)
        second_pool = await _open_pool(backend_url, one_connection=True)
        release = asyncio.Event()
        approvers = (_approver("first"), _approver("second"))

        async def approve(pool: _RepositoryPool, actor: Actor) -> str:
            await asyncio.wait_for(release.wait(), timeout=5)
            return await _backend(
                PsycopgSejongRepository(pool).approve_kb_candidate(
                    candidate_id,
                    actor,
                    "시연용 샘플 공식 출처 검수 완료",
                )
            )

        tasks = [
            asyncio.create_task(approve(first_pool, approvers[0])),
            asyncio.create_task(approve(second_pool, approvers[1])),
        ]
        release.set()
        results = cast(list[object], await asyncio.gather(*tasks, return_exceptions=True))

        public_ids = [result for result in results if isinstance(result, str)]
        errors = _rule_errors(results)
        assert not any(
            isinstance(result, BaseException) and not isinstance(result, DatabaseRuleError)
            for result in results
        ), "UNEXPECTED_BACKEND_APPROVAL_ERROR"
        assert len(public_ids) == 1
        assert len(errors) == 1
        assert errors[0].code is DatabaseRuleCode.INVALID_CANDIDATE_STATE
        assert str(errors[0]) == DatabaseRuleCode.INVALID_CANDIDATE_STATE.value
        owned.kb_public_ids.add(public_ids[0])
        rows = await _admin_rows(
            admin_url,
            """
            SELECT
              candidates.review_status::text AS review_status,
              count(DISTINCT kb.id)::integer AS kb_count,
              count(DISTINCT questions.id)::integer AS question_count,
              count(DISTINCT candidates.activated_kb_id)::integer AS link_count,
              count(DISTINCT audits.id)::integer AS approval_audit_count,
              min(kb.public_id)::text AS linked_public_id,
              bool_and(kb.status = 'ACTIVE' AND kb.data_origin = 'OFFICIAL') AS valid_kb
            FROM app_private.kb_candidates AS candidates
            LEFT JOIN app_private.kb_documents AS kb
              ON kb.id = candidates.activated_kb_id
            LEFT JOIN app_private.kb_question_examples AS questions
              ON questions.kb_document_id = kb.id
            LEFT JOIN app_private.audit_logs AS audits
              ON audits.target_id = candidates.id
             AND audits.action = 'CANDIDATE_APPROVED'
            WHERE candidates.id = %s
            GROUP BY candidates.id
            """,
            (candidate_id,),
        )
        assert rows[0]["review_status"] == "APPROVED"
        assert rows[0]["kb_count"] == 1
        assert rows[0]["question_count"] == 1
        assert rows[0]["link_count"] == 1
        assert rows[0]["approval_audit_count"] == 1
        assert rows[0]["linked_public_id"] == public_ids[0]
        assert rows[0]["valid_kb"] is True
    finally:
        if first_pool is not None:
            await first_pool.close()
        if second_pool is not None:
            await second_pool.close()
        await setup_pool.close()
        await _cleanup(admin_url, owned)


@pytest.mark.asyncio
async def test_purge_boundary_is_exact_and_idempotent() -> None:
    backend_url, admin_url = _database_urls()
    owned = _OwnedRows()
    cutoff = datetime(2030, 1, 15, 12, 0, tzinfo=UTC)
    expiries = (cutoff - timedelta(microseconds=1), cutoff, cutoff + timedelta(microseconds=1))
    failure_ids = [uuid4(), uuid4(), uuid4()]
    request_ids = [uuid4(), uuid4(), uuid4()]
    owned.failure_ids.update(failure_ids)
    owned.request_ids.update(request_ids)
    pool = await _open_pool(backend_url)
    try:
        for failure_id, request_id, expiry in zip(failure_ids, request_ids, expiries, strict=True):
            event_rows = await _admin_rows(
                admin_url,
                """
                INSERT INTO app_private.interaction_events (
                  intent, answer_status, fallback_reason, source_count, used_source_ids,
                  response_time_ms, selected_region, routed_office_id, is_test, request_id
                ) VALUES (
                  'MOVE_IN_RESIDENT_REGISTRATION', 'FALLBACK',
                  'INSUFFICIENT_GROUNDING', 0, '[]'::jsonb,
                  1, NULL, NULL, true, %s
                ) RETURNING id
                """,
                (request_id,),
            )
            await _admin_rows(
                admin_url,
                """
                INSERT INTO app_private.failed_questions (
                  id, interaction_event_id, masked_question, intent, fallback_reason,
                  candidate_eligible, status, created_at, text_expires_at, updated_at
                ) VALUES (
                  %s, %s, %s, 'MOVE_IN_RESIDENT_REGISTRATION',
                  'INSUFFICIENT_GROUNDING', true, 'NEW', %s, %s, %s
                )
                """,
                (
                    failure_id,
                    event_rows[0]["id"],
                    "[MASKED] 시연용 샘플 보관 경계 질문",
                    expiry - timedelta(days=30),
                    expiry,
                    expiry - timedelta(days=30),
                ),
            )

        first = await _admin_rows(
            admin_url,
            "SELECT * FROM app_private.purge_expired_failed_question_text_at(%s)",
            (cutoff,),
        )
        assert first[0]["purged_count"] == 2
        assert tuple(first[0]["purged_ids"]) == tuple(sorted(failure_ids[:2]))
        second = await _admin_rows(
            admin_url,
            "SELECT * FROM app_private.purge_expired_failed_question_text_at(%s)",
            (cutoff,),
        )
        assert second[0]["purged_count"] == 0
        assert second[0]["purged_ids"] == []

        state = await _admin_rows(
            admin_url,
            """
            SELECT
              count(*)::integer AS row_count,
              count(*) FILTER (
                WHERE id = ANY(%s) AND masked_question IS NULL
                  AND text_purged_at IS NOT NULL
              )::integer AS purged_count,
              count(*) FILTER (
                WHERE id = %s AND masked_question IS NOT NULL
                  AND text_purged_at IS NULL
              )::integer AS retained_count,
              count(DISTINCT interaction_event_id)::integer AS event_link_count
            FROM app_private.failed_questions
            WHERE id = ANY(%s)
            """,
            (failure_ids[:2], failure_ids[2], failure_ids),
        )
        assert state[0]["row_count"] == 3
        assert state[0]["purged_count"] == 2
        assert state[0]["retained_count"] == 1
        assert state[0]["event_link_count"] == 3

        public_result = await _backend(
            PsycopgSejongRepository(pool).purge_expired_failed_question_text()
        )
        assert public_result.purged_count == 0
        assert public_result.purged_ids == ()
    finally:
        await pool.close()
        await _cleanup(admin_url, owned)


@pytest.mark.asyncio
async def test_backend_login_cannot_select_private_tables() -> None:
    backend_url, _admin_url = _database_urls()
    connection: AsyncConnection[tuple[Any, ...]] | None = None
    pool = cast(_RepositoryPool, create_pool(backend_url))
    try:
        connection = await AsyncConnection.connect(backend_url, autocommit=False)
        try:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT count(*) FROM app_private.failed_questions")
        except psycopg.Error as error:
            assert error.sqlstate == "42501"
            await connection.rollback()
        else:
            pytest.fail("PRIVATE_TABLE_ACCESS_NOT_DENIED")

        adapter: SejongRepository = PsycopgSejongRepository(pool)
        assert not hasattr(adapter, "execute")
        assert not hasattr(adapter, "query")
        assert not hasattr(adapter, "cursor")
    finally:
        if connection is not None:
            await connection.close()
        await pool.close()


@pytest.mark.asyncio
async def test_mock_and_non_active_rows_never_reach_citizen_reads() -> None:
    backend_url, admin_url = _database_urls()
    owned = _OwnedRows()
    request_id = uuid4()
    owned.request_ids.add(request_id)
    pool = await _open_pool(backend_url)
    try:
        repository = PsycopgSejongRepository(pool)
        created = await _backend(repository.record_interaction(_interaction(request_id)))
        assert created.failed_question_id is not None
        author = _operator("read-filter")
        await _backend(
            repository.confirm_failed_question_reason(
                created.failed_question_id,
                author,
                FallbackReason.INSUFFICIENT_GROUNDING,
            )
        )
        candidate_id = await _backend(
            repository.create_kb_candidate(
                _candidate(created.failed_question_id, author, uuid4().hex)
            )
        )
        owned.candidate_ids.add(candidate_id)
        await _backend(repository.submit_kb_candidate(candidate_id, author))
        active_public_id = await _backend(
            repository.approve_kb_candidate(
                candidate_id,
                _approver("read-filter"),
                "시연용 샘플 시민 읽기 검수 완료",
            )
        )
        owned.kb_public_ids.add(active_public_id)

        excluded_rows = (
            (f"T9-OFFICIAL-DRAFT-{uuid4().hex}", "DRAFT", "OFFICIAL"),
            (f"T9-OFFICIAL-PENDING-{uuid4().hex}", "PENDING", "OFFICIAL"),
            (f"T9-OFFICIAL-RETIRED-{uuid4().hex}", "RETIRED", "OFFICIAL"),
            (f"T9-OFFICIAL-REJECTED-{uuid4().hex}", "REJECTED", "OFFICIAL"),
            (f"T9-MOCK-DRAFT-{uuid4().hex}", "DRAFT", "MOCK"),
        )
        excluded_ids = {public_id for public_id, _status, _origin in excluded_rows}
        owned.kb_public_ids.update(excluded_ids)
        for public_id, status, origin in excluded_rows:
            await _admin_rows(
                admin_url,
                """
                INSERT INTO app_private.kb_documents (
                  public_id, data_origin, category, service_name, answer_summary,
                  procedure_steps, required_documents, department, source_title,
                  source_url, last_verified_at, status, created_by
                ) VALUES (
                  %s, %s, 'MOVE_IN_RESIDENT_REGISTRATION', %s, %s,
                  '[]'::jsonb, '[]'::jsonb, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    public_id,
                    origin,
                    "시연용 샘플 제외 서비스",
                    "시연용 샘플 제외 답변",
                    "시연용 샘플 부서",
                    "시연용 샘플 출처",
                    "https://example.invalid/sejong-task-9-excluded",
                    date(2026, 7, 17),
                    status,
                    f"fixture-{uuid4().hex}",
                ),
            )

        official_office_id = f"T9-OFFICE-OFFICIAL-{uuid4().hex}"
        mock_office_id = f"T9-OFFICE-MOCK-{uuid4().hex}"
        owned.office_public_ids.update((official_office_id, mock_office_id))
        for public_id, origin in (
            (official_office_id, "OFFICIAL"),
            (mock_office_id, "MOCK"),
        ):
            rows = await _admin_rows(
                admin_url,
                """
                INSERT INTO app_private.offices (
                  public_id, data_origin, region, office_name, address, phone,
                  source_title, source_url, last_verified_at
                ) VALUES (%s, %s, '아름동', %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    public_id,
                    origin,
                    "시연용 샘플 행정복지센터",
                    "시연용 샘플 세종시 주소",
                    "044-000-0000",
                    "시연용 샘플 기관 안내",
                    "https://example.invalid/sejong-task-9-office",
                    date(2026, 7, 17),
                ),
            )
            await _admin_rows(
                admin_url,
                """
                INSERT INTO app_private.office_service_mappings (
                  office_id, intent, department_label
                ) VALUES (%s, 'MOVE_IN_RESIDENT_REGISTRATION', %s)
                """,
                (rows[0]["id"], "시연용 샘플 민원행정팀"),
            )

        knowledge = await _backend(repository.list_active_kb(Intent.MOVE_IN_RESIDENT_REGISTRATION))
        offices = await _backend(
            repository.list_offices(
                Region.AREUM_DONG,
                Intent.MOVE_IN_RESIDENT_REGISTRATION,
            )
        )
        knowledge_ids = tuple(item.public_id for item in knowledge)
        office_ids = tuple(item.public_id for item in offices)

        assert type(knowledge) is tuple
        assert type(offices) is tuple
        assert knowledge_ids == tuple(sorted(knowledge_ids))
        assert office_ids == tuple(sorted(office_ids))
        assert active_public_id in knowledge_ids
        assert excluded_ids.isdisjoint(knowledge_ids)
        assert official_office_id in office_ids
        assert mock_office_id not in office_ids
        assert all(not hasattr(item, "data_origin") for item in knowledge)
        assert all(not hasattr(item, "status") for item in knowledge)
        assert all(not hasattr(item, "id") for item in (*knowledge, *offices))
    finally:
        await pool.close()
        await _cleanup(admin_url, owned)
