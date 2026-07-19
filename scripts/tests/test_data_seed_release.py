"""Focused tests for the DATA-SEED approved-input trust boundary."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
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

    def mutate_manifest(self, draft: Path, **changes: object) -> None:
        path = draft / "approval_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest.update(changes)
        path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def approve_waste_03(self, draft: Path) -> None:
        path = draft / "approval_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        decisions = manifest["decisions"]
        assert isinstance(decisions, list)
        for decision in decisions:
            if isinstance(decision, dict) and decision.get("record_id") == "KB-WASTE-03":
                decision["decision"] = "APPROVE_INITIAL_RELEASE"
                break
        else:
            self.fail("canonical approval fixture lacks KB-WASTE-03")
        path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_duplicate_json_member_is_rejected(self) -> None:
        path = self.write_raw('{"schema_version":1,"schema_version":1}\n')
        with self.assertRaisesRegex(ValueError, "JSON_DUPLICATE_MEMBER"):
            load_json_object_strict(path)

    def test_canonical_approved_input_is_accepted(self) -> None:
        issues = validate_approved_input(self.root, self.copy_canonical_draft())
        self.assertEqual((), issues)
        self.assertTrue(all(isinstance(issue, ReleaseIssue) for issue in issues))

    def test_noncanonical_or_stale_approval_is_rejected(self) -> None:
        draft = self.copy_canonical_draft()
        self.mutate_manifest(draft, state="PENDING_PM_REVIEW")
        codes = {issue.code for issue in validate_approved_input(self.root, draft)}
        self.assertIn("APPROVAL_STATE_INVALID", codes)

    def test_exact_projection_and_exclusions_are_required(self) -> None:
        draft = self.copy_canonical_draft()
        self.approve_waste_03(draft)
        codes = {issue.code for issue in validate_approved_input(self.root, draft)}
        self.assertIn("APPROVED_PROJECTION_INVALID", codes)

    def test_exact_canonical_draft_path_is_required(self) -> None:
        alias = self.root / "data" / "staging" / "data-001" / "wrong-draft"
        shutil.copytree(self.copy_canonical_draft(), alias)
        codes = {issue.code for issue in validate_approved_input(self.root, alias)}
        self.assertIn("CANONICAL_DRAFT_PATH_INVALID", codes)

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


if __name__ == "__main__":
    unittest.main()
