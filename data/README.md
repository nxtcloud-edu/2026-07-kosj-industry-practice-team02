# Data directories

- `official/`: 사람 승인 뒤의 immutable release와 source registry만 둔다. 현재 PM 승인 projection은 19/3/10이지만 DATA-SEED 실행계획 승인 전이므로 official release/seed는 0건이다.
- `staging/`: DATA-001의 공식 데이터 authoring·승인 증거다. `0.1.0-draft.1`은 KB 20·office 3·mapping 12, `PM-LOCAL-001`의 35개 disposition과 validator PASS 상태다. staging 자체는 시민 검색·seed·readiness에 사용할 수 없음
- `schemas/`: staging artifact를 위한 내부 데이터 계약과 DATA-001 exact source/content/audit hash 승인 매트릭스. DATA-SEED release schema는 승인된 실행계획 구현 뒤 추가한다.
- `evaluation/`: 표본 20개와 회귀 케이스
- `mock/`: 시연용, 공식 답변 근거 사용 금지
- `processed/`: 스크립트 재현 산출물
- `legacy/`: 이전 seed, 비권위
