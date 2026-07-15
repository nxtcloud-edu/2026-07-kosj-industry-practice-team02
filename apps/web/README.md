# apps/web

세종 민원 AI 길잡이의 Next.js 웹 앱이다. 현재 구현 범위는 정적 소개 화면 `/` 하나이며, 승인된 공식 KB를 사용하는 `/chat`과 local/private 전용 `/admin`은 후속 수직 흐름에서 구현한다.

## 현재 동작

- 서비스명과 핵심 원칙을 소개한다.
- 지원 예정인 네 분야를 안내한다.
- 채팅 답변·민원 신청·개인 조회·공식 KB 데이터가 아직 제공되지 않는 개발 상태를 명시한다.
- 키보드로 본문 건너뛰기와 지원 분야 내부 링크를 사용할 수 있으며, 아직 없는 `/chat` 링크는 제공하지 않는다.
- 현재 화면은 API, 브라우저 저장소, 쿠키, 분석 도구, 외부 폰트·이미지를 사용하지 않는다.

## 로컬 환경변수

`apps/web/.env.example`을 `apps/web/.env.local`로 복사한다. 브라우저에 포함 가능한 값은
`NEXT_PUBLIC_API_BASE_URL` 한 개뿐이며 기본값은 local API `http://127.0.0.1:8000`이다.
현재 정적 `/` 화면은 아직 이 값을 읽거나 API를 호출하지 않는다. backend 비밀 이름이나 값을
web 템플릿에 추가하면 안 된다.

## 로컬 명령

저장소 루트에서 실행한다.

```powershell
corepack pnpm --filter @sejong-ai/web dev
corepack pnpm --filter @sejong-ai/web lint
corepack pnpm --filter @sejong-ai/web typecheck
corepack pnpm --filter @sejong-ai/web test
corepack pnpm --filter @sejong-ai/web build
```

Node와 pnpm의 정확한 버전은 저장소 루트의 `.node-version`과 `package.json#packageManager`를 따른다.
