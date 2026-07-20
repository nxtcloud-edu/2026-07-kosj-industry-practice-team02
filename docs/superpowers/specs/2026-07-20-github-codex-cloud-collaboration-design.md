# GitHub·Codex Cloud 협업 운영 설계

- Status: **Approved / In Progress** — Q-COLLAB-001=A, Q-GIT-004=A, D-054 execution approval
- Date: 2026-07-20
- Human owners: 사용자·Frontend 팀원
- AI executor: Codex local/Cloud
- Related: Q-GIT-001, Q-OWN-001, Q-GIT-002, Q-GIT-003, Q-CLOUD-001, Q-GIT-004,
  D-047~D-054, ADR-0019

## 1. 목표

현재 단일 PC의 local Git 저장소를 사용자의 개인 GitHub 계정 아래 비공개 단일 저장소와
연결한다. 팀원은 프론트엔드 전체 수직 흐름을 맡고, 사용자는 Codex Cloud를 주 작업 환경으로
사용하면서 백엔드·DB·공식 데이터·보안·공개 계약의 최종 책임을 유지한다.

협업 전환은 개발 속도와 해외 체류 중 연속성을 개선해야 하지만 다음 제품 안전 규칙을
완화해서는 안 된다.

- 시민 답변은 ACTIVE 공식 KB에만 근거한다.
- 질문 원문과 비밀은 Git·GitHub·CI·Codex Cloud에 들어가지 않는다.
- 외부 LLM 전 PII 마스킹과 실제 시민 DeepSeek 전송 금지는 유지한다.
- 작성자와 승인자는 분리한다.
- 원격 Git 저장소는 원격 DB나 공개 배포 승인이 아니다.

## 2. 선택한 운영 모델

단일 비공개 모노레포에서 역할을 분리한다.

| 주체 | 쓰기 책임 | 금지·제한 | 병합 권한 |
|---|---|---|---|
| Frontend 팀원 | `apps/web/**`, `tools/web-e2e/**`, frontend 전용 테스트·문서, 자신의 구현 노트 | API·DB·공식 데이터·보안 정책·공용 계약 직접 변경 금지 | 아래 exact self-merge allowlist와 CI를 만족한 PR만 자가 병합 가능 |
| 사용자 + Codex Cloud | `apps/api/**`, `contracts/**`, `packages/shared-contracts/**`, `database/**`, `supabase/**`, `data/official/**`, 정책·계획·통합 | Cloud에서 DeepSeek 실호출·Docker/Supabase actual gate·공개 배포 금지 | Cloud는 branch와 Draft PR까지만; 사용자가 병합 |
| 사용자 local | Docker/Supabase actual 검증, DeepSeek 합성 fixture 검증, 위험 migration·seed·복구 gate | remote/public DB 실행과 비밀 출력 금지 | 증거 확인 뒤 사용자 병합 |

다음 대안은 채택하지 않았다.

- 모든 PR 사용자 승인: 안전하지만 해외 체류·시차 동안 frontend 흐름이 멈춘다.
- frontend/backend 저장소 분리: 현재 규모에서 계약·fixture·E2E 동기화 비용이 크다.
- Cloud 자동 병합: GitHub Free private 저장소의 제한과 사용자 검토 경계를 약화한다.

## 3. 저장소와 권한

- 대상: 사용자 개인 GitHub 계정의 private repository.
- 권장 이름: `sejong-minwon-ai`; 실제 owner와 사용 가능 이름은 실행 시 확인한다.
- 기본 브랜치: `main`.
- 팀원: repository collaborator.
- Codex GitHub 연결: 이 저장소 하나만 허용한다.
- 사용 플랜: GitHub Free, 초기 외부 인프라 예산 0원.

GitHub Free private repository에서는 protected branch와 CODEOWNERS 기반 필수 승인을 운영의
강제 장치로 전제하지 않는다. PR·CI·범위 분류를 증거와 경고로 사용하고, 직접 `main` push 금지는
팀 규칙으로 유지한다. 향후 GitHub Pro 이상을 사용하면 같은 정책을 required PR/status check와
CODEOWNERS로 승격할 수 있다.

## 4. 브랜치와 PR 규칙

### 브랜치

- 팀원: `feat/web-<task-id>-<slug>`
- 사용자 직접 작업: `feat/<task-id>-<slug>` 또는 `fix/<task-id>-<slug>`
- Codex local/Cloud: `codex/<task-id>-<slug>`
- 문서 전용: `docs/<task-id>-<slug>`; Codex가 만들면 `codex/` 접두사를 유지한다.

브랜치는 최신 `origin/main`에서 만들고, 한 PR에는 하나의 TASK ID와 하나의 검토 가능한 목적만
담는다. 장기 브랜치와 여러 수직 흐름을 섞는 PR은 만들지 않는다.

### Frontend 팀원의 자가 병합 조건

다음을 모두 만족할 때만 자가 병합할 수 있다.

1. 제품 동작이 승인된 P0/P1 범위 안이고 TASK ID와 인수 기준이 있다.
2. 변경이 `apps/web/src/**`, `tools/web-e2e/e2e/**`, 정확히 하나의 신규
   `docs/implementation-notes/IMP-*-web-*.md`와 그 신규 행만 append한 INDEX에 한정된다. rename은
   old/new 양쪽이 이 allowlist 안일 때만 가능하다.
3. 공개 계약·생성 공용 타입·backend·DB·migration·official data·privacy/security source-of-truth를
   변경하지 않는다.
4. 기존 implementation note/INDEX 행, `apps/web/AGENTS.md`, `apps/web/.env.example`, README/config,
   모든 `package.json`·lockfile, `.github/**`, 환경변수 계약을 변경하지 않는다.
5. 새 production dependency가 없다.
6. frontend lint·typecheck·unit·build·E2E와 범위 검사가 통과한다.
7. user-visible loading, empty, error, offline, responsive, keyboard와 focus 상태를 검증한다.
8. diff 자체 리뷰와 구현 노트가 완료됐다.

하나라도 만족하지 않으면 Draft 또는 Ready-for-review PR로 남기고 사용자의 승인을 기다린다.
GitHub Free에서 merge 버튼이 보인다는 사실은 정책상 병합 허가를 의미하지 않는다.

## 5. 계약 경계와 협업 프로토콜

팀원은 다음을 read-only 권위로 소비한다.

- `packages/shared-contracts/src/generated/api.ts`
- `contracts/fixtures/**`
- `docs/05_API_AND_CONTRACTS.md`
- `docs/24_UI_STATE_MATRIX.md`
- 관련 ADR과 TASK 인수 기준

필요한 필드·endpoint·상태가 없으면 frontend에서 임의 타입이나 mock 공식 값을 영구 계약처럼
추가하지 않는다. 대신 Issue를 생성한다.

```text
Title: [CONTRACT] <화면/상태>에 필요한 <필드 또는 endpoint>
현재 TASK / 막힌 사용자 흐름 / 현재 계약 경로 / 필요한 최소 shape /
fallback 가능 여부 / 요청 기한 / mock이면 시연용 샘플 표시 방식
```

사용자·Backend·Contract owner가 계약을 승인·구현한 뒤 generated type과 fixture가 갱신되면
팀원이 integration PR을 이어간다. 공용 계약 변경은 frontend·backend·fixture·테스트를 동시에
갱신하는 별도 PR로 취급한다.

## 6. Codex Cloud와 local 실행 경계

Codex Cloud는 GitHub의 선택한 branch/SHA를 격리된 container에서 checkout하고 저장소의
`AGENTS.md`를 따른다. 작업 결과는 branch와 Draft PR로만 전달한다. Cloud task에는 명확한 TASK
ID, 허용 파일, 금지 파일, 인수 기준, 실행 명령, 사람 승인 항목을 함께 준다.

Cloud에서 허용하는 작업:

- backend pure code, contract 초안, 테스트, 문서와 offline/template 경로
- frontend가 아닌 사용자 소유 영역의 branch/Draft PR
- Docker·외부 LLM이 필요 없는 lint·typecheck·unit·contract 검증

Cloud에서 금지하거나 완료 근거로 인정하지 않는 작업:

- DeepSeek API key 저장 또는 실제 호출
- 실제 시민/PII fixture 전송
- Docker Desktop, patched Supabase CLI, exact `127.0.0.1:54322` actual DB gate
- remote DB migration·seed·reset·compensation
- 공개 배포, admin 공개, `/ready=200` 승격
- 사람의 PM 데이터 승인이나 별도 승인자 역할 대행

Cloud와 local 사이의 연속성은 대화 handoff가 아니라 Git branch·commit·Draft PR·구현 노트를
사용한다. local-only gate가 필요한 PR에는 `local-verification-required`를 명시하고 사용자가 귀국
중 local 환경에서 실행 결과를 PR에 기록한다.

## 7. 비밀·개인정보·공식 데이터

- local ignored env의 DeepSeek key, DB DSN, context secret은 GitHub와 Codex Cloud에 복사하지 않는다.
- GitHub Actions와 Cloud 설정에는 현재 비밀이 필요하지 않다.
- 실제 값이 필요한 setup을 새로 도입하려면 목적·범위·로그·회전·삭제를 별도 승인한다.
- `.env*` 중 추적 허용 파일은 값 없는 `.env.example`뿐이다.
- CI 로그에 request body, 질문, 응답, DSN, token, approval comment 원문을 출력하지 않는다.
- official data는 이미 승인된 tracked artifact만 읽으며 팀원이 수정·승인하지 않는다.
- mock은 항상 `시연용 샘플`로 표시하고 official data와 합치지 않는다.

원격 최초 push 전 현재 worktree와 전체 Git history를 비밀·실제 개인정보 관점에서 검사한다.
의심 항목이 발견되면 push를 중단하고 값 회전, history 정리 범위와 협업자 통지를 사용자에게
승인받는다. private repository는 노출 영향도를 낮출 뿐 유출을 무효화하지 않는다.

2026-07-20 read-only 감사에서는 도달 가능한 163개 commit의 credential/content secret이 0건이고,
ignored local LLM key의 exact value도 history 0건이었다. 다만 실제 형태 author/committer email
metadata가 확인돼 A-039/Q-GIT-004로 분리했다. 사용자가 현재 history 보존을 승인하거나 noreply
재작성 계획을 별도로 승인하기 전에는 collaboration commit·remote·push를 수행하지 않는 경계를
두었다. 사용자는 Q-GIT-004=A/D-053으로 본인 email의 private collaborator 공개와 현재 history·SHA
보존을 승인했다. noreply rewrite는 하지 않으며 최초 전송은 계획 승인 뒤 검토된 `main`만 대상으로
하고 `git push --mirror`를 금지한다.

## 8. CI와 실패 처리

최초 협업 CI는 frontend 변경에 필요한 빠른 검증과 범위 분류를 우선한다.

- 항상 실행: 변경 범위 분류, contract generation drift, secret pattern, 문서 링크/JSON 정합성
- frontend 변경: frozen install, lint, typecheck, unit, production build
- frontend E2E 변경: Playwright Chromium E2E
- backend/DB/DATA actual: Cloud CI의 완료 근거가 아니라 owner/local gate로 표시

path-filter 때문에 필수 workflow 자체가 실행되지 않아 영원히 pending 되는 구성을 만들지 않는다.
GitHub Free 단계에서는 CI가 실패하면 병합하지 않는 운영 규칙을 적용한다. runner 장애나 quota
고갈이면 실패를 무시하지 않고 동일 SHA를 local에서 검증해 명령·결과를 PR에 기록한 뒤 사용자
검토를 받는다.

## 9. 충돌·롤백·복구

- merge conflict는 마지막 작성자가 무조건 해결하지 않는다. contract/DB/data/security 충돌은
  owner가, `apps/web/**` 내부 충돌은 frontend 팀원이 해결한다.
- 잘못 병합된 PR은 force push나 history rewrite 대신 새 revert PR로 되돌린다.
- 이미 팀원이 pull한 commit을 rebase 강제하거나 삭제하지 않는다.
- secret이 push된 경우 파일 삭제 commit만으로 해결됐다고 보지 않고 즉시 key를 회전한 뒤
  history 정리 여부를 별도 결정한다.
- `main`이 실패하면 원인 PR 이후 추가 병합을 중지하고 마지막 green commit 기준으로 복구한다.

## 10. 인수 기준

- private repository, collaborator와 repository-limited Codex 연결이 확인된다.
- 최초 push 전 worktree/history secret audit가 Critical 0이고 Q-GIT-004=A consent가 기록됐다.
- 팀원과 사용자가 동일 `origin/main`을 clone/pull할 수 있다.
- branch·PR template·scope classification·frontend CI가 한 test PR에서 동작한다.
- 팀원은 허용 frontend-only PR을 자가 병합하고, 금지 경계 test PR은 병합하지 않고 owner review로
  전환하는 리허설을 수행한다.
- Codex Cloud는 secret 없는 task에서 Draft PR을 만들고 스스로 merge하지 않는다.
- Docker/Supabase/DeepSeek local-only gate와 public deployment blocker가 그대로 남는다.

## 11. 공식 참고

- [Codex Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment.md)
- [Codex GitHub integration and review](https://learn.chatgpt.com/docs/third-party/github.md)
- [Codex agent internet access](https://learn.chatgpt.com/docs/cloud/internet-access.md)
- [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitHub status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
