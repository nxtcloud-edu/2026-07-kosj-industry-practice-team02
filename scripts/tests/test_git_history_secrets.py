from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCANNER = ROOT / "scripts" / "check_git_history_secrets.py"


def run_command(arguments: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def initialize_repository(path: Path) -> None:
    run_command(["git", "init", "-b", "main"], cwd=path)
    run_command(["git", "config", "user.name", "Synthetic Test"], cwd=path)
    run_command(
        ["git", "config", "user.email", "synthetic-history@example.invalid"],
        cwd=path,
    )


def commit_all(path: Path, message: str) -> str:
    run_command(["git", "add", "-A"], cwd=path)
    run_command(["git", "commit", "-m", message], cwd=path)
    return run_command(["git", "rev-parse", "HEAD"], cwd=path).stdout.strip()


def load_scanner(testcase: unittest.TestCase) -> ModuleType:
    testcase.assertTrue(SCANNER.is_file(), f"missing history scanner: {SCANNER}")
    spec = importlib.util.spec_from_file_location("check_git_history_secrets", SCANNER)
    testcase.assertIsNotNone(spec)
    testcase.assertIsNotNone(spec.loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GitHistorySecretScannerTests(unittest.TestCase):
    maxDiff = None

    def run_scanner(
        self, repository: Path, *additional_arguments: str
    ) -> subprocess.CompletedProcess[str]:
        self.assertTrue(SCANNER.is_file(), f"missing history scanner: {SCANNER}")
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCANNER),
                "--repo",
                str(repository),
                *additional_arguments,
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_scans_historical_blobs_on_all_refs_and_redacts_every_match(self) -> None:
        github_token = "gh" + "p_" + ("A" * 32)
        provider_token = "s" + "k-" + "synthetic_" + ("B" * 24)
        private_key_header = "-----BEGIN " + "PRIVATE KEY-----"
        credential_url = "postgresql" + "://synthetic-user:synthetic-pass@db.invalid/sejong"
        jwt_token = ".".join(
            (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                "eyJzdWIiOiJzeW50aGV0aWMtaGlzdG9yeSJ9",
                "c3ludGhldGljLXNpZ25hdHVyZS12YWx1ZQ",
            )
        )
        question_sentinel = "ACTUAL_" + "QUESTION_SENTINEL=synthetic-citizen-question-text"
        sensitive_values = (
            github_token,
            provider_token,
            private_key_header,
            credential_url,
            jwt_token,
            question_sentinel,
        )

        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            (repository / "README.md").write_text("clean baseline\n", encoding="utf-8")
            commit_all(repository, "initial clean baseline")

            run_command(["git", "checkout", "-b", "historical-secret"], cwd=repository)
            secret_path = repository / f"historical-{github_token}.txt"
            secret_path.write_text("\n".join(sensitive_values) + "\n", encoding="utf-8")
            secret_commit = commit_all(repository, "add historical synthetic fixture")
            secret_blob = run_command(
                ["git", "rev-parse", f"{secret_commit}:{secret_path.name}"],
                cwd=repository,
            ).stdout.strip()
            secret_path.unlink()
            commit_all(repository, "remove historical synthetic fixture")
            run_command(["git", "checkout", "main"], cwd=repository)

            result = self.run_scanner(repository)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        for value in sensitive_values:
            self.assertNotIn(value, result.stdout)
            self.assertNotIn(value, result.stderr)

        findings = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(
            {finding["category"] for finding in findings},
            {
                "ACTUAL_QUESTION_SENTINEL",
                "CREDENTIAL_DATABASE_URL",
                "GITHUB_TOKEN",
                "JWT_LIKE_TOKEN",
                "PRIVATE_KEY_HEADER",
                "PROVIDER_BEARER_KEY",
            },
        )
        for finding in findings:
            self.assertEqual(set(finding), {"blob", "category", "commit", "path"})
            self.assertEqual(finding["blob"], secret_blob)
            self.assertEqual(finding["commit"], secret_commit)
            self.assertEqual(finding["path"], "<redacted-path>")

    def test_returns_zero_and_no_output_for_clean_reachable_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            (repository / "README.md").write_text(
                "Synthetic repository without credentials.\n", encoding="utf-8"
            )
            commit_all(repository, "initial clean baseline")

            result = self.run_scanner(repository)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_ignores_explicit_local_placeholder_database_url(self) -> None:
        placeholder_url = "postgresql" + "://user:password@localhost:5432/example"
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            (repository / ".env.example").write_text(
                f"DATABASE_URL={placeholder_url}\n", encoding="utf-8"
            )
            commit_all(repository, "add keyless local example")

            result = self.run_scanner(repository)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_exact_ignored_secret_stays_out_of_child_argv_env_stdin_and_output(
        self,
    ) -> None:
        module = load_scanner(self)
        exact_secret = "s" + "k-" + "local_exact_" + ("Z" * 24)
        commit_oid = "c" * 40
        blob_oid = "b" * 40
        invocations: list[tuple[list[str], dict[str, object]]] = []

        def completed(
            command: list[str], returncode: int, stdout: bytes = b"", stderr: bytes = b""
        ) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(command, returncode, stdout, stderr)

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
            invocations.append((list(command), dict(kwargs)))
            command_text = " ".join(command)
            if "check-ignore" in command:
                return completed(command, 0)
            if "rev-list --objects --all" in command_text:
                return completed(
                    command,
                    0,
                    f"{commit_oid}\n{blob_oid} synthetic.txt\n".encode("ascii"),
                )
            if any(argument.startswith("--batch-check=") for argument in command):
                return completed(
                    command,
                    0,
                    (f"{commit_oid} commit\n{blob_oid} blob\n").encode("ascii"),
                )
            if "--batch" in command:
                requested = bytes(kwargs.get("input", b"")).splitlines()
                output = bytearray()
                for object_id in requested:
                    if object_id == commit_oid.encode("ascii"):
                        content = b"tree " + (b"d" * 40) + b"\n\nclean commit\n"
                        object_type = b"commit"
                    elif object_id == blob_oid.encode("ascii"):
                        content = exact_secret.encode("utf-8")
                        object_type = b"blob"
                    else:
                        raise AssertionError(f"unexpected batch object: {object_id!r}")
                    output.extend(
                        object_id
                        + b" "
                        + object_type
                        + b" "
                        + str(len(content)).encode("ascii")
                        + b"\n"
                    )
                    output.extend(content + b"\n")
                return completed(command, 0, bytes(output))
            if "rev-list --all" in command_text:
                return completed(command, 0, f"{commit_oid}\n".encode("ascii"))
            if "ls-tree" in command:
                return completed(
                    command,
                    0,
                    f"100644 blob {blob_oid}\tsynthetic.txt\0".encode("ascii"),
                )
            raise AssertionError(f"unexpected git command: {command!r}")

        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            secret_file = repository / ".env"
            secret_file.write_text(f"LLM_API_KEY={exact_secret}\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.dict(os.environ, {"SYNTHETIC_PARENT_SECRET": exact_secret}, clear=False),
                mock.patch.object(module.subprocess, "run", side_effect=fake_run),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = module.main(
                    [
                        "--repo",
                        str(repository),
                        "--local-secret-file",
                        str(secret_file),
                        "--local-secret-name",
                        "LLM_API_KEY",
                    ]
                )

        self.assertEqual(returncode, 1)
        self.assertIn("LOCAL_SECRET_EXACT", stdout.getvalue())
        self.assertNotIn(exact_secret, stdout.getvalue())
        self.assertNotIn(exact_secret, stderr.getvalue())
        self.assertTrue(invocations)
        for command, kwargs in invocations:
            self.assertNotIn(exact_secret, repr(command))
            self.assertNotIn(exact_secret, repr(kwargs.get("env")))
            self.assertNotIn(exact_secret.encode("utf-8"), bytes(kwargs.get("input", b"")))

    def test_child_failure_does_not_relay_untrusted_stdout_or_stderr(self) -> None:
        module = load_scanner(self)
        child_sentinel = "synthetic-child-secret-must-not-be-relayed"

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(
                command,
                128,
                child_sentinel.encode("utf-8"),
                child_sentinel.encode("utf-8"),
            )

        with tempfile.TemporaryDirectory() as directory:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(module.subprocess, "run", side_effect=fake_run),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = module.main(["--repo", directory])

        self.assertEqual(returncode, 2)
        self.assertNotIn(child_sentinel, stdout.getvalue())
        self.assertNotIn(child_sentinel, stderr.getvalue())
        record = json.loads(stdout.getvalue())
        self.assertEqual(set(record), {"blob", "category", "commit", "path"})
        self.assertEqual(record["category"], "SCANNER_OPERATIONAL_ERROR")

    def test_malformed_git_object_listing_fails_closed(self) -> None:
        module = load_scanner(self)

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(command, 0, b"not-an-object-id\n", b"")

        with tempfile.TemporaryDirectory() as directory:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(module.subprocess, "run", side_effect=fake_run),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = module.main(["--repo", directory])

        self.assertEqual(returncode, 2)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue())["category"], "SCANNER_OPERATIONAL_ERROR")

    def test_ignores_missing_credential_containers_but_keeps_root_npmrc(self) -> None:
        ignored = {
            line.strip()
            for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertTrue(
            {
                "*.pfx",
                "*.jks",
                "*.keystore",
                ".netrc",
                "_netrc",
                ".authinfo",
                ".authinfo.gpg",
                ".pypirc",
                ".npmrc.local",
            }.issubset(ignored)
        )
        self.assertNotIn(".npmrc", ignored)
        self.assertEqual(
            (ROOT / ".npmrc").read_text(encoding="utf-8"),
            "engine-strict=true\nsave-exact=true\n",
        )


if __name__ == "__main__":
    unittest.main()
