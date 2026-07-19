# IMP-20260719-008 — DATA-SEED-001 불변 공식 release와 local seed 검증

- Date/Time (KST): 2026-07-19T09:52:17+09:00 ~ 2026-07-20T02:43:52+09:00 Task 8 review remediation
- Task ID: DATA-SEED-001
- Type: implementation-data-security
- Status: Blocked — final-review Important remediation implemented; A-030/Q-SEED-002 remains open
- Author/Agent: primary architect/controller + task별 구현·검토 subagent + Task 6 actual runner/diagnostician + final reviewer/remediation agent
- Branch: main → `codex/data-seed-001-initial-release` isolated worktree
- Base commit: c312488
- Task 8 remediation base: f55d5c690a8bea960f495ab4f6d8d60303e8edca
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
- Final review I1의 partial-delete 후 canonical release 복원을 실제 CLI RED로 고정하고,
  cleanup 실패 시 canonical 부재·noncanonical residual·safe retry를 보장한다.
- M2-01은 `_validate_current_staging` 성공 직후 mutation을 주입하는 snapshot regression으로
  닫고, 계획의 validator signature를 raw `str` token 계약과 맞춘다.

### Task 6 actual status

- 2026-07-20 actual disposable DB gate는 seed write 전 identity에서 차단됐다.
- 불변 `0.1.0-initial.1` SQL의 single-row membership guard와 기존 migration/pgTAP의
  grantor별 effective option union 계약이 충돌한다.
- 따라서 19/3/10 seed, rollback, concurrency, compensation, replay, final citizen 19는
  실제 PASS 근거가 아니며 `official_data`를 올리지 않았다.

### Task 5/7/8 actual completion boundary

- Task 5는 immutable filesystem release `.1` 19/3/10을 게시·검증하고 dispatcher를 byte-active로
  바꿨다. `[db.seed].enabled=false`는 그대로다.
- Task 7A는 active-release-compatible offline/root gate를 구현·검증했다. 이는 filesystem
  근거이지 actual DB 근거가 아니다.
- Task 7B는 lineage·source-of-truth·ADR·decision·backlog·version을 actual Blocked 상태로
  동기화하고 A-030/Q-SEED-002를 새 인간 결정 blocker로 열었다.
- Task 8 final review의 Important 1건은 temp-only RED로 재현했다. owned quarantine이
  확인된 뒤 cleanup이 실패하면 canonical을 복원하지 않고 residual을 비정규 경로에
  남겨 즉시 재시도를 허용하도록 수정했다. 게시된 `.1`·dispatcher byte는 변경하지 않았다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자/PM이 승인, primary agent가 조정, task별 구현자와 별도 reviewer가 구현·검토 |
| When — 언제 | 2026-07-19 KST 시작; spec 승인 09:20:31, 실행 승인 09:52:08 |
| Where — 어디서 | local Git worktree, `data/`, `scripts/`, `supabase/seed.sql`, disposable PostgreSQL 17 |
| What — 무엇을 | 승인된 19/3/10을 불변 official release와 재현 가능한 local seed로 승격 |
| Why — 왜 | 승인 근거만 시민 검색 후보로 만들고 실패·재실행·보상에서도 데이터 무결성과 추적성을 지키기 위해 |
| How — 어떻게 | strict input trust, deterministic bytes/hash, two-phase publication, guarded SQL, actual DB cycle, 독립 review |
| How much — 어느 정도 | release 7파일, dispatcher 1파일, filesystem projection 19/3/10, 실제 runner 3회 시도, reviewed code fix 2개, DB application write 0, DB schema/API/role/grant 변화 0, 외부 API·비용 0원 |

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
| A-030 | A/Blocker | grantor option union 권위와 immutable `.1` single-row guard 충돌 | Q-SEED-002 Open. A 추천/default이지만 미응답 시 미구현 | DATA-SEED/READY/AI Blocked; successor release 또는 DB migration은 인간 승인 필요 |

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
| `data/official/releases/0.1.0-initial.1/` | 불변 7-file 19/3/10 release | PM 승인 projection의 create-once filesystem 권위 |
| `supabase/seed.sql` | release seed와 byte-identical dispatcher; auto-seed disabled | 검증가능한 local activation과 DB reset 자동 삽입을 분리 |
| `scripts/verify.ps1`, active-release test fixtures | Task 7A no-Docker DATA-SEED root stages | 게시 후 release/dispatcher drift를 지속 검증 |
| `docs/data-lineage/DATA-SEED-001-0.1.0-initial.1.md` | approval/release/artifact/semantic hash, exclusions, Task 5/6/7 경계, correction policy | filesystem 성공과 DB 실패 혼동 방지 |
| source-of-truth/ADR/decision/backlog/readmes/changelog/versions | Blocked actual status와 A-030/Q-SEED-002 동기화 | stale release-0/data-free/in-progress 표현 제거 |
| `scripts/promote_data_seed.py` | verified owned quarantine 이후 cleanup 실패에서 canonical restore 금지 | partial release 재노출 차단·safe retry |
| `scripts/tests/test_promote_data_seed.py` | post-publish flush + 두 번째 artifact delete 실패 RED/GREEN | canonical 부재·residual quarantine·retry 계약 |
| `scripts/tests/test_data_seed_release.py` | staging validator 성공 직후 source mutation 주입 | M2-01의 실제 race window snapshot 고정 |
| DATA-SEED plan | `validate_approved_input(Path, str)` raw token signature/example | 구현·테스트와 승인 계획 정합 |

### 데이터 흐름/상태 변화

- approved staging → immutable 19/3/10 release → byte-identical dispatcher까지는 Task 5에서 완료됐다.
- Task 6에서 DB write 전 role identity guard가 차단했으므로 application row 상태 변화는 0이다.
- Task 7A는 filesystem 검증만 root gate에 영구 추가했고, Task 7B는 문서·버전만
  actual Blocked 상태로 동기화했다. 새 공식 데이터나 DB row는 만들지 않았다.
- Task 8 remediation은 테스트 임시 저장소에서만 실패 release/quarantine를 만들었다.
  tracked immutable `.1`, dispatcher, staging approval bytes, DB row와 official-data version은 변경 0이다.

### 오류·빈 상태·롤백

- Attempt 1은 baseline PASS 뒤 patched-runtime strict-mode bug로 중단됐고, attempt 2는
  reset이 남긴 default-network runtime을 baseline이 fail closed로 거부했다.
- 승인된 pinned CLI stop으로 repo-owned runtime만 absent로 복구한 뒤 attempt 3을
  처음부터 재실행했다. baseline/runtime/status는 PASS, identity에서 중단됐다.
- syntax fix 후 actual catalog의 grantor-specific 2개 row와 immutable SQL의 count=1 조건이
  충돌했다. role/grant/release를 변경하지 않고 Blocked로 마감했다.
- Task 8 cleanup은 initial no-replace rename으로 owned directory를 randomized quarantine으로
  옮긴다. 소유권 불일치는 artifact 삭제 전에만 원위치로 복원해 경쟁 replacement를
  보존하고, 소유권 확인 후 열거·신뢰·삭제·rmdir 실패는 canonical을 빈 경로로
  유지하며 residual quarantine을 자동 삭제하지 않는다.

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
| Application | 0.2.0 | unchanged | 시민 runtime/API 동작이 아닌 repository release tooling patch |
| Web | 0.2.0-static-chat-shell | unchanged | UI 범위 아님 |
| API | 2.0.1-draft / shared 0.2.1 | unchanged | 공개 계약 변경 금지 |
| DB schema | 0.3.0-local | unchanged | migration/role/grant 변경 금지 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | actual full DB cycle이 identity 전에서 차단되어 미승격 |
| Mock data | 0.0.0-not-populated | unchanged | mock 미사용 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | unchanged | LLM 미호출 |
| Test suite | 0.8.0-web-browser-gate | 0.8.2-data-seed-filesystem-gate | Task 7A gate + Task 8 cleanup/M2-01 regression patch |
| Docs | note 생성 2.7.2; Task 7B 직전 2.7.3 | 2.7.5 | Task 5/6/7 lineage + Task 8 final-review remediation |

Task 8 patch 경계는 `test_suite` 0.8.1→0.8.2, `documentation` 2.7.4→2.7.5이며
다른 version axis는 모두 그대로다.

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
| Task 5 prepare/release/dispatcher + independent review | PASS | 19/3/10, artifact issues 0, review 0/0/0 | `.superpowers/sdd/task-5-report.md`, `task-5-review.md` |
| Task 7A full `scripts/tests`/root/release/dispatcher + review | PASS | 286 PASS, 1 environment skip; root complete; review 0/0/0 | `.superpowers/sdd/task-7a-report.md`, `task-7a-review.md` |
| Task 7B DATA-001/release/dispatcher read-only validation | PASS | staging PASS, release issues 0, dispatcher active=1 | Task 7B terminal/report |
| package + JSON/version invariant | PASS | 12 required files; 3 JSON parse; official unchanged, tests 0.8.1, docs 2.7.4 | package validator/Task 7B report |
| Markdown/evidence link·path·reference check | PASS after helper correction | 17 active files, missing 0; first helper did not handle root-file empty parent and was corrected without repository change | Task 7B terminal/report |
| stale state / D-040 / RFP check | PASS after independent-review correction | 초기 pattern이 놓친 Q-SEC-004/005의 역사적 A-024 표현과 plan decision-table `In Progress`를 정정한 뒤 expanded current-state scan 0; D-040 row 0; RFP diff 0 | `rg`/Git read-only checks |
| immutable hash/protected diff/scope check | PASS after helper correction | 7 release hashes+dispatcher exact; protected diff 0; 17 visible docs/version paths + ignored Task 7B report. Initial scope regex mishandled quoted/nonterminal docs paths and was corrected without repository change | Task 7B terminal/report |
| `git diff --check` + secret scan | PASS | issues 0 | Task 7B terminal/report |
| plan checkbox/status consistency | PASS | Task 0–5 complete; Task 6 one explicit unreached; Task 7 pre-commit boundary; Task 8 parent-owned pending | approved plan |
| I1 focused RED | EXPECTED FAIL | 1 test, 0.579s; `AssertionError: True is not false` at canonical-absence assertion | Task 8 terminal evidence |
| I1 focused GREEN | PASS | 1/1, 0.936s | Task 8 terminal evidence |
| cleanup ownership boundary regressions | PASS | 4/4, 1.119s | Task 8 terminal evidence |
| full publication/activation suite | PASS | 49/49, 34.624s | `scripts.tests.test_promote_data_seed` |
| full release/projection suite | PASS | 31/31, 16.204s | `scripts.tests.test_data_seed_release` |
| DB verifier/runner static suite | PASS | 35/35, 7.455s | `scripts.tests.test_verify_data_seed_db`, `test_verify_data_seed_runner` |
| unified relevant no-DB suite | PASS | 195/195, 68.113s | staging/release/promotion/DB-static/root-static 6 modules |
| direct staging/release/local/package | PASS | staging PASS; release issues=0; local active=1; package 12 required files | production CLIs/package validator |
| Ruff format/lint + root-runner static | PASS | 3 files formatted; issues 0; root-runner 17/17 | project Ruff, `test_verify_runner` |
| secret/diff/immutable/protected/version/count invariants | PASS | secret 0; diff issues 0; protected changes 0; official version unchanged; 19/3/10 | repository scanners/read-only scripts |
| initial staging-suite invocation | INCONCLUSIVE, recovered | stdout/stderr 없이 exit 1 한 번; class별 18+29+16 및 full 63/63, unified 195/195 재실행 PASS | non-reproduced runner anomaly; repository change 0 |

### 미실행 검증과 이유

- forced rollback, concurrency A/B, 19/3/10 DB seed, second seed, compensation guard/replay,
  final DB semantic hash, citizen 19/exclusions 0/operational 0은 identity 차단 때문에
  도달하지 못했다. 이 항목들은 PASS가 아니다.
- broad 202-test 조합의 역사적 42 failures/2 errors는 Task 7A에서 active-release-aware fixture로
  보정됐다. 이후 full `scripts/tests` discovery는 286 PASS, 1 environment-dependent skip이고 root
  gate도 PASS했다. 단 이 결과는 Task 6 actual DB blocker를 해소하지 않는다.
- Task 7B는 문서/manifest-only이므로 Docker/DB/full root를 재실행하지 않았다. Task 7A의
  current-code root PASS와 Task 6 actual Blocked report를 근거로 사용하고 release/dispatcher만 새로
  read-only 검증했다.
- Task 8의 commit-SHA 기준 독립 final review는 controller가 이 remediation commit 직후 수행한다.
  이 note 시점에는 그 결과를 선반영하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문/PII/transcript/provider payload를 읽거나 저장하지 않는다.
- Security: exact canonical path/reparse·secret-free output·exact local DSN/role/lock/empty guards를 fail closed로 유지했다. grantor union 충돌을 이유로 role/grant를 변경하지 않았다.
- Security: verified quarantine 이후 부분 삭제된 release를 canonical로 재노출하지 않는다.
  unrelated replacement 보존을 위한 pre-mutation ownership-mismatch restore와 file/dispatcher rollback은 유지했다.
- Accessibility: UI 변경 0; 기존 회귀만 유지한다.
- Performance/cost: local 19/3/10 규모, 외부 API 0, 새 dependency 0, 비용 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: Task 5 immutable 19/3/10 release/dispatcher byte는 변경 0이다. DB seed는 identity 전에서 차단됐다.
- mock/AI 생성: mock 0; AI가 공식 사실을 추가하지 않는다.
- schema/lineage: DB schema unchanged. approval→release artifact→dispatcher의 actual hash는
  `docs/data-lineage/DATA-SEED-001-0.1.0-initial.1.md`에 기록했다. DB semantic hash는
  seed 전 blocker로 생성되지 않았으며 filesystem semantic hash와 구분한다.
- verified date: source verified date는 기존 2026-07-18 유지; governance release timestamp는 2026-07-19T09:20:31+09:00.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 사용자는 local release와 disposable DB cycle을 승인했다. public/remote, non-empty DB, successor release, WASTE-03, API/readiness/migration은 승인하지 않았다.
- immutable release는 생성 뒤 in-place 수정·삭제하지 않는다. 실제 DB gate가 실패하면 official version을 올리지 않는다.
- A-030/Q-SEED-002의 인간 결정이 필요하다. A(추천/default)는 migration/pgTAP
  effective-union 권위를 유지하고 같은 PM 승인 19/3/10 data를 separately approved immutable
  `0.1.0-initial.2`로 새로 게시한다. B는 새 DB migration으로 grantor-specific membership를
  한 row로 정규화하는 플랫폼 권한/스키마 변경이다.
- 답이 없으면 A를 추천만 유지하고 A/B 모두 구현하지 않는다. D-040을 확정 선택으로
  작성하지 않으며 DATA-SEED/READY/AI는 Blocked다.
- Final review M1은 지우거나 거짓 PASS로 바꾸지 않았다. `.1`과 적용 migration/pgTAP은
  모두 immutable이고 compatibility test의 정답은 Q-SEED-002 A/B 선택에 따라 달라진다.
  현재 불호환은 actual runner의 fail-closed evidence와 A-030 blocker로 명시하고,
  사람이 successor 또는 migration 권위를 승인하기 전에는 자동 compatibility PASS guard를 추가하지 않았다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- helper/file split, fixture, stable issue code, SQL formatting, 문서 링크·hash 전사, non-mutating
  validator 실행은 승인된 계약 안에서 자율 처리한다. successor bytes·manifest·migration·DB
  mutation·version promotion은 인간 승인 범위다.

## 13. 인수인계·재현·롤백

### 재현

`docs/test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md`의 attempts와 blocker를 먼저 읽는다.
인간이 successor design/release를 승인한 뒤에만 absent repo-owned runtime에서 승인 plan의
exact runner를 처음부터 실행한다.

### 롤백

Task 5 후 release bytes는 수정·삭제하지 않고 new successor 절차를 사용한다. 이 actual
시도는 seed 전에 차단됐으므로 application row compensation을 실행하지 않았다.
pinned CLI로 repo-owned runtime만 정지했고 volume/network를 보존했다.
Task 8 코드 rollback은 remediation commit을 역패치하되 immutable release는 건드리지 않는다.
실제 실패에서 남은 randomized cleanup quarantine은 자동 삭제·canonical 복원하지 말고
소유권·reparse를 수동 확인한 뒤 별도 운영 절차로 정리한다.

### 다음 개발자 시작점

lineage, Blocked report와 authoritative migration/pgTAP union 계약을 확인하고
A-030/Q-SEED-002 인간 결정부터 재개한다. 선택 A가 확정되기 전에 `.2`를 만들거나,
선택 B가 확정되기 전에 migration을 만들지 않는다. `official_data`는 actual full cycle 전에
올리지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- Q-SEC-003/A-021은 public release blocker로 남는다.
- A-030/Q-SEED-002: authoritative grantor-specific membership union과 immutable `.1` single-row guard 충돌.
- M1 compatibility regression은 Q-SEED-002 인간 결정에 묶여 있다. 사람이 선택한 권위에 맞는
  successor pre-publication guard를 새 승인 계획에서 먼저 RED로 추가해야 한다.
- 다음 한 단계: 인간이 A successor immutable `.2`(추천)와 B grantor normalization migration 중
  하나를 명시적으로 선택한다. 그전까지 아무 방안도 구현하지 않는다.

## 15. 자체 리뷰

- [x] 요청 충족 — Task 8 Important cleanup fix·M2-01·plan signature 반영; actual DB acceptance는 정확히 Blocked로 유지
- [x] 테스트/검증 — 도달한 경계와 미실행 항목을 구분해 기록
- [x] source-of-truth/계약/버전 동기화 — 공개 contract/DB 무변경, docs/test manifest만 actual에 맞게 갱신
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
