from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sejong_ai_api.chat.readiness import INITIAL_ACTIVE_KB_IDS, REQUIRED_OFFICE_PROJECTIONS
from sejong_ai_api.db.models import (
    Intent,
    InteractionWrite,
    InteractionWriteResult,
    KnowledgeRecord,
    OfficeRecord,
    Region,
)
from sejong_ai_api.local import create_local_app, load_local_settings


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


def _config() -> dict[str, str]:
    return {
        "DATABASE_URL": "postgresql://local.invalid/sejong",
        "CONTEXT_TOKEN_SECRET": "x" * 32,
    }


def test_process_environment_wins_over_the_known_env_file(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "DATABASE_URL=postgresql://file.invalid/sejong\n"
        f"CONTEXT_TOKEN_SECRET={'f' * 32}\n"
        "LLM_API_KEY=DEEPSEEK-SENTINEL-MUST-NOT-BE-READ\n",
        encoding="utf-8",
    )

    settings = load_local_settings(environ=_config(), env_path=env_path)

    assert settings is not None
    assert settings.database_url == "postgresql://local.invalid/sejong"
    assert settings.context_token_secret == b"x" * 32
    assert not hasattr(settings, "llm_api_key")


def test_known_env_file_is_a_fallback_for_each_missing_allowlisted_value(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        f"CONTEXT_TOKEN_SECRET={'s' * 32}\nDATABASE_URL=postgresql://file.invalid/sejong\n",
        encoding="utf-8",
    )

    settings = load_local_settings(
        environ={"DATABASE_URL": "postgresql://process.invalid/sejong"},
        env_path=env_path,
    )

    assert settings is not None
    assert settings.database_url == "postgresql://process.invalid/sejong"
    assert settings.context_token_secret == b"s" * 32


@pytest.mark.parametrize(
    "environ",
    [
        {},
        {"DATABASE_URL": "postgresql://local.invalid/sejong"},
        {"CONTEXT_TOKEN_SECRET": "x" * 32},
        {"DATABASE_URL": "postgresql://local.invalid/sejong", "CONTEXT_TOKEN_SECRET": "short"},
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

    assert pool_factory_calls == ["postgresql://local.invalid/sejong"]
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
    assert pool.close_count == 1
    assert len(repositories) == 1
    assert len(repositories[0].events) == 1


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
