# ADR-0014: Windows patched CLI short checkout roots

- Status: Accepted; revised implementation plan awaiting user approval
- Date: 2026-07-18
- Deciders: 사용자, Codex
- Related: Q-TOOL-001, D-032, A-025, ADR-0013, DB-001 Task 10
- Amends: ADR-0013의 generated source checkout workspace만 변경

## Context

ADR-0013에 따라 official Supabase CLI v2.109.1 exact source를 두 independent checkout에서
검증·patch·build했다. repository-local `core.longpaths=true`를 적용한 checkout 자체는 성공했지만,
재실행 전 PowerShell 5.1 `Remove-Item -Recurse -Force`가 기존 source A에서 `.git`만 제거한 뒤
tracked tree를 남기고 실패했다. Extended-length read-only 열거 결과 source A에는 3,035 files가
남았고 가장 긴 absolute file path는 299자였다. 같은 exact tree를 `.tools/s/a`에 투영하면 최대
244자다.

다음 중 인간 결정이 필요했다.

- A: checkout만 `.tools/s/{a,b}`로 단축한다.
- B: Win32 extended-length recursive delete를 새로 구현한다.
- C: Docker/WSL Linux build workspace로 전환한다.

## Decision

사용자가 2026-07-18 `Q-TOOL-001: A`를 명시적으로 선택했다.

- 두 checkout은 정확히 `.tools/s/a`, `.tools/s/b`를 사용한다.
- source manifest가 tool-root-relative checkout `s/a`, `s/b`, pinned upstream tree의 최대 relative
  file path 134자, 허용 absolute file path 상한 248자를 고정한다.
- bootstrap은 checkout 생성·cleanup, Go archive download/extraction, network fetch 전에 각
  destination의 projected maximum absolute file path를 계산하고 248자를 넘으면 stable failure로 중단한다.
- `Remove-OwnedPath`의 safe-child/reparse 검증과 PowerShell 5.1 삭제 primitive는 유지한다.
  Win32 native delete, global Git setting, sparse checkout, path exclusion을 추가하지 않는다.
- 기존 ignored `.tools/supabase-source/6d4c19870ed213ba7f682f117d0345c8a40bfa94/`
  partial tree는 새 bootstrap이 checkout/build input으로 사용하거나 자동 삭제하지 않는다. 별도 human-approved cleanup 전까지
  격리된 재생성 artifact로 기록한다.
- official tag/commit, patch, Go/archive/hash, two-build binary hash, stock CLI, actual Docker loopback와
  full DB gates는 모두 그대로 유지한다.

248자 상한은 Windows의 보수적인 directory/path 운용 한계 안에서 현재 244자 tree에 4자 여유를
제공한다. 향후 upstream identity를 바꾸려면 pinned maximum relative length를 다시 산출·검토하고,
현재 workspace에서 projected path gate를 통과해야 한다.

## Alternatives considered

- Win32 extended-length recursive delete: 기존 tree를 직접 정리할 수 있지만 파괴적 native helper,
  reparse/readonly/partial-failure 보안 표면이 커서 거부했다.
- Docker/WSL build root: Windows 장경로를 피하지만 image/digest/mount/output permission 공급망과
  추가 다운로드를 만들어 local-first 0원 경계를 복잡하게 하므로 거부했다.
- guard 완화·global long-path 설정·sparse checkout: 승인된 exact source와 fail-closed cleanup 경계를
  약화하므로 거부했다.

## Consequences

- source manifest, bootstrap path assertions와 tooling tests가 함께 바뀐다.
- 현재 exact worktree에서 projected maximum은 244자지만 repository root가 더 긴 환경에서는
  checkout 전에 명시적으로 실패할 수 있다.
- 기존 long-path artifact는 disk space를 계속 사용하지만 product/runtime authority가 아니며 어떤
  runner도 참조하지 않는다.
- 공개 API, DB schema/migration/data, privacy, DeepSeek, production dependency, Docker Desktop 설정,
  remote/public deployment는 변하지 않는다.

## Rollback

Task 2C commit을 revert하고 DB runtime을 fail-closed Blocked 상태로 둔다. stock CLI나 기존 long
checkout을 fallback으로 사용하지 않는다. `.tools/s/{a,b}`는 safe-child/path-budget 검증 뒤
재생성할 수 있다. 기존 `.tools/supabase-source/...` tree는 이 rollback에서도 자동 삭제하지 않는다.

## Validation gate

수정 spec/plan 승인, manifest schema RED→GREEN, 두-root main preflight ordering, synthetic 244/248
acceptance·249 rejection, exact 248-character cleanup, short-root junction sentinel, direct/reparse
`.tools/s` archive override, legacy-root deny-only tests, full patched 23/23와 stock 7/7 tooling regression,
independent review를 먼저 통과한다. 그 뒤에만
Task 3의 two-build hash/runtime pin을 재개한다. actual single `127.0.0.1:54322`, full DB/root gate와
independent review 전에는 DB-001 완료나 `database_schema=0.3.0-local`을 선언하지 않는다.
