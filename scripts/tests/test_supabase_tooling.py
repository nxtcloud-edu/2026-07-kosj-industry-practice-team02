from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
PIN_PATH = ROOT / "scripts" / "supabase-cli.version.json"
BOOTSTRAP_PATH = ROOT / "scripts" / "bootstrap_supabase.ps1"
EXPECTED_PIN = {
    "version": "2.109.1",
    "release": "v2.109.1",
    "published_at": "2026-07-07T09:00:28Z",
    "asset": "supabase_2.109.1_windows_amd64.zip",
    "size_bytes": 75309565,
    "url": (
        "https://github.com/supabase/cli/releases/download/v2.109.1/"
        "supabase_2.109.1_windows_amd64.zip"
    ),
    "sha256": "d0d270692cf78b8aa56545461f02cdf929ce9bb94e95e5e66404fd0e7d2c0c16",
}


def powershell_executable() -> str:
    executable = shutil.which("powershell.exe") or shutil.which("powershell")
    if executable is None:
        raise AssertionError("Windows PowerShell 5.1+ is required")
    return executable


def copy_tooling_fixture(root: Path, *, url: str | None = None) -> Path:
    if not BOOTSTRAP_PATH.is_file():
        raise AssertionError(f"missing required tooling file: {BOOTSTRAP_PATH.name}")
    if not PIN_PATH.is_file():
        raise AssertionError(f"missing required tooling file: {PIN_PATH.name}")
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(BOOTSTRAP_PATH, scripts / BOOTSTRAP_PATH.name)
    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    if url is not None:
        pin["url"] = url
    (scripts / PIN_PATH.name).write_text(
        json.dumps(pin, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return scripts / BOOTSTRAP_PATH.name


def run_bootstrap(
    script: Path, *arguments: str, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            powershell_executable(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            *arguments,
        ],
        cwd=cwd,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )


class SupabaseToolPinTests(unittest.TestCase):
    def read_required_text(self, path: Path) -> str:
        self.assertTrue(path.is_file(), f"missing required tooling file: {path.name}")
        return path.read_text(encoding="utf-8")

    def test_exact_official_windows_pin(self) -> None:
        pin = json.loads(self.read_required_text(PIN_PATH))

        self.assertEqual(pin, EXPECTED_PIN)
        parsed_url = urlparse(pin["url"])
        self.assertEqual(parsed_url.scheme, "https")
        self.assertEqual(parsed_url.hostname, "github.com")

    def test_bootstrap_is_local_checksum_gated_and_non_secret(self) -> None:
        script = self.read_required_text(BOOTSTRAP_PATH)
        lowered = script.lower()

        self.assertIn("Get-FileHash", script)
        self.assertIn("Expand-Archive", script)
        self.assertIn(".tools\\supabase", script)
        self.assertIn("$PSScriptRoot", script)
        self.assertIn("--version", script)
        self.assertIn("[PASS] step=VERIFY-SUPABASE-ARCHIVE", script)
        self.assertIn("[PASS] step=VERIFY-SUPABASE-VERSION", script)
        self.assertIsNone(
            re.match(r"\A\s*param\(", script),
            "typed top-level binding can disclose argument errors before controlled handling",
        )
        self.assertIn('"-VerifyOnly"', script)
        self.assertIn('"-ArchivePath"', script)
        self.assertNotIn("Get-Location", script)
        for forbidden_operation in (
            "npm install",
            "winget",
            "supabase login",
            "supabase link",
            "supabase db push",
        ):
            self.assertNotIn(forbidden_operation, lowered)


class SupabaseBootstrapBehaviorTests(unittest.TestCase):
    def assert_stable_output(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertFalse(result.stderr, "bootstrap wrote to stderr")
        for line in result.stdout.splitlines():
            self.assertRegex(
                line,
                r"^\[(?:START|PASS|FAIL)\] step=[A-Z0-9-]+"
                r"(?: reason=[a-z-]+ code=[012])?$",
            )

    def test_verify_only_missing_is_stable_and_never_downloads(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong supabase verify ") as directory:
            root = Path(directory)
            script = copy_tooling_fixture(root)
            unrelated_cwd = root / "unrelated-current-directory"
            unrelated_cwd.mkdir()

            result = run_bootstrap(script, "-VerifyOnly", cwd=unrelated_cwd)

            self.assertEqual(result.returncode, 2)
            self.assertEqual(
                result.stdout.strip(),
                "[FAIL] step=VERIFY-SUPABASE-BINARY reason=missing code=2",
            )
            self.assertFalse((root / ".tools").exists(), "verify-only created local tooling")
            self.assert_stable_output(result)

    def test_archive_path_without_value_is_controlled_before_typed_binding(self) -> None:
        result = run_bootstrap(BOOTSTRAP_PATH, "-ArchivePath", cwd=ROOT)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stdout.strip(),
            "[FAIL] step=VALIDATE-SUPABASE-ARGUMENTS reason=invalid code=2",
        )
        self.assertFalse(result.stderr, "missing value wrote localized binding details")
        combined = result.stdout + result.stderr
        self.assertNotIn(str(ROOT), combined)
        self.assertNotIn(str(BOOTSTRAP_PATH), combined)
        self.assert_stable_output(result)

    def test_duplicate_approved_arguments_are_controlled(self) -> None:
        cases = (
            ("-VerifyOnly", "-VerifyOnly"),
            (
                "-ArchivePath",
                "synthetic-first-archive.zip",
                "-ArchivePath",
                "synthetic-second-archive.zip",
            ),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = run_bootstrap(BOOTSTRAP_PATH, *arguments, cwd=ROOT)

                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    result.stdout.strip(),
                    "[FAIL] step=VALIDATE-SUPABASE-ARGUMENTS reason=invalid code=2",
                )
                self.assertFalse(result.stderr, "duplicate argument wrote binding details")
                for value in arguments:
                    self.assertNotIn(value, result.stdout + result.stderr)
                self.assert_stable_output(result)

    def test_unapproved_argument_is_rejected_before_other_work(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sejong supabase arguments ") as directory:
            root = Path(directory)
            script = copy_tooling_fixture(root)

            result = run_bootstrap(
                script,
                "-VerifyOnly",
                "-UnapprovedArgument",
                cwd=root,
            )

            self.assertEqual(result.returncode, 2)
            self.assertEqual(
                result.stdout.strip(),
                "[FAIL] step=VALIDATE-SUPABASE-ARGUMENTS reason=invalid code=2",
            )
            self.assertFalse((root / ".tools").exists(), "invalid arguments started work")
            self.assert_stable_output(result)

    def test_verify_only_uses_release_directory_and_rejects_wrong_child_version(self) -> None:
        harmless_executable = shutil.which("whoami.exe") or shutil.which("whoami")
        if harmless_executable is None:
            self.fail("a harmless synthetic child executable is required")

        with tempfile.TemporaryDirectory(prefix="sejong supabase child ") as directory:
            root = Path(directory)
            script = copy_tooling_fixture(root)
            binary = root / ".tools" / "supabase" / "v2.109.1" / "supabase.exe"
            binary.parent.mkdir(parents=True)
            shutil.copy2(harmless_executable, binary)

            result = run_bootstrap(script, "-VerifyOnly", cwd=root)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                result.stdout.splitlines(),
                [
                    "[START] step=VERIFY-SUPABASE-VERSION",
                    "[FAIL] step=VERIFY-SUPABASE-VERSION reason=child code=1",
                ],
            )
            self.assertNotIn(binary.name, result.stdout + result.stderr)
            self.assert_stable_output(result)

    def test_same_size_invalid_checksum_fails_without_disclosure_or_extraction(self) -> None:
        marker = b"synthetic-invalid-supabase-archive-value"
        with tempfile.TemporaryDirectory(prefix="sejong supabase checksum ") as directory:
            root = Path(directory)
            script = copy_tooling_fixture(root)
            archive = root / "synthetic-invalid-archive-path.zip"
            with archive.open("wb") as stream:
                stream.write(marker)
                stream.truncate(EXPECTED_PIN["size_bytes"])
            with archive.open("rb") as stream:
                synthetic_digest = hashlib.file_digest(stream, "sha256").hexdigest()

            result = run_bootstrap(script, "-ArchivePath", str(archive), cwd=root)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                result.stdout.splitlines(),
                [
                    "[START] step=VERIFY-SUPABASE-ARCHIVE",
                    "[FAIL] step=VERIFY-SUPABASE-ARCHIVE reason=integrity code=1",
                ],
            )
            combined = result.stdout + result.stderr
            for sensitive_value in (marker.decode("ascii"), archive.name, synthetic_digest):
                self.assertNotIn(sensitive_value, combined)
            self.assertFalse((root / ".tools").exists(), "invalid archive was extracted")
            self.assert_stable_output(result)

    def test_unapproved_url_or_host_is_rejected_without_network(self) -> None:
        urls = (
            "http://github.com/supabase/cli/releases/download/v2.109.1/"
            "supabase_2.109.1_windows_amd64.zip",
            "https://example.com/supabase_2.109.1_windows_amd64.zip",
        )
        for url in urls:
            with self.subTest(url=url), tempfile.TemporaryDirectory(
                prefix="sejong supabase source "
            ) as directory:
                root = Path(directory)
                script = copy_tooling_fixture(root, url=url)
                local_archive = root / "local-source-rejection-fixture.zip"
                local_archive.write_bytes(b"offline-only")

                result = run_bootstrap(
                    script,
                    "-ArchivePath",
                    str(local_archive),
                    cwd=root,
                )

                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    result.stdout.strip(),
                    "[FAIL] step=VALIDATE-SUPABASE-MANIFEST "
                    "reason=unapproved-source code=2",
                )
                self.assertFalse((root / ".tools").exists(), "rejected source was downloaded")
                self.assertNotIn(url, result.stdout + result.stderr)
                self.assert_stable_output(result)


if __name__ == "__main__":
    unittest.main()
