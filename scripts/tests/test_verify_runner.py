from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "scripts" / "verify.ps1"
POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")

STAGE_IDS = (
    "PREFLIGHT-POWERSHELL",
    "PREFLIGHT-NODE",
    "PREFLIGHT-PNPM",
    "PREFLIGHT-UV",
    "INSTALL-PNPM",
    "SYNC-API",
    "PREFLIGHT-API-PYTHON",
    "TEST-ROOT",
    "VALIDATE-DATA-001",
    "TEST-DATA-SEED",
    "VERIFY-DATA-SEED-RELEASE-INITIAL",
    "VERIFY-DATA-SEED-RELEASE-SUCCESSOR",
    "VERIFY-LOCAL-SEED",
    "LINT-WEB",
    "TYPECHECK-WEB",
    "TEST-WEB",
    "INSTALL-WEB-E2E",
    "CHECK-WEB-PROD-DEPENDENCY-BOUNDARY",
    "BUILD-WEB-SENTINEL",
    "FORMAT-API",
    "LINT-API",
    "TYPECHECK-API",
    "TEST-API",
    "CHECK-CONTRACT-GENERATED",
    "GENERATE-CONTRACT",
    "DIFF-CONTRACT-GENERATED",
    "TEST-CONTRACT",
    "SCAN-REPOSITORY-SECRETS",
    "SCAN-WEB-BUNDLE",
    "VALIDATE-PACKAGE",
    "CHECK-DIFF",
)


def read_verify() -> str:
    if not VERIFY.is_file():
        raise AssertionError("scripts/verify.ps1 is required")
    return VERIFY.read_text(encoding="utf-8")


def run_verify(
    *,
    environment: dict[str, str] | None = None,
    cwd: Path | None = None,
    arguments: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    if POWERSHELL is None:
        raise AssertionError("Windows PowerShell is required")
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(VERIFY),
            *arguments,
        ],
        cwd=cwd or ROOT,
        env=environment,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )


def run_powershell_command(
    command: str,
    *,
    environment: dict[str, str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    if POWERSHELL is None:
        raise AssertionError("Windows PowerShell is required")
    return subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=cwd,
        env=environment,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )


class VerifyRunnerStructureTest(unittest.TestCase):
    def test_declares_only_the_offline_public_option_and_uses_repo_root(self) -> None:
        source = read_verify()
        preamble = source.split("Set-StrictMode", 1)[0]

        self.assertIn("param(", source)
        self.assertEqual(re.findall(r"\[switch\]\$(\w+)", preamble), ["Offline"])
        self.assertNotIn("[CmdletBinding()]", source)
        self.assertNotIn("[switch]$Test", source)
        self.assertIn("$PSScriptRoot", source)
        self.assertIn("Push-Location", source)
        self.assertIn("Pop-Location", source)

    def test_wires_stages_to_approved_tools_and_root_relative_paths(self) -> None:
        source = read_verify()
        compact = re.sub(r"\s+", " ", source)

        required_wiring = (
            '-StepId "PREFLIGHT-NODE" -Executable "node"',
            '-StepId "PREFLIGHT-PNPM" -Executable "corepack.cmd"',
            '$repoUv = Join-Path $repoRoot ".tools\\uv\\uv.exe"',
            '$uvExecutable = "uv"',
            '-StepId "PREFLIGHT-UV" -Executable $uvExecutable',
            '-StepId "INSTALL-PNPM" -Executable "corepack.cmd" -Arguments $PnpmInstallArguments',
            '-StepId "SYNC-API" -Executable $uvExecutable -Arguments $UvSyncArguments',
            '$apiPython = Join-Path $repoRoot "apps\\api\\.venv\\Scripts\\python.exe"',
            '-StepId "PREFLIGHT-API-PYTHON" -Executable $apiPython',
            '-StepId "TEST-ROOT" -Executable $apiPython',
            '-StepId "VALIDATE-DATA-001" -Executable $apiPython',
            '-StepId "TEST-DATA-SEED" -Executable $apiPython',
            '-StepId "VERIFY-DATA-SEED-RELEASE-INITIAL" -Executable $apiPython',
            '-StepId "VERIFY-DATA-SEED-RELEASE-SUCCESSOR" -Executable $apiPython',
            '-StepId "VERIFY-LOCAL-SEED" -Executable $apiPython',
            '-StepId "LINT-WEB" -Executable "corepack.cmd"',
            '-StepId "TYPECHECK-WEB" -Executable "corepack.cmd"',
            '-StepId "TEST-WEB" -Executable "corepack.cmd"',
            '-StepId "INSTALL-WEB-E2E" -Executable "corepack.cmd"',
            '-StepId "CHECK-WEB-PROD-DEPENDENCY-BOUNDARY" -Executable "node"',
            '-StepId "FORMAT-API" -Executable $uvExecutable',
            '-StepId "LINT-API" -Executable $uvExecutable',
            '-StepId "TYPECHECK-API" -Executable $uvExecutable',
            '-StepId "TEST-API" -Executable $uvExecutable',
            '-StepId "CHECK-CONTRACT-GENERATED" -Executable "corepack.cmd"',
            '-StepId "GENERATE-CONTRACT" -Executable "corepack.cmd"',
            '-StepId "DIFF-CONTRACT-GENERATED" -Executable "git"',
            '-StepId "TEST-CONTRACT" -Executable "corepack.cmd"',
            '-StepId "SCAN-REPOSITORY-SECRETS" -Executable "powershell.exe"',
            '-StepId "VALIDATE-PACKAGE" -Executable $apiPython',
            '-StepId "CHECK-DIFF" -Executable "git"',
        )
        for wiring in required_wiring:
            with self.subTest(wiring=wiring):
                self.assertIn(wiring, compact)

        self.assertLess(compact.find('Test-Path -LiteralPath $repoUv'), compact.find('$uvExecutable = "uv"'))
        self.assertIn('$uvRunArguments += "--offline"', source)
        self.assertEqual(source.count('$uvRunArguments + @('), 4)
        self.assertLess(
            source.find("Enter-RunnerEnvironment"),
            source.find('Invoke-NativeStep -StepId "PREFLIGHT-NODE"'),
        )
        self.assertGreater(source.rfind("Exit-RunnerEnvironment"), source.rfind('StepId "CHECK-DIFF"'))

    def test_runs_focused_data_seed_gate_after_data001_without_db_or_mutation(self) -> None:
        source = read_verify()
        compact = re.sub(r"\s+", " ", source)

        focused_arguments = (
            '"-B", "-m", "unittest", "-v", '
            '"scripts.tests.test_data_seed_release", '
            '"scripts.tests.test_promote_data_seed", '
            '"scripts.tests.test_verify_data_seed_db", '
            '"scripts.tests.test_verify_data_seed_runner"'
        )
        self.assertIn(focused_arguments, compact)
        self.assertIn(
            '"-B", "scripts/promote_data_seed.py", "verify-release", '
            '"--release-dir", $dataSeedInitialReleaseToken',
            compact,
        )
        self.assertIn(
            '"-B", "scripts/promote_data_seed.py", "verify-release", '
            '"--release-dir", $dataSeedSuccessorReleaseToken',
            compact,
        )
        self.assertIn(
            '"-B", "scripts/promote_data_seed.py", "verify-local-seed", '
            '"--release-dir", $dataSeedSuccessorReleaseToken',
            compact,
        )
        self.assertIn(
            '$dataSeedInitialReleaseToken = "data/official/releases/0.1.0-initial.1"',
            source,
        )
        self.assertIn(
            '$dataSeedSuccessorReleaseToken = "data/official/releases/0.1.0-initial.2"',
            source,
        )
        self.assertIn('"release_manifest.json"', source)
        self.assertIn(
            '"data\\schemas\\data-seed\\v1\\release-manifest.schema.json"',
            source,
        )
        self.assertIn(
            '"data\\schemas\\data-seed\\v2\\release-manifest.schema.json"',
            source,
        )
        self.assertIn('"supabase\\seed.sql"', source)
        self.assertLess(
            source.find('-StepId "VALIDATE-DATA-001"'),
            source.find('-StepId "TEST-DATA-SEED"'),
        )
        for forbidden in (
            "verify_data_seed.ps1",
            "verify_data_seed_db.py",
            "test_data_seed_concurrency.py",
            '"prepare"',
            "activate-local-seed",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

        initial = source.find('-StepId "VERIFY-DATA-SEED-RELEASE-INITIAL"')
        successor = source.find('-StepId "VERIFY-DATA-SEED-RELEASE-SUCCESSOR"')
        local = source.find('-StepId "VERIFY-LOCAL-SEED"')
        self.assertLess(initial, successor)
        self.assertLess(successor, local)

    def test_has_all_stable_stage_ids_in_the_required_order(self) -> None:
        source = read_verify()
        positions = []
        for stage_id in STAGE_IDS:
            position = source.find(f'"{stage_id}"')
            self.assertGreaterEqual(position, 0, f"missing stage id: {stage_id}")
            positions.append(position)

        self.assertEqual(positions, sorted(positions), "verification stages are out of order")

    def test_pins_versions_and_frozen_dependency_commands(self) -> None:
        source = read_verify()

        self.assertIn('[version]"5.1"', source)
        for expected in ("v24.12.0", "11.13.0", "uv 0.11.28", "Python 3.12.13"):
            self.assertIn(expected, source)
        self.assertNotIn("AllowTrailingMetadata", source)
        self.assertIn("ExpectedPattern", source)
        self.assertIn('"install", "--frozen-lockfile", "--ignore-scripts"', source)
        self.assertIn('"sync", "--project", "apps/api", "--frozen"', source)
        self.assertIn('$PnpmInstallArguments += "--offline"', source)
        self.assertIn('$UvSyncArguments += "--offline"', source)
        self.assertIn("PNPM_CONFIG_OFFLINE", source)
        self.assertIn("PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN", source)
        self.assertIn('Value "false"', source)
        self.assertIn('$uvExecutable = "uv"', source)
        self.assertNotIn('$uvCommand = Get-Command "uv"', source)

    def test_completion_pass_is_emitted_only_after_environment_and_location_restore(self) -> None:
        source = read_verify()
        completion = source.rfind('Write-Output "[PASS] verification=complete"')

        self.assertGreater(completion, source.rfind("Exit-RunnerEnvironment"))
        self.assertGreater(completion, source.rfind("Pop-Location"))
        self.assertIn('if ($exitCode -eq 0)', source[completion - 100 : completion + 100])

    def test_includes_quality_generation_and_security_gates(self) -> None:
        source = read_verify()

        required_fragments = (
            '"unittest", "discover", "-s", "scripts/tests"',
            '"--filter", "@sejong-ai/web", "lint"',
            '"--filter", "@sejong-ai/web", "typecheck"',
            '"--filter", "@sejong-ai/web", "test"',
            '"--dir", "tools/web-e2e", "install", "--frozen-lockfile", "--ignore-scripts"',
            '"scripts/check_web_prod_dependency_boundary.mjs"',
            '"--filter", "@sejong-ai/web", "build"',
            '"ruff", "format", "--check"',
            '"ruff", "check"',
            '"mypy", "src", "tests"',
            '"pytest", "-q"',
            '"-p", "no:cacheprovider"',
            '"generate:check"',
            '"generate"',
            '"diff", "--exit-code", "--", "packages/shared-contracts/src/generated/api.ts"',
            '"scripts/check_secret_patterns.ps1"',
            '"scripts/check_web_bundle_secrets.mjs", "apps/web/.next"',
            '"scripts/validate_codex_package.py"',
            '"diff", "--check"',
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, source)

    def test_synthetic_server_environment_is_scoped_and_restored(self) -> None:
        source = read_verify()

        for name in (
            "SEJONG_WEB_SECRET_SENTINEL",
            "DATABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "LLM_API_KEY",
            "CONTEXT_TOKEN_SECRET",
            "DEEPSEEK_API_KEY",
        ):
            with self.subTest(name=name):
                self.assertIn(f'"{name}"', source)
        self.assertIn("finally", source)
        self.assertIn("Restore-Environment", source)
        self.assertIn("Assert-EnvironmentRestored", source)

    def test_runner_has_no_cleanup_or_server_launch(self) -> None:
        lowered = read_verify().lower()

        for forbidden in (
            "remove-item",
            "clear-content",
            "start-process",
            "stop-process",
            "uvicorn",
            "next start",
            "docker ",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, lowered)

    def test_windows_powershell_51_parser_accepts_the_script(self) -> None:
        if POWERSHELL is None:
            self.fail("Windows PowerShell is required")
        command = (
            "$tokens=$null; $errors=$null; "
            "[System.Management.Automation.Language.Parser]::ParseFile("
            "[Environment]::GetEnvironmentVariable('SEJONG_VERIFY_PARSE_PATH'), "
            "[ref]$tokens, [ref]$errors) | Out-Null; "
            "if ($errors.Count -ne 0) { exit 1 }"
        )
        environment = os.environ.copy()
        environment["SEJONG_VERIFY_PARSE_PATH"] = str(VERIFY)
        result = subprocess.run(
            [POWERSHELL, "-NoProfile", "-Command", command],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )

        self.assertEqual(result.returncode, 0, "Windows PowerShell parser rejected verify.ps1")


class VerifyRunnerExecutionTest(unittest.TestCase):
    def test_unknown_option_returns_two_without_script_path_disclosure(self) -> None:
        result = run_verify(arguments=("-UnexpectedOption",))
        combined = result.stdout + result.stderr

        self.assertEqual(result.returncode, 2, combined)
        self.assertIn("[FAIL] step=VALIDATE-ARGUMENTS reason=exception code=2", combined)
        self.assertNotIn(str(VERIFY), combined)

    def test_missing_absolute_executable_returns_two_without_path_disclosure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong verify missing ") as directory:
            temp = Path(directory)
            private_fragment = "private-missing-command-fragment"
            missing = temp / private_fragment / "python.exe"
            environment = os.environ.copy()
            environment["SEJONG_VERIFY_PARSE_PATH"] = str(VERIFY)
            environment["SEJONG_VERIFY_MISSING_PATH"] = str(missing)
            command = """
$path=[Environment]::GetEnvironmentVariable('SEJONG_VERIFY_PARSE_PATH')
$missing=[Environment]::GetEnvironmentVariable('SEJONG_VERIFY_MISSING_PATH')
. $path
try { Invoke-NativeStep -StepId 'TEST-MISSING' -Executable $missing }
catch { Write-Output '[FAIL] step=TEST-MISSING reason=exception code=2'; exit 2 }
exit 99
"""
            result = run_powershell_command(command, environment=environment, cwd=temp)

        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 2, combined)
        self.assertIn("[FAIL] step=TEST-MISSING reason=exception code=2", combined)
        self.assertNotIn(private_fragment, combined)

    def test_successful_child_output_is_not_relayed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong verify output ") as directory:
            temp = Path(directory)
            bin_dir = temp / "bin"
            bin_dir.mkdir()
            disclosed = "synthetic-success-content-must-not-be-disclosed"
            (bin_dir / "quiet-success.cmd").write_text(
                f"@echo {disclosed}\r\n@echo {disclosed} 1>&2\r\n@exit /b 0\r\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["PATH"] = str(bin_dir) + os.pathsep + environment.get("PATH", "")
            environment["SEJONG_VERIFY_PARSE_PATH"] = str(VERIFY)
            command = (
                "$path=[Environment]::GetEnvironmentVariable('SEJONG_VERIFY_PARSE_PATH'); "
                ". $path; Invoke-NativeStep -StepId 'TEST-QUIET' "
                "-Executable 'quiet-success.cmd'"
            )
            result = run_powershell_command(command, environment=environment, cwd=temp)

        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)
        self.assertIn("[PASS] step=TEST-QUIET", combined)
        self.assertNotIn(disclosed, combined)

    def test_build_environment_restores_exact_existing_and_absent_values(self) -> None:
        for should_fail in (False, True):
            with self.subTest(should_fail=should_fail):
                with tempfile.TemporaryDirectory(prefix="sejong verify env ") as directory:
                    temp = Path(directory)
                    bin_dir = temp / "bin"
                    bin_dir.mkdir()
                    checks = "\r\n".join(
                        f'if not "%{name}%"=="synthetic-scope" exit /b 91'
                        for name in (
                            "SEJONG_WEB_SECRET_SENTINEL",
                            "DATABASE_URL",
                            "SUPABASE_SERVICE_ROLE_KEY",
                            "LLM_API_KEY",
                            "CONTEXT_TOKEN_SECRET",
                            "DEEPSEEK_API_KEY",
                        )
                    )
                    (bin_dir / "corepack.cmd").write_text(
                        "@echo off\r\n"
                        + checks
                        + "\r\n"
                        + "if \"%SEJONG_VERIFY_TEST_FAIL%\"==\"true\" exit /b 41\r\n"
                        + "exit /b 0\r\n",
                        encoding="utf-8",
                    )
                    environment = os.environ.copy()
                    environment["PATH"] = str(bin_dir) + os.pathsep + environment.get("PATH", "")
                    environment["SEJONG_VERIFY_PARSE_PATH"] = str(VERIFY)
                    environment["SEJONG_VERIFY_TEST_FAIL"] = str(should_fail).lower()
                    command = """
$path=[Environment]::GetEnvironmentVariable('SEJONG_VERIFY_PARSE_PATH')
. $path
$existing=@{
  'SEJONG_WEB_SECRET_SENTINEL'='prior-sentinel'
  'SUPABASE_SERVICE_ROLE_KEY'='prior-service-role'
  'CONTEXT_TOKEN_SECRET'='prior-context'
}
$absent=@('DATABASE_URL','LLM_API_KEY','DEEPSEEK_API_KEY')
foreach ($entry in $existing.GetEnumerator()) {
  [Environment]::SetEnvironmentVariable($entry.Key,$entry.Value,'Process')
}
foreach ($name in $absent) {
  [Environment]::SetEnvironmentVariable($name,$null,'Process')
}
$caught=$false
try { Invoke-SentinelWebBuild -Sentinel 'synthetic-scope' -StepId 'TEST-BUILD' }
catch { $caught=$true }
if ($caught -ne ([Environment]::GetEnvironmentVariable('SEJONG_VERIFY_TEST_FAIL') -eq 'true')) { exit 92 }
foreach ($entry in $existing.GetEnumerator()) {
  if ([Environment]::GetEnvironmentVariable($entry.Key,'Process') -cne $entry.Value) { exit 93 }
}
foreach ($name in $absent) {
  if ($null -ne [Environment]::GetEnvironmentVariable($name,'Process')) { exit 94 }
}
exit 0
"""
                    result = run_powershell_command(command, environment=environment, cwd=temp)

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runner_environment_restores_offline_and_dependency_flags(self) -> None:
        scenarios = (
            (True, "prior-verify", None, True),
            (False, None, "prior-offline", False),
            (True, "prior-verify", "prior-offline", True),
        )
        for offline, prior_verify, prior_offline, simulate_failure in scenarios:
            with self.subTest(offline=offline, simulate_failure=simulate_failure):
                environment = os.environ.copy()
                environment["SEJONG_VERIFY_PARSE_PATH"] = str(VERIFY)
                environment["SEJONG_TEST_OFFLINE"] = str(offline).lower()
                environment["SEJONG_TEST_FAIL"] = str(simulate_failure).lower()
                if prior_verify is None:
                    environment.pop("PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN", None)
                else:
                    environment["PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN"] = prior_verify
                if prior_offline is None:
                    environment.pop("PNPM_CONFIG_OFFLINE", None)
                else:
                    environment["PNPM_CONFIG_OFFLINE"] = prior_offline
                command = """
$path=[Environment]::GetEnvironmentVariable('SEJONG_VERIFY_PARSE_PATH')
. $path
$useOffline=[Environment]::GetEnvironmentVariable('SEJONG_TEST_OFFLINE') -eq 'true'
$beforeVerify=[Environment]::GetEnvironmentVariable('PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN','Process')
$beforeOffline=[Environment]::GetEnvironmentVariable('PNPM_CONFIG_OFFLINE','Process')
$snapshot=@()
try {
  $snapshot=@(Enter-RunnerEnvironment -UseOffline $useOffline)
  if ([Environment]::GetEnvironmentVariable('PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN','Process') -cne 'false') { exit 81 }
  if ($useOffline -and [Environment]::GetEnvironmentVariable('PNPM_CONFIG_OFFLINE','Process') -cne 'true') { exit 82 }
  if ([Environment]::GetEnvironmentVariable('SEJONG_TEST_FAIL') -eq 'true') { throw 'simulated' }
}
catch { }
finally { Exit-RunnerEnvironment -Snapshot $snapshot }
if ([Environment]::GetEnvironmentVariable('PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN','Process') -cne $beforeVerify) { exit 83 }
if ([Environment]::GetEnvironmentVariable('PNPM_CONFIG_OFFLINE','Process') -cne $beforeOffline) { exit 84 }
exit 0
"""
                result = run_powershell_command(command, environment=environment, cwd=ROOT)

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_preserves_child_exit_fails_fast_and_hides_failed_child_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong verify fail ") as directory:
            temp = Path(directory)
            bin_dir = temp / "bin"
            bin_dir.mkdir()
            sentinel = "synthetic-child-output-must-not-be-disclosed"
            (bin_dir / "corepack.cmd").write_text(
                "@echo off\r\n"
                "if \"%2\"==\"--version\" (echo 11.13.0& exit /b 0)\r\n"
                f"echo {sentinel}\r\n"
                f"echo {sentinel} 1>&2\r\n"
                "exit /b 37\r\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["PATH"] = str(bin_dir) + os.pathsep + environment.get("PATH", "")
            result = run_verify(environment=environment, cwd=temp)

        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 37, combined)
        self.assertIn("[FAIL] step=INSTALL-PNPM reason=child-exit code=37", combined)
        self.assertNotIn(sentinel, combined)
        self.assertNotIn("[START] step=SYNC-API", combined)

    def test_unexpected_runner_exception_returns_two_without_exception_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong verify exception ") as directory:
            temp = Path(directory)
            secret_path_fragment = "private-path-fragment-must-not-be-disclosed"
            environment = os.environ.copy()
            environment["PATH"] = str(temp / secret_path_fragment)
            result = run_verify(environment=environment, cwd=temp)

        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 2, combined)
        self.assertIn("[FAIL] step=PREFLIGHT-NODE reason=exception code=2", combined)
        self.assertNotIn(secret_path_fragment, combined)


if __name__ == "__main__":
    unittest.main()
