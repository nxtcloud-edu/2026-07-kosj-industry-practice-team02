# IMP-20260720-010 — Q-GIT-004 A author identity 공개 동의와 COLLAB 실행계획 전환

- Date/Time (KST): 2026-07-20T22:44:54+09:00
- Task ID: `COLLAB-001-PREFLIGHT`
- Type: decision-privacy-source-control
- Status: Decision-only Done / COLLAB-001 plan Review
- Author/Agent: Codex (human decision: 사용자)
- Branch: `main`
- Base commit: `177dac810468f3cd5aaa4929a971cbde21b4deba`
- Related plan/ADR/RFP: `docs/superpowers/plans/2026-07-20-github-codex-cloud-collaboration-transition.md`,
  ADR-0019, D-053, A-039, Q-GIT-004, RFP collaboration trace

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 `Q-GIT-004: A — 내 이메일이고 private 팀원에게 보여도 괜찮음`으로 답했다.

### Acceptance Criteria

- 사용자 본인의 author/committer email을 private Frontend collaborator에게 공개해도 된다는 동의를
  원문 그대로 보존한다.
- 현재 reachable Git history와 SHA를 유지하고 noreply history rewrite를 하지 않는다고 기록한다.
- A-039를 Resolved, COLLAB-001을 Blocked에서 Review로 전환한다.
- source-of-truth, decision log, ADR, plan, TASKS, discovery, risk, handoff와 이전 note 상태를 동기화한다.
- 제품 코드·API·DB·data·dependency·remote·commit·push·CI·invite·App 변경은 0으로 유지한다.
- 새 구현 노트와 INDEX, 버전, 검증 증거를 완료한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자: identity 공개 범위 결정자; Codex: 기록·정합성·검증 |
| When — 언제 | 2026-07-20 KST, 최초 private remote push 전 |
| Where — 어디서 | local `main` working tree의 source-of-truth·ADR·plan·discovery·handoff·notes; 외부 GitHub state 0 |
| What — 무엇을 | Q-GIT-004=A, D-053, A-039 Resolved, current history/SHA 보존, COLLAB plan Review |
| Why — 왜 | 동의 없이 commit identity를 collaborator에게 공개하거나 불필요한 rewrite로 감사 계보를 훼손하지 않기 위해 |
| How — 어떻게 | 사용자 원문 보존 → 결정/ADR/ambiguity/plan/TASK 상태 동기화 → static/security/diff 검증 |
| How much — 어느 정도 | reachable 163 commit의 metadata 공개 동의; 제품·외부 state 변화 0; guidance/docs patch version 증가 |

## 3. 시작 전 상태

- 관련 파일: TEAM_DECISIONS, PROJECT_PLAN, ADR-0019, DECISION_LOG, AMBIGUITY_REGISTER,
  INTERVIEW_ANSWERS, COLLAB spec/plan, TASKS, Frontend handoff, IMP-009/INDEX, manifest.
- 기존 동작: Q-COLLAB-001 명세는 Approved였지만 A-039/Q-GIT-004 때문에 COLLAB-001 execution이
  Blocked였다.
- 감사 상태: reachable 163, `main` 157, 두 local branch의 main 밖 commit 2+4, content credential
  Critical/High 0, remote 0.
- 보안 부채: ignored local key exact-history 일회성 audit는 값을 출력·Git 저장하지 않았지만 child
  process argument caveat가 있어 재사용을 금지했다. 안전한 in-process scanner는 plan Task 1 소유다.
- Git 상태: `main` / HEAD `177dac8`; 기존 협업 문서 working tree 변경이 있으며 staged 0, remote 0.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-GIT-004 / A-039 | A / Blocker | 기존 author/committer email 공개 또는 noreply rewrite | A / D-053: 본인 email, private 팀원 공개 허용, history·SHA 보존 | Git identity·감사 계보 |
| COLLAB-001 approval | Human gate | 작성된 8-task 실행계획 실제 시작 | 아직 미승인; 명시적 `계획 승인, 구현 시작` 필요 | scripts/workflows/remote/CI/App |
| GitHub identifiers | Operational | owner/repository/collaborator login | 실행 시 사용자가 직접 확인; AI 추정 금지 | 외부 접근 권한 |

열린 architecture A/Blocker는 0개다. 실행계획 승인과 계정 식별자는 architecture 질문이 아니라
남은 인간 실행 gate다.

## 5. 설계 결정과 대안

### 선택

- D-053으로 private Frontend collaborator 범위의 author/committer identity 공개에 동의한다.
- 현재 reachable history와 모든 SHA를 보존한다.
- noreply rewrite, force push, ref remapping을 하지 않는다.
- public 전환, 추가 collaborator 또는 identity visibility 확대는 새 승인 대상으로 둔다.

### 이유

이메일은 사용자 본인의 것이고 승인된 private collaborator에게 보여도 괜찮다고 명시했다. history
보존은 기존 SHA·branch·구현 노트·감사 증거를 그대로 유지해 가장 단순하고 재현 가능하다.

### 고려했지만 선택하지 않은 대안

- GitHub noreply 전면 rewrite: identity 노출은 줄지만 모든 SHA와 문서·branch 계보를 바꾼다.
- 답 없이 push: 동의 없는 개인정보 공개라 금지한다.
- public repository: Q-GIT-001의 private source 범위를 벗어나므로 금지한다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `docs/decisions/DECISION_LOG.md` | D-053 추가, D-052 successor 상태 정리 | 결정 계보 |
| `docs/11_AMBIGUITY_REGISTER.md` | A-039 Resolved, 열린 A blocker 0, Q-GIT-004 해결 질문 이동 | ambiguity 권위 |
| TEAM_DECISIONS, PROJECT_PLAN, ADR-0019 | consent·history/SHA 보존·no rewrite | source-of-truth |
| COLLAB spec/plan, `TASKS.md` | execution Blocked → plan Review | 승인 gate 정확성 |
| INTERVIEW_ANSWERS, INITIAL_DISCOVERY_REPORT | 사용자 원문과 발견→해결 계보 | 재현·감사 |
| README, CONTRIBUTING, deployment, risk, handoff, CHANGELOG, CODEX index | 현재 상태·운영 위험 동기화 | 문서 위생 |
| IMP-009, implementation-note INDEX | successor resolution과 Review 상태 링크 | 이전 note 인수인계 |
| `versions/manifest.json` | repo guidance 1.6.1, docs 2.8.1 | 결정 patch 추적 |

### 데이터 흐름/상태 변화

`Q-GIT-004 Open → 사용자 A → D-053 → A-039 Resolved → COLLAB-001 Review`. Git object·ref·SHA와
application/DB/data는 바꾸지 않는다.

### 오류·빈 상태·롤백

동의를 철회하거나 가시성 범위가 바뀌면 기존 D-053을 삭제하지 않고 successor 결정을 추가한다.
최초 push 전이면 remote를 만들지 않고 별도 rewrite plan을 검토한다. push 뒤에는 collaborator/App
접근을 먼저 회수하고 이미 공유된 clone/cache를 삭제된 것으로 단정하지 않는다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | `0.3.0-pii-core` | 유지 | 제품 코드 0 |
| Web | `0.2.0-static-chat-shell` | 유지 | UI 코드 0 |
| API | `2.0.1-draft` | 유지 | 공개 계약 0 |
| DB schema | `0.3.0-local` | 유지 | migration/DB 0 |
| Official data | `0.0.0-not-populated` | 유지 | seed/data 0 |
| Mock data | `0.0.0-not-populated` | 유지 | mock 0 |
| Prompt set | `0.0.2-deepseek-v4-flash-selected` | 유지 | LLM/prompt 0 |
| Test suite | `0.9.0-pii-core` | 유지 | test code 0 |
| Product spec | `2.2.5` | 유지 | 사용자-visible 제품 동작 불변 |
| Repo guidance | `1.6.0` | `1.6.1` | identity consent·history 정책 해결 |
| Docs | `2.8.0` | `2.8.1` | D-053·A-039·plan 상태 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `git status --short --branch`, `git remote -v`, `git rev-parse HEAD` | PASS: main, `177dac8`, remote 0, staged 0 | modified 25, untracked 6, total 31 | terminal |
| D-053/A-039/COLLAB status assertion | PASS | D-053 present, A-039 Resolved, plan/TASK Review | terminal |
| `python -B -m unittest -v scripts.tests.test_repository_scaffold` | PASS | 6/6 | terminal |
| `python -B scripts/validate_codex_package.py` | PASS | 12 required files | terminal |
| `powershell ... scripts/check_secret_patterns.ps1` | PASS, value output 0 | exit 0 | terminal |
| manifest JSON/version assertion | PASS | product 2.2.5, guidance 1.6.1, docs 2.8.1 | terminal |
| `git diff --check` | PASS | exit 0; INDEX CRLF→LF warning only | terminal |
| changed Markdown local-link check | PASS | 30 files, 89 local links | terminal |
| docs/guidance-only scope audit | PASS | 31 files, executable/product path 0 | terminal |
| `git diff --quiet -- scripts/check_scope_drift.py` | PASS | scanner 변경 0 | terminal |

### 미실행 검증과 이유

- Web/API/DB/product build/test: 이 요청은 identity consent와 문서 상태만 바꾸며 executable/product
  파일을 수정하지 않는다.
- GitHub/CI/Cloud: COLLAB-001 실행계획이 아직 승인되지 않았고 remote 0이다.
- Docker/Supabase/DeepSeek: 이 결정에 필요하지 않으며 local-only actual gate를 재실행하지 않는다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 사용자가 본인 email의 **private Frontend collaborator 범위** 공개에 동의했다. public이나
  추가 collaborator로 자동 확대하지 않는다.
- Security: history rewrite를 피하고 SHA 계보를 보존한다. ignored env/key는 GitHub·Cloud·CI에 넣지
  않으며 unsafe exact-key subprocess 비교를 재사용하지 않는다.
- Accessibility: 사용자 UI 변경 0.
- Performance/cost: GitHub Free·초기 0원 유지; runtime 성능 변화 0.

## 10. 데이터와 출처 영향

- 공식 데이터: 변경·승인·seed·push 0; `official_data=0.0.0-not-populated` 유지.
- mock/AI 생성: 신규 0.
- schema/lineage: API/DB/data lineage 불변; Git history identity decision lineage만 D-053으로 추가.
- verified date: 2026-07-20 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-GIT-004는 해결됐으며 현재 history·SHA를 그대로 유지한다.
- 동의 범위는 private Frontend collaborator다. public 전환·추가 collaborator·history rewrite는 재승인
  대상이다.
- remote·commit·push·CI·invite·Codex App은 여전히 0이다.
- 다음 gate는 작성된 COLLAB-001 실행계획의 `계획 승인, 구현 시작`이다.
- 이전 exact-key local audit의 process-argument caveat가 걱정되고 PC에 EDR/command-line auditing 또는
  다른 사용자가 있다면 DeepSeek key 회전을 권장한다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- D-053 cross-reference와 Markdown 상태 문구 정렬
- manifest timestamp/version patch
- 계획 실행 뒤 stdlib history scanner의 in-process blob comparator, classifier helper와 workflow 배치

## 13. 인수인계·재현·롤백

### 재현

1. D-053, A-039 Resolved, ADR-0019을 확인한다.
2. COLLAB plan/TASKS가 Review이고 remote 0인지 확인한다.
3. manifest가 guidance 1.6.1/docs 2.8.1이며 application/API/DB/data 축은 불변인지 확인한다.
4. 이 note의 최종 명령 결과와 INDEX를 확인한다.

### 롤백

문서 오기이면 같은 변경 묶음을 revert하고 manifest를 함께 되돌린다. 사용자 consent 철회는 D-053을
삭제·소급 변경하지 않고 successor decision으로 기록한다. plan 승인 전이므로 외부 rollback은 없다.

### 다음 개발자 시작점

사용자 실행 승인 전에는 plan read/review만 한다. 승인 뒤 `superpowers:executing-plans` 또는
`superpowers:subagent-driven-development`로 Task 1 safe history scanner TDD부터 시작한다. remote 생성은
Task 1 PASS 뒤이며 최초 push는 검토된 `main`만 사용하고 `--all`/`--mirror`를 금지한다.

## 14. 남은 위험·미해결 질문·다음 단계

- COLLAB-001 실행계획 승인 미수령.
- GitHub owner/repository/collaborator login과 초대 수락은 실행 시 인간 확인 필요.
- GitHub Free의 PR/direct-push 기술적 강제 한계.
- safe in-process history scanner, CI workflow, Playwright portability는 계획 실행 전 미구현.
- scope-drift 기존 false-positive inventory는 별도 tooling 보정 대상.
- DATA-SEED-002, PII-CONSUMER, public `00700`의 독립 gate는 그대로 유지.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/ADR/TASK/plan 동기화
- [x] 개인정보 원문·비밀값 노출 없음
- [x] 구현 노트 INDEX 생성 확인
