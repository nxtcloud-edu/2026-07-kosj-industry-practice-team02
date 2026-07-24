# 버전 관리와 릴리스

현재 값의 단일 권위는 [`versions/manifest.json`](../versions/manifest.json)입니다.

| Axis | Current |
|---|---|
| Product spec | `2.4.0` |
| Repository guidance | `1.7.7` |
| Application | `0.8.0-pr8-frontend-baseline` |
| Web | `0.5.0-pr8-citizen-admin-baseline` |
| API | `3.1.0-draft` |
| Shared contracts | `0.4.0` |
| Database schema | `0.4.0-local` |
| Official data | `0.1.0-initial.2` |
| Mock data | `0.0.0-not-populated` |
| Prompt set | `0.1.0-upstage-solar-pro3-synthetic` |
| Test suite | `1.5.0-pr8-web-baseline` |
| Documentation | `2.16.3` |

## 증가 기준

- Major: 호환성 파괴 API/DB, 제품 범위·개인정보 정책·데이터 의미 변경
- Minor: 호환 가능한 기능·필드·공식 데이터·테스트 군 추가
- Patch: 문구·오탈자·내부 수정과 비호환 없는 버그 수정

`local`, `draft`, `baseline`, `synthetic` suffix는 production/public release가 아님을 나타냅니다.
공식 데이터 release는 immutable이며 오류 수정은 기존 파일 변경 대신 승인된 successor version으로
게시합니다.

## 릴리스 체크

- manifest와 changelog
- OpenAPI/JSON Schema/generated type
- migration/rollback/pgTAP
- official data hash와 lineage
- lint/typecheck/test/build/E2E
- 비밀·PII·browser bundle 검사
- 구현 노트와 rollback
