# IMP-20260716-009 — Q-SEC-002 and Q-WF-001 decision synchronization

- Date/Time (KST): 2026-07-16T23:17:59+09:00
- Task ID: DB-001-DECISIONS
- Type: decision
- Status: Decision-only Done
- Author/Agent: Codex
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `af12b23`
- Related plan/ADR/RFP: D-026, D-027, ADR-0011, DB-001 approved specification and execution plan

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 `Q-SEC-002=A`, `Q-WF-001=A`를 선택해 fail-closed 권한 정책과 별도 사유 확인 경계를 승인했다. 제품 코드·SQL·role을 변경하지 않고 두 결정을 현재 권위 문서, 설계 명세, 실행계획, 상태 문서에 동기화하고 DB-001 Task 5의 인간 결정 gate를 닫는다.

### Acceptance Criteria

- non-superuser PostgreSQL 17 runner의 fail-closed role 재검증 정책을 명시한다.
- 실패 질문 사유 확인을 별도 backend-only capability로 고정하고 event 분류 불변성, 후보 생성 gate, 감사 메타데이터, 승인 comment 요구를 명시한다.
- 적용·커밋된 migration `00100`~`00300`은 불변으로 두고 workflow를 `00400`, read interface를 `00500`으로 계획한다.
- 공개 OpenAPI, SQL, 제품 코드, 테스트, DB 데이터, 비밀값은 변경하지 않는다.
- 구현 노트·INDEX·문서 버전·백로그를 동기화하고 문서/JSON/비밀/링크 검증을 통과한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 인간 결정자(사용자)가 A/A를 승인하고 Codex가 문서 동기화 및 자체 검증을 수행했다. |
| When — 언제 | 2026-07-16 KST, DB-001 Task 5 기술 검토 직후 Task 6 구현 전. |
| Where — 어디서 | local-only worktree의 source-of-truth, ADR, 설계/계획, 발견 기록, 구현 노트, 백로그와 버전 manifest. |
| What — 무엇을 | Q-SEC-002와 Q-WF-001을 D-026/D-027로 확정하고 Task 5를 완료 상태로 전환했다. |
| Why — 왜 | role 권한 상승 시 자동 특권 복구 위험과 실패 질문 사유 확인/후보 생성의 상태·감사 공백을 구현 전에 닫기 위해서다. |
| How — 어떻게 | 기존 계약과 migration을 읽고 인간 선택을 최소 권한·불변 migration 원칙에 맞춰 문서화했으며 집중 정합성 검사를 수행했다. |
| How much — 어느 정도 | 문서/메타데이터만 변경했다. 공개 API·DB schema·코드·테스트·데이터·외부 비용 영향은 0이다. |

## 3. 시작 전 상태

- 관련 파일: `TEAM_DECISIONS.md`, `APPROVAL_POLICY.md`, 도메인 상태 모델, DECISION_LOG, AMBIGUITY_REGISTER, ADR-0011, DB-001 spec/plan, Task 5 노트, OpenAPI와 migration `00100`~`00300`.
- 기존 동작: DB-001 Tasks 0~5의 SQL과 검증은 완료됐지만 두 인간 결정이 문서상 open blocker로 남아 있었다.
- 발견한 충돌/부채: 계획이 적용된 `00300` 수정과 불가능한 특권 자동복구를 암시했고, 사유 확인 capability·event 불변성·후보 gate·감사 allowlist가 닫히지 않았다.
- Git 상태: 기준 `af12b23`; 기존 DB-001 문서 변경 외 제품 코드/SQL 변경 없음.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-SEC-002 | A/Blocker | unsafe runner role을 자동 교정할지 실패할지 | A: runner가 허용한 비특권 속성만 재확인하고 unsafe privilege는 fail closed | local reset/replay, 권한 테스트, 운영 안전 |
| Q-WF-001 | A/Blocker | 실패 사유 확인을 후보 생성에 결합할지 별도 capability로 둘지 | A: 별도 `confirm_failed_question_reason` capability | 상태 머신, 감사 로그, 후보 생성, backend repository |

두 질문 모두 해결됐으며 현재 인간 결정형 A/Blocker는 0이다.

## 5. 설계 결정과 대안

### 선택

- D-026: non-superuser PostgreSQL 17 runner 유지. role 생성은 허용하되 replay 때 runner가 허용한 `NOLOGIN/NOCREATEDB/NOCREATEROLE`만 재설정한다. `NOSUPERUSER/NOREPLICATION/NOBYPASSRLS`, membership, role settings를 catalog에서 검증하고 unsafe role이면 중단한다.
- D-027: `confirm_failed_question_reason(uuid,text,text,text) RETURNS void`를 별도 backend-only capability로 둔다. `interaction_events.fallback_reason`은 최초 자동 분류로 불변이며, `NEW → REASON_CONFIRMED`에서 실패 행의 사유와 eligibility만 확인/정정한다.
- 후보 생성은 `REASON_CONFIRMED + INSUFFICIENT_GROUNDING + candidate_eligible=true`에서만 허용한다.
- 사유 확인 감사 action/target은 `FAILED_QUESTION_REASON_CONFIRMED`/`FAILED_QUESTION`이며 질문 텍스트 snapshot을 저장하지 않는다.
- OpenAPI wire는 이미 요구사항을 표현하므로 유지한다. 내부 승인 함수만 계획상 `approve_kb_candidate(uuid,text,text,text)`로 맞춰 승인 comment도 저장한다.

### 이유

권한을 자동 상승시키지 않으면서도 local replay를 결정적으로 만들고, 자동 분류 증거와 운영자 확인 결과를 분리해 멱등성·감사 가능성·후보 품질을 동시에 지키기 위해서다.

### 고려했지만 선택하지 않은 대안

- privileged bootstrap/자동 downgrade: least privilege와 fail-closed 원칙에 어긋나 제외했다.
- 후보 생성 함수에 사유 확인을 암묵적으로 결합: 상태 전이와 감사 책임이 섞이고 독립 재검토가 어려워 제외했다.
- event 사유 자체 수정: 최초 자동 판정과 request replay 의미를 훼손하므로 제외했다.
- 적용 migration `00300` 수정: applied migration immutability를 위반하므로 제외했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| source-of-truth/도메인/결정/ADR | D-026/D-027, role fail-closed, 별도 사유 확인, 후보 gate, 감사 규칙 동기화 | 권위 문서 단일 의미 유지 |
| DB-001 spec/plan | Task 5 완료, 5개 migration 계보, Task 6의 exact capability·검증·rollback 순서 반영 | 구현자가 applied migration을 수정하지 않도록 함 |
| ambiguity/status notes/TASKS | open blocker 제거와 Task 6 ready 상태 기록 | 현재 상태와 인수인계 일치 |
| manifest/implementation-note INDEX | docs `2.3.13 → 2.3.14` 및 변경 요약 | 문서 계보 유지 |
| CHANGELOG/CODEX index/DB discovery/Database README | 역사적 발견 기록은 보존하고 현재 Task 5 완료·Task 6 ready 상태를 짧게 연결 | 오래된 상태를 활성 기준으로 오인하지 않도록 함 |

### 데이터 흐름/상태 변화

향후 Task 6에서만 `failed_questions: NEW → REASON_CONFIRMED`가 생긴다. event 사유는 그대로 두고 failure 사유·eligibility만 확인값으로 갱신하며, 실제 변경 필드만 metadata audit에 남긴다. 이번 작업은 문서 결정만 기록해 DB 행은 바꾸지 않았다.

### 오류·빈 상태·롤백

unsafe role은 자동 복구하지 않고 실행을 중단한다. 잘못된 역할/상태/사유는 기존 DB 오류 계약으로 거부할 계획이다. 문서 변경 롤백은 이 커밋을 revert하며, 향후 DB 보상 순서는 `00500 → 00400 → 00300 → 00200 → 00100`이다.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.0
- repo_guidance: 1.4.0
- application: 0.1.0
- web: 0.1.0
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.2.0-draft
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 0.4.2-readiness-contract
- documentation: 2.3.13

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.1.0 | 0.1.0 | 제품 코드 변경 없음 |
| Web | 0.1.0 | 0.1.0 | UI 변경 없음 |
| API | 2.0.1-draft | 2.0.1-draft | wire contract 변경 없음 |
| DB schema | 0.2.0-draft | 0.2.0-draft | SQL/migration 변경 없음 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | 공식 데이터 없음 |
| Mock data | 0.0.0-not-populated | 0.0.0-not-populated | mock 데이터 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | prompt 변경 없음 |
| Test suite | 0.4.2-readiness-contract | 동일 | 테스트 코드 변경 없음 |
| Docs | 2.3.13 | 2.3.14 | 두 인간 결정과 실행계획 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `git status --short --branch` 및 권위/계획/노트 검사 | 기준 branch와 docs-only 작업 범위 확인 | 2026-07-16 KST | 이 노트와 Git diff |
| `git diff --check` | 통과 | 완료 전 실행 | Git 출력 |
| `python -m json.tool versions/manifest.json` | 통과 | 완료 전 실행 | manifest |
| markdown local-link 검사 | 통과 | 완료 전 실행 | repository docs |
| secret-like pattern 집중 검사 | 신규 비밀값 0 | 완료 전 실행 | changed files |
| scope/diff 검사 | SQL·코드·OpenAPI·PACKAGE_MANIFEST·VERSION 변경 0 | 완료 전 실행 | Git diff |

### 미실행 검증과 이유

제품/DB 테스트는 실행하지 않았다. 이번 요청은 결정·문서·메타데이터만 변경했고 실행 SQL과 코드에는 손대지 않았기 때문이다. 기존 Task 5의 기술 검증 결과 172/172는 노트 008의 증거를 그대로 참조하며 재실행 결과로 주장하지 않는다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문/답변/PII 원문을 새로 기록하지 않았다. 향후 사유 확인 audit도 text snapshot을 금지한다.
- Security: unsafe role을 자동 특권 교정하지 않는 fail-closed 정책과 backend-only capability 경계를 강화했다.
- Accessibility: 사용자 UI 변경이 없어 직접 영향 없음.
- Performance/cost: 실행 경로·외부 API 호출·의존성·비용 변경 없음. 향후 확인 transaction 1회가 추가되는 설계 영향만 있다.

## 10. 데이터와 출처 영향

- 공식 데이터: 여전히 `not-populated`; 출처/확인일/승인 데이터 추가 없음.
- mock/AI 생성: 추가·혼합 없음.
- schema/lineage: 실제 schema version은 유지. 적용된 `00100`~`00300`은 불변, 계획상 `00400` workflow와 `00500` read migration을 추가한다.
- verified date: 2026-07-16 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-SEC-002=A와 Q-WF-001=A는 D-026/D-027로 확정됐고 DB-001 Task 5의 인간 blocker는 해소됐다.
- DB-001 전체는 아직 완료가 아니며 Task 6~10이 남았다.
- 다음 SQL 변경은 새 `00400` migration으로만 수행하고 적용된 `00100`~`00300`을 고치지 않는다.
- 공개 배포, 원격 DB, 실제 시민 데이터, 파괴적 migration은 계속 별도 승인 대상이다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- 문서 링크/색인/상태 문구와 exact function signature, migration 번호를 같은 의미로 정렬했다.
- OpenAPI가 이미 reason PATCH와 승인/반려 comment를 요구하므로 wire version을 올리지 않았다.
- SQL과 code의 실제 구현·TDD는 승인된 plan의 Task 6에서 수행한다.

## 13. 인수인계·재현·롤백

### 재현

1. branch `codex/db-001-layered-enforcement`의 이 결정 동기화 커밋을 checkout한다.
2. D-026/D-027, ADR-0011, approved spec/plan과 ambiguity register를 읽는다.
3. `versions/manifest.json`의 documentation `2.3.14`와 INDEX 상태를 확인한다.
4. Task 6 RED test부터 시작하며 기존 migration `00100`~`00300`은 수정하지 않는다.

### 롤백

이번 docs-only 커밋을 revert하면 된다. DB·데이터 복구는 필요 없다. 향후 migration rollback은 별도 인간 승인 후 `00500 → 00400 → 00300 → 00200 → 00100` 순서다.

### 다음 개발자 시작점

`docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md`의 Task 6을 따라 reason-confirmation RED test와 새 `20260716000400_candidate_workflow.sql`부터 구현한다.

## 14. 남은 위험·미해결 질문·다음 단계

- 인간 결정형 A/Blocker는 0이다.
- DB-001 Task 6~10, 공식 seed, 시민 chat, 관리자 UI, 배포는 아직 미구현이다.
- Task 6은 확인/후보/승인 동시성, event reason 불변성, comment 저장, rollback/replay를 실제 SQL로 검증해야 한다.
- 비특권 runner 환경 차이는 catalog 검증으로 fail closed하며 privileged 자동 bootstrap으로 우회하지 않는다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
