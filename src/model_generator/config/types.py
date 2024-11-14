"""
Author: Nyimbi Odero
Copyright: 2024
License: MIT

types.py: Comprehensive Configuration System for Flask-AppBuilder Code Generation

This module implements a robust, type-safe configuration system for the Flask-AppBuilder
code generator, providing structured configuration management with validation,
serialization, and extensive customization options.

Key Components:
    1. Enumerations
        - OutputStyle: Code generation output format options
        - RelationshipType: Database relationship types
        - AuthenticationType: Authentication method options
        - DocstringStyle: Documentation style options

    2. Core Configurations
        - DatabaseConfig: Database connection and schema settings
        - GenerationConfig: Code generation preferences
        - SecurityConfig: Security and authentication settings
        - APIConfig: REST API configuration
        - RelationshipsConfig: Database relationship management
        - LoggingConfig: Logging system configuration

    3. Model and View Configurations
        - ModelConfig: Individual model customization
        - ViewConfig: View generation settings

    4. Validation and Processing
        - ValidationMixin: Base validation functionality
        - Type conversion utilities
        - Configuration validation rules

Detailed Class Documentation:

OutputStyle (Enum):
    Defines supported code output formats.
    Values:
        - SINGLE_FILE: All code in one file
        - MULTIPLE_FILES: Separate files for models/views
        - MODULAR: Full package structure
        - PACKAGE: Complete installable package
    Methods:
        - is_valid(value: str) -> bool: Validates output style
        - from_string(value: str) -> OutputStyle: Creates enum from string

RelationshipType (Enum):
    Defines database relationship types.
    Values:
        - ONE_TO_ONE: One-to-one relationships
        - ONE_TO_MANY: One-to-many relationships
        - MANY_TO_ONE: Many-to-one relationships
        - MANY_TO_MANY: Many-to-many relationships
    Methods:
        - is_valid(value: str) -> bool: Validates relationship type
        - from_string(value: str) -> RelationshipType: Creates enum from string

AuthenticationType (Enum):
    Defines authentication methods.
    Values:
        - JWT: JSON Web Token authentication
        - SESSION: Session-based authentication
        - BASIC: Basic HTTP authentication
        - OAUTH: OAuth2 authentication
        - NONE: No authentication
    Methods:
        - is_valid(value: str) -> bool: Validates authentication type

DocstringStyle (Enum):
    Defines documentation styles.
    Values:
        - GOOGLE: Google style docstrings
        - SPHINX: Sphinx style docstrings
        - NUMPY: NumPy style docstrings
        - EPYTEXT: Epytext style docstrings
    Methods:
        - is_valid(value: str) -> bool: Validates docstring style

ValidationMixin (Class):
    Base class providing validation functionality.
    Methods:
        - validate() -> List[str]: Base validation method
        - validate_field(): Validates individual fields

ModelConfig (Class):
    Configuration for individual database models.
    Attributes:
        - table_name: Database table name
        - class_name: Generated Python class name
        - base_classes: Additional base classes
        - mixins: Mixin classes
        - validators: Field validators
        - widgets: Form widgets
        - excluded_columns: Columns to exclude
        - custom_methods: Additional methods
        - doc_string: Custom documentation
        - primary_key: Primary key configuration
        - indexes: Index definitions
        - unique_constraints: Unique constraints
        - relationships: Relationship definitions
    Methods:
        - validate(): Validates configuration
        - get_class_name(): Generates Python class name

ViewConfig (Class):
    Configuration for view generation.
    Attributes:
        - model_name: Associated model name
        - view_type: View class type
        - endpoints: Custom endpoints
        - permissions: Permission settings
        - templates: Custom templates
        - widgets: Form widgets
        - excluded_fields: Excluded fields
        - search_columns: Searchable columns
        - list_columns: List view columns
        - form_columns: Form fields
        - show_columns: Detail view fields
        - add_columns: Add form fields
        - edit_columns: Edit form fields
        - description_columns: Field descriptions
        - label_columns: Custom labels
        - order_columns: Sortable columns
        - base_permissions: Default permissions
    Methods:
        - validate(): Validates configuration
        - get_view_name(): Generates view class name
        - merge_column_configs(): Combines column settings

DatabaseConfig (Class):
    Comprehensive database connection and schema configuration.
    Attributes:
        - uri: Database connection string
        - schema: Database schema name
        - exclude_tables: Tables to exclude
        - include_tables: Tables to include
        - custom_type_mappings: Custom type conversions
        - connection_pool_size: Connection pool size
        - connection_timeout: Connection timeout
        - enable_ssl: SSL connection flag
        - ssl_ca_cert: SSL certificate path
        - schema_version: Schema version
        - migration_dir: Migration directory
        - auto_pluralize: Table name pluralization
        - column_name_case: Column naming style
        - lazy_loading: Loading strategy
        - batch_size: Query batch size
    Methods:
        - validate(): Validates database settings
    Usage:
        >>> config = DatabaseConfig(
        ...     uri='postgresql://user:pass@localhost/db',
        ...     schema='public',
        ...     connection_pool_size=10
        ... )

GenerationConfig (Class):
    Code generation settings and preferences.
    Attributes:
        - output_dir: Output directory
        - output_style: Code organization style
        - indent_size: Code indentation
        - template_dir: Template directory
        - include_views: View generation flag
        - include_procedures: Procedure generation
        - backup_existing: Backup existing files
        - timestamp_files: Add timestamps
        - line_length: Maximum line length
        - docstring_style: Documentation style
        - type_hints: Include type hints
        - generate_tests: Generate unit tests
        - generate_docs: Generate documentation
        - file_header: Custom file headers
        - import_style: Import organization
        - class_template: Class templates
    Methods:
        - validate(): Validates generation settings
        - get_template_path(): Resolves template paths
        - get_output_path(): Generates output paths
    Usage:
        >>> config = GenerationConfig(
        ...     output_dir=Path('./generated'),
        ...     output_style=OutputStyle.MODULAR,
        ...     generate_tests=True
        ... )

APIConfig (Class):
    REST API generation configuration.
    Attributes:
        - enable_api: API generation flag
        - version: API version
        - prefix: URL prefix
        - authentication: Auth method
        - allowed_methods: HTTP methods
        - rate_limiting: Rate limit flag
        - documentation: API docs generation
        - cors_enabled: CORS support
        - security_schemes: Security definitions
        - response_formats: Response formats
        - error_responses: Error templates
        - versioning: Version strategy
        - pagination: Pagination settings
    Methods:
        - validate(): Validates API configuration
        - get_security_scheme(): Gets security config
        - get_error_response(): Gets error template
    Usage:
        >>> config = APIConfig(
        ...     enable_api=True,
        ...     version='v1',
        ...     authentication=AuthenticationType.JWT
        ... )

SecurityConfig (Class):
    Security and authentication configuration.
    Attributes:
        - enable_permissions: Permission system flag
        - sensitive_fields: Sensitive data fields
        - password_fields: Password fields
        - role_model: Role model name
        - user_model: User model name
        - permission_model: Permission model
        - hash_method: Password hashing
        - salt_length: Salt length
        - token_lifetime: Token expiration
        - require_2fa: 2FA requirement
        - audit_logging: Audit log flag
        - max_login_attempts: Login attempts
        - lockout_duration: Lockout period
        - password_policy: Password rules
        - csrf_protection: CSRF settings
        - session_config: Session settings
        - oauth_providers: OAuth configs
    Methods:
        - validate(): Validates security settings
        - get_password_validator(): Creates validator
    Usage:
        >>> config = SecurityConfig(
        ...     enable_permissions=True,
        ...     require_2fa=True,
        ...     max_login_attempts=3
        ... )

RelationshipsConfig (Class):
    Database relationship configuration.
    Attributes:
        - auto_detect: Auto-detection flag
        - manual_relationships: Manual definitions
        - handle_circular_dependencies: Circular refs
        - use_backref: Backref usage
        - lazy_loading: Loading strategy
        - cascade_deletions: Cascade delete
        - relationship_naming_template: Name template
        - secondary_table_template: M2M table names
        - backref_naming: Backref templates
        - relationship_defaults: Default settings
        - association_tables: M2M definitions
        - polymorphic_config: Polymorphic settings
    Methods:
        - validate(): Validates relationships
        - get_relationship_name(): Generates names
        - get_backref_name(): Generates backrefs
        - get_association_table_name(): M2M names
    Usage:
        >>> config = RelationshipsConfig(
        ...     auto_detect=True,
        ...     use_backref=True,
        ...     lazy_loading='select'
        ... )

LoggingConfig (Class):
    Logging system configuration and management.
    Attributes:
        - enabled: Logging enabled flag
        - level: Log level (DEBUG, INFO, etc.)
        - format: Log message format
        - file: Log file path
        - rotate: Log rotation flag
        - max_size: Maximum file size
        - backup_count: Backup file count
        - console_output: Console logging flag
    Methods:
        - validate(): Validates logging settings
    Usage:
        >>> config = LoggingConfig(
        ...     enabled=True,
        ...     level='INFO',
        ...     file=Path('./logs/generator.log')
        ... )

GeneratorConfig (Class):
    Master configuration class orchestrating all aspects of code generation.
    Attributes:
        - database: Database configuration
        - generation: Generation settings
        - relationships: Relationship config
        - security: Security settings
        - models: Model configurations
        - views: View configurations
        - api: API settings
        - logging: Logging config
        - metadata: Project metadata
        - templates: Custom templates
        - hooks: Generation hooks
        - extensions: Custom extensions
    Methods:
        Core Methods:
            - validate(): Validates entire configuration
            - to_dict(): Serializes to dictionary
            - from_dict(): Creates from dictionary
            - __post_init__(): Post-initialization setup

        Utility Methods:
            - get_model_config(): Retrieves model config
            - get_view_config(): Retrieves view config
            - is_table_excluded(): Checks table exclusion
            - register_hook(): Registers generation hook
            - run_hooks(): Executes registered hooks
            - _setup_logging(): Configures logging

    Hook Points:
        - pre_generation: Before code generation
        - post_model_generation: After each model
        - post_view_generation: After each view
        - post_generation: After all generation
        - pre_validation: Before validation
        - post_validation: After validation

    Usage Example:
        >>> config = GeneratorConfig(
        ...     database=DatabaseConfig(uri='postgresql://localhost/db'),
        ...     generation=GenerationConfig(output_dir=Path('./output')),
        ...     relationships=RelationshipsConfig(),
        ...     security=SecurityConfig(),
        ...     api=APIConfig(enable_api=True),
        ...     logging=LoggingConfig(enabled=True)
        ... )
        >>>
        >>> # Validate configuration
        >>> errors = config.validate()
        >>> if not errors:
        ...     # Register hooks
        ...     config.register_hook('post_generation', lambda ctx: print('Done!'))
        ...
        ...     # Convert to dictionary
        ...     config_dict = config.to_dict()
        ...
        ...     # Create from dictionary
        ...     new_config = GeneratorConfig.from_dict(config_dict)

Type Definitions:
    ModelType:
        Union type for model references.
        Type: Union[Type['Model'], str]
        Usage: For model class references or names

    WidgetType:
        Union type for form widgets.
        Type: Union[Type[FormWidget], str]
        Usage: For form field widget definitions

    ValidatorType:
        Union type for field validators.
        Type: Union[Type[wtforms.validators.ValidationError], str]
        Usage: For field validation rules

    CustomValidator:
        Type alias for custom validators.
        Type: Callable[[Any], bool]
        Usage: For custom validation functions

    HookCallback:
        Type alias for generation hooks.
        Type: Callable[[Dict[str, Any]], None]
        Usage: For hook function definitions

Integration Guidelines:
    1. Configuration Creation:
        - Create individual configurations first
        - Combine into GeneratorConfig
        - Validate before use

    2. Hook Registration:
        - Register hooks early
        - Use type-safe callbacks
        - Handle hook exceptions

    3. Custom Extensions:
        - Add to extensions dict
        - Follow naming conventions
        - Provide documentation

    4. Validation:
        - Validate complete configuration
        - Handle validation errors
        - Log validation issues

Best Practices:
    1. Configuration:
        - Use type hints consistently
        - Validate early and often
        - Keep configurations immutable
        - Use proper error handling

    2. Extension:
        - Subclass for custom configs
        - Add validation rules
        - Document extensions
        - Use type checking

    3. Integration:
        - Use dependency injection
        - Handle all errors
        - Log operations
        - Follow conventions

Error Handling:
    - ValidationError: Configuration validation
    - ValueError: Invalid values
    - TypeError: Type mismatches
    - IOError: File operations
    - ImportError: Module imports

See Also:
    - Flask-AppBuilder documentation
    - SQLAlchemy relationship documentation
    - WTForms validation documentation
    - Python dataclasses documentation

Notes:
    - All paths are handled as Path objects
    - Validation is strict by default
    - Hooks must handle their own exceptions
    - Templates support Jinja2 syntax
    - Configuration is serializable

"""

from dataclasses import dataclass, field, asdict, fields
from typing import (
    List, Dict, Optional, Union, Type, Any, Set, Callable,
    TypeVar, Generic, Tuple
)
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta
import importlib
import re
import logging
from wtforms import widgets, FormWidget
import wtforms.validators

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar('T')

class OutputStyle(Enum):
    """
    Enumeration of supported code output styles.

    Attributes:
        SINGLE_FILE: Generate all code in a single file
        MULTIPLE_FILES: Split code across multiple files
        MODULAR: Generate a modular package structure
        PACKAGE: Generate a complete package with setup.py
    """
    SINGLE_FILE = 'single_file'
    MULTIPLE_FILES = 'multiple_files'
    MODULAR = 'modular'
    PACKAGE = 'package'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Validate if a value is a valid output style."""
        return value in [item.value for item in cls]

    @classmethod
    def from_string(cls, value: str) -> 'OutputStyle':
        """Create an OutputStyle from string."""
        if not cls.is_valid(value):
            raise ValueError(f"Invalid output style: {value}")
        return cls(value)

class RelationshipType(Enum):
    """
    Enumeration of supported relationship types.

    Attributes:
        ONE_TO_ONE: One-to-one relationship
        ONE_TO_MANY: One-to-many relationship
        MANY_TO_ONE: Many-to-one relationship
        MANY_TO_MANY: Many-to-many relationship
    """
    ONE_TO_ONE = 'one_to_one'
    ONE_TO_MANY = 'one_to_many'
    MANY_TO_ONE = 'many_to_one'
    MANY_TO_MANY = 'many_to_many'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Validate if a value is a valid relationship type."""
        return value in [item.value for item in cls]

    @classmethod
    def from_string(cls, value: str) -> 'RelationshipType':
        """Create a RelationshipType from string."""
        if not cls.is_valid(value):
            raise ValueError(f"Invalid relationship type: {value}")
        return cls(value)

class AuthenticationType(Enum):
    """
    Enumeration of supported authentication types.

    Attributes:
        JWT: JSON Web Token authentication
        SESSION: Session-based authentication
        BASIC: Basic authentication
        OAUTH: OAuth2 authentication
        NONE: No authentication
    """
    JWT = 'jwt'
    SESSION = 'session'
    BASIC = 'basic'
    OAUTH = 'oauth'
    NONE = 'none'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Validate if a value is a valid authentication type."""
        return value in [item.value for item in cls]

class DocstringStyle(Enum):
    """
    Enumeration of supported docstring styles.

    Attributes:
        GOOGLE: Google style docstrings
        SPHINX: Sphinx style docstrings
        NUMPY: NumPy style docstrings
        EPYTEXT: Epytext style docstrings
    """
    GOOGLE = 'google'
    SPHINX = 'sphinx'
    NUMPY = 'numpy'
    EPYTEXT = 'epytext'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Validate if a value is a valid docstring style."""
        return value in [item.value for item in cls]

@dataclass
class ValidationMixin:
    """Mixin class providing validation functionality."""

    def validate(self) -> List[str]:
        """
        Validate the configuration.

        Returns:
            List[str]: List of validation errors
        """
        return []

    def validate_field(self, field: str, value: Any,
                      validators: List[Callable[[Any], bool]],
                      error_messages: List[str]) -> List[str]:
        """
        Validate a field using provided validators.

        Args:
            field: Field name
            value: Field value
            validators: List of validator functions
            error_messages: Corresponding error messages

        Returns:
            List[str]: Validation errors
        """
        errors = []
        for validator, message in zip(validators, error_messages):
            if not validator(value):
                errors.append(f"{field}: {message}")
        return errors

@dataclass
class ModelConfig(ValidationMixin):
    """
    Configuration for individual model customization.

    Attributes:
        table_name: Database table name
        class_name: Python class name to generate
        base_classes: Additional base classes for the model
        mixins: Mixin classes to include
        validators: Field-specific validators
        widgets: Custom widgets for form fields
        excluded_columns: Columns to exclude from the model
        custom_methods: Additional methods to generate
        doc_string: Custom docstring for the model
        primary_key: Custom primary key field
        indexes: Custom indexes to create
        unique_constraints: Unique constraints to enforce
        relationships: Custom relationship definitions
        __tablename__: Custom table name override
    """
    table_name: str
    class_name: Optional[str] = None
    base_classes: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    validators: Dict[str, List[ValidatorType]] = field(default_factory=dict)
    widgets: Dict[str, WidgetType] = field(default_factory=dict)
    excluded_columns: List[str] = field(default_factory=list)
    custom_methods: List[str] = field(default_factory=list)
    doc_string: Optional[str] = None
    primary_key: Optional[str] = None
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    unique_constraints: List[List[str]] = field(default_factory=list)
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    __tablename__: Optional[str] = None

    def validate(self) -> List[str]:
        """Validate model configuration."""
        errors = []

        # Validate table name
        if not self.table_name:
            errors.append("Table name is required")
        elif not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.table_name):
            errors.append(f"Invalid table name: {self.table_name}")

        # Validate class name if provided
        if self.class_name and not self.class_name.isidentifier():
            errors.append(f"Invalid class name: {self.class_name}")

        # Validate base classes
        for base in self.base_classes:
            if not base.isidentifier():
                errors.append(f"Invalid base class name: {base}")

        # Validate relationships
        for rel_name, rel_config in self.relationships.items():
            if not rel_name.isidentifier():
                errors.append(f"Invalid relationship name: {rel_name}")
            if 'type' in rel_config and not RelationshipType.is_valid(rel_config['type']):
                errors.append(f"Invalid relationship type for {rel_name}: {rel_config['type']}")

        return errors

    def get_class_name(self) -> str:
        """Get the Python class name for the model."""
        if self.class_name:
            return self.class_name
        # Convert table_name to PascalCase
        return ''.join(word.capitalize() for word in self.table_name.split('_'))

@dataclass
class ViewConfig(ValidationMixin):
    """
    Configuration for view generation.

    Attributes:
        model_name: Model this view is for
        view_type: Type of view to generate
        endpoints: Custom endpoints to generate
        permissions: Permission requirements
        templates: Custom templates for different view types
        widgets: Custom widgets for forms
        excluded_fields: Fields to exclude from views
        search_columns: Columns to include in search
        list_columns: Columns to show in list view
        form_columns: Columns to include in forms
        show_columns: Columns to show in detail view
        add_columns: Columns for add form
        edit_columns: Columns for edit form
        description_columns: Column descriptions
        label_columns: Custom column labels
        order_columns: Columns that can be sorted
        base_permissions: Base permissions for the view
        base_order: Default ordering
        page_size: Number of items per page
    """
    model_name: str
    view_type: str = 'ModelView'
    endpoints: List[str] = field(default_factory=list)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    templates: Dict[str, str] = field(default_factory=dict)
    widgets: Dict[str, WidgetType] = field(default_factory=dict)
    excluded_fields: List[str] = field(default_factory=list)
    search_columns: List[str] = field(default_factory=list)
    list_columns: List[str] = field(default_factory=list)
    form_columns: List[str] = field(default_factory=list)
    show_columns: List[str] = field(default_factory=list)
    add_columns: List[str] = field(default_factory=list)
    edit_columns: List[str] = field(default_factory=list)
    description_columns: Dict[str, str] = field(default_factory=dict)
    label_columns: Dict[str, str] = field(default_factory=dict)
    order_columns: List[str] = field(default_factory=list)
    base_permissions: List[str] = field(default_factory=lambda: ['can_list', 'can_show'])
    base_order: Optional[Tuple[str, str]] = None
    page_size: int = 10

    def validate(self) -> List[str]:
        """Validate view configuration."""
        errors = []

        # Validate model name
        if not self.model_name:
            errors.append("Model name is required")
        elif not self.model_name.isidentifier():
            errors.append(f"Invalid model name: {self.model_name}")

        # Validate view type
        valid_view_types = {'ModelView', 'RestCRUDView', 'CompactCRUDMixin',
                           'MasterDetailView', 'MultipleView'}
        if self.view_type not in valid_view_types:
            errors.append(f"Invalid view type: {self.view_type}")

        # Validate endpoints
        for endpoint in self.endpoints:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', endpoint):
                errors.append(f"Invalid endpoint name: {endpoint}")

        # Validate permissions
        valid_permissions = {'can_list', 'can_show', 'can_add', 'can_edit',
                           'can_delete', 'can_download'}
        for permission_set in self.permissions.values():
            for permission in permission_set:
                if permission not in valid_permissions:
                    errors.append(f"Invalid permission: {permission}")

        # Validate page size
        if self.page_size < 1:
            errors.append("Page size must be positive")

        # Validate base order
        if self.base_order:
            if not isinstance(self.base_order, tuple) or len(self.base_order) != 2:
                errors.append("Base order must be a tuple of (column, direction)")
            elif self.base_order[1] not in ['asc', 'desc']:
                errors.append("Order direction must be 'asc' or 'desc'")

        return errors

    def get_view_name(self) -> str:
        """Get the Python class name for the view."""
        return f"{self.model_name}{self.view_type}"

    def merge_column_configs(self) -> Dict[str, Set[str]]:
        """Merge all column configurations for analysis."""
        columns = {
            'all': set(self.form_columns + self.list_columns +
                      self.show_columns + self.add_columns +
                      self.edit_columns + self.search_columns +
                      self.order_columns),
            'form': set(self.form_columns),
            'list': set(self.list_columns),
            'show': set(self.show_columns),
            'add': set(self.add_columns),
            'edit': set(self.edit_columns),
            'search': set(self.search_columns),
            'order': set(self.order_columns)
        }
        return columns

@dataclass
class DatabaseConfig(ValidationMixin):
    """
    Enhanced database configuration with comprehensive connection options.

    Attributes:
        uri: Database connection URI
        schema: Database schema to use
        exclude_tables: Tables to exclude from generation
        include_tables: Tables to include in generation
        custom_type_mappings: Custom database to Python type mappings
        connection_pool_size: Size of connection pool
        connection_timeout: Connection timeout in seconds
        enable_ssl: Whether to use SSL for connection
        ssl_ca_cert: Path to SSL CA certificate
        schema_version: Schema version for migrations
        migration_dir: Directory for migration files
        auto_pluralize: Auto-pluralize table names
        column_name_case: Case style for column names
        lazy_loading: Default lazy loading strategy
        batch_size: Default batch size for queries
    """
    uri: str
    schema: str = 'public'
    exclude_tables: List[str] = field(default_factory=list)
    include_tables: List[str] = field(default_factory=list)
    custom_type_mappings: Dict[str, str] = field(default_factory=dict)
    connection_pool_size: int = 5
    connection_timeout: int = 30
    enable_ssl: bool = False
    ssl_ca_cert: Optional[str] = None
    schema_version: Optional[str] = None
    migration_dir: Optional[Path] = None
    auto_pluralize: bool = True
    column_name_case: str = 'snake_case'
    lazy_loading: str = 'select'
    batch_size: int = 100

    def validate(self) -> List[str]:
        """Validate database configuration."""
        errors = []

        # Validate URI
        if not self.uri:
            errors.append("Database URI is required")
        elif not self.uri.startswith(('postgresql://', 'mysql://', 'sqlite:///')):
            errors.append("Unsupported database type in URI")

        # Validate schema name
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.schema):
            errors.append(f"Invalid schema name: {self.schema}")

        # Validate connection settings
        if self.connection_pool_size < 1:
            errors.append("Connection pool size must be positive")
        if self.connection_timeout < 1:
            errors.append("Connection timeout must be positive")

        # Validate SSL configuration
        if self.enable_ssl and self.ssl_ca_cert:
            if not Path(self.ssl_ca_cert).exists():
                errors.append(f"SSL CA certificate not found: {self.ssl_ca_cert}")

        # Validate type mappings
        for db_type, python_type in self.custom_type_mappings.items():
            try:
                module_path, class_name = python_type.rsplit('.', 1)
                importlib.import_module(module_path)
            except (ImportError, ValueError):
                errors.append(f"Invalid Python type mapping: {python_type}")

        return errors

@dataclass
class GenerationConfig(ValidationMixin):
    """
    Enhanced generation configuration with comprehensive code generation options.

    Attributes:
        output_dir: Directory for generated code
        output_style: Style of code output
        indent_size: Number of spaces for indentation
        template_dir: Directory containing templates
        include_views: Generate view classes
        include_procedures: Generate stored procedure wrappers
        backup_existing: Create backups of existing files
        timestamp_files: Add timestamps to generated files
        line_length: Maximum line length
        docstring_style: Style of docstrings
        type_hints: Include type hints
        generate_tests: Generate test files
        generate_docs: Generate documentation
        file_header: Custom file header template
        import_style: Style for import statements
        class_template: Template for class definitions
    """
    output_dir: Path
    output_style: OutputStyle = OutputStyle.MULTIPLE_FILES
    indent_size: int = 4
    template_dir: Path = Path('templates')
    include_views: bool = True
    include_procedures: bool = False
    backup_existing: bool = True
    timestamp_files: bool = True
    line_length: int = 88
    docstring_style: DocstringStyle = DocstringStyle.GOOGLE
    type_hints: bool = True
    generate_tests: bool = True
    generate_docs: bool = True
    file_header: Optional[str] = None
    import_style: str = 'grouped'
    class_template: Optional[str] = None

    def validate(self) -> List[str]:
        """Validate generation configuration."""
        errors = []

        # Validate directories
        if not self.output_dir:
            errors.append("Output directory is required")
        if not self.template_dir.exists():
            errors.append(f"Template directory not found: {self.template_dir}")

        # Validate numeric values
        if self.indent_size < 2 or self.indent_size > 8:
            errors.append("Indent size must be between 2 and 8")
        if self.line_length < 60:
            errors.append("Line length must be at least 60")

        # Validate enum values
        if not DocstringStyle.is_valid(self.docstring_style.value):
            errors.append(f"Invalid docstring style: {self.docstring_style}")
        if not OutputStyle.is_valid(self.output_style.value):
            errors.append(f"Invalid output style: {self.output_style}")

        # Validate import style
        valid_import_styles = {'grouped', 'inline', 'separate'}
        if self.import_style not in valid_import_styles:
            errors.append(f"Invalid import style: {self.import_style}")

        return errors

    def get_template_path(self, template_name: str) -> Path:
        """Get the full path for a template file."""
        return self.template_dir / template_name

    def get_output_path(self, filename: str) -> Path:
        """Get the full output path for a generated file."""
        if self.timestamp_files:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
        return self.output_dir / filename

@dataclass
class APIConfig(ValidationMixin):
    """
    Enhanced API configuration with comprehensive REST API options.

    Attributes:
        enable_api: Whether to generate API endpoints
        version: API version string
        prefix: URL prefix for API endpoints
        authentication: Authentication method
        allowed_methods: Allowed HTTP methods
        rate_limiting: Enable rate limiting
        documentation: Generate API documentation
        cors_enabled: Enable CORS support
        security_schemes: Security scheme definitions
        response_formats: Supported response formats
        error_responses: Custom error response templates
        versioning: API versioning strategy
        pagination: Pagination configuration
    """
    enable_api: bool = True
    version: str = 'v1'
    prefix: str = '/api'
    authentication: AuthenticationType = AuthenticationType.JWT
    allowed_methods: Set[str] = field(default_factory=lambda: {'GET', 'POST', 'PUT', 'DELETE'})
    rate_limiting: bool = False
    documentation: bool = True
    cors_enabled: bool = False
    security_schemes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    response_formats: List[str] = field(default_factory=lambda: ['json'])
    error_responses: Dict[int, Dict[str, str]] = field(default_factory=dict)
    versioning: str = 'url'
    pagination: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'page_size': 20,
        'max_page_size': 100
    })

    def validate(self) -> List[str]:
        """Validate API configuration."""
        errors = []

        # Validate basic settings
        if self.enable_api:
            if not self.version:
                errors.append("API version is required when API is enabled")
            if not self.prefix.startswith('/'):
                errors.append("API prefix must start with '/'")

        # Validate authentication
        if not AuthenticationType.is_valid(self.authentication.value):
            errors.append(f"Invalid authentication type: {self.authentication}")

        # Validate HTTP methods
        valid_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
        invalid_methods = self.allowed_methods - valid_methods
        if invalid_methods:
            errors.append(f"Invalid HTTP methods: {invalid_methods}")

        # Validate versioning
        valid_versioning = {'url', 'header', 'parameter', 'media_type'}
        if self.versioning not in valid_versioning:
            errors.append(f"Invalid versioning strategy: {self.versioning}")

        # Validate pagination
        if self.pagination['enabled']:
            if self.pagination['page_size'] > self.pagination['max_page_size']:
                errors.append("Page size cannot exceed max page size")
            if self.pagination['page_size'] < 1:
                errors.append("Page size must be positive")

        return errors

    def get_security_scheme(self, scheme_name: str) -> Optional[Dict[str, Any]]:
        """Get a security scheme configuration."""
        return self.security_schemes.get(scheme_name)

    def get_error_response(self, status_code: int) -> Optional[Dict[str, str]]:
        """Get an error response template."""
        return self.error_responses.get(status_code)


@dataclass
class SecurityConfig(ValidationMixin):
    """
    Enhanced security configuration with comprehensive security options.

    Attributes:
        enable_permissions: Enable permission-based security
        sensitive_fields: Fields containing sensitive data
        password_fields: Fields containing passwords
        role_model: Custom role model name
        user_model: Custom user model name
        permission_model: Custom permission model name
        hash_method: Password hashing method
        salt_length: Length of password salt
        token_lifetime: JWT token lifetime in seconds
        require_2fa: Require two-factor authentication
        audit_logging: Enable audit logging
        max_login_attempts: Maximum login attempts
        lockout_duration: Account lockout duration
        password_policy: Password policy requirements
        csrf_protection: CSRF protection settings
        session_config: Session configuration
        oauth_providers: OAuth provider configurations
    """
    enable_permissions: bool = True
    sensitive_fields: List[str] = field(default_factory=list)
    password_fields: List[str] = field(default_factory=list)
    role_model: str = 'ab_role'
    user_model: str = 'ab_user'
    permission_model: str = 'ab_permission'
    hash_method: str = 'pbkdf2:sha256'
    salt_length: int = 8
    token_lifetime: int = 3600
    require_2fa: bool = False
    audit_logging: bool = True
    max_login_attempts: int = 3
    lockout_duration: int = 300  # seconds
    password_policy: Dict[str, Any] = field(default_factory=lambda: {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special': True,
        'max_age': 90  # days
    })
    csrf_protection: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'time_limit': 3600,
        'ssl_only': True
    })
    session_config: Dict[str, Any] = field(default_factory=lambda: {
        'permanent': False,
        'lifetime': 3600,
        'refresh_each_request': True,
        'secure': True,
        'httponly': True,
        'samesite': 'Lax'
    })
    oauth_providers: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate security configuration."""
        errors = []

        # Validate model names
        for model_name in [self.role_model, self.user_model, self.permission_model]:
            if not model_name.isidentifier():
                errors.append(f"Invalid model name: {model_name}")

        # Validate hash method
        valid_hash_methods = {'pbkdf2:sha256', 'pbkdf2:sha512', 'bcrypt', 'argon2'}
        if not any(self.hash_method.startswith(method) for method in valid_hash_methods):
            errors.append(f"Invalid hash method: {self.hash_method}")

        # Validate numeric values
        if self.salt_length < 8:
            errors.append("Salt length must be at least 8")
        if self.token_lifetime < 60:
            errors.append("Token lifetime must be at least 60 seconds")
        if self.max_login_attempts < 1:
            errors.append("Max login attempts must be positive")
        if self.lockout_duration < 60:
            errors.append("Lockout duration must be at least 60 seconds")

        # Validate password policy
        policy = self.password_policy
        if policy['min_length'] < 8:
            errors.append("Minimum password length must be at least 8")
        if policy['max_age'] < 1:
            errors.append("Password max age must be positive")

        # Validate OAuth providers
        required_oauth_fields = {'client_id', 'client_secret', 'authorize_url', 'token_url'}
        for provider, config in self.oauth_providers.items():
            missing_fields = required_oauth_fields - set(config.keys())
            if missing_fields:
                errors.append(f"Missing required OAuth fields for {provider}: {missing_fields}")

        return errors

    def get_password_validator(self) -> Callable[[str], bool]:
        """Create a password validator based on policy."""
        def validate_password(password: str) -> bool:
            if len(password) < self.password_policy['min_length']:
                return False
            if self.password_policy['require_uppercase'] and not any(c.isupper() for c in password):
                return False
            if self.password_policy['require_lowercase'] and not any(c.islower() for c in password):
                return False
            if self.password_policy['require_numbers'] and not any(c.isdigit() for c in password):
                return False
            if self.password_policy['require_special'] and not any(not c.isalnum() for c in password):
                return False
            return True
        return validate_password

@dataclass
class RelationshipsConfig(ValidationMixin):
    """
    Enhanced relationships configuration with comprehensive relationship options.

    Attributes:
        auto_detect: Automatically detect relationships
        manual_relationships: Manual relationship definitions
        handle_circular_dependencies: Handle circular relationship dependencies
        use_backref: Use backreferences in relationships
        lazy_loading: Default lazy loading strategy
        cascade_deletions: Enable cascade deletions
        relationship_naming_template: Template for relationship names
        secondary_table_template: Template for many-to-many association tables
        backref_naming: Template for backref names
        relationship_defaults: Default relationship settings
        association_tables: Custom association table definitions
        polymorphic_config: Polymorphic relationship settings
    """
    auto_detect: bool = True
    manual_relationships: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)
    handle_circular_dependencies: bool = True
    use_backref: bool = True
    lazy_loading: str = 'select'
    cascade_deletions: bool = False
    relationship_naming_template: str = '{tablename}_{reltype}'
    secondary_table_template: str = '{table1}_{table2}_association'
    backref_naming: Dict[str, str] = field(default_factory=lambda: {
        'one_to_many': '{table}_collection',
        'many_to_one': '{table}_parent',
        'many_to_many': '{table}_collection'
    })
    relationship_defaults: Dict[str, Any] = field(default_factory=lambda: {
        'cascade': 'all, delete-orphan',
        'single_parent': True,
        'passive_deletes': False,
        'lazy': 'select',
        'enable_typechecks': True
    })
    association_tables: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    polymorphic_config: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate relationships configuration."""
        errors = []

        # Validate manual relationships
        for table, relationships in self.manual_relationships.items():
            for rel in relationships:
                if 'type' not in rel:
                    errors.append(f"Missing relationship type for {table}")
                elif not RelationshipType.is_valid(rel['type']):
                    errors.append(f"Invalid relationship type for {table}: {rel['type']}")
                if 'target' not in rel:
                    errors.append(f"Missing relationship target for {table}")

        # Validate lazy loading strategy
        valid_lazy = {'select', 'joined', 'subquery', 'raise', 'noload', 'dynamic'}
        if self.lazy_loading not in valid_lazy:
            errors.append(f"Invalid lazy loading strategy: {self.lazy_loading}")

        # Validate templates
        template_vars = {'{tablename}', '{reltype}'}
        if not all(var in self.relationship_naming_template for var in template_vars):
            errors.append("Invalid relationship naming template")

        # Validate association tables
        for table_name, config in self.association_tables.items():
            if 'left_table' not in config or 'right_table' not in config:
                errors.append(f"Invalid association table configuration for {table_name}")

        # Validate polymorphic configuration
        for table_name, config in self.polymorphic_config.items():
            if 'identity' not in config:
                errors.append(f"Missing polymorphic identity for {table_name}")
            if 'type_column' not in config:
                errors.append(f"Missing polymorphic type column for {table_name}")

        return errors

    def get_relationship_name(self, table_name: str, rel_type: RelationshipType) -> str:
        """Generate relationship name based on template."""
        return self.relationship_naming_template.format(
            tablename=table_name,
            reltype=rel_type.value
        )

    def get_backref_name(self, table_name: str, rel_type: RelationshipType) -> str:
        """Generate backref name based on template."""
        template = self.backref_naming.get(rel_type.value, '{table}')
        return template.format(table=table_name)

    def get_association_table_name(self, table1: str, table2: str) -> str:
        """Generate association table name based on template."""
        return self.secondary_table_template.format(
            table1=table1,
            table2=table2
        )


@dataclass
class LoggingConfig(ValidationMixin):
    """
    Configuration for logging settings.

    Attributes:
        enabled: Enable logging
        level: Logging level
        format: Log message format
        file: Log file path
        rotate: Enable log rotation
        max_size: Maximum log file size
        backup_count: Number of backup files to keep
        console_output: Enable console output
    """
    enabled: bool = True
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file: Optional[Path] = None
    rotate: bool = True
    max_size: int = 1024 * 1024  # 1MB
    backup_count: int = 5
    console_output: bool = True

    def validate(self) -> List[str]:
        """Validate logging configuration."""
        errors = []
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}

        if self.level not in valid_levels:
            errors.append(f"Invalid log level: {self.level}")
        if self.file and not self.file.parent.exists():
            errors.append(f"Log file directory does not exist: {self.file.parent}")
        if self.max_size < 1024:
            errors.append("Log file max size must be at least 1KB")
        if self.backup_count < 0:
            errors.append("Backup count must be non-negative")

        return errors

@dataclass
class GeneratorConfig(ValidationMixin):
    """
    Master configuration class for the code generator.

    Attributes:
        database: Database connection configuration
        generation: Code generation settings
        relationships: Relationship handling configuration
        security: Security settings
        models: Model-specific configurations
        views: View-specific configurations
        api: API generation settings
        logging: Logging configuration
        metadata: Project metadata
        templates: Custom template overrides
        hooks: Custom generation hooks
        extensions: Generator extensions
    """
    database: DatabaseConfig
    generation: GenerationConfig
    relationships: RelationshipsConfig
    security: SecurityConfig
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    views: Dict[str, ViewConfig] = field(default_factory=dict)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        'project_name': '',
        'version': '0.1.0',
        'author': '',
        'description': '',
        'license': 'MIT'
    })
    templates: Dict[str, Path] = field(default_factory=dict)
    hooks: Dict[str, List[Callable]] = field(default_factory=dict)
    extensions: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize logging after instance creation."""
        if self.logging.enabled:
            self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging based on settings."""
        logger = logging.getLogger('model_generator')
        logger.setLevel(self.logging.level)

        # Create formatter
        formatter = logging.Formatter(self.logging.format)

        # Add file handler if specified
        if self.logging.file:
            if self.logging.rotate:
                handler = logging.handlers.RotatingFileHandler(
                    self.logging.file,
                    maxBytes=self.logging.max_size,
                    backupCount=self.logging.backup_count
                )
            else:
                handler = logging.FileHandler(self.logging.file)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # Add console handler if enabled
        if self.logging.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

    def validate(self) -> List[str]:
        """Validate entire configuration."""
        errors = []

        # Validate each component
        errors.extend(self.database.validate())
        errors.extend(self.generation.validate())
        errors.extend(self.relationships.validate())
        errors.extend(self.security.validate())
        errors.extend(self.api.validate())
        errors.extend(self.logging.validate())

        # Validate models
        for model_name, model_config in self.models.items():
            model_errors = model_config.validate()
            errors.extend(f"Model {model_name}: {error}" for error in model_errors)

        # Validate views
        for view_name, view_config in self.views.items():
            view_errors = view_config.validate()
            errors.extend(f"View {view_name}: {error}" for error in view_errors)

        # Validate metadata
        if not self.metadata.get('project_name'):
            errors.append("Project name is required")
        if not re.match(r'^[0-9]+\.[0-9]+\.[0-9]+$', self.metadata.get('version', '')):
            errors.append("Invalid version format (should be x.y.z)")

        # Validate templates
        for template_name, template_path in self.templates.items():
            if not template_path.exists():
                errors.append(f"Template not found: {template_path}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        def _convert_value(value: Any) -> Any:
            if isinstance(value, Path):
                return str(value)
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, (list, tuple, set)):
                return [_convert_value(v) for v in value]
            if isinstance(value, dict):
                return {k: _convert_value(v) for k, v in value.items()}
            if dataclasses.is_dataclass(value):
                return dataclasses.asdict(value)
            return value

        return {
            field.name: _convert_value(getattr(self, field.name))
            for field in dataclasses.fields(self)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratorConfig':
        """Create configuration from dictionary."""
        try:
            # Convert nested configurations
            database = DatabaseConfig(**data.get('database', {}))
            generation = GenerationConfig(
                output_dir=Path(data.get('generation', {}).get('output_dir', '.')),
                output_style=OutputStyle(data.get('generation', {}).get('output_style', 'multiple_files')),
                **{k: v for k, v in data.get('generation', {}).items()
                   if k not in ['output_dir', 'output_style']}
            )
            relationships = RelationshipsConfig(**data.get('relationships', {}))
            security = SecurityConfig(**data.get('security', {}))

            # Convert model configurations
            models = {
                name: ModelConfig(**config)
                for name, config in data.get('models', {}).items()
            }

            # Convert view configurations
            views = {
                name: ViewConfig(**config)
                for name, config in data.get('views', {}).items()
            }

            # Convert API configuration
            api = APIConfig(**data.get('api', {}))

            # Convert logging configuration
            logging_config = LoggingConfig(**data.get('logging', {}))

            return cls(
                database=database,
                generation=generation,
                relationships=relationships,
                security=security,
                models=models,
                views=views,
                api=api,
                logging=logging_config,
                metadata=data.get('metadata', {}),
                templates={k: Path(v) for k, v in data.get('templates', {}).items()},
                extensions=data.get('extensions', {})
            )
        except Exception as e:
            raise ValueError(f"Error creating configuration from dictionary: {str(e)}")

    def get_model_config(self, table_name: str) -> Optional[ModelConfig]:
        """Get model configuration for a table."""
        return self.models.get(table_name)

    def get_view_config(self, model_name: str) -> Optional[ViewConfig]:
        """Get view configuration for a model."""
        return self.views.get(model_name)

    def is_table_excluded(self, table_name: str) -> bool:
        """Check if a table should be excluded from generation."""
        if self.database.include_tables:
            return table_name not in self.database.include_tables
        return table_name in self.database.exclude_tables

    def register_hook(self, hook_point: str, callback: Callable) -> None:
        """Register a generation hook."""
        if hook_point not in self.hooks:
            self.hooks[hook_point] = []
        self.hooks[hook_point].append(callback)

    def run_hooks(self, hook_point: str, context: Dict[str, Any]) -> None:
        """Run all registered hooks for a hook point."""
        for hook in self.hooks.get(hook_point, []):
            try:
                hook(context)
            except Exception as e:
                logger.error(f"Error running hook {hook.__name__}: {str(e)}")

# Type definitions
ModelType = Union[Type['Model'], str]
WidgetType = Union[Type[FormWidget], str]
ValidatorType = Union[Type[wtforms.validators.ValidationError], str]
CustomValidator = Callable[[Any], bool]
HookCallback = Callable[[Dict[str, Any]], None]
