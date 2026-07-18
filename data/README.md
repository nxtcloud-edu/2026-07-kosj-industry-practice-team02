# Data directories

- `official/`: 사람 승인 뒤의 immutable release와 source registry만 둔다. 현재 official release/seed는 0건이다.
- `staging/`: DATA-001의 미승인 공식 데이터 초안이다. 현재 `0.1.0-draft.1`은 KB 20·office 3·mapping 12와 validator PASS 상태지만 PM review KEEP이며 시민 검색·seed·readiness에 사용할 수 없음
- `schemas/`: staging artifact를 위한 내부 데이터 계약
- `evaluation/`: 표본 20개와 회귀 케이스
- `mock/`: 시연용, 공식 답변 근거 사용 금지
- `processed/`: 스크립트 재현 산출물
- `legacy/`: 이전 seed, 비권위
