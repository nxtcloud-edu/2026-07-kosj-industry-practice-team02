# ADR-0015: staging JSON과 hash-bound 공식 데이터 승인

- Status: Accepted
- Date: 2026-07-18
- Deciders: 사용자(PM), Codex(Architecture·AI/Data·Backend)
- Related: Q-DATA-002 / D-033 / A-026 / DATA-001 / DAR-001·002

## Context

공식 KB 20건, 기관 3건, 지역×민원 매핑 10~12건의 작성·승인 책임과 기한은
Q-DATA-001/D-011로 확정됐지만, 승인 전 DRAFT를 저장할 경계와 PM이 무엇을 승인하는지
나타내는 artifact가 없었다. 기존 `data/official/kb_source_registry.csv`는 출처 감사 인덱스이며
KB 본문·기관·매핑의 canonical authoring format이나 승인 증거가 아니다. SQL seed를 직접
작성하면 승인 전 데이터와 시민 검색용 ACTIVE 데이터의 경계를 우회할 수 있다.

## Decision

1. DATA-001의 canonical authoring 위치는
   `data/staging/data-001/<draft-version>/`이다.
2. 한 draft version은 `kb_records.json`, `offices.json`,
   `office_service_mappings.json`, `approval_manifest.json` 네 artifact로 구성한다.
3. `approval_manifest.json`은 세 content artifact의 SHA-256, 레코드 수, 작성자, 제출 시각,
   레코드별 PM 결정과 검수 comment를 묶는다. manifest 자체는 자기참조 hash 대상이 아니다.
   PM 승인자는 작성자와 달라야 한다.
4. staging artifact는 시민 검색, DB seed, readiness, 성과 수치에 사용할 수 없다.
5. PM이 hash-bound manifest에서 승인한 레코드만 후속 DATA-SEED-001에서 immutable
   `data/official/releases/<data-version>/` snapshot으로 승격할 수 있다.
6. DATA-001은 official release나 SQL seed를 직접 생성하지 않는다. promotion/import는
   별도 계획·테스트·승인 경계를 가진 DATA-SEED-001 책임이다.
7. 회귀 시나리오를 위해 20개 KB를 staging에 작성하되 초기 release에는 19개만 승인한다.
   `KB-WASTE-03`은 `WITHHOLD_FOR_REGRESSION`으로 staging에 남기고 REG-001의 별도 작성자·승인자
   흐름으로 최종 20번째 ACTIVE가 된다.
8. 기관 3건과 매핑 12건을 staging한다. 초기 release는 PM이 승인한 매핑 10~12건만 포함한다.
9. `data/official/kb_source_registry.csv`를 source registry의 canonical 파일명으로 유지하고,
   미존재 `07_KB_출처대장.csv` 참조는 현재 파일명으로 고친다. source registry는 approval
   manifest를 대체하지 않는다.

`APPROVED_FOR_INITIAL_RELEASE`는 모든 record의 무조건 승인이 아니라 모든 record에 대한 처분이
완료되어 승인된 부분집합을 후속 promotion에 전달할 수 있다는 dataset 상태다.

## Alternatives considered

### 확장 CSV 하나로 authoring·승인 관리

스프레드시트 검토는 쉽지만 배열, nullable 조건, cross-file reference, artifact hash와
레코드별 승인 상태를 안전하게 표현하기 어렵다. JSON 문자열 셀이 늘어나 schema validation과
diff review가 취약해져 선택하지 않았다.

### SQL seed 직접 작성

DB에 바로 적재하기 쉽지만 승인 전 DRAFT와 ACTIVE seed가 결합되고, source artifact와 DB 상태의
계보를 분리하기 어려워 선택하지 않았다.

## Consequences

### Positive

- DRAFT·승인·official release·DB seed 경계가 파일 시스템과 상태로 분리된다.
- PM 승인이 검토한 exact content hash에 묶여 승인 뒤 조용한 내용 변경을 차단한다.
- JSON Schema와 cross-file validator로 필드·수량·참조·PII·mock 혼입을 자동 검사할 수 있다.
- 초기 19 KB와 회귀 후 최종 20 KB를 모순 없이 재현할 수 있다.

### Negative / tradeoffs

- 네 artifact와 validator, approval manifest 검수 절차를 관리해야 한다.
- 사람이 JSON을 직접 검토할 때 CSV보다 불편할 수 있어 validation summary를 별도로 제공해야 한다.
- staging 수정 뒤에는 hash를 다시 계산하고 PM 재승인을 받아야 한다.

## Security, data, cost impact

- 실제 시민 질문·PII·비밀값은 staging과 manifest에 넣지 않는다.
- 기관 공개 주소·전화는 공식 source URL과 확인일이 있을 때만 허용한다.
- LLM은 source title, URL, 확인일, 승인 결정을 생성하지 않는다.
- official/mock version, DB schema, public API, readiness와 외부 비용은 이 결정만으로 변하지 않는다.
- 새 production dependency는 승인하지 않았다. 구현은 기존 Node/Ajv·Python 표준 도구 경계를
  우선 사용한다.

## Migration and rollback

현재 official record와 seed가 0이므로 데이터 migration은 없다. 명세 구현 전에는 문서만
되돌리면 된다. 구현 뒤 staging draft는 official release와 독립적으로 삭제·재작성할 수 있지만,
승인된 immutable release는 덮어쓰지 않고 새 version으로 교정한다. DB import rollback은
DATA-SEED-001의 별도 보상 절차가 소유한다.

## Verification

- 네 artifact의 schema validation과 deterministic ordering
- KB 20, office 3, mapping 12 staging count
- 초기 승인: KB 19, office 3, mapping 10~12, WASTE-03 withheld exactly 1
- 작성자와 PM 승인자 동일 0건
- artifact hash mismatch 시 promotion fail closed
- PII·mock·비공식 source·누락 source/date 0건
- staging 경로를 seed/readiness/citizen read가 참조하는 코드 0건
