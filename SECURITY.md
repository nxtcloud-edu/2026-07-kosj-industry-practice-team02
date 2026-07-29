# 보안 및 개인정보 원칙

## 저장소에 포함하지 않는 정보

- 실제 `.env`, API key, token, DSN, 서명 secret
- 실제 시민 개인정보와 질문 원문
- local DB 상태, 액세스 로그, 오류 추적 payload
- provider request·response body

비밀값이나 실제 개인정보를 발견하면 commit과 push를 중단하고 해당 credential을 먼저 회수·교체합니다.

## 시민 질문 처리

- 외부 AI 호출 전에 개인정보를 마스킹합니다.
- 시민 검색 대상은 `ACTIVE+OFFICIAL` KB로 제한합니다.
- 출처명·URL·확인일과 기관 정보는 서버가 공식 KB에서 결합합니다.
- 질문 원문은 애플리케이션 DB와 일반 로그에 저장하지 않습니다.
- `PERSONAL_LOOKUP`, `LEGAL_JUDGMENT`, `OUT_OF_SCOPE`, `PRIVACY_UNRESOLVED`는 실패 질문 행과 KB 후보를 만들지 않습니다.
- 공급자 장애나 계약 위반은 공식 KB 기반 TEMPLATE 또는 안전한 폴백으로 처리합니다.

## 관리자와 DB

- KB 후보 작성자와 승인자는 달라야 합니다.
- 승인되지 않은 후보와 mock 데이터는 시민 답변에 사용할 수 없습니다.
- DB reset, rollback과 seed 검증은 `127.0.0.1`의 disposable local DB에서만 실행합니다.
- local DB credential을 public 또는 remote 환경에서 재사용하지 않습니다.
- 관리자 화면은 local/private MVP 범위이며 공개 인증·SSO/RBAC를 제공하지 않습니다.

## 검사 명령

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/check_secret_patterns.ps1

python -B scripts/check_git_history_secrets.py --repo .
```

현재 파일 검사와 Git history 검사는 명백한 credential 패턴을 탐지하지만 모든 형태의 난독화·암호화된 비밀 부재를 보증하지 않습니다. 제출 전에는 변경 파일과 환경 설정을 함께 수동 확인합니다.

세부 정책은 다음 문서를 참고합니다.

- `docs/07_SECURITY_PRIVACY.md`
- `docs/source-of-truth/PRIVACY_POLICY.md`
