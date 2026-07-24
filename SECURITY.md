# Security

이 저장소는 local/private 교육용 MVP입니다. public 운영, 실제 시민 데이터 처리 또는 기관
내부 시스템 연결을 승인한 자료가 아닙니다.

## 비협상 경계

- 질문 원문을 애플리케이션 DB, 액세스 로그, 오류 추적에 저장하지 않습니다.
- 외부 모델 호출 전 개인정보를 마스킹합니다. 안전한 마스킹 결과를 만들 수 없으면 호출과
  저장을 모두 중단하고 `PRIVACY_UNRESOLVED`로 응답합니다.
- 시민 검색은 `ACTIVE + OFFICIAL` KB만 사용합니다.
- 출처명·URL·확인일은 서버가 승인 KB 메타데이터에서 결합합니다.
- `PERSONAL_LOOKUP`, `LEGAL_JUDGMENT`, `OUT_OF_SCOPE`, `PRIVACY_UNRESOLVED`는 개선 후보가
  아니며 질문 text/failed row를 저장하지 않습니다.
- 작성자와 승인자는 달라야 하며 mock 후보는 ACTIVE로 승인할 수 없습니다.

## 비밀과 로그

- 실제 `.env`, API key, token, DSN, DB password와 service-role credential을 커밋하지 않습니다.
- API 로그는 서버 생성 request ID, method, route template, status만 허용합니다.
- request body, query, header, cookie, Authorization, client IP, 답변과 provider/DB payload를
  기록하지 않습니다.
- 예제 환경 파일은 변수 이름만 제공하고 민감한 값은 비워 둡니다.

검사:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/check_secret_patterns.ps1 -RepositoryRoot .
python -B scripts/check_git_history_secrets.py --repo .
node scripts/check_web_bundle_secrets.mjs apps/web/.next
```

검사 결과는 credential 회전, 저장소 접근 검토와 배포 전 수동 보안 검토를 대체하지 않습니다.

## 외부 모델

Upstage `solar-pro3` 경로는 서버 allowlist의 canonical 합성 평가 전용입니다. 실제 시민 자유
입력, 실제 개인정보, public/remote 요청은 provider로 보내지 않습니다. provider key, raw prompt,
raw response와 reasoning은 로그·보고서에 기록하지 않습니다.

## local DB와 관리자

- patched Supabase CLI는 PostgreSQL 포트를 정확히 `127.0.0.1:54322`에만 바인딩하는
  disposable local 검증 경로입니다.
- reset, rollback, seed와 login rotation을 remote DB 또는 실제 데이터에 실행하지 않습니다.
- `/admin`의 역할 전환과 고정 actor는 데모용이며 인증이 아닙니다.
- public 환경에서는 별도 서버측 인증/RBAC gate가 없으면 관리자 UI와 API를 비활성화합니다.
- 개발 credential, TLS/rate-limit 부재와 deferred privileged-function hardening 때문에 local
  기준선을 production-ready로 부르지 않습니다.

상세 정책은 [`docs/07_SECURITY_PRIVACY.md`](docs/07_SECURITY_PRIVACY.md)와
[`docs/source-of-truth/PRIVACY_POLICY.md`](docs/source-of-truth/PRIVACY_POLICY.md)를 따릅니다.

## 취약점 또는 노출 발견 시

커밋·배포를 중단하고 노출 credential을 먼저 회수·교체합니다. 질문 원문·개인정보가 포함됐다면
복사·재게시하지 말고 저장 위치와 접근 범위만 값 없이 기록합니다. Git history 정리나 데이터
삭제는 owner 승인과 별도 복구 계획을 거쳐 수행합니다.
