from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cmd(*args: str) -> str:
    try:
        return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as exc:
        return f"ERROR({exc.returncode}): {exc.output.strip()}"
    except FileNotFoundError:
        return "UNAVAILABLE"


print("# Repository State")
print()
print(f"- root: {ROOT}")
print(f"- branch: {cmd('git', 'branch', '--show-current')}")
print(f"- commit: {cmd('git', 'rev-parse', '--short', 'HEAD')}")
print("- status:")
print("```text")
print(cmd('git', 'status', '--short') or '(clean)')
print("```")
manifest = ROOT / 'versions' / 'manifest.json'
if manifest.exists():
    data = json.loads(manifest.read_text(encoding='utf-8'))
    print("- versions:")
    for key, value in data.get('versions', {}).items():
        print(f"  - {key}: {value}")
