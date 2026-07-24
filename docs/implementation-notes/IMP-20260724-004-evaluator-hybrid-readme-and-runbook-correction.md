# IMP-20260724-004 — evaluator hybrid README and runbook correction

- Date/Time (KST): 2026-07-24T20:44:33+09:00
- Task ID: SNAPSHOT-HYBRID-README-001
- Type: documentation-review
- Status: Ready for Draft PR — human merge required
- Author/Agent: Codex
- Branch: `codex/week3-final-evaluator-audit`
- Base commit: `2f3c056f212fb397a3b51a2cb33c9514a5523f81`
- Related: public evaluation repository PR #3, `README.md`, `WEEK3_EVALUATION.md`

## 1. 사용자 요청과 완료 기준

### 요청

평가 README를 이전 상태로 통째로 되돌리지 않고 제품 소개 중심 정보 구조를 복원한다. 현재
검증된 apps/api·apps/web 구조, 버전, seed·승인·개인정보·LLM·테스트·Pending 경계는 유지한다.
대외 제목 `세종 민원이음`과 팀원 실명 역할을 되살리고, 문서 링크와 실행 명령을 대조한다.

### Acceptance Criteria

- 첫 1분에 문제·대상 사용자·시민/관리자/Backend 구조와 원칙을 이해할 수 있다.
- 10~15분 안에 DB 없는 UI 확인과 actual local 실행 절차를 찾을 수 있다.
- 김정하 PM/Frontend/발표, 곽태성 Backend, 이유라·오현송 AI/Data 역할을 보존한다.
- `[db.seed].enabled=false`, patched CLI, `.2` seed-cycle/verify-final, 19→20 승인 루프를 정확히 쓴다.
- 개인 조회·법적 판단 미저장, 시민 LLM 0회, Upstage 합성 전용 경계를 유지한다.
- 오래된 branch/TBD/내부 agent 문서와 동작하지 않는 명령을 README에 복원하지 않는다.
- 제품 코드·계약·DB schema·공식 데이터와 production dependency를 변경하지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 브랜드·역할·README 구성을 확정하고 Codex가 fresh clone 감사·교정·검증 |
| When — 언제 | 2026-07-24 KST, PR #3 병합 후 평가자 최종 점검 |
| Where — 어디서 | 공개 평가 저장소의 첫 진입 문서·active runbook·source-of-truth 명칭 |
| What — 무엇을 | 제품 중심 혼합형 README, 역할표, actual seed/runtime 실행, 문서 상태 동기화 |
| Why — 왜 | 익명 역할·약한 제품 소개와 runtime을 제거하는 seed 명령이 평가 이해·재현을 방해해서 |
| How — 어떻게 | 과거 README의 유효한 정보 구조와 현재 코드·manifest·스크립트의 실제 동작을 대조 |
| How much — 어느 정도 | docs 2.16.3→2.16.4; runtime·API·Web·DB·공식 release 동작 변경 0 |

## 3. 시작 전 상태

- public `main` base는 PR #3 squash commit `2f3c056`; fresh clone은 clean이었다.
- README 제목과 역할이 대외 브랜드·실제 4인 분담을 잃고 익명 3줄로 축약돼 있었다.
- `verify_data_seed.ps1` 직후 API를 실행하라고 했지만 해당 gate는 finally에서 자신이 소유한
  runtime을 종료한다.
- actual API에는 32-byte 이상 context secret이 필요하고 actual `/admin`은 Web gate 3개가
  필요하지만 첫 진입 실행 절차에 빠져 있었다.
- 설치는 fresh clone에서 Node 24.12.0, pnpm 11.13.0, Python 3.12.13/uv 0.11.28로 재현했다.

## 4. 미지의 영역·가정·결정

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| DOC-BRAND-001 | Human | 대외 제목 | `세종 민원이음`; 내부 문제 설명명은 구분 표기 | README·active docs |
| DOC-ROLE-001 | Human | 팀 역할 | 이전 실명 4인 표와 사용자의 역할 확정을 복원 | 평가 기여도 |
| DOC-RUN-001 | D/Internal | seed 검증과 demo runtime 관계 | 종합 disposable gate와 persistent actual 절차 분리 | fresh-clone 실행 |
| DOC-SCOPE-001 | Human | 배포 주장 | local/private만; remote/public은 Pending 유지 | 평가 경계 |

## 5. 설계 결정과 버린 대안

### 선택

- 문제 → 구조 → 원칙 → 구현·데이터 → 스택 → 실행 → 역할 → 일정 → 데모 → 검증 순서의
  혼합형 README를 사용했다.
- 이전 README의 설명 구조는 복원하되 실제 파일·고정 버전·현재 정책과 맞는 문장만 사용했다.
- actual demo는 `verify_database`가 유지한 runtime에 별도 `seed-cycle`과 `verify-final`을
  실행하고, 종합 `verify_data_seed.ps1`은 독립 disposable gate로 명시했다.

### 선택하지 않은 대안

- 이전 README 전체 되돌리기: 사라진 내부 파일, 오래된 branch, TBD 배포와 부정확한 seed 명령이
  되살아나므로 제외했다.
- fixture를 actual 증거로 표현: MOCK 승인 금지와 19→20 경계를 흐리므로 제외했다.
- product script에 preserve 옵션 추가: 공개 snapshot의 제품 코드 변경 없이 문서로 정확한 기존
  명령을 조합할 수 있어 제외했다.

## 6. 변경 상세

| 파일/영역 | 변경 |
|---|---|
| `README.md` | 제품 소개·문제·구조·원칙·스택·실명 역할·일정·5문항 데모와 정확한 실행·검증 결합 |
| `WEEK3_EVALUATION.md` | main 평가 대상, env 설명, 실행 완료 시제, persistent/disposable seed 구분 |
| `scripts/README.md`, `docs/15_DEPLOYMENT_AND_OPERATIONS.md` | actual runtime을 제거하던 잘못된 연속 실행 교정 |
| active name docs | 대외 서비스명 `세종 민원이음`과 내부 설명명 구분 |
| `CHANGELOG.md`, `versions/manifest.json` | docs 2.16.4 계보 |
| IMP-003/INDEX | PR #3 병합·CI 완료 상태와 본 노트 연결 |

제품 코드·API 계약·migration·rollback·공식 `.2` release·mock·prompt·테스트 코드는 바뀌지 않았다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.8.0-pr8-frontend-baseline | 동일 | 동작 변경 없음 |
| Web | 0.5.0-pr8-citizen-admin-baseline | 동일 | 동작 변경 없음 |
| API | 3.1.0-draft | 동일 | 동작·계약 변경 없음 |
| DB schema | 0.4.0-local | 동일 | migration 변경 없음 |
| Official data | 0.1.0-initial.2 | 동일 | immutable release 변경 없음 |
| Prompt set | 0.1.0-upstage-solar-pro3-synthetic | 동일 | provider actual 0 |
| Test suite | 1.5.0-pr8-web-baseline | 동일 | 테스트 코드 변경 없음 |
| Docs | 2.16.3 | 2.16.4 | 평가자 정보 구조·실행 재현 교정 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 |
|---|---|
| fresh `pnpm install --frozen-lockfile --ignore-scripts` | PASS — 465 packages |
| fresh `uv sync --project apps/api --frozen` | PASS — Python 3.12.13, 33 packages |
| API Ruff/Mypy/full pytest | PASS — 87 files, 1,782 passed / 8 local DB skips |
| Web lint/typecheck/Vitest/build | PASS — 49/49, production build |
| fixture Playwright E2E | PASS — 390/430/desktop 18/18 |
| shared contracts | PASS — 89/89 |
| data·staging·docs focused pytest | PASS — 120 passed, 1 skipped, 85 subtests |
| README PowerShell AST parse | PASS — 8/8 code blocks |
| README referenced runtime path check | PASS — 13/13 |
| repository documentation check | PASS |
| current tree / reachable Git history secret scan | PASS — finding 0 |
| product·contract·DB·official data diff boundary | PASS — 변경 0 |
| `git diff --check` | PASS |

API 성능 test 1건은 API·Web·contracts·data suite를 동시에 실행했을 때만 2.10초로 기준을
넘었지만, 해당 test 단독 3회는 0.91/0.87/0.86초, API 전체 단독은 1,782 passed였다. 제품
회귀가 아니라 병렬 CPU 경합으로 판정해 코드·threshold를 변경하지 않았다.

### 미실행 검증

- 이 후속 작업은 문서 감사이므로 patched Supabase actual DB, Upstage actual, remote DB,
  public deploy를 새로 실행하지 않았다. actual 19→20과 `/ready=200`은 snapshot의 기존
  local/private 증거를 유지하며, 교정한 명령은 구현 코드와 정적으로 대조했다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문·PII 추가 0; PERSONAL_LOOKUP/LEGAL_JUDGMENT 미저장 문구 유지.
- Security: 비밀값 추가 0; process-only 랜덤 secret 생성법만 설명하고 값을 기록하지 않음.
- Accessibility: UI 변경 0; 390/430/desktop E2E 18/18 증거 유지.
- Performance/cost: runtime 변경·외부 provider 호출·새 dependency·비용 0.

## 10. 데이터와 출처 영향

- 공식 `.2` release와 19/3/10 파일 byte 변경 0.
- fixture는 `시연용 샘플 — 공식 데이터 아님`, 승인·ACTIVE 전환 비활성이라고 명시.
- 20번째 `KB-WASTE-03`은 runtime 사람 승인 결과이며 immutable release에 넣지 않음.

## 11. 인간이 반드시 알아야 하는 내용

- public/remote 배포와 실사용 시민 provider 연결은 완료 상태가 아니다.
- actual 전체 흐름은 Windows amd64·PowerShell 5.1+·Docker 28+에서만 지원한다.
- 이 branch는 Draft PR까지만 게시하고 자동 merge하지 않는다. 최종 merge는 사람이 결정한다.

## 12. AI 내부 구현 세부

- README의 모든 PowerShell block을 parser로 검사하고 참조 경로·버전 값을 실제 파일과 대조했다.
- 내부 설명명과 대외 브랜드를 구분해 역사 문서를 무차별 치환하지 않았다.
- seed script의 finally cleanup과 API/Web 설정 loader를 직접 읽어 실행 순서를 정했다.

## 13. 재현·롤백·인수인계

### 재현

1. `README.md`의 6.1 설치와 6.2 fixture를 fresh clone에서 실행한다.
2. `python -B scripts/check_repository_docs.py`와 secret scan을 실행한다.
3. 실제 DB가 필요하면 6.3의 Windows-only 순서를 따르고 19 기준선에서 actual E2E를 1회 실행한다.

### 롤백

이 branch의 문서 commit을 새 revert PR로 되돌린다. product code·DB·공식 data rollback은 없다.

### 다음 개발자 시작점

README → WEEK3_EVALUATION → sample-20 report 순으로 읽고, 공개 배포 결정 전에는 local/private
경계를 유지한다.

## 14. 남은 위험·다음 단계

- Draft PR hosted CI와 GitHub diff를 사람이 검토한 뒤 merge 여부를 결정한다.
- 발표 당일 actual DB를 19 기준선으로 새로 준비해 5문항을 수동 리허설한다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트·문서 링크·명령 정적 검증
- [x] source-of-truth·버전 동기화
- [x] 개인정보 원문·비밀값 추가 없음
- [x] 구현 노트 INDEX 갱신
