# 인수인계 가이드

새 개발자는 다음 순서로 읽는다.

1. `README.md`
2. `AGENTS.md`
3. `docs/00_SOURCE_OF_TRUTH.md`
4. `docs/source-of-truth/TEAM_DECISIONS.md`
5. `docs/03_ARCHITECTURE.md`
6. `TASKS.md`와 최신 plan
7. 최근 구현 노트 3개
8. 버전 매니페스트
9. DB 작업이면 `docs/handoffs/HANDOFF-20260717-DB-001-LOCAL-BASELINE.md`
10. Frontend 협업이면 `docs/handoffs/HANDOFF-20260720-FRONTEND-COLLABORATOR.md`
11. GitHub App·PR·Cloud·팀원 최초 실행이면 `docs/handoffs/HANDOFF-20260721-OWNER-GITHUB-CLOUD-CHECKLIST.md`

## 인수인계에 반드시 포함

- 현재 브랜치/HEAD/dirty 상태
- 로컬 실행 명령과 요구 버전
- 환경변수 목록(값 제외)
- DB migrate/seed/rollback
- 공식 데이터와 mock 위치
- 완료/미완료 P0/P1
- 테스트 명령과 마지막 결과
- 알려진 위험/버그
- 배포 URL과 소유자(비밀 제외)
- 다음 작업과 acceptance criteria
- source remote owner/name/visibility, `origin`/upstream과 마지막 verified SHA
- collaborator 초대·수락 상태와 역할(인증정보·개인 연락처 제외)
- Codex GitHub App selected-repository scope와 열린 Draft PR
- self-merge/owner-review 책임, local-only pending gate와 revert/revoke 절차

## 재현 기준

처음 보는 사람이 빈 환경에서 다음을 수행할 수 있어야 한다.

```text
clone
→ env example 확인
→ install
→ migrate/seed
→ run web/api
→ run tests
→ REG-01 데모
```

재현이 안 되면 handoff가 완료되지 않은 것이다.

Cloud 작업은 branch·commit·Draft PR·구현 노트가 handoff 권위다. 대화 내용만으로 local과 Cloud의
상태가 이어졌다고 가정하지 않으며, Codex는 스스로 merge하지 않는다.

현재 DB-001 handoff는 local/private 기준선만 다룬다. official seed, READY 200, public admin,
remote deployment, production backup은 후속 작업이며 D-046의 deferred `00700` 구현·검증 전
공개 경로를 열지 않는다.
