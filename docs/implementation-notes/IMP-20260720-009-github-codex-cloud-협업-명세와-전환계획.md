# IMP-20260720-009 — GitHub·Codex Cloud 협업 명세와 전환계획

- Date/Time (KST): 2026-07-20T22:26:13+09:00
- Task ID: `COLLAB-001-DESIGN-PLAN`
- Type: decision-architecture-planning-handoff
- Status: Decision documentation Done / COLLAB execution Review — Q-GIT-004 resolved by IMP-010;
  plan approval required
- Author/Agent: Codex (human decisions: 사용자)
- Branch: `main`
- Base commit: `177dac810468f3cd5aaa4929a971cbde21b4deba`
- Related plan/ADR/RFP: `docs/superpowers/plans/2026-07-20-github-codex-cloud-collaboration-transition.md`,
  `docs/adr/0019-private-github-role-scoped-collaboration.md`, D-047~D-053, RFP collaboration trace

## 1. 기본 정보 — 6W1H

- Who: 사용자(owner), 새 인간 Frontend 팀원 1명, Codex local/Cloud; 문서 작성·감사는 Codex
- When: 2026-07-20 KST
- Where: `main`의 source-of-truth·ADR·협업 spec/plan·handoff; 외부 GitHub state는 아직 없음
- What: private GitHub, Frontend 전체 위임, self-merge, Codex Cloud Draft-PR-only 결정을 동기화하고
  실행 가능한 전환계획과 팀원 인수인계를 작성
- Why: 단일 개발자의 속도 병목을 줄이고 해외 체류 중 Cloud와 팀원 개발을 이어가되 계약·공식
  데이터·개인정보·DB·배포의 인간 책임을 유지하기 위해
- How: repository discovery → 한 질문씩 A/B 인터뷰 → 3개 운영 모델 비교 → 명세 승인 → ADR/
  source-of-truth/TASK/리스크/handoff/실행계획 동기화 → 병렬 읽기 전용 감사 → 정적 검증
- How much: 제품 코드·API·DB·data·dependency·remote·CI·초대·Cloud 설정 0; 협업 문서와 guidance만
  변경. 실행은 별도 plan 승인 뒤 8개 task로 수행

## 2. 사용자 요청과 인수 기준

요청:

- 인간 팀원 한 명에게 Frontend를 자세히 분리해 위임
- 사용자는 해외에서 Codex Cloud를 주로 사용하고 가끔 local에서 검증
- Git으로 충돌 없이 협업하는 방법과 실제 순서를 상세히 설명
- Q-GIT-001=A, Q-OWN-001=A, Q-GIT-002=A, Q-GIT-003=B, Q-CLOUD-001=A,
  Q-COLLAB-001=A 반영

인수 기준:

- 결정이 source-of-truth, decision log, ambiguity register, ADR과 TASKS에 모순 없이 기록됨
- 팀원의 허용/금지 경로, 작업 순서, 테스트, Issue·PR·병합·롤백 절차가 handoff에 있음
- GitHub Free의 강제력 한계와 Cloud/local 검증 경계가 명시됨
- 실제 remote/CI/App 설정은 별도 실행계획 승인 전 수행되지 않음
- 비밀·시민 원문·실제 개인정보·DeepSeek key가 문서·Git 출력에 없음
- 구현 노트와 INDEX가 갱신되고 관련 정적 검증이 통과함

## 3. 조사한 파일과 기존 상태

- 시작 Git: `main`, HEAD `177dac810468f3cd5aaa4929a971cbde21b4deba`, clean, remote 0
- 기존 원격/CI: `.github/` 없음; D-021/A-008/ADR-0002/TEAM_DECISIONS/CONTRIBUTING/
  deployment 문서가 “사용자 재요청까지 보류” 상태
- Web: `/`와 입력·저장·fetch 없는 정적 `/chat`; `/admin` 없음
- Contract: generated TypeScript와 chat fixtures는 존재하지만 team member에게 read-only
- Runtime: Node 24.12.0, pnpm 11.13.0, Python 3.12.13, uv 0.11.28
- DATA-SEED-002 plan은 Review, official data는 `0.0.0-not-populated`, `/ready=503`
- AI-001A pure PII core는 Done; PII-CONSUMER/API-CHAT/WEB-CHAT/admin은 dependency에 따라 Blocked
- current Playwright config는 unconditional `corepack.cmd`라 Cloud/Linux E2E portability gap 존재
- root `scripts/verify.ps1`은 Windows 전용이지만 Docker를 시작하지 않는다. actual DB/data gate는
  별도 `scripts/verify_database.ps1`과 `scripts/verify_data_seed.ps1`이며 Cloud completion gate가 아님
- 관련 권위: `AGENTS.md`, TEAM_DECISIONS, PROJECT_PLAN, ADR-0002, D-009/D-021,
  deployment/security/handoff/workflow 문서, `TASKS.md`, frontend AGENTS/README

Legacy는 사용하지 않았고 현재 범위·계약의 근거로 취급하지 않았다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-GIT-001 | A | source remote/visibility/App scope | A: 개인 GitHub private, collaborator, selected-repo-only App | 소스 접근·원격 |
| Q-OWN-001 | A | 팀원 소유 범위 | A: 세 페이지와 typed client·상태·a11y·test 전체 frontend | 역할·TASKS |
| Q-GIT-002 | B | private protection 비용 | A: GitHub Free/0원 | 강제력·CI |
| Q-GIT-003 | B | 팀원 merge 권한 | B: 허용 frontend-only green PR 자가 병합 | 속도·리스크 |
| Q-CLOUD-001 | A | Cloud merge | A: branch+Draft PR, 사람 merge | 책임·보안 |
| Q-COLLAB-001 | A | 전체 협업 명세 | A: 승인 | ADR/spec/plan |
| Q-GIT-004 | A / Blocker | 기존 author/committer email metadata 공개 여부 | Subsequently Resolved A/D-053: 사용자 본인 email의 private collaborator 공개 허용, history·SHA 보존 | identity privacy·Git SHA |

전체 history 감사에서 credential/content secret은 0건이고 ignored local LLM key의 exact value도
history 0건이었다. 다만 163개 도달 가능 commit의 실제 형태 author/committer email metadata가
확인됐다. 작성 시 Q-GIT-004 답 전에는 commit·remote·push를 하지 않았고, 이후 A/D-053으로
history·SHA 보존이 확정됐다. 필요한 GitHub owner, 실제 repository name, collaborator login과 초대
수락 여부는 실행 시 사람이 직접 확인할 운영 식별자이며 AI가 추정하지 않는다. plan 승인은 별도다.

## 5. 선택한 설계와 버린 대안

### 선택

- private single monorepo
- 인간 Frontend 팀원에게 frontend 전체 수직 흐름 위임
- 허용 frontend-only PR의 사람 self-merge
- 사용자/Codex는 backend·DB·contract·data·security 소유
- Codex Cloud는 Draft PR까지만
- GitHub Actions는 scope와 frontend green evidence를 제공하되 Free에서 강제 보안 경계로 주장하지
  않음
- DeepSeek·Docker/Supabase actual은 local-only

### 버린 대안

- 모든 PR 사용자 승인: 해외·시차 병목
- frontend/backend repository 분리: contract/fixture/E2E 동기화 비용
- GitHub Pro 즉시 도입: 초기 0원 결정 위반
- Codex Cloud 자동 merge: 사람 책임·Free enforcement 경계 약화
- Cloud에 DeepSeek key 등록: 합성 local-only 정책과 비밀 경계 위반

## 6. 변경 파일·함수·계약·DB·데이터

| 파일/영역 | 변경 |
|---|---|
| `docs/superpowers/specs/2026-07-20-github-codex-cloud-collaboration-design.md` | 승인된 상세 협업 명세 신규 |
| `docs/superpowers/plans/2026-07-20-github-codex-cloud-collaboration-transition.md` | 8-task TDD/remote/CI/Cloud/onboarding 실행계획 신규; IMP-010/D-053 뒤 Review |
| `docs/adr/0019-private-github-role-scoped-collaboration.md`, ADR index/0002 | 장기 결정과 기존 유예의 부분 successor 기록 |
| `docs/handoffs/HANDOFF-20260720-FRONTEND-COLLABORATOR.md` | 팀원 읽기 순서·범위·lane·명령·Git·Issue·금지·rollback 신규 |
| TEAM_DECISIONS, PROJECT_PLAN | 실제 2인 개발 협업, frontend owner, GitHub/Cloud/merge 정책과 version 동기화 |
| DECISION_LOG, AMBIGUITY_REGISTER, INTERVIEW_ANSWERS | D-047~053, A-033~039, Batch 6~7과 Q-GIT-004 기록 |
| `TASKS.md` | 작성 시 COLLAB-001 Blocked; IMP-010/D-053 뒤 Review와 frontend owner 표기 |
| AGENTS/CONTRIBUTING/workflow/human-AI/deployment/security/risk/handoff/PLANS | 일상 협업·보안·권한·복구 규칙 동기화 |
| README/CHANGELOG/CODEX_FILE_INDEX | 발견·handoff·plan 진입 링크와 변경 요약 |
| `versions/manifest.json` | product spec/repo guidance/docs version 증가 |

제품 source, API contract, generated type, DB migration/schema, official/mock data, prompt, dependency,
CI workflow와 Git remote는 변경하지 않았다. 함수·endpoint·table·enum 변화는 0이다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | `0.3.0-pii-core` | 유지 | 제품 코드 0 |
| Web | `0.2.0-static-chat-shell` | 유지 | UI 코드 0 |
| API | `2.0.1-draft` | 유지 | 공개 계약 0 |
| DB schema | `0.3.0-local` | 유지 | migration/DB 0 |
| Official data | `0.0.0-not-populated` | 유지 | seed/승인 row 0 |
| Mock data | `0.0.0-not-populated` | 유지 | mock 0 |
| Prompt set | `0.0.2-deepseek-v4-flash-selected` | 유지 | provider/prompt 0 |
| Test suite | `0.9.0-pii-core` | 유지 | 이 단계에서는 test code 0 |
| Product spec | `2.2.4` | `2.2.5` | 실제 협업 인원·소유권·운영 정책 |
| Repo guidance | `1.5.0` | `1.6.0` | GitHub/Cloud/merge 경계 |
| Docs | `2.7.12` | `2.8.0` | 승인 spec·ADR·handoff·실행계획 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 |
|---|---|---|---|
| `git branch --show-current`, `git rev-parse HEAD`, `git status --short`, `git remote -v` | 시작 baseline PASS: `main`, `177dac8`, clean, remote 0 | 1 baseline | terminal |
| `rg --files`, 관련 `rg -n`과 권위 문서 read | PASS: stale remote/CI 문구와 update map 확인 | active docs/contracts/web/tooling | terminal |
| 병렬 collaboration document audit | note closure와 unsafe exact-key 재현 방식 보정 후 Critical/Important/Minor 0 | 4 audits, agent edits 0 | 이 note 자체 리뷰와 final agent report |
| 병렬 CI/Cloud feasibility audit | 이전 Important 12개와 final 4개 보정 후 Critical/Important/Minor 0 | 3 audits, agent edits 0 | plan의 frozen invariants와 final agent report |
| full-history secret audit | 조건부 GO: credential/content secret 0, one-time ignored local LLM key exact history 0, author-email identity decision 1 | 163 reachable commits; main 157; extra local branch commits 6; exact-key 방법 caveat 아래 기록 | redacted agent report + safe count 재현 |
| Git push scope audit | `main` only 권고; `--mirror` 금지, extra local branches 별도 검토 | remote 0, push 0 | redacted agent report |
| `python -B -m unittest -v scripts.tests.test_repository_scaffold` | PASS | 6/6 | terminal |
| `python -B scripts/validate_codex_package.py` | PASS | 12 required files | terminal |
| `powershell ... scripts/check_secret_patterns.ps1` | PASS, value output 0 | exit 0 | terminal |
| manifest JSON/version assertion | PASS | product 2.2.5, guidance 1.6.0, docs 2.8.0 | terminal |
| changed Markdown local-link check | PASS | 29 files, 88 local links | terminal |
| docs/guidance-only path audit | PASS | 30 changed/untracked files; product/executable path 0 | terminal |
| `git diff --check` | PASS | exit 0; INDEX CRLF→LF warning only | terminal |
| `python -B scripts/check_scope_drift.py` | FAIL, current task 밖 기존 false-positive inventory | exit 1; `.worktrees`, synthetic privacy fixtures, unchanged historical docs/package manifest | terminal |

### Full-history 감사 재현 명령

아래 명령은 이메일·key 값 자체를 출력하지 않고 key를 subprocess 인자로도 넘기지 않는 안전한
개수 검증만 재현한다. 전용 tracked history scanner는 승인된 COLLAB plan Task 1에서 TDD로 추가할
예정이며 현재 존재한다고 주장하지 않는다.

```powershell
git rev-list --all --count
git rev-list main --count
git rev-list --count main..codex/data-approval-materialization
git rev-list --count main..codex/web-home-static-chat
@(git log --all --format='%ae' | Sort-Object -Unique).Count
```

재현 기대값은 각각 reachable 163, `main` 157, main 밖 branch commit 2와 4, author-email identity
1종이다. credential category 검사는 값 대신 commit/path만 출력하는 `git grep -I -l` 방식으로
수행했고 Critical/High 0이었다. ignored local key exact history 0 결과를 얻은 일회성 감사 방식은
값을 출력·커밋하지 않았지만 `git -S` child process argument로 잠깐 전달하는 결함이 있어 안전한
재현 명령에서 폐기했다. 해당 값은 문서·Git·terminal output에는 없지만 OS/EDR process-command-line
audit가 켜진 환경에서는 관측됐을 가능성을 배제할 수 없다. Task 1 scanner는 key를 subprocess
argv/env/tempfile에 넣지 않고 Python process memory에서 Git blob bytes와 비교해야 한다.

### 미실행 검증과 이유

- Product test/build: 제품 코드·dependency를 바꾸지 않은 decision/plan 단계다. 관련 static/package/
  secret 검증만 수행한다.
- Scope drift: 검사는 실행했지만 기존 scanner가 `.worktrees`를 순회하고 승인된 합성
  `044-000-` privacy fixture와 역사 문서를 예외 처리하지 않아 exit 1이다. 이번 변경 파일은 finding
  0이며 scanner/tooling 보정은 COLLAB 실행이나 별도 tooling task에서 TDD로 다룬다.
- GitHub Actions/Cloud PR: remote와 workflow가 없고 plan 실행 승인이 아직 없다.
- Docker/Supabase/DeepSeek: 이 문서 작업과 무관하며 local-only actual gate를 재실행하지 않는다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문 원문·PII·transcript·token의 GitHub/Issue/PR/Cloud/CI 업로드를 명시적으로 금지했다.
- Security: pre-push full-history redacted scan, private visibility, selected-repository App, Cloud secret
  0, read-only Actions, scope/revoke/revert 경계를 계획했다. content secret은 0이지만 author-email
  metadata는 Q-GIT-004 전 비공개를 유지한다. 일회성 exact-key audit의 subprocess-argument caveat는
  위에 공개했으며 재사용을 금지했다. 실제 external state 변화는 0이다.
- Accessibility: 인간 Frontend owner의 필수 인수 기준으로 390/430, 200% zoom, keyboard/focus,
  4.5:1, user-visible states를 고정했다.
- Performance/cost: GitHub Free/0원. CI 시간/quota는 첫 rehearsal에서 측정하며 GitHub Pro나 새
  유료 서비스는 승인하지 않았다.

## 10. 데이터와 출처 영향

- 공식 데이터: 변경·push·seed·승격 0, `official_data=0.0.0-not-populated` 유지
- mock/AI 생성: 신규 mock 0; 팀원은 mock을 `시연용 샘플`로 표시해야 함
- schema/lineage: API/DB/data schema·lineage 불변
- verified date: 2026-07-20 KST 문서 상태 기준

## 11. 마이그레이션·롤백·복구

- DB migration/data rollback: 해당 없음
- 현재 문서 단계 rollback: 이 변경 묶음을 일반 revert commit으로 되돌리고 manifest/source version을
  함께 이전 값으로 되돌린다. history rewrite는 사용하지 않는다.
- 실제 remote 실행 뒤 rollback: collaborator/App revoke, PR pause, 필요 시 private repository
  archive/delete를 인간이 명시적으로 수행한다. `origin` 삭제만으로 이미 push된 데이터를 지우지
  못한다.
- secret 발견: push 중단 → key rotation → 영향 분석 → 별도 history cleanup 승인 순서다.

## 12. 인간이 반드시 알아야 하는 내용

- 지금 완료된 것은 **협업 명세·책임 분리·인수인계·실행계획**이며 GitHub 저장소·CI·초대·Codex
  연결은 아직 만들지 않았다.
- Q-GIT-004는 이후 IMP-010/D-053으로 해결됐다. 다음 인간 gate는 COLLAB-001 계획 승인과 GitHub
  owner/repo/collaborator login 확인이다.
- GitHub Free에서는 frontend self-merge 경계를 플랫폼이 완전히 강제하지 못한다.
- Codex Cloud는 merge하지 않고 비밀·DeepSeek·Docker actual을 사용하지 않는다.
- private GitHub는 public deployment/remote DB/production backup이 아니다.
- Frontend 팀원은 공식 데이터/PM 승인/계약/DB/security owner가 아니다.
- exact key 값은 출력·Git 저장되지 않았지만 일회성 local audit에서 child-process argument가 됐다.
  이 PC에 process-command-line audit/EDR 또는 다른 local 사용자가 있거나 key 가치가 크면 DeepSeek
  dashboard에서 key를 회전하는 것이 안전하다. 최초 push 전에는 새 in-process scanner로 재검증한다.

## 13. AI 내부 구현 세부 — 인간이 굳이 이해하지 않아도 되는 내용

- 후속 scope classifier의 stdlib parsing, path normalization과 stable output 코드 구조
- GitHub workflow job 분할, cache key, action SHA의 내부 배치
- frontend component/helper/test fixture 파일 분리와 명명
- 문서 링크·색인·formatting

## 14. 인수인계·재현

### 재현

1. 이 노트의 시작 HEAD에서 `git remote -v`가 비어 있었음을 확인한다.
2. collaboration spec에서 actor/path/merge/secret/local 경계를 확인한다.
3. Frontend handoff의 Lane F0~F4와 명령을 읽는다.
4. COLLAB-001 plan의 Task 1~8을 순서대로 검토한다.
5. plan 승인 전 remote/CI/App가 없고 제품 version 축이 유지됐는지 manifest/diff로 확인한다.

### 다음 개발자 시작점

- Q-GIT-004=A/D-053은 해결됨. plan 승인 전: read/review만 수행하고 commit·remote·push 0
- plan 승인 뒤: Task 1 history scanner TDD와 audit 재현부터 시작하며 remote 생성부터 시작하지 않음
- Frontend 팀원: remote/CI owner bootstrap 뒤 handoff Lane F0의 no-product-change rehearsal부터 시작
- 사용자 Cloud: repository 제한 App과 secret 0 environment 뒤 docs/test-only Draft PR rehearsal

## 15. 남은 위험·미해결 사항

- exact GitHub owner/repository/collaborator login 미확인
- COLLAB-001 execution plan 미승인
- remote/CI/App/Cloud environment 실제 evidence 0
- Playwright E2E의 Windows-only `corepack.cmd`는 plan 실행에서 cross-platform TDD 보정 필요
- GitHub Free의 direct push/self-merge 기술적 미강제
- two extra local branches의 main 밖 6개 commit은 push 대상에서 제외하고 별도 검토해야 함
- exact local key 비교는 safe in-process history scanner 구현 전 다시 실행하지 않음; process audit
  가능성이 우려되면 인간이 DeepSeek key 회전
- DATA-SEED-002, PII-CONSUMER, public `00700`은 기존 별도 gate 그대로 유지

## 16. 자체 리뷰

- [x] 요청과 여섯 결정 반영
- [x] 최종 static/secret/history 검증 수행 — scope drift의 기존 false-positive 실패는 위에 공개
- [x] source-of-truth/ADR/TASK/plan/handoff/version 동기화
- [x] 제품/API/DB/data/dependency/external state 변경 0
- [x] 개인정보 원문·비밀값 노출 없음
- [x] 구현 노트 INDEX 갱신
