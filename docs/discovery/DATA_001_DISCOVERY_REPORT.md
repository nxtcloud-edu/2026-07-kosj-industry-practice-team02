# DATA-001 공식 데이터 발견 보고서

- 조사 기준일: 2026-07-18 KST
- 조사 주체: Codex(Architecture·AI/Data·Backend·Security·Docs)
- 기준 브랜치/커밋: `main` / `204cd969cc8104fdca430691960c794932d060c0`
- 상태: Discovery complete — staging artifact 설계 승인 대기
- 관련 결정: Q-DATA-001 / D-011 / A-005

## 1. 결론 요약

DB-001의 private schema와 ACTIVE-only 읽기 경계는 구현됐지만, 시민 답변에 사용할 공식 데이터는 아직 0건이다. 현재 활성 데이터는 20개 후보의 출처대장과 평가 질문 20개뿐이며, KB 레코드·기관·기관×민원 매핑·승인 seed·data lineage artifact는 없다. 따라서 현재 `/ready=503`은 의도한 안전 상태다.

Q-DATA-001로 작성 책임(AI/Data·Backend), 승인 책임(PM), 목표일(2026-07-20), 승인 전 staging 원칙은 이미 확정됐다. 다시 질문할 A/Blocker는 발견되지 않았다. 다만 DRAFT를 어디에 어떤 형식으로 저장하고 PM이 어떤 artifact를 승인할지는 활성 계약에 없으므로, 실제 DRAFT 작성 전 설계 승인과 실행계획이 필요하다.

## 2. 읽은 권위 문서와 활성 계약

- `AGENTS.md`, `data/AGENTS.md`
- `docs/00_SOURCE_OF_TRUTH.md`
- `docs/source-of-truth/TEAM_DECISIONS.md`
- `docs/source-of-truth/PROJECT_PLAN.md`
- `docs/source-of-truth/RFP_MATRIX.md`
- `docs/source-of-truth/KB_GUIDE.md`
- `docs/source-of-truth/APPROVAL_POLICY.md`
- `docs/06_DATA_AND_KB_POLICY.md`
- `docs/11_AMBIGUITY_REGISTER.md`
- `docs/decisions/DECISION_LOG.md`
- `docs/plans/PLAN-20260714-001-foundation-and-governed-chat.md`
- `contracts/kb-record.schema.json`
- `supabase/migrations/20260716000100_private_schema.sql`
- `supabase/migrations/20260716000500_indexes_and_read_interfaces.sql`
- `data/official/kb_source_registry.csv`
- `data/evaluation/sample_questions_20.csv`
- `versions/manifest.json`, `TASKS.md`

`legacy/`는 현재 계약이나 데이터 근거로 사용하지 않았다.

## 3. 실제 저장소 상태

| 영역 | 기대 | 실제 | 판정 |
|---|---|---|---|
| 공식 KB | 4개 분야 × 5건, 총 20건 | 실제 KB record 0건 | Missing |
| 출처대장 | 20건, 공식 출처·확인일·작성자·승인자·상태 | 후보 20행은 있으나 작성자·검수자 값이 모두 공란이고 승인일 열 없음 | Partial |
| 공식 기관 | 아름동·도담동·조치원읍 3건 이상 | 0건 | Missing |
| 지역×민원 매핑 | PM 검수된 10~12건 | 0건 | Missing |
| 승인 seed | ACTIVE KB 20·기관 3+·매핑 10~12 | `supabase/seed.sql`은 의도적으로 비어 있음 | Safe missing |
| 계보 | 버전별 source/provider/date/raw/transform/count/reviewer/rollback | 안내 README만 있고 버전별 ledger 0건 | Missing |
| 평가셋 | 표본 20개 + 회귀 1개 | 표본 CSV 20행; KB-WASTE-03 개선 회귀는 KB 가이드에만 정의 | Partial |
| 공식 데이터 버전 | 승인 전 `0.0.0-not-populated` | 정확히 `0.0.0-not-populated` | Consistent |
| readiness | 승인 seed 전 503 | 안전 기본값 503 | Consistent |

## 4. 최종 기준과 활성 계약의 차이

| ID | 권위 기준 | 현재 구현/데이터 | 영향 | 권고 |
|---|---|---|---|---|
| G-DATA-001 | 승인 전 데이터는 staging | 활성 데이터 디렉터리에 staging 경계가 없음 | DRAFT가 official/processed/mock 중 잘못된 위치에 섞일 수 있음 | 별도 staging artifact 계약을 설계하고 PM 승인 뒤 official로 승격 |
| G-DATA-002 | 모든 공식 record에 provider/source/date/author/reviewer/status | `kb_source_registry.csv`의 작성자·검수자 값은 전부 공란이고 approval date 열이 없음 | 승인 책임·최신성 추적 불가 | source registry/approval manifest에서 필수화 |
| G-DATA-003 | KB 20건을 schema로 검증 | `contracts/kb-record.schema.json`은 있지만 실제 record·data validator 0 | 필드 누락과 enum drift를 자동 차단하지 못함 | 기존 schema를 재사용하는 stdlib validator와 fixture gate 계획 |
| G-DATA-004 | 기관 3+와 매핑 10~12를 전수 검수 | 기관/매핑 artifact schema와 입력 파일 0 | seed importer의 입력 계약이 없음 | office·mapping 별도 schema/artifact 정의 |
| G-DATA-005 | source registry lineage | KB 가이드·제안서는 미존재 `07_KB_출처대장.csv`를 참조하지만 실제 활성 파일명은 `kb_source_registry.csv`이고 별도 approval artifact는 없음 | 최초 개발자가 canonical 파일과 승인 evidence를 추측해야 함 | canonical 명칭을 하나로 고치고 approval manifest 형식을 설계 승인 |
| G-DATA-006 | ACTIVE만 시민 검색 | DB는 이를 강제하지만 ACTIVE seed 0 | 기능 개발과 정상 SUCCESS가 차단됨 | DRAFT 작성→PM 승인→versioned seed 순서 유지 |
| G-DATA-007 | KB-WASTE-03은 초기 ACTIVE 제외 | 출처대장 상태가 `회귀 테스트 후 승인 예정` | `DATA-001(20 승인) → DATA-SEED → chat/admin → REG-001 → WASTE-03 승인`으로 현재 TASK 의존성이 순환함 | 20건 모두 작성·출처검증, 초기 19 ACTIVE+WASTE-03 보류 1, REG-001 승인 뒤 최종 20 ACTIVE로 단계화 |

## 5. 데이터 모델 적합성

### KB

`contracts/kb-record.schema.json`과 `app_private.kb_documents`는 핵심 필드가 대체로 일치한다. JSON 계약의 `id`는 DB의 `public_id`로 매핑되고, `question_examples`는 DB에서 `kb_question_examples`로 정규화된다. `procedure_steps`와 `required_documents`는 JSON array에서 DB `jsonb`로 매핑된다.

드리프트 가능 지점은 다음과 같다.

- JSON 계약은 provider와 `data_origin`을 포함하지 않지만 데이터 거버넌스는 provider와 OFFICIAL/MOCK 분리를 요구한다.
- DB는 ACTIVE에 `approved_by`와 `approved_at`을 요구하지만 JSON schema는 ACTIVE 조건부 필수 규칙을 표현하지 않는다.
- 데이터 가이드는 질문 예시 3~5개를 요구하지만 JSON schema는 최소 1개다.
- `approved_at`의 JSON Schema `format` 위치가 nullable union 전체에 적용되는지 validator별 동작이 다를 수 있다.

### 기관과 매핑

DB 필드는 이미 존재하지만 파일 기반 활성 계약은 없다. 기관은 `public_id`, `region`, `office_name`, `address`, `phone`, optional `opening_hours`/`map_url`, source metadata와 `data_origin`이 필요하다. 매핑은 `office_public_id`, 지원 intent, optional `department_label`의 복합키가 필요하다.

## 6. 보안·개인정보·품질 경계

- 공식 데이터 작업에는 실제 시민 질문, 이름, 주소, 연락처 등 개인정보를 넣지 않는다.
- 연락처·주소는 시민의 개인정보가 아니라 공식 기관 공개정보만 허용하고, 공식 페이지 URL과 확인일을 함께 보존한다.
- 검색 결과 요약, 블로그, 민간 안내 페이지는 source-of-truth로 채택하지 않는다.
- 수수료·기간·운영시간·전화번호처럼 변경 가능한 사실은 `last_verified_at`과 caution을 필수로 둔다.
- LLM은 source title/URL/date를 생성하지 않는다. 공식 출처를 사람이 확인한 metadata만 서버가 결합한다.
- DRAFT와 AI 보조 문장은 PM 승인 전 시민 검색·seed·readiness 판단에 사용하지 않는다.
- KB-WASTE-03은 회귀 시나리오가 끝날 때까지 ACTIVE에서 제외한다.

## 7. 공식 출처 재검증 중간 결과

### 대형폐기물·지방세·기관

2026-07-18 KST에 공식 1차 출처만으로 KB 10건, 기관 3건, 매핑 후보 12건을
재검증했다. 이 결과는 source audit이며 PM 승인이나 ACTIVE 전환이 아니다.

| 범위 | 결과 | 승인 전 조치 |
|---|---|---|
| KB-WASTE-01/02/04/05 | 세종시설관리공단 현재 페이지에서 절차·환불·품목 요금·요일·문의처 확인 | 페이지 자체 개정일이 없어 PM 승인 직전 재열람 |
| KB-WASTE-03 | 침대 프레임 1인용 8,000원·2인용 10,000원 확인 | 초기 ACTIVE 제외, REG-001에서 별도 승인 |
| KB-TAX-01 | 공식 위택스 조회·납부 경로 확인 | 개인 금액 조회 기능처럼 표현 금지 |
| KB-TAX-02 | 기존 URL은 자동차세 전용 근거가 아니라 로그인 화면 | DRAFT를 로그인 후 본인 고지 확인·납부 경로로 축소하거나 2026 전용 공식 출처 보강 |
| KB-TAX-03/04/05 | 정부24에서 방법·자격·기간·수수료·접수기관 범위 확인 | 개인 결과 조회 금지, 기관/신청자 유형별 예외 표시 |
| 기관 3건 | 세종시 공식 페이지에서 명칭·주소·전화·업무시간·지도·업무분장 확인 | 페이지 자체 확인일이 2025-02이므로 승인 직전 재확인 |
| 매핑 12건 | 3개 지역×4개 intent 후보 작성 가능 | 아름동×지방세, 도담동×대형폐기물의 1차 문의 범위·department label PM 확인 |

주요 공식 출처:

- 세종시설관리공단: <https://sjwaste.kr/board?menuId=MENU00303>
- 대형폐기물 품목: <https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305>
- 위택스: <https://www.wetax.go.kr/main.do>
- 아름동: <https://www.sejong.go.kr/areum/sub02_02.do?cmsNo=1461>
- 도담동: <https://www.sejong.go.kr/dodam/sub02_02.do?cmsNo=1458>
- 조치원읍: <https://www.sejong.go.kr/jochiwon/sub02_02.do?cmsNo=1425>

상세 감사 증거는 gitignored
`.superpowers/sdd/data-001-waste-tax-office-source-audit.md`에 보존했다. SHA-256은
`E874C812A5B7D7098D16E3CF57C6F0FE3C9DD9F549389F9C2F5F6DB4626A2737`이다.

### 전입·주민등록·증명서

정부24·국가법령정보센터 공식 경계에서 KB 10건을 재검증했다. 기존 `gov.kr/mw` 9개
URL은 일반 브라우저에서는 실제 서비스로 도달하지만 일부 자동 클라이언트에는 과거 점검
공지를 반환한다. 완전 단절로 판정하지 않으며, 현재 `plus.gov.kr` canonical 링크로 교체하는
B/High 안정성 조치가 필요하다.

| 범위 | 결과 | 승인 전 조치 |
|---|---|---|
| KB-MOVE-01/02 | 방법·자격·기간·수수료와 상황별 방문서류 확인 | `신분증 하나면 항상 가능` 같은 축약 금지 |
| KB-MOVE-03 | 온라인 본인 신청·대리 불가 범위 확인 | 특정 인증수단은 현재 안정 근거가 없어 단정 금지 |
| KB-MOVE-04 | 통보 대상·방법·자격 확인 | 현재 공식 전체 제목으로 갱신, 전입신고 자체와 구분 |
| KB-MOVE-05 | 주민등록법 현행 페이지와 일반 14일 원칙 확인 | 개인 위반·과태료·법적 판단 단정 금지 |
| KB-CERT-01..04 | 등본/초본 차이, 발급·열람 방법·자격·기간·수수료 확인 | 제출처 요구·대리/이해관계 예외와 확인일 표시 |
| KB-CERT-05 | 무인발급 장소·안내 경로 확인 | 시간·수수료·가능민원을 전국 고정값으로 단정 금지 |

현재 canonical 출처 예시:

- 전입신고: <https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01>
- 주민등록 통보: <https://plus.gov.kr/search/searchdtl/?srvcId=13110000039&typeSn=01>
- 등·초본 발급: <https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01>
- 주민등록표 열람: <https://plus.gov.kr/search/searchdtl/?srvcId=13100000014&typeSn=01>
- 무인민원발급: <https://plus.gov.kr/portal/custcntr/utztngd/unmncvlcptissugd/>
- 주민등록법: <https://www.law.go.kr/LSW/lsInfoP.do?lsId=001655&urlMode=lsInfoP>

상세 감사 증거는 gitignored
`.superpowers/sdd/data-001-move-cert-source-audit.md`에 보존했다. SHA-256은
`E009EE8DD14C1EF01F2CA4BFFD32B363E72427160AB2E65B6E9D56F0759D6C4A`이다. 두 병렬
감사 모두 새로운 A/아키텍처 blocker는 찾지 않았으며, 기존 PM 전수 승인만 ACTIVE gate로
유지한다.

## 8. 미지의 영역 분류

| ID | 등급 | 내용 | 현재 처리 |
|---|---|---|---|
| Q-DATA-002 | B/High, 설계 승인 필요 | staging artifact와 PM approval manifest 형식 | 발견 결과와 2개 대안을 제시하고 사용자 승인 후 계획 작성 |
| A-DATA-002 | C/Defaultable | author/reviewer의 저장소용 stable ID 표기 | `AI-DATA-BACKEND` / `PM` 같은 비개인 식별자를 추천하되 설계에 명시 |
| A-DATA-003 | C/Defaultable | 날짜·URL 정규화·CSV 정렬 방식 | ISO 8601 date, HTTPS canonical URL, public ID lexical sort 추천 |
| A-DATA-004 | D/Internal | JSON/CSV validator의 helper/file 분리 | 기존 Python 3.12 stdlib 중심으로 계획 |
| A-DATA-005 | D/Internal | generated SQL formatting과 deterministic ordering | importer 산출물 hash와 row count로 재현성 검증 |

Q-DATA-001의 책임·승인자·기한은 이미 해결됐으므로 다시 질문하지 않는다. PM의 실명이나 계정 체계는 local/private DRAFT 제작에는 필요하지 않으며, 실제 인증/RBAC는 P2 또는 공개 운영 결정이다.

### 회귀 예외의 권위 해석

`RFP_MATRIX`의 DAR-001과 `TASKS.md`는 최종 20 ACTIVE를 요구하지만, `KB_GUIDE` 8절은
KB-WASTE-03을 개선 전 폴백→관리자 후보 작성→별도 승인→동일 질문 개선 시연에 사용하도록 더
구체적으로 정한다. 두 목표를 모두 만족하려면 수량 기준을 다음 두 gate로 나눠야 한다.

1. DATA-001/DATA-SEED 초기 gate: KB 20건의 내용·출처를 작성하되 19건만 PM 승인 ACTIVE,
   KB-WASTE-03은 source-verified DRAFT/PENDING으로 보류한다.
2. REG-001 최종 gate: 관리자 개선 루프에서 KB-WASTE-03을 별도 승인한 뒤 최종 20 ACTIVE를
   확인한다.

이는 범위 변경이 아니라 이미 승인된 회귀 동작과 최종 20건 요구의 의존성 순환을 제거하는
추적성 보정이다. 실제 TASKS/계획 변경은 설계 승인 뒤 함께 반영한다.

## 9. 지금 안전하게 가능한 작업

1. 20개 후보와 3개 기관의 공식 1차 출처를 2026-07-18 기준으로 재검증한다.
2. 오래되거나 redirect/동적 페이지인 URL, 출처로 확인할 수 없는 구체 수치, 지역별 예외를 표시한다.
3. staging/approval artifact의 설계 대안을 제시한다.
4. 승인된 설계로 DATA-001 실행계획을 작성한다.

## 10. 현재 차단된 작업

- PM 승인 전 `ACTIVE` KB 생성
- 승인 전 데이터를 `supabase/seed.sql`에 넣는 작업
- official data version을 `0.1.0`으로 올리는 작업
- `/ready=200` 전환
- DRAFT를 시민 답변·검색·데모 성과 근거로 사용하는 작업
- 실제 시민 개인정보가 포함된 질문을 평가·출처 데이터에 추가하는 작업

## 11. 다음 산출물

- 공식 출처 재검증 결과 통합본
- DATA-001 staging·approval 설계 명세
- 승인 후 DATA-001 상세 실행계획
- DRAFT KB/기관/매핑과 자동 검증 report
- PM 승인 후에만 official dataset/lineage/seed로 승격
