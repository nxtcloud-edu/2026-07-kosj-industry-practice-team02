from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import ModuleType
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
PIN_PATH = ROOT / "scripts" / "supabase-cli.version.json"
BOOTSTRAP_PATH = ROOT / "scripts" / "bootstrap_supabase.ps1"
CONFIG_PATH = ROOT / "supabase" / "config.toml"
SEED_PATH = ROOT / "supabase" / "seed.sql"
PROVISION_PATH = ROOT / "scripts" / "provision_local_database_login.py"
SQL_RUNNER_PATH = ROOT / "scripts" / "run_database_sql.py"
DATABASE_RUNNER_PATH = ROOT / "scripts" / "verify_database.ps1"
EXPECTED_PIN = {
    "version": "2.109.1",
    "release": "v2.109.1",
    "published_at": "2026-07-07T09:00:28Z",
    "asset": "supabase_2.109.1_windows_amd64.zip",
    "size_bytes": 75309565,
    "url": (
        "https://github.com/supabase/cli/releases/download/v2.109.1/"
        "supabase_2.109.1_windows_amd64.zip"
    ),
    "sha256": "d0d270692cf78b8aa56545461f02cdf929ce9bb94e95e5e66404fd0e7d2c0c16",
}


def powershell_executable() -> str:
    executable = shutil.which("powershell.exe") or shutil.which("powershell")
    if executable is None:
        raise AssertionError("Windows PowerShell 5.1+ is required")
    return executable


def copy_tooling_fixture(root: Path, *, url: str | None = None) -> Path:
    if not BOOTSTRAP_PATH.is_file():
        raise AssertionError(f"missing required tooling file: {BOOTSTRAP_PATH.name}")
    if not PIN_PATH.is_file():
        raise AssertionError(f"missing required tooling file: {PIN_PATH.name}")
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(BOOTSTRAP_PATH, scripts / BOOTSTRAP_PATH.name)
    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    if url is not None:
        pin["url"] = url
    (scripts / PIN_PATH.name).write_text(
        json.dumps(pin, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return scripts / BOOTSTRAP_PATH.name


def run_bootstrap(
    script: Path, *arguments: str, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            powershell_executable(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            *arguments,
        ],
        cwd=cwd,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )


def load_module(path: Path, name: str) -> ModuleType:
    if not path.is_file():
        raise AssertionError(f"missing required tooling file: {path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load tooling module: {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_python_tool(path: Path, *arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    if env is not None:
        environment.update(env)
    return subprocess.run(
        [str(ROOT / "apps" / "api" / ".venv" / "Scripts" / "python.exe"), "-B", str(path), *arguments],
        cwd=ROOT,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        env=environment,
        timeout=20,
    )


class SupabaseToolPinTests(unittest.TestCase):
    def read_required_text(self, path: Path) -> str:
        self.assertTrue(path.is_file(), f"missing required tooling file: {path.name}")
        return path.read_text(encoding="utf-8")

    def test_exact_official_windows_pin(self) -> None:
        pin = json.loads(self.read_required_text(PIN_PATH))

        self.assertEqual(pin, EXPECTED_PIN)
        parsed_url = urlparse(pin["url"])
        self.assertEqual(parsed_url.scheme, "https")
        self.assertEqual(parsed_url.hostname, "github.com")

    def test_bootstrap_is_local_checksum_gated_and_non_secret(self) -> None:
        script = self.read_required_text(BOOTSTRAP_PATH)
        lowered = script.lower()

        self.assertIn("Get-FileHash", script)
        self.assertIn("Expand-Archive", script)
        self.assertIn(".tools\\supabase", script)
        self.assertIn("$PSScriptRoot", script)
        self.assertIn("--version", script)
        self.assertIn("[PASS] step=VERIFY-SUPABASE-ARCHIVE", script)
        self.assertIn("[PASS] step=VERIFY-SUPABASE-VERSION", script)
        self.assertIsNone(
            re.match(r"\A\s*param\(", script),
            "typed top-level binding can disclose argument errors before controlled handling",
        )
        self.assertIn('"-VerifyOnly"', script)
        self.assertIn('"-ArchivePath"', script)
        self.assertNotIn("Get-Location", script)
        for forbidden_operation in (
            "npm install",
            "winget",
            "supabase login",
            "supabase link",
            "supabase db push",
        ):
            self.assertNotIn(forbidden_operation, lowered)


class LocalDatabaseToolingContractTests(unittest.TestCase):
    def test_local_config_runs_database_only_and_exposes_no_app_schema(self) -> None:
        config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))

        self.assertEqual(config["project_id"], "sejong-ai-local")
        self.assertEqual(config["db"]["port"], 54322)
        self.assertEqual(config["db"]["major_version"], 17)
        self.assertFalse(config["api"]["enabled"])
        self.assertEqual(config["api"]["schemas"], ["public", "graphql_public"])
        self.assertEqual(config["api"]["extra_search_path"], ["public", "extensions"])
        self.assertFalse(config["auth"]["enabled"])
        self.assertFalse(config["realtime"]["enabled"])
        self.assertFalse(config["storage"]["enabled"])
        self.assertFalse(config["studio"]["enabled"])
        self.assertFalse(config["local_smtp"]["enabled"])
        self.assertNotIn("inbucket", config)
        self.assertFalse(config["analytics"]["enabled"])
        self.assertFalse(config["edge_runtime"]["enabled"])
        self.assertFalse(config["db"]["pooler"]["enabled"])
        self.assertFalse(config["db"]["seed"]["enabled"])
        self.assertEqual(config["db"]["seed"]["sql_paths"], ["./seed.sql"])
        exposed = config["api"]["schemas"] + config["api"]["extra_search_path"]
        self.assertNotIn("app_private", exposed)
        self.assertNotIn("app_api", exposed)

    def test_seed_is_intentionally_empty_and_names_data_owners(self) -> None:
        seed = SEED_PATH.read_text(encoding="utf-8")

        self.assertEqual(
            seed,
            "-- DB-001 deliberately contains no official or mock seed.\n"
            "-- DATA-001 and DATA-SEED-001 own PM-approved data and versioned lineage.\n"
            "-- An empty approved-data set must keep /ready at HTTP 503.\n",
        )

    def test_env_update_preserves_every_non_target_byte(self) -> None:
        module = load_module(PROVISION_PATH, "provision_local_database_login_test")
        self.assertEqual(module.ROLE_NAME, "sejong_local_login")
        self.assertEqual(module.TARGET_ENV_KEY, "DATABASE_URL")
        original = (
            b"# synthetic local configuration\r\n"
            b"APP_ENV=development\r\n"
            b"DATABASE_URL=old-local-value\r\n"
            b"\r\n"
            b"LLM_API_KEY=synthetic-deepseek-sentinel\r\n"
            b"LOG_LEVEL=INFO\r\n"
        )
        expected = original.replace(
            b"DATABASE_URL=old-local-value",
            b"DATABASE_URL=postgresql://local.invalid/new-value",
        )
        with tempfile.TemporaryDirectory(prefix="sejong env update ") as directory:
            env_path = Path(directory) / ".env"
            env_path.write_bytes(original)

            module.update_env_assignment(
                env_path,
                "DATABASE_URL",
                "postgresql://local.invalid/new-value",
            )

            self.assertEqual(env_path.read_bytes(), expected)

    def test_env_update_appends_target_without_rewriting_existing_bytes(self) -> None:
        module = load_module(PROVISION_PATH, "provision_local_database_login_append_test")
        original = b"# keep\nLLM_API_KEY=synthetic-deepseek-sentinel"
        with tempfile.TemporaryDirectory(prefix="sejong env append ") as directory:
            env_path = Path(directory) / ".env"
            env_path.write_bytes(original)

            module.update_env_assignment(env_path, "DATABASE_URL", "postgresql://local.invalid/new")

            self.assertEqual(
                env_path.read_bytes(),
                original + b"\nDATABASE_URL=postgresql://local.invalid/new\n",
            )

    def test_provisioner_missing_admin_dsn_is_stable(self) -> None:
        environment = os.environ.copy()
        environment.pop("SEJONG_ADMIN_DATABASE_URL", None)
        result = subprocess.run(
            [
                str(ROOT / "apps" / "api" / ".venv" / "Scripts" / "python.exe"),
                "-B",
                str(PROVISION_PATH),
            ],
            cwd=ROOT,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            env=environment,
            timeout=20,
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stdout.strip(),
            "[FAIL] step=PROVISION-LOCAL-DB-LOGIN reason=missing-admin-dsn code=2",
        )
        self.assertFalse(result.stderr)

    def test_database_sql_runner_rejects_empty_and_outside_paths(self) -> None:
        missing_environment = {"SEJONG_ADMIN_DATABASE_URL": ""}
        empty = run_python_tool(SQL_RUNNER_PATH, env=missing_environment)
        outside = run_python_tool(
            SQL_RUNNER_PATH,
            str(ROOT / "README.md"),
            env=missing_environment,
        )

        self.assertEqual(empty.returncode, 2)
        self.assertEqual(
            empty.stdout.strip(),
            "[FAIL] step=RUN-DATABASE-SQL reason=invalid-files code=2",
        )
        self.assertEqual(outside.returncode, 2)
        self.assertEqual(
            outside.stdout.strip(),
            "[FAIL] step=RUN-DATABASE-SQL reason=invalid-files code=2",
        )
        self.assertFalse(empty.stderr or outside.stderr)

    def test_database_runner_has_no_remote_or_destructive_host_commands(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8").lower()
        for forbidden in ("db push", "link", "login", "projects", "volume prune", "system prune"):
            self.assertNotIn(forbidden, script)
        self.assertIn("db reset", script)
        self.assertIn("test db", script)
        self.assertIn('"-skipstart"', script)
        self.assertIn('"-skiprollbackreplay"', script)

    def test_database_runner_uses_exact_newest_first_compensation_order(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")
        rollback_paths = re.findall(
            r'database\\rollbacks\\([^"\r\n]+\.rollback\.sql)',
            script,
        )

        self.assertEqual(
            rollback_paths,
            [
                "20260716000400_indexes_and_read_interfaces.rollback.sql",
                "20260716000300_capabilities_and_functions.rollback.sql",
                "20260716000200_invariants_and_lineage.rollback.sql",
                "20260716000100_private_schema.rollback.sql",
            ],
        )


class SupabaseBootstrapBehaviorTests(unittest.TestCase):
    def assert_stable_output(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertFalse(result.stderr, "bootstrap wrote to stderr")
        for line in result.stdout.splitlines():
            self.assertRegex(
                line,
                r"^\[(?:START|PASS|FAIL)\] step=[A-Z0-9-]+"
                r"(?: reason=[a-z-]+ code=[012])?$",
            )

    def test_verify_only_missing_is_stable_and_never_downloads(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong supabase verify ") as directory:
            root = Path(directory)
            script = copy_tooling_fixture(root)
            unrelated_cwd = root / "unrelated-current-directory"
            unrelated_cwd.mkdir()

            result = run_bootstrap(script, "-VerifyOnly", cwd=unrelated_cwd)

            self.assertEqual(result.returncode, 2)
            self.assertEqual(
                result.stdout.strip(),
                "[FAIL] step=VERIFY-SUPABASE-BINARY reason=missing code=2",
            )
            self.assertFalse((root / ".tools").exists(), "verify-only created local tooling")
            self.assert_stable_output(result)

    def test_archive_path_without_value_is_controlled_before_typed_binding(self) -> None:
        result = run_bootstrap(BOOTSTRAP_PATH, "-ArchivePath", cwd=ROOT)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stdout.strip(),
            "[FAIL] step=VALIDATE-SUPABASE-ARGUMENTS reason=invalid code=2",
        )
        self.assertFalse(result.stderr, "missing value wrote localized binding details")
        combined = result.stdout + result.stderr
        self.assertNotIn(str(ROOT), combined)
        self.assertNotIn(str(BOOTSTRAP_PATH), combined)
        self.assert_stable_output(result)

    def test_duplicate_approved_arguments_are_controlled(self) -> None:
        cases = (
            ("-VerifyOnly", "-VerifyOnly"),
            (
                "-ArchivePath",
                "synthetic-first-archive.zip",
                "-ArchivePath",
                "synthetic-second-archive.zip",
            ),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = run_bootstrap(BOOTSTRAP_PATH, *arguments, cwd=ROOT)

                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    result.stdout.strip(),
                    "[FAIL] step=VALIDATE-SUPABASE-ARGUMENTS reason=invalid code=2",
                )
                self.assertFalse(result.stderr, "duplicate argument wrote binding details")
                for value in arguments:
                    self.assertNotIn(value, result.stdout + result.stderr)
                self.assert_stable_output(result)

    def test_unapproved_argument_is_rejected_before_other_work(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong supabase arguments ") as directory:
            root = Path(directory)
            script = copy_tooling_fixture(root)

            result = run_bootstrap(
                script,
                "-VerifyOnly",
                "-UnapprovedArgument",
                cwd=root,
            )

            self.assertEqual(result.returncode, 2)
            self.assertEqual(
                result.stdout.strip(),
                "[FAIL] step=VALIDATE-SUPABASE-ARGUMENTS reason=invalid code=2",
            )
            self.assertFalse((root / ".tools").exists(), "invalid arguments started work")
            self.assert_stable_output(result)

    def test_verify_only_uses_release_directory_and_rejects_wrong_child_version(self) -> None:
        harmless_executable = shutil.which("whoami.exe") or shutil.which("whoami")
        if harmless_executable is None:
            self.fail("a harmless synthetic child executable is required")

        with tempfile.TemporaryDirectory(prefix="sejong supabase child ") as directory:
            root = Path(directory)
            script = copy_tooling_fixture(root)
            binary = root / ".tools" / "supabase" / "v2.109.1" / "supabase.exe"
            binary.parent.mkdir(parents=True)
            shutil.copy2(harmless_executable, binary)

            result = run_bootstrap(script, "-VerifyOnly", cwd=root)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                result.stdout.splitlines(),
                [
                    "[START] step=VERIFY-SUPABASE-VERSION",
                    "[FAIL] step=VERIFY-SUPABASE-VERSION reason=child code=1",
                ],
            )
            self.assertNotIn(binary.name, result.stdout + result.stderr)
            self.assert_stable_output(result)

    def test_same_size_invalid_checksum_fails_without_disclosure_or_extraction(self) -> None:
        marker = b"synthetic-invalid-supabase-archive-value"
        with tempfile.TemporaryDirectory(prefix="sejong supabase checksum ") as directory:
            root = Path(directory)
            script = copy_tooling_fixture(root)
            archive = root / "synthetic-invalid-archive-path.zip"
            with archive.open("wb") as stream:
                stream.write(marker)
                stream.truncate(EXPECTED_PIN["size_bytes"])
            with archive.open("rb") as stream:
                synthetic_digest = hashlib.file_digest(stream, "sha256").hexdigest()

            result = run_bootstrap(script, "-ArchivePath", str(archive), cwd=root)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                result.stdout.splitlines(),
                [
                    "[START] step=VERIFY-SUPABASE-ARCHIVE",
                    "[FAIL] step=VERIFY-SUPABASE-ARCHIVE reason=integrity code=1",
                ],
            )
            combined = result.stdout + result.stderr
            for sensitive_value in (marker.decode("ascii"), archive.name, synthetic_digest):
                self.assertNotIn(sensitive_value, combined)
            self.assertFalse((root / ".tools").exists(), "invalid archive was extracted")
            self.assert_stable_output(result)

    def test_unapproved_url_or_host_is_rejected_without_network(self) -> None:
        urls = (
            "http://github.com/supabase/cli/releases/download/v2.109.1/"
            "supabase_2.109.1_windows_amd64.zip",
            "https://example.com/supabase_2.109.1_windows_amd64.zip",
        )
        for url in urls:
            with self.subTest(url=url), tempfile.TemporaryDirectory(
                prefix="sejong supabase source "
            ) as directory:
                root = Path(directory)
                script = copy_tooling_fixture(root, url=url)
                local_archive = root / "local-source-rejection-fixture.zip"
                local_archive.write_bytes(b"offline-only")

                result = run_bootstrap(
                    script,
                    "-ArchivePath",
                    str(local_archive),
                    cwd=root,
                )

                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    result.stdout.strip(),
                    "[FAIL] step=VALIDATE-SUPABASE-MANIFEST "
                    "reason=unapproved-source code=2",
                )
                self.assertFalse((root / ".tools").exists(), "rejected source was downloaded")
                self.assertNotIn(url, result.stdout + result.stderr)
                self.assert_stable_output(result)


if __name__ == "__main__":
    unittest.main()
