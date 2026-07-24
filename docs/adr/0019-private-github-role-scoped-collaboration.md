# ADR-0019: 비공개 GitHub 단일 저장소와 역할 제한형 Cloud 협업

- 상태: Accepted
- 날짜: 2026-07-20
- 결정자: 사용자
- 관련 결정: D-047~D-053

## 맥락

저장소는 원본 원격 없이 한 PC의 local `main`으로 운영됐다. 사용자는 해외 체류 중 Codex Cloud를
주로 사용하고, 새 팀원에게 frontend 전체 수직 흐름을 위임하려 한다. 동시에 초기 예산 0원,
개인정보·비밀 미저장, 공개 배포 보류, 계약·DB·공식 데이터의 인간 승인 경계를 유지해야 한다.

GitHub Free private repository에서는 protected branch와 CODEOWNERS를 강제 장치로 전제할 수 없다.
Codex Cloud 결과를 자동 병합하면 사용자의 보안·계약 검토 경계도 약해진다.

## 결정

1. 사용자의 개인 GitHub 계정 아래 단일 private monorepo를 source-control 원격으로 사용한다.
2. 팀원을 collaborator로 추가하고 Codex GitHub 연결은 이 repository 하나로 제한한다.
3. 팀원은 frontend 전체 수직 흐름을 소유하고, 허용 범위와 CI를 만족한 frontend-only PR을
   자가 병합할 수 있다.
4. 계약·backend·DB·migration·official data·privacy/security 정책·의존성 변경은 팀원 자가 병합
   범위가 아니며 사용자 검토로 승격한다.
5. Codex Cloud는 branch와 Draft PR까지만 만들고 사람이 병합한다.
6. DeepSeek 실호출과 Docker/Supabase actual DB 검증은 local-only로 유지한다.
7. GitHub 원격은 source collaboration이며 remote DB·public deployment 승인이 아니다.

구현 전제 처리: 최초 push 전 history audit에서 credential/content secret은 0건이었지만 실제 형태
author/committer email metadata가 확인됐다. Q-GIT-004=A/D-053으로 사용자는 본인 email의 private
Frontend collaborator 공개를 허용했다. 따라서 현재 history·SHA를 보존하고 noreply rewrite를 하지
않는다. D-054로 COLLAB-001 plan 실행은 승인됐으며, pre-push gate와 로컬 collaboration automation을
먼저 구현한다. 실제 remote·push·초대·App 연결은 정확한 account 확인과 사용자 인증 뒤에만 수행한다.

## 결과

### 장점

- 팀원과 사용자가 같은 계약·fixture·history를 공유한다.
- frontend 작업은 사용자의 시차 대기 없이 진행할 수 있다.
- Cloud와 local 사이를 branch·PR·구현 노트로 재현 가능하게 연결한다.
- 실제 비밀과 local-only 검증을 Cloud에서 분리한다.

### 단점과 완화

- GitHub Free에서는 direct push/승인 규칙을 기술적으로 완전히 강제하지 못한다.
  - PR-only 팀 규칙, scope CI, 체크리스트, 작은 PR과 revert runbook으로 완화한다.
- frontend 자가 병합이 contract 경계를 넘을 위험이 있다.
  - 변경 경로와 dependency/contract 여부를 분류하고 경계 변경은 owner review로 전환한다.
- Cloud 검증만으로 Windows/Docker 경로를 증명할 수 없다.
  - `local-verification-required` 표시와 사용자의 local final gate를 유지한다.

## 기각한 대안

- 모든 PR 사용자 승인: 해외 체류 중 병목이 크다.
- frontend/backend 별도 저장소: 현 규모에서 contract와 E2E 동기화 비용이 과도하다.
- GitHub Pro 즉시 도입: 초기 0원 결정을 위반한다.
- Codex Cloud 자동 병합: 사람의 최종 책임 경계를 약화한다.

## 재검토 조건

- GitHub Pro/Team으로 전환해 protected branch·CODEOWNERS를 강제할 수 있을 때
- 실제 시민 데이터, production secret 또는 public deployment가 범위에 들어올 때
- 팀원 수 증가로 actor별 권한과 감사가 팀 규칙만으로 부족할 때
- CI quota·시간이 개발 흐름을 지속적으로 방해할 때
