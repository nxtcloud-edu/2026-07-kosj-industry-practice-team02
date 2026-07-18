"""Tests for the dependency-free DATA-001 staging schema helpers."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

from scripts.data_staging_validation import (
    ValidationIssue,
    load_json_object,
    sha256_file,
    validate_schema,
    write_json,
)


SCHEMA_DIR = Path("data/schemas/data-001/v1")


class DataStagingSchemaValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kb_schema = json.loads(
            (SCHEMA_DIR / "kb-records.schema.json").read_text(encoding="utf-8")
        )
        self.kb_record_schema = self.kb_schema["properties"]["records"]["items"]

    def valid_kb(self) -> dict[str, object]:
        return {
            "id": "KB-MOVE-01",
            "data_origin": "OFFICIAL",
            "category": "MOVE_IN_RESIDENT_REGISTRATION",
            "service_name": "전입신고",
            "question_examples": ["하나", "둘", "셋"],
            "answer_summary": "안내입니다.",
            "procedure_steps": ["신청합니다."],
            "required_documents": ["신분증"],
            "processing_time": None,
            "fee": None,
            "department": "민원행정과",
            "provider": "정부24",
            "source_title": "전입신고 안내",
            "source_url": "https://example.test/service",
            "source_service_id": None,
            "last_verified_at": "2026-07-18",
            "caution": None,
            "status": "DRAFT",
            "created_by": "AI-DATA-BACKEND",
            "approved_by": None,
            "approved_at": None,
        }

    def test_unknown_kb_field_is_rejected(self) -> None:
        issues = validate_schema(
            self.valid_kb() | {"unexpected": "x"},
            self.kb_record_schema,
            "kb_records.json",
        )
        self.assertIn("SCHEMA_ADDITIONAL_PROPERTY", {issue.code for issue in issues})

    def test_question_examples_require_three_to_five_unique_items(self) -> None:
        record = self.valid_kb() | {"question_examples": ["하나", "둘"]}
        issues = validate_schema(record, self.kb_record_schema, "kb_records.json")
        self.assertIn("SCHEMA_MIN_ITEMS", {issue.code for issue in issues})

    def test_invalid_date_and_non_https_url_are_rejected(self) -> None:
        record = self.valid_kb() | {
            "last_verified_at": "18-07-2026",
            "source_url": "http://example.test",
        }
        codes = {
            issue.code
            for issue in validate_schema(record, self.kb_record_schema, "kb_records.json")
        }
        self.assertEqual({"SCHEMA_DATE", "SCHEMA_HTTPS_URL"} - codes, set())

    def test_datetime_requires_iso_t_separator_and_timezone(self) -> None:
        manifest_schema = json.loads(
            (SCHEMA_DIR / "approval-manifest.schema.json").read_text(encoding="utf-8")
        )
        manifest = {
            "schema_version": 1,
            "dataset_id": "sejong-data-001",
            "draft_version": "0.1.0-draft.1",
            "state": "DRAFT",
            "created_by": "AI-DATA-BACKEND",
            "submitted_at": "2026-07-18 18:00:00+09:00",
            "reviewed_by": None,
            "reviewed_at": None,
            "review_comment": None,
            "artifacts": [],
            "decisions": [],
        }
        issues = validate_schema(manifest, manifest_schema, "approval_manifest.json")
        self.assertIn("SCHEMA_DATETIME", {issue.code for issue in issues})

    def test_missing_required_field_is_rejected(self) -> None:
        record = self.valid_kb()
        del record["source_title"]
        issues = validate_schema(record, self.kb_record_schema, "kb_records.json")
        self.assertIn("SCHEMA_REQUIRED", {issue.code for issue in issues})

    def test_wrong_type_is_rejected(self) -> None:
        record = self.valid_kb() | {"procedure_steps": "신청합니다."}
        issues = validate_schema(record, self.kb_record_schema, "kb_records.json")
        self.assertIn("SCHEMA_TYPE", {issue.code for issue in issues})

    def test_invalid_enum_is_rejected(self) -> None:
        record = self.valid_kb() | {"category": "NOT_A_CATEGORY"}
        issues = validate_schema(record, self.kb_record_schema, "kb_records.json")
        self.assertIn("SCHEMA_ENUM", {issue.code for issue in issues})

    def test_invalid_id_pattern_is_rejected(self) -> None:
        record = self.valid_kb() | {"id": "move-01"}
        issues = validate_schema(record, self.kb_record_schema, "kb_records.json")
        self.assertIn("SCHEMA_PATTERN", {issue.code for issue in issues})

    def test_nullable_fields_allow_null_but_reject_other_types(self) -> None:
        valid_issues = validate_schema(
            self.valid_kb() | {"processing_time": None},
            self.kb_record_schema,
            "kb_records.json",
        )
        invalid_issues = validate_schema(
            self.valid_kb() | {"processing_time": 30},
            self.kb_record_schema,
            "kb_records.json",
        )
        self.assertNotIn("SCHEMA_TYPE", {issue.code for issue in valid_issues})
        self.assertIn("SCHEMA_TYPE", {issue.code for issue in invalid_issues})

    def test_root_schema_version_mismatch_is_rejected(self) -> None:
        root = {
            "schema_version": 2,
            "draft_version": "0.1.0-draft.1",
            "records": [self.valid_kb()],
        }
        issues = validate_schema(root, self.kb_schema, "kb_records.json")
        self.assertIn("SCHEMA_CONST", {issue.code for issue in issues})

    def test_issues_are_sorted_by_public_fields(self) -> None:
        first = self.valid_kb() | {"id": "KB-MOVE-02", "source_url": "http://x.test"}
        second = self.valid_kb() | {"id": "KB-MOVE-01", "category": "NOT_A_CATEGORY"}
        root = {
            "schema_version": 1,
            "draft_version": "0.1.0-draft.1",
            "records": [first, second],
        }
        issues = validate_schema(root, self.kb_schema, "kb_records.json")
        keys = [
            (issue.artifact, issue.record_id or "", issue.field or "", issue.code)
            for issue in issues
        ]
        self.assertEqual(keys, sorted(keys))

    def test_issue_serialization_never_contains_offending_value(self) -> None:
        secret_like_value = "DO-NOT-SERIALIZE-THIS-VALUE"
        issue = validate_schema(
            self.valid_kb() | {"category": secret_like_value},
            self.kb_record_schema,
            "kb_records.json",
        )[0]
        serialized = asdict(issue)
        self.assertEqual(set(serialized), {"code", "artifact", "record_id", "field"})
        self.assertNotIn(secret_like_value, json.dumps(serialized, ensure_ascii=False))

    def test_json_helpers_load_write_and_hash_objects_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "artifact.json"
            write_json(path, {"b": 1, "a": ["x"]})
            self.assertEqual(load_json_object(path), {"a": ["x"], "b": 1})
            self.assertEqual(
                sha256_file(path),
                "a6fb0a0dda9d2f80ff03cc39f1ee7b6ac375f2f2abc7e52f2af9a510014f39e3",
            )

    def test_validation_issue_is_frozen_and_orderable(self) -> None:
        first = ValidationIssue("A", "artifact", None, None)
        second = ValidationIssue("B", "artifact", None, None)
        self.assertLess(first, second)
        with self.assertRaises(AttributeError):
            first.code = "C"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
