# Scripts

```bash
python scripts/new_implementation_note.py --title "제목" --task-id TASK-001 --type feature
python scripts/capture_repo_state.py
python scripts/check_scope_drift.py
python scripts/validate_codex_package.py
```

위 Python 유틸리티와 `scripts/tests/`의 저장소 경계 검사는 Python 표준 라이브러리만 사용한다.

## 보안 경계 검사

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
node scripts/check_web_bundle_secrets.mjs apps/web/.next
```

첫 명령은 Windows PowerShell 5.1 호환 저장소 secret pattern 검사이고, 두 번째 명령은 Node
표준 라이브러리만 사용하는 browser artifact 검사다. 둘 다 clean 0, leak 1, 입력 누락·읽기
실패 같은 운영 오류 2 이상을 반환하며 출력에는 경로·stable rule ID·개수만 포함한다. 검사
범위와 제외 대상, 보장하지 않는 항목은 `SECURITY.md`를 따른다. secret assignment 검사는
일반/`export`, PowerShell `$env:NAME=value`, cmd `set NAME=value` 형식을 포함하지만 등호 없는
`setx NAME value`는 현재 P2 한계로 탐지하지 않는다.
