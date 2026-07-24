from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
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


class RetainedInput(io.BytesIO):
    def close(self) -> None:
        self.flush()


class FakePopenProcess:
    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: bytes = b"",
        stderr: bytes = b"",
    ) -> None:
        self.stdin = RetainedInput()
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode

    def poll(self) -> int:
        return self.returncode

    def terminate(self) -> None:
        pass

    def kill(self) -> None:
        pass


class StallingBatchInput(io.BytesIO):
    def __init__(self, stalled_stage: str, release: threading.Event) -> None:
        super().__init__()
        self._stalled_stage = stalled_stage
        self._release = release

    def write(self, value: bytes) -> int:
        if self._stalled_stage == "stdin":
            self._release.wait()
        return super().write(value)


class StallingBatchOutput:
    def __init__(
        self,
        stalled_stage: str,
        release: threading.Event,
        object_id: bytes,
        content: bytes,
    ) -> None:
        self._stalled_stage = stalled_stage
        self._release = release
        self._stream = io.BytesIO(
            object_id + b" blob " + str(len(content)).encode("ascii") + b"\n" + content + b"\n"
        )
        self._read_calls = 0

    def readline(self, size: int = -1) -> bytes:
        if self._stalled_stage == "header":
            self._release.wait()
        return self._stream.readline(size)

    def read(self, size: int = -1) -> bytes:
        self._read_calls += 1
        if self._stalled_stage == "body" and self._read_calls == 1:
            self._release.wait()
        if self._stalled_stage == "trailing" and self._read_calls == 3:
            self._release.wait()
        return self._stream.read(size)

    def close(self) -> None:
        self._stream.close()


class StallingBatchProcess:
    def __init__(self, stalled_stage: str, object_id: bytes, content: bytes) -> None:
        self.release = threading.Event()
        self.stdin = StallingBatchInput(stalled_stage, self.release)
        self.stdout = StallingBatchOutput(
            stalled_stage,
            self.release,
            object_id,
            content,
        )
        self.stderr = io.BytesIO()
        self.returncode: int | None = None
        self.terminate_called = False

    def wait(self, timeout: float | None = None) -> int:
        if self.returncode is None:
            self.returncode = 0
        return self.returncode

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminate_called = True
        self.returncode = -15
        self.release.set()

    def kill(self) -> None:
        self.returncode = -9
        self.release.set()


def consume_batch_for_test(
    module: ModuleType,
    object_id: bytes,
    failures: list[BaseException],
) -> None:
    try:
        list(
            module._batch_contents(
                Path.cwd(),
                [object_id],
                {object_id: b"blob"},
                environment={"GIT_NO_REPLACE_OBJECTS": "1"},
            )
        )
    except BaseException as error:
        failures.append(error)


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
        contextual_findings = [
            finding
            for finding in findings
            if finding["commit"] == secret_commit and finding["path"] == "<redacted-path>"
        ]
        self.assertEqual(
            {finding["category"] for finding in contextual_findings},
            {
                "ACTUAL_QUESTION_SENTINEL",
                "CREDENTIAL_DATABASE_URL",
                "GITHUB_TOKEN",
                "JWT_LIKE_TOKEN",
                "PRIVATE_KEY_HEADER",
                "PROVIDER_BEARER_KEY",
            },
        )
        for finding in contextual_findings:
            self.assertEqual(set(finding), {"blob", "category", "commit", "path"})
            self.assertEqual(finding["blob"], secret_blob)
            self.assertEqual(finding["commit"], secret_commit)
            self.assertEqual(finding["path"], "<redacted-path>")

    def test_disables_replace_refs_and_detects_original_secret(self) -> None:
        github_token = "gh" + "p_" + ("R" * 32)
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            (repository / "secret.txt").write_text(github_token, encoding="utf-8")
            secret_commit = commit_all(repository, "commit synthetic secret")

            run_command(["git", "checkout", "--orphan", "clean-replacement"], cwd=repository)
            run_command(["git", "rm", "-rf", "."], cwd=repository)
            (repository / "README.md").write_text("clean replacement\n", encoding="utf-8")
            replacement_commit = commit_all(repository, "create clean replacement")
            run_command(["git", "replace", secret_commit, replacement_commit], cwd=repository)

            result = self.run_scanner(repository)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("GITHUB_TOKEN", result.stdout)
        self.assertNotIn(github_token, result.stdout)
        self.assertNotIn(github_token, result.stderr)

    def test_scans_annotated_tag_object_bytes(self) -> None:
        provider_token = "s" + "k-" + "tag_" + ("T" * 24)
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            (repository / "README.md").write_text("clean\n", encoding="utf-8")
            commit_all(repository, "create clean commit")
            run_command(
                ["git", "tag", "-a", "synthetic-tag", "-m", provider_token],
                cwd=repository,
            )

            result = self.run_scanner(repository)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        findings = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertIn("PROVIDER_BEARER_KEY", {item["category"] for item in findings})
        self.assertTrue(any(item["path"] == "<tag-object>" for item in findings))
        self.assertNotIn(provider_token, result.stdout)
        self.assertNotIn(provider_token, result.stderr)

    def test_detects_path_only_secret_with_redacted_json_safe_context(self) -> None:
        github_token = "gh" + "p_" + ("P" * 32)
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            secret_path = repository / f"unicode-한글-{github_token}.txt"
            secret_path.write_text("clean blob content\n", encoding="utf-8")
            secret_commit = commit_all(repository, "add synthetic path fixture")

            result = self.run_scanner(repository)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertNotIn(github_token, result.stdout)
        findings = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertTrue(
            any(
                item["category"] == "GITHUB_TOKEN"
                and item["commit"] == secret_commit
                and item["path"] == "<redacted-path>"
                for item in findings
            )
        )
        for finding in findings:
            self.assertEqual(set(finding), {"blob", "category", "commit", "path"})

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

    def test_detects_local_placeholder_database_url_in_production_path(self) -> None:
        placeholder_url = "postgresql" + "://user:password@localhost:5432/example"
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            (repository / ".env.production").write_text(
                f"DATABASE_URL={placeholder_url}\n", encoding="utf-8"
            )
            production_commit = commit_all(repository, "add unsafe production fixture")

            result = self.run_scanner(repository)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        findings = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertTrue(
            any(
                item["category"] == "CREDENTIAL_DATABASE_URL"
                and item["path"] == ".env.production"
                and item["commit"] == production_commit
                for item in findings
            )
        )
        self.assertNotIn(placeholder_url, result.stdout)
        self.assertNotIn(placeholder_url, result.stderr)

    def test_exact_ignored_secret_stays_out_of_child_argv_env_stdin_and_output(
        self,
    ) -> None:
        module = load_scanner(self)
        exact_secret = "s" + "k-" + "local_exact_" + ("Z" * 24)
        commit_oid = "c" * 40
        blob_oid = "b" * 40
        popen_invocations: list[tuple[list[str], dict[str, object], FakePopenProcess]] = []

        def batch_output() -> bytes:
            output = bytearray()
            for object_id, object_type, content in (
                (
                    commit_oid.encode("ascii"),
                    b"commit",
                    b"tree " + (b"d" * 40) + b"\n\nclean commit\n",
                ),
                (blob_oid.encode("ascii"), b"blob", exact_secret.encode("utf-8")),
            ):
                output.extend(
                    object_id
                    + b" "
                    + object_type
                    + b" "
                    + str(len(content)).encode("ascii")
                    + b"\n"
                )
                output.extend(content + b"\n")
            return bytes(output)

        def fake_popen(command: list[str], **kwargs: object) -> FakePopenProcess:
            command_text = " ".join(command)
            if "check-ignore" in command:
                process = FakePopenProcess()
            elif "rev-list --objects --all" in command_text:
                process = FakePopenProcess(
                    stdout=f"{commit_oid}\n{blob_oid} synthetic.txt\n".encode("ascii")
                )
            elif any(argument.startswith("--batch-check=") for argument in command):
                process = FakePopenProcess(
                    stdout=(f"{commit_oid} commit\n{blob_oid} blob\n").encode("ascii")
                )
            elif "--batch" in command:
                process = FakePopenProcess(stdout=batch_output())
            elif "ls-tree" in command:
                process = FakePopenProcess(
                    stdout=f"100644 blob {blob_oid}\tsynthetic.txt\0".encode("ascii")
                )
            else:
                raise AssertionError(f"unexpected git command: {command!r}")
            popen_invocations.append((list(command), dict(kwargs), process))
            return process

        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            secret_file = repository / ".env"
            secret_file.write_text(f"LLM_API_KEY={exact_secret}\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.dict(os.environ, {"SYNTHETIC_PARENT_SECRET": exact_secret}, clear=False),
                mock.patch.object(module.subprocess, "Popen", side_effect=fake_popen),
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
        self.assertTrue(popen_invocations)
        for command, kwargs, process in popen_invocations:
            self.assertNotIn(exact_secret, repr(command))
            self.assertNotIn(exact_secret, repr(kwargs.get("env")))
            self.assertNotIn(exact_secret.encode("utf-8"), process.stdin.getvalue())
            self.assertEqual(dict(kwargs["env"]).get("GIT_NO_REPLACE_OBJECTS"), "1")

    def test_exact_secret_collision_with_fixed_git_environment_fails_before_child(
        self,
    ) -> None:
        module = load_scanner(self)
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            secret_file = repository / ".env"
            secret_file.write_text("LLM_API_KEY=1\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(module.subprocess, "Popen") as child_process,
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

        self.assertEqual(returncode, 2)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue())["category"], "SCANNER_OPERATIONAL_ERROR")
        child_process.assert_not_called()

    def test_every_git_command_uses_streaming_process(self) -> None:
        module = load_scanner(self)

        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            (repository / "README.md").write_text("clean\n", encoding="utf-8")
            commit_all(repository, "create clean repository")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(
                    module.subprocess,
                    "run",
                    side_effect=AssertionError("every Git command must stream bounded output"),
                ),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = module.main(["--repo", str(repository)])

        self.assertEqual(returncode, 0, stdout.getvalue() + stderr.getvalue())

    def test_git_stderr_over_limit_fails_closed(self) -> None:
        module = load_scanner(self)
        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.object(module, "MAX_GIT_OUTPUT_BYTES", 8),
            self.assertRaises(module.ScannerOperationalError),
        ):
            module._run_git(
                Path(directory),
                ["not-a-real-git-command"],
                environment={"GIT_NO_REPLACE_OBJECTS": "1"},
                accepted_returncodes=(1,),
            )

    def test_batch_git_stderr_over_limit_fails_closed(self) -> None:
        module = load_scanner(self)
        object_id = b"a" * 40
        content = b"clean"

        class FakeBatchProcess:
            def __init__(self) -> None:
                self.stdin = io.BytesIO()
                self.stdout = io.BytesIO(
                    object_id
                    + b" blob "
                    + str(len(content)).encode("ascii")
                    + b"\n"
                    + content
                    + b"\n"
                )
                self.stderr = io.BytesIO(b"x" * 9)

            def wait(self, timeout: float | None = None) -> int:
                return 0

            def poll(self) -> int:
                return 0

            def terminate(self) -> None:
                pass

            def kill(self) -> None:
                pass

        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.object(module, "MAX_GIT_OUTPUT_BYTES", 8),
            mock.patch.object(module.subprocess, "Popen", return_value=FakeBatchProcess()),
            self.assertRaises(module.ScannerOperationalError),
        ):
            list(
                module._batch_contents(
                    Path(directory),
                    [object_id],
                    {object_id: b"blob"},
                    environment={"GIT_NO_REPLACE_OBJECTS": "1"},
                )
            )

    def test_batch_io_stalls_obey_wall_clock_deadline(self) -> None:
        module = load_scanner(self)
        object_id = b"a" * 40
        content = b"clean"

        for stalled_stage in ("stdin", "header", "body", "trailing"):
            with self.subTest(stalled_stage=stalled_stage):
                process = StallingBatchProcess(stalled_stage, object_id, content)
                failures: list[BaseException] = []

                with (
                    mock.patch.object(module, "GIT_TIMEOUT_SECONDS", 0.05),
                    mock.patch.object(module.subprocess, "Popen", return_value=process),
                ):
                    worker = threading.Thread(
                        target=consume_batch_for_test,
                        args=(module, object_id, failures),
                        daemon=True,
                    )
                    worker.start()
                    worker.join(timeout=0.5)
                    missed_deadline = worker.is_alive()
                    if missed_deadline:
                        process.release.set()
                    worker.join(timeout=1)

                self.assertFalse(worker.is_alive(), "stalled test worker did not clean up")
                self.assertFalse(
                    missed_deadline,
                    f"{stalled_stage} I/O exceeded the wall-clock deadline",
                )
                self.assertEqual(len(failures), 1)
                self.assertIsInstance(failures[0], module.ScannerOperationalError)
                self.assertTrue(process.terminate_called)

    def test_per_object_size_limit_fails_operationally(self) -> None:
        module = load_scanner(self)
        self.assertTrue(hasattr(module, "MAX_OBJECT_BYTES"))
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            (repository / "oversized.bin").write_bytes(b"x" * 64)
            commit_all(repository, "add oversized synthetic object")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(module, "MAX_OBJECT_BYTES", 8),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = module.main(["--repo", str(repository)])

        self.assertEqual(returncode, 2)
        self.assertEqual(stderr.getvalue(), "")

    def test_aggregate_object_size_limit_fails_operationally(self) -> None:
        module = load_scanner(self)
        self.assertTrue(hasattr(module, "MAX_AGGREGATE_OBJECT_BYTES"))
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_repository(repository)
            (repository / "one.txt").write_bytes(b"one")
            (repository / "two.txt").write_bytes(b"two")
            commit_all(repository, "add aggregate synthetic objects")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(module, "MAX_OBJECT_BYTES", 1024 * 1024),
                mock.patch.object(module, "MAX_AGGREGATE_OBJECT_BYTES", 10),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = module.main(["--repo", str(repository)])

        self.assertEqual(returncode, 2)
        self.assertEqual(stderr.getvalue(), "")

    def test_child_failure_does_not_relay_untrusted_stdout_or_stderr(self) -> None:
        module = load_scanner(self)
        child_sentinel = "synthetic-child-secret-must-not-be-relayed"
        process = FakePopenProcess(
            returncode=128,
            stdout=child_sentinel.encode("utf-8"),
            stderr=child_sentinel.encode("utf-8"),
        )

        with tempfile.TemporaryDirectory() as directory:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(module.subprocess, "Popen", return_value=process),
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
        process = FakePopenProcess(stdout=b"not-an-object-id\n")

        with tempfile.TemporaryDirectory() as directory:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(module.subprocess, "Popen", return_value=process),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = module.main(["--repo", directory])

        self.assertEqual(returncode, 2)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue())["category"], "SCANNER_OPERATIONAL_ERROR")

    def test_batch_check_rejects_missing_unknown_duplicate_and_mismatched_types(
        self,
    ) -> None:
        module = load_scanner(self)
        object_id = "a" * 40
        other_id = "b" * 40
        scenarios = {
            "missing": f"{object_id} missing\n",
            "unknown": f"{object_id} mystery\n",
            "duplicate": f"{object_id} blob\n{object_id} blob\n",
            "set-mismatch": f"{other_id} blob\n",
            "malformed": f"{object_id} blob extra\n",
        }

        for name, output in scenarios.items():
            with (
                self.subTest(name=name),
                tempfile.TemporaryDirectory() as directory,
                mock.patch.object(module, "_run_git", return_value=output.encode("ascii")),
                self.assertRaises(module.ScannerOperationalError),
            ):
                module._object_types(
                    Path(directory),
                    [object_id.encode("ascii")],
                    environment={"GIT_NO_REPLACE_OBJECTS": "1"},
                )

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
