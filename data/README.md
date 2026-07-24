# Data directories

- `official/`: 사람 승인 뒤의 immutable release와 source registry만 둔다. 현재 정식 release
  `0.1.0-initial.2`는 ACTIVE KB 19개·공식 기관 3개·승인 매핑 10개이며 local DB seed·최종
  membership 검증을 통과했다. `[db.seed].enabled=false`이므로 migration reset과 정식 seed는
  의도적으로 분리한다. 계보는 `docs/data-lineage/DATA-SEED-002-0.1.0-initial.2.md`를 따른다.
- `staging/`: DATA-001의 공식 데이터 authoring·승인 증거다. `0.1.0-draft.1`은 KB 20·office 3·mapping 12, `PM-LOCAL-001`의 35개 disposition과 validator PASS 상태다. staging 자체는 시민 검색·seed·readiness에 사용할 수 없음
- `schemas/`: staging artifact와 immutable DATA-SEED release를 위한 내부 데이터 계약,
  DATA-001 exact source/content/audit hash 승인 매트릭스.
- `evaluation/`: 표본 20개와 회귀 케이스
- `mock/`: 시연용, 공식 답변 근거 사용 금지
- `processed/`: 데이터 검증 테스트가 요구하는 canonical PM 검토 패킷·검증 보고서만 포함한다.
  그 밖의 재생성 가능한 산출물은 공개 snapshot에서 제외한다.
