# IMP-20260719-008 — DATA-SEED-001 불변 공식 release와 local seed 검증

- Date/Time (KST): 2026-07-19T09:52:17+09:00
- Task ID: DATA-SEED-001
- Type: implementation-data-security
- Status: In Progress
- Author/Agent: primary architect/controller + task별 구현·검토 subagent
- Branch: main → `codex/data-seed-001-initial-release` isolated worktree
- Base commit: c312488
- Related plan/ADR/RFP: DATA-SEED-001 plan, approved DATA-SEED design, ADR-0015/0016, D-033/D-035/D-036/D-038/D-039, DAR-001/DAR-002/SER-001/SER-003/COR-001

## 1. 사용자 요청과 완료 기준

### 요청

- 사용자가 `ㅇㅋ 전체 승인 구현 ㄱㄱ`로 DATA-SEED-001의 written specification과 실행계획 전체 구현을 승인했다.
- 승인 범위에는 local disposable DB reset, seed, compensation, replay가 포함된다.
- 가능한 구현은 멈추지 않고 subagent를 사용해 진행하되 사람 작업과 public/remote 범위는 분리한다.

### Acceptance Criteria

- PM-approved staging에서 정확히 19 KB·3기관·10매핑의 immutable `0.1.0-initial.1` release를 생성한다.
- release/dispatcher hash, empty-local transactional seed, second-seed rejection, rollback, compensation, replay, concurrency를 검증한다.
- migration/API/readiness/UI/LLM/public/remote/new dependency를 변경하지 않는다.
- task별 TDD·독립 review, 전체 Sol review, root gate, lineage/version/docs 동기화를 모두 통과한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자/PM이 승인, primary agent가 조정, task별 구현자와 별도 reviewer가 구현·검토 |
| When — 언제 | 2026-07-19 KST 시작; spec 승인 09:20:31, 실행 승인 09:52:08 |
| Where — 어디서 | local Git worktree, `data/`, `scripts/`, `supabase/seed.sql`, disposable PostgreSQL 17 |
| What — 무엇을 | 승인된 19/3/10을 불변 official release와 재현 가능한 local seed로 승격 |
| Why — 왜 | 승인 근거만 시민 검색 후보로 만들고 실패·재실행·보상에서도 데이터 무결성과 추적성을 지키기 위해 |
| How — 어떻게 | strict input trust, deterministic bytes/hash, two-phase publication, guarded SQL, actual DB cycle, 독립 review |
| How much — 어느 정도 | release 7파일, dispatcher 1파일, DB schema/API 변화 0, 외부 API·비용 0원 |

## 3. 시작 전 상태

- 관련 파일: approved plan/spec, DATA-001 staging/approval manifest, migrations 6개, patched DB runner, version manifest.
- 기존 동작: staging은 APPROVED 19/3/10이지만 official release는 없고 `supabase/seed.sql`은 data-free, `official_data=0.0.0-not-populated`, `/ready=503`.
- 발견한 충돌/부채: `database/README.md`의 Q-SEC-006 설명 일부가 D-031 이후 상태보다 오래됨; Task 7에서 actual 근거로 정정한다.
- Git 상태: `main` clean, base `c312488`; 원격 없음.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-028 | A | DATA-SEED 실행 승인 | D-039로 해결; local disposable DB cycle 포함 | release/seed/DB local mutation |
| A-021 | A/Public | public privileged function hardening | 본 범위 밖, 계속 차단 | public/remote 배포 금지 |

## 5. 설계 결정과 대안

### 선택

- 승인된 DATA-SEED plan을 그대로 실행하고 `released_at=2026-07-19T09:20:31+09:00`을 고정한다.
- `superpowers:subagent-driven-development`로 task별 fresh implementer와 reviewer를 분리한다.

### 이유

- release timestamp는 ambient clock이 아니라 이미 승인된 governance evidence다.
- 좁은 task·TDD·독립 review가 데이터/보안 결함을 조기에 차단하고 durable ledger가 장기 실행 중 중복을 막는다.

### 고려했지만 선택하지 않은 대안

- main에서 직접 구현: 격리·복구성이 낮아 제외.
- runtime timestamp: 동일 input 재현성과 승인 증거를 깨므로 제외.
- non-empty/remote DB 적용이나 새 migration: 승인 범위 밖이라 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|

### 데이터 흐름/상태 변화

### 오류·빈 상태·롤백

## 7. 버전 전후

### 생성 시 매니페스트
- product_spec: 2.2.1
- repo_guidance: 1.5.0
- application: 0.2.0
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 0.8.0-web-browser-gate
- documentation: 2.7.2

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.2.0 | target unchanged | runtime 범위 아님 |
| Web | 0.2.0-static-chat-shell | target unchanged | UI 범위 아님 |
| API | 2.0.1-draft / shared 0.2.1 | target unchanged | 공개 계약 변경 금지 |
| DB schema | 0.3.0-local | target unchanged | migration/role/grant 변경 금지 |
| Official data | 0.0.0-not-populated | target 0.1.0-initial.1 | actual full DB cycle PASS 뒤만 |
| Mock data | 0.0.0-not-populated | target unchanged | mock 미사용 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | target unchanged | LLM 미호출 |
| Test suite | 0.8.0-web-browser-gate | target 0.9.0-data-seed-release | focused/root/actual gates |
| Docs | 2.7.2 | 2.7.3 start; target 2.8.0 | 승인 기록과 최종 lineage |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `git status --short --branch`, `git log -5 --oneline` | PASS | main clean, base c312488 | terminal evidence |
| `python scripts/new_implementation_note.py ...` | PASS | 이 note와 INDEX 생성 | 이 파일/INDEX |
| pinned ignored runtime copy + `uv sync --frozen` + frozen pnpm installs | PASS | uv 33, root 465, E2E 3 packages | isolated worktree |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1` | PASS | full baseline; TEST-ROOT, DATA-001, Web/API/contracts, secret/package/diff | isolated worktree at `eb84690` |

### 미실행 검증과 이유

- DATA-SEED unit/release/DB actual 검증은 Task 1~6 구현 전이므로 아직 실행하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문/PII/transcript/provider payload를 읽거나 저장하지 않는다.
- Security: exact canonical path/reparse·secret-free output·exact local DSN/role/lock/empty guards를 fail closed로 구현한다.
- Accessibility: UI 변경 0; 기존 회귀만 유지한다.
- Performance/cost: local 19/3/10 규모, 외부 API 0, 새 dependency 0, 비용 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: PM-approved staging 19/3/10만 target이며 실제 release는 Task 5 전 0.
- mock/AI 생성: mock 0; AI가 공식 사실을 추가하지 않는다.
- schema/lineage: DB schema unchanged; approval→release→dispatcher→DB semantic hash를 기록할 예정이다.
- verified date: source verified date는 기존 2026-07-18 유지; governance release timestamp는 2026-07-19T09:20:31+09:00.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 사용자는 local release와 disposable DB cycle을 승인했다. public/remote, non-empty DB, successor release, WASTE-03, API/readiness/migration은 승인하지 않았다.
- immutable release는 생성 뒤 in-place 수정·삭제하지 않는다. 실제 DB gate가 실패하면 official version을 올리지 않는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- helper/file split, fixture, stable issue code, SQL formatting과 task agent 배정은 승인된 계약 안에서 자율 처리한다.

## 13. 인수인계·재현·롤백

### 재현

승인 plan Task 0~8의 exact 명령과 `.superpowers/sdd/progress.md` ledger를 따른다.

### 롤백

Task 5 전에는 branch commit을 revert한다. Task 5 뒤 release bytes는 수정·삭제하지 않고 code remediation/new successor 절차를 사용한다. DB는 승인된 compensation을 exact empty disposable local projection에서만 실행한다.

### 다음 개발자 시작점

D-039/A-028와 progress ledger를 확인하고 최초 미완료 task부터 재개한다. `official_data`는 Task 6 actual full cycle 전에는 올리지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- Q-SEC-003/A-021은 public release blocker로 남는다.
- Docker/patched runtime actual 검증은 Task 6에서 증거가 생기기 전 성공으로 주장하지 않는다.

## 15. 자체 리뷰

- [ ] 요청 충족
- [ ] 테스트/검증
- [ ] source-of-truth/계약/버전 동기화
- [ ] 개인정보 원문 노출 없음
- [ ] 구현 노트 INDEX 갱신
