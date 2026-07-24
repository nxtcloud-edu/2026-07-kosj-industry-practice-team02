# Local 운영과 향후 배포 경계

## 이번 평가 범위

- Web: Next.js, `127.0.0.1:3000`
- API: FastAPI, `127.0.0.1:8000`
- DB: disposable local PostgreSQL, `127.0.0.1:54322`
- 자동 seed: 비활성 (`[db.seed].enabled=false`)
- 공식 seed: 별도 검증된 `0.1.0-initial.2`

## fresh local 재현

실행 권위는 루트 [README의 §6.3](../README.md)입니다. 핵심 순서는
patched CLI bootstrap → `verify_database.ps1` → 같은 runtime에 별도 `.2` `seed-cycle`과
`verify-final` → process-only context secret → API → actual Web입니다.

`verify_data_seed.ps1`은 failure rollback·동시성·보상·재실행 방지까지 확인하는 **독립적인
disposable gate**입니다. 완료 시 자신이 소유한 runtime을 종료하므로 API 실행 직전에 이어
붙이지 않습니다. actual Web은 `CHAT_UI_MODE=actual`, `ADMIN_UI_ENABLED=true`,
`ADMIN_UI_MODE=actual`을 명시해야 `/admin` 승인 루프를 사용할 수 있습니다.

DB와 seed가 없으면 `/health=200`, `/ready=503`이 정상입니다. 검증된 schema, login과 approved
19/3/10 seed가 있으면 `/ready=200`이어야 합니다.

## 복구·종료

- schema 복구: versioned migration 재실행
- 공식 데이터 복구: immutable `.2` seed 재실행
- rollback: `database/rollbacks/`를 역순으로 disposable local DB에만 적용
- local stack 종료:

```powershell
.\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe stop
```

Docker volume delete/prune, remote `db push`, 실제 데이터 rollback은 승인 범위가 아닙니다.

## public 배포 전 필수 결정

- 도메인·HTTPS·CORS
- 인프라 계정·리전·데이터 위치
- secret manager와 rotation
- public admin SSO/RBAC
- 인프라 로그 보관·삭제와 PII 처리
- remote DB backup·복구·RPO/RTO
- 공급자 개인정보 처리·비용·쿼터
- 부하·장애·보안 검증

따라서 이 snapshot은 Vercel/Render/Supabase public 배포 또는 production readiness를 주장하지
않습니다.
