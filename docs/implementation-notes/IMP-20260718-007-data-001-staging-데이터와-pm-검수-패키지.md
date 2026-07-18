# IMP-20260718-007 — DATA-001 staging 데이터와 PM 검수 패키지

- Date/Time (KST): 2026-07-18T16:24:34+09:00
- Task ID: DATA-001
- Type: implementation/data-quality
- Status: In Progress — AI-executable scope; PM review KEEP
- Author/Agent: Codex(Architecture·AI/Data·Backend·Security·Docs)
- Branch: `codex/data-001-staging-review`; worktree `.worktrees/data-001-staging-review`
- Base commit: `e4aa1cd`
- Related plan/ADR/RFP: DATA-001 staging plan / D-033 / A-026 / ADR-0015 / DAR-001·002 / SER-001·003

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 DATA-001 written specification을 승인했다. 앞으로 큰 작업 중간의 반복 승인 질문은 줄이고,
사람이 해야 할 일은 KEEP으로 남긴 채 AI가 수행 가능한 나머지를 계속 진행하라고 지시했다. 데이터는
AI가 공식 출처 범위 안에서 DRAFT로 판단·작성하고 사용자가 나중에 PM 관점으로 검토한다.

### Acceptance Criteria

- 실행계획을 repository와 superpowers 형식에 맞게 작성하고 승인 근거를 기록한다.
- KB 20, office 3, mapping 12의 DRAFT와 내부 schema·validator·PENDING manifest를 만든다.
- source, count, PII, mock, deterministic order, artifact hash, WASTE-03 gate를 fail closed로 검증한다.
- 공식 출처·확인일과 AI 초안을 분리하고 PM 승인으로 오인할 표현을 쓰지 않는다.
- PM review·official release·seed/import·ACTIVE·readiness는 이 요청에서 수행하지 않는다.
- 관련 tests/root gate/secret/package/diff를 실행하고 실제 결과를 기록한다.
- source-of-truth/TASKS/version/data lineage/INDEX를 동기화하고 독립 review 뒤 커밋한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자(PM)가 spec과 연속 진행 방식을 승인; Codex root가 계획·통합; 독립 agent가 4개 source domain을 조사; AI/Data·Backend가 DRAFT 작성; PM 최종 검수는 KEEP |
| When — 언제 | 2026-07-18 KST 시작, 기존 DATA-001 목표 2026-07-20 유지 |
| Where — 어디서 | `data/staging`, `data/schemas`, `data/processed`, `scripts`, `docs`; runtime/DB/remote 제외 |
| What — 무엇을 | dependency-free validator, 20/3/12 DRAFT, hash-bound PENDING manifest, PM packet과 lineage |
| Why — 왜 | 승인 전 content와 시민용 official/ACTIVE를 분리하면서 사용자가 실제 검수할 exact content를 만들기 위해 |
| How — 어떻게 | approved spec→source audit→TDD validator→DRAFT authoring→hash/validation→independent review→PM KEEP handoff |
| How much — 어느 정도 | content record 35, content artifact 3+manifest 1, initial projection 19 KB/3 office/10 mapping, 외부 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: DATA-001 discovery/spec/ADR, source registry 20행, DB read boundary, data policies.
- 기존 동작: official KB/office/mapping/release/seed 0, `/ready=503`, source registry만 존재.
- 발견한 충돌/부채: 정부24 URL 이전, TAX-02 source 범위 과대 가능성, mapping 2건의 근거 부족,
  staging schema/validator/manifest/PM packet 부재.
- Git 상태: `main@e4aa1cd`, 시작 시 clean, remote 0.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-DATA-002/A-026 | Resolved | staging/approval artifact | A/D-033/ADR-0015; spec 승인 | path/state/hash |
| DATA-SRC-001 | C/Resolved by audit | 정부24 9개 canonical URL | MOVE/CERT는 verified plus URL 사용 | source registry/DRAFT |
| DATA-SRC-002 | C/Defaulted | TAX-02 source 범위 | 로그인 후 개인 고지 확인 경로로 축소 | 답변 안전성 |
| DATA-MAP-001 | B/KEEP for PM | 아름동×TAX, 도담동×WASTE 근거 약함 | staging 12 유지, PM packet REJECT 권고, initial 10 | office routing |
| DATA-APPROVAL-001 | Human KEEP | record별 승인/comment | AI는 PENDING까지만, PM이 직접 결정 | official release blocker |
| A-021 | B/unchanged | public DB function hardening | public release 계속 차단 | deployment |

## 5. 설계 결정과 대안

### 선택

- internal schema는 public `contracts/`가 아닌 `data/schemas/data-001/v1/`에 둔다.
- Python 3.12 standard library로 필요한 JSON Schema subset과 business validation을 구현한다.
- PENDING manifest는 세 content artifact만 hash하고 manifest 자기참조 hash는 만들지 않는다.
- 20/3/12를 모두 staging하되 review packet은 19/3/10 initial projection, WASTE-03 WITHHOLD,
  weak mapping 2 REJECT를 명시한다.

### 이유

공개 API/공통 계약과 repository authoring contract를 분리하고 새 dependency 없이 재현 가능하게 한다.
사람 검수 전에는 승인 결정을 만들지 않으면서도 exact bytes와 source scope를 검토할 수 있다.

### 고려했지만 선택하지 않은 대안

- `contracts/kb-record.schema.json` 수정: public cross-app contract 영향이 있어 제외.
- jsonschema production/dev dependency 추가: 현재 필요한 subset에 비해 비용과 승인 범위가 커 제외.
- direct SQL seed/official release: PM approval 경계를 우회해 제외.
- weak mapping 12개 전부 승인 권고: source를 확대 해석하게 되어 제외.

## 6. 구현 상세

| 파일/영역 | 현재 계획 | 이유 |
|---|---|---|
| DATA-001 plan/spec/decision/ambiguity/TASKS | 승인·실행·KEEP 경계 동기화 | governance |
| `data/schemas/data-001/v1/` | internal JSON schema 4개 | field/type/state 제한 |
| `scripts/data_staging_validation.py` | pure validation/hash/report helpers | testability |
| `scripts/validate_data_staging.py` | prepare/validate CLI | reproducible review gate |
| `scripts/tests/test_data_staging_validation.py` | RED/GREEN schema/business/privacy tests | regression |
| `data/staging/data-001/0.1.0-draft.1/` | 20/3/12+PENDING manifest | canonical DRAFT |
| `data/processed/...` | validation report/PM packet | human review |
| source registry/lineage/docs/versions | URL·status·evidence sync | traceability |

### 데이터 흐름/상태 변화

`source audit → DRAFT content → validation/hash → PENDING_PM_REVIEW → PM KEEP`까지만 수행한다.
official release/DB/ACTIVE row는 0을 유지한다.

### 오류·빈 상태·롤백

validator는 stable code만 출력하고 payload value를 숨긴다. 실패하면 manifest approval 전환과 후속
promotion은 없다. 승인 전 변경은 branch commit revert로 제거할 수 있다.

## 7. 버전 전후

### 생성 시 매니페스트

- application 0.1.0, web 0.1.0, api 2.0.1-draft, shared 0.2.1
- database 0.3.0-local, official data 0.0.0-not-populated, mock 0.0.0-not-populated
- prompt 0.0.2-deepseek-v4-flash-selected, tests 0.5.0-db-baseline, docs 2.4.2

| 축 | Before | Planned After | 변경 이유 |
|---|---|---|---|
| Application/Web/API/Shared/DB | current | 동일 | runtime/public/DB 변경 없음 |
| Official data | 0.0.0-not-populated | 동일 | staging은 official release 아님 |
| Mock/Prompt | current | 동일 | mock/LLM 없음 |
| Test suite | 0.5.0-db-baseline | 0.6.0-data-staging | data gate 추가 |
| Docs | 2.4.2 | 2.5.0 | plan/lineage/handoff |

## 8. 명령과 테스트 증거

| 명령/검증 | 현재 결과 | 증거 |
|---|---|---|
| authority/spec/contract/source reads | PASS | terminal evidence |
| 4-domain official source audit | PASS, new A/Blocker 0 | ignored `.superpowers/sdd/data-001-*-audit.md` |
| focused root baseline | PASS, 85 tests + 1 expected symlink skip | terminal evidence |
| patched runtime baseline | PASS, 24 tests | pinned local runtime hash evidence |
| `scripts/verify.ps1` clean baseline | PASS, all stable steps | terminal evidence |
| exact implementation tests/root gate | 실행 전 | Task 1~4에서 실제 결과로 교체 |

### 미실행 검증과 이유

구현 시작 note이므로 validator tests와 final root gate는 아직 실행 전이다. Task별 RED/GREEN과 최종
full verification을 마친 뒤 이 표를 실제 count/시간/exit code로 갱신한다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문·PII 수집 0; DRAFT 예시는 일반화; public office contact만 office field에서 허용.
- Security: secret 0; payload-less errors; content hash와 self-approval gate.
- Accessibility: UI 변화 없음; PM packet은 텍스트/표 기반.
- Performance/cost: local 35-record validation, LLM/API cost 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: 승인/ACTIVE/release/seed 0을 유지한다. source registry는 authoring index로 갱신 예정.
- mock/AI 생성: KB wording/question examples는 AI DRAFT이며 PM 승인 전 시민 근거가 아니다.
- schema/lineage: internal schema v1과 draft `0.1.0-draft.1`을 새로 만든다.
- verified date: 2026-07-18 source audit; PM 승인 직전 변동 사실 재확인 필요.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- PM이 35개 record와 source를 전수 검수하고 record별 decision/comment를 직접 입력해야 한다.
- WASTE-03은 source가 맞아도 REG-001 전 initial release에서 보류한다.
- 아름동×지방세, 도담동×대형폐기물은 현재 REJECT 권고다.
- TAX legacy link와 요금·요일·환불·기관 연락처/시간은 승인 직전 재확인이 필요하다.
- DATA-SEED/DB/readiness는 별도 승인·계획 대상이다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- schema helper, stable issue ordering, temporary fixture factory, atomic writer, CLI parser 구성.
- format/명명/중복 제거와 비공개 test helper 분리.

## 13. 인수인계·재현·롤백

### 재현

계획 파일의 Task 0~4를 순서대로 실행하고 각 RED/GREEN/commit/review evidence를 이 note에 기록한다.

### 롤백

PM 승인 전에는 execution branch commits를 revert한다. official release/DB row가 없어 data migration
rollback은 없다. reviewed content는 덮어쓰지 않고 새 draft version으로 교정한다.

### 다음 개발자 시작점

`.superpowers/sdd/progress.md`, plan checkboxes, Git log를 확인하고 첫 미완료 task부터 재개한다.

## 14. 남은 위험·미해결 질문·다음 단계

- 사람 PM 검수는 KEEP이다.
- 변동 source와 weak mapping은 review risk다.
- implementation/review/final verification이 남았다.
- A-021 public release blocker는 이 작업과 별개로 남는다.

## 15. 자체 리뷰

- [ ] 요청 충족
- [ ] 테스트/검증
- [x] source-of-truth/계약/버전 계획 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
