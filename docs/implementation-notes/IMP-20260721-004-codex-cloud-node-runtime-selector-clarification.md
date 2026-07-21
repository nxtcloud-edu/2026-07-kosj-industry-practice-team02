# IMP-20260721-004 — Codex Cloud Node runtime selector clarification

- Date/Time (KST): 2026-07-21T07:15:35+09:00
- Task ID: COLLAB-CLOUD-RUNTIME-UI
- Type: documentation-environment-guidance
- Status: Superseded by IMP-20260721-005 after expanded dropdown evidence
- Author/Agent: Codex primary agent
- Branch: `codex/COLLAB-001-post-merge-evidence`
- Base commit: `afce31d`
- Related plan/ADR/RFP: COLLAB-001 plan, ADR-0019, D-010, D-057

> **Successor correction:** 이 노트는 첫 screenshot만 본 당시의 기록이다. 후속 screenshot에서 Node 선택지가
> `22 / 20 / 18`뿐임을 확인했으므로 아래의 “Node 24를 UI에서 선택” 지시는 실행하지 않는다. 현재 절차는
> [IMP-20260721-005](IMP-20260721-005-codex-cloud-node-24-setup-fallback-after-selector-limit.md)와 owner
> Cloud checklist의 Node 22 bootstrap + nvm Node 24.12.0 setup을 따른다.

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 Codex Cloud environment의 **사전 설치된 패키지** 화면을 캡처해 현재 Node.js `22` 선택이
맞는지 물었다.

### Acceptance Criteria

- 스크린샷의 실제 선택값을 판독한다.
- repository exact runtime contract와 비교해 선택할 값을 단정적으로 안내한다.
- UI가 major/minor만 보여 주는 경우와 Node 24가 없는 경우의 중단 조건을 설명한다.
- active owner checklist와 구현 노트를 갱신하되 제품/API/DB/data는 바꾸지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 Cloud UI 선택, Codex가 이미지·repo contract·공식 manual 대조 |
| When — 언제 | 2026-07-21 KST, Cloud environment 생성 중 |
| Where — 어디서 | Codex Cloud `universal` image package selector와 repository runtime files |
| What — 무엇을 | Node 22 불일치, Node 24/Python 3.12 선택과 exact setup 검증 안내 |
| Why — 왜 | 잘못된 major로 frozen install·engine gate가 실패하는 것을 사전에 막기 위해 |
| How — 어떻게 | original screenshot 확인, `.node-version`·`.python-version`·`package.json`과 Codex manual 대조 |
| How much — 어느 정도 | runbook 문장 1개·note/INDEX/version sync; runtime code·dependency·비용 영향 0 |

## 3. 시작 전 상태

- 관련 파일: `.node-version`, `.python-version`, `package.json`, owner Cloud checklist, manifest/INDEX.
- 기존 동작: repo는 Node `24.12.0`, Python `3.12.13`, pnpm `11.13.0`을 pin하고 Node engine
  `>=24.0.0 <25.0.0`을 요구한다.
- 발견한 충돌/부채: screenshot은 Python `3.12`, Node.js `22`를 선택한 상태다. Python major/minor는
  맞지만 Node major는 계약과 충돌한다. 기존 runbook은 exact patch를 언급했으나 major-only UI의 실제
  선택값을 충분히 직접적으로 설명하지 않았다.
- Git 상태: local docs branch `afce31d` 뒤의 documentation-only follow-up; remote write 없음.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| CLOUD-RT-001 | Human UI | Node dropdown에 24가 있는가 | 있으면 24 선택; 없으면 저장 중지 후 expanded screenshot 요청 | environment creation |
| CLOUD-RT-002 | Runtime | selector의 exact patch | setup의 exact `test`로 확인; 실패 evidence 뒤 조정 | reproducibility |
| CLOUD-RT-003 | Internal | 다른 언어 선택값 | repository가 사용하지 않으므로 기본값 유지 | no project impact |

## 5. 설계 결정과 대안

### 선택

Cloud UI에서 Python `3.12`, Node.js `24`를 선택한다. Node `22`는 저장하지 않는다. Node 24가 옵션에
없으면 setup 설치 방식을 추측하지 않고 dropdown 증거를 추가로 확인한다. exact patch는 existing setup
script가 fail-fast로 검증한다.

### 이유

`package.json`의 Node engine은 major 24만 허용한다. UI의 major 선택과 repository의 exact patch pin은
서로 다른 층이므로, UI에서 올바른 major를 선택한 뒤 setup에서 exact 값을 검증해야 한다.

### 고려했지만 선택하지 않은 대안

- Node 22 그대로 저장: engine contract 위반이므로 제외.
- Node 22에서 dependency install을 먼저 시도: 예측 가능한 실패를 만들므로 제외.
- 확인 없이 nvm/별도 설치 명령 추가: 현재 image capability와 옵션을 보지 않은 추측이므로 제외.
- 사용하지 않는 Ruby/Rust/Go 등도 변경: 범위와 무관해 기본값 유지.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| owner Cloud checklist | major-only UI에서 Python 3.12/Node 24, Node 22 금지, 24 부재 시 stop 조건 | 화면 그대로 실행 가능하게 함 |
| CHANGELOG/manifest | guidance와 repo/docs version sync | 인수인계·버전 계보 |
| this note/INDEX | screenshot diagnosis와 테스트·rollback | 요청별 의무 기록 |

### 데이터 흐름/상태 변화

```text
Cloud UI Node 22 (invalid)
  → dropdown Node 24
  → setup checks exact Node 24.12.0 / Python 3.12.13 / pnpm 11.13.0 / uv 0.11.28
  → pass면 environment 저장·리허설 진행, fail이면 중단·증거 확인
```

### 오류·빈 상태·롤백

- Node 24가 없으면 저장하지 않고 dropdown screenshot을 요청한다.
- setup exact version check가 실패하면 runtime을 임의 완화하지 않고 non-secret version output만 기록한다.
- 잘못 저장했으면 package selection/setup을 수정하고 Cloud environment cache를 reset한다.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.5
- repo_guidance: 1.7.3
- application: 0.3.0-pii-core
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 1.0.0-collaboration
- documentation: 2.9.3

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Repo guidance | 1.7.3 | 1.7.4 | Cloud runtime selector clarification |
| Docs | 2.9.3 | 2.9.4 | screenshot diagnosis/runbook/note |
| Application/Web/API/contracts/DB/data/prompt/tests | unchanged | unchanged | runtime/product 변경 없음 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| original-resolution screenshot inspection | PASS | Python 3.12, Node.js 22 selected | user-provided temporary image; not committed |
| `.node-version`, `.python-version`, `package.json` inspection | PASS | 24.12.0 / 3.12.13 / Node >=24 <25 / pnpm 11.13.0 | repository files |
| Codex manual Cloud environment section | PASS | package versions selectable; setup script and cache semantics confirmed | official manual cache |
| `python -B scripts/check_repository_docs.py --repository-root .` | PASS | active docs/JSON/link rules | terminal |
| `powershell.exe ... scripts/check_secret_patterns.ps1 -RepositoryRoot .` | PASS | current-tree findings 0 | terminal |
| collaboration documentation tests | PASS | 32 passed, 1 expected Windows symlink skip | terminal |
| manifest invariant and `git diff --check` | PASS | repo 1.7.4/docs 2.9.4, whitespace errors 0 | terminal |

### 미실행 검증과 이유

- Node 24 dropdown availability: 사용자 브라우저 UI에서만 보이며 expanded screenshot이 아직 없다.
- actual Cloud setup: 사용자가 선택·저장한 뒤 실행된다.
- product/API/DB tests: product change가 없고 이 UI 질문의 완료 근거가 아니다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: screenshot에서 secret/시민 원문을 문서에 복사하지 않고 image도 commit하지 않았다.
- Security: Cloud secret 0 정책 유지; runtime mismatch를 dependency 실행 전에 차단한다.
- Accessibility: 제품 UI 변경 0.
- Performance/cost: runtime 실행·dependency 추가·외부 API 호출·비용 0.

## 10. 데이터와 출처 영향

- 공식 데이터/mock: unchanged, 생성·혼합 0.
- schema/lineage: API/DB/data lineage 불변.
- verified date: 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 현재 화면의 Node.js `22`는 틀렸다.
- Python `3.12`는 그대로, Node.js는 `24`로 선택한다.
- Node 24가 dropdown에 없으면 저장하지 말고 펼친 화면을 보낸다.
- 다른 언어는 이 저장소가 사용하지 않으므로 바꿀 필요가 없다.
- exact patch는 setup에서 검증되며, 실패하면 contract를 낮추지 않고 환경을 조정한다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- UI major selector와 repo exact patch/engine constraint를 분리해 판단했다.
- source-of-truth/product contract는 변경하지 않고 handoff wording만 강화했다.

## 13. 인수인계·재현·롤백

### 재현

스크린샷의 Node 22와 `.node-version=24.12.0`, package engine `>=24 <25`를 비교하고 owner checklist
Cloud section을 따른다.

### 롤백

문서 변경은 이 commit을 revert한다. Cloud에서 잘못 선택했으면 environment package version을 Node 24로
수정하고 cache reset 후 setup을 재실행한다.

### 다음 개발자 시작점

사용자가 Node dropdown에서 24를 선택했는지 확인한다. 옵션이 없으면 expanded screenshot을 받아 image의
available runtime options를 기준으로 setup 설치 경로를 설계한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Node 24 dropdown 존재 여부와 selected image의 exact patch는 아직 human/runtime evidence가 없다.
- 다음 한 단계: Node `24` 선택 후 environment setup으로 진행하거나, 옵션이 없으면 dropdown screenshot 공유.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화 — runtime contract 불변
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
