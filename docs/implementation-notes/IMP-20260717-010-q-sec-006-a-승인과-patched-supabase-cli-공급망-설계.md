# IMP-20260717-010 — Q-SEC-006 A 승인과 patched Supabase CLI 공급망 설계

- Date/Time (KST): 2026-07-17T11:31:09+09:00
- Task ID: DB-001-T10-QSEC006-DESIGN
- Type: decision/security/design
- Status: Decision-only Done — spec review requested
- Author/Agent: 사용자(결정), Codex(조사·설계·기록)
- Branch: codex/db-001-layered-enforcement
- Base commit: 8a2abe4
- Related plan/ADR/RFP: Q-SEC-006, D-031, A-024, ADR-0013, DB-001 Task 10

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 `Q-SEC-006: A`로 official Supabase CLI v2.109.1의 local DB port HostIP를
project-local 최소 patch로 명시하고 source/toolchain/diff/binary hash를 고정하는 안을 승인했다.

### Acceptance Criteria

- Q-SEC-006을 새 결정과 ADR로 기록한다.
- active source-of-truth와 ambiguity 상태를 동기화한다.
- 구현 전 review 가능한 공급망·TDD·실패·롤백 설계를 작성한다.
- 설치, patch/build, actual DB runtime, 제품 코드 변경은 시작하지 않는다.
- 문서 검증과 구현 노트/INDEX를 완료하고 설계 검토를 요청한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 A를 결정했고 Codex가 공식 소스와 저장소 근거를 조사·기록했다. |
| When — 언제 | 2026-07-17 KST, DB-001 Task 10 port blocker 조사 직후 |
| Where — 어디서 | project worktree의 source-of-truth/ADR/spec/decision/ambiguity/version/note; 읽기 전용 upstream temp checkout |
| What — 무엇을 | exact v2.109.1 local DB start 한 줄 patch의 공급망·TDD·artifact·runner·rollback 설계 |
| Why — 왜 | 세 환경 보정이 actual IPv6 wildcard를 제거하지 못했고 explicit HostIP control만 통과했기 때문 |
| How — 어떻게 | tag/commit·Go archive SHA·patch·두 clean build hash를 고정하고 actual runner gate를 유지 |
| How much — 어느 정도 | 문서/메타데이터만 변경; API/schema/data/dependency/DB/container mutation 0, 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: `scripts/bootstrap_supabase.ps1`, `scripts/supabase-cli.version.json`,
  `scripts/verify_database.ps1`, `scripts/tests/test_supabase_tooling.py`, ADR/결정/ambiguity 문서.
- 기존 동작: stock CLI v2.109.1은 local DB publish의 HostIP를 생략하며 actual binding은
  `127.0.0.1`과 `::`였다. runner는 이를 fail closed하고 unsafe owned runtime을 제거한다.
- 발견한 충돌/부채: Docker Desktop의 승인된 두 보정과 network 보정 모두 exact gate를
  충족하지 못했다. 로컬에 Go가 없고 patched artifact provenance 계약도 없었다.
- Git 상태: 시작 시 branch `codex/db-001-layered-enforcement`, commit `8a2abe4`, clean.
- Docker 상태: Desktop running, setting `local-only-port-binding`, container 0; 이번 요청에서
  설정·container·DB를 바꾸지 않았다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-024/Q-SEC-006 | A/Blocker | source patch 공급망을 승인할지 | A / D-031 / ADR-0013 | 인간 결정 해소, 구현 gate는 남음 |
| A-021/Q-SEC-003 | B/High | public privileged function search path | 미응답 기본 B | local 설계와 독립, public 차단 유지 |
| D/Internal | 범위 | `db diff` shadow binding도 patch할지 | 제외 | DB-001 runner 미호출, 최소 patch 유지 |
| D/Internal | 재현성 | upstream 공식 flags 외 VCS metadata 처리 | `-buildvcs=false` 추가 | clean build hash 안정화 |

## 5. 설계 결정과 대안

### 선택

official annotated tag `v2.109.1` object `9d25ff8...`, peeled commit `6d4c198...`, Go
1.25.11 Windows archive SHA `b7401f...2112`를 고정한다. `internal/db/start`의 test를 먼저
RED로 만들고 `NewHostConfig()`에 `HostIP: "127.0.0.1"`만 추가한다. build-input source
manifest와 검증 완료 runtime manifest를 분리하고 별도 `.tools/` 경로를 사용하며 stock CLI를
보존한다. 공식 CI에서도 직접 실행하는 Go CLI만 build하고 Bun wrapper는 추가하지 않는다.

### 이유

실제 Docker control이 explicit HostIP의 효과를 반복 입증했고, 원인 위치가 official source 한
줄로 확인됐다. exact port gate와 rollback을 보존하면서 변경 표면을 가장 작게 제한한다.

### 고려했지만 선택하지 않은 대안

- Docker network 전체 IPv4-only: 전역 영향과 미입증 효과 때문에 제외.
- DB runtime 보류: 검증 실패 시 안전 fallback으로만 유지.
- shadow DB 동시 patch: 현재 호출 범위 밖이라 제외.
- stock binary overwrite/PATH fallback: provenance와 rollback이 불명확해 제외.
- port gate 완화: IPv6 wildcard를 허용하므로 거부.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `docs/superpowers/specs/2026-07-17-q-sec-006-patched-supabase-cli-design.md` | exact 공급망·TDD·runner·rollback 설계 | 구현 전 review gate |
| `docs/adr/0013-project-local-patched-supabase-cli.md`, ADR index | 장기 보안/도구 결정 | architecture lineage |
| decision/ambiguity/team decisions | D-031과 A-024 resolved 동기화 | active source-of-truth 일치 |
| architecture/security/test/version/ops/task/report/handoff/parent spec-plan | D-031 승인과 구현 전 gate로 현재 상태 갱신 | stale blocker 서술 제거 |
| `versions/manifest.json` | documentation 2.3.14→2.3.15 | 문서 결정 version 추적 |
| 이 note와 INDEX | 6W1H·명령·위험·인수인계 | 요청별 재현 의무 |

### 데이터 흐름/상태 변화

문서 상태만 `A-024 Open`에서 `Resolved decision / implementation gated`로 바뀐다. runtime,
DB row, migration, schema/data version, readiness는 변하지 않는다.

### 오류·빈 상태·롤백

설계가 승인되지 않으면 이 decision/spec commit을 revert하고 기존 fail-closed 상태를 유지한다.
승인 뒤 구현이 실패해도 stock CLI로 우회하지 않고 DB Blocked로 되돌린다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.1.0 | 0.1.0 | 제품 코드 없음 |
| Web | 0.1.0 | 0.1.0 | UI 없음 |
| API | 2.0.1-draft | 2.0.1-draft | 공개 계약 없음 |
| DB schema | 0.2.0-draft | 0.2.0-draft | migration/DB 실행 없음 |
| Official data | 0.0.0-not-populated | 동일 | 공식 데이터 없음 |
| Mock data | 0.0.0-not-populated | 동일 | mock 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 변경 없음 |
| Test suite | 0.4.2-readiness-contract | 동일 | test 구현은 다음 단계 |
| Docs | 2.3.14 | 2.3.15 | D-031/ADR-0013/spec 추가 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `git status --short --branch`, `git log -5 --oneline` | 시작 branch/clean/base 확인 | 1회 | terminal |
| `git ls-remote --tags ... v2.109.1`과 temp tag checkout | tag object `9d25ff8...`, peeled commit `6d4c198...` 확인 | 1 checkout | upstream Git |
| upstream `go.mod`, `mise.toml`, `mise.lock` 검사 | Go 1.25.11, Windows ZIP URL/SHA 확인 | 3 files | temp checkout |
| upstream `start.go`, `start_test.go`, build workflow/script 검사 | HostIP 생략 위치, test 부재, official build flags 확인 | 5+ files | temp checkout |
| current bootstrap/runner/tooling tests 검사 | stock pin과 exact runtime gate 확인 | 4 files | repository |
| Docker status/version, settings-store, container count 조회 | running, Engine 29.2.1, `local-only-port-binding`, project/all `0/0` | 읽기 전용 | Docker Engine/Desktop |
| `python -B scripts/validate_codex_package.py` | PASS, required 12 files와 manifest valid | 1회 | terminal |
| repository scaffold/security unit tests | PASS, 19 tests, skipped 1 | 38.867s | terminal |
| `scripts/check_secret_patterns.ps1` | PASS, tracked secret pattern 0 | 1회 | terminal |
| changed Markdown relative-link/template scan | PASS, broken relative link·template placeholder 0 | changed Markdown | terminal |
| `git diff --check` | PASS | changed 22 paths | terminal |
| `scripts/check_scope_drift.py` | 기존 후보로 exit 1; 이번 changed path와 교집합 0 | pre-existing candidates 15 | terminal |

### 미실행 검증과 이유

Go download, patch RED/GREEN, 두 clean build, binary hash/version, actual DB/full gate는 서면 설계와
후속 실행계획 승인 전이라 의도적으로 실행하지 않았다.

scope drift scanner의 기존 후보는 original `PACKAGE_MANIFEST.json`, synthetic DB test의
`044-000-`, ignored `.tools/isolated-repo`, `.superpowers` recovery 사본이다. 이번 22개 changed
path에는 하나도 포함되지 않아 새 scope drift로 보지 않는다. 원본 snapshot이나 기존 test를
이 문서 요청에서 고치지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문/응답/PII/API key/DSN을 읽거나 저장하지 않았다.
- Security: exact provenance, checksum, allowlisted patch, binary hash, actual loopback, stock 보존을
  설계했다. public security blocker A-021은 그대로다.
- Accessibility: 사용자 화면 변화 없음.
- Performance/cost: local build 시간·디스크만 추가될 예정이며 외부 인프라/API 비용은 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: 0건, 변화 없음.
- mock/AI 생성: 0건, 변화 없음.
- schema/lineage: migration·schema 변화 없음; tooling lineage만 설계.
- verified date: upstream source와 local 환경은 2026-07-17 KST 확인.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- A 선택은 local/private 개발 도구 fork 유지보수를 수용한다는 뜻이다.
- 이번에는 설계만 완료했다. 사용자가 서면 명세를 승인해야 실행계획을 작성한다.
- 실행계획도 승인되기 전에는 Go 설치·patch/build·DB start/reset을 하지 않는다.
- 이 결정은 public release blocker Q-SEC-003을 해결하지 않는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- bootstrap helper 분리, stable step label, fixture naming, 두 build 임시 경로는 공개 계약을
  지키는 범위에서 구현 단계에 결정한다.
- patch allowlist는 `internal/db/start/start.go`와 `start_test.go` 두 파일로 제한한다.

## 13. 인수인계·재현·롤백

### 재현

설계 문서의 상류 identity를 temp exact checkout에서 확인하고 decision/ADR/ambiguity/team
decisions가 D-031을 동일하게 서술하는지 비교한다. `versions/manifest.json`의 docs version과
INDEX row도 확인한다.

### 롤백

이 문서 전용 commit을 revert한다. runtime/DB/artifact가 없으므로 data cleanup은 필요 없다.

### 다음 개발자 시작점

사용자의 `명세 승인`을 받은 뒤 `superpowers:writing-plans`와 `PLANS.md` 형식으로 exact
파일·test·명령·hash finalization 절차를 작성한다. 그 계획 승인 전 구현하지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- 최초 clean build binary SHA-256은 아직 존재하지 않는다. source manifest와 runtime manifest를
  분리하고, 빈/TBD runtime manifest를 commit하지 않으며 두 build hash 일치 후 별도 reviewed
  runtime manifest commit으로 고정해야 한다.
- upstream module download는 network 실패·상류 availability 영향을 받으므로 cache와 stable
  failure가 필요하다.
- `db diff` shadow port는 이번 DB-001 범위 밖이며 향후 그 명령 사용 전 별도 보안 검토가 필요하다.
- 다음 단계는 사용자 설계 검토이며, 그 뒤 실행계획 작성이다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 읽기 전용 근거 확인; 미실행 검증 이유 기록
- [x] source-of-truth/ADR/decision/ambiguity/version 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
