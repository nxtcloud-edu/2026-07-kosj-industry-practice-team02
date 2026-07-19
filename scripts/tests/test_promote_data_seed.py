from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from scripts.promote_data_seed import cli
from scripts.data_seed_release import (
    CANONICAL_DRAFT_TOKEN,
    RELEASE_VERSION,
    verify_release_directory,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DRAFT = CANONICAL_DRAFT_TOKEN
CANONICAL_RELEASE = "data/official/releases/0.1.0-initial.1"
RELEASED_AT = "2026-07-19T09:20:31+09:00"
EXPECTED_FILES = {
    "approval_manifest.json",
    "compensation.sql",
    "kb_records.json",
    "office_service_mappings.json",
    "offices.json",
    "release_manifest.json",
    "seed.sql",
}


class PromoteDataSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name) / "repository"
        shutil.copytree(REPOSITORY_ROOT / "data", self.root / "data")
        (self.root / "supabase").mkdir(parents=True)
        shutil.copy2(
            REPOSITORY_ROOT / "supabase" / "seed.sql",
            self.root / "supabase" / "seed.sql",
        )
        shutil.copy2(
            REPOSITORY_ROOT / "supabase" / "config.toml",
            self.root / "supabase" / "config.toml",
        )
        self.release = self.root / CANONICAL_RELEASE
        self.prepare_temp = self.release.with_name(f".{RELEASE_VERSION}.prepare")
        self.dispatcher = self.root / "supabase" / "seed.sql"
        self.initial_dispatcher = self.dispatcher.read_bytes()
        self.initial_config = (self.root / "supabase" / "config.toml").read_bytes()

    @staticmethod
    def prepare_args() -> list[str]:
        return [
            "prepare",
            "--draft-dir",
            CANONICAL_DRAFT,
            "--release-version",
            RELEASE_VERSION,
            "--released-at",
            RELEASED_AT,
        ]

    @staticmethod
    def release_args(command: str, token: str = CANONICAL_RELEASE) -> list[str]:
        return [command, "--release-dir", token]

    def run_cli(self, arguments: list[str]) -> tuple[int, str]:
        output = io.StringIO()
        with mock.patch("scripts.promote_data_seed.REPOSITORY_ROOT", self.root):
            with redirect_stdout(output):
                result = cli(arguments)
        return result, output.getvalue()

    def prepare_valid_release(self) -> None:
        result, output = self.run_cli(self.prepare_args())
        self.assertEqual(0, result, output)
        self.assertEqual(
            "[PASS] step=PREPARE-DATA-SEED release=0.1.0-initial.1 "
            "kb=19 office=3 mapping=10\n",
            output,
        )

    @staticmethod
    def hash_tree(root: Path) -> str:
        digest = hashlib.sha256()
        if not root.exists():
            return digest.hexdigest()
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            relative = path.relative_to(root).as_posix().encode("utf-8")
            digest.update(relative)
            if path.is_symlink():
                digest.update(b"LINK")
                digest.update(os.readlink(path).encode("utf-8"))
            elif path.is_file():
                digest.update(b"FILE")
                digest.update(path.read_bytes())
            else:
                digest.update(b"DIR")
        return digest.hexdigest()

    def assert_stable_failure(self, output: str, step: str) -> None:
        self.assertRegex(
            output,
            rf"^\[FAIL\] step={step} reason=[A-Z0-9_]+ issues=[1-9][0-9]*\n$",
        )
        self.assertEqual(1, len(output.splitlines()))
        self.assertNotIn(str(self.root), output)

    def create_reparse_directory(self, alias: Path, target: Path) -> None:
        try:
            alias.symlink_to(target, target_is_directory=True)
            return
        except OSError as symlink_error:
            if os.name != "nt":
                self.skipTest(
                    f"directory symlink unavailable: {type(symlink_error).__name__}"
                )
        junction = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(target)],
            text=True,
            capture_output=True,
            check=False,
        )
        if junction.returncode != 0:
            self.skipTest("directory symlink and junction fixtures are unavailable")

    @staticmethod
    def remove_reparse_directory(alias: Path) -> None:
        if alias.is_symlink():
            alias.unlink()
        elif alias.exists():
            alias.rmdir()

    def test_prepare_writes_verified_seven_file_release_once(self) -> None:
        dispatcher_before = self.dispatcher.read_bytes()

        self.prepare_valid_release()

        self.assertEqual(EXPECTED_FILES, {path.name for path in self.release.iterdir()})
        self.assertFalse(self.prepare_temp.exists())
        self.assertEqual(dispatcher_before, self.dispatcher.read_bytes())
        summary = verify_release_directory(self.root, self.release)
        self.assertEqual(RELEASE_VERSION, summary["release_version"])
        self.assertEqual({"kb": 19, "office": 3, "mapping": 10}, summary["counts"])
        self.assertEqual(
            (self.release / "seed.sql").read_bytes(), summary["seed_sql_bytes"]
        )

        result, output = self.run_cli(self.release_args("verify-release"))
        self.assertEqual(0, result, output)
        self.assertEqual(
            "[PASS] step=VERIFY-DATA-SEED-RELEASE release=0.1.0-initial.1 issues=0\n",
            output,
        )

    def test_existing_release_fails_without_byte_change(self) -> None:
        self.release.mkdir(parents=True)
        (self.release / "sentinel.bin").write_bytes(b"existing-release-sentinel")
        before = self.hash_tree(self.release)

        result, output = self.run_cli(self.prepare_args())

        self.assertEqual(2, result)
        self.assert_stable_failure(output, "PREPARE-DATA-SEED")
        self.assertEqual(before, self.hash_tree(self.release))
        self.assertFalse(self.prepare_temp.exists())

    def test_existing_prepare_temp_fails_without_byte_change(self) -> None:
        self.prepare_temp.mkdir(parents=True)
        (self.prepare_temp / "sentinel.bin").write_bytes(b"existing-temp-sentinel")
        before = self.hash_tree(self.prepare_temp)

        result, output = self.run_cli(self.prepare_args())

        self.assertEqual(2, result)
        self.assert_stable_failure(output, "PREPARE-DATA-SEED")
        self.assertEqual(before, self.hash_tree(self.prepare_temp))
        self.assertFalse(self.release.exists())

    def test_prepare_failure_cleans_only_its_own_partial_temp(self) -> None:
        def write_partially(directory: Path, _bundle: object) -> None:
            (directory / "release_manifest.json").write_bytes(b"partial")
            raise OSError("injected partial write")

        with mock.patch(
            "scripts.promote_data_seed._write_bundle", side_effect=write_partially
        ):
            result, output = self.run_cli(self.prepare_args())

        self.assertEqual(2, result)
        self.assert_stable_failure(output, "PREPARE-DATA-SEED")
        self.assertFalse(self.release.exists())
        self.assertFalse(self.prepare_temp.exists())

    def test_prepare_failure_does_not_delete_replacement_temp(self) -> None:
        def replace_owned_temp(directory: Path, _bundle: object) -> None:
            directory.rmdir()
            directory.mkdir()
            (directory / "sentinel.bin").write_bytes(b"not-owned-by-current-call")
            raise OSError("injected replacement")

        with mock.patch(
            "scripts.promote_data_seed._write_bundle", side_effect=replace_owned_temp
        ):
            result, output = self.run_cli(self.prepare_args())

        self.assertEqual(2, result)
        self.assert_stable_failure(output, "PREPARE-DATA-SEED")
        self.assertFalse(self.release.exists())
        self.assertEqual(
            b"not-owned-by-current-call",
            (self.prepare_temp / "sentinel.bin").read_bytes(),
        )

    def test_prepare_rename_failure_leaves_release_absent_and_cleans_owned_temp(
        self,
    ) -> None:
        with mock.patch(
            "scripts.promote_data_seed.os.rename", side_effect=OSError("injected")
        ):
            result, output = self.run_cli(self.prepare_args())

        self.assertEqual(2, result)
        self.assert_stable_failure(output, "PREPARE-DATA-SEED")
        self.assertFalse(self.release.exists())
        self.assertFalse(self.prepare_temp.exists())

    def test_prepare_publish_race_never_overwrites_new_release_target(self) -> None:
        sentinel = b"concurrent-release-sentinel"

        def create_target_then_fail(_source: Path, target: Path) -> None:
            target.mkdir()
            (target / "sentinel.bin").write_bytes(sentinel)
            raise FileExistsError("injected publish race")

        with mock.patch(
            "scripts.promote_data_seed._rename_create_once",
            side_effect=create_target_then_fail,
        ):
            result, output = self.run_cli(self.prepare_args())

        self.assertEqual(2, result)
        self.assert_stable_failure(output, "PREPARE-DATA-SEED")
        self.assertEqual(sentinel, (self.release / "sentinel.bin").read_bytes())
        self.assertFalse(self.prepare_temp.exists())

    def test_prepare_preserves_raw_tokens_and_rejects_aliases_before_writes(
        self,
    ) -> None:
        cases = {
            "absolute_draft": [
                "prepare",
                "--draft-dir",
                str(self.root / CANONICAL_DRAFT),
                "--release-version",
                RELEASE_VERSION,
                "--released-at",
                RELEASED_AT,
            ],
            "dot_alias": [
                "prepare",
                "--draft-dir",
                f"{CANONICAL_DRAFT.rsplit('/', maxsplit=1)[0]}/./"
                f"{CANONICAL_DRAFT.rsplit('/', maxsplit=1)[1]}",
                "--release-version",
                RELEASE_VERSION,
                "--released-at",
                RELEASED_AT,
            ],
            "parent_alias": [
                "prepare",
                "--draft-dir",
                f"{CANONICAL_DRAFT.rsplit('/', maxsplit=1)[0]}/x/../"
                f"{CANONICAL_DRAFT.rsplit('/', maxsplit=1)[1]}",
                "--release-version",
                RELEASE_VERSION,
                "--released-at",
                RELEASED_AT,
            ],
            "alternate_separator": [
                "prepare",
                "--draft-dir",
                CANONICAL_DRAFT.replace("/", "\\"),
                "--release-version",
                RELEASE_VERSION,
                "--released-at",
                RELEASED_AT,
            ],
            "case_alias": [
                "prepare",
                "--draft-dir",
                f"D{CANONICAL_DRAFT[1:]}",
                "--release-version",
                RELEASE_VERSION,
                "--released-at",
                RELEASED_AT,
            ],
            "version_alias": [
                "prepare",
                "--draft-dir",
                CANONICAL_DRAFT,
                "--release-version",
                "0.1.0-initial.01",
                "--released-at",
                RELEASED_AT,
            ],
            "timestamp_alias": [
                "prepare",
                "--draft-dir",
                CANONICAL_DRAFT,
                "--release-version",
                RELEASE_VERSION,
                "--released-at",
                "2026-07-19T00:20:31Z",
            ],
        }
        for name, arguments in cases.items():
            with self.subTest(name=name):
                result, output = self.run_cli(arguments)
                self.assertEqual(2, result)
                self.assert_stable_failure(output, "PREPARE-DATA-SEED")
                self.assertFalse(self.release.exists())
                self.assertFalse(self.prepare_temp.exists())

    def test_release_commands_reject_every_noncanonical_raw_path_alias(self) -> None:
        self.prepare_valid_release()
        release_hash = self.hash_tree(self.release)
        candidates = (
            str(self.release),
            "data/official/releases/./0.1.0-initial.1",
            "data/official/releases/x/../0.1.0-initial.1",
            r"data\official\releases\0.1.0-initial.1",
            "Data/official/releases/0.1.0-initial.1",
            "data/official/releases/0.1.0-initial.1/",
            "data/official/releases/0.1.0-initial-1",
        )
        for command, step in (
            ("verify-release", "VERIFY-DATA-SEED-RELEASE"),
            ("activate-local-seed", "ACTIVATE-LOCAL-SEED"),
            ("verify-local-seed", "VERIFY-LOCAL-SEED"),
        ):
            for candidate in candidates:
                with self.subTest(command=command, candidate=candidate):
                    result, output = self.run_cli(self.release_args(command, candidate))
                    self.assertEqual(2, result)
                    self.assert_stable_failure(output, step)
                    self.assertEqual(release_hash, self.hash_tree(self.release))
                    self.assertEqual(
                        self.initial_dispatcher, self.dispatcher.read_bytes()
                    )

    def test_release_reparse_component_is_rejected(self) -> None:
        self.prepare_valid_release()
        alias = self.root / "data" / "official"
        target = alias.with_name("official-target")
        alias.rename(target)
        try:
            self.create_reparse_directory(alias, target)
            result, output = self.run_cli(self.release_args("verify-release"))
            self.assertEqual(2, result)
            self.assert_stable_failure(output, "VERIFY-DATA-SEED-RELEASE")
        finally:
            self.remove_reparse_directory(alias)

    def test_release_verification_binds_file_set_schema_lineage_order_and_bytes(
        self,
    ) -> None:
        self.prepare_valid_release()
        release_files = {
            path.name: path.read_bytes()
            for path in self.release.iterdir()
            if path.is_file()
        }
        schema_path = (
            self.root
            / "data"
            / "schemas"
            / "data-seed"
            / "v1"
            / "release-manifest.schema.json"
        )
        schema_bytes = schema_path.read_bytes()

        def add_unexpected() -> None:
            (self.release / "unexpected.bin").write_bytes(b"unexpected")

        def remove_unexpected() -> None:
            (self.release / "unexpected.bin").unlink()

        def malformed_json() -> None:
            (self.release / "release_manifest.json").write_bytes(
                b'{"schema_version":1,"schema_version":1}\n'
            )

        def approval_lineage_drift() -> None:
            path = self.release / "approval_manifest.json"
            path.write_bytes(
                path.read_bytes().replace(b"PM-LOCAL-001", b"PM-LOCAL-999")
            )

        def record_order_drift() -> None:
            path = self.release / "kb_records.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["records"].reverse()
            path.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
                + "\n",
                encoding="utf-8",
            )

        def semantic_hash_drift() -> None:
            path = self.release / "release_manifest.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["seed_semantic_sha256"] = "0" * 64
            path.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
                + "\n",
                encoding="utf-8",
            )

        def generated_seed_drift() -> None:
            path = self.release / "seed.sql"
            path.write_bytes(path.read_bytes() + b"-- drift\n")

        def generated_compensation_drift() -> None:
            path = self.release / "compensation.sql"
            path.write_bytes(path.read_bytes() + b"-- drift\n")

        def strict_schema_drift() -> None:
            payload = json.loads(schema_path.read_text(encoding="utf-8"))
            payload["properties"]["release_version"]["const"] = "wrong"
            schema_path.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
                + "\n",
                encoding="utf-8",
            )

        cases = (
            ("file_set", add_unexpected, remove_unexpected),
            (
                "malformed_json",
                malformed_json,
                lambda: (self.release / "release_manifest.json").write_bytes(
                    release_files["release_manifest.json"]
                ),
            ),
            (
                "approval_lineage",
                approval_lineage_drift,
                lambda: (self.release / "approval_manifest.json").write_bytes(
                    release_files["approval_manifest.json"]
                ),
            ),
            (
                "record_order",
                record_order_drift,
                lambda: (self.release / "kb_records.json").write_bytes(
                    release_files["kb_records.json"]
                ),
            ),
            (
                "semantic_hash",
                semantic_hash_drift,
                lambda: (self.release / "release_manifest.json").write_bytes(
                    release_files["release_manifest.json"]
                ),
            ),
            (
                "seed_regeneration",
                generated_seed_drift,
                lambda: (self.release / "seed.sql").write_bytes(
                    release_files["seed.sql"]
                ),
            ),
            (
                "compensation_regeneration",
                generated_compensation_drift,
                lambda: (self.release / "compensation.sql").write_bytes(
                    release_files["compensation.sql"]
                ),
            ),
            (
                "strict_schema",
                strict_schema_drift,
                lambda: schema_path.write_bytes(schema_bytes),
            ),
        )
        for name, mutate, restore in cases:
            with self.subTest(name=name):
                mutate()
                try:
                    result, output = self.run_cli(self.release_args("verify-release"))
                    self.assertEqual(2, result)
                    self.assert_stable_failure(output, "VERIFY-DATA-SEED-RELEASE")
                finally:
                    restore()

        result, output = self.run_cli(self.release_args("verify-release"))
        self.assertEqual(0, result, output)

    def test_activation_and_idempotent_reactivation_use_verified_seed_bytes(
        self,
    ) -> None:
        self.prepare_valid_release()
        config_before = (self.root / "supabase" / "config.toml").read_bytes()

        result, output = self.run_cli(self.release_args("activate-local-seed"))

        self.assertEqual(0, result, output)
        self.assertEqual(
            "[PASS] step=ACTIVATE-LOCAL-SEED release=0.1.0-initial.1 changed=1\n",
            output,
        )
        self.assertEqual(
            (self.release / "seed.sql").read_bytes(), self.dispatcher.read_bytes()
        )
        self.assertEqual(
            config_before, (self.root / "supabase" / "config.toml").read_bytes()
        )
        self.assertIn(b"[db.seed]", config_before)
        self.assertIn(b"enabled = false", config_before)

        result, output = self.run_cli(self.release_args("activate-local-seed"))
        self.assertEqual(0, result, output)
        self.assertEqual(
            "[PASS] step=ACTIVATE-LOCAL-SEED release=0.1.0-initial.1 changed=0\n",
            output,
        )

        result, output = self.run_cli(self.release_args("verify-local-seed"))
        self.assertEqual(0, result, output)
        self.assertEqual(
            "[PASS] step=VERIFY-LOCAL-SEED release=0.1.0-initial.1 active=1\n",
            output,
        )

    def test_unrelated_dispatcher_drift_fails_closed_without_byte_change(self) -> None:
        self.prepare_valid_release()
        sentinel = b"DO-NOT-LEAK-UNRELATED-DISPATCHER-DRIFT"
        self.dispatcher.write_bytes(sentinel)

        result, output = self.run_cli(self.release_args("activate-local-seed"))

        self.assertEqual(2, result)
        self.assertEqual(sentinel, self.dispatcher.read_bytes())
        self.assert_stable_failure(output, "ACTIVATE-LOCAL-SEED")
        self.assertNotIn("DO-NOT-LEAK", output)

    def test_invalid_release_cannot_activate_dispatcher(self) -> None:
        self.prepare_valid_release()
        (self.release / "seed.sql").write_bytes(b"malformed release seed")

        result, output = self.run_cli(self.release_args("activate-local-seed"))

        self.assertEqual(2, result)
        self.assertEqual(self.initial_dispatcher, self.dispatcher.read_bytes())
        self.assert_stable_failure(output, "ACTIVATE-LOCAL-SEED")

    def test_activation_replace_failure_retains_and_verifies_previous_dispatcher(
        self,
    ) -> None:
        self.prepare_valid_release()
        prior = self.dispatcher.read_bytes()
        with mock.patch(
            "scripts.promote_data_seed.os.replace", side_effect=OSError("injected")
        ):
            result, output = self.run_cli(self.release_args("activate-local-seed"))

        self.assertEqual(2, result)
        self.assertEqual(prior, self.dispatcher.read_bytes())
        self.assert_stable_failure(output, "ACTIVATE-LOCAL-SEED")
        self.assertEqual([], list(self.dispatcher.parent.glob(".seed.sql.*")))

    def test_activation_post_check_failure_restores_previous_bytes_atomically(
        self,
    ) -> None:
        self.prepare_valid_release()
        prior = self.dispatcher.read_bytes()
        real_replace = os.replace
        with mock.patch(
            "scripts.promote_data_seed.os.replace", wraps=real_replace
        ) as replace_spy:
            with mock.patch(
                "scripts.promote_data_seed._dispatcher_matches",
                side_effect=[False, True],
            ):
                result, output = self.run_cli(self.release_args("activate-local-seed"))

        self.assertEqual(2, result)
        self.assertEqual(2, replace_spy.call_count)
        self.assertEqual(prior, self.dispatcher.read_bytes())
        self.assert_stable_failure(output, "ACTIVATE-LOCAL-SEED")
        self.assertEqual([], list(self.dispatcher.parent.glob(".seed.sql.*")))

    def test_activation_temp_write_failure_does_not_change_dispatcher(self) -> None:
        self.prepare_valid_release()
        prior = self.dispatcher.read_bytes()
        with mock.patch(
            "scripts.promote_data_seed._write_dispatcher_temp",
            side_effect=OSError("injected"),
        ):
            result, output = self.run_cli(self.release_args("activate-local-seed"))

        self.assertEqual(2, result)
        self.assertEqual(prior, self.dispatcher.read_bytes())
        self.assert_stable_failure(output, "ACTIVATE-LOCAL-SEED")

    def test_dispatcher_reparse_component_is_rejected_without_outside_write(
        self,
    ) -> None:
        self.prepare_valid_release()
        alias = self.root / "supabase"
        target = alias.with_name("supabase-target")
        alias.rename(target)
        outside_before = (target / "seed.sql").read_bytes()
        try:
            self.create_reparse_directory(alias, target)
            result, output = self.run_cli(self.release_args("activate-local-seed"))
            self.assertEqual(2, result)
            self.assert_stable_failure(output, "ACTIVATE-LOCAL-SEED")
            self.assertEqual(outside_before, (target / "seed.sql").read_bytes())
        finally:
            self.remove_reparse_directory(alias)

    def test_verify_local_seed_fails_when_dispatcher_is_not_active(self) -> None:
        self.prepare_valid_release()

        result, output = self.run_cli(self.release_args("verify-local-seed"))

        self.assertEqual(2, result)
        self.assertEqual(self.initial_dispatcher, self.dispatcher.read_bytes())
        self.assert_stable_failure(output, "VERIFY-LOCAL-SEED")

    def test_parser_rejects_missing_extra_duplicate_and_unknown_arguments_safely(
        self,
    ) -> None:
        cases = (
            ([], "DATA-SEED-CLI"),
            (["unknown"], "DATA-SEED-CLI"),
            (["prepare"], "PREPARE-DATA-SEED"),
            (
                [*self.prepare_args(), "--release-dir", CANONICAL_RELEASE],
                "PREPARE-DATA-SEED",
            ),
            (
                [
                    *self.release_args("verify-release"),
                    "--release-dir",
                    CANONICAL_RELEASE,
                ],
                "VERIFY-DATA-SEED-RELEASE",
            ),
        )
        for arguments, step in cases:
            with self.subTest(arguments=arguments):
                result, output = self.run_cli(list(arguments))
                self.assertEqual(2, result)
                self.assert_stable_failure(output, step)
                self.assertFalse(self.release.exists())
                self.assertEqual(self.initial_dispatcher, self.dispatcher.read_bytes())

    def test_unexpected_internal_failure_still_has_only_stable_output(self) -> None:
        with mock.patch(
            "scripts.promote_data_seed.verify_release_directory",
            side_effect=RuntimeError("DO-NOT-LEAK-UNEXPECTED-CONTENT"),
        ):
            result, output = self.run_cli(self.release_args("verify-release"))

        self.assertEqual(2, result)
        self.assertEqual(
            "[FAIL] step=VERIFY-DATA-SEED-RELEASE reason=OPERATION_FAILED issues=1\n",
            output,
        )
        self.assertNotIn("DO-NOT-LEAK", output)


if __name__ == "__main__":
    unittest.main()
