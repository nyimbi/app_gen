from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set, Sequence, Tuple
import json
import logging

logger = logging.getLogger(__name__)

class PromptCategory(Enum):
    """High-level categories for organizing prompts"""
    CODE_IMPROVEMENT = "code_improvement"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEBUGGING = "debugging"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TYPES = "types"
    ARCHITECTURE = "architecture"
    STANDARDS = "standards"

class PromptType(Enum):
    """Available prompt types within categories"""

    # Code Generation & Improvement (CI_*)
    CI_IMPROVE = "ci_improve"
    CI_REFACTOR = "ci_refactor"
    CI_CLEAN = "ci_clean"
    CI_BEST_PRACTICES = "ci_best_practices"
    CI_GENERATE = "ci_generate"
    CI_BOILERPLATE = "ci_boilerplate"
    CI_SCAFFOLD = "ci_scaffold"
    CI_MODERNIZE = "ci_modernize"
    CI_MIGRATE = "ci_migrate"
    CI_UPGRADE = "ci_upgrade"

    # Refactoring (RF_*)
    RF_EXTRACT_METHOD = "rf_extract_method"
    RF_EXTRACT_CLASS = "rf_extract_class"
    RF_INLINE_METHOD = "rf_inline_method"
    RF_MOVE_METHOD = "rf_move_method"
    RF_RENAME = "rf_rename"
    RF_ENCAPSULATE = "rf_encapsulate"
    RF_PULL_UP = "rf_pull_up"
    RF_PUSH_DOWN = "rf_push_down"
    RF_TEMPLATE = "rf_template"
    RF_ALGORITHM = "rf_algorithm"

    # Design Patterns (PAT_*)
    PAT_FACTORY = "pat_factory"
    PAT_ABSTRACT_FACTORY = "pat_abstract_factory"
    PAT_BUILDER = "pat_builder"
    PAT_SINGLETON = "pat_singleton"
    PAT_ADAPTER = "pat_adapter"
    PAT_BRIDGE = "pat_bridge"
    PAT_COMPOSITE = "pat_composite"
    PAT_DECORATOR = "pat_decorator"
    PAT_FACADE = "pat_facade"
    PAT_PROXY = "pat_proxy"

    # Documentation (DOC_*)
    DOC_CLASS = "doc_class"
    DOC_MODULE = "doc_module"
    DOC_FUNCTION = "doc_function"
    DOC_INLINE = "doc_inline"
    DOC_API = "doc_api"
    DOC_ARCHITECTURE = "doc_architecture"
    DOC_DEPLOYMENT = "doc_deployment"
    DOC_TUTORIAL = "doc_tutorial"
    DOC_EXAMPLES = "doc_examples"

    # Testing (TEST_*)
    TEST_UNIT = "test_unit"
    TEST_INTEGRATION = "test_integration"
    TEST_E2E = "test_e2e"
    TEST_PROPERTY = "test_property"
    TEST_FUZZ = "test_fuzz"
    TEST_MUTATION = "test_mutation"
    TEST_LOAD = "test_load"
    TEST_STRESS = "test_stress"
    TEST_SECURITY = "test_security"

    # Debugging (DBG_*)
    DBG_TRACE = "dbg_trace"
    DBG_PROFILE = "dbg_profile"
    DBG_MEMORY = "dbg_memory"
    DBG_STATIC = "dbg_static"
    DBG_DYNAMIC = "dbg_dynamic"
    DBG_LEAK = "dbg_leak"
    DBG_RACE = "dbg_race"
    DBG_DEADLOCK = "dbg_deadlock"

    # Performance (PERF_*)
    PERF_OPTIMIZE = "perf_optimize"
    PERF_ALGORITHM = "perf_algorithm"
    PERF_MEMORY = "perf_memory"
    PERF_CPU = "perf_cpu"
    PERF_IO = "perf_io"
    PERF_CACHE = "perf_cache"
    PERF_PARALLEL = "perf_parallel"
    PERF_DISTRIBUTED = "perf_distributed"
    PERF_ASYNC = "perf_async"
    PERF_BATCH = "perf_batch"

    # Security (SEC_*)
    SEC_AUDIT = "sec_audit"
    SEC_VULN = "sec_vuln"
    SEC_INJECTION = "sec_injection"
    SEC_VALIDATE = "sec_validate"
    SEC_AUTH = "sec_auth"
    SEC_CRYPTO = "sec_crypto"
    SEC_SECRETS = "sec_secrets"
    SEC_PERMS = "sec_perms"
    SEC_SANITIZE = "sec_sanitize"

    # Types (TYPE_*)
    TYPE_HINTS = "type_hints"
    TYPE_CHECK = "type_check"
    TYPE_RUNTIME = "type_runtime"
    TYPE_GENERIC = "type_generic"
    TYPE_PROTOCOL = "type_protocol"
    TYPE_STRUCTURAL = "type_structural"
    TYPE_GRADUAL = "type_gradual"
    TYPE_INFER = "type_infer"

    # Architecture (ARCH_*)
    ARCH_PATTERN = "arch_pattern"
    ARCH_SOLID = "arch_solid"
    ARCH_CLEAN = "arch_clean"
    ARCH_MICRO = "arch_micro"
    ARCH_EVENT = "arch_event"
    ARCH_DOMAIN = "arch_domain"
    ARCH_MESH = "arch_mesh"
    ARCH_API = "arch_api"
    ARCH_DB = "arch_db"

    # Quality (QUAL_*)
    QUAL_COMPLEX = "qual_complex"
    QUAL_MAINTAIN = "qual_maintain"
    QUAL_READ = "qual_read"
    QUAL_SMELL = "qual_smell"
    QUAL_DEBT = "qual_debt"
    QUAL_COHESION = "qual_cohesion"
    QUAL_COUPLING = "qual_coupling"
    QUAL_MODULE = "qual_module"

    # Standards (STD_*)
    STD_PEP8 = "std_pep8"
    STD_TYPES = "std_types"
    STD_IMPORTS = "std_imports"
    STD_DOCSTRING = "std_docstring"
    STD_NAMING = "std_naming"
    STD_LOGGING = "std_logging"
    STD_ERRORS = "std_errors"
    STD_CONFIG = "std_config"

    @classmethod
    def get_category(cls, prompt_type: 'PromptType') -> PromptCategory:
        """Get category for prompt type"""
        prefix = prompt_type.value.split('_')[0].upper()
        category_map = {
            'CI': PromptCategory.CODE_IMPROVEMENT,
            'RF': PromptCategory.REFACTORING,
            'PAT': PromptCategory.ARCHITECTURE,
            'DOC': PromptCategory.DOCUMENTATION,
            'TEST': PromptCategory.TESTING,
            'DBG': PromptCategory.DEBUGGING,
            'PERF': PromptCategory.PERFORMANCE,
            'SEC': PromptCategory.SECURITY,
            'TYPE': PromptCategory.TYPES,
            'ARCH': PromptCategory.ARCHITECTURE,
            'QUAL': PromptCategory.CODE_IMPROVEMENT,
            'STD': PromptCategory.STANDARDS
        }
        return category_map.get(prefix, PromptCategory.CODE_IMPROVEMENT)

@dataclass
class PromptTemplate:
    """Template for code-related prompts"""
    name: str
    prompt_type: PromptType
    system_message: str
    template: str
    examples: List[Dict[str, str]] = field(default_factory=list)
    guidelines: List[str] = field(default_factory=list)
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: Optional[datetime] = None
    use_count: int = 0
    success_count: int = 0

    def record_use(self, success: bool) -> None:
        """Record template usage"""
        self.use_count += 1
        if success:
            self.success_count += 1
        self.modified_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert template to dictionary"""
        return {
            "name": self.name,
            "prompt_type": self.prompt_type.value,
            "system_message": self.system_message,
            "template": self.template,
            "examples": self.examples,
            "guidelines": self.guidelines,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "use_count": self.use_count,
            "success_count": self.success_count
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PromptTemplate':
        """Create template from dictionary"""
        data = data.copy()
        data["prompt_type"] = PromptType(data["prompt_type"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data["modified_at"]:
            data["modified_at"] = datetime.fromisoformat(data["modified_at"])
        return cls(**data)

@dataclass
class PromptSequence:
    """Defines a sequence of prompts to be executed in order with metadata and execution tracking"""
    name: str
    description: str
    prompts: List[PromptType]
    tags: Set[str] = field(default_factory=set)
    enabled: bool = True
    priority: int = 0
    max_retries: int = 3
    timeout: int = 300
    required_templates: Set[str] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)
    results_cache: Dict[str, List[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: Optional[datetime] = None
    last_run: Optional[datetime] = None
    use_count: int = 0
    success_count: int = 0
    avg_duration: float = 0.0

    def record_execution(self, duration: float, success: bool) -> None:
        """Record execution metrics"""
        self.use_count += 1
        if success:
            self.success_count += 1
        self.last_run = datetime.now()
        self.avg_duration = (
            (self.avg_duration * (self.use_count - 1) + duration) / self.use_count
        )

    def add_dependency(self, sequence_name: str) -> None:
        """Add dependent sequence"""
        if sequence_name not in self.dependencies:
            self.dependencies.append(sequence_name)
            self.modified_at = datetime.now()

    def add_required_template(self, template_name: str) -> None:
        """Add required template"""
        self.required_templates.add(template_name)
        self.modified_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Add tag to sequence"""
        self.tags.add(tag)
        self.modified_at = datetime.now()

    def cache_result(self, code_hash: str, results: List[str]) -> None:
        """Cache execution results"""
        self.results_cache[code_hash] = results
        self.modified_at = datetime.now()

    def get_cached_result(self, code_hash: str) -> Optional[List[str]]:
        """Get cached results if available"""
        return self.results_cache.get(code_hash)

    def clear_cache(self) -> None:
        """Clear results cache"""
        self.results_cache.clear()
        self.modified_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert sequence to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "prompts": [p.value for p in self.prompts],
            "tags": list(self.tags),
            "enabled": self.enabled,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "required_templates": list(self.required_templates),
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "use_count": self.use_count,
            "success_count": self.success_count,
            "avg_duration": self.avg_duration
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PromptSequence':
        """Create sequence from dictionary"""
        data = data.copy()
        data["prompts"] = [PromptType(p) for p in data["prompts"]]
        data["tags"] = set(data.get("tags", []))
        data["required_templates"] = set(data.get("required_templates", []))
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data["modified_at"]:
            data["modified_at"] = datetime.fromisoformat(data["modified_at"])
        if data["last_run"]:
            data["last_run"] = datetime.fromisoformat(data["last_run"])
        return cls(**data)

class PromptLibrary:
    """Manages prompt templates and sequences with persistence"""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path.home() / ".prompts"
        self.templates_dir = self.storage_dir / "templates"
        self.sequences_dir = self.storage_dir / "sequences"
        self.backup_dir = self.storage_dir / "backups"

        # Create directories
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.sequences_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize storage
        self.templates: Dict[str, PromptTemplate] = {}
        self.sequences: Dict[str, PromptSequence] = {}
        self.template_categories: Dict[PromptCategory, List[str]] = {
            cat: [] for cat in PromptCategory
        }

        self._load_templates()
        self._load_sequences()

    def _load_templates(self) -> None:
        """Load templates from storage"""
        try:
            for file in self.templates_dir.glob("*.json"):
                template_data = json.loads(file.read_text())
                template = PromptTemplate.from_dict(template_data)
                self.templates[template.name] = template

                # Categorize template
                category = PromptType.get_category(template.prompt_type)
                self.template_categories[category].append(template.name)
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            self._backup_storage("templates")

    def _load_sequences(self) -> None:
        """Load sequences from storage"""
        try:
            for file in self.sequences_dir.glob("*.json"):
                sequence_data = json.loads(file.read_text())
                sequence = PromptSequence.from_dict(sequence_data)
                self.sequences[sequence.name] = sequence
        except Exception as e:
            logger.error(f"Failed to load sequences: {e}")
            self._backup_storage("sequences")

    def _backup_storage(self, storage_type: str) -> None:
        """Backup storage directory on error"""
        try:
            source = self.templates_dir if storage_type == "templates" else self.sequences_dir
            backup_path = self.backup_dir / f"{storage_type}_{datetime.now().isoformat()}"
            import shutil
            shutil.copytree(source, backup_path)
            logger.info(f"Created backup at {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")

    def save_template(self, template: PromptTemplate, backup: bool = True) -> None:
        """Save template to storage"""
        try:
            if backup:
                self._backup_template(template.name)

            file_path = self.templates_dir / f"{template.name}.json"
            file_path.write_text(json.dumps(template.to_dict(), indent=2))
            self.templates[template.name] = template

            # Update categorization
            category = PromptType.get_category(template.prompt_type)
            if template.name not in self.template_categories[category]:
                self.template_categories[category].append(template.name)

        except Exception as e:
            logger.error(f"Failed to save template {template.name}: {e}")

    def save_sequence(self, sequence: PromptSequence, backup: bool = True) -> None:
        """Save sequence to storage"""
        try:
            if backup:
                self._backup_sequence(sequence.name)

            file_path = self.sequences_dir / f"{sequence.name}.json"
            file_path.write_text(json.dumps(sequence.to_dict(), indent=2))
            self.sequences[sequence.name] = sequence
        except Exception as e:
            logger.error(f"Failed to save sequence {sequence.name}: {e}")

    def _backup_template(self, template_name: str) -> None:
        """Create backup of existing template"""
        existing = self.templates_dir / f"{template_name}.json"
        if existing.exists():
            backup_path = self.backup_dir / "templates" / f"{template_name}_{datetime.now().isoformat()}.json"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(existing, backup_path)

    def _backup_sequence(self, sequence_name: str) -> None:
        """Create backup of existing sequence"""
        existing = self.sequences_dir / f"{sequence_name}.json"
        if existing.exists():
            backup_path = self.backup_dir / "sequences" / f"{sequence_name}_{datetime.now().isoformat()}.json"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(existing, backup_path)

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get template by name"""
        return self.templates.get(name)

    def get_sequence(self, name: str) -> Optional[PromptSequence]:
        """Get sequence by name"""
        return self.sequences.get(name)

    def get_templates_by_category(self, category: PromptCategory) -> List[PromptTemplate]:
        """Get all templates in a category"""
        return [self.templates[name] for name in self.template_categories[category]]

    def delete_template(self, name: str, backup: bool = True) -> bool:
        """Delete template with optional backup"""
        if name not in self.templates:
            return False

        try:
            if backup:
                self._backup_template(name)

            template = self.templates[name]
            file_path = self.templates_dir / f"{name}.json"
            file_path.unlink()

            # Update categorization
            category = PromptType.get_category(template.prompt_type)
            self.template_categories[category].remove(name)
            del self.templates[name]

            return True
        except Exception as e:
            logger.error(f"Failed to delete template {name}: {e}")
            return False

    def delete_sequence(self, name: str, backup: bool = True) -> bool:
        """Delete sequence with optional backup"""
        if name not in self.sequences:
            return False

        try:
            if backup:
                self._backup_sequence(name)

            file_path = self.sequences_dir / f"{name}.json"
            file_path.unlink()
            del self.sequences[name]
            return True
        except Exception as e:
            logger.error(f"Failed to delete sequence {name}: {e}")
            return False

    def list_templates(self) -> List[str]:
        """List all template names"""
        return list(self.templates.keys())

    def list_sequences(self) -> List[str]:
        """List all sequence names"""
        return list(self.sequences.keys())

    def get_template_count(self) -> int:
        """Get total number of templates"""
        return len(self.templates)

    def get_sequence_count(self) -> int:
        """Get total number of sequences"""
        return len(self.sequences)

class PromptManager:
    """Manages prompt templates and sequences with execution"""

    def __init__(self):
        self.library = PromptLibrary()
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Initialize default templates and sequences"""
        templates = self._create_default_templates()
        sequences = self._create_default_sequences()

        for template in templates:
            self.library.save_template(template)
        for sequence in sequences:
            self.library.save_sequence(sequence)

    def _create_default_templates(self) -> List[PromptTemplate]:
        """Create default prompt templates"""
        templates = []

        # Generate template for each PromptType
        for prompt_type in PromptType:
            template_config = self._get_template_config(prompt_type)
            templates.append(PromptTemplate(
                name=prompt_type.value,
                prompt_type=prompt_type,
                system_message=template_config["system_message"],
                template=template_config["template"],
                guidelines=template_config["guidelines"]
            ))

        return templates

    def _get_template_config(self, prompt_type: PromptType) -> Dict[str, any]:
        """Get template configuration for prompt type"""
        configs = {
            # Refactoring
            PromptType.RF_EXTRACT_METHOD: {
                "system_message": "You are a Python refactoring expert specializing in method extraction.",
                "template": """Extract methods from this code to improve modularity:

```python
{code}
```

Focus on:
1. Identifying code blocks for extraction
2. Single Responsibility Principle
3. Method cohesion
4. Parameter passing
5. Return values
6. Method naming
7. Code reusability
8. Testing considerations

Provide only the refactored code with extracted methods.""",
                "guidelines": [
                    "Extract cohesive code blocks",
                    "Follow Single Responsibility Principle",
                    "Use clear method names",
                    "Handle parameters and return values properly",
                    "Maintain code testability",
                    "Consider method reusability"
                ]
            },

            PromptType.RF_EXTRACT_CLASS: {
                "system_message": "You are a Python refactoring expert specializing in class extraction.",
                "template": """Extract appropriate classes from this code:

```python
{code}
```

Focus on:
1. Identifying related attributes and methods
2. Class responsibilities
3. Class relationships
4. Interface design
5. Dependency management
6. Encapsulation
7. Class cohesion
8. Testing approach

Provide only the refactored code with extracted classes.""",
                "guidelines": [
                    "Group related functionality",
                    "Define clear responsibilities",
                    "Design proper interfaces",
                    "Manage dependencies",
                    "Ensure proper encapsulation",
                    "Consider testing implications"
                ]
            },

            PromptType.RF_INLINE_METHOD: {
                "system_message": "You are a Python refactoring expert specializing in method inlining.",
                "template": """Inline appropriate methods in this code:

```python
{code}
```

Focus on:
1. Identifying methods for inlining
2. Code clarity impact
3. Performance implications
4. Maintenance considerations
5. Code duplication
6. Method complexity
7. Call hierarchy
8. Testing strategy

Provide only the refactored code with inlined methods.""",
                "guidelines": [
                    "Evaluate inlining benefits",
                    "Maintain code clarity",
                    "Consider performance impact",
                    "Avoid excessive complexity",
                    "Prevent code duplication",
                    "Preserve functionality"
                ]
            },

            PromptType.RF_MOVE_METHOD: {
                "system_message": "You are a Python refactoring expert specializing in method relocation.",
                "template": """Move methods to appropriate classes:

```python
{code}
```

Focus on:
1. Method placement analysis
2. Class relationships
3. Feature envy detection
4. Dependency management
5. Interface consistency
6. Class cohesion
7. Method accessibility
8. Testing strategy

Provide only the refactored code with moved methods.""",
                "guidelines": [
                    "Analyze method usage",
                    "Maintain class cohesion",
                    "Handle dependencies",
                    "Update interfaces",
                    "Ensure proper access",
                    "Preserve behavior"
                ]
            },

            PromptType.RF_RENAME: {
                "system_message": "You are a Python refactoring expert specializing in code renaming.",
                "template": """Rename identifiers for better clarity:

```python
{code}
```

Focus on:
1. Naming conventions
2. Code clarity
3. Semantic accuracy
4. Consistency
5. Context appropriateness
6. Domain terminology
7. Scope considerations
8. Documentation updates

Provide only the refactored code with renamed elements.""",
                "guidelines": [
                    "Use clear, descriptive names",
                    "Follow naming conventions",
                    "Maintain consistency",
                    "Consider context",
                    "Use domain terminology",
                    "Update related documentation"
                ]
            },

            PromptType.RF_ENCAPSULATE: {
                "system_message": "You are a Python refactoring expert specializing in encapsulation.",
                "template": """Improve encapsulation in this code:

```python
{code}
```

Focus on:
1. Data hiding
2. Access control
3. Property usage
4. Interface design
5. Validation logic
6. State management
7. Method exposure
8. Implementation hiding

Provide only the refactored code with improved encapsulation.""",
                "guidelines": [
                    "Hide implementation details",
                    "Use properties appropriately",
                    "Control access",
                    "Add validation",
                    "Design clean interfaces",
                    "Protect object state"
                ]
            },

            PromptType.RF_PULL_UP: {
                "system_message": "You are a Python refactoring expert specializing in inheritance refactoring.",
                "template": """Pull up common elements to superclass:

```python
{code}
```

Focus on:
1. Common functionality
2. Method signatures
3. Interface consistency
4. Inheritance hierarchy
5. Behavior preservation
6. Abstract methods
7. Template methods
8. Testing implications

Provide only the refactored code with pulled up elements.""",
                "guidelines": [
                    "Identify common elements",
                    "Maintain consistency",
                    "Preserve behavior",
                    "Consider abstraction",
                    "Update interfaces",
                    "Ensure proper inheritance"
                ]
            },

            PromptType.RF_PUSH_DOWN: {
                "system_message": "You are a Python refactoring expert specializing in inheritance optimization.",
                "template": """Push down specific elements to subclasses:

```python
{code}
```

Focus on:
1. Specific functionality
2. Inheritance structure
3. Method placement
4. Interface segregation
5. Dependency management
6. Code duplication
7. Implementation specifics
8. Testing strategy

Provide only the refactored code with pushed down elements.""",
                "guidelines": [
                    "Identify specific elements",
                    "Maintain hierarchy",
                    "Avoid duplication",
                    "Handle dependencies",
                    "Update interfaces",
                    "Consider testing impact"
                ]
            },

            PromptType.RF_TEMPLATE: {
                "system_message": "You are a Python refactoring expert specializing in template method pattern.",
                "template": """Apply template method pattern:

```python
{code}
```

Focus on:
1. Algorithm structure
2. Abstract steps
3. Hook methods
4. Default implementations
5. Method ordering
6. Extension points
7. Inheritance hierarchy
8. Testing approach

Provide only the refactored code using template method pattern.""",
                "guidelines": [
                    "Define algorithm structure",
                    "Identify abstract steps",
                    "Add hook methods",
                    "Provide defaults",
                    "Order methods logically",
                    "Consider extensibility"
                ]
            },

            PromptType.RF_ALGORITHM: {
                "system_message": "You are a Python refactoring expert specializing in algorithm substitution.",
                "template": """Substitute algorithm implementation:

```python
{code}
```

Focus on:
1. Algorithm selection
2. Performance characteristics
3. Memory usage
4. Edge cases
5. Input handling
6. Error scenarios
7. Implementation clarity
8. Testing requirements

Provide only the refactored code with the new algorithm.""",
                "guidelines": [
                    "Choose appropriate algorithm",
                    "Consider performance",
                    "Handle edge cases",
                    "Maintain clarity",
                    "Ensure robustness",
                    "Verify correctness"
                ]
            },

            # Rest of existing configs...
            PromptType.DOC_FUNCTION: {
                "system_message": "You are a Python documentation expert.",
                "template": """Add docstrings to all functions:
```python
{code}
```
Follow Google docstring format.""",
                "guidelines": ["Google Style", "Complete Parameters", "Return Types"]
            },

            PromptType.TEST_UNIT: {
                "system_message": "You are a Python testing expert.",
                "template": """Generate unit tests for:
```python
{code}
```
Use pytest and cover edge cases.""",
                "guidelines": ["Use pytest", "Test Edge Cases", "Mock Dependencies"]
            },

            PromptType.PERF_OPTIMIZE: {
                "system_message": "You are a Python performance expert.",
                "template": """Optimize this code:
```python
{code}
```
Focus on algorithmic efficiency.""",
                "guidelines": ["Optimize Algorithms", "Reduce Memory", "Cache Results"]
            },

            PromptType.SEC_AUDIT: {
                "system_message": "You are a Python security expert.",
                "template": """Audit this code for security:
```python
{code}
```
Fix any vulnerabilities found.""",
                "guidelines": ["Input Validation", "Access Control", "Data Protection"]
            },

            PromptType.TYPE_HINTS: {
                "system_message": "You are a Python type system expert.",
                "template": """Add type hints to:
```python
{code}
```
Use strict typing.""",
                "guidelines": ["Complete Coverage", "Use Generic Types", "Document Complex Types"]
            },

            PromptType.ARCH_PATTERN: {
                "system_message": "You are a software architecture expert.",
                "template": """Apply design patterns to:
```python
{code}
```
Focus on maintainability.""",
                "guidelines": ["Clean Architecture", "SOLID Principles", "Design Patterns"]
            },

            PromptType.QUAL_COMPLEX: {
                "system_message": "You are a code quality expert.",
                "template": """Reduce complexity in:
```python
{code}
```
Focus on maintainability.""",
                "guidelines": ["Reduce Nesting", "Extract Methods", "Simplify Logic"]
            },

            PromptType.STD_PEP8: {
                "system_message": "You are a Python standards expert.",
                "template": """Apply PEP 8 to:
```python
{code}
```
Fix style issues.""",
                "guidelines": ["Line Length", "Naming", "Whitespace", "Imports"]
            },

            # Default fallback
            "default": {
                "system_message": f"You are an expert Python developer specializing in {prompt_type.value}.",
                "template": f"""Process this Python code for {prompt_type.value}:
```python
{{code}}
```
Context: {{context}}
Provide only the processed code.""",
                "guidelines": [
                    "Follow Python best practices",
                    "Maintain code functionality",
                    "Ensure code quality"
                ]
            }
        }
        return configs.get(prompt_type, configs["default"])

    def _create_default_sequences(self) -> List[PromptSequence]:
        """Create default prompt sequences"""
        return [
            PromptSequence(
                name="basic_cleanup",
                description="Basic code cleanup sequence",
                prompts=[
                    PromptType.CI_IMPROVE,
                    PromptType.DOC_FUNCTION,
                    PromptType.TYPE_HINTS
                ]
            )
        ]

    async def execute_prompt(
            self,
            prompt_type: PromptType,
            code: str,
            context: str = ""
    ) -> str:
        """Execute a single prompt"""
        template = self.library.get_template(prompt_type.value)
        if not template:
            raise ValueError(f"No template found for prompt type: {prompt_type}")

        # Here you'd implement the actual prompt execution logic
        # For now, just return the template
        return f"Template: {template.name}"

    async def execute_sequence(
            self,
            sequence_name: str,
            code: str,
            context: str = ""
    ) -> List[str]:
        """Execute a sequence of prompts"""
        sequence = self.library.get_sequence(sequence_name)
        if not sequence:
            raise ValueError(f"No sequence found: {sequence_name}")

        results = []
        current_code = code

        for prompt_type in sequence.prompts:
            result = await self.execute_prompt(prompt_type, current_code, context)
            results.append(result)
            current_code = result  # Use result as input for next prompt

        sequence.use_count += 1
        self.library.save_sequence(sequence)

        return results
