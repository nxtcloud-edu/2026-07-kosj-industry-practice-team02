# Database

로컬 MVP DB는 PostgreSQL과 patched Supabase CLI로 실행합니다.

## 구조

- `supabase/migrations/`: 순서대로 적용되는 forward migration 12개
- `database/rollbacks/`: migration별 matching rollback 12개
- `supabase/tests/database/`: pgTAP 검증 12개
- `supabase/seed.sql`: 승인된 `.2` 공식 데이터
- `database/schema-v1.draft.sql`: 읽기용 논리 구조 참고본

적용이 끝난 migration은 수정하지 않고 새로운 forward migration을 추가합니다. rollback과
reset은 disposable local DB에서만 사용합니다.

## 로컬 DB 준비

저장소 루트에서 Docker Desktop을 먼저 실행합니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/bootstrap_patched_supabase.ps1 -Install

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_database.ps1
```

DB는 `127.0.0.1:54322`에만 바인딩합니다. remote DB push와 public 관리자 활성화는 이
프로젝트 범위에 포함되지 않습니다.

## 공식 데이터

`supabase/config.toml`은 `[db.seed].enabled=false`를 유지합니다. DB reset 뒤 저장소 루트
`README.md`의 정식 `.2` seed 절차를 별도로 실행합니다.

초기 projection은 ACTIVE KB 19개, 공식 기관 3개, 매핑 10개입니다. 관리자 흐름에서
근거 부족 질문을 후보로 만들고 작성자와 다른 승인자가 승인하면 20번째 ACTIVE KB로
전환됩니다.

## 보안

- 애플리케이션 계정은 capability 함수만 사용합니다.
- 질문 원문과 답변 전체를 감사 로그에 저장하지 않습니다.
- 개인 조회·법적 판단·지원 범위 밖 질문은 저장하지 않습니다.
- DB 비밀번호와 DSN은 ignored local 환경 파일에만 둡니다.

세부 데이터 검증 근거는
[`DATA-SEED-002 local verification`](../docs/test-reports/DATA-SEED-002-LOCAL-VERIFICATION.md)을
참고합니다.
