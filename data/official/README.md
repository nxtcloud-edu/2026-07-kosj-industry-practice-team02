# Official data

`kb_source_registry.csv`는 20개 KB 후보의 출처 관리대장이다. DATA-001의 canonical 20
KB·3 office·12 mapping과 `PM-LOCAL-001`의 35개 최종 disposition은
`data/staging/data-001/0.1.0-draft.1/`에 있다.

`releases/0.1.0-initial.1/`은 historical predecessor이고,
`releases/0.1.0-initial.2/`는 같은 승인 projection 19 KB·3 office·10 mapping에 PostgreSQL 17
effective membership-option union guard를 적용한 게시·검증된 immutable successor다.
`KB-WASTE-03`과 반려 mapping 2건은 두 release 모두에서 제외됐다. 현재
`supabase/seed.sql`은 `.2` release seed와 byte-identical하지만 `[db.seed].enabled=false`이다.

초기 actual 실행에서 확인한 concurrency observer 문제를 OID equality로 교정한 뒤 지원된
disposable PostgreSQL 전체 cycle이 통과했다. `.2`는 ACTIVE 19·공식 기관 3·승인 매핑 10으로
seed·최종 membership·rollback/replay·cleanup 검증됐고 manifest의
`official_data=0.1.0-initial.2`가 현재 기준선이다. 자동 seed는 계속 비활성이고 `.1`과 `.2`
byte는 수정·삭제하지 않는다. 상세 hash·시도·cleanup·다음 gate는 공개 snapshot에 포함된
[`DATA-SEED-002-0.1.0-initial.2.md`](../../docs/data-lineage/DATA-SEED-002-0.1.0-initial.2.md)를
따른다. 원본 저장소의 내부 실행 보고서는 평가 snapshot에서 제외했다.
