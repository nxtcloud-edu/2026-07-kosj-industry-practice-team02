# ADR-0020: 7월 25일 local/private 핵심 개선 루프 마일스톤

- 상태: Accepted
- 날짜: 2026-07-22
- 결정자: 사용자
- 관련 결정: Q-MVP-001=A, D-058

## 맥락

기반 스캐폴딩, DB schema, 계약 초안, 승인 데이터 staging, PII core, private GitHub 협업은 준비됐지만
실제 ACTIVE DB seed, chat application service/API, frontend 연동, 관리자 개선 루프는 아직 연결되지
않았다. 7월 31일 최종 범위를 모두 같은 깊이로 병렬 구현하면 critical path와 검증 증거가 흐려진다.

## 결정

1. 2026-07-25를 **local/private demo-ready core-loop milestone**로 둔다.
2. 최종 4개 분야·20 ACTIVE KB·3페이지·승인형 개선 루프 범위는 유지한다.
3. 7월 25일에는 deterministic/template chat 경로, 19개 초기 ACTIVE, 개선 루프로 만든 20번째 ACTIVE,
   최소 `/chat`·`/admin`, 표본 20·회귀 1·보안/데모 gate를 완료한다.
4. 실제 시민 질문은 DeepSeek에 보내지 않는다. DeepSeek 품질 튜닝은 마일스톤 뒤로 미룬다.
5. 100명 부하, 자동 백업, public 배포와 public `00700`, 고급 UI polish는 7월 25일 뒤 P1로 유지한다.
6. Q-MVP-001의 즉시 실행 지시는 기존 DATA-SEED-002 명세·계획과 이 ADR에 연결된 실행계획을
   승인한다. 단, public/remote/secret/새 production dependency 권한은 확대하지 않는다.
7. 일정 단축은 privacy, ACTIVE-only, official/mock 분리, server-bound source, self-approval 차단,
   접근성 최소선, 테스트/구현 노트 gate를 완화하지 않는다.

## 결과

### 장점

- 사용자가 확인할 수 있는 end-to-end 가치가 4일 안에 한 흐름으로 모인다.
- provider와 public infrastructure 없이도 핵심 제품 가설과 승인 루프를 검증할 수 있다.
- Frontend fixture 구현과 Backend/Data critical path를 병렬화할 수 있다.

### 단점과 완화

- UI polish·provider 품질·부하/복구 증거가 마일스톤에 포함되지 않는다.
  - 최종 백로그에서 삭제하지 않고 별도 P1 gate로 명확히 남긴다.
- local demo actor는 실제 인증처럼 보일 수 있다.
  - 화면과 문서에 `local/private demo` 표시를 강제하고 public route를 닫는다.
- 4일 일정은 DATA actual이나 계약 drift가 실패하면 연쇄 지연된다.
  - 7/22 기준선 복구, 매일 exit gate, template-first와 fixture-first로 위험을 앞당긴다.

## 기각한 대안

- DeepSeek 연결부터 시작: 데이터·privacy·grounding gate가 뒤로 밀린다.
- frontend/backend를 한 브랜치에서 동시 수정: 역할 경계와 충돌 위험이 커진다.
- 100명/배포까지 7월 25일 완료 정의에 포함: 현재 핵심 흐름보다 운영 증거가 critical path를 점유한다.
- 19건을 완료로 간주: 최종 개선 루프와 20번째 ACTIVE 가치를 검증하지 못한다.

## 재검토 조건

- DATA-SEED-002 actual DB가 approved plan 안에서 복구 불가능한 새 보안/데이터 결정에 막힐 때
- 공개 배포·remote DB·실제 시민 provider 사용을 요구할 때
- 7월 25일 이후 100명·백업·고급 UI의 우선순위를 다시 배치할 때
