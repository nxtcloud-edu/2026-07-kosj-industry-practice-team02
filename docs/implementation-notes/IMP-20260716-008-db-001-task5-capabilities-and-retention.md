# IMP-20260716-008 — DB-001 Task5 capabilities and retention

- Date/Time (KST): 2026-07-16T22:42:19+09:00
- Task ID: DB-001-T5
- Type: implementation/status
- Status: Done — Q-SEC-002=A accepted Task 5; Q-WF-001=A unblocked Task 6
- Author/Agent: Codex `/root` coordinator, Task 5 구현·검토 agents, 문서 closeout agent
- Branch: `codex/db-001-layered-enforcement`
- Base commit: Task 5 `67a40df`; 문서 closeout `264772d`
- Related plan/ADR/RFP: `docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md`, ADR-0011, D-018/D-025/D-026/D-027, RFP F-11/F-12/F-13, `.superpowers/sdd/task-5-brief.md`, `.superpowers/sdd/task-5-report.md`

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 승인된 DB-001 계획을 계속 구현하고, 독립적인 작업은 agent로 병렬 처리해 빠르게 진행하라고 요청했다. 이 기록은 Task 5의 역할·forced RLS·interaction 기록·30일 text retention 구현과 검증 결과를 남겼고, 이후 Q-SEC-002=A가 현재 fail-closed model을 승인해 Task 5가 완료됐다. Q-WF-001=A도 Task 6의 별도 사유 확인 capability를 승인했다.

### Acceptance Criteria

- TDD RED 뒤 `sejong_schema_owner`·`sejong_backend`, 여덟 테이블의 forced RLS와 owner-only policy, backend-only reviewed function 경계를 구현한다.
- `record_interaction`이 상태/사유/출처/office/text 조합, 원자적 event/failure write, 동일 요청 replay와 충돌 replay를 안전하게 처리한다.
- cutoff helper와 caller-time이 없는 public wrapper가 만료된 masked text만 파기하고 event/candidate 연결을 보존한다.
- pgTAP, 두 연결 replay·purge probe, error diagnostic 비노출, compensation→absence→replay를 통과한다.
- 제품 코드·공개 API·공식 seed·원격 DB·새 dependency·version manifest는 변경하지 않는다.
- 독립 검토 결과와 인간 결정 블로커를 숨기지 않고 plan·ambiguity register·누적 note·INDEX에 반영한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 승인자, Codex root coordinator, Task 5 구현 agent, 두 차례 독립 명세/품질 reviewer, 문서 closeout agent |
| When — 언제 | 2026-07-16 KST; Task 5 구현·재검토 직후 기록 |
| Where — 어디서 | `.worktrees/db-001-layered-enforcement`, disposable local Supabase PostgreSQL 17, `supabase/`, `database/`, DB-001 plan·notes |
| What — 무엇을 | capability roles, ownership/ACL/forced RLS, `record_interaction`, retention helper/wrapper, compensation, pgTAP과 동시성·privacy 증거 |
| Why — 왜 | 앱 실수나 직접 SQL이 승인·근거·개인정보 보관 규칙을 우회하지 못하게 하고, 같은 요청 재시도와 동시 실행을 안전하게 만들기 위해 |
| How — 어떻게 | pgTAP RED→GREEN, 최소 SQL 수정, deterministic lock과 `ON CONFLICT` re-read, stable SQLSTATE, 독립 review 두 번, root 재검증 |
| How much — 어느 정도 | 실행 migration 1개, compensation 1개, pgTAP 파일 1개; 현재 전체 172 assertions; 제품/공식 데이터/외부 비용 변화 0 |

## 3. 시작 전 상태

- 관련 파일: Task 5 brief/report, DB-001 plan, migration `00100`·`00200`, pgTAP `001`·`002`, logical DB draft, ADR-0011.
- 기존 동작: private schema·7 enum·8 table과 Task 4 불변조건까지 있었고 roles/RLS/capability/retention 함수는 없었다. baseline pgTAP은 94/94였다.
- 발견한 충돌/부채: 승인 계획은 모든 disabled elevated attribute를 replay 때 unconditional `ALTER ROLE`로 복구하라고 요구하지만, 현재 local migration runner는 non-superuser라 `NOSUPERUSER`, `NOREPLICATION`, `NOBYPASSRLS`를 비활성 방향으로도 실행할 수 없다. 구현은 생성 시 exact 속성을 부여하고 replay 시 위험 속성을 검증해 fail closed한다.
- Git 상태: Task 5 base `67a40df`; 구현 `fa6b755`; review fix `264772d`; 문서 작업 시작 전 clean.
- 비밀 경계: ignored env, DSN, DeepSeek key, 시민 질문 원문을 읽거나 출력하지 않았다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-SEC-002 | Resolved — Human | fail-closed non-superuser runner와 privileged auto-downgrade 중 선택 | A: 현재 model 유지, unsafe role 중단 / D-026 | Task 5 acceptance 완료 |
| Q-WF-001 | Resolved — Human | `NEW → REASON_CONFIRMED` capability 경계 | A: 별도 backend-only capability / D-027 | Task 6 구현 가능 |
| DB-T5-RC | Operational | Task 4 invariant-bearing write isolation | 기존 승인 계약인 `READ COMMITTED`; 다른 격리수준은 fail closed | `record_interaction`과 후속 repository |
| DB-T5-DATA | Safety | test/probe 데이터 성격 | synthetic fixture만 사용하고 종료 후 0 rows | 공식/mock lineage와 privacy |

## 5. 설계 결정과 대안

### 선택

- 업무 테이블은 `app_private`에 두고 여덟 테이블 모두 forced RLS와 정확히 하나의 `sejong_schema_owner` 전용 permissive `FOR ALL` policy로 잠갔다.
- `sejong_backend`에는 base-table CRUD나 `app_private` USAGE 없이 `app_api` USAGE와 검토된 함수 EXECUTE만 부여했다.
- `record_interaction`은 caller 입력을 enum cast/native constraint 전에 `P1010 / INVALID_INTERACTION`으로 검증하고, 이미 commit된 `request_id` replay를 현재 source/office provenance 조회보다 먼저 판정한다.
- 새 요청은 source→office 순서로 잠그고 `INSERT ... ON CONFLICT DO NOTHING RETURNING` 뒤 re-read해 동시 최초 요청도 하나의 event로 수렴시켰다.
- retention은 private exact-cutoff helper와 caller time을 받지 않는 public wrapper로 나눴고, text만 NULL 처리하며 행과 FK를 보존했다.
- role replay의 위험 속성은 현재 runner 권한 안에서 자동 변경하지 않고 검증 실패로 중단한다. Q-SEC-002=A가 이 최소권한 선택을 승인했다.

### 이유

공식 근거·승인·개인정보 규칙을 앱 코드만 믿지 않고 DB capability 경계에서도 강제해야 한다. replay가 현재 mutable provenance에 의존하면 과거 성공 요청이 출처 상태 변경 뒤 충돌로 바뀌므로, 저장된 immutable event metadata를 먼저 비교해야 idempotency가 안정적이다. caller가 cutoff를 정하지 못하게 해야 보관 정책을 임의로 앞당길 수 없다.

### 고려했지만 선택하지 않은 대안

- backend에 직접 table privilege와 RLS policy 부여: 함수별 최소 capability와 감사 가능한 경계가 사라져 제외.
- replay 때 ACTIVE/OFFICIAL source와 office를 다시 검증: 과거 동일 요청의 결과가 현재 데이터 변경에 따라 달라지는 review 재현 실패로 제외.
- replay 때 `masked_question` 비교 또는 복원: retention 후 replay가 text를 되살릴 수 있어 제외.
- public purge에 caller cutoff 노출: 보관 기간 우회가 가능해 제외.
- non-superuser runner에서 불가능한 `ALTER ROLE ... NOSUPERUSER/NOREPLICATION/NOBYPASSRLS`를 실행했다고 가장: 실제 PostgreSQL 권한과 다르므로 제외. Q-SEC-002=A로 privileged auto-downgrade도 제외.
- candidate 생성에 사유 확인을 암묵 결합: Q-WF-001=A가 별도 backend-only capability를 선택해 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `supabase/migrations/20260716000300_capabilities_and_functions.sql` | roles·ownership·schema/table/function ACL·forced RLS/policies, `record_interaction`, private/public purge, replay fix | backend capability와 privacy/provenance/idempotency를 DB에서 강제 |
| `database/rollbacks/20260716000300_capabilities_and_functions.rollback.sql` | grants/functions/policies/role-owned dependency를 역순 제거하고 FORCE만 해제; lower compensation 전제 | disposable local DB에서 Task 5를 복구 가능하게 함 |
| `supabase/tests/database/003_capabilities_test.sql` | exact role/RLS/policy/function allowlist, 상태 matrix, replay, retention, backend diagnostic 비노출 포함 78 assertions | vacuous ACL/policy 검사와 mutable-provenance replay 회귀를 차단 |
| `.superpowers/sdd/task-5-report.md` | RED/GREEN·동시성·compensation·review fix 증거 | ignored coordination evidence; 실행 권위는 migration/test 파일에 유지 |
| 이 note·plan·ambiguity register·INDEX | 기술 완료 증거와 후속 `Q-SEC-002`/`Q-WF-001` 해결 상태 기록 | 인간 결정 전 허위 완료와 결정 후 stale blocker를 모두 방지 |

### 데이터 흐름/상태 변화

1. backend가 이미 마스킹된 선택적 text와 metadata만 `app_api.record_interaction`에 전달한다.
2. 함수가 모든 입력과 상태 matrix를 먼저 검증하고 기존 `request_id`를 잠가 동일 replay면 기존 event/failure ID를 반환한다.
3. 새 SUCCESS는 ACTIVE+OFFICIAL sources와 OFFICIAL office를 결정적 순서로 잠그고 event 1건을 기록한다.
4. 지원 범위 fallback은 사유/text 유무에 따라 event 1건과 failure 0/1건을 같은 transaction에 기록한다. FOLLOWUP·OUT_OF_SCOPE·SYSTEM_ERROR는 event-only다.
5. purge helper는 `masked_question IS NOT NULL AND text_expires_at <= cutoff`인 행만 잠가 text를 NULL로 만들고 exact cutoff를 `text_purged_at`에 기록한다. event/failure/candidate 식별자와 FK는 유지된다.

### 오류·빈 상태·롤백

- invalid/status conflict/replay conflict/cutoff NULL은 caller text 없는 stable `P1010` 메시지로 fail closed하며 write 0건이다.
- purge 대상이 없으면 `0`과 empty UUID array를 반환하며 반복 호출도 동일하다.
- compensation은 후속 `00500` read와 `00400` workflow가 남아 있으면 중단하고, 정상 역순에서는 Task 5 capability와 roles를 제거하되 PUBLIC `public` schema CREATE를 복원하지 않는다.
- Q-SEC-002=A이므로 현재 migration의 fail-closed replay를 유지하고 privileged runner 변경은 하지 않는다.

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
- documentation: 2.3.13

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 범위 변경 없음 |
| Repo guidance | 1.4.0 | 1.4.0 | Task 10 전 manifest 유지 |
| Application | 0.1.0 | 0.1.0 | 제품 코드 변경 없음 |
| Web | 0.1.0 | 0.1.0 | UI 변경 없음 |
| API | 2.0.1-draft | 2.0.1-draft | 공개 계약 변경 없음 |
| Shared contracts | 0.2.1 | 0.2.1 | 계약 변경 없음 |
| DB schema manifest | 0.2.0-draft | 0.2.0-draft | executable migration은 3/5이나 Task 10까지 승격 보류 |
| Official data | 0.0.0-not-populated | 동일 | 공식 seed 0 rows |
| Mock data | 0.0.0-not-populated | 동일 | tracked mock seed 0 rows |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 미사용 |
| Test suite manifest | 0.4.2-readiness-contract | 동일 | 실행 pgTAP은 172 assertions이나 최종 baseline 승격 전 |
| Documentation | 2.3.13 | 2.3.13 | 중간 상태 문서만 추가; manifest 변경 없음 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `.tools/supabase/v2.109.1/supabase.exe test db` — 최초 Task 5 RED | exit 1; roles/RLS/functions 부재의 의도한 실패 | 새 6/6 fail, 기존 94 pass, 전체 100 | Task 5 report |
| 최초 구현 뒤 reset/test | exit 0 | 3 files, 167/167 | Task 5 report, commit `fa6b755` |
| review-fix RED `supabase test db` | exit 1; mutable provenance 변경 뒤 replay가 `P1010`, ID assertion NULL | Task 5 2/78 fail, 전체 172 | Task 5 report lines 214~240 |
| policy/function disposable catalog mutation probes | 예상 assertion이 각각 실패하고 mutation 즉시 제거 | unexpected policy 2 assertions, unapproved execute 2 assertions | Task 5 report lines 242~255 |
| `.tools/supabase/v2.109.1/supabase.exe db reset --local` | root 독립 재실행 PASS | migration `00100`→`00300` | root terminal |
| `.tools/supabase/v2.109.1/supabase.exe test db` | root 독립 재실행 PASS | `32 + 62 + 78 = 172/172` | root terminal, Task 5 report |
| `scripts/run_database_sql.py`로 `00300 → 00200 → 00100` compensation | root 독립 재실행 PASS | 3 files, 각 transaction commit | root terminal |
| `scripts/run_database_sql.py database/verify_db001_absent.sql` | PASS | app schemas/roles absence proof | root terminal |
| compensation 뒤 fresh reset/test | root 독립 재적용 PASS | 172/172 | root terminal |
| 두 독립 PostgreSQL session — identical/conflicting first request | 동일 요청은 같은 ID, 충돌은 wait 뒤 `P1010`; native `23505` 없음 | 2 scenarios, fixture 0 | Task 5 report lines 308~320 |
| 두 독립 PostgreSQL session — concurrent purge | A `1`, B wait 뒤 `0`, third `0`; exact cutoff와 event/candidate link 보존 | 2 sessions, fixture 0 | Task 5 report lines 322~335 |
| non-superuser backend diagnostic capture | `P1010`, stable message, 모든 diagnostic field에 sentinel 없음, write 0 | 1 synthetic probe | Task 5 report lines 293~306 |
| 독립 review 두 차례 | replay/policy/function test 보강 뒤 코드·명세상 추가 blocking finding 0 | Q-SEC-002=A로 acceptance 완료 | reviewer reports, commits `fa6b755`·`264772d`, D-026 |

### 미실행 검증과 이유

- Task 5 acceptance는 후속 Q-SEC-002=A 결정으로 완료됐다.
- `verify_database.ps1` 전체 gate는 Task 6~9 함수/read/repository/integration 파일이 아직 없어 Task 9 전까지 미실행이다.
- Task 9가 소유할 영구 두-connection integration test는 아직 만들지 않았다. Task 5에서는 독립 local session probe로 현재 race 동작만 확인했다.
- Task 6 reason confirmation 함수는 이 note 시점에는 미구현이며, Q-WF-001=A 이후 새 `00400`에서 구현한다.
- DeepSeek/API/UI/accessibility 실행은 DB-001 Task 5 범위 밖이며 외부 호출 0이다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문 원문 입력·저장 0. 함수는 이미 마스킹된 선택적 text만 받으며 FOLLOWUP/OUT_OF_SCOPE/SUCCESS text를 거부한다. replay와 purge가 text를 비교·복원하지 않는다.
- Security: forced RLS와 owner-only policies, base-table CRUD 거부, allowlisted SECURITY DEFINER owner/search_path/EXECUTE를 실제 backend role에서 검증했다. error diagnostic sentinel 비노출도 검증했다. Q-SEC-002=A가 role bootstrap acceptance를 닫았다.
- Accessibility: DB/문서 변경뿐이며 UI·키보드·대비 영향 없음.
- Performance/cost: source→office deterministic locking과 indexed request ID replay를 사용한다. concurrent insert/purge wait는 의도한 transaction serialization이다. local Docker 자원 외 외부 API·cloud·유료 비용 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: 0 rows; 공식 seed·PM 승인 데이터 변경 없음.
- mock/AI 생성: tracked seed 0 rows. 테스트와 probe는 합성 UUID/`MOCK` fixture 또는 capability 증명에 필요한 최소 synthetic OFFICIAL fixture만 transaction/local reset 안에서 사용했고 최종 잔존 0이다.
- schema/lineage: executable migration은 `00100`~`00300` 3/5까지 존재한다. 실행 권위는 timestamp migration이고 logical draft/manifest 승격은 Task 10 소유다.
- 출처명·URL·확인일: caller/LLM이 생성하지 않고 잠긴 ACTIVE+OFFICIAL KB/office row에서만 해석한다.
- verified date: 2026-07-16 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-SEC-002=A: 현재 non-superuser runner와 unsafe-role fail-closed 검증을 유지하며 privileged bootstrap은 추가하지 않는다.
- Q-WF-001=A: 새 별도 reason-confirmation capability를 `00400`에 구현하고 event 자동 사유는 불변으로 둔다. 후보는 확인 완료 IG만 허용한다.
- Task 5 SQL 동작, 권한 경계, 172/172 tests, replay/purge concurrency, diagnostic nonleak, compensation/replay는 모두 녹색이며 acceptance도 완료됐다.
- remote/public DB, official ACTIVE seed, production role bootstrap, data deletion, 새 production dependency는 승인되지 않았다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- PostgreSQL 17 membership option은 grantor별 row로 분리될 수 있어 test는 한 catalog row가 아니라 effective ADMIN/INHERIT/SET union을 검사한다.
- schema owner는 migration/test executor가 기존 fixture DML과 ownership transfer를 수행하도록 effective membership을 갖고, backend는 inherited table capability가 생기지 않게 INHERIT/SET을 갖지 않는다.
- committed replay는 현재 provenance 검증보다 먼저 수행하고 `IS NOT DISTINCT FROM`으로 저장 metadata를 비교한다. genuinely new request만 source/office를 잠근다.
- pgTAP은 effective ACL을 확장해 NULL ACL을 denial로 오인하는 vacuous test를 피하고, approved `app_api` OID/regprocedure allowlist 밖 backend EXECUTE를 0건으로 요구한다.
- private cutoff helper는 sorted UUID array를 반환하고 zero case를 typed empty UUID array로 고정한다.

## 13. 인수인계·재현·롤백

### 재현

1. branch에 `fa6b755`와 `264772d`가 순서대로 있는지, tracked status가 clean인지 확인한다.
2. local-only 환경에서 `supabase db reset --local` 뒤 `supabase test db`를 실행해 `Files=3, Tests=172, Result: PASS`를 확인한다.
3. process environment에만 local admin DSN을 두고 `00300 → 00200 → 00100` compensation과 `database/verify_db001_absent.sql`을 실행한다. DSN/child error detail은 출력하지 않는다.
4. 다시 reset/test해 172/172와 fixture 0을 확인한다.
5. D-026/D-027과 ADR-0011의 refined decision을 확인한다.
6. 적용된 `00100~00300`을 수정하지 않고 `00400_candidate_workflow.sql` RED부터 시작한다.

### 롤백

- disposable local DB 목표 순서는 `00500`, `00400`, `00300`, `00200`, `00100` compensation 뒤 absence proof다. 현재 Task 5만 적용된 상태에서는 `00300 → 00200 → 00100`을 사용한다. 정상 복구는 fresh `db reset --local`이다.
- Task 5 코드만 되돌릴 때는 `264772d` 뒤 `fa6b755` 순서로 revert한다. 적용된/공유된 migration을 직접 수정하지 않는다.
- 이 문서 commit만 잘못됐으면 해당 docs commit을 revert하면 되며 제품 schema/data에는 변화가 없다.

### 다음 개발자 시작점

D-026/D-027이 반영된 plan에서 새 `00400` candidate workflow/audit RED부터 시작한다. 시민 read/index는 `00500`으로 이동했다.

## 14. 남은 위험·미해결 질문·다음 단계

- Q-SEC-002/Q-WF-001은 A로 해결됐고 인간 A/Blocker는 0개다.
- 현재 concurrent probes는 one-off local evidence다. Task 9에서 영구 자동화해야 한다.
- PostgreSQL native CHECK `DETAIL`과 SQL parameters를 Task 8 repository가 로그/응답에 남기지 않는 sanitizer 검증이 여전히 필요하다.
- parent KB와 child question explicit delete 동시성은 삭제 API 추가 전 별도 검증이 필요한 P2 위험이다.
- 다음 단계: immutable 새 `00400` workflow migration의 Task 6 RED부터 시작한다.

## 15. 자체 리뷰

- [x] 요청·6W1H·인수 기준·설계/대안 기록
- [x] Task 5 RED/GREEN·root verification·review·compensation·concurrency 증거 기록
- [x] 제품 코드·SQL·계약·version manifest·공식 데이터 변경 없음
- [x] 개인정보 원문·secret·DSN 노출 없음
- [x] `Q-SEC-002`/`Q-WF-001`을 인간 결정과 AI 내부 세부에서 분리
- [x] rollback·recovery·재현·handoff 기록
- [x] 구현 노트 INDEX 갱신
