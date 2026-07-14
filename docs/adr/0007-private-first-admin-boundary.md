# ADR-0007: 관리자 기능 local/private 우선 보안 경계

- Status: Accepted
- Date: 2026-07-14
- Decision source: Q-SEC-001 / D-014

## Context

MVP의 역할 전환 헤더는 작성자와 승인자 분리 시연을 위한 장치이며 인증 수단이 아니다. 이를 공개 인터넷에서 신뢰하면 마스킹 질문, 후보 작성, 승인 기능이 무단 노출될 수 있다. 반면 기관 SSO·완전한 RBAC는 P2다.

## Decision

- 초기 `/admin`과 `/api/v1/admin/*`는 loopback 또는 팀이 통제하는 private 환경에서만 활성화한다.
- `X-Demo-Actor-Id`와 `X-Demo-Role`은 local/test 시연에서만 허용하며 public 인증으로 간주하지 않는다.
- 공개 시민 demo를 배포하더라도 별도 승인된 서버측 gate가 없으면 관리자 페이지와 관리자 API route를 비활성화한다.
- DB는 브라우저가 직접 쓰지 않고 backend-only 경계를 사용한다. 공개 환경으로 전환할 때는 deny-by-default DB 권한/RLS, 인증·세션, CORS/CSRF, 감사 테스트를 함께 승인한다.
- SSO·기관 단위 RBAC·전자결재는 P2로 유지한다.

## Consequences

초기 0원·local-first 데모에서 구현 복잡도와 무단 공개 위험을 줄인다. 대신 공개 URL에서 관리자 개선 루프를 시연하려면 별도 보안 설계와 배포 승인이 필요하다.

## Verification

- public 환경 설정에서 관리자 UI와 API가 404 또는 403으로 차단된다.
- local/test에서도 역할·작성자 본인 승인 차단과 감사 메타데이터 검사를 수행한다.
- 데모 헤더를 인증으로 표현하는 문서·화면이 없다.
