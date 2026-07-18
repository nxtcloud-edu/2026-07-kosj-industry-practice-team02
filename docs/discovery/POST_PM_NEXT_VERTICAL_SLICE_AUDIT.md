# PM 검수 완료 진술 이후 다음 수직 흐름 감사

- 감사일: 2026-07-19 (KST)
- 기준 커밋: `73719b9`
- 상태: Discovery complete — 제품·공식 데이터 변경 없음
- 범위: DATA-001 승인 증거, DATA-SEED-001, WEB-HOME-001

## 1. 결론

사용자는 `pm 검수 다 완료`라고 보고했다. 이 발화는 검수 완료 **진술**로 접수한다. 다만 저장소의
canonical 승인 증거인
`data/staging/data-001/0.1.0-draft.1/approval_manifest.json`은 여전히
`PENDING_PM_REVIEW`이며, 검토자·검토시각·총평과 35개 레코드의 결정·코멘트가 비어 있다.
따라서 현재 bytes만으로는 DATA-001을 `Approved`로 바꾸거나 official release/DB seed를 만들 수 없다.

사람이 해야 하는 결정은 `KEEP`하고, 그 밖의 안전한 작업으로 실제 상태·질문·다음 순서를 이 문서,
모호성 레지스터, 결정 로그와 TASKS에 동기화했다. 제품 코드, DB, 공식 데이터, mock, API 계약과
dependency는 변경하지 않았다.

## 2. 읽고 확인한 근거

- 권위 문서: `AGENTS.md`, `docs/00_SOURCE_OF_TRUTH.md`, TEAM_DECISIONS, PROJECT_PLAN,
  RFP_MATRIX, ADR-0015, DATA-001 spec/plan
- 정책·계약: `docs/06_DATA_AND_KB_POLICY.md`, `docs/07_APPROVAL_POLICY.md`,
  `data/schemas/data-001/v1/approval-manifest.schema.json`, `database/`, `contracts/`
- 실제 승인 산출물: DATA-001 staging JSON 3종, approval manifest, processed PM review package
- 다음 구현 표면: `TASKS.md`, `/` page/tests/CSS, 현재 route와 API route
- 실행 경계: local/private, official data `0.0.0-not-populated`, mock data
  `0.0.0-not-populated`

`legacy/`는 현재 계약의 근거로 사용하지 않았다.

## 3. 최종 기준과 실제 상태의 간극

| ID | 최종 기준 | 실제 저장소 | 영향 | 현재 처리 |
|---|---|---|---|---|
| G-PM-001 | PM이 35건을 전수 결정하고 코멘트를 남긴 hash-bound manifest | 상태 `PENDING_PM_REVIEW`; `reviewed_by`·`reviewed_at`·`review_comment`가 `null`; 35개 decision/comment가 `null` | 승인 record 집합을 확정할 수 없음 | Q-DATA-003 `KEEP`; 승격 금지 |
| G-PM-002 | 작성자와 승인자는 달라야 함 | 작성자는 `AI-DATA-BACKEND`; 승인자 ID 미기록 | 자기 승인 금지 증거가 없음 | 독립 reviewer ID 필요 |
| G-SEED-001 | 승인 record만 immutable official release와 seed/import로 승격 | official release/seed 0; TASKS가 별도 plan approval 요구 | 시민 ACTIVE 검색·readiness·AI 흐름 시작 불가 | Q-SEED-001 `KEEP` |
| G-WEB-001 | `/`에 동작하는 `/chat` 진입 제공 | `/chat` route 없음; 현재 `/` 테스트는 `/chat` 링크가 없음을 요구 | 지금 링크를 추가하면 404, placeholder는 새 사용자 동작 | Q-WEB-001 `KEEP` |
| G-SEC-001 | public release 전 privileged function search path 보정 또는 public 차단 | A-021/Q-SEC-003 미해결; local/private는 허용 | 원격/public 배포 차단 | 기존 기본값 B 유지 |

승인 manifest가 참조하는 세 content artifact의 SHA-256은 현재 bytes와 일치한다. 문제는 content
변조가 아니라 사람의 최종 disposition과 audit metadata가 기록되지 않은 것이다.

## 4. 안전하게 진행 가능한 범위

이번 요청에서 자율적으로 진행할 수 있는 범위는 다음과 같다.

1. PM 완료 진술과 canonical evidence 간극을 감사 문서와 추적표에 기록한다.
2. DATA-SEED-001의 구현 대안을 분석하고 추천안을 고정하되 release/seed를 만들지 않는다.
3. WEB-HOME-001의 현재 구현·테스트·접근성 경계를 분석하되 사용자에게 보이는 동작은 바꾸지 않는다.
4. 결정 이후 실행 순서와 검증 gate를 준비한다.

공식 데이터 승격, DB import, `/ready=200`, 시민 답변 검색, `/chat` placeholder는 모두 제품/데이터
동작을 바꾸므로 아래 결정 전에는 수행하지 않는다.

## 5. 추천 설계

### 5.1 DATA-SEED-001

추천은 **immutable filesystem release + 결정론적 transactional seed 생성**이다.

- `data/official/releases/<version>/`에 승인된 content, 승인 manifest, release manifest를 불변 저장
- 승인 `APPROVE` record만 포함하고 KB-WASTE-03, rejected mapping, mock은 제외
- 초기 목표: KB 19, office 3, mapping은 최종 PM 결정 수만큼(현재 권고는 10)
- 기존 DB schema를 그대로 사용하고 새 migration이나 release-ledger table은 만들지 않음
- import는 한 transaction에서 수행하고 partial commit을 금지
- compensation delete는 참조 row가 없는 초기 빈 disposable local DB에서만 허용하고, non-empty 또는
  released DB는 preflight에서 fail closed
- release version과 source hash를 seed/lineage에 고정한다. release bytes의 교정은 삭제/수정이 아니라
  새 immutable release로 수행

대안인 DB release ledger는 감사 질의를 강화하지만 새 migration·ADR·인간 승인이 필요하다. release만
만들고 import를 미루는 대안은 가장 보수적이지만 READY/AI 흐름을 계속 차단한다.

### 5.2 WEB-HOME-001

현재 정적 Server Component, semantic HTML, system font, 외부 asset 없음 경계를 유지한다. 확정된
4개 지원 분야와 명시적 한계를 보여주고 `/chat` CTA는 실제 destination이 안전하게 존재할 때만
활성화한다. 404 링크를 만드는 선택은 권고하지 않는다.

## 6. 우선순위 인터뷰 질문

Q-DATA-003. PM 검수 결과를 canonical approval manifest에 어떤 방식으로 확정할 것인가
- 왜 지금 필요한가: 사용자 진술만으로는 35건의 승인/보류/반려 집합과 독립 검토자, 시각, 코멘트를 재현할 수 없다. 이를 추정하면 공식 데이터 승인 이력을 AI가 위조하게 된다.
- 선택지 A / 장점 / 단점: 현재 PM review package의 권고안(19 KB 승인, KB-WASTE-03 보류, 기관 3 승인, 매핑 10 승인·2 반려)을 PM의 최종 결정으로 채택하고, stable local reviewer ID와 레코드별 권고 근거를 PM 확인 코멘트로 materialize한다 / 가장 빠르고 현재 검증 근거와 일치하지만 PM이 권고안을 실제로 그대로 채택했다는 명시 확인이 필요하다.
- 선택지 B / 장점 / 단점: PM이 수정한 35건의 최종 disposition·코멘트와 reviewer ID를 제공한다 / 실제 검수 의도를 가장 정확히 보존하지만 입력·재검증 시간이 더 든다.
- 당신의 추천안: A. PM이 `PM-LOCAL-001`을 자신의 stable local reviewer ID로 명시 확인하고, 실제 final disposition을 확정한 시각을 KST ISO-8601로 제공·확인한다. PM이 이 답변을 final confirmation으로 삼는다면 `이 답변 시각`이라고 명시할 수 있다. 이후 validator와 hash를 다시 검증한다.
- 답을 받지 못할 때 사용할 기본값: 현재 manifest를 `PENDING_PM_REVIEW`로 유지하고 official release/seed를 만들지 않는다.
- 영향을 받는 파일·계약·데이터·배포: approval manifest, processed review report, DATA-001 lineage/status, official release 후보 집합, DATA-SEED 입력; DB/API/dependency/public 배포는 아직 변하지 않는다.

Q-SEED-001. 승인 레코드를 어떤 release/import 구조로 승격할 것인가
- 왜 지금 필요한가: TASKS와 ADR-0015가 DATA-SEED-001을 별도 계획·승인 경계로 두며, 선택에 따라 새 DB migration, rollback, lineage와 readiness가 달라진다.
- 선택지 A / 장점 / 단점: immutable filesystem release와 기존 schema용 결정론적 transactional seed를 생성하고, 참조 row가 없는 초기 빈 disposable local DB에만 compensation을 허용한다 / 새 migration 없이 재현·감사·복구가 가능하지만 release 조회용 DB ledger는 없고 non-empty DB는 delete rollback 대신 새 release가 필요하다.
- 선택지 B / 장점 / 단점: release ledger table과 import function을 next unused versioned migration으로 추가한다 / DB에서 배포 이력을 쉽게 조회하지만 migration·보안 표면·회귀 범위가 커지고 Q-SEC-003 migration과 순서를 조정해야 한다.
- 당신의 추천안: A. 0원 local-first 데모에 필요한 최소 구조이며 기존 승인 경계를 보존한다.
- 답을 받지 못할 때 사용할 기본값: release/seed를 생성하지 않고 DATA-SEED-001을 Blocked로 유지한다.
- 영향을 받는 파일·계약·데이터·배포: `data/official/releases/`, seed/import/rollback scripts, lineage/version manifest, DB rows, `/ready`; 선택지 B이면 migration/ADR/DB schema version도 변경된다.

Q-WEB-001. `/chat` 기능이 아직 없을 때 홈의 채팅 시작 CTA를 어떻게 동작시킬 것인가
- 왜 지금 필요한가: WEB-HOME-001 완료 기준은 `/chat` 진입을 요구하지만 현재 route가 없다. 404 링크, 준비중 화면, CTA 보류는 시민이 보는 동작이 서로 다르다.
- 선택지 A / 장점 / 단점: 접근 가능한 최소 `/chat` 준비중 화면을 먼저 만들고 홈 CTA를 연결한다 / 홈 흐름과 오류 없는 navigation을 검증할 수 있지만 임시 사용자 화면이 하나 생긴다.
- 선택지 B / 장점 / 단점: 실제 WEB-CHAT-001을 구현할 때까지 현재 CTA를 유지하고 WEB-HOME-001 완료를 보류한다 / 임시 화면이 없지만 홈 수직 흐름 완료가 늦어진다.
- 당신의 추천안: A. 지원 분야·개인조회 불가·데이터 미준비 상태를 명확히 알리고 입력/저장은 하지 않는 static shell로 제한한다.
- 답을 받지 못할 때 사용할 기본값: B. dead link를 만들지 않고 현 상태를 유지한다.
- 영향을 받는 파일·계약·데이터·배포: `/`, 새 `/chat` route와 route test, responsive/accessibility 검증; API/DB/LLM/개인정보 저장은 변하지 않는다.

## 7. 답변 예시

```text
Q-DATA-003: A — PM-LOCAL-001을 reviewer ID로 확인, 권고안 그대로 확정, 이 답변 시각을 final confirmation 시각으로 사용
Q-SEED-001: A
Q-WEB-001: A
```

## 8. 결정 이후 실행 순서

1. Q-DATA-003 확정 → approval manifest materialize → canonical validator/hash/secret 검증
2. Q-SEED-001 확정 → DATA-SEED 명세 제시 → 사용자 명세 승인 → 실행계획 제시 → 계획 승인 후 TDD 구현. import preflight, deterministic replay, failed transaction partial row 0, 빈 disposable DB compensation 조건을 gate로 포함
3. DATA-SEED 완료 → READY-001 → AI-001 → API-CHAT-001 → WEB-CHAT-001
4. Q-WEB-001=A이면 데이터 흐름과 독립적인 static home/chat shell을 먼저 병렬 구현
5. public 경로는 Q-SEC-003 해결 전 계속 차단

## 9. 인간/AI 책임 경계

### 인간이 반드시 알아야 하거나 승인할 내용

- 35건의 최종 disposition과 reviewer identity는 AI가 추정하지 않는다.
- official release/DB seed 구조와 사용자에게 보이는 `/chat` 임시 동작은 승인 전 변경하지 않는다.
- 현재는 local/private 기준이며 public release는 A-021/Q-SEC-003 때문에 계속 차단된다.

### AI 내부 구현 세부 — 인간이 굳이 이해하지 않아도 되는 내용

- 승인 후 JSON 정렬, hash 재계산, fixed SQL 순서, fixture 분리, fail-closed preflight, 테스트 helper와 문서 링크 정리는
  기존 계약 안에서 자율 처리한다.
