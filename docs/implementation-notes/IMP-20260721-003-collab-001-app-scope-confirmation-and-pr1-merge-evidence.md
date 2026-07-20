# IMP-20260721-003 — COLLAB-001 App scope confirmation and PR1 merge evidence

- Date/Time (KST): 2026-07-21T07:04:15+09:00
- Task ID: COLLAB-001-POST-MERGE
- Type: documentation-security-evidence
- Status: Done — COLLAB-001 remains In Progress
- Author/Agent: Codex primary agent
- Branch: `codex/COLLAB-001-post-merge-evidence`
- Base commit: `ce8a6085fb57670ca74e009ed45e3d02d784c24b`
- Related plan/ADR/RFP: COLLAB-001 plan, ADR-0019, D-047~D-057, RFP-10/RFP-11

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 앞선 체크리스트 1번 GitHub App 확인과 3번 PR #1 병합을 완료했다고 알리고, 2번
MFA/recovery가 단순히 친구 개인 계정 보안을 위한 것인지 질문했다.

### Acceptance Criteria

- PR #1 merge와 remote `main`/post-merge CI를 외부 evidence로 검증한다.
- 사용자의 App UI 확인을 human evidence로 기록하되 인증값을 수집하지 않는다.
- MFA가 collaborator 개인 계정과 repository 공급망을 함께 보호한다는 이유를 설명한다.
- MFA는 Cloud/backend 진행 blocker가 아니지만 팀원의 첫 push 전 강한 권고임을 구분한다.
- source-of-truth/plan/TASKS/version/implementation note를 동기화하고 제품/API/DB/data는 바꾸지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 App/merge 완료 확인, GitHub가 PR/CI evidence 제공, Codex가 검증·문서화, `koregy`가 자기 MFA 수행 |
| When — 언제 | PR merge `2026-07-21T07:01:36+09:00`; 사용자 완료 진술과 처리 `2026-07-21T07:04+09:00` |
| Where — 어디서 | private `tskwak111/Sejong_AI`, GitHub App UI, GitHub Actions, active collaboration docs |
| What — 무엇을 | PR #1 merge/post-merge CI/App scope 완료와 MFA 의미·남은 경계 기록 |
| Why — 왜 | 완료 상태를 추측 없이 갱신하고 write collaborator 계정 탈취의 repository 위험을 분명히 하기 위해 |
| How — 어떻게 | GitHub connector PR/repository 조회, local `git fetch`, `gh run list`, docs/security gate |
| How much — 어느 정도 | merge commit 1개·hosted run 2개 검증, 문서/메타데이터만 변경, runtime·비용·데이터 영향 0 |

## 3. 시작 전 상태

- 관련 파일: COLLAB-001 plan/checklist, `TASKS.md`, ambiguity/decision/source-of-truth, README,
  deployment guide, CHANGELOG, manifest, INDEX.
- 기존 동작: PR #1은 Draft/CLEAN/green이었고 App scope와 merge는 사람 작업 Pending이었다.
- 발견한 충돌/부채: 사용자의 완료 진술 뒤 active docs가 App/PR merge를 Pending으로 표시했다.
- Git 상태: remote `main`은 merge 전 `5e09dec`; root local `main`도 그 SHA였다. fetch 후 remote
  `main=ce8a608`, status branch는 remote merge commit 기반 새 docs branch다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| COLLAB-PM-001 | Human evidence | App UI value | 사용자 1번 완료 진술을 `Only select / Sejong_AI` confirmation으로 기록 | Task 6 App gate complete |
| COLLAB-PM-002 | External evidence | PR #1 merge/main CI | connector·git·Actions로 independent verification | trusted source baseline |
| COLLAB-PM-003 | Human pending | `koregy` MFA/recovery | 코드 없이 status만 확인; first push 전 strongly recommended | Task 5 partial, non-blocking |
| COLLAB-PM-004 | External pending | Cloud/teammate rehearsals | actual PR evidence 전 완료 주장 금지 | Tasks 6~7 remain open |

## 5. 설계 결정과 대안

### 선택

D-057에 App scope와 merge/post-merge CI evidence를 append하고, Task 6은 `Pending`에서 `Partial`로
바꾼다. MFA는 계정·repository supply-chain 통제이지만 Cloud/backend blocker는 아니며, 팀원의 첫 push
전 완료를 권고한다.

### 이유

`koregy` 계정은 private repository write 권한이 있다. 계정 탈취 시 소스 열람뿐 아니라 branch/PR/commit
작성과, branch protection을 전제하지 않는 현재 0원 운영에서는 direct `main` push 위험도 생긴다. 반면
MFA 설정은 계정 소유자의 책임이고 인증 자료를 repository owner가 수집할 필요가 없다.

### 고려했지만 선택하지 않은 대안

- MFA 생략·개인 문제로만 분류: repository write 공급망 위험을 무시하므로 선택하지 않았다.
- MFA 코드/복구 코드 수집: 비밀 수집 위험이며 상태 증명에 불필요하다.
- MFA가 끝날 때까지 모든 개발 차단: Cloud/backend와 독립이므로 과도하다.
- 사용자 진술만으로 PR/CI 완료 기록: GitHub에서 독립 검증할 수 있어 선택하지 않았다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| D-057, source-of-truth, ambiguity | App/merge evidence와 MFA 경계 | 권위 상태 정확성 |
| COLLAB plan/TASKS | Task 6 Partial, remaining evidence | 실행 순서와 완료 기준 |
| README/deployment/CHANGELOG | 현재 운영 상태 요약 | 신규 개발자·운영자 인수인계 |
| manifest/INDEX/this note | repo/docs version·6W1H evidence | 문서 위생·재현성 |

### 데이터 흐름/상태 변화

```text
PR #1 head 46506c7
  → merge commit ce8a608 on remote main
  → post-merge policy PASS + Frontend CI PASS

App scope: Pending → Confirmed
Task 6: Pending → Partial
MFA/recovery: Pending, non-blocking but recommended before teammate first push
```

제품 데이터, 시민 질문, KB, DB row, API payload는 변하지 않는다.

### 오류·빈 상태·롤백

- App confirmation이 잘못 전달된 경우 GitHub UI를 다시 확인하고 후속 correction decision을 append한다.
- merge commit은 force/reset하지 않는다. 문제가 발견되면 별도 revert PR을 사용한다.
- Actions failure가 새로 확인되면 COLLAB 진행을 멈추고 CI debugging workflow로 전환한다.
- teammate가 MFA를 사용하지 않으면 owner는 위험을 명시적으로 수용하거나 collaborator write access를 revoke한다.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.5
- repo_guidance: 1.7.2
- application: 0.3.0-pii-core
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 1.0.0-collaboration
- documentation: 2.9.2

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.5 | 2.2.5 | 제품 범위 불변 |
| Repo guidance | 1.7.2 | 1.7.3 | post-merge/App/MFA 운영 상태 |
| Application | 0.3.0-pii-core | 0.3.0-pii-core | runtime 불변 |
| Web | 0.2.0-static-chat-shell | 0.2.0-static-chat-shell | frontend 불변 |
| API | 2.0.1-draft | 2.0.1-draft | 공개 계약 불변 |
| Shared contracts | 0.2.1 | 0.2.1 | generated types 불변 |
| DB schema | 0.3.0-local | 0.3.0-local | migration/row 불변 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | seed 없음 |
| Mock data | 0.0.0-not-populated | 0.0.0-not-populated | mock 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 0.0.2-deepseek-v4-flash-selected | LLM 불변 |
| Test suite | 1.0.0-collaboration | 1.0.0-collaboration | test behavior 불변 |
| Docs | 2.9.2 | 2.9.3 | external evidence/status sync |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| GitHub connector `get_pr_info` / `get_repo` | PASS | PR #1 merged, private repo, merge SHA | authenticated connector |
| `git fetch origin --prune`, local/remote refs | PASS | `origin/main=ce8a608` | terminal |
| `gh run list --branch main ...` | PASS | policy `29782433649`, frontend `29782433682` success | GitHub Actions metadata |
| `python -B scripts/check_repository_docs.py --repository-root .` | PASS | active docs/JSON/link rules | terminal |
| `powershell.exe ... scripts/check_secret_patterns.ps1 -RepositoryRoot .` | PASS | current-tree findings 0 | terminal |
| `python -B -m unittest -v scripts.tests.test_repository_docs scripts.tests.test_github_collaboration_config` | PASS | 32 passed, 1 expected Windows symlink skip | terminal |
| exact manifest invariant and `git diff --check` | PASS | repo 1.7.3/docs 2.9.3; whitespace errors 0 | terminal |

### 미실행 검증과 이유

- App UI 재조회: human-only 화면이며 사용자 완료 진술을 기록했다.
- `koregy` MFA: 계정 소유자가 수행하며 인증 자료를 수집하지 않는다.
- Cloud environment/Draft PR와 teammate rehearsals: 아직 실행 증거가 없다.
- product build/API/DB/Docker/DeepSeek: 변경 영역 밖이며 이 상태 기록의 완료 근거가 아니다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 이메일·전화번호·OTP·recovery code·시민 원문·secret을 수집하거나 기록하지 않았다.
- Security: App private-repo scope와 merge CI를 확인했고 MFA의 write-supply-chain 목적을 명시했다.
- Accessibility: 제품 UI 변경 0.
- Performance/cost: runtime/API/LLM call/dependency/비용 변경 0; GitHub Free·초기 0원 유지.

## 10. 데이터와 출처 영향

- 공식 데이터: unchanged, `0.0.0-not-populated`.
- mock/AI 생성: unchanged; official/mock 혼합 0.
- schema/lineage: DB/API/data lineage 불변; D-057은 source-control operational evidence lineage다.
- verified date: 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- App scope와 PR #1 merge/post-merge CI는 완료됐다.
- MFA는 친구 계정 자체뿐 아니라 write collaborator를 통한 repository 변조 위험을 줄인다.
- owner는 MFA code/recovery code를 받지 않고 `enabled/stored` 상태만 확인한다.
- MFA는 지금 Cloud/backend 진행을 막지 않지만 `koregy`의 첫 push/PR 전 완료를 강하게 권장한다.
- MFA를 하지 않기로 하면 위험 수용 또는 collaborator revoke 중 하나를 사람이 선택한다.
- 다음 owner 작업은 no-secret Codex Cloud environment와 docs-only Draft PR rehearsal이다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- connector PR metadata와 local refs/Actions run을 교차 검증했다.
- 문서 status wording과 manifest/INDEX만 동기화했으며 public contract와 product behavior는 불변이다.

## 13. 인수인계·재현·롤백

### 재현

1. GitHub PR #1에서 merged/merge commit을 확인한다.
2. remote `main`이 `ce8a6085...`인지 확인한다.
3. 해당 SHA의 policy/frontend push run이 success인지 확인한다.
4. App scope는 사용자 human evidence, MFA는 teammate status-only evidence로 구분한다.

### 롤백

- 이 docs status commit은 별도 revert로 되돌린다.
- PR #1 제품 문제가 발견되면 merge commit에 대한 revert PR을 만들고 force/reset하지 않는다.
- App/teammate access는 GitHub settings에서 revoke하며 인증 자료를 저장하지 않는다.

### 다음 개발자 시작점

COLLAB owner checklist의 Cloud environment와 Task 6 docs-only prompt를 실행한다. MFA는 병렬로 친구에게
요청하되 기다리는 동안 backend/Cloud 준비를 멈추지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- Task 5: `koregy` MFA/recovery와 첫 PR-only/no-direct-main-push rehearsal Pending.
- Task 6: Cloud environment, docs-only Draft PR, owner manual merge Pending.
- Task 7: clone/baseline/self-merge/forbidden-scope rehearsal Pending.
- GitHub Free에서 branch protection을 전제하지 않으므로 collaborator account security와 사람 규칙이 중요하다.
- 다음 한 단계: 사용자가 Cloud environment를 만들거나 `koregy`가 MFA status를 회신한다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화 — product/API/DB/data 불변
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
