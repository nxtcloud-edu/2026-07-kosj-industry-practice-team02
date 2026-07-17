# IMP-20260718-001 — Q-SEC-006 patched Supabase CLI implementation and long-path cleanup blocker

- Date/Time (KST): 2026-07-17 13:13 ~ 2026-07-18 00:28
- Task ID: DB-001-T10-QSEC006-IMPL
- Type: implementation-security-status
- Status: Blocked — A-025/Q-TOOL-001 human decision required
- Author/Agent: Codex root, task implementers, independent specification/quality reviewers
- Branch: `codex/db-001-layered-enforcement`
- Approved-plan base commit: `5c3b91e`
- Current implementation commit: `8b40b71`
- Related: D-031, A-024/A-025, Q-TOOL-001, ADR-0013, approved Q-SEC-006 spec/plan, DB-001 parent plan

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 `계획 승인, 구현 시작`이라고 명시해 승인된 project-local patched Supabase CLI 계획을
TDD·에이전트 구현·독립 review로 실행하고, exact runtime/full DB gate까지 진행하도록 요청했다.

### Acceptance Criteria

- official Supabase CLI v2.109.1 exact tag object/commit과 Go 1.25.11 archive를 검증한다.
- local DB start의 한 port binding에만 `HostIP: "127.0.0.1"`를 넣는 exact 2-file patch를 적용한다.
- 독립 build A/B SHA-256이 같을 때만 runtime manifest와 final binary를 pin한다.
- stock CLI, 공개 API, DB schema/migration/data/dependency/privacy 경계를 바꾸지 않는다.
- actual Docker binding과 full DB/root gate를 통과하기 전 DB-001 완료/version 승격을 금지한다.
- 각 task에 focused/full tests, diff review, 독립 spec/quality review, 구현 노트를 남긴다.

현재 첫 네 구현 단위는 완료했지만 Windows 장경로 cleanup 아키텍처가 인간 결정형 blocker가 되어
runtime manifest·final binary·DB 실행은 완료하지 않았다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 설계·계획을 승인했고 Codex root가 다수 구현/검토 에이전트를 지휘했다. |
| When — 언제 | 2026-07-17~18 KST, Docker Desktop 4.62.0/Engine 29.2.1 환경에서 수행했다. |
| Where — 어디서 | isolated worktree `codex/db-001-layered-enforcement`, tracked `scripts/`와 ignored `.tools/`에서 수행했다. |
| What — 무엇을 | source/patch lock, hardened PS5.1 bootstrap, 다중 Git 선택, local Git longpaths를 구현했다. Task 3 실제 build/cleanup blocker를 조사했다. |
| Why — 왜 | stock CLI가 Docker Desktop에서 IPv6 wildcard를 남기므로 exact project-local IPv4 loopback 요청이 필요했다. |
| How — 어떻게 | TDD RED→GREEN, exact manifest/hash, two-checkout build, stable child output, 독립 spec/quality review, systematic debugging을 사용했다. |
| How much — 어느 정도 | tracked 구현 4개 주요 파일, 구현 commit 5개와 문서 보강 commit 4개, patched suites 최대 18/18, stock 7/7. API/DB/data 변화 0, containers/DB mutation 0. |

## 3. 시작 전 상태

- authoritative design/plan과 ADR-0013은 승인됐지만 patched source/bootstrap/runtime artifact는 없었다.
- stock CLI tooling baseline은 40/40 PASS였으나 actual wildcard publish 때문에 DB-001은 Blocked였다.
- Git은 branch `codex/db-001-layered-enforcement`, plan-approved base `5c3b91e`, 원격 없음이었다.
- database schema는 `0.2.0-draft`, official/mock seed 0, `/ready=503`이었다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-024/Q-SEC-006 | A/Resolved | stock CLI 대신 exact patched CLI를 만들지 | A/D-031 | 이번 구현의 승인 근거 |
| Task2A | D/Resolved | PATH에 `git.exe` 두 개일 때 array가 scalar로 결합됨 | 첫 Application의 단일 absolute existing path | commit `6ff830e`, review clean |
| Task2B | D/Resolved | Windows exact checkout의 `Filename too long` | checkout-local `core.longpaths=true`, global 변경 금지 | commit `8b40b71`, review clean |
| A-025/Q-TOOL-001 | A/Open | 재실행 시 PS5.1 long-path recursive cleanup 방식 | A 추천 short `.tools/s/{a,b}`; 미응답은 중단 | Task 3, runtime/full DB gate 차단 |

## 5. 설계 결정과 대안

### 구현된 선택

- exact upstream/tag/commit, Go archive/hash/environment, patch bytes/scope와 build argv를 tracked lock으로 고정했다.
- stock CLI는 보존하고 patched artifact는 별도 ignored/runtime 경로를 사용한다.
- child는 suspended 생성 후 Job Object에 할당하고 timeout 시 tree 전체를 종료한다.
- multiple Git discovery는 normal PATH precedence의 첫 Application 하나를 fail-closed 검증한다.
- checkout별 local `core.autocrlf=false`, local `core.longpaths=true`만 사용한다.

### 현재 추천

Q-TOOL-001=A: checkout relative path만 `.tools/s/{a,b}`로 줄인다. extended-length 열거로 확인한
현재 exact tree의 longest file path는 299자이고 short root 투영값은 244자라 MAX_PATH 대비 약
16자 여유가 생긴다. future upstream path growth는 길이 gate로 막고 기존 실패 long-path tree는 자동 삭제하지 않는다.

### 고려했지만 선택하지 않은 대안

- Win32 extended-length recursive delete: 기존 layout/cleanup은 가능하지만 파괴적 native helper와
  reparse/readonly/partial-failure 보안 검증이 커진다.
- Docker/WSL build: 장경로 문제를 피하지만 새 image/digest/mount/output 공급망과 복잡도를 만든다.
- PATH 축소, global Git config, sparse checkout, 파일 제외, guard 완화: 승인 계약을 우회하므로 금지했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `scripts/patches/supabase-cli-v2.109.1-db-loopback.patch` | exact upstream test+one-field production patch | source review와 범위 제한 |
| `scripts/supabase-cli.local-patch.source.json` | upstream/Go/patch/build input lock | 공급망 재현성 |
| `scripts/bootstrap_patched_supabase.ps1` | verified build/install/rollback/process/path bootstrap, single Git selection, local longpaths | fail-closed PS5.1 tooling |
| `scripts/tests/test_patched_supabase_tooling.py` | source/bootstrap/process/rollback/Git/checkout behavior tests | TDD와 회귀 방지 |
| plans/version/docs | runtime RED, staged scope, Task2A/2B, A-025 status | 실제 실행과 문서 정합성 |

### commits

- `b117a02` Task 1 source/patch contract
- `b353e1e`, `a0fbc35` Task 2 bootstrap와 official-review corrections
- `6ff830e` Task 2A single Git application
- `8b40b71` Task 2B repository-local long paths
- `c1405c4`, `8ae5f00`, `2fc7435`, `2be40d4` 실행계획 안전 보강

### 데이터 흐름/상태 변화

tracked manifest/patch/bootstrap/test만 변경됐다. generated Go/source/diagnostic artifacts는 ignored
`.tools/` 안에 있다. runtime manifest와 final patched binary는 생성되지 않았고 DB는 시작하지 않았다.

### 오류·빈 상태·롤백

각 Task 3 실패는 stable parent failure 뒤 containers 0/0와 final binary absent를 확인했다. 마지막 bounded
retry는 source A의 `.git`을 제거한 뒤 3,035 files와 관측 최대 299자 file을 남기는 partial cleanup으로 중단됐다. 이 tree는
자동 삭제하지 않는다. tracked rollback은 아래 commit별 revert이며 데이터 복구는 없다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product/Application/Web/API/shared | 기존 manifest 값 | 동일 | 제품/public contract 변화 없음 |
| DB schema | 0.2.0-draft | 0.2.0-draft | runtime/full gate 미완료 |
| Official/Mock data | 0 / 0 | 0 / 0 | seed 작업 아님 |
| Prompt/Test suite | 0.0.2 / 0.4.2 | 동일 | manifest test 축 승격 없음 |
| Documentation | 2.3.17 | 2.3.22 | plan hardening, Task2A/2B, A-025 blocker 기록 |

## 8. 명령과 테스트 증거

아래 명령과 결과가 tracked 재현 권위다. `.superpowers/sdd/*-report.md`는 존재할 때만 쓰는
supplementary local evidence이며 커밋 후 인수인계의 전제가 아니다.

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling.PatchedSourceLockTests -v
```

- Task 1 GREEN: exit 0, 2/2 PASS.

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling -v
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling.SupabaseBootstrapBehaviorTests -v
```

- Task 2 official corrections: patched exit 0, 16/16 PASS in 423.484s; stock exit 0,
  7/7 PASS in 56.538s.
- Task 2A final: patched exit 0, 17/17 PASS in 193.095s; stock exit 0,
  7/7 PASS in 39.533s.
- Task 2B final: patched exit 0, 18/18 PASS in 341.736s; stock exit 0,
  7/7 PASS in 46.500s.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
$tokens = $null
$errors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path scripts/bootstrap_patched_supabase.ps1),
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -ne 0) { throw "PowerShell parse failed" }
```

- 각 Task 2/2A/2B final run에서 secret scanner exit 0, diff check exit 0, parser error 0.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -BuildCandidate
```

- 첫 실행: exit 2, `VERIFY-SUPABASE-SOURCE-A operational code=2`; PATH의 두 Git Application
  `.Source` array가 한 scalar path로 결합되는 원인을 확인했다.
- Task 2A 뒤: exit 1; exact origin/tag/peeled commit 뒤 detached checkout `Filename too long`,
  local `core.longpaths` unset과 HEAD absent를 확인했다.
- Task 2B 뒤: exit 1; source A/B exact patch와 module verify 뒤 first build A 전에 candidate가 없었다.
- 최종 bounded retry: exit 2; `[FAIL] step=VERIFY-SUPABASE-SOURCE-A reason=operational code=2`.
  source A `.git` absent, 3,035 files/max 299-character file path 잔존, source B exact, final absent였다.

장경로 잔존 tree는 일반 `Get-ChildItem -Recurse` 대신 아래 extended-length read-only 열거로
재검증했다. 경로 길이는 `\\?\` prefix를 제거한 실제 absolute path 기준이다.

```powershell
$sourceA = Join-Path (Resolve-Path -LiteralPath '.').Path `
    '.tools\supabase-source\6d4c19870ed213ba7f682f117d0345c8a40bfa94\a'
$extendedSourceA = '\\?\' + $sourceA
$extendedGit = $extendedSourceA.TrimEnd('\') + '\.git'
$count = 0
$maxLength = 0
$maxPath = $null
foreach ($file in [System.IO.Directory]::EnumerateFiles(
    $extendedSourceA,
    '*',
    [System.IO.SearchOption]::AllDirectories
)) {
    $normalPath = if ($file.StartsWith('\\?\')) { $file.Substring(4) } else { $file }
    $count++
    if ($normalPath.Length -gt $maxLength) {
        $maxLength = $normalPath.Length
        $maxPath = $normalPath
    }
}
"SOURCE_A_EXISTS=$([System.IO.Directory]::Exists($extendedSourceA))"
"SOURCE_A_GIT_EXISTS=$([System.IO.Directory]::Exists($extendedGit))"
"SOURCE_A_FILE_COUNT=$count"
"SOURCE_A_MAX_ABSOLUTE_FILE_PATH_LENGTH=$maxLength"
"SOURCE_A_MAX_PATH=$maxPath"
```

- exit 0; `SOURCE_A_EXISTS=True`, `SOURCE_A_GIT_EXISTS=False`,
  `SOURCE_A_FILE_COUNT=3035`, `SOURCE_A_MAX_ABSOLUTE_FILE_PATH_LENGTH=299`.
- longest path는 source A 아래
  `apps\cli-e2e\fixtures\scenarios\db-advisors-security-exits-zero-when-fail-on-error-and-no-error-level-advisors-found\interactions.json`이었다.

첫 build-A 실패의 source/compiler 가설은 아래 exact pinned diagnostic으로 분리했다. 출력 경로는
ignored이고 runtime authority가 아니다.

```powershell
$go = (Resolve-Path .tools/go/1.25.11/windows-amd64/bin/go.exe).Path
$sourceA = (Resolve-Path .tools/supabase-source/6d4c19870ed213ba7f682f117d0345c8a40bfa94/a/apps/cli-go).Path
$diagnostic = Join-Path $PWD ".tools/supabase-build/diagnostic-a.exe"
$env:GOOS = "windows"; $env:GOARCH = "amd64"; $env:GOAMD64 = "v1"
$env:CGO_ENABLED = "0"; $env:GOPROXY = "https://proxy.golang.org"
$env:GOSUMDB = "sum.golang.org"; $env:GOPRIVATE = ""; $env:GONOPROXY = ""
$env:GONOSUMDB = ""; $env:GOINSECURE = ""; $env:GOENV = "off"
$env:GOWORK = "off"; $env:GOTOOLCHAIN = "local"; $env:GOFLAGS = ""
$env:GOEXPERIMENT = ""
Push-Location $sourceA
try {
    & $go build -trimpath -buildvcs=false -ldflags `
        "-s -w -X github.com/supabase/cli/internal/utils.Version=2.109.1" `
        -o $diagnostic main.go
    if ($LASTEXITCODE -ne 0) { throw "diagnostic build failed" }
}
finally { Pop-Location }
```

- exit 0; official proxy download progress 4 lines; ignored executable 103,027,200 bytes.

```powershell
docker ps -aq
docker ps -aq --filter 'label=com.supabase.cli.project=sejong-ai-local'
```

- 모든 Task 3 safe stop에서 두 출력 모두 empty, all/project `0/0`; final runtime absent.

### 미실행 검증과 이유

- runtime manifest/install/VerifyOnly/runtime test: two-build hash가 없어 실행 금지.
- DB start/reset/status/credential/SQL/pgTAP/integration: verified patched runtime이 없어 실행 금지.
- Task 4/5, actual `127.0.0.1:54322`, DB version promotion: A-025 blocker 때문에 미실행.
- public/remote/login/link/push/prune/volume deletion: 승인 범위 밖이라 미실행.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문·PII·DSN·credential을 읽거나 저장하지 않았다.
- Security: patch는 explicit IPv4 loopback 한 필드이며 exact source/hash/path/reparse/child/rollback gate를 유지했다.
  A-025 답 전 파괴적 cleanup을 추가하지 않았다.
- Accessibility: 사용자 UI 변화 없음.
- Performance/cost: 외부 비용 0원. official Go/Git/Go proxy 네트워크와 긴 local build 시간만 사용했다.

## 10. 데이터와 출처 영향

- 공식 데이터/mock/DB row 변화: 0.
- source는 official `https://github.com/supabase/cli.git` v2.109.1 exact tag object/commit이다.
- Go는 official 1.25.11 Windows AMD64 archive SHA-256 lock이다.
- verified date: 2026-07-17~18 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-TOOL-001을 답해야 Task 3을 재개할 수 있다. 추천은 A(short project-local checkout root)다.
- runtime manifest/final patched CLI와 DB actual full gate는 아직 없다. DB-001은 완료가 아니다.
- existing ignored long-path source A는 partial cleanup 상태이며 자동 삭제하지 않았다.
- A-021/Q-SEC-003 public-release blocker도 별도로 남아 있다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- helper naming, AST harness 구성, stable status line parsing, exact staged set 검사 등은 승인 계약 안의 내부 세부다.
- diagnostic executable은 runtime authority가 아니며 어떤 runner도 참조하지 않는다.

## 13. 인수인계·재현·롤백

### 재현

1. 이 note와 A-025/Q-TOOL-001을 읽는다. ignored Task reports가 있으면 보조 근거로만 사용한다.
2. 답을 반영해 patched CLI spec/ADR-0013/plan/tests/bootstrap source paths를 갱신한다.
3. TDD/review 후 clean tracked preflight, Docker 29.2.1, containers 0/0, final absent를 확인한다.
4. approved `-BuildCandidate`를 실행하고 A/B hash가 같을 때만 Task 3 runtime pin을 계속한다.

### 롤백

- Task 2B `git revert 8b40b71`, Task 2A `git revert 6ff830e`, Task 2 official corrections/bootstrap은
  역순 revert한다. runtime/DB/data rollback은 현재 필요 없다.
- ignored partial long-path tree는 사용자 결정 전 recursive delete하지 않는다.

### 다음 개발자 시작점

Q-TOOL-001 답을 먼저 반영한다. 답 없이 Task 3을 재실행하거나 cleanup guard를 완화하지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- A-025/Q-TOOL-001 A/Blocker
- A-021/Q-SEC-003 B/public-release blocker
- runtime hash/install/runner/full DB gate 미완료
- existing partial ignored checkout recovery/hygiene

## 15. 자체 리뷰

- [x] 완료 범위와 미완료 범위를 구분
- [x] 실행한 테스트/검증과 실제 결과 기록
- [x] source-of-truth/계약/버전/blocker 동기화
- [x] 개인정보 원문·비밀 노출 없음
- [x] 구현 노트 INDEX 갱신
