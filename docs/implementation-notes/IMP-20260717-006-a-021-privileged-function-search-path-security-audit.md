# IMP-20260717-006 — A-021 privileged function search path security audit

- Date/Time (KST): 2026-07-17
- Task ID: DB-001-A021
- Type: discovery
- Status: Done — B/High follow-up remains open
- Author/Agent: Codex `/root` coordinator and security audit agent
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `228d8cb`
- Related plan/ADR/RFP: A-021, proposed Q-SEC-003, [ADR-0012](../adr/0012-deferred-active-question-trigger-execution.md), [DB-001 design](../superpowers/specs/2026-07-16-db-001-layered-enforcement-design.md), [Task 9A plan](../superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md), RFP F-11/F-12/F-13

## 1. 사용자 요청과 완료 기준

### 요청

Task 9 closeout 전 A-021을 read-only로 감사하고, 실제 확인된 privileged function graph와 PostgreSQL 17 공식 근거, 위험 신뢰도, 인간 선택지, public-release 차단 경계를 문서화한다. `00700`이나 Task 10을 구현하지 않고 모든 version 축과 코드·SQL·계약·데이터를 유지한다.

### Acceptance Criteria

- local catalog에서 `app_api` SECURITY DEFINER 9개와 중첩/trigger `app_private` 13개, 합계 22개를 exact signature로 확인한다.
- `00600`으로 validator 하나만 교정돼 unsafe `pg_catalog`-only path가 21개임을 확인한다.
- application relation/helper qualification과 dynamic SQL 0을 확인한다.
- data-type shadow DoS와 privilege escalation을 서로 다른 신뢰도로 기록하고 exploit 재현을 주장하지 않는다.
- Q-SEC-003 A/B/default와 public release 차단을 ambiguity register에 기록한다.
- 새 note, ambiguity register, INDEX 정확히 3개만 docs-only commit한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 보안 승인자, Codex root coordinator, read-only audit agent, 후속 DB/security reviewer |
| When — 언제 | 2026-07-17 KST, `00600`·Task 9 구현/review 완료 후 문서 closeout 전 |
| Where — 어디서 | disposable local PostgreSQL 17 catalog, immutable migrations `00200`~`00600`, `docs/11_AMBIGUITY_REGISTER.md`, 이 note와 INDEX |
| What — 무엇을 | privileged execution graph 22개와 search-path posture, object qualification, dynamic SQL, TEMP 전제, 공식 근거 감사 |
| Why — 왜 | local-only 성공을 public 안전성으로 오인하지 않고 remote/public release 전에 별도 인간 결정을 받기 위해 |
| How — 어떻게 | DSN을 메모리에서만 child process에 전달한 read-only catalog query, migration source review, PostgreSQL 17 공식 문서 대조 |
| How much — 어느 정도 | 함수 22개, unsafe path 21개, dynamic SQL 0, docs 3개, DB/API/table/data/dependency/version/cost 변화 0 |

## 3. 시작 전 상태

- 관련 파일: migrations `00200`~`00600`, pgTAP `002`/`006`, D-028/ADR-0012, A-021, Task 9 implementation/review commits `5266abc`, `04a944f`, `228d8cb`.
- 기존 동작: Task 9 full local gate와 review는 통과했다. validator는 exact `search_path=pg_catalog, pg_temp`; 나머지 graph는 `pg_catalog`-only다.
- 발견한 충돌/부채: DB-001 local/private 완료 조건과 public release 보안 조건을 분리하지 않으면 21개 unsafe path를 완료로 오인할 수 있다.
- Git 상태: clean base `228d8cb`; 원격 저장소 없음. 감사 시작 뒤 generator가 이 note와 INDEX entry만 만들었다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-021 | B/High — Open/Deferred | privileged graph 22개 중 21개 `pg_catalog`-only | local Task 9 blocker 아님; public release blocker | remote/public 배포·public admin/API·public backend credential |
| Q-SEC-003 A | Human recommended | exact 22 signatures property-only hardening | 새 `00700` + compensation + catalog/behavior regression | DB migration/test/docs; 공개 API/data 불변 |
| Q-SEC-003 B/default | Human safe default | 현 posture 유지 | local-only 완료 허용, public release 차단, `00700` 미구현 | 비용 0, 공개 운영 불가 |
| exploit proof | Not performed | 실제 temp-domain/table/operator exploit | 재현했다고 주장하지 않음 | 신뢰도 제한을 명시 |

## 5. 설계 결정과 대안

### 선택

이번 요청은 read-only audit로 종료한다. A-021을 B/High Open/Deferred로 유지하고 Q-SEC-003 A를 추천한다. A는 새 `00700` property-only forward migration에서 아래 exact 22 signatures의 `search_path`만 `pg_catalog, pg_temp`로 보정하고 matching compensation과 catalog/behavior 회귀를 요구한다. 사용자가 답하지 않으면 B/default로 local-only 완료만 허용하며 public release 관련 경로를 차단한다.

### 이유

PostgreSQL 17은 SECURITY DEFINER가 owner 권한으로 실행되므로 untrusted writable schema를 search path에서 배제하고 `pg_temp`를 마지막에 명시하라고 요구한다. runtime `search_path`는 단순 이름의 table뿐 아니라 data type, function 등에도 적용된다. 현재 source는 application relation/helper를 schema-qualified하고 dynamic SQL을 쓰지 않아 직접적인 relation/helper masking 표면을 줄였지만, 이것만으로 모든 runtime type/operator/function resolution 위험이 사라졌다고 증명할 수 없다.

### 위험 신뢰도

- data-type shadow DoS: **high-confidence plausible**. 공식 문서는 search path가 data type에도 적용되고 writable temporary schema가 기본적으로 먼저 검색될 수 있음을 설명한다. PL/pgSQL/SQL body의 execution-time parsing·compilation 특성과 현재 21개 unsafe path/TEMP 전제가 결합한다. 실제 exploit은 실행하지 않았다.
- privilege escalation: **conservative medium-confidence inference**. 공식 SECURITY DEFINER 지침은 masking object가 owner 권한 실행을 바꿀 수 있음을 경고하지만, 현재 application relation/helper qualification과 dynamic SQL 0 때문에 이 저장소의 구체적 escalation chain은 입증되지 않았다.

### 고려했지만 선택하지 않은 대안

- 이번 commit에서 `00700` 구현: 인간 승인과 별도 SQL/TDD 범위를 건너뛰므로 금지.
- TEMP 권한 제거: local capability/운영 동작에 별도 영향을 줄 수 있고 exact 22 posture correction보다 넓어 이번 선택지에서 제외.
- 함수 body rewrite/type 전수 qualification: property-only 최소 변경을 넘고 body hash/behavior risk가 커 별도 대안으로 보류.
- 위험 무시 후 public release: 공식 지침과 B/High 판단에 반하므로 금지.

## 6. 감사 결과

### privileged execution graph — exact 22 signatures

`app_api` SECURITY DEFINER 9개:

1. `app_api.approve_kb_candidate(p_candidate_id uuid, p_actor_id text, p_actor_role text, p_review_comment text)`
2. `app_api.confirm_failed_question_reason(p_failed_question_id uuid, p_actor_id text, p_actor_role text, p_confirmed_reason text)`
3. `app_api.create_kb_candidate(p_failed_question_id uuid, p_actor_id text, p_actor_role text, p_title text, p_representative_question text, p_category text, p_answer_summary text, p_procedure_steps jsonb, p_required_documents jsonb, p_processing_time text, p_fee text, p_department text, p_source_title text, p_source_url text, p_last_verified_at date, p_caution text, p_data_origin text)`
4. `app_api.list_active_kb(p_intent text)`
5. `app_api.list_offices(p_region text, p_intent text)`
6. `app_api.purge_expired_failed_question_text()`
7. `app_api.record_interaction(p_request_id uuid, p_intent text, p_answer_status text, p_fallback_reason text, p_used_source_ids text[], p_response_time_ms integer, p_selected_region text, p_routed_office_public_id text, p_is_test boolean, p_masked_question text)`
8. `app_api.reject_kb_candidate(p_candidate_id uuid, p_actor_id text, p_actor_role text, p_review_comment text)`
9. `app_api.submit_kb_candidate(p_candidate_id uuid, p_actor_id text, p_actor_role text)`

중첩/helper/trigger `app_private` 13개:

1. `app_private.is_allowed_audit_changed_fields(p_value jsonb)`
2. `app_private.is_nonempty_text(p_value text)`
3. `app_private.is_text_array(p_value jsonb)`
4. `app_private.is_unique_text_array(p_value jsonb)`
5. `app_private.lock_kb_question_parents()`
6. `app_private.purge_expired_failed_question_text_at(p_cutoff timestamp with time zone)`
7. `app_private.set_updated_at()`
8. `app_private.validate_active_kb_question()`
9. `app_private.validate_failed_question_candidate()`
10. `app_private.validate_failed_question_event()`
11. `app_private.validate_interaction_event_failure()`
12. `app_private.validate_interaction_event_sources()`
13. `app_private.validate_kb_candidate_failure()`

`00600` 뒤 `validate_active_kb_question()`만 exact `pg_catalog, pg_temp`다. 따라서 22개 중 unsafe `pg_catalog`-only path는 21개다. `sejong_backend`의 effective database TEMP는 true다.

### body/source review

- graph 22개 catalog body에서 `EXECUTE` token은 0이며 dynamic SQL은 없다.
- application table/relation과 nested helper의 실제 object references는 `app_private.`로 schema-qualified됐다. `offices` 같은 table alias와 `TG_TABLE_NAME='kb_documents'` 같은 metadata string은 object reference가 아니므로 qualification 결함으로 세지 않았다.
- 이 결과는 application object masking 표면을 줄였다는 증거이지 runtime data type/operator/function resolution 전체가 안전하다는 증거는 아니다.

### 공식 PostgreSQL 17 출처

- [CREATE FUNCTION — Writing SECURITY DEFINER Functions Safely](https://www.postgresql.org/docs/17/sql-createfunction.html#SQL-CREATEFUNCTION-SECURITY): owner 권한 실행, untrusted writable schema 배제, `pg_temp` 마지막, PUBLIC EXECUTE revoke 지침.
- [Client Connection Defaults — search_path](https://www.postgresql.org/docs/17/runtime-config-client.html#GUC-SEARCH-PATH): simple name의 table/data type/function 등을 search path 순서로 해석.
- [PL/pgSQL under the Hood](https://www.postgresql.org/docs/17/plpgsql-implementation.html): execution-time statement preparation, variable substitution, plan caching의 안전성 관련 전제.
- [CREATE DOMAIN](https://www.postgresql.org/docs/17/sql-createdomain.html): domain이 schema에 속하는 data type이며 지정 schema 또는 current schema에 생성되는 규칙.

### 데이터 흐름/상태 변화

없다. read-only catalog/source audit와 문서만 변경했다. DB function property, role, table, row, API route/contract는 바뀌지 않았다.

### 오류·빈 상태·롤백

첫 qualification 자동검사는 table alias/trigger metadata string 3개를 unqualified object로 오인해 fail했다. 실제 source context를 대조해 세 항목이 object reference가 아님을 확인하고, 최종 주장은 catalog dynamic-SQL 판정+source review로 제한했다. DB transaction이나 persistent object는 만들지 않았다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 제품 범위 무변경 |
| Repo guidance | 1.4.0 | 1.4.0 | 운영 규칙 무변경 |
| Application | 0.1.0 | 0.1.0 | 코드 무변경 |
| Web | 0.1.0 | 0.1.0 | UI 무변경 |
| API | 2.0.1-draft | 2.0.1-draft | wire contract 무변경 |
| Shared contracts | 0.2.1 | 0.2.1 | 계약 무변경 |
| DB schema | 0.2.0-draft | 0.2.0-draft | `00700` 미구현 |
| Official data | 0.0.0-not-populated | 동일 | row/seed 무변경 |
| Mock data | 0.0.0-not-populated | 동일 | row/seed 무변경 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 무관 |
| Test suite | 0.4.2-readiness-contract | 동일 | 테스트 코드 무변경 |
| Docs | 2.3.14 | 2.3.14 | manifest promotion 없음 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `python scripts/new_implementation_note.py --title "A-021 privileged function search path security audit" --task-id DB-001-A021 --type discovery` | PASS, IMP-20260717-006 생성·INDEX 추가 | note 1 | 이 파일/INDEX |
| memory-only local status + read-only catalog audit | `A021-GRAPH PASS app_api=9 app_private=13 total=22 unsafe=21`; dynamic SQL 0; backend TEMP true | signatures 22 | 이 note의 exact list |
| migration source context review | application object references qualified; alias/metadata false positives 3개 분리 | 22 bodies | `supabase/migrations/00200`~`00600` |
| PostgreSQL 17 official documentation review | required four primary sources 확인 | sources 4 | 위 공식 출처 링크 |
| local links/control/stale scan | PASS | docs 3, invalid link/control/placeholder 0 | repository PowerShell/`rg` |
| secret/package/version/protected scope/diff | PASS | secret exit 0, package 12 required, protected diff 0 | repository gates |
| exact staged scope | PASS | docs 3, code/SQL/version excluded | Git staged-name comparison |

### 미실행 검증과 이유

- exploit/DoS/privilege-escalation reproduction: read-only audit 범위를 벗어나며 실제 공격 성공을 주장하지 않기 위해 미실행.
- `00700`, compensation, pgTAP, integration regression: Q-SEC-003 인간 승인 전 구현 금지.
- remote/public DB, public admin/API, public backend credential: A-021 해결 전 차단.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문·답변·실제 row·DSN·password·key를 출력하거나 저장하지 않았다. local DB URL은 process memory에만 두고 종료 시 제거했다.
- Security: local risk는 B/High이며 Task 9 blocker는 아니다. remote/public deployment, public admin/API activation, public backend DB credentials는 A-021 해결 전 차단한다.
- Accessibility: UI·사용자 동작 무변경.
- Performance/cost: read-only local catalog/source audit만 수행; 외부 API·cloud·새 dependency·비용 0.

## 10. 데이터와 출처 영향

- 공식 데이터: 0 rows, source/approval/verified date 무변경.
- mock/AI 생성: 0 rows, 생성 없음.
- schema/lineage: executable authority `00100`~`00600` 불변; `00700` 미생성.
- verified date: PostgreSQL 17 official docs와 local catalog를 2026-07-17 KST 확인.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-SEC-003 A를 추천한다: exact 22 signatures의 property-only `00700`, matching compensation, catalog/behavior regression.
- 답이 없으면 B/default다: local-only 완료는 허용하지만 public release 관련 경로는 차단하며 `00700`을 구현하지 않는다.
- DoS는 high-confidence plausible, escalation은 conservative medium-confidence inference이며 둘 다 exploit-reproduced가 아니다.
- 공개 API/table/data/retention/dependency/cost는 어느 선택에서도 바꾸지 않는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- graph는 app_api `prosecdef=true` 9개와 app_private 함수 전체 13개의 union으로 고정했다.
- unsafe 판정은 exact `proconfig=['search_path=pg_catalog, pg_temp']`와 비교했다.
- qualification 검사는 alias/string false positive를 source context로 분리했고, dynamic SQL은 catalog `prosrc`의 `EXECUTE` token 0으로 확인했다.

## 13. 인수인계·재현·롤백

### 재현

1. disposable local PostgreSQL을 시작하되 status/DSN payload를 출력하지 않는다.
2. `pg_proc`/`pg_namespace`에서 exact signature, `prosecdef`, `proconfig`, `prosrc`를 read-only로 읽는다.
3. app_api definer 9+app_private 13=22, safe exact config 1, unsafe 21, dynamic SQL 0, backend TEMP true를 확인한다.
4. migration source에서 relation/helper object references의 `app_private.` qualification을 확인한다.
5. 위 PostgreSQL 17 공식 4개 문서를 대조한다.

### 롤백

이 commit은 docs-only이므로 commit을 revert한다. DB compensation, data rollback, secret rotation은 필요 없다.

### 다음 개발자 시작점

Q-SEC-003 인간 결정을 먼저 받는다. A 승인 전 `00700`을 만들지 않는다. A 승인 시 exact 22 signature allowlist와 property-only function search-path update, compensation, RED→GREEN catalog/behavior regression을 별도 계획한다.

## 14. 남은 위험·미해결 질문·다음 단계

- A-021 B/High Open/Deferred; local Task 9 blocker 아님, public release blocker.
- Q-SEC-003 미결정. default는 local-only/public block.
- concrete exploit chain과 실제 영향은 미재현이라 DoS/escalation 신뢰도를 분리 유지한다.
- Task 10은 이 caveat를 제거하거나 DB-001 Done으로 오인하면 안 된다.

## 15. 자체 리뷰

- [x] 요청 충족과 exact 22/21 사실 기록
- [x] docs link/control/stale/secret/package/diff/staged-scope 검증
- [x] source-of-truth/계약/버전 무변경
- [x] 개인정보 원문·secret/DSN 노출 없음
- [x] 구현 노트 INDEX 갱신
