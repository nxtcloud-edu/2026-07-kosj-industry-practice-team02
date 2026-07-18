# 데이터·KB·계보 정책

## 데이터 영역

```text
data/staging/      승인 전 공식 출처 기반 DRAFT와 hash-bound approval manifest
data/official/     공식 출처를 사람이 확인한 원본/정제본
data/evaluation/   표본 20개와 회귀 케이스
data/mock/         관리자 화면 시연용, 공식 근거로 사용 금지
data/processed/    재현 가능한 스크립트가 만든 산출물
```

staging은 시민 근거가 아니다. PM이 artifact hash와 record decision을 전수 검수한 뒤에도
DATA-SEED-001의 immutable release promotion을 통과하기 전에는 `data/official/releases/`나 DB
seed로 승격할 수 없다.

## 공식 데이터 규칙

- 출처, 제공기관, URL/문서 ID, 확인일, 작성자, 승인자, 상태를 기록한다.
- 원본을 장문 복사하지 않고 필요한 사실을 구조화한다.
- 수수료·기간·운영시간처럼 변하는 정보는 확인일과 주의사항을 표시한다.
- 시민 화면 기관 정보는 공식 데이터만 사용한다.
- 데이터 수집/정제 변경 시 data version과 계보 문서를 갱신한다.

## Mock 규칙

- mock은 `is_mock=true` 또는 명확한 dataset 분류를 가진다.
- 시민 답변 근거 검색에서 제외한다.
- 화면에 `시연용 샘플` 배지를 표시한다.
- 실제 사용량·성과로 표현하지 않는다.

## KB 승인

- 세부 주제 단위 20건
- ACTIVE만 검색
- 사람 작성, 별도 사람 승인
- LLM이 source metadata를 만들지 않음
- 회귀용 침대 프레임 KB는 초기 ACTIVE에서 제외

## 버전

데이터 변경은 `versions/manifest.json`의 `official_data` 또는 `mock_data`를 갱신하고 구현 노트에 다음을 기록한다.

- 추가/수정/삭제 레코드 수
- 출처와 기준일
- 스키마 버전
- 재현 명령
- 영향받는 테스트
- 롤백 파일/마이그레이션
