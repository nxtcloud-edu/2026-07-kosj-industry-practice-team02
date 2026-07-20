from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import check_repository_docs as repository_docs
from scripts.check_repository_docs import RepositoryCheckError, check_repository


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/check_repository_docs.py"


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

    def stage_index_entry(
        self,
        repository: Path,
        mode: str,
        relative_path: str,
        contents: str,
    ) -> None:
        hashed = subprocess.run(
            ["git", "-C", str(repository), "hash-object", "-w", "--stdin"],
            input=contents.encode("utf-8"),
            check=True,
            capture_output=True,
        )
        object_id = hashed.stdout.decode("ascii").strip()
        subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "update-index",
                "--add",
                "--cacheinfo",
                f"{mode},{object_id},{relative_path}",
            ],
            check=True,
            capture_output=True,
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

        self.assertEqual(
            errors,
            [
                'REPO_DOCS_MISSING_MARKDOWN_TARGET source="docs/index.md" '
                "line=1 ordinal=1"
            ],
        )

    def test_reports_malformed_tracked_json_without_echoing_contents(self) -> None:
        repository = self.make_repository()
        malformed_contents = '{"private_value": '
        self.track(repository, "data/bad.json", malformed_contents)

        errors = check_repository(repository)

        self.assertTrue(any("REPO_DOCS_INVALID_JSON" in error for error in errors))
        self.assertFalse(any(malformed_contents in error for error in errors))

    def test_rejects_non_standard_json_numeric_constants(self) -> None:
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                repository = self.make_repository()
                self.track(repository, "data/value.json", f'{{"value": {constant}}}\n')

                errors = check_repository(repository)

                self.assertEqual(len(errors), 1)
                self.assertIn("REPO_DOCS_INVALID_JSON", errors[0])
                self.assertNotIn(constant, errors[0])

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

    def test_four_backtick_fence_requires_same_marker_and_opener_length(self) -> None:
        repository = self.make_repository()
        self.track(
            repository,
            "docs/index.md",
            "````md\n"
            "[ignored](missing-one.md)\n"
            "```\n"
            "[still ignored](missing-two.md)\n"
            "````\n"
            "[real](exists.md)\n",
        )
        self.track(repository, "docs/exists.md", "# exists\n")

        self.assertEqual(check_repository(repository), [])

    def test_tilde_fence_requires_whitespace_only_close_of_sufficient_length(self) -> None:
        repository = self.make_repository()
        self.track(
            repository,
            "docs/index.md",
            "~~~~ info\n"
            "[ignored](missing-one.md)\n"
            "```\n"
            "[still ignored](missing-two.md)\n"
            "~~~\n"
            "[also ignored](missing-three.md)\n"
            "~~~~ not-a-close\n"
            "[yet ignored](missing-four.md)\n"
            "~~~~  \t\n"
            "[real](exists.md)\n",
        )
        self.track(repository, "docs/exists.md", "# exists\n")

        self.assertEqual(check_repository(repository), [])

    def test_backtick_in_backtick_fence_info_does_not_open_fence(self) -> None:
        repository = self.make_repository()
        self.track(
            repository,
            "docs/index.md",
            "```lang`invalid\n[missing](not-found.md)\n```\n",
        )

        self.assertEqual(
            check_repository(repository),
            [
                'REPO_DOCS_MISSING_MARKDOWN_TARGET source="docs/index.md" '
                "line=2 ordinal=1"
            ],
        )

    def test_rejects_tracked_symlink_before_reading_its_target(self) -> None:
        repository = self.make_repository()
        self.stage_index_entry(
            repository,
            "120000",
            "docs/external.md",
            "../../outside-sensitive-file",
        )

        with self.assertRaisesRegex(
            RepositoryCheckError,
            r'^REPO_DOCS_UNSUPPORTED_TRACKED_ENTRY source="docs/external.md" mode="120000"$',
        ):
            check_repository(repository)

    def test_rejects_tracked_gitlink_before_blob_inspection(self) -> None:
        repository = self.make_repository()
        self.stage_index_entry(repository, "160000", "vendor/component", "not-read")

        with self.assertRaisesRegex(
            RepositoryCheckError,
            r'^REPO_DOCS_UNSUPPORTED_TRACKED_ENTRY source="vendor/component" mode="160000"$',
        ):
            check_repository(repository)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink API unavailable")
    def test_reads_regular_tracked_json_from_git_blob_not_external_worktree_symlink(self) -> None:
        repository = self.make_repository()
        self.track(repository, "data/safe.json", "{}\n")
        external = repository.parent / f"{repository.name}-external.json"
        external.write_text('{"EXTERNAL_CONTENT_SENTINEL": ', encoding="utf-8")
        self.addCleanup(external.unlink, missing_ok=True)
        tracked_path = repository / "data/safe.json"
        tracked_path.unlink()
        try:
            tracked_path.symlink_to(external)
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {error.__class__.__name__}")

        self.assertEqual(check_repository(repository), [])

    def test_missing_link_diagnostic_redacts_destination_and_control_characters(self) -> None:
        repository = self.make_repository()
        destination_sentinel = "SECRET_DESTINATION_SENTINEL%0A%1B%5B31m"
        self.track(
            repository,
            "docs/index.md",
            f"[missing](./{destination_sentinel}.md)\n",
        )

        errors = check_repository(repository)
        completed = subprocess.run(
            [sys.executable, str(CHECKER), "--repository-root", str(repository)],
            check=False,
            capture_output=True,
            text=True,
        )
        combined = "".join(errors) + completed.stdout + completed.stderr

        self.assertEqual(completed.returncode, 1)
        self.assertNotIn("SECRET_DESTINATION_SENTINEL", combined)
        self.assertNotIn("\x1b", combined)
        self.assertFalse(any("\n" in error or "\r" in error for error in errors))
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr.count("\n"), 1)

    def test_json_escapes_control_characters_in_untrusted_source_path(self) -> None:
        source_path = "docs/control-\n-\x1b.md"

        escaped = repository_docs.escape_source_path(source_path)

        self.assertEqual(escaped, json.dumps(source_path, ensure_ascii=True))
        self.assertNotIn("\n", escaped)
        self.assertNotIn("\x1b", escaped)

    def test_rejects_single_blob_over_byte_limit_without_content_output(self) -> None:
        repository = self.make_repository()
        sentinel = "SINGLE_BLOB_CONTENT_SENTINEL"
        self.track(repository, "docs/large.md", sentinel)

        with mock.patch.object(repository_docs, "MAX_ACTIVE_BLOB_BYTES", 8):
            with self.assertRaises(RepositoryCheckError) as raised:
                check_repository(repository)

        message = str(raised.exception)
        self.assertIn("REPO_DOCS_BLOB_LIMIT_EXCEEDED", message)
        self.assertNotIn(sentinel, message)

    def test_rejects_aggregate_blobs_over_byte_limit_without_content_output(self) -> None:
        repository = self.make_repository()
        sentinel = "AGGREGATE_BLOB_CONTENT_SENTINEL"
        self.track(repository, "docs/one.md", f"{sentinel}-one")
        self.track(repository, "docs/two.md", f"{sentinel}-two")

        with (
            mock.patch.object(repository_docs, "MAX_ACTIVE_BLOB_BYTES", 128),
            mock.patch.object(repository_docs, "MAX_ACTIVE_TOTAL_BYTES", 40),
        ):
            with self.assertRaises(RepositoryCheckError) as raised:
                check_repository(repository)

        message = str(raised.exception)
        self.assertIn("REPO_DOCS_AGGREGATE_LIMIT_EXCEEDED", message)
        self.assertNotIn(sentinel, message)

    def test_rejects_invalid_object_id_before_cat_file(self) -> None:
        repository = self.make_repository()
        record = repository_docs.TrackedBlob(
            mode="100644",
            object_id="A" * 40,
            relative_path="docs/index.md",
        )

        with mock.patch("scripts.check_repository_docs.subprocess.Popen") as popen:
            with self.assertRaisesRegex(
                RepositoryCheckError,
                "REPO_DOCS_INVALID_OBJECT_ID",
            ):
                repository_docs.read_git_blobs(repository, [record])

        popen.assert_not_called()

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
