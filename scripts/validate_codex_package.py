from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'AGENTS.md', 'CODEX_START_PROMPT.md', 'PLANS.md', 'TASKS.md',
    'docs/00_SOURCE_OF_TRUTH.md', 'docs/02_CURRENT_REPO_AUDIT.md',
    'docs/implementation-notes/INDEX.md', 'docs/implementation-notes/TEMPLATE.md',
    'contracts/openapi-v1.yaml', 'database/schema-v1.draft.sql',
    'versions/manifest.json', '.env.example'
]
missing = [p for p in REQUIRED if not (ROOT / p).exists()]
if missing:
    raise SystemExit('Missing required files:\n- ' + '\n- '.join(missing))
manifest = json.loads((ROOT / 'versions/manifest.json').read_text(encoding='utf-8'))
if 'versions' not in manifest or not manifest['versions']:
    raise SystemExit('Version manifest has no versions.')
root_agents = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
for phrase in ['구현 노트', '원문', 'ACTIVE', 'legacy']:
    if phrase not in root_agents:
        raise SystemExit(f'AGENTS.md missing critical phrase: {phrase}')
print(f'Codex package validation passed: {len(REQUIRED)} required files, version manifest valid.')
