# CONTRIBUTING

## 작업 흐름

1. source-of-truth와 관련 ADR을 읽는다.
2. 작업 ID를 `TASKS.md`에서 확인하거나 새로 제안한다.
3. 복잡한 작업은 실행계획을 만든다.
4. 브랜치에서 구현한다.
5. 테스트·린트·타입체크·빌드·diff 리뷰를 수행한다.
6. 계약·문서·버전·데이터 계보를 갱신한다.
7. 구현 노트를 만들고 INDEX를 갱신한다.
8. 작은 논리 단위로 커밋한다.

## 브랜치 예시

```text
codex/DEV-001-repo-scaffold
codex/API-CHAT-001-chat-endpoint
codex/LOG-001-redaction-leak
codex/DOC-001-sync-decisions
feat/web-WEB-CHAT-001-answer-states
```

기본 브랜치는 `main`이다. Codex는 `codex/<task-id>-<slug>`, 인간 Frontend 팀원은
`feat/web-<task-id>-<slug>`를 사용한다. 한 PR에는 하나의 TASK ID와 하나의 수직 목적만 담는다.

Q-GIT/Q-COLLAB 결정으로 사용자의 개인 GitHub private source remote와 collaboration CI 방향은
승인됐다. Q-GIT-004=A로 기존 author email의 private collaborator 공개와 history·SHA 보존도
확정했고 D-054로 COLLAB-001 실행계획도 승인됐다. 로컬 검사기·workflow/template는 구현 중이며,
실제 remote·초대·Codex 연결은 정확한 account identifier와 사용자 browser 인증 뒤에만 수행한다.
실행 뒤에도 각 작업자는 변경 영역의 local 검증과 구현 노트 의무를 유지한다. GitHub remote는
public application deployment나 remote DB가 아니다.

## 역할별 PR·병합

- 인간 Frontend 팀원은 frontend 전체 범위를 작성할 수 있지만 자가 병합은
  `apps/web/src/**`, `tools/web-e2e/e2e/**`, 정확히 하나의 신규 `IMP-*-web-*.md`와 그 행만
  append한 INDEX로 제한한다. 기존 노트/INDEX 행 수정·삭제, rename의 old/new 경계 이탈은 금지한다.
- `package.json`/lockfile, `.github/**`, 공용 계약/generated type, backend, DB/migration,
  official/staging data, privacy/security/approval 정책이 포함되면 자가 병합하지 않고 사용자
  검토로 승격한다.
- Codex Cloud는 `codex/**` branch와 Draft PR까지만 만들고 스스로 병합하지 않는다. local Codex는
  현재 task의 명시적 인간 승인 범위만 따른다.
- GitHub Free private repository에서 branch protection을 전제하지 않으므로 direct `main` push 금지,
  PR-only, green evidence와 작은 revert 가능한 commit을 사람 규칙으로 지킨다.
- API/contract 간극은 frontend 임의 type으로 메우지 않고 `[CONTRACT]` Issue로 요청한다.

기본 흐름:

```text
origin/main 갱신 → task branch → 작은 commit → push → Draft/Ready PR
→ scope/CI 확인 → 구현 노트·diff review → 권한 있는 인간 merge → branch 정리
```

## 커밋 예시

```text
feat(api): add typed chat fallback contract
feat(web): render server-provided source cards
test(security): verify raw question is never persisted
docs(impl): add IMP-20260713-001 discovery note
```

## 새 의존성

프로덕션 의존성 추가 전 다음을 기록하고 인간 승인을 받는다.

- 왜 표준 라이브러리/기존 의존성으로 해결할 수 없는가
- 라이선스·보안·유지관리 상태
- 번들/런타임/비용 영향
- 대안
- 제거/롤백 방법

개발 전용 의존성도 테스트/도구 가치와 유지비를 설명한다.

## PR/리뷰 체크

- 범위와 P0/P1/P2 일치
- 공개 API/DB 호환성
- 개인정보 원문 노출 여부
- ACTIVE KB 전용 검색
- mock/공식 데이터 표시
- 실패·빈 상태·장애 경로
- 접근성·모바일
- 테스트와 구현 노트
- actor/변경 경로가 self-merge 또는 owner-review 경계와 일치
- 비밀·시민 질문·DSN·token·local env·Docker artifact 0
