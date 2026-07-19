"""Focused tests for the DATA-SEED approved-input trust boundary."""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import scripts.data_staging_validation as staging_validation
from scripts.data_seed_release import (
    ReleaseIssue,
    load_json_object_strict,
    validate_approved_input,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DRAFT_RELATIVE = Path("data/staging/data-001/0.1.0-draft.1")
EXPECTED_RUNTIME_ALLOWLIST = frozenset({
    "scripts/data_seed_release.py",
    "scripts/data_staging_validation.py",
    "scripts/tests/test_data_seed_release.py",
    "scripts/tests/test_data_staging_validation.py",
    "scripts/validate_data_staging.py",
    "scripts/verify.ps1",
})


class DataSeedReleaseTrustBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name) / "repository"
        shutil.copytree(REPOSITORY_ROOT / "data", self.root / "data")

    def write_raw(self, content: str) -> Path:
        path = self.root / "raw.json"
        path.write_text(content, encoding="utf-8")
        return path

    def copy_canonical_draft(self) -> Path:
        return self.root / CANONICAL_DRAFT_RELATIVE

    def validate(self) -> tuple[ReleaseIssue, ...]:
        return tuple(validate_approved_input(self.root, CANONICAL_DRAFT_RELATIVE))

    def read_json(self, relative_path: str) -> dict[str, object]:
        path = self.copy_canonical_draft() / relative_path
        value = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(value, dict)
        return value

    def write_json(self, relative_path: str, value: object) -> None:
        path = self.copy_canonical_draft() / relative_path
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def mutate_manifest(self, **changes: object) -> None:
        manifest = self.read_json("approval_manifest.json")
        manifest.update(changes)
        self.write_json("approval_manifest.json", manifest)

    def approve_waste_03(self) -> None:
        manifest = self.read_json("approval_manifest.json")
        decisions = manifest["decisions"]
        assert isinstance(decisions, list)
        for decision in decisions:
            if isinstance(decision, dict) and decision.get("record_id") == "KB-WASTE-03":
                decision["decision"] = "APPROVE_INITIAL_RELEASE"
                break
        else:
            self.fail("canonical approval fixture lacks KB-WASTE-03")
        self.write_json("approval_manifest.json", manifest)

    def test_duplicate_json_member_is_rejected(self) -> None:
        path = self.write_raw('{"schema_version":1,"schema_version":1}\n')
        with self.assertRaisesRegex(ValueError, "JSON_DUPLICATE_MEMBER"):
            load_json_object_strict(path)

    def test_invalid_utf8_is_rejected_with_stable_error(self) -> None:
        path = self.root / "invalid-utf8.json"
        path.write_bytes(b"{\"schema_version\":\xff}\n")
        with self.assertRaisesRegex(ValueError, "^JSON_UTF8_INVALID$"):
            load_json_object_strict(path)

    def test_canonical_approved_input_is_accepted(self) -> None:
        issues = self.validate()
        self.assertEqual((), issues)
        self.assertTrue(all(isinstance(issue, ReleaseIssue) for issue in issues))

    def test_noncanonical_or_stale_approval_is_rejected(self) -> None:
        self.mutate_manifest(state="PENDING_PM_REVIEW")
        codes = {issue.code for issue in self.validate()}
        self.assertIn("APPROVAL_STATE_INVALID", codes)

    def test_exact_projection_and_exclusions_are_required(self) -> None:
        self.approve_waste_03()
        codes = {issue.code for issue in self.validate()}
        self.assertIn("APPROVED_PROJECTION_INVALID", codes)

    def test_only_exact_repository_relative_draft_token_is_accepted(self) -> None:
        canonical_token = os.fspath(CANONICAL_DRAFT_RELATIVE)
        alternate_separator = "/" if os.sep == "\\" else "\\"
        cases: dict[str, object] = {
            "absolute": self.copy_canonical_draft(),
            "dot_alias": f".{os.sep}{canonical_token}",
            "parent_alias": str(
                Path("data/staging/data-001/alias") / ".." / "0.1.0-draft.1"
            ),
            "alternate_separator": canonical_token.replace(os.sep, alternate_separator),
            "wrong_case": canonical_token.upper(),
            "wrong_spelling": canonical_token.replace("data-001", "data-01"),
            "outside_repository": self.root.parent / "0.1.0-draft.1",
        }
        for name, candidate in cases.items():
            with self.subTest(name=name):
                codes = {
                    issue.code
                    for issue in validate_approved_input(self.root, candidate)  # type: ignore[arg-type]
                }
                self.assertIn("CANONICAL_DRAFT_PATH_INVALID", codes)

    def test_rejected_self_and_wrong_identity_approvals_are_rejected(self) -> None:
        cases = (
            ({"state": "REJECTED"}, "APPROVAL_STATE_INVALID"),
            ({"reviewed_by": "AI-DATA-BACKEND"}, "APPROVAL_REVIEWER_INVALID"),
            ({"created_by": "WRONG-AUTHOR"}, "APPROVAL_AUTHOR_INVALID"),
            ({"reviewed_by": "WRONG-REVIEWER"}, "APPROVAL_REVIEWER_INVALID"),
        )
        for changes, expected_code in cases:
            with self.subTest(expected_code=expected_code, changes=tuple(changes)):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory) / "repository"
                    shutil.copytree(REPOSITORY_ROOT / "data", root / "data")
                    manifest_path = root / CANONICAL_DRAFT_RELATIVE / "approval_manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest.update(changes)
                    manifest_path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    codes = {
                        issue.code
                        for issue in validate_approved_input(root, CANONICAL_DRAFT_RELATIVE)
                    }
                    self.assertIn(expected_code, codes)

    def test_empty_dataset_and_decision_comments_are_rejected(self) -> None:
        self.mutate_manifest(review_comment="  ")
        self.assertIn("APPROVAL_COMMENT_INVALID", {issue.code for issue in self.validate()})

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "repository"
            shutil.copytree(REPOSITORY_ROOT / "data", root / "data")
            manifest_path = root / CANONICAL_DRAFT_RELATIVE / "approval_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            decisions = manifest["decisions"]
            assert isinstance(decisions, list) and isinstance(decisions[0], dict)
            decisions[0]["comment"] = ""
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            codes = {
                issue.code
                for issue in validate_approved_input(root, CANONICAL_DRAFT_RELATIVE)
            }
            self.assertIn("APPROVAL_DECISIONS_INVALID", codes)

    def test_stale_approval_and_content_hashes_are_rejected(self) -> None:
        manifest_path = self.copy_canonical_draft() / "approval_manifest.json"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        self.assertIn(
            "APPROVAL_MANIFEST_HASH_INVALID",
            {issue.code for issue in self.validate()},
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "repository"
            shutil.copytree(REPOSITORY_ROOT / "data", root / "data")
            content_path = root / CANONICAL_DRAFT_RELATIVE / "kb_records.json"
            content_path.write_text(
                content_path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            codes = {
                issue.code
                for issue in validate_approved_input(root, CANONICAL_DRAFT_RELATIVE)
            }
            self.assertIn("CANONICAL_CONTENT_HASH_INVALID", codes)

    def test_wrong_artifact_count_is_rejected(self) -> None:
        manifest = self.read_json("approval_manifest.json")
        artifacts = manifest["artifacts"]
        assert isinstance(artifacts, list) and isinstance(artifacts[0], dict)
        artifacts[0]["record_count"] = 19
        self.write_json("approval_manifest.json", manifest)
        self.assertIn("APPROVAL_ARTIFACTS_INVALID", {issue.code for issue in self.validate()})

    def test_both_rejected_mappings_must_remain_excluded(self) -> None:
        for record_id in (
            "OFFICE-AREUM:LOCAL_TAX_GENERAL",
            "OFFICE-DODAM:BULKY_WASTE",
        ):
            with self.subTest(record_id=record_id):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory) / "repository"
                    shutil.copytree(REPOSITORY_ROOT / "data", root / "data")
                    path = root / CANONICAL_DRAFT_RELATIVE / "approval_manifest.json"
                    manifest = json.loads(path.read_text(encoding="utf-8"))
                    decisions = manifest["decisions"]
                    assert isinstance(decisions, list)
                    for decision in decisions:
                        if isinstance(decision, dict) and decision.get("record_id") == record_id:
                            decision["decision"] = "APPROVE_INITIAL_RELEASE"
                            break
                    path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    codes = {
                        issue.code
                        for issue in validate_approved_input(root, CANONICAL_DRAFT_RELATIVE)
                    }
                    self.assertIn("APPROVED_PROJECTION_INVALID", codes)

    def test_mock_content_is_rejected(self) -> None:
        kb = self.read_json("kb_records.json")
        records = kb["records"]
        assert isinstance(records, list) and isinstance(records[0], dict)
        records[0]["data_origin"] = "MOCK"
        self.write_json("kb_records.json", kb)
        codes = {issue.code for issue in self.validate()}
        self.assertIn("DATA_STAGING_INVALID", codes)
        self.assertIn("CANONICAL_CONTENT_HASH_INVALID", codes)

    def test_duplicate_and_reordered_decisions_are_rejected(self) -> None:
        for mutation in ("duplicate", "reorder"):
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory) / "repository"
                    shutil.copytree(REPOSITORY_ROOT / "data", root / "data")
                    path = root / CANONICAL_DRAFT_RELATIVE / "approval_manifest.json"
                    manifest = json.loads(path.read_text(encoding="utf-8"))
                    decisions = manifest["decisions"]
                    assert isinstance(decisions, list)
                    if mutation == "duplicate":
                        decisions[1] = dict(decisions[0])
                    else:
                        decisions[0], decisions[1] = decisions[1], decisions[0]
                    path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    codes = {
                        issue.code
                        for issue in validate_approved_input(root, CANONICAL_DRAFT_RELATIVE)
                    }
                    self.assertIn("APPROVAL_DECISIONS_INVALID", codes)

    def test_issue_output_is_stable_and_never_contains_untrusted_content(self) -> None:
        sentinel = "DO-NOT-LEAK-APPROVAL-CONTENT"
        self.mutate_manifest(review_comment=sentinel)
        first = self.validate()
        second = self.validate()
        self.assertEqual(first, second)
        serialized = json.dumps([asdict(issue) for issue in first], sort_keys=True)
        self.assertNotIn(sentinel, serialized)

    def test_reparse_component_is_rejected(self) -> None:
        alias = self.root / "data" / "staging" / "data-001"
        target = alias.with_name("data-001-target")
        alias.rename(target)
        try:
            try:
                alias.symlink_to(target, target_is_directory=True)
            except OSError as symlink_error:
                if os.name != "nt":
                    self.skipTest(f"directory symlink unavailable: {type(symlink_error).__name__}")
                junction = subprocess.run(
                    ["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(target)],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if junction.returncode != 0:
                    self.skipTest(
                        "directory symlink and junction fixtures are unavailable"
                    )
            codes = {issue.code for issue in self.validate()}
            self.assertIn("CANONICAL_DRAFT_PATH_INVALID", codes)
        finally:
            if alias.is_symlink():
                alias.unlink()
            elif alias.exists():
                alias.rmdir()

    def test_release_schemas_are_strict_and_encode_initial_projection(self) -> None:
        schema_dir = self.root / "data" / "schemas" / "data-seed" / "v1"
        release_manifest = json.loads(
            (schema_dir / "release-manifest.schema.json").read_text(encoding="utf-8")
        )
        kb = json.loads((schema_dir / "kb-records.schema.json").read_text(encoding="utf-8"))
        offices = json.loads((schema_dir / "offices.schema.json").read_text(encoding="utf-8"))
        mappings = json.loads(
            (schema_dir / "office-service-mappings.schema.json").read_text(encoding="utf-8")
        )

        for schema in (release_manifest, kb, offices, mappings):
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(1, schema["properties"]["schema_version"]["const"])
            self.assertEqual(
                "0.1.0-initial.1",
                schema["properties"]["release_version"]["const"],
            )

        self.assertEqual(
            {
                "kb": 19,
                "office": 3,
                "mapping": 10,
                "withheld_kb": 1,
                "rejected_mapping": 2,
                "mock": 0,
            },
            {
                name: property_schema["const"]
                for name, property_schema in release_manifest["properties"]["projection"][
                    "properties"
                ].items()
            },
        )
        self.assertEqual("ACTIVE", kb["properties"]["records"]["items"]["properties"]["status"]["const"])
        self.assertEqual(19, kb["properties"]["records"]["minItems"])
        self.assertEqual(3, offices["properties"]["records"]["minItems"])
        self.assertEqual(10, mappings["properties"]["records"]["minItems"])

    def test_release_tool_is_the_only_new_staging_scanner_exception(self) -> None:
        self.assertEqual(EXPECTED_RUNTIME_ALLOWLIST, staging_validation._RUNTIME_ALLOWLIST)
        paths = [
            REPOSITORY_ROOT / "scripts" / "data_seed_release.py",
            REPOSITORY_ROOT / "scripts" / "tests" / "test_data_seed_release.py",
        ]
        issues: list[staging_validation.ValidationIssue] = []
        staging_validation._scan_runtime_files(
            paths,
            REPOSITORY_ROOT,
            issues,
            staging_validation._RUNTIME_ALLOWLIST,
        )
        self.assertEqual([], issues)

        unauthorized = self.root / "scripts" / "data_seed_release_neighbor.py"
        unauthorized.parent.mkdir(parents=True)
        unauthorized.write_text(
            'draft = "data/staging/data-001/0.1.0-draft.1"\n',
            encoding="utf-8",
        )
        staging_validation._scan_runtime_files(
            [unauthorized],
            self.root,
            issues,
            staging_validation._RUNTIME_ALLOWLIST,
        )
        self.assertEqual(1, len(issues))
        self.assertEqual("RUNTIME_STAGING_REFERENCE", issues[0].code)
        self.assertEqual("scripts/data_seed_release_neighbor.py", issues[0].artifact)


if __name__ == "__main__":
    unittest.main()
