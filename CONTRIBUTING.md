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

Q-GIT/Q-COLLAB 결정에 따라 private `tskwak111/Sejong_AI` source remote가 연결됐다. 최초 push는
`5e09deccc7205503df07d938b6d4a88f4d5a327e`에서 보통의 `git push -u origin main`만 사용했고,
PR #1 병합 뒤 canonical remote `main`은 `ce8a6085fb57670ca74e009ed45e3d02d784c24b`다. 해당 SHA의
hosted policy `29782433649`와 Frontend CI `29782433682`가 통과했다. primary local `main`은 자체
worktree에서 안전하게 fast-forward하기 전까지 초기 SHA에 남아 있으므로 local/remote가 같다고 전제하지
않는다. `koregy`의 accepted write access, `FRONTEND_COLLABORATOR_LOGIN=koregy`, read-only default
Actions permissions와 repository-description direct-push warning은 확인됐다.
MFA/recovery와 첫 Task 7 PR-only/no-direct-main-push rehearsal은 팀원이 직접 확인해야 한다.
Codex App의 **Only select repositories / `Sejong_AI`**와 secret-free `sejong-ai-cloud-docs` 환경 저장은
확인됐다. Cloud docs-only task/Draft PR/manual merge 및 teammate self-merge rehearsal은 아직 없다.
실행 뒤에도 각 작업자는 변경 영역의 local 검증과 구현 노트 의무를 유지한다. GitHub remote는 public
application deployment나 remote DB가 아니다.

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

remote가 연결된 뒤 PR head를 분류할 때는 GitHub가 전달한 full base/head commit SHA와 repository
variable의 exact Frontend login을 사용한다.

```text
python -B scripts/check_collaboration_scope.py --base-sha <full-sha> --head-sha <full-sha> \
  --pr-author <login> --frontend-login <configured-login>
```

`FRONTEND_SELF_MERGE_ELIGIBLE`만 Frontend 자가 병합 후보이며, exit 0의
`OWNER_REVIEW_REQUIRED`는 검사 성공이지 병합 승인이 아니다. exit 2 `OPERATIONAL_ERROR`, docs/
current-tree secret/contract/frontend gate 실패, final summary 누락은 모두 병합 중지다. GitHub
Actions는 trusted base의 검사기로 별도 candidate checkout을 검사하고 read-only token을 사용한다.
CI 결과도 구현 노트·diff review와 인간 정책을 대체하지 않는다.

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
