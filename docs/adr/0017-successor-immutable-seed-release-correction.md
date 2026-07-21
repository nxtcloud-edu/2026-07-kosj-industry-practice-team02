# ADR-0017: successor immutable seed release로 membership guard 교정

- Status: Accepted; immutable `.2` published, actual database verification Blocked
- Date: 2026-07-20
- Deciders: 사용자, Codex
- Related: Q-SEED-002, D-044, A-030, ADR-0015, ADR-0016, DATA-SEED-002

## Context

`0.1.0-initial.1`은 PM이 승인한 19 KB·3 offices·10 mappings를 담은 불변 filesystem
release로 게시됐다. 그러나 실제 disposable PostgreSQL 17 cycle은 seed write 전에 멈췄다.
DB migration은 같은 role/member 쌍에 대한 grantor별 membership row 전체에서 ADMIN,
INHERIT, SET option을 세 독립 `EXISTS`로 확인한다. 현재 pgTAP은 실제 두-row catalog를
통과하지만 `INHERIT+SET`을 같은 row에 묶어 검사한다. `.1` seed와 compensation은 세 option이
한 row에서 동시에 true이고 row count도 정확히 1일 때만 통과한다. 실제 안전한 local catalog는
두 grantor row에 option이 나뉘어 있어 migration 권위와 `.1`이 충돌한다.

게시된 `.1` byte를 수정하면 불변 release 원칙과 당시 실패 증거를 모두 훼손한다. 반대로
role/grant를 한 row로 정규화하면 platform privilege state와 migration lineage를 바꾸므로
교정 범위가 과도해진다.

## Decision

Q-SEED-002 선택지 A를 채택한다.

1. 기존 migration의 세 독립 `EXISTS` effective-option union을 권위로 유지한다. successor
   실행에서 현재 pgTAP의 narrower predicate를 같은 의미로 정렬하되 assertion count와 runtime
   DB object는 바꾸지 않는다.
2. `.1`의 release 7개 파일과 `data/schemas/data-seed/v1/` 4개 schema byte를 수정·삭제하지
   않는다.
3. 같은 PM 승인 artifact와 동일한 19/3/10 seed-owned projection으로 새 immutable
   `0.1.0-initial.2`를 만든다. `KB-WASTE-03`, 거절 mapping 2건과 mock은 계속 제외한다.
4. `.2` manifest는 `schema_version=2`, `release_id=sejong-official-0.1.0-initial.2`,
   `generator=data-seed-release-v2`, governance decision time
   `2026-07-20T11:41:24Z`를 사용한다. source approval identity와 byte는 그대로
   `PM-LOCAL-001` 및 기존 approval manifest SHA-256에 묶는다.
5. 새 `data/schemas/data-seed/v2/`가 `.2`의 strict schema authority다. v1 schema는
   historical `.1` 검증용으로 보존한다.
6. seed와 compensation은 principal, database, role switch, advisory/table lock, empty or
   exact-projection guard를 그대로 유지한다. membership만 같은 exact role/member 쌍에서
   `admin_option`, `inherit_option`, `set_option` 각각을 만족하는 row가 하나 이상 존재하는지
   독립적으로 확인한다. grantor 이름이나 row count를 제한하지 않는다.
7. `.2` 후보는 byte 재생성, v1 immutability fingerprint, v2 strict schema, 19/3/10 count,
   excluded/mock 0, 동일 semantic SHA-256과 독립 기술 검토를 통과한 뒤에만 create-once로
   게시한다. 기술 검토는 exact candidate diff와 hash에 대한 별도 agent의
   Critical/Important 0 판정이며 기존 사람의 source/data 승인을 대체하지 않는다.
8. dispatcher는 현재 `.1` seed byte 또는 이미 활성화된 `.2` byte만 predecessor로 인정한다.
   `.1 → .2`는 원자 교체하고 실패 시 exact `.1`로 복구한다. `[db.seed].enabled=false`는
   유지한다.
9. 게시 뒤에도 실제 supported runner의 전체 failure rollback, concurrency A/B, seed,
   second-seed rejection, compensation guard, compensation, six-migration replay, final
   projection/citizen-read를 처음부터 다시 통과하기 전에는 `official_data`를 올리지 않는다.
10. 최초 D-044는 written specification과 plan 작성까지만 승인했다. 이후 Q-MVP-001=A/D-058의
    `즉시 실행` 지시가 local `.2`, dispatcher와 disposable DB 실행을 승인했다. actual 전체 PASS
    전 official-data 승격과 public/remote 실행은 계속 금지한다.

## Current execution status

- Immutable `0.1.0-initial.2`, strict v2 schemas and the byte-identical local dispatcher were
  published and verified after independent technical review. Historical `.1`/v1 bytes remain exact.
- Three supported actual local DB runs passed baseline, identity, forced rollback and concurrency A,
  then stopped at concurrency B. The bounded diagnostic run returned exact stable reason
  `CAPABILITY_WRITE_DID_NOT_BLOCK`; cleanup passed and restored exact-owned container/listener 0.
- Seed-cycle, PostgreSQL 19/3/10 counts, citizen-visible ACTIVE 19, final semantic hash and READY were
  not reached and are not claimed. `official_data=0.0.0-not-populated` and `/ready=503` remain.
- Static diagnosis found a search-path-sensitive relation-name observer. Its OID-equality correction
  `eb74ac8` passed 25/25 tests and independent Critical/Important/Minor `0/0/0` review, then was
  committed. This ADR does not authorize another actual run; a separate execution decision is still
  required. Non-DB MVP lanes may continue independently.

## Rejected alternatives

### B — grantor-specific membership를 한 row로 정규화

`.1` guard와 맞출 수 있지만 PostgreSQL platform role/grant state, 새 migration,
compensation, pgTAP, replay와 public security review를 추가한다. 데이터 release의 guard
불일치를 해결하기 위해 더 넓은 전역 권한 상태를 바꾸므로 선택하지 않았다.

### `.1` in-place 수정

불변 release와 실제 실패 lineage를 파괴하므로 금지한다.

### Python verifier만 완화

immutable SQL 자체가 같은 catalog에서 실패하므로 문제를 해결하지 못한다.

## Consequences

- DB schema, role/grant, migration, public API, application behavior와 production dependency는
  이 correction으로 바뀌지 않는다.
- `.1`과 `.2`는 함께 보존된다. `.1`은 historical failed-import artifact, `.2`는 corrected
  successor다.
- 데이터 내용과 `seed_semantic_sha256`은 같아야 하지만 release JSON/SQL/manifest byte hash는
  version과 guard가 달라 새 값이어야 한다.
- actual cycle이 모두 통과하면 `official_data=0.1.0-initial.2`로 승격할 수 있다. 현재 세 실행은
  concurrency B에서 Blocked이므로 승격하지 않는다. `/ready=200` 전환은 별도 READY-001이
  소유하므로 계속 503이다.
- local/private actual DB cycle만 허용한다. Q-SEC-003의 `00700` 구현과 public deployment는
  별도 gate다.

## Rollback and recovery

- publish 전 실패: owned prepare directory만 제거하고 `.1`과 dispatcher를 보존한다.
- dispatcher 교체 실패: captured identity와 byte를 확인한 exact `.1` quarantine만 복원한다.
- seed/compensation 실패: 한 transaction rollback과 empty/exact guards로 partial row 0을
  확인한다.
- `.2`가 정상 게시된 뒤에는 삭제하거나 수정하지 않는다. 새 결함은 `.3` successor로
  교정한다.
- actual DB cycle 성공 전 문서 결정을 철회하더라도 게시된 `.1`과 `.2` byte는 그대로 둔다.
  교정이 필요하면 별도 승인된 immutable `.3`를 만든다.

## Validation

- `.1` release 7개와 v1 schema 4개 SHA-256/length immutability gate
- effective option union split-row positive, missing ADMIN/INHERIT/SET 각각 negative
- seed와 compensation guard parity
- `.2` deterministic regeneration, strict schema, approval hash, counts/exclusions/mock 0
- `.1 → .2` dispatcher atomic replace/rollback/race/reparse tests
- full no-Docker root gate and supported disposable local actual DB cycle
- independent specification and code-quality review before version promotion
