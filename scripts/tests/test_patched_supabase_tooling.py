from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = ROOT / "scripts" / "supabase-cli.local-patch.source.json"
RUNTIME_MANIFEST = ROOT / "scripts" / "supabase-cli.local-patch.runtime.json"
PATCH_PATH = ROOT / "scripts" / "patches" / "supabase-cli-v2.109.1-db-loopback.patch"
BOOTSTRAP_PATH = ROOT / "scripts" / "bootstrap_patched_supabase.ps1"

EXPECTED_SOURCE = {
    "schema_version": 1,
    "upstream": {
        "repository": "https://github.com/supabase/cli.git",
        "tag": "v2.109.1",
        "tag_object_sha1": "9d25ff8b5b0fba3c6f0ef000e7dd658c8d710c38",
        "commit_sha1": "6d4c19870ed213ba7f682f117d0345c8a40bfa94",
    },
    "go": {
        "version": "1.25.11",
        "platform": "windows-amd64",
        "url": "https://dl.google.com/go/go1.25.11.windows-amd64.zip",
        "sha256": "b7401f1b41517428e537493316256fb7cf03c66a130a0103ab07f3a2152e2112",
    },
    "patch": {
        "relative_path": "scripts/patches/supabase-cli-v2.109.1-db-loopback.patch",
        "size_bytes": 1824,
        "sha256": "109c096480e8185d761e9ce8fba10e93efc55190c42eab978f769a6993833f7d",
        "allowed_files": [
            "apps/cli-go/internal/db/start/start_test.go",
            "apps/cli-go/internal/db/start/start.go",
        ],
    },
    "build": {
        "working_directory": "apps/cli-go",
        "version": "2.109.1",
        "goos": "windows",
        "goarch": "amd64",
        "cgo_enabled": "0",
        "goproxy": "https://proxy.golang.org",
        "gosumdb": "sum.golang.org",
        "goprivate": "",
        "gonoproxy": "",
        "gonosumdb": "",
        "goinsecure": "",
        "goenv": "off",
        "gowork": "off",
        "gotoolchain": "local",
        "goflags": "",
        "goamd64": "v1",
        "goexperiment": "",
        "flags": ["-trimpath", "-buildvcs=false"],
        "ldflags": "-s -w -X github.com/supabase/cli/internal/utils.Version=2.109.1",
    },
}


class PatchedSourceLockTests(unittest.TestCase):
    def test_source_manifest_is_exact(self) -> None:
        self.assertTrue(SOURCE_MANIFEST.is_file())
        self.assertEqual(
            json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8")),
            EXPECTED_SOURCE,
        )

    def test_patch_bytes_hash_and_scope_are_exact(self) -> None:
        payload = PATCH_PATH.read_bytes()
        self.assertEqual(len(payload), EXPECTED_SOURCE["patch"]["size_bytes"])
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            EXPECTED_SOURCE["patch"]["sha256"],
        )
        self.assertNotIn(b"\r\n", payload)
        text = payload.decode("utf-8")
        changed = re.findall(r"^diff --git a/(\S+) b/(\S+)$", text, re.MULTILINE)
        self.assertEqual(
            changed,
            [(path, path) for path in EXPECTED_SOURCE["patch"]["allowed_files"]],
        )
        self.assertEqual(text.count('HostIP: "127.0.0.1"'), 1)
        self.assertNotIn("internal/db/diff", text)


if __name__ == "__main__":
    unittest.main()
