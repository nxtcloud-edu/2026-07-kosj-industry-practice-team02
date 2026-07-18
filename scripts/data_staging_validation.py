"""Dependency-free helpers for validating DATA-001 staging JSON contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping, Sequence
from urllib.parse import urlparse


@dataclass(frozen=True, order=True)
class ValidationIssue:
    """A stable, value-free schema validation failure."""

    code: str
    artifact: str
    record_id: str | None
    field: str | None


def load_json_object(path: Path) -> dict[str, object]:
    """Load a JSON object without accepting arrays or scalar roots."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_ROOT_MUST_BE_OBJECT")
    return value


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for the exact bytes of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    """Write canonical UTF-8 JSON used by DATA-001 staging artifacts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(f"{serialized}\n", encoding="utf-8", newline="\n")


def validate_schema(
    instance: object, schema: dict[str, object], artifact: str
) -> Sequence[ValidationIssue]:
    """Validate the small JSON Schema subset used by DATA-001 contracts."""
    issues: list[ValidationIssue] = []
    _validate(instance, schema, artifact, None, None, issues)
    return sorted(issues, key=lambda issue: (
        issue.artifact,
        issue.record_id or "",
        issue.field or "",
        issue.code,
    ))


def _validate(
    value: object,
    schema: Mapping[str, object],
    artifact: str,
    record_id: str | None,
    field: str | None,
    issues: list[ValidationIssue],
) -> None:
    current_record_id = _record_id(value, record_id)
    if "const" in schema and value != schema["const"]:
        _issue(issues, "SCHEMA_CONST", artifact, current_record_id, field)

    allowed_types = schema.get("type")
    if allowed_types is not None and not _matches_type(value, allowed_types):
        _issue(issues, "SCHEMA_TYPE", artifact, current_record_id, field)
        return

    if "enum" in schema and value not in schema["enum"]:
        _issue(issues, "SCHEMA_ENUM", artifact, current_record_id, field)

    if isinstance(value, dict):
        _validate_object(value, schema, artifact, current_record_id, field, issues)
    elif isinstance(value, list):
        _validate_array(value, schema, artifact, current_record_id, field, issues)
    elif isinstance(value, str):
        _validate_string(value, schema, artifact, current_record_id, field, issues)


def _validate_object(
    value: dict[object, object],
    schema: Mapping[str, object],
    artifact: str,
    record_id: str | None,
    field: str | None,
    issues: list[ValidationIssue],
) -> None:
    properties = schema.get("properties", {})
    if not isinstance(properties, Mapping):
        properties = {}
    required = schema.get("required", [])
    if isinstance(required, list):
        for name in required:
            if isinstance(name, str) and name not in value:
                _issue(issues, "SCHEMA_REQUIRED", artifact, record_id, _join(field, name))
    if schema.get("additionalProperties") is False:
        for name in value:
            if isinstance(name, str) and name not in properties:
                _issue(
                    issues,
                    "SCHEMA_ADDITIONAL_PROPERTY",
                    artifact,
                    record_id,
                    _join(field, name),
                )
    for name, child_schema in properties.items():
        if name in value and isinstance(name, str) and isinstance(child_schema, Mapping):
            _validate(
                value[name],
                child_schema,
                artifact,
                record_id,
                _join(field, name),
                issues,
            )


def _validate_array(
    value: list[object],
    schema: Mapping[str, object],
    artifact: str,
    record_id: str | None,
    field: str | None,
    issues: list[ValidationIssue],
) -> None:
    minimum = schema.get("minItems")
    maximum = schema.get("maxItems")
    if isinstance(minimum, int) and len(value) < minimum:
        _issue(issues, "SCHEMA_MIN_ITEMS", artifact, record_id, field)
    if isinstance(maximum, int) and len(value) > maximum:
        _issue(issues, "SCHEMA_MAX_ITEMS", artifact, record_id, field)
    if schema.get("uniqueItems") is True and len({_canonical(item) for item in value}) != len(value):
        _issue(issues, "SCHEMA_UNIQUE_ITEMS", artifact, record_id, field)
    child_schema = schema.get("items")
    if isinstance(child_schema, Mapping):
        for index, item in enumerate(value):
            _validate(
                item,
                child_schema,
                artifact,
                record_id,
                _join(field, str(index)),
                issues,
            )


def _validate_string(
    value: str,
    schema: Mapping[str, object],
    artifact: str,
    record_id: str | None,
    field: str | None,
    issues: list[ValidationIssue],
) -> None:
    minimum = schema.get("minLength")
    maximum = schema.get("maxLength")
    if isinstance(minimum, int) and len(value) < minimum:
        _issue(issues, "SCHEMA_MIN_LENGTH", artifact, record_id, field)
    if isinstance(maximum, int) and len(value) > maximum:
        _issue(issues, "SCHEMA_MAX_LENGTH", artifact, record_id, field)
    pattern = schema.get("pattern")
    if isinstance(pattern, str) and re.search(pattern, value) is None:
        _issue(issues, "SCHEMA_PATTERN", artifact, record_id, field)
    format_name = schema.get("format")
    if format_name == "date" and not _is_iso_date(value):
        _issue(issues, "SCHEMA_DATE", artifact, record_id, field)
    elif format_name == "date-time" and not _is_iso_datetime(value):
        _issue(issues, "SCHEMA_DATETIME", artifact, record_id, field)
    elif format_name in {"https-url", "uri"} and not _is_https_url(value):
        _issue(issues, "SCHEMA_HTTPS_URL", artifact, record_id, field)


def _matches_type(value: object, allowed_types: object) -> bool:
    names = [allowed_types] if isinstance(allowed_types, str) else allowed_types
    if not isinstance(names, list):
        return False
    checks = {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "boolean": lambda: isinstance(value, bool),
        "null": lambda: value is None,
    }
    return any(isinstance(name, str) and name in checks and checks[name]() for name in names)


def _is_iso_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _is_iso_datetime(value: str) -> bool:
    if "T" not in value:
        return False
    try:
        normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _record_id(value: object, previous: str | None) -> str | None:
    if not isinstance(value, dict):
        return previous
    for key in ("id", "public_id", "record_id", "office_public_id"):
        candidate = value.get(key)
        if isinstance(candidate, str):
            return candidate
    return previous


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _join(parent: str | None, child: str) -> str:
    return child if parent is None else f"{parent}.{child}"


def _issue(
    issues: list[ValidationIssue],
    code: str,
    artifact: str,
    record_id: str | None,
    field: str | None,
) -> None:
    issues.append(ValidationIssue(code, artifact, record_id, field))
