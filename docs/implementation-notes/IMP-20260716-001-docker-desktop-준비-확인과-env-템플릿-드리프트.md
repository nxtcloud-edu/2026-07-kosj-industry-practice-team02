# IMP-20260716-001 — Docker Desktop 준비 확인과 env 템플릿 드리프트

- Date/Time (KST): 2026-07-16T00:40:00+09:00
- Task ID: ENV-001
- Type: security
- Status: Done
- Author/Agent: Codex `/root`
- Branch: main
- Base commit: 993034b
- Related plan/ADR/RFP: `TASKS.md` (`DEV-002`, `DB-001`), `docs/plans/PLAN-20260714-001-foundation-and-governed-chat.md`, `docs/adr/ADR-0002*`, `docs/10_HUMAN_AI_BOUNDARY.md`

## 1. 사용자 요청과 완료 기준

### 요청

Docker Desktop을 처음 사용하지만 앱을 실행했다는 사용자 보고를 확인하고, 다음에 사용자가 해야 할 일을 안내한다.

### Acceptance Criteria

- Docker CLI뿐 아니라 Linux daemon 연결까지 실제로 확인한다.
- Docker나 `.env`의 비밀값·내용을 출력하지 않는다.
- 사용자가 Docker UI를 직접 조작할 필요가 있는지 명확히 설명한다.
- 발견한 기존 Git 드리프트를 임의 복구·stage·commit하지 않는다.
- 제품 코드는 변경하지 않고 요청별 구현 노트와 INDEX만 갱신한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자는 Docker Desktop을 실행했고, Codex가 daemon·Git·환경 파일 존재 여부를 점검했다. |
| When — 언제 | 2026-07-16 00:40 KST 이후. |
| Where — 어디서 | 로컬 Windows Docker Desktop Linux engine과 저장소 `main`. |
| What — 무엇을 | Docker 준비 완료를 검증하고 `apps/api/.env.example` 삭제 드리프트를 발견했다. |
| Why — 왜 | local Supabase 작업 전 엔진 가용성과 비밀·템플릿 경계를 안전하게 확인하기 위해서다. |
| How — 어떻게 | Docker info/version을 값 제한 format으로 실행하고 Git status·Test-Path·check-ignore만 사용했다. `.env` 내용은 읽지 않았다. |
| How much — 어느 정도 | Docker 29.2.1, Linux x86_64, 18 CPU, 약 8.1GB 메모리, container/image 0. 제품 파일 변경 0, 문서 2개 변경. |

## 3. 시작 전 상태

- 관련 파일: `apps/api/.env`, `apps/api/.env.example`, `.gitignore`, `TASKS.md`.
- 기존 동작: 직전 기록은 HEAD `993034b`와 clean worktree였고 Docker daemon은 이전 점검에서 꺼져 있었다.
- 발견한 충돌/부채: 이번 점검 시 daemon은 준비됐지만 tracked `apps/api/.env.example`이 삭제돼 있었고 ignored `apps/api/.env`는 존재했다. 삭제 원인과 의도는 확인되지 않았다.
- Git 상태: 구현 노트 생성 전 `main` / `993034b`, `D apps/api/.env.example` 1건. 이 삭제는 Codex 변경으로 간주하지 않고 보존했다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| ENV-001-A | B/High | `.env.example` 삭제가 사용자의 의도적 rename인가 | 답을 받기 전 복구·stage 금지 | 온보딩·환경 계약·Phase 2 보안 검증 |
| ENV-001-B | Resolved | daemon 준비 여부 | Docker 29.2.1 Linux engine 연결 성공 | local Supabase 실행 전제 충족 |
| ENV-001-C | Internal | sandbox에서 Docker named pipe 접근 거부 | 상태 조회만 승인된 외부 실행으로 재검증 | 사용자 Docker 상태와 sandbox 오류 분리 |

## 5. 설계 결정과 대안

### 선택

Docker Desktop은 켜둔 상태만 유지하도록 안내한다. `.env.example` 삭제는 원인을 추측해 복구하지 않고 사용자에게 의도를 확인한다. `.env`는 존재·ignore 여부만 확인하고 내용을 열지 않는다.

### 이유

Docker 엔진은 이미 정상이라 UI 조작이 필요 없다. 반면 dirty worktree 변경은 사용자 소유일 수 있어 명시적 지시 없이 되돌리면 안 된다. 비밀 파일은 내용 검사가 아니라 경계 검사만으로 충분하다.

### 고려했지만 선택하지 않은 대안

- Docker Desktop 화면 설정 변경: 필요하지 않아 제외했다.
- `.env` 내용 확인: 비밀 노출 위험으로 금지했다.
- `.env.example` 즉시 복원: 사용자 변경 보존 규칙 때문에 보류했다.
- `.env.example` 삭제를 현재 문서 커밋에 포함: 범위 밖이라 금지했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| 이 구현 노트 | Docker 증거·환경 드리프트·책임 경계 기록 | 요청별 기록 의무 |
| `docs/implementation-notes/INDEX.md` | IMP-20260716-001 Done 행 갱신 | 검색·상태 동기화 |
| `apps/api/.env.example` | 변경하지 않음; 기존 삭제 상태 보존 | 사용자 변경 보호 |
| `apps/api/.env` | 읽지 않음; ignored 존재 여부만 확인 | 비밀 보호 |

### 데이터 흐름/상태 변화

앱·DB·공식 데이터 상태 변화는 없다. Docker daemon 가용성만 확인했다.

### 오류·빈 상태·롤백

첫 임시 `DOCKER_CONFIG` 폴더 생성은 `C:\tmp` 권한 거부로 실패했고 저장소 변경은 없었다. sandbox 내부 Docker 연결도 named pipe 권한으로 실패해 상태 조회만 승인된 외부 실행으로 재검증했다.

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
| Application/Web | 0.1.0 / 0.1.0 | 동일 | 변경 없음 |
| API/DB | 2.0.1-draft / 0.2.0-draft | 동일 | 변경 없음 |
| Official/Mock data | 0.0.0-not-populated | 동일 | 변경 없음 |
| Prompt/Test | 0.0.2 / 0.4.2 | 동일 | 변경 없음 |
| Docs | 2.3.10 | 2.3.10 | 운영 상태 노트만 추가 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `docker info --format ...` (승인된 로컬 daemon 조회) | ready True, exit 0 | 1회 | 셸 출력 |
| `docker version --format ...` | client/server 29.2.1, API 1.53 | 1회 | 셸 출력 |
| Docker 제한 info | Linux x86_64, CPU 18, memory 8107257856, containers/running/images 0 | 2회 | 셸 출력 |
| sandbox 내부 `docker info` | named pipe permission denied | 1회 | 셸 출력 |
| `git status --short --branch` | `D apps/api/.env.example` | 1회 | Git worktree |
| `Test-Path` | `.env=True`, `.env.example=False` | 2개 경로 | 셸 출력 |
| `git check-ignore -v apps/api/.env` | `.gitignore:2:.env`, ignored True | 1회 | `.gitignore` |
| `git ls-files --error-unmatch apps/api/.env.example` | tracked True | 1회 | Git index |
| `python scripts/new_implementation_note.py ...` | IMP-20260716-001과 Draft INDEX 생성 | 1회 | 이 노트, INDEX |
| 표준 편집 전용 patch 호출 | 응답 없이 정지, 파일 변경 없음 | 1회 | 도구 상태 |

### 미실행 검증과 이유

제품·계약·DB를 변경하지 않아 test/lint/typecheck/build는 실행하지 않았다. Docker container 실행이나 image pull도 아직 필요하지 않아 수행하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: `.env` 내용과 값은 전혀 읽거나 출력하지 않았다. 시민 데이터도 다루지 않았다.
- Security: `.env` ignore 규칙은 유효하다. tracked template 삭제는 보안·온보딩 drift라 사용자 확인 전 보존한다.
- Accessibility: UI 변경 없음.
- Performance/cost: Docker Desktop에 약 8.1GB 메모리가 할당됐고 현재 container/image는 0이다. 유료 서비스·API 호출·image pull 없음.

## 10. 데이터와 출처 영향

- 공식 데이터: 변경 없음.
- mock/AI 생성: 변경 없음.
- schema/lineage: 변경 없음.
- verified date: 2026-07-16 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Docker는 정상 준비됐다. 개발 작업 중 켜두기만 하면 되고 Docker UI를 직접 조작할 필요가 없다.
- `apps/api/.env.example`이 삭제되고 `apps/api/.env`가 생겨 있다. `.env.example`을 `.env`로 이름 변경했는지 여부를 알려줘야 한다.
- 이름 변경한 것이라면 `.env`는 그대로 보존하고 tracked 예제만 복구하는 방식으로 처리할 수 있다.
- `.env` 내용이나 API key는 채팅으로 보내면 안 된다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- Docker 조회는 사용자 config를 읽지 않도록 process-local `DOCKER_CONFIG=$env:TEMP`에서 수행했다.
- local Supabase 단계에서는 exact CLI version·image·migration draft를 먼저 만들고, migration 적용 전 별도 인간 승인을 받는다.
- 현재 삭제된 env template은 stage/commit 대상에서 명시적으로 제외한다.

## 13. 인수인계·재현·롤백

### 재현

1. 제한 format의 `docker version`과 `docker info`로 daemon을 확인한다.
2. `git status --short`로 tracked 삭제를 확인한다.
3. `Test-Path`와 `git check-ignore`만 사용해 `.env` 값 없이 경계를 확인한다.

### 롤백

제품 변경은 없다. 이 상태 기록을 되돌릴 때는 IMP-20260716-001과 INDEX 행만 함께 제거한다. `.env`와 `.env.example`에는 손대지 않는다.

### 다음 개발자 시작점

사용자에게 env 파일 rename 의도를 확인한다. 승인 전에는 삭제를 stage·commit·복구하지 않는다. 해결 후 Docker 상태를 재확인하고 DB-001 상세 계획·migration draft로 진행한다.

## 14. 남은 위험·미해결 질문·다음 단계

- `.env.example` 삭제 의도가 미확인이다.
- `.env`에 실제 key가 있는지는 알 수 없으며 확인할 필요도 없다.
- Supabase CLI와 images는 아직 없으므로 추후 첫 설치/pull에 네트워크와 디스크가 필요하다.
- Docker Desktop을 종료하면 local DB도 중단되지만 데이터 volume 정책은 DB 계획에서 별도로 정의한다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
