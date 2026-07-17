# Scripts

```bash
python scripts/new_implementation_note.py --title "제목" --task-id TASK-001 --type feature
python scripts/capture_repo_state.py
python scripts/check_scope_drift.py
python scripts/validate_codex_package.py
```

위 Python 유틸리티와 `scripts/tests/`의 저장소 경계 검사는 Python 표준 라이브러리만 사용한다.

## 단일 로컬 검증 gate

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1 -Offline
```

러너는 Windows PowerShell 5.1+, Node 24.12.0, pnpm 11.13.0, uv 0.11.28과 API venv Python 3.12.13을 먼저 확인한다. 이어 frozen pnpm/uv sync, root tests, Web lint/typecheck/test/synthetic-secret build, API format/lint/mypy/pytest, 계약 생성·diff·test, 두 secret scanner, package validator와 `git diff --check`를 fail-fast로 실행한다.

공개 옵션은 `-Offline` 하나뿐이다. 오프라인 모드는 warm cache를 요구하며 pnpm/uv offline을 강제한다. 성공·실패 하위 명령의 원문 출력은 비밀·경로 유출을 막기 위해 전달하지 않고 stable step ID만 표시한다. child 실패는 해당 종료코드를 보존하고, 버전·실행·복원 같은 운영 오류는 2를 반환한다. 러너 자체는 삭제와 서버 실행을 하지 않는다.

## 프로젝트 로컬 Supabase CLI

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1 -VerifyOnly
```

첫 명령은 고정된 공식 Windows amd64 release archive의 byte count와 SHA-256을 확인한 뒤
`.tools/supabase/v2.109.1/`에 프로젝트 로컬 CLI만 설치한다. 두 번째 명령은 다운로드 없이
설치된 실행 파일과 정확한 버전만 확인한다. 별도 archive를 검증하려면 첫 명령에
`-ArchivePath <zip>`을 추가한다.

이 CLI는 로컬 개발 도구이며 production dependency가 아니다. 스크립트는 Supabase `login`,
`link`, `db push` 또는 다른 remote project operation을 수행하지 않는다.

## 로컬 PostgreSQL gate

Supabase v2.109.1이 생성한 프로젝트는 DB-001에 필요한 로컬 PostgreSQL 경로만 실행한다.
Data API, Auth, Realtime, Storage, Studio, Local SMTP/Mailpit, Analytics, Edge Runtime과 DB pooler는
비활성화했다. DATA-001의 PM 승인 전까지 seed는 의도적으로 비어 있다.

DB-001의 6개 version migration/compensation과 6개 pgTAP suite가 존재하며 다음
Docker-backed gate가 executable local baseline을 검증한다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart
```

기본 경로는 Docker Engine 28+와 고정 `sejong-ai-local-loopback` network를 확인한 뒤 pinned
CLI의 `db start --network-id sejong-ai-local-loopback`을 runner 내부에서 호출한다. bare/direct
Supabase start는 runner의 actual binding 검증을 우회하므로 사용하지 않는다. runner는 고정
project/container identity와 HostConfig 요청, actual `NetworkSettings.Ports`의 exact single
`127.0.0.1:54322`를 reset/status/env 전에 검증한다. `supabase test db`가 pgTAP 실행 중 일회성 `pg_prove` container를
사용할 수 있지만, 이는 persistent project runtime의 PostgreSQL-only 경계를 넓히지 않는다.

`-SkipStart`는 이미 실행 중인 disposable local PostgreSQL container를 재사용한다.
`-SkipRollbackReplay`는 진단 중 compensation/replay 증명만 생략하므로 완료 gate가 아니다.
러너는 child 출력을 숨기고, 임시 process 환경변수를 복원하며, stable phase ID만
출력한다. 안전하지 않은 새 runtime은 fail-closed 정지하되 pre-existing/`-SkipStart` runtime과
Docker volume은 변경하지 않는다. 완료 조건은 exact loopback 뒤 pgTAP 6 files/282 assertions,
exact six-stage rollback/absence/reset/replay와 backend integration 8/8의 fresh 재검증이다.

현재 Docker Desktop 4.62.0/Engine 29.2.1은 optioned network에서도 stock CLI의 HostIP 생략을
wildcard binding으로 해석했다. runner는 reset 전에 fail-closed했고 stack은 중지돼 project
container count 0이다. runner가 새 runtime을 시작한 경우에는 `db start`가 일부 생성 뒤 실패하거나
post-start binding 검증이 실패해도 해당 project stack을 중지하고 container 부재를 확인한다. 기존
runtime이나 `-SkipStart` 경로는 자동 중지하지 않는다. Q-SEC-004=A의
`default-local-port-binding`과 Q-SEC-005=A의 `local-only-port-binding` 적용 뒤에도 HostIP
미지정 probe가 `127.0.0.1`+`::`를 만들었으므로 Q-SEC-006/A-024 해결 전 실제 DB gate를
반복하거나 우회하지 않는다.
[Docker published ports](https://docs.docker.com/engine/network/port-publishing/)와
[Supabase local development](https://supabase.com/docs/guides/local-development/)를 따른다.

credential provisioning은 Supabase status의 admin DSN을 runner process memory/environment에서만 사용하고
`sejong_local_login`을 생성하거나 password를 회전한 다음 `sejong_backend` capability만
부여한다. 무시된 `apps/api/.env` 전체 bytes를 읽어 `DATABASE_URL`만 원자 갱신하고
주석·순서·다른 provider 값을 파싱하지 않은 채 byte-identical하게 보존한다. 이 파일은
commit하지 않는다.

ordered SQL helper는 resolve 결과가 `database/` 안에 남는 명시적인 파일만 받는다.
disposable local DB-001 compensation과 absence proof에만 사용하며 remote나 실제 데이터 DB에
파괴적 SQL을 실행하라는 승인이 아니다.

선택적 local stop은 `.\.tools\supabase\v2.109.1\supabase.exe stop`을 사용한다. volume
삭제·prune은 하지 않는다. local stack은 기본 개발 credential과 TLS/rate-limit 부재를
전제로 하므로 공개하지 않는다. A-021/Q-SEC-003 default B에 따라 `00700`은 만들지 않고
remote/public 배포·public admin/API·public backend DB credential을 차단한다.

## 보안 경계 검사

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
node scripts/check_web_bundle_secrets.mjs apps/web/.next
```

첫 명령은 Windows PowerShell 5.1 호환 저장소 secret pattern 검사이고, 두 번째 명령은 Node
표준 라이브러리만 사용하는 browser artifact 검사다. 둘 다 clean 0, leak 1, 입력 누락·읽기
실패 같은 운영 오류 2 이상을 반환하며 출력에는 경로·stable rule ID·개수만 포함한다. 검사
범위와 제외 대상, 보장하지 않는 항목은 `SECURITY.md`를 따른다. secret assignment 검사는
일반/`export`, PowerShell `$env:NAME=value`, cmd `set NAME=value` 형식을 포함하지만 등호 없는
`setx NAME value`는 현재 P2 한계로 탐지하지 않는다.
