from __future__ import annotations

import json
import time
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from sejong_ai_api.chat.idempotency import IdempotencyClaim, IdempotencyClaimStatus
from sejong_ai_api.chat.readiness import INITIAL_ACTIVE_KB_IDS, REQUIRED_OFFICE_PROJECTIONS
from sejong_ai_api.contracts.admin import FailedQuestion, KBCandidateSummary
from sejong_ai_api.db.models import (
    Actor,
    CandidateDraft,
    FallbackReason,
    Intent,
    InteractionWrite,
    InteractionWriteResult,
    KnowledgeRecord,
    OfficeRecord,
    PurgeResult,
    Region,
)
from sejong_ai_api.local import create_local_app, load_local_settings


def _database_dsn(scheme: str, authority: str) -> str:
    return f"{scheme}://{authority}"


_PROVISIONED_DATABASE_URL = _database_dsn(
    "postgresql",
    "sejong_local_login:synthetic%3A%2F%40%25%20password@127.0.0.1:54322/postgres",
)
_FILE_DATABASE_URL = _database_dsn(
    "postgresql", "sejong_local_login:file-secret@127.0.0.1:54322/postgres"
)


def _knowledge(public_id: str, intent: Intent) -> KnowledgeRecord:
    question = (
        "이사했는데 전입신고는 어떻게 하나요?"
        if public_id == "KB-MOVE-01"
        else f"{public_id} 대표 질문"
    )
    return KnowledgeRecord(
        public_id=public_id,
        category=intent,
        service_name=f"service-{public_id}",
        answer_summary="공식 안내입니다.",
        procedure_steps=("공식 경로를 확인합니다.",),
        required_documents=(),
        processing_time=None,
        fee=None,
        department="담당 부서",
        source_title="공식 출처",
        source_url="https://example.invalid/official",
        last_verified_at=date(2026, 7, 18),
        caution=None,
        question_examples=(question,),
    )


def _office(public_id: str, region: Region) -> OfficeRecord:
    return OfficeRecord(
        public_id=public_id,
        region=region,
        office_name=f"{region.value} 행정복지센터",
        address="세종특별자치시 공식 주소",
        phone="044-000-0000",
        opening_hours="평일 09:00~18:00",
        map_url=None,
        department_label="담당 부서",
        source_title="공식 기관 안내",
        source_url="https://example.invalid/office",
        last_verified_at=date(2026, 7, 18),
    )


def _intent_for(public_id: str) -> Intent:
    if public_id.startswith("KB-CERT-"):
        return Intent.CERTIFICATE_ISSUANCE
    if public_id.startswith("KB-MOVE-"):
        return Intent.MOVE_IN_RESIDENT_REGISTRATION
    if public_id.startswith("KB-TAX-"):
        return Intent.LOCAL_TAX_GENERAL
    if public_id.startswith("KB-WASTE-"):
        return Intent.BULKY_WASTE
    raise AssertionError("unknown fixture ID")


class FakePool:
    def __init__(self, *, open_error: BaseException | None = None) -> None:
        self.open_error = open_error
        self.open_calls: list[bool] = []
        self.close_count = 0

    async def open(self, *, wait: bool = False) -> None:
        self.open_calls.append(wait)
        if self.open_error is not None:
            raise self.open_error

    async def close(self) -> None:
        self.close_count += 1


class FakeRepository:
    def __init__(self, _pool: object, *, ready: bool = True) -> None:
        self.ready = ready
        self.records = tuple(
            _knowledge(public_id, _intent_for(public_id))
            for public_id in sorted(INITIAL_ACTIVE_KB_IDS)
        )
        self.offices = {
            (region, intent): (_office(office_id, region),)
            for region, intent, office_id in REQUIRED_OFFICE_PROJECTIONS
        }
        self.events: list[InteractionWrite] = []
        self.idempotency: dict[UUID, tuple[str, UUID, dict[str, object] | None]] = {}
        self.failed_text_purge_count = 0
        self.idempotency_purge_count = 0

    async def list_active_kb(self, intent: Intent) -> Sequence[KnowledgeRecord]:
        if not self.ready:
            return ()
        return tuple(record for record in self.records if record.category is intent)

    async def list_offices(self, region: Region, intent: Intent) -> Sequence[OfficeRecord]:
        if not self.ready:
            return ()
        return self.offices.get((region, intent), ())

    async def record_interaction(self, event: InteractionWrite) -> InteractionWriteResult:
        self.events.append(event)
        return InteractionWriteResult(interaction_id=uuid4(), failed_question_id=None)

    async def list_failed_questions(self, *, reason: str | None, status: str | None) -> tuple[()]:
        del reason, status
        return ()

    async def get_failed_question(self, failed_question_id: UUID) -> FailedQuestion | None:
        del failed_question_id
        return None

    async def list_kb_candidates(self) -> tuple[KBCandidateSummary, ...]:
        return ()

    async def get_kb_candidate(self, candidate_id: UUID) -> KBCandidateSummary | None:
        del candidate_id
        return None

    async def confirm_failed_question_reason(
        self,
        failed_question_id: UUID,
        actor: Actor,
        fallback_reason: FallbackReason,
    ) -> None:
        del failed_question_id, actor, fallback_reason

    async def create_kb_candidate(self, draft: CandidateDraft) -> UUID:
        del draft
        return uuid4()

    async def submit_kb_candidate(self, candidate_id: UUID, actor: Actor) -> None:
        del candidate_id, actor

    async def approve_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> str:
        del candidate_id, actor, review_comment
        return "KB-FAKE"

    async def approve_kb_candidate_with_public_id(
        self,
        candidate_id: UUID,
        actor: Actor,
        review_comment: str,
        public_id: str,
    ) -> str:
        del candidate_id, actor, review_comment
        return public_id

    async def reject_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> None:
        del candidate_id, actor, review_comment

    async def purge_expired_failed_question_text(self) -> PurgeResult:
        self.failed_text_purge_count += 1
        return PurgeResult(purged_count=0, purged_ids=())

    async def claim_chat_idempotency(
        self,
        *,
        idempotency_key: UUID,
        request_fingerprint: str,
        claim_token: UUID,
    ) -> IdempotencyClaim:
        existing = self.idempotency.get(idempotency_key)
        if existing is None:
            self.idempotency[idempotency_key] = (
                request_fingerprint,
                claim_token,
                None,
            )
            return IdempotencyClaim(status=IdempotencyClaimStatus.ACQUIRED)
        fingerprint, _claim_id, response = existing
        if fingerprint != request_fingerprint:
            return IdempotencyClaim(status=IdempotencyClaimStatus.CONFLICT)
        if response is None:
            return IdempotencyClaim(status=IdempotencyClaimStatus.IN_PROGRESS)
        return IdempotencyClaim(
            status=IdempotencyClaimStatus.COMPLETED,
            response_payload=response,
        )

    async def complete_chat_idempotency(
        self,
        *,
        idempotency_key: UUID,
        request_fingerprint: str,
        claim_token: UUID,
        response_payload: dict[str, object],
    ) -> None:
        self.idempotency[idempotency_key] = (
            request_fingerprint,
            claim_token,
            response_payload,
        )

    async def commit_chat_idempotency(
        self,
        *,
        idempotency_key: UUID,
        request_fingerprint: str,
        claim_token: UUID,
        response_payload: dict[str, object],
        interaction: InteractionWrite | None,
    ) -> None:
        await self.complete_chat_idempotency(
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            claim_token=claim_token,
            response_payload=response_payload,
        )
        if interaction is not None:
            self.events.append(interaction)

    async def abandon_chat_idempotency(
        self,
        *,
        idempotency_key: UUID,
        request_fingerprint: str,
        claim_token: UUID,
    ) -> None:
        if self.idempotency.get(idempotency_key) == (
            request_fingerprint,
            claim_token,
            None,
        ):
            self.idempotency.pop(idempotency_key)

    async def purge_expired_chat_idempotency(self) -> PurgeResult:
        self.idempotency_purge_count += 1
        return PurgeResult(purged_count=0, purged_ids=())


def _config() -> dict[str, str]:
    return {
        "DATABASE_URL": _PROVISIONED_DATABASE_URL,
        "CONTEXT_TOKEN_SECRET": "x" * 32,
    }


def test_process_environment_wins_over_the_known_env_file(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        f"DATABASE_URL={_FILE_DATABASE_URL}\n"
        f"CONTEXT_TOKEN_SECRET={'f' * 32}\n"
        "LLM_API_KEY=DEEPSEEK-SENTINEL-MUST-NOT-BE-READ\n",
        encoding="utf-8",
    )

    settings = load_local_settings(environ=_config(), env_path=env_path)

    assert settings is not None
    assert settings.database_url == _PROVISIONED_DATABASE_URL
    assert settings.context_token_secret == b"x" * 32
    assert not hasattr(settings, "llm_api_key")


def test_known_env_file_is_a_fallback_for_each_missing_allowlisted_value(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        f"CONTEXT_TOKEN_SECRET={'s' * 32}\nDATABASE_URL={_FILE_DATABASE_URL}\n",
        encoding="utf-8",
    )

    settings = load_local_settings(
        environ={"DATABASE_URL": _PROVISIONED_DATABASE_URL},
        env_path=env_path,
    )

    assert settings is not None
    assert settings.database_url == _PROVISIONED_DATABASE_URL
    assert settings.context_token_secret == b"s" * 32


def test_percent_encoded_provisioned_database_uri_is_accepted_without_secret_repr(
    tmp_path: Path,
) -> None:
    settings = load_local_settings(environ=_config(), env_path=tmp_path / "missing")

    assert settings is not None
    assert settings.database_url == _PROVISIONED_DATABASE_URL
    assert _PROVISIONED_DATABASE_URL not in repr(settings)
    assert "synthetic:/@% password" not in repr(settings)


@pytest.mark.parametrize(
    "database_url",
    [
        "user=sejong_local_login password=secret host=127.0.0.1 port=54322 dbname=postgres",
        _database_dsn("postgres", "sejong_local_login:secret@127.0.0.1:54322/postgres"),
        _database_dsn("postgresql", "sejong_local_login:secret@db.example.invalid:54322/postgres"),
        _database_dsn("postgresql", "sejong_local_login:secret@localhost:54322/postgres"),
        _database_dsn("postgresql", "postgres:secret@127.0.0.1:54322/postgres"),
        _database_dsn("postgresql", "sejong_local_login:secret@127.0.0.1:54321/postgres"),
        _database_dsn("postgresql", "sejong_local_login:secret@127.0.0.1:54322/template1"),
        _database_dsn("postgresql", "sejong_local_login:@127.0.0.1:54322/postgres"),
        _database_dsn(
            "postgresql", "sejong_local_login:secret@127.0.0.1:54322/postgres?sslmode=disable"
        ),
        _database_dsn(
            "postgresql", "sejong_local_login:secret@127.0.0.1:54322/postgres?hostaddr=127.0.0.2"
        ),
        _database_dsn(
            "postgresql",
            "sejong_local_login:secret@remote.example.invalid@127.0.0.1:54322/postgres",
        ),
        _database_dsn("postgresql", "sejong_local_login:secret%ZZ@127.0.0.1:54322/postgres"),
    ],
)
def test_database_uri_rejects_malformed_remote_or_untrusted_configuration(
    tmp_path: Path,
    database_url: str,
) -> None:
    pool_factory_calls: list[str] = []

    def pool_factory(value: str) -> FakePool:
        pool_factory_calls.append(value)
        return FakePool()

    assert (
        load_local_settings(
            environ={
                "DATABASE_URL": database_url,
                "CONTEXT_TOKEN_SECRET": "x" * 32,
            },
            env_path=tmp_path / "missing",
        )
        is None
    )
    create_local_app(
        environ={
            "DATABASE_URL": database_url,
            "CONTEXT_TOKEN_SECRET": "x" * 32,
        },
        env_path=tmp_path / "missing",
        pool_factory=pool_factory,
    )
    assert pool_factory_calls == []


@pytest.mark.parametrize(
    "variable",
    ["PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS", "pgpassword"],
)
def test_ambient_libpq_environment_keeps_local_pool_unconstructed(
    tmp_path: Path,
    variable: str,
) -> None:
    environ = {**_config(), variable: "synthetic-ambient-value"}
    pool_factory_calls: list[str] = []

    def pool_factory(value: str) -> FakePool:
        pool_factory_calls.append(value)
        return FakePool()

    assert load_local_settings(environ=environ, env_path=tmp_path / "missing") is None
    create_local_app(
        environ=environ,
        env_path=tmp_path / "missing",
        pool_factory=pool_factory,
    )
    assert pool_factory_calls == []


@pytest.mark.parametrize(
    "environ",
    [
        {},
        {"DATABASE_URL": _PROVISIONED_DATABASE_URL},
        {"CONTEXT_TOKEN_SECRET": "x" * 32},
        {"DATABASE_URL": _PROVISIONED_DATABASE_URL, "CONTEXT_TOKEN_SECRET": "short"},
    ],
)
def test_missing_or_short_configuration_is_closed_without_an_exception(
    tmp_path: Path,
    environ: dict[str, str],
) -> None:
    assert load_local_settings(environ=environ, env_path=tmp_path / "missing") is None


def test_missing_configuration_keeps_health_alive_and_chat_readiness_closed(tmp_path: Path) -> None:
    pool_factory_calls: list[str] = []

    def unexpected_pool_factory(value: str) -> FakePool:
        pool_factory_calls.append(value)
        return FakePool()

    app = create_local_app(
        environ={},
        env_path=tmp_path / "missing",
        pool_factory=unexpected_pool_factory,
    )

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/ready").status_code == 503
        assert client.post("/api/v1/chat", json={"question": "전입신고"}).status_code == 503
        assert (
            client.get(
                "/api/v1/admin/failed-questions",
                headers={
                    "X-Demo-Actor-Id": "OPERATOR-LOCAL-001",
                    "X-Demo-Role": "OPERATOR",
                },
            ).status_code
            == 404
        )
    assert pool_factory_calls == []


def test_valid_configuration_creates_one_lazy_pool_and_opens_and_closes_it_once(
    tmp_path: Path,
) -> None:
    pool = FakePool()
    pool_factory_calls: list[str] = []
    repositories: list[FakeRepository] = []

    def pool_factory(database_url: str) -> FakePool:
        pool_factory_calls.append(database_url)
        return pool

    def repository_factory(value: object) -> FakeRepository:
        repository = FakeRepository(value)
        repositories.append(repository)
        return repository

    app = create_local_app(
        environ=_config(),
        env_path=tmp_path / "missing",
        pool_factory=pool_factory,
        repository_factory=repository_factory,
    )

    assert pool_factory_calls == [_PROVISIONED_DATABASE_URL]
    assert pool.open_calls == []
    with TestClient(app) as client:
        assert pool.open_calls == [True]
        assert client.get("/health").status_code == 200
        assert client.get("/ready").json() == {"status": "ready"}
        chat = client.post(
            "/api/v1/chat",
            json={"question": "이사했는데 전입신고는 어떻게 하나요?"},
        )
        assert chat.status_code == 200
        assert chat.json()["answer_status"] == "SUCCESS"
        admin = client.get(
            "/api/v1/admin/failed-questions",
            headers={
                "X-Demo-Actor-Id": "OPERATOR-LOCAL-001",
                "X-Demo-Role": "OPERATOR",
            },
        )
        assert admin.status_code == 200
        assert admin.json() == {"items": [], "total": 0}
    assert pool.close_count == 1
    assert len(repositories) == 1
    assert len(repositories[0].events) == 1
    assert repositories[0].failed_text_purge_count == 2
    assert repositories[0].idempotency_purge_count == 1


def test_local_chat_replays_same_logical_request_without_duplicate_event(
    tmp_path: Path,
) -> None:
    pool = FakePool()
    repositories: list[FakeRepository] = []

    def repository_factory(value: object) -> FakeRepository:
        repository = FakeRepository(value)
        repositories.append(repository)
        return repository

    app = create_local_app(
        environ=_config(),
        env_path=tmp_path / "missing",
        pool_factory=lambda _value: pool,
        repository_factory=repository_factory,
    )
    idempotency_key = str(uuid4())
    payload = {"question": "이사했는데 전입신고는 어떻게 하나요?"}

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/chat",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        )
        replay = client.post(
            "/api/v1/chat",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.json()["request_id"] != replay.json()["request_id"]
    assert len(repositories[0].events) == 1


def test_local_runtime_periodically_purges_expired_private_records(tmp_path: Path) -> None:
    pool = FakePool()
    repositories: list[FakeRepository] = []

    def repository_factory(value: object) -> FakeRepository:
        repository = FakeRepository(value)
        repositories.append(repository)
        return repository

    app = create_local_app(
        environ=_config(),
        env_path=tmp_path / "missing",
        pool_factory=lambda _value: pool,
        repository_factory=repository_factory,
        purge_interval_seconds=0.01,
    )

    with TestClient(app):
        deadline = time.monotonic() + 0.5
        while repositories[0].idempotency_purge_count < 2 and time.monotonic() < deadline:
            time.sleep(0.01)

    assert repositories[0].failed_text_purge_count >= 2
    assert repositories[0].idempotency_purge_count >= 2


def test_runtime_repository_failure_closes_readiness_and_chat_without_restart(
    tmp_path: Path,
) -> None:
    pool = FakePool()
    repositories: list[FakeRepository] = []

    def repository_factory(value: object) -> FakeRepository:
        repository = FakeRepository(value)
        repositories.append(repository)
        return repository

    app = create_local_app(
        environ=_config(),
        env_path=tmp_path / "missing",
        pool_factory=lambda _value: pool,
        repository_factory=repository_factory,
    )

    with TestClient(app) as client:
        assert client.get("/ready").status_code == 200
        repositories[0].ready = False
        assert client.get("/ready").status_code == 503
        assert client.post("/api/v1/chat", json={"question": "전입신고"}).status_code == 503
        repositories[0].ready = True
        assert client.get("/ready").status_code == 200
        assert client.post("/api/v1/chat", json={"question": "전입신고"}).status_code == 200


def test_incomplete_repository_keeps_guarded_chat_and_readiness_closed(tmp_path: Path) -> None:
    pool = FakePool()

    app = create_local_app(
        environ=_config(),
        env_path=tmp_path / "missing",
        pool_factory=lambda _value: pool,
        repository_factory=lambda value: FakeRepository(value, ready=False),
    )

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
        response = client.post("/api/v1/chat", json={"question": "전입신고"})
        assert response.status_code == 503
        serialized = json.dumps(response.json(), ensure_ascii=False)
        assert "database" not in serialized.casefold()


def test_pool_startup_failure_stays_value_free_and_health_remains_live(tmp_path: Path) -> None:
    sentinel = "RAW-POOL-DIAGNOSTIC-MUST-NOT-ESCAPE"
    pool = FakePool(open_error=RuntimeError(sentinel))

    app = create_local_app(
        environ=_config(),
        env_path=tmp_path / "missing",
        pool_factory=lambda _value: pool,
        repository_factory=lambda value: FakeRepository(value),
    )

    with TestClient(app) as client:
        health = client.get("/health")
        ready = client.get("/ready")
        chat = client.post("/api/v1/chat", json={"question": "전입신고"})

    assert health.status_code == 200
    assert ready.status_code == 503
    assert chat.status_code == 503
    assert sentinel not in json.dumps(ready.json())
    assert sentinel not in json.dumps(chat.json())
    assert pool.open_calls == [True]
    assert pool.close_count == 1


def test_pool_construction_failure_stays_closed_without_leaking_the_diagnostic(
    tmp_path: Path,
) -> None:
    sentinel = "RAW-POOL-CONSTRUCTION-DIAGNOSTIC-MUST-NOT-ESCAPE"

    def fail_pool(_value: str) -> Any:
        raise RuntimeError(sentinel)

    app = create_local_app(
        environ=_config(),
        env_path=tmp_path / "missing",
        pool_factory=fail_pool,
    )

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        response = client.get("/ready")
    assert response.status_code == 503
    assert sentinel not in json.dumps(response.json())
