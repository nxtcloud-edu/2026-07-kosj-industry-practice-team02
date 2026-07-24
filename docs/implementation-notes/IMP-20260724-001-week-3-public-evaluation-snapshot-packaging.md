# IMP-20260724-001 — Week 3 public evaluation snapshot packaging

- Date/Time (KST): 2026-07-24T14:42:11+09:00
- Task ID: WEEK3-MVP-SNAPSHOT-001
- Type: release-packaging-security-documentation
- Status: Done — Draft PR publication pending
- Author/Agent: Codex
- Branch: `submission/week3-mvp`
- Evaluation base commit: `343ac1a`
- Source commit: `4cc2f4e5e478668e1d7216fddc08874c9285274b`
- Related: `README.md`, `WEEK3_EVALUATION.md`, `docs/00_SOURCE_OF_TRUTH.md`

## 1. 사용자 요청과 완료 기준

### 요청

private `Sejong_AI/main`을 새 폴더에 clone하고 검증된 tracked 파일을 공개 평가 저장소의
`submission/week3-mvp` snapshot으로 패키징한다. 기존 PDF와 `notice.md`를 보존하고, 비밀·PII·로컬
산출물·private Git history를 제외하며 lint/typecheck/test/build 뒤 Draft PR까지만 게시한다.

### Acceptance Criteria

- source SHA와 evaluation commit/PR을 기록한다.
- source 저장소와 기존 사용자 폴더·`.env`를 변경하거나 복사하지 않는다.
- 실제 `apps/api`, `apps/web`, 정식 `.2` seed, `/ready=200`, 19→20 승인 흐름,
  `PERSONAL_LOOKUP` 무저장을 평가 문서에 정확히 설명한다.
- secret scan과 API/Web/contracts 검증을 통과한 경우만 push한다.
- 평가 `main` 직접 push와 자동 merge를 하지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 공개 snapshot 범위를 승인했고 Codex가 격리 export·검증·게시를 수행 |
| When — 언제 | 2026-07-24 14:25~14:46 KST |
| Where — 어디서 | 새 `week3_snapshot_20260724_4cc2f4e/source-private`, `evaluation-public` clone |
| What — 무엇을 | private main의 tracked MVP를 민감·내부 산출물 없이 공개 평가 branch로 패키징 |
| Why — 왜 | 3주차 평가자가 실제 앱 구조·안전 정책·검증 가능한 실행 절차를 재현하도록 하기 위해 |
| How — 어떻게 | shallow clone → source SHA 고정 → tracked archive allow/deny export → 문서 교정 → 새 clone 검증 |
| How much — 어느 정도 | source tracked 651개에서 공개 대상 451개를 export하고 README/WEEK3/note를 추가; 제품 로직 변경 0 |

## 3. 시작 전 상태

- source private `main`: PR #9 squash commit `4cc2f4e`, clean.
- evaluation `main`: `README.md`, `notice.md`, 입찰제안서 PDF, `data/README.md`.
- 후속 Web 접근성·actual 연동·runbook 수정은 PR #9 commit에 포함됐다.
- 평가 원격에 `submission/week3-mvp` branch는 없었다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| SNAPSHOT-PUBLIC-001 | 보안 | 내부 이력·운영 trace 공개 여부 | 평가에 필요한 활성 코드/계약/데이터만 포함 | private history·local 경로 유출 방지 |
| SNAPSHOT-DB-001 | 실행 | actual DB 재실행 여부 | 이번 export에서는 DB를 변경하지 않고 source의 검증 증거와 정식 절차 기록 | remote/public DB 사용 0 |

## 5. 설계 결정과 대안

### 선택

- private와 public 저장소를 별도 fresh clone으로 분리하고 source tracked archive만 export했다.
- `legacy`, internal agent/Cloud/collaboration 설정, discovery/audit/implementation trace, test runtime
  artifact와 `data/processed`를 제외했다.

### 이유

private `.git`이나 ignored local state를 실수로 복사할 경로를 제거하고, 평가자가 실행에 필요한
코드·계약·공식 데이터·검증 도구에 집중하게 한다.

### 고려했지만 선택하지 않은 대안

- source 폴더에서 remote만 교체: private history push 위험 때문에 금지.
- 전체 폴더 복사: `.env`, cache, DB data, trace 혼입 위험 때문에 금지.
- 평가 `main` 직접 push: 사용자 요청과 리뷰 경계 위반이므로 금지.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| source tracked snapshot | 활성 앱·계약·DB·공식 데이터·검증 도구 export | 재현 가능한 MVP |
| `README.md` | 실제 구조·설치·실행·seed·검증·안전 경계로 교체 | 기존 README의 오래된 backend/frontend 경로 제거 |
| `WEEK3_EVALUATION.md` | provenance, 제외 목록, 19→20, PERSONAL_LOOKUP, 실제 gate 기록 | 평가 근거 단일 문서 |
| PDF, `notice.md` | byte 변경 0 | 기존 제출물 보존 |
| 이 note와 INDEX | 6W1H·보안·검증·롤백 기록 | 인수인계와 저장소 규칙 |

### 데이터 흐름/상태 변화

DB·공식 release는 실행하거나 수정하지 않았다. immutable `.2`의 파일 snapshot과 별도
`reset → seed-cycle → verify-final → provision` 절차만 공개한다.

### 오류·빈 상태·롤백

첫 API pytest는 root cwd에서 `--project`를 사용해 import path가 잘못되어 collection 실패했다.
코드 변경 없이 정식 `--directory apps/api` 명령으로 재실행해 1,782 PASS를 확인했다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.8.0-pr8-frontend-baseline | 동일 | 제품 코드 변경 없음 |
| Web | 0.5.0-pr8-citizen-admin-baseline | 동일 | Web 로직 변경 없음 |
| API | 3.1.0-draft | 동일 | API/계약 변경 없음 |
| DB schema | 0.4.0-local | 동일 | migration 변경 없음 |
| Official data | 0.1.0-initial.2 | 동일 | immutable release 변경 없음 |
| Mock data | 0.0.0-not-populated | 동일 | mock 승격 없음 |
| Prompt set | 0.1.0-upstage-solar-pro3-synthetic | 동일 | provider 호출 0 |
| Test suite | 1.5.0-pr8-web-baseline | 동일 | 기존 test 재실행 |
| Docs | 2.16.0 | 2.16.1 | 평가 README/WEEK3/note |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 |
|---|---|---|---|
| source/evaluation fresh clone·SHA | PASS | source `4cc2f4e` | local terminal |
| `check_secret_patterns.ps1` source/export | PASS | finding 0 | local terminal |
| API Ruff format/check | PASS | 87 files | local terminal |
| API strict Mypy | PASS | 87 files | local terminal |
| API pytest (`--directory apps/api`) | PASS | 1,782 passed, DB-only 8 skipped, warning 1 | local terminal |
| Web ESLint/TypeScript/Vitest | PASS | 11 files, 48 tests | local terminal |
| Web Next production build | PASS | `/`, `/chat`, `/admin*` routes | local terminal |
| shared contracts | PASS | 89 tests | local terminal |
| PDF/notice diff | PASS | 변경 0 | `git diff --` |

### 미실행 검증과 이유

- Docker/Supabase actual DB와 `/ready=200` 재실행은 source code/DB를 수정하지 않는 packaging 범위라
  실행하지 않았다. source PR #9의 이미 검증된 local 증거와 재현 절차를 기록했다.
- Upstage actual, remote DB, public deploy는 승인 범위 밖이며 실행 0이다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 실제 질문·PII·로그·local user path를 export하지 않았다.
- Security: `.env`, key/token/DSN, private `.git`, Docker/Supabase state, dependency/build artifact를 제외했다.
- Accessibility: 제품 변경 없음. source의 Web 자동 접근성 gate를 보존했다.
- Performance/cost: provider/remote 호출 0. local dependency install과 검증만 수행했다.

## 10. 데이터와 출처 영향

- 공식 데이터: immutable `0.1.0-initial.2` bytes를 source에서 export, 수정 0.
- mock/AI 생성: 표시된 mock 자료만 포함, 공식으로 승격 0.
- schema/lineage: source migration·contract·lineage 그대로, 변경 0.
- verified date: 2026-07-24 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 이 공개 snapshot은 local/private MVP 평가본이며 production/public readiness가 아니다.
- Draft PR은 사용자가 파일·CI를 검토한 뒤에만 merge한다.
- evaluation commit SHA와 PR URL은 게시 후 최종 보고에 제공한다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- source archive에는 tracked pathspec만 사용했고 private `.git`을 통과시키지 않았다.
- 의존성은 public clone에서 새로 생성됐으며 ignored `.venv`, `node_modules`, `.next`는 stage하지 않는다.

## 13. 인수인계·재현·롤백

### 재현

1. Draft PR의 source SHA가 `4cc2f4e…`인지 확인한다.
2. `README.md`의 exact runtime과 검증 명령을 사용한다.
3. actual DB가 필요하면 `db.seed=false`를 유지하고 별도 `.2` seed 절차를 따른다.

### 롤백

- Draft PR을 merge하지 않거나 `submission/week3-mvp` branch를 삭제하면 평가 `main`은 그대로다.
- merge 뒤 롤백은 force push 대신 GitHub Revert PR을 사용한다.

### 다음 개발자 시작점

- `README.md` → `WEEK3_EVALUATION.md` → `docs/00_SOURCE_OF_TRUTH.md` 순서로 읽는다.

## 14. 남은 위험·미해결 질문·다음 단계

- Draft PR human review/merge만 Pending.
- public deployment, remote DB, 실제 provider 연결은 계속 별도 승인 대상.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
