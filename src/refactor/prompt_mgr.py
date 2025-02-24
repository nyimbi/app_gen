import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import (AsyncGenerator, Callable, Dict, List, Optional, Set, Tuple,
                    Union)


class PromptType(Enum):
    """Types of code-related generation and improvement prompts"""

    # Code Generation & Improvement
    IMPROVEMENT = "improvement"
    REFACTOR = "refactor"
    CLEAN_CODE = "clean_code"
    BEST_PRACTICES = "best_practices"
    CODE_GENERATION = "code_generation"
    BOILERPLATE = "boilerplate"
    SCAFFOLDING = "scaffolding"
    MODERNIZATION = "modernization"
    MIGRATION = "migration"
    UPGRADE = "upgrade"

    # Code Refactoring
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    INLINE_METHOD = "inline_method"
    MOVE_METHOD = "move_method"
    RENAME_SYMBOL = "rename_symbol"
    ENCAPSULATE_FIELD = "encapsulate_field"
    PULL_UP = "pull_up"
    PUSH_DOWN = "push_down"
    FORM_TEMPLATE_METHOD = "form_template_method"
    SUBSTITUTE_ALGORITHM = "substitute_algorithm"

    # Advanced Patterns
    FACTORY_METHOD = "factory_method"
    ABSTRACT_FACTORY = "abstract_factory"
    BUILDER = "builder"
    SINGLETON = "singleton"
    ADAPTER = "adapter"
    BRIDGE = "bridge"
    COMPOSITE = "composite"
    DECORATOR = "decorator"
    FACADE = "facade"
    PROXY = "proxy"

    # Documentation
    DOCSTRING = "docstring"
    INLINE_COMMENTS = "inline_comments"
    MODULE_DOCS = "module_docs"
    API_DOCS = "api_docs"
    ARCHITECTURE_DOCS = "architecture_docs"
    DEPLOYMENT_DOCS = "deployment_docs"
    TUTORIAL = "tutorial"
    EXAMPLES = "examples"

    # Testing
    TEST = "test"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    E2E_TEST = "e2e_test"
    PROPERTY_TEST = "property_test"
    FUZZ_TEST = "fuzz_test"
    MUTATION_TEST = "mutation_test"
    LOAD_TEST = "load_test"
    STRESS_TEST = "stress_test"
    SECURITY_TEST = "security_test"

    # Debugging & Analysis
    DEBUG = "debug"
    TRACE = "trace"
    PROFILING = "profiling"
    MEMORY_ANALYSIS = "memory_analysis"
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_ANALYSIS = "dynamic_analysis"
    LEAK_DETECTION = "leak_detection"
    RACE_DETECTION = "race_detection"
    DEADLOCK_DETECTION = "deadlock_detection"

    # Performance
    OPTIMIZATION = "optimization"
    ALGORITHM = "algorithm"
    MEMORY_OPTIMIZATION = "memory_optimization"
    CPU_OPTIMIZATION = "cpu_optimization"
    IO_OPTIMIZATION = "io_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    PARALLELIZATION = "parallelization"
    DISTRIBUTED = "distributed"
    ASYNC_OPTIMIZATION = "async_optimization"
    BATCH_PROCESSING = "batch_processing"

    # Security
    SECURITY = "security"
    VULNERABILITY_CHECK = "vulnerability_check"
    CODE_INJECTION = "code_injection"
    INPUT_VALIDATION = "input_validation"
    AUTH_SECURITY = "auth_security"
    CRYPTO_AUDIT = "crypto_audit"
    SECRETS_SCAN = "secrets_scan"
    PERMISSION_CHECK = "permission_check"
    SANITIZATION = "sanitization"

    # Types
    TYPE_HINTS = "type_hints"
    TYPE_CHECKING = "type_checking"
    RUNTIME_TYPES = "runtime_types"
    GENERIC_TYPES = "generic_types"
    PROTOCOL_TYPES = "protocol_types"
    STRUCTURAL_TYPES = "structural_types"
    GRADUAL_TYPING = "gradual_typing"
    TYPE_INFERENCE = "type_inference"

    # Architecture
    DESIGN_PATTERNS = "design_patterns"
    SOLID = "solid_principles"
    CLEAN_ARCHITECTURE = "clean_architecture"
    MICROSERVICES = "microservices"
    EVENT_DRIVEN = "event_driven"
    DOMAIN_DRIVEN = "domain_driven"
    SERVICE_MESH = "service_mesh"
    API_DESIGN = "api_design"
    DATABASE_DESIGN = "database_design"

    # Code Quality
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    CODE_SMELL = "code_smell"
    TECH_DEBT = "tech_debt"
    COHESION = "cohesion"
    COUPLING = "coupling"
    MODULARITY = "modularity"

    # Standards & Conventions
    PEP8 = "pep8"
    TYPING_PEP = "typing_pep"
    IMPORT_SORTING = "import_sorting"
    DOCSTRING_STYLE = "docstring_style"
    NAMING_CONVENTION = "naming_convention"
    LOGGING_STANDARD = "logging_standard"
    ERROR_HANDLING = "error_handling"
    CONFIGURATION = "configuration"


@dataclass
class PromptTemplate:
    """Template for AI code generation and improvement prompts with context and examples"""

    # Core components
    system_message: str
    template: str
    examples: List[Dict[str, str]] = field(default_factory=list)
    guidelines: List[str] = field(default_factory=list)

    # Additional metadata
    version: str = field(default="1.0")
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: Optional[datetime] = field(default=None)
    author: Optional[str] = field(default=None)
    tags: Set[str] = field(default_factory=set)

    # Template configuration
    max_examples: int = field(default=5)
    min_guidelines: int = field(default=1)
    allow_variables: bool = field(default=True)
    supported_formats: Set[str] = field(default_factory=lambda: {"markdown", "plain"})

    # Validation rules
    required_placeholders: Set[str] = field(default_factory=set)
    max_length: Optional[int] = field(default=None)
    min_length: Optional[int] = field(default=None)

    # Usage tracking
    use_count: int = field(default=0)
    success_rate: float = field(default=0.0)
    avg_response_time: float = field(default=0.0)
    last_used: Optional[datetime] = field(default=None)

    def validate(self) -> bool:
        """Validate template configuration"""
        if not self.system_message or not self.template:
            return False
        if len(self.examples) > self.max_examples:
            return False
        if len(self.guidelines) < self.min_guidelines:
            return False
        if self.max_length and len(self.template) > self.max_length:
            return False
        if self.min_length and len(self.template) < self.min_length:
            return False
        return True

    def add_example(self, example: Dict[str, str]) -> None:
        """Add an example if within limits"""
        if len(self.examples) < self.max_examples:
            self.examples.append(example)
            self.modified_at = datetime.now()

    def add_guideline(self, guideline: str) -> None:
        """Add a guideline"""
        if guideline not in self.guidelines:
            self.guidelines.append(guideline)
            self.modified_at = datetime.now()

    def record_usage(self, success: bool, response_time: float) -> None:
        """Record template usage statistics"""
        self.use_count += 1
        self.last_used = datetime.now()
        self.success_rate = (
            (self.success_rate * (self.use_count - 1)) + (1 if success else 0)
        ) / self.use_count
        self.avg_response_time = (
            (self.avg_response_time * (self.use_count - 1)) + response_time
        ) / self.use_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "system_message": self.system_message,
            "template": self.template,
            "examples": self.examples,
            "guidelines": self.guidelines,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "author": self.author,
            "tags": list(self.tags),
            "use_count": self.use_count,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time,
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Create template from dictionary"""
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data["modified_at"]:
            data["modified_at"] = datetime.fromisoformat(data["modified_at"])
        if data["last_used"]:
            data["last_used"] = datetime.fromisoformat(data["last_used"])
        data["tags"] = set(data["tags"])
        return cls(**data)


class PromptManager:
    """Manages prompt templates and generation for different code operations"""

    def __init__(self):
        self.templates: Dict[PromptType, PromptTemplate] = self._initialize_templates()

    def _initialize_templates(self) -> Dict[PromptType, PromptTemplate]:
        """Initialize all prompt templates"""
        templates = {}

        # Code Improvement Prompts
        templates[PromptType.IMPROVEMENT] = PromptTemplate(
            system_message="You are an expert Python code reviewer with deep knowledge of clean code principles.",
            template="""Analyze and improve this Python code:

Context:
{context}

Current Code:
```python
{code}
```

Focus on:
1. Code clarity and readability
2. Error handling and robustness
3. Performance optimization opportunities
4. Python idioms and best practices
5. Type safety and annotations

Provide only the improved code without explanations.""",
            guidelines=[
                "Use descriptive variable names",
                "Follow PEP 8 style guidelines",
                "Add proper error handling",
                "Include type hints",
                "Use context managers where appropriate",
            ],
        )

        templates[PromptType.REFACTOR] = PromptTemplate(
            system_message="You are a Python refactoring expert focused on code structure.",
            template="""Refactor this Python code to improve its structure:

```python
{code}
```

Apply these refactoring principles:
1. Single Responsibility Principle
2. Don't Repeat Yourself (DRY)
3. Dependency Injection
4. Interface Segregation
5. Composition over Inheritance

Provide the refactored code only.""",
        )

        templates[PromptType.CLEAN_CODE] = PromptTemplate(
            system_message="You are a clean code expert focused on code clarity.",
            template="""Clean up this code following clean code principles:

```python
{code}
```

Focus on:
1. Clear naming
2. Small functions
3. Code organization
4. Removing duplication
5. Simplifying logic

Return only the cleaned code.""",
        )

        templates[PromptType.BEST_PRACTICES] = PromptTemplate(
            system_message="You are a Python best practices expert.",
            template="""Apply Python best practices to this code:

```python
{code}
```

Focus on:
1. Pythonic idioms
2. Standard library usage
3. Performance patterns
4. Error handling
5. Code organization

Return only the updated code.""",
        )

        # Documentation Prompts
        templates[PromptType.DOCSTRING] = PromptTemplate(
            system_message="You are a technical documentation expert.",
            template="""Generate comprehensive docstrings for this code:

```python
{code}
```

Requirements:
1. Follow Google docstring format
2. Include type hints
3. Document parameters, returns, raises
4. Add usage examples
5. Note any important caveats

Provide the code with added docstrings only.""",
        )

        templates[PromptType.INLINE_COMMENTS] = PromptTemplate(
            system_message="You are a code documentation expert.",
            template="""Add clear inline comments to this code:

```python
{code}
```

Add comments explaining:
1. Complex logic
2. Important caveats
3. Key variables
4. Logic flow
5. Edge cases

Return the code with added comments.""",
        )

        templates[PromptType.MODULE_DOCS] = PromptTemplate(
            system_message="You are a module documentation expert.",
            template="""Generate module-level documentation:

```python
{code}
```

Include:
1. Module overview
2. Usage examples
3. Key classes/functions
4. Dependencies
5. Configuration

Return the documented module.""",
        )

        templates[PromptType.API_DOCS] = PromptTemplate(
            system_message="You are an API documentation expert.",
            template="""Generate API documentation:

```python
{code}
```

Document:
1. Public interfaces
2. Parameters
3. Return values
4. Examples
5. Error cases

Return the API documentation.""",
        )

        # Testing Prompts
        templates[PromptType.TEST] = PromptTemplate(
            system_message="You are a Python testing expert.",
            template="""Generate tests for this code:

```python
{code}
```

Create tests for:
1. Main functionality
2. Edge cases
3. Error handling
4. Performance cases
5. Integration points

Return only the test code.""",
        )

        templates[PromptType.UNIT_TEST] = PromptTemplate(
            system_message="You are a unit testing expert.",
            template="""Generate unit tests for this code:

```python
{code}
```

Test:
1. Individual functions
2. Input validation
3. Return values
4. Exceptions
5. Edge cases

Return only the unit tests.""",
        )

        templates[PromptType.INTEGRATION_TEST] = PromptTemplate(
            system_message="You are an integration testing expert.",
            template="""Create integration tests:

```python
{code}
```

Test:
1. Component interactions
2. Data flow
3. Error handling
4. System states
5. Performance

Return only the tests.""",
        )

        templates[PromptType.E2E_TEST] = PromptTemplate(
            system_message="You are an end-to-end testing expert.",
            template="""Generate E2E tests for:

```python
{code}
```

Test:
1. User workflows
2. System integration
3. Data persistence
4. Error recovery
5. Performance

Return the E2E tests.""",
        )

        templates[PromptType.PROPERTY_TEST] = PromptTemplate(
            system_message="You are a property-based testing expert.",
            template="""Create property-based tests:

```python
{code}
```

Test properties:
1. Invariants
2. State transitions
3. Reversible operations
4. Data transformations
5. Boundary conditions

Return the property tests.""",
        )

        # Debugging Prompts
        templates[PromptType.DEBUG] = PromptTemplate(
            system_message="You are a Python debugging expert.",
            template="""Debug this code:

```python
{code}
```

Look for:
1. Logic errors
2. Edge cases
3. Resource leaks
4. Race conditions
5. Error handling

Return the fixed code.""",
        )

        templates[PromptType.TRACE] = PromptTemplate(
            system_message="You are a code tracing expert.",
            template="""Add tracing to this code:

```python
{code}
```

Add:
1. Logging points
2. Performance metrics
3. State tracking
4. Error capture
5. Debug info

Return the traced code.""",
        )

        templates[PromptType.PROFILING] = PromptTemplate(
            system_message="You are a code profiling expert.",
            template="""Add profiling to this code:

```python
{code}
```

Profile:
1. Execution time
2. Memory usage
3. Function calls
4. I/O operations
5. Resource usage

Return the profiled code.""",
        )

        templates[PromptType.MEMORY_ANALYSIS] = PromptTemplate(
            system_message="You are a memory analysis expert.",
            template="""Analyze memory usage:

```python
{code}
```

Check:
1. Memory leaks
2. Object lifecycle
3. Resource cleanup
4. Cache usage
5. Memory patterns

Return the analysis.""",
        )

        # Performance Prompts
        templates[PromptType.OPTIMIZATION] = PromptTemplate(
            system_message="You are a code optimization expert.",
            template="""Optimize this code:

```python
{code}
```

Focus on:
1. Algorithm efficiency
2. Data structures
3. Resource usage
4. Caching
5. Parallelization

Return the optimized code.""",
        )

        templates[PromptType.ALGORITHM] = PromptTemplate(
            system_message="You are an algorithmic optimization expert.",
            template="""Optimize algorithms in:

```python
{code}
```

Improve:
1. Time complexity
2. Space complexity
3. Resource usage
4. Scalability
5. Maintainability

Return optimized code.""",
        )

        templates[PromptType.MEMORY_OPTIMIZATION] = PromptTemplate(
            system_message="You are a memory optimization expert.",
            template="""Optimize memory usage:

```python
{code}
```

Focus on:
1. Memory allocation
2. Object lifecycle
3. Cache efficiency
4. Resource pooling
5. Memory patterns

Return optimized code.""",
        )

        templates[PromptType.CPU_OPTIMIZATION] = PromptTemplate(
            system_message="You are a CPU optimization expert.",
            template="""Optimize CPU usage:

```python
{code}
```

Improve:
1. Computation efficiency
2. Thread usage
3. Process allocation
4. Task scheduling
5. Resource sharing

Return optimized code.""",
        )

        templates[PromptType.IO_OPTIMIZATION] = PromptTemplate(
            system_message="You are an I/O optimization expert.",
            template="""Optimize I/O operations:

```python
{code}
```

Improve:
1. File operations
2. Network calls
3. Database queries
4. Cache usage
5. Resource pooling

Return optimized code.""",
        )

        # Security Prompts
        templates[PromptType.SECURITY] = PromptTemplate(
            system_message="You are a security expert.",
            template="""Secure this code:

```python
{code}
```

Check:
1. Input validation
2. Authentication
3. Authorization
4. Data protection
5. Error handling

Return secured code.""",
        )

        templates[PromptType.VULNERABILITY_CHECK] = PromptTemplate(
            system_message="You are a vulnerability detection expert.",
            template="""Check for vulnerabilities:

```python
{code}
```

Look for:
1. Injection flaws
2. Authentication gaps
3. Data exposure
4. Security misconfigs
5. API vulnerabilities

Return secure code.""",
        )

        templates[PromptType.CODE_INJECTION] = PromptTemplate(
            system_message="You are a code injection security expert.",
            template="""Prevent code injection:

```python
{code}
```

Secure against:
1. SQL injection
2. Command injection
3. XSS
4. CSRF
5. Path traversal

Return secured code.""",
        )

        templates[PromptType.INPUT_VALIDATION] = PromptTemplate(
            system_message="You are an input validation expert.",
            template="""Add input validation:

```python
{code}
```

Validate:
1. Data types
2. Value ranges
3. Format patterns
4. Size limits
5. Content safety

Return validated code.""",
        )

        # Type System Prompts
        templates[PromptType.TYPE_HINTS] = PromptTemplate(
            system_message="You are a Python type system expert.",
            template="""Add type hints to:

```python
{code}
```

Add:
1. Function annotations
2. Variable types
3. Return types
4. Generic types
5. Type aliases

Return typed code.""",
        )

        templates[PromptType.TYPE_CHECKING] = PromptTemplate(
            system_message="You are a type checking expert.",
            template="""Add type checking:

```python
{code}
```

Check:
1. Type consistency
2. Optional types
3. Union types
4. Generic types
5. Protocol conformance

Return type-checked code.""",
        )

        templates[PromptType.RUNTIME_TYPES] = PromptTemplate(
            system_message="You are a runtime typing expert.",
            template="""Add runtime type checking:

```python
{code}
```

Add:
1. Type assertions
2. Runtime checks
3. Type guards
4. Conversion logic
5. Validation code

Return type-safe code.""",
        )

        templates[PromptType.GENERIC_TYPES] = PromptTemplate(
            system_message="You are a generic typing expert.",
            template="""Add generic types:

```python
{code}
```

Add:
1. Type variables
2. Bounded types
3. Variance annotations
4. Protocol classes
5. Type constraints

Return generic code.""",
        )

        # Architecture Prompts
        templates[PromptType.DESIGN_PATTERNS] = PromptTemplate(
            system_message="You are a design patterns expert.",
            template="""Apply design patterns:

```python
{code}
```

Consider:
1. Creational patterns
2. Structural patterns
3. Behavioral patterns
4. Concurrency patterns
5. Architecture patterns

Return pattern-based code.""",
        )

        templates[PromptType.SOLID] = PromptTemplate(
            system_message="You are a SOLID principles expert.",
            template="""Apply SOLID principles:

```python
{code}
```

Apply:
1. Single Responsibility
2. Open-Closed
3. Liskov Substitution
4. Interface Segregation
5. Dependency Inversion

Return SOLID code.""",
        )

        templates[PromptType.CLEAN_ARCHITECTURE] = PromptTemplate(
            system_message="You are a clean architecture expert.",
            template="""Apply clean architecture:

```python
{code}
```

Structure:
1. Entity layer
2. Use case layer
3. Interface layer
4. Framework layer
5. Dependencies

Return clean architecture.""",
        )

        # Code Quality Prompts
        templates[PromptType.COMPLEXITY] = PromptTemplate(
            system_message="You are a code complexity expert.",
            template="""Reduce complexity in:

```python
{code}
```

Reduce:
1. Cyclomatic complexity
2. Cognitive complexity
3. Structural complexity
4. Data complexity
5. Interface complexity

Return simplified code.""",
        )

        templates[PromptType.MAINTAINABILITY] = PromptTemplate(
            system_message="You are a code maintainability expert.",
            template="""Improve maintainability:

```python
{code}
```

Improve:
1. Code organization
2. Documentation
3. Testing
4. Error handling
5. Configuration

Return maintainable code.""",
        )

        templates[PromptType.READABILITY] = PromptTemplate(
            system_message="You are a code readability expert.",
            template="""Improve readability:

```python
{code}
```

Improve:
1. Naming
2. Formatting
3. Comments
4. Structure
5. Flow

Return readable code.""",
        )

        templates[PromptType.CODE_SMELL] = PromptTemplate(
            system_message="You are a code smell detection expert.",
            template="""Fix code smells in:

```python
{code}
```

Fix:
1. Duplicated code
2. Long methods
3. Large classes
4. Long parameter lists
5. Divergent change

Return clean code.""",
        )

        # Standards Prompts
        templates[PromptType.PEP8] = PromptTemplate(
            system_message="You are a PEP 8 expert.",
            template="""Apply PEP 8 to:

```python
{code}
```

Fix:
1. Naming conventions
2. Code layout
3. Whitespace usage
4. Import organization
5. Code style

Return PEP 8 compliant code.""",
        )

        templates[PromptType.TYPING_PEP] = PromptTemplate(
            system_message="You are a typing PEP expert.",
            template="""Apply typing PEPs:

```python
{code}
```

Apply:
1. PEP 484 type hints
2. PEP 526 variable annotations
3. PEP 544 protocols
4. PEP 585 type hinting
5. PEP 593 flexible types

Return typing-compliant code.""",
        )

        templates[PromptType.IMPORT_SORTING] = PromptTemplate(
            system_message="You are an import organization expert.",
            template="""Organize imports in:

```python
{code}
```

Sort:
1. Standard library
2. Third-party
3. Local imports
4. Import order
5. Import style

Return organized imports.""",
        )

        templates[PromptType.DOCSTRING_STYLE] = PromptTemplate(
            system_message="You are a docstring style expert.",
            template="""Apply docstring style:

```python
{code}
```

Format:
1. Module docstrings
2. Class docstrings
3. Function docstrings
4. Variable docstrings
5. Package docstrings

Return styled docstrings.""",
        )

        return templates

    def get_prompt(
        self, prompt_type: PromptType, code: str, context: str = ""
    ) -> Tuple[str, str]:
        """Get system message and prompt for given type"""
        if prompt_type not in self.templates:
            raise ValueError(f"No template found for prompt type: {prompt_type}")

        template = self.templates[prompt_type]
        prompt = template.template.format(code=code, context=context)

        return template.system_message, prompt
