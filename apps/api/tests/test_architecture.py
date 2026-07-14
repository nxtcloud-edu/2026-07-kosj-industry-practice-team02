import ast
import tomllib
import unittest
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    API_ROOT / "src" / "sejong_ai_api" / "main.py",
    API_ROOT / "src" / "sejong_ai_api" / "api" / "health.py",
)

APPROVED_RUNTIME_DEPENDENCIES = {
    "fastapi==0.139.0",
    "httpx==0.28.1",
    "psycopg[binary,pool]==3.3.4",
    "pydantic==2.13.4",
    "uvicorn==0.51.0",
}
APPROVED_DEVELOPMENT_DEPENDENCIES = {
    "mypy==2.3.0",
    "pytest==9.1.1",
    "pytest-asyncio==1.4.0",
    "ruff==0.15.21",
}
BANNED_IMPORT_ROOTS = {
    "anthropic",
    "deepseek",
    "httpx",
    "openai",
    "psycopg",
    "requests",
    "sqlalchemy",
}
BANNED_CONSTRUCTION_CALLS = {
    "AsyncClient",
    "AsyncConnection",
    "AsyncConnectionPool",
    "Client",
    "Connection",
    "ConnectionPool",
    "connect",
    "create_engine",
    "create_pool",
    "getenv",
    "open",
    "urlopen",
}


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


class ApiArchitectureTest(unittest.TestCase):
    def test_exact_approved_dependencies_and_tool_configuration(self) -> None:
        pyproject_path = API_ROOT / "pyproject.toml"
        self.assertTrue(pyproject_path.is_file(), "apps/api/pyproject.toml must exist")

        pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        self.assertEqual(set(pyproject["project"]["dependencies"]), APPROVED_RUNTIME_DEPENDENCIES)
        self.assertEqual(
            set(pyproject["dependency-groups"]["dev"]), APPROVED_DEVELOPMENT_DEPENDENCIES
        )
        self.assertEqual(pyproject["project"]["requires-python"], ">=3.12.13,<3.13")
        self.assertIs(pyproject["tool"]["uv"]["package"], False)
        self.assertEqual(pyproject["tool"]["pytest"]["ini_options"]["pythonpath"], ["src"])
        self.assertEqual(pyproject["tool"]["mypy"]["mypy_path"], "src")

    def test_health_modules_exist_without_concrete_io_imports_or_construction(self) -> None:
        for source_path in SOURCE_FILES:
            with self.subTest(source_path=source_path.relative_to(API_ROOT)):
                self.assertTrue(source_path.is_file(), f"missing API source: {source_path}")
                tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))

                imported_roots: set[str] = set()
                call_names: set[str] = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imported_roots.update(
                            alias.name.split(".", maxsplit=1)[0] for alias in node.names
                        )
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported_roots.add(node.module.split(".", maxsplit=1)[0])
                    elif isinstance(node, ast.Call):
                        call_name = _call_name(node)
                        if call_name is not None:
                            call_names.add(call_name)

                self.assertEqual(imported_roots & BANNED_IMPORT_ROOTS, set())
                self.assertEqual(call_names & BANNED_CONSTRUCTION_CALLS, set())


if __name__ == "__main__":
    unittest.main()
