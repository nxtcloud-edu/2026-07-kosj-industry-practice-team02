# Codex 첫 실행 체크리스트

- [ ] Git 저장소 루트에서 열었는가
- [ ] `AGENTS.md`가 로드되는지 확인했는가
- [ ] `CODEX_START_PROMPT.md`를 첫 메시지로 사용했는가
- [ ] Codex가 제품 코드 전에 discovery report를 만들었는가
- [ ] legacy와 source-of-truth 충돌표가 있는가
- [ ] A/Blocker 질문에 답했는가
- [ ] 결정 로그·ADR·모호성 레지스터가 갱신됐는가
- [ ] 실행계획을 검토하고 명시적으로 승인했는가
- [ ] 첫 구현 노트가 생성됐는가

## Phase 1 로컬 개발 시작

- [ ] Windows PowerShell 5.1 이상인가
- [ ] Node 24.12.0, pnpm 11.13.0, Python 3.12.13, uv 0.11.28 exact 버전인가
- [ ] `apps/web/.env.example`과 `apps/api/.env.example`을 서비스별 로컬 파일로 복사했는가
- [ ] 실제 비밀값·개인정보를 예제 파일이나 Git에 넣지 않았는가
- [ ] `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1`이 통과했는가
- [ ] 기본 gate 이후 `scripts/verify.ps1 -Offline` warm-cache gate가 통과했는가
- [ ] 별도 uvicorn smoke에서 `/health=200`과 DB·승인 seed 전 `/ready=503`을 확인했는가

`-Offline`은 최초 설치 명령이 아니다. DB migration·공식 데이터·외부 LLM·공개 배포는 이 체크리스트의 Phase 1 범위에 포함되지 않는다.
