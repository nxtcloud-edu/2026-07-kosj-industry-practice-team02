# IMP-20260718-006 — Q-DATA-002 A 결정과 DATA-001 staging artifact 명세

- Date/Time (KST): 2026-07-18T15:58:52+09:00
- Task ID: DATA-001-QDATA002-DESIGN
- Type: decision/data-architecture/design
- Status: Decision-only Done — written specification user review pending
- Author/Agent: Codex(Architecture·AI/Data·Backend·Security·Docs)
- Branch: main
- Base commit: 745a700
- Related plan/ADR/RFP: Q-DATA-002 / D-033 / A-026 / ADR-0015 / DATA-001 /
  DAR-001·002 / `docs/discovery/DATA_001_DISCOVERY_REPORT.md`

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 `Q-DATA-002: A`를 명시해 승인 전 공식 데이터 artifact를 별도 staging JSON과
hash-bound PM approval manifest로 관리하는 추천안을 선택했다.

### Acceptance Criteria

- 사용자 답을 D-033/A-026/ADR-0015와 interview evidence에 정확히 기록한다.
- staging·approval·official release·seed 경계를 written specification으로 고정한다.
- 초기 KB 19+WASTE-03 보류→REG-001 뒤 최종 20 ACTIVE의 dependency cycle 해소를
  source-of-truth/RFP/TASKS에 반영한다.
- canonical source registry 이름을 실제 파일명으로 정정한다.
- 공식/mock data, DB, seed, API, 제품 코드와 dependency는 변경하지 않는다.
- 구현 노트·INDEX·version manifest를 동기화하고 검증·커밋한다.
- written spec 사용자 검토 전 구현계획이나 DRAFT authoring을 시작하지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 A안을 결정했고 Codex가 결정·ADR·명세·추적 문서를 작성했다. 이후 AI/Data·Backend가 작성하고 별도 PM이 record별 검수한다. |
| When — 언제 | 2026-07-18 KST. DATA-001 목표일은 기존 2026-07-20 유지. |
| Where — 어디서 | `docs/`, `TASKS.md`, `versions/manifest.json`만 변경. 향후 경로는 `data/staging/data-001/<draft-version>/`. |
| What — 무엇을 | staging JSON 3종+approval manifest, hash-bound PM gate, 후속 immutable release handoff, 19→20 회귀 gate를 설계했다. |
| Why — 왜 | 승인 전 DRAFT가 official/seed와 섞이고 PM이 검토한 exact content가 불명확해지는 위험을 제거하기 위해. |
| How — 어떻게 | Q-DATA-002=A를 D-033/A-026/ADR-0015로 추적하고 source-of-truth·RFP·TASKS·discovery·spec을 동기화했다. |
| How much — 어느 정도 | 향후 staging 목표 KB 20·기관 3·매핑 12; 초기 승인 KB 19·기관 3·매핑 10~12; 현재 공식 record/mock/seed/DB mutation 0, 비용 0원. |

## 3. 시작 전 상태

- 관련 파일: DATA-001 discovery, source registry 20행, KB/approval guides, RFP matrix,
  logical KB contract, DB schema, TASKS, versions manifest.
- 기존 동작: DB-001 local baseline은 완료됐지만 official KB·office·mapping·seed는 0이고
  `/ready=503`이다. source registry만 20행 존재한다.
- 발견한 충돌/부채: staging directory·canonical artifact·approval manifest가 없고,
  `07_KB_출처대장.csv`라는 미존재 이름을 두 문서가 참조했다. DATA-001의 ACTIVE 20 선행조건과
  WASTE-03 회귀 후 승인 사이에 dependency cycle이 있었다.
- Git 상태: 시작 `main@745a700`, clean, remote 0.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-DATA-002 | B/High → Resolved | staging/approval artifact 방식 | A: four JSON artifacts, hash-bound PM approval | data architecture, lineage, seed handoff |
| A-026 | B/High → Resolved | repository data boundary | D-033/ADR-0015로 추적 | source-of-truth/TASKS/spec |
| A-DATA-002 | C/Defaulted in spec | non-personal author/reviewer ID | `AI-DATA-BACKEND` / `PM`; 실제 인증 아님 | manifest·DB text actor mapping |
| A-DATA-003 | C/Defaulted in spec | version/order/format | `0.1.0-draft.1`, UTF-8/LF/2-space, lexical record order | deterministic hash/diff |
| A-021 | B/High, unchanged | public DB function hardening | local/private만 허용 | public release 별도 차단 |

## 5. 설계 결정과 대안

### 선택

- canonical authoring: `data/staging/data-001/<draft-version>/`
- artifact: KB, office, mapping JSON과 별도 approval manifest
- PM approval: artifact SHA-256/count와 record별 decision/comment에 결합
- promotion: DATA-SEED-001에서 승인 record만 immutable official release로 생성
- 회귀: 20 staging, initial 19 approved, WASTE-03 withheld, REG-001 뒤 final 20 ACTIVE

### 이유

구조화 array와 cross-file reference를 schema로 검증할 수 있고, 승인한 content를 hash로
고정하며, DRAFT/approval/release/seed 책임을 서로 다른 단계로 분리할 수 있다.

### 고려했지만 선택하지 않은 대안

- 단일 확장 CSV: 사람이 보기 쉽지만 array·nullable·reference·hash/decision 표현이 취약하다.
- direct SQL seed: 승인 전 DRAFT와 시민 ACTIVE를 결합하고 rollback/lineage를 불명확하게 한다.
- official directory에 DRAFT 저장: 디렉터리 의미와 승인 상태를 혼동시켜 선택하지 않았다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `docs/decisions/DECISION_LOG.md` | D-033 추가 | 사용자 결정 원문 추적 |
| `docs/11_AMBIGUITY_REGISTER.md` | A-026 resolved와 Q-DATA-002 상세 추가 | 미지의 영역 해소 |
| `docs/adr/0015-*.md`, ADR index | 장기 데이터 경계 ADR | 아키텍처 결정 고정 |
| `docs/superpowers/specs/2026-07-18-data-001-*.md` | artifact contract·state·validation·handoff 명세 | written spec review gate |
| TEAM_DECISIONS/PROJECT_PLAN/RFP_MATRIX | initial 19→REG final 20과 hash approval 동기화 | source-of-truth·요구 추적 |
| KB_GUIDE/BID_PROPOSAL/data policy | canonical registry 이름과 staging 경계 정정 | 문서 drift 제거 |
| `TASKS.md` | DATA-001 Review, DATA-SEED initial 19 경계 | dependency cycle 제거 |
| discovery/interview | Q-DATA-002 resolved evidence | 감사 결과 최신화 |
| version/note/index | docs 2.4.2, 요청별 기록 | 완료 조건 |

### 데이터 흐름/상태 변화

이 요청의 실제 data row/status/seed 변화는 0이다. 향후 흐름만
source audit→staging DRAFT→validation/hash→PM review→별도 DATA-SEED promotion으로 고정했다.

### 오류·빈 상태·롤백

stale hash, self approval, PII/mock/source 누락, count/reference drift는 fail closed한다. 문서 설계를
되돌릴 때는 이 commit을 revert한다. official release/DB rollback은 이 요청 범위가 아니다.

## 7. 버전 전후

### 생성 시 매니페스트
- product_spec: 2.2.0
- repo_guidance: 1.5.0
- application: 0.1.0
- web: 0.1.0
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 0.5.0-db-baseline
- documentation: 2.4.1

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.1.0 | 동일 | 제품 코드 없음 |
| Web | 0.1.0 | 동일 | UI 없음 |
| API | 2.0.1-draft | 동일 | public contract 없음 |
| DB schema | 0.3.0-local | 동일 | migration/data mutation 없음 |
| Official data | 0.0.0-not-populated | 동일 | DRAFT/approval/release/seed 0 |
| Mock data | 0.0.0-not-populated | 동일 | mock 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 미호출 |
| Test suite | 0.5.0-db-baseline | 동일 | 테스트 코드 없음 |
| Docs | 2.4.1 | 2.4.2 | 결정·ADR·spec·추적 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `git status --short --branch`, `git log -4` | PASS | clean `main@745a700` 시작 | terminal evidence |
| authority/decision/spec file read + `rg` | PASS | resolved 질문 재질문 0, old registry reference 2건 발견 | terminal evidence |
| `git diff --check` | PASS | whitespace error 0 | terminal evidence |
| `python -m json.tool versions/manifest.json` | PASS | JSON parse 1 | `versions/manifest.json` |
| `python scripts/validate_codex_package.py` | PASS | required files 12, manifest valid | terminal evidence |
| `scripts/check_secret_patterns.ps1` | PASS | secret pattern finding 0 | terminal evidence |
| active old-reference + spec placeholder `rg` | PASS | `07_KB_출처대장` active reference 0, TODO/TBD/FIXME 0 | terminal evidence |

### 미실행 검증과 이유

- 제품 test/build와 Docker/DB gate는 실행하지 않았다. 문서·결정만 변경하고 제품/API/DB/data를
  수정하지 않았기 때문이다. 대신 package/manifest/secret/diff/active-reference 검사를 통과했다.
- DRAFT validator test는 implementation plan 승인 전이라 아직 만들지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 실제 PII/시민 질문 0. 향후 staging PII fail-closed 규칙을 명세했다.
- Security: secret 0. 승인 content를 SHA-256에 묶고 self approval·stale hash를 차단한다.
- Accessibility: UI 변경 없음.
- Performance/cost: runtime 변화·LLM 호출·외부 비용 0원. JSON 35건 규모로 성능 위험 낮음.

## 10. 데이터와 출처 영향

- 공식 데이터: actual KB/office/mapping/release/seed 변경 0. source registry 내용도 미수정.
- mock/AI 생성: mock 0. written spec은 데이터 evidence가 아니다.
- schema/lineage: future four-artifact contract와 immutable release handoff만 설계했다.
- verified date: source audit 기준 2026-07-18 유지; PM 승인 직전 변동 사실 재확인 필요.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-DATA-002=A는 architecture 선택 승인이다. written spec을 검토한 뒤 `명세 승인`이 필요하다.
- 명세 승인 뒤에도 implementation plan을 별도 작성·검토하며, `계획 승인, 구현 시작` 전에는
  staging/schema/validator/DRAFT를 만들지 않는다.
- PM 승인자는 20 KB·3 office·12 mapping을 전수 검토하고 record별 decision/comment를 남겨야 한다.
- DATA-SEED/DB/readiness/public deployment와 새 production dependency는 이 승인에 포함되지 않는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- JSON schema 파일 분리, validator helper, deterministic serializer와 fixture naming은 승인된
  contract 안에서 AI가 계획 단계에서 구체화할 수 있다.
- 기존 Ajv 또는 Python 표준 라이브러리 중 exact validator path는 writing-plans에서 선택한다.

## 13. 인수인계·재현·롤백

### 재현

1. D-033, A-026, ADR-0015와 written spec의 path/state/count를 대조한다.
2. TEAM_DECISIONS/PROJECT_PLAN/RFP_MATRIX/TASKS의 initial 19/final 20을 검색한다.
3. `rg "07_KB_출처대장" docs` 결과가 역사적 discovery/ADR 설명 외 활성 참조 0인지 확인한다.
4. package validator, secret scan, JSON manifest parse, `git diff --check`를 실행한다.

### 롤백

아직 data/DB/code change가 없으므로 이 decision/spec commit을 revert한다. D-033 행은 삭제보다
새 superseding decision을 추가하는 원칙을 따른다. 승인된 official release는 이 rollback 대상이 아니다.

### 다음 개발자 시작점

사용자 written spec 승인 후 `superpowers:writing-plans`로 DATA-001 authoring/validator/manifest만
계획한다. DATA-SEED-001은 별도 spec/plan으로 유지한다.

## 14. 남은 위험·미해결 질문·다음 단계

- written spec 사용자 검토가 남았다.
- source facts의 변동성과 약한 mapping 2건은 PM approval risk다.
- Q-SEC-003/A-021 public-release blocker는 계속 열린 상태다.
- 공식 data/seed 0과 `/ready=503`은 정상이며 DATA-001 설계 완료로 바꾸지 않는다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
