#!/usr/bin/env python3
"""
Advanced Automated Code Refactoring Tool

This tool performs intelligent code refactoring of Python classes with dependency analysis,
configuration management, documentation generation, and automated testing support.

Key Features:
- Intelligent dependency analysis and resolution
- Automated project structure generation
- Type stub generation
- Test case generation
- Documentation generation
- Comment preservation
- License management
- Import optimization

Core Components:

1. Core Data Structures:
   - DependencyInfo: Tracks class dependencies (imports, inheritance, composition, etc.)
   - ClassInfo: Stores comprehensive class information
   - CommentBlock: Represents source code comments with context

2. Analysis & Resolution:
   - DependencyResolver: Performs deep dependency analysis and cycle detection
     * Analyzes class relationships
     * Handles nested classes
     * Resolves import aliases
     * Detects circular dependencies
     * Supports async dependencies

3. Code Generation:
   - ModuleGenerator: Generates refactored module structure
     * Creates package hierarchy
     * Generates class files
     * Handles imports
     * Preserves type information
   - ProjectScaffolder: Creates project infrastructure
     * Generates setup.py, pyproject.toml
     * Creates package structure
     * Handles license files
   - TypeStubGenerator: Generates .pyi stub files
     * Preserves type hints
     * Handles complex types
     * Generates method signatures

4. Testing Support:
   - EnhancedTestGenerator: Creates comprehensive test files
     * Generates pytest fixtures
     * Creates test cases
     * Handles async tests
     * Supports mocking
     * Adds type checking

5. Documentation:
   - DocumentationGenerator: Creates project documentation
     * Generates API docs
     * Creates tutorials
     * Builds examples
     * Uses Sphinx

6. Utility Components:
   - AdvancedCommentPreserver: Preserves source comments
   - LicenseManager: Handles license files and headers

Usage:
    refactor.py <source_file> <output_dir> <config_file>

Configuration (config.yaml):
    version: "1.0"
    project_name: "MyProject"
    project_description: "Project description"
    modules:
      module_name:
        description: "Module description"
        classes: ["Class1", "Class2"]
        dependencies: ["dep1", "dep2"]
    settings:
      format_code: true
      generate_docs: true
      check_dependencies: true
      validate_structure: true

Example:
    # Refactor a source file
    python refactor.py source.py ./output config.yaml

    # Generated structure:
    output/
    ├── src/
    │   ├── module1/
    │   │   ├── __init__.py
    │   │   ├── class1.py
    │   │   └── class1.pyi
    │   └── module2/
    ├── tests/
    ├── docs/
    ├── setup.py
    └── pyproject.toml

Dependencies:
    - Python 3.7+
    - networkx
    - black
    - isort
    - jinja2
    - pyyaml
    - sphinx

Error Handling:
    The tool provides comprehensive error handling:
    - Dependency cycle detection
    - File permission checks
    - Syntax validation
    - Configuration validation
    - Automatic rollback on failure

Type Support:
    Handles complex type annotations including:
    - Generic types
    - Union types
    - Optional types
    - Nested type hints
    - Async types

Features in Detail:

1. Dependency Analysis:
   - Import analysis
   - Inheritance tracking
   - Composition detection
   - Type hint analysis
   - Async dependency detection
   - Circular dependency detection

2. Code Generation:
   - Namespace package support
   - Type stub generation
   - Test file generation
   - Documentation generation
   - License header insertion
   - Import optimization

3. Testing Support:
   - Fixture generation
   - Mock creation
   - Edge case detection
   - Async test support
   - Parametrized tests
   - Coverage tracking

4. Documentation:
   - API documentation
   - Usage examples
   - Tutorial generation
   - Type information
   - Dependency graphs

5. Error Recovery:
   - Automatic backups
   - Rollback support
   - Error logging
   - Progress tracking
   - Validation checks

Notes:
    - Requires write permission in output directory
    - Preserves original source code
    - Maintains type safety
    - Handles circular dependencies
    - Supports incremental updates

See Also:
    - Project documentation in docs/
    - Configuration examples in examples/
    - Test cases in tests/
"""

import ast
import inspect
import io
import json
import logging
import os
import re
import sys
import tokenize
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, TypeVar, Union

import astroid
import isort
import networkx as nx
import pkg_resources
import pytest
import sphinx.ext.autodoc
import toml
import yaml
from black import FileMode, format_str
from jinja2 import Environment, FileSystemLoader, Template
from sphinx.application import Sphinx
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 1. Core Data Structures
@dataclass
class DependencyInfo:
    """Information about class dependencies"""

    imports: Set[str]
    inherits_from: Set[str]
    composes: Set[str]
    uses: Set[str]
    type_hints: Set[str]


@dataclass
class ClassInfo:
    """Information about a class"""

    name: str
    code: str
    docstring: Optional[str]
    methods: List[str]
    dependencies: DependencyInfo
    source_lines: Tuple[int, int]


@dataclass
class CommentBlock:
    """Represents a block of related comments"""

    content: str
    type: str  # 'inline', 'block', 'docstring'
    context: Optional[str]  # Associated code element
    lineno: int
    indent: int


class DependencyResolver:
    """Advanced dependency resolution for Python classes"""

    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.resolved_order = []
        self.analyzed_classes: Dict[str, ClassInfo] = {}
        self.import_aliases: Dict[str, str] = {}
        self.nested_classes: Dict[str, List[ClassInfo]] = {}
        self.async_dependencies: Set[str] = set()
        self.relative_imports: Dict[str, str] = {}
        self.function_deps: Dict[str, Set[str]] = defaultdict(set)
        self.complex_type_hints: Set[str] = set()
        self.current_class: Optional[str] = None  # Add this line

    def analyze_class(self, node: ast.ClassDef, source: str) -> ClassInfo:
        """Analyze a class node for dependencies and structure"""
        self.current_class = node.name

        dependencies = DependencyInfo(
            imports=set(),
            inherits_from=set(),
            composes=set(),
            uses=set(),
            type_hints=set(),
        )

        # Add Pydantic imports
        dependencies.imports.add("from pydantic import BaseModel")
        dependencies.imports.add("from dataclasses import dataclass")

        # Handle decorators including Pydantic
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                dependencies.uses.add(decorator.id)
                if decorator.id in ("dataclass", "BaseModel"):
                    dependencies.imports.add("from pydantic import BaseModel")
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    dependencies.uses.add(decorator.func.id)

        # Analyze class body for field definitions
        for child in ast.walk(node):
            if isinstance(
                child, ast.AnnAssign
            ):  # Handle annotated assignments (fields)
                if isinstance(child.annotation, ast.Name):
                    dependencies.type_hints.add(child.annotation.id)
                elif isinstance(child.annotation, ast.Subscript):
                    # Handle complex types like List[str], Optional[int], etc.
                    self._analyze_type_hint(child.annotation, dependencies)

        # Analyze imports and their aliases
        for child in ast.walk(node):
            if isinstance(child, ast.Import):
                for name in child.names:
                    if name.asname:
                        self.import_aliases[name.asname] = name.name
                    dependencies.imports.add(name.name)
            elif isinstance(child, ast.ImportFrom):
                module = child.module or ""
                for name in child.names:
                    full_name = f"{module}.{name.name}" if module else name.name
                    if name.asname:
                        self.import_aliases[name.asname] = full_name
                    if child.level > 0:  # Relative import
                        self.relative_imports[full_name] = f"{'.'*child.level}{module}"
                    dependencies.imports.add(full_name)

        # Analyze inheritance including multiple inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = self.import_aliases.get(base.id, base.id)
                dependencies.inherits_from.add(base_name)
            elif isinstance(base, ast.Attribute):
                base_name = f"{base.value.id}.{base.attr}"
                dependencies.inherits_from.add(base_name)

        # Find type hints with enhanced support including complex types
        for child in ast.walk(node):
            if isinstance(child, (ast.AnnAssign, ast.arg)) and child.annotation:
                self._analyze_type_hint(
                    child.annotation, dependencies, include_complex=True
                )

        # Analyze nested classes
        nested_classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
        if nested_classes:
            self.nested_classes[node.name] = [
                self.analyze_class(nc, source) for nc in nested_classes
            ]

        # Analyze function/method dependencies including async
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if isinstance(child, ast.AsyncFunctionDef):
                    self.async_dependencies.add(node.name)

                # Analyze function body for dependencies
                method_deps = self._analyze_function_deps(child)
                self.function_deps[f"{node.name}.{child.name}"] = method_deps
                dependencies.uses.update(method_deps)

                # Check for async/await usage
                for grandchild in ast.walk(child):
                    if isinstance(grandchild, ast.Await):
                        self.async_dependencies.add(node.name)
                        if isinstance(grandchild.value, ast.Call):
                            self._analyze_call(grandchild.value, dependencies)

        # Get methods including async methods
        methods = [
            method.name
            for method in node.body
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        # Get source lines
        start_line = node.lineno if hasattr(node, "lineno") else 0
        end_line = node.end_lineno if hasattr(node, "end_lineno") else 0
        source_lines = (start_line, end_line)

        try:
            return ClassInfo(
                name=node.name,
                code=ast.unparse(node),
                docstring=ast.get_docstring(node),
                methods=methods,
                dependencies=dependencies,
                source_lines=source_lines,
            )
        finally:
            # Reset current class after analysis
            self.current_class = None

    def _analyze_type_hint(
        self, node: ast.AST, deps: DependencyInfo, include_complex: bool = False
    ):
        """Enhanced type hint analysis including Union, Generic etc"""
        if isinstance(node, ast.Name):
            deps.type_hints.add(node.id)
            if include_complex and node.id in ("Union", "Generic", "TypeVar"):
                self.complex_type_hints.add(node.id)
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                deps.type_hints.add(node.value.id)
                if include_complex:
                    self.complex_type_hints.add(node.value.id)
            if isinstance(node.slice, ast.Name):
                deps.type_hints.add(node.slice.id)
            elif isinstance(node.slice, (ast.Tuple, ast.List)):
                for elt in node.slice.elts:
                    if isinstance(elt, ast.Name):
                        deps.type_hints.add(elt.id)
                        if include_complex:
                            self.complex_type_hints.add(elt.id)

    def _analyze_function_deps(self, node: ast.AST) -> Set[str]:
        """Analyze function dependencies"""
        deps = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                self._get_call_target(child, deps)
            elif isinstance(child, ast.Name):
                deps.add(child.id)
        return deps

    def _analyze_call(self, node: ast.Call, deps: DependencyInfo):
        """Enhanced call analysis"""
        if isinstance(node.func, ast.Name):
            deps.uses.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                real_name = self.import_aliases.get(
                    node.func.value.id, node.func.value.id
                )
                deps.uses.add(real_name)
            # Add async context check
            if node.func.attr in {"create_task", "gather", "wait_for"}:
                self.async_dependencies.add(self.current_class)

    def _get_call_target(self, node: ast.Call, deps: Set[str]):
        """Extract dependency target from call"""
        if isinstance(node.func, ast.Name):
            deps.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                deps.add(node.func.value.id)

    def build_dependency_graph(self, source_code: str):
        """Build a dependency graph from source code"""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.error(f"Failed to parse source code: {e}")
            raise

        # Debug logging
        logger.info("Starting dependency analysis")

        # First pass: collect all class information
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for both regular dataclass and pydantic dataclass
                is_dataclass = any(
                    decorator.id in ("dataclass", "BaseModel")
                    for decorator in node.decorator_list
                    if isinstance(decorator, ast.Name)
                )
                logger.debug(f"Found class: {node.name} (dataclass: {is_dataclass})")
                class_info = self.analyze_class(node, source_code)
                self.analyzed_classes[node.name] = class_info
                self.dependency_graph.add_node(node.name)

        logger.info(f"Analyzed classes: {list(self.analyzed_classes.keys())}")

        # Second pass: add dependencies with enhanced resolution
        for class_name, info in self.analyzed_classes.items():
            deps = info.dependencies
            all_deps = (
                deps.inherits_from
                | deps.composes
                | deps.uses
                | {self.import_aliases.get(d, d) for d in deps.uses}
            )

            for dep in all_deps:
                if dep in self.analyzed_classes:
                    self.dependency_graph.add_edge(class_name, dep)
                    # Add edges for nested classes
                    if dep in self.nested_classes:
                        for nested in self.nested_classes[dep]:
                            self.dependency_graph.add_edge(class_name, nested.name)

        # Detect and handle cycles with enhanced reporting
        try:
            self.resolved_order = list(nx.topological_sort(self.dependency_graph))
        except nx.NetworkXUnfeasible:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            detailed_cycles = [
                {"components": cycle, "type": self._determine_cycle_type(cycle)}
                for cycle in cycles
            ]
            logger.error(f"Circular dependencies detected: {detailed_cycles}")
            raise ValueError(
                f"Circular dependencies must be resolved: {detailed_cycles}"
            )

    def _determine_cycle_type(self, cycle: List[str]) -> str:
        """Determine the type of dependency cycle"""
        if all(c in self.async_dependencies for c in cycle):
            return "async_cycle"
        elif any(c in self.nested_classes for c in cycle):
            return "nested_class_cycle"
        return "standard_cycle"


class ModuleGenerator:
    """Generates refactored module structure with error handling & caching"""

    TEMPLATE_VERSIONS = {"module": 1, "init": 1, "class_file": 1, "test": 1}
    TEMPLATE_KEYS = {
        "module": "module_v1",
        "init": "init_v1",
        "class_file": "class_file_v1",
        "test": "test_v1",
    }

    TYPE_VALIDATORS = {
        "module_name": str,
        "module_description": str,
        "classes": list,
        "imports": list,
        "class_defs": list,
        "version": str,
        "package_name": str,
        "package_description": str,
        "class_name": str,
        "class_docstring": str,
        "methods": list,
        "bases": list,
        "fixture_name": str,
    }

    def __init__(self, output_dir: Path, config: dict):
        """Initialize the module generator with configuration and setup caching"""
        self.output_dir = Path(output_dir)
        self.config = config
        self.current_module = None

        # Setup caching
        self.cache_dir = Path.home() / ".cache" / "refactor"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.template_cache = {}
        self.file_cache = {}

        # Setup templates
        self.templates = self._setup_templates()
        self._validate_templates()

        # Load cached data
        self._load_cache()

    def _setup_templates(self) -> Dict[str, Template]:
        """Setup and version all templates"""
        templates = {}
        for name, version in self.TEMPLATE_VERSIONS.items():
            template_content = getattr(self, f"_get_{name}_template")()
            template_key = f"{name}_v{version}"
            templates[template_key] = Template(
                template_content,
                keep_trailing_newline=True,
                trim_blocks=True,
                lstrip_blocks=True,
            )
        return templates

    def _validate_templates(self) -> None:
        """Validate all templates with dummy data"""
        dummy_context = {
            "module_name": "test",
            "module_description": "test",
            "classes": [],
            "imports": [],
            "class_defs": [],
            "package_name": "test",
            "package_description": "test",
            "version": "0.1.0",
            "class_name": "Test",
            "class_docstring": "Test class",
            "methods": [],
            "bases": [],
            "fixture_name": "test_fixture",
        }

        try:
            for name, template in self.templates.items():
                template.render(**dummy_context)
        except Exception as e:
            raise ValueError(f"Invalid template {name}: {e}")

    def _load_cache(self) -> None:
        """Load cached templates and files"""
        try:
            cache_file = self.cache_dir / "module_generator.json"
            if cache_file.exists():
                cache_data = json.loads(cache_file.read_text())
                self.template_cache = cache_data.get("templates", {})
                self.file_cache = cache_data.get("files", {})
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            self.template_cache = {}
            self.file_cache = {}

    def _save_cache(self) -> None:
        """Save current cache state"""
        try:
            cache_file = self.cache_dir / "module_generator.json"
            cache_data = {
                "templates": {
                    k: v
                    for k, v in self.template_cache.items()
                    if isinstance(k, str)  # Ensure key is string
                },
                "files": self.file_cache,
            }
            cache_file.write_text(json.dumps(cache_data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _validate_context(self, template_name: str, context: dict) -> None:
        """Validate template context structure and types"""
        required_fields = {
            "module": {"module_name", "module_description", "classes", "imports"},
            "init": {
                "package_name",
                "package_description",
                "version",
                "imports",
            },
            "class_file": {
                "class_name",
                "class_docstring",  # This is the main docstring
                "imports",
                "methods",
                "is_exception",  # Add this field
                "base_class",
            },
            "test": {"class_name", "fixture_name", "imports", "methods"},
        }

        if template_name not in required_fields:
            raise ValueError(f"Unknown template: {template_name}")

        # Check required fields
        missing = required_fields[template_name] - set(context.keys())
        if missing:
            raise ValueError(f"Missing required context for {template_name}: {missing}")

        # Validate types
        for key, value in context.items():
            if key in self.TYPE_VALIDATORS:
                expected_type = self.TYPE_VALIDATORS[key]
                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"Context key '{key}' must be of type {expected_type}"
                    )

    def _safe_write(self, path: Path, content: str) -> None:
        """Safely write content to file with backup and verification"""

        def get_checksum(content: str) -> str:
            import hashlib

            return hashlib.md5(content.encode()).hexdigest()

        self._validate_file_path(path)
        original_checksum = get_checksum(content)
        backup_path = None

        try:
            if path.exists():
                backup_path = path.with_suffix(".bak")
                path.rename(backup_path)

            path.write_text(content)

            # Verify written content
            written_content = path.read_text()
            if get_checksum(written_content) != original_checksum:
                raise RuntimeError(f"Content verification failed for {path}")

            if backup_path and backup_path.exists():
                backup_path.unlink()

        except Exception as e:
            if backup_path and backup_path.exists():
                backup_path.rename(path)
            raise RuntimeError(f"Failed to write file {path}: {e}")

    def _validate_file_path(self, path: Path) -> None:
        """Validate file path is safe to write to"""
        if not path.parent.exists():
            raise ValueError(f"Parent directory does not exist: {path.parent}")
        if path.exists() and not os.access(path, os.W_OK):
            raise PermissionError(f"No write permission for {path}")

    def _create_cache_key(self, template_name: str, context: dict) -> str:
        """Create a hashable cache key from template name and context"""

        # Convert lists to tuples and create a stable representation
        def make_hashable(obj):
            if isinstance(obj, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
            elif isinstance(obj, list):
                return tuple(make_hashable(x) for x in obj)
            elif isinstance(obj, set):
                return tuple(sorted(make_hashable(x) for x in obj))
            return obj

        # Create a stable representation of the context
        hashable_context = make_hashable(context)

        # Use string representation for hashing
        return f"{template_name}:{hash(str(hashable_context))}"

    def render_template(self, template_name: str, context: dict) -> str:
        """Render a template with error handling and caching"""
        try:
            # Debug logging
            logger.debug(f"Rendering template: {template_name}")
            logger.debug(f"Available templates: {list(self.templates.keys())}")

            # Get versioned template name
            if template_name not in self.TEMPLATE_KEYS:
                raise ValueError(f"Unknown template: {template_name}")

            versioned_name = self.TEMPLATE_KEYS[template_name]
            logger.debug(f"Using versioned template: {versioned_name}")

            # Validate inputs
            if versioned_name not in self.templates:
                raise ValueError(f"Template not found: {versioned_name}")

            self._validate_context(template_name, context)

            # Create a cache key using our helper method
            cache_key = self._create_cache_key(template_name, context)

            # Check cache
            if cache_key in self.template_cache:
                return self.template_cache[cache_key]

            # Render template
            template = self.templates[versioned_name]
            result = template.render(**context)

            # Cache result
            self.template_cache[cache_key] = result
            self._save_cache()

            return result
        except Exception as e:
            logger.error(f"Failed to render {template_name} template: {e}")
            logger.debug(f"Template context: {context}")
            raise

    def generate_module(self, module_name: str, classes: List[ClassInfo]) -> List[Path]:
        """Generate a module with all associated files"""
        logger.info(f"Generating module {module_name}")
        module_path = self.output_dir / module_name
        module_path.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Set current module for import path calculation
        self.current_module = module_name

        # Calculate total steps
        total_steps = len(classes) * 3 + 2  # 3 files per class + init + package
        current_step = 0

        def update_progress(message: str):
            nonlocal current_step
            current_step += 1
            logger.info(f"[{current_step}/{total_steps}] {message}")

        try:
            # Generate package files
            update_progress("Generating package files")
            init_file = self._generate_init_file(module_path, classes)
            generated_files.append(init_file)

            # Process each class
            for class_info in classes:
                update_progress(f"Processing class {class_info.name}")
                class_files = self._generate_class_files(module_path, class_info)
                generated_files.extend(class_files)

            # Save cache after successful generation
            self._save_cache()
            return generated_files

        except Exception as e:
            logger.error(f"Failed to generate module {module_name}: {e}")
            # Clean up generated files
            for file in generated_files:
                try:
                    if file.exists():
                        file.unlink()
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up {file}: {cleanup_error}")
            raise
        finally:
            self.cleanup()

    def _get_module_template(self) -> str:
        """Get template for module files"""
        return '''"""
{{ module_description }}
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
{% for import_stmt in imports %}
{{ import_stmt }}
{% endfor %}

{% for class_def in class_defs %}
{{ class_def }}
{% endfor %}
'''

    def _get_init_template(self) -> str:
        """Get template for __init__.py files"""
        return '''"""
{{ package_description }}
"""

__version__ = "{{ version }}"

{% for import_stmt in imports %}
{{ import_stmt }}
{% endfor %}

__all__ = [
    {% if classes %}
    {% for class_name in classes %}
    "{{ class_name }}",
    {% endfor %}
    {% endif %}
]
'''

    def _get_class_file_template(self) -> str:
        """Get template for individual class files"""
        return '''"""
{{ class_docstring }}
"""

{% if not is_exception %}
from typing import Any, Dict, List, Optional, Set, Tuple, Union
{% if is_pydantic %}
from pydantic import BaseModel
from dataclasses import dataclass
{% endif %}
{% for import_stmt in imports %}
{{ import_stmt }}
{% endfor %}
{% endif %}

class {{ class_name }}({{ base_class }}):
    """{{ class_docstring }}"""
    {% if is_exception %}
    pass
    {% else %}
    {% for field in fields %}
    {{ field.name }}: {{ field.type }}{% if field.default %} = {{ field.default }}{% endif %}
    {% endfor %}

    {% for method in methods %}
    {{ method }}
    {% endfor %}
    {% endif %}
'''

    def _get_test_template(self) -> str:
        """Get template for test files"""
        return '''"""
Tests for {{ class_name }}
"""

import pytest
from typing import Any, Dict, List, Optional, Set, Tuple, Union
{% for import_stmt in imports %}
{{ import_stmt }}
{% endfor %}

@pytest.fixture
def {{ fixture_name }}():
    """Fixture for testing {{ class_name }}"""
    return {{ class_name }}()

class Test{{ class_name }}:
    """Test cases for {{ class_name }}"""

    {% for method in methods %}
    def test_{{ method }}(self, {{ fixture_name }}):
        """Test {{ method }} method"""
        # TODO: Implement test
        pass

    {% endfor %}
'''

    def _create_template_context(self, template_type: str, **kwargs) -> Dict[str, Any]:
        """Create context dictionary for template rendering with validation"""
        context = {}

        # Define required fields for each template type
        required_fields = {
            "module": {"module_name", "module_description", "imports", "class_defs"},
            "init": {
                "package_name",
                "package_description",
                "version",
                "imports",  # Remove 'classes' from required fields
            },
            "class_file": {
                "class_name",
                "class_docstring",
                "imports",
                "methods",
                "bases",
            },
            "test": {"class_name", "fixture_name", "imports", "methods"},
        }

        # Validate template type
        if template_type not in required_fields:
            raise ValueError(f"Invalid template type: {template_type}")

        # Check for required fields
        missing = required_fields[template_type] - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required fields for {template_type}: {missing}")

        # Copy validated fields to context
        for key, value in kwargs.items():
            if (
                key in required_fields[template_type] or key == "classes"
            ):  # Allow optional 'classes'
                context[key] = value

        return context

    def _is_pydantic_class(self, class_info: ClassInfo) -> bool:
        """Check if class is a Pydantic model"""
        try:
            tree = ast.parse(class_info.code)
            if isinstance(tree.body[0], ast.ClassDef):
                return any(
                    decorator.id in ("dataclass", "BaseModel")
                    for decorator in tree.body[0].decorator_list
                    if isinstance(decorator, ast.Name)
                )
        except Exception:
            return False
        return False

    def _generate_imports(self, class_info: "ClassInfo") -> List[str]:
        """Generate import statements for a class"""
        imports = set()

        # Add typing imports if needed
        imports.add("from typing import Any, Dict, List, Optional, Set, Tuple, Union")

        # if self._is_pydantic_class(class_info):
        #     imports.add("from pydantic import BaseModel")
        #     imports.add("from dataclasses import dataclass")

        # Process inherited class imports
        for base in class_info.dependencies.inherits_from:
            if "." in base:
                module, name = base.rsplit(".", 1)
                imports.add(f"from {module} import {name}")

        # Process dependencies
        for imp in class_info.dependencies.imports:
            if "." in imp:
                module, name = imp.rsplit(".", 1)
                imports.add(f"from {module} import {name}")
            else:
                imports.add(f"import {imp}")

        # Clean and sort imports
        return self._clean_imports(list(imports))

    def _get_base_classes(self, class_info: "ClassInfo") -> List[str]:
        """Get list of base classes"""
        return sorted(list(class_info.dependencies.inherits_from))

    def _get_test_imports(self, class_info: "ClassInfo") -> List[str]:
        """Generate imports for test files"""
        imports = {
            "import pytest",
            "from unittest.mock import Mock, patch",
            f"from {self.config['project_name']}.{self.current_module} import {class_info.name}",
        }

        # Add typing imports if needed
        if class_info.dependencies.type_hints:
            imports.add(
                "from typing import Any, Dict, List, Optional, Set, Tuple, Union"
            )

        # Add additional imports for testing
        for imp in class_info.dependencies.imports:
            imports.add(f"import {imp}")

        return sorted(list(imports))

    def _get_test_methods(self, class_info: "ClassInfo") -> List[str]:
        """Generate test method signatures"""
        test_methods = []
        for method in class_info.methods:
            # Skip private methods
            if not method.startswith("_"):
                test_methods.append(f"test_{method}")
        return test_methods

    def _extract_fields(self, class_info: ClassInfo) -> List[Dict[str, Any]]:
        """Extract fields from a Pydantic dataclass"""
        fields = []
        tree = ast.parse(class_info.code)
        class_node = tree.body[0]  # Assuming the class is at the top level

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign):
                field = {
                    "name": node.target.id,
                    "type": ast.unparse(node.annotation),
                    "default": ast.unparse(node.value) if node.value else None,
                }
                fields.append(field)

        return fields

    def _validate_python_syntax(self, content: str) -> bool:
        """Validate Python syntax of generated code"""
        try:
            ast.parse(content)
            return True
        except SyntaxError as e:
            logger.error(f"Invalid Python syntax: {e}")
            return False

    def _clean_imports(self, imports: List[str]) -> List[str]:
        """Clean and deduplicate import statements"""
        cleaned_imports = set()
        for imp in imports:
            # Remove duplicate 'import' words
            imp = re.sub(r"import\s+import", "import", imp)
            # Remove empty imports
            if imp.strip() and not imp.strip().endswith("import"):
                cleaned_imports.add(imp.strip())
        return sorted(list(cleaned_imports))

    def _generate_class_files(self, module_path: Path, class_info: ClassInfo) -> List[Path]:
        """Generate all files for a class"""
        generated_files = []

        try:
            # Determine if it's an Exception class
            is_exception = 'Exception' in class_info.name

            # Determine if it's a Pydantic class (only if not an exception)
            is_pydantic = False if is_exception else self._is_pydantic_class(class_info)

            # Set base class
            base_class = 'Exception' if is_exception else ('BaseModel' if is_pydantic else 'object')

            # Only include imports for non-exception classes
            imports = []
            if not is_exception:
                imports = self._clean_imports(self._generate_imports(class_info))

            class_context = {
                "class_name": class_info.name,
                "class_docstring": class_info.docstring or f"The {class_info.name} class",
                "imports": imports,
                "base_class": base_class,
                "is_pydantic": is_pydantic,
                "is_exception": is_exception,
                "fields": [] if is_exception else self._extract_fields(class_info),
                "methods": [] if is_exception else class_info.methods,
            }

            class_file = module_path / f"{class_info.name.lower()}.py"
            class_content = self.render_template("class_file", class_context)

            # Validate syntax before writing
            if not self._validate_python_syntax(class_content):
                logger.error(f"Generated invalid code for {class_info.name}:")
                logger.error(class_content)
                raise ValueError(f"Generated code for {class_info.name} has invalid syntax")

            self._safe_write(class_file, class_content)
            generated_files.append(class_file)

            # Generate type stub (if not an exception)
            if not is_exception:
                stub_file = module_path / f"{class_info.name.lower()}.pyi"
                stub_gen = TypeStubGenerator(class_info)
                stub_content = stub_gen.generate_stub()

                if not self._validate_python_syntax(stub_content):
                    raise ValueError(f"Generated stub for {class_info.name} has invalid syntax")

                self._safe_write(stub_file, stub_content)
                generated_files.append(stub_file)

            # Generate tests
            test_context = self._create_template_context(
                "test",
                class_name=class_info.name,
                fixture_name=class_info.name.lower(),
                imports=self._get_test_imports(class_info),
                methods=[] if is_exception else self._get_test_methods(class_info),
            )

            test_path = self.output_dir / "tests" / module_path.name
            test_path.mkdir(parents=True, exist_ok=True)
            test_file = test_path / f"test_{class_info.name.lower()}.py"
            test_content = self.render_template("test", test_context)

            if not self._validate_python_syntax(test_content):
                raise ValueError(f"Generated test for {class_info.name} has invalid syntax")

            self._safe_write(test_file, test_content)
            generated_files.append(test_file)

            return generated_files

        except Exception as e:
            logger.error(f"Failed to generate files for {class_info.name}: {e}")
            # Clean up any generated files on failure
            for file in generated_files:
                try:
                    if file.exists():
                        file.unlink()
                except Exception:
                    pass
            raise


    def _generate_init_file(self, module_path: Path, classes: List[ClassInfo]) -> Path:
        """Generate module __init__.py"""
        # Get module description from config, with fallback
        module_description = (
            self.config.get("modules", {})
            .get(module_path.name, {})
            .get("description", "Module description")
        )

        # Create class names list for export
        class_names = [c.name for c in classes] if classes else []

        context = {
            "package_name": module_path.name,
            "package_description": module_description,
            "version": self.config.get("version", "0.1.0"),
            "imports": [f"from .{c.name.lower()} import {c.name}" for c in classes],
            "classes": class_names,  # Add class names for __all__
        }

        init_file = module_path / "__init__.py"
        try:
            init_content = self.render_template("init", context)
            self._safe_write(init_file, init_content)

            # Generate py.typed marker for type stubs
            typed_file = module_path / "py.typed"
            typed_file.touch()

            return init_file
        except Exception as e:
            logger.error(f"Failed to generate init file: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up temporary files and caches"""
        try:
            # Clear caches
            self.template_cache.clear()
            self.file_cache.clear()

            # Remove backup files
            for backup_file in self.output_dir.rglob("*.bak"):
                try:
                    backup_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove backup file {backup_file}: {e}")

        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


class ProjectScaffolder:
    """Handles generation of project infrastructure files"""

    def __init__(self, config: dict, output_dir: Path):
        self.config = config
        self.output_dir = Path(output_dir)
        self.templates_dir = Path(__file__).parent / "templates"

    def generate_project_files(self):
        """Generate all project infrastructure files and directories"""
        # Create main project structure
        self._create_directory_structure()

        # Generate project files
        self.generate_setup_py()
        self.generate_pyproject_toml()
        self.generate_init_files()
        self.generate_license_headers()
        self.generate_readme()
        self.generate_manifest()

    def _create_directory_structure(self):
        """Create the complete project directory structure"""
        try:
            # Create main output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Create standard project directories
            directories = [
                self.output_dir / "src",
                self.output_dir / "tests",
                self.output_dir / "docs",
                self.output_dir / "examples",
                self.output_dir / ".github" / "workflows",  # For GitHub Actions
            ]

            # Create module directories from config
            package_dir = self.output_dir / "src" / self.config["project_name"].lower()
            directories.append(package_dir)

            # Add module subdirectories
            for module_name in self.config["modules"]:
                directories.append(package_dir / module_name)
                directories.append(self.output_dir / "tests" / module_name)

            # Create all directories
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)

            # Set proper permissions (rwxr-xr-x)
            for directory in directories:
                directory.chmod(0o755)

            logger.info(f"Created project directory structure in {self.output_dir}")

        except Exception as e:
            logger.error(f"Failed to create directory structure: {e}")
            raise RuntimeError(f"Directory structure creation failed: {e}")

    def generate_pyproject_toml(self):
        """Generate pyproject.toml with build system and tool configs"""
        pyproject_config = {
            "build-system": {
                "requires": ["setuptools>=45", "wheel"],
                "build-backend": "setuptools.build_meta",
            },
            "tool": {
                "black": {"line-length": 88},
                "isort": {"profile": "black"},
                "mypy": {"ignore_missing_imports": True},
            },
            "project": {
                "name": self.config["project_name"],
                "version": self.config.get("version", "0.1.0"),
                "description": self.config.get("project_description", ""),
                "requires-python": f">={self.config.get('python_version', '3.7')}",
            },
        }
        (self.output_dir / "pyproject.toml").write_text(toml.dumps(pyproject_config))

    def generate_manifest(self):
        """Generate MANIFEST.in file"""
        manifest_template = """include LICENSE
include README.md
include pyproject.toml

recursive-include {package_name} *.py
recursive-include {package_name} py.typed
recursive-include tests *.py
"""
        content = manifest_template.format(
            package_name=self.config["project_name"].lower()
        )
        (self.output_dir / "MANIFEST.in").write_text(content)

    def generate_license_headers(self):
        """Generate license headers for source files"""
        license_template = """# Copyright (c) {year} {author}. All rights reserved.
# Licensed under the {license} license. See LICENSE file for details.
        """
        header = license_template.format(
            year=datetime.now().year,
            author=self.config.get("author", ""),
            license=self.config.get("license", "MIT"),
        )

        license_file = self.output_dir / "LICENSE"
        license_file.write_text(header)

    def generate_setup_py(self):
        """Generate setup.py with project metadata"""
        setup_template = """
        from setuptools import setup, find_namespace_packages

        setup(
            name="{{ project_name }}",
            version="{{ version }}",
            description="{{ description }}",
            author="{{ author }}",
            packages=find_namespace_packages(include=["{{ package_name }}.*"]),
            package_dir={"": "src"},
            install_requires=[
                {% for dep in dependencies %}
                "{{ dep }}",
                {% endfor %}
            ],
            python_requires=">={{ python_version }}",
            extras_require={
                "dev": [
                    "pytest",
                    "pytest-cov",
                    "black",
                    "isort",
                    "mypy",
                    "sphinx",
                ]
            },
        )
        """
        content = Template(setup_template).render(
            project_name=self.config["project_name"],
            version=self.config.get("version", "0.1.0"),
            description=self.config.get("project_description", ""),
            author=self.config.get("author", ""),
            package_name=self.config["project_name"].lower(),
            dependencies=self.config.get("dependencies", []),
            python_version=self.config.get("python_version", "3.7"),
        )
        setup_file = self.output_dir / "setup.py"
        setup_file.write_text(dedent(content))
        setup_file.chmod(0o644)  # Set proper file permissions (rw-r--r--)

    def generate_init_files(self):
        """Generate __init__.py files for all packages"""
        # Main package init
        src_dir = self.output_dir / "src"
        package_dir = src_dir / self.config["project_name"].lower()
        package_dir.mkdir(parents=True, exist_ok=True)

        main_init = package_dir / "__init__.py"
        main_init.write_text(
            f'''"""
{self.config["project_description"]}
"""

__version__ = "{self.config.get("version", "0.1.0")}"
'''
        )

        # Module inits
        for module in self.config["modules"]:
            module_dir = package_dir / module
            module_dir.mkdir(parents=True, exist_ok=True)

            module_init = module_dir / "__init__.py"
            module_init.write_text(
                f'''"""
{self.config["modules"][module].get("description", "")}
"""
'''
            )

            # Create py.typed marker for type checking
            (module_dir / "py.typed").touch()

        # Initialize test directories with __init__.py
        test_dir = self.output_dir / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "__init__.py").touch()

        for module in self.config["modules"]:
            module_test_dir = test_dir / module
            module_test_dir.mkdir(parents=True, exist_ok=True)
            (module_test_dir / "__init__.py").touch()

        # Set proper permissions for all files
        for init_file in self.output_dir.rglob("__init__.py"):
            init_file.chmod(0o644)

    def _create_github_workflows(self):
        """Create GitHub Actions workflow files"""
        workflow_dir = self.output_dir / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # CI workflow
        ci_workflow = """
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    - name: Run tests
      run: |
        pytest --cov
    - name: Type checking
      run: |
        mypy src/
    - name: Code formatting
      run: |
        black --check src/
        isort --check src/
        """

        (workflow_dir / "ci.yml").write_text(dedent(ci_workflow))

    def generate_readme(self):
        """Generate project README.md"""
        readme_template = Template(
            """# {{ project_name }}

    {{ description }}

    ## Installation

    ```bash
    pip install {{ package_name }}
    ```

    ## Development Setup

    1. Clone the repository:
       ```bash
       git clone https://github.com/username/{{ package_name }}.git
       cd {{ package_name }}
       ```

    2. Create and activate a virtual environment:
       ```bash
       python -m venv venv
       source venv/bin/activate  # On Windows: venv\\Scripts\\activate
       ```

    3. Install development dependencies:
       ```bash
       pip install -e ".[dev]"
       ```

    ## Testing

    Run the test suite:
    ```bash
    pytest
    ```

    With coverage:
    ```bash
    pytest --cov
    ```

    ## Type Checking

    ```bash
    mypy src/
    ```

    ## Code Formatting

    ```bash
    black src/
    isort src/
    ```

    ## Documentation

    Build the documentation:
    ```bash
    cd docs
    make html
    ```

    ## License

    {{ license }} © {{ author }}
    """
        )

        # Create Template object and render
        content = readme_template.render(
            project_name=self.config["project_name"],
            description=self.config.get("project_description", ""),
            package_name=self.config["project_name"].lower(),
            license=self.config.get("license", "MIT"),
            author=self.config.get("author", ""),
        )

        # Write the README file
        readme_file = self.output_dir / "README.md"
        readme_file.write_text(dedent(content))
        readme_file.chmod(0o644)


class TypeStubGenerator:
    """Generates .pyi type stub files with complex type support"""

    def __init__(self, class_info: ClassInfo):
        self.class_info = class_info
        self.type_map = self._build_type_map()

    def _build_type_map(self) -> Dict[str, str]:
        """Build mapping of variables to their type hints"""
        type_map = {}

        # Analyze type annotations
        for node in ast.walk(ast.parse(self.class_info.code)):
            if isinstance(node, ast.AnnAssign):
                # Handle both simple names and attribute access
                target_name = self._get_target_name(node.target)
                if target_name:
                    type_map[target_name] = self._format_type_annotation(
                        node.annotation
                    )

        return type_map

    def _get_target_name(self, node: ast.AST) -> Optional[str]:
        """Extract the target name from an assignment target"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle attribute access (e.g., self.attribute)
            if isinstance(node.value, ast.Name):
                if node.value.id == "self":
                    return node.attr
                return f"{node.value.id}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Subscript):
            # Handle subscript targets if needed
            base = self._get_target_name(node.value)
            return (
                f"{base}[{self._format_type_annotation(node.slice)}]" if base else None
            )
        else:
            logger.warning(f"Unexpected target type: {type(node)}")
            return None

    def _format_type_annotation(self, node: ast.AST) -> str:
        """Format complex type annotations"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                # Handle basic subscript types (List[str], Dict[str, int], etc.)
                base_type = node.value.id

                # Handle the slice part differently based on its type
                if isinstance(node.slice, ast.Name):
                    # Simple case like List[str]
                    return f"{base_type}[{node.slice.id}]"
                elif isinstance(node.slice, ast.Tuple):
                    # Multiple type parameters like Dict[str, int]
                    params = [
                        self._format_type_annotation(elt) for elt in node.slice.elts
                    ]
                    return f"{base_type}[{', '.join(params)}]"
                elif isinstance(node.slice, ast.Subscript):
                    # Nested type like List[Optional[str]]
                    return f"{base_type}[{self._format_type_annotation(node.slice)}]"
                else:
                    # Handle any other slice type
                    return f"{base_type}[{self._format_type_annotation(node.slice)}]"
        elif isinstance(node, ast.Tuple):
            # Handle tuple types
            return f"Tuple[{', '.join(self._format_type_annotation(elt) for elt in node.elts)}]"
        elif isinstance(node, ast.BinOp):
            # Handle union types using |
            return f"Union[{self._format_type_annotation(node.left)}, {self._format_type_annotation(node.right)}]"
        elif isinstance(node, ast.Attribute):
            # Handle attribute access like module.type
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
            return f"{self._format_type_annotation(node.value)}.{node.attr}"
        elif isinstance(node, ast.List):
            # Handle list literals in type annotations
            return f"List[{', '.join(self._format_type_annotation(elt) for elt in node.elts)}]"
        elif isinstance(node, ast.Call):
            # Handle type constructor calls
            if isinstance(node.func, ast.Name):
                args = [self._format_type_annotation(arg) for arg in node.args]
                return f"{node.func.id}[{', '.join(args)}]"

        # Default to Any for unknown types
        logger.warning(f"Unknown type annotation node: {type(node)}")
        return "Any"

    def generate_stub(self) -> str:
        """Generate type stub content for a class"""
        # Check if class is a Pydantic dataclass
        is_pydantic = False
        try:
            tree = ast.parse(self.class_info.code)
            if isinstance(tree.body[0], ast.ClassDef):
                is_pydantic = any(
                    decorator.id in ("dataclass", "BaseModel")
                    for decorator in tree.body[0].decorator_list
                    if isinstance(decorator, ast.Name)
                )
        except Exception as e:
            logger.warning(f"Failed to check if class is Pydantic dataclass: {e}")

        # Add debug logging
        logger.debug(f"Generating stub for class: {self.class_info.name}")
        logger.debug(f"Fields: {self.type_map}")
        logger.debug(f"Is Pydantic: {is_pydantic}")

        stub_template = """
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field
from dataclasses import dataclass
{% for import_stmt in imports %}
{{ import_stmt }}
{% endfor %}

{% if is_pydantic %}
@dataclass
{% endif %}
class {{ class_name }}{% if bases %}({{ bases|join(', ') }}){% endif %}:
    '''{{ class_docstring }}'''

    {% for field_name, field_type in fields.items() %}
    {{ field_name }}: {{ field_type }}
    {% endfor %}

    {% for method in methods %}
    {{ method.signature }}: ...
    {% endfor %}
        """

        context = {
            "imports": self._get_stub_imports(),
            "class_name": self.class_info.name,
            "class_docstring": self.class_info.docstring
            or f"The {self.class_info.name} class",
            "bases": self._get_base_classes(),
            "fields": self.type_map,
            "methods": self._get_method_signatures(),
            "is_pydantic": is_pydantic,
        }

        return Template(stub_template).render(**context)

    def _get_stub_imports(self) -> List[str]:
        """Extract required imports for stub file"""
        imports = {
            "from typing import Any, Dict, List, Optional, Set, Tuple, Union",
            "from pydantic import BaseModel",
            "from dataclasses import dataclass",
        }

        # Add dependencies imports
        deps = self.class_info.dependencies
        for imp in deps.imports:
            if "." in imp:
                module, name = imp.rsplit(".", 1)
                imports.add(f"from {module} import {name}")
            else:
                imports.add(f"import {imp}")

        return sorted(list(imports))

    def _get_base_classes(self) -> List[str]:
        """Get base class names"""
        bases = list(self.class_info.dependencies.inherits_from)
        if not bases and self._is_pydantic_model():
            bases.append("BaseModel")
        return bases

    def _is_pydantic_model(self) -> bool:
        """Check if the class is a Pydantic model"""
        try:
            tree = ast.parse(self.class_info.code)
            if isinstance(tree.body[0], ast.ClassDef):
                return any(
                    decorator.id in ("dataclass", "BaseModel")
                    for decorator in tree.body[0].decorator_list
                    if isinstance(decorator, ast.Name)
                )
        except Exception:
            return False
        return False

    def _get_method_signatures(self) -> List[Dict[str, str]]:
        """Extract method signatures with type hints"""
        signatures = []

        for method in self.class_info.methods:
            # Find method node
            method_node = None
            for node in ast.walk(ast.parse(self.class_info.code)):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == method
                ):
                    method_node = node
                    break

            if method_node:
                # Get args info
                args = []
                for arg in method_node.args.args:
                    if arg.annotation:
                        arg_type = self._format_type_annotation(arg.annotation)
                    else:
                        arg_type = "Any"
                    args.append(f"{arg.arg}: {arg_type}")

                # Get return type
                if method_node.returns:
                    return_type = self._format_type_annotation(method_node.returns)
                else:
                    return_type = "Any"

                # Build signature
                is_async = isinstance(method_node, ast.AsyncFunctionDef)
                signature = f"{'async ' if is_async else ''}def {method}({', '.join(args)}) -> {return_type}"

                signatures.append(
                    {
                        "method_name": method,
                        "signature": signature,
                        "is_async": is_async,
                        "args": args,
                        "return_type": return_type,
                    }
                )

        return signatures


class LicenseManager:
    """Handles multiple license types and templates, including header generation"""

    LICENSES = {
        "MIT": """MIT License

Copyright (c) {{ year }} {{ author }}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
""",
        "Apache-2.0": """Apache License, Version 2.0

Copyright (c) {{ year }} {{ author }}

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
""",
        "GPL-3.0": """GNU GENERAL PUBLIC LICENSE Version 3

Copyright (c) {{ year }} {{ author }}

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
""",
    }

    HEADERS = {
        "py": """# Copyright (c) {{ year }} {{ author }}. All rights reserved.
# {{ license_type }}
""",
        "default": """Copyright (c) {{ year }} {{ author }}. All rights reserved.
{{ license_type }}
""",
    }

    def __init__(self, config: dict):
        self.config = config
        self.year = datetime.now().year

    def generate_license(self) -> str:
        """Generate complete license file"""
        license_type = self.config.get("license", "MIT")
        template = Template(self.LICENSES[license_type])

        content = template.render(
            year=self.year,
            author=self.config.get("author", ""),
            project=self.config.get("project_name", ""),
        )

        # Write license file
        license_file = Path(self.config.get("output_dir", ".")) / "LICENSE"
        license_file.write_text(content)

        return content

    def generate_header(self, file_type: str = "default") -> str:
        """Generate license header for source files

        Args:
            file_type: Type of file to generate header for ('py', 'default', etc)
        """
        header_template = Template(self.HEADERS.get(file_type, self.HEADERS["default"]))
        return header_template.render(
            year=self.year,
            author=self.config.get("author", ""),
            license_type=self.config.get("license", "MIT"),
        )


# 4. Documentation Generation
class DocumentationGenerator:
    """Generates comprehensive documentation"""

    CONF_TEMPLATE = """
    project = '{{ project_name }}'
    copyright = '{{ year }}, {{ author }}'
    author = '{{ author }}'

    extensions = [
        'sphinx.ext.autodoc',
        'sphinx.ext.napoleon',
        'sphinx.ext.viewcode',
        'sphinx.ext.intersphinx',
    ]

    templates_path = ['_templates']
    exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

    html_theme = 'sphinx_rtd_theme'
    """

    TUTORIAL_INDEX_TEMPLATE = """
    Tutorials
    =========

    .. toctree::
       :maxdepth: 2

       getting_started
       advanced_usage
    """

    TUTORIAL_PAGE_TEMPLATE = """
    {{ title }}
    {{ '=' * title|length }}

    This is a placeholder for the {{ title|lower }} tutorial.
    """

    EXAMPLES_INDEX_TEMPLATE = """
    Examples
    ========

    .. toctree::
       :maxdepth: 2

       basic_examples
       advanced_examples
    """

    EXAMPLE_PAGE_TEMPLATE = """
    {{ title }}
    {{ '=' * title|length }}

    This is a placeholder for {{ title|lower }}.

    .. code-block:: python

        # Example code here
        def example():
            pass
    """

    INDEX_TEMPLATE = """
    Welcome to {{ project_name }}'s documentation!
    {{ '=' * (project_name|length + 24) }}

    .. toctree::
       :maxdepth: 2
       :caption: Contents:

       api/index
       tutorials/index
       examples/index

    Indices and tables
    ==================

    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`
    """

    API_TEMPLATE = """
    {{ module_name }}
    {{ '=' * module_name|length }}

    .. automodule:: {{ project_name }}.{{ module_name }}
       :members:
       :undoc-members:
       :show-inheritance:
    """

    def __init__(self, project_dir: Path, config: dict):
        self.project_dir = project_dir
        self.config = config
        self.docs_dir = project_dir / "docs"
        self.source_dir = project_dir / "src"
        # Ensure docs directory exists
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def generate_documentation(self):
        """Generate complete documentation suite"""
        try:
            self._setup_sphinx()
            self._generate_api_docs()
            self._generate_tutorials()
            self._generate_examples()
            self._build_docs()
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            raise

    def _setup_sphinx(self):
        """Configure Sphinx documentation"""
        # Create conf.py
        conf_content = f"""
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = '{self.config["project_name"]}'
copyright = '{datetime.now().year}, {self.config.get("author", "")}'
author = '{self.config.get("author", "")}'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {{
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}}
"""
        (self.docs_dir / "conf.py").write_text(dedent(conf_content))

        # Create index.rst
        index_content = f"""
{self.config["project_name"]} Documentation
{'=' * (len(self.config["project_name"]) + 14)}

{self.config.get("project_description", "")}

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/index
   tutorials/index
   examples/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
"""
        (self.docs_dir / "index.rst").write_text(dedent(index_content))

        # Create necessary subdirectories
        (self.docs_dir / "_static").mkdir(exist_ok=True)
        (self.docs_dir / "_templates").mkdir(exist_ok=True)
        (self.docs_dir / "api").mkdir(exist_ok=True)

    def _generate_api_docs(self):
        """Generate API documentation using autodoc"""
        api_dir = self.docs_dir / "api"
        api_dir.mkdir(exist_ok=True)

        # Create api/index.rst
        api_index_content = """
API Reference
============

.. toctree::
   :maxdepth: 2

"""
        for module_name in self.config["modules"]:
            api_index_content += f"   {module_name}\n"

        (api_dir / "index.rst").write_text(dedent(api_index_content))

        # Generate module documentation
        for module_name, module_info in self.config["modules"].items():
            module_content = f"""
{module_name}
{'=' * len(module_name)}

{module_info.get('description', '')}

.. automodule:: {self.config['project_name']}.{module_name}
   :members:
   :undoc-members:
   :show-inheritance:

"""
            (api_dir / f"{module_name}.rst").write_text(dedent(module_content))

    def _generate_api_docs(self):
        """Generate API documentation using autodoc"""
        api_dir = self.docs_dir / "api"
        api_dir.mkdir(exist_ok=True)

        for module_name, module_info in self.config["modules"].items():
            content = Template(self.API_TEMPLATE).render(
                module_name=module_name, project_name=self.config["project_name"]
            )
            (api_dir / f"{module_name}.rst").write_text(dedent(content))

    def _generate_tutorials(self):
        """Generate tutorial documentation"""
        tutorial_dir = self.docs_dir / "tutorials"
        tutorial_dir.mkdir(exist_ok=True)

        (tutorial_dir / "index.rst").write_text(dedent(self.TUTORIAL_INDEX_TEMPLATE))

        tutorials = {
            "getting_started": "Getting Started Guide",
            "advanced_usage": "Advanced Usage",
        }

        for filename, title in tutorials.items():
            content = Template(self.TUTORIAL_PAGE_TEMPLATE).render(title=title)
            (tutorial_dir / f"{filename}.rst").write_text(dedent(content))

    def _generate_examples(self):
        """Generate example code documentation"""
        examples_dir = self.docs_dir / "examples"
        examples_dir.mkdir(exist_ok=True)

        (examples_dir / "index.rst").write_text(dedent(self.EXAMPLES_INDEX_TEMPLATE))

        example_files = {
            "basic_examples": "Basic Examples",
            "advanced_examples": "Advanced Examples",
        }

        for filename, title in example_files.items():
            content = Template(self.EXAMPLE_PAGE_TEMPLATE).render(title=title)
            (examples_dir / f"{filename}.rst").write_text(dedent(content))

    def _build_docs(self):
        """Build documentation using Sphinx"""
        import subprocess
        import sys

        # Ensure sphinx-build is available
        try:
            import sphinx
        except ImportError:
            logger.error("Sphinx is not installed. Installing required packages...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "sphinx", "sphinx-rtd-theme"],
                check=True,
            )

        try:
            # Create requirements.txt for Read the Docs
            requirements_content = """
sphinx>=4.0.0
sphinx-rtd-theme
"""
            (self.docs_dir / "requirements.txt").write_text(
                requirements_content.strip()
            )

            # Run sphinx-build with detailed error output
            result = subprocess.run(
                [
                    "sphinx-build",
                    "-b",
                    "html",
                    "-v",  # verbose output
                    "-W",  # treat warnings as errors
                    "-a",  # write all files
                    str(self.docs_dir),
                    str(self.docs_dir / "_build/html"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error("Sphinx build failed!")
                logger.error("STDOUT:")
                logger.error(result.stdout)
                logger.error("STDERR:")
                logger.error(result.stderr)

                # Check for common issues
                if "ImportError" in result.stderr:
                    logger.error(
                        "Import error detected. Make sure all required packages are installed."
                    )
                elif "WARNING: autodoc" in result.stderr:
                    logger.error(
                        "Autodoc warning detected. Check your docstrings and module imports."
                    )
                elif "ERROR: Unknown directive type" in result.stderr:
                    logger.error(
                        "Sphinx extension error. Check if all required extensions are installed."
                    )

                raise RuntimeError(f"Documentation build failed: {result.stderr}")

            logger.info("Documentation built successfully")

        except Exception as e:
            logger.error(f"Failed to build documentation: {e}")
            raise

    def _ensure_dependencies(self):
        """Ensure all required documentation dependencies are installed"""
        required_packages = [
            "sphinx",
            "sphinx-rtd-theme",
            "sphinx-autodoc-typehints",
            "sphinx-napoleon",
        ]

        import subprocess
        import sys

        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                logger.info(f"Installing {package}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package], check=True
                )

    def _create_make_files(self):
        """Create Makefile and make.bat for building docs"""
        # Create Makefile
        makefile_content = """
# Minimal makefile for Sphinx documentation

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
"""
        (self.docs_dir / "Makefile").write_text(dedent(makefile_content))

        # Create make.bat for Windows
        make_bat_content = """
@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=.
set BUILDDIR=_build

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.https://www.sphinx-doc.org/
	exit /b 1
)

if "%1" == "" goto help

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd
"""
        (self.docs_dir / "make.bat").write_text(dedent(make_bat_content))


# 5. Testing Support
class EnhancedTestGenerator:
    """Generates detailed test files with sophisticated templates"""

    def __init__(self, class_info: ClassInfo):
        self.class_info = class_info
        self.method_signatures = self._analyze_methods()
        self.mock_templates = self._load_mock_templates()
        self.test_config = self._load_test_config()
        self.coverage_targets = {"branch": 85, "line": 90}

    def _analyze_methods(self) -> Dict[str, Dict]:
        """Analyze method signatures for test generation with enhanced type checking"""
        signatures = {}
        tree = ast.parse(self.class_info.code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_name = node.name
                if method_name in self.class_info.methods:
                    signatures[method_name] = {
                        "args": self._get_arguments(node),
                        "returns": self._get_return_type(node),
                        "raises": self._get_exceptions(node),
                        "async": isinstance(node, ast.AsyncFunctionDef),
                        "decorators": self._get_decorators(node),
                        "complexity": self._analyze_complexity(node),
                        "dependencies": self._extract_dependencies(node),
                        "doc_tests": self._extract_doctests(node),
                        "param_constraints": self._get_parameter_constraints(node),
                        "mocks_required": self._identify_required_mocks(node),
                    }
        return signatures

    def _get_arguments(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Extract detailed argument information including type hints and defaults"""
        args = []
        for arg in node.args.args:
            arg_info = {
                "name": arg.arg,
                "type_hint": (
                    self._format_type_annotation(arg.annotation)
                    if arg.annotation
                    else None
                ),
                "default": None,
                "is_required": True,
            }
            args.append(arg_info)
        # Handle defaults
        if node.args.defaults:
            for i, default in enumerate(reversed(node.args.defaults)):
                args[-(i + 1)]["default"] = ast.unparse(default)
                args[-(i + 1)]["is_required"] = False
        return args

    def _get_return_type(self, node: ast.AST) -> Optional[str]:
        """Extract return type with support for complex type hints"""
        if node.returns:
            return self._format_type_annotation(node.returns)
        return self._infer_return_type(node)

    def _get_exceptions(self, node: ast.AST) -> List[str]:
        """Analyze raised exceptions including from called functions"""
        exceptions = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if isinstance(child.exc, ast.Name):
                    exceptions.add(child.exc.id)
                elif isinstance(child, ast.Call):
                    exceptions.add(child.func.id)
        return sorted(list(exceptions))

    def _get_decorators(self, node: ast.AST) -> List[str]:
        """Extract decorator information for test generation"""
        return [ast.unparse(dec) for dec in node.decorator_list]

    def _get_test_template(self) -> str:
        """Get template for test files"""
        return '''"""
Tests for {{ class_name }}
"""

import pytest
from pydantic import BaseModel, ValidationError
from typing import Any, Dict, List, Optional, Set, Tuple, Union
{% for import_stmt in imports %}
{{ import_stmt }}
{% endfor %}

@pytest.fixture
def {{ fixture_name }}():
    """Fixture for testing {{ class_name }}"""
    return {{ class_name }}(
        {% for field in fields %}
        {{ field.name }}={{ field.test_value }},
        {% endfor %}
    )

class Test{{ class_name }}:
    """Test cases for {{ class_name }}"""

    def test_create_valid(self):
        """Test creating a valid instance"""
        instance = {{ class_name }}(
            {% for field in fields %}
            {{ field.name }}={{ field.test_value }},
            {% endfor %}
        )
        {% for field in fields %}
        assert instance.{{ field.name }} == {{ field.test_value }}
        {% endfor %}

    def test_validation_error(self):
        """Test validation errors"""
        with pytest.raises(ValidationError):
            {{ class_name }}()  # Missing required fields

    {% for method in methods %}
    def test_{{ method }}(self, {{ fixture_name }}):
        """Test {{ method }} method"""
        # TODO: Implement test
        pass
    {% endfor %}
'''

    def _analyze_complexity(self, node: ast.AST) -> Dict[str, int]:
        """Analyze code complexity to determine test coverage needs"""
        branches = len(
            [n for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While))]
        )
        return {
            "cyclomatic": branches + 1,
            "cognitive": self._calculate_cognitive_complexity(node),
        }

    def _extract_dependencies(self, node: ast.AST) -> Set[str]:
        """Identify external dependencies for mocking"""
        deps = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                deps.add(child.id)
        return deps

    def _load_mock_templates(self) -> Dict[str, str]:
        """Load mock templates for different types of dependencies"""
        return {
            "http": "Mock(return_value=httpx.Response(200, content=b'{}'))",
            "database": "Mock(return_value=DatabaseConnection(mock=True))",
            "file": "mock_open(read_data='')",
            "default": "Mock(return_value=None)",
        }

    def _load_test_config(self) -> Dict[str, Any]:
        """Load test configuration settings"""
        return {
            "mock_external_calls": True,
            "generate_edge_cases": True,
            "min_test_cases": 3,
        }

    def _extract_doctests(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Extract doctests from method docstrings"""
        doctests = []
        docstring = ast.get_docstring(node)
        if docstring:
            # Parse doctest examples
            import doctest

            parser = doctest.DocTestParser()
            try:
                examples = parser.get_examples(docstring)
                for example in examples:
                    doctests.append(
                        {
                            "source": example.source,
                            "want": example.want,
                            "exc_msg": example.exc_msg,
                        }
                    )
            except Exception:
                pass
        return doctests

    def _get_parameter_constraints(self, node: ast.AST) -> Dict[str, Any]:
        """Extract parameter constraints from docstring"""
        constraints = {}
        docstring = ast.get_docstring(node)
        if docstring:
            # Parse param constraints from docstring
            param_lines = [
                line
                for line in docstring.split("\n")
                if ":param" in line or ":type" in line
            ]
            for line in param_lines:
                if ":param" in line:
                    param = line.split(":param")[1].split(":")[0].strip()
                    desc = line.split(":")[-1].strip()
                    constraints[param] = {"description": desc}
        return constraints

    def _identify_required_mocks(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Identify dependencies that need to be mocked"""
        mocks = []
        for dep in self._extract_dependencies(node):
            if dep not in self.class_info.methods:
                mocks.append(
                    {
                        "target": dep,
                        "template": self.mock_templates.get(
                            dep, self.mock_templates["default"]
                        ),
                    }
                )
        return mocks

    def _format_type_annotation(self, node: ast.AST) -> str:
        """Format type annotation node as string"""
        return ast.unparse(node)

    def _infer_return_type(self, node: ast.AST) -> Optional[str]:
        """Infer return type from method body"""
        return_nodes = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
        if return_nodes:
            return "Any"  # Could be enhanced with type inference
        return None

    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity metric"""
        complexity = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += 1
        return complexity

    def _get_module_path(self) -> str:
        """Get import path for the class"""
        return f"{self.class_info.name.lower()}.{self.class_info.name}"

    def _generate_fixtures(self) -> List[Dict[str, Any]]:
        """Generate pytest fixtures for test dependencies"""
        fixtures = []
        for dep in self.class_info.dependencies.uses:
            fixtures.append(
                {
                    "name": f"{dep.lower()}_fixture",
                    "setup": f"return Mock(spec={dep})",
                    "doc": f"Fixture for {dep} dependency",
                }
            )
        return fixtures

    def _get_fixture_list(self) -> List[str]:
        """Get list of fixture names needed for tests"""
        return [f["name"] for f in self._generate_fixtures()]

    def _get_required_imports(self) -> List[str]:
        """Get list of required import statements"""
        imports = ["from unittest.mock import Mock, patch", "import pytest"]
        imports.extend(self.class_info.dependencies.imports)
        return sorted(imports)

    def generate_test_file(self) -> str:
        """Generate comprehensive test file with fixtures and tests"""
        template = """
        import pytest
        from unittest.mock import Mock, patch, mock_open
        from {{ module_path }} import {{ class_name }}
        {% for import_stmt in required_imports %}
        {{ import_stmt }}
        {% endfor %}

        {% for fixture in fixtures %}
        @pytest.fixture
        def {{ fixture.name }}():
            '''{{ fixture.doc }}'''
            {{ fixture.setup }}
            {% if fixture.cleanup %}
            yield {{ fixture.yield_value }}
            {{ fixture.cleanup }}
            {% else %}
            return {{ fixture.return_value }}
            {% endif %}
        {% endfor %}

        @pytest.mark.describe("{{ class_name }}")
        class Test{{ class_name }}:
            {% for method, sig in method_signatures.items() %}

            @pytest.mark.it("Should correctly handle {{ method }}")
            {% for decorator in sig.decorators %}
            {{ decorator }}
            {% endfor %}
            {% if sig.async %}
            @pytest.mark.asyncio
            async def test_{{ method }}(self, {{ fixture_list|join(', ') }}):
                # Arrange
                {% for mock in sig.mocks_required %}
                {{ mock.setup }}
                {% endfor %}
                {{ sig.setup }}

                # Act
                {% if sig.returns %}
                result = await instance.{{ method }}(
                    {% for arg in sig.args %}
                    {{ arg.name }}={{ arg.test_value }},
                    {% endfor %}
                )

                # Assert
                {% for assertion in sig.assertions %}
                {{ assertion }}
                {% endfor %}
                {% else %}
                await instance.{{ method }}({{ sig.args|join(', ') }})
                {% endif %}

            {% else %}
            def test_{{ method }}(self, {{ fixture_list|join(', ') }}):
                # Arrange
                {% for mock in sig.mocks_required %}
                {{ mock.setup }}
                {% endfor %}
                {{ sig.setup }}

                # Act
                {% if sig.returns %}
                result = instance.{{ method }}(
                    {% for arg in sig.args %}
                    {{ arg.name }}={{ arg.test_value }},
                    {% endfor %}
                )

                # Assert
                {% for assertion in sig.assertions %}
                {{ assertion }}
                {% endfor %}
                {% else %}
                instance.{{ method }}({{ sig.args|join(', ') }})
                {% endif %}

            {% endif %}

            {% if sig.raises %}
            @pytest.mark.parametrize("error_case", {{ sig.error_cases }})
            def test_{{ method }}_raises(self, error_case, {{ fixture_list|join(', ') }}):
                with pytest.raises({{ sig.raises }}) as exc_info:
                    {% if sig.async %}
                    await instance.{{ method }}(**error_case['inputs'])
                    {% else %}
                    instance.{{ method }}(**error_case['inputs'])
                    {% endif %}
                assert str(exc_info.value) == error_case['message']
            {% endif %}

            {% if sig.complexity.cyclomatic > 5 %}
            @pytest.mark.parametrize("edge_case", {{ method }}_edge_cases)
            def test_{{ method }}_edge_cases(self, edge_case, {{ fixture_list|join(', ') }}):
                # Test complex edge cases
                {{ edge_case.test_code }}
            {% endif %}
            {% endfor %}

            @pytest.mark.parametrize("invalid_input", [
                None, "", [], {}, object()
            ])
            def test_invalid_inputs(self, invalid_input):
                '''Test invalid input handling'''
                with pytest.raises(ValueError):
                    instance = {{ class_name }}(invalid_input)
        """

        try:
            return Template(template).render(
                module_path=self._get_module_path(),
                class_name=self.class_info.name,
                method_signatures=self.method_signatures,
                fixtures=self._generate_fixtures(),
                fixture_list=self._get_fixture_list(),
                required_imports=self._get_required_imports(),
            )
        except Exception as e:
            logger.error(f"Failed to generate test file: {e}")
            raise


# 6. Utility Classes
class AdvancedCommentPreserver:
    """Enhanced comment preservation with context awareness"""

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.comments: Dict[int, List[CommentBlock]] = {}
        self.docstrings: Dict[str, str] = {}

    def extract_comments(self):
        """Extract and categorize all comments from source"""
        # Tokenize source to get comments
        tokens = tokenize.generate_tokens(io.StringIO(self.source_code).readline)
        current_block = []

        for token in tokens:
            if token.type == tokenize.COMMENT:
                comment = CommentBlock(
                    content=token.string.lstrip("#"),
                    type="inline",
                    context=self._get_context(token.start[0]),
                    lineno=token.start[0],
                    indent=token.start[1],
                )
                self.comments.setdefault(token.start[0], []).append(comment)

        # Parse AST for docstrings
        try:
            tree = ast.parse(self.source_code)
            self._extract_docstrings(tree)
        except Exception as e:
            logger.warning(f"Failed to extract docstrings: {e}")

    def _extract_docstrings(self, tree: ast.AST):
        """Extract docstrings from valid nodes"""
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                try:
                    docstring = ast.get_docstring(node)
                    if docstring:
                        if isinstance(node, ast.Module):
                            self.docstrings["module"] = docstring
                        else:
                            self.docstrings[node.name] = docstring
                except Exception as e:
                    logger.debug(f"Failed to get docstring for {type(node)}: {e}")

    def _get_context(self, lineno: int) -> Optional[str]:
        """Determine code context for a comment line"""
        try:
            tree = ast.parse(self.source_code)
            for node in ast.walk(tree):
                if hasattr(node, "lineno"):
                    if node.lineno == lineno + 1:  # Comment is just above
                        if isinstance(node, ast.ClassDef):
                            return f"class:{node.name}"
                        elif isinstance(node, ast.FunctionDef):
                            return f"method:{node.name}"
        except Exception as e:
            logger.debug(f"Failed to get context for line {lineno}: {e}")
        return None

    def reattach_comments(self, generated_code: str) -> str:
        """Reattach comments while preserving context and formatting"""
        lines = generated_code.splitlines()
        output = []

        for i, line in enumerate(lines, 1):
            # Add any comments that should precede this line
            if i in self.comments:
                for comment in self.comments[i]:
                    indent = " " * comment.indent
                    output.append(f"{indent}# {comment.content}")

            # Add the line itself
            output.append(line)

            # Add any inline comments
            if i in self.comments:
                inline_comments = [c for c in self.comments[i] if c.type == "inline"]
                for comment in inline_comments:
                    output[-1] += f"  # {comment.content}"

        return "\n".join(output)


class RefactoringState:
    """Manages refactoring state and checkpoints"""

    def __init__(self, output_dir: Path):
        self.state_dir = output_dir / ".refactor"
        self.state_file = self.state_dir / "state.json"
        self.checkpoints_dir = self.state_dir / "checkpoints"
        self.current_checkpoint = None
        self.state = self._load_state()

    def _serialize_state(self, obj):
        """Convert state object to JSON-serializable format"""
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return {k: self._serialize_state(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_state(item) for item in obj]
        return obj

    def save_state(self):
        """Save current state to disk"""
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Convert state to JSON-serializable format
        serializable_state = self._serialize_state(self.state)

        self.state_file.write_text(json.dumps(serializable_state, indent=2))

    def _load_state(self) -> dict:
        """Load refactoring state from disk"""
        if self.state_file.exists():
            state_data = json.loads(self.state_file.read_text())
            # Convert lists back to sets where needed
            if "processed_modules" in state_data:
                state_data["processed_modules"] = set(state_data["processed_modules"])
            return state_data
        return {
            "status": "new",
            "processed_modules": set(),
            "checkpoints": {},
            "last_run": None,
            "stats": {"files_processed": 0, "classes_refactored": 0, "errors": []},
        }

    def create_checkpoint(self, name: str) -> str:
        """Create a named checkpoint of current state"""
        checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Convert state to serializable format
        serializable_state = self._serialize_state(self.state)

        checkpoint = {
            "id": checkpoint_id,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "state": serializable_state,
            "files": self._snapshot_files(),
        }

        # Save checkpoint
        checkpoint_dir = self.checkpoints_dir / checkpoint_id
        checkpoint_dir.mkdir(parents=True)
        (checkpoint_dir / "checkpoint.json").write_text(
            json.dumps(checkpoint, indent=2)
        )

        self.state["checkpoints"][checkpoint_id] = {
            "name": name,
            "timestamp": checkpoint["timestamp"],
        }
        self.save_state()
        return checkpoint_id

    def _snapshot_files(self) -> Dict[str, str]:
        """Take snapshot of current files with checksums"""
        snapshots = {}
        for file in self.state_dir.parent.rglob("*.py"):
            if ".refactor" not in str(file):
                rel_path = file.relative_to(self.state_dir.parent)
                snapshots[str(rel_path)] = self._get_file_hash(file)
        return snapshots

    def _get_file_hash(self, file: Path) -> str:
        """Get hash of file contents"""
        import hashlib

        return hashlib.md5(file.read_bytes()).hexdigest()

    def rollback_to_checkpoint(self, checkpoint_id: str):
        """Rollback to a specific checkpoint"""
        if checkpoint_id not in self.state["checkpoints"]:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        checkpoint_dir = self.checkpoints_dir / checkpoint_id
        checkpoint = json.loads((checkpoint_dir / "checkpoint.json").read_text())

        # Convert lists back to sets in restored state
        restored_state = checkpoint["state"]
        if "processed_modules" in restored_state:
            restored_state["processed_modules"] = set(
                restored_state["processed_modules"]
            )

        # Restore state
        self.state = restored_state

        # Restore files
        for rel_path, checksum in checkpoint["files"].items():
            file = self.state_dir.parent / rel_path
            if file.exists():
                current_hash = self._get_file_hash(file)
                if current_hash != checksum:
                    # File changed since checkpoint
                    backup = file.with_suffix(".bak")
                    file.rename(backup)
                    shutil.copy2(checkpoint_dir / rel_path, file)

        self.save_state()

    def get_status(self) -> dict:
        """Get current refactoring status"""
        return {
            "status": self.state["status"],
            "processed_modules": list(self.state["processed_modules"]),
            "last_run": self.state["last_run"],
            "stats": self.state["stats"],
            "checkpoints": self.state["checkpoints"],
        }

    def validate(self) -> List[str]:
        """Validate current refactoring state"""
        issues = []

        # Check file integrity
        for module in self.state["processed_modules"]:
            module_dir = self.state_dir.parent / module
            if not module_dir.exists():
                issues.append(f"Missing module directory: {module}")

            # Check required files
            required = ["__init__.py", "py.typed"]
            for req in required:
                if not (module_dir / req).exists():
                    issues.append(f"Missing {req} in {module}")

        # Validate imports
        for py_file in self.state_dir.parent.rglob("*.py"):
            try:
                ast.parse(py_file.read_text())
            except SyntaxError:
                issues.append(f"Invalid syntax in {py_file}")

        return issues


class CodeRefactorer:
    """Main refactoring orchestrator"""

    def __init__(self, source_file: str, output_dir: str, config_file: str):
        """Initialize the refactorer with configuration"""
        self.source_file = Path(source_file) if source_file else None
        self.output_dir = Path(output_dir)
        self.config = self._load_config(config_file) if config_file else {}
        self.dependency_resolver = DependencyResolver()
        self.module_generator = ModuleGenerator(self.output_dir, self.config)
        self.backup_dir = Path(output_dir) / ".backup"
        self.stats = {"files_processed": 0, "classes_refactored": 0, "errors": []}

        # Only initialize these if we have a source file
        if self.source_file:
            self.comment_preserver = AdvancedCommentPreserver(
                self.source_file.read_text()
            )
        else:
            self.comment_preserver = None

        self.license_manager = LicenseManager(self.config)
        self.doc_generator = DocumentationGenerator(self.output_dir, self.config)
        self.scaffolder = ProjectScaffolder(self.config, self.output_dir)
        self.state = RefactoringState(self.output_dir)

        # Initialize progress tracker after config is loaded
        if self.config and "modules" in self.config:
            module_counts = {
                name: len(self.config["modules"][name]["classes"])
                for name in self.config["modules"]
            }
            self.progress = ProgressTracker(module_counts)
        else:
            self.progress = None

    def ref_resume(self):
        """Resume previous refactoring"""
        if self.state.get_status()["status"] == "new":
            raise ValueError("No previous refactoring to resume")

        # Continue from last processed module
        processed = self.state.state["processed_modules"]
        remaining = set(self.config["modules"]) - processed

        for module_name in remaining:
            self._process_module(module_name)

    def ref_refactor_modules(self, modules: List[str]):
        """Refactor specific modules"""
        invalid = set(modules) - set(self.config["modules"])
        if invalid:
            raise ValueError(f"Invalid modules: {invalid}")

        for module_name in modules:
            self._process_module(module_name)

    def _process_module(self, module_name: str):
        """Process a single module"""
        self.progress.start_module(module_name)
        logger.info(f"Processing module {module_name}")

        module_config = self.config["modules"][module_name]
        classes = [
            self.dependency_resolver.analyzed_classes[class_name]
            for class_name in module_config["classes"]
        ]

        for class_info in classes:
            self.module_generator.generate_module(module_name, [class_info])
            self.progress.complete_class(module_name)

        self.state.state["processed_modules"].add(module_name)
        self.state.state["stats"]["classes_refactored"] += len(classes)
        self.state.save_state()

    def ref_validate(self) -> List[str]:
        """Validate current state"""
        return self.state.validate()

    def ref_create_checkpoint(self, name: str) -> str:
        """Create named checkpoint"""
        return self.state.create_checkpoint(name)

    def ref_rollback(self, checkpoint_id: str):
        """Rollback to checkpoint"""
        self.state.rollback_to_checkpoint(checkpoint_id)

    def _validate_config_structure(self, config: dict):
        """Validate the structure and required fields of the config"""
        # Split required fields into separate variables for better readability
        required_top_level = {
            "version",
            "project_name",
            "project_description",
            "modules",
            "settings",
        }
        missing = required_top_level - set(config.keys())
        if missing:
            raise ValueError(f"Missing required top-level config keys: {missing}")

        # Validate modules section
        if not isinstance(config["modules"], dict):
            raise ValueError("'modules' must be a dictionary")

        for module_name, module_config in config["modules"].items():
            self._validate_module_config(module_name, module_config)

        # Validate settings section
        self._validate_settings_config(config["settings"])

    def _validate_module_config(self, module_name: str, module_config: dict):
        """Validate individual module configuration"""
        required_module_fields = {"description", "classes", "dependencies"}
        missing = required_module_fields - set(module_config.keys())
        if missing:
            raise ValueError(
                f"Module '{module_name}' missing required fields: {missing}"
            )

        if not isinstance(module_config["classes"], list):
            raise ValueError(f"Module '{module_name}' classes must be a list")

        if not isinstance(module_config["dependencies"], list):
            raise ValueError(f"Module '{module_name}' dependencies must be a list")

    def _validate_settings_config(self, settings: dict):
        """Validate settings configuration"""
        required_settings = {
            "format_code",
            "generate_docs",
            "check_dependencies",
            "validate_structure",
        }
        missing = required_settings - set(settings.keys())
        if missing:
            raise ValueError(f"Missing required settings: {missing}")

        for setting in required_settings:
            if not isinstance(settings[setting], bool):
                raise ValueError(f"Setting '{setting}' must be a boolean")

    def _load_config(self, config_file: str) -> dict:
        """Load and validate configuration from YAML file"""
        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
                self._validate_config_structure(config)
                return config
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config: {e}")
            raise
        except IOError as e:
            logger.error(f"Failed to read config file: {e}")
            raise

    def validate_environment(self):
        """Validate environment before refactoring"""
        try:
            # Create main project structure using scaffolder
            self.scaffolder._create_directory_structure()
        except Exception as e:
            logger.error(f"Failed to create directory structure: {e}")
            raise

        # Check file permissions
        if not os.access(self.output_dir, os.W_OK):
            raise PermissionError(f"No write permission for {self.output_dir}")

        # Validate Python version
        if sys.version_info < (3, 7):
            raise RuntimeError("Python 3.7+ required")

        # Validate source file exists
        if not self.source_file.exists():
            raise FileNotFoundError(f"Source file not found: {self.source_file}")

        # Validate source file is readable
        if not os.access(self.source_file, os.R_OK):
            raise PermissionError(f"No read permission for {self.source_file}")

    def create_backup(self):
        """Create backup of files before refactoring"""
        import shutil

        try:
            self.backup_dir.mkdir(exist_ok=True, parents=True)
            if self.source_file.exists():
                shutil.copy2(self.source_file, self.backup_dir)
                logger.info(f"Created backup at {self.backup_dir}")
        except OSError as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def rollback(self):
        """Rollback changes in case of failure"""
        import shutil

        try:
            if self.backup_dir.exists():
                for backup_file in self.backup_dir.glob("*"):
                    shutil.copy2(backup_file, self.source_file.parent)
                logger.info("Successfully rolled back changes")
        except OSError as e:
            logger.error(f"Failed to rollback changes: {e}")
            raise

    def _generate_dependency_graph(self):
        """Generate visual dependency graph"""
        try:
            graph = self.dependency_resolver.dependency_graph
            nx.draw(graph, with_labels=True)
            plt.savefig(self.output_dir / "dependencies.png")
        except Exception as e:
            logger.error(f"Failed to generate dependency graph: {e}")
            self.stats["errors"].append(str(e))

    def _generate_metrics_report(self):
        """Generate metrics report"""
        report = {
            "files_processed": self.stats["files_processed"],
            "classes_refactored": self.stats["classes_refactored"],
            "errors": self.stats["errors"],
        }
        with open(self.output_dir / "metrics.json", "w") as f:
            json.dump(report, f, indent=2)

    def _generate_change_summary(self):
        """Generate summary of changes made"""
        with open(self.output_dir / "changes.txt", "w") as f:
            f.write(f"Files processed: {self.stats['files_processed']}\n")
            f.write(f"Classes refactored: {self.stats['classes_refactored']}\n")
            if self.stats["errors"]:
                f.write("\nErrors encountered:\n")
                for error in self.stats["errors"]:
                    f.write(f"- {error}\n")

    def _reattach_comments(self):
        """Reattach preserved comments to generated code"""
        for py_file in self.output_dir.rglob("*.py"):
            content = py_file.read_text()
            modified_content = self.comment_preserver.reattach_comments(content)
            py_file.write_text(modified_content)

    def refactor(self):
        """Perform the refactoring with error handling and statistics"""

        logger.info("Available classes in source:")
        for class_name in self.dependency_resolver.analyzed_classes.keys():
            logger.info(f"  - {class_name}")
        logger.info("Starting refactoring process")
        try:
            # 1. Validate environment
            self.validate_environment()

            # 2. Create backup
            self.create_backup()

            # 3. Read source code
            source_code = self.source_file.read_text()
            self.stats["files_processed"] += 1

            # 4. Create project structure first
            logger.info("Generating project structure")
            self.scaffolder.generate_project_files()

            # 5. Analyze dependencies
            logger.info("Analyzing dependencies")
            self.dependency_resolver.build_dependency_graph(source_code)

            # 6. Extract comments
            logger.info("Extracting comments")
            self.comment_preserver.extract_comments()

            # 7. Generate licenses
            logger.info("Generating licenses")
            self.license_manager.generate_license()

            # 8. Process modules and classes
            logger.info("Processing modules and classes")
            processed_files = []
            for module_name, module_config in self.config["modules"].items():
                logger.info(f"Processing module: {module_name}")
                self._process_module(module_name)
                classes = [
                    self.dependency_resolver.analyzed_classes[class_name]
                    for class_name in module_config["classes"]
                ]
                generated_files = self.module_generator.generate_module(
                    module_name, classes
                )
                processed_files.extend(generated_files)
                self.stats["classes_refactored"] += len(classes)

            # 9. Reattach comments
            logger.info("Reattaching comments")
            self._reattach_comments()

            # 10. Format code if enabled and files exist
            if self.config["settings"]["format_code"] and processed_files:
                logger.info("Formatting generated code")
                self._format_code(processed_files)

            # 11. Generate documentation
            if self.config["settings"]["generate_docs"]:
                logger.info("Generating documentation")
                try:
                    self.doc_generator.generate_documentation()
                except Exception as e:
                    logger.error(f"Documentation generation failed: {e}")
                    self.stats["errors"].append(f"Documentation generation failed: {e}")

            # 12. Generate reports
            logger.info("Generating reports")
            self._generate_dependency_graph()
            self._generate_metrics_report()
            self._generate_change_summary()

            logger.info("Refactoring complete")

        except Exception as e:
            logger.error(f"Refactoring failed: {e}")
            self.stats["errors"].append(str(e))
            self.rollback()
            raise

    def _format_code(self, processed_files: List[Path]):
        """Format processed Python files with error handling"""
        temp_files = []
        try:
            for py_file in processed_files:
                if py_file.exists() and py_file.suffix == ".py":
                    logger.debug(f"Formatting file: {py_file}")

                    # Read current content and validate
                    content = py_file.read_text()
                    try:
                        ast.parse(content)  # Validate syntax before formatting
                    except SyntaxError as e:
                        logger.error(f"Invalid Python syntax in {py_file}: {e}")
                        continue

                    # Create backup
                    temp_file = py_file.with_suffix(".py.bak")
                    temp_files.append(temp_file)
                    py_file.rename(temp_file)

                    try:
                        # Format with isort
                        sorted_content = isort.code(content, settings_path=None)

                        # Validate sorted content
                        try:
                            ast.parse(sorted_content)
                        except SyntaxError:
                            logger.error(f"isort produced invalid syntax for {py_file}")
                            raise

                        # Format with black
                        try:
                            formatted = format_str(sorted_content, mode=FileMode())
                        except Exception as black_error:
                            logger.error(
                                f"black formatting failed for {py_file}: {black_error}"
                            )
                            raise

                        # Final syntax check
                        try:
                            ast.parse(formatted)
                        except SyntaxError:
                            logger.error(
                                f"Formatting produced invalid syntax for {py_file}"
                            )
                            raise

                        # Write formatted content
                        py_file.write_text(formatted)

                    except Exception as format_error:
                        logger.error(f"Failed to format {py_file}: {format_error}")
                        # Restore from backup
                        if temp_file.exists():
                            temp_file.rename(py_file)
                        raise

            # Clean up backup files
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()

        except Exception as e:
            logger.error(f"Code formatting failed: {e}")
            # Restore all files from backups
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.rename(temp_file.with_suffix(""))
            self.stats["errors"].append(str(e))
            raise


class ProgressTracker:
    """Track and display refactoring progress"""

    DONE = "✓"  # Completed module
    PENDING = "○"  # Not started
    IN_PROGRESS = "⋯"  # Currently processing
    BAR_WIDTH = 40  # Progress bar width

    def __init__(self, modules: Dict[str, int]):
        """Initialize with module names and class counts"""
        self.modules = modules
        self.total_classes = sum(modules.values())
        self.completed_classes = 0
        self.current_module = None
        self.module_progress = {name: 0 for name in modules}

    def start_module(self, module_name: str):
        """Start processing a module"""
        self.current_module = module_name
        self._display_progress()

    def complete_class(self, module_name: str):
        """Mark a class as completed"""
        self.completed_classes += 1
        self.module_progress[module_name] += 1
        self._display_progress()

    def _get_progress_bar(self) -> str:
        """Generate progress bar string"""
        progress = self.completed_classes / self.total_classes
        filled = int(self.BAR_WIDTH * progress)
        bar = "█" * filled + "░" * (self.BAR_WIDTH - filled)
        percentage = int(progress * 100)
        return f"[{bar}] {percentage}%"

    def _display_progress(self):
        """Display current progress"""
        # Clear screen in a cross-platform way
        os.system("cls" if os.name == "nt" else "clear")

        print("Refactoring Progress:")
        print(self._get_progress_bar())
        print("\nCompleted:")
        for module, count in self.modules.items():
            completed = self.module_progress[module]
            if completed == count:
                print(f"  {self.DONE} {module} ({completed}/{count} classes)")

        print("\nIn Progress:")
        if self.current_module:
            completed = self.module_progress[self.current_module]
            total = self.modules[self.current_module]
            if completed < total:
                print(
                    f"  {self.IN_PROGRESS} {self.current_module} ({completed}/{total} classes)"
                )

        print("\nPending:")
        for module, count in self.modules.items():
            if self.module_progress[module] == 0:
                print(f"  {self.PENDING} {module} (0/{count} classes)")


def main():
    """Main function to run the refactoring"""
    import argparse

    parser = argparse.ArgumentParser(description="Advanced Python code refactoring")
    parser.add_argument("source", help="Source file path")
    parser.add_argument("output", help="Output directory path")
    parser.add_argument("config", help="Configuration file path")
    # Add incremental options
    parser.add_argument(
        "--resume", action="store_true", help="Resume previous refactoring"
    )
    parser.add_argument("--modules", help="Comma-separated modules to refactor")
    parser.add_argument("--status", action="store_true", help="Show refactoring status")
    parser.add_argument(
        "--validate", action="store_true", help="Validate current state"
    )
    parser.add_argument("--checkpoint", help="Create named checkpoint")
    parser.add_argument("--rollback", help="Rollback to checkpoint ID")

    args = parser.parse_args()

    try:
        if (
            args.resume
            or args.modules
            or args.status
            or args.validate
            or args.checkpoint
            or args.rollback
        ):
            # Incremental operations
            if not all([args.output]):
                parser.error("Output directory required")
            refactorer = CodeRefactorer(None, args.output, None)

            if args.resume:
                refactorer.resume()
            elif args.modules:
                modules = [m.strip() for m in args.modules.split(",")]
                refactorer.refactor_modules(modules)
            elif args.status:
                status = refactorer.state.get_status()
                print(json.dumps(status, indent=2))
            elif args.validate:
                issues = refactorer.validate()
                if issues:
                    print("Validation issues found:")
                    for issue in issues:
                        print(f"- {issue}")
                else:
                    print("Validation passed")
            elif args.checkpoint:
                checkpoint_id = refactorer.create_checkpoint(args.checkpoint)
                print(f"Created checkpoint: {checkpoint_id}")
            elif args.rollback:
                refactorer.rollback(args.rollback)
                print(f"Rolled back to checkpoint: {args.rollback}")

        else:
            # Full refactoring
            if not all([args.source, args.output, args.config]):
                parser.error("Source, output and config required")
            refactorer = CodeRefactorer(args.source, args.output, args.config)
            refactorer.refactor()

    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise


if __name__ == "__main__":
    main()
