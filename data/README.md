# 데이터 구성

최종 MVP는 승인된 공식 지식만 시민 답변에 사용합니다.

- `official/releases/0.1.0-initial.2/`: 승인된 최신 immutable release
  - ACTIVE KB 19개
  - 공식 기관 3개
  - 기관·서비스 매핑 10개
- `staging/data-001/0.1.0-draft.1/`: `.2` release를 재검증하기 위한 승인 입력
- `schemas/data-seed/v2/`: 최신 release 검증 스키마
- `retrieval/topic-coverage.v1.json`: 지원 주제와 coverage 경계
- `evaluation/sample_questions_20.csv`: 대표 질문 20개

시민 검색은 `ACTIVE` 상태의 공식 KB만 대상으로 합니다. staging 데이터와 테스트 fixture는
시민 답변 근거로 사용하지 않습니다.

`supabase/seed.sql`은 `.2` release의 `seed.sql`과 동일하지만
`supabase/config.toml`의 `[db.seed].enabled=false` 설정 때문에 DB reset 시 자동 적용되지
않습니다. 정식 seed 절차는 저장소 루트 `README.md`의 **실행 방법**을 따릅니다.
