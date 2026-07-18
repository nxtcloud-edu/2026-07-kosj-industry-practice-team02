# Q-SEC-006 project-local patched Supabase CLI 설계

- Status: Completed for disposable local/private use; implementation, remediation, actual gate, final reviews 0/0/0, final verification and closeout commit complete
- Date: 2026-07-17
- Decision: Q-SEC-006=A / D-031 / ADR-0013; Q-TOOL-001=A / D-032 / ADR-0014
- Scope: DB-001 Task 10의 local/private 개발 환경만

## 1. 문제와 목표

Docker Desktop 4.62.0/Engine 29.2.1에서 stock Supabase CLI v2.109.1의 local DB
publish 요청은 `HostIP`를 생략한다. Docker network의 `host_binding_ipv4`, Desktop의
`default-local-port-binding`, `local-only-port-binding`을 각각 적용해도 actual binding은
IPv4 `127.0.0.1`과 IPv6 wildcard `::`를 함께 만들었다. 반면 동일 Engine에서
`HostIP=127.0.0.1`을 명시한 control은 단일 IPv4 loopback만 만들었다.

목표는 exact local gate를 완화하지 않고, 공식 v2.109.1 Go CLI의 DB start 요청 한 곳에만
IPv4 loopback을 명시하는 project-local 도구를 재현 가능하게 만들고 검증하는 것이다.

## 2. 목표와 비목표

### 목표

- 공식 tag와 peeled commit, Go toolchain, patch, build flags, 최종 binary SHA-256을 고정한다.
- stock CLI를 덮어쓰지 않고 patched CLI를 별도 경로에 둔다.
- 패치가 local DB `5432/tcp` 요청에 정확히 `127.0.0.1`을 넣는지 TDD로 검증한다.
- runner가 pinned patched binary만 사용하고 actual single `127.0.0.1:54322`를 다시 확인한다.
- 어떤 검증이든 실패하면 DB reset, credential 추출, SQL, version 승격 전에 중단한다.

### 비목표

- Supabase CLI를 일반 fork로 유지하거나 상류에 배포하지 않는다.
- `db diff`가 만드는 shadow DB의 별도 port binding은 DB-001 runner 호출 경로가 아니므로
  이번 패치에 포함하지 않는다.
- Docker Desktop 전역 설정을 추가로 바꾸지 않는다.
- 공개 API, DB migration/schema/data, 개인정보 정책, production dependency를 바꾸지 않는다.
- 이 설계만으로 public/production readiness를 주장하지 않는다. A-021/Q-SEC-003은 별도다.

## 3. 고정된 상류 근거

| 항목 | 고정값 |
|---|---|
| Repository | `https://github.com/supabase/cli.git` |
| Annotated tag | `v2.109.1` |
| Tag object | `9d25ff8b5b0fba3c6f0ef000e7dd658c8d710c38` |
| Peeled commit | `6d4c19870ed213ba7f682f117d0345c8a40bfa94` |
| Go module | `apps/cli-go` |
| Go version | `1.25.11` |
| Windows toolchain URL | `https://dl.google.com/go/go1.25.11.windows-amd64.zip` |
| Toolchain SHA-256 | `b7401f1b41517428e537493316256fb7cf03c66a130a0103ab07f3a2152e2112` |
| Upstream production location | `apps/cli-go/internal/db/start/start.go`, `NewHostConfig()` |
| Upstream test location | `apps/cli-go/internal/db/start/start_test.go` |

tag object와 peeled commit은 `git ls-remote` 및 tag checkout으로 확인했고, Go version과
Windows archive checksum은 해당 commit의 `go.mod`, `mise.toml`, `mise.lock`에서 확인했다.

## 4. 선택한 설계

### 4.1 별도 artifact와 manifest

구현 시 다음 project-tracked 파일을 추가한다.

- `scripts/supabase-cli.local-patch.source.json`: 상류 identity, Go archive, patch SHA-256,
  build flags를 담는 build-input 권위 manifest
- `scripts/supabase-cli.local-patch.runtime.json`: 두 clean build가 일치한 뒤에만 추가하는
  기대 binary SHA-256, exact version, output 상대 경로의 runtime 권위 manifest
- `scripts/patches/supabase-cli-v2.109.1-db-loopback.patch`: upstream test와 production
  한 줄만 바꾸는 reviewable patch
- `scripts/bootstrap_patched_supabase.ps1`: clone/verify/patch/test/build/verify를 수행하는
  fail-closed bootstrap

생성물은 ignored `.tools/` 아래에 분리한다.

- source checkouts: `.tools/s/a`, `.tools/s/b`
- Go toolchain: `.tools/go/1.25.11/windows-amd64/`
- binary: `.tools/supabase/v2.109.1-sejong-loopback/supabase.exe`

stock `.tools/supabase/v2.109.1/`은 비교·롤백 기준으로 그대로 보존한다.

이전 실패에서 남은 ignored
`.tools/supabase-source/6d4c19870ed213ba7f682f117d0345c8a40bfa94/` tree는 runtime
authority가 아니며 새 bootstrap이 checkout/build input으로 사용하거나 자동 삭제하지 않는다. 별도 human-approved cleanup
전까지 격리된 재생성 artifact로만 기록한다.

### 4.2 최소 patch

TDD 순서는 다음과 같다.

1. `start_test.go`에 `NewHostConfig()`가 `5432/tcp`의 유일한 binding을 만들고,
   `HostIP == "127.0.0.1"`, `HostPort == configured port`임을 확인하는 test를 먼저 추가한다.
2. 공식 소스에서 그 test가 RED임을 확인한다.
3. `start.go`의 기존 binding에 `HostIP: "127.0.0.1"` 한 필드만 추가한다.
4. focused test와 `./internal/db/start` package 전체를 GREEN으로 확인한다.

restart policy, volume bind, tmpfs, network ID, container image와 다른 명령은 바꾸지 않는다.
patch 적용 후 `git diff --name-only`는 위 두 파일만 허용하고 `git diff --check`를 통과해야 한다.

### 4.3 공급망과 빌드

bootstrap은 임의 branch나 PATH를 신뢰하지 않는다.

1. source manifest는 tool-root-relative checkout `s/a`, `s/b`, pinned upstream tree의 최대
   relative file path 134자와 허용 absolute file path 상한 248자를 고정한다. bootstrap은
   `.tools/s/a`, `.tools/s/b`의 projected maximum absolute file path를 cleanup·directory 생성·Go
   archive download/extraction·network fetch 전에 계산하고 상한을 넘으면 fail closed한다. 현재 exact
   worktree 투영값은 244자다.
2. exact HTTPS repository만 허용하고 서로 독립된 두 fresh checkout에서 Git tag object와 peeled
   commit을 각각 검증한다.
3. detached exact commit에서만 patch SHA-256과 `git apply --check`를 검증해 적용한다.
4. official Go ZIP을 exact URL에서 받아 SHA-256을 먼저 확인한 뒤 `.tools/`에
   추출한다. 시스템 Go나 자동 설치 package manager는 사용하지 않는다.
5. exact checkout의 `go.sum`과 Go checksum database 검증을 유지한다. bootstrap은 inherited
   module proxy/private 설정 대신 `GOPROXY=https://proxy.golang.org`,
   `GOSUMDB=sum.golang.org`, 빈 `GOPRIVATE`/`GONOPROXY`/`GONOSUMDB`/`GOINSECURE`를 사용하고
   `go mod verify`를 통과시킨다. dependency version을 수정하거나 vendor tree를 생성하지 않는다.
6. 상류 build와 동일한 핵심 조건 `GOOS=windows`, `GOARCH=amd64`, `GOAMD64=v1`,
   `CGO_ENABLED=0`, `GOENV=off`, `GOWORK=off`, `GOTOOLCHAIN=local`, 빈 `GOFLAGS`와
   `GOEXPERIMENT`, `-trimpath`,
   `-ldflags="-s -w -X github.com/supabase/cli/internal/utils.Version=2.109.1"`을 사용한다.
   local reproducibility를 위해 `-buildvcs=false`를 추가하며 telemetry secret ldflag는 모두
   비우고, 모든 pinned Go 환경변수를 `finally`에서 원상 복구한다.
7. 두 independent exact checkout에 같은 verified patch를 적용해 두 번 build하고 SHA-256
   일치를 요구한다. 최초 승인된
   build의 hash를 runtime manifest에 기록한 뒤 bootstrap verify-only와 runner가 그 hash를
   강제한다.
8. binary `--version`은 정확히 `2.109.1`이어야 한다.

`apps/cli-go`는 공식 CI에서도 `go build main.go` 뒤 직접 `init`/`start`에 사용되는 실행 가능한
CLI다. DB-001 runner는 Go DB 명령만 필요하므로 stock release의 Bun shell wrapper를 새로
빌드하지 않는다. 이 제한으로 Bun/Node build dependency를 추가하지 않는다.

build hash가 아직 확정되지 않은 초기 bootstrap은 source manifest만 사용해 candidate hash를
출력하고 binary를 운영 runner에 넘기지 않는다. 두 clean build의 동일 hash와 diff review 후
tracked runtime manifest를 별도 commit으로 추가한다. `TBD`, 빈 hash, 자동 tracked manifest
수정은 허용하지 않는다.

### 4.4 runner 경계

`scripts/verify_database.ps1`은 구현 후 stock manifest가 아니라 local-patch runtime manifest의 exact
binary path와 SHA-256을 먼저 검증한다. PATH fallback은 두지 않는다. patched binary로
`supabase db start --network-id sejong-ai-local-loopback`을 실행한 직후 기존 Docker inspect
gate가 actual binding을 확인한다.

- 허용: 정확히 하나의 `127.0.0.1:54322 -> 5432/tcp`
- 거부: `0.0.0.0`, `::`, 빈/null HostIP, 복수 binding, 미게시, 다른 host port/network

runner가 새 runtime을 만들었는데 검증에 실패하면 기존 owned-runtime cleanup을 실행하고
container 0을 재검증한다. 이 gate 뒤에만 reset, credential, pgTAP, integration, replay가 온다.

## 5. 오류 처리와 관찰 가능성

- bootstrap과 runner는 기존처럼 stable `[PASS]`/`[FAIL] step=... reason=... code=...`만
  stdout에 남기고 child stderr, 로컬 경로, URL query, 환경변수, DSN을 노출하지 않는다.
- source/tag/commit/toolchain/patch/binary/version 중 하나라도 다르면 operational/invalid로
  fail closed한다.
- download 중간 파일과 실패한 build output은 소유한 `.tools/` child 경로만 안전하게 지운다.
- source checkout cleanup은 path budget을 먼저 통과한 `.tools/s/{a,b}`에만 수행한다. 이전
  `.tools/supabase-source/...` partial tree는 자동 cleanup 대상이 아니다.
- 질문 원문, 응답, API key, DSN, 실제 개인정보는 이 흐름에 들어오지 않는다.

## 6. 테스트와 인수 기준

승인된 구현은 다음 증거를 만들었다.

- repository tooling test의 source/runtime manifest schema/allowlisted-host/path/hash/verify-only RED→GREEN
- short checkout exact path, 두 root의 pre-toolchain/pre-mutation ordering, synthetic 244/248 accept와
  249 reject, exact 248-character tree cleanup, short-root junction sentinel 보존, direct/reparse
  `.tools/s` archive override 거부, legacy-root deny-only 사용처 RED→GREEN
- upstream focused Go test RED→GREEN, `go test ./internal/db/start -count=1` GREEN
- clean build 2회의 동일 SHA-256과 exact `--version=2.109.1`
- patched binary를 사용하는 runner unit/mutation tests GREEN
- disposable actual start의 single IPv4 loopback, wildcard/multiple/null mutant fail closed
- full DB gate: 282 pgTAP, backend integration 8/8, compensation/replay, synthetic row zero
- root/API/web/contract/secret/package/diff 검증과 container 0 cleanup
- public API/DB migration/data/version에 승인되지 않은 변화가 없음

모든 local 증거가 통과해 `database_schema=0.3.0-local`과 DB-001 local/private Done을 기록했다.
공식 seed가 없으므로 `/ready=503`은 유지하며 public/remote 경계는 열지 않는다.

## 7. 대안과 트레이드오프

### B — Docker network를 IPv4-only로 추가 보정

CLI source 유지 장점은 있지만 네 번째 환경 전역 변경이며 빈 HostIP의 IPv6 wildcard 제거가
입증되지 않았다. 명시 HostIP control만 반복 성공한 현재 증거보다 약해 선택하지 않았다.

### C — DB runtime 보류

새 도구 위험은 없지만 DB-001과 후속 DB 의존 수직 흐름이 계속 차단된다. patch 검증 실패 시
자동으로 돌아갈 안전 기본값이자 rollback 상태로 유지한다.

### shadow DB까지 함께 patch

`internal/db/diff/diff.go`에도 HostIP 생략 binding이 있으나 DB-001 runner는 `db diff`를
호출하지 않는다. 변경 범위와 회귀 표면을 불필요하게 넓히므로 이번 승인에서는 제외한다.

### stock binary 덮어쓰기 또는 PATH 우선순위

출처와 롤백 경계가 모호해지고 다른 개발 명령까지 암묵적으로 바뀌므로 금지한다.

## 8. 롤백과 후속 승인

롤백은 runner를 stock CLI로 되돌려 DB를 실행하는 것이 아니다. patched manifest 선택과
artifact를 제거하고 기존 fail-closed DB 차단 상태로 복원한다. `.tools/`의 source/toolchain/
binary는 재생성 가능하므로 안전 경로 확인 후 삭제할 수 있으며 tracked patch·manifest·script는
commit revert로 철회한다. DB migration/data 삭제는 없다.

기존 failed `.tools/supabase-source/...` tree는 short-root rollback이나 bootstrap cleanup에 포함하지
않는다. 별도 삭제가 필요하면 absolute target과 reparse 경계를 다시 확인하고 인간 승인을 받는다.

사용자가 원 설계와 실행계획을 승인한 뒤 구현을 시작했고, 2026-07-18 Q-TOOL-001=A와
`수정 계획 승인, 구현 시작`으로 workspace amendment 실행을 승인했다. Task 2C, reproducible
source build/runtime pin, patched-only runner와 actual full DB gate가 완료됐다. runner cleanup은
`73f300b`, tests와 independent review 0/0/0, final-code DB gate로 해결됐다. Final cumulative
specification과 quality docs re-review도 각각 0/0/0이고 full final verification과 closeout commit도 완료됐다. 실제 SHA는 Git 이력을 권위로 확인한다.
