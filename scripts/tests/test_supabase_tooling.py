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
from unittest.mock import patch
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
CHILD_OUTPUT_SENTINEL = "postgresql://synthetic.invalid/private-question-sentinel"


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


def run_database_runner_with_supabase_capture(
    source: str,
    *,
    full_path: bool = False,
    failure_phase: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    runtime_executable = ROOT / "apps" / "api" / ".venv" / "Scripts" / "python.exe"
    if not runtime_executable.is_file():
        raise AssertionError("API venv Python is required for the synthetic runner fixture")

    with tempfile.TemporaryDirectory(prefix="sejong database runner ") as directory:
        root = Path(directory)
        scripts = root / "scripts"
        fake_bin = root / "fake-bin"
        supabase_dir = root / ".tools" / "supabase" / "v2.109.1"
        python_dir = root / "apps" / "api" / ".venv" / "Scripts"
        for path in (scripts, fake_bin, supabase_dir, python_dir):
            path.mkdir(parents=True, exist_ok=True)

        capture_path = root / "supabase-invocations.jsonl"
        if full_path:
            restoration_line = "        Restore-ProcessEnvironment -Saved $savedEnvironment"
            if source.count(restoration_line) != 1:
                raise AssertionError("runner restoration point must be unique")
            instrumentation = restoration_line + '''
        $adminState = if (
            [Environment]::GetEnvironmentVariable(
                "SEJONG_ADMIN_DATABASE_URL", "Process"
            ) -ceq $env:SEJONG_SYNTHETIC_INITIAL_ADMIN
        ) { "restored" } else { "changed" }
        $backendState = if (
            [Environment]::GetEnvironmentVariable(
                "SEJONG_DB_TEST_URL", "Process"
            ) -ceq $env:SEJONG_SYNTHETIC_INITIAL_BACKEND
        ) { "restored" } else { "changed" }
        $environmentLine = '["environment","' + $adminState + '","' + $backendState + '"]'
        [System.IO.File]::AppendAllText(
            $env:SEJONG_SYNTHETIC_SUPABASE_CAPTURE,
            $environmentLine + [Environment]::NewLine,
            [System.Text.Encoding]::UTF8
        )
'''
            source = source.replace(restoration_line, instrumentation)

        runner = scripts / DATABASE_RUNNER_PATH.name
        runner.write_text(source, encoding="utf-8")
        bootstrap_source = "exit 0\n"
        provision_source = "# synthetic fixture\n"
        sql_runner_source = "# synthetic fixture\n"
        if full_path:
            bootstrap_source = (
                f'[Console]::Out.WriteLine("{CHILD_OUTPUT_SENTINEL}")\n'
                f'[Console]::Error.WriteLine("{CHILD_OUTPUT_SENTINEL}")\n'
                "exit 0\n"
            )
            provision_source = f'''
import json
import os
import sys
from pathlib import Path

capture = Path(os.environ["SEJONG_SYNTHETIC_SUPABASE_CAPTURE"])
with capture.open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(["provision"]) + "\\n")
environment_path = Path.cwd() / "apps" / "api" / ".env"
environment_path.parent.mkdir(parents=True, exist_ok=True)
environment_path.write_text(
    "DATABASE_URL=postgresql://synthetic.invalid/backend\\n", encoding="utf-8"
)
print({CHILD_OUTPUT_SENTINEL!r})
print({CHILD_OUTPUT_SENTINEL!r}, file=sys.stderr)
raise SystemExit(0)
'''
            sql_runner_source = f'''
import json
import os
import sys
from pathlib import Path

event = ["sql", *(Path(value).name for value in sys.argv[1:])]
with open(os.environ["SEJONG_SYNTHETIC_SUPABASE_CAPTURE"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps(event) + "\\n")
print({CHILD_OUTPUT_SENTINEL!r})
print({CHILD_OUTPUT_SENTINEL!r}, file=sys.stderr)
raise SystemExit(0)
'''
        (scripts / BOOTSTRAP_PATH.name).write_text(bootstrap_source, encoding="utf-8")
        (scripts / PROVISION_PATH.name).write_text(provision_source, encoding="utf-8")
        (scripts / SQL_RUNNER_PATH.name).write_text(sql_runner_source, encoding="utf-8")

        for destination in (
            fake_bin / "docker.exe",
            supabase_dir / "supabase.exe",
            python_dir / "python.exe",
        ):
            shutil.copy2(runtime_executable, destination)

        version_source = "raise SystemExit(0)\n"
        if full_path:
            version_source = f'''
import sys
print({CHILD_OUTPUT_SENTINEL!r})
print({CHILD_OUTPUT_SENTINEL!r}, file=sys.stderr)
raise SystemExit(0)
'''
        (root / "version").write_text(version_source, encoding="utf-8")
        capture_program = f'''
import json
import os
import sys
from pathlib import Path

invocation = [Path(sys.argv[0]).name, *sys.argv[1:]]
with open(os.environ["SEJONG_SYNTHETIC_SUPABASE_CAPTURE"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps(invocation) + "\\n")
if os.environ.get("SEJONG_SYNTHETIC_FULL_PATH") == "1":
    print({CHILD_OUTPUT_SENTINEL!r})
    print({CHILD_OUTPUT_SENTINEL!r}, file=sys.stderr)
if invocation in (["db", "start"], ["start"]):
    raise SystemExit(0)
if invocation == ["db", "reset", "--local"]:
    raise SystemExit(0 if os.environ.get("SEJONG_SYNTHETIC_FULL_PATH") == "1" else 7)
if invocation == ["status", "-o", "env"]:
    print('DB_URL="postgresql://synthetic.invalid/admin"')
    raise SystemExit(0)
if invocation == ["test", "db"]:
    if os.environ.get("SEJONG_SYNTHETIC_FAILURE_PHASE") == "pgtap-one":
        raise SystemExit(17)
    raise SystemExit(0)
raise SystemExit(9)
'''
        commands = ("db", "start", "status", "test") if full_path else ("db", "start")
        for command in commands:
            (root / command).write_text(capture_program, encoding="utf-8")

        if full_path:
            pytest_package = root / "pytest"
            pytest_package.mkdir()
            (pytest_package / "__init__.py").write_text("", encoding="utf-8")
            (pytest_package / "__main__.py").write_text(
                f'''
import json
import os
import sys
from pathlib import Path

event = ["pytest", Path(sys.argv[-1]).name]
with open(os.environ["SEJONG_SYNTHETIC_SUPABASE_CAPTURE"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps(event) + "\\n")
print({CHILD_OUTPUT_SENTINEL!r})
print({CHILD_OUTPUT_SENTINEL!r}, file=sys.stderr)
if os.environ.get("SEJONG_SYNTHETIC_FAILURE_PHASE") == "integration":
    raise SystemExit(19)
raise SystemExit(0)
''',
                encoding="utf-8",
            )

        environment = {
            key: os.environ[key]
            for key in ("COMSPEC", "PATHEXT", "SystemRoot", "TEMP", "TMP", "WINDIR")
            if key in os.environ
        }
        environment["PATH"] = str(fake_bin)
        environment["SEJONG_SYNTHETIC_SUPABASE_CAPTURE"] = str(capture_path)
        if full_path:
            environment["SEJONG_SYNTHETIC_FULL_PATH"] = "1"
            environment["SEJONG_SYNTHETIC_FAILURE_PHASE"] = failure_phase or ""
            environment["SEJONG_SYNTHETIC_INITIAL_ADMIN"] = "initial-admin-sentinel"
            environment["SEJONG_SYNTHETIC_INITIAL_BACKEND"] = "initial-backend-sentinel"
            environment["SEJONG_ADMIN_DATABASE_URL"] = environment[
                "SEJONG_SYNTHETIC_INITIAL_ADMIN"
            ]
            environment["SEJONG_DB_TEST_URL"] = environment[
                "SEJONG_SYNTHETIC_INITIAL_BACKEND"
            ]
        result = subprocess.run(
            [
                powershell_executable(),
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(runner),
            ],
            cwd=root,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            env=environment,
            timeout=30,
        )
        invocations = []
        if capture_path.is_file():
            invocations = [
                json.loads(line)
                for line in capture_path.read_text(encoding="utf-8").splitlines()
            ]
        return result, invocations


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

    def test_env_update_replace_failure_keeps_original_and_cleans_temp(self) -> None:
        module = load_module(PROVISION_PATH, "provision_local_database_login_atomic_test")
        original = (
            b"# synthetic local configuration\r\n"
            b"DATABASE_URL=old-local-value\r\n"
            b"LLM_API_KEY=synthetic-deepseek-sentinel\r\n"
        )
        expected_staged = original.replace(
            b"DATABASE_URL=old-local-value",
            b"DATABASE_URL=postgresql://local.invalid/rotated",
        )
        with tempfile.TemporaryDirectory(prefix="sejong env atomic ") as directory:
            root = Path(directory)
            env_path = root / ".env"
            env_path.write_bytes(original)

            def fail_after_complete_write(source: str | Path, destination: str | Path) -> None:
                staged_path = Path(source)
                self.assertEqual(Path(destination), env_path)
                self.assertEqual(staged_path.parent, env_path.parent)
                self.assertTrue(staged_path.name.startswith(".env."))
                self.assertEqual(staged_path.read_bytes(), expected_staged)
                raise OSError("synthetic replace failure")

            with patch.object(module.os, "replace", side_effect=fail_after_complete_write):
                with self.assertRaises(OSError):
                    module.update_env_assignment(
                        env_path,
                        "DATABASE_URL",
                        "postgresql://local.invalid/rotated",
                    )

            self.assertEqual(env_path.read_bytes(), original)
            self.assertEqual(list(root.glob(".env.*")), [])

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

    def test_database_runner_starts_only_postgres_with_exact_cli_arguments(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")

        result, invocations = run_database_runner_with_supabase_capture(script)

        self.assertEqual(result.returncode, 7)
        self.assertFalse(result.stderr)
        self.assertEqual(
            invocations,
            [["db", "start"], ["db", "reset", "--local"]],
        )
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "[START] step=PREFLIGHT-DOCKER",
                "[PASS] step=PREFLIGHT-DOCKER",
                "[START] step=VERIFY-SUPABASE-VERSION",
                "[PASS] step=VERIFY-SUPABASE-VERSION",
                "[START] step=START-LOCAL-DATABASE",
                "[PASS] step=START-LOCAL-DATABASE",
                "[START] step=RESET-DATABASE-ONE",
                "[FAIL] step=RESET-DATABASE-ONE reason=child code=7",
            ],
        )

    def test_database_start_capture_rejects_dead_exact_block_and_live_bare_call(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")
        exact_block = '''    if (-not $skipStart) {
        $null = Invoke-DatabaseStep `
            -Step "START-LOCAL-DATABASE" `
            -FilePath $supabaseBinary `
            -Arguments @("db", "start") `
            -WorkingDirectory $repositoryRoot
    }
'''
        mutant_block = '''    if (-not $skipStart) {
        if ($false) {
            $null = Invoke-DatabaseStep `
                -Step "START-LOCAL-DATABASE" `
                -FilePath $supabaseBinary `
                -Arguments @("db", "start") `
                -WorkingDirectory $repositoryRoot
        }
        $null = & $supabaseBinary start
        if ($LASTEXITCODE -ne 0) {
            Throw-DatabaseGateFailure `
                -Step "START-LOCAL-DATABASE" `
                -Reason "child" `
                -Code $LASTEXITCODE
        }
    }
'''
        self.assertEqual(script.count(exact_block), 1)
        mutant = script.replace(exact_block, mutant_block)

        result, invocations = run_database_runner_with_supabase_capture(mutant)

        self.assertEqual(result.returncode, 7)
        self.assertFalse(result.stderr)
        self.assertEqual(invocations, [["start"], ["db", "reset", "--local"]])
        self.assertNotEqual(
            invocations,
            [["db", "start"], ["db", "reset", "--local"]],
        )

    def test_database_start_capture_rejects_extra_live_bare_call(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")
        exact_block = '''    if (-not $skipStart) {
        $null = Invoke-DatabaseStep `
            -Step "START-LOCAL-DATABASE" `
            -FilePath $supabaseBinary `
            -Arguments @("db", "start") `
            -WorkingDirectory $repositoryRoot
    }
'''
        mutant_block = exact_block.replace(
            "    }\n",
            "        $null = & $supabaseBinary start\n    }\n",
        )
        self.assertEqual(script.count(exact_block), 1)
        mutant = script.replace(exact_block, mutant_block)

        result, invocations = run_database_runner_with_supabase_capture(mutant)

        self.assertEqual(result.returncode, 7)
        self.assertFalse(result.stderr)
        self.assertEqual(
            invocations,
            [["db", "start"], ["start"], ["db", "reset", "--local"]],
        )
        self.assertNotEqual(
            invocations,
            [["db", "start"], ["db", "reset", "--local"]],
        )

    def test_database_runner_uses_exact_newest_first_compensation_order(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")
        rollback_paths = re.findall(
            r'database\\rollbacks\\([^"\r\n]+\.rollback\.sql)',
            script,
        )

        self.assertEqual(
            rollback_paths,
            [
                "20260717000600_deferred_active_question_trigger_security.rollback.sql",
                "20260716000500_indexes_and_read_interfaces.rollback.sql",
                "20260716000400_candidate_workflow.rollback.sql",
                "20260716000300_capabilities_and_functions.rollback.sql",
                "20260716000200_invariants_and_lineage.rollback.sql",
                "20260716000100_private_schema.rollback.sql",
            ],
        )

    def test_database_runner_full_path_orders_replay_and_restores_environment(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")

        result, invocations = run_database_runner_with_supabase_capture(
            script,
            full_path=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertFalse(result.stderr)
        self.assertFalse(CHILD_OUTPUT_SENTINEL in result.stdout)
        self.assertEqual(
            invocations,
            [
                ["db", "start"],
                ["db", "reset", "--local"],
                ["status", "-o", "env"],
                ["provision"],
                ["test", "db"],
                [
                    "sql",
                    "20260717000600_deferred_active_question_trigger_security.rollback.sql",
                    "20260716000500_indexes_and_read_interfaces.rollback.sql",
                    "20260716000400_candidate_workflow.rollback.sql",
                    "20260716000300_capabilities_and_functions.rollback.sql",
                    "20260716000200_invariants_and_lineage.rollback.sql",
                    "20260716000100_private_schema.rollback.sql",
                ],
                ["sql", "verify_db001_absent.sql"],
                ["db", "reset", "--local"],
                ["provision"],
                ["test", "db"],
                ["pytest", "test_integration.py"],
                ["environment", "restored", "restored"],
            ],
        )
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "[START] step=PREFLIGHT-DOCKER",
                "[PASS] step=PREFLIGHT-DOCKER",
                "[START] step=VERIFY-SUPABASE-VERSION",
                "[PASS] step=VERIFY-SUPABASE-VERSION",
                "[START] step=START-LOCAL-DATABASE",
                "[PASS] step=START-LOCAL-DATABASE",
                "[START] step=RESET-DATABASE-ONE",
                "[PASS] step=RESET-DATABASE-ONE",
                "[START] step=PROVISION-LOCAL-DB-LOGIN-ONE",
                "[PASS] step=PROVISION-LOCAL-DB-LOGIN-ONE",
                "[START] step=TEST-PGTAP-ONE",
                "[PASS] step=TEST-PGTAP-ONE",
                "[START] step=ROLLBACK-DB001",
                "[PASS] step=ROLLBACK-DB001",
                "[START] step=VERIFY-DB001-ABSENT",
                "[PASS] step=VERIFY-DB001-ABSENT",
                "[START] step=RESET-DATABASE-TWO",
                "[PASS] step=RESET-DATABASE-TWO",
                "[START] step=PROVISION-LOCAL-DB-LOGIN-TWO",
                "[PASS] step=PROVISION-LOCAL-DB-LOGIN-TWO",
                "[START] step=TEST-PGTAP-TWO",
                "[PASS] step=TEST-PGTAP-TWO",
                "[START] step=TEST-DATABASE-INTEGRATION",
                "[PASS] step=TEST-DATABASE-INTEGRATION",
            ],
        )

    def test_database_runner_propagates_pgtap_failure_and_restores_environment(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")

        result, invocations = run_database_runner_with_supabase_capture(
            script,
            full_path=True,
            failure_phase="pgtap-one",
        )

        self.assertEqual(result.returncode, 17)
        self.assertFalse(result.stderr)
        self.assertFalse(CHILD_OUTPUT_SENTINEL in result.stdout)
        self.assertEqual(invocations[-1], ["environment", "restored", "restored"])
        self.assertEqual(
            result.stdout.splitlines()[-1],
            "[FAIL] step=TEST-PGTAP-ONE reason=child code=17",
        )

    def test_database_runner_propagates_integration_failure_without_child_output(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")

        result, invocations = run_database_runner_with_supabase_capture(
            script,
            full_path=True,
            failure_phase="integration",
        )

        self.assertEqual(result.returncode, 19)
        self.assertFalse(result.stderr)
        self.assertFalse(CHILD_OUTPUT_SENTINEL in result.stdout)
        self.assertEqual(invocations[-2], ["pytest", "test_integration.py"])
        self.assertEqual(invocations[-1], ["environment", "restored", "restored"])
        self.assertEqual(
            result.stdout.splitlines()[-1],
            "[FAIL] step=TEST-DATABASE-INTEGRATION reason=child code=19",
        )

    def test_database_runner_source_never_names_external_llm_key(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")
        forbidden_name = "LLM" + "_" + "API" + "_" + "KEY"

        self.assertNotIn(forbidden_name, script)


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
