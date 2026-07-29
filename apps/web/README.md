# Web

Next.js 기반의 시민·관리자 웹 애플리케이션입니다.

## 화면

- `/`: 프로젝트 소개, 지원 분야와 추천 질문
- `/chat`: 시민 질문, 후속 질문, 공식 출처·기관 카드, 만족도 피드백
- `/admin`: 실패 질문 확인, KB 후보 작성, 별도 승인자 검수

## 실행 모드

- `actual`: local API와 연결하는 기본 모드
- `fixture`: 네트워크 없이 UI 상태만 확인하는 시연용 샘플 모드

fixture 데이터는 공식 데이터가 아니며 ACTIVE 승인에 사용할 수 없습니다.

`apps/web/.env.example`을 참고해 ignored `apps/web/.env.local`에 다음 local 설정을
작성할 수 있습니다.

```dotenv
API_INTERNAL_BASE_URL=http://127.0.0.1:8000
CHAT_UI_MODE=actual
ADMIN_UI_ENABLED=true
ADMIN_UI_MODE=actual
```

## 실행

저장소 루트에서:

```powershell
corepack pnpm --filter @sejong-ai/web dev
```

기본 주소는 `http://localhost:3000`입니다.

## 검증

```powershell
corepack pnpm --filter @sejong-ai/web lint
corepack pnpm --filter @sejong-ai/web typecheck
corepack pnpm --filter @sejong-ai/web test
corepack pnpm --filter @sejong-ai/web build
```

브라우저에는 질문 원문·대화 context를 영구 저장하지 않습니다. API 주소와 관리자 모드 설정은
server-only 환경변수로 관리합니다.
