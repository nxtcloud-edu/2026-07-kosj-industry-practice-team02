# 세종 민원 AI 길잡이 — Codex Ready Repository

이 저장소는 기존 스타터 패키지와 최종 확정 개발 기준을 합쳐, Codex가 **오래된 범위를 정답으로 오인하지 않고**, 발견 → 인터뷰 → 계획 → 구현 → 테스트 → 구현 노트 → 인수인계 순서로 작업하도록 구성한 개발 준비본이다.

## 가장 먼저 할 일

1. 이 폴더를 Git 저장소 루트로 연다.
2. `AGENTS.md`를 확인한다. Codex는 프로젝트 작업 전 `AGENTS.md`를 자동으로 읽는 방식으로 프로젝트 지침을 적용한다.
3. Codex의 첫 메시지로 `CODEX_START_PROMPT.md` 본문을 입력한다.
4. Codex가 저장소 감사를 끝내고 질문할 때까지 큰 코드 변경을 승인하지 않는다.
5. 인터뷰에 답한 뒤 실행계획을 검토하고 `진행`이라고 명시한다.

## 권장 Codex 확인 명령

Codex CLI를 사용한다면 저장소 루트에서 다음처럼 활성 지침을 확인할 수 있다.

```bash
codex --ask-for-approval never "현재 적용 중인 프로젝트 지침 파일과 핵심 규칙을 요약해줘. 코드 변경은 하지 마."
```

Codex 공식 가이드의 핵심 원칙을 반영했다.

- `AGENTS.md`는 저장소의 지속적 프로젝트 지침으로 자동 로드된다.
- 복잡하거나 모호한 작업은 계획과 인터뷰를 먼저 수행한다.
- 테스트·검증·diff 리뷰까지 완료 기준에 포함한다.
- 반복 가능한 절차는 저장소 스킬로 분리할 수 있다.

## 권위 구조

```text
AGENTS.md                       Codex 행동 규칙
CODEX_START_PROMPT.md           첫 세션 발견·인터뷰 프롬프트
docs/00_SOURCE_OF_TRUTH.md      문서 권위와 충돌 해결
docs/source-of-truth/           최종 확정 제품·정책·RFP 기준
docs/adr/                       아키텍처 결정 기록
contracts/                      API·JSON 계약 초안
supabase/migrations/            DB executable timestamp authority
database/                       local baseline 논리 projection·보상·absence proof
docs/implementation-notes/      모든 작업의 재현 가능한 기록
legacy/                         오래된 스타터·문서, 비권위 참고자료
```

## 현재 상태

- 최종 제품과 정책 문서는 확정됨.
- 활성 API의 첫 수직 흐름은 스캐폴딩됨: `/health=200`, 승인 seed 전 `/ready=503`. Web은 정적 소개 `/` shell까지 구현됐고 `/chat`·`/admin`은 아직 없음.
- 독립 local Git과 root workspace 계약은 준비됨: Node 24.12.0, pnpm 11.13.0, Python 3.12.13, uv 0.11.28.
- root `package.json`은 dependency-free이며 API dependency는 `apps/api/pyproject.toml`·`uv.lock`, Web dependency는 `apps/web/package.json`·root `pnpm-lock.yaml`에 격리됨.
- 공유 계약 package는 17개 합성 fixture를 OpenAPI·standalone JSON Schema·strict Pydantic에서 검증하고, 닫힌 health/readiness 200·FALLBACK 구조와 OpenAPI 기반 TypeScript 생성물의 byte drift까지 차단함.
- DB-001 local/private 후보는 pinned Supabase CLI 2.109.1, PostgreSQL 17.6,
  6개 forward/compensation, 7 enum·8 table, forced RLS/capability, pgTAP 282와 backend
  integration 8/8을 갖췄다. 실행 권위는 `supabase/migrations/`, 논리 projection은
  `database/schema-v1.draft.sql`이다.
- Windows PowerShell 5.1+ root gate와 별도 Docker DB gate가 exact runtime, frozen install,
  Web/API/계약, secret/package/diff, reset/rollback/replay를 검증한다. 공식 승인 seed가 0이므로
  `/ready=503`은 의도한 정상 상태다.
- 기존 FastAPI·CSV·정적 HTML 스타터는 `legacy/`에 보존됨.
- `contracts/`의 API spec revision은 2.0.1-draft다. DB executable authority는 timestamp
  migrations이며 `database/`의 `0.3.0-local` projection은 후보 참고용이다. 실제 manifest는
  host-port blocker 때문에 `database_schema=0.2.0-draft`를 유지한다.
- LLM은 local/private 합성 fixture에서만 `deepseek-v4-flash`를 제한 사용하고, 실제 시민·공개 경로는 disabled/template provider를 사용함.
- 권장 배포는 Vercel + Render + Supabase이며 실제 계정·리전·비밀값은 별도 확인이 필요함.
- A-021/Q-SEC-003의 기본값 B가 활성이다. A-022가 해결돼 DB 후보가 local baseline으로
  승격되더라도 local/private 전용이며 privileged function 21개의 public hardening 전에는
  remote/public 배포, public admin/API, public backend DB credential 사용과 `00700` 생성을
  금지한다.

## 개발 런타임 계약

```text
Node       24.12.0      .node-version
pnpm       11.13.0      package.json#packageManager
Python     3.12.13      .python-version
uv         0.11.28      uv.toml#required-version
```

`pnpm-workspace.yaml`은 `apps/*`와 `packages/*`만 활성 workspace로 포함한다. `uv.toml`은 지원되지 않는 uv 버전의 실행을 즉시 거부한다. `.tools/`, `.worktrees/`, `.superpowers/`, dependency/build cache는 Git에 넣지 않는다. root 계약은 `python -B -m unittest scripts.tests.test_repository_scaffold -v`, Web은 `corepack pnpm install --frozen-lockfile --ignore-scripts` 후 `test`·`typecheck`·`lint`·`build` script로 검증한다. 공유 계약은 `corepack.cmd pnpm --filter @sejong-ai/shared-contracts test`로 검증한다.

## 단일 로컬 검증

저장소 루트에서 다음 명령을 실행한다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
```

기본 검증을 한 번 통과해 dependency cache가 준비된 뒤에는 warm-cache 오프라인 재현도 확인할 수 있다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1 -Offline
```

`-Offline`은 미리 받은 cache의 재사용 가능성을 검증하며 빈 PC의 최초 설치를 대신하지 않는다. 러너는 파일을 삭제하거나 서버를 띄우지 않고, 실패 시 하위 명령의 내용 대신 stable step ID와 종료코드만 표시한다. 실제 `/health`·`/ready` HTTP smoke는 서버를 명시적으로 실행하는 별도 검증이다.

Docker Desktop이 실행 중일 때 DB 기준선은 별도 gate로 검증한다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart
```

이 gate의 reset/compensation은 disposable local DB 전용이다. remote project, 실제 데이터,
Docker volume에는 실행하지 않는다.

현재 Docker Desktop 4.62.0/Engine 29.2.1에서는 stock CLI가 생성한 actual binding이 wildcard로
해석돼 runner가 reset 전에 fail-closed한다. Q-SEC-004/A-022 해결 전에는 DB gate를 우회하거나
DB-001을 완료로 표시하지 않는다. [Docker port publishing](https://docs.docker.com/engine/network/port-publishing/), [Supabase local development](https://supabase.com/docs/guides/local-development/)

다른 현재 디렉터리에서 실행할 때는 `-File`에 이 저장소의 `scripts/verify.ps1` 절대 경로를 전달한다. 러너는 호출된 파일 위치를 기준으로 저장소 루트를 찾는다.

## 개발 시 절대 혼동하지 말 것

기존 업로드 패키지에는 다음 오래된 범위가 남아 있었다.

- 10개 이상 민원 분야
- 100개 테스트
- mock 신청 상태 조회
- 다국어·음성
- 급증 분석·자동 추천·주간 리포트
- 가상 기관 주소와 전화번호

현재 확정 범위는 4개 분야, 20개 표본, 회귀 테스트 1개, 관리자 승인형 개선 루프이다. 자세한 차이는 `docs/02_CURRENT_REPO_AUDIT.md`를 참조한다.

## 구현 노트 생성

```bash
python scripts/new_implementation_note.py --title "초기 저장소 감사" --task-id DISC-001 --type discovery
```

생성된 노트는 `docs/implementation-notes/`와 `INDEX.md`에 반영된다.

## 패키지 구성

- `apps/`: 신규 활성 애플리케이션 위치
- `packages/`: 프론트·백엔드 공용 계약/타입 위치
- `contracts/`: OpenAPI·JSON Schema
- `supabase/migrations/`: DB 실행 권위와 `supabase/tests/database/` pgTAP
- `database/`: 논리 projection·역순 disposable-local compensation·absence proof
- `data/`: 공식·평가·mock 데이터의 활성 위치
- `docs/`: 권위 문서, ADR, 구현 노트, 계획, 테스트, 인수인계
- `scripts/`: 노트 생성·상태 캡처·드리프트 검사
- `legacy/`: 사용자가 업로드한 이전 스타터 전체

## 제출 전 사용자 직접 입력 항목

- 팀명
- 팀원과 역할
- 대표 연락처
- 제출일
- 실제 배포 계정·URL·비밀값
