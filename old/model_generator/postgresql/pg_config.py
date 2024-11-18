"""
pg_config.py: PostgreSQL-specific configuration options.

This module defines configuration classes for PostgreSQL-specific features and settings,
extending the base configuration system to handle PostgreSQL's advanced capabilities.

Key Features:
    - Type handling configuration
    - Schema management settings
    - Security feature controls
    - Performance settings
    - Extended feature toggles

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from pathlib import Path

@dataclass
class PostgreSQLTypeConfig:
    """Configuration for PostgreSQL type handling."""
    
    # Type System Features
    use_native_enums: bool = True
    use_native_ranges: bool = True
    use_native_arrays: bool = True
    use_native_domains: bool = False  # More complex, off by default
    use_native_jsonb: bool = True
    
    # Custom Type Mappings
    type_mappings: Dict[str, str] = field(default_factory=dict)
    array_mappings: Dict[str, str] = field(default_factory=dict)
    composite_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Type Options
    varchar_length: int = 255  # Default length for varchar fields
    text_length: Optional[int] = None  # None means unlimited
    numeric_precision: int = 18
    numeric_scale: int = 6
    timestamp_timezone: bool = True
    interval_fields: Optional[str] = None


@dataclass
class PostgreSQLSchemaConfig:
    """Configuration for PostgreSQL schema handling."""
    
    # Schema Selection
    schema_name: str = "public"
    search_path: List[str] = field(default_factory=lambda: ["public"])
    include_schemas: List[str] = field(default_factory=list)
    exclude_schemas: List[str] = field(default_factory=list)
    
    # Object Selection
    include_tables: List[str] = field(default_factory=list)
    exclude_tables: List[str] = field(default_factory=list)
    include_views: bool = False
    include_materialized_views: bool = False
    include_foreign_tables: bool = False
    
    # Naming
    schema_name_template: str = "{schema}"
    table_name_template: str = "{table}"
    view_name_template: str = "{view}"
    
    # Comments
    include_table_comments: bool = True
    include_column_comments: bool = True
    include_constraint_comments: bool = True


@dataclass
class PostgreSQLSecurityConfig:
    """Configuration for PostgreSQL security features."""
    
    # Row Level Security
    include_rls_policies: bool = False
    rls_force_per_table: bool = False
    default_rls_policy: Optional[str] = None
    
    # Grants and Privileges
    include_grants: bool = False
    include_column_grants: bool = False
    default_privileges: List[str] = field(default_factory=list)
    
    # Roles and Users
    owner_role: Optional[str] = None
    application_roles: List[str] = field(default_factory=list)
    
    # Security Labels
    include_security_labels: bool = False
    security_label_providers: List[str] = field(default_factory=list)


@dataclass
class PostgreSQLPerformanceConfig:
    """Configuration for PostgreSQL performance features."""
    
    # Connection Settings
    min_connections: int = 1
    max_connections: int = 5
    connection_timeout: int = 30
    
    # Query Settings
    statement_timeout: int = 0  # 0 means no timeout
    lock_timeout: int = 0
    idle_in_transaction_timeout: int = 0
    
    # Storage Settings
    temp_tablespaces: List[str] = field(default_factory=list)
    maintenance_work_mem: str = "64MB"
    autovacuum_enabled: bool = True


@dataclass
class PostgreSQLFeatureConfig:
    """Configuration for PostgreSQL extended features."""
    
    # Extensions
    required_extensions: List[str] = field(default_factory=list)
    optional_extensions: List[str] = field(default_factory=list)
    
    # Inheritance
    include_inheritance: bool = True
    inherit_foreign_keys: bool = True
    inherit_indexes: bool = True
    
    # Partitioning
    include_partitioning: bool = True
    partition_key_template: str = "{key_columns}"
    
    # Triggers
    include_triggers: bool = False
    trigger_templates: Dict[str, str] = field(default_factory=dict)


@dataclass
class PostgreSQLConfig:
    """Main PostgreSQL configuration class."""
    
    # Basic Settings
    database_name: str
    host: str = "localhost"
    port: int = 5432
    user: Optional[str] = None
    password: Optional[str] = None
    
    # SSL Configuration
    use_ssl: bool = False
    ssl_mode: str = "prefer"
    ssl_cert: Optional[Path] = None
    ssl_key: Optional[Path] = None
    ssl_root_cert: Optional[Path] = None
    
    # Component Configurations
    types: PostgreSQLTypeConfig = field(default_factory=PostgreSQLTypeConfig)
    schema: PostgreSQLSchemaConfig = field(default_factory=PostgreSQLSchemaConfig)
    security: PostgreSQLSecurityConfig = field(default_factory=PostgreSQLSecurityConfig)
    performance: PostgreSQLPerformanceConfig = field(default_factory=PostgreSQLPerformanceConfig)
    features: PostgreSQLFeatureConfig = field(default_factory=PostgreSQLFeatureConfig)
    
    def get_connection_string(self) -> str:
        """Generate database connection string."""
        parts = [
            f"postgresql://"
        ]
        
        # Add authentication if provided
        if self.user:
            parts.append(self.user)
            if self.password:
                parts.append(f":{self.password}")
            parts.append("@")
            
        # Add host and port
        parts.append(f"{self.host}:{self.port}")
        
        # Add database name
        parts.append(f"/{self.database_name}")
        
        # Add SSL parameters if enabled
        if self.use_ssl:
            params = [f"sslmode={self.ssl_mode}"]
            if self.ssl_cert:
                params.append(f"sslcert={self.ssl_cert}")
            if self.ssl_key:
                params.append(f"sslkey={self.ssl_key}")
            if self.ssl_root_cert:
                params.append(f"sslrootcert={self.ssl_root_cert}")
            parts.append("?" + "&".join(params))
            
        return "".join(parts)
    
    def validate(self) -> List[str]:
        """Validate the configuration."""
        errors = []
        
        # Basic validation
        if not self.database_name:
            errors.append("Database name is required")
            
        if self.port < 1 or self.port > 65535:
            errors.append("Invalid port number")
            
        # SSL validation
        if self.use_ssl:
            if self.ssl_cert and not self.ssl_cert.exists():
                errors.append("SSL certificate file not found")
            if self.ssl_key and not self.ssl_key.exists():
                errors.append("SSL key file not found")
            if self.ssl_root_cert and not self.ssl_root_cert.exists():
                errors.append("SSL root certificate file not found")
                
        # Schema validation
        if self.schema.include_schemas and self.schema.exclude_schemas:
            errors.append("Cannot specify both include_schemas and exclude_schemas")
            
        if self.schema.include_tables and self.schema.exclude_tables:
            errors.append("Cannot specify both include_tables and exclude_tables")
            
        # Performance validation
        if self.performance.min_connections > self.performance.max_connections:
            errors.append("min_connections cannot be greater than max_connections")
            
        if self.performance.connection_timeout < 0:
            errors.append("connection_timeout cannot be negative")
            
        return errors
    
    def merge_with_defaults(self, defaults: Dict[str, Any]) -> None:
        """Merge configuration with defaults."""
        for key, value in defaults.items():
            if not hasattr(self, key):
                continue
                
            current = getattr(self, key)
            if isinstance(current, dict) and isinstance(value, dict):
                current.update({k: v for k, v in value.items() if k not in current})
            elif current is None:
                setattr(self, key, value)
