# IMP-20260721-002 — COLLAB-001 owner GitHub Cloud execution guide and App-scope evidence correction

- Date/Time (KST): 2026-07-21T06:38:34+09:00
- Task ID: COLLAB-001-HUMAN-RUNBOOK
- Type: documentation-security-handoff
- Status: Done — human execution remains Pending
- Author/Agent: Codex primary agent
- Branch: `codex/COLLAB-001-bootstrap-evidence`
- Base commit: `ea33e9d1de2e053998f1bfd1071777ca33a5ea57`
- Related plan/ADR/RFP: COLLAB-001 transition plan, ADR-0019, D-047~D-056, RFP-10/RFP-11

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 앞서 남은 사람 작업인 GitHub App 범위, 팀원 MFA/recovery, Draft PR #1 병합, Codex Cloud와
팀원 Git 온보딩을 각각 어떻게 해야 하는지 자세히 요청했다.

### Acceptance Criteria

- 소유자와 팀원이 그대로 따라 할 수 있는 화면·명령·판정·실패 대응 순서를 제공한다.
- App 범위, 계정 보안, PR, Cloud, team self-merge/forbidden-scope 리허설을 분리한다.
- 비밀·개인정보·private URL을 tracked 문서에 기록하지 않는다.
- 완료되지 않은 외부 작업은 Pending으로 유지한다.
- 공식 GitHub/OpenAI 문서로 변동 가능한 UI·서비스 동작을 확인한다.
- 발견한 App-scope 증거 해석 오류를 권위 문서·결정 로그·계획에서 정정한다.
- 제품 코드, 공개 API, DB, 공식/mock data, dependency, 배포 동작은 변경하지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | Codex가 조사·문서화, 사용자 `tskwak111`이 App/PR/Cloud 실행, `koregy`가 MFA/clone/리허설 실행 |
| When — 언제 | 2026-07-21 KST; PR #1 전 단계와 병합 후 병렬 단계로 구분 |
| Where — 어디서 | GitHub 개인 계정 설정·private repository, Codex Cloud environment, 팀원 Windows clone, tracked docs |
| What — 무엇을 | 사람 실행 체크리스트, D-056 evidence correction, handoff/계획/상태/버전 동기화 |
| Why — 왜 | 처음 쓰는 사용자도 권한·비밀·병합 경계를 어기지 않고 COLLAB-001 Tasks 5~7을 재현하기 위해 |
| How — 어떻게 | 공식 문서 대조, 최소권한 UI 확인, exact 명령·Cloud prompt·성공/중단 조건 고정 |
| How much — 어느 정도 | 새 handoff 1개·결정 정정 1개·구현 노트 1개와 관련 문서 동기화; runtime 영향 0·비용 추가 0원 |

## 3. 시작 전 상태

- 관련 파일: `AGENTS.md`, COLLAB-001 design/plan, ADR-0019, `CONTRIBUTING.md`, `TASKS.md`,
  `TEAM_DECISIONS.md`, `DECISION_LOG.md`, ambiguity register, handoff guide, IMP-20260721-001,
  `versions/manifest.json`.
- 기존 동작: private remote, matching `main`, accepted collaborator/write access, repository variable,
  read-only Actions, initial hosted CI, Draft PR #1과 그 green checks까지 확인됐다.
- 발견한 충돌/부채: IMP-001과 일부 권위 문서가 connector에서 public repositories가 보인다는 사실을
  `All repositories` 또는 selected-repository 제약 미충족 증거로 잘못 해석했다.
- Git 상태: PR #1 head `ea33e9d`; 이 요청 시작 때 note generator가 INDEX와 Draft note를 생성했다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| COLLAB-H-001 | Human-only | GitHub 설치 화면의 실제 Repository access 값 | `Only select / Sejong_AI`를 사람이 직접 확인; `All`일 때만 변경 | Task 6 시작 gate |
| COLLAB-H-002 | Human-only | `koregy` MFA·복구 상태 | 인증값 없이 완료 여부만 팀원이 확인 | Task 5 closeout |
| COLLAB-H-003 | External | PR #1 merge 후 SHA/CI | 사용자가 merge한 뒤 Codex가 조회 | Task 4 evidence integration |
| COLLAB-H-004 | External rehearsal | Cloud Draft PR과 teammate 두 PR | 실제 실행 전 완료 주장 금지 | Tasks 6~7 |
| COLLAB-I-001 | Internal | PR #1 merge method | 검토 head SHA를 부모로 보존하는 merge commit 추천 | history lineage |

## 5. 설계 결정과 대안

### 선택

`docs/handoffs/HANDOFF-20260721-OWNER-GITHUB-CLOUD-CHECKLIST.md`를 단일 실행 권위로 추가하고, 순서를
pre-merge와 post-merge 병렬 단계로 나눴다. D-056은 D-055를 삭제하지 않고 증거 해석만 append-only로
정정한다.

### 이유

- 공개 repository 접근은 GitHub App의 기본 read-only 특성일 수 있어 connector 목록만으로 설치 범위를
  판정할 수 없다.
- 계정 보안 값은 repository API나 Codex가 수집할 대상이 아니며, 사람의 최소 상태 확인만 필요하다.
- Cloud와 팀원 리허설은 협업 workflow가 `main`에 있어야 실제 policy evidence가 된다.
- 상세 명령과 중단 조건을 한 문서에 모아 비전문가의 누락·잘못된 merge·secret upload 위험을 줄인다.

### 고려했지만 선택하지 않은 대안

- connector 목록만으로 App 범위를 확정: public repository 가시성 때문에 증거로 부적합하다.
- MFA 코드/화면을 소유자가 수집: 보안 위험이며 완료 여부에 필요 없다.
- PR #1보다 Cloud/team rehearsal을 먼저 실행: 현재 `main`에는 최신 협업 문서·workflow 증거가 없다.
- Cloud에 DeepSeek/DB secret 추가: docs-only 리허설에 불필요하고 승인된 local-only 경계를 위반한다.
- PR #1 squash/rebase: 검토된 head SHA를 새 SHA로 바꾸므로 merge commit보다 계보 보존이 약하다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| owner GitHub/Cloud checklist | App, MFA, PR #1, Cloud setup/task, teammate baseline/두 리허설의 exact 절차 | 사람 실행의 단일 권위 |
| D-056/TEAM_DECISIONS/ambiguity | public repository visibility의 App-scope 해석 정정 | 사실·보안 상태 정확성 |
| COLLAB-001 plan/TASKS/CONTRIBUTING | UI 확인 대기와 runbook link 동기화 | 활성 상태·완료 기준 일치 |
| IMP-20260721-001 | 후속 erratum을 해당 historical evidence note에 명시 | 잘못된 현재 행동 방지 |
| handoff/CHANGELOG/manifest/INDEX | 발견 가능성·version·lineage 갱신 | 인수인계와 문서 위생 |

### 데이터 흐름/상태 변화

```text
connector의 public repo 목록
  └─ 설치 범위 판정에 사용하지 않음
GitHub Installed App UI
  └─ Only select / Sejong_AI 사람 확인 → Cloud 환경 생성 허용
PR #1 merge
  ├─ Codex Cloud docs-only Draft PR
  └─ koregy baseline → 허용 self-merge PR → 금지 범위 close-only PR
```

제품 데이터·시민 질문·KB·DB row·API payload 흐름은 변하지 않는다.

### 오류·빈 상태·롤백

- App UI가 `All repositories`이면 `Only select / Sejong_AI`로 바꾸고 저장한다.
- 예상하지 못한 permission, PR red check/conflict, baseline 실패, 금지 파일 diff가 있으면 merge하지 않는다.
- Cloud PR이 Ready이면 Draft로 되돌리고, secret 또는 금지 파일이 있으면 PR을 닫고 branch를 폐기한다.
- forbidden dry-run PR은 `OWNER_REVIEW_REQUIRED`를 확인한 뒤 반드시 close하며 main에 marker가 없어야 한다.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.5
- repo_guidance: 1.7.1
- application: 0.3.0-pii-core
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 1.0.0-collaboration
- documentation: 2.9.1

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.5 | 2.2.5 | 제품 범위 불변 |
| Repo guidance | 1.7.1 | 1.7.2 | 사람 협업 실행 절차·App evidence correction |
| Application | 0.3.0-pii-core | 0.3.0-pii-core | runtime 불변 |
| Web | 0.2.0-static-chat-shell | 0.2.0-static-chat-shell | frontend 불변 |
| API | 2.0.1-draft | 2.0.1-draft | 공개 계약 불변 |
| Shared contracts | 0.2.1 | 0.2.1 | 생성 계약 불변 |
| DB schema | 0.3.0-local | 0.3.0-local | migration/row 불변 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | seed 없음 |
| Mock data | 0.0.0-not-populated | 0.0.0-not-populated | mock 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 0.0.2-deepseek-v4-flash-selected | LLM prompt 불변 |
| Test suite | 1.0.0-collaboration | 1.0.0-collaboration | test behavior 불변 |
| Docs | 2.9.1 | 2.9.2 | runbook·권위 문서 정정 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| official GitHub/OpenAI web documentation review | PASS | App access, 2FA/recovery, Draft/merge, Cloud environment | linked checklist sources |
| `gh repo list tskwak111 --limit 100 --json ...` | PASS | account repo visibility cross-check; private repo 1 | terminal, value-free summary only |
| `gh api user/installations` | expected unavailable | HTTP 403 for user token; cannot prove installation selection | terminal; human UI gate retained |
| `python -B scripts/check_repository_docs.py --repository-root .` | PASS | active Markdown/JSON links and tracked-file rules | terminal |
| `powershell.exe ... scripts/check_secret_patterns.ps1 -RepositoryRoot .` | PASS | current-tree findings 0; values not printed | terminal |
| `python -B -m unittest -v scripts.tests.test_repository_docs scripts.tests.test_github_collaboration_config` | PASS | 32 passed, 1 expected Windows symlink skip | terminal |
| exact JSON/manifest invariant and `git diff --check` | PASS | expected repo/docs versions; whitespace errors 0 | terminal |

### 미실행 검증과 이유

- GitHub App UI: account owner browser confirmation이 필요하다.
- PR #1 merge: 사용자 행동이며 이 문서 작업이 대신 merge하지 않는다.
- Cloud environment/Draft PR: PR #1 merge 뒤 실행한다.
- `koregy` MFA, clone, baseline, two rehearsals: 팀원 계정·환경에서만 유효한 사람 작업이다.
- Docker/Supabase/DeepSeek actual: 이 docs-only 요청 범위 밖이며 local-only owner gate를 유지한다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 원문·실제 PII·계정 이메일·전화번호·인증정보를 추가하지 않았다.
- Security: App 최소 private-repo scope, 2FA/recovery, no-secret Cloud, PR-only와 owner-review 중단 조건을
  구체화했다. public repository visibility를 보안 실패로 오판한 기록을 정정했다.
- Accessibility: 제품 UI 변경 0. 문서는 순서·복사 가능한 명령·판정 표를 제공한다.
- Performance/cost: runtime 성능·bundle·API call 0. GitHub Free와 초기 예산 0원 유지.

## 10. 데이터와 출처 영향

- 공식 데이터: unchanged, `0.0.0-not-populated`; seed/approval/verified date 변경 0.
- mock/AI 생성: unchanged; official/mock 혼합 0.
- schema/lineage: DB/API/data lineage 불변. D-056과 이 note가 collaboration evidence correction lineage다.
- verified date: official web documentation checked 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 먼저 GitHub App UI를 확인한다. 이미 `Only select repositories / Sejong_AI`이면 바꿀 것이 없고, `All
  repositories`일 때만 변경한다.
- public repository가 Codex에서 보이는 것은 설치 범위 위반의 증거가 아니다.
- `koregy`는 MFA와 recovery를 직접 확인하고 상태만 공유한다. 어떠한 인증 값도 공유하지 않는다.
- PR #1은 Ready 전환·green checks·diff 확인 뒤 merge commit으로 병합한다.
- PR #1 이후 Cloud 리허설과 teammate onboarding은 병렬 가능하지만, 실제 증거 전 Tasks 6~7은 Pending이다.
- Cloud에 DeepSeek key, DB DSN, context secret, 시민 fixture를 넣지 않는다.
- 이 작업은 public deployment, remote DB, data deletion/migration 또는 제품 범위 승인이 아니다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- Markdown 링크·행 배치·D-056 append·manifest timestamp와 version 축을 동기화했다.
- 외부 UI의 완료 여부를 추론하지 않고 human-only/remote evidence를 Pending으로 유지했다.
- runbook 명령은 existing lock/runtime/workflow contract를 재사용하며 새 production dependency가 없다.

## 13. 인수인계·재현·롤백

### 재현

1. owner checklist의 0→9 순서로 실행한다.
2. 각 external 완료 뒤 PR 번호·check 이름·상태만 이 Codex 작업에 전달한다.
3. Codex가 remote evidence를 읽고 source-of-truth/plan/TASKS/note를 갱신한다.
4. 비밀값·private URL·MFA 자료·전체 CI log는 tracked 문서에 복사하지 않는다.

### 롤백

- 문서 정정 롤백: 이 요청 commit을 revert한다. 단, D-056을 되돌리면 잘못된 App-scope 해석이 되살아나므로
  공식 GitHub 동작 변화의 새 증거가 있을 때만 한다.
- App 변경 롤백: GitHub Installed App의 repository access를 이전 값으로 되돌리거나 App을 suspend/uninstall한다.
- PR 리허설 롤백: merge 전 close/delete branch, merge 뒤에는 별도 revert PR을 사용한다. force/reset하지 않는다.
- Cloud 환경 롤백: task/PR을 close하고 environment를 삭제한다. local secret/DB에는 영향이 없어야 한다.

### 다음 개발자 시작점

`docs/handoffs/HANDOFF-20260721-OWNER-GITHUB-CLOUD-CHECKLIST.md`를 읽고, 완료된 외부 증거만 COLLAB-001
plan Task 5~7에 체크한다. PR #1 merge 전 Cloud/team rehearsal을 시작하지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- Human pending: App UI, `koregy` MFA/recovery, PR #1 merge.
- Post-merge pending: Cloud Draft PR, teammate baseline/self-merge/forbidden-scope PR.
- GitHub Free private repo에서 branch protection을 전제하지 않으므로 사람의 direct-main 금지 준수가 중요하다.
- Codex/OpenAI/GitHub UI 명칭은 서비스 업데이트로 변할 수 있다. 찾지 못하면 official links의 최신 경로를 따른다.
- 다음 한 단계: 사용자가 App UI 확인 결과와 PR #1 merge 완료를 알려 준다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화 — public contract/DB 불변
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
