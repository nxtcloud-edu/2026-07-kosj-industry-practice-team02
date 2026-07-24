# 코딩 표준

## 공통

- 공개 동작은 계약과 테스트로 고정한다.
- 함수/모듈은 한 책임을 갖고, 도메인 용어를 사용한다.
- 하드코딩된 상태 문자열 대신 enum/typed model을 사용한다.
- 오류를 삼키지 않고 안전한 사용자 메시지와 내부 코드로 분리한다.
- raw question/PII를 예외 메시지, repr, snapshot에 포함하지 않는다.
- 주석은 ‘무엇’보다 ‘왜/제약’을 설명한다.

## Python/FastAPI 기본 추천

- Python 3.12, `uv` — Q-DEV-001로 확정; 정확한 도구 patch는 스캐폴딩 lock/manifest에서 고정
- Pydantic v2 models, `from __future__ import annotations`
- Ruff format/lint, strict-enough type checking, pytest
- router → application service → domain/policy → repository/provider 경계
- route handler에 검색·승인·마스킹 로직을 몰아넣지 않는다.
- DB transaction boundary를 service에서 명시한다.
- 비동기는 외부 I/O에서만 일관되게 사용한다.

## TypeScript/Next.js 기본 추천

- Node 24.x, pnpm — Q-DEV-001로 확정; 정확한 도구 patch는 스캐폴딩 lock/manifest에서 고정
- TypeScript strict
- API 타입은 계약에서 생성/동기화
- Server/Client component 경계를 의도적으로 선택
- 접근 가능한 공용 UI 컴포넌트 사용
- 서버 상태와 로컬 UI 상태를 분리
- `any`, 무분별한 non-null assertion, 숨은 side effect를 피한다.

## 테스트 이름

```text
should_<expected>_when_<condition>
```

한국어 설명을 추가할 수 있지만 코드 식별자는 일관된 영어를 권장한다.

## 날짜와 시간

- DB: UTC timestamptz
- 표시/문서: Asia/Seoul
- 기준일은 `YYYY-MM-DD`
- 테스트에서 시스템 시간을 주입/고정한다.
