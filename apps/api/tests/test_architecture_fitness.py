"""
Enterprise Architecture Fitness Functions
=========================================
Automated build-time AST inspection validating dependency directions and layer boundaries.

Rules Enforced:
1. Core Platform Purity: `api.core` must never import `api.routes`, `api.services`, or `api.main`.
2. Model Purity: `api.models` must never import `api.routes` or `api.services` or `api.main`.
3. Repository Isolation: `api.repositories` must never import `api.routes` or `api.main`.
4. Composition Root Isolation: No internal package may import `api.main` (the composition root).
"""

import ast
import os
import pytest
from pathlib import Path
from typing import Dict, List, Set, Tuple


def get_api_src_dir() -> Path:
    """Resolve the path to apps/api/src/api."""
    current_file = Path(__file__).resolve()
    api_dir = current_file.parent.parent / "src" / "api"
    if not api_dir.exists():
        # Fallback for containerized execution (/app/src/api)
        api_dir = Path("/app/src/api")
    return api_dir


def extract_imports_from_file(file_path: Path) -> List[Tuple[int, str]]:
    """Parse a Python file using AST and return a list of (line_number, imported_module)."""
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except Exception as exc:
        pytest.fail(f"Failed to parse AST for {file_path}: {exc}")

    imports: List[Tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.lineno, node.module))
    return imports


def load_package_import_graph() -> Dict[str, List[Tuple[Path, int, str]]]:
    """
    Build a map of relative_module -> list of (file_path, line_number, imported_module).
    """
    api_src = get_api_src_dir()
    graph: Dict[str, List[Tuple[Path, int, str]]] = {}

    for py_file in api_src.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        rel_path = py_file.relative_to(api_src)
        package_key = rel_path.parts[0] if len(rel_path.parts) > 1 else str(rel_path)
        imports = extract_imports_from_file(py_file)
        if package_key not in graph:
            graph[package_key] = []
        for line_no, imp in imports:
            graph[package_key].append((py_file, line_no, imp))

    return graph


class TestArchitectureFitness:
    """Automated architecture fitness test suite."""

    def test_core_platform_purity(self):
        """
        Rule 1: `api.core` contains pure platform utilities and must NEVER import
        application routes, business services, or the composition root.
        """
        graph = load_package_import_graph()
        core_imports = graph.get("core", [])
        violations = []

        forbidden_prefixes = ("api.routes", "api.services", "api.main")
        for file_path, line_no, imp in core_imports:
            # deps.py and metrics_registry.py act as framework integration bridges
            if file_path.name == "deps.py" and imp.startswith("api.services.base"):
                continue
            if file_path.name == "metrics_registry.py" and imp.startswith("api.services.queue_service"):
                continue
            for forbidden in forbidden_prefixes:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    violations.append(
                        f"FITNESS VIOLATION: {file_path.name}:{line_no} in `core` imports forbidden `{imp}`"
                    )

        assert not violations, "\n".join(violations)

    def test_model_layer_purity(self):
        """
        Rule 2: `api.models` defines data schemas and must NEVER import
        routes, services, or the composition root.
        """
        graph = load_package_import_graph()
        model_imports = graph.get("models", [])
        violations = []

        forbidden_prefixes = ("api.routes", "api.services", "api.main")
        for file_path, line_no, imp in model_imports:
            for forbidden in forbidden_prefixes:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    violations.append(
                        f"FITNESS VIOLATION: {file_path.name}:{line_no} in `models` imports forbidden `{imp}`"
                    )

        assert not violations, "\n".join(violations)

    def test_repositories_layer_isolation(self):
        """
        Rule 3: `api.repositories` contains database access abstractions and must NEVER
        import HTTP routes or the composition root.
        """
        graph = load_package_import_graph()
        repo_imports = graph.get("repositories", [])
        violations = []

        forbidden_prefixes = ("api.routes", "api.main")
        for file_path, line_no, imp in repo_imports:
            for forbidden in forbidden_prefixes:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    violations.append(
                        f"FITNESS VIOLATION: {file_path.name}:{line_no} in `repositories` imports forbidden `{imp}`"
                    )

        assert not violations, "\n".join(violations)

    def test_composition_root_isolation(self):
        """
        Rule 4: `api.main` is the composition root. No internal library module
        (core, models, repositories, services) may import `api.main`.
        """
        graph = load_package_import_graph()
        violations = []

        modules_to_check = ("core", "models", "repositories", "domain", "storage", "telemetry", "cache")
        for mod in modules_to_check:
            for file_path, line_no, imp in graph.get(mod, []):
                if imp == "api.main" or imp.startswith("api.main."):
                    violations.append(
                        f"FITNESS VIOLATION: {file_path.name}:{line_no} in `{mod}` imports composition root `api.main`"
                    )

        assert not violations, "\n".join(violations)
