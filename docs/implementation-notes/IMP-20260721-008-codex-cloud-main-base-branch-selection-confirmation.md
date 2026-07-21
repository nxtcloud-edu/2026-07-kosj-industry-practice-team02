# IMP-20260721-008 — Codex Cloud main base branch selection confirmation

- Date/Time (KST): 2026-07-21T08:56:28+09:00
- Task ID: COLLAB-CLOUD-BASE-BRANCH
- Type: documentation-source-control-evidence
- Status: Done — base selection verified; submit/setup/Draft PR pending
- Author/Agent: Codex primary agent
- Branch: `codex/COLLAB-001-post-merge-evidence`
- Base commit: `4b473e2`
- Related plan/ADR/RFP: COLLAB-001 plan, ADR-0019, D-057, IMP-20260721-007

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 첫 Codex Cloud rehearsal 작성 화면에서 branch selector를 `main`으로 둬도 되는지 물었다.

### Acceptance Criteria

- screenshot의 environment와 branch selection을 판독한다.
- base branch와 task working branch의 차이를 비전문가도 이해할 수 있게 설명한다.
- main 직접 commit/merge로 오해하지 않도록 금지 경계를 명확히 한다.
- 다음 UI 동작을 한 문장으로 안내한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | repository owner가 base 선택, Cloud agent가 별도 task branch 작성 |
| When — 언제 | 2026-07-21 KST, rehearsal prompt 제출 직전 |
| Where — 어디서 | Codex Cloud composer의 `sejong-ai-cloud-docs` environment와 branch selector |
| What — 무엇을 | `main`을 base로 선택하고 변경은 `codex/COLLAB-CLOUD-REHEARSAL-001-doc-check`에 제한 |
| Why — 왜 | 최신 승인 기준선에서 시작하되 main 직접 변경을 막기 위해 |
| How — 어떻게 | screenshot과 active runbook branch instruction을 대조 |
| How much — 어느 정도 | screenshot 1장·branch 경계 1개; product/source/dependency 변경 0 |

## 3. 시작 전 상태

- 관련 파일: owner Cloud checklist section 5, current screenshot.
- 기존 동작: active prompt는 exact `codex/COLLAB-CLOUD-REHEARSAL-001-doc-check` branch와 Draft PR only를
  요구한다.
- 발견한 상태: composer는 saved `sejong-ai-cloud-docs` environment와 base selector `main`을 표시한다.
- Git 상태: local documentation evidence branch는 prior unpushed changes를 보존하며 remote write 0이다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| CLOUD-BRANCH-001 | Resolved | composer base branch | `main` | checkout baseline |
| CLOUD-BRANCH-002 | Enforced by prompt | change branch | `codex/COLLAB-CLOUD-REHEARSAL-001-doc-check` | PR head |
| CLOUD-BRANCH-003 | Pending evidence | agent가 branch/diff 제한을 실제 지켰는가 | result diff와 Draft PR에서 확인 | merge safety |

## 5. 설계 결정과 대안

### 선택

composer에서 `main`을 유지하고 제출한다. 이것은 읽어 시작할 기준선이며, agent가 main에 직접 쓰거나 merge하는
승인이 아니다. 결과는 prompt의 별도 `codex/*` branch와 Draft PR로만 남긴다.

### 이유

Cloud task는 선택한 branch/commit에서 checkout을 시작한다. approved latest baseline은 remote main이며 isolation은
task branch와 Draft PR이 담당한다.

### 고려했지만 선택하지 않은 대안

- 현재 local docs branch 선택: remote에 없고 rehearsal 기준선이 아니므로 제외.
- main 직접 commit/merge: branch policy와 rehearsal 목적을 위반하므로 금지.
- 임의 새 base branch 선택: 승인 근거와 재현성이 없어 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| CHANGELOG/manifest | main base/task branch 경계와 docs 2.9.8 | lineage |
| this note/INDEX | screenshot decision evidence | request-level note |

### 데이터 흐름/상태 변화

```text
remote main (read base) → isolated codex/* task branch (two docs changes) → Draft PR → no merge
```

### 오류·빈 상태·롤백

- agent가 main 직접 변경, 다른 branch, 또는 forbidden file diff를 만들면 PR을 만들거나 merge하지 않는다.
- 아직 제출 전이므로 selector는 그대로 두거나 prompt를 수정할 수 있다.

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
- documentation: 2.9.7

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Docs | 2.9.7 | 2.9.8 | Cloud base-branch screenshot confirmation |
| Product/repo/application/web/API/contracts/DB/data/prompt/tests | unchanged | unchanged | product/source-control policy 변경 없음 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `view_image(..., detail=original)` | PASS | environment `sejong-ai-cloud-docs`, branch `main` | user temp image; not committed |
| active runbook branch instruction lookup | PASS | exact codex task branch + Draft PR only | owner checklist section 5 |
| `python -B scripts/check_repository_docs.py --repository-root .` | PASS | active docs/JSON/link rules | terminal |
| secret pattern scan | PASS | findings 0 | terminal |
| repository docs unit tests | PASS | 21 passed, 1 expected Windows symlink skip | terminal |

### 미실행 검증과 이유

- Cloud setup/task branch/diff/PR: prompt가 아직 제출되지 않았다.
- product tests: product code change 0; scoped docs/security checks로 대체한다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: screenshot을 commit하지 않고 account data를 문서화하지 않았다.
- Security: main write/merge 금지와 isolated Draft PR 경계를 유지한다.
- Accessibility: product UI 변경 0.
- Performance/cost: API/infrastructure 실행·비용 0; submit 후 Cloud setup만 발생한다.

## 10. 데이터와 출처 영향

- official/mock/schema/lineage: unchanged.
- source: user screenshot and active owner checklist.
- verified date: 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- `main` 선택은 맞으며 출발 기준선일 뿐이다.
- 변경은 반드시 prompt의 `codex/*` branch와 Draft PR에만 있어야 한다.
- main 직접 commit 또는 merge는 승인되지 않았다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- base ref와 PR head ref를 별개 gate로 모델링했다.
- 기존 Git/Cloud 정책과 product contract는 변경하지 않았다.

## 13. 인수인계·재현·롤백

### 재현

composer에서 environment `sejong-ai-cloud-docs`, branch `main`, exact rehearsal prompt를 확인한다.

### 롤백

제출 전에는 작업을 보내지 않으면 된다. 제출 후 잘못된 branch/diff면 PR을 merge하지 않고 닫는다.

### 다음 개발자 시작점

main selector를 유지하고 submit한 뒤 setup result와 final diff branch를 확인한다.

## 14. 남은 위험·미해결 질문·다음 단계

- 실제 agent branch/diff/Draft PR evidence는 pending이다.
- 다음 한 단계: 오른쪽 화살표로 제출하고 첫 setup/task 결과를 확인한다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화 — policy unchanged
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
