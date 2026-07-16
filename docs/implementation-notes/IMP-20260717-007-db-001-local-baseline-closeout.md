# IMP-20260717-007 — DB-001 local baseline candidate closeout (blocked)

- Date/Time (KST): 2026-07-17T06:32:44+09:00
- Task ID: DB-001-T10
- Type: implementation/security/documentation/handoff
- Status: Blocked — Q-SEC-004/A-022 human decision, safe runtime, fresh DB gate, and independent completion review pending
- Author/Agent: Codex `/root/task10_implementation`, coordinated by `/root`
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `85067d04c3f498303d13426bf275e4196e8d5bdf`
- Related plan/ADR/RFP: DB-001 plan/spec, D-018/D-025~D-028, ADR-0008/0011/0012,
  RFP DAR-001/002/003, SER-001/002/003, COR-001

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 승인된 DB-001 계획 구현을 계속하고, 가능한 작업은 agent로 병렬 처리하며 완료까지
진행하라고 요청했다. Task 10은 이미 검증된 DB 실행 계보를 논리 projection·버전·작업 의존성·
운영 문서·test report·handoff와 동기화하려 했으나 actual Docker port finding으로 closeout 전에
차단됐다. 이 노트는 완료 기록이 아니라 재개 조건을 포함한 blocked candidate 기록이다.

### Acceptance Criteria

- timestamp forward migration 6개를 executable authority로, compensation 6개를 disposable-local
  reverse authority로 문서화한다.
- `schema-v1.draft.sql`은 non-active 0.3.0-local 후보의 7 enum·8 table·3 provenance column·generated
  `is_official`·5 index를 보여주는 비실행 projection으로만 만든다.
- official/mock seed 0, DATA-001 PM 승인 목표 2026-07-20, `/ready=503`을 유지한다.
- Q-SEC-004 해결과 safe runtime/fresh full gate/review가 통과한 뒤에만 exact 4개 manifest 축과
  TASK 의존성을 갱신한다. 그 전에는 HEAD 값을 그대로 유지한다.
- exact 환경/12개 lineage hash/test 결과 report와 setup/test/migrate/seed/rollback/recovery
  handoff를 작성한다.
- A-021/Q-SEC-003 무응답 기본값 B를 적용해 public/remote 경로와 `00700`을 차단한다.
- application product code, public contract, production package dependency, seed/data,
  migration/rollback, env value, `PACKAGE_MANIFEST.json`을 변경하지 않는다.
- Docker Engine 28+와 project-scoped loopback network/runtime binding을 reset/credential 처리 전에
  fail-closed로 검증하고, stock CLI/host가 이를 만족하지 못하면 DB mutation 없이 중단한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 승인자, root coordinator, Task 10 implementation agent, preflight/spec/quality reviewers |
| When — 언제 | 2026-07-17 KST; DB-001 Tasks 0~9 검증 뒤 Task 10 closeout |
| Where — 어디서 | `.worktrees/db-001-layered-enforcement`, `database/`, active docs, versions, report/handoff |
| What — 무엇을 | logical DB candidate projection, blocked status/dependency/version, 운영·검증·인수인계 증거 동기화 |
| Why — 왜 | 논리 draft를 실행 권위로 오인하거나 local credential/rollback을 public 환경에서 오용하지 않게 하기 위해 |
| How — 어떻게 | immutable lineage/hash를 읽고 candidate projection/docs를 작성하고, security review finding은 runner/tooling TDD로 fail-closed화하되 인간 결정 전 Docker/DB 재실행·version promotion·완료 처리는 보류 |
| How much — 어느 정도 | 현재 33 paths; application/public contract/migration/data/production package/version manifest 변경 0, local runner/test 2 paths 보정, 외부 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: approved DB-001 spec/plan, ADR-0008/0011/0012, migrations/compensations 6+6,
  pgTAP 6, main IMP-006, A-021 audit, Task 9 report.
- 기존 동작: executable DB는 pgTAP 282와 integration 8/8을 통과했지만 manifest와 logical
  projection은 `0.2.0-draft`, active docs/TASKS는 Tasks 0~5 또는 Task 10 ready였다.
- 발견한 충돌/부채: projection은 enum 6, unqualified objects, provenance 0, mutable
  `is_official`, stale ACTIVE index, executable lineage에 없는 extension을 담았다. API/scripts/root
  README와 ADR/status/operations도 migration 부재 또는 public caveat 누락 상태였다.
- Git 상태: clean base `85067d0`, branch `codex/db-001-layered-enforcement`, remote 없음.
- 실행 환경: Supabase CLI 2.109.1, Docker Server 29.2.1, PostgreSQL 17.6,
  Python 3.12.13. runner가 captured DSN을 process memory/environment에서 사용하고 provisioner는
  원자 `DATABASE_URL` 교체를 위해 `.env` 전체 bytes를 읽는다. non-target/provider 값은 파싱하지
  않고 byte-identical하게 보존하며 표시·로그·별도 영구 복사하지 않았다.
- independent quality review가 기존 Docker runtime이 host wildcard 두 종류로 publish된 사실을
  발견했다. 기존 `localhost-only` 문구는 실제 실행 경계보다 강한 과장이었다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-021 / Q-SEC-003 | B/High Human, unanswered | privileged graph 22개 중 21개 public hardening 미완료 | default B: A-022 해결 뒤에도 local/private만, `00700` 없음 | remote/public/admin/API/backend credential 차단 |
| A-022 / Q-SEC-004 | A/Blocker Human, unanswered | actual Docker port가 wildcard로 해석됨 | default C: DB runtime·manifest promotion·후속 DB dependency 차단 | DB-001 Task 10, DATA-SEED/READY/LOG/BACKUP |
| DATA-001 | Human/PM | 공식 KB/기관/매핑 승인 미완료 | persistent seed 0, 2026-07-20 목표 | DATA-SEED/READY blocked, 503 |
| public/remote | Human deferred | 계정·리전·CORS·비밀·로그·backup | 이번 task에서 미승인 | 배포 변경 0 |
| projection detail | D/Internal | helper/trigger/RLS/GRANT 복제 여부 | 복제하지 않고 실행 lineage/tests를 권위로 유지 | 문서 중복·drift 축소 |

인간 A/Blocker는 A-022/Q-SEC-004 1개다. Q-SEC-003은 B/High라 답변을 가장하지 않고
문서화된 기본값 B를 적용하며, Q-SEC-004는 무응답 기본값 C로 runtime/후속 작업을 차단한다.

## 5. 설계 결정과 대안

### 선택

실행 migration/compensation을 byte-for-byte 보존하고, logical SQL을 현재 table/enum/index
shape와 최종 check family 의미를 읽을 수 있는 non-active candidate projection으로 동기화했다.
활성 상태 문서는 local DB-001 차단과 별도 public-release block을 함께 기록한다.

리뷰에서 발견된 port 경계는 TDD로 별도 보정했다. runner는 Docker Engine 28+, 고정 project ID,
고정 이름/소유 label/bridge/local scope/loopback driver option network, 정확한 실행 DB container와
project label/network mode, HostConfig 요청과 `NetworkSettings.Ports` 실제 결과를 reset/status/env
처리 전에 검증한다. 실제 결과가 단일 `127.0.0.1:54322`가 아니면 안정된 오류만 내고 중단한다.

### 이유

DB 권한·trigger·function을 projection에 복사하면 두 실행 권위가 생긴다. timestamp migration과
pgTAP/integration을 유일한 실행 근거로 유지하면서 다음 개발자가 현재 데이터 shape와 후속
DATA-SEED 의존성을 이해할 수 있어야 한다.

### 고려했지만 선택하지 않은 대안

- 기존 `00100~00600` 수정: applied migration 불변 원칙 위반.
- logical SQL을 executable consolidated schema로 전환: 권위 중복과 rollback/ACL drift 위험.
- `00700` 자동 구현: Q-SEC-003 인간 결정 없음.
- official/mock seed나 `/ready=200`: DATA-001/READY-001 범위와 PM 승인 위반.
- `PACKAGE_MANIFEST.json` 재생성: 2026-07-14 원본 package snapshot 의미 훼손.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `database/schema-v1.draft.sql`, `database/README.md` | non-active 0.3.0-local candidate projection·7/8/5·provenance·authority/rollback/seed 경계 | executable lineage와 logical view 동기화 |
| architecture/domain/security/test/workflow/structure/operations/handoff guides | DB capability·privacy·test·local run/stop/recovery·public block | 신규 개발자 재현과 오용 방지 |
| root/API/scripts README, SECURITY, CODEX index | current local DB boundary와 명령·경로 | pre-DB stale claim 제거 |
| `scripts/verify_database.ps1`, `scripts/tests/test_supabase_tooling.py` | Engine 28+·network identity/option·container identity/state·requested/resolved binding fail-closed TDD | 실제 wildcard publish critical finding 재발 방지 |
| TEAM_DECISIONS, D-018/D-025 status, ADR-0011, ambiguity/discovery append | local 구현 결과와 default B public block | 권위/status 정합; 새 인간 결정은 만들지 않음 |
| parent plan/spec, TASKS | Task 10 blocked state, dependency retention, A-021/A-022 gates | 실행/백로그 정합 |
| `versions/manifest.json`, CHANGELOG | blocker 발견 뒤 4축 후보 승격 철회와 summary | 현재 manifest 유지 |
| test report/handoff | exact env/hash/test/commands/rollback/recovery/risks | 재현 가능한 milestone handoff |
| IMP-006, IMP-007, INDEX | cumulative lineage와 Task 10 전용 6W1H | per-task note 의무 충족 |

### 데이터 흐름/상태 변화

DB schema/row/public route는 바뀌지 않았다. local container start boundary는 안전 검증으로
강화했고 불일치 시 reset 전 중단한다. persistent official/mock row는 0이며
`supabase/seed.sql`은 data-free다. 후보 closeout에서 시도한 TASK dependency reduction은
Q-SEC-004/A-022 blocker 발견 뒤 철회해 DATA-SEED/READY/LOG/BACKUP의 DB-001 의존성을 유지한다.

### 오류·빈 상태·롤백

- 빈 데이터: `/health=200`, `/ready=503`, official/mock seed 0을 정상으로 기록한다.
- custom verifier 초안 2개가 각각 주석의 GRANT/REVOKE를 statement로 오인한 regex와
  `Join-Path` 공백 오타로 제품 검사 전에 중단됐다. 고친 재실행은 PASS했다.
- Task 10 docs rollback은 final docs commit revert이며 SQL/data compensation이 없다.
- 전체 disposable-local DB rollback은 `006→005→004→003→002→001`과 absence proof,
  복구는 fresh reset/replay다. remote/real-data/volume에는 실행하지 않는다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 범위 변경 없음 |
| Repo guidance | 1.4.0 | 1.4.0 | Q-SEC-004 blocker로 후보 승격 보류 |
| Application | 0.1.0 | 0.1.0 | 제품 코드/public route 변경 없음 |
| Web | 0.1.0 | 0.1.0 | 변경 없음 |
| API | 2.0.1-draft | 2.0.1-draft | wire contract 불변 |
| Shared contracts | 0.2.1 | 0.2.1 | 변경 없음 |
| DB schema | 0.2.0-draft | 0.2.0-draft | exact loopback/fresh full gate 전 승격 금지 |
| Official data | 0.0.0-not-populated | 동일 | PM 승인 seed 없음 |
| Mock data | 0.0.0-not-populated | 동일 | tracked mock 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 미사용 |
| Test suite | 0.4.2-readiness-contract | 0.4.2-readiness-contract | 후보 version 미승격 |
| Documentation | 2.3.14 | 2.3.14 | 후보 version 미승격 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| focused loopback TDD RED — `python -B -m unittest scripts.tests.test_supabase_tooling.LocalDatabaseToolingContractTests.test_database_runner_creates_and_uses_loopback_network_before_reset -v` | expected FAIL: runner가 `docker network create ...host_binding_ipv4=127.0.0.1`을 호출하지 않아 assertion 실패; 기존 호출은 `docker version`, bare `db start`, `db reset --local`뿐 | 1 test, 5.929s, exit 1 | terminal; root/quality reviewer의 실제 `0.0.0.0`/`[::]` 재현을 회귀 테스트로 고정하는 RED |
| Docker Engine minimum RED→GREEN | Docker `27.5.1` fixture가 기존에는 reset까지 진행해 RED(exit expected 2, actual 7); 28+ parser 추가 후 1/1 PASS | GREEN 3.637s | terminal |
| requested/resolved binding divergence RED→GREEN | safe-looking HostConfig + unsafe `NetworkSettings.Ports`가 기존에는 reset까지 진행해 RED(actual 7); resolved exact binding 검증 후 safe/unsafe/non-exact 3/3 PASS | GREEN 41.643s | terminal |
| null binding RED→GREEN | StrictMode generic operational을 expected runtime-invalid로 재현; null 선검증 뒤 1/1 PASS | GREEN 18.162s | terminal |
| partial start failure RED→GREEN | `db start`가 runtime을 만든 뒤 exit 23을 반환하는 fixture에서 기존 runner는 `stop`을 호출하지 않아 RED; start 실패도 runner-owned runtime을 정리하고 원래 `START-LOCAL-DATABASE` failure를 보존하도록 보정 | RED 1 fail/10.426s; GREEN 1/1, 8.008s | terminal; reset 호출 0, stop 뒤 runtime none |
| stopped-container visibility RED→GREEN | 실제 `docker ps`처럼 stopped container를 숨기는 fixture에서 기존 runner가 absent로 오인해 start/reset으로 진행하며 RED(expected 2, actual 7); `docker ps -a` exact project inventory로 변경 | RED 1 fail/8.624s; GREEN 1/1, 6.077s | terminal; stopped owned container는 start 전에 invalid로 거부 |
| actual safe-run attempt | network/version/pre-start PASS, pinned `db start --network-id` PASS, post-start actual runtime binding `invalid`; reset/status/credential handling 0회 | fail-closed; project container final count 0 | terminal; Docker Desktop가 optioned network에서도 wildcard two-class 결과를 반환 |
| historical `scripts/verify_database.ps1 -SkipStart` before port finding | exit 0; reset1/pgTAP1/6 rollback/absence/reset2/pgTAP2/integration PASS | 2 resets, 6 compensations, integration 8/8 | terminal/report; 현재 완료 증거 아님 |
| historical `supabase.exe test db` before port finding | `Result: PASS` | Files=6, Tests=282 | terminal/report; 현재 완료 증거 아님 |
| final non-DB `scripts/verify.ps1` after runner remediation | exit 0; root/Web/API/contract/secret/package/diff PASS | all stable phases; DB start 없음 | root terminal, 2026-07-17 |
| API full pytest without DB URLs | PASS | 156 passed, 8 skipped, 1 warning, 4 subtests | terminal |
| focused integration without DB URLs | PASS | exact 8 skips, `local DB gate only` | terminal |
| tooling contract | PASS | 31/31, 176.911s | terminal; partial-start cleanup·stopped inventory 포함 |
| package validator / JSON / secret / diff | PASS | required files 12; finding/parse/whitespace error 0 | terminal |
| projection/version/hash checks | PASS | enum 7, table 8, index 5, provenance 3, hashes 12 | terminal/report |
| local link/control/protected scope | PASS | changed 33 paths, Markdown 30, local link error 0, disallowed control 0, protected diff 0 | terminal |
| `git diff --exit-code -- PACKAGE_MANIFEST.json` | PASS | byte change 0 | Git |

### 미실행 검증과 이유

- remote/public DB, deployment, TLS/rate limit, production backup/restore: 미승인·범위 밖.
- official seed/readiness 200: DATA-001/DATA-SEED-001/READY-001 미완료.
- Q-SEC-003 option A/`00700`: 인간 답변 없음; default B.
- initial Task 10 spec review는 Important 1/Minor 1, quality review는 Critical 1/Important 4를
  반환했다. 문서 ledger/DSN/overclaim과 runner failure-path finding은 보정했고 fresh non-DB
  root/tooling/static gate는 통과했다. Docker Desktop 실환경이 stock pinned CLI의 loopback 요구를
  아직 만족하지 못하므로 actual DB gate와 그 뒤 independent completion review는 pending이다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문·답변·transcript·token·IP/device 값 접근/기록 0. DSN은 process
  memory/environment에서만 provisioning/compensation/integration에 사용하며 값/원문은
  출력·로그·별도 영구 복사하지 않는다. Provisioning은 `.env` 전체 bytes를 읽지만
  non-target/provider 값은 파싱하지 않고 byte-identical하게 보존한다.
- Security: local default credential, TLS/rate-limit 부재, Docker Engine 28+와 exact resolved
  loopback gate, no volume prune, no public exposure를 runbook에 고정한다. 현재 host에서 safe
  binding 증거가 없으므로 DB mutation을 fail-closed로 차단했고 A-021 default B도 보존한다.
- Accessibility: UI 변경 없음.
- Performance/cost: 외부 API/유료 인프라 호출 0. local pgTAP/integration 결과를 public capacity로
  일반화하지 않는다.

## 10. 데이터와 출처 영향

- 공식 데이터: 0 rows; AI/Data·Backend 작성/PM 전수 승인 목표 2026-07-20 유지.
- mock/AI 생성: persistent 0 rows; test synthetic row는 cleanup 후 8 table groups 0.
- schema/lineage: executable 6 forward+6 compensation byte 불변. report에 12개 SHA-256 기록.
- logical projection: 7 enum, 8 table, data_origin 3 columns, generated `is_official`, 5 indexes,
  final 42 check family 의미를 반영하되 function/RLS/GRANT/trigger body는 복제하지 않음.
- verified date: 2026-07-17 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- `0.3.0-local`은 exact loopback/fresh full gate 뒤에만 사용할 후보이며 현재 manifest는
  `0.2.0-draft`다. Q-SEC-004/A-022가 local 완료 blocker다.
- official seed는 없고 `/ready=503`이 정상이다. 다음은 DATA-001 PM 승인이다.
- Q-SEC-003은 미응답이다. default B로 public/remote, public admin/API, public backend DB
  credential과 `00700`을 차단한다.
- remote DB, data deletion, backup, CORS/domain, credential, public deploy, 새 production
  dependency는 모두 별도 승인 사항이다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- projection은 executable helper/privilege graph를 복제하지 않고 names/shape/check-family
  의미와 authority comment만 유지한다.
- historical discovery/task notes의 당시 상태는 보존하고 active status 파일과 append-only
  current addendum만 갱신했다.
- D-018/D-025는 결정 내용이 아니라 implementation status만 바꿨고 Q-SEC-003의 새 D/ADR은
  만들지 않았다.
- `PACKAGE_MANIFEST.json`은 active inventory가 아니라 original package snapshot이라 보존했다.

## 13. 인수인계·재현·롤백

### 재현

1. [handoff](../handoffs/HANDOFF-20260717-DB-001-LOCAL-BASELINE.md)의 요구 버전과 env 이름을 확인한다.
2. Q-SEC-004에서 인간이 선택한 경계를 적용하고 Docker restart/recreate를 완료한다.
3. 그 뒤에만 `scripts/verify_database.ps1`로 runner-owned loopback start와 full local DB gate를 실행한다.
   runtime binding 검증이 실패하면 reset/status/env 작업으로 우회하지 말고 stack을 중지한다.
4. `scripts/verify.ps1`, package/secret/diff gate를 실행한다.
5. [report](../test-reports/DB-001-LOCAL-BASELINE.md)의 hash/test totals와 비교한다.

### 롤백

Task 10 문서만 철회하면 final docs commit을 revert하고 manifest/TASKS/docs를 함께 복원한다.
DB executable/data는 Task 10에서 바뀌지 않아 SQL compensation이 없다. DB 전체 보상은
handoff의 6개 file list와 absence proof를 disposable local 환경에서만 사용한다.

### 다음 개발자 시작점

먼저 Q-SEC-004/A-022의 인간 결정을 받고 safe runtime/full gate/review를 완료한다. 그 전에는
DB를 실행하거나 DB-001 의존성을 해제하지 않는다. 이후 DATA-001의 PM 승인 진행을 확인하고
승인 전에는 seed를 만들지 않으며 DATA-SEED-001, READY-001 순으로 진행한다. public 작업
전에는 반드시 A-021/Q-SEC-003을 인간에게 다시 제시한다.

## 14. 남은 위험·미해결 질문·다음 단계

- A-021/Q-SEC-003 public-release blocker와 privileged function 21개 hardening.
- 공식 seed/READY/chat/admin/backup/public deploy 미완료.
- off-device backup 없음과 단일 PC 손실 위험.
- parent KB/child question 동시 delete lock path는 삭제 API가 없는 현재 P2 위험.
- non-failing Starlette/httpx TestClient deprecation warning 1건.
- 즉시 다음 단계: Q-SEC-004/A-022의 인간 결정을 받고 safe runtime 증거 뒤 full DB/root/static
  gate와 independent review를 재실행한다. 그 다음 DATA-001 PM 승인 → DATA-SEED-001 순서다.

## 15. 자체 리뷰

- [x] 요청/Task 10 acceptance와 6W1H
- [x] security remediation 뒤 fresh non-DB root/API/tooling/package/JSON/secret/diff 검증
- [ ] Q-SEC-004 해결 뒤 actual loopback/full DB gate
- [x] source-of-truth/status/계약 경계/버전/의존성 동기화
- [x] 개인정보 원문·secret/env value 노출 없음
- [x] official/mock 0과 `/ready=503`
- [x] report/handoff/main IMP/새 IMP/INDEX
- [x] migration/contract/data/application product code/production package manifest 보호 범위 diff 0
- [ ] safe runtime/full DB gate 뒤 independent specification review
- [ ] safe runtime/full DB gate 뒤 independent quality/security review
- [ ] final completion status/version/commit evidence
