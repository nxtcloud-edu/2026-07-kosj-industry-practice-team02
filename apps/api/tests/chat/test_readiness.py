from __future__ import annotations

from collections.abc import Sequence
from datetime import date

import pytest

from sejong_ai_api.chat.readiness import (
    INITIAL_ACTIVE_KB_IDS,
    REQUIRED_OFFICE_PROJECTIONS,
    RepositoryReadinessProbe,
)
from sejong_ai_api.db.errors import DatabaseUnavailableError
from sejong_ai_api.db.models import Intent, KnowledgeRecord, OfficeRecord, Region


def _knowledge(public_id: str, intent: Intent) -> KnowledgeRecord:
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
        question_examples=("대표 질문",),
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


_INTENT_BY_PREFIX = {
    "KB-CERT-": Intent.CERTIFICATE_ISSUANCE,
    "KB-MOVE-": Intent.MOVE_IN_RESIDENT_REGISTRATION,
    "KB-TAX-": Intent.LOCAL_TAX_GENERAL,
    "KB-WASTE-": Intent.BULKY_WASTE,
}


def _intent_for(public_id: str) -> Intent:
    for prefix, intent in _INTENT_BY_PREFIX.items():
        if public_id.startswith(prefix):
            return intent
    raise AssertionError("test fixture has an unknown public ID")


class FakeReadRepository:
    def __init__(self) -> None:
        self.knowledge = {
            intent: tuple(
                _knowledge(public_id, intent)
                for public_id in sorted(INITIAL_ACTIVE_KB_IDS)
                if _intent_for(public_id) is intent
            )
            for intent in set(_INTENT_BY_PREFIX.values())
        }
        self.offices = {
            (region, intent): (_office(office_id, region),)
            for region, intent, office_id in REQUIRED_OFFICE_PROJECTIONS
        }
        self.kb_calls: list[Intent] = []
        self.office_calls: list[tuple[Region, Intent]] = []
        self.error: BaseException | None = None

    async def list_active_kb(self, intent: Intent) -> Sequence[KnowledgeRecord]:
        self.kb_calls.append(intent)
        if self.error is not None:
            raise self.error
        return self.knowledge[intent]

    async def list_offices(self, region: Region, intent: Intent) -> Sequence[OfficeRecord]:
        self.office_calls.append((region, intent))
        if self.error is not None:
            raise self.error
        return self.offices.get((region, intent), ())


def test_canonical_initial_active_ids_are_the_approved_nineteen() -> None:
    assert (
        frozenset(
            {
                "KB-CERT-01",
                "KB-CERT-02",
                "KB-CERT-03",
                "KB-CERT-04",
                "KB-CERT-05",
                "KB-MOVE-01",
                "KB-MOVE-02",
                "KB-MOVE-03",
                "KB-MOVE-04",
                "KB-MOVE-05",
                "KB-TAX-01",
                "KB-TAX-02",
                "KB-TAX-03",
                "KB-TAX-04",
                "KB-TAX-05",
                "KB-WASTE-01",
                "KB-WASTE-02",
                "KB-WASTE-04",
                "KB-WASTE-05",
            }
        )
        == INITIAL_ACTIVE_KB_IDS
    )


@pytest.mark.asyncio
async def test_readiness_requires_all_nineteen_and_exact_three_office_ten_pair_projection() -> None:
    repository = FakeReadRepository()
    probe = RepositoryReadinessProbe(repository)

    assert probe.is_ready() is False
    assert await probe.refresh() is True
    assert probe.is_ready() is True
    assert set(repository.kb_calls) == set(_INTENT_BY_PREFIX.values())
    assert len(repository.kb_calls) == 4
    assert len(repository.office_calls) == 12


@pytest.mark.asyncio
async def test_readiness_remains_true_after_the_twentieth_active_kb_is_added() -> None:
    repository = FakeReadRepository()
    repository.knowledge[Intent.BULKY_WASTE] += (_knowledge("KB-WASTE-03", Intent.BULKY_WASTE),)

    probe = RepositoryReadinessProbe(repository)

    assert await probe.refresh() is True
    assert probe.is_ready() is True


@pytest.mark.asyncio
async def test_readiness_closes_when_one_canonical_kb_is_missing() -> None:
    repository = FakeReadRepository()
    repository.knowledge[Intent.BULKY_WASTE] = tuple(
        record
        for record in repository.knowledge[Intent.BULKY_WASTE]
        if record.public_id != "KB-WASTE-05"
    )

    probe = RepositoryReadinessProbe(repository)

    assert await probe.refresh() is False
    assert probe.is_ready() is False


@pytest.mark.asyncio
async def test_readiness_closes_for_an_extra_or_missing_office_projection() -> None:
    repository = FakeReadRepository()
    repository.offices[(Region.AREUM_DONG, Intent.LOCAL_TAX_GENERAL)] = (
        _office("OFFICE-AREUM", Region.AREUM_DONG),
    )

    probe = RepositoryReadinessProbe(repository)

    assert await probe.refresh() is False
    assert probe.is_ready() is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        DatabaseUnavailableError(),
        RuntimeError("RAW-DATABASE-DIAGNOSTIC-MUST-NOT-ESCAPE"),
    ],
)
async def test_readiness_maps_database_or_malformed_failures_to_value_free_false(
    failure: BaseException,
) -> None:
    repository = FakeReadRepository()
    repository.error = failure
    probe = RepositoryReadinessProbe(repository)

    assert await probe.refresh() is False
    assert probe.is_ready() is False


@pytest.mark.asyncio
async def test_readiness_can_be_closed_after_a_runtime_dependency_failure() -> None:
    repository = FakeReadRepository()
    probe = RepositoryReadinessProbe(repository)
    assert await probe.refresh() is True

    probe.mark_unavailable()

    assert probe.is_ready() is False
    assert await probe.check_ready() is True
