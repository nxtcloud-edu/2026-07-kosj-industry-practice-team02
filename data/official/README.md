# Official data

`kb_source_registry.csv`는 20개 KB 후보의 출처 관리대장이다. DATA-001의 canonical 20
KB·3 office·12 mapping과 `PM-LOCAL-001`의 35개 최종 disposition은
`data/staging/data-001/0.1.0-draft.1/`에 있다.

`releases/0.1.0-initial.1/`은 historical predecessor이고,
`releases/0.1.0-initial.2/`는 같은 승인 projection 19 KB·3 office·10 mapping에 PostgreSQL 17
effective membership-option union guard를 적용한 게시·검증된 immutable successor다.
`KB-WASTE-03`과 반려 mapping 2건은 두 release 모두에서 제외됐다. 현재
`supabase/seed.sql`은 `.2` release seed와 byte-identical하지만 `[db.seed].enabled=false`이다.

지원된 actual disposable PostgreSQL 실행 3회는 baseline·identity·failure rollback·concurrency A를
통과한 뒤 모두 concurrency B에서 멈췄다. bounded diagnostic이 확인한 exact reason은
`CAPABILITY_WRITE_DID_NOT_BLOCK`이며 마지막 두 실행의 cleanup은 PASS했다. 따라서 PostgreSQL
ACTIVE 19·READY·AI 승격은 주장하지 않고 `official_data=0.0.0-not-populated`를 유지한다.
search-path-sensitive relation-name observer를 OID equality로 바꾼 `eb74ac8`은 독립 검토
0/0/0과 commit까지 끝났지만 추가 actual 실행은 아직 승인되지 않았다. `.1`과 `.2` byte는
수정·삭제하지 않는다. 상세
hash·시도·cleanup·다음 gate는
[`DATA-SEED-002-0.1.0-initial.2.md`](../../docs/data-lineage/DATA-SEED-002-0.1.0-initial.2.md)와
[`DATA-SEED-002-LOCAL-VERIFICATION.md`](../../docs/test-reports/DATA-SEED-002-LOCAL-VERIFICATION.md)를
따른다.
