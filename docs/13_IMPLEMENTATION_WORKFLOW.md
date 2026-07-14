# 구현 워크플로

## 단계 1 — Discover

- 지침·source-of-truth·관련 ADR 읽기
- Git과 파일 상태 확인
- 기존 구현/legacy/계약 차이 확인
- 미지의 영역 분류

## 단계 2 — Interview

- A/B만 질문
- 최대 7개
- 영향이 큰 질문 우선
- 옵션·추천·기본값 제공

## 단계 3 — Decide and Plan

- 결정 로그/ADR/모호성 레지스터 갱신
- 실행계획 작성
- 인수 기준과 테스트 정의
- 인간 승인

## 단계 4 — Implement

- 작은 수직 슬라이스
- 타입/계약 먼저
- 최소 변경
- 장애·빈 상태·보안 경계 포함

## 단계 5 — Verify

- unit/contract/integration/E2E
- lint/type/build
- privacy/accessibility/performance when relevant
- diff review

## 단계 6 — Document

- source-of-truth/contract/version/data lineage
- implementation note + index
- human/AI boundary summary

## 단계 7 — Handoff

- 실행 방법
- 변경 이유
- 테스트 증거
- 미해결 위험
- 롤백/다음 단계

## 중단 조건

- A/Blocker 미해결
- 비밀 또는 실제 개인정보 발견
- source-of-truth와 요청 충돌
- destructive migration without approval
- 공식 출처 불명확
