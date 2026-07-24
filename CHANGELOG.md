# Changelog

이 파일은 공개 평가 snapshot의 주요 변경만 기록합니다. 개인 계정, 내부 작업 대화와
세부 구현 이력은 공개 평가 범위에서 제외합니다.

## 2026-07-24 — Week 3 MVP evaluation snapshot

- FastAPI `/api/v1/chat`의 마스킹 → 정책 분류 → ACTIVE KB 검색 → 근거 gate →
  구조화 답변/폴백 흐름을 포함했습니다.
- Next.js `/`, `/chat`, local/private `/admin`과 390/430/desktop 브라우저 검증을 포함했습니다.
- immutable `0.1.0-initial.2` 공식 데이터 19/3/10과 사람 승인으로 생성되는 20번째 ACTIVE
  개선 흐름을 문서화했습니다.
- `PERSONAL_LOOKUP` 질문의 text/event/failed row 미저장 정책을 계약과 테스트로 고정했습니다.
- Upstage `solar-pro3` adapter는 서버 allowlist의 합성 평가 전용이며 시민 자유 입력과 public
  provider 연결에는 사용하지 않습니다.
- 평가용 README, 직접 증거, 비밀 검사와 GitHub Frontend CI를 추가했습니다.
- 대외 서비스명 `세종 민원이음`, 실제 팀 역할, 문제·구조·원칙·일정·5문항 데모를 첫 진입
  README에 복원하고 검증된 현재 실행 절차와 결합했습니다.
- actual 실행용 persistent seed 절차와 완료 후 runtime을 종료하는 종합 seed gate를 분리해
  fresh-clone 실행 순서를 교정했습니다.

## Current versions

정확한 현재 값은 [`versions/manifest.json`](versions/manifest.json)이 권위입니다.

| Axis | Version |
|---|---|
| Application | `0.8.0-pr8-frontend-baseline` |
| Web | `0.5.0-pr8-citizen-admin-baseline` |
| API | `3.1.0-draft` |
| Shared contracts | `0.4.0` |
| Database schema | `0.4.0-local` |
| Official data | `0.1.0-initial.2` |
| Prompt set | `0.1.0-upstage-solar-pro3-synthetic` |
| Test suite | `1.5.0-pr8-web-baseline` |

## Limits

- public deployment, remote DB, public admin 인증과 실제 시민 provider 호출은 포함하지 않습니다.
- 상세 개발 history는 source 저장소에 유지하며 이 공개 snapshot의 완료 증거로 사용하지 않습니다.
