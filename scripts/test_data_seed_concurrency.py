"""Two-connection ordering probes for the disposable official seed gate."""

from __future__ import annotations

import os
from pathlib import Path
from queue import Queue
import sys
import threading
import time
from typing import Any, Sequence

import psycopg

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.data_seed_release import SUCCESSOR_RELEASE_PROFILE
from scripts.verify_data_seed_db import (
    ADMIN_DSN_ENVIRONMENT,
    REPOSITORY_ROOT,
    VerifiedRelease,
    _assert_exact_projection,
    _assert_session_identity,
    _expect_sql_failure,
    _open_connection,
    _rollback_quietly,
    _stable_reason,
    assert_no_ambient_libpq_environment,
    load_verified_release,
    parse_and_validate_dsn,
)


RELEASE_VERSION = SUCCESSOR_RELEASE_PROFILE.version
CAPABILITY_BEFORE_SEED = "capability-before-seed"
SEED_BEFORE_CAPABILITY = "seed-before-capability"
_SCENARIO_STEPS = {
    CAPABILITY_BEFORE_SEED: "VERIFY-DATA-SEED-CONCURRENCY-A",
    SEED_BEFORE_CAPABILITY: "VERIFY-DATA-SEED-CONCURRENCY-B",
}
_CAPABILITY_SQL = """
SELECT interaction_id, failed_question_id
FROM app_api.record_interaction(
  %s::uuid,
  'MOVE_IN_RESIDENT_REGISTRATION',
  'FOLLOWUP',
  NULL,
  ARRAY[]::text[],
  0,
  NULL,
  NULL,
  true,
  NULL
)
""".strip()
_SEED_PREFLIGHT_MARKER = b"\n\nDO $data_seed_empty_guard$"
# record_interaction first touches interaction_events with SELECT ... FOR SHARE.
CAPABILITY_FIRST_ACCESS_LOCK_MODE = "RowShareLock"
LOCK_WAIT_QUERY = """
SELECT
  pg_catalog.pg_blocking_pids(%s),
  locks.locktype,
  locks.relation::pg_catalog.regclass::text,
  locks.mode,
  locks.granted
FROM pg_catalog.pg_locks AS locks
WHERE locks.pid = %s
  AND NOT locks.granted
""".strip()


def _parse_cli(argv: Sequence[str]) -> tuple[str, str]:
    if isinstance(argv, (str, bytes)) or len(argv) != 4:
        raise ValueError("CLI_ARGUMENTS_INVALID")
    values: dict[str, str] = {}
    for index in range(0, 4, 2):
        flag = argv[index]
        value = argv[index + 1]
        if flag not in {"--scenario", "--release-version"} or flag in values:
            raise ValueError("CLI_ARGUMENTS_INVALID")
        values[flag] = value
    scenario = values.get("--scenario", "")
    version = values.get("--release-version", "")
    if scenario not in _SCENARIO_STEPS or version != RELEASE_VERSION:
        raise ValueError("CLI_ARGUMENTS_INVALID")
    return scenario, version


def _record_followup(
    connection: psycopg.Connection[Any],
    request_id: str,
) -> None:
    connection.execute("SET statement_timeout = '10s'")
    connection.execute("SET lock_timeout = '10s'")
    row = connection.execute(_CAPABILITY_SQL, (request_id,)).fetchone()
    if row is None or len(row) != 2 or row[0] is None or row[1] is not None:
        raise ValueError("CAPABILITY_WRITE_INVALID")


def _seed_owned_count(connection: psycopg.Connection[Any]) -> int:
    row = connection.execute(
        """
SELECT
  (SELECT pg_catalog.count(*) FROM app_private.kb_documents)
  + (SELECT pg_catalog.count(*) FROM app_private.kb_question_examples)
  + (SELECT pg_catalog.count(*) FROM app_private.offices)
  + (SELECT pg_catalog.count(*) FROM app_private.office_service_mappings)
""".strip()
    ).fetchone()
    if row is None or len(row) != 1 or not isinstance(row[0], int):
        raise ValueError("DATABASE_COUNT_INVALID")
    return row[0]


def _scenario_capability_before_seed(
    dsn: str,
    release: VerifiedRelease,
) -> None:
    with _open_connection(dsn) as capability, _open_connection(dsn) as seed:
        _assert_session_identity(capability)
        _assert_session_identity(seed)
        _record_followup(capability, "45000000-0000-4000-8000-000000000911")
        _expect_sql_failure(seed, release.seed_sql, "DATA_SEED_DATABASE_NOT_EMPTY")
        if _seed_owned_count(seed) != 0:
            raise ValueError("DATABASE_PARTIAL_MUTATION")
        row = seed.execute(
            "SELECT pg_catalog.count(*)::integer FROM app_private.interaction_events"
        ).fetchone()
        if row != (1,):
            raise ValueError("CAPABILITY_WRITE_INVALID")


def _wait_until_lock_blocked(
    connection: psycopg.Connection[Any],
    worker_backend_pid: int,
) -> None:
    seed_backend_pid = connection.info.backend_pid
    if type(seed_backend_pid) is not int or seed_backend_pid <= 0:
        raise ValueError("SEED_BACKEND_PID_INVALID")
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        rows = connection.execute(
            LOCK_WAIT_QUERY,
            (worker_backend_pid, worker_backend_pid),
        ).fetchall()
        for row in rows:
            if len(row) != 5:
                continue
            blockers, locktype, relation, mode, granted = row
            if (
                isinstance(blockers, (list, tuple))
                and seed_backend_pid in blockers
                and locktype == "relation"
                and relation == "app_private.interaction_events"
                and mode == CAPABILITY_FIRST_ACCESS_LOCK_MODE
                and granted is False
            ):
                return
        time.sleep(0.05)
    raise ValueError("CAPABILITY_WRITE_DID_NOT_BLOCK")


def _scenario_seed_before_capability(
    dsn: str,
    release: VerifiedRelease,
) -> None:
    if release.seed_sql.count(_SEED_PREFLIGHT_MARKER) != 1:
        raise ValueError("RELEASE_SQL_MARKER_INVALID")
    prefix, suffix = release.seed_sql.split(_SEED_PREFLIGHT_MARKER, 1)
    worker_pid: Queue[int] = Queue(maxsize=1)
    worker_error: Queue[BaseException] = Queue(maxsize=1)
    worker_done = threading.Event()

    def capability_worker() -> None:
        try:
            with _open_connection(dsn) as connection:
                worker_pid.put(connection.info.backend_pid, timeout=2)
                _record_followup(
                    connection,
                    "45000000-0000-4000-8000-000000000912",
                )
        except BaseException as error:
            worker_error.put(error)
        finally:
            worker_done.set()

    worker = threading.Thread(
        target=capability_worker,
        name="data-seed-capability-writer",
        daemon=True,
    )
    with _open_connection(dsn) as seed:
        _assert_session_identity(seed)
        try:
            seed.execute(prefix.decode("utf-8", errors="strict"))
            worker.start()
            pid = worker_pid.get(timeout=3)
            _wait_until_lock_blocked(seed, pid)
            if worker_done.is_set():
                raise ValueError("CAPABILITY_WRITE_DID_NOT_BLOCK")
            seed.execute(
                (_SEED_PREFLIGHT_MARKER + suffix).decode("utf-8", errors="strict")
            )
        except BaseException:
            _rollback_quietly(seed)
            raise

        worker.join(timeout=10)
        if worker.is_alive():
            raise ValueError("CAPABILITY_WRITE_TIMEOUT")
        if not worker_error.empty():
            raise ValueError("CAPABILITY_WRITE_FAILED") from worker_error.get()
        _assert_exact_projection(seed, release)
        row = seed.execute(
            "SELECT pg_catalog.count(*)::integer FROM app_private.interaction_events"
        ).fetchone()
        if row != (1,):
            raise ValueError("CAPABILITY_WRITE_INVALID")


def cli(argv: Sequence[str]) -> int:
    scenario = ""
    try:
        scenario, version = _parse_cli(argv)
        dsn = os.environ.get(ADMIN_DSN_ENVIRONMENT, "")
        parse_and_validate_dsn(dsn)
        assert_no_ambient_libpq_environment(os.environ)
        release = load_verified_release(REPOSITORY_ROOT, version)
        if scenario == CAPABILITY_BEFORE_SEED:
            _scenario_capability_before_seed(dsn, release)
            detail = "ordering=capability-before-lock seed_rows=0 capability_rows=1"
        else:
            _scenario_seed_before_capability(dsn, release)
            detail = "ordering=lock-before-capability seed_complete=1 capability_rows=1"
        print(
            f"[PASS] step={_SCENARIO_STEPS[scenario]} "
            f"release={RELEASE_VERSION} {detail}"
        )
        return 0
    except Exception as error:
        step = _SCENARIO_STEPS.get(scenario, "VERIFY-DATA-SEED-CONCURRENCY")
        print(f"[FAIL] step={step} reason={_stable_reason(error)} issues=1")
        return 2


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
