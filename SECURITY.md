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

## 보안 관련 변경

마스킹, 로그, 권한, 보관기간, 외부 LLM, CORS, 배포 비밀, DB RLS/권한 변경은 반드시 인간 승인을 받고 ADR 또는 결정 로그를 남긴다.

자세한 정책은 `docs/07_SECURITY_PRIVACY.md`와 `docs/source-of-truth/PRIVACY_POLICY.md`를 따른다.

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
node scripts/check_web_bundle_secrets.mjs apps/web/.next
```

두 스캐너 모두 clean은 0, 탐지 결과는 1, 입력 누락·읽기 실패 같은 운영 오류는 2 이상을
반환한다. 출력은 경로·stable rule ID·개수만 포함하며 일치한 값이나 파일 내용을 출력하지
않는다.

패턴 검사는 명백한 private-key header, provider/GitHub token, AWS access-key ID, 승인된 secret
assignment, credential URL을 찾지만 엔트로피 분석·Git 과거 이력·프로세스 환경·클라우드
로그까지 검사하지 않는다. assignment 검사는 일반/`export`, PowerShell `$env:NAME=value`, cmd
`set NAME=value` 형식을 포함한다. 등호가 없는 `setx NAME value`는 P2 한계로 탐지하지 않는다.
기본 저장소 검사는 active tracked/untracked nonignored 파일만 대상으로 하고
legacy·cache·build·quarantine과 symlink는 제외한다.

번들 검사는 build 시 materialize된 `.next/static`, app HTML/RSC, pages HTML에서 server secret
marker 이름과 선택적 `SEJONG_WEB_SECRET_SENTINEL` 값의 byte literal을 찾는다. 서버 전용
JavaScript·cache, 동적 RSC/HTML live response와 Pages `_next/data/*.json` runtime 경로는 보증하지
않는다. WEB-CHAT/DEV-001D에서 live-response sentinel gate를 추가해야 한다. 난독화·인코딩된
값도 보증하지 않으므로 두 검사는 비밀 회수·provider 설정 검토·배포 전 수동 보안 검토를
대체하지 않는다.
