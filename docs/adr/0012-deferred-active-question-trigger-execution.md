# ADR-0012: deferred ACTIVE-question trigger의 제한된 SECURITY DEFINER 실행

- Status: Accepted; implemented and verified
- Date: 2026-07-17
- Deciders: 사용자, Codex
- Related: Q-DB-003, D-028, ADR-0003/0004/0007/0008/0011, DB-001 Task 9

## Context

DB-001 Task 9의 실제 backend login 통합 테스트 8개 중 6개는 통과했지만 승인 경로
2개는 transaction commit에서 실패했다. `app_api.approve_kb_candidate(...)`는
`sejong_schema_owner` 소유 SECURITY DEFINER 함수로 ACTIVE KB, 필수 질문, 후보 연결,
감사를 한 transaction에 만든다. 그러나 두 constraint trigger가 commit 시 호출하는
`app_private.validate_active_kb_question()`은 SECURITY INVOKER다. 호출자인
`sejong_backend`에는 의도적으로 `app_private` USAGE와 base-table 권한이 없으므로
deferred validator가 private table을 읽지 못한다.

안전 catalog probe는 validator `prosecdef=false`, backend private-schema usage=false를
확인했다. 실패한 승인 transaction은 candidate `PENDING_APPROVAL`, activated link NULL,
KB/question/approval-audit 0으로 모두 rollback됐고 synthetic cleanup 8범주도 0이었다.
따라서 데이터 손상이나 권한 과다는 없지만 Task 9 완료를 위해 최소권한 실행 경계를
새 forward migration으로 보정해야 한다.

사용자는 직전 Q-DB-003 질문에서 A를 추천받은 뒤 2026-07-17 KST에
`이거 끝나면 계속해서 진행해줘. 5시간 동안 루프 ㄱㄱ`라고 답했다. 이 응답은 직전
추천안 A의 실행 승인으로 해석한다. 사용자가 문자 `A`를 직접 입력했다고 기록하지 않는다.

## Decision

기존 적용·commit migration `00100`~`00500`은 수정하지 않는다. 새 versioned forward
migration `20260717000600_deferred_active_question_trigger_security.sql`에서 오직
`app_private.validate_active_kb_question()`의 실행 posture만 다음처럼 변경한다.

- 함수는 SECURITY DEFINER로 실행한다.
- owner를 `sejong_schema_owner`로 재확인한다.
- `search_path`를 정확히 `pg_catalog, pg_temp`로 고정해 system catalog를 먼저,
  임시 스키마를 마지막에 검색한다. PostgreSQL 17의
  [SECURITY DEFINER 안전 작성 지침](https://www.postgresql.org/docs/17/sql-createfunction.html#SQL-CREATEFUNCTION-SECURITY)에 따른 D/Internal 예방 보정이다. 로컬에서는 함수 본문의 unqualified `uuid`/`boolean` 선언과 backend의 effective database TEMP 권한이라는 위험 전제를 확인했으며, 실제 승인 경로 exploit/DoS 재현을 완료했다고 단정하지 않는다.
- `PUBLIC`, `anon`, `authenticated`, `sejong_backend`의 직접 EXECUTE를 명시적으로
  revoke한다.
- 함수 본문, constraint trigger의 DEFERRABLE INITIALLY DEFERRED 성질, table, data,
  app_api interface는 바꾸지 않는다.

matching compensation
`20260717000600_deferred_active_question_trigger_security.rollback.sql`은 함수를 SECURITY
INVOKER로 복원하고 owner, 고정 search path, 동일 revoke를 다시 적용한다. 전체 disposable
local compensation 순서는 `00600 → 00500 → 00400 → 00300 → 00200 → 00100`이다.

pgTAP은 exact owner/posture/`proconfig=['search_path=pg_catalog, pg_temp']`,
PUBLIC·browser·backend 직접 EXECUTE 0, `app_private` 전체 함수 중 validator만 sole
definer임을 검증한다. 두 constraint trigger는 exact schema/table/name, `tgenabled=O`,
row-level AFTER event 조합, DEFERRABLE INITIALLY DEFERRED, 함수 binding과
`pg_get_triggerdef`까지 고정한다. backend 권한 검사는 hardcoded allowlist가 아니라
`app_private`의 모든 base/partitioned table과 PostgreSQL 17 `MAINTAIN`을 포함한다. 함수
본문은 `md5(prosrc)=6014f41ed693231e30a9369dd0e394a4`로 불변을 증명한다. 실제 backend
approval integration은 한 성공, 한 안전한 `P1003` loser, ACTIVE OFFICIAL KB 1개, 필수
질문 1개, 후보 연결 1개, approval audit 1개를 행동 증거로 검증한다.

## Security invariants

- `sejong_backend`에 `app_private` USAGE나 base-table 권한을 추가하지 않는다.
- trigger validator를 backend가 직접 호출할 수 없게 direct EXECUTE를 모두 revoke한다.
- `pg_temp`를 search path 마지막에 명시해 호출자 임시 객체가 `pg_catalog` 타입을
  가리지 못하게 한다. backend의 database TEMP 권한 자체는 이번 공개 경계에서 바꾸지 않는다.
- 함수는 dynamic SQL을 추가하지 않고 모든 application object를 schema-qualified로 참조한다.
- native database diagnostic, DSN, 비밀값, 질문·답변 snapshot을 출력하거나 저장하지 않는다.
- repository에서 admin DSN을 사용하거나 권한 실패를 우회하지 않는다.
- 적용된 migration을 수정하지 않고 forward-only correction을 사용한다.

## Alternatives considered

### B — approval 함수 안에서 constraint를 즉시 실행

`approve_kb_candidate` 안에서 `SET CONSTRAINTS ... IMMEDIATE`를 호출하면 definer 함수
문맥에서 검사를 실행할 수 있다. 그러나 approval 함수가 constraint 이름과 transaction
constraint mode에 결합되고 호출자 transaction의 후속 동작에 영향을 줄 수 있어 선택하지
않았다.

### backend private schema/table grant

validator 실행은 쉬워지지만 capability-only 경계와 forced-RLS 최소권한 모델을 약화하므로
거부한다.

### repository/admin-DSN workaround

application이 DB 정책을 우회하고 credential 책임을 넓히므로 거부한다.

### 기존 `00200` 또는 `00400` 수정

applied migration 불변 원칙과 재현 가능한 lineage를 깨므로 거부한다.

## Consequences

- 이 ADR 구현 시 executable lineage는 forward/compensation 각각 6단계가 됐다. 후속 local
  admin·idempotency·public ID migration을 포함한 현재 기준선은 각각 9단계다.
- private trigger function 하나가 제한된 definer surface에 추가되므로 catalog·ACL·동시성
  회귀가 완료 gate가 된다.
- 공개 HTTP 계약, table/data/seed, dependency, retention, 비용, remote/public 배포,
  `/ready=503` 동작은 변하지 않는다.
- `database_schema`, test, documentation version은 구현·최종 gate가 끝나는 Task 10 전까지
  올리지 않는다.

## Rollback and recovery

disposable local DB에서 `00600` compensation을 실행하면 validator는 SECURITY INVOKER로
복원되고 owner, exact `search_path=pg_catalog, pg_temp`, direct EXECUTE revocation, body hash,
두 trigger binding과 backend private privilege 0도 유지돼야 한다. 이어 단일 pgTAP 호출로
`00500` 기준선의 274 assertions를 다시 통과해야 한다. 이후 fresh reset은 6개 forward
migration과 새 pgTAP을 다시 적용한다. remote DB, 실제 데이터, Docker volume 삭제에는 이
compensation을 사용하지 않는다.

문서 결정만 철회할 때는 결정 동기화 commit을 revert한다. 이미 `00600`이 공유된 뒤에는
그 migration을 수정하지 않고 새 reviewed forward migration으로 교정한다.

## Validation

- 새 pgTAP catalog/ACL/security file의 RED→GREEN
- runner compensation order `00600 → 00500 → 00400 → 00300 → 00200 → 00100`
- `00600`-only compensation 뒤 invoker/owner/proconfig/ACL/body/trigger/private-privilege
  전체 posture와 기존 274/274 기준선
- fresh six-migration replay와 실제 full pgTAP emitted total
- real backend integration 8/8와 concurrent approval 단일 성공/단일 audit
- full disposable DB gate, no-Docker root gate, Ruff/Mypy, secret/package/diff/scope
- synthetic row 8범주 0과 독립 spec/quality review

## Implementation result — 2026-07-17 KST

- correction commit `5266abc`은 새 `00600` forward/compensation/pgTAP과 stale
  `002_invariants_test.sql` search-path assertion 동기화, 정확히 4개 test/SQL
  path만 포함했다. 기존 immutable migration `00100`~`00500`은 수정하지 않았다.
- Task 9 commit `04a944f`과 review fix `228d8cb`은 runner/tooling/integration
  3개 path만 변경했다. cleanup은 identifier-scoped 단일 admin transaction으로
  강화됐다.
- historical RED는 real integration 6 pass/2 fail, 새 `006` pgTAP은 collation
  correction 뒤 의미 있는 2/8 failure, tooling은 expected RED 2개였다.
- GREEN은 focused `006` 8/8, full pgTAP `Files=6, Tests=282`, compensation full
  posture PASS, compensated prior baseline `Files=5, Tests=274`, retained diagnostic
  branch 8/8와 제거 뒤 8/8이다.
- full gate는 exact `006→005→004→003→002→001`, absence, reset/replay, 두 번째
  pgTAP, integration을 모두 통과했다. tooling 16/16, Ruff/Mypy/root/API/web/
  contract/secret/package/diff와 synthetic 8-table zero도 PASS다.
- initial specification review Important 1/Minor 1은 `228d8cb`로 보정됐다. final
  specification과 quality review는 각각 Critical/Important/Minor 0/0/0이다.
- A-021은 local Task 9 blocker가 아니지만 public-release blocker다. Task 10은
  이 caveat와 모든 현재 version 축을 보존해야 한다.
