# IMP-20260719-008 — DATA-SEED-001 불변 공식 release와 local seed 검증

- Date/Time (KST): 2026-07-19T09:52:17+09:00
- Task ID: DATA-SEED-001
- Type: implementation-data-security
- Status: Blocked
- Author/Agent: primary architect/controller + task별 구현·검토 subagent + Task 6 actual runner/diagnostician
- Branch: main → `codex/data-seed-001-initial-release` isolated worktree
- Base commit: c312488
- Related plan/ADR/RFP: DATA-SEED-001 plan, approved DATA-SEED design, ADR-0015/0016, D-033/D-035/D-036/D-038/D-039, DAR-001/DAR-002/SER-001/SER-003/COR-001

## 1. 사용자 요청과 완료 기준

### 요청

- 사용자가 `ㅇㅋ 전체 승인 구현 ㄱㄱ`로 DATA-SEED-001의 written specification과 실행계획 전체 구현을 승인했다.
- 승인 범위에는 local disposable DB reset, seed, compensation, replay가 포함된다.
- 가능한 구현은 멈추지 않고 subagent를 사용해 진행하되 사람 작업과 public/remote 범위는 분리한다.

### Acceptance Criteria

- PM-approved staging에서 정확히 19 KB·3기관·10매핑의 immutable `0.1.0-initial.1` release를 생성한다.
- release/dispatcher hash, empty-local transactional seed, second-seed rejection, rollback, compensation, replay, concurrency를 검증한다.
- migration/API/readiness/UI/LLM/public/remote/new dependency를 변경하지 않는다.
- task별 TDD·독립 review, 전체 Sol review, root gate, lineage/version/docs 동기화를 모두 통과한다.

### Task 6 actual status

- 2026-07-20 actual disposable DB gate는 seed write 전 identity에서 차단됐다.
- 불변 `0.1.0-initial.1` SQL의 single-row membership guard와 기존 migration/pgTAP의
  grantor별 effective option union 계약이 충돌한다.
- 따라서 19/3/10 seed, rollback, concurrency, compensation, replay, final citizen 19는
  실제 PASS 근거가 아니며 `official_data`를 올리지 않았다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자/PM이 승인, primary agent가 조정, task별 구현자와 별도 reviewer가 구현·검토 |
| When — 언제 | 2026-07-19 KST 시작; spec 승인 09:20:31, 실행 승인 09:52:08 |
| Where — 어디서 | local Git worktree, `data/`, `scripts/`, `supabase/seed.sql`, disposable PostgreSQL 17 |
| What — 무엇을 | 승인된 19/3/10을 불변 official release와 재현 가능한 local seed로 승격 |
| Why — 왜 | 승인 근거만 시민 검색 후보로 만들고 실패·재실행·보상에서도 데이터 무결성과 추적성을 지키기 위해 |
| How — 어떻게 | strict input trust, deterministic bytes/hash, two-phase publication, guarded SQL, actual DB cycle, 독립 review |
| How much — 어느 정도 | release 7파일, dispatcher 1파일, 실제 runner 3회 시도, reviewed code fix 2개, DB schema/API/role/grant 변화 0, 외부 API·비용 0원 |

## 3. 시작 전 상태

- 관련 파일: approved plan/spec, DATA-001 staging/approval manifest, migrations 6개, patched DB runner, version manifest.
- 기존 동작: staging은 APPROVED 19/3/10이지만 official release는 없고 `supabase/seed.sql`은 data-free, `official_data=0.0.0-not-populated`, `/ready=503`.
- 발견한 충돌/부채: `database/README.md`의 Q-SEC-006 설명 일부가 D-031 이후 상태보다 오래됨; Task 7에서 actual 근거로 정정한다.
- Git 상태: `main` clean, base `c312488`; 원격 없음.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-028 | A | DATA-SEED 실행 승인 | D-039로 해결; local disposable DB cycle 포함 | release/seed/DB local mutation |
| A-021 | A/Public | public privileged function hardening | 본 범위 밖, 계속 차단 | public/remote 배포 금지 |

## 5. 설계 결정과 대안

### 선택

- 승인된 DATA-SEED plan을 그대로 실행하고 `released_at=2026-07-19T09:20:31+09:00`을 고정한다.
- `superpowers:subagent-driven-development`로 task별 fresh implementer와 reviewer를 분리한다.

### 이유

- release timestamp는 ambient clock이 아니라 이미 승인된 governance evidence다.
- 좁은 task·TDD·독립 review가 데이터/보안 결함을 조기에 차단하고 durable ledger가 장기 실행 중 중복을 막는다.

### 고려했지만 선택하지 않은 대안

- main에서 직접 구현: 격리·복구성이 낮아 제외.
- runtime timestamp: 동일 input 재현성과 승인 증거를 깨므로 제외.
- non-empty/remote DB 적용이나 새 migration: 승인 범위 밖이라 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `scripts/verify_data_seed.ps1` | PowerShell 5.1 strict mode에서 empty `Compare-Object` 결과를 배열로 고정 | valid patched runtime operational 오판 방지 |
| `scripts/tests/test_verify_data_seed_runner.py` | exact manifest/binary empty property diff 회귀 | actual 실패를 RED로 고정 |
| `scripts/verify_data_seed_db.py` | SQL special form `COALESCE` schema 한정 제거 | PostgreSQL `42883 UndefinedFunction` 해결 |
| `scripts/tests/test_verify_data_seed_db.py` | identity query unqualified `COALESCE` 회귀 | 동일 문법 결함 방지 |
| `docs/test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md` | Blocked actual attempts, 계약 충돌, cleanup 증거 | 미실행 항목을 PASS로 오인하지 않도록 인수인계 |

### 데이터 흐름/상태 변화

- approved staging → immutable 19/3/10 release → byte-identical dispatcher까지는 Task 5에서 완료됐다.
- Task 6에서 DB write 전 role identity guard가 차단했으므로 application row 상태 변화는 0이다.

### 오류·빈 상태·롤백

- Attempt 1은 baseline PASS 뒤 patched-runtime strict-mode bug로 중단됐고, attempt 2는
  reset이 남긴 default-network runtime을 baseline이 fail closed로 거부했다.
- 승인된 pinned CLI stop으로 repo-owned runtime만 absent로 복구한 뒤 attempt 3을
  처음부터 재실행했다. baseline/runtime/status는 PASS, identity에서 중단됐다.
- syntax fix 후 actual catalog의 grantor-specific 2개 row와 immutable SQL의 count=1 조건이
  충돌했다. role/grant/release를 변경하지 않고 Blocked로 마감했다.

## 7. 버전 전후

### 생성 시 매니페스트
- product_spec: 2.2.1
- repo_guidance: 1.5.0
- application: 0.2.0
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 0.8.0-web-browser-gate
- documentation: 2.7.2

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.2.0 | target unchanged | runtime 범위 아님 |
| Web | 0.2.0-static-chat-shell | target unchanged | UI 범위 아님 |
| API | 2.0.1-draft / shared 0.2.1 | target unchanged | 공개 계약 변경 금지 |
| DB schema | 0.3.0-local | target unchanged | migration/role/grant 변경 금지 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | actual full DB cycle이 identity 전에서 차단되어 미승격 |
| Mock data | 0.0.0-not-populated | target unchanged | mock 미사용 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | target unchanged | LLM 미호출 |
| Test suite | 0.8.0-web-browser-gate | target 0.9.0-data-seed-release | focused/root/actual gates |
| Docs | 2.7.2 | 2.7.3 start; target 2.8.0 | 승인 기록과 최종 lineage |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `git status --short --branch`, `git log -5 --oneline` | PASS | main clean, base c312488 | terminal evidence |
| `python scripts/new_implementation_note.py ...` | PASS | 이 note와 INDEX 생성 | 이 파일/INDEX |
| pinned ignored runtime copy + `uv sync --frozen` + frozen pnpm installs | PASS | uv 33, root 465, E2E 3 packages | isolated worktree |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1` | PASS | full baseline; TEST-ROOT, DATA-001, Web/API/contracts, secret/package/diff | isolated worktree at `eb84690` |
| exact `scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.1` attempt 1 | BLOCKED | about 42.1 s; baseline PASS, patched runtime failure | Task 6 report |
| same runner attempt 2 | BLOCKED | about 2.1 s; retained default-network runtime rejected | Task 6 report |
| approved pinned CLI stop + same runner attempt 3 | BLOCKED | about 47.1 s; baseline/runtime/status PASS, identity failure | Task 6 report |
| patched runtime exact TDD regression | PASS | RED 1/1 → GREEN; focused 34/34 | commit `faa34d49` |
| identity SQL exact TDD regression | PASS | RED 1/1 → GREEN; focused 35/35 | commit `afe47ccc` |
| current-compatible runner/tooling/root-runner regression | PASS | 94/94 in 89.088 s | terminal evidence |
| Ruff/format/Mypy, package, secret, diff/hash/protected-scope | PASS | issues 0; protected change 0 | terminal evidence |
| pinned CLI final stop + resource inspection | PASS | container 0, 54322 listener 0, volumes 2/network 1 preserved | Task 6 report |

### 미실행 검증과 이유

- forced rollback, concurrency A/B, 19/3/10 DB seed, second seed, compensation guard/replay,
  final DB semantic hash, citizen 19/exclusions 0/operational 0은 identity 차단 때문에
  도달하지 못했다. 이 항목들은 PASS가 아니다.
- broad 202-test 조합은 Task 5 후에도 release absent/data-free seed를 가정한 시험으로
  42 failures/2 errors를 냈다. Task 7에서 active-release-aware로 갱신해야 하며 숨기지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문/PII/transcript/provider payload를 읽거나 저장하지 않는다.
- Security: exact canonical path/reparse·secret-free output·exact local DSN/role/lock/empty guards를 fail closed로 유지했다. grantor union 충돌을 이유로 role/grant를 변경하지 않았다.
- Accessibility: UI 변경 0; 기존 회귀만 유지한다.
- Performance/cost: local 19/3/10 규모, 외부 API 0, 새 dependency 0, 비용 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: Task 5 immutable 19/3/10 release/dispatcher byte는 변경 0이다. DB seed는 identity 전에서 차단됐다.
- mock/AI 생성: mock 0; AI가 공식 사실을 추가하지 않는다.
- schema/lineage: DB schema unchanged; approval→release→dispatcher→DB semantic hash를 기록할 예정이다.
- verified date: source verified date는 기존 2026-07-18 유지; governance release timestamp는 2026-07-19T09:20:31+09:00.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 사용자는 local release와 disposable DB cycle을 승인했다. public/remote, non-empty DB, successor release, WASTE-03, API/readiness/migration은 승인하지 않았다.
- immutable release는 생성 뒤 in-place 수정·삭제하지 않는다. 실제 DB gate가 실패하면 official version을 올리지 않는다.
- successor release/design에서 migration/pgTAP과 동일한 effective ADMIN/INHERIT/SET union
  guard를 쓸지 인간 승인이 필요하다. global role/grant 정규화는 더 큰 권한 변경이며 현재 미승인이다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- helper/file split, fixture, stable issue code, SQL formatting과 task agent 배정은 승인된 계약 안에서 자율 처리한다.

## 13. 인수인계·재현·롤백

### 재현

`docs/test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md`의 attempts와 blocker를 먼저 읽는다.
인간이 successor design/release를 승인한 뒤에만 absent repo-owned runtime에서 승인 plan의
exact runner를 처음부터 실행한다.

### 롤백

Task 5 후 release bytes는 수정·삭제하지 않고 new successor 절차를 사용한다. 이 actual
시도는 seed 전에 차단됐으므로 application row compensation을 실행하지 않았다.
pinned CLI로 repo-owned runtime만 정지했고 volume/network를 보존했다.

### 다음 개발자 시작점

Blocked report와 authoritative migration/pgTAP union 계약을 확인하고 successor release
의사결정부터 재개한다. `official_data`는 Task 6 actual full cycle 전에는 올리지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- Q-SEC-003/A-021은 public release blocker로 남는다.
- Blocker: authoritative grantor-specific membership union과 immutable `.1` single-row guard 충돌.
- 다음 한 단계: 인간이 successor immutable release/design의 effective-union guard를 승인한다.

## 15. 자체 리뷰

- [ ] 요청 충족 — actual acceptance는 blocker로 미도달
- [x] 테스트/검증 — 도달한 경계와 미실행 항목을 구분해 기록
- [ ] source-of-truth/계약/버전 동기화 — Task 7/successor 의사결정 필요
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
