# IMP-20260722-004 — Q-MVP-001 4일 local-private 핵심 개선 루프 명세와 실행

- Date/Time (KST): 2026-07-22T02:10:51+09:00
- Task ID: MVP-001 / Q-MVP-001
- Type: implementation
- Status: In Progress
- Author/Agent: 사용자(제품 결정·PM), Codex owner agent(아키텍처·Backend·Data·Security·문서), frontend collaborator(`/chat` UI)
- Branch: codex/MVP-001-four-day-core-loop
- Base commit: 9044ddb
- Related plan/ADR/RFP: `docs/superpowers/plans/2026-07-22-four-day-local-private-core-loop-mvp.md`, ADR-0020, RFP-P0-001~012

## 1. 사용자 요청과 완료 기준

### 요청

Q-MVP-001=A로 2026-07-25 토요일까지 local/private 핵심 개선 루프 MVP를 완성한다. 기존
source-of-truth와 실제 저장소를 대조해 4일 축소 명세와 날짜별·역할별 계획을 작성한 뒤,
owner/협업 PR 기준선, 19개 ACTIVE 데이터, PII/chat, 시민 `/chat`, 운영 개선 루프, 최소
`/admin`, 표본·보안·데모 순서로 즉시 실행한다.

### Acceptance Criteria

- 기존 2026-07-31 최종 P1 범위를 삭제하지 않고 7/25 local/private 마일스톤을 별도로 정의한다.
- 사람이 승인해야 하는 정책과 AI가 구현할 내부 세부를 분리한다.
- PR #5 통합 기준을 확인하고 PR #4의 문서 ID 충돌을 최소 교정한다.
- 토요일 gate는 19개 초기 ACTIVE와 승인 흐름으로 생성되는 20번째 ACTIVE, 개인정보 원문 0,
  구조화 chat/fallback, 최소 admin, 표본 20개·회귀 1개·보안/데모 검증이다.
- DeepSeek 품질 튜닝, 고급 UI, 100명 성능, 자동 백업, 공개 배포는 명시적으로 연기한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자는 범위·정책·최종 데이터 승인, owner agent는 Backend/Data/Security/통합, 협업자는 Frontend |
| When — 언제 | 2026-07-22 시작, 2026-07-25 local/private 데모 gate 목표(KST) |
| Where — 어디서 | private GitHub `Sejong_AI`, Windows owner worktree, Docker/Supabase local, `/chat`, `/admin` |
| What — 무엇을 | 4일 축소 명세·계획 및 시민 질문에서 운영 개선까지 한 바퀴 도는 MVP |
| Why — 왜 | 외부 배포보다 핵심 가치인 “모르면 지어내지 않고, 알면 끝까지 안내”를 먼저 검증하기 위해 |
| How — 어떻게 | 승인된 ACTIVE KB만 검색하고, 개인정보를 먼저 마스킹하며, 결정적 분류/근거 gate/서버 출처 결합과 별도 승인 상태 머신으로 구현 |
| How much — 어느 정도 | 초기 ACTIVE 19개, 개선 후 20개, 표본 20개, 회귀 1개, local/private만; 초기 외부 사용비 0원 |

## 3. 시작 전 상태

- 관련 파일: AGENTS와 source-of-truth, ADR-0016/0017/0019, DATA-SEED-002 명세·계획,
  계약 6종, DB migration/capability tests, PII 코어, 정적 web shell, collaboration 정책.
- 기존 동작: PII 코어·DB 후보 상태 머신·19개 승인 데이터 릴리스 초안은 있으나 local DB ACTIVE=19
  증거가 없고, `/api/v1/chat`, chat orchestration, `/admin` 화면은 없었다.
- 발견한 충돌/부채: PR #4 구현 노트 ID `012` 중복, 협업 정책 문자열 때문에 canonical staging
  false positive, known-broken `.1` PostgreSQL 17 membership guard, root 검증기의 환경 의존 gate.
- Git 상태: `origin/main`은 PR #5 merge `9044ddb`; 작업 브랜치는
  `codex/MVP-001-four-day-core-loop`; 기존 사용자 문서 변경을 보존했다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-MVP-001 | A/Blocker | 7/25 축소 범위를 별도 마일스톤으로 승인할지 | A 확정 | 일정·계약·데이터·테스트 |
| PR #4 merge | Human gate | 교정 후 팀원 PR을 main에 병합할지 | CLEAN/MERGEABLE까지 자동 교정, 병합은 사람 | 협업 기준선 |
| PM source review | Human gate | 19개 공식 콘텐츠 최종 승인 | 기존 승인 유지, 실제 DB gate 전에 재확인 | official lineage |
| Persistent privacy metadata | Deferred | PRIVACY_UNRESOLVED를 DB 이벤트로 보존할지 | 7/25는 DB row 0; 예약 migration `00700` 단계로 연기 | DB/개인정보 |

## 5. 설계 결정과 대안

### 선택

- 기존 최종 범위 아래에 “7/25 local/private 핵심 개선 루프”를 추가하고 ADR-0020으로 경계를 고정했다.
- 시민 답변은 DeepSeek 없이 결정적 템플릿 경로로 구현하며, 서버만 공식 출처를 결합한다.
- `PRIVACY_UNRESOLVED`는 HTTP 200 fallback이지만 저장·provider 호출·출처·context token을 모두 0으로 한다.
- 20번째 KB는 초기 `.2`에 섞지 않고 실패 질문→후보→별도 승인 경로로만 ACTIVE가 된다.

### 이유

4일 안에 외부 공급자 품질까지 동시에 튜닝하면 개인정보·근거·승인 경계의 검증이 흐려진다.
local DB와 결정적 응답만으로도 제품의 핵심 개선 루프는 완전히 증명할 수 있다.

### 고려했지만 선택하지 않은 대안

- 기존 7/31 계획을 7/25로 단순 덮어쓰기: 최종 P1과 축소 MVP 완료를 혼동하므로 제외.
- DeepSeek를 시민 정상 답변 경로에 즉시 포함: 비용·쿼터·품질 변동과 개인정보 위험 때문에 연기.
- 20번째 KB를 초기 seed에 포함: 개선 전후 회귀 증거가 사라지므로 제외.
- privacy unresolved event를 즉시 DB migration: 예약된 공개 migration 번호·배포 경계를 건드려 연기.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| source-of-truth/decision/ADR | D-058, A-040, ADR-0020, 7/22~25 역할별 gate 반영 | 승인과 구현 경계 단일화 |
| discovery/spec/plan/TASKS | 실제 저장소 차이와 10개 수직 task 기록 | 재현 가능한 실행 순서 제공 |
| collaboration | PR #4 `012→014` 교정, main merge-parent 동기화 | 팀원 PR 충돌 제거 |
| staging scanner | 정책 자체의 path literal false positive 제거, 실제 runtime 차단 유지 | DATA-SEED canonical 검증 복구 |

### 데이터 흐름/상태 변화

질문 → PII 마스킹 → 결정적 분류 → ACTIVE 검색 → 근거 gate → 구조화 ANSWER/FOLLOWUP/FALLBACK
→ 실패 질문 메타데이터 → 후보 작성 → 작성자와 다른 승인자 → 20번째 ACTIVE → 동일 질문 재질의 개선.

### 오류·빈 상태·롤백

근거 부족/범위 밖/개인 조회/법적 판단/마스킹 불확실은 서로 다른 안전 폴백으로 종료한다.
각 데이터 릴리스는 immutable 디렉터리와 dispatcher byte 비교로 롤백 가능하며, PR 단위로 되돌린다.

## 7. 버전 전후

### 생성 시 매니페스트
- product_spec: 2.2.5
- repo_guidance: 1.7.6
- application: 0.3.0-pii-core
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 1.0.0-collaboration
- documentation: 2.10.9

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.3.0-pii-core | 진행 중(완료 시 기록) | 핵심 개선 루프 |
| Web | 0.2.0-static-chat-shell | 진행 중 | `/chat`·최소 `/admin` |
| API | 2.0.1-draft | 진행 중 | chat/admin 공개 경계 |
| DB schema | 0.3.0-local | 유지 예정 | 예약 migration 보존 |
| Official data | 0.0.0-not-populated | 진행 중 | `.2` 및 local ACTIVE=19 |
| Mock data | 0.0.0-not-populated | 유지 | 공식·mock 혼합 금지 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 유지 | 품질 튜닝 연기 |
| Test suite | 1.0.0-collaboration | 진행 중 | data/chat/admin/security gate |
| Docs | 2.10.9 | 2.11.0 | Q-MVP 결정·4일 명세·계획 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `gh pr view 4 ...` | PASS: OPEN, non-draft, MERGEABLE, checks green | 2026-07-22 | PR #4 head `37dfc8b` |
| `gh pr view 5 ...` | PASS: MERGED | 2026-07-22 | merge `9044ddb` |
| collaboration focused tests | PASS | 26/26 | Task 0 report |
| staging/release/dispatcher/docs/secret focused checks | PASS | Task 0 | `.superpowers/sdd/task-0-report.md` |
| independent Task 0 review | PASS | spec/code quality clean | review `9044ddb..777d54b` |
| `python -B scripts/check_repository_docs.py` | PASS | 2026-07-22 | terminal output |

### 미실행 검증과 이유

- 전체 root suite와 실제 disposable DB cycle은 DATA-SEED-002 후속 task에서 실행한다.
- Docker/Supabase/DeepSeek/public deployment는 해당 milestone gate 또는 명시적 연기 범위다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 원문 저장 금지와 provider 전 마스킹을 유지한다. `PRIVACY_UNRESOLVED`는 local MVP에서 DB row 0이다.
- Security: ACTIVE-only, 서버 결합 출처, 작성자≠승인자, 감사 로그 원문 금지, 비밀 스캔을 gate로 둔다.
- Accessibility: 390/430/desktop, 키보드, 4.5:1, 큰 글씨 검증을 7/25 gate에 포함했다.
- Performance/cost: local-first·초기 0원. 100명 성능과 DeepSeek 품질/쿼터 검증은 이후로 연기했다.

## 10. 데이터와 출처 영향

- 공식 데이터: 기존 PM 승인 19개를 수정 릴리스 `.2`로 기술 교정하며 내용 자체를 임의 변경하지 않는다.
- mock/AI 생성: 이 마일스톤의 시민 정상 답변 근거에 사용하지 않는다.
- schema/lineage: `.1` immutable 보존, `.2` predecessor/correction/approval/evidence lineage를 별도 기록한다.
- verified date: 실제 DB cycle 완료 후 test report에 기록한다.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-MVP-001=A와 7/25 local/private 목표는 확정됐다.
- PR #4는 자동 교정과 CI 확인까지 완료했지만 최종 merge는 사용자/팀원의 사람 검토 경계다.
- PM은 `.2` 공개 및 실제 DB 반영 전에 기존 19개 공식 콘텐츠가 최종 승인본인지 확인해야 한다.
- 공개 배포·자동 백업·100명 성능·DeepSeek 품질·고급 UI는 토요일 이후다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- release profile helper, deterministic classifier/retriever 분리, 테스트 fixture 이름, 내부 모듈 배치는 계약과 gate 안에서 자율 처리한다.

## 13. 인수인계·재현·롤백

### 재현

활성 MVP 계획의 dependency graph 순서로 각 task의 focused test를 실행하고, 마지막에 root/offline/security/
sample/demo gate를 실행한다. 원격 기준은 `origin/main@9044ddb`, 로컬 브랜치는 위 Branch 항목이다.

### 롤백

문서 결정은 본 브랜치의 문서 커밋을 revert한다. 제품/데이터는 task별 독립 커밋을 역순 revert하고,
immutable `.1`은 절대 수정하지 않는다. `.2` dispatcher 전환은 검증된 predecessor byte에 한해 복구한다.

### 다음 개발자 시작점

`docs/superpowers/plans/2026-07-22-four-day-local-private-core-loop-mvp.md`의 현재 체크박스와
`.superpowers/sdd/progress.md`를 확인하고, DATA-SEED-002의 첫 미완료 task부터 시작한다.

## 14. 남은 위험·미해결 질문·다음 단계

- PR #4 사람 merge, PM 최종 source 검수, 실제 local DB/Docker cycle은 남아 있다.
- 전체 root suite는 초기 환경에서 장시간 실행과 local runtime prerequisite가 섞여 아직 종합 PASS가 아니다.
- 이후 계약/API/Frontend 병렬 변경은 owner가 계약 파일을 선행 동결한 후에만 허용한다.

## 15. 자체 리뷰

- [ ] 요청 충족 — 실행 루프 진행 중
- [ ] 테스트/검증 — 단계별 진행 중
- [x] source-of-truth/결정/계획/문서 버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
