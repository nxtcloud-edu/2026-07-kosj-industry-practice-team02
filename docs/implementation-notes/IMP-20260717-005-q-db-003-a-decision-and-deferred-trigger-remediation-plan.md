# IMP-20260717-005 — Q-DB-003 A decision and deferred trigger remediation plan

- Date/Time (KST): 2026-07-17
- Task ID: DB-001-T9A
- Type: decision
- Status: Done — decision implemented and Task 9 verified
- Author/Agent: Codex `/root` coordinator and documentation/preflight agent
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `b862cde`
- Related plan/ADR/RFP: [Task 9A plan](../superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md), [parent DB-001 plan](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md), [ADR-0012](../adr/0012-deferred-active-question-trigger-execution.md), D-028, RFP F-11/F-12/F-13

## 1. 사용자 요청과 완료 기준

### 요청

직전 Q-DB-003에서 A를 추천받은 사용자는 2026-07-17 KST에 `이거 끝나면 계속해서 진행해줘. 5시간 동안 루프 ㄱㄱ`라고 지시했다. 이 노트는 그 문장을 직전 추천안 A의 실행 승인으로 투명하게 해석하되 사용자가 문자 `A`를 직접 입력했다고 쓰지 않고, 구현 전 권위 문서와 실행 가능한 보안 보정 계획을 동기화한다.

### Acceptance Criteria

- `00100`~`00500`을 수정하지 않고 validator 하나만 새 `00600`에서 제한된 SECURITY DEFINER로 전환하는 경계를 기록한다.
- owner, exact `search_path=pg_catalog, pg_temp`, direct EXECUTE revoke, sole-definer, exact trigger binding, 모든 private base/partitioned table 권한 0을 계획한다.
- matching compensation과 `00600 → 00500 → 00400 → 00300 → 00200 → 00100`을 계획한다.
- API, table/data/seed, dependency, remote/public, retention, cost, readiness와 모든 version manifest 축을 유지한다.
- 실제 SQL·Task 9 dirty 파일을 수정·stage·commit하지 않고 docs-only 검증과 commit을 완료한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 결정자, Codex root coordinator, 문서/preflight agent, 후속 구현·명세·보안 reviewer |
| When — 언제 | 2026-07-17 KST, Task 9 real-DB 6/8 blocker 확인과 사용자 계속 지시 직후 |
| Where — 어디서 | `.worktrees/db-001-layered-enforcement`, 권위 문서·ADR·계획·TASKS·구현 노트, disposable local PostgreSQL 17 catalog |
| What — 무엇을 | Q-DB-003=A 결정, validator-only `00600` 보안 posture, compensation, RED→GREEN·rollback/replay·8/8 계획 |
| Why — 왜 | backend에 private grant를 주지 않으면서 commit-time deferred ACTIVE-question invariant를 원자적으로 실행하기 위해 |
| How — 어떻게 | 결정 로그/ADR/ambiguity/spec/plan 동기화, PostgreSQL 17 공식 SECURITY DEFINER 지침 적용, exact catalog/ACL/trigger/body 검증 설계 |
| How much — 어느 정도 | 새 ADR 1개·Task 9A 계획 1개·결정 노트 1개와 기존 권위/상태 문서 동기화; 제품 코드·SQL·데이터·외부 API·비용 0 |

## 3. 시작 전 상태

- 당시 관련 파일: source-of-truth, D-025~D-027, ADR-0011, approved DB spec/plan, immutable migrations `00100`~`00500`, Task 9 blocker note와 당시 작업 트리의 Task 9 파일 3개.
- 기존 동작: reset/pgTAP 274/274/다섯 compensation/absence/replay는 통과하고 실제 integration은 6/8이었다. 두 approval path는 deferred SECURITY INVOKER validator가 private table을 읽지 못해 안전하게 rollback됐다.
- 발견한 충돌/부채: A 승인 기록이 아직 없었고 계획은 blocker 상태였다. PostgreSQL 17 공식 지침은 SECURITY DEFINER search path의 임시 스키마를 마지막에 명시한다. 로컬에서 validator의 unqualified `uuid`/`boolean` 선언과 backend effective TEMP라는 위험 전제를 확인했지만 실제 승인 경로 exploit/DoS를 재현했다고 단정하지 않는다.
- Git 상태: base `b862cde`; 기존 Task 9 dirty 3개는 이 문서 작업의 소유가 아니며 stage/commit 금지다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-DB-003 | Resolved — Human | deferred validator 실행 posture | A / D-028 / ADR-0012; 계속 지시를 직전 추천 A 승인으로 해석, 문자 A 직접 입력 아님 | 새 `00600`/compensation/pgTAP/Task 9 gate |
| search path order | D/Internal security | validator body에 unqualified built-in type 선언, backend TEMP precondition | PostgreSQL 17 공식 지침에 따라 exact `pg_catalog, pg_temp` | 공개 계약/권한 grant 변화 없이 예방 hardening |
| A-021 | B/High — Open/Deferred | 기존 `app_api` SECURITY DEFINER 9개는 모두 `pg_catalog`-only | 이번 `00600` 제외; 함수/ACL/호출 영향 조사 뒤 public 배포 전 별도 인간 승인 | 별도 forward migration 후보 |

## 5. 설계 결정과 대안

### 선택

새 `00600`은 `app_private.validate_active_kb_question()`의 posture만 SECURITY DEFINER로 변경하고 owner `sejong_schema_owner`, exact `search_path=pg_catalog, pg_temp`, PUBLIC/anon/authenticated/backend direct EXECUTE revoke를 재확인한다. 본문 hash와 두 deferred constraint trigger의 exact binding을 보존한다. compensation은 SECURITY INVOKER로 복원하면서 같은 owner/search path/revoke를 재확인한다.

### 이유

이 방식은 승인 transaction의 기존 deferred invariant와 원자성을 보존하면서 권한 상승 표면을 한 함수로 제한한다. `pg_temp`를 마지막에 명시하는 것은 A 선택을 바꾸는 제품 결정이 아니라 공식 PostgreSQL 17 안전 지침에 따른 내부 예방 보정이다.

### 고려했지만 선택하지 않은 대안

- approval 함수 내부 `SET CONSTRAINTS ... IMMEDIATE`: constraint 이름과 transaction mode 결합 때문에 B로 보류.
- backend private schema/table grant: capability-only 최소권한 경계를 약화해 거부.
- repository/admin DSN workaround: application이 DB 정책을 우회하므로 거부.
- 기존 migration 수정: immutable lineage를 깨므로 거부.
- 기존 app_api 9개 동시 hardening: D-028 validator-only 범위를 넘으므로 A-021로 분리.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| source-of-truth/decision/ambiguity | D-028, Q-DB-003 resolved, six-stage lineage, A-021 Open/Deferred | 권위와 인간/AI 경계 명시 |
| `docs/adr/0012-deferred-active-question-trigger-execution.md` | validator-only posture, 보안 불변조건, 대안, rollback, 검증 | 아키텍처 결정 영구 기록 |
| approved spec/parent plan/`TASKS.md` | Blocked→In Progress, Task 9 historical 6/8, Task 9A 링크 | 허위 완료 없이 실행 재개 |
| Task 9A plan | exact RED/GREEN SQL 경계, 8-assertion pgTAP, compensation posture, two-stage integration proof, recovery snapshot, review/closeout | fresh agent 재현 가능성 |
| 구현 노트/INDEX | 결정·부분 증거·위험·인수인계 동기화 | 요청별 6W1H 의무 |

### 데이터 흐름/상태 변화

문서 결정만 바뀐다. 실제 migration, DB catalog, application code, API contract, 공식/mock row와 readiness 상태는 이 task에서 바뀌지 않는다.

### 오류·빈 상태·롤백

Task 9 historical 6/8과 원자 rollback을 보존한다. 후속 plan은 `00600` compensation의 전체 posture, 기존 274/274, fresh six-stage replay, integration 8/8, synthetic 8-table zero를 모두 통과하기 전 Task 9 완료를 금지한다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.1.0 | 0.1.0 | 코드 무변경 |
| Web | 0.1.0 | 0.1.0 | UI 무변경 |
| API | 2.0.1-draft | 2.0.1-draft | 공개 계약 무변경 |
| DB schema | 0.2.0-draft | 0.2.0-draft | `00600` 구현 완료; manifest 승격은 Task 10 소유 |
| Official data | 0.0.0-not-populated | 동일 | seed 0 |
| Mock data | 0.0.0-not-populated | 동일 | seed 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 호출 0 |
| Test suite | 0.4.2-readiness-contract | 동일 | 최종 282·integration 8/8; manifest 승격은 Task 10 소유 |
| Docs | 2.3.14 | 2.3.14 | manifest promotion은 Task 10 소유 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| 권위 문서·migration·dirty scope `rg`/`Get-Content`/`git status` | Q-DB-003 drift, exact function/trigger/Task 9 scope 확인 | docs/SQL/3 dirty paths | 이 노트와 ADR/plan |
| local PostgreSQL 17 safe catalog inspection | owner/invoker/현재 proconfig/body hash, exact trigger definitions, backend TEMP precondition 확인 | target 1, triggers 2 | Task 9A plan expected values |
| local Markdown link validator | PASS | 13 changed docs | repository PowerShell check |
| control-character scan | PASS | 13 changed docs, disallowed control 0 | repository PowerShell check |
| stale decision/placeholder scan | PASS | owned docs match 0 | `rg` evidence |
| secret pattern scanner | PASS | exit 0, secret output 0 | `scripts/check_secret_patterns.ps1` |
| package/version/contract drift | PASS | package validator 12 required files; manifest/contract diff 0 | validator and `git diff --exit-code` |
| whitespace and staged scope | PASS | `git diff --check`; exact docs-only staged set | Git evidence at commit |

### 결정 당시 미실행 검증과 최종 상태

- 이 결정 note를 처음 작성할 때 migration/compensation/pgTAP/integration 8/8은 미구현이었다. 이후 `5266abc`/`04a944f`/`228d8cb`에서 구현·검증을 완료했다.
- 실제 승인 경로의 temp-object exploit/DoS는 재현하지 않았으며 재현했다고 단정하지 않는다.
- remote/public DB, 실제 데이터, DeepSeek API는 승인 범위 밖이라 호출하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문·답변·DSN·key·실제 개인정보를 문서나 DB에 저장하지 않았다.
- Security: direct grant 없이 validator 하나만 제한하고 exact owner/proconfig/ACL/body/trigger/private-table posture를 계획했다. 기존 app_api 9개 위험은 A-021로 분리했다.
- Accessibility: 사용자 UI 무변경.
- Performance/cost: 외부 API·cloud·새 dependency 0; 후속 검증은 disposable local Docker만 사용한다.

## 10. 데이터와 출처 영향

- 공식 데이터: 0 rows, 출처/승인 상태 무변경.
- mock/AI 생성: 영구 row 0, 생성 없음.
- schema/lineage: 현재 실행 권위는 immutable `00100`~`00500`과 새 forward correction `00600`; matching compensation까지 6단계다.
- verified date: 2026-07-17 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-DB-003=A 승인은 직전 추천 뒤 계속 지시를 해석한 것이며 사용자가 문자 A를 직접 입력한 것은 아니다.
- 구현 후에도 public API·데이터·비용·remote/public·readiness는 변하지 않는다.
- 이 결정 당시에는 DB-001/Task 9가 완료되지 않았으므로 Task 9A full gate 전 Task 10/version 승격을 금지했다. 현재 Task 9A full gate는 통과했고 Task 9은 완료됐으며, DB-001은 Task 10 전까지 `Done`이 아니다.
- A-021은 기존 app_api 9개 전수 hardening 후보이며 public 배포 전 별도 조사·인간 승인이 필요하다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- pgTAP actual/expected는 order-stable query와 exact catalog identity를 사용한다.
- compensation probe는 고정 boolean 한 행만 읽고 stable PASS만 출력한다.
- recovery는 기존 dirty 3개의 ignored snapshot과 SHA-256을 사용해 재현 가능하게 복원한다.

## 13. 인수인계·재현·롤백

### 재현

1. D-028, ADR-0012, A-020/A-021과 두 DB plan을 읽는다.
2. 구현 commits `5266abc`, `04a944f`, `228d8cb`과 exact 변경 경로를 확인한다.
3. 완료된 Task 9A plan의 RED→GREEN, compensation, 두 번의 integration 8/8, full gate, review evidence를 확인한다.

### 롤백

이 docs-only closeout은 해당 commit을 revert한다. SQL 구현을 되돌릴 때는 `228d8cb`, `04a944f`, `5266abc`를 역순 revert하고 local DB를 reset/replay한다. 공유된 기존 migration은 수정하지 않고 `00600` matching compensation을 newest-first 순서로 사용한다.

### 다음 개발자 시작점

[Task 9A plan](../superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md)은 완료됐다. 다음 시작점은 parent plan Task 10이며 `00100`~`00600` lineage, A-021 caveat, contract/env/data/dependency 경계를 보존한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Task 9 historical RED 6/8은 `00600`으로 해소됐고 final integration은 8/8이다.
- A-021 audit은 privileged graph 22개, unsafe path 21개를 확인했다. exploit은 미재현이며 Q-SEC-003 전 `00700`은 구현하지 않고 public release를 차단한다.
- official seed가 없어 `/ready=503`은 계속 정상이다.

## 15. 자체 리뷰

- [x] 요청과 승인 해석을 투명하게 기록
- [x] 최종 문서 링크·stale/control-character·secret/package/diff 검증
- [x] source-of-truth/ADR/plan/TASKS/INDEX 동기화
- [x] 개인정보 원문·secret/env 값 노출 없음
- [x] 이 문서 closeout에서 제품 코드·SQL·DB test 미수정, exact 10 docs-only scope 유지

## 16. Implementation closeout — 2026-07-17 KST

### 6W1H delta and actual scope

사용자 승인 경계를 `5266abc`의 `00600` property correction으로 구현했고,
`04a944f`/`228d8cb`에서 Task 9 runner와 integration evidence를 마감했다. 기존
`00100`~`00500`은 불변이다. authorized deviation으로 stale
`002_invariants_test.sql` exact search-path assertion 하나를 동기화해 첫 commit은
계획의 3개가 아니라 4개 path다. 공개 API/table/data/retention/dependency/cost는 0변경이다.

### RED/GREEN and review

- RED: real integration 6/8, corrected `006` pgTAP 2/8 meaningful failures,
  tooling expected RED 2.
- GREEN: focused 8/8, full `Files=6, Tests=282`, compensation posture PASS,
  compensated `Files=5, Tests=274`, retained/removed diagnostic branch 각각 8/8.
- full exact rollback `006→005→004→003→002→001`, absence, reset/replay,
  pgTAP2, integration PASS; tooling 16/16, Ruff/Mypy, root/web/API/contract,
  secret/package/diff, no-URL 8 skips, synthetic 8-table zero PASS.
- initial spec Important 1/Minor 1은 `228d8cb`로 해결됐고 final spec/quality는
  각각 Critical/Important/Minor 0/0/0. root도 전체 gate를 독립 재실행했다.
- exact 10 docs-only closeout은 local link/control/stale/secret/package,
  protected scope 0, `git diff --check`를 재검증해 모두 PASS했다.

### Versions, security/privacy/data, rollback, handoff

모든 manifest version은 before/after 동일하다. secret/DSN/question/answer/native
diagnostic 저장 0, persistent synthetic row 0이다. rollback은 `00600` compensation으로
invoker posture와 prior 274를 복구하고 전체는 newest-first다. Task 9은 완료됐고
DB-001은 Task 10 ready다. A-021 public-release blocker를 Task 10에 인계한다.
