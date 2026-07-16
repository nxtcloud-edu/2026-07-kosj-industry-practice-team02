# IMP-20260717-002 — DB-001 Task 7 official citizen reads

- Date/Time (KST): 2026-07-17T02:00:20+09:00
- Task ID: DB-001-T7
- Type: implementation
- Status: Done
- Author/Agent: Codex `/root` coordinator, Task 7 implementation/review agents
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `e05e0368f421c1379123d02b282cb2aaef2382eb`
- Implementation commits: `37b5e2c2b4c50c7466c3b5ed8f9161ec13fe6b49`, `59a69bd`
- Related plan/ADR/RFP: [DB-001 실행계획](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md), [ADR-0011](../adr/0011-layered-database-and-backend-enforcement.md), D-025/D-026/D-027, RFP F-11/F-12/F-13, [Task 6 완료 노트](IMP-20260717-001-db-001-task-6-atomic-candidate-workflow.md)

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 승인된 DB-001 계획의 구현을 계속하고 병렬 처리 가능한 검토는 에이전트로 수행하라고 요청했다. Task 7 범위는 공식 시민 읽기 인터페이스와 조회 인덱스를 TDD로 추가하되 공식 seed, 공개 API, remote, 새 의존성, DeepSeek 호출을 만들지 않는 것이다.

### Acceptance Criteria

- `list_active_kb(text)`는 유효한 지원 intent의 `ACTIVE+OFFICIAL` KB만 반환하고 질문 예시와 저장된 공식 출처 메타데이터를 결정적 순서로 결합한다.
- `list_offices(text,text)`는 지원 지역·intent에 매핑된 `OFFICIAL` 기관만 반환한다.
- 두 함수는 `STABLE`, `SECURITY DEFINER`, 고정 `search_path`, schema owner 소유이고 backend만 실행 가능하다.
- PUBLIC/anon/authenticated 실행과 backend의 private base-table SELECT는 계속 차단한다.
- 승인된 다섯 index의 이름·table·key order·predicate를 정확히 생성한다.
- mock·DRAFT/PENDING/RETIRED/REJECTED·비일치 mapping은 시민 결과에 나타나지 않는다.
- `00500`만 보상한 뒤 함수/index가 0이고 Task 1~6의 234 assertions와 concurrency 4 scenarios가 보존되며, fresh replay가 274/274와 concurrency 4를 통과한다.
- persistent 공식/mock row, 실제 개인정보·비밀값, 계약·버전·환경·의존성 변화가 없다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 승인자, Codex root coordinator, Task 7 구현 agent, 독립 reviewer |
| When — 언제 | 2026-07-17 KST, Task 6 clean 기준선 뒤 Task 7 구현·검증·문서 마감 |
| Where — 어디서 | `.worktrees/db-001-layered-enforcement`, local Docker Desktop/Supabase PostgreSQL, `supabase/`, `database/`, `.superpowers/sdd/`, `docs/` |
| What — 무엇을 | 다섯 조회 index, 두 backend-only 공식 시민 읽기 함수, 역보상 SQL, 40개 pgTAP assertion |
| Why — 왜 | LLM이 출처를 만들지 않고 서버가 승인된 공식 KB/기관 메타데이터만 읽도록 DB 경계를 강제하기 위해 |
| How — 어떻게 | migration 부재 RED → 최소 SQL GREEN → test-only 진단 강화 → compensation/absence/replay → 두 연결 concurrency → 독립 review |
| How much — 어느 정도 | production SQL 1, compensation 1, pgTAP 1, index 5, function 2, 최종 274 assertions, persistent row 0, 외부 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: 적용된 immutable migrations `00100~00400`, matching compensations, pgTAP `001~004`, [Task 7 brief/report](../../.superpowers/sdd/task-7-report.md).
- 기존 동작: private schema·RLS/capabilities·retention·원자 후보 workflow까지 구현됐고 full pgTAP은 234/234, concurrency는 4 scenarios였다. 시민 읽기 함수와 다섯 index는 없었다.
- 발견한 충돌/부채: 첫 focused GREEN 시 catalog `name::text`의 `C` collation과 expected literal의 default collation이 달라 test harness가 assertion 전에 실패했다. production behavior가 아닌 test comparison 경계였다.
- Git 상태: clean base `e05e036`; 기존 forward migrations `00100~00400`은 수정하지 않았다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| DB-001 plan | Human approved | Task 7 local implementation | 승인된 계획 그대로 실행 | 00500·pgTAP·보상 허용 |
| official seed | Human/PM deferred | 승인 공식 row | DATA-001 전 0 rows 유지 | `/ready=503`, persistent read result empty |
| read filters | Already decided | 지원 intent/지역 | 네 intent, 아름동·도담동·조치원읍 allowlist | invalid input은 고정 `P1010` |
| Task 8 boundary | Planned | DB native diagnostic 처리 | repository가 sqlstate만 매핑하고 detail/parameter 폐기 | 현재 public/API route 없음 |
| collation | Internal | catalog expected-row 비교 | test expected literal에 명시적 `C` 적용 | production SQL 변화 없음 |

새 인간 A/Blocker는 없으며 기존 source-of-truth와 D-025~D-027을 다시 묻지 않았다.

## 5. 설계 결정과 대안

### 선택

- `app_api.list_active_kb(text)`와 `app_api.list_offices(text,text)`를 schema-qualified 고정 SQL을 사용하는 backend-only `SECURITY DEFINER` 함수로 제공한다.
- enum cast 전에 text allowlist를 검증해 잘못된 입력이 native enum diagnostic으로 새지 않게 하고 `P1010 / INVALID_READ_FILTER`만 반환한다.
- KB는 `status='ACTIVE' AND data_origin='OFFICIAL'`, 기관은 `data_origin='OFFICIAL'`과 region+intent mapping으로 제한한다.
- 질문 예시는 row-local correlated aggregate로 한 번만 모으고 `C` collation lexical order, 결과 row는 public ID 순서로 고정한다.
- 다섯 index는 계획의 exact name/key/predicate만 생성하며 보상은 함수부터 제거한 뒤 index만 제거한다.

### 이유

시민 응답 근거와 기관 카드는 LLM 생성물이 아니라 승인된 DB 메타데이터여야 한다. private table을 backend에 열지 않고 제한된 함수만 공개하면 API 구현 실수에도 ACTIVE+OFFICIAL 경계와 반환 열 allowlist를 유지할 수 있다.

### 고려했지만 선택하지 않은 대안

- base table SELECT grant: private 열·비공식 상태 노출 위험 때문에 제외했다.
- view/Data API 노출: app schema가 Data API에서 제외된 local-only 설계와 맞지 않고 필터 우회 범위가 넓어 제외했다.
- dynamic SQL 또는 caller-provided sorting/filter: SQL injection·계약 확장·diagnostic 노출 위험 때문에 제외했다.
- 실제 공식 seed로 테스트: PM 승인 전 데이터 혼입 위험 때문에 transaction-scoped synthetic fixture만 사용했다.
- application-side provenance filter: DB 우회를 막지 못해 제외했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `supabase/migrations/20260716000500_indexes_and_read_interfaces.sql` | exact five indexes와 두 `STABLE SECURITY DEFINER` read function, owner/ACL | ACTIVE+OFFICIAL와 backend-only 시민 조회 경계 |
| `database/rollbacks/20260716000500_indexes_and_read_interfaces.rollback.sql` | backend execute revoke, 두 함수 drop, 다섯 index drop | Task 6 기준선을 보존하는 부분 보상 |
| `supabase/tests/database/005_citizen_reads_test.sql` | catalog/posture/ACL/index/filter/ordering/diagnostic/cleanup 40 assertions | 비공허 read 계약과 privacy regression 검증 |
| `.superpowers/sdd/task-7-report.md` | RED/GREEN/compensation/replay/catalog 증거 | 작업 재현과 review handoff |
| 이 노트·실행계획·`TASKS.md`·INDEX | Task 7 완료, Task 8 준비 상태 동기화 | 인수인계와 단일 진행 상태 유지 |

### 데이터 흐름/상태 변화

유효한 intent/region을 받은 backend가 `app_api` 함수를 호출하면 함수가 private table을 schema-qualified로 읽고 공식·상태·mapping 조건을 DB에서 적용한다. KB 응답에는 stored source title/URL/verified date와 질문 예시 JSON 배열만, 기관 응답에는 stored official office/source 열만 반환한다. 테스트 fixture는 transaction 안에서 생성·rollback되고 concurrency cleanup 뒤 application-table row total은 0이다. tracked seed와 공식/mock persistent row는 추가하지 않았다.

### 오류·빈 상태·롤백

- NULL·blank·padded·미지원·OUT_OF_SCOPE·UNKNOWN filter는 `P1010 / INVALID_READ_FILTER`; stacked diagnostics에 sentinel input이 없다.
- 유효한 필터에 match가 없으면 오류가 아니라 0 rows다.
- 첫 test harness collation failure는 expected catalog literal에 `C` collation을 지정해 해결했고 production SQL은 변경하지 않았다.
- `00500` 보상은 두 함수와 다섯 index만 제거한다. roles, RLS, event/retention, workflow, table rows/definitions는 건드리지 않는다.

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
| Application | 0.1.0 | 0.1.0 | Task 8 전 application code 변화 없음 |
| Web | 0.1.0 | 0.1.0 | UI 변화 없음 |
| API | 2.0.1-draft | 2.0.1-draft | public wire/API 계약 변화 없음 |
| Shared contracts | 0.2.1 | 0.2.1 | 계약 변화 없음 |
| DB schema | 0.2.0-draft | 0.2.0-draft | executable 00500은 추가됐으나 Task 10 final gate 전 manifest 유지 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | persistent official row 0 |
| Mock data | 0.0.0-not-populated | 0.0.0-not-populated | persistent mock row 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 0.0.2-deepseek-v4-flash-selected | LLM 호출/프롬프트 변화 없음 |
| Test suite | 0.4.2-readiness-contract | 0.4.2-readiness-contract | Task 10 전 manifest 유지 |
| Docs | 2.3.14 | 2.3.14 | 중간 Task closeout; Task 10에서 최종 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| migration 없는 기준선에서 `.tools/supabase/v2.109.1/supabase.exe test db` | 의도한 RED: 기존 234 pass, 005 catalog 9/11 fail 뒤 undefined function, exit nonzero | production 00500 작성 전 | `.superpowers/sdd/task-7-report.md` |
| focused `supabase test db supabase/tests/database/005_citizen_reads_test.sql` | PASS | 40/40 | Task 7 report/agent terminal |
| full `supabase test db` | PASS | 274/274 | Task 7 report/root terminal |
| process-only admin DSN으로 `scripts/run_database_sql.py database/rollbacks/20260716000500_indexes_and_read_interfaces.rollback.sql` | PASS, stable output `files=1` | compensation 1 file | Task 7 report/root terminal |
| post-compensation catalog probe | 함수 0, index 0 | Task 7 object absence | Task 7 report/root terminal |
| post-compensation pgTAP + `scripts/test_database_concurrency.py` | PASS | 234/234 + 4 scenarios/2 connections | Task 7 report/root terminal |
| fresh `supabase db reset --local` + full pgTAP + concurrency | PASS | five migrations, 274/274 + 4 scenarios/2 connections | Task 7 report/root terminal |
| final catalog/ACL/privacy probe | `functions=2 posture=2 acl=2 indexes=5 rows=0 backend_select=0` | exact counts | Task 7 report/root terminal |
| independent code review after test-hardening commit `59a69bd` | clean | Critical/Important/Minor 0 | coordinator/reviewer result |
| secret scan + `git diff --check` | PASS | matches 0, whitespace error 0 | Task 7 report/root terminal |

Root는 reset/full `274+4`, compensated `234+4`, final reset/full `274+4`를 독립 재현했다. test-hardening은 dynamic SQL assertion을 exact-two-function non-vacuous check로 강화하고 두 함수의 stacked diagnostics를 각각 검사했으며 production/compensation behavior는 바꾸지 않았다.

### 미실행 검증과 이유

- `scripts/verify_database.ps1`: Task 8 repository와 Task 9 integration/gate가 아직 없어 최종 runner 완료 조건 전이다.
- API integration/root `scripts/verify.ps1`: Task 7은 public route/application code를 바꾸지 않았고 Task 8/9가 repository/integration 연결을 소유한다.
- DeepSeek/API call: DB read boundary 범위 밖이며 실제 key를 읽거나 전송하지 않았다.
- 원격 Supabase/deploy: 승인되지 않았고 원격 저장소도 없다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 반환 열은 승인된 시민용 KB/기관 메타데이터 allowlist뿐이다. raw question/answer/transcript/token/IP/device/creator/approver/private timestamp를 반환하지 않는다. synthetic sentinel/fixture만 썼고 persistent row는 0이다.
- Security: fixed search path, schema qualification, no dynamic SQL, exact owner/ACL, backend-only EXECUTE, private base-table SELECT denial을 검증했다. invalid filter는 고정 오류만 내며 input을 diagnostic에 반사하지 않는다. `.env`와 DeepSeek key는 읽지 않았다.
- Accessibility: UI·사용자 상호작용 변화 없음. Task 7은 DB interface만 추가했다.
- Performance/cost: ACTIVE+OFFICIAL category partial index와 event/failure/candidate 운영 index 4개를 추가했다. question aggregate는 KB row-local이며 결정적 정렬을 사용한다. local CPU/disk 외 외부 API·클라우드 비용은 0원이다.

## 10. 데이터와 출처 영향

- 공식 데이터: persistent 0 rows. 공식 source title/URL/verified date는 테스트의 synthetic record에서 저장값 그대로 반환되는지만 검증했다.
- mock/AI 생성: persistent 0 rows. transaction-scoped synthetic MOCK/non-active rows로 exclusion만 검증했다.
- schema/lineage: executable migration은 5/5가 됐다. `00500`은 table/lineage를 바꾸지 않고 index/function/ACL만 추가한다. manifest DB version은 Task 10 전까지 0.2.0-draft다.
- verified date: 2026-07-17 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 시민 읽기 DB 경계는 구현됐지만 실제 공식 데이터는 아직 0건이므로 `/ready=503`이 맞다. DATA-001의 PM 승인과 DATA-SEED-001 전에는 실서비스 데이터로 간주하면 안 된다.
- 두 함수는 지원 intent/지역만 허용하고 ACTIVE+OFFICIAL KB·OFFICIAL 기관만 반환한다. 이 공개 사용자 동작을 바꾸려면 제품/데이터 계약 검토가 필요하다.
- remote Supabase, 공개 배포, official seed 활성화, retention/권한 변경, 새 production dependency는 이번 Task에서 승인되지 않았다.
- public API나 UI는 아직 이 함수를 호출하지 않는다. Task 8이 typed repository와 diagnostic sanitizer를, Task 9가 integration/rollback gate를 구현한다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- index catalog tests는 exact five ordinary indexes만 허용하고 key order, DESC, predicate, validity/readiness를 검사한다.
- question examples는 correlated `jsonb_agg`와 `C` collation을 써서 locale과 관계없이 lexical order를 고정한다.
- test-hardening은 함수 정의 두 개가 모두 standalone `EXECUTE` token을 포함하지 않음을 비공허하게 검사하며, 각 invalid read의 모든 diagnostic field에서 sentinel 비노출을 확인한다.
- compensation 실행 시 admin DSN은 process environment `SEJONG_ADMIN_DATABASE_URL`로만 전달하고 CLI status child output을 억제한다. 값을 출력하거나 파일에 새로 쓰지 않는다.

## 13. 인수인계·재현·롤백

### 재현

1. branch `codex/db-001-layered-enforcement`의 commits `37b5e2c`, `59a69bd`와 clean status를 확인한다.
2. `.tools/supabase/v2.109.1/supabase.exe db start`로 local PostgreSQL-only runtime을 시작한다.
3. child output에 local credential이 보이지 않도록 억제한 `db reset --local`로 `00100~00500`을 fresh replay한다.
4. `.tools/supabase/v2.109.1/supabase.exe test db`가 `Files=5, Tests=274, Result: PASS`인지 확인한다.
5. 관리자 DSN은 출력하지 않고 process environment `SEJONG_ADMIN_DATABASE_URL`로만 전달해 `apps/api/.venv/Scripts/python.exe -B scripts/test_database_concurrency.py`가 `scenarios=4 connections=2` PASS인지 확인한다. 안전한 env/runner 경계는 [Task 6 완료 노트](IMP-20260717-001-db-001-task-6-atomic-candidate-workflow.md)와 `scripts/run_database_sql.py`를 따른다.
6. catalog probe가 `functions=2 posture=2 acl=2 indexes=5 rows=0 backend_select=0`인지 확인한다.

### 롤백

Task 7만 보상하려면 관리자 DSN을 process environment로만 넘겨 다음 검토된 파일 하나를 `scripts/run_database_sql.py`로 실행한다.

```text
database/rollbacks/20260716000500_indexes_and_read_interfaces.rollback.sql
```

이후 두 read function과 다섯 index가 0인지, 기존 네 pgTAP file이 234/234인지, concurrency 4 scenarios가 통과하는지 확인한다. 복구는 `supabase db reset --local`로 다섯 migration을 replay하고 274/274+4를 재검증한다. 전체 DB-001 보상 순서는 `00500 → 00400 → 00300 → 00200 → 00100`이다. 코드 rollback은 test-only `59a69bd`를 먼저, production `37b5e2c`를 다음에 revert한다.

### 다음 개발자 시작점

[DB-001 실행계획의 Task 8](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md)을 읽고 lazy typed FastAPI DB boundary의 error/model tests를 RED로 시작한다. `00100~00500` forward migrations는 immutable로 취급하고 public route나 새 production dependency는 추가하지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- Task 8 전에는 PostgreSQL native CHECK/detail과 parameter를 API/log에서 폐기하는 sanitizer가 없다. 현재 public route는 연결되지 않았지만 repository 구현에서 반드시 sqlstate-only mapping을 검증해야 한다.
- Task 9의 permanent Python integration과 complete five-stage rollback/replay runner는 아직 남았다.
- 공식 seed가 0이라 빈 valid 결과만 실제 persistent 상태다. DATA-001/DATA-SEED-001 전에는 readiness 503을 유지한다.
- index의 production 규모 성능은 실제 데이터가 없어 측정하지 않았다. 데이터 승인 후 query plan과 latency budget을 별도 확인한다.
- 다음 단계: Task 8 lazy typed FastAPI repository boundary TDD.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화 — 계약·manifest 버전 변화 없음
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
- [x] 공식/mock persistent row 0과 `/ready=503` 경계 기록
- [x] compensation/replay·인수인계·다음 Task 명시
