# IMP-20260721-009 — Frontend collaborator kickoff message and onboarding runbook

- Date/Time (KST): 2026-07-21T09:04:25+09:00
- Task ID: COLLAB-FRONTEND-KICKOFF
- Type: documentation-handoff-source-control-security
- Status: Done — teammate execution and F1 contract consumption pending
- Author/Agent: Codex primary agent
- Branch: `codex/COLLAB-001-post-merge-evidence`
- Base commit: `4b473e2`
- Related plan/ADR/RFP: COLLAB-001 approved plan/spec, ADR-0019, D-047~D-057, TASKS COLLAB-001

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 이제 Frontend 팀원에게 어떤 명령을 내려야 하는지 자세히 설명하고 문서로 작성해 달라고 요청했다.

### Acceptance Criteria

- 팀원에게 개인 채널로 그대로 보낼 수 있는 한 덩어리의 kickoff message를 만든다.
- security/MFA, clone, exact runtime, baseline, branch, 구현 노트, PR/CI/self-merge, 완료 보고를 포함한다.
- 팀원 작성 범위와 더 좁은 self-merge allowlist, owner-review 경계를 평이하게 설명한다.
- 첫날에는 제품 코딩보다 no-product-change onboarding rehearsal을 먼저 수행하도록 한다.
- 현재 remote/local main 상태와 Cloud environment 상태를 source-of-truth/plan/task/handoff에 동기화한다.
- 다음 실제 F1 작업을 막는 shared-contract consumption gap을 숨기지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 지시·확인, `koregy`가 Frontend clone/baseline/PR/self-merge 실행, Codex가 handoff 작성 |
| When — 언제 | 2026-07-21 KST, private remote/CI/App/Cloud environment 준비 뒤 첫 teammate 작업 전 |
| Where — 어디서 | private `Sejong_AI`, Windows PowerShell, GitHub PR/Actions, active frontend handoff |
| What — 무엇을 | copy/paste kickoff, exact tool setup, full baseline, two-file onboarding PR와 stop/report 경계 |
| Why — 왜 | 해외 협업에서 main 직접 push·scope 침범·secret 노출·환경 차이로 인한 재작업을 먼저 차단하기 위해 |
| How — 어떻게 | handoff template, ADR/decisions/plan/Task 7, current remote SHA와 repo manifests를 대조 |
| How much — 어느 정도 | handoff 1개 확장, source/plan/task/status sync, note/INDEX/version; product code/dependency/API/DB/data 0 |

## 3. 시작 전 상태

- 관련 파일: frontend handoff, owner checklist sections 6~8, collaboration spec/plan, ADR-0019,
  TEAM_DECISIONS, TASKS, CONTRIBUTING, manifest.
- 기존 동작: detailed teammate commands는 owner checklist에 흩어져 있고 frontend handoff에는 owner가 그대로
  전송할 단일 message가 없었다.
- 발견한 충돌: active handoff/TEAM_DECISIONS/plan은 local/remote main이 초기 SHA에서 같다고 썼지만 read-only
  evidence는 remote main `ce8a608...`, primary local main `5e09dec...`로 다르다. Cloud environment도 saved
  evidence 뒤 문서 일부에 pending으로 남아 있었다.
- 첫 검증에서 owner/frontend checklist의 `scripts/check_current_tree_secrets.py`가 실제 저장소에 없음을
  발견했다. tracked+untracked nonignored active file을 검사하는 실제 권위 명령
  `scripts/check_secret_patterns.ps1 -RepositoryRoot .`로 교정했다.
- 구현 전제 gap: F1은 generated shared contract 사용을 요구하지만 `apps/web/package.json`은 shared package를
  소비 dependency로 선언하지 않고 shared package에 public export도 없다. 팀원의 manifest/lockfile 변경은
  owner review이므로 onboarding 직후 임의 구현시키지 않는다.
- Git 상태: existing post-merge documentation branch와 notes 005~008을 보존하며 remote write 0.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| FRONT-KICK-001 | Human pending | teammate MFA/recovery | 완료 사실만 회신; code 수집 0 | account supply chain |
| FRONT-KICK-002 | Human pending | teammate Windows tool availability | exact checks; mismatch면 product code 0/stop | reproducibility |
| FRONT-KICK-003 | Human pending | baseline/PR/CI/self-merge evidence | structured report로 owner 확인 | Task 5/7 |
| FRONT-KICK-004 | Owner gate | shared-contract web consumption | onboarding 후 owner-review task/PR로 준비 | first real F1 task |
| FRONT-KICK-005 | Verified | remote main | `ce8a608...`; local primary remains pre-merge | teammate base |

## 5. 설계 결정과 대안

### 선택

팀원에게 첫날 바로 제품 코딩을 시키지 않고 보안·clone·exact runtime·full baseline 뒤 정확히 신규 web note
1개와 INDEX append 1개만 담은 `feat/web-COLLAB-ONBOARDING-doc-check` PR을 만들게 한다. policy가
`FRONTEND_SELF_MERGE_ELIGIBLE`이고 모든 CI가 green일 때만 Create a merge commit으로 자가 병합한다.
그 결과를 owner가 확인한 뒤 forbidden-scope close-without-merge rehearsal과 첫 실제 task를 따로 발행한다.

### 이유

GitHub Free에서는 main direct push나 path ownership을 완전 강제하지 못한다. no-product-change PR은 clone,
credential, branch, note, CI, scope classifier와 self-merge를 가장 낮은 위험으로 한 번에 검증한다.

### 고려했지만 선택하지 않은 대안

- 바로 `/chat` 개발: 환경/권한 미검증과 shared-contract consumption gap 때문에 제외.
- 모든 명령을 구두로만 전달: 재현성과 시차 협업이 약해져 제외.
- token/PAT 공유: credential 노출이므로 금지.
- Python 3.12.13 Windows MSI 안내: 공식 release는 source-only이므로 uv exact managed Python으로 대체.
- 팀원에게 package/lockfile를 고치게 함: self-merge 경계를 넘으므로 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| frontend handoff/owner checklist | current SHA/status, copy/paste message, exact setup/baseline/PR/report, 실제 current-tree secret scanner, F1 stop gate | 팀원이 문서만으로 재현 |
| TEAM_DECISIONS/PROJECT_PLAN/TASKS/CONTRIBUTING/AMBIGUITY/CODEX index/COLLAB plan | remote/local divergence, post-merge runs, Cloud saved status | active status 단일화 |
| CHANGELOG/manifest | repo guidance 1.7.6/docs 2.10.0 | version lineage |
| this note/INDEX | 조사·결정·명령·위험·handoff | request-level evidence |

### 데이터 흐름/상태 변화

```text
private invite accepted
  → MFA/recovery self-check
  → remote main clone
  → exact runtimes + full baseline
  → two-doc onboarding branch/PR
  → eligible + green
  → teammate merge commit
  → owner evidence review
  → forbidden dry-run close
  → owner-prepared shared-contract consumption
  → first fixture UI task
```

### 오류·빈 상태·롤백

- runtime/baseline 실패: product code 수정 0, 실패 명령과 non-secret 마지막 20줄만 보고.
- remote SHA 예상 불일치: reset/force push 금지, SHA 보고 후 owner 판단.
- scope/CI 실패 또는 예상 밖 파일: merge 금지.
- 잘못 병합: history rewrite 대신 revert PR.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.5
- repo_guidance: 1.7.5
- application: 0.3.0-pii-core
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 1.0.0-collaboration
- documentation: 2.9.8

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Repo guidance | 1.7.5 | 1.7.6 | teammate executable collaboration handoff/status correction |
| Docs | 2.9.8 | 2.10.0 | comprehensive kickoff/runbook/source sync |
| Product/application/web/API/contracts/DB/data/prompt/tests | unchanged | unchanged | 제품·계약·dependency 변경 0 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `git rev-parse origin/main`, local `main`, `git ls-remote` | PASS | remote ce8a608; local 5e09dec | terminal |
| ADR/decisions/plan/Task 7/handoff/web rules inspection | PASS | ownership/self-merge/onboarding boundary | repository docs |
| current web/fixture/package inspection | PASS | F1 fixtures exist; web shared-contract consumption missing | repository files |
| official Node archive lookup | PASS | Windows x64 MSI available for 24.12.0 | nodejs.org |
| official uv installation/Python management lookup | PASS | versioned installer URL and exact managed Python supported | docs.astral.sh |
| runtime command syntax | PASS | Node 24.12.0, Corepack 0.34.5, pnpm 11.13.0, uv 0.11.28, managed Python 3.12.13 | terminal |
| `check_repository_docs.py --repository-root .` | PASS | exit 0 | terminal |
| `check_secret_patterns.ps1 -RepositoryRoot .` | PASS | exit 0, finding/output 0 | terminal |
| scoped collaboration/config/docs unit tests | PASS | 57 tests, 1 expected Windows symlink skip | terminal |
| `git diff --check` and manifest JSON parse | PASS | whitespace error 0; JSON valid | terminal |

### 미실행 검증과 이유

- teammate commands/clone/MFA/PR/CI: teammate machine/account에서만 가능해 human pending이다.
- Node/uv installers: 현재 owner workstation에 exact versions가 이미 있어 재설치하지 않고 버전·실행 명령만
  검증했다.
- product/API/DB tests: product code change 0; scoped docs/collaboration tests로 대체한다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: account codes/email/secret 값을 수집하거나 note에 기록하지 않는다.
- Security: web login, PR-only, no-force-push, exact scope classifier, secret-free error reporting을 명시한다.
- Accessibility: product UI change 0; future frontend ownership criteria는 390/430, 200%, keyboard, focus,
  contrast 4.5:1을 유지한다.
- Performance/cost: GitHub Free/0원 유지; initial install/E2E 시간만 발생, API/provider cost 0.

## 10. 데이터와 출처 영향

- official/mock data: unchanged, 생성·혼합·승인 0.
- schema/lineage: unchanged.
- technical sources: official Node 24.12.0 archive and Astral uv installation/Python docs.
- verified date: 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 사용자에게 지금 필요한 행동은 private repository link와 handoff의 section 0 message를 팀원에게 개인 채널로
  보내는 것이다.
- 팀원은 onboarding PR까지만 하고 멈춘다. green button이 보여도 exact eligibility 전에는 merge하지 않는다.
- first real F1 task 전에 owner가 shared-contract consumption을 준비·검토해야 한다.
- 팀원의 MFA/recovery/token/email 값은 받지 않는다; 완료 사실과 non-secret evidence만 받는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- teammate Python은 source-only CPython release 때문에 uv-managed exact interpreter로 실행하도록 명령을 구성했다.
- base SHA, write branch, self-merge path allowlist를 서로 다른 gate로 유지했다.

## 13. 인수인계·재현·롤백

### 재현

frontend handoff section 0을 개인 채널로 전달하고 teammate structured completion report를 수집한다. owner는
PR diff/author/classification/checks/merge commit과 post-merge main CI를 검증한다.

### 롤백

teammate onboarding PR 전에는 아무것도 merge하지 않으면 된다. 잘못된 PR은 close, 잘못된 merge는 revert PR,
credential 의심은 즉시 revoke/rotate한다. 문서 변경은 이 change를 revert한다.

### 다음 개발자 시작점

teammate report를 받아 Task 7 first self-merge evidence를 기록하고 forbidden-scope dry-run을 발행한다. 그 후
shared-contract consumption owner task를 준비한 뒤 WEB-CHAT fixture task를 발행한다.

## 14. 남은 위험·미해결 질문·다음 단계

- teammate actual environment/MFA/baseline/PR/CI는 pending이다.
- current local primary main은 remote main보다 뒤이며 별도 worktree에서 안전한 fast-forward가 필요하다.
- F1 web/shared-contract package/export boundary는 owner task 전까지 pending이다.
- 다음 한 단계: 사용자가 private link와 section 0 message를 `koregy`에게 보낸다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증 — docs/secret/unit 57/manifest/diff/runtime command PASS; teammate external execution pending
- [x] source-of-truth/계약/버전 동기화 — collaboration status/guidance only
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
