"""
The engine is a standalone module: no web framework, ORM or domain imports.
"""

import ast
from pathlib import Path

import pytest

import app.engine

ENGINE_DIR = Path(app.engine.__file__).parent
FORBIDDEN = ("fastapi", "starlette", "sqlalchemy", "pydantic", "app.domains", "app.core")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


@pytest.mark.parametrize("path", sorted(ENGINE_DIR.glob("*.py")), ids=lambda p: p.name)
def test_engine_module_has_no_forbidden_imports(path: Path):
    forbidden = {
        m for m in imported_modules(path) if any(m == f or m.startswith(f + ".") for f in FORBIDDEN)
    }
    assert not forbidden, f"{path.name} imports {sorted(forbidden)}"
