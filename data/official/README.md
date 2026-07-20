# Official data

`kb_source_registry.csv`는 20개 KB 후보의 출처 관리대장이다. DATA-001의 canonical 20
KB·3 office·12 mapping과 `PM-LOCAL-001`의 35개 최종 disposition은
`data/staging/data-001/0.1.0-draft.1/`에 있다.

`releases/0.1.0-initial.1/`은 승인 projection 19 KB·3 office·10 mapping을 담은 게시·검증된
create-once filesystem release다. `KB-WASTE-03`과 반려 mapping 2건은 제외됐다. release
`seed.sql`과 `supabase/seed.sql`은 byte-identical이지만 `[db.seed].enabled=false`이다.

Actual disposable PostgreSQL 검증은 seed write 전, migration의 grantor별
ADMIN/INHERIT/SET effective union과 불변 `.1` SQL의 single-row guard 충돌로 Blocked다. 현재
pgTAP은 관측된 두-row 상태는 통과하지만 `INHERIT+SET`을 같은 row에 묶어 검사하므로 후속
계획에서 migration의 세 독립 `EXISTS` 의미로 정렬한다. 그러므로
DB의 citizen-visible ACTIVE row·READY·AI는 승격되지 않았고 `official_data`는
`0.0.0-not-populated`다. `.1` byte는 수정·삭제하지 않는다. Q-SEED-002=A/D-044는 같은 승인
projection을 immutable `.2` effective-union successor로 보정하는 방향을 확정했다. 명세·계획은
Review이며 후속 plan 승인 전 `.2`를 생성하지 않는다. 상세 hash·시도·cleanup·보정 정책은
[`DATA-SEED-001-0.1.0-initial.1.md`](../../docs/data-lineage/DATA-SEED-001-0.1.0-initial.1.md)를
따른다.
