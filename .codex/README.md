# Codex local setup notes

이 저장소는 `AGENTS.md` 자동 발견을 사용한다. 개인 설정은 사용자의 `~/.codex/config.toml`에 두고, 저장소에는 비밀이나 개인별 권한 설정을 커밋하지 않는다.

권장 시작:

```bash
codex "CODEX_START_PROMPT.md를 읽고 그 절차대로 저장소 발견 감사부터 시작해. 제품 코드는 아직 수정하지 마."
```

지침 확인:

```bash
codex --ask-for-approval never "현재 로드된 AGENTS 지침과 source-of-truth 우선순위를 요약해."
```

처음에는 기본 샌드박스/승인 설정을 유지한다. 파괴적 명령, 외부 배포, DB 삭제, 비밀 변경은 자동 승인하지 않는다.
