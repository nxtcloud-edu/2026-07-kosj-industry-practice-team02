# ADR-0001: 권위 문서 계층과 legacy 격리

- Status: Accepted
- Date: 2026-07-13

## Context

기존 패키지에 초기 범위와 최종 범위가 혼재해 에이전트가 오래된 10개 분야·100문항·상태조회·고급 분석을 구현할 위험이 있다.

## Decision

root AGENTS → source-of-truth → ADR → contracts/schema → implementation notes 순서의 권위 체계를 사용한다. 기존 업로드는 `legacy/`에 격리한다.

## Consequences

legacy 재사용에는 검증과 구현 노트가 필요하지만 범위 드리프트를 크게 줄인다.
