from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = ROOT / "scripts" / "supabase-cli.local-patch.source.json"
RUNTIME_MANIFEST = ROOT / "scripts" / "supabase-cli.local-patch.runtime.json"
PATCH_PATH = ROOT / "scripts" / "patches" / "supabase-cli-v2.109.1-db-loopback.patch"
BOOTSTRAP_PATH = ROOT / "scripts" / "bootstrap_patched_supabase.ps1"

EXPECTED_SOURCE = {
    "schema_version": 1,
    "upstream": {
        "repository": "https://github.com/supabase/cli.git",
        "tag": "v2.109.1",
        "tag_object_sha1": "9d25ff8b5b0fba3c6f0ef000e7dd658c8d710c38",
        "commit_sha1": "6d4c19870ed213ba7f682f117d0345c8a40bfa94",
    },
    "go": {
        "version": "1.25.11",
        "platform": "windows-amd64",
        "url": "https://dl.google.com/go/go1.25.11.windows-amd64.zip",
        "sha256": "b7401f1b41517428e537493316256fb7cf03c66a130a0103ab07f3a2152e2112",
    },
    "patch": {
        "relative_path": "scripts/patches/supabase-cli-v2.109.1-db-loopback.patch",
        "size_bytes": 1824,
        "sha256": "109c096480e8185d761e9ce8fba10e93efc55190c42eab978f769a6993833f7d",
        "allowed_files": [
            "apps/cli-go/internal/db/start/start_test.go",
            "apps/cli-go/internal/db/start/start.go",
        ],
    },
    "build": {
        "working_directory": "apps/cli-go",
        "version": "2.109.1",
        "goos": "windows",
        "goarch": "amd64",
        "cgo_enabled": "0",
        "goproxy": "https://proxy.golang.org",
        "gosumdb": "sum.golang.org",
        "goprivate": "",
        "gonoproxy": "",
        "gonosumdb": "",
        "goinsecure": "",
        "goenv": "off",
        "gowork": "off",
        "gotoolchain": "local",
        "goflags": "",
        "goamd64": "v1",
        "goexperiment": "",
        "flags": ["-trimpath", "-buildvcs=false"],
        "ldflags": "-s -w -X github.com/supabase/cli/internal/utils.Version=2.109.1",
    },
}


def powershell_executable() -> str:
    executable = shutil.which("powershell.exe") or shutil.which("powershell")
    if executable is None:
        raise AssertionError("Windows PowerShell 5.1+ is required")
    return executable


@contextmanager
def run_patched_fixture(
    *arguments: str,
    include_runtime: bool,
    mutate_source: Callable[[dict[str, object]], None] | None = None,
) -> Iterator[tuple[subprocess.CompletedProcess[str], Path]]:
    with tempfile.TemporaryDirectory(prefix="sejong patched supabase ") as directory:
        root = Path(directory)
        scripts = root / "scripts"
        patches = scripts / "patches"
        patches.mkdir(parents=True)
        shutil.copy2(BOOTSTRAP_PATH, scripts / BOOTSTRAP_PATH.name)
        shutil.copy2(PATCH_PATH, patches / PATCH_PATH.name)
        source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        if mutate_source is not None:
            mutate_source(source)
        (scripts / SOURCE_MANIFEST.name).write_text(
            json.dumps(source, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if include_runtime:
            shutil.copy2(RUNTIME_MANIFEST, scripts / RUNTIME_MANIFEST.name)
        environment = {
            key: os.environ[key]
            for key in ("COMSPEC", "PATHEXT", "SystemRoot", "TEMP", "TMP", "WINDIR")
            if key in os.environ
        }
        result = subprocess.run(
            [
                powershell_executable(),
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(scripts / BOOTSTRAP_PATH.name),
                *arguments,
            ],
            cwd=root,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            env=environment,
            timeout=30,
        )
        yield result, root


class PatchedSourceLockTests(unittest.TestCase):
    def test_source_manifest_is_exact(self) -> None:
        self.assertTrue(SOURCE_MANIFEST.is_file())
        self.assertEqual(
            json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8")),
            EXPECTED_SOURCE,
        )

    def test_patch_bytes_hash_and_scope_are_exact(self) -> None:
        payload = PATCH_PATH.read_bytes()
        self.assertEqual(len(payload), EXPECTED_SOURCE["patch"]["size_bytes"])
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            EXPECTED_SOURCE["patch"]["sha256"],
        )
        self.assertNotIn(b"\r\n", payload)
        text = payload.decode("utf-8")
        changed = re.findall(r"^diff --git a/(\S+) b/(\S+)$", text, re.MULTILINE)
        self.assertEqual(
            changed,
            [(path, path) for path in EXPECTED_SOURCE["patch"]["allowed_files"]],
        )
        self.assertEqual(text.count('HostIP: "127.0.0.1"'), 1)
        self.assertNotIn("internal/db/diff", text)


class PatchedBootstrapContractTests(unittest.TestCase):
    def test_script_has_only_approved_modes_sources_and_operations(self) -> None:
        script = BOOTSTRAP_PATH.read_text(encoding="utf-8")
        lowered = script.lower()
        for token in (
            '"-BuildCandidate"',
            '"-Install"',
            '"-VerifyOnly"',
            '"-GoArchivePath"',
            "Get-FileHash",
            "git.exe",
            "go.exe",
            '@("mod", "verify")',
            "-trimpath",
            "-buildvcs=false",
            "GOPROXY",
            "GOSUMDB",
            "GOPRIVATE",
            "GONOPROXY",
            "GONOSUMDB",
            "GOINSECURE",
            "GOENV",
            "GOWORK",
            "GOTOOLCHAIN",
            "GOFLAGS",
            "GOAMD64",
            "GOEXPERIMENT",
            '"supabase-source/6d4c19870ed213ba7f682f117d0345c8a40bfa94/a"',
            '"supabase-source/6d4c19870ed213ba7f682f117d0345c8a40bfa94/b"',
            '"supabase-build/supabase-v2.109.1-sejong-loopback-a.exe"',
            '"supabase-build/supabase-v2.109.1-sejong-loopback-b.exe"',
        ):
            self.assertIn(token, script)
        for forbidden in (
            "npm install",
            "bun build",
            "winget",
            "supabase login",
            "supabase link",
            "supabase db push",
            "volume prune",
            "system prune",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_verify_only_without_runtime_manifest_is_non_mutating(self) -> None:
        with run_patched_fixture("-VerifyOnly", include_runtime=False) as (result, root):
            self.assertEqual(result.returncode, 2)
            self.assertEqual(
                result.stdout.strip(),
                "[FAIL] step=LOAD-PATCHED-SUPABASE-RUNTIME-MANIFEST reason=missing code=2",
            )
            self.assertFalse(result.stderr)
            self.assertFalse((root / ".tools").exists())

    def test_duplicate_or_unknown_arguments_fail_before_work(self) -> None:
        for arguments in (
            ("-VerifyOnly", "-VerifyOnly"),
            ("-VerifyOnly", "-Unknown"),
            ("-GoArchivePath",),
        ):
            with self.subTest(arguments=arguments):
                with run_patched_fixture(*arguments, include_runtime=False) as (result, root):
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(
                        result.stdout.strip(),
                        "[FAIL] step=VALIDATE-PATCHED-SUPABASE-ARGUMENTS reason=invalid code=2",
                    )
                    self.assertFalse(result.stderr)
                    self.assertFalse((root / ".tools").exists())

    def test_unapproved_source_manifest_fails_before_network(self) -> None:
        with run_patched_fixture(
            "-BuildCandidate",
            mutate_source=lambda value: value["upstream"].update(
                {"repository": "https://example.invalid/supabase/cli.git"}
            ),
            include_runtime=False,
        ) as (result, root):
            self.assertEqual(result.returncode, 2)
            self.assertEqual(
                result.stdout.strip(),
                "[FAIL] step=VALIDATE-PATCHED-SUPABASE-SOURCE-MANIFEST reason=unapproved-source code=2",
            )
            self.assertFalse(result.stderr)
            self.assertFalse((root / ".tools").exists())

    def test_duplicate_source_property_fails_before_runtime_or_network(self) -> None:
        duplicate_source = SOURCE_MANIFEST.read_text(encoding="utf-8").replace(
            '    "repository": "https://github.com/supabase/cli.git",',
            '    "repository": "https://github.com/supabase/cli.git",\n'
            '    "repository": "https://github.com/supabase/cli.git",',
            1,
        )
        with patch.object(json, "dumps", return_value=duplicate_source.rstrip("\n")):
            with run_patched_fixture("-VerifyOnly", include_runtime=False) as (result, root):
                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    result.stdout.strip(),
                    "[FAIL] step=VALIDATE-PATCHED-SUPABASE-SOURCE-MANIFEST "
                    "reason=unapproved-source code=2",
                )
                self.assertFalse(result.stderr)
                self.assertFalse((root / ".tools").exists())

    def test_non_scalar_source_values_fail_before_runtime_or_network(self) -> None:
        scalar_paths = (
            ("schema_version",),
            ("upstream", "repository"),
            ("upstream", "tag"),
            ("upstream", "tag_object_sha1"),
            ("upstream", "commit_sha1"),
            ("go", "version"),
            ("go", "platform"),
            ("go", "url"),
            ("go", "sha256"),
            ("patch", "relative_path"),
            ("patch", "size_bytes"),
            ("patch", "sha256"),
            ("build", "working_directory"),
            ("build", "version"),
            ("build", "goos"),
            ("build", "goarch"),
            ("build", "cgo_enabled"),
            ("build", "goproxy"),
            ("build", "gosumdb"),
            ("build", "goprivate"),
            ("build", "gonoproxy"),
            ("build", "gonosumdb"),
            ("build", "goinsecure"),
            ("build", "goenv"),
            ("build", "gowork"),
            ("build", "gotoolchain"),
            ("build", "goflags"),
            ("build", "goamd64"),
            ("build", "goexperiment"),
            ("build", "ldflags"),
        )

        def poison_scalar(source: dict[str, object], path: tuple[str, ...]) -> None:
            node = source
            for segment in path[:-1]:
                node = node[segment]  # type: ignore[assignment]
            value = node[path[-1]]
            node[path[-1]] = str(value) if isinstance(value, int) else [value]

        cases = tuple((path, None) for path in scalar_paths) + (
            (("patch", "allowed_files", "0"), "nested"),
            (("build", "flags", "0"), "nested"),
        )
        for path, kind in cases:
            with self.subTest(path=".".join(path)):
                def mutate(
                    source: dict[str, object],
                    path: tuple[str, ...] = path,
                    kind: str | None = kind,
                ) -> None:
                    if kind == "nested":
                        values = source[path[0]][path[1]]  # type: ignore[index]
                        values[int(path[2])] = [values[int(path[2])]]
                    else:
                        poison_scalar(source, path)

                with run_patched_fixture(
                    "-VerifyOnly",
                    mutate_source=mutate,
                    include_runtime=False,
                ) as (result, root):
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(
                        result.stdout.strip(),
                        "[FAIL] step=VALIDATE-PATCHED-SUPABASE-SOURCE-MANIFEST "
                        "reason=unapproved-source code=2",
                    )
                    self.assertFalse(result.stderr)
                    self.assertFalse((root / ".tools").exists())

    def test_non_scalar_runtime_values_fail_before_binary_work(self) -> None:
        source_hash = hashlib.sha256(SOURCE_MANIFEST.read_bytes()).hexdigest()
        runtime_template: dict[str, object] = {
            "schema_version": 1,
            "source_manifest_sha256": source_hash,
            "version": "2.109.1",
            "platform": "windows-amd64",
            "relative_path": ".tools/supabase/v2.109.1-sejong-loopback/supabase.exe",
            "sha256": "0" * 64,
        }
        real_copy2 = shutil.copy2
        for key in runtime_template:
            with self.subTest(key=key):
                runtime = dict(runtime_template)
                value = runtime[key]
                runtime[key] = str(value) if isinstance(value, int) else [value]

                def copy_with_runtime(
                    source: str | os.PathLike[str],
                    destination: str | os.PathLike[str],
                    *args: object,
                    runtime: dict[str, object] = runtime,
                    **kwargs: object,
                ) -> str:
                    if Path(source) == RUNTIME_MANIFEST:
                        Path(destination).write_text(
                            json.dumps(runtime, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8",
                        )
                        return str(destination)
                    return str(real_copy2(source, destination, *args, **kwargs))

                with patch.object(shutil, "copy2", side_effect=copy_with_runtime):
                    with run_patched_fixture(
                        "-VerifyOnly",
                        include_runtime=True,
                    ) as (result, root):
                        self.assertEqual(result.returncode, 2)
                        self.assertEqual(
                            result.stdout.strip(),
                            "[FAIL] step=LOAD-PATCHED-SUPABASE-RUNTIME-MANIFEST "
                            "reason=invalid code=2",
                        )
                        self.assertFalse(result.stderr)
                        self.assertFalse((root / ".tools").exists())

    def test_override_inside_owned_cleanup_tree_is_rejected_without_mutation(
        self,
    ) -> None:
        for mutable_child in (
            "cache",
            "go",
            "supabase-source",
            "supabase-build",
            "supabase",
        ):
            with self.subTest(mutable_child=mutable_child), tempfile.TemporaryDirectory(
                prefix="sejong unsafe go override "
            ) as directory:
                root = Path(directory)
                override = root / ".tools" / mutable_child / "owned" / "override.zip"
                override.parent.mkdir(parents=True)
                payload = b"read-only-invalid-override"
                override.write_bytes(payload)
                before = {
                    path.relative_to(root).as_posix() for path in root.rglob("*")
                }

                @contextmanager
                def fixed_directory(*_args: object, **_kwargs: object) -> Iterator[str]:
                    yield str(root)

                with patch.object(tempfile, "TemporaryDirectory", fixed_directory):
                    with run_patched_fixture(
                        "-BuildCandidate",
                        "-GoArchivePath",
                        str(override),
                        include_runtime=False,
                    ) as (result, fixture_root):
                        self.assertEqual(fixture_root, root)
                        self.assertEqual(result.returncode, 2)
                        self.assertEqual(
                            result.stdout.strip(),
                            "[START] step=VERIFY-GO-ARCHIVE\n"
                            "[FAIL] step=VERIFY-GO-ARCHIVE reason=invalid code=2",
                        )
                        self.assertFalse(result.stderr)
                        self.assertEqual(override.read_bytes(), payload)
                        after = {
                            path.relative_to(root).as_posix() for path in root.rglob("*")
                        }
                        self.assertEqual(
                            after - before,
                            {
                                "scripts",
                                "scripts/bootstrap_patched_supabase.ps1",
                                "scripts/patches",
                                "scripts/patches/supabase-cli-v2.109.1-db-loopback.patch",
                                "scripts/supabase-cli.local-patch.source.json",
                            },
                        )

    def test_reparse_override_targeting_owned_tree_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong reparse go override ") as directory:
            root = Path(directory)
            owned = root / ".tools" / "go" / "owned"
            owned.mkdir(parents=True)
            target = owned / "override.zip"
            payload = b"read-only-reparse-override"
            target.write_bytes(payload)
            alias = root / "external-override-alias"
            junction_environment = os.environ.copy()
            junction_environment["SEJONG_TEST_JUNCTION_ALIAS"] = str(alias)
            junction_environment["SEJONG_TEST_JUNCTION_TARGET"] = str(owned)
            junction = subprocess.run(
                [
                    powershell_executable(),
                    "-NoProfile",
                    "-Command",
                    "New-Item -ItemType Junction "
                    "-Path $env:SEJONG_TEST_JUNCTION_ALIAS "
                    "-Target $env:SEJONG_TEST_JUNCTION_TARGET | Out-Null",
                ],
                capture_output=True,
                check=False,
                encoding="utf-8",
                env=junction_environment,
                errors="replace",
                timeout=30,
            )
            self.assertEqual(junction.returncode, 0, junction.stderr)

            @contextmanager
            def fixed_directory(*_args: object, **_kwargs: object) -> Iterator[str]:
                yield str(root)

            try:
                with patch.object(tempfile, "TemporaryDirectory", fixed_directory):
                    with run_patched_fixture(
                        "-BuildCandidate",
                        "-GoArchivePath",
                        str(alias / "override.zip"),
                        include_runtime=False,
                    ) as (result, _fixture_root):
                        self.assertEqual(result.returncode, 2)
                        self.assertEqual(
                            result.stdout.strip(),
                            "[START] step=VERIFY-GO-ARCHIVE\n"
                            "[FAIL] step=VERIFY-GO-ARCHIVE reason=invalid code=2",
                        )
                        self.assertFalse(result.stderr)
                        self.assertEqual(target.read_bytes(), payload)
            finally:
                os.rmdir(alias)

    def test_install_rollback_preserves_backup_on_restore_failure(self) -> None:
        script = BOOTSTRAP_PATH.read_text(encoding="utf-8")
        for token in (
            "$replacementCompleted = $false",
            "$rollbackRestored = $false",
            "$preserveBackup = $true",
            "if (-not $preserveBackup",
            '"INSTALL-PATCHED-SUPABASE" "operational" 2',
        ):
            self.assertIn(token, script)

    def test_child_timeout_starts_suspended_before_job_assignment(self) -> None:
        script = BOOTSTRAP_PATH.read_text(encoding="utf-8")
        for token in (
            "CreateJobObject",
            "SetInformationJobObject",
            "CreateProcess",
            "CREATE_SUSPENDED",
            "AssignProcessToJobObject",
            "ResumeThread",
            "TerminateJobObject",
            "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
            "Task.WaitAll",
        ):
            self.assertIn(token, script)
        self.assertLess(
            script.index("AssignProcessToJobObject(job, processInformation.Process)"),
            script.index("ResumeThread(processInformation.Thread)"),
        )

    def test_child_timeout_terminates_spawned_descendant(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong child tree ") as directory:
            root = Path(directory)
            harness = root / "job_harness.ps1"
            parent_script = root / "spawn_parent.ps1"
            pid_file = root / "descendant.pid"
            parent_script.write_text(
                r"""
param([string]$PidFile)
$ErrorActionPreference = "Stop"
$child = Start-Process -FilePath powershell.exe -ArgumentList @(
    "-NoProfile",
    "-Command",
    "Start-Sleep -Seconds 30"
) -PassThru
$child.Id | Set-Content -LiteralPath $PidFile
Start-Sleep -Seconds 30
""".lstrip(),
                encoding="utf-8",
            )
            harness.write_text(
                r"""
param(
    [string]$Bootstrap,
    [string]$PowerShell,
    [string]$ParentScript,
    [string]$PidFile
)
$ErrorActionPreference = "Stop"
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $Bootstrap,
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -ne 0) {
    exit 1
}
$wanted = @(
    "Throw-PatchedBootstrapFailure",
    "ConvertTo-PatchedProcessArgument",
    "Initialize-PatchedJobSupport",
    "Invoke-PatchedChild"
)
foreach ($functionAst in @($ast.FindAll(
    {
        param($node)
        $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
            $wanted -contains $node.Name
    },
    $true
))) {
    . ([ScriptBlock]::Create($functionAst.Extent.Text))
}
$script:CurrentStep = "TEST-CHILD-TREE"
$probe = Invoke-PatchedChild $PowerShell @(
    "-NoProfile",
    "-Command",
    "[Console]::Out.WriteLine('child-probe-ok')"
) (Get-Location).Path 5000
if (
    $probe.TimedOut -or
    $probe.ExitCode -ne 0 -or
    $probe.Stdout.Trim() -cne "child-probe-ok"
) {
    [Console]::Error.WriteLine(
        "probe-failed timed_out=$($probe.TimedOut) exit_code=$($probe.ExitCode) " +
        "stdout=$($probe.Stdout) stderr=$($probe.Stderr)"
    )
    exit 1
}
$result = Invoke-PatchedChild $PowerShell @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $ParentScript,
    $PidFile
) (Get-Location).Path 5000
if (-not $result.TimedOut -or $result.ExitCode -ne -1) {
    [Console]::Error.WriteLine(
        "unexpected-result timed_out=$($result.TimedOut) exit_code=$($result.ExitCode)"
    )
    exit 1
}
if (-not (Test-Path -LiteralPath $PidFile -PathType Leaf)) {
    [Console]::Error.WriteLine(
        "descendant-pid-missing stdout=$($result.Stdout) stderr=$($result.Stderr)"
    )
    exit 1
}
$descendantPid = [int](Get-Content -LiteralPath $PidFile -Raw)
for ($attempt = 0; $attempt -lt 20; $attempt += 1) {
    if ($null -eq (Get-Process -Id $descendantPid -ErrorAction SilentlyContinue)) {
        [Console]::Out.WriteLine("DESCENDANT-TIMEOUT-OK")
        exit 0
    }
    Start-Sleep -Milliseconds 100
}
[Console]::Error.WriteLine("descendant-still-running pid=$descendantPid")
exit 1
""".lstrip(),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    powershell_executable(),
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(harness),
                    str(BOOTSTRAP_PATH),
                    powershell_executable(),
                    str(parent_script),
                    str(pid_file),
                ],
                cwd=root,
                capture_output=True,
                check=False,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), "DESCENDANT-TIMEOUT-OK")
            self.assertFalse(result.stderr)

    def test_unapproved_go_build_environment_fails_before_network(self) -> None:
        poisoned = {
            "gonoproxy": "example.invalid",
            "goinsecure": "example.invalid",
            "goenv": "C:/unapproved/go.env",
            "gowork": "C:/unapproved/go.work",
            "gotoolchain": "auto",
            "goflags": "-mod=mod",
            "goamd64": "v3",
            "goexperiment": "arenas",
        }
        for key, value in poisoned.items():
            with self.subTest(key=key):
                with run_patched_fixture(
                    "-BuildCandidate",
                    mutate_source=lambda source, key=key, value=value: source[
                        "build"
                    ].update({key: value}),
                    include_runtime=False,
                ) as (result, root):
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(
                        result.stdout.strip(),
                        "[FAIL] step=VALIDATE-PATCHED-SUPABASE-SOURCE-MANIFEST reason=unapproved-source code=2",
                    )
                    self.assertFalse(result.stderr)
                    self.assertFalse((root / ".tools").exists())


if __name__ == "__main__":
    unittest.main()
