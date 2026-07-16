# IMP-20260717-001 — DB-001 Task 6 atomic candidate workflow

- Date/Time (KST): 2026-07-17T01:07:14+09:00 (2026-07-16 시작 작업이 자정을 넘어 마감됨)
- Task ID: DB-001-T6
- Type: implementation
- Status: Done
- Author/Agent: 사용자 결정자, Codex `/root` coordinator, Task 6 구현·검토 agent
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `dee1ccb31059a38042b041e9f457cd1ba62ffbe3`
- Implementation commits: `cd18ff69818c82c266c34b48dc5e7abb9838777b`, semantic review fix `2ba566d39e6b68445d59a335a98202c79e4d8ba1`, formatting-only gate fix `72b7ab15ee48dfdb20b088954ce7f62741ed50b9`
- Related plan/ADR/RFP: [DB-001 plan](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md), [ADR-0011](../adr/0011-layered-database-and-backend-enforcement.md), [D-026/D-027](../decisions/DECISION_LOG.md), [RFP matrix](../source-of-truth/RFP_MATRIX.md) F-11/F-12/F-13, [Task 6 report](../../.superpowers/sdd/task-6-report.md), [TASKS](../../TASKS.md) DB-001

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 Q-SEC-002=A와 Q-WF-001=A를 결정하고 승인된 DB-001 계획의 구현을 계속하도록 요청했다. Task 6 범위는 별도 실패 사유 확인 capability, 후보 작성·제출, 작성자와 다른 승인자의 승인·반려, ACTIVE KB 전환, 메타데이터 전용 감사 이력을 하나의 DB 원자 경계로 만드는 것이다.

### Acceptance Criteria

- 다섯 backend-only `SECURITY DEFINER` interface와 exact ACL/owner/search path를 강제한다.
- `NEW → REASON_CONFIRMED → DRAFTED → PENDING_APPROVAL → APPROVED/REJECTED` 전이를 역할·작성자 분리·고정 SQLSTATE로 제한한다.
- 승인 시 ACTIVE OFFICIAL KB, 첫 질문 예시, 후보 링크, 감사행이 전부 성공하거나 전부 롤백된다.
- 원문 질문·답변 snapshot 없이 허용된 action/target/status/changed fields/comment만 감사한다.
- 동시 확인·생성·승인·replay가 deadlock, 중복 활성화, native diagnostic 누출 없이 직렬화된다.
- 004 compensation 뒤 Task 1~5가 보존되고 reset/replay 뒤 전체 결과가 동일하다.
- pgTAP, 두 연결 concurrency, lint/type/secret/diff, 독립 code review가 통과한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 Q-SEC-002/Q-WF-001을 결정했고, 구현 agent가 TDD로 작성했으며, 독립 reviewer와 root가 검토·재검증했다. |
| When — 언제 | 2026-07-16 KST 구현 시작, 2026-07-17 KST 문서 마감; worktree 작업이 자정을 넘었다. |
| Where — 어디서 | `.worktrees/db-001-layered-enforcement`, local Docker Desktop/Supabase PostgreSQL, `supabase/migrations`, `supabase/tests/database`, `database/rollbacks`, `scripts`. |
| What — 무엇을 | 00400 workflow migration·compensation, 승인 pgTAP, capability/lineage 회귀, 영구 두 연결 concurrency probe를 구현했다. |
| Why — 왜 | 운영자의 사유 정정과 후보 승인에서 자기 승인·중복 활성화·부분 성공·원문 감사·동시성 우회를 DB 자체가 막도록 하기 위해서다. |
| How — 어떻게 | 실패 테스트 RED→최소 SQL GREEN→독립 review→5/62 및 deadlock 재현→lock order/monotonic lineage/고정 collision 오류 수정→root reset/rollback/replay 검증으로 수행했다. |
| How much — 어느 정도 | forward migration 1, compensation 1 및 선행 compensation guard 1, DB test file 3개(002/003 수정, 004 추가), concurrency script 1개 수정, workflow interface 5개, 최종 pgTAP 234개, forward/replay 4개와 compensated 3개 concurrency scenario; 외부 비용 0원. |

## 3. 시작 전 상태

- 관련 파일: `20260716000100~00300` immutable migrations, Task 4 lineage trigger, Task 5 role/RLS/capability/retention, 승인 DB plan과 D-026/D-027.
- 기존 동작: 실패 질문·후보·감사 table은 있었지만 실패 사유 확인, 후보 생성/제출, 승인/반려 capability와 ACTIVE 전환이 없었다. `00100~00300`는 이미 적용·review된 immutable 기준선이었다.
- 발견한 충돌/부채: 초기 구현 review에서 replay와 confirmation의 반대 lock order가 deterministic `40P01`을 만들었고, confirmed failure를 `NEW`로 되돌릴 수 있었으며, deterministic KB ID collision이 native `23505` 진단을 노출했다.
- Git 상태: clean base `dee1ccb`; 원격 저장소 없음; 허용 범위 밖 계약·환경·seed·dependency 변경 없음.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-SEC-002 | Human resolved | non-superuser migration runner와 안전 역할 검증 | A, D-026: fail-closed model 유지 | 004 interface owner/ACL은 Task 5 role 경계를 그대로 사용 |
| Q-WF-001 | Human resolved | 실패 사유 확인 전이의 capability 경계 | A, D-027: 별도 backend-only interface | event 자동 분류는 immutable, failure만 운영자 확인/정정 |
| Public/API | Fixed | 공개 wire 계약 변경 여부 | 변경 없음 | OpenAPI/API version 유지 |
| Official seed | Deferred | 승인 공식 row 입력 | DATA-001/PM 승인 전 0 rows | 이번 migration은 schema/workflow만 제공 |
| Task 7 reads | Planned | ACTIVE+OFFICIAL 시민 read/index | `00500`에서 구현 | Task 6에서는 만들지 않음 |

## 5. 설계 결정과 대안

### 선택

- `confirm_failed_question_reason(uuid,text,text,text)`를 후보 생성과 분리해 operator 확인 자체를 감사한다.
- 모든 workflow write는 backend-only 함수로만 열고 backend의 대상 table 직접 DML은 계속 0으로 유지한다.
- failure/candidate row lock과 event-first compatible `FOR SHARE` lineage lock으로 replay와 workflow lock order를 맞춘다.
- 승인 KB ID는 candidate UUID의 32자리 대문자 hex를 사용해 결정적으로 생성하되, 해당 단일 INSERT의 unique violation은 고정 `P1003`으로 변환한다.
- 감사 changed fields는 caller 입력이 아니라 서버가 실제 변화에서 canonical 배열로 만든다.

### 이유

사유 확인과 후보 생성을 분리해야 사람의 판단 시점과 변경 필드를 추적하면서, ineligible 정정 뒤 후보 생성을 차단할 수 있다. DB 함수 하나의 transaction에 활성화 네 쓰기를 묶으면 API 장애나 동시 요청에서도 부분 상태가 남지 않는다. 고정 SQLSTATE/message는 운영 데이터나 식별자가 diagnostic에 새는 경로를 없앤다.

### 고려했지만 선택하지 않은 대안

- event 분류값 자체 수정: 최초 자동 분류 계보를 잃으므로 제외했다.
- backend table 직접 DML: RLS/상태 머신 우회 면적이 커져 제외했다.
- 후보 생성 시 암묵적 사유 확인: 확인 audit와 eligibility 재도출이 불명확해 제외했다.
- native unique/deadlock 오류 전달: 내부 ID·constraint 노출과 불안정 계약 때문에 제외했다.
- 00100~00300 forward migration 수정: 적용 migration 불변 원칙 때문에 새 00400만 사용했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `supabase/migrations/20260716000400_candidate_workflow.sql` | 다섯 workflow function, 상태/action shape, audit allowlist, lineage/lock 보강, exact owner/ACL | 사유 확인부터 승인/반려까지 원자·역할 분리 경계 |
| `database/rollbacks/20260716000400_candidate_workflow.rollback.sql` | 다섯 interface와 Task 6 trigger/constraint를 제거하고 exact Task 4 lineage 정의 복구 | Task 5 기준선으로 안전한 부분 보상 |
| `database/rollbacks/20260716000300_capabilities_and_functions.rollback.sql` | 004가 남아 있으면 `WORKFLOW_COMPENSATION_REQUIRED`로 mutation 전 중단 | 역순 보상 강제 |
| `supabase/tests/database/003_capabilities_test.sql` | exact workflow allowlist/ACL 및 direct DML denial | 권한의 과다·누락을 catalog에서 검증 |
| `supabase/tests/database/004_approval_test.sql` | state/role/comment/audit/rollback/collision/lineage 62 assertion | 승인 workflow 기능·비누출·원자성 회귀 |
| `supabase/tests/database/002_invariants_test.sql` | 004 존재 여부에 따른 exact 4-column/3-column trigger catalog 검증 | forward와 compensated phase 모두 비공허하게 검증 |
| `scripts/test_database_concurrency.py` | 004 존재 시 replay-vs-confirm 포함 4 scenario, 보상 뒤 기존 3 scenario | 실제 두 연결 lock order/deadlock 회귀 자동화 |

### 데이터 흐름/상태 변화

`interaction_events`의 최초 자동 `fallback_reason`은 바뀌지 않는다. OPERATOR가 NEW failure를 확인하면 failure에만 확인/정정 reason, eligibility, `REASON_CONFIRMED`가 저장되고 metadata-only audit 1행이 생성된다. eligible INSUFFICIENT_GROUNDING failure만 DRAFTED candidate로 이어지고, creator가 제출해 PENDING_APPROVAL이 된다. 다른 APPROVER만 comment와 함께 승인할 수 있으며 ACTIVE OFFICIAL KB, 대표 질문 1개, APPROVED candidate link, 승인 audit이 한 transaction으로 생성된다. 반려는 KB를 만들지 않고 candidate와 audit만 함께 갱신한다.

### 오류·빈 상태·롤백

role/ownership은 `P1001`, 자기 검수는 `P1002`, 누락·중복·잘못된 상태는 `P1003`, 내용/comment 불완전은 `P1004`, 허용되지 않은 origin은 `P1005`, 잘못된 사유/lineage는 `P1010`의 고정 message로 실패한다. 004 compensation은 workflow interface/Task 6 trigger를 제거하고 Task 4 세 열 trigger와 `FOR UPDATE` validator를 복구한다. 003 compensation은 004가 남아 있으면 mutation 전에 중단한다. 공식 seed가 없으므로 빈 DB에서도 schema와 테스트 fixture만으로 재현된다.

## 7. 버전 전후

매니페스트의 모든 축은 Task 6 부분 구현 동안 유지한다. DB/test/repository 최종 baseline 승격은 DB-001 Task 10에서 한 번만 수행한다.

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 범위 변경 없음 |
| Repo guidance | 1.4.0 | 1.4.0 | 최종 Task 10에서 승격 |
| Application | 0.1.0 | 0.1.0 | 제품 코드/wire 변경 없음 |
| Web | 0.1.0 | 0.1.0 | 변경 없음 |
| API | 2.0.1-draft | 2.0.1-draft | 공개 계약 변경 없음 |
| Shared contracts | 0.2.1 | 0.2.1 | 변경 없음 |
| DB schema | 0.2.0-draft | 0.2.0-draft | 부분 migration; 최종 Task 10에서 승격 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | persistent row/seed 없음 |
| Mock data | 0.0.0-not-populated | 0.0.0-not-populated | persistent row/seed 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 0.0.2-deepseek-v4-flash-selected | LLM 미사용 |
| Test suite | 0.4.2-readiness-contract | 0.4.2-readiness-contract | 부분 suite; 최종 Task 10에서 승격 |
| Docs | 2.3.14 | 2.3.14 | Task 5와 같은 intermediate-note 정책 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| 초기 `.tools/supabase/v2.109.1/supabase.exe test db` | expected RED, 001~003 통과 후 004 interface 부재로 exit 1 | 새 workflow assertion 실패 | Task 6 report |
| review focused 004 pgTAP | expected RED: lineage/lock/reversal/collision 5개 실패 | 5/62 실패 | Task 6 report review fix |
| deterministic replay-vs-confirm probe | expected RED: native `40P01`, `REPLAY_CONFIRM_DEADLOCK` | 2 connections | Task 6 report review fix |
| focused 004 pgTAP | PASS | 62/62 | Task 6 report |
| forward complete pgTAP | PASS | 4 files, 234/234 | Task 6 report/root terminal |
| forward concurrency | PASS | 4 scenarios, 2 connections | Task 6 report/root terminal |
| 003 compensation with 004 present | expected fail-closed, no mutation | `WORKFLOW_COMPENSATION_REQUIRED` | root terminal |
| 004 compensation + catalog proof | PASS; workflow functions/Task 6 triggers absent, Task 4 exact definitions restored | implementer proof `t|t|t|t`; root는 guard/rollback·172/172·concurrency 3을 독립 확인 | Task 6 report; root terminal |
| compensated pgTAP | PASS | 3 files, 172/172 | Task 6 report/root terminal |
| compensated concurrency | PASS | 3 scenarios, 2 connections | Task 6 report/root terminal |
| fresh reset/replay complete pgTAP | PASS | 4 files, 234/234 | Task 6 report/root terminal |
| replay concurrency | PASS | 4 scenarios, 2 connections | Task 6 report/root terminal |
| repository tooling tests | PASS | 55 passed, 1 skipped, 68 subtests | Task 6 report |
| Ruff check/format, mypy, secret scan, `git diff --check` | PASS | formatting/type/secret/whitespace finding 0 | Task 6 report/root terminal |
| post-review formatting gate | last line wrapping을 canonical Ruff format으로 정리한 뒤 Ruff format/check·lint·mypy·tooling target·concurrency 재통과 | semantic change 0; concurrency 4 PASS | commit `72b7ab1`, root terminal |
| independent code review | clean | Critical/Important/Minor 0 | reviewer report |

검증 중 두 번의 probe 명령 조합이 PowerShell/로컬 CLI 경로 quoting 때문에 harness 단계에서 실패했다. 두 실패는 제품 SQL이나 테스트 실패가 아니며 secret을 출력하지 않았고, 성공한 004 rollback 이외의 DB mutation을 만들지 않았다. 명령 구성을 바로잡은 뒤 위 compensation·concurrency·replay 결과를 다시 확보했다.

### 미실행 검증과 이유

- remote Supabase, 공개 배포, 실제 API/LLM 호출: local-only 승인 범위 밖이며 이번 DB workflow 검증에 불필요하다.
- 실제 운영 데이터 승인: DATA-001/PM 승인 전이어서 persistent row 0을 유지했다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문 원문·답변 snapshot을 audit에 넣지 않고, failure reason은 parent event의 최초 자동 분류와 분리해 metadata만 추적한다. `.env`와 DeepSeek key를 읽거나 출력하지 않았다.
- Security: 다섯 함수는 schema owner 소유, `SECURITY DEFINER`, `search_path=pg_catalog`, backend-only EXECUTE다. anon/authenticated/PUBLIC execute와 backend direct 대상-table DML은 0이다. 작성자 자기 승인, 상태 우회, native diagnostic leakage를 DB에서 막는다.
- Accessibility: DB-only 변경이라 시민/관리자 UI와 접근성 동작 변화가 없다.
- Performance/cost: 대상 row lock과 indexed UUID 조회 범위의 작은 transaction만 추가했다. 두 연결 probe에서 lock timeout/deadlock이 없었고, DeepSeek·외부 API를 호출하지 않아 비용 0원이다.

## 10. 데이터와 출처 영향

- 공식 데이터: persistent 공식 row를 추가·수정하지 않았다. OFFICIAL origin은 workflow invariant일 뿐 실제 출처 승인은 DATA-001에서 수행한다.
- mock/AI 생성: pgTAP/concurrency의 명시적 합성 fixture는 reset/rollback으로 제거되며 persistent mock row와 tracked seed는 0이다. AI 생성 데이터를 공식 데이터로 저장하지 않았다.
- schema/lineage: migration `00400`이 event 최초 분류 immutable, failure 확인/정정, candidate/ACTIVE KB one-to-one lineage와 metadata audit shape를 강제한다.
- verified date: 2026-07-17 KST local disposable PostgreSQL.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-SEC-002=A, Q-WF-001=A가 구현됐다. 공개 API, production provider, 비용, retention 정책, 공식 데이터는 변경하지 않았다.
- 승인으로 생기는 KB는 `OFFICIAL` origin이지만, 실제 시민 검색에는 별도 PM 승인 공식 seed와 Task 7 ACTIVE+OFFICIAL read가 필요하다.
- migration 004는 부분 단계다. remote 적용·배포·데이터 migration은 승인되지 않았으며 실행하지 않았다.
- 다음 인간 gate는 DATA-001 공식 KB/기관 데이터의 PM 승인이다. 목표는 2026-07-20로 유지된다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- confirmation changed fields는 실제 변화에 따라 canonical `status`, `fallback_reason`, `candidate_eligible` 순서로 서버가 생성한다.
- lineage validator는 parent event에 `FOR SHARE`, candidate/failure state writer는 대상 row에 `FOR UPDATE`를 사용해 replay와 lock order를 맞춘다.
- approval deterministic public ID collision은 KB INSERT 한 곳의 `unique_violation`만 잡아 `P1003`으로 변환한다.
- 002 catalog test는 exact 004 function 존재 여부에 따라 4-column forward와 3-column compensated trigger를 각각 엄격히 검증한다.

## 13. 인수인계·재현·롤백

### 재현

Docker Desktop을 켜고 worktree root에서 다음을 실행한다.

```powershell
.tools/supabase/v2.109.1/supabase.exe db reset --local
.tools/supabase/v2.109.1/supabase.exe test db
```

concurrency probe 전에는 `scripts/README.md`와 `scripts/verify_database.ps1`의
`Read-DatabaseUrlFromStatus` 경계를 따라 admin DSN을 stdout에 출력하지 않고
process environment에만 넣는다. PowerShell에서 안전하게 재현하는 절차는 다음과 같다.

```powershell
$saved = $env:SEJONG_ADMIN_DATABASE_URL
try {
    $status = & '.tools/supabase/v2.109.1/supabase.exe' status -o env 2>$null
    $line = $status | Where-Object { $_.StartsWith('DB_URL=', [System.StringComparison]::Ordinal) } | Select-Object -First 1
    if ($null -eq $line) { throw 'LOCAL_ADMIN_DSN_UNAVAILABLE' }
    $value = $line.Substring(7).Trim()
    if ($value.Length -ge 2 -and $value.StartsWith('"') -and $value.EndsWith('"')) {
        $value = $value.Substring(1, $value.Length - 2)
    }
    if ([string]::IsNullOrWhiteSpace($value)) { throw 'LOCAL_ADMIN_DSN_UNAVAILABLE' }
    $env:SEJONG_ADMIN_DATABASE_URL = $value
    & 'apps/api/.venv/Scripts/python.exe' -B scripts/test_database_concurrency.py
    if ($LASTEXITCODE -ne 0) { throw "CONCURRENCY_FAILED_$LASTEXITCODE" }
} finally {
    if ($null -eq $saved) { Remove-Item Env:SEJONG_ADMIN_DATABASE_URL -ErrorAction SilentlyContinue }
    else { $env:SEJONG_ADMIN_DATABASE_URL = $saved }
}
```

변수 자체를 출력하지 않는다. 기대 결과는 pgTAP 234/234와 concurrency 4
scenarios/2 connections다.

### 롤백

Task 7의 `00500`이 존재하면 먼저 005 compensation을 적용한다. 다음으로 `scripts/run_database_sql.py`를 통해 `database/rollbacks/20260716000400_candidate_workflow.rollback.sql`을 적용한다. 004 workflow 함수/trigger 부재와 Task 1~5 pgTAP 172/172, compensated concurrency 3개를 확인한다. 004가 남은 상태에서 003 compensation은 `WORKFLOW_COMPENSATION_REQUIRED`로 실패해야 정상이다. 복구는 fresh `db reset --local`로 00100~00400을 재적용하고 234/234와 4 scenario를 다시 확인한다.

### 다음 개발자 시작점

Task 7의 `20260716000500_indexes_and_read_interfaces.sql`과 matching compensation/test를 TDD로 시작한다. 시민 read는 ACTIVE+OFFICIAL만 반환하고 application schema나 private table을 직접 노출하지 않아야 한다. `00100~00400` forward migration은 수정하지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- Task 7 ACTIVE+OFFICIAL citizen read/index, Task 8 backend adapter, Task 9 permanent full integration/concurrency gate, Task 10 rollback/replay/version/handoff가 남았다.
- 실제 승인 official KB/office row는 0이므로 `/ready=503`이 정상이다.
- remote migration, backup/restore, 공개 배포는 여전히 별도 인간 승인과 후속 작업이 필요하다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
