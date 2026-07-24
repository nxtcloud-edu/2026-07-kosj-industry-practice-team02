# ADR-0018: public 준비 시 privileged function search path 전수 보정

- Status: Accepted; implementation explicitly deferred until public preparation
- Date: 2026-07-20
- Deciders: 사용자, Codex
- Related: Q-SEC-003, D-046, A-021, ADR-0012, DB-001-A021 audit

## Context

read-only audit는 privileged execution graph를 `app_api` SECURITY DEFINER 9개와
중첩/helper/trigger `app_private` 13개, 합계 22개로 고정했다. `00600`이
`app_private.validate_active_kb_question()` 하나만 `search_path=pg_catalog, pg_temp`로
보정해 나머지 21개는 `pg_catalog` 단독이다. application relation/helper는 qualified이고
dynamic SQL은 0이지만, PostgreSQL 17의 안전한 SECURITY DEFINER 작성 지침을 public 경계에서
충족했다고 볼 수 없다.

## Decision

Q-SEC-003 선택지 A를 채택하되 실행 시점을 public 준비 단계로 명시적으로 보류한다.

- 새 forward migration `00700`은 audit에 기록된 exact 22 signature allowlist만 대상으로 한다.
- 함수 body, owner, signature, ACL, table, data와 public API는 바꾸지 않고 function property의
  `search_path`만 정확히 `pg_catalog, pg_temp`로 통일한다.
- matching compensation과 exact catalog/ACL/body fingerprint/behavior/compensation/replay
  regression을 함께 구현한다.
- 구현 전 별도 public-preparation spec, DB migration 승인, 실행계획 승인을 받는다.
- 그때까지 local/private demo는 허용하지만 remote/public 배포, public admin/API,
  public backend DB credential은 계속 차단한다.

## Alternatives considered

- 현재 posture를 영구 유지: local 범위에는 가능하지만 public 배포를 계속 막으므로 최종
  방향으로 선택하지 않았다.
- 함수 body rewrite 또는 TEMP revoke: property-only 최소 변경보다 영향 범위가 넓어 별도
  증거와 인간 승인이 없으면 수행하지 않는다.

## Consequences

결정은 확정됐지만 property-only public 준비 migration `00700`은 여전히 구현하지 않았다.
후속 local 기능을 포함한 현재 executable 기준선은 `00100`~`00670` 아홉 개,
`database_schema=0.4.0-local`, pgTAP 9 files/356 assertions다. public readiness는
`00700` 구현·검증과 별도 배포 승인이 모두 끝날 때까지 Blocked다.

## Rollback

구현 전에는 이 ADR/결정 문서만 revert한다. 구현 후에는 적용된 `00700`을 수정하지 않고
승인된 matching compensation 또는 후속 forward migration을 사용한다.
