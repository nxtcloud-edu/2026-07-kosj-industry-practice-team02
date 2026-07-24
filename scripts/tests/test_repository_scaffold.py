from __future__ import annotations

import json
import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RepositoryScaffoldContractTests(unittest.TestCase):
    def read_required_text(self, relative_path: str) -> str:
        path = ROOT / relative_path
        self.assertTrue(path.is_file(), f"missing required root contract: {relative_path}")
        return path.read_text(encoding="utf-8")

    def test_should_pin_exact_node_and_python_versions(self) -> None:
        self.assertEqual(self.read_required_text(".node-version").strip(), "24.12.0")
        self.assertEqual(self.read_required_text(".python-version").strip(), "3.12.13")

    def test_should_define_private_dependency_free_root_package(self) -> None:
        package = json.loads(self.read_required_text("package.json"))

        self.assertIs(package.get("private"), True)
        self.assertEqual(package.get("packageManager"), "pnpm@11.13.0")
        self.assertEqual(package.get("engines", {}).get("node"), ">=24.0.0 <25.0.0")
        self.assertEqual(package.get("dependencies", {}), {})
        self.assertEqual(package.get("devDependencies", {}), {})

    def test_should_include_active_app_and_package_workspaces(self) -> None:
        workspace = self.read_required_text("pnpm-workspace.yaml")
        entries = {
            match.group(1)
            for line in workspace.splitlines()
            if (match := re.fullmatch(r"\s*-\s+['\"]?([^'\"]+)['\"]?\s*", line))
        }

        self.assertIn("apps/*", entries)
        self.assertIn("packages/*", entries)

    def test_should_pin_exact_uv_without_index_or_credentials(self) -> None:
        uv_toml = self.read_required_text("uv.toml")

        self.assertEqual(uv_toml.strip(), 'required-version = "==0.11.28"')
        self.assertEqual(tomllib.loads(uv_toml), {"required-version": "==0.11.28"})
        lowered = uv_toml.lower()
        for forbidden_setting in (
            "index-url",
            "extra-index-url",
            "default-index",
            "username",
            "password",
            "credential",
            "token",
        ):
            self.assertNotIn(forbidden_setting, lowered)

    def test_should_enforce_exact_saves_and_engine_checks_without_credentials(self) -> None:
        npmrc = self.read_required_text(".npmrc")
        settings = {
            key.strip().lower(): value.strip().lower()
            for line in npmrc.splitlines()
            if line.strip() and not line.lstrip().startswith(("#", ";")) and "=" in line
            for key, value in [line.split("=", 1)]
        }

        self.assertEqual(settings.get("save-exact"), "true")
        self.assertEqual(settings.get("engine-strict"), "true")
        lowered = npmrc.lower()
        for credential_marker in ("_auth", "authtoken", "username=", "password=", "npm_token"):
            self.assertNotIn(credential_marker, lowered)

    def test_should_ignore_repository_transient_paths(self) -> None:
        ignored = {
            line.strip()
            for line in self.read_required_text(".gitignore").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        required = {
            "node_modules/",
            ".pnpm-store/",
            ".next/",
            ".venv/",
            "__pycache__/",
            ".worktrees/",
            ".superpowers/",
            ".tools/",
            "supabase/.temp/",
            "supabase/.branches/",
        }
        self.assertEqual(required - ignored, set())


if __name__ == "__main__":
    unittest.main()
