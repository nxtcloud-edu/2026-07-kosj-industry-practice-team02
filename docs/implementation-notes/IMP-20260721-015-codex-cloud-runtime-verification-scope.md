# IMP-20260721-015 — Codex Cloud runtime verification scope

- Date/Time (KST): 2026-07-21T16:43:00+09:00
- Task ID: COLLAB-CLOUD-RUNTIME-EVIDENCE-001
- Type: documentation-environment-handoff
- Status: Done — read-only Cloud prompt prepared; human execution Pending
- Author/Agent: Codex primary agent
- Branch: `codex/COLLAB-001-pr2-merge-evidence`
- Base commit: `b64f4c4`
- Related plan/ADR/RFP: COLLAB-001 Task 6, ADR-0019, D-051/D-052/D-054, owner Cloud checklist

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 현재 Codex Cloud에서 무엇을 실행할 것인지 물었다.

### Acceptance Criteria

- 당장 실행할 Cloud 작업을 한 가지로 좁힌다.
- 복사 가능한 prompt, 명령, 기대 버전, 실패 처리 기준을 제공한다.
- secrets/DeepSeek/Docker/Supabase/DB/배포 금지 경계를 명시한다.
- Cloud가 가능한 후속 작업과 반드시 local에서 끝내야 하는 gate를 분리한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 저장소 owner가 Cloud task를 제출하고 Codex Cloud가 읽기 전용 검증 수행 |
| When — 언제 | owner docs PR과 teammate PR 조정 중 병렬 실행 가능 |
| Where — 어디서 | Codex Cloud environment `sejong-ai-cloud-docs`, base `main` |
| What — 무엇을 | Node/Python/pnpm/uv exact runtime과 clean tree 검증 |
| Why — 왜 | COLLAB-001 Task 6의 마지막 Cloud runtime evidence를 닫기 위해 |
| How — 어떻게 | version/status/diff/docs-check 명령만 실행하고 파일·commit·PR 생성 금지 |
| How much — 어느 정도 | runtime 4개, Git 상태 3개, docs check 1개; 외부 API/DB 호출 0 |

## 3. 시작 전 상태

- 관련 파일: COLLAB plan Task 6, owner Cloud checklist, `AGENTS.md`.
- 기존 동작: secret-free Cloud environment와 docs-only Draft PR/manual merge는 검증됐다.
- 발견한 충돌/부채: exact Node `24.12.0`, Python `3.12.13`, pnpm `11.13.0`, uv `0.11.28` 실제 출력이 tracked evidence에 없다.
- Git 상태: local docs branch clean before this request; Cloud execution itself is Pending.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| CLOUD-RUNTIME-001 | Human execution | Cloud runtime actual values | mismatch면 설치/수정하지 않고 실제 값과 실패 명령만 보고 | supply-chain reproducibility |
| CLOUD-RUNTIME-002 | Security | 환경 전체 출력은 secret 노출 가능 | `env`, `printenv`, `.env` 열람 금지 | credential confidentiality |
| CLOUD-RUNTIME-003 | Scope | no-change task가 branch/PR을 만들 필요가 있는가 | 파일 변경·commit·PR 모두 금지 | note sequence/PR churn 방지 |

## 5. 설계 결정과 대안

### 선택

현재 Cloud에는 `COLLAB-CLOUD-RUNTIME-EVIDENCE-001` 읽기 전용 task 하나만 실행한다. 결과를 owner에게 전달하고 repository 변경은 만들지 않는다.

### 이유

Cloud PR rehearsal은 이미 완료됐고 남은 Task 6 gap은 exact runtime 출력뿐이다. 제품 구현을 섞으면 원인과 evidence가 흐려진다.

### 고려했지만 선택하지 않은 대안

- Cloud에서 DATA-SEED-002 actual DB 실행: patched local Supabase/Docker gate가 필요해 제외.
- DeepSeek key를 Cloud secret으로 추가: local-only/initial budget/secret boundary와 충돌해 제외.
- runtime mismatch를 task가 즉시 설치로 수정: 승인된 setup과 실제 image drift를 숨기므로 제외.
- no-change task에서 구현 노트/PR 생성: note ID와 PR churn을 늘려 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| COLLAB plan | exact read-only Cloud prompt 추가 | canonical reproduction |
| this note/INDEX | 사용자 안내와 경계 기록 | request-level audit |
| manifest | docs `2.10.3→2.10.4` | lineage |

### 데이터 흐름/상태 변화

```text
Cloud setup/cache
  → exact version commands
  → clean git/docs check
  → text-only result to owner
  → no file / no commit / no PR
```

### 오류·빈 상태·롤백

- 한 버전이라도 다르면 `FAIL`로 보고하고 설치·alias·PATH 변경을 하지 않는다.
- command가 없으면 `command not found`인 도구명만 보고한다.
- 이 문서 변경의 rollback은 note/INDEX/plan/manifest를 함께 revert한다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.3.0-pii-core | unchanged | no product code |
| Web | 0.2.0-static-chat-shell | unchanged | no UI work |
| API | 2.0.1-draft | unchanged | no route/contract |
| DB schema | 0.3.0-local | unchanged | no DB |
| Official data | 0.0.0-not-populated | unchanged | no seed |
| Mock data | 0.0.0-not-populated | unchanged | no fixture |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | unchanged | no provider call |
| Test suite | 1.0.0-collaboration | unchanged | existing docs check only |
| Docs | 2.10.3 | 2.10.4 | Cloud runtime handoff |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| Codex manual helper | FAIL — official manual HEAD returned HTTP 403 | 1 attempt | terminal; no project impact |
| `codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp` | PASS | global docs MCP registered | terminal; app restart may be needed |
| official-domain fallback search | Partial | official Codex use-case page found; environment-specific claims not derived from it | official OpenAI docs |
| repository plan/prompt review | PASS | Task 6 exact versions and local-only boundaries confirmed | tracked COLLAB plan |

### 미실행 검증과 이유

- Cloud runtime commands: user must submit the task in Cloud; Pending.
- product/API/DB/browser tests: repository behavior change 0.
- DeepSeek/Supabase/Docker: explicitly prohibited in this Cloud task.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: citizen text와 fixture 사용 0.
- Security: env dump, secret access, external provider/DB calls 금지.
- Accessibility: UI 변경 없음.
- Performance/cost: Cloud task 1회 외 runtime/provider 비용 0.

## 10. 데이터와 출처 영향

- 공식 데이터/mock/schema/lineage: unchanged.
- verified date: 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Cloud 새 task에 아래 canonical prompt를 붙여 넣어야 실제 evidence가 완료된다.
- task 결과에서 값이 다르면 수정하지 말고 결과를 owner Codex에게 전달한다.
- DeepSeek API key는 Cloud에 넣지 않는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- teammate용 note ID `014`를 보존하기 위해 이 note는 수동으로 `015`를 사용한다.
- no-change Cloud task는 implementation-note 규칙의 repository mutation을 만들지 않고 결과를 이 owner note에 후속 기록한다.

## 13. 인수인계·재현·롤백

### 재현

Cloud에서 `sejong-ai-cloud-docs`와 base `main`을 선택하고 COLLAB plan의 canonical prompt를 제출한다.

### 롤백

이 note/INDEX/plan과 docs manifest bump를 revert한다. 등록한 docs MCP를 제거하려면 사용자가 별도로 Codex global MCP 설정에서 삭제한다.

### 다음 개발자 시작점

Cloud result의 네 version과 clean-tree/docs-check 결과를 그대로 수집하고 Task 6 status를 갱신한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Pending: actual Cloud runtime output.
- Local-only: DATA-SEED-002 actual DB, Docker/Supabase, DeepSeek actual.
- Next: user runs the prompt and returns the textual summary or screenshot.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증 — prompt/document checks; actual Cloud run Pending 명시
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
