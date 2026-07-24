"""Closed readiness policy for the approved local/private data projection."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from sejong_ai_api.db.models import Intent, KnowledgeRecord, OfficeRecord, Region

INITIAL_ACTIVE_KB_IDS = frozenset(
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

_SUPPORTED_INTENTS = (
    Intent.MOVE_IN_RESIDENT_REGISTRATION,
    Intent.CERTIFICATE_ISSUANCE,
    Intent.BULKY_WASTE,
    Intent.LOCAL_TAX_GENERAL,
)

REQUIRED_OFFICE_PROJECTIONS = (
    (Region.AREUM_DONG, Intent.BULKY_WASTE, "OFFICE-AREUM"),
    (Region.AREUM_DONG, Intent.CERTIFICATE_ISSUANCE, "OFFICE-AREUM"),
    (Region.AREUM_DONG, Intent.MOVE_IN_RESIDENT_REGISTRATION, "OFFICE-AREUM"),
    (Region.DODAM_DONG, Intent.CERTIFICATE_ISSUANCE, "OFFICE-DODAM"),
    (Region.DODAM_DONG, Intent.LOCAL_TAX_GENERAL, "OFFICE-DODAM"),
    (Region.DODAM_DONG, Intent.MOVE_IN_RESIDENT_REGISTRATION, "OFFICE-DODAM"),
    (Region.JOCHIWON_EUP, Intent.BULKY_WASTE, "OFFICE-JOCHIWON"),
    (Region.JOCHIWON_EUP, Intent.CERTIFICATE_ISSUANCE, "OFFICE-JOCHIWON"),
    (Region.JOCHIWON_EUP, Intent.LOCAL_TAX_GENERAL, "OFFICE-JOCHIWON"),
    (Region.JOCHIWON_EUP, Intent.MOVE_IN_RESIDENT_REGISTRATION, "OFFICE-JOCHIWON"),
)

_EXPECTED_OFFICE_BY_PAIR = {
    (region, intent): office_id for region, intent, office_id in REQUIRED_OFFICE_PROJECTIONS
}


class ReadinessRepository(Protocol):
    async def list_active_kb(self, intent: Intent) -> Sequence[KnowledgeRecord]: ...

    async def list_offices(self, region: Region, intent: Intent) -> Sequence[OfficeRecord]: ...


class RepositoryReadinessProbe:
    """Evaluate the current repository projection and retain diagnostic-free state."""

    __slots__ = ("_enabled", "_ready", "_repository")

    def __init__(self, repository: ReadinessRepository) -> None:
        self._repository = repository
        self._enabled = True
        self._ready = False

    def is_ready(self) -> bool:
        """Return the last observed state for startup and test diagnostics only."""
        return self._ready

    async def check_ready(self) -> bool:
        """Re-evaluate dependencies so health never relies on stale startup state."""
        if not self._enabled:
            return False
        return await self.refresh()

    async def refresh(self) -> bool:
        """Refresh without exposing database or malformed-row diagnostics."""

        try:
            ready = await self._read_exact_projection()
        except Exception:
            ready = False
        self._ready = ready
        return ready

    def mark_unavailable(self) -> None:
        self._ready = False

    def disable(self) -> None:
        """Latch closed only when the local runtime itself failed to start or stopped."""
        self._enabled = False
        self._ready = False

    async def _read_exact_projection(self) -> bool:
        public_ids: list[str] = []
        for intent in _SUPPORTED_INTENTS:
            records = await self._repository.list_active_kb(intent)
            for record in records:
                if type(record) is not KnowledgeRecord or record.category is not intent:
                    return False
                public_ids.append(record.public_id)

        if len(public_ids) != len(set(public_ids)):
            return False
        if not INITIAL_ACTIVE_KB_IDS.issubset(public_ids):
            return False

        projected_office_ids: set[str] = set()
        observed_projection_count = 0
        for region in Region:
            for intent in _SUPPORTED_INTENTS:
                offices = tuple(await self._repository.list_offices(region, intent))
                expected_office_id = _EXPECTED_OFFICE_BY_PAIR.get((region, intent))
                if expected_office_id is None:
                    if offices:
                        return False
                    continue
                if len(offices) != 1:
                    return False
                office = offices[0]
                if (
                    type(office) is not OfficeRecord
                    or office.region is not region
                    or office.public_id != expected_office_id
                ):
                    return False
                projected_office_ids.add(office.public_id)
                observed_projection_count += 1

        return observed_projection_count == 10 and projected_office_ids == {
            "OFFICE-AREUM",
            "OFFICE-DODAM",
            "OFFICE-JOCHIWON",
        }


__all__ = [
    "INITIAL_ACTIVE_KB_IDS",
    "REQUIRED_OFFICE_PROJECTIONS",
    "ReadinessRepository",
    "RepositoryReadinessProbe",
]
