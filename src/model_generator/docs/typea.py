"""
config/types.py

This module defines the configuration dataclasses and types used throughout the
Flask-AppBuilder code generation subsystem. These dataclasses provide a
structured way to manage and validate the various configuration settings
required for the code generation process.

The configuration is divided into several main sections, each with its own set
of parameters and validation rules. This separation of concerns allows for
better maintainability, extensibility, and testability of the configuration
system.
"""

from dataclasses import dataclass, field, asdict, fields
from typing import List, Dict, Optional, Union, Type, Any, Set, Callable
from pathlib import Path
from enum import Enum
from datetime import datetime
from wtforms import widgets, FormWidget
import wtforms.validators

class OutputStyle(Enum):
    """Enumeration of supported code output styles."""
    SINGLE_FILE = 'single_file'
    MULTIPLE_FILES = 'multiple_files'
    MODULAR = 'modular'
    PACKAGE = 'package'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Validate if a value is a valid output style."""
        return value in [item.value for item in cls]

class RelationshipType(Enum):
    """Enumeration of supported relationship types."""
    ONE_TO_ONE = 'one_to_one'
    ONE_TO_MANY = 'one_to_many'
    MANY_TO_ONE = 'many_to_one'
    MANY_TO_MANY = 'many_to_many'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Validate if a value is a valid relationship type."""
        return value in [item.value for item in cls]


@dataclass
class ModelConfig:
    """
    Configuration for individual model customization.

    Attributes:
        table_name (str): The database table name
        class_name (str): The Python class name to generate
        base_classes (List[str]): Additional base classes for the model
        mixins (List[str]): Mixin classes to include
        validators (Dict[str, List[ValidatorType]]): Field-specific validators
        widgets (Dict[str, WidgetType]): Custom widgets for form fields
        excluded_columns (List[str]): Columns to exclude from the model
        custom_methods (List[str]): Additional methods to generate
        doc_string (str): Custom docstring for the model
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

    def validate(self) -> List[str]:
        """Validate model configuration."""
        errors = []
        if not self.table_name:
            errors.append("Table name is required")
        if self.class_name and not self.class_name.isidentifier():
            errors.append(f"Invalid class name: {self.class_name}")
        return errors

@dataclass
class ViewConfig:
    """
    Configuration for view generation.

    Attributes:
        model_name (str): The model this view is for
        view_type (str): Type of view to generate
        endpoints (List[str]): Custom endpoints to generate
        permissions (Dict[str, List[str]]): Permission requirements
        templates (Dict[str, str]): Custom templates for different view types
        widgets (Dict[str, WidgetType]): Custom widgets for forms
        excluded_fields (List[str]): Fields to exclude from views
        search_columns (List[str]): Columns to include in search
        list_columns (List[str]): Columns to show in list view
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

    def validate(self) -> List[str]:
        """Validate view configuration."""
        errors = []
        if not self.model_name:
            errors.append("Model name is required")
        if not self.view_type:
            errors.append("View type is required")
        return errors

@dataclass
class APIConfig:
    """
    Configuration for API generation.

    Attributes:
        enable_api (bool): Whether to generate API endpoints
        version (str): API version
        prefix (str): URL prefix for API endpoints
        authentication (str): Authentication method
        allowed_methods (Set[str]): HTTP methods to support
        rate_limiting (bool): Enable rate limiting
        documentation (bool): Generate API documentation
        cors_enabled (bool): Enable CORS support
    """
    enable_api: bool = True
    version: str = 'v1'
    prefix: str = '/api'
    authentication: str = 'jwt'
    allowed_methods: Set[str] = field(default_factory=lambda: {'GET', 'POST', 'PUT', 'DELETE'})
    rate_limiting: bool = False
    documentation: bool = True
    cors_enabled: bool = False

@dataclass
class DatabaseConfig:
    """Enhanced DatabaseConfig with additional features."""
    uri: str
    schema: str
    exclude_tables: List[str] = field(default_factory=list)
    include_tables: List[str] = field(default_factory=list)
    custom_type_mappings: Dict[str, str] = field(default_factory=dict)
    connection_pool_size: int = 5
    connection_timeout: int = 30
    enable_ssl: bool = False
    ssl_ca_cert: Optional[str] = None
    schema_version: Optional[str] = None
    migration_dir: Optional[Path] = None

@dataclass
class GenerationConfig:
    """Enhanced GenerationConfig with additional features."""
    output_dir: Path
    output_style: OutputStyle = OutputStyle.MULTIPLE_FILES
    indent_size: int = 4
    template_dir: Path = Path('templates')
    include_views: bool = False
    include_procedures: bool = False
    backup_existing: bool = True
    timestamp_files: bool = True
    line_length: int = 88  # Black default
    docstring_style: str = 'google'
    type_hints: bool = True
    generate_tests: bool = True
    generate_docs: bool = True

@dataclass
class RelationshipsConfig:
    """Enhanced RelationshipsConfig with additional features."""
    auto_detect: bool = True
    manual_relationships: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)
    handle_circular_dependencies: bool = True
    use_backref: bool = True
    lazy_loading: str = 'select'
    cascade_deletions: bool = False
    relationship_naming_template: str = '{tablename}_{reltype}'
    secondary_table_template: str = '{table1}_{table2}_association'

@dataclass
class SecurityConfig:
    """Enhanced SecurityConfig with additional features."""
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

@dataclass
class GeneratorConfig:
    """Enhanced master configuration with validation and utility methods."""
    database: DatabaseConfig
    generation: GenerationConfig
    relationships: RelationshipsConfig
    security: SecurityConfig
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    views: Dict[str, ViewConfig] = field(default_factory=dict)
    api: APIConfig = field(default_factory=APIConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)

    def validate(self) -> List[str]:
        """
        Validate the configuration.

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []

        # Validate database configuration
        if not self.database.uri:
            errors.append("Database URI is required")

        # Validate output directory
        if not self.generation.output_dir:
            errors.append("Output directory is required")

        # Add more validation rules as needed

        return errors

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratorConfig':
        """Create config from dictionary."""
        # Implement conversion logic
        pass

# Additional type definitions
ModelType = Union[Type['Model'], str]
WidgetType = Union[Type[FormWidget], str]
ValidatorType = Union[Type[wtforms.validators.ValidationError], str]
CustomValidator = Callable[[Any], bool]
