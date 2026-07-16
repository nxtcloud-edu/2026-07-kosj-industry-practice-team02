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

### 데이터 흐름/상태 변화

Task 0에서는 DB row/container/schema 변화가 없다. 이후 task 결과를 순차 기록한다.

### 오류·빈 상태·롤백

첫 verify 도구 호출은 repo-local uv 부재로 `PREFLIGHT-UV` 종료, 두 번째 호출은 tool timeout 124, 세 번째 fresh 호출은 143.6초에 24/24 통과했다. Task 0 rollback은 이 문서 commit revert이며 ignored tool copy는 Git/data 영향이 없다.

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

### 미실행 검증과 이유

- Supabase/Docker DB gate: Task 1/2 tooling과 migrations가 아직 없음.
- DB/API implementation tests: production/test code를 아직 변경하지 않음.
- DeepSeek call: DB-001 범위 밖이며 key를 읽거나 전송하지 않음.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: Task 0에서 env/key/질문/DB 데이터 접근 0.
- Security: ignored tool path만 복구; repository secret scan은 baseline gate에서 통과.
- Accessibility: UI 변경 없음.
- Performance/cost: baseline local CPU/disk 사용; 외부 유료 API/인프라 비용 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: 0 rows, 0 files changed.
- mock/AI 생성: 0 rows.
- schema/lineage: 아직 0.2.0-draft; migration 0.
- verified date: 2026-07-16 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 계획 실행은 승인됐으며 local CLI download, image pull, disposable DB reset 범위가 열렸다.
- remote Supabase, public deployment, official ACTIVE data, retention/권한 변경, 새 production dependency는 여전히 별도 승인 사항이다.
- 최종 branch 통합 방식은 모든 검증 완료 후 finishing skill에서 사용자에게 선택받는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- root는 coordinator로 남고 task별 fresh agent가 코딩한다.
- review 순서는 명세 적합성 → 코드 품질이며 둘 다 승인되기 전 다음 task로 이동하지 않는다.
- ignored uv copy는 worktree bootstrap일 뿐 commit 대상이 아니다.

## 13. 인수인계·재현·롤백

### 재현

1. worktree branch가 `cf76b17`에서 분기했는지 확인한다.
2. worktree ignored `.tools/uv/uv.exe --version`이 0.11.28인지 확인한다.
3. `scripts/verify.ps1`에서 24/24 exit 0을 재현한다.
4. approved plan Task 1부터 순차 실행한다.

### 롤백

Task 0 commit을 revert하고 worktree를 유지한다. ignored `.tools/uv`는 필요 시 worktree 소유 경로만 검증 후 제거한다. main과 DB/data에는 rollback 대상이 없다.

### 다음 개발자 시작점

Task 1의 failing tooling tests부터 시작하고 production bootstrap script 전에 RED를 확인한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Supabase CLI binary download와 공식 digest runtime verification 미실행.
- Docker image pull 크기/시간 미측정.
- migration/permission/retention/concurrency test 미구현.
- 다음 단계: Task 1 project-local CLI pin/bootstrap TDD.

## 15. 자체 리뷰

- [x] 사용자 승인과 baseline 기록
- [x] worktree 격리와 clean baseline
- [x] source-of-truth/계약/버전 목표 유지
- [x] 개인정보 원문·secret 노출 없음
- [x] INDEX 갱신
