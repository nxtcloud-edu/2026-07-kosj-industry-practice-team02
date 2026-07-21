# IMP-20260721-006 — Codex Cloud setup form screenshot verification

- Date/Time (KST): 2026-07-21T07:30:00+09:00
- Task ID: COLLAB-CLOUD-SETUP-FORM
- Type: documentation-environment-evidence
- Status: Done — visible form verified; hidden lower script and actual execution pending
- Author/Agent: Codex primary agent
- Branch: `codex/COLLAB-001-post-merge-evidence`
- Base commit: `4b473e2`
- Related plan/ADR/RFP: COLLAB-001 plan, ADR-0019, D-057, IMP-20260721-005

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 Codex Cloud environment form과 설정 스크립트를 보여 주는 screenshot 2장을 공유하고 현재 입력이
맞는지 확인을 요청했다.

### Acceptance Criteria

- 화면에서 실제로 보이는 container/cache/manual/env/secret/script 설정을 판독한다.
- script의 보이는 각 줄을 approved setup과 문자 단위로 비교한다.
- 화면 아래에 가려진 내용을 확인한 것처럼 단정하지 않는다.
- 다음 인간 동작과 실패 시 공유할 안전한 증거를 짧게 안내한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 Cloud form 입력, Codex가 original-resolution screenshot 검증 |
| When — 언제 | 2026-07-21 KST, environment 저장 전 |
| Where — 어디서 | `Sejong_AI` Codex Cloud environment 생성 화면 |
| What — 무엇을 | universal/manual/cache/env-secret empty와 visible nvm/pyenv script prefix 검증 |
| Why — 왜 | 잘못된 runtime 또는 secret 노출 상태로 environment를 생성하지 않기 위해 |
| How — 어떻게 | 두 PNG를 original detail로 열어 IMP-005/runbook의 approved lines와 대조 |
| How much — 어느 정도 | screenshot 2장, form 설정 5개, visible shell line 8개; code/API/DB/data 변경 0 |

## 3. 시작 전 상태

- 관련 파일: owner Cloud checklist, IMP-20260721-005, current screenshots.
- 기존 동작: UI Node 22 bootstrap 후 setup에서 exact Node/Python/pnpm/uv를 적용하기로 정정됐다.
- 발견한 상태: `universal`, cache On, manual setup, 환경변수/비밀 empty, maintenance blank가 보인다. script
  editor는 상단만 보여 nvm 5줄과 pyenv 2줄까지만 판독 가능하다.
- Git 상태: 기존 Cloud documentation changes가 local/unpushed 상태이며 이번에는 제품 코드를 변경하지 않는다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| CLOUD-FORM-001 | Verified | universal/manual/cache On/env-secret empty | 그대로 유지 | safe setup |
| CLOUD-FORM-002 | Verified visible | nvm/pyenv prefix가 approved text와 일치 | PASS | exact runtime preparation |
| CLOUD-FORM-003 | Not visible | corepack/test/pnpm/uv와 final line | 사용자가 editor를 아래로 내려 마지막 줄 확인 | install gate |
| CLOUD-FORM-004 | Not run | actual setup exit/output | environment 저장·생성 뒤 확인 | rehearsal gate |

## 5. 설계 결정과 대안

### 선택

보이는 form과 script prefix는 맞다고 판정한다. 하단 미노출 부분은 full pass로 단정하지 않고 editor 마지막
줄이 `"$UV_BIN" sync --project apps/api --frozen`인지 사용자가 확인한 뒤 저장하도록 안내한다.

### 이유

두 screenshot 모두 script editor scrollbar가 상단에 있고 Python global 아래 줄은 보이지 않는다. 보이는
부분만으로 전체 paste와 실제 shell 성공을 증명할 수 없다.

### 고려했지만 선택하지 않은 대안

- 전체 script가 맞다고 단정: 숨겨진 부분과 실행 결과가 없어 제외.
- maintenance script에도 동일 명령 복사: 초기 rehearsal에서 불필요하고 중복 설치 위험이 있어 제외.
- env/secret에 runtime/API key 추가: 이번 docs-only rehearsal의 secret 0 경계를 깨므로 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| CHANGELOG/manifest | visible screenshot evidence와 docs 2.9.6 | 문서 계보 |
| this note/INDEX | 확인 범위·미확인 범위·다음 동작 | 요청별 재현 기록 |

### 데이터 흐름/상태 변화

```text
user paste → visible prefix verified → hidden tail human check → save/create → setup exit evidence
```

### 오류·빈 상태·롤백

- red wavy underline는 browser spell checker 표시이며 shell error evidence가 아니다.
- setup failure 시 secret 없는 터미널 출력만 공유하고 cache reset/edit로 복구한다.
- 실제 environment가 아직 생성되지 않았으므로 현재 rollback 작업은 없다.

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
- documentation: 2.9.5

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Docs | 2.9.5 | 2.9.6 | Cloud form screenshot evidence |
| Product/repo/application/web/API/contracts/DB/data/prompt/tests | unchanged | unchanged | 제품·runtime 계약 변경 없음 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `view_image(..., detail=original)` | PASS | 2 screenshots | user temp images; not committed |
| visible form comparison | PASS | universal/manual/cache On/env-secret empty/maintenance blank | screenshot evidence |
| visible script comparison | PASS | set, NVM_DIR, nvm source/install/alias/use, pyenv install/global | screenshot evidence |
| `python -B scripts/check_repository_docs.py --repository-root .` | PASS | active docs/JSON/link rules | terminal |
| secret pattern scan | PASS | findings 0 | terminal |
| repository docs unit tests | PASS | 21 passed, 1 expected Windows symlink skip | terminal |

### 미실행 검증과 이유

- lower script text: screenshots viewport 아래라 판독할 수 없다.
- actual Cloud setup/runtime: 사용자가 environment를 저장·생성해야 실행된다.
- product tests: product code change 0; scoped docs/security check로 대체한다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: screenshots를 commit하지 않았고 citizen data가 보이지 않는다.
- Security: 환경변수/비밀 empty와 docs-only rehearsal secret 0 경계를 확인했다.
- Accessibility: product UI 변경 0.
- Performance/cost: cache On은 후속 startup 시간을 줄인다. 아직 runtime/API 호출·비용 0.

## 10. 데이터와 출처 영향

- 공식 데이터/mock: unchanged, 생성·수정·혼합 0.
- schema/lineage: unchanged.
- source: user screenshot evidence와 IMP-005 approved setup.
- verified date: 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 현재 보이는 form과 script 앞부분은 맞다.
- red underline는 맞춤법 검사 표시라 무시해도 된다.
- maintenance script는 비워 두고 env/secret도 추가하지 않는다.
- editor를 끝까지 내려 final uv sync 줄이 있는지 확인한 뒤 저장한다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- screenshot-visible evidence와 runtime-executed evidence를 별도 gate로 유지했다.
- 제품·공개 계약·runtime pin은 변경하지 않았다.

## 13. 인수인계·재현·롤백

### 재현

두 screenshot을 original resolution으로 열고 IMP-005의 setup prefix와 form settings를 비교한다. editor 하단과
actual exit status는 별도 증거로 확인한다.

### 롤백

environment 저장 전에는 field를 고치거나 페이지를 닫는다. 저장 후 setup 오류면 script를 수정하고 cache를
reset한다. 문서 증거는 이 change를 revert한다.

### 다음 개발자 시작점

사용자가 마지막 줄 확인 후 environment를 생성하면 setup 로그에서 exact four-version tests와 frozen installs를
확인한다.

## 14. 남은 위험·미해결 질문·다음 단계

- hidden script tail typo 가능성과 actual image/runtime 차이는 아직 해소되지 않았다.
- 다음 한 단계: editor를 아래로 내려 마지막 줄 확인 → 저장/생성 → setup 결과 공유.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화 — product contract 불변
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
