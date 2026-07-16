# Scripts

```bash
python scripts/new_implementation_note.py --title "제목" --task-id TASK-001 --type feature
python scripts/capture_repo_state.py
python scripts/check_scope_drift.py
python scripts/validate_codex_package.py
```

위 Python 유틸리티와 `scripts/tests/`의 저장소 경계 검사는 Python 표준 라이브러리만 사용한다.

## 단일 로컬 검증 gate

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1 -Offline
```

러너는 Windows PowerShell 5.1+, Node 24.12.0, pnpm 11.13.0, uv 0.11.28과 API venv Python 3.12.13을 먼저 확인한다. 이어 frozen pnpm/uv sync, root tests, Web lint/typecheck/test/synthetic-secret build, API format/lint/mypy/pytest, 계약 생성·diff·test, 두 secret scanner, package validator와 `git diff --check`를 fail-fast로 실행한다.

공개 옵션은 `-Offline` 하나뿐이다. 오프라인 모드는 warm cache를 요구하며 pnpm/uv offline을 강제한다. 성공·실패 하위 명령의 원문 출력은 비밀·경로 유출을 막기 위해 전달하지 않고 stable step ID만 표시한다. child 실패는 해당 종료코드를 보존하고, 버전·실행·복원 같은 운영 오류는 2를 반환한다. 러너 자체는 삭제와 서버 실행을 하지 않는다.

## 프로젝트 로컬 Supabase CLI

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1 -VerifyOnly
```

첫 명령은 고정된 공식 Windows amd64 release archive의 byte count와 SHA-256을 확인한 뒤
`.tools/supabase/v2.109.1/`에 프로젝트 로컬 CLI만 설치한다. 두 번째 명령은 다운로드 없이
설치된 실행 파일과 정확한 버전만 확인한다. 별도 archive를 검증하려면 첫 명령에
`-ArchivePath <zip>`을 추가한다.

이 CLI는 로컬 개발 도구이며 production dependency가 아니다. 스크립트는 Supabase `login`,
`link`, `db push` 또는 다른 remote project operation을 수행하지 않는다.

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
