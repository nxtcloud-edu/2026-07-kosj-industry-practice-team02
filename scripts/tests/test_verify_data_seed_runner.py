"""Static and stub-child tests for the supported DATA-SEED PowerShell runner."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "verify_data_seed.ps1"
POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")
MAIN_MARKER = "# DATA-SEED-RUNNER-MAIN"


def read_runner() -> str:
    if not RUNNER.is_file():
        raise AssertionError("scripts/verify_data_seed.ps1 is required")
    return RUNNER.read_text(encoding="utf-8")


def run_library_command(
    command: str, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    if POWERSHELL is None:
        raise AssertionError("Windows PowerShell is required")
    loader = r"""
$path=[Environment]::GetEnvironmentVariable('SEJONG_DATA_SEED_RUNNER_PATH')
$source=[System.IO.File]::ReadAllText($path,[System.Text.Encoding]::UTF8)
$marker='# DATA-SEED-RUNNER-MAIN'
$index=$source.IndexOf($marker,[System.StringComparison]::Ordinal)
if ($index -lt 0) { exit 90 }
Invoke-Expression $source.Substring(0,$index)
"""
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            loader + command,
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )


class VerifyDataSeedRunnerStructureTests(unittest.TestCase):
    def test_accepts_only_exact_initial_release_version(self) -> None:
        source = read_runner()
        preamble = source.split("Set-StrictMode", 1)[0]

        self.assertEqual(re.findall(r"\[string\]\$(\w+)", preamble), ["ReleaseVersion"])
        self.assertIn('"0.1.0-initial.1"', source)
        self.assertIn("RELEASE-VERSION-INVALID", source)
        self.assertNotIn("[switch]", preamble)

    def test_uses_only_pinned_patched_supabase_and_exact_runtime_allowlist(
        self,
    ) -> None:
        source = read_runner()

        self.assertIn(
            '".tools\\supabase\\v2.109.1-sejong-loopback\\supabase.exe"',
            source,
        )
        self.assertIn('"scripts\\supabase-cli.local-patch.runtime.json"', source)
        self.assertIn('"2.109.1"', source)
        self.assertIn(
            '"751068e73834c5da58ac7c5287a1d66a82ad356f508637b0478d6531cdb3941c"',
            source,
        )
        self.assertNotRegex(source, r"Get-Command\s+['\"]?supabase")
        self.assertNotRegex(source, r"(?i)(npx|pnpm\s+dlx|npm\s+exec).*supabase")

    def test_stages_are_present_in_exact_required_order(self) -> None:
        source = read_runner().split(MAIN_MARKER, 1)[1]
        stages = (
            "VERIFY-DATABASE-BASELINE",
            "READ-LOCAL-DATABASE-STATUS",
            "VERIFY-DATA-SEED-IDENTITY",
            "RESET-BEFORE-FAILURE-ROLLBACK",
            "VERIFY-DATA-SEED-FAILURE-ROLLBACK",
            "RESET-BEFORE-CONCURRENCY-A",
            "VERIFY-DATA-SEED-CONCURRENCY-A",
            "RESET-BEFORE-CONCURRENCY-B",
            "VERIFY-DATA-SEED-CONCURRENCY-B",
            "RESET-BEFORE-SEED-CYCLE",
            "VERIFY-DATA-SEED-SEED-CYCLE",
            "VERIFY-DATA-SEED-FINAL",
        )
        positions = [source.find(f'"{stage}"') for stage in stages]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))

        baseline_position = source.find('"VERIFY-DATABASE-BASELINE"')
        status_position = source.find('"READ-LOCAL-DATABASE-STATUS"')
        self.assertLess(baseline_position, status_position)
        self.assertIn('"scripts\\verify_database.ps1"', source)
        self.assertIn('"status", "-o", "env"', source)

    def test_runner_wires_exact_python_subcommands_and_scenarios(self) -> None:
        source = re.sub(r"\s+", " ", read_runner())

        for fragment in (
            '"identity", "--release-version", $ReleaseVersion',
            '"failure-rollback", "--release-version", $ReleaseVersion',
            '"--scenario", "capability-before-seed"',
            '"--scenario", "seed-before-capability"',
            '"seed-cycle", "--release-version", $ReleaseVersion',
            '"verify-final", "--release-version", $ReleaseVersion',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, source)

    def test_child_timeout_output_secrecy_and_environment_restore_are_explicit(
        self,
    ) -> None:
        source = read_runner()

        self.assertIn("TimeoutMilliseconds", source)
        self.assertIn("WaitForExit", source)
        self.assertIn("Stop-DataSeedProcessTree", source)
        self.assertIn("Save-DataSeedEnvironment", source)
        self.assertIn("Restore-DataSeedEnvironment", source)
        self.assertIn("finally", source)
        self.assertIn('"SEJONG_ADMIN_DATABASE_URL"', source)
        self.assertNotIn("Write-Output $adminDsn", source)
        self.assertNotIn("Write-Host $adminDsn", source)

    def test_database_evidence_is_allowlisted_before_relay(self) -> None:
        source = read_runner()

        self.assertIn("Write-DataSeedEvidence", source)
        for step in (
            "VERIFY-DATA-SEED-IDENTITY",
            "VERIFY-DATA-SEED-FAILURE-ROLLBACK",
            "VERIFY-DATA-SEED-CONCURRENCY-A",
            "VERIFY-DATA-SEED-CONCURRENCY-B",
            "VERIFY-DATA-SEED-SEED-CYCLE",
            "VERIFY-DATA-SEED-FINAL",
        ):
            with self.subTest(step=step):
                self.assertIn(f'Write-DataSeedEvidence -Step "{step}"', source)
        self.assertIn("semantic_sha256=[0-9a-f]{64}", source)

    def test_forbids_manual_sql_stock_seed_and_scope_expansion(self) -> None:
        lowered = read_runner().lower()
        for forbidden in (
            "psql",
            "run_database_sql.py",
            "supabase/seed.sql",
            "db push",
            "migration new",
            "docker prune",
            "deepseek",
            "curl ",
            "invoke-webrequest",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, lowered)

    def test_windows_powershell_51_parser_accepts_runner(self) -> None:
        if POWERSHELL is None:
            self.fail("Windows PowerShell is required")
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        command = (
            "$tokens=$null;$errors=$null;"
            "[System.Management.Automation.Language.Parser]::ParseFile("
            "[Environment]::GetEnvironmentVariable('SEJONG_DATA_SEED_RUNNER_PATH'),"
            "[ref]$tokens,[ref]$errors)|Out-Null;"
            "if($errors.Count -ne 0){exit 1}"
        )
        result = subprocess.run(
            [POWERSHELL, "-NoProfile", "-Command", command],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class VerifyDataSeedRunnerStubTests(unittest.TestCase):
    def test_evidence_relay_accepts_exact_line_and_rejects_extra_content(self) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        sentinel = "synthetic-evidence-secret-must-not-be-relayed"
        environment["SEJONG_DATA_SEED_EVIDENCE_SENTINEL"] = sentinel
        command = r"""
$safe='[PASS] step=VERIFY-DATA-SEED-IDENTITY release=0.1.0-initial.1 identity=exact'
Write-DataSeedEvidence -Step 'VERIFY-DATA-SEED-IDENTITY' -Output $safe
$sentinel=[Environment]::GetEnvironmentVariable('SEJONG_DATA_SEED_EVIDENCE_SENTINEL')
try {
  Write-DataSeedEvidence -Step 'VERIFY-DATA-SEED-IDENTITY' -Output ($safe+"`n"+$sentinel)
}
catch {
  if($_.Exception.Data['reason'] -cne 'invalid'){exit 94}
  Write-Output '[PASS] step=STUB-EVIDENCE-REJECTED'
  exit 0
}
exit 95
"""
        result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        self.assertIn(
            "[PASS] step=VERIFY-DATA-SEED-IDENTITY "
            "release=0.1.0-initial.1 identity=exact",
            combined,
        )
        self.assertIn("[PASS] step=STUB-EVIDENCE-REJECTED", combined)
        self.assertNotIn(sentinel, combined)

    def test_environment_snapshot_restores_existing_and_absent_dsn(self) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        command = r"""
$had=Test-Path Env:SEJONG_ADMIN_DATABASE_URL
$before=[Environment]::GetEnvironmentVariable('SEJONG_ADMIN_DATABASE_URL','Process')
$saved=Save-DataSeedEnvironment -Names @('SEJONG_ADMIN_DATABASE_URL')
try { [Environment]::SetEnvironmentVariable('SEJONG_ADMIN_DATABASE_URL','temporary','Process') }
finally { Restore-DataSeedEnvironment -Saved $saved }
$afterHad=Test-Path Env:SEJONG_ADMIN_DATABASE_URL
$after=[Environment]::GetEnvironmentVariable('SEJONG_ADMIN_DATABASE_URL','Process')
if($afterHad -ne $had -or $after -cne $before){exit 91}
exit 0
"""
        for prior in (None, "prior-synthetic-value"):
            with self.subTest(prior=prior):
                candidate = environment.copy()
                if prior is None:
                    candidate.pop("SEJONG_ADMIN_DATABASE_URL", None)
                else:
                    candidate["SEJONG_ADMIN_DATABASE_URL"] = prior
                result = run_library_command(command, candidate)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_child_timeout_is_bounded_and_does_not_relay_child_output(self) -> None:
        if POWERSHELL is None:
            self.fail("Windows PowerShell is required")
        with tempfile.TemporaryDirectory(prefix="sejong seed child ") as directory:
            temp = Path(directory)
            child = temp / "slow-child.cmd"
            sentinel = "synthetic-child-secret-must-not-be-relayed"
            child.write_text(
                "@echo off\r\n"
                f"echo {sentinel}\r\n"
                "ping -n 6 127.0.0.1 >nul\r\n"
                "exit /b 0\r\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
            environment["SEJONG_DATA_SEED_SLOW_CHILD"] = str(child)
            command = r"""
$child=[Environment]::GetEnvironmentVariable('SEJONG_DATA_SEED_SLOW_CHILD')
try {
  $null=Invoke-DataSeedChild -FilePath $child -Arguments @() -WorkingDirectory (Get-Location).Path -TimeoutMilliseconds 100
}
catch {
  if($_.Exception.Data['reason'] -cne 'timeout'){exit 92}
  Write-Output '[PASS] step=STUB-TIMEOUT'
  exit 0
}
exit 93
"""
            result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        self.assertIn("[PASS] step=STUB-TIMEOUT", combined)
        self.assertNotIn(sentinel, combined)


if __name__ == "__main__":
    unittest.main()
