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
    def test_accepts_only_exact_successor_release_version(self) -> None:
        source = read_runner()
        preamble = source.split("Set-StrictMode", 1)[0]

        self.assertEqual(re.findall(r"\[string\]\$(\w+)", preamble), ["ReleaseVersion"])
        self.assertIn('"0.1.0-initial.2"', source)
        self.assertNotIn('"0.1.0-initial.1"', source)
        self.assertIn("RELEASE-VERSION-INVALID", source)
        self.assertNotIn("[switch]", preamble)

    def test_known_broken_initial_release_is_rejected_before_runtime_work(self) -> None:
        if POWERSHELL is None:
            self.fail("Windows PowerShell is required")
        result = subprocess.run(
            [
                POWERSHELL,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(RUNNER),
                "-ReleaseVersion",
                "0.1.0-initial.1",
            ],
            cwd=ROOT,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertEqual(
            "[FAIL] step=VALIDATE-DATA-SEED-ARGUMENTS "
            "reason=RELEASE-VERSION-INVALID code=2",
            result.stdout.strip(),
        )
        self.assertFalse(result.stderr)

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
        self.assertIn("Get-DataSeedLibpqEnvironmentNames", source)
        self.assertIn("Clear-DataSeedEnvironment", source)
        self.assertNotIn("Write-Output $adminDsn", source)
        self.assertNotIn("Write-Host $adminDsn", source)

    def test_owned_runtime_cleanup_is_wired_after_any_baseline_attempt(self) -> None:
        source = read_runner()
        main = source.split(MAIN_MARKER, 1)[1]

        baseline_attempt = main.find("$baselineAttempted = $true")
        baseline_call = main.find('-Step "VERIFY-DATABASE-BASELINE"')
        finally_block = main.split("finally", 1)[1]

        self.assertNotEqual(-1, baseline_attempt)
        self.assertNotEqual(-1, baseline_call)
        self.assertLess(baseline_attempt, baseline_call)
        self.assertIn("Complete-DataSeedRuntimeAttempt", finally_block)
        self.assertIn("Remove-DataSeedOwnedRuntime", source)
        self.assertIn("Write-DataSeedFailureEvidence -Failure $failure", main)
        self.assertLess(
            finally_block.find("Complete-DataSeedRuntimeAttempt"),
            finally_block.find("Restore-DataSeedEnvironment"),
        )

    def test_cleanup_preserves_volumes_network_and_uses_only_patched_stop(self) -> None:
        source = read_runner()
        cleanup = source.split("function Remove-DataSeedOwnedRuntime", 1)[1].split(
            "function Complete-DataSeedRuntimeAttempt", 1
        )[0]
        lowered = cleanup.lower()

        self.assertIn('@("stop", "--project-id", $ProjectId)', cleanup)
        self.assertNotRegex(cleanup, r'-Arguments\s+@\("stop"\)\s*`')
        for forbidden in (
            "--no-backup",
            "volume rm",
            "network rm",
            "docker stop",
            "docker rm",
            "system prune",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, lowered)

    def test_database_evidence_is_allowlisted_before_relay(self) -> None:
        source = read_runner()
        main = source.split(MAIN_MARKER, 1)[1]
        normalized_main = re.sub(r"\s+", " ", main.replace("`", ""))

        self.assertIn("Write-DataSeedEvidence", source)
        self.assertIn("Invoke-DataSeedEvidenceStep", source)
        for step in (
            "VERIFY-DATA-SEED-IDENTITY",
            "VERIFY-DATA-SEED-FAILURE-ROLLBACK",
            "VERIFY-DATA-SEED-CONCURRENCY-A",
            "VERIFY-DATA-SEED-CONCURRENCY-B",
            "VERIFY-DATA-SEED-SEED-CYCLE",
            "VERIFY-DATA-SEED-FINAL",
        ):
            with self.subTest(step=step):
                self.assertIn(
                    f'Invoke-DataSeedEvidenceStep -Step "{step}"',
                    normalized_main,
                )
                self.assertNotIn(f'Write-DataSeedEvidence -Step "{step}"', main)
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
    def test_pre_run_requires_zero_owned_containers_and_zero_listener(self) -> None:
        base_environment = os.environ.copy()
        base_environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        command = r"""
$containerCount=[int][Environment]::GetEnvironmentVariable('SEJONG_SYNTHETIC_CONTAINER_COUNT')
$listenerCount=[int][Environment]::GetEnvironmentVariable('SEJONG_SYNTHETIC_LISTENER_COUNT')
$script:stopCalled=$false
function Invoke-DataSeedChild {
  param($FilePath,$Arguments,$WorkingDirectory,$TimeoutMilliseconds)
  if($Arguments[0] -ceq 'ps') {
    $ids=@()
    for($i=0;$i -lt $containerCount;$i+=1){$ids+=('a'*11)+[string]$i}
    return [pscustomobject]@{ExitCode=0;Output=($ids -join "`n")}
  }
  if($Arguments[0] -ceq 'stop'){$script:stopCalled=$true}
  return [pscustomobject]@{ExitCode=0;Output=''}
}
function Get-DataSeedListenerCount { param($Port,$Step) return $listenerCount }
try {
  Assert-DataSeedRuntimeAbsent -DockerPath (Join-Path $PSHOME 'powershell.exe') -ProjectId 'sejong-ai-local' -WorkingDirectory (Get-Location).Path
}
catch {
  if($_.Exception.Data['reason'] -cne 'invalid'){exit 81}
  if($script:stopCalled){exit 82}
  Write-Output '[PASS] step=STUB-PRE-RUN-REJECTED'
  exit 0
}
if($containerCount -ne 0 -or $listenerCount -ne 0){exit 83}
if($script:stopCalled){exit 84}
Write-Output '[PASS] step=STUB-PRE-RUN-ABSENT'
exit 0
"""
        for container_count, listener_count, marker in (
            (0, 0, "STUB-PRE-RUN-ABSENT"),
            (1, 0, "STUB-PRE-RUN-REJECTED"),
            (0, 1, "STUB-PRE-RUN-REJECTED"),
        ):
            with self.subTest(
                container_count=container_count, listener_count=listener_count
            ):
                environment = base_environment.copy()
                environment["SEJONG_SYNTHETIC_CONTAINER_COUNT"] = str(container_count)
                environment["SEJONG_SYNTHETIC_LISTENER_COUNT"] = str(listener_count)
                result = run_library_command(command, environment)
                combined = result.stdout + result.stderr
                self.assertEqual(0, result.returncode, combined)
                self.assertIn(f"[PASS] step={marker}", combined)

    def test_exact_owned_runtime_is_stopped_and_output_is_content_free(self) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        environment["SEJONG_SYNTHETIC_INSPECT_SENTINEL"] = (
            "synthetic-container-secret-must-not-be-relayed"
        )
        command = r"""
$script:listCalls=0
$script:stopCalls=0
$script:exactStop=$false
$sentinel=[Environment]::GetEnvironmentVariable('SEJONG_SYNTHETIC_INSPECT_SENTINEL')
function Get-DataSeedListenerCount { param($Port,$Step) return 0 }
function Invoke-DataSeedChild {
  param($FilePath,$Arguments,$WorkingDirectory,$TimeoutMilliseconds)
  if($Arguments[0] -ceq 'ps') {
    $script:listCalls+=1
    if($script:listCalls -eq 1){return [pscustomobject]@{ExitCode=0;Output='aaaaaaaaaaaa'}}
    return [pscustomobject]@{ExitCode=0;Output=''}
  }
  if($Arguments[0] -ceq 'inspect') {
    $json='{"Name":"/supabase_db_sejong-ai-local","State":{"Running":true,"Status":"running"},"Config":{"Labels":{"com.supabase.cli.project":"sejong-ai-local","sentinel":"'+$sentinel+'"}},"HostConfig":{"NetworkMode":"sejong-ai-local-loopback","PortBindings":{"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":"54322"}]}},"NetworkSettings":{"Networks":{"sejong-ai-local-loopback":{}},"Ports":{"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":"54322"}]}}}'
    return [pscustomobject]@{ExitCode=0;Output=$json}
  }
  if($Arguments[0] -ceq 'stop') {
    $script:stopCalls+=1
    $script:exactStop=(
      $Arguments.Count -eq 3 -and
      $Arguments[1] -ceq '--project-id' -and
      $Arguments[2] -ceq 'sejong-ai-local'
    )
    return [pscustomobject]@{ExitCode=0;Output=$sentinel}
  }
  exit 85
}
Remove-DataSeedOwnedRuntime -SupabasePath (Join-Path $PSHOME 'powershell.exe') -DockerPath (Join-Path $PSHOME 'powershell.exe') -ProjectId 'sejong-ai-local' -NetworkName 'sejong-ai-local-loopback' -ExpectedContainerName 'supabase_db_sejong-ai-local' -WorkingDirectory (Get-Location).Path
if($script:listCalls -ne 2 -or $script:stopCalls -ne 1 -or -not $script:exactStop){exit 86}
exit 0
"""
        result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        self.assertIn("[START] step=CLEANUP-DATA-SEED-RUNTIME", combined)
        self.assertIn("[PASS] step=CLEANUP-DATA-SEED-RUNTIME", combined)
        self.assertNotIn("aaaaaaaaaaaa", combined)
        self.assertNotIn(environment["SEJONG_SYNTHETIC_INSPECT_SENTINEL"], combined)

    def test_exact_stopped_owned_runtime_is_cleaned_without_resolved_fields(self) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        command = r"""
$script:listCalls=0
$script:stopCalls=0
function Get-DataSeedListenerCount { param($Port,$Step) return 0 }
function Invoke-DataSeedChild {
  param($FilePath,$Arguments,$WorkingDirectory,$TimeoutMilliseconds)
  if($Arguments[0] -ceq 'ps') {
    $script:listCalls+=1
    if($script:listCalls -eq 1){return [pscustomobject]@{ExitCode=0;Output='aaaaaaaaaaaa'}}
    return [pscustomobject]@{ExitCode=0;Output=''}
  }
  if($Arguments[0] -ceq 'inspect') {
    return [pscustomobject]@{ExitCode=0;Output='{"Name":"/supabase_db_sejong-ai-local","State":{"Running":false,"Status":"exited"},"Config":{"Labels":{"com.supabase.cli.project":"sejong-ai-local"}},"HostConfig":{"NetworkMode":"sejong-ai-local-loopback","PortBindings":{"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":"54322"}]}},"NetworkSettings":{}}'}
  }
  if($Arguments[0] -ceq 'stop') {
    if($Arguments.Count -ne 3 -or $Arguments[1] -cne '--project-id' -or $Arguments[2] -cne 'sejong-ai-local'){exit 108}
    $script:stopCalls+=1
    return [pscustomobject]@{ExitCode=0;Output=''}
  }
  exit 109
}
Remove-DataSeedOwnedRuntime -SupabasePath (Join-Path $PSHOME 'powershell.exe') -DockerPath (Join-Path $PSHOME 'powershell.exe') -ProjectId 'sejong-ai-local' -NetworkName 'sejong-ai-local-loopback' -ExpectedContainerName 'supabase_db_sejong-ai-local' -WorkingDirectory (Get-Location).Path
if($script:listCalls -ne 2 -or $script:stopCalls -ne 1){exit 110}
Write-Output '[PASS] step=STUB-STOPPED-OWNED-CLEANUP'
exit 0
"""
        result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        self.assertIn("[PASS] step=STUB-STOPPED-OWNED-CLEANUP", combined)

    def test_cleanup_rejects_multiple_or_wrong_owner_without_stop(self) -> None:
        base_environment = os.environ.copy()
        base_environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        command = r"""
$case=[Environment]::GetEnvironmentVariable('SEJONG_SYNTHETIC_CLEANUP_CASE')
$script:stopCalls=0
function Get-DataSeedListenerCount { param($Port,$Step) return 0 }
function Invoke-DataSeedChild {
  param($FilePath,$Arguments,$WorkingDirectory,$TimeoutMilliseconds)
  if($Arguments[0] -ceq 'ps') {
    if($case -ceq 'multiple'){return [pscustomobject]@{ExitCode=0;Output="aaaaaaaaaaaa`nbbbbbbbbbbbb"}}
    return [pscustomobject]@{ExitCode=0;Output='aaaaaaaaaaaa'}
  }
  if($Arguments[0] -ceq 'inspect') {
    if($case -ceq 'malformed'){return [pscustomobject]@{ExitCode=0;Output='{not-json'}}
    $name=if($case -ceq 'wrong-name'){'not-owned'}else{'supabase_db_sejong-ai-local'}
    $label=if($case -ceq 'wrong-label'){'not-owned'}else{'sejong-ai-local'}
    $network=if($case -ceq 'wrong-network'){'not-owned'}else{'sejong-ai-local-loopback'}
    $port=if($case -ceq 'wrong-port'){'54323'}else{'54322'}
    $hostIp=if($case -ceq 'wrong-host-ip'){'0.0.0.0'}else{'127.0.0.1'}
    $running=if($case -ceq 'invalid-status'){'false'}else{'true'}
    $status=if($case -ceq 'invalid-status'){'removing'}else{'running'}
    $networkEntries='"'+$network+'":{}'
    if($case -ceq 'extra-network'){$networkEntries+=',"unexpected-network":{}'}
    $portEntries='"5432/tcp":[{"HostIp":"'+$hostIp+'","HostPort":"'+$port+'"}]'
    if($case -ceq 'extra-port'){$portEntries+=',"9999/tcp":[{"HostIp":"127.0.0.1","HostPort":"59999"}]'}
    $json='{"Name":"/'+$name+'","State":{"Running":'+$running+',"Status":"'+$status+'"},"Config":{"Labels":{"com.supabase.cli.project":"'+$label+'"}},"HostConfig":{"NetworkMode":"'+$network+'","PortBindings":{'+$portEntries+'}},"NetworkSettings":{"Networks":{'+$networkEntries+'},"Ports":{'+$portEntries+'}}}'
    return [pscustomobject]@{ExitCode=0;Output=$json}
  }
  if($Arguments[0] -ceq 'stop'){$script:stopCalls+=1}
  return [pscustomobject]@{ExitCode=0;Output=''}
}
try {
  Remove-DataSeedOwnedRuntime -SupabasePath (Join-Path $PSHOME 'powershell.exe') -DockerPath (Join-Path $PSHOME 'powershell.exe') -ProjectId 'sejong-ai-local' -NetworkName 'sejong-ai-local-loopback' -ExpectedContainerName 'supabase_db_sejong-ai-local' -WorkingDirectory (Get-Location).Path
}
catch {
  if($_.Exception.Data['reason'] -cne 'invalid'){exit 87}
  if($script:stopCalls -ne 0){exit 88}
  Write-Output '[PASS] step=STUB-UNOWNED-REJECTED'
  exit 0
}
exit 89
"""
        for case in (
            "multiple",
            "malformed",
            "wrong-name",
            "wrong-label",
            "wrong-network",
            "wrong-port",
            "wrong-host-ip",
            "extra-port",
            "extra-network",
            "invalid-status",
        ):
            with self.subTest(case=case):
                environment = base_environment.copy()
                environment["SEJONG_SYNTHETIC_CLEANUP_CASE"] = case
                result = run_library_command(command, environment)
                combined = result.stdout + result.stderr
                self.assertEqual(0, result.returncode, combined)
                self.assertIn("[PASS] step=STUB-UNOWNED-REJECTED", combined)

    def test_cleanup_child_error_and_timeout_fail_closed_without_output(self) -> None:
        base_environment = os.environ.copy()
        base_environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        base_environment["SEJONG_SYNTHETIC_CHILD_SENTINEL"] = (
            "synthetic-runtime-child-secret-must-not-be-relayed"
        )
        command = r"""
$case=[Environment]::GetEnvironmentVariable('SEJONG_SYNTHETIC_CHILD_CASE')
$sentinel=[Environment]::GetEnvironmentVariable('SEJONG_SYNTHETIC_CHILD_SENTINEL')
$script:stopCalls=0
function Get-DataSeedListenerCount { param($Port,$Step) return 0 }
function Invoke-DataSeedChild {
  param($FilePath,$Arguments,$WorkingDirectory,$TimeoutMilliseconds)
  if($Arguments[0] -ceq 'stop'){$script:stopCalls+=1}
  if($case -ceq 'timeout') {
    Throw-DataSeedFailure -Step 'DATA-SEED-CHILD' -Reason 'timeout' -Code 2
  }
  return [pscustomobject]@{ExitCode=23;Output=$sentinel}
}
try {
  Remove-DataSeedOwnedRuntime -SupabasePath (Join-Path $PSHOME 'powershell.exe') -DockerPath (Join-Path $PSHOME 'powershell.exe') -ProjectId 'sejong-ai-local' -NetworkName 'sejong-ai-local-loopback' -ExpectedContainerName 'supabase_db_sejong-ai-local' -WorkingDirectory (Get-Location).Path
}
catch {
  $expected=if($case -ceq 'timeout'){'timeout'}else{'child'}
  if($_.Exception.Data['reason'] -cne $expected){exit 102}
  if($script:stopCalls -ne 0){exit 103}
  Write-Output '[PASS] step=STUB-CLEANUP-CHILD-REJECTED'
  exit 0
}
exit 104
"""
        for case in ("child", "timeout"):
            with self.subTest(case=case):
                environment = base_environment.copy()
                environment["SEJONG_SYNTHETIC_CHILD_CASE"] = case
                result = run_library_command(command, environment)
                combined = result.stdout + result.stderr
                self.assertEqual(0, result.returncode, combined)
                self.assertIn("[PASS] step=STUB-CLEANUP-CHILD-REJECTED", combined)
                self.assertNotIn(
                    environment["SEJONG_SYNTHETIC_CHILD_SENTINEL"], combined
                )

    def test_cleanup_fails_when_container_or_listener_remains_after_stop(self) -> None:
        base_environment = os.environ.copy()
        base_environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        command = r"""
$case=[Environment]::GetEnvironmentVariable('SEJONG_SYNTHETIC_POST_STOP_CASE')
$script:listCalls=0
$script:stopCalls=0
function Get-DataSeedListenerCount {
  param($Port,$Step)
  if($case -ceq 'listener-remains'){return 1}
  return 0
}
function Invoke-DataSeedChild {
  param($FilePath,$Arguments,$WorkingDirectory,$TimeoutMilliseconds)
  if($Arguments[0] -ceq 'ps') {
    $script:listCalls+=1
    if($script:listCalls -eq 1){return [pscustomobject]@{ExitCode=0;Output='aaaaaaaaaaaa'}}
    if($case -ceq 'container-remains'){return [pscustomobject]@{ExitCode=0;Output='aaaaaaaaaaaa'}}
    return [pscustomobject]@{ExitCode=0;Output=''}
  }
  if($Arguments[0] -ceq 'inspect') {
    return [pscustomobject]@{ExitCode=0;Output='{"Name":"/supabase_db_sejong-ai-local","State":{"Running":true,"Status":"running"},"Config":{"Labels":{"com.supabase.cli.project":"sejong-ai-local"}},"HostConfig":{"NetworkMode":"sejong-ai-local-loopback","PortBindings":{"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":"54322"}]}},"NetworkSettings":{"Networks":{"sejong-ai-local-loopback":{}},"Ports":{"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":"54322"}]}}}'}
  }
  if($Arguments[0] -ceq 'stop'){
    if($Arguments.Count -ne 3 -or $Arguments[1] -cne '--project-id' -or $Arguments[2] -cne 'sejong-ai-local'){exit 111}
    $script:stopCalls+=1
    return [pscustomobject]@{ExitCode=0;Output=''}
  }
  exit 90
}
try {
  Remove-DataSeedOwnedRuntime -SupabasePath (Join-Path $PSHOME 'powershell.exe') -DockerPath (Join-Path $PSHOME 'powershell.exe') -ProjectId 'sejong-ai-local' -NetworkName 'sejong-ai-local-loopback' -ExpectedContainerName 'supabase_db_sejong-ai-local' -WorkingDirectory (Get-Location).Path
}
catch {
  if($_.Exception.Data['reason'] -cne 'invalid'){exit 91}
  if($script:stopCalls -ne 1){exit 92}
  Write-Output '[PASS] step=STUB-POST-STOP-REMAINS-REJECTED'
  exit 0
}
exit 93
"""
        for case in ("container-remains", "listener-remains"):
            with self.subTest(case=case):
                environment = base_environment.copy()
                environment["SEJONG_SYNTHETIC_POST_STOP_CASE"] = case
                result = run_library_command(command, environment)
                combined = result.stdout + result.stderr
                self.assertEqual(0, result.returncode, combined)
                self.assertIn("[PASS] step=STUB-POST-STOP-REMAINS-REJECTED", combined)

    def test_cleanup_listener_probe_error_is_attributed_to_cleanup(self) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        command = r"""
function Invoke-DataSeedChild {
  param($FilePath,$Arguments,$WorkingDirectory,$TimeoutMilliseconds)
  return [pscustomobject]@{ExitCode=0;Output=''}
}
function Get-DataSeedListenerCount {
  param($Port,$Step)
  Throw-DataSeedFailure -Step $Step -Reason 'operational' -Code 2
}
try {
  Remove-DataSeedOwnedRuntime -SupabasePath (Join-Path $PSHOME 'powershell.exe') -DockerPath (Join-Path $PSHOME 'powershell.exe') -ProjectId 'sejong-ai-local' -NetworkName 'sejong-ai-local-loopback' -ExpectedContainerName 'supabase_db_sejong-ai-local' -WorkingDirectory (Get-Location).Path
}
catch {
  if($_.Exception.Data['step'] -cne 'CLEANUP-DATA-SEED-RUNTIME'){exit 105}
  if($_.Exception.Data['reason'] -cne 'operational'){exit 106}
  Write-Output '[PASS] step=STUB-CLEANUP-LISTENER-ERROR'
  exit 0
}
exit 107
"""
        result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        self.assertIn("[PASS] step=STUB-CLEANUP-LISTENER-ERROR", combined)

    def test_cleanup_runs_for_success_and_failure_and_preserves_primary(self) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        command = r"""
$script:cleanupCalls=0
function Remove-DataSeedOwnedRuntime {
  param($SupabasePath,$DockerPath,$ProjectId,$NetworkName,$ExpectedContainerName,$WorkingDirectory)
  $script:cleanupCalls+=1
}
$common=@{
  SupabasePath=(Join-Path $PSHOME 'powershell.exe');
  DockerPath=(Join-Path $PSHOME 'powershell.exe');
  ProjectId='sejong-ai-local';
  NetworkName='sejong-ai-local-loopback';
  ExpectedContainerName='supabase_db_sejong-ai-local';
  WorkingDirectory=(Get-Location).Path
}
$success=Complete-DataSeedRuntimeAttempt @common -PrimaryFailure $null
$primary=New-Object System.InvalidOperationException('synthetic primary')
$failure=Complete-DataSeedRuntimeAttempt @common -PrimaryFailure $primary
if($null -ne $success){exit 94}
if(-not [object]::ReferenceEquals($primary,$failure)){exit 95}
if($script:cleanupCalls -ne 2){exit 96}

function Remove-DataSeedOwnedRuntime {
  param($SupabasePath,$DockerPath,$ProjectId,$NetworkName,$ExpectedContainerName,$WorkingDirectory)
  Throw-DataSeedFailure -Step 'CLEANUP-DATA-SEED-RUNTIME' -Reason 'timeout' -Code 2
}
$cleanupOnly=Complete-DataSeedRuntimeAttempt @common -PrimaryFailure $null
$primaryWithCleanup=Complete-DataSeedRuntimeAttempt @common -PrimaryFailure $primary
if($cleanupOnly.Data['step'] -cne 'CLEANUP-DATA-SEED-RUNTIME'){exit 97}
if(-not [object]::ReferenceEquals($primary,$primaryWithCleanup)){exit 98}
if($primaryWithCleanup.Data['cleanup_step'] -cne 'CLEANUP-DATA-SEED-RUNTIME'){exit 99}
if($primaryWithCleanup.Data['cleanup_reason'] -cne 'timeout'){exit 100}
if([int]$primaryWithCleanup.Data['cleanup_code'] -ne 2){exit 101}
Write-Output '[PASS] step=STUB-CLEANUP-PRIMARY-PRESERVED'
exit 0
"""
        result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        self.assertIn("[PASS] step=STUB-CLEANUP-PRIMARY-PRESERVED", combined)

    def test_primary_cleanup_and_restore_diagnostics_are_stable_and_content_free(
        self,
    ) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        environment["SEJONG_SYNTHETIC_DIAGNOSTIC_SENTINEL"] = (
            "synthetic-diagnostic-secret-must-not-be-relayed"
        )
        command = r"""
$sentinel=[Environment]::GetEnvironmentVariable('SEJONG_SYNTHETIC_DIAGNOSTIC_SENTINEL')
try {
  Throw-DataSeedFailure -Step 'VERIFY-DATA-SEED-FINAL' -Reason 'child' -Code 37
}
catch {$primary=$_.Exception}
$primary.Data['cleanup_step']='CLEANUP-DATA-SEED-RUNTIME'
$primary.Data['cleanup_reason']='timeout'
$primary.Data['cleanup_code']=2
$primary.Data['restore_step']='RESTORE-DATA-SEED-ENVIRONMENT'
$primary.Data['restore_reason']='operational'
$primary.Data['restore_code']=2
$primary.Data['sentinel']=$sentinel
Write-DataSeedFailureEvidence -Failure $primary
exit 0
"""
        result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        self.assertEqual(
            [
                "[FAIL] step=VERIFY-DATA-SEED-FINAL reason=child code=37",
                "[FAIL] step=CLEANUP-DATA-SEED-RUNTIME reason=timeout code=2",
                "[FAIL] step=RESTORE-DATA-SEED-ENVIRONMENT reason=operational code=2",
            ],
            result.stdout.splitlines(),
        )
        self.assertNotIn(
            environment["SEJONG_SYNTHETIC_DIAGNOSTIC_SENTINEL"], combined
        )

    def test_patched_runtime_accepts_exact_manifest_when_property_diff_is_empty(
        self,
    ) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        environment["SEJONG_DATA_SEED_REPOSITORY_ROOT"] = str(ROOT)
        command = r"""
$root=[Environment]::GetEnvironmentVariable('SEJONG_DATA_SEED_REPOSITORY_ROOT')
$manifest=Join-Path $root 'scripts\supabase-cli.local-patch.runtime.json'
$binary=Join-Path $root '.tools\supabase\v2.109.1-sejong-loopback\supabase.exe'
try {
  Assert-DataSeedPatchedRuntime -RepositoryRoot $root -RuntimeManifestPath $manifest -SupabaseBinary $binary
}
catch { exit 89 }
exit 0
"""
        result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        self.assertIn("[PASS] step=VERIFY-DATA-SEED-PATCHED-RUNTIME", combined)

    def test_invalid_zero_exit_evidence_child_has_no_generic_pass_or_payload(
        self,
    ) -> None:
        if POWERSHELL is None:
            self.fail("Windows PowerShell is required")
        with tempfile.TemporaryDirectory(prefix="sejong evidence child ") as directory:
            child = Path(directory) / "invalid-evidence.cmd"
            stdout_sentinel = "synthetic-invalid-evidence-stdout"
            stderr_sentinel = "synthetic-invalid-evidence-stderr"
            child.write_text(
                "@echo off\r\n"
                f"echo {stdout_sentinel}\r\n"
                f"echo {stderr_sentinel} 1>&2\r\n"
                "exit /b 0\r\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
            environment["SEJONG_DATA_SEED_EVIDENCE_CHILD"] = str(child)
            command = r"""
$child=[Environment]::GetEnvironmentVariable('SEJONG_DATA_SEED_EVIDENCE_CHILD')
try {
  Invoke-DataSeedEvidenceStep -Step 'VERIFY-DATA-SEED-IDENTITY' -FilePath $child -Arguments @() -WorkingDirectory (Get-Location).Path -TimeoutMilliseconds 5000
}
catch {
  if($_.Exception.Data['reason'] -cne 'invalid'){exit 99}
  Write-Output '[PASS] step=STUB-EVIDENCE-SEQUENCE-REJECTED'
  exit 0
}
exit 100
"""
            result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        self.assertIn("[START] step=VERIFY-DATA-SEED-IDENTITY", combined)
        self.assertIn("[PASS] step=STUB-EVIDENCE-SEQUENCE-REJECTED", combined)
        self.assertNotIn("[PASS] step=VERIFY-DATA-SEED-IDENTITY\n", combined)
        self.assertNotIn(stdout_sentinel, combined)
        self.assertNotIn(stderr_sentinel, combined)

    def test_dynamic_pg_environment_is_saved_cleared_and_restored(self) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        environment["PGHOSTADDR"] = "synthetic-host-address"
        environment["PGSERVICE"] = "synthetic-service"
        environment["PGSERVICEFILE"] = "synthetic-service-file"
        environment["PGOPTIONS"] = "synthetic-options"
        command = r"""
$names=@(Get-DataSeedLibpqEnvironmentNames)
$saved=Save-DataSeedEnvironment -Names (@('SEJONG_ADMIN_DATABASE_URL')+$names)
try {
  Clear-DataSeedEnvironment -Names $names
  foreach($name in $names) {
    if(Test-Path -LiteralPath ('Env:\'+$name)){exit 96}
  }
}
finally { Restore-DataSeedEnvironment -Saved $saved }
foreach($name in @('PGHOSTADDR','PGSERVICE','PGSERVICEFILE','PGOPTIONS')) {
  if(-not (Test-Path -LiteralPath ('Env:\'+$name))){exit 97}
  if([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($name,'Process'))){exit 98}
}
exit 0
"""
        result = run_library_command(command, environment)

        combined = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined)
        for sentinel in (
            "synthetic-host-address",
            "synthetic-service",
            "synthetic-service-file",
            "synthetic-options",
        ):
            self.assertNotIn(sentinel, combined)

    def test_evidence_relay_accepts_exact_line_and_rejects_extra_content(self) -> None:
        environment = os.environ.copy()
        environment["SEJONG_DATA_SEED_RUNNER_PATH"] = str(RUNNER)
        sentinel = "synthetic-evidence-secret-must-not-be-relayed"
        environment["SEJONG_DATA_SEED_EVIDENCE_SENTINEL"] = sentinel
        command = r"""
$safe='[PASS] step=VERIFY-DATA-SEED-IDENTITY release=0.1.0-initial.2 identity=exact'
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
            "release=0.1.0-initial.2 identity=exact",
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
