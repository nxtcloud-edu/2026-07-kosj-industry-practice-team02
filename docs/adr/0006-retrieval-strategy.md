# ADR-0006: 키워드·메타데이터 우선, 임베딩 보조 검색

- Status: Accepted default; embedding enablement pending
- Date: 2026-07-13

## Decision

20개 KB에서는 intent filter와 키워드/alias/metadata를 기본으로 한다. 임베딩은 feature flag로 보조한다.

## Consequences

검색 이유를 설명하고 테스트하기 쉽다. 대규모 KB 확장 시 rerank와 vector index 고도화가 필요하다.
