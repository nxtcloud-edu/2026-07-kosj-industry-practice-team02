"""Unit tests for the disposable DATA-SEED database verifier.

The suite deliberately uses fakes only at the PostgreSQL connection boundary.  It
never starts Docker, publishes a release, or mutates the tracked dispatcher.
"""

from __future__ import annotations

from contextlib import redirect_stdout
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import tempfile
from typing import cast
import unittest
from unittest import mock

from scripts import verify_data_seed_db as verifier
from scripts import test_data_seed_concurrency as concurrency


RELEASE_VERSION = "0.1.0-initial.1"
SECRET_DSN = "postgresql://postgres:" + "synthetic-secret@127.0.0.1:54322/postgres"


class DirectEntrypointTests(unittest.TestCase):
    def assert_stable_direct_failure(
        self, script_name: str, expected_step: str
    ) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-B", str(repository_root / "scripts" / script_name)],
            cwd=repository_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(2, result.returncode)
        self.assertEqual(
            f"[FAIL] step={expected_step} reason=CLI_ARGUMENTS_INVALID issues=1\n",
            result.stdout,
        )
        self.assertEqual("", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stdout + result.stderr)

    def test_direct_database_verifier_reaches_stable_cli_failure(self) -> None:
        self.assert_stable_direct_failure(
            "verify_data_seed_db.py",
            "VERIFY-DATA-SEED-CLI",
        )

    def test_direct_concurrency_probe_reaches_stable_cli_failure(self) -> None:
        self.assert_stable_direct_failure(
            "test_data_seed_concurrency.py",
            "VERIFY-DATA-SEED-CONCURRENCY",
        )


class _RowsConnection:
    """Small connection fake returning rows by stable query marker."""

    def __init__(self, rows: dict[str, list[tuple[object, ...]]]) -> None:
        self.rows = rows
        self.statements: list[str] = []
        self._current: list[tuple[object, ...]] = []

    def execute(self, statement: str) -> _RowsConnection:
        self.statements.append(statement)
        self._current = []
        for marker, rows in self.rows.items():
            if marker in statement:
                self._current = rows
                break
        return self

    def fetchall(self) -> list[tuple[object, ...]]:
        return list(self._current)

    def fetchone(self) -> tuple[object, ...] | None:
        return self._current[0] if self._current else None


class _LockProbeConnection:
    """Expose the old opaque boolean and the desired exact lock rows."""

    def __init__(self, rows: list[tuple[object, ...]], seed_pid: int = 701) -> None:
        self.rows = rows
        self.info = SimpleNamespace(backend_pid=seed_pid)
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def execute(
        self,
        statement: str,
        parameters: tuple[object, ...],
    ) -> _LockProbeConnection:
        self.calls.append((statement, parameters))
        return self

    def fetchone(self) -> tuple[object, ...]:
        return (True,)

    def fetchall(self) -> list[tuple[object, ...]]:
        return list(self.rows)


class AdminDsnIdentityTests(unittest.TestCase):
    def test_dsn_identity_requires_exact_local_admin(self) -> None:
        accepted = verifier.parse_and_validate_dsn(SECRET_DSN)
        self.assertEqual(
            ("postgres", "127.0.0.1", 54322, "postgres"),
            accepted.identity,
        )

        invalid = (
            SECRET_DSN.replace("postgres:", "other:", 1),
            SECRET_DSN.replace("127.0.0.1", "localhost", 1),
            SECRET_DSN.replace("54322", "54321", 1),
            SECRET_DSN.replace("/postgres", "/template1", 1),
            SECRET_DSN + "?hostaddr=127.0.0.2",
            SECRET_DSN + "?service=synthetic",
            SECRET_DSN + "?sslmode=disable",
            SECRET_DSN + "?options=-csearch_path%3Dpublic",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "ADMIN_DSN_IDENTITY_INVALID"):
                    verifier.parse_and_validate_dsn(value)

    def test_uri_dsn_with_password_is_accepted_without_retaining_secret(self) -> None:
        parsed = verifier.parse_and_validate_dsn(SECRET_DSN)

        self.assertEqual(("postgres", "127.0.0.1", 54322, "postgres"), parsed.identity)
        self.assertNotIn("synthetic-secret", repr(parsed))
        self.assertNotIn(SECRET_DSN, repr(parsed))

    def test_dsn_requires_password_and_rejects_every_extra_parsed_key(self) -> None:
        without_password = "user=postgres host=127.0.0.1 port=54322 dbname=postgres"
        empty_password = SECRET_DSN.replace("synthetic-secret", "", 1)
        for value in (without_password, empty_password):
            with self.subTest(value_present=bool(value)):
                with self.assertRaisesRegex(ValueError, "ADMIN_DSN_IDENTITY_INVALID"):
                    verifier.parse_and_validate_dsn(value)

        parsed_with_extra = {
            "user": "postgres",
            "password": "synthetic-secret",
            "host": "127.0.0.1",
            "port": "54322",
            "dbname": "postgres",
            "application_name": "synthetic",
        }
        with mock.patch.object(
            verifier,
            "conninfo_to_dict",
            return_value=parsed_with_extra,
        ):
            with self.assertRaisesRegex(ValueError, "ADMIN_DSN_IDENTITY_INVALID"):
                verifier.parse_and_validate_dsn(SECRET_DSN)

    def test_verifier_rejects_nonempty_ambient_pg_before_release_or_connect(
        self,
    ) -> None:
        for name in ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS"):
            with self.subTest(name=name):
                buffer = StringIO()
                with (
                    mock.patch.dict(
                        verifier.os.environ,
                        {
                            "SEJONG_ADMIN_DATABASE_URL": SECRET_DSN,
                            name: "synthetic-ambient-value",
                        },
                        clear=True,
                    ),
                    mock.patch.object(verifier, "load_verified_release") as load,
                    mock.patch.object(verifier, "_open_connection") as connect,
                    redirect_stdout(buffer),
                ):
                    code = verifier.cli(
                        ["identity", "--release-version", RELEASE_VERSION]
                    )

                self.assertEqual(2, code)
                self.assertEqual(
                    "[FAIL] step=VERIFY-DATA-SEED-IDENTITY "
                    "reason=AMBIENT_LIBPQ_ENVIRONMENT_INVALID issues=1\n",
                    buffer.getvalue(),
                )
                self.assertNotIn("synthetic-ambient-value", buffer.getvalue())
                load.assert_not_called()
                connect.assert_not_called()

    def test_concurrency_rejects_ambient_pg_before_release_or_connect(self) -> None:
        buffer = StringIO()
        with (
            mock.patch.dict(
                concurrency.os.environ,
                {
                    "SEJONG_ADMIN_DATABASE_URL": SECRET_DSN,
                    "PGOPTIONS": "synthetic-ambient-value",
                },
                clear=True,
            ),
            mock.patch.object(concurrency, "load_verified_release") as load,
            mock.patch.object(
                concurrency,
                "_scenario_capability_before_seed",
            ) as scenario,
            redirect_stdout(buffer),
        ):
            code = concurrency.cli(
                [
                    "--scenario",
                    concurrency.CAPABILITY_BEFORE_SEED,
                    "--release-version",
                    RELEASE_VERSION,
                ]
            )

        self.assertEqual(2, code)
        self.assertEqual(
            "[FAIL] step=VERIFY-DATA-SEED-CONCURRENCY-A "
            "reason=AMBIENT_LIBPQ_ENVIRONMENT_INVALID issues=1\n",
            buffer.getvalue(),
        )
        self.assertNotIn("synthetic-ambient-value", buffer.getvalue())
        load.assert_not_called()
        scenario.assert_not_called()

    def test_malformed_or_blank_dsn_has_one_stable_error(self) -> None:
        for value in ("", "   ", "not-a-valid-conninfo"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "ADMIN_DSN_IDENTITY_INVALID"):
                    verifier.parse_and_validate_dsn(value)


class ProjectionCanonicalizationTests(unittest.TestCase):
    def test_concurrency_wait_probe_uses_permission_independent_lock_catalog(
        self,
    ) -> None:
        self.assertIn("pg_catalog.pg_locks", concurrency.LOCK_WAIT_QUERY)
        self.assertIn("pg_catalog.pg_blocking_pids", concurrency.LOCK_WAIT_QUERY)
        self.assertIn("NOT locks.granted", concurrency.LOCK_WAIT_QUERY)
        self.assertIn("locks.locktype", concurrency.LOCK_WAIT_QUERY)
        self.assertIn(
            "locks.relation::pg_catalog.regclass::text", concurrency.LOCK_WAIT_QUERY
        )
        self.assertIn("locks.mode", concurrency.LOCK_WAIT_QUERY)
        self.assertNotIn("pg_stat_activity", concurrency.LOCK_WAIT_QUERY)

    def test_concurrency_wait_rejects_wrong_blocker_relation_or_mode(self) -> None:
        unrelated_rows = (
            (
                [999],
                "relation",
                "app_private.interaction_events",
                "RowExclusiveLock",
                False,
            ),
            ([701], "relation", "app_private.audit_logs", "RowExclusiveLock", False),
            ([701], "relation", "app_private.interaction_events", "ShareLock", False),
            ([701], "advisory", None, "ExclusiveLock", False),
        )
        for row in unrelated_rows:
            with self.subTest(row=row):
                connection = _LockProbeConnection([row])
                with (
                    mock.patch.object(
                        concurrency.time,
                        "monotonic",
                        side_effect=[0.0, 1.0, 6.0],
                    ),
                    mock.patch.object(concurrency.time, "sleep"),
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        "CAPABILITY_WRITE_DID_NOT_BLOCK",
                    ):
                        concurrency._wait_until_lock_blocked(connection, 702)

    def test_concurrency_wait_accepts_only_direct_seed_relation_lock(self) -> None:
        connection = _LockProbeConnection(
            [
                (
                    [701],
                    "relation",
                    "app_private.interaction_events",
                    "RowExclusiveLock",
                    False,
                )
            ]
        )
        with mock.patch.object(concurrency.time, "monotonic", side_effect=[0.0, 1.0]):
            concurrency._wait_until_lock_blocked(connection, 702)

        self.assertEqual(1, len(connection.calls))
        self.assertEqual((702, 702), connection.calls[0][1])

    def test_projection_queries_select_only_seed_owned_fields(self) -> None:
        self.assertEqual(
            {
                "kb_documents",
                "kb_question_examples",
                "offices",
                "office_service_mappings",
            },
            set(verifier.PROJECTION_QUERIES),
        )
        for table, query in verifier.PROJECTION_QUERIES.items():
            with self.subTest(table=table):
                self.assertNotIn("SELECT *", query.upper())
                self.assertIn("app_private.", query)
                self.assertIn('COLLATE pg_catalog."C"', query)

    def test_database_values_are_normalized_like_release_projection(self) -> None:
        projection = {
            "kb_documents": [
                {
                    "public_id": "KB-TAX-01",
                    "last_verified_at": date(2026, 7, 18),
                    "approved_at": datetime(
                        2026, 7, 18, 17, 6, 19, tzinfo=timezone.utc
                    ),
                    "procedure_steps": ["a", "b"],
                }
            ],
            "kb_question_examples": [],
            "offices": [],
            "office_service_mappings": [],
        }

        normalized = verifier.canonicalize_database_projection(projection)

        self.assertEqual(
            "2026-07-18", normalized["kb_documents"][0]["last_verified_at"]
        )
        self.assertEqual(
            "2026-07-18T17:06:19Z",
            normalized["kb_documents"][0]["approved_at"],
        )
        self.assertEqual(["a", "b"], normalized["kb_documents"][0]["procedure_steps"])

    def test_database_timestamp_rejects_nonzero_microseconds(self) -> None:
        changed = datetime(
            2026,
            7,
            18,
            17,
            6,
            19,
            1,
            tzinfo=timezone.utc,
        )

        with self.assertRaisesRegex(ValueError, "^TIMESTAMP_PRECISION_INVALID$"):
            verifier._canonical_database_value(changed)

    def test_query_projection_uses_exact_python_codepoint_order(self) -> None:
        rows = {
            "FROM app_private.kb_documents": [("KB-Z",), ("KB-A",)],
            "FROM app_private.kb_question_examples": [],
            "FROM app_private.offices": [],
            "FROM app_private.office_service_mappings": [],
        }
        fields = {
            "kb_documents": ("public_id",),
            "kb_question_examples": ("kb_public_id", "question_example"),
            "offices": ("public_id",),
            "office_service_mappings": ("office_public_id", "intent"),
        }
        with mock.patch.object(verifier, "PROJECTION_FIELDS", fields):
            projection = verifier.query_database_projection(_RowsConnection(rows))

        self.assertEqual(
            ["KB-A", "KB-Z"],
            [row["public_id"] for row in projection["kb_documents"]],
        )


class ReleaseAndOutputBoundaryTests(unittest.TestCase):
    def test_blocked_compensation_injects_probe_before_first_of_two_guards(
        self,
    ) -> None:
        marker = b"\n\nDO $data_seed_empty_guard$"
        payload = b"BEGIN;" + marker + b" first;" + marker + b" second; COMMIT;\n"

        injected = verifier._blocked_compensation_sql(payload)

        self.assertEqual(2, injected.count(marker))
        self.assertEqual(1, injected.count(b"45000000-0000-4000-8000-000000000901"))
        self.assertLess(injected.find(b"45000000"), injected.find(marker))

    def test_release_loader_reverifies_exact_canonical_path_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong seed verifier ") as directory:
            root = Path(directory)
            release = root / "data" / "official" / "releases" / RELEASE_VERSION
            release.mkdir(parents=True)
            summary = {
                "release_version": RELEASE_VERSION,
                "release_id": "sejong-official-0.1.0-initial.1",
                "counts": {"kb": 19, "office": 3, "mapping": 10},
                "seed_semantic_sha256": "a" * 64,
                "seed_sql_bytes": b"BEGIN; SELECT 1; COMMIT;\n",
                "compensation_sql_bytes": b"BEGIN; SELECT 1; COMMIT;\n",
            }
            with (
                mock.patch.object(
                    verifier, "verify_release_directory", return_value=summary
                ) as verify,
                mock.patch.object(
                    verifier,
                    "build_seed_projection",
                    return_value={
                        "kb_documents": [],
                        "kb_question_examples": [],
                        "offices": [],
                        "office_service_mappings": [],
                    },
                ),
                mock.patch.object(verifier, "semantic_sha256", return_value="a" * 64),
            ):
                loaded = verifier.load_verified_release(root, RELEASE_VERSION)

        verify.assert_called_once_with(root.absolute(), release.absolute())
        self.assertEqual("a" * 64, loaded.semantic_sha256)
        self.assertEqual(19, loaded.counts["kb"])

    def test_wrong_release_version_fails_before_release_read(self) -> None:
        with mock.patch.object(verifier, "verify_release_directory") as verify:
            with self.assertRaisesRegex(ValueError, "RELEASE_VERSION_INVALID"):
                verifier.load_verified_release(Path.cwd(), "0.1.0")
        verify.assert_not_called()

    def test_cli_output_never_contains_dsn_release_sql_or_exception_content(
        self,
    ) -> None:
        secret_sql = "SELECT 'synthetic-release-content';"
        buffer = StringIO()
        with (
            mock.patch.dict(
                verifier.os.environ,
                {"SEJONG_ADMIN_DATABASE_URL": SECRET_DSN},
                clear=False,
            ),
            mock.patch.object(
                verifier,
                "load_verified_release",
                side_effect=RuntimeError(secret_sql),
            ),
            redirect_stdout(buffer),
        ):
            code = verifier.cli(["identity", "--release-version", RELEASE_VERSION])

        output = buffer.getvalue()
        self.assertEqual(2, code)
        self.assertRegex(
            output,
            r"^\[FAIL\] step=VERIFY-DATA-SEED-IDENTITY reason=[A-Z0-9_]+ issues=1\n$",
        )
        self.assertNotIn(SECRET_DSN, output)
        self.assertNotIn("synthetic-secret", output)
        self.assertNotIn(secret_sql, output)

    def test_expected_database_error_is_checked_by_sqlstate_and_message(self) -> None:
        matching = SimpleNamespace(
            sqlstate="P0001",
            diag=SimpleNamespace(message_primary="DATA_SEED_DATABASE_NOT_EMPTY"),
        )
        verifier.require_expected_database_error(
            cast(BaseException, matching), "DATA_SEED_DATABASE_NOT_EMPTY"
        )

        wrong = SimpleNamespace(
            sqlstate="P0001",
            diag=SimpleNamespace(message_primary="SOMETHING_ELSE"),
        )
        with self.assertRaisesRegex(ValueError, "EXPECTED_DATABASE_ERROR_MISSING"):
            verifier.require_expected_database_error(
                cast(BaseException, wrong), "DATA_SEED_DATABASE_NOT_EMPTY"
            )


if __name__ == "__main__":
    unittest.main()
