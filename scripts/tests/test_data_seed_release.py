"""Focused tests for the DATA-SEED approved-input trust boundary."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import scripts.data_seed_release as data_seed_release
import scripts.data_staging_validation as staging_validation
from scripts.data_seed_release import (
    ReleaseBundle,
    ReleaseIssue,
    build_release_bundle,
    build_seed_projection,
    canonical_json_bytes,
    load_json_object_strict,
    semantic_sha256,
    validate_approved_input,
)
from scripts.data_seed_sql import (
    render_compensation_sql,
    render_expected_rows,
    render_seed_sql,
    sql_literal,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DRAFT_TOKEN = "data/staging/data-001/0.1.0-draft.1"
CANONICAL_DRAFT_RELATIVE = Path(CANONICAL_DRAFT_TOKEN)
RELEASE_VERSION = "0.1.0-initial.1"
RELEASED_AT = "2026-07-19T09:20:31+09:00"
INITIAL_RELEASE_FILES = {
    "approval_manifest.json": (
        13074,
        "466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a",
    ),
    "compensation.sql": (
        41710,
        "6fde4e35e185453ca1bba42af4440fc0f935257efbc1701f84cc349ecedc2368",
    ),
    "kb_records.json": (
        37208,
        "831a0c01c9cdb08130febb122ebcad7d7b4fd9e7d846764d0d49d3e3c02402ec",
    ),
    "office_service_mappings.json": (
        4057,
        "361ba3f4024abdfc7f1d0b4c8107d3aff708e377ac309bc18beda7613bfccebd",
    ),
    "offices.json": (
        2263,
        "d83d48ff56cb945ddbb262e26c7d876dbc4b34af9b038048884057ab54e10b4e",
    ),
    "release_manifest.json": (
        1605,
        "e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2",
    ),
    "seed.sql": (
        75891,
        "42d67828bb23c0eb0fa17ae2daa7d457fd71806b7cc796a54643dd975597783d",
    ),
}
INITIAL_SCHEMA_FILES = {
    "kb-records.schema.json": (
        2564,
        "97bd21438bbfc1a60c13de13106b9378961ddef20839c3227d88bcf75eae9527",
    ),
    "office-service-mappings.schema.json": (
        1460,
        "82853a80f7147cd9948580bec97a9bf5c765cf1956520680f205ebfd5d4d2bfa",
    ),
    "offices.schema.json": (
        1885,
        "7a251ba5fff8e5990788db010faf946d221b845089c2192ae5c0a122e632f280",
    ),
    "release-manifest.schema.json": (
        2765,
        "0b6cc2deb20cf25ea9b02059cc6400826304c0452ee957e3757a41679e91423e",
    ),
}
EXPECTED_RUNTIME_ALLOWLIST = frozenset(
    {
        "scripts/data_seed_release.py",
        "scripts/data_staging_validation.py",
        "scripts/tests/test_data_seed_release.py",
        "scripts/tests/test_data_staging_validation.py",
        "scripts/validate_data_staging.py",
        "scripts/verify.ps1",
    }
)


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
        return tuple(validate_approved_input(self.root, CANONICAL_DRAFT_TOKEN))

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
            if (
                isinstance(decision, dict)
                and decision.get("record_id") == "KB-WASTE-03"
            ):
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
        path.write_bytes(b'{"schema_version":\xff}\n')
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

    def test_only_exact_raw_repository_relative_draft_token_is_accepted(self) -> None:
        cases = {
            "absolute": str(self.copy_canonical_draft()),
            "dot_alias": f"./{CANONICAL_DRAFT_TOKEN}",
            "parent_alias": "data/staging/data-001/alias/../0.1.0-draft.1",
            "alternate_separator": CANONICAL_DRAFT_TOKEN.replace("/", "\\"),
            "trailing_separator": f"{CANONICAL_DRAFT_TOKEN}/",
            "wrong_case": CANONICAL_DRAFT_TOKEN.upper(),
            "wrong_spelling": CANONICAL_DRAFT_TOKEN.replace("data-001", "data-01"),
            "outside_repository": "../0.1.0-draft.1",
        }
        for name, candidate in cases.items():
            with self.subTest(name=name):
                codes = {
                    issue.code
                    for issue in validate_approved_input(self.root, candidate)
                }
                self.assertIn("CANONICAL_DRAFT_PATH_INVALID", codes)

    def test_path_and_other_non_string_tokens_fail_closed(self) -> None:
        normalized_dot_alias = Path(f".{os.sep}{CANONICAL_DRAFT_TOKEN}")
        self.assertEqual(CANONICAL_DRAFT_RELATIVE, normalized_dot_alias)
        for candidate in (
            normalized_dot_alias,
            Path(CANONICAL_DRAFT_TOKEN),
            b"data/staging",
        ):
            with self.subTest(candidate_type=type(candidate).__name__):
                codes = {
                    issue.code
                    for issue in validate_approved_input(self.root, candidate)
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
                    manifest_path = (
                        root / CANONICAL_DRAFT_RELATIVE / "approval_manifest.json"
                    )
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest.update(changes)
                    manifest_path.write_text(
                        json.dumps(
                            manifest, ensure_ascii=False, indent=2, sort_keys=True
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    codes = {
                        issue.code
                        for issue in validate_approved_input(
                            root, CANONICAL_DRAFT_TOKEN
                        )
                    }
                    self.assertIn(expected_code, codes)

    def test_empty_dataset_and_decision_comments_are_rejected(self) -> None:
        self.mutate_manifest(review_comment="  ")
        self.assertIn(
            "APPROVAL_COMMENT_INVALID", {issue.code for issue in self.validate()}
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "repository"
            shutil.copytree(REPOSITORY_ROOT / "data", root / "data")
            manifest_path = root / CANONICAL_DRAFT_RELATIVE / "approval_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            decisions = manifest["decisions"]
            assert isinstance(decisions, list) and isinstance(decisions[0], dict)
            decisions[0]["comment"] = ""
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            codes = {
                issue.code
                for issue in validate_approved_input(root, CANONICAL_DRAFT_TOKEN)
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
                for issue in validate_approved_input(root, CANONICAL_DRAFT_TOKEN)
            }
            self.assertIn("CANONICAL_CONTENT_HASH_INVALID", codes)

    def test_wrong_artifact_count_is_rejected(self) -> None:
        manifest = self.read_json("approval_manifest.json")
        artifacts = manifest["artifacts"]
        assert isinstance(artifacts, list) and isinstance(artifacts[0], dict)
        artifacts[0]["record_count"] = 19
        self.write_json("approval_manifest.json", manifest)
        self.assertIn(
            "APPROVAL_ARTIFACTS_INVALID", {issue.code for issue in self.validate()}
        )

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
                        if (
                            isinstance(decision, dict)
                            and decision.get("record_id") == record_id
                        ):
                            decision["decision"] = "APPROVE_INITIAL_RELEASE"
                            break
                    path.write_text(
                        json.dumps(
                            manifest, ensure_ascii=False, indent=2, sort_keys=True
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    codes = {
                        issue.code
                        for issue in validate_approved_input(
                            root, CANONICAL_DRAFT_TOKEN
                        )
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
                        json.dumps(
                            manifest, ensure_ascii=False, indent=2, sort_keys=True
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    codes = {
                        issue.code
                        for issue in validate_approved_input(
                            root, CANONICAL_DRAFT_TOKEN
                        )
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
        kb = json.loads(
            (schema_dir / "kb-records.schema.json").read_text(encoding="utf-8")
        )
        offices = json.loads(
            (schema_dir / "offices.schema.json").read_text(encoding="utf-8")
        )
        mappings = json.loads(
            (schema_dir / "office-service-mappings.schema.json").read_text(
                encoding="utf-8"
            )
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
                for name, property_schema in release_manifest["properties"][
                    "projection"
                ]["properties"].items()
            },
        )
        self.assertEqual(
            "ACTIVE",
            kb["properties"]["records"]["items"]["properties"]["status"]["const"],
        )
        self.assertEqual(19, kb["properties"]["records"]["minItems"])
        self.assertEqual(3, offices["properties"]["records"]["minItems"])
        self.assertEqual(10, mappings["properties"]["records"]["minItems"])

    def test_release_tool_is_the_only_new_staging_scanner_exception(self) -> None:
        self.assertEqual(
            EXPECTED_RUNTIME_ALLOWLIST, staging_validation._RUNTIME_ALLOWLIST
        )
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


class DataSeedProjectionAndSqlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name) / "repository"
        shutil.copytree(REPOSITORY_ROOT / "data", self.root / "data")
        self.draft = self.root / CANONICAL_DRAFT_RELATIVE
        self.projection = build_seed_projection(self.draft, RELEASE_VERSION)

    def test_initial_release_and_v1_schema_bytes_are_frozen(self) -> None:
        release_dir = self.root / "data/official/releases/0.1.0-initial.1"
        for name, (length, digest) in INITIAL_RELEASE_FILES.items():
            payload = (release_dir / name).read_bytes()
            self.assertEqual(length, len(payload), name)
            self.assertEqual(digest, hashlib.sha256(payload).hexdigest(), name)

        schema_dir = self.root / "data/schemas/data-seed/v1"
        for name, (length, digest) in INITIAL_SCHEMA_FILES.items():
            payload = (schema_dir / name).read_bytes()
            self.assertEqual(length, len(payload), name)
            self.assertEqual(digest, hashlib.sha256(payload).hexdigest(), name)

        profile = data_seed_release.release_profile(RELEASE_VERSION)
        bundle = build_release_bundle(
            self.root,
            self.draft,
            profile.version,
            profile.released_at,
        )
        generated = data_seed_release.release_bundle_files(bundle)
        self.assertEqual(set(INITIAL_RELEASE_FILES), set(generated))
        for name, payload in generated.items():
            self.assertEqual((release_dir / name).read_bytes(), payload, name)

    def test_profiles_are_closed_and_successor_preserves_projection(self) -> None:
        initial = data_seed_release.release_profile("0.1.0-initial.1")
        successor = data_seed_release.release_profile("0.1.0-initial.2")

        self.assertIsInstance(initial, data_seed_release.ReleaseProfile)
        self.assertEqual("legacy-single-row", initial.membership_guard)
        self.assertEqual("effective-option-union", successor.membership_guard)
        self.assertEqual(
            "e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2",
            successor.predecessor_manifest_sha256,
        )
        self.assertEqual("D-044", successor.decision_id)
        self.assertEqual(
            "POSTGRES17_EFFECTIVE_MEMBERSHIP_OPTION_UNION",
            successor.correction_reason,
        )
        self.assertEqual(
            {"0.1.0-initial.1", "0.1.0-initial.2"},
            set(data_seed_release.RELEASE_PROFILES),
        )
        self.assertEqual("0.1.0-initial.2", data_seed_release.RELEASE_VERSION)
        self.assertEqual(
            build_seed_projection(self.draft, initial.version),
            build_seed_projection(self.draft, successor.version),
        )
        with self.assertRaisesRegex(ValueError, "RELEASE_VERSION_INVALID"):
            data_seed_release.release_profile("0.1.0-initial.3")

    def test_successor_bundle_uses_profile_metadata_and_correction(self) -> None:
        profile = data_seed_release.SUCCESSOR_RELEASE_PROFILE
        bundle = build_release_bundle(
            self.root,
            self.draft,
            profile.version,
            profile.released_at,
        )

        self.assertEqual(2, bundle.manifest["schema_version"])
        self.assertEqual(profile.release_id, bundle.manifest["release_id"])
        self.assertEqual(profile.version, bundle.manifest["release_version"])
        self.assertEqual(profile.released_at_utc, bundle.manifest["released_at"])
        self.assertEqual(profile.generator_id, bundle.manifest["generator"])
        self.assertEqual(
            {
                "predecessor_release_version": "0.1.0-initial.1",
                "predecessor_manifest_sha256": (
                    "e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2"
                ),
                "decision_id": "D-044",
                "reason": "POSTGRES17_EFFECTIVE_MEMBERSHIP_OPTION_UNION",
            },
            bundle.manifest["correction"],
        )
        for payload in (
            bundle.kb_records_bytes,
            bundle.offices_bytes,
            bundle.office_service_mappings_bytes,
        ):
            document = json.loads(payload)
            self.assertEqual(2, document["schema_version"])
            self.assertEqual(profile.version, document["release_version"])

    def test_projection_is_exact_19_3_10_and_excludes_rejected_records(self) -> None:
        self.assertEqual(19, len(self.projection["kb_documents"]))
        self.assertEqual(3, len(self.projection["offices"]))
        self.assertEqual(10, len(self.projection["office_service_mappings"]))
        kb_ids = {row["public_id"] for row in self.projection["kb_documents"]}
        mapping_ids = {
            f"{row['office_public_id']}:{row['intent']}"
            for row in self.projection["office_service_mappings"]
        }
        self.assertNotIn("KB-WASTE-03", kb_ids)
        self.assertNotIn("OFFICE-AREUM:LOCAL_TAX_GENERAL", mapping_ids)
        self.assertNotIn("OFFICE-DODAM:BULKY_WASTE", mapping_ids)
        self.assertTrue(
            all(
                row["data_origin"] == "OFFICIAL"
                for row in self.projection["kb_documents"]
            )
        )
        self.assertTrue(
            all(row["data_origin"] == "OFFICIAL" for row in self.projection["offices"])
        )

    def test_projection_has_exact_seed_owned_fields_and_canonical_order(self) -> None:
        self.assertEqual(
            {
                "public_id",
                "data_origin",
                "category",
                "service_name",
                "answer_summary",
                "procedure_steps",
                "required_documents",
                "processing_time",
                "fee",
                "department",
                "source_title",
                "source_url",
                "last_verified_at",
                "caution",
                "status",
                "created_by",
                "approved_by",
                "approved_at",
            },
            set(self.projection["kb_documents"][0]),
        )
        self.assertEqual(
            {"kb_public_id", "question_example", "normalized_text"},
            set(self.projection["kb_question_examples"][0]),
        )
        self.assertEqual(
            {
                "public_id",
                "data_origin",
                "region",
                "office_name",
                "address",
                "phone",
                "opening_hours",
                "map_url",
                "source_title",
                "source_url",
                "last_verified_at",
            },
            set(self.projection["offices"][0]),
        )
        self.assertEqual(
            {"office_public_id", "intent", "department_label"},
            set(self.projection["office_service_mappings"][0]),
        )
        self.assertEqual(
            sorted(row["public_id"] for row in self.projection["kb_documents"]),
            [row["public_id"] for row in self.projection["kb_documents"]],
        )
        self.assertEqual(
            sorted(
                (row["kb_public_id"], row["question_example"])
                for row in self.projection["kb_question_examples"]
            ),
            [
                (row["kb_public_id"], row["question_example"])
                for row in self.projection["kb_question_examples"]
            ],
        )
        self.assertTrue(
            all(
                row["approved_at"] == "2026-07-18T17:06:19Z"
                for row in self.projection["kb_documents"]
            )
        )

    def test_semantic_hash_uses_exact_canonical_bytes(self) -> None:
        expected = hashlib.sha256(
            canonical_json_bytes(self.projection, trailing_newline=False)
        ).hexdigest()
        self.assertEqual(expected, semantic_sha256(self.projection))
        canonical = canonical_json_bytes(self.projection, trailing_newline=False)
        self.assertFalse(canonical.endswith(b"\n"))
        self.assertNotIn(b"\\u", canonical)
        self.assertTrue(
            canonical_json_bytes(self.projection, trailing_newline=True).endswith(b"\n")
        )

    def test_sql_literal_covers_null_bool_date_timestamp_json_and_safe_text(
        self,
    ) -> None:
        self.assertEqual("NULL", sql_literal(None))
        self.assertEqual("TRUE::boolean", sql_literal(True))
        self.assertEqual("'2026-07-19'::date", sql_literal(date(2026, 7, 19)))
        self.assertEqual(
            "'2026-07-19T00:20:31Z'::timestamptz",
            sql_literal(
                datetime(
                    2026,
                    7,
                    19,
                    9,
                    20,
                    31,
                    tzinfo=timezone(timedelta(hours=9)),
                )
            ),
        )
        text_literal = sql_literal("세종 O'Brien \\ 경로")
        self.assertEqual("'세종 O''Brien \\ 경로'::text", text_literal)
        self.assertEqual(
            "'[\"세종\",null,true]'::jsonb", sql_literal(["세종", None, True])
        )
        with self.assertRaisesRegex(ValueError, "SQL_TIMESTAMP_TIMEZONE_REQUIRED"):
            sql_literal(datetime(2026, 7, 19, 9, 20, 31))

    def test_sql_renderer_preserves_quote_backslash_unicode_date_and_null(self) -> None:
        projection = json.loads(
            canonical_json_bytes(self.projection, trailing_newline=False).decode(
                "utf-8"
            )
        )
        projection["kb_documents"][0]["answer_summary"] = "세종 O'Brien \\ 경로"
        projection["kb_documents"][0]["fee"] = None
        sql = render_seed_sql(projection).decode("utf-8")
        self.assertIn("세종 O''Brien \\ 경로", sql)
        self.assertIn("'2026-07-18'::date", sql)
        self.assertIn("NULL::text", sql)

    def test_bundle_rejects_non_initial_version_or_governance_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "RELEASE_VERSION_INVALID"):
            build_release_bundle(self.root, self.draft, "0.1.0", RELEASED_AT)
        with self.assertRaisesRegex(ValueError, "RELEASE_TIMESTAMP_INVALID"):
            build_release_bundle(
                self.root,
                self.draft,
                RELEASE_VERSION,
                "2026-07-19T09:20:32+09:00",
            )
        with self.assertRaisesRegex(ValueError, "TIMESTAMP_PRECISION_INVALID"):
            build_release_bundle(
                self.root,
                self.draft,
                RELEASE_VERSION,
                "2026-07-19T09:20:31.999999+09:00",
            )

    def test_bundle_uses_the_single_validated_snapshot_when_source_path_changes(
        self,
    ) -> None:
        original_summary = self.projection["kb_documents"][0]["answer_summary"]
        mutated_summary = "SNAPSHOT-RACE-MUTATION-MUST-NOT-BE-RELEASED"
        reads: list[str] = []

        def read_once(path: Path) -> bytes:
            payload = path.read_bytes()
            reads.append(path.name)
            if path.name == "kb_records.json":
                kb = json.loads(payload.decode("utf-8"))
                kb["records"][0]["answer_summary"] = mutated_summary
                path.write_text(
                    json.dumps(kb, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            return payload

        bundle: ReleaseBundle | None = None
        error: ValueError | None = None
        with mock.patch(
            "scripts.data_seed_release._read_artifact_bytes_once",
            side_effect=read_once,
        ):
            try:
                bundle = build_release_bundle(
                    self.root,
                    self.draft,
                    RELEASE_VERSION,
                    RELEASED_AT,
                )
            except ValueError as caught:
                error = caught

        self.assertEqual(
            [
                "kb_records.json",
                "offices.json",
                "office_service_mappings.json",
                "approval_manifest.json",
            ],
            reads,
        )
        if error is not None:
            self.assertEqual("APPROVED_INPUT_INVALID", str(error))
        else:
            assert bundle is not None
            self.assertIn(
                str(original_summary).encode("utf-8"), bundle.kb_records_bytes
            )
            self.assertNotIn(mutated_summary.encode("utf-8"), bundle.kb_records_bytes)

    def test_bundle_keeps_snapshot_when_source_changes_after_staging_validation(
        self,
    ) -> None:
        original_summary = self.projection["kb_documents"][0]["answer_summary"]
        mutated_summary = "POST-VALIDATION-MUTATION-MUST-NOT-BE-RELEASED"
        kb_path = self.draft / "kb_records.json"
        real_validate = data_seed_release._validate_current_staging
        validation_calls = 0

        def validate_then_mutate(
            draft: Path,
            stage_schema_dir: Path,
            source_registry: Path,
            issues: list[data_seed_release.ReleaseIssue],
        ) -> None:
            nonlocal validation_calls
            real_validate(draft, stage_schema_dir, source_registry, issues)
            validation_calls += 1
            kb = json.loads(kb_path.read_text(encoding="utf-8"))
            kb["records"][0]["answer_summary"] = mutated_summary
            kb_path.write_text(
                json.dumps(kb, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        with mock.patch(
            "scripts.data_seed_release._validate_current_staging",
            side_effect=validate_then_mutate,
        ):
            bundle = build_release_bundle(
                self.root,
                self.draft,
                RELEASE_VERSION,
                RELEASED_AT,
            )

        self.assertEqual(1, validation_calls)
        self.assertIn(mutated_summary.encode("utf-8"), kb_path.read_bytes())
        self.assertIn(str(original_summary).encode("utf-8"), bundle.kb_records_bytes)
        self.assertNotIn(mutated_summary.encode("utf-8"), bundle.kb_records_bytes)

    def test_seed_sql_has_fixed_principal_lock_order_preflight_and_guards(self) -> None:
        sql = render_seed_sql(self.projection).decode("utf-8")
        self.assertTrue(sql.startswith("BEGIN;\n"))
        self.assertTrue(sql.endswith("COMMIT;\n"))
        self.assertIn("pg_advisory_xact_lock(20260719001)", sql)
        self.assertIn("SET LOCAL lock_timeout = '5s'", sql)
        for token in (
            "session_user = 'postgres'",
            "current_user = 'postgres'",
            "current_database() = 'postgres'",
            "memberships.admin_option",
            "memberships.inherit_option",
            "memberships.set_option",
            "SET LOCAL ROLE sejong_schema_owner",
            "current_user = 'sejong_schema_owner'",
        ):
            self.assertIn(token, sql)
        lock_order = (
            "kb_documents",
            "kb_question_examples",
            "offices",
            "office_service_mappings",
            "interaction_events",
            "failed_questions",
            "kb_candidates",
            "audit_logs",
        )
        lock_positions = [
            sql.index(f"LOCK TABLE app_private.{table} IN ACCESS EXCLUSIVE MODE;")
            for table in lock_order
        ]
        self.assertEqual(sorted(lock_positions), lock_positions)
        self.assertLess(
            sql.index("DATA_SEED_DATABASE_NOT_EMPTY"), sql.index("INSERT INTO")
        )
        self.assertGreaterEqual(sql.count("EXCEPT ALL"), 8)
        self.assertIn(
            "INSERT INTO app_private.kb_documents (public_id, data_origin, category, service_name",
            sql,
        )
        self.assertNotIn("EXECUTE ", sql)
        self.assertNotIn("format(", sql)
        self.assertIn("KB-WASTE-03", sql)

    def test_membership_guard_counts_the_pair_before_checking_all_options(self) -> None:
        sql = render_seed_sql(self.projection).decode("utf-8")
        query_start = sql.index("pg_catalog.count(*)")
        query_end = sql.index("IF v_total_memberships", query_start)
        membership_query = sql[query_start:query_end]
        where_clause = membership_query.split("WHERE", maxsplit=1)[1]

        self.assertIn("v_total_memberships", membership_query)
        self.assertIn("v_membership_options_valid", membership_query)
        self.assertIn("pg_catalog.bool_and", membership_query)
        self.assertNotIn("memberships.admin_option", where_clause)
        self.assertNotIn("memberships.inherit_option", where_clause)
        self.assertNotIn("memberships.set_option", where_clause)
        self.assertIn(
            "IF v_total_memberships <> 1 OR NOT v_membership_options_valid THEN",
            sql,
        )

    def test_expected_rows_cover_every_seed_owned_column(self) -> None:
        expected = render_expected_rows(self.projection)
        for cte in (
            "expected_kb_documents",
            "expected_kb_question_examples",
            "expected_offices",
            "expected_office_service_mappings",
        ):
            self.assertIn(cte, expected)
        for field in self.projection["kb_documents"][0]:
            self.assertIn(field, expected)
        self.assertIn("normalized_text", expected)
        self.assertIn("department_label", expected)

    def test_compensation_is_guarded_and_deletes_in_fk_safe_order(self) -> None:
        sql = render_compensation_sql(self.projection).decode("utf-8")
        self.assertIn("DATA_SEED_COMPENSATION_OPERATIONAL_ROWS_PRESENT", sql)
        self.assertGreaterEqual(sql.count("EXCEPT ALL"), 8)
        guard = sql.index("DATA_SEED_COMPENSATION_PROJECTION_MISMATCH")
        mapping_delete = sql.index("DELETE FROM app_private.office_service_mappings")
        kb_delete = sql.index("DELETE FROM app_private.kb_documents")
        office_delete = sql.index("DELETE FROM app_private.offices")
        absence = sql.index("DATA_SEED_COMPENSATION_ABSENCE_FAILED")
        self.assertLess(guard, mapping_delete)
        self.assertLess(mapping_delete, kb_delete)
        self.assertLess(kb_delete, office_delete)
        self.assertLess(office_delete, absence)
        self.assertNotIn("EXECUTE ", sql)

    def test_release_bundle_is_byte_deterministic_across_roots_and_writes_nothing(
        self,
    ) -> None:
        bundles: list[ReleaseBundle] = []
        for suffix in ("one", "two"):
            root = Path(self.temporary_directory.name) / suffix
            shutil.copytree(
                REPOSITORY_ROOT / "data",
                root / "data",
                ignore=shutil.ignore_patterns("releases"),
            )
            self.assertFalse((root / "data" / "official" / "releases").exists())
            bundles.append(
                build_release_bundle(
                    root,
                    root / CANONICAL_DRAFT_RELATIVE,
                    RELEASE_VERSION,
                    RELEASED_AT,
                )
            )
            self.assertFalse((root / "data" / "official" / "releases").exists())

        first, second = bundles
        self.assertEqual(first, second)
        self.assertEqual(
            "sejong-official-0.1.0-initial.1", first.manifest["release_id"]
        )
        self.assertEqual("2026-07-19T00:20:31Z", first.manifest["released_at"])
        byte_fields = (
            "approval_manifest_bytes",
            "kb_records_bytes",
            "offices_bytes",
            "office_service_mappings_bytes",
            "seed_sql_bytes",
            "compensation_sql_bytes",
        )
        for field in byte_fields:
            self.assertEqual(
                hashlib.sha256(getattr(first, field)).digest(),
                hashlib.sha256(getattr(second, field)).digest(),
            )
        self.assertEqual(
            semantic_sha256(self.projection),
            first.seed_semantic_sha256,
        )


if __name__ == "__main__":
    unittest.main()
