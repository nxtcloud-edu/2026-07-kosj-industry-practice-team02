# ADR-0013: project-local patched Supabase CLI 공급망

- Status: Accepted; written spec approved, implementation plan review pending
- Date: 2026-07-17
- Deciders: 사용자, Codex
- Related: Q-SEC-006, D-031, A-024, ADR-0002/0007/0008/0011, DB-001 Task 10

## Context

stock Supabase CLI v2.109.1은 local database container의 `5432/tcp` publish 요청에
`HostPort`만 전달하고 `HostIP`를 생략한다. Docker Desktop 4.62.0/Engine 29.2.1에서 세
단계의 network/Desktop 보정을 적용해도 actual binding에 IPv6 wildcard `::`가 남았다.
동일 환경에서 `HostIP=127.0.0.1`을 명시한 control만 exact single loopback을 만들었다.
보안 gate 완화, 추가 전역 보정, DB runtime 장기 보류 중 하나를 결정해야 했다.

## Decision

사용자가 2026-07-17 `Q-SEC-006: A`를 명시적으로 선택했다. 공식 v2.109.1 Go CLI의 exact
tag/commit에서 local DB start binding의 `HostIP`만 `127.0.0.1`로 지정하는 최소 patch를
project-local 도구로 build한다.

- 상류 tag object `9d25ff8b5b0fba3c6f0ef000e7dd658c8d710c38`, peeled commit
  `6d4c19870ed213ba7f682f117d0345c8a40bfa94`를 고정한다.
- Go 1.25.11 Windows AMD64 official archive와 SHA-256
  `b7401f1b41517428e537493316256fb7cf03c66a130a0103ab07f3a2152e2112`를 고정한다.
- patch diff와 build inputs는 tracked source manifest로, 두 clean build가 일치한 binary
  SHA-256은 별도 tracked runtime manifest로 고정한다. 빈/TBD hash는 허용하지 않는다.
- stock CLI와 patched CLI를 별도 `.tools/` 경로에 두고 stock을 덮어쓰지 않는다.
- 공식 CI에서도 직접 실행하는 `apps/cli-go`만 build하며 Bun shell wrapper와 그 dependency는
  추가하지 않는다. official Go proxy/sumdb와 빈 private bypass를 강제하고 TDD,
  `go mod verify`, 두 independent checkout build의 hash 일치, exact version, actual Docker
  loopback 검증을 요구한다.
- 어떤 검증 실패도 reset, credential, SQL, schema version 승격 전에 fail closed한다.
- `db diff` shadow DB, 공개 API, DB migration/data, production dependency는 바꾸지 않는다.

상세 artifact 경계와 acceptance criteria는
`docs/superpowers/specs/2026-07-17-q-sec-006-patched-supabase-cli-design.md`가 권위다.

## Alternatives considered

- Docker network 전체를 IPv4-only로 추가 변경: 전역 영향이 크고 효과가 입증되지 않아 거부했다.
- 현 상태에서 DB runtime 보류: 안전 fallback과 rollback으로 유지하지만 기본 선택은 아니다.
- exact port gate 완화: IPv6 wildcard 공개를 허용하므로 거부했다.
- stock binary 덮어쓰기/PATH fallback: provenance와 rollback이 불명확해져 거부했다.
- `db diff` shadow DB까지 patch: 현재 승인된 DB-001 실행 경로 밖이므로 제외했다.

## Consequences

- local 개발 도구 공급망과 Go toolchain 유지보수 비용이 생긴다.
- 상류 CLI upgrade마다 patch applicability와 필요성을 다시 검토해야 한다.
- exact pinned binary를 사용해야 하므로 runner/tooling tests가 늘어난다.
- 공개 계약, schema/data, privacy, 비용 0원 원칙과 local/private 범위는 유지된다.
- A-021/Q-SEC-003 public-release blocker는 해결되지 않는다.

## Rollback

patched artifact 선택을 제거하고 DB runtime을 다시 fail-closed Blocked 상태로 둔다. stock CLI로
안전 gate를 우회하지 않는다. generated `.tools/` artifact는 재생성 가능하며 tracked
manifest/patch/bootstrap/runner 변경은 commit revert한다. DB migration이나 데이터 삭제는 없다.

## Validation gate

서면 설계 승인, `PLANS.md` 실행계획 승인, upstream Go test RED→GREEN, clean build 2회 hash
일치, exact binary pin, actual single `127.0.0.1:54322`, full DB gate와 repository regression을
모두 통과하기 전에는 DB-001 완료나 `database_schema=0.3.0-local` 승격을 선언하지 않는다.
