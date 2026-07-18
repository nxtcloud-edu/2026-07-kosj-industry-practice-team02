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

## 현재 local DB 기준선과 manifest

DB-001 Task 10은 2026-07-18 disposable actual gate를 통과해 local/private 기준선으로 승격됐다.

```text
repo_guidance: 1.5.0
database_schema: 0.3.0-local
test_suite: 0.5.0-db-baseline
documentation: 2.4.0
```

승격 근거는 6개 timestamp forward/compensation, pinned patched runtime, actual exact one
`127.0.0.1:54322`, fresh pgTAP 282, integration 8/8, compensation/absence/replay와 static/root gate다.
제품·API·shared contracts·official/mock data·prompt 축은 바뀌지 않았다. 공식 데이터·mock 데이터는
모두 `0.0.0-not-populated`이고 `/ready=503`이 정상이다. `local` suffix는 공개·원격·production
release가 아님을 명시한다. A-021/Q-SEC-003은 계속 별도 public blocker다.

## 릴리스 체크

- version manifest
- CHANGELOG
- migration/rollback
- OpenAPI/JSON schema
- tests/report
- data lineage
- implementation notes/handoff
