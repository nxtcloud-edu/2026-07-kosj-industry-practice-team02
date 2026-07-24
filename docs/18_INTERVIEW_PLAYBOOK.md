# 인터뷰 플레이북

## 목적

사용자가 기술적으로 언급하지 않은 부분을 무조건 구현에서 누락시키지 않되, 모든 사소한 질문을 사용자에게 떠넘기지도 않는다. 아키텍처와 책임을 바꿀 질문만 인간에게 묻고, 내부 구현 세부는 AI가 기본값을 선택해 기록한다.

## 질문 탐색 체크리스트

### 제품과 사용자

- 대표 사용자가 누구이며 어떤 한 흐름을 끝까지 완주해야 하는가
- 성공/실패/후속질문/오류의 사용자 문구와 다음 행동
- P0/P1/P2 경계와 제외 범위
- 공식 정보가 없을 때 기관 안내 수준

### 아키텍처

- 단일/모노레포, 런타임, 패키지 관리자
- API 경계와 버전
- DB migration과 seed
- provider adapter, retry, timeout, fallback
- admin 역할 전달과 보호

### 데이터

- 공식 출처와 사용 허가
- raw/processed/official/mock 구분
- 버전·확인일·승인·삭제
- 수수료/운영시간 최신성
- 데이터 수집 담당과 마감

### 보안·개인정보

- PII 범위와 오탐 허용
- LLM 전송, 로그, trace, 인프라 자동 로그
- 보관기간, 삭제 job, 백업
- secrets, CORS, admin public access

### 운영·배포

- 계정·리전·플랜·쿼터·비용
- health/readiness, cold start
- 배포 실패와 rollback
- 발표 네트워크와 로컬/녹화 백업

### 품질

- 정답/평가자/판정 기준
- deterministic vs model-dependent tests
- 접근성 기기/브라우저
- 성능 측정 범위
- mock KPI 표시

## 질문 우선순위 산정

다음 점수를 합산한다.

- 아키텍처 변경 0~3
- 개인정보/보안 0~3
- 비용/공급자 0~2
- 데이터 손실/마이그레이션 0~3
- 사용자 동작 0~2
- 롤백 난이도 0~2

8점 이상 A/Blocker, 5~7점 B/High, 2~4점 C/Defaultable, 0~1점 D/Internal.

## 질문 형식

```text
Q-SEC-001. 외부 LLM에 전송하기 전에 이름과 상세주소까지 마스킹할까요?
- 왜 필요한가: 오탐/누락과 답변 품질, 개인정보 정책이 달라집니다.
- A. 보수적 마스킹: 개인정보 위험↓, 일부 질문 맥락 손실
- B. 주민번호/전화 등 명확한 패턴만: 답변 품질↑, 이름/주소 누락 위험
- 추천: A를 기본으로 하고 allowlist/테스트로 오탐을 관리
- 답이 없을 때 기본값: A
- 영향: redaction 모듈, test fixtures, privacy docs, provider payload
```

## 인터뷰 후 처리

- 결정 로그 행 추가
- ADR 필요성 판단
- 모호성 상태 Resolved/Deferred
- plan/task/contract/version 영향 반영
- 구현 노트 작성
