from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import check_collaboration_note_append as note_append
from scripts import check_collaboration_scope as scope
from scripts import data_staging_validation as staging_validation


ROOT = Path(__file__).resolve().parents[2]
SCOPE_SCRIPT = ROOT / "scripts" / "check_collaboration_scope.py"
INDEX_PATH = "docs/implementation-notes/INDEX.md"
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40


def run_git(cwd: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git command failed: args={arguments!r} exit={result.returncode} "
            f"stderr_lines={len(result.stderr.splitlines())}"
        )
    return result.stdout.strip()


class TemporaryGitRepository:
    def __init__(self, object_format: str = "sha1") -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="sejong collaboration scope ")
        self.root = Path(self._temporary.name)
        init_arguments = ["init", "--quiet"]
        if object_format != "sha1":
            init_arguments.append(f"--object-format={object_format}")
        run_git(self.root, *init_arguments)
        run_git(self.root, "config", "user.name", "Synthetic Test User")
        run_git(self.root, "config", "user.email", "synthetic@example.invalid")
        run_git(self.root, "config", "core.autocrlf", "false")
        run_git(self.root, "config", "diff.renames", "true")
        self.write(
            INDEX_PATH,
            "\n".join(
                (
                    "# Implementation Notes Index",
                    "",
                    "| Note | Date | Task | Type | Summary | Versions | Status |",
                    "|---|---|---|---|---|---|---|",
                    "| [IMP-20260719-001](IMP-20260719-001-existing.md) | 2026-07-19 | TEST-BASE | test | Existing row | unchanged | Done |",
                    "",
                )
            ),
        )
        self.write("apps/web/src/existing.tsx", "export const existing = true;\n")
        self.base_sha = self.commit("baseline")

    def __enter__(self) -> TemporaryGitRepository:
        return self

    def __exit__(self, *_args: object) -> None:
        self._temporary.cleanup()

    def write(self, relative_path: str, content: str) -> None:
        path = self.root / Path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    def append(self, relative_path: str, content: str) -> None:
        path = self.root / Path(relative_path)
        current = path.read_text(encoding="utf-8")
        path.write_text(current + content, encoding="utf-8", newline="\n")

    def commit(self, message: str) -> str:
        run_git(self.root, "add", "-A")
        run_git(self.root, "commit", "--quiet", "-m", message)
        sha = run_git(self.root, "rev-parse", "HEAD")
        if len(sha) not in (40, 64):
            raise AssertionError("test repository did not produce a full commit SHA")
        return sha


def run_classifier(
    repository: TemporaryGitRepository,
    base_sha: str,
    head_sha: str,
    *,
    pr_author: str | None = "frontend-owner",
    frontend_login: str | None = "frontend-owner",
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "-B",
        str(SCOPE_SCRIPT),
        "--base-sha",
        base_sha,
        "--head-sha",
        head_sha,
    ]
    if pr_author is not None:
        command.extend(("--pr-author", pr_author))
    if frontend_login is not None:
        command.extend(("--frontend-login", frontend_login))
    return subprocess.run(
        command,
        cwd=repository.root,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        env=environment,
    )


def parse_result(test: unittest.TestCase, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    test.assertEqual(result.stderr, "", f"unexpected stderr lines={len(result.stderr.splitlines())}")
    test.assertEqual(len(result.stdout.splitlines()), 1, "classifier must emit one stable JSON line")
    parsed = json.loads(result.stdout)
    test.assertEqual(set(parsed), {"classification", "counts", "paths"})
    test.assertEqual(set(parsed["counts"]), {"changes", "paths"})
    return parsed


def index_row(note_name: str) -> str:
    identifier = note_name.removeprefix("IMP-").split("-web-", 1)[0]
    return (
        f"| [IMP-{identifier}]({note_name}) | 2026-07-20 | WEB-TEST | "
        "implementation/frontend | Synthetic note | unchanged | Done |"
    )


def valid_append_diff(note_path: str) -> bytes:
    note_name = note_path.rsplit("/", 1)[-1]
    row = index_row(note_name)
    return (
        f"diff --git a/{note_path} b/{note_path}\n"
        "new file mode 100644\n"
        "index 0000000..1111111\n"
        "--- /dev/null\n"
        f"+++ b/{note_path}\n"
        "@@ -0,0 +1,2 @@\n"
        "+# Synthetic implementation note\n"
        "+Body that remains private to the validator.\n"
        f"diff --git a/{INDEX_PATH} b/{INDEX_PATH}\n"
        "index 2222222..3333333 100644\n"
        f"--- a/{INDEX_PATH}\n"
        f"+++ b/{INDEX_PATH}\n"
        "@@ -1,2 +1,3 @@\n"
        " # Implementation Notes Index\n"
        " | existing row |\n"
        f"+{row}\n"
    ).encode("utf-8")


class ScopePolicyUnitTests(unittest.TestCase):
    def test_name_status_git_invocation_is_argument_safe_and_nul_delimited(self) -> None:
        calls: list[tuple[list[str], dict[str, object]]] = []

        def fake_runner(arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
            calls.append((arguments, kwargs))
            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout=b"M\0apps/web/src/page.tsx\0",
                stderr=b"",
            )

        changes = scope.read_name_status(BASE_SHA, HEAD_SHA, runner=fake_runner)

        self.assertEqual(
            calls[0][0],
            ["git", "diff", "--name-status", "-z", BASE_SHA, HEAD_SHA, "--"],
        )
        self.assertNotIn("shell", calls[0][1])
        self.assertNotIn("cwd", calls[0][1])
        self.assertEqual(changes, [scope.Change("M", ("apps/web/src/page.tsx",))])

    def test_nul_parser_preserves_tabs_newlines_and_rename_sides(self) -> None:
        changes = scope.parse_name_status(
            b"R100\0apps/web/src/old\tname.tsx\0apps/web/src/new\n\x1bname.tsx\0"
        )

        self.assertEqual(
            changes,
            [
                scope.Change(
                    "R100",
                    ("apps/web/src/old\tname.tsx", "apps/web/src/new\n\x1bname.tsx"),
                )
            ],
        )

    def test_malformed_nul_stream_is_operational_error(self) -> None:
        malformed_streams = (
            b"M\0apps/web/src/page.tsx",
            b"M\0",
            b"R100\0apps/web/src/old.tsx\0",
            b"\xff\0apps/web/src/page.tsx\0",
            b"M\0apps/web/src/\xff.tsx\0",
        )
        for stream in malformed_streams:
            with self.subTest(stream=stream), self.assertRaises(scope.OperationalError):
                scope.parse_name_status(stream)

    def test_sha_format_accepts_only_full_40_or_64_hex_values(self) -> None:
        self.assertTrue(scope.is_full_commit_sha("a" * 40))
        self.assertTrue(scope.is_full_commit_sha("B" * 64))
        for invalid in ("a" * 39, "a" * 41, "g" * 40, "--help", "", " a" * 20):
            with self.subTest(invalid=invalid):
                self.assertFalse(scope.is_full_commit_sha(invalid))

    def test_exact_allow_roots_include_typed_api_and_source_config_modules(self) -> None:
        changes = [
            scope.Change("M", ("apps/web/src/api/client.ts",)),
            scope.Change("A", ("apps/web/src/lib/config.ts",)),
            scope.Change("M", ("tools/web-e2e/e2e/chat.spec.ts",)),
        ]

        classification = scope.classify_changes(
            changes,
            pr_author="frontend-owner",
            frontend_login="frontend-owner",
            note_append_valid=False,
        )

        self.assertEqual(classification, scope.FRONTEND_SELF_MERGE_ELIGIBLE)

    def test_deny_overrides_cover_protected_paths_and_source_escapes(self) -> None:
        protected_paths = (
            "apps/web/AGENTS.md",
            "apps/web/.env.example",
            "README.md",
            "next.config.ts",
            "apps/web/package.json",
            "pnpm-lock.yaml",
            ".github/workflows/frontend.yml",
            "contracts/openapi.yaml",
            "packages/shared-contracts/src/generated/api.ts",
            "apps/api/app/main.py",
            "database/schema.sql",
            "supabase/migrations/20260720.sql",
            "data/official/releases/0.1/kb.json",
            scope.DATA_STAGING_PREFIX + "data-001/draft/kb.json",
            "docs/source-of-truth/PRIVACY_POLICY.md",
            "docs/adr/0019-policy.md",
            "apps/web/src/generated/api.ts",
            "apps/web/src/contracts/chat.ts",
            "apps/web/src/policy/privacy.ts",
            "apps/web/src/adr/decision.ts",
            "apps/web/src/.env.local",
            "apps/web/src/.envrc",
            "apps/web/src/README.md",
            "apps/web/src/button.example.tsx",
            "apps/web/src/package.json",
            "apps/web/src/pnpm-lock.yaml",
        )
        for path in protected_paths:
            with self.subTest(path=path):
                classification = scope.classify_changes(
                    [scope.Change("M", (path,))],
                    pr_author="frontend-owner",
                    frontend_login="frontend-owner",
                    note_append_valid=False,
                )
                self.assertEqual(classification, scope.OWNER_REVIEW_REQUIRED)

    def test_policy_and_tests_do_not_trigger_staging_scan_but_runtime_path_does(self) -> None:
        issues: list[staging_validation.ValidationIssue] = []
        staging_validation._scan_runtime_files(
            [SCOPE_SCRIPT, Path(__file__)],
            ROOT,
            issues,
        )
        self.assertEqual([], issues)

        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            runtime_file = fixture_root / "apps" / "runtime.py"
            runtime_file.parent.mkdir(parents=True)
            runtime_file.write_text(
                f'path = "{scope.DATA_STAGING_PREFIX}data-001"\n', encoding="utf-8"
            )
            staging_validation._scan_runtime_files(
                [runtime_file], fixture_root, issues
            )

        self.assertEqual(["RUNTIME_STAGING_REFERENCE"], [issue.code for issue in issues])

    def test_mixed_delete_copy_unknown_empty_and_path_escape_fail_closed(self) -> None:
        cases = (
            [
                scope.Change("M", ("apps/web/src/page.tsx",)),
                scope.Change("M", ("contracts/chat.yaml",)),
            ],
            [scope.Change("D", ("apps/web/src/page.tsx",))],
            [scope.Change("C100", ("apps/web/src/a.tsx", "apps/web/src/b.tsx"))],
            [scope.Change("T", ("apps/web/src/page.tsx",))],
            [scope.Change("U", ("apps/web/src/page.tsx",))],
            [scope.Change("Q", ("apps/web/src/page.tsx",))],
            [scope.Change("M", ("apps/web/src/../../contracts/chat.yaml",))],
            [],
        )
        for changes in cases:
            with self.subTest(changes=changes):
                self.assertEqual(
                    scope.classify_changes(
                        changes,
                        pr_author="frontend-owner",
                        frontend_login="frontend-owner",
                        note_append_valid=False,
                    ),
                    scope.OWNER_REVIEW_REQUIRED,
                )

    def test_rename_is_eligible_only_when_both_sides_are_allowed(self) -> None:
        cases = (
            (
                scope.Change(
                    "R100",
                    ("apps/web/src/old.tsx", "tools/web-e2e/e2e/new.spec.ts"),
                ),
                scope.FRONTEND_SELF_MERGE_ELIGIBLE,
            ),
            (
                scope.Change("R100", ("apps/web/src/old.tsx", "contracts/chat.ts")),
                scope.OWNER_REVIEW_REQUIRED,
            ),
            (
                scope.Change("R100", ("contracts/chat.ts", "apps/web/src/new.tsx")),
                scope.OWNER_REVIEW_REQUIRED,
            ),
        )
        for change, expected in cases:
            with self.subTest(change=change):
                actual = scope.classify_changes(
                    [change],
                    pr_author="frontend-owner",
                    frontend_login="frontend-owner",
                    note_append_valid=False,
                )
                self.assertEqual(actual, expected)

    def test_owner_and_codex_authors_always_require_owner_review(self) -> None:
        allowed = [scope.Change("M", ("apps/web/src/page.tsx",))]
        for author in ("repository-owner", "chatgpt-codex-connector[bot]"):
            with self.subTest(author=author):
                self.assertEqual(
                    scope.classify_changes(
                        allowed,
                        pr_author=author,
                        frontend_login="frontend-owner",
                        note_append_valid=False,
                    ),
                    scope.OWNER_REVIEW_REQUIRED,
                )

    def test_output_is_one_json_line_with_escaped_untrusted_paths(self) -> None:
        path = "apps/web/src/line\n\x1b[31m\tcomponent.tsx"
        rendered = scope.render_result(scope.OWNER_REVIEW_REQUIRED, 1, [path])

        self.assertEqual(len(rendered.splitlines()), 1)
        self.assertIn(r"\n", rendered)
        self.assertIn(r"\u001b", rendered)
        self.assertIn(r"\t", rendered)
        self.assertNotIn("\x1b", rendered)
        parsed = json.loads(rendered)
        self.assertEqual(parsed["paths"], [path])
        self.assertEqual(parsed["counts"], {"changes": 1, "paths": 1})

    def test_append_validator_reads_only_restricted_unified_diff(self) -> None:
        note_path = "docs/implementation-notes/IMP-20260720-901-web-chat-shell.md"
        calls: list[tuple[list[str], dict[str, object]]] = []

        def fake_runner(arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
            calls.append((arguments, kwargs))
            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout=valid_append_diff(note_path),
                stderr=b"",
            )

        valid = note_append.validate_note_and_index_append(
            BASE_SHA,
            HEAD_SHA,
            note_path,
            runner=fake_runner,
        )

        self.assertTrue(valid)
        self.assertEqual(
            calls[0][0],
            [
                "git",
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--no-color",
                "--unified=1000000",
                BASE_SHA,
                HEAD_SHA,
                "--",
                note_path,
                INDEX_PATH,
            ],
        )
        self.assertNotIn("shell", calls[0][1])
        self.assertNotIn("cwd", calls[0][1])

    def test_append_validator_rejects_insertion_or_existing_row_replacement(self) -> None:
        note_path = "docs/implementation-notes/IMP-20260720-901-web-chat-shell.md"
        insertion = valid_append_diff(note_path).replace(
            b"+| [IMP-20260720-901]",
            b"+| [IMP-20260720-901]",
        ).replace(
            b"+| [IMP-20260720-901](IMP-20260720-901-web-chat-shell.md) | 2026-07-20 | WEB-TEST | implementation/frontend | Synthetic note | unchanged | Done |\n",
            b"+| [IMP-20260720-901](IMP-20260720-901-web-chat-shell.md) | 2026-07-20 | WEB-TEST | implementation/frontend | Synthetic note | unchanged | Done |\n | existing tail row |\n",
        ).replace(b"@@ -1,2 +1,3 @@", b"@@ -1,3 +1,4 @@")
        replacement = valid_append_diff(note_path).replace(
            b" | existing row |\n",
            b"-| existing row |\n+| changed existing row |\n",
        ).replace(b"@@ -1,2 +1,3 @@", b"@@ -1,2 +1,3 @@")

        for unified_diff in (insertion, replacement):
            with self.subTest(kind=unified_diff[-80:]):
                actual = note_append.validate_unified_diff(unified_diff, note_path)
                self.assertFalse(actual)

    def test_web_note_filename_uses_safe_ascii_slug_grammar(self) -> None:
        self.assertIsNotNone(
            note_append.web_note_identity(
                "docs/implementation-notes/IMP-20260720-901-web-chat-shell-2.md"
            )
        )
        for unsafe in (
            "docs/implementation-notes/IMP-20260720-901-web-chat shell.md",
            "docs/implementation-notes/IMP-20260720-901-web-채팅.md",
            "docs/implementation-notes/IMP-20260720-901-web--chat.md",
            "docs/implementation-notes/IMP-20260720-901-web-Chat.md",
        ):
            with self.subTest(unsafe=unsafe):
                self.assertIsNone(note_append.web_note_identity(unsafe))


class ScopePolicyCommandTests(unittest.TestCase):
    def test_frontend_changes_in_both_exact_roots_are_eligible_without_content_output(self) -> None:
        with TemporaryGitRepository() as repository:
            file_secret = "synthetic-file-content-must-not-be-reported"
            environment_secret = "synthetic-environment-value-must-not-be-reported"
            repository.write("apps/web/src/page.tsx", file_secret + "\n")
            repository.write("tools/web-e2e/e2e/chat.spec.ts", "test('chat', () => {});\n")
            head_sha = repository.commit("allowed frontend changes")
            environment = os.environ.copy()
            environment["SYNTHETIC_SCOPE_TEST_SECRET"] = environment_secret

            result = run_classifier(
                repository,
                repository.base_sha,
                head_sha,
                environment=environment,
            )
            parsed = parse_result(self, result)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(parsed["classification"], scope.FRONTEND_SELF_MERGE_ELIGIBLE)
        self.assertEqual(parsed["counts"], {"changes": 2, "paths": 2})
        self.assertEqual(
            parsed["paths"],
            ["apps/web/src/page.tsx", "tools/web-e2e/e2e/chat.spec.ts"],
        )
        self.assertNotIn(file_secret, result.stdout + result.stderr)
        self.assertNotIn(environment_secret, result.stdout + result.stderr)

    def test_one_new_web_note_and_one_matching_index_append_are_eligible(self) -> None:
        with TemporaryGitRepository() as repository:
            note_name = "IMP-20260720-901-web-chat-shell.md"
            note_path = f"docs/implementation-notes/{note_name}"
            repository.write(note_path, "# Synthetic note\n\nNo citizen text.\n")
            repository.append(INDEX_PATH, index_row(note_name) + "\n")
            head_sha = repository.commit("valid web note append")

            result = run_classifier(repository, repository.base_sha, head_sha)
            parsed = parse_result(self, result)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(parsed["classification"], scope.FRONTEND_SELF_MERGE_ELIGIBLE)
        self.assertEqual(parsed["counts"], {"changes": 2, "paths": 2})
        self.assertEqual(parsed["paths"], sorted((note_path, INDEX_PATH)))

    def test_duplicate_logical_note_id_requires_owner_review(self) -> None:
        with TemporaryGitRepository() as repository:
            note_name = "IMP-20260719-001-web-duplicate.md"
            note_path = f"docs/implementation-notes/{note_name}"
            repository.write(note_path, "# Duplicate logical ID\n")
            repository.append(INDEX_PATH, index_row(note_name) + "\n")
            head_sha = repository.commit("duplicate implementation note identity")

            result = run_classifier(repository, repository.base_sha, head_sha)
            parsed = parse_result(self, result)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(parsed["classification"], scope.OWNER_REVIEW_REQUIRED)

    def test_crlf_index_append_is_eligible_without_replacing_existing_bytes(self) -> None:
        with TemporaryGitRepository() as repository:
            index_path = repository.root / INDEX_PATH
            crlf_base = index_path.read_text(encoding="utf-8").replace("\n", "\r\n")
            index_path.write_bytes(crlf_base.encode("utf-8"))
            base_sha = repository.commit("CRLF index baseline")

            note_name = "IMP-20260720-904-web-crlf-note.md"
            note_path = f"docs/implementation-notes/{note_name}"
            repository.write(note_path, "# CRLF append test\n")
            index_path.write_bytes(
                index_path.read_bytes() + index_row(note_name).encode("utf-8") + b"\r\n"
            )
            head_sha = repository.commit("append one CRLF index row")

            result = run_classifier(repository, base_sha, head_sha)
            parsed = parse_result(self, result)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(parsed["classification"], scope.FRONTEND_SELF_MERGE_ELIGIBLE)

    def test_index_insert_replacement_multiple_rows_and_mismatched_link_require_review(self) -> None:
        def build_case(kind: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
            with TemporaryGitRepository() as repository:
                note_name = "IMP-20260720-902-web-admin-shell.md"
                note_path = f"docs/implementation-notes/{note_name}"
                repository.write(note_path, "# Synthetic note\n")
                current = (repository.root / INDEX_PATH).read_text(encoding="utf-8")
                row = index_row(note_name)
                if kind == "insert":
                    updated = current.replace("| [IMP-20260719-001]", row + "\n| [IMP-20260719-001]")
                elif kind == "replace":
                    updated = current.replace("Existing row", "Changed existing row") + row + "\n"
                elif kind == "multiple":
                    updated = current + row + "\n" + row.replace("WEB-TEST", "WEB-TEST-2") + "\n"
                elif kind == "mismatch":
                    updated = current + row.replace(note_name, "IMP-20260720-999-web-other.md") + "\n"
                else:
                    raise AssertionError(f"unknown test case: {kind}")
                repository.write(INDEX_PATH, updated)
                head_sha = repository.commit(f"invalid append {kind}")
                result = run_classifier(repository, repository.base_sha, head_sha)
                return result, parse_result(self, result)

        for kind in ("insert", "replace", "multiple", "mismatch"):
            with self.subTest(kind=kind):
                result, parsed = build_case(kind)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(parsed["classification"], scope.OWNER_REVIEW_REQUIRED)

    def test_missing_note_pair_or_existing_note_change_requires_review(self) -> None:
        note_name = "IMP-20260720-903-web-chat.md"
        note_path = f"docs/implementation-notes/{note_name}"

        with TemporaryGitRepository() as repository:
            repository.write(note_path, "# Missing INDEX append\n")
            head_sha = repository.commit("note only")
            note_only = run_classifier(repository, repository.base_sha, head_sha)
            note_only_parsed = parse_result(self, note_only)

        with TemporaryGitRepository() as repository:
            repository.write(note_path, "# Baseline note\n")
            note_base = repository.commit("baseline existing note")
            repository.write(note_path, "# Modified existing note\n")
            note_head = repository.commit("modify existing note")
            modified = run_classifier(repository, note_base, note_head)
            modified_parsed = parse_result(self, modified)

        self.assertEqual(note_only.returncode, 0)
        self.assertEqual(note_only_parsed["classification"], scope.OWNER_REVIEW_REQUIRED)
        self.assertEqual(modified.returncode, 0)
        self.assertEqual(modified_parsed["classification"], scope.OWNER_REVIEW_REQUIRED)

    def test_owner_and_codex_authors_return_green_owner_review_classification(self) -> None:
        with TemporaryGitRepository() as repository:
            repository.write("apps/web/src/page.tsx", "export default function Page() {}\n")
            head_sha = repository.commit("allowed path")
            for author in ("repository-owner", "chatgpt-codex-connector[bot]"):
                with self.subTest(author=author):
                    result = run_classifier(
                        repository,
                        repository.base_sha,
                        head_sha,
                        pr_author=author,
                    )
                    parsed = parse_result(self, result)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(parsed["classification"], scope.OWNER_REVIEW_REQUIRED)

    def test_allowed_rename_passes_and_cross_boundary_rename_requires_review(self) -> None:
        with TemporaryGitRepository() as repository:
            run_git(
                repository.root,
                "mv",
                "apps/web/src/existing.tsx",
                "apps/web/src/renamed.tsx",
            )
            allowed_head = repository.commit("allowed rename")
            allowed = run_classifier(repository, repository.base_sha, allowed_head)
            allowed_parsed = parse_result(self, allowed)

        with TemporaryGitRepository() as repository:
            (repository.root / "contracts").mkdir()
            run_git(
                repository.root,
                "mv",
                "apps/web/src/existing.tsx",
                "contracts/renamed.tsx",
            )
            denied_head = repository.commit("cross boundary rename")
            denied = run_classifier(repository, repository.base_sha, denied_head)
            denied_parsed = parse_result(self, denied)

        self.assertEqual(allowed.returncode, 0)
        self.assertEqual(allowed_parsed["classification"], scope.FRONTEND_SELF_MERGE_ELIGIBLE)
        self.assertEqual(allowed_parsed["counts"], {"changes": 1, "paths": 2})
        self.assertEqual(denied.returncode, 0)
        self.assertEqual(denied_parsed["classification"], scope.OWNER_REVIEW_REQUIRED)

    def test_missing_blank_or_whitespace_logins_are_operational_errors(self) -> None:
        with TemporaryGitRepository() as repository:
            cases = (
                {"pr_author": None, "frontend_login": "frontend-owner"},
                {"pr_author": "", "frontend_login": "frontend-owner"},
                {"pr_author": "   ", "frontend_login": "frontend-owner"},
                {"pr_author": "frontend-owner", "frontend_login": None},
                {"pr_author": "frontend-owner", "frontend_login": ""},
                {"pr_author": "frontend-owner", "frontend_login": "\n"},
            )
            for case in cases:
                with self.subTest(case=case):
                    result = run_classifier(
                        repository,
                        repository.base_sha,
                        repository.base_sha,
                        **case,
                    )
                    parsed = parse_result(self, result)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(parsed["classification"], scope.OPERATIONAL_ERROR)
                    self.assertEqual(parsed["paths"], [])

    def test_invalid_missing_and_non_commit_full_shas_are_operational_errors(self) -> None:
        with TemporaryGitRepository() as repository:
            blob_sha = run_git(repository.root, "hash-object", "apps/web/src/existing.tsx")
            cases = (
                "a" * 39,
                "0" * 40,
                blob_sha,
            )
            for base_sha in cases:
                with self.subTest(base_sha=base_sha):
                    result = run_classifier(
                        repository,
                        base_sha,
                        repository.base_sha,
                    )
                    parsed = parse_result(self, result)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(parsed["classification"], scope.OPERATIONAL_ERROR)

    def test_full_64_hex_shas_resolve_in_a_sha256_repository(self) -> None:
        with TemporaryGitRepository(object_format="sha256") as repository:
            repository.write("apps/web/src/page.tsx", "export default function Page() {}\n")
            head_sha = repository.commit("sha256 allowed path")

            result = run_classifier(repository, repository.base_sha, head_sha)
            parsed = parse_result(self, result)

        self.assertEqual(len(repository.base_sha), 64)
        self.assertEqual(len(head_sha), 64)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(parsed["classification"], scope.FRONTEND_SELF_MERGE_ELIGIBLE)

    def test_forbidden_and_allowed_paths_mixed_together_require_review(self) -> None:
        with TemporaryGitRepository() as repository:
            repository.write("apps/web/src/page.tsx", "export default function Page() {}\n")
            repository.write("contracts/chat.yaml", "openapi: 3.1.0\n")
            head_sha = repository.commit("mixed scope")

            result = run_classifier(repository, repository.base_sha, head_sha)
            parsed = parse_result(self, result)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(parsed["classification"], scope.OWNER_REVIEW_REQUIRED)
        self.assertEqual(parsed["counts"], {"changes": 2, "paths": 2})


if __name__ == "__main__":
    unittest.main()
