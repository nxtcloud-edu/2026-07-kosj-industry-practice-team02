from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_repository_docs import RepositoryCheckError, check_repository


ROOT = Path(__file__).resolve().parents[2]


class RepositoryDocsCheckerTests(unittest.TestCase):
    def make_repository(self) -> Path:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        repository = Path(temporary_directory.name)
        subprocess.run(
            ["git", "init", "--quiet", str(repository)],
            check=True,
            capture_output=True,
            text=True,
        )
        return repository

    def track(self, repository: Path, relative_path: str, contents: str) -> None:
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(repository), "add", "--", relative_path],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_accepts_unicode_target_with_query_and_anchor(self) -> None:
        repository = self.make_repository()
        self.track(
            repository,
            "docs/index.md",
            "[안내](./안내/민원 안내.md?view=full#신청-절차)\n",
        )
        self.track(repository, "docs/안내/민원 안내.md", "# 신청 절차\n")

        self.assertEqual(check_repository(repository), [])

    def test_reports_missing_repository_local_markdown_target(self) -> None:
        repository = self.make_repository()
        self.track(repository, "docs/index.md", "[missing](./not-found.md#section)\n")

        errors = check_repository(repository)

        self.assertTrue(any("missing Markdown target" in error for error in errors))
        self.assertTrue(any("docs/not-found.md" in error for error in errors))

    def test_reports_malformed_tracked_json_without_echoing_contents(self) -> None:
        repository = self.make_repository()
        malformed_contents = '{"private_value": '
        self.track(repository, "data/bad.json", malformed_contents)

        errors = check_repository(repository)

        self.assertTrue(any("invalid JSON" in error for error in errors))
        self.assertFalse(any(malformed_contents in error for error in errors))

    def test_ignores_legacy_and_generated_runtime_directories(self) -> None:
        repository = self.make_repository()
        self.track(repository, "legacy/broken.md", "[missing](missing.md)\n")
        self.track(repository, "legacy/bad.json", "{")
        self.track(repository, "generated/runtime/broken.md", "[missing](missing.md)\n")
        self.track(repository, "generated/runtime/bad.json", "{")
        self.track(repository, ".superpowers/broken.md", "[missing](missing.md)\n")
        self.track(repository, ".superpowers/bad.json", "{")

        self.assertEqual(check_repository(repository), [])

    def test_ignores_links_to_excluded_runtime_artifacts(self) -> None:
        repository = self.make_repository()
        self.track(repository, "docs/index.md", "[report](../runtime/generated-report.md)\n")
        self.track(repository, "docs/notes.md", "[report](../.superpowers/generated-report.md)\n")

        self.assertEqual(check_repository(repository), [])

    def test_accepts_repository_root_relative_markdown_target(self) -> None:
        repository = self.make_repository()
        self.track(repository, "docs/plans/index.md", "[note](docs/notes/record.md)\n")
        self.track(repository, "docs/notes/record.md", "# record\n")

        self.assertEqual(check_repository(repository), [])

    def test_ignores_link_like_text_inside_fenced_code(self) -> None:
        repository = self.make_repository()
        self.track(repository, "docs/index.md", "```md\n[example](missing.md)\n```\n")

        self.assertEqual(check_repository(repository), [])

    def test_fails_closed_when_tracked_file_listing_fails(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)

        with self.assertRaises(RepositoryCheckError):
            check_repository(Path(temporary_directory.name))


class PlaywrightPortabilityTests(unittest.TestCase):
    def test_selects_corepack_command_for_the_current_platform(self) -> None:
        config = (ROOT / "tools/web-e2e/playwright.config.ts").read_text(encoding="utf-8")

        self.assertIn('process.platform === "win32" ? "corepack.cmd" : "corepack"', config)
        self.assertIn("next start", config)
        self.assertNotIn('"corepack.cmd pnpm', config)


if __name__ == "__main__":
    unittest.main()
