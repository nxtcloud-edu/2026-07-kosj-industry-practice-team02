# IMP-20260716-006 — DB-001 layered enforcement

- Date/Time (KST): 2026-07-16
- Task ID: DB-001
- Type: implementation
- Status: Blocked — Task 10 Q-SEC-005/A-023 IPv6 local port boundary; actual DB review, version promotion, and completion commit pending
- Author/Agent: Codex `/root` coordinator with task-specific implementation/review agents
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `cf76b17`
- Related plan/ADR/RFP: `docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md`, `docs/superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md`, ADR-0008/0011/0012, D-018/D-025/D-026/D-027/D-028, RFP F-11/F-12/F-13

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 `계획 승인, 구현 시작`이라고 명시해 승인된 DB-001 실행계획의 local-only 구현을 허가했다. 이전 선호에 따라 코딩은 task별 fresh agent가 담당하고 root가 명세·품질 review와 중요한 명령·결정을 통제한다.

### Acceptance Criteria

- checksum-pinned project-local Supabase CLI와 PostgreSQL-only local config를 만든다.
- 다섯 기존 immutable migration과 승인된 새 `00600`을 포함한 6단계 역순 compensation을 재현한다.
- private schema, RLS/GRANT, ACTIVE+OFFICIAL read, 원자 승인, retention, audit invariants를 DB에서 강제한다.
- 같은 구조 규칙을 lazy typed FastAPI repository 경계에서 중복 검증한다.
- pgTAP, API unit/integration, concurrency, reset/rollback/replay, root gate를 통과한다.
- 공식 seed·공개 API·readiness 200·remote/public·새 production dependency는 만들지 않는다.
- 실제 결과, 버전, 보안·개인정보·데이터·rollback·handoff를 이 note와 test report에 남긴다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 승인자, Codex root coordinator, task별 구현 agent, 명세 reviewer, 품질 reviewer |
| When — 언제 | 2026-07-16 KST 시작; Task 10 closeout 2026-07-17 KST |
| Where — 어디서 | `.worktrees/db-001-layered-enforcement`, local Docker Desktop/Supabase PostgreSQL, `apps/api`, `supabase/`, `database/`, `scripts/` |
| What — 무엇을 | DB-001 executable local schema, capability boundary, tests, rollback/replay, lazy typed backend adapter |
| Why — 왜 | 승인·공식 데이터·보관·개인정보 규칙이 API 실수·직접 SQL·동시 요청으로 우회되지 않게 하기 위해 |
| How — 어떻게 | TDD RED→GREEN, task별 commit, 명세 review 후 품질 review, 최종 독립 verification |
| How much — 어느 정도 | 6 forward migrations, 6 compensation files, 6 pgTAP suites/282 assertions, 9 DB interfaces, Task 8 API boundary 10 files, API 156 tests+4 subtests, Task 9 integration 8/8, 당시 tooling 16/16, synthetic 8-table zero, local-only 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: approved DB-001 spec/plan, ADR-0011, logical DB draft, root verify, API architecture tests.
- 기존 동작: Supabase CLI/config/migration/DB tests 없음; `/health=200`, no seed `/ready=503`.
- 발견한 환경 차이: `.tools/`가 Git ignored라 새 worktree에 repo-local uv가 없었고 첫 verify가 `PREFLIGHT-UV`에서 종료됨.
- 해결: main workspace의 검증된 ignored uv 0.11.28 도구 디렉터리만 worktree `.tools/uv/`에 복구.
- Git 상태: clean base `cf76b17`; 원격 저장소 없음; branch `codex/db-001-layered-enforcement`.
- 시작 전 감사 비밀 경계: ignored `apps/api/.env`의 내용·길이·hash·DeepSeek key를 열거나 출력하지 않음. 이후 승인된 provisioning은 원자적 `DATABASE_URL` 교체를 위해 파일 전체 bytes를 읽지만 non-target 값을 해석·출력·별도 복사하지 않는다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| DB-001 plan gate | Human | 실행 승인 | 2026-07-16 승인 | Task 0~10 실행 허용 |
| CLI pin | Internal verified | stable Windows x64 | v2.109.1 + approved SHA-256 | local tooling |
| public/remote | Human deferred | remote link/push/deploy | 승인되지 않음 | 실행 금지 |
| official data | Human/PM | 승인 seed | DATA-001 전 0 rows | readiness 503 |
| worktree uv | Internal | ignored tool missing | verified 0.11.28 copy | baseline only |
| Q-SEC-002 | Resolved — Human | non-superuser role replay와 privileged auto-downgrade 중 선택 | A: 현재 fail-closed non-superuser model 유지 / D-026 | Task 5 acceptance 완료 |
| Q-WF-001 | Resolved — Human | `NEW → REASON_CONFIRMED` 전이 capability 경계 | A: 별도 backend-only capability / D-027 | Task 6 구현 가능 |
| Q-DB-003 | Resolved — Human | backend approval commit의 deferred ACTIVE-question trigger 실행 권한 | A / D-028 / ADR-0012: 새 `00600`에서 validator만 SECURITY DEFINER+owner/exact `search_path=pg_catalog, pg_temp`/revoke 검증, compensation은 INVOKER | migration/rollback/pgTAP/Task 9; API·data·dependency·remote 불변 |

## 5. 설계 결정과 대안

### 선택

승인 plan을 그대로 subagent-driven 방식으로 수행한다. 각 implementation task 뒤 별도 명세 reviewer와 품질 reviewer 승인을 모두 받아야 다음 task로 이동한다.

### 이유

DB 권한과 state transition은 task 간 의존성이 강해 한 task의 drift가 뒤 단계로 번지기 전에 검출해야 한다.

### 고려했지만 선택하지 않은 대안

- main에서 직접 구현: 격리 원칙 때문에 제외.
- parallel implementation agents: 동일 migration/script 충돌 위험 때문에 제외.
- 기존 기준선 실패 무시: 검증 근거가 없어 제외; uv 환경을 복구하고 fresh 24/24를 확보.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| plan/TASKS/이 note | 승인·In Progress·baseline 기록 | Task 0 실행 gate |
| `scripts/supabase-cli.version.json` | 공식 Windows x64 CLI 2.109.1의 release·게시시각·asset·byte size·URL·SHA-256 exact pin | upstream 변경과 공급망 drift 차단 |
| `scripts/bootstrap_supabase.ps1` | PS 5.1 local-only 다운로드/검증/임시 sibling 설치/정확 버전 확인/소유 경로 정리와 안정 출력 | 원격 프로젝트 동작 없이 재현 가능한 로컬 CLI 경계 |
| `scripts/tests/test_supabase_tooling.py` | pin·인자·CWD·missing binary·잘못된 child version·동일 크기 오해시·비승인 source를 offline subprocess로 검증 | 정적 문자열 검사만으로는 놓치는 실제 PowerShell 경계 회귀 차단 |
| `.gitignore`, `scripts/README.md`, scaffold test | Supabase 임시 경로 ignore와 local-only 사용 경계 | 산출물 커밋·원격 명령 오용 방지 |
| `supabase/config.toml`, `supabase/seed.sql` | pinned CLI 생성본에서 Postgres 외 서비스와 seed를 끄고 application schema를 Data API에서 제외 | local DB-only·공식 데이터 0 경계 |
| `scripts/provision_local_database_login.py` | 제한 login 생성/회전, capability grant, 다른 env byte를 보존하는 same-directory atomic `DATABASE_URL` 교체 | 실제 provider key 손상 없이 backend credential 제공 |
| `scripts/run_database_sql.py` | `database/` 내부의 명시 파일만 파일별 transaction으로 실행 | 검토된 compensation/absence SQL만 허용 |
| `scripts/verify_database.ps1` | Docker·CLI·Python preflight, exact `db start`, reset→pgTAP→rollback→absence→replay→integration 순서, child 비노출·timeout·env 복원 | PostgreSQL-only persistent runtime과 Task 3~9 결과를 한 번에 검증할 explicit gate |
| API/scripts README와 tooling tests | 실행 시점·local-only·empty seed·DB gate 제한 및 failure behavior 문서화 | 신규 개발자 오용·secret 노출 방지 |
| `supabase/migrations/20260716000200_invariants_and_lineage.sql` | text/JSON/status/provenance CHECK, lineage trigger, ACTIVE-question deferred constraint, `updated_at` trigger, `READ COMMITTED` fail-closed guard | 잘못된 행·교차 테이블 불일치·stale snapshot 우회 차단 |
| `database/rollbacks/20260716000200_invariants_and_lineage.rollback.sql` | Task 4 trigger→function→constraint→validator 역순 보상 | Task 3의 schema·8 table을 보존한 안전한 부분 rollback |
| `supabase/tests/database/002_invariants_test.sql` | 명시적 MOCK fixture 기반 62개 pgTAP invariant assertion | text/JSON/status/source/lineage/rollback 계약 재현 |
| `scripts/test_database_concurrency.py` | 두 DB 연결로 ACTIVE-question, event/failure, failure/candidate stale-snapshot 3개 시나리오 검증 | 기본 격리수준 계약과 deadlock 회귀를 실제 transaction으로 검증 |
| `supabase/migrations/20260716000300_capabilities_and_functions.sql` | safe roles·ownership·ACL·forced RLS/policies, interaction recording, private/public retention과 replay fix | backend-only capability와 privacy/provenance/idempotency 강제 |
| `database/rollbacks/20260716000300_capabilities_and_functions.rollback.sql` | Task 5 capability·policies·roles를 역순 제거하고 FORCE만 해제 | lower-layer compensation 전 안전한 local rollback |
| `supabase/tests/database/003_capabilities_test.sql` | exact policy/function allowlist, role denial, 상태 matrix, replay, retention, diagnostic nonleak 78 assertions | privilege와 privacy 회귀의 비공허 검증 |
| `supabase/migrations/20260716000400_candidate_workflow.sql` | 사유 확인, 후보 작성·제출, 별도 승인·반려, ACTIVE 전환, metadata audit와 exact ACL/lock order | 관리자 개선 workflow를 원자·backend-only DB capability로 강제 |
| `database/rollbacks/20260716000400_candidate_workflow.rollback.sql` | Task 6 함수/trigger/constraint를 제거하고 exact Task 4 lineage 정의 복구 | Task 5 기준선으로 안전한 부분 보상 |
| `supabase/tests/database/004_approval_test.sql` | workflow 상태·역할·comment·audit·atomic rollback·diagnostic 62 assertions | 승인/반려 및 실패 경로의 비누출·비부분성 검증 |
| `supabase/tests/database/002_invariants_test.sql`, `scripts/test_database_concurrency.py` | forward/compensated trigger catalog과 replay-vs-confirm 포함 영구 두 연결 probe | lock order·단조 lineage·rollback 회귀 자동화 |
| `supabase/migrations/20260716000500_indexes_and_read_interfaces.sql` | ACTIVE+OFFICIAL KB와 OFFICIAL region+intent office를 위한 exact five indexes·two backend-only read functions | 시민 근거/기관 결과를 승인된 stored metadata로 제한 |
| `database/rollbacks/20260716000500_indexes_and_read_interfaces.rollback.sql` | 두 read function과 다섯 index만 역순 제거 | Task 6 기준선을 보존하는 부분 보상 |
| `supabase/tests/database/005_citizen_reads_test.sql` | exact catalog/ACL/index와 상태·출처·정렬·고정 diagnostic 40 assertions | mock/non-active/private 열 노출 회귀 차단 |
| `apps/api/src/sejong_ai_api/db/{__init__,errors,models}.py` | safe package export, SQLSTATE-only stable error mapping, exact enum·frozen/slotted typed models·structural validators | native DB diagnostic 누출과 잘못된 backend input을 pool 접근 전 차단 |
| `apps/api/src/sejong_ai_api/db/{pool,repository}.py` | unopened explicit pool factory, repository protocol, fixed 9-SQL psycopg adapter, typed immutable reads·transactional writes | import/env side effect 없이 backend-only capability 호출 경계 고정 |
| `apps/api/tests/db/`, `apps/api/tests/test_architecture.py` | DB focused 112 passed(81+31), 전체 API 156 passed+main-import 4 subtests | SQL/parameter/transaction/mapping과 driver/pool/env lazy-import 회귀 차단 |
| Task 9 세 owned 파일 | real-DB integration 8개와 exact reset→pgTAP→5-file rollback→absence→reset/replay→pgTAP→integration runner gate | repository·권한·동시성·retention·rollback/replay를 실제 backend login으로 검증; 이 행은 Task 9A 전 작업 트리 상태를 기록 |

### 데이터 흐름/상태 변화

Task 0~2에서는 DB row/container/schema 변화가 없다. Task 2에서 ignored `.tools/supabase/v2.109.1/`에 공식 archive를 설치했고, Task 3에서 local PostgreSQL을 기동해 `app_private`/`app_api`, 7 enum, 8 table을 첫 migration으로 생성했다. Task 4는 두 번째 migration으로 table-level CHECK, validator, `updated_at`, source/lineage/ACTIVE-question trigger를 추가했다. Task 5는 세 번째 migration으로 safe capability roles, ownership/ACL, 여덟 forced-RLS table과 owner-only policies, `record_interaction`, retention helper/wrapper를 추가했다. Task 6는 네 번째 migration으로 event의 최초 자동 사유를 보존하면서 failure를 확인/정정하고, eligible failure에서 후보 작성·제출·별도 승인/반려·ACTIVE OFFICIAL KB 전환·metadata-only audit을 원자적으로 수행하는 다섯 backend-only interface를 추가했다. Task 7은 다섯 번째 migration으로 ACTIVE+OFFICIAL KB와 OFFICIAL region+intent office만 반환하는 두 backend-only read interface와 exact five indexes를 추가했다. Task 8은 DB/schema/data를 변경하지 않고 이 9개 capability를 safe typed model·sqlstate-only error·lazy pool·fixed SQL repository로 연결했다. Task 9의 최초 real-DB 검증은 6/8에서 deferred validator 권한 경계를 발견했고 transaction의 원자 rollback을 증명했다. 새 여섯 번째 `00600` migration으로 validator 하나만 보정한 뒤 retained diagnostic branch와 branch 제거 후 integration이 각각 8/8을 통과했다. public route는 아직 연결하지 않았고 tracked seed는 설명 주석뿐이며 cleanup 뒤 공식/mock persistent row는 0이다.

### 오류·빈 상태·롤백

첫 verify 도구 호출은 repo-local uv 부재로 `PREFLIGHT-UV` 종료, 두 번째 호출은 tool timeout 124, 세 번째 fresh 호출은 143.6초에 24/24 통과했다. Task 1 검증 중 root가 1초 제한으로 시작한 첫 unittest 부모가 종료된 뒤 잠시 남아 두 번째 실행과 고정 임시 파일을 경합해 기존 secret-scanner 테스트 1개가 한 번 실패했다. 단일 테스트와 고립된 전체 재실행은 각각 통과해 구현 결함이 아닌 검증 명령 중첩으로 판정했다. Task 2 reviews는 deprecated `[inbucket]`이 실제 `local_smtp=true`를 끄지 못하는 drift, rollback 이름 2개, in-place `.env` 손상 위험을 발견했고 모두 TDD로 수정했다. DB password commit과 filesystem 교체는 단일 transaction이 될 수 없으므로 파일 실패는 기존 env를 보존하고 gate를 닫으며, 재실행이 password를 다시 회전해 복구한다.

Task 3 첫 실행 뒤 read-only Docker inventory에서 PostgreSQL 외 persistent Kong container가
관찰됐다. v2.109.1 source/CLI 확인 결과 bare `supabase start`는 Data API config와 별개로 Kong을
시작하지만 `supabase db start`는 PostgreSQL만 시작한다. runner test를 먼저 exact `db start`
요구와 bare `start` 거부로 RED 확인한 뒤 runner·계획·운영 문서를 보정했다. root는 데이터 volume을 삭제하지 않고 기존 local project를 정상 종료한 뒤 `supabase db start`로 재기동했다. persistent inventory는 healthy PostgreSQL 1개(54322)이고 Kong container와 54321 bind는 각각 0임을 확인했다. `supabase test db`의 일회성 `pg_prove` container는
테스트 실행용이며 persistent runtime 범위에 포함하지 않는다.

Task 3은 pgTAP 32개를 migration 전 RED로 확인한 뒤 schema migration·역순 compensation·read-only 부재 증명을 구현했다. 초기 명세 review에서 `public` schema가 없어도 통과하는 vacuous assertion 1건을 발견해 `public` 존재와 8개 business table 부재를 하나의 non-vacuous assertion으로 교체했다. 이후 명세·품질 review가 모두 승인됐고, DB-only 전환 후 `db reset --local` exit 0과 pgTAP 32/32를 root가 다시 확인했다.

Task 4는 migration 전 57개 assertion 중 41개가 예상대로 실패하는 RED를 확보한 뒤 불변조건과 보상 SQL을 구현했다. 첫 GREEN 이후 독립 품질·동시성 review가 양방향 trigger의 lock ordering과 stale snapshot 위험을 발견했다. reverse lookup의 불필요한 row lock과 trigger 범위를 줄이고, invariant-bearing write를 `READ COMMITTED`에서만 허용하도록 fail-closed `P0001` guard를 추가했다. 최종 pgTAP은 Task 4 62/62, 전체 94/94였고, 두 연결 3개 시나리오와 별도 deadlock probe가 통과했다. 보상 적용 뒤 Task 4 function/trigger/check는 `0|0|0`, Task 3 table은 8개 보존됐으며 replay, fixture 잔존 0, 명세·품질 재검토가 모두 승인됐다.

Task 5는 capability 부재 6/6의 의도한 RED 뒤 roles·forced RLS·function/retention을 구현했다. 첫 구현의 167/167 GREEN 후 독립 review가 mutable source/office provenance 변경 뒤 동일 `request_id` replay가 `P1010`이 되는 회귀와 policy/function allowlist coverage를 발견했다. test-only RED는 Task 5 2/78 실패, 전체 172였고, committed event를 current provenance보다 먼저 비교하도록 최소 수정한 뒤 172/172가 됐다. root가 reset, 172/172, `00300 → 00200 → 00100` compensation, absence proof, fresh replay, 172/172를 독립 재현했다. 동일/충돌 최초 요청, concurrent purge, backend diagnostic sentinel 비노출 probe도 통과했고 두 review pass에 다른 blocking finding은 없다. Q-SEC-002=A가 현재 non-superuser fail-closed model을 승인해 Task 5 acceptance도 완료됐다.

Task 6는 새 workflow interface 부재 RED 뒤 초기 228/228 GREEN을 만들었다. 독립 review가 replay/confirmation lock inversion, confirmed failure reversal, deterministic KB-ID collision의 native diagnostic을 발견했다. focused RED 5/62와 deterministic `40P01`을 재현한 뒤 parent event `FOR SHARE`, status-aware monotonic lineage trigger, 단일 KB INSERT의 `P1003` collision mapping으로 보정했다. 최종 root 검증은 reset/forward 234/234와 4개 concurrency scenario, 003 guard expected fail, 004 compensation, Task 1~5 172/172와 3개 compensated scenario, fresh replay 234/234와 4개 scenario를 모두 통과했다. 두 probe command 조합 실패는 PowerShell/로컬 CLI 경로 quoting 문제로 제품 SQL failure가 아니며 secret 노출이나 성공한 rollback 외 DB mutation은 없었다. 독립 code review는 clean이다.

Task 7은 새 citizen read/index가 없는 상태에서 기존 234 assertions가 통과하고 새 catalog checks 9/11이 실패한 뒤 undefined function으로 멈추는 RED를 확보했다. exact five indexes와 `list_active_kb`/`list_offices`를 구현한 뒤 focused 40/40, full 274/274가 통과했다. test-only hardening은 dynamic SQL 부재와 함수별 stacked diagnostic 비누출 검사를 비공허하게 강화했다. `00500` compensation 뒤 함수/index는 0, Task 1~6은 234/234와 concurrency 4 scenarios를 보존했고 fresh five-migration replay는 274/274+4를 통과했다. root가 forward `274+4`, compensated `234+4`, final replay `274+4`를 독립 재현했으며 final catalog는 `functions=2 posture=2 acl=2 indexes=5 rows=0 backend_select=0`, 독립 review는 Critical/Important/Minor 0이다.

Task 8은 error/model production module이 없는 상태의 import error 2개 RED와 pool module 부재 RED를 먼저 확보한 뒤, exact enum·frozen/slotted model·safe error mapping과 explicit unopened pool·repository protocol/adapter를 구현했다. 초기 GREEN 후 ACTIVE KB가 question example 적어도 1개를 가져야 한다는 DB invariant의 Python mirror 누락을 focused 2-test RED로 재현하고 최소 validator로 닫았다. 최종 API는 156 passed+4 subtests, Ruff/Mypy clean이며 exact 10 files·독립 review Critical/Important/Minor 0이다. native DB message/detail/parameter는 stringify/log하지 않고 고정 code로만 축약된다.

후속 품질 review에서 첫 regression test가 source 전체 문자열을 검사해 주석 속 정답과 실제
대소문자 변형 호출을 구분하지 못하는 false-pass가 발견됐다. AST 검사로 한 차례 강화했지만,
재검토에서 exact 호출을 `if ($false)`에 두고 live direct bare `start`를 실행하면 syntactic AST가
통과하는 Important 우회가 재현됐다. 이 mutant가 기존 AST checker에서 `True`가 되는 RED를 확보한
뒤 static control-flow 주장을 제거했다. 현재 test는 실제 `verify_database.ps1`을 synthetic temp
repo에서 실행한다. API venv Python launcher를 fake Docker/Supabase/Python executable로 복사하고,
fake Supabase가 실제 받은 argv만 합성 JSONL에 기록하도록 했다.
초기 behavioral fixture는 exact `db start` 직후 exit 7이라 그 뒤에 추가된 live bare start를
관찰하지 못하는 세 번째 Important false-pass가 있었다. extra-bare mutant가 production과 같은
`[['db', 'start']]`만 기록해 RED로 실패함을 확인한 뒤 중단 지점을 다음 controlled
`['db', 'reset', '--local']`로 옮겼다. 현재 fake exact/bare start는 기록 후 0을 반환하고 reset만
7로 중단한다. 현재 production sequence는 정확히
`[['db', 'start', '--network-id', 'sejong-ai-local-loopback'], ['db', 'reset', '--local']]`이며,
dead exact + live bare는 `[['start'], reset]`, correct + extra bare는
`[['db','start','--network-id',...], ['start'],
reset]`으로 관찰돼 계약을 통과하지 못한다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 변경 없음 |
| Repo guidance | 1.4.0 | 1.4.0 | Q-SEC-005 blocker로 후보 승격 보류 |
| Application | 0.1.0 | 0.1.0 | 변경 없음 |
| Web | 0.1.0 | 0.1.0 | 변경 없음 |
| API | 2.0.1-draft | 2.0.1-draft | public contract 유지 |
| DB schema | 0.2.0-draft | 0.2.0-draft | exact loopback/fresh full gate 전 승격 금지 |
| Official data | 0.0.0-not-populated | 동일 | seed 금지 |
| Mock data | 0.0.0-not-populated | 동일 | tracked seed 금지 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 미사용 |
| Test suite | 0.4.2-readiness-contract | 0.4.2-readiness-contract | 후보 test version 미승격 |
| Docs | 2.3.14 | 2.3.14 | 후보 docs version 미승격 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| worktree detection/ignore check | normal main checkout, `.worktrees/` ignored | 1 check | terminal |
| `git worktree add ... -b codex/db-001-layered-enforcement` | success at base `cf76b17` | 1 worktree | Git metadata |
| first `scripts/verify.ps1` | `PREFLIGHT-UV` operational failure | 5.5s | terminal |
| ignored uv reconstruction | `uv 0.11.28` verified; tracked diff 0 | 1 tool | worktree `.tools/uv` |
| second `scripts/verify.ps1` | outer tool timeout 124; no runner verdict | 124.2s | terminal |
| third `scripts/verify.ps1` | exit 0, 24/24 stable stages | 143.6s | terminal |
| Task 1 initial focused suite | expected RED: missing manifest/bootstrap/ignore; 후속 release-dir·argument 회귀 RED | 11 tests에서 7 expected failures | agent terminal |
| Task 1 PowerShell argument regression | `-ArchivePath` missing value가 typed binder에서 exit 1/path stderr 노출하는 RED 재현 후 raw allowlist parser로 GREEN | focused 3/3 | commit `857e2b2` |
| `python -B -m unittest scripts.tests.test_supabase_tooling scripts.tests.test_repository_scaffold scripts.tests.test_security_boundaries -v` | root fresh exit 0 | 28 passed, 1 Windows symlink permission skip, 48.360s | terminal |
| `powershell ... scripts/check_secret_patterns.ps1` | exit 0, output 0 | 1 scan | terminal |
| `git diff --check 4455ad5..HEAD` | exit 0 | whitespace error 0 | terminal |
| independent specification review | initial P1 argument-binding disclosure found; fix 후 compliant | 2 review rounds | reviewer report |
| independent quality/security review | APPROVED; Critical/Important 0, Minor 3 | 1 review | reviewer report |
| pinned `bootstrap_supabase.ps1` install | official archive size/SHA-256/exact `2.109.1` version PASS, `supabase init` success | 1 install/init | ignored `.tools/supabase/v2.109.1` |
| Task 2 initial focused RED | 새 config/seed/helper/runner 부재 | existing 9 pass, 7 expected fail/error | agent terminal |
| Task 2 first GREEN | generated config의 required local mail toggle mismatch 1 failure 후 보완 | tooling 16/16 | agent terminal |
| Task 2 spec review | 실제 `local_smtp` toggle·rollback filenames P1 2건 발견; TDD 수정 후 compliant | 2 rounds | commit `339f04f`, reviewer report |
| Task 2 quality review | in-place env corruption Important 1건 발견; injected failure RED 후 atomic replace; 재검토 APPROVED | 2 rounds | commit `9733ec7`, reviewer report |
| final Task 2 unittest | root sequential exit 0 | 31 passed, 1 Windows symlink permission skip, 97.367s | terminal |
| final Ruff / Mypy | exit 0 / exit 0 | Python tools 2 files | terminal |
| final secret / CLI verify / diff | exit 0 / exit 0 / exit 0 | CLI exact version PASS, secret output 0 | terminal |
| PostgreSQL-only start regression RED | bare `start`만 있어 exact `db start` assertion이 예상대로 실패 | focused 1 failure | agent terminal |
| PostgreSQL-only start regression GREEN | runner가 exact `db start`를 사용하고 bare start pattern 0 | focused 1/1 | agent terminal |
| PostgreSQL-only correction full scripts suite | exit 0 | 54 tests, 1 Windows symlink permission skip, 136.459s, OK | agent terminal |
| Ruff/Mypy full-file audit | 기존 test의 I001/E501×2/SIM117 및 line 465 `arg-type`, 기존 helper의 import/format drift 확인; 새 test line 진단 0 | Ruff non-zero / Mypy tooling scripts 2 files pass | agent terminal |
| changed-scope Ruff/Mypy with 확인된 baseline codes 제외 | exit 0 / exit 0 | modified test file 1개, 추가 진단 0 | agent terminal |
| correction secret / pinned CLI / diff | exit 0 / exit 0 / exit 0 | secret output 0, exact CLI PASS, whitespace error 0 | agent terminal |
| independent correction quality review | whole-source string test의 false-pass Important 1건 | fix required | reviewer report |
| AST mutant regression RED | 주석 속 정답 + live alternate-case arguments가 기존 checker에서 `True` | focused 1 expected failure | agent terminal |
| AST contract GREEN (superseded) | actual runner pass; comment/dead-string/case/extra/variable/wrong-binary/duplicate mutants reject | focused 2/2 | agent terminal |
| case-insensitive duplicate mutant RED→GREEN (superseded) | PowerShell의 case-insensitive command 중복을 추가 재현하고 AST 수집도 case-insensitive로 보정 | focused expected failure 후 2/2 pass | agent terminal |
| corrected tooling module | exit 0 | 20 tests, 64.560s, OK | agent terminal |
| independent correction quality re-review | dead exact AST + live direct bare start false-pass Important 1건 | behavioral fix required | reviewer report |
| behavioral bypass RED | `if ($false)` exact call + direct bare invocation이 AST checker에서 `True` | focused 1 expected failure | agent terminal |
| actual runner argument capture GREEN | production `['db','start']`, mutant `['start']`, stable exit 7/no stderr | focused 2/2, 16.930s | agent terminal |
| behavioral correction tooling module | exit 0 | 20 tests, 53.179s, OK | agent terminal |
| independent behavioral quality review | exact start에서 조기 exit해 후속 extra bare가 unreachable인 Important 1건 | fix required | reviewer report |
| post-start extra-bare RED | correct call 뒤 bare start mutant가 production과 같은 `[['db','start']]`로 false-pass | focused 1 expected failure | agent terminal |
| reset-boundary capture GREEN | production exact start→reset; dead/extra bare mutant sequence 분리; reset에서 stable exit 7 | focused 3/3, 30.953s | agent terminal |
| reset-boundary tooling module | exit 0 | 21 tests, 59.928s, OK | agent terminal |
| root focused start-capture rerun | exit 0 | 3/3, 36.688s | terminal |
| independent runtime-correction quality review | 최종 APPROVED; Critical/Important 0 | 4 review rounds, false-pass 3건 TDD 폐쇄 | reviewer report |
| Task 3 schema contract RED | migration 전 32 assertion 중 private schema 관련 30개 expected failure, 기존 privacy/public 부재 2개 pass | 1 pgTAP file | agent terminal |
| Task 3 migration GREEN | `Files=1, Tests=32`, `Result: PASS` | 32/32 | agent/root terminal |
| Task 3 compensation→absence→reset/replay | application schema 제거, platform schema 보존, migration 재적용, 32/32 | exit 0 | agent terminal |
| Task 3 specification review | `public` schema 부재 시 vacuous pass 1건 수정 후 compliant | 2 rounds | commits `7a03259`, `d90ee14` |
| Task 3 quality/security review | APPROVED; Critical/Important/Minor 0 | 1 review | reviewer report |
| local runtime one-time transition | default stop exit 0; `db start` exit 0; persistent PostgreSQL 1 healthy/54322; Kong 0; 54321 bind 0 | 데이터 volume 삭제 0 | root terminal |
| DB-only reset and Task 3 replay | `db reset --local` exit 0; `test db` exit 0 | 32/32 | root terminal |
| Task 4 invariant RED | migration 전 57 assertion 중 기존 shape 관련 16개 pass, 새 규칙 41개 expected failure | 41/57 RED | agent/root terminal |
| Task 4 invariant GREEN | 두 pgTAP file 모두 PASS | Task 4 62/62; 전체 94/94 | agent/root terminal |
| Task 4 two-connection concurrency | ACTIVE-question, event/failure, failure/candidate stale-snapshot 차단 | 3 scenarios, 2 connections, PASS | `scripts/test_database_concurrency.py`, agent/root terminal |
| Task 4 deadlock probes | event↔failure와 failure↔candidate 양방향 동시 write가 제한시간 내 종료 | deadlock 0 | agent terminal |
| Task 4 compensation absence | 보상 뒤 Task 4 function/trigger/check 0, Task 3 table 8 보존 | `0|0|0|8` | agent terminal |
| Task 4 replay and cleanup | reset/replay 뒤 94/94; Task 4 fixture row 합계 0 | PASS, rows 0 | agent/root terminal |
| Task 4 independent reviews | 초기 lock inversion/stale snapshot 지적을 수정한 뒤 명세·품질 승인 | blocking finding 0 | reviewer reports, commits `f181ffd`, `cc22161` |
| Task 5 initial RED | role/RLS/functions 부재의 의도한 실패 | 새 6/6 fail, 기존 94 pass | Task 5 report |
| Task 5 initial GREEN | role/RLS/interaction/retention 구현 뒤 PASS | 167/167 | commit `fa6b755`, Task 5 report |
| Task 5 review regression RED→GREEN | mutable provenance 뒤 replay 2/78 fail을 재현하고 committed replay-first로 수정 | 최종 Task 5 78/78, 전체 172/172 | commit `264772d`, Task 5 report |
| Task 5 root reset/test | fresh exit 0 / exit 0 | 172/172 | root terminal |
| Task 5 root compensation/absence/replay | `00300 → 00200 → 00100`, absence proof, fresh reset/test 모두 PASS | 재적용 172/172 | root terminal |
| Task 5 two-session probes | identical same ID, conflicting `P1010`, purge `1→0→0`, links 보존, fixture 0 | replay 2 scenarios + purge 1 | Task 5 report |
| Task 5 diagnostic nonleak | non-superuser backend `P1010`, sentinel diagnostic leak 0, write 0 | 1 synthetic probe | Task 5 report |
| Task 5 independent review passes | privilege/replay coverage fix 뒤 추가 blocking finding 0; Q-SEC-002=A로 acceptance 완료 | Task 5 Done | reviewer reports, D-026 |
| Task 6 initial RED→GREEN | workflow interface 부재 RED 뒤 초기 구현 | 최초 228/228 | commits `cd18ff6`, Task 6 report |
| Task 6 review RED | lineage/lock/reversal/collision focused 실패와 deterministic deadlock 재현 | 5/62 fail + native `40P01` | Task 6 report |
| Task 6 final forward/root test | reset, focused/full pgTAP, two-connection probe | 62/62; 234/234; 4 scenarios | commit `2ba566d`, root terminal |
| Task 6 guard/compensation | 003 guard expected fail, 004 compensation, exact Task 4 definition 복구 | Task 1~5 172/172; 3 scenarios | Task 6 report/root terminal |
| Task 6 fresh replay | 00100~00400 재적용 뒤 full pgTAP/concurrency | 234/234; 4 scenarios | root terminal |
| Task 6 static/review gates | Ruff check/format, mypy, secret scan, diff-check, 독립 code review | 모두 PASS; Critical/Important/Minor 0 | Task 6 report/reviewer report |
| Task 6 post-review format gate | canonical Ruff format/check·lint·mypy·tooling target·concurrency 재검증 | semantic change 0; Critical/Important/Minor 0 | commit `72b7ab1`, root terminal/reviewer report |
| Task 7 initial RED | 기존 234 pass, 새 catalog 9/11 fail 뒤 read function 부재 | expected nonzero | Task 7 report |
| Task 7 focused/full GREEN | citizen read catalog·ACL·filter·ordering·diagnostic | 40/40; 274/274 | commits `37b5e2c`, `59a69bd`, Task 7 report |
| Task 7 compensation preservation | `00500`만 보상, read function/index absence, 이전 기준선 | 함수 0, index 0; 234/234 + concurrency 4 | Task 7 report/root terminal |
| Task 7 fresh replay/root verification | five migrations, full pgTAP, two-connection probe | 274/274 + concurrency 4; root forward/compensated/final 재현 | Task 7 report/root terminal |
| Task 7 catalog/static/review | catalog/ACL/privacy count, secret/diff, 독립 review | `2/2/2/5/0/0`; secret 0; C/I/M 0 | Task 7 report/reviewer result |
| Task 8 Phase 1 error/model RED→GREEN | DB import 2개 부재 RED 후 typed model·safe error mapping | 81 passed | Task 8 report/agent terminal |
| Task 8 Phase 2 repository RED→GREEN | pool 부재 RED 후 lazy pool·protocol·fixed-SQL adapter·import isolation | 31 passed + 4 subtests | Task 8 report/agent terminal |
| Task 8 interim ACTIVE question invariant | missing-validation RED 후 minimal model guard | focused 2/2 | Task 8 report |
| Task 8 API root+agent verification | Ruff format/lint, strict Mypy, full pytest | 22 files clean; 156 passed + 4 subtests | Task 8 report/root+agent terminal |
| Task 8 static/scope/review | secret/package/diff/exact 10-file checks, independent review | PASS; Critical/Important/Minor 0 | Task 8 report/reviewer result |
| Task 9 no-URL collection | DB env 두 항목 없는 child에서 implicit connection 없음 | exact 8 skip, reason `local DB gate only` | `.superpowers/sdd/task-9-report.md` |
| Task 9 runner contract | stale rollback RED 뒤 exact 5-file order·exit·비노출·env 복원 보정 | 16/16 pass, 32.425s | Task 9 report; 이 행은 당시 세 owned 파일의 작업 트리 상태를 기록 |
| Task 9 disposable rollback/replay | reset 1·274/274·5-file rollback·absence·reset/replay 2·274/274 | integration 전 단계 모두 PASS | Task 9 report/root runner |
| Task 9 real DB integration | replay/reason/candidate/purge/permission/read 6개 통과, approval 2개 동일 권한 경계 실패 | 6 pass, 2 fail, 3.17s | Task 9 report |
| Task 9 safe blocker proof | deferred trigger `prosecdef=false`, backend private-schema usage=false, `42501`→`DatabaseUnavailableError` | catalog 2 booleans, native diagnostic 노출 0 | Task 9 report |
| Task 9 rollback/cleanup | candidate PENDING, link NULL, KB/question/approval-audit 0; 8 table categories cleanup 0 | atomic rollback·residue 0 | Task 9 report |

### 역사적 미실행 검증과 최종 해소

- `verify_database.ps1`은 Task 9에서 stale compensation 목록을 TDD로 보정했고 reset·두 번의 274/274·5-file rollback·absence·replay까지 통과했다. 이 문단의 integration 6/8·exit 1은 Q-DB-003 결정 전 역사적 RED이며, 최종 closeout은 006 보정 뒤 integration 8/8과 full gate 통과다.
- 당시 남아 있던 Task 9 no-Docker root gate, final secret/package/scope gate와 세 owned 파일 commit은 Task 9A 이후 모두 실행·통과·커밋됐다.
- global `scripts/check_scope_drift.py`는 기존 `PACKAGE_MANIFEST.json`과 ignored `.tools/isolated-repo` 때문에 baseline-red이다. Task 8 파일은 보고 0이고 secret/package/diff/exact-scope 대체 gate는 통과했다.
- DeepSeek call: DB-001 범위 밖이며 외부 provider 호출·전송 0. Provisioning은 `.env` 전체 bytes를
  원자 갱신하기 위해 읽지만 DeepSeek key 값을 파싱·출력·별도 복사하지 않는다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 실제 시민 질문 원문 접근 0. Approved provisioning은 ignored `.env` 전체 bytes를 읽어
  `DATABASE_URL`만 원자 교체했지만 non-target/provider 값을 파싱·출력·별도 복사하지 않았다.
  Task 4~9는 합성 `MOCK`/`[MASKED]` fixture 또는 capability 증명용 최소 synthetic OFFICIAL
  fixture만 사용했고 Task 9 cleanup은 events/failures/candidates/KB/questions/offices/mappings/audits
  모두 0이다. Task 7 read는 시민용 stored metadata allowlist만 반환하며, Task 8 repository는 raw
  answer/context token/HTTP role header/arbitrary SQL을 인자로 받지 않고 OUT_OF_SCOPE text 저장을
  model에서 거부한다.
- Security: CLI 공급망·child 비노출 경계에 더해 Task 5 forced RLS/owner-only policy/backend base-table denial, Task 6 다섯 workflow capability, Task 7 두 `STABLE SECURITY DEFINER` read allowlist와 invalid-filter diagnostic 비누출을 검증했다. Task 8은 SQLSTATE만 고정 error로 매핑하고 PostgreSQL native message/detail/parameter를 stringify/log하지 않으며, fixed schema-qualified SQL/positional parameter/lazy pool을 강제했다. Task 9은 `42501`을 `DatabaseUnavailableError`로 안전하게 축약하고 direct private access denial을 재확인했으며, 발견한 deferred trigger invoker 권한 blocker는 exact `search_path=pg_catalog, pg_temp`인 validator-only `00600`으로 해소했다. broad grant·repository/admin 우회·기존 migration 수정 금지는 유지된다. privileged graph 22개 중 나머지 unsafe path 21개는 A-021/Q-SEC-003으로 분리됐고 public release를 차단한다. 실제 provider 값은 로그·문서·Git에 노출하지 않았다.
- Accessibility: UI 변경 없음.
- Performance/cost: Task 7 exact five indexes와 row-local deterministic question aggregate를 추가했다. Task 8 pool은 `open=False`, min 1/max 4이고 read는 불필요한 transaction을 열지 않는다. Task 9은 disposable local DB만 호출했고 외부 provider·유료 API·인프라 비용은 0원이다.

## 10. 데이터와 출처 영향

- 공식 데이터: 0 rows. `supabase/seed.sql`은 DATA-001/DATA-SEED-001 소유를 설명하는 주석 3줄뿐이다.
- mock/AI 생성: 0 rows.
- schema/lineage: manifest는 Task 10 전후 모두 `0.2.0-draft`를 유지하며 logical projection의
  `0.3.0-local`은 미승격 후보다. executable migration 6/6(`20260716000100_private_schema.sql`~
  `20260717000600_deferred_active_question_trigger_security.sql`)과 matching compensation의 과거
  실행 증거는 있다. Task 7은 table/lineage를 바꾸지 않고 index/function/ACL만 추가했고,
  Task 8은 schema/data를 바꾸지 않은 채 9개 function 계약의 typed API boundary를 추가했다.
  Q-DB-003=A에 따라 기존 migration을 수정하지 않고 새 `00600` forward/compensation/pgTAP을 추가했다.
- tooling source: official Supabase CLI tag `v2.109.1`; `apps/cli-go/pkg/config/config.go`의 `local_smtp` mapping/deprecated `inbucket` normalization과 `internal/start/start.go`, `internal/db/start/start.go`, `internal/db/test/test.go`의 실행 경계를 기준으로 DB-only drift를 보정했다.
- verified date: 2026-07-17 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 계획 실행은 승인됐으며 local CLI download, image pull, disposable DB reset 범위가 열렸다.
- official CLI 2.109.1, PostgreSQL-only config·빈 seed·검증 runner가 준비됐고 local DB에 private schema·7 enum·8 table, Task 4 불변조건, Task 5 role·grant·forced RLS·interaction/retention capability가 생성됐다.
- Q-SEC-002=A로 Task 5를 완료했고, Q-WF-001=A의 별도 사유 확인 capability와 새 `00400` workflow migration을 구현·검증해 Task 6를 완료했다.
- `00500`의 ACTIVE+OFFICIAL KB와 OFFICIAL 기관 read를 구현·검증해 Task 7을 완료했다. 실제 공식 데이터는 0이므로 `/ready=503` 상태는 유지한다.
- Task 8의 lazy typed FastAPI DB boundary가 구현됐다. native DB diagnostic은 SQLSTATE 기반 고정 error로만 축약되고, pool은 명시적 생성 전에 열리지 않는다. public route는 아직 연결되지 않았다.
- 역사적 Task 9 RED에서는 no-URL 8 skip, runner contract 16 pass, reset·274/274·다섯 보상·absence·replay·274/274를 통과했지만 실제 approval 2개가 deferred trigger 권한 때문에 실패해 6/8이었다. `00600` 보정 뒤 최종 integration은 retained diagnostic branch와 branch 제거 후 모두 8/8이다. Task 9은 완료됐고 DB-001은 Task 10 전까지 `Done`이 아니다.
- Q-DB-003=A는 새 `00600` migration으로 `validate_active_kb_question()` 하나만 SECURITY DEFINER로 제한하고 기존 owner·exact `search_path=pg_catalog, pg_temp`·명시 revoke를 검증하는 방식이다. B는 approval 함수 안에서 constraint를 즉시 실행하지만 transaction 결합이 커 선택하지 않았다.
- 질문 예시·ACTIVE 전환·lineage 관련 직접 write는 `READ COMMITTED` transaction 계약이다. FastAPI 기본 경로도 이 격리수준을 유지해야 하며 다른 격리수준은 안정된 `P0001`로 거부된다.
- bare `supabase start`가 만든 Kong은 데이터 volume 삭제 없이 제거했다. Task 10 port finding 뒤
  stock CLI runtime도 fail-closed stop했고 project container count 0을 확인했다. 현재 사용자가
  직접 결정할 항목은 Q-SEC-005다. Q-SEC-004=A/D-029의 1차 보정은 actual IPv6 wildcard를 남겼다.
- remote Supabase, public deployment, official ACTIVE data, retention/권한 변경, 새 production dependency는 여전히 별도 승인 사항이다.
- 최종 branch 통합 방식은 모든 검증 완료 후 finishing skill에서 사용자에게 선택받는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- root는 coordinator로 남고 task별 fresh agent가 코딩한다.
- review 순서는 명세 적합성 → 코드 품질이며 둘 다 승인되기 전 다음 task로 이동하지 않는다.
- ignored uv copy는 worktree bootstrap일 뿐 commit 대상이 아니다.
- Supabase v2.109.1에서 deprecated `[inbucket]` 대신 실제 `[local_smtp]`를 꺼야 한다는 upstream drift는 승인된 DB-only 의도를 유지하는 내부 호환성 보정이다.
- 같은 버전에서 persistent DB-only 시작 명령은 `supabase db start`이다. `test db`가 만드는 일회성 `pg_prove` container는 persistent project container inventory와 구분한다.
- Task 4 review는 양방향 trigger의 역방향 lookup에서 row lock을 제거하고 변화 가능 column으로 trigger를 좁혔다. 두 연결 probe는 fixture UUID를 고정하고 `finally` cleanup을 수행한다.
- Task 5 replay는 stored metadata를 먼저 비교하고 genuinely new request만 source→office 순서로 잠근다. role membership option은 grantor별 effective union으로 검사한다.
- Task 6 confirmation은 event 최초 사유를 바꾸지 않고 failure 사유·eligibility·상태만 갱신한다. parent `FOR SHARE`와 failure/candidate `FOR UPDATE` 순서, monotonic status trigger, 단일 KB INSERT collision mapping이 replay/approval 동시성·비누출 경계를 유지한다.
- Task 7 read는 enum cast 전 text allowlist, exact owner/ACL, 고정 `search_path`, schema-qualified SQL, `C` collation 정렬을 사용한다. test-hardening은 두 함수 모두의 no-dynamic-SQL과 stacked diagnostic 비누출을 비공허하게 확인한다.
- Task 8 model은 PostgreSQL enum을 `str, Enum`으로 mirror하고 frozen/slotted dataclass로 입출력을 제한한다. repository는 fixed SQL 9개만 positional parameter로 호출하며 read는 tuple, write는 connection+transaction context를 사용한다.
- Task 9 Windows async hang은 selector event-loop policy로 해소했고 test pool은 open 뒤 single-connection resize한다. blocker는 이 test harness 문제가 아니라 `prosecdef=false` deferred validator와 backend private-schema usage=false의 조합이다.

## 13. 인수인계·재현·롤백

### 재현

1. worktree branch가 `cf76b17`에서 분기했고 Task 1 commits `41c6dcf`, `857e2b2`가 있는지 확인한다.
2. worktree ignored `.tools/uv/uv.exe --version`이 0.11.28인지 확인한다.
3. `scripts/verify.ps1`에서 24/24 exit 0을 재현한다.
4. `scripts/bootstrap_supabase.ps1 -VerifyOnly`가 exact version PASS를 내는지 확인한다.
5. Task 2 focused unittest 31 pass와 Ruff/Mypy/secret/diff를 재현한다.
6. `.tools/supabase/v2.109.1/supabase.exe db start`를 child output 비노출 방식으로 실행하고 persistent inventory가 PostgreSQL 하나인지 확인한다.
7. `supabase db reset --local` 후 `supabase test db`가 `Files=6, Tests=282`, `Result: PASS`인지 확인한다.
8. 관리자 DSN을 출력하지 않고 `SEJONG_ADMIN_DATABASE_URL` process env로만 전달해 `scripts/test_database_concurrency.py`가 `scenarios=4 connections=2` PASS인지 확인한다.
9. D-026/D-027과 refined plan을 확인한다.
10. final catalog가 `functions=2 posture=2 acl=2 indexes=5 rows=0 backend_select=0`이고 focused 006 posture가 8/8인지 확인한다.
11. `.\.tools\uv\uv.exe run --directory apps/api --frozen ruff format --check src tests`, `ruff check`, `mypy`, `pytest -q -p no:cacheprovider`를 실행해 22 files format/lint/strict type 검사와 API 156 passed+4 subtests를 확인한다.
12. [Task 9 blocker 노트](IMP-20260717-004-db-001-task-9-deferred-trigger-permission-blocker.md)의 역사적 6/8·rollback/cleanup 증거와 D-028/ADR-0012/[Task 9A plan](../superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md)을 확인한다.

### 롤백

Task 8만 rollback할 때는 DB/schema/data compensation 없이 `git revert 3cae552`를 실행하고 기존 API 게이트와 Task 7 `274/274+4`를 재확인한다. Task 7만 보상할 때는 관리자 DSN을 출력하지 않고 process environment로만 전달해 `database/rollbacks/20260716000500_indexes_and_read_interfaces.rollback.sql`을 실행한다. read function/index 부재, Task 1~6 234/234와 concurrency 4개를 확인하고 fresh reset으로 274/274+4를 복구한다. 전체 DB-001 목표 순서는 `00600 → 00500 → 00400 → 00300 → 00200 → 00100`과 absence proof이다. Task 9은 `228d8cb`, `04a944f`, `5266abc`를 역순 revert하고 local reset/replay한다. 공유된 migration은 수정하지 않는다. Task 7 코드 rollback은 test-only `59a69bd`, 최초 구현 `37b5e2c` 순서로 revert한다. 이후 Task 6은 formatting-only `72b7ab1`, review fix `2ba566d`, 최초 구현 `cd18ff6`, Task 5는 `264772d`, `fa6b755`, Task 4는 `cc22161`, `f181ffd`, `be69d94`, Task 2는 `9733ec7`, `339f04f`, `840d949`, Task 1은 `857e2b2`, `41c6dcf`를 각각 역순 revert한다.

### 다음 개발자 시작점

D-026~D-029, ADR-0011/0012, [Task 9 closeout evidence](IMP-20260717-004-db-001-task-9-deferred-trigger-permission-blocker.md)와 완료된 [Task 9A plan](../superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md)을 확인한다. 이 문단의 당시 다음 작업은 Task 10 authority/version/changelog/handoff 동기화였으며 현재는 역사적 지시다. 활성 다음 순서는 Q-SEC-005 인간 결정 → safe runtime/full gate → 독립 review이고, 그 뒤에만 DATA-001 PM 승인 → DATA-SEED-001로 진행한다. A-021/Q-SEC-003 caveat를 보존하고 `00700`은 인간 승인 전 구현하지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- 품질 review 비차단 개선: 다운로드 timeout/크기 상한, 합성 success extraction test, child output async drain.
- Docker image pull 크기/시간 미측정.
- Q-SEC-002/Q-WF-001/Q-DB-003은 A로 해결됐다. 현재 인간 A/Blocker는
  A-023/Q-SEC-005 1개이고 A-021은 별도 B/High Open/Deferred다.
- migration/compensation은 6/6이고 full pgTAP은 282/282다. Task 9 runner는 exact six-stage rollback/absence/replay와 integration 8/8을 통과해 commit됐다.
- 역사적 DB integration 6/8 blocker는 `00600`으로 해소됐다. retained diagnostic branch와 제거 뒤 각각 8/8이며 cleanup은 identifier-scoped 단일 admin transaction이다.
- pinned Starlette/httpx TestClient deprecation warning 1건은 non-failing이며 새 production dependency 승인 없이 수정하지 않았다.
- parent KB DELETE와 explicit child question DELETE가 동시에 일어나는 경로는 잠금 순서 P2 위험이 남아 있다. 현재 삭제 API가 없어 비차단이며, 삭제 기능을 추가하기 전에 별도 concurrency test가 필요하다.
- 역사적 다음 단계: Task 10 실행. 현재 다음 단계는 local port security finding을 해소한 뒤 DATA-001 PM 승인 → DATA-SEED-001이며, A-021 public-release blocker를 보존하고 `00700`은 Q-SEC-003 승인 전 구현하지 않는다.

## 15. 자체 리뷰

- [x] 사용자 승인과 baseline 기록
- [x] worktree 격리와 clean baseline
- [x] source-of-truth/계약/버전 목표 유지
- [x] 개인정보 원문·secret 노출 없음
- [x] INDEX 갱신
- [x] Task 1 명세 review와 품질 review 승인
- [x] Task 2 명세 review와 품질 review 승인
- [x] Task 3 RED→GREEN·compensation/replay·명세 review·품질 review 승인
- [x] PostgreSQL-only runtime 전환·Kong/54321 부재·root 32/32 재검증
- [x] Task 4 RED 41/57→GREEN 62/62, 전체 94/94·두 연결 3시나리오·deadlock probe 통과
- [x] Task 4 compensation `0|0|0|8`·replay·fixture 0·명세/품질 재검토 승인
- [x] Task 5 RED→GREEN·review fix·172/172·동시성·diagnostic 비노출·compensation/replay 기술 검증
- [x] Task 5 Step 3 acceptance — Q-SEC-002=A / D-026
- [x] Task 6 gate 해소 — Q-WF-001=A / D-027
- [x] Task 6 RED→GREEN·review fix·234/234·concurrency 4/3·compensation/replay·독립 review clean
- [x] Task 7 RED→GREEN·test hardening·274/274·concurrency 4·compensation/replay·독립 review clean
- [x] Task 8 two-phase RED→GREEN·ACTIVE invariant RED→GREEN·Ruff/Mypy·API 156+4·exact 10 files·독립 review clean
- [x] Task 9 부분 증거(no-URL 8 skip, tooling 16, rollback/replay 274/274×2, integration 6/8, cleanup 0)와 Q-DB-003 blocker를 허위 완료 없이 기록
- [x] Task 9A RED→GREEN·pgTAP 282·6단계 compensation/replay·integration 8/8·zero-row 검증
- [x] Task 9 initial review Important 1/Minor 1 보정과 final spec/quality 0/0/0
- [x] root independent DB/root/tooling/no-URL/protected-scope 재검증과 clean worktree

## 16. Task 9 closeout addendum — 2026-07-17 KST

### 구현·테스트·review

- commits: `5266abc`(authorized 4 paths), `04a944f`(Task 9 3 paths),
  `228d8cb`(integration evidence 1 path).
- RED: integration 6/8, focused `006` 2/8 meaningful failures, tooling expected
  RED 2. GREEN: focused 8/8, full `Files=6, Tests=282`, compensation posture
  PASS, compensated `Files=5, Tests=274`, retained/removed branch integration
  각각 8/8.
- full runner exact `006→005→004→003→002→001`, absence, replay, pgTAP2,
  integration PASS. Tooling 16/16, Ruff, strict Mypy, root/web/API/contract,
  secret/package/diff와 synthetic 8-table zero PASS.
- initial spec review Important 1/Minor 1은 `228d8cb`로 해결됐다. final spec과
  quality review는 각각 Critical/Important/Minor 0/0/0이다.
- docs-only closeout exact 10 paths의 local link/control/stale/secret/package,
  protected scope 0과 `git diff --check`가 모두 PASS다.

### 버전·보안·개인정보·데이터

모든 manifest version 축은 이 closeout에서 그대로다. 공개 API/table/data/seed,
30-day retention, dependency, cost, remote/public state는 변하지 않았다. 질문/답변,
DSN, key, native diagnostic을 문서에 저장하지 않았다. synthetic 8-table row는 0이다.
A-021은 local Task 9 blocker가 아니지만 public-release blocker다.

### 인수인계

Task 9은 완료됐고 Task 10은 schema authority/changelog/report/handoff 후보를
동기화했다. Q-SEC-004=A/D-029의 보정은 IPv6 wildcard를 남겼고, Q-SEC-005/A-023 해결과 safe runtime/full gate 전 DB-001은 Blocked다.
A-021/Q-SEC-003 기본값 B는 public-release blocker로 계속 보존한다.

## 17. Task 10 local baseline closeout — 2026-07-17 KST

### 요청·인수 기준·6W1H 보충

- Who: Codex root coordinator, Task 10 implementation agent, independent preflight/spec/quality reviewers.
- When/Where: 2026-07-17 KST, `codex/db-001-layered-enforcement` worktree.
- What: executable migration authority와 logical projection을 동기화하고 version/task/dependency,
  active docs, exact test report, operations handoff를 마감한다.
- Why: 다음 개발자가 논리 draft를 실행 권위로 오인하거나 local credential/rollback을 public
  환경에서 사용하지 않게 하고, DB-001 후보 증거와 아직 막힌 local port/seed/public release를 분리한다.
- How/How much: product code·migration·seed·production package dependency/manifest를 바꾸지 않고
  active docs/report/handoff와 security runner/tooling test를 포함한 현재 33개 경로를 갱신한다.
  4개 manifest 축 후보 승격과 TASK dependency reduction은 blocker 해소 전 철회했다.

Conditional acceptance는 7 enum·8 table·5 index 논리 projection, timestamp migration 권위, reverse local
compensation, exact 6+6 SHA-256, pgTAP 282, integration 8/8, no-URL 8 skips, two resets/replay,
synthetic 8-table zero, root/API/Web/contract/secret/package/diff PASS, `/ready=503`, A-021 default B
public block, 공식/mock seed 0을 문서와 fresh actual loopback gate에서 함께 증명하는 것이다.
현재는 과거 DB 증거와 후보 문서만 있으며 Q-SEC-005/A-023 때문에 완료되지 않았다.

### 조사한 상태와 선택/대안

- 기존 `schema-v1.draft.sql`은 6 enum, unqualified table, provenance column 부재,
  mutable `is_official`, stale ACTIVE index와 `pgcrypto` extension을 담아 executable 001~006과
  불일치했다.
- `database/README`, root/API/scripts README, architecture/security/test/operations, ADR-0011,
  plan/spec/TASKS/CHANGELOG/INDEX는 Tasks 0~5 또는 Task 10 ready 상태가 남아 있었다.
- 선택: migration은 불변으로 보존하고 projection을 0.3.0-local의 읽기 전용 shape로만
  동기화했다. helper/capability/trigger/RLS/GRANT 본문은 projection에 복제하지 않고 실행
  lineage와 tests를 유일한 권한 근거로 유지했다.
- 버린 대안: `00700` 자동 구현, public-ready 주장, logical SQL을 migration처럼 실행,
  official/mock seed 생성, PACKAGE_MANIFEST 재생성. 모두 승인/범위/보안 경계를 위반한다.

### 변경 영향

- Product code/API/DB migration/data/prompt/production package dependency: 변경 없음. local verification
  runner/tooling test만 보안 보정했고 public API 2.0.1-draft와 application 0.1.0을 유지한다.
- Logical DB/docs: `database/schema-v1.draft.sql`을 7 enum·8 `app_private` table·3 provenance
  column·generated `is_official`·최종 상태/감사 의미·5 index projection으로 동기화했다.
- Task/dependencies: DB-001과 DATA-SEED/READY/LOG/BACKUP의 DB-001 dependency를 유지한다.
- Versions: repo guidance `1.4.0`, database `0.2.0-draft`, tests
  `0.4.2-readiness-contract`, docs `2.3.14`를 포함해 모든 manifest 축을 유지한다.
- Security/privacy: 질문·답변·DSN/key 값을 terminal·문서·Git에 표시하거나 별도 영구 복사하지
  않았다. runner는 captured admin DSN과 backend DSN을 process memory/environment에서만 사용하고,
  provisioner는 `.env` 전체 bytes를 읽되 non-target 값을 파싱하지 않고 byte-identical하게 보존한다.
  local 기본 credential, TLS/rate-limit 부재와
  A-021/Q-SEC-003 default B public block을 active docs와 handoff에 고정했다.
- Accessibility/performance: UI/동작 변경 없음. local test 결과를 public capacity로 일반화하지 않는다.
- Official/mock data: 둘 다 persistent row 0, `supabase/seed.sql` data-free. DATA-001 PM 승인 목표
  2026-07-20과 `/ready=503`을 유지한다.

### 증거·재현·롤백

Exact 환경, 12개 lineage hash, test totals, commits/reviews는
[DB-001 report](../test-reports/DB-001-LOCAL-BASELINE.md)에, setup/run/migrate/seed/rollback/stop/
recovery와 env 이름은 [handoff](../handoffs/HANDOFF-20260717-DB-001-LOCAL-BASELINE.md)에 있다.
Task 10 docs만 되돌릴 때는 final docs commit을 revert하고 manifest/task/docs 상태를 함께
복원한다. DB executable objects/data는 Task 10에서 바뀌지 않아 SQL compensation이 필요 없다.
전체 disposable-local DB 보상은 `006→005→004→003→002→001` 뒤 absence proof, 정상 복구는
fresh reset/replay다. remote/actual-data/volume에는 실행하지 않는다.

Task 10 pre-security-review historical verification(최종 완료 증거 아님):

| 명령 | 실제 결과 |
|---|---|
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart` | exit 0; reset1/pgTAP1/6-stage rollback/absence/reset2/pgTAP2/integration stable phases 전부 PASS |
| `.\.tools\supabase\v2.109.1\supabase.exe test db` | `Files=6, Tests=282`, `Result: PASS` |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1` | exit 0; root/Web/API/contract/secret/package/diff 전체 stable phase PASS |
| API full pytest without DB URLs | `156 passed, 8 skipped, 1 warning, 4 subtests passed` |
| focused integration without DB URLs | exact 8 skips, 각 reason `local DB gate only` |
| package validator + JSON parse + secret scanner + `git diff --check` | 모두 exit 0; package required 12, secret finding 0, whitespace error 0 |
| projection/version/hash/control/link/scope checks | 7 enum, 8 table, 5 index, provenance 3; manifest unchanged; 12 hashes; changed 33 paths/Markdown 30의 final non-DB rerun PASS |

Task 10 initial review에서 spec `0/1/1`, quality `1/4/0`이 나왔고 actual port critical은
fail-closed runner로 재현했다. Q-SEC-005/A-023 해결 전 fresh DB review/commit을 완료로 기록하지 않는다.

두 custom verifier 초안은 제품 실패 전에 각각 projection 주석의 `GRANT/REVOKE` 단어까지
statement로 오인한 과도한 regex와 PowerShell `Join-Path` 공백 오타로 중단됐다. statement
anchor와 올바른 cmdlet syntax로 고친 재실행은 당시 projection/protected scope와 31-path
control/link를 통과했다. 이후 independent quality review가 Docker wildcard port를 발견했고,
보안 runner/test까지 현재 33-path로 확장한 뒤 fresh non-DB root/tooling/static gate는 PASS했다.
actual loopback/full DB gate와 independent completion review는 Q-SEC-005/A-023 해결 뒤 pending이다.

### 인간이 반드시 알아야 하는 내용

- `0.3.0-local`은 exact loopback/full gate 뒤에만 사용할 후보이며 현재 manifest는
  `0.2.0-draft`다. Q-SEC-005/A-023은 인간 A/Blocker다.
- A-021/Q-SEC-003은 답변되지 않았다. 기본값 B로 public/remote, public admin/API, public
  backend DB credential과 `00700`을 차단한다.
- 공개 배포, CORS/domain, credential, backup, data deletion, official seed는 별도 승인 사항이다.

### AI 내부 구현 세부 — 인간이 굳이 이해하지 않아도 되는 내용

- Markdown link/control/stale/version/scope 검사는 active 파일만 대상으로 하고 역사적
  implementation note의 당시 수치·상태는 증거 보존을 위해 대량 수정하지 않는다.
- projection은 executable helper를 복제하지 않고 table shape와 table-local 의미,
  cross-row capability invariant 설명만 유지해 권위 중복을 피한다.

### Task 10 자체 review

- [x] product code·migration·rollback·seed·dependency·contract 보호 경로 diff 0
- [x] projection 7 enum·8 table·5 index·3 provenance·generated `is_official`
- [x] blocker 발견 뒤 candidate manifest promotion 철회와 모든 축 유지
- [x] report/handoff/implementation note/INDEX 및 active local links
- [x] A-021/Q-SEC-003 default B, `/ready=503`, official/mock 0 보존
- [x] 보안 runner 보정 뒤 31/31 tooling과 fresh non-DB root/static gate
- [ ] Q-SEC-005 해결 뒤 fresh DB/root/static verification
- [ ] independent specification review
- [ ] independent quality/security review
- [ ] final completion docs/version commit
