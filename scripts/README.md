# Scripts

평가와 재현에 필요한 주요 명령만 정리합니다. 모든 명령은 저장소 루트에서 실행합니다.

## 저장소·계약·보안

```powershell
python -B scripts/check_repository_docs.py
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/check_secret_patterns.ps1 -RepositoryRoot .
python -B scripts/check_git_history_secrets.py --repo .
corepack pnpm --filter @sejong-ai/shared-contracts generate:check
corepack pnpm --filter @sejong-ai/shared-contracts test
```

## local DB와 공식 seed

```powershell
# fresh clone: reproducible patched CLI 설치·검증
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/bootstrap_patched_supabase.ps1 -Install
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/bootstrap_patched_supabase.ps1 -VerifyOnly

# migration/rollback/pgTAP/backend integration
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_database.ps1

# immutable approved release의 실패·동시성·보상·재실행 방지 검증
# 주의: 성공·실패와 무관하게 자신이 소유한 local DB runtime을 종료한다.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.2
```

이 경로는 disposable local DB 전용입니다. remote project, 실제 데이터, stock CLI fallback과
volume 삭제를 허용하지 않습니다. 실행 가능한 19/3/10 DB를 유지해 API와 Web을 연결할 때는
이 gate를 API 직전에 실행하지 말고, 루트 [README의 §6.3](../README.md)의
`verify_database` → 별도 `seed-cycle` → `verify-final` 절차를 따릅니다.

## API 실행

```powershell
uv run --project apps/api --frozen python scripts/run_local_api.py --port 8000
```

import-safe 기본 API는 DB와 approved seed가 없으면 `/ready=503`입니다. 검증된 local DB와
`official_data=0.1.0-initial.2`, process-only `CONTEXT_TOKEN_SECRET`이 준비됐을 때만
`/ready=200`입니다. actual `/admin` Web 환경변수도 루트 README §6.3을 따릅니다.

## Upstage 합성 평가

```powershell
uv run --project apps/api --frozen python `
  scripts/run_upstage_synthetic_evaluation.py --preflight-only
```

actual 실행은 별도 인간 승인과 local secret이 있을 때만 허용됩니다. canonical 합성 allowlist
밖의 자유 입력·실제 시민 질문·PII는 전송하지 않으며 raw prompt/response를 보고서에 기록하지
않습니다.

## 전체 local gate

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1 -Offline
```

오프라인 실행은 dependency cache가 준비된 환경을 전제로 합니다. 실패 시 stable 단계명과
종료코드를 사용하고 비밀값·DSN·질문 원문을 출력하지 않습니다.
