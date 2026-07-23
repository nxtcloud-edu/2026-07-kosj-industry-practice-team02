# apps/web

세종 민원 AI 길잡이의 Next.js 웹 앱이다. 소개 화면 `/`, local/private `/chat` 대화 화면,
기본 memory-only 시연 fixture와 명시적 local/private actual transport를 선택할 수 있는 최소 `/admin`을 제공한다.

## 현재 동작

- 서비스명과 핵심 원칙을 소개한다.
- 승인된 네 지원 분야와 현재 제공하지 않는 기능을 안내한다.
- 홈의 `민원 안내 시작하기`는 404가 아닌 정적 `/chat` 준비 화면으로 이동한다.
- `/chat`은 생성된 API union을 소비해 SUCCESS, FOLLOWUP, 5개 폴백, 출처·기관 카드,
  loading/error/retry를 표시한다.
- logical retry마다 UUID `Idempotency-Key` 하나를 만들고 같은 재시도에는 유지한다. correlation ID는
  backend가 별도로 만들며 Web은 저장하지 않는다.
- 대화와 signed context token은 React 메모리에만 두며 브라우저 저장소·쿠키·분석 도구를
  사용하지 않는다.
- 두 화면 모두 키보드 본문 건너뛰기와 보이는 포커스 표시를 제공한다.

## 로컬 환경변수

`apps/web/.env.example`을 `apps/web/.env.local`로 복사할 수 있다. `API_INTERNAL_BASE_URL`은
Next 서버가 same-origin `/api/v1/*` 요청을 local API로 전달할 때만 사용하며 기본값은
`http://127.0.0.1:8000`이다. 이 이름에는 비밀값을 넣지 않으며 `NEXT_PUBLIC_*` API 주소나
backend 비밀을 브라우저 번들에 추가하지 않는다.

`ADMIN_UI_ENABLED`는 서버 전용 local/private 관리자 화면 게이트다. 기본값과 공개 모드는
`false`로 유지한다. `ADMIN_UI_ENABLED=true`와 `ADMIN_UI_MODE=actual`을 함께 준 local/private
리허설에서만 typed actual admin transport를 사용하고, 그 외에는 명시적 fixture다. 이는 인증을
대체하지 않으며 public 관리자 연결은 계속 금지한다.

## 로컬 명령

저장소 루트에서 실행한다.

```powershell
corepack pnpm --filter @sejong-ai/web dev
corepack pnpm --filter @sejong-ai/web lint
corepack pnpm --filter @sejong-ai/web typecheck
corepack pnpm --filter @sejong-ai/web test
corepack pnpm --filter @sejong-ai/web build
corepack pnpm --dir tools/web-e2e install --frozen-lockfile --ignore-scripts
corepack pnpm --dir tools/web-e2e test
node scripts/check_web_prod_dependency_boundary.mjs
```

Node와 pnpm의 정확한 버전은 저장소 루트의 `.node-version`과 `package.json#packageManager`를 따른다.
