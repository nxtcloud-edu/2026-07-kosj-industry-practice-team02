# SECURITY.md

## 민감정보 보고

이 실습 저장소에는 실제 시민 개인정보, 실제 운영 비밀키, 실제 기관 내부자료를 올리지 않는다. 발견 시 즉시 커밋/배포를 중단하고 노출 범위를 확인한다. 비밀값은 회수·교체하고 Git 이력 정리가 필요한지 인간 책임자에게 보고한다.

## 금지 사항

- `.env`, API 키, Supabase service-role key 커밋
- 실제 주민등록번호·전화·상세주소·접수번호를 test fixture에 사용
- 질문 원문을 로그/DB/오류 추적에 기록
- LLM이 생성한 출처를 공식 근거로 표시
- 승인되지 않은 KB를 시민 답변에 노출
- mock 기관 정보를 실제처럼 표시
- private GitHub·Issue·PR·Actions artifact·Codex Cloud에 local env/secret/시민 원문 업로드
- Codex Cloud에서 DeepSeek 실호출, remote DB mutation 또는 자기 PR merge

## 보안 관련 변경

마스킹, 로그, 권한, 보관기간, 외부 LLM, CORS, 배포 비밀, DB RLS/권한 변경은 반드시 인간 승인을 받고 ADR 또는 결정 로그를 남긴다.

자세한 정책은 `docs/07_SECURITY_PRIVACY.md`와 `docs/source-of-truth/PRIVACY_POLICY.md`를 따른다.

## GitHub·Codex Cloud 경계

- 원격 최초 push 전 current worktree와 전체 reachable Git history를 서로 다른 값 비노출 검사기로
  검사한다. history scanner의 local 통합·독립 review·fresh PASS는 완료됐지만, 이후 commit이 생기면
  최초 remote 생성/push 직전에 두 검사를 다시 실행한다.
- 확인된 secret은 파일 삭제 commit만으로 닫지 않고 먼저 회전하며 history 정리는 인간 승인을
  받는다.
- private repository는 노출 가능성을 줄일 뿐 secret/PII 커밋을 허용하지 않는다.
- Codex GitHub App은 selected repository 하나만 허용하고 Cloud에는 DeepSeek key, DB DSN,
  context-token secret을 등록하지 않는다.
- Actions 권한은 `contents: read` 기본이며 `pull_request_target`으로 untrusted PR code를 실행하지
  않는다. workflow action은 공식 출처의 검토된 commit SHA로 고정한다.
- Frontend 팀원의 self-merge는 협업 정책이지 GitHub Free의 강제 보안 경계가 아니다. contract,
  backend, DB/migration, official/staging data, security/privacy, dependency/lockfile 변경은 owner
  review로 승격한다.
- GitHub source remote는 application deployment나 DB backup이 아니다. ignored env·Docker state·
  local logical dump는 GitHub에 올리지 않는다.

## 환경변수와 로그 경계

- root `.env.example`은 안내만 제공한다. Web은 `apps/web/.env.example`을
  `apps/web/.env.local`로, API는 `apps/api/.env.example`을 `apps/api/.env`로 복사한다.
- Web 템플릿은 승인된 브라우저 공개값 한 개만 포함한다. DB·provider·서명 비밀은 API
  환경에만 두고 예제의 민감 필드는 비워 둔다.
- API 요청 로그의 allowlist는 서버 생성 `request_id`, method, 라우트 템플릿 path,
  status뿐이다. 미매칭 경로는 `<unmatched>`로 기록한다.
- request body·query·header·cookie·Authorization·client IP·답변·provider/DB 상세는
  app/access/error log에 넣지 않는다. `uvicorn.access`, raw `uvicorn.asgi` trace와
  client 주소를 포함할 수 있는 `uvicorn.error`의 INFO 미만 protocol record 및 고정 WebSocket
  INFO protocol record를 차단한다. WebSocket은 현재 범위 밖이므로 Uvicorn은
  `--no-access-log --ws none`으로 실행한다.

## 로컬 비밀 검사

저장소 루트에서 다음을 실행한다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File trusted/scripts/check_secret_patterns.ps1 `
  -RepositoryRoot candidate
python -B scripts/check_git_history_secrets.py --repo .
node scripts/check_web_bundle_secrets.mjs apps/web/.next
```

첫 명령은 현재 repository, 두 번째 예시는 trusted base의 scanner로 별도 checkout한 candidate
repository를 검사한다. `-RepositoryRoot`는 요청 경로가 정확한 Git top-level인지 확인한 뒤 그
candidate의 tracked + untracked nonignored regular file만 읽고 reparse point/symlink와 제외 runtime
directory는 건너뛴다. Git discovery 출력은 32 MiB로 제한되며 한도·root 불일치·읽기 실패는 exit
2로 fail closed한다. current-tree와 bundle scanner는 clean 0, finding 1, operational error 2 이상을
반환한다. 출력은 escaped 경로·stable rule ID·개수만 포함하며 일치한 값이나 파일 내용을 출력하지
않는다.

history scanner는 `git rev-list --objects --all`의 reachable commit/tree/tag/blob raw bytes를 검사한다.
선택한 ignored local secret을 exact 비교할 때도 값은 process memory에만 두며 Git argv/env·임시 파일·
출력으로 전달하지 않는다. clean 0, finding 1, operational/limit failure 2이고 출력은 값 없는 JSON
Lines metadata뿐이다. 고정 한도는 reachable object 100,000개, object당 16 MiB/합계 256 MiB,
Git 출력당 64 MiB, unique tree 20,000개, tree entry 1,000,000개, path 4,096 bytes/합계 128 MiB,
Git 명령당 60초다. 한도 초과는 불완전 clean으로 간주하지 않는다.

current-tree 패턴 검사는 명백한 private-key header, provider/GitHub token, AWS access-key ID, 승인된
secret assignment, credential URL을 찾지만 엔트로피 분석·Git 과거 이력·프로세스 환경·클라우드
로그까지 검사하지 않는다. 과거 이력은 별도 history scanner의 명시 패턴/exact-value 경계만 맡는다.
assignment 검사는 일반/`export`, PowerShell `$env:NAME=value`, cmd `set NAME=value` 형식을 포함한다.
등호가 없는 `setx NAME value`는 P2 한계로 탐지하지 않는다. 기본 저장소 검사는 active tracked/
untracked nonignored 파일만 대상으로 하고 legacy·cache·build·quarantine과 symlink는 제외한다.

번들 검사는 build 시 materialize된 `.next/static`, app HTML/RSC, pages HTML에서 server secret
marker 이름과 선택적 `SEJONG_WEB_SECRET_SENTINEL` 값의 byte literal을 찾는다. 서버 전용
JavaScript·cache, 동적 RSC/HTML live response와 Pages `_next/data/*.json` runtime 경로는 보증하지
않는다. WEB-CHAT/DEV-001D에서 live-response sentinel gate를 추가해야 한다. current-tree,
history, bundle scanner 모두 분할·암호화·압축·난독화·인코딩된 값의 부재를 보증하지 않으므로
credential 회수/회전, GitHub 접근 검토, provider 설정 확인과 배포 전 수동 보안 검토를 대체하지
않는다.

## Local PostgreSQL 안전 경계

- DB-001은 project-local patched Supabase CLI `2.109.1`의 exact loopback/full gate를 통과한
  disposable `0.3.0-local` 기준선이다. stock CLI와 Q-SEC-004/005의 Docker 전역 설정은 IPv6
  wildcard를 남겼으므로 DB 실행 권위나 fallback이 아니다.
- local Supabase/PostgreSQL의 개발용 기본 credential, TLS/rate-limit 부재를 전제로 한다.
  runner는 Engine 28+, 고정 network/container identity와 actual single `127.0.0.1:54322`를
  reset/status/env 전에 요구한다. port를 외부 interface에 bind하거나 credential을
  public/remote 환경에서 재사용하지 않는다.
- DB gate가 `sejong_local_login` password를 회전하고 ignored `apps/api/.env`의
  `DATABASE_URL`만 갱신한다. `SEJONG_ADMIN_DATABASE_URL`과 `DATABASE_URL` 값, status 원문,
  password를 terminal·문서·Git에 남기지 않는다.
- reset/compensation/absence 명령은 disposable local DB에만 허용한다. remote project,
  실제 데이터, Docker volume 삭제·prune에는 사용하지 않는다.
- Q-SEC-003=A/D-046으로 exact 22 signature의 property-only `00700` 방향은 확정됐지만 구현은
  public 준비까지 보류한다. `00700`·matching compensation·전체 regression 전까지
  remote/public 배포, public admin/API, public backend DB credential을 차단한다.
- Q-SEC-004=A/D-029의 `default-local-port-binding`과 Q-SEC-005=A/D-030의
  `local-only-port-binding`은 모두 actual HostIP 미지정 probe에서 `127.0.0.1`과 IPv6 wildcard
  `::`를 함께 생성해 exact local 기준에 실패했다. Q-SEC-006=A/D-031과
  Q-TOOL-001=A/D-032의 source/hash-pinned patched CLI·short workspace가 exact one
  `127.0.0.1:54322`, pgTAP 282, integration 8/8과 cleanup 0/0을 통과했다. 이는 local/private
  기준선일 뿐 public readiness가 아니다. 공식 근거:
  [Docker published ports](https://docs.docker.com/engine/network/port-publishing/),
  [Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/).
