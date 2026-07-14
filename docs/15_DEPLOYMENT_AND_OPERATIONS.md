# 배포·운영 기준

## 확정 초기 환경과 향후 권장 환경

- 초기 완료 기준: local-first, 외부 인프라 예산 0원
- Local Web: Node 24.x + pnpm
- Local API: Python 3.12 + uv
- Local DB: Docker + Supabase CLI, `supabase/migrations/` 버전 SQL이 실행 권위
- 향후 공개 배포 추천: Vercel(Web) + Render(API) + Supabase PostgreSQL(DB)
- 공개 배포·배포 URL·녹화본은 계정·리전·로그·CORS·예산과 서버측 admin gate를 별도 승인한 뒤 추가

## 아직 인간 확인이 필요한 것

- 실제 계정과 소유자
- 리전과 데이터 위치
- 무료 플랜 sleep/쿼터
- 도메인/HTTPS
- admin 노출 보호
- CORS origin
- secret rotation
- 인프라 자동 로그 보관
- 공개 환경 LLM 데이터 처리·비용/한도 재승인

현재 위 항목은 공개 배포 전에 확인할 Deferred 항목이다. 초기 구현을 막는 배포 계정 요구사항으로 해석하지 않는다.

현재 원격 저장소와 CI는 사용하지 않는다. local Git에서 lint·typecheck·test·build·OpenAPI/JSON Schema·secret scan을 수동 gate로 실행하고 구현 노트에 명령과 실제 결과를 남긴다. 원격/CI는 사용자가 Git 연결을 다시 요청할 때 추가한다.

## 필수 엔드포인트

- `/health`: 프로세스 생존
- `/ready`: DB·필수 데이터 준비

health/readiness에 비밀이나 내부 상세를 노출하지 않는다.

## 환경 분리

- development
- test
- demo/staging

실제 production을 주장하지 않는다. demo 데이터와 공식 데이터의 표시가 유지되어야 한다.

## 장애·복구

- DB/LLM/API 장애 시 raw question 임시 저장 금지
- 고정 공식 KB 템플릿 경로
- seed/migration 재현
- 빈 DB `supabase db reset` replay와 위험 변경의 명시적 보상/rollback SQL
- 백업 복구 후 서비스 개방 전 만료된 `masked_question` 재파기
- 배포 rollback 지침
- 발표용 캡처/녹화

local/private 합성 MVP의 기본 복구 목표는 RPO 24시간, RTO 60분이다. 승인 seed와 versioned migration을 1차 복구 수단으로 사용하고 매일 및 파괴적 migration/데모 milestone 직전에 gitignored local logical dump를 만든다. dump에는 비밀·실제 시민 데이터를 넣지 않으며 30일이 지난 dump는 삭제한다. 인수인계 전에 reset/replay 또는 dump restore와 서비스 개방 전 retention purge를 한 번 재현한다. 원격/off-device backup이 없으므로 단일 PC 손실 위험은 남으며, 실제·비재현 데이터나 공개 운영 전에는 백업 위치·암호화·RPO/RTO·삭제 전파를 다시 승인한다.
