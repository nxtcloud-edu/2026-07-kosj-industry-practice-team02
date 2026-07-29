# Data directories

- `official/`: 사람 승인 뒤의 immutable release와 source registry만 둔다. `0.1.0-initial.1`
  filesystem release는 19 KB·3 office·10 mapping으로 게시·검증됐고 `supabase/seed.sql`은 release
  seed와 byte-identical이다. 단 `[db.seed].enabled=false`이고 actual DB import는 write 전 membership guard
  계약 충돌로 Blocked다. 따라서 citizen-visible ACTIVE row·READY·AI 승격은 없고
  `official_data=0.0.0-not-populated`를 유지한다. 계보는
  `docs/data-lineage/DATA-SEED-001-0.1.0-initial.1.md`를 따른다.
- `staging/`: DATA-001의 공식 데이터 authoring·승인 증거다. `0.1.0-draft.1`은 KB 20·office 3·mapping 12, `PM-LOCAL-001`의 35개 disposition과 validator PASS 상태다. staging 자체는 시민 검색·seed·readiness에 사용할 수 없음
- `schemas/`: staging artifact와 immutable DATA-SEED release를 위한 내부 데이터 계약,
  DATA-001 exact source/content/audit hash 승인 매트릭스.
- `evaluation/`: 표본 20개와 회귀 케이스
- `mock/`: 시연용, 공식 답변 근거 사용 금지
- `processed/`: 스크립트 재현 산출물
- `legacy/`: 이전 seed, 비권위
