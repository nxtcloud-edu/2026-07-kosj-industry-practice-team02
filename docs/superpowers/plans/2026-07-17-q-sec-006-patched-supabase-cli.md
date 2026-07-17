# Q-SEC-006 Patched Supabase CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and pin a project-local Supabase CLI v2.109.1 whose local database publish request explicitly binds to `127.0.0.1`, then use it to complete the fail-closed DB-001 local baseline.

**Architecture:** Keep the official stock CLI as a rollback reference and build only the official directly runnable `apps/cli-go` command from an exact annotated tag/commit. A tracked source manifest pins upstream, Go, patch, dependency-verification, short Windows checkout roots and path budget; a second tracked runtime manifest is created only after two independent clean builds produce the same binary SHA-256. The existing DB runner accepts only that runtime-pinned binary and still inspects the actual Docker binding before reset, credentials, or SQL.

**Tech Stack:** Windows PowerShell 5.1, Git, official Go 1.25.11 Windows AMD64, Supabase CLI Go source v2.109.1, Python 3.12 standard-library unittest, Docker Desktop 4.62.0/Engine 29.2.1, PostgreSQL 17.6, pgTAP.

**Implementation status (2026-07-18):** Tasks 1/2/2A/2B are implemented and independently reviewed.
Q-TOOL-001=A/D-032/ADR-0014 resolves A-025 by selecting `.tools/s/a`, `.tools/s/b` and a pre-checkout
path-budget gate. The revised Task 2C plan awaits user approval. Do not edit tooling or resume Task 3 until
that approval; the old `.tools/supabase-source/...` partial tree remains quarantined and must not be deleted.

## Global Constraints

- Decision authority is Q-SEC-006=A/D-031/ADR-0013 plus Q-TOOL-001=A/D-032/ADR-0014 and the amended written specification.
- Upstream repository is exactly `https://github.com/supabase/cli.git`; annotated tag object is `9d25ff8b5b0fba3c6f0ef000e7dd658c8d710c38`; peeled commit is `6d4c19870ed213ba7f682f117d0345c8a40bfa94`.
- Go is exactly 1.25.11 from `https://dl.google.com/go/go1.25.11.windows-amd64.zip` with SHA-256 `b7401f1b41517428e537493316256fb7cf03c66a130a0103ab07f3a2152e2112`.
- The source patch is exactly two upstream files: `apps/cli-go/internal/db/start/start_test.go` and `apps/cli-go/internal/db/start/start.go`.
- Repository `.gitattributes` keeps tracked text LF; every upstream checkout forces local
  `core.autocrlf=false` and local `core.longpaths=true` before patching/building. Never mutate global Git config.
- Source checkouts are exactly `.tools/s/a` and `.tools/s/b`. The source manifest pins tool-root-relative
  `s/a`, `s/b`, maximum tracked relative file path 134 and maximum absolute file path 248. Validate both
  projected paths before cleanup, directory creation, Go archive download/extraction or network fetch.
- Never read, reuse, migrate or automatically delete the failed ignored `.tools/supabase-source/6d4c19870ed213ba7f682f117d0345c8a40bfa94/` tree.
- Do not patch `internal/db/diff`, build the Bun wrapper, add a production dependency, change Docker Desktop settings, or weaken the exact single-loopback gate.
- Use `GOPROXY=https://proxy.golang.org`, `GOSUMDB=sum.golang.org`, empty `GOPRIVATE`, `GONOPROXY`,
  `GONOSUMDB`, and `GOINSECURE`; require `go mod verify`.
- Build with `GOOS=windows`, `GOARCH=amd64`, `GOAMD64=v1`, `CGO_ENABLED=0`, `GOENV=off`,
  `GOWORK=off`, `GOTOOLCHAIN=local`, empty `GOFLAGS` and `GOEXPERIMENT`, `-trimpath`,
  `-buildvcs=false`, and `-ldflags=-s -w -X github.com/supabase/cli/internal/utils.Version=2.109.1`;
  save and restore every pinned variable and do not embed telemetry credentials.
- Preserve `.tools/supabase/v2.109.1/`; install the patched executable only at `.tools/supabase/v2.109.1-sejong-loopback/supabase.exe`.
- Never run `supabase login`, `link`, `db push`, a remote project command, volume deletion, prune, or public deployment.
- Before the patched runtime manifest and runner gate pass, do not start/reset the DB or read credentials. If any actual binding is wildcard, null, multiple, unpublished, or on the wrong port/network, stop only a runner-owned runtime and return to container zero.
- Preserve public API 2.0.1-draft, application/web/shared versions, six immutable migrations and compensations, official/mock data 0, no-seed `/ready=503`, privacy/retention, and A-021/Q-SEC-003 public-release default B.
- Every task ends with its focused tests, diff review, implementation-note update where applicable, and a commit. Do not combine task commits.

---

## Plan governance

- Plan ID: `DB-001-T10-QSEC006-PLAN`
- Status: Revised after Q-TOOL-001=A; awaiting user approval before Task 2C
- User approval: `계획 승인, 구현 시작` on 2026-07-17 KST
- Amendment decision: `Q-TOOL-001: A` on 2026-07-18 KST; implementation approval for this revision not yet received
- Date: 2026-07-17 KST
- Branch: `codex/db-001-layered-enforcement`
- Worktree: `.worktrees/db-001-layered-enforcement`
- Specification: [Q-SEC-006 patched CLI design](../specs/2026-07-17-q-sec-006-patched-supabase-cli-design.md)
- Parent plan: [DB-001 layered enforcement](2026-07-16-db-001-layered-enforcement.md)
- Decision: [D-031](../../decisions/DECISION_LOG.md), [ADR-0013](../../adr/0013-project-local-patched-supabase-cli.md)
- Planning note: [IMP-20260717-011](../../implementation-notes/IMP-20260717-011-q-sec-006-명세-승인과-patched-supabase-cli-실행계획.md)
- Execution mode: use a fresh implementation worker per task and separate specification/quality review when agent capacity is available. If capacity is unavailable, perform the same two reviews inline and record that limitation.

## File map and ownership

Create during implementation:

- `scripts/patches/supabase-cli-v2.109.1-db-loopback.patch` — reviewable upstream test-first and one-field production patch.
- `scripts/supabase-cli.local-patch.source.json` — immutable upstream, Go, patch and build-input lock.
- `scripts/supabase-cli.local-patch.runtime.json` — exact binary output/version/hash lock, added only after reproducible builds agree.
- `scripts/bootstrap_patched_supabase.ps1` — verify-only, candidate-build and install workflow with stable output.
- `scripts/tests/test_patched_supabase_tooling.py` — source/patch/bootstrap/runtime contract and behavior tests.
- `docs/implementation-notes/IMP-20260717-012-...md` — implementation/full-gate evidence generated during Task 5.

Modify during implementation:

- `scripts/verify_database.ps1:565-640` — select and verify only the patched runtime.
- `scripts/tests/test_supabase_tooling.py:15-220, 520-1415` — synthetic runner fixture and exact patched-bootstrap/path assertions.
- `scripts/README.md` — source lock, candidate build, runtime pin, install/verify and rollback commands.
- `TASKS.md`, `README.md`, `CHANGELOG.md`, `CODEX_FILE_INDEX.md` — verified local baseline status.
- `docs/03_ARCHITECTURE.md`, `docs/07_SECURITY_PRIVACY.md`, `docs/08_TEST_STRATEGY.md`, `docs/12_VERSIONING_AND_RELEASES.md`, `docs/15_DEPLOYMENT_AND_OPERATIONS.md` — actual tooling/runtime authority.
- `docs/source-of-truth/TEAM_DECISIONS.md`, `docs/decisions/DECISION_LOG.md`, `docs/11_AMBIGUITY_REGISTER.md` — D-031 implementation result without changing Q-SEC-003.
- `docs/discovery/DB_001_DISCOVERY_REPORT.md`, `docs/test-reports/DB-001-LOCAL-BASELINE.md`, `docs/handoffs/HANDOFF-20260717-DB-001-LOCAL-BASELINE.md` — fresh evidence and recovery.
- parent DB spec/plan, this plan, `versions/manifest.json`, implementation-note INDEX.

Preserve unchanged:

- `scripts/bootstrap_supabase.ps1` and `scripts/supabase-cli.version.json` stock tooling.
- `supabase/migrations/`, `database/rollbacks/`, `database/schema-v1.draft.sql`, `supabase/tests/database/`.
- `apps/api/src`, `apps/web`, `contracts`, `data`, `prompts`, dependency and lock files.
- `PACKAGE_MANIFEST.json`, `.env.example`, ignored real `.env`, remote/public state.

## Interfaces

### Source manifest

`scripts/supabase-cli.local-patch.source.json` is consumed only by the patched bootstrap. It contains
`schema_version`, exact `upstream`, exact `go`, exact `patch`, and exact `build`; unknown or missing
properties fail before network or `.tools/` mutation.

### Runtime manifest

`scripts/supabase-cli.local-patch.runtime.json` contains exactly:

- `schema_version: 1`
- `source_manifest_sha256`: SHA-256 of the tracked source manifest bytes
- `version: 2.109.1`
- `platform: windows-amd64`
- `relative_path: .tools/supabase/v2.109.1-sejong-loopback/supabase.exe`
- `sha256`: the lowercase 64-character value emitted after two independent builds agree

The bootstrap and DB runner do not accept a PATH fallback or the stock binary.

### Bootstrap command contract

Exactly one mode is required:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -BuildCandidate
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -Install
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -VerifyOnly
```

`-GoArchivePath <zip>` is allowed only with `-BuildCandidate` or `-Install`. Child output is suppressed.
Parent output uses stable uppercase step identifiers; the candidate success line alone adds
`sha256=<64 lowercase hex>`.

## Task 1: Pin the exact source and two-file patch

**Files:**

- Create: `scripts/tests/test_patched_supabase_tooling.py`
- Create: `scripts/patches/supabase-cli-v2.109.1-db-loopback.patch`
- Create: `scripts/supabase-cli.local-patch.source.json`

**Interfaces:**

- Consumes: D-031 exact upstream/Go/build values.
- Produces: patch SHA-256 `109c096480e8185d761e9ce8fba10e93efc55190c42eab978f769a6993833f7d`, 1,824 LF-normalized UTF-8 bytes, and the source manifest consumed by Task 2.

- [ ] **Step 1: Write the failing source-lock tests**

Create `scripts/tests/test_patched_supabase_tooling.py` with this initial content:

```python
from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling.PatchedSourceLockTests -v
```

Expected: two failures because the source manifest and patch do not exist. No `.tools/` path is created.

- [ ] **Step 3: Add the exact upstream patch**

Create `scripts/patches/supabase-cli-v2.109.1-db-loopback.patch` with `apply_patch`. The block below is
a whitespace-safe byte recipe: replace every literal `<SP>` with one ASCII space (U+0020) and every
literal `<TAB>` with one tab (U+0009). The markers themselves must not appear in the created file.
Preserve LF UTF-8 and one final newline; the decoded file must be exactly 1,824 bytes with the pinned
SHA-256.

```diff
diff --git a/apps/cli-go/internal/db/start/start_test.go b/apps/cli-go/internal/db/start/start_test.go
--- a/apps/cli-go/internal/db/start/start_test.go
+++ b/apps/cli-go/internal/db/start/start_test.go
@@ -11,6 +11,7 @@ import (
<SP><TAB>"github.com/docker/docker/api/types"
<SP><TAB>"github.com/docker/docker/api/types/container"
<SP><TAB>"github.com/docker/docker/api/types/volume"
+<TAB>"github.com/docker/go-connections/nat"
<SP><TAB>"github.com/h2non/gock"
<SP><TAB>"github.com/spf13/afero"
<SP><TAB>"github.com/stretchr/testify/assert"
@@ -23,6 +24,21 @@ import (
<SP><TAB>"github.com/supabase/cli/pkg/pgtest"
<SP>)
<SP>
+func TestNewHostConfigBindsDatabaseToIPv4Loopback(t *testing.T) {
+<TAB>originalPort := utils.Config.Db.Port
+<TAB>t.Cleanup(func() {
+<TAB><TAB>utils.Config.Db.Port = originalPort
+<TAB>})
+<TAB>utils.Config.Db.Port = 54322
+
+<TAB>hostConfig := NewHostConfig()
+<TAB>bindings := hostConfig.PortBindings[nat.Port("5432/tcp")]
+
+<TAB>require.Len(t, bindings, 1)
+<TAB>assert.Equal(t, "127.0.0.1", bindings[0].HostIP)
+<TAB>assert.Equal(t, "54322", bindings[0].HostPort)
+}
+
<SP>func TestInitBranch(t *testing.T) {
<SP><TAB>t.Run("throws error on permission denied", func(t *testing.T) {
<SP><TAB><TAB>// Setup in-memory fs
diff --git a/apps/cli-go/internal/db/start/start.go b/apps/cli-go/internal/db/start/start.go
--- a/apps/cli-go/internal/db/start/start.go
+++ b/apps/cli-go/internal/db/start/start.go
@@ -119,6 +119,6 @@ func NewHostConfig() container.HostConfig {
<SP><TAB>hostPort := strconv.FormatUint(uint64(utils.Config.Db.Port), 10)
<SP><TAB>hostConfig := container.HostConfig{
-<TAB><TAB>PortBindings:  nat.PortMap{"5432/tcp": []nat.PortBinding{{HostPort: hostPort}}},
+<TAB><TAB>PortBindings:  nat.PortMap{"5432/tcp": []nat.PortBinding{{HostIP: "127.0.0.1", HostPort: hostPort}}},
<SP><TAB><TAB>RestartPolicy: container.RestartPolicy{Name: container.RestartPolicyUnlessStopped},
<SP><TAB><TAB>Binds: []string{
<SP><TAB><TAB><TAB>utils.DbId + ":/var/lib/postgresql/data",
```

- [ ] **Step 4: Add the exact source manifest**

Create `scripts/supabase-cli.local-patch.source.json` with the exact JSON represented by
`EXPECTED_SOURCE`, preserving its property order and adding one final newline. Do not add a runtime
manifest in this task.

- [ ] **Step 5: Verify GREEN and patch applicability**

Run with a fresh exact checkout:

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling.PatchedSourceLockTests -v
$patchCheckRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("sejong-supabase-patch-check-" + [guid]::NewGuid().ToString("N"))
git -c core.autocrlf=false clone --quiet --depth 1 --branch v2.109.1 --filter=blob:none https://github.com/supabase/cli.git $patchCheckRoot
if ((git -C $patchCheckRoot rev-parse 'refs/tags/v2.109.1^{}').Trim() -cne '6d4c19870ed213ba7f682f117d0345c8a40bfa94') { throw 'unexpected upstream commit' }
git -C $patchCheckRoot apply --check "$PWD\scripts\patches\supabase-cli-v2.109.1-db-loopback.patch"
Get-FileHash -Algorithm SHA256 scripts/patches/supabase-cli-v2.109.1-db-loopback.patch
git diff --check
$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\') + '\'
$resolvedCheckRoot = [System.IO.Path]::GetFullPath($patchCheckRoot)
if (-not $resolvedCheckRoot.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase) -or -not ([System.IO.Path]::GetFileName($resolvedCheckRoot)).StartsWith('sejong-supabase-patch-check-', [System.StringComparison]::Ordinal)) { throw 'unsafe patch-check cleanup path' }
Remove-Item -LiteralPath $resolvedCheckRoot -Recurse -Force
```

Expected: 2/2 tests pass; `git apply --check` exits 0; the patch hash is
`109C096480E8185D761E9CE8FBA10E93EFC55190C42EAB978F769A6993833F7D`; diff check passes.

- [ ] **Step 6: Commit Task 1**

```powershell
git add scripts/tests/test_patched_supabase_tooling.py scripts/patches/supabase-cli-v2.109.1-db-loopback.patch scripts/supabase-cli.local-patch.source.json
git commit -m "test(tooling): pin patched Supabase source contract"
```

## Task 2: Implement the fail-closed patched bootstrap

**Files:**

- Modify: `scripts/tests/test_patched_supabase_tooling.py`
- Create: `scripts/bootstrap_patched_supabase.ps1`

**Interfaces:**

- Consumes: Task 1 source manifest and patch.
- Produces: `-BuildCandidate`, `-Install`, `-VerifyOnly`, optional approved `-GoArchivePath`, stable output, two independent source/build artifacts, and no tracked mutation.

- [ ] **Step 1: Add failing bootstrap contract and behavior tests**

Extend the test module imports with `contextmanager`, `os`, `shutil`, `subprocess`, and `tempfile`. Add this
fixture helper, which copies the bootstrap, source manifest and patch into a temporary repository-shaped
fixture and keeps it alive for each assertion:

```python
from collections.abc import Callable, Iterator
from contextlib import contextmanager


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
```

Add these tests:

```python
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
```

- [ ] **Step 2: Run bootstrap tests and verify RED**

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests -v
```

Expected: failures because `scripts/bootstrap_patched_supabase.ps1` does not exist.

- [ ] **Step 3: Implement exact argument, manifest and child-process boundaries**

Create `scripts/bootstrap_patched_supabase.ps1` with PowerShell 5.1-compatible functions:

```powershell
function Throw-PatchedBootstrapFailure([string]$Step, [string]$Reason, [int]$Code)
function Resolve-SafeChildPath([string]$Root, [string]$Candidate)
function Remove-OwnedPath([string]$Root, [string]$Candidate)
function Invoke-PatchedChild([string]$FilePath, [string[]]$Arguments, [string]$WorkingDirectory, [int]$TimeoutMilliseconds)
function Read-PatchedJson([string]$Path, [string]$Step)
function Assert-ExactSourceManifest([object]$Manifest)
function Assert-ExactRuntimeManifest([object]$Manifest, [string]$SourceManifestHash)
function Test-PatchedSupabaseVersion([string]$BinaryPath)
function Get-VerifiedGoToolchain([string]$ArchiveOverride)
function New-VerifiedSupabaseCheckout([string]$Destination)
function Apply-And-TestSupabasePatch([string]$Checkout, [bool]$RequireRed)
function Build-PatchedSupabase([string]$Checkout, [string]$Output)
```

Implement the following exact control flow:

1. Parse raw `$args`; require exactly one of `-BuildCandidate`, `-Install`, `-VerifyOnly`; accept one
   `-GoArchivePath` value only for candidate/install. Reject duplicates, missing values and unknown tokens
   with `VALIDATE-PATCHED-SUPABASE-ARGUMENTS` before reading or creating `.tools/`.
2. Load and compare the source manifest to every constant in Task 1, including exact property names,
   patch byte count/hash and HTTPS hosts. Resolve the patch path under repository root and verify its bytes.
3. For verify-only, load the runtime manifest without creating `.tools/`; require exact source-manifest
   hash, version/platform/path and lowercase 64-hex binary hash. Verify file hash, then run `--version` with
   a 15-second timeout and require stdout exactly `2.109.1`.
4. For candidate/install, verify or download the Go ZIP to an owned `.tools/cache/` child, hash before
   extraction, extract to `.tools/go/1.25.11/windows-amd64`, and require `go version` to contain
   `go1.25.11 windows/amd64`. An override archive is read-only and is never deleted.
5. Before any Git or Go child process, save and pin `GOOS=windows`, `GOARCH=amd64`, `GOAMD64=v1`,
   `CGO_ENABLED=0`, `GOPROXY=https://proxy.golang.org`, `GOSUMDB=sum.golang.org`, empty `GOPRIVATE`,
   `GONOPROXY`, `GONOSUMDB`, `GOINSECURE`, `GOFLAGS`, and `GOEXPERIMENT`, plus `GOENV=off`,
   `GOWORK=off`, and `GOTOOLCHAIN=local`. Restore every variable in `finally`, including removing ones
   that were originally absent. Do not read or print unrelated environment values.
6. Recreate two owned checkout directories. For each, force `core.autocrlf=false`, `git init`, add only the approved origin, fetch
   `refs/tags/v2.109.1:refs/tags/v2.109.1` with `--depth=1 --filter=blob:none`, verify the tag object and
   peeled commit, and checkout detached exact commit.
7. Checkout A applies only the test file, runs focused `go test -json`, and accepts RED only when the JSON
   contains `Action=fail` for `TestNewHostConfigBindsDatabaseToIPv4Loopback`. Then apply production.
   Checkout B applies both allowed files without the RED probe.
8. On both checkouts require exact two-file `git diff --name-only`, `git diff --check`, `go mod verify`.
   On A require focused and full `go test ./internal/db/start -count=1` GREEN.
9. Build both outputs with the global exact flags; require identical SHA-256 and exact version.
10. Candidate mode leaves binaries only under ignored candidate paths and prints one hash-bearing PASS.
    Install mode requires runtime manifest hash equality before atomically moving checkout A output to the
    final path, then repeats hash/version verification.
11. Catch only controlled exceptions into stable `[FAIL]`; suppress all child stdout/stderr and dispose
    processes. Codes are 1 for integrity/child mismatch, 2 for arguments/manifest/missing/operational.

Required top-level step order is:

```text
VALIDATE-PATCHED-SUPABASE-ARGUMENTS
LOAD-PATCHED-SUPABASE-SOURCE-MANIFEST
VALIDATE-PATCHED-SUPABASE-SOURCE-MANIFEST
VERIFY-PATCHED-SUPABASE-PATCH
LOAD-PATCHED-SUPABASE-RUNTIME-MANIFEST        verify/install only
VERIFY-PATCHED-SUPABASE-BINARY                verify-only ends here after version
VERIFY-GO-ARCHIVE
VERIFY-GO-TOOLCHAIN
VERIFY-SUPABASE-SOURCE-A
VERIFY-SUPABASE-SOURCE-B
TEST-PATCHED-SUPABASE-RED
TEST-PATCHED-SUPABASE-GREEN
VERIFY-PATCHED-SUPABASE-MODULES
BUILD-PATCHED-SUPABASE-A
BUILD-PATCHED-SUPABASE-B
VERIFY-PATCHED-SUPABASE-REPRODUCIBILITY
BUILD-PATCHED-SUPABASE-CANDIDATE              candidate only
INSTALL-PATCHED-SUPABASE                      install only
VERIFY-PATCHED-SUPABASE-BINARY                install final
```

- [ ] **Step 4: Run focused and existing tooling tests**

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling -v
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling.SupabaseBootstrapBehaviorTests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

Expected: new tests pass; stock bootstrap tests remain unchanged and pass; secret/diff checks pass.

- [ ] **Step 5: Commit Task 2**

```powershell
git add scripts/bootstrap_patched_supabase.ps1 scripts/tests/test_patched_supabase_tooling.py
git commit -m "feat(tooling): build verified patched Supabase CLI"
```

## Task 2A: Correct deterministic Git discovery after the first real build attempt

**Files:**

- Modify: `scripts/tests/test_patched_supabase_tooling.py`
- Modify: `scripts/bootstrap_patched_supabase.ps1`

**Observed root cause:** On the approved Windows host, `Get-Command git.exe -CommandType Application`
returns two PATH applications. Reading `.Source` from the unbounded result produces an object array, which
PowerShell coerces into one space-joined scalar application path. `CreateProcess` therefore fails before
the first `git init` with stable `operational code=2`. Do not work around this by changing PATH.

- [ ] **Step 1: Add the focused multiple-Git RED**

Add `test_multiple_git_applications_select_first_path_without_array_coercion`. The test must extract and
execute the production Git-discovery function in a temporary harness whose PATH contains two real
`git.exe` decoys. Assert that `Get-Command` observes exactly two applications and the production function
returns exactly the first application's absolute path, never an array or space-joined path.

Run only the new test and confirm RED against the current unbounded `.Source` assignment.

- [ ] **Step 2: Implement the single root-cause fix**

Extract Git discovery into `Get-PatchedGitExecutable`. Collect the command results as an array, require at
least one result, select index zero (normal PATH precedence), require a non-empty absolute existing leaf,
and return one scalar full path. Replace only the current lines 1819–1821 discovery assignment with the
helper call. Preserve Git arguments, network allowlist, checkout verification, stable failures, and all
other build behavior.

- [ ] **Step 3: Verify the regression and full Task 2 boundary**

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling -v
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling.SupabaseBootstrapBehaviorTests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

Expected: the multiple-Git test and full patched/stock tooling suites pass; no network build or DB action
is required for this correction.

- [ ] **Step 4: Review exact scope and commit Task 2A**

Review the two-file unstaged diff, stage exactly the bootstrap and its test, verify the cached path set and
cached diff/check, then commit `fix(tooling): select one Git application path`. Obtain a fresh Task 2A
specification/quality review before restarting Task 3.

## Task 2B: Enable exact upstream checkout on Windows long paths

**Files:**

- Modify: `scripts/tests/test_patched_supabase_tooling.py`
- Modify: `scripts/bootstrap_patched_supabase.ps1`

**Observed root cause:** After Task 2A, source A successfully initialized Git and verified the exact origin,
tag object and peeled commit, then detached checkout failed with `Filename too long`. The isolated repository
had no local `core.longpaths` value and no `HEAD`. Do not shorten the workspace, change global Git config, or
skip files as a workaround.

- [ ] **Step 1: Add the focused checkout-configuration RED**

Add `test_checkout_sets_local_longpaths_before_fetch_and_checkout`. Extract the production
`New-VerifiedSupabaseCheckout` function into a temporary PowerShell harness with controlled stubs for path
ownership and `Invoke-VerifiedGit`. Simulate the approved origin/tag/commit/HEAD outputs, capture every exact
Git argument array, and require exactly one `config --local core.longpaths true` call after init/local
autocrlf and before remote/fetch/checkout. Also assert that no `--global`, `--system`, sparse checkout, path
exclusion or changed upstream command exists. Run the new test and confirm RED specifically because the local
longpaths call is absent.

- [ ] **Step 2: Implement the single repository-local fix**

Immediately after local `core.autocrlf=false`, add only:

```powershell
$null = Invoke-VerifiedGit @("config", "--local", "core.longpaths", "true") $checkout 30000
```

Preserve exact Git selection, init, origin, fetch, tag/commit verification, detached checkout, timeouts,
network allowlist, stable failures and every build/install behavior.

- [ ] **Step 3: Verify the regression and full Task 2 boundary**

Run the focused RED/GREEN, the full patched tooling suite, stock bootstrap behavior suite, secret scanner,
PowerShell 5.1 parser and diff check. No `-BuildCandidate`, network, Docker, DB or remote operation belongs in
Task 2B.

- [ ] **Step 4: Review exact scope and commit Task 2B**

Review the exact two-file diff, stage only the bootstrap and its test, assert the cached path set is exactly
those two files, review cached diff/check, and commit `fix(tooling): enable local Git long paths`. Obtain a
fresh specification/quality review before the next Task 3 retry.

## Task 2C: Shorten Windows checkout roots and enforce the path budget

**Files:**

- Modify: `scripts/supabase-cli.local-patch.source.json`
- Modify: `scripts/tests/test_patched_supabase_tooling.py`
- Modify: `scripts/bootstrap_patched_supabase.ps1`

**Interfaces:**

- Consumes: Q-TOOL-001=A/D-032/ADR-0014, Task 2B local `core.longpaths=true`, existing
  `Resolve-SafeChildPath` and `Remove-OwnedPath`.
- Produces: exact source-manifest `workspace` contract, `.tools/s/a` and `.tools/s/b`, fail-closed
  projected path validation before any checkout mutation, and no legacy checkout/build/delete path.

- [ ] **Step 1: Add source-workspace and production-path RED tests**

Extend `EXPECTED_SOURCE` in `scripts/tests/test_patched_supabase_tooling.py` with this exact peer of
`patch` and `build`:

```python
"workspace": {
    "checkout_a": "s/a",
    "checkout_b": "s/b",
    "max_tracked_relative_file_path_length": 134,
    "max_absolute_file_path_length": 248,
},
```

In `test_script_has_only_approved_modes_sources_and_operations`, require exact production literals
`$sourceManifest.workspace.checkout_a`, `$sourceManifest.workspace.checkout_b`, and
`VALIDATE-PATCHED-SUPABASE-CHECKOUT-WORKSPACE`; remove the two old long checkout destination literals.

Update existing `test_checkout_sets_local_longpaths_before_fetch_and_checkout` before production changes:
require the extracted `New-VerifiedSupabaseCheckout` AST parameter names to be exactly `Destination`,
`MaxTrackedRelativeFilePathLength`, `MaxAbsoluteFilePathLength`; this explicit signature assertion makes the
current one-parameter production function RED instead of allowing extra positional values through `$args`.
Set the expected destination to `s/a`, derive the expected checkout under the fixture `.tools`, and invoke
`New-VerifiedSupabaseCheckout $script:ExpectedDestination 134 248`. Define a controlled
`Assert-PatchedCheckoutPathBudget` stub that accepts only those exact three values, returns the expected
checkout, records one call, and fails if `Remove-OwnedPath` occurs first. Preserve the exact init/local
autocrlf/local longpaths/origin/fetch/tag/commit/checkout/HEAD argv, timeout and call-order assertions and
require exactly one budget-stub call before the one owned-path removal.

Add these five tests to `PatchedBootstrapContractTests` before any production change:

```python
def test_checkout_workspace_preflight_validates_both_roots_before_toolchain_or_mutation(self) -> None:
    """Main-flow AST order plus exact long-root fixture: both checks precede Go/tool/network/mutation."""

def test_checkout_budget_accepts_244_and_248_rejects_249_before_cleanup(self) -> None:
    """Synthetic roots prove current projection, inclusive cap, and fail-before-remove at cap+1."""

def test_remove_owned_path_cleans_inclusive_248_character_tree(self) -> None:
    """Existing PS5.1 cleanup must remove an owned non-reparse tree at the inclusive cap."""

def test_short_checkout_reparse_is_rejected_and_external_sentinel_untouched(self) -> None:
    """A `.tools/s` or `.tools/s/a` junction must fail controlled before external deletion."""

def test_legacy_source_root_is_deny_only_never_checkout_build_or_delete(self) -> None:
    """AST permits one exact deny-list string and zero data-flow uses as checkout/build/delete input."""
```

The main-flow test must inspect the script end block and require both manifest-derived A/B budget calls
before `Get-VerifiedGoToolchain`, `New-VerifiedSupabaseCheckout`, download/extraction helpers, directory
creation, `Remove-OwnedPath`, and child/network invocation. It must also run an exact source-manifest fixture
whose projected A path is 249, require the stable workspace failure, and prove `.tools` was never created.

The budget test uses synthetic roots to assert projected 244 and 248 both return the exact safe child, then
invokes `New-VerifiedSupabaseCheckout` at projected 249 with a stubbed `Remove-OwnedPath` counter and requires
`VALIDATE-PATCHED-SUPABASE-CHECKOUT-WORKSPACE:invalid:2` with counter zero. The legacy test walks PowerShell
AST string constants and command arguments: `supabase-source` must appear exactly once inside the
`-GoArchivePath` mutable-child deny list, and never flow to checkout destination, build working directory,
`Resolve-SafeChildPath`, `Remove-OwnedPath`, or directory creation.

The short-checkout reparse test creates a temporary external directory with a sentinel, creates only a
junction at the temporary fixture's `.tools/s` (and a subtest at `.tools/s/a`), calls the extracted production
checkout/path functions, requires controlled `VALIDATE-PATCHED-SUPABASE-PATH:invalid:2`, and proves the
sentinel and junction target are unchanged. It must remove only the junction during test teardown.

Extend existing `test_override_inside_owned_cleanup_tree_is_rejected_without_mutation` so
`mutable_child` includes `"s"`. Extend `test_reparse_override_targeting_owned_tree_is_rejected` with
`owned_child in ("go", "s")`. The `.tools/s` direct and junction archive overrides must both retain their
payload and fail at `VERIFY-GO-ARCHIVE reason=invalid` before hash, extraction, or checkout work.

First run the two unchanged-production characterizations:

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_remove_owned_path_cleans_inclusive_248_character_tree `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_short_checkout_reparse_is_rejected_and_external_sentinel_untouched -v
```

Expected: 2/2 PASS against unchanged `Resolve-SafeChildPath`/`Remove-OwnedPath`: the 248 tree is removed,
both junction cases are rejected, and the external sentinel is untouched. If either fails or leaves a partial
tree, stop and reopen Q-TOOL-001; do not implement the 248 cap.

Then run the remaining eight focused RED methods:

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest `
  scripts.tests.test_patched_supabase_tooling.PatchedSourceLockTests.test_source_manifest_is_exact `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_script_has_only_approved_modes_sources_and_operations `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_checkout_sets_local_longpaths_before_fetch_and_checkout `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_checkout_workspace_preflight_validates_both_roots_before_toolchain_or_mutation `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_checkout_budget_accepts_244_and_248_rejects_249_before_cleanup `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_legacy_source_root_is_deny_only_never_checkout_build_or_delete `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_override_inside_owned_cleanup_tree_is_rejected_without_mutation `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_reparse_override_targeting_owned_tree_is_rejected -v
```

Expected: 8 methods are RED only for the absent manifest workspace, short-root/signature/main-order/budget helper,
deny-only contract, and missing new `s` archive-override boundary. No repository `.tools` mutation, Go
download/extraction, network, Docker or DB action.

- [ ] **Step 2: Pin the exact workspace contract in the source manifest and validator**

Add this exact object to `scripts/supabase-cli.local-patch.source.json` between `patch` and `build`:

```json
"workspace": {
  "checkout_a": "s/a",
  "checkout_b": "s/b",
  "max_tracked_relative_file_path_length": 134,
  "max_absolute_file_path_length": 248
},
```

Update `Assert-ExactSourceManifest` so raw/parsed property allowlists include `workspace` and its four exact
properties. Require both checkout values to be non-empty strings; require both length values to be integers;
approve only the four literal values above. Do not increment schema version 1 because this manifest has no
published consumer and the validator changes atomically with it.

Run the exact manifest test again.

Expected: `test_source_manifest_is_exact` passes; the other production signature/behavior/archive-boundary tests remain RED.

- [ ] **Step 3: Add the fail-closed path-budget helper before any checkout mutation**

Add this helper after `Remove-OwnedPath`:

```powershell
function Assert-PatchedCheckoutPathBudget {
    param(
        [string]$Destination,
        [int]$MaxTrackedRelativeFilePathLength,
        [int]$MaxAbsoluteFilePathLength
    )

    $checkout = Resolve-SafeChildPath $script:ToolRoot $Destination
    $projectedMaximum = $checkout.Length + 1 + $MaxTrackedRelativeFilePathLength
    if (
        $MaxTrackedRelativeFilePathLength -ne 134 -or
        $MaxAbsoluteFilePathLength -ne 248 -or
        $projectedMaximum -gt $MaxAbsoluteFilePathLength
    ) {
        Throw-PatchedBootstrapFailure $script:CurrentStep "invalid" 2
    }
    return $checkout
}
```

Immediately after `$script:ToolRoot` is resolved and before Go archive/toolchain work, set
`$script:CurrentStep = "VALIDATE-PATCHED-SUPABASE-CHECKOUT-WORKSPACE"`, validate checkout A and B with
the four pinned manifest values, and emit one stable START/PASS pair. Then change
`New-VerifiedSupabaseCheckout` to accept the two length values and make the same helper its first operation,
before `Remove-OwnedPath`:

```powershell
$checkout = Assert-PatchedCheckoutPathBudget (
    $Destination
) $MaxTrackedRelativeFilePathLength $MaxAbsoluteFilePathLength
Remove-OwnedPath $script:ToolRoot $checkout
```

Replace the main calls with manifest-derived destinations:

```powershell
$checkoutA = New-VerifiedSupabaseCheckout (
    $sourceManifest.workspace.checkout_a
) $sourceManifest.workspace.max_tracked_relative_file_path_length (
    $sourceManifest.workspace.max_absolute_file_path_length
)
$checkoutB = New-VerifiedSupabaseCheckout (
    $sourceManifest.workspace.checkout_b
) $sourceManifest.workspace.max_tracked_relative_file_path_length (
    $sourceManifest.workspace.max_absolute_file_path_length
)
```

Add `"s"` to the existing mutable-child rejection list used by `-GoArchivePath`; retain the existing
`"supabase-source"` entry only as a deny boundary so the quarantined tree can never become an archive input.

Do not change `Remove-OwnedPath`, add Win32 deletion, touch the legacy long root, or alter Git/source/build
arguments. The approved current-worktree projections must be exactly 244 for both roots.

- [ ] **Step 4: Prove the pre-written workspace tests GREEN and run full boundaries**

Before the focused tests, remeasure the exact approved worktree projections without touching `.tools`:

```powershell
$root = (Resolve-Path -LiteralPath '.').Path
$relative = 'apps\cli-e2e\fixtures\scenarios\db-advisors-security-exits-zero-when-fail-on-error-and-no-error-level-advisors-found\interactions.json'
$projectedA = (Join-Path $root '.tools\s\a').Length + 1 + $relative.Length
$projectedB = (Join-Path $root '.tools\s\b').Length + 1 + $relative.Length
if ($relative.Length -ne 134 -or $projectedA -ne 244 -or $projectedB -ne 244) {
    throw "approved checkout projection changed"
}
```

Run all five new workspace tests plus the updated Git-argv harness and two expanded archive-override methods,
then full boundaries and the PowerShell parser:

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_checkout_workspace_preflight_validates_both_roots_before_toolchain_or_mutation `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_checkout_sets_local_longpaths_before_fetch_and_checkout `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_checkout_budget_accepts_244_and_248_rejects_249_before_cleanup `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_remove_owned_path_cleans_inclusive_248_character_tree `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_short_checkout_reparse_is_rejected_and_external_sentinel_untouched `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_legacy_source_root_is_deny_only_never_checkout_build_or_delete `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_override_inside_owned_cleanup_tree_is_rejected_without_mutation `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_reparse_override_targeting_owned_tree_is_rejected -v
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling -v
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling.SupabaseBootstrapBehaviorTests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
$tokens = $null
$errors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path scripts/bootstrap_patched_supabase.ps1),
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -ne 0) { throw "PowerShell parse failed" }
git diff --check
```

Expected: focused 8/8 methods, patched 23/23 and stock 7/7 pass; projected A/B are 244; 248 cleanup leaves no
partial tree; 249 calls cleanup zero times; short-root junction targets stay untouched; direct/reparse
`.tools/s` archive overrides fail invalid; secret scan/diff check exit 0 and parser errors 0. Do not run
`-BuildCandidate`, Docker or DB in Task 2C.

- [ ] **Step 5: Review exact three-file scope and commit Task 2C**

Review the literal workspace contract and every legacy-root use, then stage and verify exactly three files:

```powershell
$expected = @(
    'scripts/bootstrap_patched_supabase.ps1',
    'scripts/supabase-cli.local-patch.source.json',
    'scripts/tests/test_patched_supabase_tooling.py'
)
git add -- $expected
$staged = @(git -c core.quotepath=false diff --cached --name-only)
if (@(Compare-Object -ReferenceObject $expected -DifferenceObject $staged).Count -ne 0) {
    throw "unexpected staged scope"
}
git diff --cached -- scripts/bootstrap_patched_supabase.ps1 `
    scripts/supabase-cli.local-patch.source.json `
    scripts/tests/test_patched_supabase_tooling.py
git diff --cached --check
git commit -m "fix(tooling): shorten patched CLI checkout roots"
```

Obtain fresh independent specification and quality reviews with Critical/Important findings zero. Only then
may Task 3 preflight begin.

## Task 3: Produce and pin the reproducible runtime artifact

**Files:**

- Modify: `scripts/tests/test_patched_supabase_tooling.py`
- Create: `scripts/supabase-cli.local-patch.runtime.json`
- Generated/ignored: `.tools/go/1.25.11/windows-amd64/`, `.tools/s/a`, `.tools/s/b`, two candidate binaries, final patched binary. The legacy `.tools/supabase-source/...` partial tree is quarantined evidence, not an input.

**Interfaces:**

- Consumes: Task 2 candidate builder plus Task 2C short-root/path-budget contract and its independent approval.
- Produces: a reviewed literal binary SHA-256 and installed exact runtime accepted by Task 4.

- [ ] **Step 1: Preflight clean external state**

```powershell
git status --short
docker desktop status
docker version --format '{{.Server.Version}}'
docker ps -aq
docker ps -aq --filter 'label=com.supabase.cli.project=sejong-ai-local'
$finalPatchedBinary = Join-Path $PWD ".tools\supabase\v2.109.1-sejong-loopback\supabase.exe"
if (Test-Path -LiteralPath $finalPatchedBinary) { throw "unexpected pre-existing final binary" }
$shortA = Join-Path $PWD ".tools\s\a"
$shortB = Join-Path $PWD ".tools\s\b"
if (Test-Path -LiteralPath $shortA) { throw "unexpected pre-existing short checkout A" }
if (Test-Path -LiteralPath $shortB) { throw "unexpected pre-existing short checkout B" }
$bootstrapText = Get-Content -Raw -LiteralPath scripts/bootstrap_patched_supabase.ps1
$legacyDenyCount = [regex]::Matches($bootstrapText, '"supabase-source"').Count
if ($legacyDenyCount -ne 1) { throw "legacy deny boundary count changed" }
apps/api/.venv/Scripts/python.exe -B -m unittest `
  scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_legacy_source_root_is_deny_only_never_checkout_build_or_delete -v
if ($LASTEXITCODE -ne 0) { throw "legacy source root usage gate failed" }
```

Expected: Git clean; Desktop running; Engine `29.2.1`; both container queries empty. Stop if any container
exists, the Engine is below 28, the final patched binary/short checkout already exists, or the exact
deny-only legacy-root test fails. The legacy ignored tree may remain on disk and must not be deleted.

- [ ] **Step 2: Build the candidate twice and capture the agreed hash**

```powershell
$candidateOutput = powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -BuildCandidate
if ($LASTEXITCODE -ne 0) { throw "candidate build failed" }
$candidateLine = @($candidateOutput | Where-Object { $_ -match '^\[PASS\] step=BUILD-PATCHED-SUPABASE-CANDIDATE sha256=([0-9a-f]{64})$' })
if ($candidateLine.Count -ne 1) { throw "candidate hash evidence missing" }
$null = $candidateLine[0] -match 'sha256=([0-9a-f]{64})$'
$candidateSha256 = $Matches[1]
$candidateSha256
```

Expected: all source/test/module/build steps pass and exactly one lowercase 64-character hash is printed.
The script itself has already compared independent build A/B hashes. No final binary path is installed.

- [ ] **Step 3: Add the runtime contract test and runtime manifest**

Add this test:

```python
class PatchedRuntimeLockTests(unittest.TestCase):
    def test_runtime_manifest_and_installed_binary_are_exact(self) -> None:
        runtime = json.loads(RUNTIME_MANIFEST.read_text(encoding="utf-8"))
        source_hash = hashlib.sha256(SOURCE_MANIFEST.read_bytes()).hexdigest()
        self.assertEqual(
            set(runtime),
            {
                "schema_version",
                "source_manifest_sha256",
                "version",
                "platform",
                "relative_path",
                "sha256",
            },
        )
        self.assertEqual(runtime["schema_version"], 1)
        self.assertEqual(runtime["source_manifest_sha256"], source_hash)
        self.assertEqual(runtime["version"], "2.109.1")
        self.assertEqual(runtime["platform"], "windows-amd64")
        self.assertEqual(
            runtime["relative_path"],
            ".tools/supabase/v2.109.1-sejong-loopback/supabase.exe",
        )
        self.assertRegex(runtime["sha256"], r"^[0-9a-f]{64}$")
        binary = ROOT / Path(runtime["relative_path"])
        self.assertTrue(binary.is_file())
        self.assertEqual(hashlib.sha256(binary.read_bytes()).hexdigest(), runtime["sha256"])
```

Use `apply_patch` to create `scripts/supabase-cli.local-patch.runtime.json`. Enter the exact literal value
held in `$candidateSha256`, not an expression, and the exact source-manifest hash printed by:

```powershell
(Get-FileHash -Algorithm SHA256 scripts/supabase-cli.local-patch.source.json).Hash.ToLowerInvariant()
```

Run and prove the exact installation-boundary RED before installation:

```powershell
$runtimeRedOutput = & apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling.PatchedRuntimeLockTests -v 2>&1
$runtimeRedCode = $LASTEXITCODE
$runtimeRedText = $runtimeRedOutput -join [Environment]::NewLine
if ($runtimeRedCode -ne 1 -or $runtimeRedText -notmatch "AssertionError: False is not true") {
    throw "runtime RED was not the expected missing final binary"
}
$runtimeRedOutput
```

Expected: the runtime contract fails with exit code `1` specifically because the final binary is absent.

- [ ] **Step 4: Install only the pinned build and verify GREEN**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -Install
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -VerifyOnly
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling.PatchedRuntimeLockTests -v
& .\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe --version
```

Expected: install and verify-only pass; runtime test passes; version output is exactly `2.109.1`.

- [ ] **Step 5: Review artifact isolation and commit the runtime pin**

```powershell
git status --short --ignored
git diff --exit-code -- scripts/bootstrap_supabase.ps1 scripts/supabase-cli.version.json
git check-ignore .tools/supabase/v2.109.1-sejong-loopback/supabase.exe
git diff --check
git diff -- scripts/supabase-cli.local-patch.runtime.json scripts/tests/test_patched_supabase_tooling.py
git add scripts/supabase-cli.local-patch.runtime.json scripts/tests/test_patched_supabase_tooling.py
$staged = @(git -c core.quotepath=false diff --cached --name-only)
$expected = @(
    "scripts/supabase-cli.local-patch.runtime.json",
    "scripts/tests/test_patched_supabase_tooling.py"
)
if (@(Compare-Object -ReferenceObject $expected -DifferenceObject $staged).Count -ne 0) {
    throw "unexpected staged scope"
}
git diff --cached -- scripts/supabase-cli.local-patch.runtime.json scripts/tests/test_patched_supabase_tooling.py
git diff --cached --check
git commit -m "build(tooling): pin patched Supabase runtime"
```

Expected: all `.tools/` outputs are ignored; stock tooling has no diff; the literal runtime/source hashes and
full two-file diff are reviewed; exactly the runtime manifest and runtime test are staged and committed.

## Task 4: Make the DB runner require the patched runtime

**Files:**

- Modify: `scripts/tests/test_supabase_tooling.py`
- Modify: `scripts/verify_database.ps1`
- Modify: `scripts/README.md`

**Interfaces:**

- Consumes: Task 3 runtime manifest and binary.
- Produces: no stock/PATH fallback; existing actual Docker inspection remains the authority before reset.

- [ ] **Step 0: Require a clean tracked/untracked start**

```powershell
if (
    @(git diff --name-only).Count -ne 0 -or
    @(git diff --cached --name-only).Count -ne 0 -or
    @(git ls-files --others --exclude-standard).Count -ne 0
) { throw "Task 4 requires a clean tracked/untracked start" }
```

Ignored Task 3 `.tools/` artifacts are allowed; tracked and ordinary untracked state must be clean.

- [ ] **Step 1: Write failing runner-selection tests**

Add `PATCHED_BOOTSTRAP_PATH` and exact assertions that the runner source contains:

```python
PATCHED_BOOTSTRAP_PATH = ROOT / "scripts" / "bootstrap_patched_supabase.ps1"
PATCHED_RUNTIME_RELATIVE = Path(
    ".tools/supabase/v2.109.1-sejong-loopback/supabase.exe"
)

class PatchedDatabaseRunnerSelectionTests(unittest.TestCase):
    def test_runner_uses_only_runtime_pinned_patched_cli(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn(
            '".tools\\supabase\\v2.109.1-sejong-loopback\\supabase.exe"',
            script,
        )
        self.assertIn('"bootstrap_patched_supabase.ps1"', script)
        self.assertNotIn('".tools\\supabase\\v2.109.1\\supabase.exe"', script)
        self.assertNotIn('"bootstrap_supabase.ps1"', script)
        self.assertIn('"-VerifyOnly"', script)

    def test_runner_still_checks_actual_binding_before_reset(self) -> None:
        script = DATABASE_RUNNER_PATH.read_text(encoding="utf-8")
        start = script.index('-Step "START-LOCAL-DATABASE"')
        inspect = script.index("Assert-LocalDatabaseRuntime", start)
        reset = script.index('-Step "RESET-DATABASE-ONE"', inspect)
        self.assertLess(start, inspect)
        self.assertLess(inspect, reset)
```

Update the synthetic fixture only as follows:

- create `.tools/supabase/v2.109.1-sejong-loopback/` instead of the stock directory;
- write the synthetic success bootstrap under `bootstrap_patched_supabase.ps1`;
- leave the stock bootstrap fixture and its tests unchanged;
- preserve all Docker unsafe/multiple/null/wrong-network and cleanup simulations.
- extend the runner fixture with keyword-only `capture_patched_bootstrap`,
  `patched_bootstrap_exit_code`, `include_patched_runtime`, and `include_fallback_decoys` controls;
- add an opt-in patched-bootstrap JSONL capture that records exactly
  `["bootstrap","bootstrap_patched_supabase.ps1","-VerifyOnly"]` and permits controlled exit codes 0/1/2;
- add opt-in stock-path and PATH `supabase.exe` decoys without changing the stock-bootstrap fixture tests.

Add behavior tests that prove:

- the exact patched `-VerifyOnly` event occurs once after Docker version preflight and before network
  create/inspect, `db start`, actual binding inspection, reset, status, credentials, SQL, pgTAP or pytest;
- patched bootstrap exit 1 yields only the stable preflight/verify failure output and exactly the Docker
  version plus bootstrap events, with every network mutation and DB/application phase at zero calls;
- when the patched runtime is absent but stock and PATH decoys exist, preflight fails missing with zero
  child events and never falls back;
- source contains no `Get-Command`/`where`/`$env:PATH` Supabase discovery and each exact patched assignment
  and `-VerifyOnly` literal occurs once.

- [ ] **Step 2: Run focused runner tests and verify RED**

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling.PatchedDatabaseRunnerSelectionTests -v
```

Expected: failures are specifically the current stock path/bootstrap selection and missing patched behavior;
the actual-binding-before-reset ordering test continues to pass. Do not accept a fixture/setup-only RED.

- [ ] **Step 3: Change exactly the runner binary and bootstrap paths**

In `scripts/verify_database.ps1`, replace only:

```powershell
$supabaseBinary = Join-Path $repositoryRoot ".tools\supabase\v2.109.1-sejong-loopback\supabase.exe"
$bootstrapScript = Join-Path $scriptDirectory "bootstrap_patched_supabase.ps1"
```

Do not change `Ensure-LocalDatabaseNetwork`, `Assert-LocalDatabaseRuntime`, owned-runtime cleanup,
start/reset/status/test command arguments, compensation order, credential handling, or integration phases.

- [ ] **Step 4: Document exact local commands**

Update `scripts/README.md` to distinguish:

```powershell
# Stock reference only
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1 -VerifyOnly

# Patched build/runtime authority
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -BuildCandidate
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -Install
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -VerifyOnly
```

State that direct stock `db start`, PATH fallback and `db diff` are outside the approved safe path.
Replace the optional stop command with the patched binary path. Rewrite the current stock-failure/Q-SEC-006
paragraph as historical rationale: Task 4 pins/selects the artifact, but actual single-loopback/full DB proof
remains Task 5 and DB-001 must not be called complete yet. Preserve the remote/public blocker and state that
API, schema, data, dependencies and readiness are unchanged.

- [ ] **Step 5: Run runner and bootstrap regressions**

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling -v
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -VerifyOnly
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

Expected: all tooling tests pass, including unsafe binding and owned-runtime cleanup mutation tests;
verify-only passes without network; secret/diff checks pass.

- [ ] **Step 6: Commit Task 4**

```powershell
git diff -- scripts/verify_database.ps1 scripts/tests/test_supabase_tooling.py scripts/README.md
if ($LASTEXITCODE -ne 0) { throw "Task 4 diff review failed" }
git diff --check
if ($LASTEXITCODE -ne 0) { throw "Task 4 diff check failed" }
git diff --exit-code -- contracts apps/api/src apps/web data prompts supabase/migrations database/rollbacks database/schema-v1.draft.sql package.json pnpm-lock.yaml apps/api/uv.lock PACKAGE_MANIFEST.json
if ($LASTEXITCODE -ne 0) { throw "protected worktree path changed" }
git add scripts/verify_database.ps1 scripts/tests/test_supabase_tooling.py scripts/README.md
if ($LASTEXITCODE -ne 0) { throw "Task 4 staging failed" }
$staged = @(git -c core.quotepath=false diff --cached --name-only | Sort-Object)
$expected = @(
    "scripts/README.md",
    "scripts/tests/test_supabase_tooling.py",
    "scripts/verify_database.ps1"
) | Sort-Object
if (@(Compare-Object -ReferenceObject $expected -DifferenceObject $staged).Count -ne 0) {
    throw "unexpected staged scope"
}
$unstaged = @(git -c core.quotepath=false diff --name-only)
$ordinaryUntracked = @(git -c core.quotepath=false ls-files --others --exclude-standard)
if ($unstaged.Count -ne 0 -or $ordinaryUntracked.Count -ne 0) {
    throw "unexpected unstaged or untracked scope"
}
git diff --cached -- scripts/verify_database.ps1 scripts/tests/test_supabase_tooling.py scripts/README.md
if ($LASTEXITCODE -ne 0) { throw "Task 4 cached diff review failed" }
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw "Task 4 cached diff check failed" }
git diff --cached --exit-code -- contracts apps/api/src apps/web data prompts supabase/migrations database/rollbacks database/schema-v1.draft.sql package.json pnpm-lock.yaml apps/api/uv.lock PACKAGE_MANIFEST.json
if ($LASTEXITCODE -ne 0) { throw "protected cached path changed" }
git status --short
git commit -m "fix(db): require loopback-patched Supabase CLI"
```

Expected: staged set is exactly the three Task 4 files, protected worktree/cached paths have no diff, and
there is no other state except approved ignored `.tools/` artifacts.

## Task 5: Prove the actual runtime, close DB-001, and hand off

**Files:**

- Modify all active status/version/report/handoff files listed in the file map.
- Create the Task 5 implementation note and update its INDEX.
- No product/API/schema/data/dependency file changes.

**Interfaces:**

- Consumes: Tasks 1–4 exact tooling and the existing DB-001 six-stage gate.
- Produces: actual single `127.0.0.1:54322`, fresh pgTAP 282, integration 8/8, replay/cleanup evidence, DB-001 Done, and local/private version promotion only.

- [ ] **Step 1: Reconfirm preconditions and verify-only**

```powershell
git status --short
docker desktop status
docker version --format '{{.Server.Version}}'
docker ps -aq
docker ps -aq --filter 'label=com.supabase.cli.project=sejong-ai-local'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -VerifyOnly
```

Expected: Git clean; Docker running/29.2.1; container counts 0/0; patched verify-only passes. Stop without
DB mutation on any difference.

- [ ] **Step 2: Run the full disposable DB gate once**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1
```

Expected phase evidence:

- patched binary verify passes;
- exact network and pre-existing runtime checks pass;
- `db start --network-id sejong-ai-local-loopback` succeeds;
- post-start actual binding is exactly one `127.0.0.1:54322 -> 5432/tcp` and no `::`/`0.0.0.0`;
- reset one, pgTAP one, six compensations newest-first, absence, reset/replay two, pgTAP two pass;
- backend integration 8/8 passes; environment is restored; no child/native diagnostic is printed.

On any start/inspect failure, confirm runner-owned cleanup returns project containers to zero and do not
continue to versions or documentation.

- [ ] **Step 3: Capture actual runtime evidence and stop cleanly**

```powershell
$dbId = docker ps -q --filter 'name=^/supabase_db_sejong-ai-local$'
if (@($dbId).Count -ne 1) { throw "exact DB container missing" }
docker inspect --format '{{json .NetworkSettings.Ports}}' $dbId
docker inspect --format '{{json .HostConfig.PortBindings}}' $dbId
& .\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe stop
if (@(docker ps -aq --filter 'label=com.supabase.cli.project=sejong-ai-local').Count -ne 0) { throw "project containers remain" }
if (@(docker ps -aq).Count -ne 0) { throw "unexpected containers remain" }
```

Expected: both inspect payloads show only IPv4 loopback for DB 5432; stop succeeds; final counts 0/0.
Do not delete volumes.

- [ ] **Step 4: Run all non-DB and static gates**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
apps/api/.venv/Scripts/python.exe -B scripts/validate_codex_package.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling scripts.tests.test_supabase_tooling -v
git diff --exit-code -- contracts apps/api/src apps/web data prompts supabase/migrations database/rollbacks database/schema-v1.draft.sql package.json pnpm-lock.yaml apps/api/uv.lock PACKAGE_MANIFEST.json
git diff --check
```

Expected: root/tooling/package/secret tests pass; protected product/contract/schema/data/dependency paths
have no diff.

- [ ] **Step 5: Update versions and active status only after every gate passes**

Set `versions/manifest.json` to these exact version axes, using the actual current KST time for
`updated_at`:

```json
{
  "repo_guidance": "1.5.0",
  "application": "0.1.0",
  "web": "0.1.0",
  "api": "2.0.1-draft",
  "shared_contracts": "0.2.1",
  "database_schema": "0.3.0-local",
  "official_data": "0.0.0-not-populated",
  "mock_data": "0.0.0-not-populated",
  "prompt_set": "0.0.2-deepseek-v4-flash-selected",
  "test_suite": "0.5.0-db-baseline",
  "documentation": "2.4.0"
}
```

Update DB-001 to Done. Keep DATA-001 Blocked on PM authoring/approval, DATA-SEED-001 blocked on
DATA-001, READY-001 blocked on DATA-SEED-001, and all later real dependencies. Remove only the satisfied
DB-001 dependency where another blocker remains; do not mark downstream work Done.

Record D-031 as implemented locally, not production-ready. Keep A-021/Q-SEC-003 open/default B and keep
remote/public/admin/API/backend-credential/`00700` deployment blocked. Update README, CHANGELOG, index,
security/ops/version docs, test report and handoff with the actual binary/source/patch hashes, commands,
test totals, binding, final container zero and rollback.

- [ ] **Step 6: Create the implementation note**

```powershell
python scripts/new_implementation_note.py --title "patched Supabase CLI와 DB-001 local baseline 완료" --task-id "DB-001-T10-QSEC006" --type "security/implementation/verification"
```

Fill all 6W1H, request/acceptance, files/functions/contracts/DB/data, exact commands/results, versions,
security/privacy/accessibility/performance, official/mock distinction, migration/rollback/recovery,
remaining A-021 risk, human-required knowledge and AI-internal details. Update INDEX to Done only after
fresh verification.

- [ ] **Step 7: Perform separate specification and quality reviews**

Specification review checks every approved design section against Tasks 1–5, including source/runtime
manifest separation, direct Go CLI, two independent hashes, test-first patch, actual runner order, stock
preservation, `db diff` exclusion, no public/schema/data/dependency change, and rollback.

Quality review checks PowerShell 5.1 compatibility, argument leakage, process disposal/timeouts, path
containment, manifest property closure, environment restoration, Git/Go network allowlists, RED event
specificity, atomic install, fixture fidelity, actual binding/cleanup and documentation truthfulness.

Fix every Critical/Important issue with focused tests and a separate commit. Record reviewer counts and
agent-capacity limitations in the implementation note.

- [ ] **Step 8: Run verification-before-completion and commit closeout**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -VerifyOnly
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
apps/api/.venv/Scripts/python.exe -B scripts/validate_codex_package.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling scripts.tests.test_supabase_tooling -v
python -m json.tool versions/manifest.json
git diff --check
git status --short
docker ps -aq
docker ps -aq --filter 'label=com.supabase.cli.project=sejong-ai-local'
```

Expected: all gates pass, both container lists are empty, protected paths remain unchanged, note/INDEX are
complete, and only authorized closeout documentation/version/task files are dirty.

```powershell
git add TASKS.md README.md CHANGELOG.md CODEX_FILE_INDEX.md versions/manifest.json docs
git commit -m "docs(db): complete safe local baseline"
```

## Rollback and recovery

- Before runtime manifest creation: remove only owned ignored candidate/source/toolchain directories after
  safe child-path validation; no tracked or DB rollback is needed.
- After runtime manifest but before runner switch: revert the runtime-pin commit and remove the ignored
  patched output. Stock CLI remains untouched, but it is not authorized for DB start.
- After runner switch but before successful full gate: revert the runner-switch commit and return DB-001 to
  Blocked. Do not replace it with stock CLI or weaken actual inspection.
- If the runner created an unsafe runtime, use its owned cleanup; confirm container zero. Do not delete
  volumes or invoke prune.
- After a successful disposable DB gate, local schema recovery remains `db reset --local` through the
  patched runner. The existing six compensations are only for the documented disposable-local replay.
- Shared/remote DB, real data deletion, official seed rollback, public deployment and backup restore are not
  authorized by this plan.

## Final acceptance checklist

- [ ] Exact source/tag object/commit/Go archive/patch/build inputs are tracked and validated.
- [ ] Patch changes only the approved test and local DB start files; focused test proves RED then GREEN.
- [ ] Two independent builds have identical SHA-256; runtime manifest and installed file match it.
- [ ] Stock CLI is preserved; DB runner has no PATH/stock fallback.
- [ ] Actual runtime is one `127.0.0.1:54322` binding with no IPv6/IPv4 wildcard.
- [ ] Fresh pgTAP 282, integration 8/8, six-stage compensation/absence/replay pass.
- [ ] Final project/all container counts are zero and no volume is deleted.
- [ ] Product/API/schema/data/dependency/privacy/readiness behavior is unchanged.
- [ ] DB-001/version promotion occurs only after evidence and reviews; public-release blocker remains.
- [ ] Implementation note, INDEX, reports, handoff and active source-of-truth are synchronized.
