from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE = {"legacy", ".git", "node_modules", ".venv", "dist", "build"}
ALLOW_FILES = {
    "docs/02_CURRENT_REPO_AUDIT.md",
    "docs/17_RISK_REGISTER.md",
    "scripts/check_scope_drift.py",
}
CHECK_EXT = {".md", ".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".sql", ".csv"}
PATTERNS = {
    "old_100_test_scope": "test_questions_100",
    "out_of_scope_status_endpoint": "/api/status",
    "legacy_welfare_intent": "YOUTH_JOB",
    "legacy_auto_analytics": "/api/admin/analytics",
    "conditional_out_of_scope_candidate": "조건부 가능",
    "fake_office_phone": "044-000-",
    "fake_office_address": "가상주소",
}

issues = []
for path in ROOT.rglob('*'):
    if not path.is_file() or path.suffix.lower() not in CHECK_EXT:
        continue
    rel = str(path.relative_to(ROOT)).replace('\\', '/')
    if any(part in IGNORE for part in path.relative_to(ROOT).parts) or rel in ALLOW_FILES:
        continue
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue
    for code, needle in PATTERNS.items():
        if needle in text:
            issues.append((code, str(path.relative_to(ROOT)), needle))

if issues:
    print("Scope drift candidates:")
    for code, path, needle in issues:
        print(f"- {code}: {path} contains {needle!r}")
    raise SystemExit(1)
print("No configured scope drift patterns found outside legacy.")
