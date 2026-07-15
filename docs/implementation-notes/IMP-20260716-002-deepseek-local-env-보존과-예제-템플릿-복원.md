# IMP-20260716-002 — DeepSeek local env 보존과 예제 템플릿 복원

- Date/Time (KST): 2026-07-16
- Task ID: ENV-002
- Type: security
- Status: Done
- Author/Agent: Codex `/root`
- Branch: main
- Base commit: 2b38e3f
- Related plan/ADR/RFP: `TASKS.md` (`DEV-002`, `LLM-001`), `docs/adr/ADR-0005*`, `docs/10_HUMAN_AI_BOUNDARY.md`, `IMP-20260716-001`

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 `apps/api/.env.example`을 `apps/api/.env`로 이름 변경하고 로컬 `.env`에 DeepSeek API key를 넣었다고 확인했다.

### Acceptance Criteria

- API key가 든 `.env`의 내용과 값을 읽거나 출력하지 않는다.
- ignored `.env`를 삭제·수정·stage·commit하지 않는다.
- tracked `.env.example`만 HEAD에서 복원한다.
- 복원 후 `.env` 존재·ignore, `.env.example` 존재·HEAD 일치, 관련 Git drift 0을 검증한다.
- 이전 ENV-001 미해결 기록과 구현 노트 INDEX를 동기화한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 rename 원인을 확인했고 Codex가 비밀 파일을 보존하며 예제 템플릿만 복원했다. |
| When — 언제 | 2026-07-16 KST. |
| Where — 어디서 | `apps/api/.env`(ignored local secret), `apps/api/.env.example`(tracked keyless template), 구현 노트. |
| What — 무엇을 | rename으로 발생한 tracked deletion을 HEAD 기준으로 복구했다. |
| Why — 왜 | 로컬 비밀은 Git 밖에 유지하면서 신규 개발자용 환경 계약 템플릿을 보존하기 위해서다. |
| How — 어떻게 | 값 없는 존재·ignore·Git status 검사를 RED 증거로 남긴 뒤 `git restore --source=HEAD --worktree`로 template 한 경로만 복원하고 같은 검사를 GREEN으로 재실행했다. |
| How much — 어느 정도 | 환경 파일 1개 복원(HEAD와 동일해 최종 product diff 0), 문서 3개 변경, API/DB/데이터/외부 호출 0. |

## 3. 시작 전 상태

- 관련 파일: `.gitignore`, `apps/api/.env`, `apps/api/.env.example`, `IMP-20260716-001`.
- 기존 동작: Docker daemon은 정상이고 `.env`는 ignore됐지만 `.env.example`은 tracked deletion 상태였다.
- 발견한 충돌/부채: 예제 파일을 copy하지 않고 rename하여 local secret은 안전했지만 tracked onboarding/security contract가 삭제됐다.
- Git 상태: 시작 시 `main` / `2b38e3f`, ` D apps/api/.env.example` 한 건.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| ENV-001-A | Resolved | 삭제 원인 | 사용자가 `.env.example`을 `.env`로 이름 변경했다고 확인 | 복구 범위 확정 |
| ENV-002-A | Fixed | secret/template 공존 | `.env`는 ignored local, `.env.example`은 tracked keyless | 비밀관리·온보딩 |
| LLM-KEY-STATE | Intentionally unknown | 실제 key 값·유효성 | 읽지 않음; LLM smoke 단계에서 값 비노출 검증만 수행 | 비밀 보호 |

## 5. 설계 결정과 대안

### 선택

ignored `.env`는 경로 존재와 ignore 여부만 확인하고, tracked `.env.example`만 현재 HEAD에서 복원했다.

### 이유

사용자가 입력한 key를 보존하면서 저장소의 keyless 환경 계약을 원상 복구하는 최소 변경이다. HEAD가 승인된 template의 권위이므로 내용을 새로 작성할 필요가 없다.

### 고려했지만 선택하지 않은 대안

- `.env`에서 template을 역생성: key 유출 위험 때문에 금지했다.
- `.env` 삭제 후 다시 만들기: 사용자 비밀을 파괴하므로 금지했다.
- `.env.example`을 새 내용으로 작성: 승인된 HEAD와 drift 가능성이 있어 제외했다.
- rename 삭제를 commit: 환경 계약 파괴이므로 제외했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `apps/api/.env.example` | HEAD의 tracked template 복원 | rename으로 발생한 deletion 해소 |
| `apps/api/.env` | 내용 미열람·변경 없음 | local secret 보존 |
| `IMP-20260716-001` | rename 미확인 위험을 ENV-002 해결로 갱신 | 역사 기록 정합성 |
| 이 구현 노트·INDEX | 원인·복구·검증 기록 | 요청별 기록 의무 |

### 데이터 흐름/상태 변화

API key는 local `.env`에만 남고 Git index로 이동하지 않는다. 외부 LLM 호출, DB 쓰기, 로그 출력은 없다.

### 오류·빈 상태·롤백

첫 sandbox `git restore`는 `.git/index.lock` 권한 거부로 파일 변경 없이 실패했다. 동일한 단일 경로 복원을 승인된 외부 실행으로 재시도해 성공했다.

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
- documentation: 2.3.10

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application/Web | 0.1.0 / 0.1.0 | 동일 | 동작 변경 없음 |
| API/DB | 2.0.1-draft / 0.2.0-draft | 동일 | 계약·schema 변경 없음 |
| Official/Mock data | 0.0.0-not-populated | 동일 | 변경 없음 |
| Prompt/Test | 0.0.2 / 0.4.2 | 동일 | provider 호출·테스트 변경 없음 |
| Docs | 2.3.10 | 2.3.10 | 보안 상태 기록만 추가 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| pre-fix `Test-Path`·`git check-ignore`·status | env=True/ignored=True, example=False, tracked deletion 1 | 1회 | 셸 출력 |
| `git restore --source=HEAD --worktree -- apps/api/.env.example` (sandbox) | index.lock permission denied, 변경 없음 | 1회 | 셸 출력 |
| 같은 단일 경로 restore (승인 실행) | exit 0 | 1회 | worktree |
| post-fix `Test-Path`·`git check-ignore` | env=True/ignored=True, example=True | 1회 | 셸 출력 |
| `git diff --quiet HEAD -- apps/api/.env.example` | HEAD 일치=True | 1회 | Git |
| env 두 경로 제한 status | count 0 | 1회 | Git |
| `python scripts/new_implementation_note.py ...` | IMP-20260716-002 및 Draft INDEX 생성 | 1회 | 이 노트, INDEX |

### 미실행 검증과 이유

제품 코드·계약·DB 변경이 없어 test/lint/typecheck/build는 실행하지 않았다. DeepSeek key 유효성 검사와 외부 호출도 이 보안 복구 범위가 아니므로 실행하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: `.env` 내용·key·길이·hash를 읽거나 출력하지 않았다. 시민 데이터도 다루지 않았다.
- Security: `.env`는 `.gitignore:2`에 의해 ignore되고, `.env.example`은 HEAD keyless template로 복원됐다.
- Accessibility: UI 변경 없음.
- Performance/cost: 외부 API 호출·Docker container·image pull·비용 0.

## 10. 데이터와 출처 영향

- 공식 데이터: 변경 없음.
- mock/AI 생성: 변경 없음.
- schema/lineage: 변경 없음.
- verified date: 2026-07-16 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- API key는 지금처럼 `apps/api/.env`에만 두고 채팅·문서·Git에 붙여 넣지 않는다.
- 다음부터는 `.env.example`을 **복사**해서 `.env`를 만들고, 예제 파일은 남겨둔다.
- 이번 복구에서 key 값은 보거나 검증하지 않았다. 실제 DeepSeek smoke는 LLM-001 단계에서 합성 fixture에 한해 별도로 실행한다.
- 현재 추가 승인 사항은 없다. DB migration 적용과 공식 데이터 ACTIVE 전환은 각각 초안을 보여준 뒤 승인받는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- restore path allowlist를 `apps/api/.env.example` 한 개로 제한했다.
- secret 보존 검증은 내용을 읽는 hash 대신 존재·ignore·명령 target·Git status 조합으로 수행했다.
- env repair 후 product worktree drift는 0이므로 DB-001 계획 작업을 재개할 수 있다.

## 13. 인수인계·재현·롤백

### 재현

1. `Test-Path apps/api/.env`와 `git check-ignore --quiet`로 local secret 경계를 확인한다.
2. `Test-Path apps/api/.env.example`과 `git diff --quiet HEAD -- <path>`로 template 복원을 확인한다.
3. `.env`의 내용 출력 명령은 실행하지 않는다.

### 롤백

문서 기록만 되돌리려면 IMP-20260716-002, INDEX 행, ENV-001 해결 문구를 함께 되돌린다. `.env.example` 복원은 승인된 HEAD 상태이므로 보안상 유지한다. `.env`는 어떤 롤백에서도 삭제하지 않는다.

### 다음 개발자 시작점

Docker daemon과 env 경계가 준비됐다. `DB-001` 상세 계획과 migration/rollback/권한 테스트 초안을 작성하고 실제 적용 전에 인간 승인을 받는다.

## 14. 남은 위험·미해결 질문·다음 단계

- key 유효성·잔액·model 접근은 아직 검증하지 않았다.
- Supabase CLI와 local images는 아직 설치되지 않았다.
- 공개/실제 시민 DeepSeek 호출 금지와 synthetic fixture 전용 경계는 계속 유효하다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
