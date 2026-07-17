# 버전 관리와 릴리스 기록

## 버전 축

`versions/manifest.json`에서 다음을 독립적으로 관리한다.

- product_spec
- repo_guidance
- application/web/api
- database_schema
- official_data/mock_data
- prompt_set
- test_suite
- documentation

## 증가 기준

### Major

- 호환성 파괴 API/DB
- 제품 범위 또는 개인정보 정책의 근본 변경
- 데이터 의미/평가 정의 변경

### Minor

- 호환 가능한 기능·필드 추가
- KB 분야/공식 데이터 추가
- 새 테스트 군/프롬프트 기능

### Patch

- 버그·문구·오탈자·비호환 없는 내부 수정

## 구현 노트 기록 예시

```text
Before
- api: 0.1.0-draft
- schema: 0.1.0-draft
- data: 0.0.0

After
- api: 0.2.0
- schema: 0.2.0
- data: 0.1.0
```

Git commit가 아직 없으면 `uncommitted`라고 기록하고, 현재 HEAD를 함께 적는다.

## 현재 local DB 후보와 manifest

DB-001 Task 10은 host port security blocker로 완료되지 않았다. 현재 manifest 축은 승격 전
값을 유지한다.

```text
repo_guidance: 1.4.0
database_schema: 0.2.0-draft
test_suite: 0.4.2-readiness-contract
documentation: 2.3.14
```

`0.3.0-local`은 6개 timestamp forward migration뿐 아니라 exact loopback runtime, full DB/root
gate와 independent review가 모두 통과한 뒤에만 사용할 후보다. Q-SEC-004=A의
`default-local-port-binding`도 actual IPv6 wildcard `::`를 남겼으므로 Q-SEC-005/A-023 해결 전
승격하지 않는다. 공식
데이터·mock 데이터는 모두 `0.0.0-not-populated`이고 A-021/Q-SEC-003은 별도 public blocker다.

## 릴리스 체크

- version manifest
- CHANGELOG
- migration/rollback
- OpenAPI/JSON schema
- tests/report
- data lineage
- implementation notes/handoff
