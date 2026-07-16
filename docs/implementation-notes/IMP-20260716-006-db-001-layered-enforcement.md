# IMP-20260716-006 — DB-001 layered enforcement

- Date/Time (KST): 2026-07-16
- Task ID: DB-001
- Type: implementation
- Status: In Progress
- Author/Agent: Codex `/root` coordinator with task-specific implementation/review agents
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `cf76b17`
- Related plan/ADR/RFP: `docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md`, ADR-0008/0011, D-018/D-025, RFP F-11/F-12/F-13

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 `계획 승인, 구현 시작`이라고 명시해 승인된 DB-001 실행계획의 local-only 구현을 허가했다. 이전 선호에 따라 코딩은 task별 fresh agent가 담당하고 root가 명세·품질 review와 중요한 명령·결정을 통제한다.

### Acceptance Criteria

- checksum-pinned project-local Supabase CLI와 PostgreSQL-only local config를 만든다.
- 네 단계 migration과 역순 compensation을 재현한다.
- private schema, RLS/GRANT, ACTIVE+OFFICIAL read, 원자 승인, retention, audit invariants를 DB에서 강제한다.
- 같은 구조 규칙을 lazy typed FastAPI repository 경계에서 중복 검증한다.
- pgTAP, API unit/integration, concurrency, reset/rollback/replay, root gate를 통과한다.
- 공식 seed·공개 API·readiness 200·remote/public·새 production dependency는 만들지 않는다.
- 실제 결과, 버전, 보안·개인정보·데이터·rollback·handoff를 이 note와 test report에 남긴다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 승인자, Codex root coordinator, task별 구현 agent, 명세 reviewer, 품질 reviewer |
| When — 언제 | 2026-07-16 KST 시작; 완료 시각은 최종 갱신 |
| Where — 어디서 | `.worktrees/db-001-layered-enforcement`, local Docker Desktop/Supabase PostgreSQL, `apps/api`, `supabase/`, `database/`, `scripts/` |
| What — 무엇을 | DB-001 executable local schema, capability boundary, tests, rollback/replay, backend adapter |
| Why — 왜 | 승인·공식 데이터·보관·개인정보 규칙이 API 실수·직접 SQL·동시 요청으로 우회되지 않게 하기 위해 |
| How — 어떻게 | TDD RED→GREEN, task별 commit, 명세 review 후 품질 review, 최종 독립 verification |
| How much — 어느 정도 | 4 forward migrations, 4 compensation files, 5 pgTAP suites, 8 DB interfaces, local-only 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: approved DB-001 spec/plan, ADR-0011, logical DB draft, root verify, API architecture tests.
- 기존 동작: Supabase CLI/config/migration/DB tests 없음; `/health=200`, no seed `/ready=503`.
- 발견한 환경 차이: `.tools/`가 Git ignored라 새 worktree에 repo-local uv가 없었고 첫 verify가 `PREFLIGHT-UV`에서 종료됨.
- 해결: main workspace의 검증된 ignored uv 0.11.28 도구 디렉터리만 worktree `.tools/uv/`에 복구.
- Git 상태: clean base `cf76b17`; 원격 저장소 없음; branch `codex/db-001-layered-enforcement`.
- 비밀 경계: ignored `apps/api/.env`의 내용·길이·hash·DeepSeek key를 읽거나 출력하지 않음.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| DB-001 plan gate | Human | 실행 승인 | 2026-07-16 승인 | Task 0~10 실행 허용 |
| CLI pin | Internal verified | stable Windows x64 | v2.109.1 + approved SHA-256 | local tooling |
| public/remote | Human deferred | remote link/push/deploy | 승인되지 않음 | 실행 금지 |
| official data | Human/PM | 승인 seed | DATA-001 전 0 rows | readiness 503 |
| worktree uv | Internal | ignored tool missing | verified 0.11.28 copy | baseline only |

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

### 데이터 흐름/상태 변화

Task 0~2에서는 DB row/container/schema 변화가 없다. Task 2에서 ignored `.tools/supabase/v2.109.1/`에 공식 archive를 실제 설치했지만 `supabase start`, role provisioning, DB runner는 migrations 전이라 실행하지 않았다. tracked seed는 설명 주석뿐이고 공식/mock row는 0이다.

### 오류·빈 상태·롤백

첫 verify 도구 호출은 repo-local uv 부재로 `PREFLIGHT-UV` 종료, 두 번째 호출은 tool timeout 124, 세 번째 fresh 호출은 143.6초에 24/24 통과했다. Task 1 검증 중 root가 1초 제한으로 시작한 첫 unittest 부모가 종료된 뒤 잠시 남아 두 번째 실행과 고정 임시 파일을 경합해 기존 secret-scanner 테스트 1개가 한 번 실패했다. 단일 테스트와 고립된 전체 재실행은 각각 통과해 구현 결함이 아닌 검증 명령 중첩으로 판정했다. Task 2 reviews는 deprecated `[inbucket]`이 실제 `local_smtp=true`를 끄지 못하는 drift, rollback 이름 2개, in-place `.env` 손상 위험을 발견했고 모두 TDD로 수정했다. DB password commit과 filesystem 교체는 단일 transaction이 될 수 없으므로 파일 실패는 기존 env를 보존하고 gate를 닫으며, 재실행이 password를 다시 회전해 복구한다.

Task 3 첫 실행 뒤 read-only Docker inventory에서 PostgreSQL 외 persistent Kong container가
관찰됐다. v2.109.1 source/CLI 확인 결과 bare `supabase start`는 Data API config와 별개로 Kong을
시작하지만 `supabase db start`는 PostgreSQL만 시작한다. runner test를 먼저 exact `db start`
요구와 bare `start` 거부로 RED 확인한 뒤 runner·계획·운영 문서를 보정했다. 이 agent는 runtime을
정지하거나 재시작하지 않았으며, root가 기존 local project를 안전하게 전환하고 persistent
container가 DB 하나뿐임을 별도로 검증한다. `supabase test db`의 일회성 `pg_prove` container는
테스트 실행용이며 persistent runtime 범위에 포함하지 않는다.

후속 품질 review에서 첫 regression test가 source 전체 문자열을 검사해 주석 속 정답과 실제
대소문자 변형 호출을 구분하지 못하는 false-pass가 발견됐다. AST 검사로 한 차례 강화했지만,
재검토에서 exact 호출을 `if ($false)`에 두고 live direct bare `start`를 실행하면 syntactic AST가
통과하는 Important 우회가 재현됐다. 이 mutant가 기존 AST checker에서 `True`가 되는 RED를 확보한
뒤 static control-flow 주장을 제거했다. 현재 test는 실제 `verify_database.ps1`을 synthetic temp
repo에서 실행한다. API venv Python launcher를 fake Docker/Supabase/Python executable로 복사하고,
fake Supabase가 실제 받은 argv만 합성 JSONL에 기록한 뒤 exit 7로 gate를 안전하게 중단한다.
production은 첫/유일 start invocation `['db', 'start']`와 stable 비노출 출력만 만들며, dead exact
block + live direct bare mutant는 `['start']`로 관찰돼 같은 계약을 통과하지 못한다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 진행 중 | 변경 금지 |
| Repo guidance | 1.4.0 | 목표 1.5.0 | DB tooling 완료 후 |
| Application | 0.1.0 | 진행 중 | wire 변경 금지 |
| Web | 0.1.0 | 0.1.0 | 변경 없음 |
| API | 2.0.1-draft | 2.0.1-draft | public contract 유지 |
| DB schema | 0.2.0-draft | 목표 0.3.0-local | 모든 migration/gate 완료 후 |
| Official data | 0.0.0-not-populated | 동일 | seed 금지 |
| Mock data | 0.0.0-not-populated | 동일 | tracked seed 금지 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 미사용 |
| Test suite | 0.4.2-readiness-contract | 목표 0.5.0-db-baseline | 최종 통과 후 |
| Docs | 2.3.13 | 목표 2.4.0 | 실행 baseline 완료 후 |

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

### 미실행 검증과 이유

- `verify_database.ps1`: migration/rollback/pgTAP/API DB integration 파일이 아직 없어 계획대로 미실행.
- 실제 role DDL·파일별 SQL transaction: Task 3~9 Docker integration에서 실행 예정.
- DB schema/API integration tests: migration·repository 경계가 아직 없어 미실행.
- DeepSeek call: DB-001 범위 밖이며 key를 읽거나 전송하지 않음.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: Task 0~2에서 실제 env/key/질문/DB 데이터 접근 0. env helper 검증은 synthetic temp fixture만 사용했다.
- Security: CLI URL·크기·SHA-256·child version을 exact 비교하고, 인자/child/예외/경로 값을 출력하지 않으며, cleanup은 `.tools/supabase/` 하위의 자체 임시 경로로 제한했다. 실제 `.env`/DeepSeek key는 읽지 않았고 atomic failure injection에서 기존 provider line byte와 CRLF 보존·temp cleanup을 확인했다. bare `start` 대신 `db start`를 강제해 불필요한 persistent Kong listener를 제거하는 방향으로 경계를 좁혔다. behavioral start regression은 synthetic temp repo와 fake executables만 사용하며 실제 Docker/network/provider env를 호출하지 않는다. fake Supabase는 합성 argv만 ACL이 적용되는 OS temp에 기록하고 runner의 stable stdout/stderr 비노출 경계도 함께 확인한다. repository secret scan 통과.
- Accessibility: UI 변경 없음.
- Performance/cost: baseline local CPU/disk 사용; 외부 유료 API/인프라 비용 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: 0 rows. `supabase/seed.sql`은 DATA-001/DATA-SEED-001 소유를 설명하는 주석 3줄뿐이다.
- mock/AI 생성: 0 rows.
- schema/lineage: 아직 0.2.0-draft; migration 0.
- tooling source: official Supabase CLI tag `v2.109.1`; `apps/cli-go/pkg/config/config.go`의 `local_smtp` mapping/deprecated `inbucket` normalization과 `internal/start/start.go`, `internal/db/start/start.go`, `internal/db/test/test.go`의 실행 경계를 기준으로 DB-only drift를 보정했다.
- verified date: 2026-07-16 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 계획 실행은 승인됐으며 local CLI download, image pull, disposable DB reset 범위가 열렸다.
- official CLI 2.109.1은 실제 설치됐고 PostgreSQL-only config·빈 seed·검증 runner는 준비됐지만 DB container/schema/role은 아직 만들지 않았다.
- bare `supabase start`가 만든 Kong은 승인 범위가 아니며, root가 local project를 한 번 안전하게 전환한 뒤 persistent container가 PostgreSQL 하나뿐인지 확인해야 한다. 사용자가 직접 조치할 항목은 아니다.
- remote Supabase, public deployment, official ACTIVE data, retention/권한 변경, 새 production dependency는 여전히 별도 승인 사항이다.
- 최종 branch 통합 방식은 모든 검증 완료 후 finishing skill에서 사용자에게 선택받는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- root는 coordinator로 남고 task별 fresh agent가 코딩한다.
- review 순서는 명세 적합성 → 코드 품질이며 둘 다 승인되기 전 다음 task로 이동하지 않는다.
- ignored uv copy는 worktree bootstrap일 뿐 commit 대상이 아니다.
- Supabase v2.109.1에서 deprecated `[inbucket]` 대신 실제 `[local_smtp]`를 꺼야 한다는 upstream drift는 승인된 DB-only 의도를 유지하는 내부 호환성 보정이다.
- 같은 버전에서 persistent DB-only 시작 명령은 `supabase db start`이다. `test db`가 만드는 일회성 `pg_prove` container는 persistent project container inventory와 구분한다.

## 13. 인수인계·재현·롤백

### 재현

1. worktree branch가 `cf76b17`에서 분기했고 Task 1 commits `41c6dcf`, `857e2b2`가 있는지 확인한다.
2. worktree ignored `.tools/uv/uv.exe --version`이 0.11.28인지 확인한다.
3. `scripts/verify.ps1`에서 24/24 exit 0을 재현한다.
4. `scripts/bootstrap_supabase.ps1 -VerifyOnly`가 exact version PASS를 내는지 확인한다.
5. Task 2 focused unittest 31 pass와 Ruff/Mypy/secret/diff를 재현한다.
6. local project를 안전하게 정지한 뒤 `.tools/supabase/v2.109.1/supabase.exe db start`를 child output 비노출 방식으로 실행하고 persistent inventory가 PostgreSQL 하나인지 확인한다.
7. approved plan Task 3부터 순차 실행한다.

### 롤백

Task 2는 `9733ec7`, `339f04f`, `840d949`를 역순 revert하고 Task 1은 `857e2b2`, `41c6dcf`를 역순 revert한다. ignored `.tools/uv` 및 `.tools/supabase/v2.109.1`은 각 소유 경로를 검증한 뒤에만 제거한다. 아직 DB container/schema/data rollback 대상은 없다.

### 다음 개발자 시작점

Task 3의 private schema/enums/tables pgTAP RED부터 시작하고 첫 migration 전에 실패를 확인한다.

## 14. 남은 위험·미해결 질문·다음 단계

- 품질 review 비차단 개선: 다운로드 timeout/크기 상한, 합성 success extraction test, child output async drain.
- Docker image pull 크기/시간 미측정.
- migration/permission/retention/concurrency test 미구현.
- PostgreSQL-only 명령 보정 뒤 기존 Kong을 제거하는 one-time local runtime 전환과 inventory 재검증이 남아 있다.
- 다음 단계: Task 3 private schema, seven enums, eight tables TDD.

## 15. 자체 리뷰

- [x] 사용자 승인과 baseline 기록
- [x] worktree 격리와 clean baseline
- [x] source-of-truth/계약/버전 목표 유지
- [x] 개인정보 원문·secret 노출 없음
- [x] INDEX 갱신
- [x] Task 1 명세 review와 품질 review 승인
- [x] Task 2 명세 review와 품질 review 승인
