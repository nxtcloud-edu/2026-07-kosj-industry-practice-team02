# 공식 데이터 release

`kb_source_registry.csv`는 KB별 공식 출처 관리대장입니다.

현재 실행 기준은 `releases/0.1.0-initial.2/`입니다. 이 release는 PM 승인 결과에서
ACTIVE KB 19개, 공식 기관 3개, 승인된 기관·서비스 매핑 10개를 고정한 immutable
artifact입니다.

release 파일은 직접 수정하지 않습니다. 내용 변경이 필요하면 사람의 작성·별도 승인 절차를
거쳐 새로운 버전을 생성해야 합니다.

`supabase/seed.sql`은 `.2`의 `seed.sql`과 동일합니다. 자동 seed는 비활성화되어 있으므로
로컬 DB 준비 후 다음 검증 명령을 사용합니다.

```powershell
uv run --project apps/api --frozen python scripts/verify_data_seed_db.py verify-final `
  --release-version 0.1.0-initial.2
```

세부 데이터 계보는
[`DATA-SEED-002-0.1.0-initial.2.md`](../../docs/data-lineage/DATA-SEED-002-0.1.0-initial.2.md)를
참고합니다.
