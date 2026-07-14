from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "docs" / "implementation-notes"
INDEX = NOTES / "INDEX.md"
TEMPLATE = NOTES / "TEMPLATE.md"
MANIFEST = ROOT / "versions" / "manifest.json"


def run_git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "not-a-git-repo"


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^0-9a-zA-Z가-힣]+", "-", value).strip("-")
    return value[:60] or "task"


def next_sequence(date_str: str) -> int:
    pattern = re.compile(rf"^IMP-{date_str}-(\d{{3}})-")
    seqs = []
    for path in NOTES.glob(f"IMP-{date_str}-*.md"):
        match = pattern.match(path.name)
        if match:
            seqs.append(int(match.group(1)))
    return max(seqs, default=0) + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--task-id", default="UNASSIGNED")
    parser.add_argument("--type", default="implementation")
    args = parser.parse_args()

    now = datetime.now(ZoneInfo("Asia/Seoul"))
    date_str = now.strftime("%Y%m%d")
    seq = next_sequence(date_str)
    note_id = f"IMP-{date_str}-{seq:03d}"
    filename = f"{note_id}-{slugify(args.title)}.md"
    branch = run_git("branch", "--show-current") or "detached"
    commit = run_git("rev-parse", "--short", "HEAD")
    timestamp = now.isoformat(timespec="seconds")

    content = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{NOTE_ID}}": note_id,
        "{{TITLE}}": args.title,
        "{{TIMESTAMP}}": timestamp,
        "{{TASK_ID}}": args.task_id,
        "{{TYPE}}": args.type,
        "{{BRANCH}}": branch,
        "{{COMMIT}}": commit,
    }
    for key, value in replacements.items():
        content = content.replace(key, value)

    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        versions = manifest.get("versions", {})
        version_lines = "\n".join(f"- {k}: {v}" for k, v in versions.items())
        content = content.replace("## 7. 버전 전후\n", f"## 7. 버전 전후\n\n### 생성 시 매니페스트\n{version_lines}\n")

    output = NOTES / filename
    output.write_text(content, encoding="utf-8")

    index = INDEX.read_text(encoding="utf-8") if INDEX.exists() else "# Implementation Notes Index\n\n| Note ID | Date | Task | Type | Summary | Versions | Status |\n|---|---|---|---|---|---|---|\n"
    row = f"| [{note_id}]({filename}) | {now.date().isoformat()} | {args.task_id} | {args.type} | {args.title} | see note | Draft |\n"
    if not index.endswith("\n"):
        index += "\n"
    INDEX.write_text(index + row, encoding="utf-8")

    print(output.relative_to(ROOT))


if __name__ == "__main__":
    main()
