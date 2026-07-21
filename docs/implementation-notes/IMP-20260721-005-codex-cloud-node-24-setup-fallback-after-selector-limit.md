# IMP-20260721-005 — Codex Cloud Node 24 setup fallback after selector limit

- Date/Time (KST): 2026-07-21T07:21:55+09:00
- Task ID: COLLAB-CLOUD-RUNTIME-SETUP
- Type: documentation-environment-security
- Status: Done — user Cloud setup execution pending
- Author/Agent: Codex primary agent
- Branch: `codex/COLLAB-001-post-merge-evidence`
- Base commit: `4b473e2`
- Related plan/ADR/RFP: COLLAB-001 plan, ADR-0019, D-010, D-057, IMP-20260721-004

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 펼친 Codex Cloud **사전 설치된 패키지** 화면을 공유했고, Node 선택지가 `22 / 20 / 18`만
표시되는 상황에서 어떻게 진행할지 물었다.

### Acceptance Criteria

- 실제 dropdown 선택지와 repository runtime pin을 증거로 비교한다.
- UI에서 지금 선택할 값과 setup에서 최종 적용할 exact 값을 구분한다.
- 공식 `universal` image가 제공하는 버전 전환 도구에 맞는 붙여넣기용 setup을 제공한다.
- runtime 계약을 Node 22로 낮추거나 제품/API/DB/data를 변경하지 않는다.
- active owner checklist, changelog, version manifest, note/INDEX를 동기화한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 Cloud UI를 실행하고 Codex가 screenshot·repo pin·OpenAI official image를 검증 |
| When — 언제 | 2026-07-21 KST, 첫 Cloud environment 생성 중 |
| Where — 어디서 | Codex Cloud `universal` package selector와 custom setup script |
| What — 무엇을 | Node 24 미노출을 Node 22 bootstrap 후 nvm exact 24.12.0 전환으로 해소 |
| Why — 왜 | 저장소의 Node `>=24 <25` 계약을 지키면서 현재 UI 제한을 통과하기 위해 |
| How — 어떻게 | original screenshot 확인, Codex manual과 official Dockerfile/setup source 대조, fail-fast setup 작성 |
| How much — 어느 정도 | handoff 1개·changelog/manifest·note/INDEX; 제품 코드·dependency·DB/data 변경 0 |

## 3. 시작 전 상태

- 관련 파일: `.node-version`, `.python-version`, `package.json`, owner Cloud checklist, manifest, note/INDEX.
- 기존 동작: repository는 Node `24.12.0`, Python `3.12.13`, pnpm `11.13.0`, uv `0.11.28`을 고정하고
  Node engine `>=24.0.0 <25.0.0`을 요구한다.
- 발견한 충돌/부채: prior guidance는 UI에서 Node 24를 고르도록 했지만 실제 dropdown에는 `22 / 20 / 18`만
  있다. 공식 README의 exposed selector 표와도 일치하며, 현재 official Dockerfile은 별도로 Node 24를
  nvm에 설치한다.
- Git 상태: local documentation branch가 `origin/main`보다 2 commits 앞선 상태에서 시작했고 remote write는
  수행하지 않았다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| CLOUD-RT-001 | Resolved UI evidence | Node 24가 dropdown에 있는가 | 없음: `22 / 20 / 18`만 확인 | bootstrap selector |
| CLOUD-RT-002 | Runtime | base image에 exact 24.12.0이 이미 있는가 | nvm `install`을 idempotent하게 실행해 있으면 재사용, 없으면 setup internet으로 설치 | setup time |
| CLOUD-RT-003 | Runtime | Python UI 3.12의 patch가 exact 3.12.13인가 | pyenv `install -s`와 `global`로 exact 보장 | setup time |
| CLOUD-RT-004 | Human execution | 실제 Cloud setup 결과 | 사용자가 저장·실행 후 non-secret output 확인 | rehearsal gate |

## 5. 설계 결정과 대안

### 선택

UI에서는 Python `3.12`, Node `22`를 선택한다. Node 22는 bootstrap에만 쓰고 custom setup 첫 단계에서
official image의 nvm으로 Node `24.12.0`을 설치하고 default alias/current shell을 모두 전환한다. Python도
pyenv로 `3.12.13`을 persistent global로 고정한 뒤 pnpm/uv frozen install을 수행한다.

### 이유

OpenAI official Dockerfile은 nvm으로 Node 18/20/22/24를 설치하고 `/etc/profile`에서 nvm을 불러온다.
official environment bootstrap도 Node 전환에 `nvm alias default`와 `nvm use`를 사용한다. custom setup은
인터넷을 사용할 수 있고, persistent alias/global은 setup과 agent가 별도 shell이라는 경계를 넘는다.

### 고려했지만 선택하지 않은 대안

- Node engine을 22로 낮춤: 승인된 repository/public development contract를 깨므로 제외.
- Node 24가 UI에 나타날 때까지 대기: official image에 nvm 경로가 있어 불필요하므로 제외.
- setup shell에서 `export PATH=...`만 수행: agent phase에 export가 지속되지 않으므로 제외.
- `mise`로 Node 설치: official image의 Node 관리자는 nvm이므로 제외.
- 새 repository production dependency 추가: runtime manager 문제이며 package 변경이 필요 없어 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| owner Cloud checklist | actual UI Node 22 bootstrap과 nvm/pyenv exact 전환 setup | 사용자가 화면 그대로 재현 가능 |
| CHANGELOG/manifest | correction과 repo/docs version sync | guidance 계보 유지 |
| this note/INDEX | 증거·대안·보안·rollback 기록 | 요청별 의무 기록 |

### 데이터 흐름/상태 변화

```text
UI: Python 3.12 + Node 22
  → built-in environment bootstrap
  → custom setup: nvm Node 24.12.0 default/current
  → custom setup: pyenv Python 3.12.13 global
  → corepack pnpm 11.13.0 + uv 0.11.28 frozen installs
  → exact version tests pass
  → docs-only Cloud Draft PR rehearsal
```

### 오류·빈 상태·롤백

- `nvm install`/`pyenv install` 또는 exact test 실패 시 dependency나 agent 작업으로 진행하지 않는다.
- version contract를 낮추지 않고 secret이 없는 setup stderr/stdout만 공유한다.
- 잘못 저장했으면 setup 수정 후 environment cache를 reset한다.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.5
- repo_guidance: 1.7.4
- application: 0.3.0-pii-core
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 1.0.0-collaboration
- documentation: 2.9.4

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Repo guidance | 1.7.4 | 1.7.5 | actual Cloud selector fallback |
| Docs | 2.9.4 | 2.9.5 | official runtime source/runbook/note sync |
| Application/Web/API/contracts/DB/data/prompt/tests | unchanged | unchanged | 제품·공개 계약·데이터·테스트 변경 없음 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| original-resolution screenshot inspection | PASS | Node options 22/20/18; Python 3.12 | user temp image; not committed |
| repo runtime inspection | PASS | Node 24.12.0, Python 3.12.13, pnpm 11.13.0, engine >=24 <25 | runtime manifests |
| current Codex manual Cloud environment section | PASS | setup internet, separate shell, cache semantics confirmed | official manual cache |
| official `codex-universal` Dockerfile/source inspection | PASS | nvm installs Node 24; official switch uses nvm alias/use | official OpenAI GitHub |
| `python -B scripts/check_repository_docs.py --repository-root .` | PASS | active docs/JSON/link rules | terminal |
| `powershell.exe ... scripts/check_secret_patterns.ps1 -RepositoryRoot .` | PASS | findings 0 | terminal |
| scoped collaboration/docs unittests | PASS | 57 passed, 1 expected Windows symlink skip | terminal |
| `git diff --check` and manifest parse | PASS | whitespace errors 0; repo 1.7.5/docs 2.9.5 | terminal |

### 미실행 검증과 이유

- actual Cloud runtime/install: 사용자의 private Cloud environment에서만 실행 가능하며 다음 인간 단계다.
- product/API/DB tests: 제품 코드가 바뀌지 않았고 scoped repository docs/collaboration gates로 대체한다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: screenshot 파일·계정 정보·secret·시민 원문을 commit하지 않았다.
- Security: Cloud secret 0 정책과 agent internet Off를 유지한다. setup은 public runtime/package fetch만 한다.
- Accessibility: 제품 UI 변경 0.
- Performance/cost: 첫 cache에서 exact Node/Python이 없으면 설치 시간이 증가한다. external API 호출과 유료
  infrastructure 비용은 0이다.

## 10. 데이터와 출처 영향

- 공식 데이터/mock: unchanged; 생성·승인·혼합 0.
- schema/lineage: API/DB/data lineage 불변.
- official technical sources: OpenAI Codex manual, `openai/codex-universal` Dockerfile와 setup script.
- verified date: 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 이 화면에서는 Python `3.12`, Node `22`를 선택한다. Node 22는 최종 project runtime이 아니다.
- setup script가 exact Node `24.12.0`으로 전환하고 검증한 뒤에만 환경이 사용 가능하다.
- 다른 언어 dropdown과 환경변수/secret은 건드리지 않는다.
- setup 실패 화면에는 key가 없어야 하며, 오류 출력만 공유한다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- nvm default alias와 pyenv global state로 setup/agent shell 경계를 넘기고 exact test로 drift를 차단한다.
- repository runtime/dependency/public contract는 변경하지 않고 human runbook만 correction했다.

## 13. 인수인계·재현·롤백

### 재현

Cloud selector에서 Python 3.12/Node 22를 선택하고 owner checklist의 setup을 붙여넣는다. setup 종료 시
`v24.12.0`, `11.13.0`, `Python 3.12.13`, `uv 0.11.28` 검사와 frozen sync가 모두 통과해야 한다.

### 롤백

documentation correction은 해당 commit을 revert한다. Cloud environment에서는 setup을 이전 값으로 돌리고 cache
reset으로 다시 만든다. 단, Node 22로 제품 개발하는 상태는 유효한 rollback target이 아니다.

### 다음 개발자 시작점

사용자의 Cloud setup 결과를 받아 exact four-version output과 frozen install 성공을 확인한 뒤 docs-only Draft PR
rehearsal을 진행한다.

## 14. 남은 위험·미해결 질문·다음 단계

- actual deployed Cloud image가 official reference image와 달라 nvm exact install이 실패할 가능성은 setup evidence 전까지
  남는다. 실패 시 non-secret output을 보고 image/runtime 경로만 조정한다.
- 다음 한 단계: 사용자가 Python 3.12/Node 22를 선택하고 아래 setup script를 저장·실행한다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화 — product/runtime contract 불변
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
