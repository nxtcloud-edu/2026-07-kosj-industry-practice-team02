# IMP-20260715-003 — Root runtime과 workspace 계약

- Date/Time (KST): 2026-07-15T00:59:32+09:00 ~ 2026-07-15T01:50:02+09:00
- Task ID: DEV-001A
- Type: implementation
- Status: Done
- Author/Agent: coding agents (`dev001a_*`), Codex `/root`(tool install·진단·검증·문서 마감)
- Branch: `codex/DEV-001-repo-scaffold`
- Base commit: `04cf605`
- Related plan/ADR/RFP: `PLAN-20260715-002` Task 1, ADR-0002, COR-001~002

## 1. 사용자 요청과 완료 기준

### 요청

- 승인된 Phase 1을 계속 진행하고, 코딩은 에이전트에게 위임하되 중요한 결정·명령·코드 검토는 `/root`가 맡는다.

### Acceptance Criteria

- Node 24.12.0, pnpm 11.13.0, Python 3.12.13, uv 0.11.28을 exact pin한다.
- dependency-free root package와 `apps/*`, `packages/*` workspace를 만든다.
- runtime/workspace/credential/ignore 계약을 표준 라이브러리 테스트로 RED→GREEN 증명한다.
- 제품 앱·DB·계약·데이터·외부 LLM은 변경하지 않는다.
- 구현 노트, INDEX, TASKS, version, changelog, README를 동기화한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 계획을 승인했고, coding agent가 test/config를 작성했으며 `/root`가 도구 설치·호환성·Git·최종 검증을 통제했다. |
| When — 언제 | 2026-07-15 KST, Phase 1 Task 1 |
| Where — 어디서 | 격리 worktree의 root manifests/runtime pins, standard-library test, README/TASKS/version/docs |
| What — 무엇을 | 독립 local monorepo의 실행 전 root 계약과 exact toolchain을 만들었다. |
| Why — 왜 | 앱 코드를 추가하기 전에 clean/reproducible install 경계와 runtime drift를 자동 차단하기 위해서다. |
| How — 어떻게 | official registry metadata, user-approved tool install, sandbox 경로 진단, RED→GREEN unittest, ignored workspace cache로 구현했다. |
| How much — 어느 정도 | root config 6개 신규, test 2개 신규, 메타/문서 6개 변경; test 6개; 제품 route/DB/data/LLM 0건; 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: ADR-0002, root `.gitignore`, README/TASKS/version manifest, 상세 Phase 1 plan.
- 기존 동작: Node 24.12.0/Corepack만 설치되어 있고 root/package/app manifest, pnpm, uv, Python 3.12가 없었다.
- 발견한 충돌/부채:
  - 처음 제안한 TS 7은 `openapi-typescript`의 TS 5 peer와 충돌해 상세 plan에서 5.9.3으로 이미 교정됐다.
  - sandbox와 실제 사용자 계정의 Python user-site/cache 권한이 달라 설치된 uv module을 sandbox가 바로 실행하지 못했다.
- Git 상태: branch `codex/DEV-001-repo-scaffold`, base `04cf605`, remote 0, task 시작 시 clean.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| PY312-PATCH | Resolved | managed Python 3.12 patch | uv resolver가 설치한 3.12.13 exact pin | Python lock/runtime |
| UV-SANDBOX | Internal | user-site uv/cache 실행 거부 | normal user는 installed uv, sandbox 검증은 ignored `.tools/uv` 사본+workspace cache | local verification only |
| PNPM-CACHE | Internal | sandbox/user cache 분리 | ignored `.tools/corepack`을 `COREPACK_HOME`으로 사용 | package tool reproducibility |
| APP-DEPS | Deferred per plan | 실제 Web/API dependency | DEV-001B/C에서 exact manifest/lock 생성 | 앱 build/test |

## 5. 설계 결정과 대안

### 선택

- root `package.json`은 private/dependency-free이며 package manager와 Node engine만 고정한다.
- workspace globs는 active `apps/*`, `packages/*`로 제한하고 legacy/data/docs를 package workspace로 취급하지 않는다.
- `.npmrc`는 `engine-strict=true`, `save-exact=true`만 두고 registry credential을 금지한다.
- `.node-version`과 `.python-version`은 실제 설치·검증한 exact patch다.
- `uv.toml`의 `required-version`으로 uv 0.11.28이 아닌 실행을 도구 수준에서 거부한다.
- transient tool cache/binary는 `.tools/`로 ignore하며 commit하지 않는다.

### 이유

- root dependency가 앱 dependency 경계를 흐리지 않고, exact manager/runtime drift를 가장 일찍 실패시킨다.
- user credential·cache·binary가 repository history에 들어가지 않는다.

### 고려했지만 선택하지 않은 대안

- caret/tilde/latest range: 재현성이 없어 제외.
- npm/yarn 또는 Python 3.11/3.14: ADR-0002 인간 결정과 달라 제외.
- uv/pnpm binary commit: OS 의존 binary와 큰 cache를 저장소에 넣으므로 제외.
- 실제 앱 dependency를 root에 선추가: 앱별 리뷰·lock 책임을 흐려 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `package.json` | private root, packageManager/Node/pnpm exact engine, dependency 0 | root tool contract |
| `pnpm-workspace.yaml` | `apps/*`, `packages/*` | active monorepo boundary |
| `.node-version`, `.python-version` | 24.12.0, 3.12.13 | exact runtime |
| `.npmrc` | exact saves, strict engines, credential 0 | deterministic/safe install |
| `uv.toml` | `required-version = "==0.11.28"` | exact uv 실행을 machine-enforce |
| `.gitignore` | `.tools/` | tool binary/cache commit 차단 |
| `scripts/tests/` | 6개 root contract unittest | drift/version/credential regression |
| README/TASKS/manifest/changelog | runtime·상태·버전 기록 | 인수인계/추적 |

### 데이터 흐름/상태 변화

- 시민/운영자/API/DB 데이터 흐름은 없다. 개발 도구 선택과 파일 검증 흐름만 추가됐다.

### 오류·빈 상태·롤백

- required root 파일이 없거나 version/workspace/ignore/credential 규칙이 다르면 test가 non-zero로 실패한다.
- `.tools/`는 없어도 repository contract는 유효하고, 필요 시 도구가 다시 생성한다.
- task commit을 revert하면 앱/DB/data 영향 없이 이전 문서-only 상태로 돌아간다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.0.0-not-scaffolded | 동일 | 제품 앱 미구현 |
| Web | 0.0.0-not-scaffolded | 동일 | Web manifest/source 미구현 |
| API | 2.0.0-draft | 동일 | 공개 계약/API source 미변경 |
| DB schema | 0.2.0-draft | 동일 | migration 0 |
| Official data | 0.0.0-not-populated | 동일 | 데이터 0 |
| Mock data | 0.0.0-not-populated | 동일 | 데이터 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 호출/프롬프트 0 |
| Test suite | 0.3.0-spec | 0.3.1-scaffold-contract | 실행 가능한 root contract test 6개 |
| Repo guidance | 1.2.0 | 1.3.0 | runtime/workspace 실행 계약 추가 |
| Docs | 2.3.2 | 2.3.3 | README/note/status 변경 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `python -B -m unittest scripts.tests.test_repository_scaffold -v` before root files | expected FAIL, exit 1 | 5 failures / 0.010s; runner wall 0.842s | interrupted implementer report recovered by follow-up |
| isolated missing-root RED reproduction | expected FAIL, exit 1 | 5 failures / 0.014s | `.superpowers/sdd/task-1-red-empty-root`, terminal |
| `python -B -m unittest scripts.tests.test_repository_scaffold -v` initial implementation | PASS | 5/5, 0.008s | `scripts/tests/test_repository_scaffold.py`, terminal |
| focused uv exact-pin test before `uv.toml` | expected FAIL, exit 1 | 1 failure: missing `uv.toml` | coding-agent terminal report |
| focused uv exact-pin test after `uv.toml` | PASS | 1/1 | coding-agent terminal report |
| full root contract after uv pin | PASS | 6/6, 0.012s | `scripts/tests/test_repository_scaffold.py`, controller terminal |
| `py -3.11 -m pip install --user uv==0.11.28` | PASS | uv 0.11.28 installed | user-site, terminal |
| `py -3.11 -m uv python install 3.12` | PASS | CPython 3.12.13 | uv managed runtime, terminal |
| workspace-local uv/cache verification | PASS | uv 0.11.28, Python 3.12.13 | ignored `.tools/`, `.superpowers/uv-cache` |
| `corepack prepare pnpm@11.13.0 --activate` with workspace `COREPACK_HOME` | PASS | pnpm 11.13.0 | ignored `.tools/corepack`, terminal |
| `python -B scripts/validate_codex_package.py` | PASS | 12 required files, manifest valid | terminal |
| `python -m json.tool package.json`, manifest | PASS | 2/2 JSON documents | terminal |
| `git diff --check` | PASS | violations 0 | terminal |
| scoped secret scan | `DEV001A_SECRET_SCAN_PASS` | findings 0 | terminal |
| changed-path allowlist scan | `DEV001A_SCOPE_PASS` | 16 tracked/untracked paths, out-of-scope 0 | terminal |
| fresh independent review after uv delta | APPROVE | 6/6 in 0.007s; P0/P1/P2 0 | `dev001a_final_reviewer` report |

### 미실행 검증과 이유

- pnpm clean install: 아직 app/package manifest와 lock이 없으므로 DEV-001C에서 실행한다.
- uv lock/sync, ruff/mypy/pytest: API pyproject가 없는 DEV-001A 범위 밖이며 DEV-001B에서 실행한다.
- health/build/contract/DB/DeepSeek: 후속 task이며 이 작업의 동작 범위를 넘는다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문·PII·context token 생성/저장/전송 0건.
- Security: `.npmrc` credential marker 0, root dependency 0, tool binary/cache Git ignore, scoped secret scan finding 0.
- Accessibility: UI 변경 0.
- Performance/cost: paid API/외부 인프라 0원. tool download만 수행했으며 runtime cache는 Git 밖이다.

## 10. 데이터와 출처 영향

- 공식 데이터: 변경/승인/ACTIVE 0건.
- mock/AI 생성: 0건.
- schema/lineage: API/DB/data schema 변경 0.
- verified date: package/tool metadata 2026-07-15; 공식 행정 데이터 해당 없음.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 승인된 도구가 exact pin됐다: Node 24.12.0, pnpm 11.13.0, Python 3.12.13, uv 0.11.28. uv는 문서 표기뿐 아니라 `uv.toml`로 실행 시점에 강제된다.
- 실제 앱 dependency와 lock은 아직 없고 제품 앱은 계속 not-scaffolded다.
- 공개 배포, 실제 시민 DeepSeek, remote/CI, DB migration/삭제는 여전히 별도 승인 또는 후속 승인 작업이다.
- 사용자 계정에는 uv 0.11.28과 managed Python 3.12.13이 설치됐다. sandbox용 ignored 사본/cache는 commit되지 않는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- Python unittest parser는 YAML library 없이 workspace list의 단순 exact line만 확인한다.
- sandbox identity 차이는 `.tools/`와 `.superpowers/` ignore 경계 안에서만 우회하고 public/product runtime에는 반영하지 않는다.

## 13. 인수인계·재현·롤백

### 재현

1. Node 24.12.0과 Corepack을 준비한다.
2. uv 0.11.28과 Python 3.12.13을 준비한다.
3. `python -B -m unittest scripts.tests.test_repository_scaffold -v`를 실행해 6개 통과를 확인한다.
4. 다음 DEV-001B/C에서 exact app manifest와 lock을 만든다.

### 롤백

- task commit을 `git revert`한다. user-level 도구를 제거하려면 실제 사용자 환경에서 uv package와 managed Python 3.12.13만 선택 제거하며 다른 Python은 건드리지 않는다.
- ignored `.tools/`/`.superpowers` cache는 언제든 재생성 가능하므로 소스 rollback에 필요하지 않다.

### 다음 개발자 시작점

- independent review findings를 반영한 뒤 DEV-001B(API health) 또는 DEV-001C(Web shell)를 시작한다. shared manifest 충돌을 피하려고 한 번에 하나만 쓴다.

## 14. 남은 위험·미해결 질문·다음 단계

- Windows sandbox와 실제 사용자 cache ACL 차이는 단일 local PC 특성으로 문서화됐고 final verify wrapper에서 처리해야 한다.
- root contract는 dependency install 성공을 증명하지 않는다. 앱 lock 생성 뒤 frozen clean install이 필수다.
- 최초 independent re-review 뒤 발견된 uv machine-enforcement gap은 TDD로 보강했다. complete Task 1 delta의 fresh independent review는 P0/P1/P2 0건으로 승인됐다.

## 15. 자체 리뷰

- [x] 요청/Task 1 범위 충족
- [x] RED→GREEN 증거
- [x] source-of-truth/ADR/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
- [x] uv 보강 이후 fresh independent review와 최종 검증
