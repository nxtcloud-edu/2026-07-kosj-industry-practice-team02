"""Fixed-statement asynchronous adapter for the private database capability API."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any, Protocol
from uuid import UUID

import psycopg
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from sejong_ai_api.db.errors import DatabaseUnavailableError, map_database_error
from sejong_ai_api.db.models import (
    Actor,
    AdminRole,
    CandidateDraft,
    FailureReasonConfirmation,
    FallbackReason,
    Intent,
    InteractionWrite,
    InteractionWriteResult,
    KnowledgeRecord,
    OfficeRecord,
    PurgeResult,
    Region,
)

LIST_ACTIVE_KB_SQL = "SELECT * FROM app_api.list_active_kb(%s)"
LIST_OFFICES_SQL = "SELECT * FROM app_api.list_offices(%s, %s)"
RECORD_INTERACTION_SQL = (
    "SELECT * FROM app_api.record_interaction(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
)
CONFIRM_FAILED_QUESTION_REASON_SQL = "SELECT app_api.confirm_failed_question_reason(%s, %s, %s, %s)"
CREATE_KB_CANDIDATE_SQL = (
    "SELECT app_api.create_kb_candidate(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
    "%s, %s, %s, %s, %s, %s, %s)"
)
SUBMIT_KB_CANDIDATE_SQL = "SELECT app_api.submit_kb_candidate(%s, %s, %s)"
APPROVE_KB_CANDIDATE_SQL = "SELECT app_api.approve_kb_candidate(%s, %s, %s, %s)"
REJECT_KB_CANDIDATE_SQL = "SELECT app_api.reject_kb_candidate(%s, %s, %s, %s)"
PURGE_EXPIRED_FAILED_QUESTION_TEXT_SQL = (
    "SELECT * FROM app_api.purge_expired_failed_question_text()"
)

_SUPPORTED_INTENTS = frozenset(
    {
        Intent.MOVE_IN_RESIDENT_REGISTRATION,
        Intent.CERTIFICATE_ISSUANCE,
        Intent.BULKY_WASTE,
        Intent.LOCAL_TAX_GENERAL,
    }
)
_CONFIRMABLE_REASONS = frozenset(
    {
        FallbackReason.INSUFFICIENT_GROUNDING,
        FallbackReason.PERSONAL_LOOKUP,
        FallbackReason.LEGAL_JUDGMENT,
    }
)


class SejongRepository(Protocol):
    async def list_active_kb(self, intent: Intent) -> Sequence[KnowledgeRecord]: ...

    async def list_offices(self, region: Region, intent: Intent) -> Sequence[OfficeRecord]: ...

    async def record_interaction(self, event: InteractionWrite) -> InteractionWriteResult: ...

    async def confirm_failed_question_reason(
        self,
        failed_question_id: UUID,
        actor: Actor,
        fallback_reason: FallbackReason,
    ) -> None: ...

    async def create_kb_candidate(self, draft: CandidateDraft) -> UUID: ...

    async def submit_kb_candidate(self, candidate_id: UUID, actor: Actor) -> None: ...

    async def approve_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> str: ...

    async def reject_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> None: ...

    async def purge_expired_failed_question_text(self) -> PurgeResult: ...


def _require_supported_intent(intent: object) -> Intent:
    if type(intent) is not Intent or intent not in _SUPPORTED_INTENTS:
        raise ValueError("CATEGORY_INVALID")
    return intent


def _require_region(region: object) -> Region:
    if type(region) is not Region:
        raise ValueError("REGION_INVALID")
    return region


def _require_uuid(value: object, message: str) -> UUID:
    if type(value) is not UUID:
        raise ValueError(message)
    return value


def _require_actor(actor: object, expected_role: AdminRole) -> Actor:
    if type(actor) is not Actor or actor.role is not expected_role:
        raise ValueError("ACTOR_ROLE_FORBIDDEN")
    return actor


def _require_review_comment(value: object) -> str:
    if type(value) is not str or not value or value.strip() != value or len(value) > 1000:
        raise ValueError("REVIEW_COMMENT_INVALID")
    return value


def _required_text(value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("MALFORMED_DATABASE_RESULT")
    return value


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    return _required_text(value)


def _required_uuid(value: object) -> UUID:
    if type(value) is not UUID:
        raise ValueError("MALFORMED_DATABASE_RESULT")
    return value


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    return _required_uuid(value)


def _required_date(value: object) -> date:
    if type(value) is not date:
        raise ValueError("MALFORMED_DATABASE_RESULT")
    return value


def _text_array(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("MALFORMED_DATABASE_RESULT")
    return tuple(_required_text(item) for item in value)


def _uuid_array(value: object) -> tuple[UUID, ...]:
    if type(value) is not list:
        raise ValueError("MALFORMED_DATABASE_RESULT")
    return tuple(_required_uuid(item) for item in value)


def _knowledge_record(row: dict[str, Any]) -> KnowledgeRecord:
    return KnowledgeRecord(
        public_id=_required_text(row["public_id"]),
        category=Intent(_required_text(row["category"])),
        service_name=_required_text(row["service_name"]),
        answer_summary=_required_text(row["answer_summary"]),
        procedure_steps=_text_array(row["procedure_steps"]),
        required_documents=_text_array(row["required_documents"]),
        processing_time=_optional_text(row["processing_time"]),
        fee=_optional_text(row["fee"]),
        department=_required_text(row["department"]),
        source_title=_required_text(row["source_title"]),
        source_url=_required_text(row["source_url"]),
        last_verified_at=_required_date(row["last_verified_at"]),
        caution=_optional_text(row["caution"]),
        question_examples=_text_array(row["question_examples"]),
    )


def _office_record(row: dict[str, Any]) -> OfficeRecord:
    return OfficeRecord(
        public_id=_required_text(row["public_id"]),
        region=Region(_required_text(row["region"])),
        office_name=_required_text(row["office_name"]),
        address=_required_text(row["address"]),
        phone=_required_text(row["phone"]),
        opening_hours=_optional_text(row["opening_hours"]),
        map_url=_optional_text(row["map_url"]),
        department_label=_optional_text(row["department_label"]),
        source_title=_required_text(row["source_title"]),
        source_url=_required_text(row["source_url"]),
        last_verified_at=_required_date(row["last_verified_at"]),
    )


def _safe_knowledge_records(rows: list[dict[str, Any]]) -> tuple[KnowledgeRecord, ...]:
    try:
        return tuple(_knowledge_record(row) for row in rows)
    except (KeyError, TypeError, ValueError):
        raise DatabaseUnavailableError() from None


def _safe_office_records(rows: list[dict[str, Any]]) -> tuple[OfficeRecord, ...]:
    try:
        return tuple(_office_record(row) for row in rows)
    except (KeyError, TypeError, ValueError):
        raise DatabaseUnavailableError() from None


class PsycopgSejongRepository:
    def __init__(
        self,
        pool: AsyncConnectionPool[AsyncConnection[dict[str, Any]]],
    ) -> None:
        self._pool = pool

    async def list_active_kb(self, intent: Intent) -> tuple[KnowledgeRecord, ...]:
        valid_intent = _require_supported_intent(intent)
        try:
            async with (
                self._pool.connection() as connection,
                connection.cursor(row_factory=dict_row) as cursor,
            ):
                await cursor.execute(LIST_ACTIVE_KB_SQL, (valid_intent.value,))
                rows = await cursor.fetchall()
        except psycopg.Error as exc:
            raise map_database_error(exc) from exc
        return _safe_knowledge_records(rows)

    async def list_offices(self, region: Region, intent: Intent) -> tuple[OfficeRecord, ...]:
        valid_region = _require_region(region)
        valid_intent = _require_supported_intent(intent)
        try:
            async with (
                self._pool.connection() as connection,
                connection.cursor(row_factory=dict_row) as cursor,
            ):
                await cursor.execute(LIST_OFFICES_SQL, (valid_region.value, valid_intent.value))
                rows = await cursor.fetchall()
        except psycopg.Error as exc:
            raise map_database_error(exc) from exc
        return _safe_office_records(rows)

    async def record_interaction(self, event: InteractionWrite) -> InteractionWriteResult:
        if type(event) is not InteractionWrite:
            raise ValueError("INTERACTION_INVALID")
        parameters = (
            event.request_id,
            event.intent.value,
            event.answer_status.value,
            event.fallback_reason.value if event.fallback_reason is not None else None,
            list(event.used_source_ids),
            event.response_time_ms,
            event.selected_region.value if event.selected_region is not None else None,
            event.routed_office_public_id,
            event.is_test,
            event.masked_question,
        )
        try:
            async with (
                self._pool.connection() as connection,
                connection.transaction(),
                connection.cursor(row_factory=dict_row) as cursor,
            ):
                await cursor.execute(RECORD_INTERACTION_SQL, parameters)
                rows = await cursor.fetchall()
                result = self._interaction_result(rows)
        except psycopg.Error as exc:
            raise map_database_error(exc) from exc
        return result

    async def confirm_failed_question_reason(
        self,
        failed_question_id: UUID,
        actor: Actor,
        fallback_reason: FallbackReason,
    ) -> None:
        valid_id = _require_uuid(failed_question_id, "FAILED_QUESTION_ID_INVALID")
        valid_actor = _require_actor(actor, AdminRole.OPERATOR)
        if (
            type(fallback_reason) is not FallbackReason
            or fallback_reason not in _CONFIRMABLE_REASONS
        ):
            raise ValueError("FALLBACK_REASON_INVALID")
        confirmation = FailureReasonConfirmation(valid_id, valid_actor, fallback_reason)
        await self._execute_void_write(
            CONFIRM_FAILED_QUESTION_REASON_SQL,
            (
                confirmation.failed_question_id,
                confirmation.actor.actor_id,
                confirmation.actor.role.value,
                confirmation.fallback_reason.value,
            ),
        )

    async def create_kb_candidate(self, draft: CandidateDraft) -> UUID:
        if type(draft) is not CandidateDraft:
            raise ValueError("CANDIDATE_DRAFT_INVALID")
        parameters = (
            draft.failed_question_id,
            draft.actor.actor_id,
            draft.actor.role.value,
            draft.title,
            draft.representative_question,
            draft.category.value,
            draft.answer_summary,
            Jsonb(list(draft.procedure_steps)),
            Jsonb(list(draft.required_documents)),
            draft.processing_time,
            draft.fee,
            draft.department,
            draft.source_title,
            draft.source_url,
            draft.last_verified_at,
            draft.caution,
            draft.data_origin.value,
        )
        try:
            async with (
                self._pool.connection() as connection,
                connection.transaction(),
                connection.cursor(row_factory=dict_row) as cursor,
            ):
                await cursor.execute(CREATE_KB_CANDIDATE_SQL, parameters)
                rows = await cursor.fetchall()
                result = self._scalar_uuid(rows, "create_kb_candidate")
        except psycopg.Error as exc:
            raise map_database_error(exc) from exc
        return result

    async def submit_kb_candidate(self, candidate_id: UUID, actor: Actor) -> None:
        valid_id = _require_uuid(candidate_id, "CANDIDATE_ID_INVALID")
        valid_actor = _require_actor(actor, AdminRole.OPERATOR)
        await self._execute_void_write(
            SUBMIT_KB_CANDIDATE_SQL,
            (valid_id, valid_actor.actor_id, valid_actor.role.value),
        )

    async def approve_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> str:
        valid_id = _require_uuid(candidate_id, "CANDIDATE_ID_INVALID")
        valid_actor = _require_actor(actor, AdminRole.APPROVER)
        valid_comment = _require_review_comment(review_comment)
        parameters = (
            valid_id,
            valid_actor.actor_id,
            valid_actor.role.value,
            valid_comment,
        )
        try:
            async with (
                self._pool.connection() as connection,
                connection.transaction(),
                connection.cursor(row_factory=dict_row) as cursor,
            ):
                await cursor.execute(APPROVE_KB_CANDIDATE_SQL, parameters)
                rows = await cursor.fetchall()
                result = self._scalar_text(rows, "approve_kb_candidate")
        except psycopg.Error as exc:
            raise map_database_error(exc) from exc
        return result

    async def reject_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> None:
        valid_id = _require_uuid(candidate_id, "CANDIDATE_ID_INVALID")
        valid_actor = _require_actor(actor, AdminRole.APPROVER)
        valid_comment = _require_review_comment(review_comment)
        await self._execute_void_write(
            REJECT_KB_CANDIDATE_SQL,
            (
                valid_id,
                valid_actor.actor_id,
                valid_actor.role.value,
                valid_comment,
            ),
        )

    async def purge_expired_failed_question_text(self) -> PurgeResult:
        try:
            async with (
                self._pool.connection() as connection,
                connection.transaction(),
                connection.cursor(row_factory=dict_row) as cursor,
            ):
                await cursor.execute(PURGE_EXPIRED_FAILED_QUESTION_TEXT_SQL, ())
                rows = await cursor.fetchall()
                result = self._purge_result(rows)
        except psycopg.Error as exc:
            raise map_database_error(exc) from exc
        return result

    async def _execute_void_write(self, sql: str, parameters: tuple[object, ...]) -> None:
        try:
            async with (
                self._pool.connection() as connection,
                connection.transaction(),
                connection.cursor(row_factory=dict_row) as cursor,
            ):
                await cursor.execute(sql, parameters)
        except psycopg.Error as exc:
            raise map_database_error(exc) from exc

    @staticmethod
    def _single_row(
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if len(rows) != 1:
            raise DatabaseUnavailableError()
        return rows[0]

    @classmethod
    def _interaction_result(cls, rows: list[dict[str, Any]]) -> InteractionWriteResult:
        try:
            row = cls._single_row(rows)
            return InteractionWriteResult(
                interaction_id=_required_uuid(row["interaction_id"]),
                failed_question_id=_optional_uuid(row["failed_question_id"]),
            )
        except (KeyError, TypeError, ValueError):
            raise DatabaseUnavailableError() from None

    @classmethod
    def _scalar_uuid(cls, rows: list[dict[str, Any]], key: str) -> UUID:
        try:
            return _required_uuid(cls._single_row(rows)[key])
        except (KeyError, TypeError, ValueError):
            raise DatabaseUnavailableError() from None

    @classmethod
    def _scalar_text(cls, rows: list[dict[str, Any]], key: str) -> str:
        try:
            return _required_text(cls._single_row(rows)[key])
        except (KeyError, TypeError, ValueError):
            raise DatabaseUnavailableError() from None

    @classmethod
    def _purge_result(cls, rows: list[dict[str, Any]]) -> PurgeResult:
        try:
            row = cls._single_row(rows)
            purged_count = row["purged_count"]
            if type(purged_count) is not int:
                raise ValueError("MALFORMED_DATABASE_RESULT")
            return PurgeResult(
                purged_count=purged_count,
                purged_ids=_uuid_array(row["purged_ids"]),
            )
        except (KeyError, TypeError, ValueError):
            raise DatabaseUnavailableError() from None
