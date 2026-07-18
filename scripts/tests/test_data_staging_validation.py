"""Tests for the dependency-free DATA-001 staging schema helpers."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.data_staging_validation import (
    ValidationIssue,
    build_pending_manifest,
    load_json_object,
    sha256_file,
    validate_staging,
    validate_schema,
    write_json,
)
from scripts.validate_data_staging import main as data_staging_cli


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

    def test_malformed_identifiers_are_not_retained_in_issues(self) -> None:
        sentinel = "DO-NOT-SERIALIZE-MALFORMED-ID"
        office_schema = json.loads(
            (SCHEMA_DIR / "offices.schema.json").read_text(encoding="utf-8")
        )
        mapping_schema = json.loads(
            (SCHEMA_DIR / "office-service-mappings.schema.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_schema = json.loads(
            (SCHEMA_DIR / "approval-manifest.schema.json").read_text(encoding="utf-8")
        )
        cases = [
            (
                self.valid_kb() | {"id": sentinel},
                self.kb_record_schema,
                "kb_records.json",
            ),
            (
                {
                    "public_id": sentinel,
                    "data_origin": "OFFICIAL",
                    "region": "아름동",
                    "office_name": "기관",
                    "address": "공개 주소",
                    "phone": "044-301-0000",
                    "opening_hours": None,
                    "map_url": None,
                    "provider": "세종시",
                    "source_title": "공식 기관",
                    "source_url": "https://example.test/office",
                    "last_verified_at": "2026-07-18",
                    "created_by": "AI-DATA-BACKEND",
                },
                office_schema["properties"]["records"]["items"],
                "offices.json",
            ),
            (
                {
                    "office_public_id": sentinel,
                    "intent": "MOVE_IN_RESIDENT_REGISTRATION",
                    "department_label": None,
                    "evidence_source_url": "https://example.test/mapping",
                    "last_verified_at": "2026-07-18",
                    "created_by": "AI-DATA-BACKEND",
                },
                mapping_schema["properties"]["records"]["items"],
                "office_service_mappings.json",
            ),
            (
                {
                    "record_type": "KB",
                    "record_id": sentinel,
                    "decision": "REJECT",
                    "comment": None,
                },
                manifest_schema["properties"]["decisions"]["items"],
                "approval_manifest.json",
            ),
        ]
        for instance, schema, artifact in cases:
            with self.subTest(artifact=artifact):
                issues = validate_schema(instance, schema, artifact)
                serialized = json.dumps([asdict(issue) for issue in issues])
                self.assertTrue(issues)
                self.assertTrue(all(issue.record_id is None for issue in issues))
                self.assertNotIn(sentinel, serialized)

    def test_const_and_enum_distinguish_boolean_and_integer_values(self) -> None:
        const_issues = validate_schema(True, {"const": 1}, "test.json")
        enum_issues = validate_schema(True, {"enum": [1]}, "test.json")
        self.assertIn("SCHEMA_CONST", {issue.code for issue in const_issues})
        self.assertIn("SCHEMA_ENUM", {issue.code for issue in enum_issues})

    def test_every_schema_version_rejects_booleans_as_non_integers(self) -> None:
        schema_names = [
            "kb-records.schema.json",
            "offices.schema.json",
            "office-service-mappings.schema.json",
            "approval-manifest.schema.json",
        ]
        for schema_name in schema_names:
            with self.subTest(schema_name=schema_name):
                schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
                version_schema = schema["properties"]["schema_version"]
                for value in (True, False):
                    issues = validate_schema(value, version_schema, schema_name)
                    self.assertIn("SCHEMA_TYPE", {issue.code for issue in issues})

    def test_negative_manifest_record_count_is_rejected(self) -> None:
        manifest_schema = json.loads(
            (SCHEMA_DIR / "approval-manifest.schema.json").read_text(encoding="utf-8")
        )
        artifact_schema = manifest_schema["properties"]["artifacts"]["items"]
        issues = validate_schema(
            {
                "path": "kb_records.json",
                "record_count": -1,
                "sha256": "a" * 64,
            },
            artifact_schema,
            "approval_manifest.json",
        )
        self.assertIn("SCHEMA_MINIMUM", {issue.code for issue in issues})

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


class DataStagingBusinessValidationTests(unittest.TestCase):
    def valid_kb(self, number: int) -> dict[str, object]:
        category = ("MOVE", "CERT", "WASTE", "TAX")[(number - 1) // 5]
        return {
            "id": f"KB-{category}-{((number - 1) % 5) + 1:02d}",
            "data_origin": "OFFICIAL",
            "category": {
                "MOVE": "MOVE_IN_RESIDENT_REGISTRATION",
                "CERT": "CERTIFICATE_ISSUANCE",
                "WASTE": "BULKY_WASTE",
                "TAX": "LOCAL_TAX_GENERAL",
            }[category],
            "service_name": "공식 민원 안내",
            "question_examples": ["어떻게 하나요", "어디서 하나요", "무엇이 필요한가요"],
            "answer_summary": "공식 안내를 확인합니다.",
            "procedure_steps": ["공식 경로를 확인합니다."],
            "required_documents": [],
            "processing_time": None,
            "fee": None,
            "department": "민원행정과",
            "provider": "정부24",
            "source_title": "공식 민원 안내",
            "source_url": f"https://plus.gov.kr/service/{number}",
            "source_service_id": None,
            "last_verified_at": "2026-07-18",
            "caution": None,
            "status": "DRAFT",
            "created_by": "AI-DATA-BACKEND",
            "approved_by": None,
            "approved_at": None,
        }

    def valid_office(self, public_id: str, region: str) -> dict[str, object]:
        return {
            "public_id": public_id,
            "data_origin": "OFFICIAL",
            "region": region,
            "office_name": "행정복지센터",
            "address": "세종특별자치시 공공기관로 1",
            "phone": "044-301-6000",
            "opening_hours": "평일 09:00~18:00",
            "map_url": "https://place.map.kakao.com/1",
            "provider": "세종특별자치시",
            "source_title": "공식 기관 안내",
            "source_url": "https://www.sejong.go.kr/office",
            "last_verified_at": "2026-07-18",
            "created_by": "AI-DATA-BACKEND",
        }

    def complete_draft(self, directory: Path) -> Path:
        kb_records = sorted(
            (self.valid_kb(number) for number in range(1, 21)),
            key=lambda record: str(record["id"]),
        )
        offices = [
            self.valid_office("OFFICE-AREUM", "아름동"),
            self.valid_office("OFFICE-DODAM", "도담동"),
            self.valid_office("OFFICE-JOCHIWON", "조치원읍"),
        ]
        intents = [
            "BULKY_WASTE",
            "CERTIFICATE_ISSUANCE",
            "LOCAL_TAX_GENERAL",
            "MOVE_IN_RESIDENT_REGISTRATION",
        ]
        mappings = [
            {
                "office_public_id": office["public_id"],
                "intent": intent,
                "department_label": "민원행정",
                "evidence_source_url": "https://www.sejong.go.kr/services",
                "last_verified_at": "2026-07-18",
                "created_by": "AI-DATA-BACKEND",
            }
            for office in offices
            for intent in intents
        ]
        write_json(directory / "kb_records.json", {
            "schema_version": 1, "draft_version": "0.1.0-draft.1", "records": kb_records,
        })
        write_json(directory / "offices.json", {
            "schema_version": 1, "draft_version": "0.1.0-draft.1", "records": offices,
        })
        write_json(directory / "office_service_mappings.json", {
            "schema_version": 1, "draft_version": "0.1.0-draft.1", "records": mappings,
        })
        write_json(directory / "approval_manifest.json", build_pending_manifest(
            directory, "2026-07-18T18:00:00+09:00"
        ))
        return directory

    def source_registry(self, directory: Path) -> Path:
        registry = directory / "kb_source_registry.csv"
        rows = [
            "kb_id,분야,세부 주제,공식 출처명,제공기관,URL,확인일,사용 필드,작성 상태,작성자,검수자,한계·주의"
        ]
        for record_id in sorted(record["id"] for record in (self.valid_kb(number) for number in range(1, 21))):
            number = next(
                number for number in range(1, 21)
                if self.valid_kb(number)["id"] == record_id
            )
            rows.append(
                f"{record_id},분야,세부 주제,공식 민원 안내,정부24,https://plus.gov.kr/service/{number},2026-07-18,사용 필드,검수 대기,AI-DATA-BACKEND,,한계"
            )
        registry.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        return registry

    def validate(self, draft_dir: Path, registry: Path) -> dict[str, object]:
        return validate_staging(draft_dir, SCHEMA_DIR, registry)

    def codes(self, report: dict[str, object]) -> set[str]:
        return {issue["code"] for issue in report["issues"]}  # type: ignore[index]

    def canonical_json_bytes(self, value: object) -> bytes:
        return (
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")

    def reviewed_manifest(
        self, directory: Path, state: str = "APPROVED_FOR_INITIAL_RELEASE",
        approved_mappings: int = 10,
    ) -> dict[str, object]:
        manifest = build_pending_manifest(directory, "2026-07-18T20:45:00+09:00")
        manifest.update({
            "state": state,
            "reviewed_by": "PM-REVIEWER",
            "reviewed_at": "2026-07-18T21:00:00+09:00",
            "review_comment": "전수 검수 완료",
        })
        decisions = manifest["decisions"]
        assert isinstance(decisions, list)
        mapping_approved = 0
        for entry in decisions:
            assert isinstance(entry, dict)
            recommendation = entry["recommended_decision"]
            decision = recommendation
            if entry["record_type"] == "MAPPING":
                if mapping_approved < approved_mappings:
                    decision = "APPROVE_INITIAL_RELEASE"
                    mapping_approved += 1
                else:
                    decision = "REJECT"
            entry["decision"] = decision
            entry["comment"] = "PM record 검수 완료"
        return manifest

    def legacy_pending_manifest(self, directory: Path) -> dict[str, object]:
        manifest = build_pending_manifest(directory, "2026-07-18T19:32:04+09:00")
        decisions = manifest["decisions"]
        assert isinstance(decisions, list)
        for entry in decisions:
            assert isinstance(entry, dict)
            entry["decision"] = entry.pop("recommended_decision")
        return manifest

    def test_exact_counts_ids_and_record_order_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            kb = load_json_object(directory / "kb_records.json")
            records = kb["records"]
            assert isinstance(records, list)
            kb["records"] = records[1:] + [records[0], records[0]]
            write_json(directory / "kb_records.json", kb)
            codes = self.codes(self.validate(directory, registry))
            self.assertTrue({"COUNT_KB", "DUPLICATE_RECORD_ID", "RECORD_ORDER"} <= codes)

    def test_source_registry_domain_and_metadata_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            kb = load_json_object(directory / "kb_records.json")
            records = kb["records"]
            assert isinstance(records, list) and isinstance(records[0], dict)
            records[0]["source_url"] = "https://example.test/private"
            write_json(directory / "kb_records.json", kb)
            registry.write_text(
                registry.read_text(encoding="utf-8").replace("KB-TAX-05", "KB-TAX-06"),
                encoding="utf-8", newline="\n",
            )
            codes = self.codes(self.validate(directory, registry))
            self.assertTrue({"SOURCE_REGISTRY_ID_SET", "SOURCE_DOMAIN_NOT_ALLOWED", "SOURCE_METADATA_MISMATCH"} <= codes)

    def test_mapping_references_keys_and_intents_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            mappings = load_json_object(directory / "office_service_mappings.json")
            records = mappings["records"]
            assert isinstance(records, list) and isinstance(records[0], dict)
            records[0]["office_public_id"] = "OFFICE-UNKNOWN"
            records[1] = dict(records[2])
            records[3]["intent"] = "UNSUPPORTED"
            write_json(directory / "office_service_mappings.json", mappings)
            codes = self.codes(self.validate(directory, registry))
            self.assertTrue({"ORPHAN_OFFICE_MAPPING", "DUPLICATE_MAPPING_KEY", "UNSUPPORTED_INTENT"} <= codes)

    def test_pii_secret_and_mock_references_are_rejected_but_public_office_contact_is_allowed(self) -> None:
        cases = [
            ("answer_summary", "900101-1234567"),
            ("answer_summary", "010-1234-5678"),
            ("answer_summary", "person@example.com"),
            ("answer_summary", "12가3456"),
            ("answer_summary", "세종시 보듬로 1 101동 1001호"),
            ("answer_summary", "api_" + "key=" + "s" + "k-test-token"),
            ("answer_summary", "시연용 샘플 mock record"),
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            kb = load_json_object(directory / "kb_records.json")
            records = kb["records"]
            assert isinstance(records, list)
            for index, (field, value) in enumerate(cases):
                assert isinstance(records[index], dict)
                records[index][field] = value
            write_json(directory / "kb_records.json", kb)
            report = self.validate(directory, registry)
            self.assertTrue({"PII_DETECTED", "SECRET_DETECTED", "MOCK_REFERENCE"} <= self.codes(report))
            office_issues = [
                issue for issue in report["issues"]
                if issue["artifact"] == "offices.json" and issue["field"] in {"records.0.phone", "records.0.address"}
            ]
            self.assertEqual([], office_issues)

    def test_draft_metadata_and_pending_manifest_review_fields_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            kb = load_json_object(directory / "kb_records.json")
            records = kb["records"]
            assert isinstance(records, list) and isinstance(records[0], dict)
            records[0]["status"] = "ACTIVE"
            records[0]["approved_by"] = "PM"
            write_json(directory / "kb_records.json", kb)
            manifest = load_json_object(directory / "approval_manifest.json")
            manifest["reviewed_by"] = "AI-DATA-BACKEND"
            manifest["reviewed_at"] = "2026-07-18T18:00:00+09:00"
            write_json(directory / "approval_manifest.json", manifest)
            codes = self.codes(self.validate(directory, registry))
            self.assertTrue({"KB_NOT_DRAFT", "APPROVAL_METADATA_IN_DRAFT", "SELF_APPROVAL"} <= codes)

    def test_manifest_paths_hashes_counts_and_fixed_recommendations_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest = load_json_object(directory / "approval_manifest.json")
            artifacts = manifest["artifacts"]
            assert isinstance(artifacts, list) and isinstance(artifacts[0], dict)
            artifacts[0]["path"] = "approval_manifest.json"
            artifacts[1]["record_count"] = 99
            artifacts[2]["sha256"] = "0" * 64
            decisions = manifest["decisions"]
            assert isinstance(decisions, list) and isinstance(decisions[0], dict)
            decisions[:] = [decision for decision in decisions if decision["record_id"] != "KB-WASTE-03"]
            write_json(directory / "approval_manifest.json", manifest)
            codes = self.codes(self.validate(directory, registry))
            self.assertTrue({
                "MANIFEST_CONTENT_PATH_SET", "MANIFEST_HASH_MISMATCH", "MANIFEST_COUNT_MISMATCH",
                "WASTE_03_DECISION", "INITIAL_PROJECTION_MISMATCH",
            } <= codes)

    def test_runtime_staging_reference_is_rejected_and_cli_has_stable_exit_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            runtime_reference = Path("apps") / "data_staging_boundary_test.py"
            runtime_reference.write_text('path = "data/staging/data-001"\n', encoding="utf-8")
            try:
                self.assertIn("RUNTIME_STAGING_REFERENCE", self.codes(self.validate(directory, registry)))
            finally:
                runtime_reference.unlink(missing_ok=True)
            cli = Path("scripts/validate_data_staging.py")
            failed = subprocess.run(
                [sys.executable, "-B", str(cli), "validate", "--draft-dir", str(directory), "--source-registry", str(registry)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, failed.returncode)
            self.assertEqual("[PASS] step=VALIDATE-DATA-001\n", failed.stdout)
            invalid = load_json_object(directory / "kb_records.json")
            invalid["records"] = []
            write_json(directory / "kb_records.json", invalid)
            failed = subprocess.run(
                [sys.executable, "-B", str(cli), "validate", "--draft-dir", str(directory), "--source-registry", str(registry)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(1, failed.returncode)
            self.assertRegex(failed.stdout, r"^\[FAIL\] step=VALIDATE-DATA-001 issues=.+\n$")
            self.assertNotIn("공식", failed.stdout)
            usage = subprocess.run(
                [sys.executable, "-B", str(cli), "validate"],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(2, usage.returncode)
            self.assertEqual("[FAIL] step=VALIDATE-DATA-001 reason=usage\n", usage.stdout)
            self.assertEqual("", usage.stderr)

    def test_office_phone_and_address_still_reject_secrets_and_mock_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            offices = load_json_object(directory / "offices.json")
            records = offices["records"]
            assert isinstance(records, list) and isinstance(records[0], dict)
            records[0]["phone"] = "token=private-value mock"
            records[0]["address"] = "secret=private-value 시연용 샘플"
            write_json(directory / "offices.json", offices)
            issues = self.validate(directory, registry)["issues"]
            codes_by_field = {
                issue["field"]: issue["code"] for issue in issues
                if issue["artifact"] == "offices.json"
            }
            self.assertEqual("SECRET_DETECTED", codes_by_field["phone"])
            self.assertEqual("SECRET_DETECTED", codes_by_field["address"])
            self.assertIn(
                "MOCK_REFERENCE",
                {issue["code"] for issue in issues if issue["artifact"] == "offices.json"},
            )

    def test_cli_report_rejects_content_and_outside_destinations_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            content = directory / "kb_records.json"
            before = content.read_bytes()
            self.assertEqual(1, data_staging_cli([
                "validate", "--draft-dir", str(directory), "--source-registry", str(registry),
                "--report", str(content),
            ]))
            self.assertEqual(before, content.read_bytes())
            outside = Path(temporary_directory) / "outside-report.json"
            self.assertEqual(1, data_staging_cli([
                "validate", "--draft-dir", str(directory), "--source-registry", str(registry),
                "--report", str(outside),
            ]))
            self.assertFalse(outside.exists())
            allowed = Path("data/processed/.task2-validation-report.json")
            try:
                self.assertEqual(0, data_staging_cli([
                    "validate", "--draft-dir", str(directory), "--source-registry", str(registry),
                    "--report", str(allowed),
                ]))
                self.assertTrue(allowed.is_file())
            finally:
                allowed.unlink(missing_ok=True)

    def test_cli_report_rejects_processed_symlink_alias_without_outside_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            alias = Path("data/processed/.task2-alias")
            target = Path(temporary_directory) / "outside"
            target.mkdir()
            try:
                alias.symlink_to(target, target_is_directory=True)
            except OSError as error:
                junction = subprocess.run(
                    ["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(target)],
                    text=True, capture_output=True, check=False,
                )
                if junction.returncode != 0:
                    self.skipTest(f"link unavailable: {type(error).__name__}")
            try:
                report = alias / "report.json"
                self.assertEqual(1, data_staging_cli([
                    "validate", "--draft-dir", str(directory), "--source-registry", str(registry),
                    "--report", str(report),
                ]))
                self.assertFalse((target / "report.json").exists())
            finally:
                if alias.is_dir():
                    alias.rmdir()
                else:
                    alias.unlink(missing_ok=True)

    def test_prepare_rejects_invalid_content_before_replacing_existing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest = directory / "approval_manifest.json"
            prior = manifest.read_bytes()
            kb = load_json_object(directory / "kb_records.json")
            kb["records"] = []
            write_json(directory / "kb_records.json", kb)
            content = (directory / "kb_records.json").read_bytes()
            self.assertEqual(1, data_staging_cli([
                "prepare", "--draft-dir", str(directory),
                "--submitted-at", "2026-07-18T18:00:00+09:00",
                "--source-registry", str(registry),
            ]))
            self.assertEqual(prior, manifest.read_bytes())
            self.assertEqual(content, (directory / "kb_records.json").read_bytes())

    def test_prepare_rejects_pii_and_unapproved_source_without_replacing_manifest(self) -> None:
        for field, value in (("answer_summary", "900101-1234567"), ("source_url", "https://example.test/nope")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary_directory:
                directory = self.complete_draft(Path(temporary_directory) / "draft")
                registry = self.source_registry(Path(temporary_directory))
                manifest = directory / "approval_manifest.json"
                prior = manifest.read_bytes()
                kb = load_json_object(directory / "kb_records.json")
                records = kb["records"]
                assert isinstance(records, list) and isinstance(records[0], dict)
                records[0][field] = value
                write_json(directory / "kb_records.json", kb)
                self.assertEqual(1, data_staging_cli([
                    "prepare", "--draft-dir", str(directory),
                    "--submitted-at", "2026-07-18T18:00:00+09:00",
                    "--source-registry", str(registry),
                ]))
                self.assertEqual(prior, manifest.read_bytes())

    def test_prepare_accepts_valid_first_submission_without_current_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest = directory / "approval_manifest.json"
            manifest.unlink()
            self.assertEqual(0, data_staging_cli([
                "prepare", "--draft-dir", str(directory),
                "--submitted-at", "2026-07-18T18:00:00+09:00",
                "--source-registry", str(registry),
            ]))
            self.assertTrue(manifest.is_file())
            prepared = load_json_object(manifest)
            self.assertEqual("PENDING_PM_REVIEW", prepared["state"])

    def test_canonical_kb_and_source_registry_rows_are_not_draft_defined(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            kb = load_json_object(directory / "kb_records.json")
            records = kb["records"]
            assert isinstance(records, list) and isinstance(records[0], dict)
            records[0]["id"] = "KB-MOVE-06"
            records[0]["category"] = "CERTIFICATE_ISSUANCE"
            write_json(directory / "kb_records.json", kb)
            registry.write_text(
                registry.read_text(encoding="utf-8").replace("KB-CERT-01", "KB-MOVE-06")
                + "KB-MOVE-06,conflict,provider,https://plus.gov.kr/conflict,2026-07-18\n",
                encoding="utf-8", newline="\n",
            )
            codes = self.codes(self.validate(directory, registry))
            self.assertTrue({
                "KB_CANONICAL_ID_SET", "KB_CATEGORY_MISMATCH", "SOURCE_REGISTRY_DUPLICATE_ID",
                "SOURCE_REGISTRY_ROW_ORDER",
            } <= codes)

    def test_source_registry_requires_exact_columns_and_nonempty_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "kb_id,분야,세부 주제,공식 출처명,제공기관,URL,확인일,사용 필드,작성 상태,작성자,검수자,한계·주의",
                    "kb_id,분야,세부 주제,공식 출처명,제공기관,URL,확인일,사용 필드,작성 상태,작성자,검수자,extra",
                ).replace("정부24", "", 1),
                encoding="utf-8", newline="\n",
            )
            codes = self.codes(self.validate(directory, registry))
            self.assertTrue({"SOURCE_REGISTRY_COLUMN_SET", "SOURCE_REGISTRY_METADATA_REQUIRED"} <= codes)

    def test_task3_shaped_source_registry_requires_pending_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            self.assertTrue(self.validate(directory, registry)["valid"])
            registry.write_text(
                registry.read_text(encoding="utf-8").replace("검수 대기", "작성 완료", 1)
                .replace("AI-DATA-BACKEND", "", 1),
                encoding="utf-8", newline="\n",
            )
            codes = self.codes(self.validate(directory, registry))
            self.assertIn("SOURCE_REGISTRY_PENDING_METADATA", codes)

    def test_task3_registry_reordered_header_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "분야,세부 주제", "세부 주제,분야", 1
                ),
                encoding="utf-8", newline="\n",
            )
            self.assertIn(
                "SOURCE_REGISTRY_COLUMN_SET", self.codes(self.validate(directory, registry))
            )

    def test_pending_manifest_separates_recommendations_from_null_pm_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest = load_json_object(directory / "approval_manifest.json")
            decisions = manifest["decisions"]
            assert isinstance(decisions, list)
            self.assertEqual(35, len(decisions))
            self.assertTrue(all(entry["decision"] is None for entry in decisions))
            self.assertTrue(all(entry["comment"] is None for entry in decisions))
            self.assertEqual("WITHHOLD_FOR_REGRESSION", decisions[17]["recommended_decision"])
            report = self.validate(directory, registry)
            self.assertTrue(report["valid"])
            self.assertEqual(["PM_REVIEW_REQUIRED"], report["warnings"])

            self.assertIsNone(report["approval_projection"])
            self.assertEqual({
                "initial_kb": 19,
                "initial_office": 3,
                "initial_mapping": 10,
                "withheld_kb": 1,
                "rejected_mapping": 2,
            }, report["recommendation_projection"])

    def test_reviewed_approved_and_rejected_states_validate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            for state in ("APPROVED_FOR_INITIAL_RELEASE", "REJECTED"):
                with self.subTest(state=state):
                    manifest = self.reviewed_manifest(directory, state)
                    if state == "REJECTED":
                        for entry in manifest["decisions"]:
                            entry["decision"] = "REJECT"
                    write_json(directory / "approval_manifest.json", manifest)
                    report = self.validate(directory, registry)
                    self.assertTrue(report["valid"], report["issues"])
                    self.assertEqual([], report["warnings"])
                    self.assertIsNone(report["recommendation_projection"])
                    if state == "REJECTED":
                        self.assertIsNone(report["approval_projection"])
                    else:
                        self.assertEqual(10, report["approval_projection"]["initial_mapping"])

    def test_invalid_approval_or_recommendation_evidence_has_no_trusted_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest_path = directory / "approval_manifest.json"

            pending = load_json_object(manifest_path)
            pending["decisions"][0]["recommended_decision"] = "REJECT"
            write_json(manifest_path, pending)
            report = self.validate(directory, registry)
            self.assertFalse(report["valid"])
            self.assertIsNone(report["approval_projection"])
            self.assertIsNone(report["recommendation_projection"])
            self.assertEqual([], report["warnings"])

            decision_invalid = self.reviewed_manifest(directory)
            decision_invalid["decisions"][0]["decision"] = None
            write_json(manifest_path, decision_invalid)
            report = self.validate(directory, registry)
            self.assertFalse(report["valid"])
            self.assertIsNone(report["approval_projection"])
            self.assertIsNone(report["recommendation_projection"])

            approved = self.reviewed_manifest(directory)
            write_json(manifest_path, approved)
            kb_path = directory / "kb_records.json"
            kb_path.write_bytes(kb_path.read_bytes() + b" ")
            report = self.validate(directory, registry)
            self.assertFalse(report["valid"])
            self.assertIn("MANIFEST_HASH_MISMATCH", self.codes(report))
            self.assertIsNone(report["approval_projection"])
            self.assertIsNone(report["recommendation_projection"])

    def test_approved_state_allows_ten_to_twelve_mapping_approvals(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            for approved_mappings in (10, 11, 12):
                with self.subTest(approved_mappings=approved_mappings):
                    write_json(
                        directory / "approval_manifest.json",
                        self.reviewed_manifest(directory, approved_mappings=approved_mappings),
                    )
                    report = self.validate(directory, registry)
                    self.assertTrue(report["valid"], report["issues"])
                    self.assertEqual(approved_mappings, report["approval_projection"]["initial_mapping"])

    def test_reviewed_state_rejects_self_review_and_missing_comments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest = self.reviewed_manifest(directory)
            manifest["reviewed_by"] = "AI-DATA-BACKEND"
            manifest["review_comment"] = ""
            manifest["decisions"][0]["comment"] = None
            write_json(directory / "approval_manifest.json", manifest)
            codes = self.codes(self.validate(directory, registry))
            self.assertTrue({"SELF_APPROVAL", "REVIEW_METADATA_REQUIRED", "DECISION_COMMENT_REQUIRED"} <= codes)

    def test_manifest_decisions_reject_duplicate_type_swap_and_wrong_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest = self.reviewed_manifest(directory)
            decisions = manifest["decisions"]
            decisions.insert(0, dict(decisions[0]))
            decisions[2]["record_type"] = "OFFICE"
            decisions[3], decisions[4] = decisions[4], decisions[3]
            write_json(directory / "approval_manifest.json", manifest)
            codes = self.codes(self.validate(directory, registry))
            self.assertTrue({"DECISION_DUPLICATE", "DECISION_TYPE_ID_MISMATCH", "DECISION_ORDER"} <= codes)

    def test_prepare_protects_reviewed_and_differing_pending_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest_path = directory / "approval_manifest.json"
            reviewed = self.reviewed_manifest(directory)
            write_json(manifest_path, reviewed)
            before = manifest_path.read_bytes()
            self.assertEqual(1, data_staging_cli([
                "prepare", "--draft-dir", str(directory),
                "--submitted-at", "2026-07-18T20:45:00+09:00",
                "--source-registry", str(registry),
            ]))
            self.assertEqual(before, manifest_path.read_bytes())
            pending = build_pending_manifest(directory, "2026-07-18T20:45:00+09:00")
            write_json(manifest_path, pending)
            before = manifest_path.read_bytes()
            self.assertEqual(1, data_staging_cli([
                "prepare", "--draft-dir", str(directory),
                "--submitted-at", "2026-07-18T20:46:00+09:00",
                "--source-registry", str(registry),
            ]))
            self.assertEqual(before, manifest_path.read_bytes())

    def test_prepare_is_idempotent_only_for_byte_identical_pending_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest_path = directory / "approval_manifest.json"
            pending = build_pending_manifest(directory, "2026-07-18T20:45:00+09:00")
            write_json(manifest_path, pending)
            before = manifest_path.read_bytes()
            self.assertEqual(0, data_staging_cli([
                "prepare", "--draft-dir", str(directory),
                "--submitted-at", "2026-07-18T20:45:00+09:00",
                "--source-registry", str(registry),
            ]))
            self.assertEqual(before, manifest_path.read_bytes())

    def test_migrate_pending_upgrades_only_legacy_unreviewed_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = self.complete_draft(Path(temporary_directory) / "draft")
            registry = self.source_registry(Path(temporary_directory))
            manifest_path = directory / "approval_manifest.json"
            legacy = self.legacy_pending_manifest(directory)
            write_json(manifest_path, legacy)
            self.assertEqual(self.canonical_json_bytes(legacy), manifest_path.read_bytes())
            self.assertEqual(0, data_staging_cli([
                "migrate-pending", "--draft-dir", str(directory),
                "--submitted-at", "2026-07-18T21:15:00+09:00",
                "--source-registry", str(registry),
            ]))
            migrated = load_json_object(manifest_path)
            self.assertEqual("2026-07-18T21:15:00+09:00", migrated["submitted_at"])
            self.assertTrue(all(entry["decision"] is None for entry in migrated["decisions"]))
            self.assertTrue(all("recommended_decision" in entry for entry in migrated["decisions"]))

    def test_migrate_pending_refuses_noncanonical_legacy_bytes_without_writes(self) -> None:
        def reversed_top_level(_: bytes, manifest: dict[str, object]) -> bytes:
            reordered = dict(reversed(tuple(manifest.items())))
            return (
                json.dumps(reordered, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
            ).encode("utf-8")

        def reversed_nested_artifact(canonical: bytes, manifest: dict[str, object]) -> bytes:
            artifacts = manifest["artifacts"]
            assert isinstance(artifacts, list) and isinstance(artifacts[0], dict)
            artifact = artifacts[0]
            old = (
                "    {\n"
                f"      \"path\": {json.dumps(artifact['path'], ensure_ascii=False)},\n"
                f"      \"record_count\": {artifact['record_count']},\n"
                f"      \"sha256\": {json.dumps(artifact['sha256'])}\n"
                "    }"
            ).encode("utf-8")
            new = (
                "    {\n"
                f"      \"sha256\": {json.dumps(artifact['sha256'])},\n"
                f"      \"record_count\": {artifact['record_count']},\n"
                f"      \"path\": {json.dumps(artifact['path'], ensure_ascii=False)}\n"
                "    }"
            ).encode("utf-8")
            self.assertIn(old, canonical)
            return canonical.replace(old, new, 1)

        variants = (
            ("reversed_top_level_keys", reversed_top_level),
            ("reversed_nested_artifact_keys", reversed_nested_artifact),
            ("four_space_indent", lambda _, value: (
                json.dumps(value, ensure_ascii=False, indent=4, sort_keys=True) + "\n"
            ).encode("utf-8")),
            ("crlf", lambda canonical, _: canonical.replace(b"\n", b"\r\n")),
            ("utf8_bom", lambda canonical, _: b"\xef\xbb\xbf" + canonical),
            ("missing_trailing_lf", lambda canonical, _: canonical.removesuffix(b"\n")),
            ("duplicate_member", lambda canonical, _: canonical.replace(
                b"{\n", b'{\n  "schema_version": 1,\n', 1
            )),
        )
        for name, alter in variants:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary_directory:
                directory = self.complete_draft(Path(temporary_directory) / "draft")
                registry = self.source_registry(Path(temporary_directory))
                manifest_path = directory / "approval_manifest.json"
                legacy = self.legacy_pending_manifest(directory)
                canonical = self.canonical_json_bytes(legacy)
                altered = alter(canonical, legacy)
                self.assertNotEqual(canonical, altered)
                manifest_path.write_bytes(altered)
                before = manifest_path.read_bytes()
                self.assertEqual(1, data_staging_cli([
                    "migrate-pending", "--draft-dir", str(directory),
                    "--submitted-at", "2026-07-18T21:15:00+09:00",
                    "--source-registry", str(registry),
                ]))
                self.assertEqual(before, manifest_path.read_bytes())

    def test_migrate_pending_refuses_every_altered_legacy_boundary_without_writes(self) -> None:
        def set_artifact(manifest: dict[str, object], field: str, value: object) -> None:
            artifacts = manifest["artifacts"]
            assert isinstance(artifacts, list) and isinstance(artifacts[0], dict)
            artifacts[0][field] = value

        def set_decision(manifest: dict[str, object], field: str, value: object) -> None:
            decisions = manifest["decisions"]
            assert isinstance(decisions, list) and isinstance(decisions[0], dict)
            decisions[0][field] = value

        def reorder_decisions(manifest: dict[str, object]) -> None:
            decisions = manifest["decisions"]
            assert isinstance(decisions, list)
            decisions[0], decisions[1] = decisions[1], decisions[0]

        mutations = (
            ("schema_version", lambda value: value.__setitem__("schema_version", 99)),
            ("schema_version_bool", lambda value: value.__setitem__("schema_version", True)),
            ("schema_version_float", lambda value: value.__setitem__("schema_version", 1.0)),
            ("dataset_id", lambda value: value.__setitem__("dataset_id", "other-data")),
            ("draft_version", lambda value: value.__setitem__("draft_version", "0.1.0-draft.2")),
            ("state", lambda value: value.__setitem__("state", "REJECTED")),
            ("created_by", lambda value: value.__setitem__("created_by", "OTHER")),
            ("submitted_at", lambda value: value.__setitem__("submitted_at", "2026-07-18 20:45:00")),
            ("submitted_at_altered", lambda value: value.__setitem__("submitted_at", "2026-07-18T19:32:05+09:00")),
            ("reviewed_by", lambda value: value.__setitem__("reviewed_by", "PM-REVIEWER")),
            ("reviewed_at", lambda value: value.__setitem__("reviewed_at", "2026-07-18T21:00:00+09:00")),
            ("review_comment", lambda value: value.__setitem__("review_comment", "검수 흔적")),
            ("top_level_unknown", lambda value: value.__setitem__("unexpected", True)),
            ("artifact_path", lambda value: set_artifact(value, "path", "other.json")),
            ("artifact_count", lambda value: set_artifact(value, "record_count", 99)),
            ("artifact_count_bool", lambda value: set_artifact(value, "record_count", True)),
            ("artifact_hash", lambda value: set_artifact(value, "sha256", "0" * 64)),
            ("artifact_unknown", lambda value: set_artifact(value, "unexpected", True)),
            ("decision_type", lambda value: set_decision(value, "record_type", "OFFICE")),
            ("decision_id", lambda value: set_decision(value, "record_id", "KB-MOVE-01")),
            ("decision_value", lambda value: set_decision(value, "decision", "REJECT")),
            ("decision_value_bool", lambda value: set_decision(value, "decision", True)),
            ("decision_comment", lambda value: set_decision(value, "comment", "altered")),
            ("decision_unknown", lambda value: set_decision(value, "unexpected", True)),
            ("decision_order", reorder_decisions),
        )
        for name, mutate in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary_directory:
                directory = self.complete_draft(Path(temporary_directory) / "draft")
                registry = self.source_registry(Path(temporary_directory))
                manifest_path = directory / "approval_manifest.json"
                legacy = self.legacy_pending_manifest(directory)
                mutate(legacy)
                write_json(manifest_path, legacy)
                before = manifest_path.read_bytes()
                self.assertEqual(1, data_staging_cli([
                    "migrate-pending", "--draft-dir", str(directory),
                    "--submitted-at", "2026-07-18T21:15:00+09:00",
                    "--source-registry", str(registry),
                ]))
                self.assertEqual(before, manifest_path.read_bytes())

    def test_migrate_pending_refuses_current_new_shape_without_writes(self) -> None:
        directory = Path("data/staging/data-001/0.1.0-draft.1")
        manifest_path = directory / "approval_manifest.json"
        before = manifest_path.read_bytes()
        self.assertEqual(1, data_staging_cli([
            "migrate-pending", "--draft-dir", str(directory),
            "--submitted-at", "2026-07-18T21:15:00+09:00",
            "--source-registry", "data/official/kb_source_registry.csv",
        ]))
        self.assertEqual(before, manifest_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
