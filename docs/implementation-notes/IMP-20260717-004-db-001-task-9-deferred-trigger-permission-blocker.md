# IMP-20260717-004 — DB-001 Task 9 deferred trigger permission blocker

- Date/Time (KST): 2026-07-17T03:43:16+09:00
- Task ID: DB-001-T9
- Type: implementation/status
- Status: Done — historical blocker resolved; Task 9 verified
- Author/Agent: Codex `/root` coordinator, Task 9 implementation agent, documentation synchronization agent
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `7af6764`
- Related plan/ADR/RFP: [DB-001 실행계획](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md), [Task 9A remediation plan](../superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md), [ADR-0011](../adr/0011-layered-database-and-backend-enforcement.md), [ADR-0012](../adr/0012-deferred-active-question-trigger-execution.md), D-025/D-026/D-027/D-028, RFP F-11/F-12/F-13

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 승인된 DB-001 계획을 계속 구현하고 독립 작업은 agent로 병렬 처리하라고 요청했다. Task 9는 local-only 실제 DB 통합 테스트 8개와 reset, 다섯 compensation, absence proof, replay를 하나의 영구 gate로 연결해야 했다. 실행 중 승인 capability가 commit 시점의 deferred trigger 권한 때문에 실패해 migration 보안 경계를 바꾸는 인간 결정 `Q-DB-003`이 필요해졌다. 이 노트는 당시 부분 성공 증거를 보존한다. 이후 사용자의 직전 추천안 뒤 계속 지시를 Q-DB-003=A 승인으로 해석해 D-028/ADR-0012와 Task 9A 계획을 만들었으며, 문자 `A`를 직접 입력했다고 기록하지 않는다.

### Acceptance Criteria

- Task 9의 세 구현 파일 밖에서 발견한 migration 보안 변경 필요성을 숨기지 않는다.
- no-URL 8 skip, real DB 6 pass/2 fail, pgTAP·rollback·absence·replay 통과를 실제 결과로 구분해 기록한다.
- 실패한 두 승인 transaction의 원자 rollback과 8개 데이터 범주의 cleanup 0을 기록한다.
- Q-DB-003의 두 선택지, 추천안, 무응답 기본값, 영향 범위를 비전문가도 판단할 수 있게 설명한다.
- 답변 전에는 새 migration, grant, repository workaround, API·data·dependency·remote 변경을 하지 않는다.
- Task 9와 DB-001을 완료로 표시하지 않고 버전을 유지한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 승인자, Codex root coordinator, Task 9 구현 agent, 문서 동기화 agent |
| When — 언제 | 2026-07-17 KST, Task 9 local DB gate 실행과 blocker 확인 직후 |
| Where — 어디서 | `.worktrees/db-001-layered-enforcement`, local Docker/Supabase PostgreSQL, `apps/api/tests/db`, `scripts`, DB-001 상태 문서 |
| What — 무엇을 | 8개 통합 테스트와 전체 rollback/replay gate를 작성·실행하고, deferred ACTIVE-question trigger 권한 blocker를 확인 |
| Why — 왜 | backend role의 private table 직접 접근을 막으면서 승인 함수가 원자적으로 ACTIVE KB와 필수 질문을 만들 수 있어야 하기 때문 |
| How — 어떻게 | no-URL gate, tooling RED→GREEN, disposable reset→pgTAP→5-file rollback→absence→reset/replay→pgTAP→integration, 안전 catalog/cleanup probe |
| How much — 어느 정도 | 당시 작업 트리의 구현 파일 3개, 통합 테스트 8개 중 6 pass/2 fail, pgTAP 274/274 두 번 통과, cleanup 8범주 모두 0, 외부 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: Task 9 실행계획, Task 8 repository, migration `00100`~`00500`, compensation 5개, pgTAP 5개, DB runner와 tooling contract tests.
- 기존 동작: repository unit 경계는 완료됐지만 실제 backend login으로 8개 capability/read 경로와 전체 보상 순서를 검증하는 영구 gate는 없었다.
- 발견한 충돌/부채: runner의 compensation 목록이 과거 `00400_indexes...` 이름을 가리키고 실제 `00500`/`00400_candidate_workflow`를 빠뜨렸다. 이를 TDD로 고친 뒤 실제 승인은 deferred trigger 실행 권한에서 중단됐다.
- Git 상태: clean base `7af6764`에서 Task 9 소유 파일 3개만 dirty이며, migration·rollback·계약·dependency·seed·env template은 변경하지 않았다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-DB-003 | Resolved — A / D-028 / ADR-0012 | commit 시 실행되는 `app_private.validate_active_kb_question()`의 최소권한 실행 경계 | 새 `00600`에서 trigger function만 SECURITY DEFINER로 만들고 owner·exact `search_path=pg_catalog, pg_temp`·명시 revoke를 검증; compensation은 SECURITY INVOKER 복원 | DB migration/rollback, pgTAP, Task 9 통합 gate, DB schema version |
| Q-DB-003 B | Human alternative | 승인 함수 내부에서 관련 deferred constraint를 즉시 실행 | 비추천: trigger 자체의 definer 표면은 늘리지 않지만 승인 함수와 constraint 이름/transaction mode를 결합 | workflow SQL, transaction semantics, rollback/pgTAP |
| 역사적 무응답 기본값 | Superseded | 당시 다섯 migration을 바꾸지 않음 | 과거에는 DB-001 Blocked 유지였으나 현재 A 승인으로 대체; broad grant와 repository workaround 금지는 유지 | API/data/dependency/remote 변화 없음 |

## 5. 설계 결정과 대안

### 선택

선택 A는 `5266abc`에서 구현됐다. 기존 deferred constraint 의미를 유지하면서 검증 함수 하나만 기존 `sejong_schema_owner` 권한으로 실행한다. 새 versioned `00600`은 함수의 `SECURITY DEFINER`, owner, exact `search_path=pg_catalog, pg_temp`, PUBLIC/anon/authenticated/backend 직접 EXECUTE revoke를 catalog와 pgTAP으로 검증하고, matching compensation은 `SECURITY INVOKER`로 복원한다. 이 노트의 6/8 수치는 역사적 RED이며 아래 closeout addendum가 최종 증거다.

### 이유

backend role에 `app_private` USAGE나 table 권한을 주면 capability-only 경계를 무너뜨린다. repository에서 관리자 DSN으로 승인하거나 오류를 무시하는 것도 같은 보안 모델을 우회한다. 반면 A는 ACTIVE KB가 필수 질문을 가져야 한다는 deferred invariant와 approval transaction의 원자성을 유지하면서 권한 상승 범위를 trigger validator 하나로 제한한다.

### 고려했지만 선택하지 않은 대안

- B — `approve_kb_candidate` 안에서 `SET CONSTRAINTS ... IMMEDIATE`: definer 함수 안에서 검사를 끝낼 수 있지만 constraint 이름과 승인 함수가 결합되고 호출자 transaction의 constraint mode에 영향을 줄 수 있어 비추천.
- backend에 private schema/table 권한 부여: 최소권한과 forced-RLS capability 경계를 약화하므로 제외.
- repository에서 admin connection 사용: application 계층이 DB 정책을 우회하므로 제외.
- 실패를 성공으로 취급하거나 trigger를 제거: ACTIVE-question 불변조건과 원자성을 깨므로 제외.
- 기존 적용 migration `00200`/`00400` 수정: migration 불변 원칙을 위반하므로 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `apps/api/tests/db/test_integration.py` | 정확히 8개 async local-only 통합 테스트, unique synthetic fixture, identifier-scoped cleanup, Windows selector policy, concurrency event/pool 경계 | 실제 backend/admin 권한·동시성·retention·시민 read 검증 |
| `scripts/verify_database.ps1` | reset→pgTAP→다섯 보상→absence→reset/replay→pgTAP→integration 순서와 child 비노출/env 복원 | 일회용 local DB 기준선 전체 재현 |
| `scripts/tests/test_supabase_tooling.py` | 정확한 compensation 순서, child exit, sentinel 비노출, 환경 복원, absence 순서, LLM key token 부재 계약 | runner 회귀 차단 |
| ambiguity/TASKS/spec/plan/ADR/주 note/INDEX/이 note | Q-DB-003=A 결정과 역사적 부분 증거, 완료 금지, Task 9A 인수인계 동기화 | 허위 완료·무승인 보안 변경 방지 |

### 데이터 흐름/상태 변화

동일 요청 replay, 충돌 replay, 사유 확인 동시성, 확인 전 후보 차단, purge 경계, backend private table 차단은 실제 DB에서 통과했다. 승인 경로는 `approve_kb_candidate`가 SECURITY DEFINER로 KB·질문·후보 링크·감사 행을 만든 뒤 transaction commit 시 deferred constraint trigger를 호출한다. trigger function은 SECURITY INVOKER이고 backend role은 private schema USAGE가 없어서 두 승인 관련 테스트가 실패한다.

### 오류·빈 상태·롤백

- backend private table 직접 SELECT의 SQLSTATE `42501`은 공개 경계에서 고정 `DatabaseUnavailableError`로 축약되며 native diagnostic을 출력하지 않는다.
- 실패한 두 동시 승인은 candidate를 `PENDING_APPROVAL`, activated link를 NULL로 유지했고 activated KB·필수 질문·승인 audit 모두 0이었다.
- 테스트 cleanup 뒤 interaction events, failed questions, candidates, KB documents, question examples, offices, mappings, audits의 합성 row는 각각 0이었다.
- full runner는 hang 없이 `TEST-DATABASE-INTEGRATION`에서 exit 1로 정확히 중단했다. 완료로 오인하거나 다음 Task 10을 실행하지 않는다.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.0
- repo_guidance: 1.4.0
- application: 0.1.0
- web: 0.1.0
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.2.0-draft
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 0.4.2-readiness-contract
- documentation: 2.3.14

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 범위 변경 없음 |
| Repo guidance | 1.4.0 | 1.4.0 | DB-001 미완료 |
| Application | 0.1.0 | 0.1.0 | 변경 없음 |
| Web | 0.1.0 | 0.1.0 | 변경 없음 |
| API | 2.0.1-draft | 2.0.1-draft | 공개 계약 변경 없음 |
| DB schema | 0.2.0-draft | 0.2.0-draft | Task 9A 구현·Task 10 전 schema 승격 금지 |
| Official data | 0.0.0-not-populated | 동일 | seed 없음 |
| Mock data | 0.0.0-not-populated | 동일 | tracked seed 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 미사용 |
| Test suite | 0.4.2-readiness-contract | 0.4.2-readiness-contract | 최종 282·integration 8/8이지만 manifest 승격은 Task 10 소유 |
| Docs | 2.3.14 | 2.3.14 | blocker 상태 동기화이며 manifest release 없음 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| env 두 항목을 제거한 `pytest ... tests/db/test_integration.py` | exit 0, exact reason `local DB gate only` | 8 skipped | `.superpowers/sdd/task-9-report.md` |
| stale compensation focused RED | exit 1, 과거 004 이름·005/004 누락 재현 | 1 expected fail | Task 9 report |
| `LocalDatabaseToolingContractTests` | exit 0; rollback 순서·exit 17/19·sentinel 비노출·env 복원·LLM token 부재 | 16 passed, 32.425s | Task 9 report |
| `verify_database.ps1 -SkipStart` full disposable gate | reset 1, pgTAP 1, 5-file rollback, absence, reset/replay 2, pgTAP 2 통과; integration에서 exit 1 | pgTAP 274/274 두 번; integration 6 pass/2 fail | Task 9 report/runner stable phases |
| real DB integration focused run | six non-approval boundaries 통과; 두 approval 경계 실패 | 6 passed, 2 failed, 3.17s | Task 9 report |
| safe catalog probe | deferred trigger `prosecdef=false`, backend private-schema usage=false | boolean 2개 | Task 9 report |
| failed approval rollback probe | candidate PENDING, link NULL, KB/question/approval-audit 0 | 5 invariants | Task 9 report |
| final cleanup probe | events/failures/candidates/KB/questions/offices/mappings/audits 모두 0 | 8 categories | Task 9 report |

### 미실행 검증과 이유

- 당시 Task 9 Step 4의 “integration 8/8” 완료 기준은 미결정 Q-DB-003 경계 때문에 달성하지 못했다. 현재는 구현·review·8/8 재검증이 완료됐다.
- no-Docker root gate, final secret/package/scope gate, 독립 review와 commit은 아래 closeout evidence에서 모두 PASS다.
- Task 10 문서·version baseline 승격과 DB-001 Done 전환은 실행하지 않는다.
- DeepSeek/API 외부 호출은 범위 밖이며 실제 key/env 값은 읽거나 출력하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: synthetic `시연용 샘플`/식별자만 사용했고 원문 시민 질문·실제 개인정보·실제 env 값은 기록하지 않았다. cleanup 8범주가 모두 0이다.
- Security: backend private table 접근은 계속 거부된다. native PostgreSQL diagnostic은 노출하지 않고 `42501`을 고정 오류로 축약한다. 인간 승인 전 private schema grant, admin-DSN repository 우회, 기존 migration 수정은 금지한다.
- Accessibility: UI 변경 없음.
- Performance/cost: local disposable DB만 사용했고 외부 API·유료 인프라 호출 0원. A/B 모두 승인 transaction semantics를 바꾸므로 구현 후 동시성 회귀가 필수다.

## 10. 데이터와 출처 영향

- 공식 데이터: 0 rows; 공식 seed를 만들거나 변경하지 않았다.
- mock/AI 생성: 영구 row 0; 테스트 fixture만 명시적 synthetic sample로 생성 후 삭제했다.
- schema/lineage: 적용 권위는 immutable `00100`~`00500`과 새 `00600`; matching compensation까지 6단계다. DB schema manifest 승격은 Task 10 소유다.
- verified date: 2026-07-17 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- `Q-DB-003`은 A로 해결됐다. deferred trigger validator 하나만 SECURITY DEFINER로 제한하고 owner/exact `search_path=pg_catalog, pg_temp`/revoke를 검증하는 새 migration이다.
- B는 승인 함수 안에서 deferred constraint를 즉시 실행하지만 transaction constraint mode와 함수/constraint 결합이 커 선택하지 않았다.
- broad grant, repository 우회, 기존 migration 수정은 계속 금지한다.
- API 공개 계약, 공식/mock 데이터, dependency, remote/public 배포, 비용은 어느 선택지에서도 변경하지 않는다.
- 역사적 통합 RED는 6/8이었고 최종 통합은 8/8이다. Task 9은 완료됐지만 DB-001은 Task 10 전 Done이 아니다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- Windows pytest hang은 selector event-loop policy로 해결됐으며 blocker와 별개다.
- test-only pool은 open 후 `resize(1, 1)`로 순서를 바로잡았다.
- Task 9의 임시 `BACKEND_APPROVAL_BOUNDARY_BLOCKED` 진단 branch를 유지한 채 8/8을 먼저 증명한 뒤 제거했고, 다시 8/8을 통과했다. generic safe backend-error wrapper와 success assertions는 유지했다.
- citizen-read test는 blocker 전용 우회가 없으므로 그대로 둔다.

## 13. 인수인계·재현·롤백

### 재현

1. 구현 commits `5266abc`, `04a944f`, `228d8cb`과 이 closeout commit을 확인한다.
2. 두 DB URL을 child process에서 제거하고 통합 파일을 실행해 8 skip과 exact reason을 확인한다. 값은 출력하지 않는다.
3. local DB를 기동한 뒤 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart`를 실행한다.
4. reset/282 pgTAP/`006→005→004→003→002→001` rollback/absence/reset-replay/282 pgTAP 뒤 integration 8/8을 확인한다.
5. 안전 catalog/pgTAP probe로 validator owner, `prosecdef=true`, exact `search_path=pg_catalog, pg_temp`, 직접 EXECUTE revoke와 backend private base-table denial을 확인하고 DSN/native diagnostic은 출력하지 않는다.
6. rollback/cleanup probe에서 상태 invariants와 8범주 합성 row 0을 확인한다.

### 롤백

- 이 문서 동기화는 해당 문서 commit 하나를 revert하면 되며 Task 9 구현 파일 3개에는 영향을 주지 않는다.
- 승인 후 A를 구현할 때는 새 `006` compensation이 `validate_active_kb_question()`을 `SECURITY INVOKER`로 복원하고 새 pgTAP catalog assertion을 제거 전 검증해야 한다.
- 당시 Task 9 구현 자체를 버릴 경우 작업 트리의 세 파일만 별도 보존/폐기하도록 기록했다. 현재 해당 구현은 후속 보정과 검증을 거쳐 커밋됐으므로 이 문장은 역사적 롤백 판단만 설명한다.

### 다음 개발자 시작점

D-028/ADR-0012/ambiguity register와 완료된 [Task 9A plan](../superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md)을 확인한다. 다음 시작점은 Task 10이며 A-021 public-release caveat를 보존한다.

## 14. 남은 위험·미해결 질문·다음 단계

- 인간 A/Blocker는 0개다. Q-DB-003=A 구현과 검증은 완료됐다.
- definer validator는 owner/exact `search_path=pg_catalog, pg_temp`/direct EXECUTE revoke/body hash/exact trigger binding/private privilege 0을 catalog와 pgTAP으로 모두 증명해야 한다.
- A-021은 기존 app_api SECURITY DEFINER 9개의 `pg_catalog`-only posture를 public 배포 전 별도 조사·승인할 B/High 위험이며 이번 `00600` 범위가 아니다.
- Task 9 세 파일은 `04a944f`로 commit됐고 `228d8cb`이 cleanup evidence를 보정했다.
- DB schema/test/docs manifest 승격과 Task 10 문서는 이 closeout이 아니라 Task 10에서 변경한다.

## 15. 자체 리뷰

- [x] 부분 성공과 blocker를 구분해 기록
- [x] 실제 테스트 수·실패 경계·rollback/cleanup 증거 기록
- [x] Q-DB-003 선택지·추천·기본값·영향 기록
- [x] source-of-truth/계약/버전 무변경 확인
- [x] 개인정보 원문·secret/env 값 노출 없음
- [x] 구현 노트 INDEX 갱신
- [x] 역사적 blocker note 작성 시 Task 9 구현 파일 3개 미수정·미stage·미commit

## 16. Resolution and closeout — 2026-07-17 KST

### 6W1H delta

- Who/When: root coordinator, implementation agent, specification/quality
  reviewers가 2026-07-17 KST에 blocker를 구현·검증했다.
- Where/What: `00600` forward/compensation/pgTAP과 Task 9 runner/tooling/integration.
- Why/How: private grant 없이 deferred invariant를 실행하기 위해 TDD,
  compensation/replay, retained-before-removal integration, independent review.
- How much: focused 8/8, full pgTAP 282, integration 8/8, tooling 16/16,
  synthetic table 8개 zero, 비용 0원.

### Evidence

- commits `5266abc`/`04a944f`/`228d8cb`; first commit의 4번째 path는 stale
  `002_invariants_test.sql` exact assertion test-only 동기화다.
- GREEN: `Files=6, Tests=282`; `00600` full posture PASS; compensated
  `Files=5, Tests=274`; exact `006→005→004→003→002→001`; absence/replay PASS.
- integration은 diagnostic branch 유지/제거 뒤 각각 8/8. cleanup은 최종
  identifier-scoped 단일 admin transaction이다.
- Ruff format/lint, strict Mypy, root/web/API/contract/secret/package/diff,
  no-URL exact 8 skips와 zero-row PASS.
- initial spec review Important 1/Minor 1은 `228d8cb`로 해결됐고 final spec과
  quality는 각각 Critical/Important/Minor 0/0/0이다.
- 이 closeout의 exact 10 docs에 대해 local link/control/stale/secret/package,
  protected scope 0, `git diff --check`를 재검증해 모두 PASS했다.

### Versions, security, privacy, data, rollback, handoff

모든 version 축은 유지됐다. API/table/data/seed/retention/dependency/cost/remote
state는 불변이고 secret/DSN/question/answer는 기록하지 않았다. rollback은 `00600`
compensation 후 기존 274 baseline, 전체는 006부터 역순이다. Task 9은 완료,
DB-001은 Task 10 ready다. A-021은 local blocker가 아니지만 public-release blocker다.
