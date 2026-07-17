# IMP-20260717-011 — Q-SEC-006 명세 승인과 patched Supabase CLI 실행계획

- Date/Time (KST): 2026-07-17T12:33:49+09:00
- Task ID: DB-001-T10-QSEC006-PLAN
- Type: decision/planning/security
- Status: Decision-only Done — plan approved 2026-07-17, implementation started
- Follow-up: 사용자가 2026-07-17 `계획 승인, 구현 시작`으로 실행계획을 승인했다.
- Historical-state note: 아래의 review pending/requested 문구는 이 계획을 처음 작성한 시점의
  상태를 설명한다. 현재 권위는 위 Follow-up이며 구현이 승인됐다.
- Author/Agent: 사용자(명세 승인), Codex(계획·검증·기록)
- Branch: codex/db-001-layered-enforcement
- Base commit: c62ff19
- Related plan/ADR/RFP: Q-SEC-006, D-031, A-024, ADR-0013, DB-001 Task 10,
  `docs/superpowers/plans/2026-07-17-q-sec-006-patched-supabase-cli.md`

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 `명세 승인`으로 Q-SEC-006 patched CLI 서면 설계를 승인했다. 승인된 명세를 실제
구현 가능한 TDD 실행계획으로 분해하되 계획 승인 전 구현을 시작하지 않는다.

### Acceptance Criteria

- 명세 상태를 Approved로 바꾸고 active decision/task/plan/source-of-truth에 반영한다.
- exact 파일·인터페이스·RED/GREEN·명령·예상 결과·commit·rollback이 있는 계획을 작성한다.
- source/runtime manifest 분리와 build 전 미확정 binary hash의 안전한 확정 절차를 포함한다.
- Go 설치, patch file 생성, source build, Docker/DB 실행, 제품 코드 변경은 하지 않는다.
- 계획을 자체 검토하고 구현 노트/INDEX를 갱신한 뒤 계획 승인을 요청한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 명세를 승인했고 Codex가 실행계획과 문서 lineage를 작성했다. |
| When — 언제 | 2026-07-17 KST, D-031 설계 commit `c62ff19` 직후 |
| Where — 어디서 | DB-001 worktree의 spec/plan/decision/task/version/implementation-note 문서 |
| What — 무엇을 | 5개 독립 review unit의 source lock→bootstrap→runtime pin→runner→full gate 계획 |
| Why — 왜 | exact loopback 보안을 유지하면서 새로운 local toolchain 공급망을 재현 가능하게 실행하기 위해 |
| How — 어떻게 | writing-plans 규칙, TDD, 두 독립 build hash, fail-closed runner, 단계별 commit과 rollback |
| How much — 어느 정도 | 계획·메타 문서만 변경; product/API/DB/data/dependency/container mutation 0, 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: approved D-031 spec/ADR, parent DB plan, stock/patched tooling 대상, runner/tests,
  active status/report/handoff/version 문서.
- 기존 동작: stock CLI HostIP 생략은 `127.0.0.1`+`::`; explicit control만 단일 loopback.
- 발견한 충돌/부채: 최초 binary hash는 build 전 알 수 없으므로 source lock과 runtime lock을
  분리해야 한다. stock CLI, Go 미설치, container 0, DB schema version 미승격 상태다.
- Git 상태: 시작 commit `c62ff19`, branch `codex/db-001-layered-enforcement`, clean.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-SEC-006 | 인간 결정 | patched CLI 방식 | A/D-031, 명세 승인 완료 | 계획 승인 뒤 구현 가능 |
| binary SHA | runtime-derived | build 전 값 미확정 | 두 독립 build 일치값만 별도 manifest에 literal pin | 임의/빈 hash 방지 |
| A-021/Q-SEC-003 | B/High | public function hardening | 기본 B 유지 | local 완료 뒤에도 public 차단 |
| execution worker | 내부 운영 | agent capacity 변동 가능 | 가능하면 fresh worker+두 review, 아니면 inline 분리 review 기록 | 품질 gate 유지 |

## 5. 설계 결정과 대안

### 선택

상류 source/Go/patch/build 입력, bootstrap, runtime artifact, DB runner, actual full gate를 다섯
review unit으로 나눈다. 각 unit은 RED→GREEN, focused/full test, diff review와 개별 commit을 가진다.

### 이유

source provenance와 runtime provenance가 서로 다른 시점에 확정되며, runner를 바꾸기 전에
binary를 독립 검증해야 한다. 실제 DB 실행은 모든 정적/tooling gate 뒤 마지막에만 온다.

### 고려했지만 선택하지 않은 대안

- 단일 대형 commit: provenance/build/runner/runtime 실패를 분리 검토·rollback하기 어려워 제외.
- build 전에 임의 binary hash 기록: 사실과 다른 pin이므로 금지.
- stock CLI 교체 또는 PATH fallback: provenance·rollback 경계를 깨므로 제외.
- `db diff` 동시 패치, Bun wrapper build: 승인 범위 밖이고 dependency 표면을 늘려 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| 새 Q-SEC-006 plan | 5 task, exact files/interfaces/tests/commands/commits/rollback | 실행 가능성 |
| approved spec/parent plan/TASKS | 작성 당시 spec approved, child plan review pending; 이후 승인 완료 | gate 정직성 |
| decision/ambiguity/team/index | D-031 계획 상태 동기화 | source-of-truth 일치 |
| version manifest | docs 2.3.15→2.3.16 | 계획 문서 lineage |
| note/INDEX | 이 요청의 6W1H·검증·인수인계 | 요청별 기록 의무 |

### 데이터 흐름/상태 변화

이 노트 작성 당시 명세 review state만 Approved로 바뀌고 실행계획은 Review requested였다.
후속 승인 뒤에도 runtime, DB, migration, data, readiness는 아직 변하지 않았다.

### 오류·빈 상태·롤백

작성 당시 계획이 승인되지 않으면 이 planning commit만 revert하도록 정했다. 이후 계획은
승인됐지만 구현 gate 실패 시 이미 승인된 D-031/명세를 유지하고 DB runtime Blocked로 복원한다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.1.0 | 0.1.0 | 코드 없음 |
| Web | 0.1.0 | 0.1.0 | UI 없음 |
| API | 2.0.1-draft | 2.0.1-draft | 공개 계약 없음 |
| DB schema | 0.2.0-draft | 0.2.0-draft | DB 실행 없음 |
| Official data | 0.0.0-not-populated | 동일 | 공식 데이터 없음 |
| Mock data | 0.0.0-not-populated | 동일 | mock 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 없음 |
| Test suite | 0.4.2-readiness-contract | 동일 | 테스트는 계획만 작성 |
| Docs | 2.3.15 | 2.3.16 | 승인 상태·실행계획 추가 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| using-superpowers/writing-plans/implementation-note skill read | PASS | 3 skills+Codex reference | local skill files |
| upstream start source line inspection | patch 대상 line/context 재확인 | 2 files | exact temp checkout |
| decoded plan patch recipe SHA-256 | `109c096...33f7d`, 1,824 bytes | `<SP>`/`<TAB>` markers decoded in memory | terminal |
| decoded recipe `git apply --check` through stdin | PASS, two approved files | exact commit checkout `6d4c198...a94` | terminal |
| `python -B scripts/validate_codex_package.py` | PASS | required files 12, version manifest valid | terminal |
| `python -m unittest scripts.tests.test_repository_scaffold scripts.tests.test_security_boundaries` | PASS | 19 tests, 1 environment-dependent skip | terminal |
| `scripts/check_secret_patterns.ps1` | PASS | tracked planning scope, finding 0 | terminal |
| plan required-token/placeholder/code-fence check | PASS | required token 12, fence 66, placeholder 0 | terminal |
| changed Markdown relative-link check | PASS | Markdown 14 files, missing link 0 | terminal |
| `git diff --check` | PASS | whitespace error 0 | terminal |
| Docker read-only state check | PASS | Engine 29.2.1, local-only setting, all/project containers 0/0 | terminal |

### 미실행 검증과 이유

새 tooling unit tests, Go download, patch RED/GREEN, candidate/install, binary hash/version, runner tests,
actual Docker/full DB/root gate는 이 노트 작성 당시 실행계획 승인 전이라 실행하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문/응답/DSN/API key/PII 접근·저장 0.
- Security: exact source/toolchain/network/module/build/runtime/runner gate와 rollback을 계획했다.
- Accessibility: 화면 변화 없음.
- Performance/cost: 향후 local clone/module download/build 시간과 디스크만 사용; 외부 예산 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: 0, 변경 없음.
- mock/AI 생성: 0, 변경 없음.
- schema/lineage: schema/migration 불변; tooling lineage 계획만 추가.
- verified date: upstream/local 근거 2026-07-17 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 이 노트의 다음 인간 gate였던 실행계획 승인은 2026-07-17 충족됐다.
- 당시 승인 전에는 Go 설치·build·DB start/reset을 하지 않았으며, 현재는 승인된 계획 gate를 따른다.
- 승인 뒤에도 actual gate 전에는 DB-001/versions를 승격하지 않는다.
- local 완료는 public/production 승인이 아니며 Q-SEC-003은 여전히 미해결이다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- helper/fixture 명명과 process wrapper는 계획의 공개 인터페이스와 stable output을 지키는 범위에서
  task별 worker가 구현한다.
- 실제 binary hash는 Task 3에서 두 build 일치 후 기록하며 새로운 인간 선택이 아니다.

## 13. 인수인계·재현·롤백

### 재현

계획의 Global Constraints, file map, five tasks, rollback, final checklist를 approved spec의 1~8절과
대조한다. source patch block을 exact upstream checkout에서 `git apply --check`한다.

### 롤백

planning commit을 revert하고 docs version을 2.3.15로 되돌린다. artifact/DB가 없어 cleanup은 없다.

### 다음 개발자 시작점

사용자가 `계획 승인, 구현 시작`으로 승인했으므로 plan Task 1부터 시작한다. fresh worker가
가능하면 task별로 사용하고, 불가능하면 inline TDD와 별도 specification/quality review를 유지한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Go module/network availability는 구현 시 operational failure가 될 수 있으나 policy 변경은 아니다.
- 실제 binary SHA는 build evidence 전까지 존재하지 않는다.
- source tag/commit, patch, module, independent binary hash 중 하나라도 다르면 DB를 시작하지 않는다.
- 다음 단계는 승인된 실행계획의 Task 1 구현이다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 계획 근거·patch applicability 확인; 구현 검증은 승인 뒤로 분리
- [x] source-of-truth/task/decision/version 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
