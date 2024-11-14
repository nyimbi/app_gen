"""
Model Generator Core Context Module
=================================

This module provides comprehensive data structures and utilities for generating SQLAlchemy
models from database schemas. It handles all aspects of database table definitions including
columns, relationships, constraints, indexes, and various database-specific features.

Key Components
-------------
1. Database Type Handling:
   - DatabaseType: Supported database engines (PostgreSQL, MySQL, SQLite, etc.)
   - AutoIncrementType: Different auto-increment implementations
   - OnUpdateAction: Foreign key update behaviors

2. Column Management:
   - ColumnInfo: Complete column definition and attributes
   Example:
       >>> column = ColumnInfo(
       ...     name="user_id",
       ...     type_name="integer",
       ...     primary_key=True,
       ...     auto_increment=AutoIncrementType.IDENTITY
       ... )
       >>> print(column.get_sqlalchemy_type())
       'Integer'

3. Foreign Key Management:
   - ForeignKeyInfo: Foreign key relationships and constraints
   Example:
       >>> fk = ForeignKeyInfo(
       ...     constrained_columns=["user_id"],
       ...     referred_table="users",
       ...     referred_columns=["id"],
       ...     on_delete=ReferentialAction.CASCADE
       ... )

4. Index Management:
   - IndexMethod: Supported index access methods
   - IndexType: Different types of indexes
   - IndexInfo: Complete index configuration
   Example:
       >>> idx = IndexInfo(
       ...     name="idx_users_email",
       ...     column_names=["email"],
       ...     is_unique=True,
       ...     method=IndexMethod.BTREE
       ... )

5. Constraint Management:
   - ConstraintType: Types of database constraints
   - ConstraintInfo: Constraint definitions and properties
   Example:
       >>> constraint = ConstraintInfo(
       ...     name="unique_email",
       ...     constraint_type=ConstraintType.UNIQUE,
       ...     columns=["email"]
       ... )

6. Table Management:
   - TableType: Different table types
   - TableInfo: Complete table definition and generation
   Example:
       >>> table = TableInfo(
       ...     name="users",
       ...     columns=[ColumnInfo("id", "integer", primary_key=True)],
       ...     indexes=[IndexInfo("idx_email", ["email"])]
       ... )
       >>> print(table.get_create_statement())

7. Relationship Management:
   - RelationshipType: Types of table relationships
   - Relationship: Relationship definition and SQLAlchemy mapping
   - RelationshipResolver: Handles relationship cycles and dependencies
   Example:
       >>> rel = Relationship(
       ...     source_table="users",
       ...     target_table="posts",
       ...     relationship_type=RelationshipType.ONE_TO_MANY,
       ...     foreign_keys=["user_id"]
       ... )

Usage Examples
-------------
1. Creating a Complete Table Definition:
    >>> table = TableInfo(
    ...     name="users",
    ...     columns=[
    ...         ColumnInfo("id", "integer", primary_key=True),
    ...         ColumnInfo("email", "varchar", max_length=255, unique=True),
    ...         ColumnInfo("created_at", "timestamp", nullable=False)
    ...     ],
    ...     indexes=[
    ...         IndexInfo("idx_users_email", ["email"], is_unique=True)
    ...     ],
    ...     constraints=[
    ...         ConstraintInfo("valid_email", ConstraintType.CHECK,
    ...                       definition="email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'")
    ...     ]
    ... )

2. Generating SQLAlchemy Models:
    >>> print(table.get_sqlalchemy_model())
    class User(Model):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        email = Column(String(255), unique=True)
        created_at = Column(DateTime, nullable=False)

3. Managing Relationships:
    >>> relationships = [
    ...     Relationship("users", "posts", RelationshipType.ONE_TO_MANY, ["user_id"]),
    ...     Relationship("posts", "categories", RelationshipType.MANY_TO_MANY,
    ...                 ["category_id"], secondary_table="post_categories")
    ... ]
    >>> resolver = RelationshipResolver(relationships)
    >>> resolved = resolver.resolve_cycles()

4. Complete Model Generation Workflow:
    >>> def generate_models(schema_info: Dict[str, Any]) -> str:
    ...     tables = []
    ...     relationships = []
    ...
    ...     # Create table definitions
    ...     for table_data in schema_info['tables']:
    ...         table = TableInfo(**table_data)
    ...         tables.append(table)
    ...
    ...     # Create relationships
    ...     for rel_data in schema_info['relationships']:
    ...         rel = Relationship(**rel_data)
    ...         relationships.append(rel)
    ...
    ...     # Resolve relationships
    ...     resolver = RelationshipResolver(relationships)
    ...     resolved_relationships = resolver.resolve_cycles()
    ...
    ...     # Generate models
    ...     models = []
    ...     for table in tables:
    ...         table_rels = [r for r in resolved_relationships
    ...                      if r.source_table == table.name]
    ...         models.append(table.get_sqlalchemy_model(relationships=table_rels))
    ...
    ...     return '\n\n'.join(models)

Dependencies
-----------
- SQLAlchemy: For model generation and type mapping
- typing: For type hints
- dataclasses: For data structure definitions
- enum: For enumeration types

Notes
-----
- All database object names are validated for compliance with SQL standards
- Relationship cycles are automatically detected and resolved
- Generated models include proper type hints and documentation
- Supports all major SQL databases with appropriate type mapping
- Handles complex scenarios like table inheritance and polymorphic relationships

Author: Nyimbi Odero
Copyright: 2024 Nyimbi Odero
License: MIT
"""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union
from enum import Enum, auto

from model_generator.utils.validation_utils import (
    validate_column_name,
    validate_table_name,
    validate_type,
    validate_numeric_range
)
from model_generator.utils.case_utils import to_snake_case, to_pascal_case
from model_generator.utils.type_utils import get_sqlalchemy_type_name,
from model_generator.exceptions import ValidationError

class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    SQLITE = 'sqlite'
    ORACLE = 'oracle'
    MSSQL = 'mssql'

class AutoIncrementType(Enum):
    """Enumeration of auto-increment types."""
    NONE = auto()
    IDENTITY = auto()
    SEQUENCE = auto()
    SERIAL = auto()

class IndexMethod(Enum):
    """Enumeration of supported index access methods."""
    BTREE = "btree"      # Default balanced tree
    HASH = "hash"        # Hash table
    GIST = "gist"        # Generalized Search Tree
    GIN = "gin"          # Generalized Inverted Index
    SPGIST = "spgist"    # Space-partitioned GiST
    BRIN = "brin"        # Block Range Index
    BLOOM = "bloom"      # Bloom filter

class IndexType(Enum):
    """Enumeration of index types and their characteristics."""
    NORMAL = "NORMAL"        # Regular index
    UNIQUE = "UNIQUE"        # Unique constraint index
    PRIMARY = "PRIMARY"      # Primary key index
    EXCLUDE = "EXCLUDE"      # Exclusion constraint index
    PARTIAL = "PARTIAL"      # Partial index with WHERE clause
    COVERING = "COVERING"    # Index with INCLUDE columns

class NullsOrder(Enum):
    """Enumeration of NULL ordering options."""
    FIRST = "NULLS FIRST"
    LAST = "NULLS LAST"
    DEFAULT = "DEFAULT"

class OnUpdateAction(Enum):
    """Enumeration of possible ON UPDATE actions."""
    NO_ACTION = "NO ACTION"
    RESTRICT = "RESTRICT"
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"


class TableType(Enum):
    """Enumeration of different table types."""
    REGULAR = "TABLE"              # Regular table
    FOREIGN = "FOREIGN TABLE"      # Foreign table
    PARTITIONED = "PARTITIONED"    # Partitioned table
    TEMPORARY = "TEMPORARY"        # Temporary table
    UNLOGGED = "UNLOGGED"         # Unlogged table
    MATERIALIZED = "MATERIALIZED"  # Materialized view


class PartitioningStrategy(Enum):
    """Enumeration of table partitioning strategies."""
    RANGE = "RANGE"
    LIST = "LIST"
    HASH = "HASH"


class ReplicaIdentity(Enum):
    """Enumeration of replica identity options."""
    DEFAULT = "DEFAULT"  # Primary key or NOTHING
    NOTHING = "NOTHING"  # No old values
    FULL = "FULL"       # All columns
    INDEX = "INDEX"     # User-specified index


class StorageParameters(Enum):
    """Common table storage parameters."""
    FILLFACTOR = "fillfactor"
    TOAST_TUPLE_TARGET = "toast_tuple_target"
    PARALLEL_WORKERS = "parallel_workers"
    AUTOVACUUM_ENABLED = "autovacuum_enabled"
    VACUUM_INDEX_CLEANUP = "vacuum_index_cleanup"
    USER_CATALOG_TABLE = "user_catalog_table"


class ConstraintType(Enum):
    """Enumeration of database constraint types."""
    CHECK = "CHECK"
    UNIQUE = "UNIQUE"
    PRIMARY_KEY = "PRIMARY KEY"
    FOREIGN_KEY = "FOREIGN KEY"
    EXCLUDE = "EXCLUDE"
    NOT_NULL = "NOT NULL"


class DeferrableStatus(Enum):
    """Enumeration of constraint deferrable options."""
    NOT_DEFERRABLE = "NOT DEFERRABLE"
    IMMEDIATE = "DEFERRABLE INITIALLY IMMEDIATE"
    DEFERRED = "DEFERRABLE INITIALLY DEFERRED"


class ExclusionOperator(Enum):
    """Common exclusion constraint operators."""
    EQUAL = "="
    NOT_EQUAL = "<>"
    LESS = "<"
    LESS_EQUAL = "<="
    GREATER = ">"
    GREATER_EQUAL = ">="
    OVERLAPS = "&&"
    ADJACENT = "-|-"
    CONTAINS = "@>"
    CONTAINED_BY = "<@"


@dataclass
class PostgreSQLTriggerInfo:
    """PostgreSQL trigger information."""
    name: str
    definition: str
    enabled: bool
    is_internal: bool
    timing: str  # BEFORE, AFTER, INSTEAD OF
    events: List[str]  # INSERT, UPDATE, DELETE, TRUNCATE
    function: str

@dataclass
class PostgreSQLSequenceInfo:
    """PostgreSQL sequence information."""
    name: str
    start_value: int
    increment: int
    min_value: int
    max_value: int
    cache_size: int
    cycle: bool
    owned_by: Optional[str]

@dataclass
class PostgreSQLDomainInfo:
    """PostgreSQL domain type information."""
    name: str
    base_type: str
    nullable: bool
    default: Optional[str]
    constraints: List[str]
    collation: Optional[str]

@dataclass
class PostgreSQLEnumType:
    """PostgreSQL enum type information."""
    name: str
    values: List[str]
    schema: str

@dataclass
class PostgreSQLRangeType:
    """PostgreSQL range type information."""
    name: str
    subtype: str
    subtype_opclass: str
    collation: Optional[str]
    canonical: Optional[str]
    subtype_diff: Optional[str]

@dataclass
class PostgreSQLCompositeType:
    """PostgreSQL composite type information."""
    name: str
    attributes: List[Dict[str, Any]]
    schema: str

class PostgreSQLStorageType(Enum):
    """PostgreSQL storage types."""
    PLAIN = 'p'
    EXTENDED = 'x'
    EXTERNAL = 'e'
    MAIN = 'm'

class PostgreSQLCompressionMethod(Enum):
    """PostgreSQL column compression methods."""
    NONE = 'n'
    LZ4 = 'l'
    PGLZ = 'p'

class PostgreSQLProcedureType(Enum):
    """PostgreSQL procedure types."""
    FUNCTION = 'f'
    PROCEDURE = 'p'
    AGGREGATE = 'a'
    WINDOW = 'w'


@dataclass
class PostgreSQLPolicyInfo:
    """PostgreSQL RLS policy information."""
    name: str
    command: str
    permissive: bool
    roles: List[str]
    qualifier: Optional[str]
    with_check: Optional[str]

@dataclass
class PostgreSQLExtensionInfo:
    """PostgreSQL extension information."""
    name: str
    version: str
    schema: str
    relocatable: bool


@dataclass
class PostgreSQLViewInfo:
    """PostgreSQL view information."""
    name: str
    definition: str
    materialized: bool
    with_data: bool
    check_option: Optional[str]
    security_barrier: bool
    security_invoker: bool

@dataclass
class PostgreSQLStatisticsInfo:
    """PostgreSQL column statistics information."""
    table_name: str
    column_name: str
    statistics_target: int
    statistics_kind: List[str]
    n_distinct: Optional[float]
    null_fraction: Optional[float]
    avg_width: Optional[int]
    correlation: Optional[float]

@dataclass
class PostgreSQLIndexAccess:
    """PostgreSQL index access method information."""
    method: IndexMethod
    operator_class: str
    operator_family: Optional[str]
    options: Dict[str, Any]

class TextSearchConfiguration(Enum):
    """Text search configuration options."""
    SIMPLE = 'simple'
    ENGLISH = 'english'
    SPANISH = 'spanish'
    CUSTOM = 'custom'

class OperatorStrategy(Enum):
    """Operator optimization strategies."""
    SUPPORT = auto()
    RESTRICT = auto()
    JOIN = auto()
    RECHECK = auto()

class TriggerTiming(Enum):
    """Event trigger timing options."""
    BEFORE = 'BEFORE'
    AFTER = 'AFTER'
    INSTEAD_OF = 'INSTEAD OF'

class TriggerEvent(Enum):
    """Event trigger types."""
    DDL_COMMAND_START = 'ddl_command_start'
    DDL_COMMAND_END = 'ddl_command_end'
    SQL_DROP = 'sql_drop'
    TABLE_REWRITE = 'table_rewrite'

class FDWValidation(Enum):
    """Foreign data wrapper validation levels."""
    IMPORT = 'IMPORT FOREIGN SCHEMA'
    IMPORT_ONLY = 'IMPORT ONLY'
    NONE = 'NONE'

class ReplicationType(Enum):
    """Publication/subscription replication types."""
    LOGICAL = 'logical'
    PHYSICAL = 'physical'
    NONE = 'none'

@dataclass
class TextSearchInfo:
    """PostgreSQL full text search configuration."""
    name: str
    parser: str
    configuration: TextSearchConfiguration
    dictionary: str
    mappings: Dict[str, str]  # token type -> dictionary
    template: Optional[str] = None
    custom_parsers: List[str] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=dict)

@dataclass
class OperatorInfo:
    """Custom operator information."""
    name: str
    left_arg: str
    right_arg: str
    result_type: str
    function: str
    commutator: Optional[str] = None
    negator: Optional[str] = None
    restrict: Optional[str] = None
    join: Optional[str] = None
    hashes: bool = False
    merges: bool = False
    strategies: List[OperatorStrategy] = field(default_factory=list)

@dataclass
class OperatorClassInfo:
    """Operator class information."""
    name: str
    index_method: str
    operators: List[OperatorInfo]
    functions: List[str]
    default: bool = False
    storage: Optional[str] = None
    family: Optional[str] = None

@dataclass
class EventTriggerInfo:
    """Event trigger configuration."""
    name: str
    event: TriggerEvent
    timing: TriggerTiming
    function: str
    condition: Optional[str] = None
    enabled: bool = True
    roles: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

@dataclass
class FDWInfo:
    """Foreign data wrapper configuration."""
    name: str
    handler: str
    validator: Optional[str] = None
    options: Dict[str, str] = field(default_factory=dict)
    validation: FDWValidation = FDWValidation.NONE
    servers: List['ForeignServerInfo'] = field(default_factory=list)

@dataclass
class ForeignServerInfo:
    """Foreign server configuration."""
    name: str
    wrapper: str
    type: Optional[str] = None
    version: Optional[str] = None
    options: Dict[str, str] = field(default_factory=dict)
    tables: List['ForeignTableInfo'] = field(default_factory=list)

@dataclass
class ForeignTableInfo:
    """Foreign table configuration."""
    name: str
    server: str
    columns: List[str]
    options: Dict[str, str] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)

@dataclass
class PublicationInfo:
    """Publication configuration for logical replication."""
    name: str
    tables: List[str]
    publish_via_partition_root: bool = False
    publish: Set[str] = field(default_factory=set)  # insert, update, delete, truncate
    where_condition: Optional[str] = None
    owner: str = 'postgres'
    enabled: bool = True

@dataclass
class SubscriptionInfo:
    """Subscription configuration for logical replication."""
    name: str
    conninfo: str
    publications: List[str]
    enabled: bool = True
    synchronous: bool = False
    copy_data: bool = True
    streaming: bool = False
    slot_name: Optional[str] = None
    owner: str = 'postgres'

@dataclass
class PartitioningDetails:
    """Detailed partitioning information."""
    strategy: str  # range, list, hash
    key_columns: List[str]
    partitions: Dict[str, 'PartitionInfo']
    subpartitioning: Optional['PartitioningDetails'] = None
    interval: Optional[str] = None
    default_partition: Optional[str] = None

@dataclass
class PartitionInfo:
    """Individual partition information."""
    name: str
    strategy: str
    bound_spec: str
    tablespace: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PostgreSQLPartitionInfo:
    """Detailed PostgreSQL partition information."""
    strategy: PartitioningStrategy
    key_columns: List[str]
    bounds: Union[List[Any], int]  # for RANGE/LIST or HASH
    subpartition: Optional['PostgreSQLPartitionInfo']
    partition_of: Optional[str]
    template: bool
    access_method: Optional[str]

class PrivilegeType(Enum):
    """Types of PostgreSQL privileges."""
    SELECT = 'SELECT'
    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    TRUNCATE = 'TRUNCATE'
    REFERENCES = 'REFERENCES'
    TRIGGER = 'TRIGGER'
    EXECUTE = 'EXECUTE'
    USAGE = 'USAGE'
    CREATE = 'CREATE'
    CONNECT = 'CONNECT'
    TEMPORARY = 'TEMPORARY'
    ALL = 'ALL'

class SecurityLabelProvider(Enum):
    """Security label providers."""
    SELINUX = 'selinux'
    APPARMOR = 'apparmor'
    LABEL = 'label'
    CUSTOM = 'custom'

class SSLMode(Enum):
    """SSL connection modes."""
    DISABLE = 'disable'
    ALLOW = 'allow'
    PREFER = 'prefer'
    REQUIRE = 'require'
    VERIFY_CA = 'verify-ca'
    VERIFY_FULL = 'verify-full'

class AuthMethod(Enum):
    """Authentication methods."""
    TRUST = 'trust'
    REJECT = 'reject'
    MD5 = 'md5'
    PASSWORD = 'password'
    SCRAM_SHA_256 = 'scram-sha-256'
    GSS = 'gss'
    SSPI = 'sspi'
    IDENT = 'ident'
    PEER = 'peer'
    PAM = 'pam'
    LDAP = 'ldap'
    RADIUS = 'radius'
    CERT = 'cert'

@dataclass
class ColumnPrivilegeInfo:
    """Column-level privilege information."""
    table_name: str
    column_name: str
    grantee: str
    privilege: PrivilegeType
    grantor: str
    grantable: bool = False
    inherited: bool = False
    with_hierarchy: bool = False

@dataclass
class SecurityLabelInfo:
    """Security label information."""
    object_type: str
    object_name: str
    provider: SecurityLabelProvider
    label: str
    comment: Optional[str] = None
    timestamp: Optional[datetime] = None

@dataclass
class SSLInfo:
    """SSL configuration information."""
    mode: SSLMode
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None
    crl_file: Optional[str] = None
    verify_depth: int = 1
    verify_host: bool = True
    ciphers: List[str] = field(default_factory=list)

@dataclass
class RoleSettingInfo:
    """Role-specific parameter settings."""
    role_name: str
    settings: Dict[str, str] = field(default_factory=dict)
    in_database: Optional[str] = None
    inheritable: bool = True

@dataclass
class ConnectionInfo:
    """Connection and authentication configuration."""
    database: str
    user: str
    auth_method: AuthMethod
    address: Optional[str] = None
    netmask: Optional[str] = None
    options: Dict[str, str] = field(default_factory=dict)
    ssl_required: bool = False

@dataclass
class RolePrivilegeInfo:
    """Comprehensive role privilege information."""
    role_name: str
    schema_privileges: Dict[str, Set[PrivilegeType]]
    table_privileges: Dict[str, Set[PrivilegeType]]
    column_privileges: Dict[str, Dict[str, Set[PrivilegeType]]]
    function_privileges: Dict[str, Set[PrivilegeType]]
    sequence_privileges: Dict[str, Set[PrivilegeType]]
    foreign_data_wrapper_privileges: Dict[str, Set[PrivilegeType]]
    foreign_server_privileges: Dict[str, Set[PrivilegeType]]
    database_privileges: Dict[str, Set[PrivilegeType]]
    tablespace_privileges: Dict[str, Set[PrivilegeType]]
    type_privileges: Dict[str, Set[PrivilegeType]]
    language_privileges: Dict[str, Set[PrivilegeType]]
    large_object_privileges: Dict[str, Set[PrivilegeType]]

@dataclass
class RoleInfo:
    """Role configuration and capabilities."""
    name: str
    superuser: bool = False
    inherit: bool = True
    create_role: bool = False
    create_db: bool = False
    can_login: bool = False
    replication: bool = False
    bypass_rls: bool = False
    connection_limit: int = -1
    valid_until: Optional[datetime] = None
    member_of: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)
    admin_of: List[str] = field(default_factory=list)
    admins: List[str] = field(default_factory=list)

@dataclass
class PolicyInfo:
    """Row-level security policy information."""
    name: str
    table_name: str
    command: str  # SELECT, INSERT, UPDATE, DELETE
    roles: List[str]
    using_expr: Optional[str] = None
    check_expr: Optional[str] = None
    with_check: Optional[str] = None
    as_role: Optional[str] = None
    permissive: bool = True

class TextSearchConfiguration:
    """Class for managing text search configurations."""

    def __init__(self, parser: str):
        self.parser = parser
        self.dictionaries = {}
        self.mappings = {}

    def add_dictionary(self, name: str, template: str = None):
        """Add a text search dictionary."""
        self.dictionaries[name] = {"template": template}

    def add_mapping(self, token_type: str, dictionary: str):
        """Add a token type to dictionary mapping."""
        self.mappings[token_type] = dictionary


@dataclass
class TableLockInfo:
    """Information about table locks."""
    lock_type: str
    granted: bool
    pid: int
    transactionid: Optional[int] = None
    virtualtransaction: Optional[str] = None
    mode: Optional[str] = None
    waiting: bool = False
    start_time: Optional[datetime] = None


@dataclass
class CollationInfo:
    """Information about database collations."""
    name: str
    locale: str
    provider: str
    deterministic: bool = True
    version: Optional[str] = None
    rules: Optional[Dict[str, str]] = None


@dataclass
class AccessMethodInfo:
    """Information about index access methods."""
    name: str
    type: str
    handler_function: Optional[str] = None
    operator_class: Optional[str] = None
    operator_family: Optional[str] = None


@dataclass
class AdvancedConstraintInfo:
    """Information about advanced database constraints."""
    name: str
    constraint_type: str
    definition: str
    predicate: Optional[str] = None
    deferrable: bool = False
    initially_deferred: bool = False
    index_method: Optional[str] = None

@dataclass
class ColumnInfo:
    """
    Comprehensive information about a database column.

    This class holds detailed information about a database column, including its
    type, constraints, and various metadata. It provides validation and type
    conversion functionality.

    Attributes:
        name (str): Column name
        type_name (str): SQL type name
        nullable (bool): Whether column allows NULL values
        primary_key (bool): Whether column is part of primary key
        default (Any): Default value for column
        max_length (Optional[int]): Maximum length for string types
        precision (Optional[int]): Precision for numeric types
        scale (Optional[int]): Scale for numeric types
        comment (Optional[str]): Column documentation/comment
        unique (bool): Whether column has unique constraint
        index (bool): Whether column is indexed
        auto_increment (AutoIncrementType): Auto-increment type
        foreign_key (Optional[str]): Referenced table.column if foreign key
        on_update (Optional[OnUpdateAction]): ON UPDATE action if foreign key
        on_delete (Optional[OnUpdateAction]): ON DELETE action if foreign key
        check_constraints (List[str]): CHECK constraints on column
        enum_values (Optional[List[str]]): Possible values for enum types
        collation (Optional[str]): Collation for text columns
        generated (Optional[str]): Generation expression if computed
        storage_params (Dict[str, Any]): Storage parameters
        statistics_target (Optional[int]): Statistics gathering target
    """

    name: str
    type_name: str
    nullable: bool = True
    primary_key: bool = False
    default: Any = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    comment: Optional[str] = None
    unique: bool = False
    index: bool = False
    auto_increment: AutoIncrementType = AutoIncrementType.NONE
    foreign_key: Optional[str] = None
    on_update: Optional[OnUpdateAction] = None
    on_delete: Optional[OnUpdateAction] = None
    check_constraints: List[str] = field(default_factory=list)
    enum_values: Optional[List[str]] = None
    collation: Optional[str] = None
    generated: Optional[str] = None
    storage_params: Dict[str, Any] = field(default_factory=dict)
    statistics_target: Optional[int] = None

    # PostgreSQL specific attributes
    compression: Optional[PostgreSQLCompressionMethod] = None
    storage_type: PostgreSQLStorageType = PostgreSQLStorageType.PLAIN
    statistics_target: Optional[int] = None
    identity_sequence: Optional[PostgreSQLSequenceInfo] = None
    domain_info: Optional[PostgreSQLDomainInfo] = None
    composite_type: Optional[PostgreSQLCompositeType] = None
    enum_type: Optional[PostgreSQLEnumType] = None
    range_type: Optional[PostgreSQLRangeType] = None

    def __post_init__(self):
        """
        Validate column information after initialization.

        Raises:
            ValidationError: If column information is invalid.
        """
        self.validate()

    def validate(self) -> None:
        """
        Validate column attributes.

        This method performs comprehensive validation of all column attributes
        to ensure they are consistent and valid.

        Raises:
            ValidationError: If validation fails, with detailed error message.
        """
        errors = []

        # Validate name
        if not validate_column_name(self.name):
            errors.append(f"Invalid column name: {self.name}")

        # Validate type name
        try:
            get_sqlalchemy_type_name(self.type_name)
        except ValueError as e:
            errors.append(f"Invalid type name: {str(e)}")

        # Validate string length
        if self.max_length is not None:
            if not validate_numeric_range(self.max_length, min_value=1):
                errors.append(f"Invalid max_length: {self.max_length}")

        # Validate numeric precision/scale
        if self.precision is not None:
            if not validate_numeric_range(self.precision, min_value=1):
                errors.append(f"Invalid precision: {self.precision}")
            if self.scale is not None:
                if not validate_numeric_range(self.scale, min_value=0, max_value=self.precision):
                    errors.append(f"Invalid scale: {self.scale}")

        # Validate foreign key reference format
        if self.foreign_key:
            if '.' not in self.foreign_key or len(self.foreign_key.split('.')) != 2:
                errors.append(f"Invalid foreign key reference: {self.foreign_key}")

        # Validate enum values
        if self.enum_values is not None:
            if not self.enum_values:
                errors.append("Enum type must have at least one value")
            if len(self.enum_values) != len(set(self.enum_values)):
                errors.append("Duplicate enum values not allowed")

        # Validate statistics target
        if self.statistics_target is not None:
            if not validate_numeric_range(self.statistics_target, min_value=0):
                errors.append(f"Invalid statistics target: {self.statistics_target}")

        if errors:
            raise ValidationError("Column validation failed", errors=errors)

    def get_sqlalchemy_type(self) -> str:
        """
        Get the SQLAlchemy type name for this column.

        Returns:
            str: SQLAlchemy type name with any modifiers

        Examples:
            >>> column = ColumnInfo("name", "varchar", max_length=100)
            >>> column.get_sqlalchemy_type()
            'String(length=100)'
        """
        base_type = get_sqlalchemy_type_name(self.type_name)

        # Add type parameters if needed
        if base_type == 'String' and self.max_length:
            return f'String(length={self.max_length})'
        elif base_type == 'Numeric' and self.precision:
            if self.scale is not None:
                return f'Numeric(precision={self.precision}, scale={self.scale})'
            return f'Numeric(precision={self.precision})'
        elif base_type == 'Enum' and self.enum_values:
            values = ', '.join(repr(v) for v in self.enum_values)
            return f'Enum({values}, name="{self.name}_enum")'

        return base_type

    def get_column_args(self) -> Dict[str, Any]:
        """
        Get SQLAlchemy Column constructor arguments.

        Returns:
            Dict[str, Any]: Dictionary of column arguments

        Examples:
            >>> column = ColumnInfo("id", "integer", primary_key=True)
            >>> column.get_column_args()
            {
                'primary_key': True,
                'nullable': False,
                'autoincrement': True
            }
        """
        args = {
            'name': self.name,
            'type_': self.get_sqlalchemy_type(),
            'primary_key': self.primary_key,
            'nullable': self.nullable and not self.primary_key,
        }

        if self.default is not None:
            args['default'] = self.default

        if self.unique:
            args['unique'] = True

        if self.comment:
            args['comment'] = self.comment

        if self.auto_increment != AutoIncrementType.NONE:
            args['autoincrement'] = True

        if self.foreign_key:
            args['foreign_key'] = self.foreign_key

        if self.on_update:
            args['onupdate'] = self.on_update.value

        if self.on_delete:
            args['ondelete'] = self.on_delete.value

        if self.check_constraints:
            args['check_constraint'] = ' AND '.join(self.check_constraints)

        if self.collation:
            args['collation'] = self.collation

        if self.generated:
            args['computed'] = self.generated

        return args

    def is_array_type(self) -> bool:
        """
        Check if column type is an array type.

        Returns:
            bool: True if column type is an array

        Examples:
            >>> column = ColumnInfo("tags", "varchar[]")
            >>> column.is_array_type()
            True
        """
        return self.type_name.endswith('[]')

    def is_numeric_type(self) -> bool:
        """
        Check if column type is numeric.

        Returns:
            bool: True if column type is numeric

        Examples:
            >>> column = ColumnInfo("amount", "decimal")
            >>> column.is_numeric_type()
            True
        """
        numeric_types = {
            'smallint', 'integer', 'bigint', 'decimal', 'numeric',
            'real', 'double precision', 'serial', 'bigserial'
        }
        return self.type_name.lower() in numeric_types

    def is_text_type(self) -> bool:
        """
        Check if column type is textual.

        Returns:
            bool: True if column type is textual

        Examples:
            >>> column = ColumnInfo("description", "text")
            >>> column.is_text_type()
            True
        """
        text_types = {
            'char', 'varchar', 'text', 'citext',
            'character varying', 'character'
        }
        return self.type_name.lower() in text_types

    def __str__(self) -> str:
        """Return string representation of column."""
        parts = [f"{self.name} {self.type_name}"]

        if self.primary_key:
            parts.append("PRIMARY KEY")
        if not self.nullable:
            parts.append("NOT NULL")
        if self.unique:
            parts.append("UNIQUE")
        if self.default is not None:
            parts.append(f"DEFAULT {self.default}")

        return " ".join(parts)

"""
core/context.py: Foreign Key information dataclass.

This module defines the ForeignKeyInfo class which represents detailed information
about foreign key relationships between database tables, including referential
actions, deferrable constraints, and match types.

Author: Nyimbi Odero
Copyright: 2024 Nyimbi Odero
License: MIT
"""



class ReferentialAction(Enum):
    """Enumeration of possible referential actions for foreign keys."""
    NO_ACTION = "NO ACTION"
    RESTRICT = "RESTRICT"
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"


class MatchType(Enum):
    """Enumeration of foreign key match types."""
    SIMPLE = "SIMPLE"
    FULL = "FULL"
    PARTIAL = "PARTIAL"


class DeferrableType(Enum):
    """Enumeration of constraint deferrable types."""
    NOT_DEFERRABLE = "NOT DEFERRABLE"
    IMMEDIATE = "DEFERRABLE INITIALLY IMMEDIATE"
    DEFERRED = "DEFERRABLE INITIALLY DEFERRED"


@dataclass
class ForeignKeyInfo:
    """
    Comprehensive information about a foreign key relationship.

    This class holds detailed information about a foreign key constraint,
    including the related tables and columns, referential actions,
    and various constraint options.

    Attributes:
        constrained_columns (List[str]): Columns in the source table
        referred_table (str): Name of the referenced table
        referred_columns (List[str]): Columns in the referenced table
        name (Optional[str]): Constraint name
        on_update (ReferentialAction): Action on parent update
        on_delete (ReferentialAction): Action on parent delete
        match_type (MatchType): Foreign key match type
        deferrable (DeferrableType): Constraint deferrable type
        validated (bool): Whether constraint is validated
        enabled (bool): Whether constraint is enabled
        comment (Optional[str]): Constraint documentation
        use_index (bool): Whether to create supporting index
        cluster_index (bool): Whether to cluster on supporting index
        inherit_fk (bool): Whether FK is inherited by child tables
    """

    constrained_columns: List[str]
    referred_table: str
    referred_columns: List[str]
    name: Optional[str] = None
    on_update: ReferentialAction = ReferentialAction.NO_ACTION
    on_delete: ReferentialAction = ReferentialAction.NO_ACTION
    match_type: MatchType = MatchType.SIMPLE
    deferrable: DeferrableType = DeferrableType.NOT_DEFERRABLE
    validated: bool = True
    enabled: bool = True
    comment: Optional[str] = None
    use_index: bool = True
    cluster_index: bool = False
    inherit_fk: bool = True

    def __post_init__(self):
        """
        Validate foreign key information after initialization.

        Raises:
            ValidationError: If foreign key information is invalid.
        """
        self.validate()

        # Generate constraint name if not provided
        if not self.name:
            self.name = self.generate_constraint_name()

    def validate(self) -> None:
        """
        Validate foreign key attributes.

        This method performs comprehensive validation of all foreign key attributes
        to ensure they are consistent and valid.

        Raises:
            ValidationError: If validation fails, with detailed error message.
        """
        errors = []

        # Validate column lists
        if not self.constrained_columns:
            errors.append("No constrained columns specified")
        if not self.referred_columns:
            errors.append("No referred columns specified")

        # Validate column counts match
        if len(self.constrained_columns) != len(self.referred_columns):
            errors.append("Number of constrained and referred columns must match")

        # Validate table name
        if not validate_table_name(self.referred_table):
            errors.append(f"Invalid referred table name: {self.referred_table}")

        # Validate column names
        for col in self.constrained_columns:
            if not validate_column_name(col):
                errors.append(f"Invalid constrained column name: {col}")
        for col in self.referred_columns:
            if not validate_column_name(col):
                errors.append(f"Invalid referred column name: {col}")

        # Validate constraint name if provided
        if self.name and not self.name.isidentifier():
            errors.append(f"Invalid constraint name: {self.name}")

        if errors:
            raise ValidationError("Foreign key validation failed", errors=errors)

    def generate_constraint_name(self) -> str:
        """
        Generate a default constraint name.

        Returns:
            str: Generated constraint name

        Examples:
            >>> fk = ForeignKeyInfo(['user_id'], 'users', ['id'])
            >>> fk.generate_constraint_name()
            'fk_user_id_users'
        """
        # Create base name from columns and tables
        parts = []
        parts.append('fk')
        parts.extend(self.constrained_columns)
        parts.append(self.referred_table)

        # Convert to snake case and join
        name = '_'.join(to_snake_case(part) for part in parts)

        # Ensure name length is reasonable
        if len(name) > 63:  # PostgreSQL identifier limit
            # Hash the full name and use first part + hash
            import hashlib
            hash_suffix = hashlib.md5(name.encode()).hexdigest()[:8]
            name = f"{name[:50]}_{hash_suffix}"

        return name

    def get_sqlalchemy_args(self) -> Dict[str, Any]:
        """
        Get SQLAlchemy ForeignKey constructor arguments.

        Returns:
            Dict[str, Any]: Dictionary of foreign key arguments

        Examples:
            >>> fk = ForeignKeyInfo(['user_id'], 'users', ['id'])
            >>> fk.get_sqlalchemy_args()
            {
                'name': 'fk_user_id_users',
                'onupdate': 'NO ACTION',
                'ondelete': 'NO ACTION',
                'deferrable': False
            }
        """
        args = {
            'name': self.name,
            'onupdate': self.on_update.value,
            'ondelete': self.on_delete.value,
            'deferrable': self.deferrable != DeferrableType.NOT_DEFERRABLE,
            'initially': 'DEFERRED' if self.deferrable == DeferrableType.DEFERRED else 'IMMEDIATE',
            'match': self.match_type.value,
            'use_alter': True  # Better for handling circular dependencies
        }

        if self.comment:
            args['comment'] = self.comment

        return args

    def get_referred_key(self) -> str:
        """
        Get the full reference key string.

        Returns:
            str: Reference key in table.column format

        Examples:
            >>> fk = ForeignKeyInfo(['user_id'], 'users', ['id'])
            >>> fk.get_referred_key()
            'users.id'
        """
        return f"{self.referred_table}.{self.referred_columns[0]}"

    def creates_one_to_one(self) -> bool:
        """
        Determine if this foreign key creates a one-to-one relationship.

        This is determined by checking if the constrained columns form a unique key.

        Returns:
            bool: True if this creates a one-to-one relationship
        """
        # This would need additional table info to determine uniqueness
        # For now, we assume false unless specifically set in table info
        return False

    def get_backref_name(self) -> str:
        """
        Generate an appropriate backref name for the relationship.

        Returns:
            str: Generated backref name

        Examples:
            >>> fk = ForeignKeyInfo(['user_id'], 'users', ['id'])
            >>> fk.get_backref_name()
            'user_references'
        """
        # Basic name generation - could be made more sophisticated
        if len(self.constrained_columns) == 1:
            base = self.constrained_columns[0]
            if base.endswith('_id'):
                base = base[:-3]
            return f"{base}_references"
        return f"{self.referred_table}_references"

    def to_sql(self) -> str:
        """
        Generate SQL representation of foreign key constraint.

        Returns:
            str: SQL constraint definition

        Examples:
            >>> fk = ForeignKeyInfo(['user_id'], 'users', ['id'])
            >>> print(fk.to_sql())
            CONSTRAINT fk_user_id_users
            FOREIGN KEY (user_id)
            REFERENCES users (id)
            ON UPDATE NO ACTION
            ON DELETE NO ACTION
        """
        parts = [
            f"CONSTRAINT {self.name}",
            f"FOREIGN KEY ({', '.join(self.constrained_columns)})",
            f"REFERENCES {self.referred_table} ({', '.join(self.referred_columns)})",
            f"ON UPDATE {self.on_update.value}",
            f"ON DELETE {self.on_delete.value}"
        ]

        if self.match_type != MatchType.SIMPLE:
            parts.append(f"MATCH {self.match_type.value}")

        if self.deferrable != DeferrableType.NOT_DEFERRABLE:
            parts.append(self.deferrable.value)

        if not self.validated:
            parts.append("NOT VALID")

        return "\n".join(parts)

    def __str__(self) -> str:
        """Return string representation of foreign key."""
        return f"FK {', '.join(self.constrained_columns)} -> {self.referred_table}({', '.join(self.referred_columns)})"



@dataclass
class IndexColumnInfo:
    """
    Information about a column in an index.

    Attributes:
        name (str): Column name
        ascending (bool): Sort direction (True=ASC, False=DESC)
        nulls_order (NullsOrder): NULL ordering
        collation (Optional[str]): Collation for the column
        opclass (Optional[str]): Operator class for the column
    """
    name: str
    ascending: bool = True
    nulls_order: NullsOrder = NullsOrder.DEFAULT
    collation: Optional[str] = None
    opclass: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation of index column."""
        parts = [self.name]
        if not self.ascending:
            parts.append("DESC")
        if self.nulls_order != NullsOrder.DEFAULT:
            parts.append(self.nulls_order.value)
        if self.collation:
            parts.append(f"COLLATE {self.collation}")
        if self.opclass:
            parts.append(self.opclass)
        return " ".join(parts)

class IndexAlgorithm(Enum):
    """Supported index algorithms."""
    DEFAULT = 'DEFAULT'
    CONCURRENTLY = 'CONCURRENTLY'
    BTREE = 'BTREE'
    HASH = 'HASH'
    GIST = 'GIST'
    GIN = 'GIN'

@dataclass
class IndexInfo:
    """
    Comprehensive information about a database index.

    This class holds detailed information about a database index, including
    its columns, type, method, and various options and parameters.

    Attributes:
        name (str): Index name
        column_names (List[str]): Names of indexed columns
        is_unique (bool): Whether index enforces uniqueness
        method (IndexMethod): Index access method
        index_type (IndexType): Type of index
        columns (List[IndexColumnInfo]): Detailed column information
        include_columns (List[str]): Additional included columns
        tablespace (Optional[str]): Custom tablespace for index
        where_clause (Optional[str]): Partial index predicate
        concurrent (bool): Create index concurrently
        fillfactor (Optional[int]): B-tree fillfactor
        buffering (Optional[str]): GiST buffering option
        fastupdate (Optional[bool]): GIN fast update option
        pages_per_range (Optional[int]): BRIN pages per range
        deduplicate (bool): Remove duplicate entries
        comment (Optional[str]): Index documentation
        storage_parameters (Dict[str, Any]): Additional storage parameters
    """

    name: str
    column_names: List[str]
    is_unique: bool = False
    method: IndexMethod = IndexMethod.BTREE
    index_type: IndexType = IndexType.NORMAL
    columns: List[IndexColumnInfo] = field(default_factory=list)
    include_columns: List[str] = field(default_factory=list)
    tablespace: Optional[str] = None
    where_clause: Optional[str] = None
    concurrent: bool = False
    fillfactor: Optional[int] = None
    buffering: Optional[str] = None
    fastupdate: Optional[bool] = None
    pages_per_range: Optional[int] = None
    deduplicate: bool = False
    comment: Optional[str] = None
    storage_parameters: Dict[str, Any] = field(default_factory=dict)

    # PostgreSQL specific attributes
    access_method: PostgreSQLIndexAccess = field(default_factory=lambda: PostgreSQLIndexAccess(
        method=IndexMethod.BTREE,
        operator_class='default'
    ))
    recheck_cond: Optional[str] = None
    clustering: bool = False
    nulls_distinct: bool = True
    pending: bool = False

    def __post_init__(self):
        """
        Initialize index after creation.

        - Validates all attributes
        - Creates IndexColumnInfo objects if not provided
        - Generates default name if needed
        """
        # Create IndexColumnInfo objects if only names provided
        if not self.columns and self.column_names:
            self.columns = [IndexColumnInfo(name) for name in self.column_names]

        # Validate
        self.validate()

    def validate(self) -> None:
        """
        Validate index attributes.

        This method performs comprehensive validation of all index attributes
        to ensure they are consistent and valid.

        Raises:
            ValidationError: If validation fails, with detailed error message.
        """
        errors = []

        # Validate name
        if not self.name.isidentifier():
            errors.append(f"Invalid index name: {self.name}")

        # Validate columns
        if not self.column_names:
            errors.append("No columns specified for index")

        for col in self.column_names:
            if not validate_column_name(col):
                errors.append(f"Invalid column name: {col}")

        # Validate included columns
        for col in self.include_columns:
            if not validate_column_name(col):
                errors.append(f"Invalid included column name: {col}")
            if col in self.column_names:
                errors.append(f"Column {col} cannot be both indexed and included")

        # Validate fillfactor
        if self.fillfactor is not None:
            if not 10 <= self.fillfactor <= 100:
                errors.append("Fillfactor must be between 10 and 100")

        # Validate pages_per_range
        if self.pages_per_range is not None and self.pages_per_range < 1:
            errors.append("Pages per range must be positive")

        # Method-specific validations
        if self.method == IndexMethod.HASH and self.is_unique:
            errors.append("Hash indexes cannot be unique")

        if self.method != IndexMethod.BTREE and self.deduplicate:
            errors.append("Only btree indexes support deduplication")

        if errors:
            raise ValidationError("Index validation failed", errors=errors)

    def get_sqlalchemy_args(self) -> Dict[str, Any]:
        """
        Get SQLAlchemy Index constructor arguments.

        Returns:
            Dict[str, Any]: Dictionary of index arguments

        Examples:
            >>> idx = IndexInfo("idx_users_email", ["email"], is_unique=True)
            >>> idx.get_sqlalchemy_args()
            {
                'name': 'idx_users_email',
                'unique': True,
                'postgresql_using': 'btree'
            }
        """
        args = {
            'name': self.name,
            'unique': self.is_unique
        }

        # Add method if not btree
        if self.method != IndexMethod.BTREE:
            args['postgresql_using'] = self.method.value

        # Add tablespace if specified
        if self.tablespace:
            args['postgresql_tablespace'] = self.tablespace

        # Add partial index clause
        if self.where_clause:
            args['postgresql_where'] = self.where_clause

        # Add storage parameters
        if self.storage_parameters:
            args['postgresql_with'] = self.storage_parameters

        # Add included columns
        if self.include_columns:
            args['postgresql_include'] = self.include_columns

        return args

    def get_create_statement(self) -> str:
        """
        Generate CREATE INDEX statement.

        Returns:
            str: SQL CREATE INDEX statement

        Examples:
            >>> idx = IndexInfo("idx_users_email", ["email"], is_unique=True)
            >>> print(idx.get_create_statement())
            CREATE UNIQUE INDEX idx_users_email
            ON users USING btree (email);
        """
        parts = []

        # Basic statement
        parts.append("CREATE")
        if self.is_unique:
            parts.append("UNIQUE")
        parts.append("INDEX")
        if self.concurrent:
            parts.append("CONCURRENTLY")
        parts.append(self.name)

        # Index definition
        parts.append("USING")
        parts.append(self.method.value)

        # Columns
        col_parts = []
        for col in self.columns:
            col_parts.append(str(col))
        parts.append(f"({', '.join(col_parts)})")

        # Include clause
        if self.include_columns:
            parts.append(f"INCLUDE ({', '.join(self.include_columns)})")

        # Where clause
        if self.where_clause:
            parts.append(f"WHERE {self.where_clause}")

        # Storage parameters
        if self.storage_parameters or self.fillfactor:
            params = self.storage_parameters.copy()
            if self.fillfactor:
                params['fillfactor'] = self.fillfactor
            param_strs = [f"{k}={v}" for k, v in params.items()]
            parts.append(f"WITH ({', '.join(param_strs)})")

        # Tablespace
        if self.tablespace:
            parts.append(f"TABLESPACE {self.tablespace}")

        return " ".join(parts) + ";"

    def estimate_size(self, row_count: int) -> int:
        """
        Estimate index size in bytes based on column types and row count.

        Args:
            row_count (int): Estimated number of rows

        Returns:
            int: Estimated size in bytes

        Examples:
            >>> idx = IndexInfo("idx_users_email", ["email"])
            >>> idx.estimate_size(1000000)
            24000000  # Approximate size for 1M email addresses
        """
        # This is a very rough estimate
        bytes_per_key = 20  # Assume average key size
        overhead = 1.2  # Index overhead factor

        if self.method == IndexMethod.HASH:
            overhead = 1.5  # Hash tables need more space
        elif self.method in (IndexMethod.GIN, IndexMethod.GIST):
            overhead = 2.0  # These index types have more overhead

        return int(row_count * bytes_per_key * overhead)

    def can_enforce_unique(self) -> bool:
        """
        Check if this index can enforce uniqueness constraint.

        Returns:
            bool: True if index can enforce uniqueness

        Examples:
            >>> idx = IndexInfo("idx_users_email", ["email"], method=IndexMethod.BTREE)
            >>> idx.can_enforce_unique()
            True
        """
        # Only btree indexes can enforce uniqueness
        if self.method != IndexMethod.BTREE:
            return False

        # Partial indexes can't enforce table-wide uniqueness
        if self.where_clause:
            return False

        return True

    def supports_order_by(self) -> bool:
        """
        Check if this index supports ORDER BY optimization.

        Returns:
            bool: True if index can be used for sorting

        Examples:
            >>> idx = IndexInfo("idx_users_name", ["name"])
            >>> idx.supports_order_by()
            True
        """
        # Only btree indexes support ordering
        return self.method == IndexMethod.BTREE

    def __str__(self) -> str:
        """Return string representation of index."""
        prefix = "UNIQUE " if self.is_unique else ""
        cols = ", ".join(self.column_names)
        return f"{prefix}INDEX {self.name} ON ({cols})"





@dataclass
class ExclusionElement:
    """
    Represents an element in an exclusion constraint.

    Attributes:
        column (str): Column or expression
        operator (ExclusionOperator): Comparison operator
        opclass (Optional[str]): Optional operator class
    """
    column: str
    operator: ExclusionOperator
    opclass: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation of exclusion element."""
        base = f"{self.column} WITH {self.operator.value}"
        if self.opclass:
            base = f"{base} {self.opclass}"
        return base


@dataclass
class ConstraintInfo:
    """
    Comprehensive information about a database constraint.

    This class holds detailed information about a database constraint,
    including its type, affected columns, and various options.

    Attributes:
        name (str): Constraint name
        constraint_type (ConstraintType): Type of constraint
        columns (List[str]): Affected column names
        definition (str): Constraint definition/expression
        deferrable (DeferrableStatus): Deferrable status
        validated (bool): Whether constraint is validated
        enabled (bool): Whether constraint is enabled
        rely (bool): Whether optimizer can rely on constraint
        no_inherit (bool): Whether constraint is non-inheritable
        comment (Optional[str]): Constraint documentation
        index_tablespace (Optional[str]): Tablespace for index
        exclusion_elements (List[ExclusionElement]): For EXCLUDE constraints
        using_method (Optional[str]): Index method for EXCLUDE/UNIQUE
        storage_parameters (Dict[str, Any]): Additional parameters
        nulls_distinct (bool): NULL values considered distinct
        nulls_not_distinct (bool): NULL values considered equal
        include_columns (List[str]): Included columns in index
    """

    name: str
    constraint_type: ConstraintType
    columns: List[str]
    definition: str = ""
    deferrable: DeferrableStatus = DeferrableStatus.NOT_DEFERRABLE
    validated: bool = True
    enabled: bool = True
    rely: bool = True
    no_inherit: bool = False
    comment: Optional[str] = None
    index_tablespace: Optional[str] = None
    exclusion_elements: List[ExclusionElement] = field(default_factory=list)
    using_method: Optional[str] = None
    storage_parameters: Dict[str, Any] = field(default_factory=dict)
    nulls_distinct: bool = True
    nulls_not_distinct: bool = False
    include_columns: List[str] = field(default_factory=list)

    def __post_init__(self):
        """
        Initialize constraint after creation.

        - Validates all attributes
        - Sets default definition for certain constraint types
        - Ensures consistency between attributes
        """
        # Set default definition if not provided
        if not self.definition:
            self.definition = self._generate_default_definition()

        # Validate
        self.validate()

    def validate(self) -> None:
        """
        Validate constraint attributes.

        This method performs comprehensive validation of all constraint attributes
        to ensure they are consistent and valid.

        Raises:
            ValidationError: If validation fails, with detailed error message.
        """
        errors = []

        # Validate name
        if not self.name.isidentifier():
            errors.append(f"Invalid constraint name: {self.name}")

        # Validate columns
        if not self.columns and self.constraint_type != ConstraintType.CHECK:
            errors.append("No columns specified for constraint")

        for col in self.columns:
            if not validate_column_name(col):
                errors.append(f"Invalid column name: {col}")

        # Type-specific validations
        if self.constraint_type == ConstraintType.CHECK:
            if not self.definition:
                errors.append("CHECK constraint requires definition")

        elif self.constraint_type == ConstraintType.EXCLUDE:
            if not self.exclusion_elements:
                errors.append("EXCLUDE constraint requires exclusion elements")

        # Validate included columns
        for col in self.include_columns:
            if not validate_column_name(col):
                errors.append(f"Invalid included column name: {col}")
            if col in self.columns:
                errors.append(f"Column {col} cannot be both constrained and included")

        # Validate nulls handling options
        if self.nulls_distinct and self.nulls_not_distinct:
            errors.append("Cannot specify both NULLS DISTINCT and NULLS NOT DISTINCT")

        if errors:
            raise ValidationError("Constraint validation failed", errors=errors)

    def _generate_default_definition(self) -> str:
        """
        Generate default constraint definition based on type.

        Returns:
            str: Generated constraint definition
        """
        if self.constraint_type == ConstraintType.UNIQUE:
            return f"UNIQUE ({', '.join(self.columns)})"
        elif self.constraint_type == ConstraintType.PRIMARY_KEY:
            return f"PRIMARY KEY ({', '.join(self.columns)})"
        elif self.constraint_type == ConstraintType.NOT_NULL:
            return f"NOT NULL ({', '.join(self.columns)})"
        elif self.constraint_type == ConstraintType.EXCLUDE:
            elements = [str(elem) for elem in self.exclusion_elements]
            return f"EXCLUDE ({', '.join(elements)})"
        return ""

    def get_sqlalchemy_args(self) -> Dict[str, Any]:
        """
        Get SQLAlchemy constraint constructor arguments.

        Returns:
            Dict[str, Any]: Dictionary of constraint arguments

        Examples:
            >>> const = ConstraintInfo("uk_email", ConstraintType.UNIQUE, ["email"])
            >>> const.get_sqlalchemy_args()
            {
                'name': 'uk_email',
                'unique': True,
                'columns': ['email']
            }
        """
        args = {
            'name': self.name
        }

        if self.constraint_type == ConstraintType.UNIQUE:
            args['unique'] = True
            args['columns'] = self.columns
            if self.using_method:
                args['postgresql_using'] = self.using_method
            if self.nulls_not_distinct:
                args['postgresql_nulls_not_distinct'] = True

        elif self.constraint_type == ConstraintType.CHECK:
            args['check'] = True
            args['sqltext'] = self.definition

        elif self.constraint_type == ConstraintType.PRIMARY_KEY:
            args['primary_key'] = True
            args['columns'] = self.columns

        elif self.constraint_type == ConstraintType.EXCLUDE:
            args['postgresql_exclude'] = self.get_exclusion_definition()
            if self.using_method:
                args['postgresql_using'] = self.using_method

        # Common options
        if self.deferrable != DeferrableStatus.NOT_DEFERRABLE:
            args['deferrable'] = True
            args['initially'] = 'DEFERRED' if self.deferrable == DeferrableStatus.DEFERRED else 'IMMEDIATE'

        if self.index_tablespace:
            args['postgresql_tablespace'] = self.index_tablespace

        if self.include_columns:
            args['postgresql_include'] = self.include_columns

        return args

    def get_create_statement(self) -> str:
        """
        Generate ALTER TABLE ADD CONSTRAINT statement.

        Returns:
            str: SQL constraint definition

        Examples:
            >>> const = ConstraintInfo("uk_email", ConstraintType.UNIQUE, ["email"])
            >>> print(const.get_create_statement())
            ALTER TABLE {table_name} ADD CONSTRAINT uk_email UNIQUE (email);
        """
        parts = [
            "ADD CONSTRAINT",
            self.name
        ]

        # Main constraint definition
        if self.constraint_type == ConstraintType.CHECK:
            parts.append(f"CHECK ({self.definition})")
        elif self.constraint_type == ConstraintType.UNIQUE:
            parts.append(f"UNIQUE ({', '.join(self.columns)})")
            if self.using_method:
                parts.append(f"USING {self.using_method}")
            if self.nulls_not_distinct:
                parts.append("NULLS NOT DISTINCT")
        elif self.constraint_type == ConstraintType.PRIMARY_KEY:
            parts.append(f"PRIMARY KEY ({', '.join(self.columns)})")
        elif self.constraint_type == ConstraintType.EXCLUDE:
            parts.append(self.get_exclusion_definition())
            if self.using_method:
                parts.append(f"USING {self.using_method}")

        # Common options
        if self.deferrable != DeferrableStatus.NOT_DEFERRABLE:
            parts.append(self.deferrable.value)

        if not self.validated:
            parts.append("NOT VALID")

        if self.no_inherit:
            parts.append("NO INHERIT")

        if self.index_tablespace:
            parts.append(f"USING INDEX TABLESPACE {self.index_tablespace}")

        if self.include_columns:
            parts.append(f"INCLUDE ({', '.join(self.include_columns)})")

        return " ".join(parts)

    def get_exclusion_definition(self) -> str:
        """
        Get the definition part of an exclusion constraint.

        Returns:
            str: Exclusion constraint definition

        Examples:
            >>> const = ConstraintInfo("ex_timespan", ConstraintType.EXCLUDE,
            ...                       exclusion_elements=[
            ...                           ExclusionElement("timespan", ExclusionOperator.OVERLAPS)
            ...                       ])
            >>> const.get_exclusion_definition()
            'EXCLUDE (timespan WITH &&)'
        """
        if not self.exclusion_elements:
            return ""
        elements = [str(elem) for elem in self.exclusion_elements]
        return f"EXCLUDE ({', '.join(elements)})"

    def can_be_deferred(self) -> bool:
        """
        Check if this type of constraint can be deferred.

        Returns:
            bool: True if constraint type supports deferral

        Examples:
            >>> const = ConstraintInfo("pk_id", ConstraintType.PRIMARY_KEY, ["id"])
            >>> const.can_be_deferred()
            True
        """
        return self.constraint_type in {
            ConstraintType.UNIQUE,
            ConstraintType.PRIMARY_KEY,
            ConstraintType.FOREIGN_KEY,
            ConstraintType.EXCLUDE
        }

    def requires_index(self) -> bool:
        """
        Check if this constraint requires an index.

        Returns:
            bool: True if constraint requires an index

        Examples:
            >>> const = ConstraintInfo("uk_email", ConstraintType.UNIQUE, ["email"])
            >>> const.requires_index()
            True
        """
        return self.constraint_type in {
            ConstraintType.UNIQUE,
            ConstraintType.PRIMARY_KEY,
            ConstraintType.EXCLUDE
        }

    def __str__(self) -> str:
        """Return string representation of constraint."""
        constraint_desc = f"{self.constraint_type.value}"
        if self.columns:
            constraint_desc += f" ({', '.join(self.columns)})"
        return f"{self.name}: {constraint_desc}"






@dataclass
class PartitionBoundSpec:
    """
    Specification for partition bounds.

    Attributes:
        strategy (PartitioningStrategy): Partitioning strategy
        columns (List[str]): Columns used for partitioning
        bounds (Union[List[Any], int]): Boundary values or modulus
    """
    strategy: PartitioningStrategy
    columns: List[str]
    bounds: Union[List[Any], int]

    def __str__(self) -> str:
        """Return string representation of partition bounds."""
        if self.strategy == PartitioningStrategy.HASH:
            return f"HASH ({', '.join(self.columns)}) WITH (modulus {self.bounds})"
        elif self.strategy == PartitioningStrategy.LIST:
            values = ", ".join(str(v) for v in self.bounds)
            return f"LIST ({', '.join(self.columns)}) VALUES ({values})"
        else:  # RANGE
            from_values = ", ".join(str(v) for v in self.bounds[0])
            to_values = ", ".join(str(v) for v in self.bounds[1])
            return f"RANGE ({', '.join(self.columns)}) FROM ({from_values}) TO ({to_values})"


@dataclass
class InheritanceInfo:
    """
    Information about table inheritance.

    Attributes:
        parent_table (str): Name of parent table
        columns (List[str]): Explicitly inherited columns
        constraints (List[str]): Inherited constraints
        storage_params (Dict[str, Any]): Inherited storage params
    """
    parent_table: str
    columns: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    storage_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TablespaceInfo:
    """
    Information about table tablespace configuration.

    Attributes:
        name (str): Tablespace name
        options (Dict[str, Any]): Tablespace options
        index_tablespace (Optional[str]): Separate tablespace for indexes
    """
    name: str
    options: Dict[str, Any] = field(default_factory=dict)
    index_tablespace: Optional[str] = None

def _format_storage_params(params: Dict[str, Any]) -> str:
    """Format storage parameters for SQL output."""
    if not params:
        return ""
    param_strs = []
    for key, value in sorted(params.items()):
        if isinstance(value, bool):
            value = str(value).lower()
        elif isinstance(value, str):
            value = f"'{value}'"
        param_strs.append(f"{key}={value}")
    return f"WITH ({', '.join(param_strs)})"







class RelationshipType(Enum):
    """Enumeration of supported relationship types."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    ONE_TO_ONE_POLYMORPHIC = "one_to_one_polymorphic"
    ONE_TO_MANY_POLYMORPHIC = "one_to_many_polymorphic"
    MANY_TO_ONE_POLYMORPHIC = "many_to_one_polymorphic"
    MANY_TO_MANY_POLYMORPHIC = "many_to_many_polymorphic"


class CascadeOption(Enum):
    """Enumeration of SQLAlchemy cascade options."""
    SAVE_UPDATE = "save-update"
    DELETE = "delete"
    DELETE_ORPHAN = "delete-orphan"
    MERGE = "merge"
    REFRESH_EXPIRE = "refresh-expire"
    EXPUNGE = "expunge"
    ALL = "all"


class LazyLoadOption(Enum):
    """Enumeration of SQLAlchemy lazy loading options."""
    SELECT = "select"
    JOINED = "joined"
    SUBQUERY = "subquery"
    SELECTIN = "selectin"
    IMMEDIATE = "immediate"
    NOLOAD = "noload"
    RAISE = "raise"
    RAISE_ON_SQL = "raise_on_sql"
    DYNAMIC = "dynamic"


class JoinType(Enum):
    """Enumeration of join types."""
    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"


@dataclass
class JoinCondition:
    """
    Represents a join condition between tables.

    Attributes:
        local_column (str): Column in the source table
        remote_column (str): Column in the target table
        operator (str): Join operator (default '==')
        join_type (JoinType): Type of join
        where_clause (Optional[str]): Additional WHERE clause
    """
    local_column: str
    remote_column: str
    operator: str = "=="
    join_type: JoinType = JoinType.INNER
    where_clause: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation of join condition."""
        return f"{self.local_column} {self.operator} {self.remote_column}"

@dataclass
class TableInfo:
    """
    Comprehensive information about a database table.

    This class holds detailed information about a database table, including its
    structure, constraints, indexes, and various PostgreSQL-specific features.

    Attributes:
        name (str): Table name
        schema (str): Schema name
        type (TableType): Type of table
        columns (List[ColumnInfo]): Table columns
        primary_key (List[str]): Primary key column names
        foreign_keys (List[ForeignKeyInfo]): Foreign key constraints
        indexes (List[IndexInfo]): Table indexes
        constraints (List[ConstraintInfo]): Table constraints
        comment (Optional[str]): Table documentation
        tablespace (Optional[TablespaceInfo]): Tablespace configuration
        inheritance (Optional[InheritanceInfo]): Inheritance information
        partition_key (Optional[PartitionBoundSpec]): Partitioning specification
        partition_of (Optional[str]): Parent partitioned table
        partition_bound (Optional[PartitionBoundSpec]): Partition bounds
        replica_identity (ReplicaIdentity): Replica identity setting
        storage_params (Dict[str, Any]): Storage parameters
        row_security (bool): Row-level security enabled
        force_row_security (bool): Force RLS for owner
        statistics_target (Optional[int]): Default statistics target
        options (Dict[str, Any]): Additional table options
        triggers (List[str]): Trigger names
        grants (Dict[str, List[str]]): Access grants by role
    """
    name: str
    schema: str = "public"
    type: TableType = TableType.REGULAR

    # Structure
    columns: List['ColumnInfo'] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List['ForeignKeyInfo'] = field(default_factory=list)
    indexes: List['IndexInfo'] = field(default_factory=list)
    constraints: List['ConstraintInfo'] = field(default_factory=list)
    comment: Optional[str] = None

    # Storage and organization
    tablespace: Optional[TablespaceInfo] = None
    inheritance: Optional[InheritanceInfo] = None
    storage_params: Dict[str, Any] = field(default_factory=dict)

    # Partitioning
    partition_key: Optional[PartitionBoundSpec] = None
    partition_of: Optional[str] = None
    partition_bound: Optional[PartitionBoundSpec] = None

    # Replication and security
    replica_identity: ReplicaIdentity = ReplicaIdentity.DEFAULT
    row_security: bool = False
    force_row_security: bool = False

    # Statistics and performance
    statistics_target: Optional[int] = None
    options: Dict[str, Any] = field(default_factory=dict)

    # Additional features
    # triggers: List[str] = field(default_factory=list)
    grants: Dict[str, List[str]] = field(default_factory=dict)

    # PostgreSQL specific attributes
    policies: List[PostgreSQLPolicyInfo] = field(default_factory=list)
    triggers: List[PostgreSQLTriggerInfo] = field(default_factory=list)
    statistics: Dict[str, PostgreSQLStatisticsInfo] = field(default_factory=dict)
    extensions: List[PostgreSQLExtensionInfo] = field(default_factory=list)
    view_info: Optional[PostgreSQLViewInfo] = None
    partition_info: Optional[PostgreSQLPartitionInfo] = None
    vacuum_settings: Dict[str, Any] = field(default_factory=dict)


    def __post_init__(self):
        """
        Initialize table information after creation.

        - Validates all attributes
        - Ensures internal consistency
        - Sets up derived attributes
        """
        # Initialize collections if None
        if self.columns is None:
            self.columns = []
        if self.primary_key is None:
            self.primary_key = []
        if self.foreign_keys is None:
            self.foreign_keys = []
        if self.indexes is None:
            self.indexes = []
        if self.constraints is None:
            self.constraints = []

        # Validate
        self.validate()

    def validate(self) -> None:
        """
        Validate table attributes.

        This method performs comprehensive validation of all table attributes
        to ensure they are consistent and valid.

        Raises:
            ValidationError: If validation fails, with detailed error message.
        """
        errors = []

        # Validate basic attributes
        if not validate_table_name(self.name):
            errors.append(f"Invalid table name: {self.name}")
        if not validate_table_name(self.schema):
            errors.append(f"Invalid schema name: {self.schema}")

        # Validate columns
        if not self.columns:
            errors.append("Table must have at least one column")

        column_names = set()
        for col in self.columns:
            if col.name in column_names:
                errors.append(f"Duplicate column name: {col.name}")
            column_names.add(col.name)

        # Validate primary key
        for col in self.primary_key:
            if col not in column_names:
                errors.append(f"Primary key column not found: {col}")

        # Validate foreign keys
        for fk in self.foreign_keys:
            for col in fk.constrained_columns:
                if col not in column_names:
                    errors.append(f"Foreign key column not found: {col}")

        # Validate partitioning
        if self.partition_key and self.partition_of:
            errors.append("Table cannot be both partitioned and a partition")

        if self.partition_bound and not self.partition_of:
            errors.append("Partition bounds specified but not a partition")

        # Validate inheritance
        if self.inheritance:
            if self.partition_of:
                errors.append("Table cannot be both inherited and a partition")
            if not validate_table_name(self.inheritance.parent_table):
                errors.append(f"Invalid parent table name: {self.inheritance.parent_table}")

        # Validate statistics target
        if self.statistics_target is not None:
            if not isinstance(self.statistics_target, int) or self.statistics_target < 0:
                errors.append(f"Invalid statistics target: {self.statistics_target}")

        # Validate tablespace
        if self.tablespace:
            if not validate_table_name(self.tablespace.name):
                errors.append(f"Invalid tablespace name: {self.tablespace.name}")
            if self.tablespace.index_tablespace:
                if not validate_table_name(self.tablespace.index_tablespace):
                    errors.append(f"Invalid index tablespace name: {self.tablespace.index_tablespace}")

        # Storage parameter validation
        for param in self.storage_params:
            if not isinstance(param, str):
                errors.append(f"Invalid storage parameter name: {param}")

        if errors:
            raise ValidationError("Table validation failed", errors=errors)

    def get_qualified_name(self) -> str:
        """
        Get fully qualified table name.

        Returns:
            str: Schema-qualified table name

        Examples:
            >>> table = TableInfo("users", schema="app")
            >>> table.get_qualified_name()
            'app.users'
        """
        return f"{self.schema}.{self.name}"

    def get_model_name(self) -> str:
        """
        Get the Python model class name for this table.

        Returns:
            str: Model class name in PascalCase

        Examples:
            >>> table = TableInfo("user_profiles")
            >>> table.get_model_name()
            'UserProfile'
        """
        return to_pascal_case(self.name)

    def has_identity_column(self) -> bool:
        """
        Check if table has an identity/serial column.

        Returns:
            bool: True if table has an identity column

        Examples:
            >>> table = TableInfo("users", columns=[
            ...     ColumnInfo("id", "serial", primary_key=True)
            ... ])
            >>> table.has_identity_column()
            True
        """
        return any(
            col.auto_increment != AutoIncrementType.NONE
            for col in self.columns
        )
    def get_create_statement(self) -> str:
        """
        Generate CREATE TABLE statement.

        Returns:
            str: Complete CREATE TABLE statement

        Examples:
            >>> table = TableInfo("users", columns=[
            ...     ColumnInfo("id", "serial", primary_key=True),
            ...     ColumnInfo("email", "varchar", max_length=255, unique=True)
            ... ])
            >>> print(table.get_create_statement())
            CREATE TABLE public.users (
                id serial PRIMARY KEY,
                email varchar(255) UNIQUE
            );
        """
        parts = []

        # Basic statement start
        create_line = ["CREATE"]
        if self.type == TableType.UNLOGGED:
            create_line.append("UNLOGGED")
        elif self.type == TableType.TEMPORARY:
            create_line.append("TEMPORARY")
        create_line.append("TABLE")
        if self.partition_of:
            create_line.append("IF NOT EXISTS")
        parts.append(" ".join(create_line))

        # Table name
        parts.append(self.get_qualified_name())

        # Partition of clause
        if self.partition_of:
            parts.append(f"PARTITION OF {self.partition_of}")
            if self.partition_bound:
                parts.append(str(self.partition_bound))
        else:
            # Column definitions
            column_defs = []
            for col in self.columns:
                column_defs.append(self._get_sql_column_definition(col))

            # Table constraints
            for const in self.constraints:
                if const.name:  # Named constraints only
                    column_defs.append(f"CONSTRAINT {const.name} {const.definition}")

            # Combine column definitions and constraints
            parts.append(f"(\n{indent_text(',\n'.join(column_defs), '    ')}\n)")

            # Partitioned by clause
            if self.partition_key:
                parts.append(f"PARTITION BY {str(self.partition_key)}")

        # Inheritance
        if self.inheritance:
            parts.append(f"INHERITS ({self.inheritance.parent_table})")

        # Storage parameters
        if self.storage_params:
            parts.append(_format_storage_params(self.storage_params))

        # Tablespace
        if self.tablespace:
            parts.append(f"TABLESPACE {self.tablespace.name}")
            if self.tablespace.options:
                parts.append(_format_storage_params(self.tablespace.options))

        # Row security
        if self.row_security:
            parts.append("ENABLE ROW LEVEL SECURITY")
        if self.force_row_security:
            parts.append("FORCE ROW LEVEL SECURITY")

        return " ".join(parts) + ";"

    def _get_sql_column_definition(self, column: 'ColumnInfo') -> str:
        """
        Generate SQL DDL column definition.

        Args:
            column (ColumnInfo): Column to generate definition for

        Returns:
            str: SQL DDL column definition

        Example:
            "user_id integer NOT NULL DEFAULT 1"
        """
        parts = [column.name, column.type_name]

        if not column.nullable:
            parts.append("NOT NULL")
        if column.default is not None:
            parts.append(f"DEFAULT {column.default}")
        if column.unique:
            parts.append("UNIQUE")
        if column.primary_key:
            parts.append("PRIMARY KEY")
        if column.check_constraints:
            for check in column.check_constraints:
                parts.append(f"CHECK ({check})")
        if column.collation:
            parts.append(f"COLLATE {column.collation}")
        if column.storage_params:
            parts.append(_format_storage_params(column.storage_params))

        return " ".join(parts)

    def analyze_schema(self) -> Dict[str, Any]:
        """
        Analyze table schema and return detailed information.

        Returns:
            Dict[str, Any]: Dictionary containing schema analysis

        Examples:
            >>> table = TableInfo("users", columns=[...])
            >>> analysis = table.analyze_schema()
            >>> analysis['has_identity']
            True
            >>> analysis['primary_key_type']
            'single_column'
        """
        analysis = {
            'table_type': self.type.value,
            'column_count': len(self.columns),
            'has_identity': self.has_identity_column(),
            'has_nullable_columns': any(col.nullable for col in self.columns),
            'primary_key_type': self._analyze_primary_key(),
            'foreign_key_count': len(self.foreign_keys),
            'index_count': len(self.indexes),
            'is_partitioned': bool(self.partition_key),
            'is_partition': bool(self.partition_of),
            'has_inheritance': bool(self.inheritance),
            'has_row_security': self.row_security,
            'column_types': self._analyze_column_types(),
            'constraint_types': self._analyze_constraints(),
            'index_types': self._analyze_indexes(),
            'storage_size': self._estimate_storage_size()
        }

        # Additional security analysis
        analysis['security'] = {
            'has_row_security': self.row_security,
            'force_row_security': self.force_row_security,
            'grants': self.grants.copy() if self.grants else {},
            'has_column_grants': any(
                col.name in (grant for grants in self.grants.values() for grant in grants)
                for col in self.columns
            )
        }

        return analysis


    def _analyze_foreign_keys(self) -> Dict[str, int]:
        """
        Analyze foreign key actions (e.g., CASCADE, SET NULL) used in the table.

        Returns:
            Dict[str, int]: Counts of each foreign key action type.
        """
        fk_actions = {}
        for fk in self.foreign_keys:
            action = fk.on_delete or 'NO ACTION'  # Default to 'NO ACTION' if None
            fk_actions[action] = fk_actions.get(action, 0) + 1
        return fk_actions

    def _analyze_primary_key(self) -> str:
        """Analyze primary key configuration."""
        if not self.primary_key:
            return 'none'
        elif len(self.primary_key) == 1:
            return 'single_column'
        return 'composite'

    def _analyze_column_types(self) -> Dict[str, int]:
        """Count usage of each column type."""
        type_counts = {}
        for col in self.columns:
            base_type = col.type_name.split('(')[0].lower()
            type_counts[base_type] = type_counts.get(base_type, 0) + 1
        return type_counts

    def _analyze_constraints(self) -> Dict[str, int]:
        """Count each type of constraint."""
        constraint_counts = {}
        for const in self.constraints:
            const_type = const.constraint_type.value
            constraint_counts[const_type] = constraint_counts.get(const_type, 0) + 1
        return constraint_counts

    def _analyze_indexes(self) -> Dict[str, int]:
        """Count each type of index."""
        index_counts = {}
        for idx in self.indexes:
            idx_method = idx.method.value
            index_counts[idx_method] = index_counts.get(idx_method, 0) + 1
        return index_counts

    def _estimate_storage_size(self) -> int:
        """
        Estimate approximate storage size in bytes.
        This is a rough estimate based on column types.
        """
        total_bytes = 0
        for col in self.columns:
            # Get base size for type
            base_size = {
                'smallint': 2,
                'integer': 4,
                'bigint': 8,
                'double': 8,
                'text': 32,  # Average text size
                'varchar': min(col.max_length or 255, 255),
                'timestamp': 8,
                'date': 4,
                'boolean': 1,
                'uuid': 16,
                'json': 100,  # Average JSON size
                'jsonb': 100,
                'bytea': 100,  # Average BYTEA size
            }.get(col.type_name.lower(), 8)  # Default to 8 bytes

            # Adjust for NULL storage
            if col.nullable:
                total_bytes += 1  # NULL bitmap

            total_bytes += base_size

        # Add overhead
        total_bytes += 24  # Tuple header
        total_bytes += len(self.columns) * 4  # Alignment padding

        return total_bytes


    def get_sqlalchemy_model(self) -> str:
        """
        Generate SQLAlchemy model class definition.

        Returns:
            str: Complete model class definition

        Examples:
            >>> table = TableInfo("users", columns=[
            ...     ColumnInfo("id", "serial", primary_key=True),
            ...     ColumnInfo("email", "varchar", max_length=255, unique=True)
            ... ])
            >>> print(table.get_sqlalchemy_model())
            class User(Model):
                __tablename__ = 'users'
                __table_args__ = {'schema': 'public'}

                id = Column(Integer, primary_key=True)
                email = Column(String(255), unique=True)
        """
        model_name = self.get_model_name()
        parts = []

        # Class definition
        parts.append(f"class {model_name}(Model):")

        # Add docstring
        docstring = f'"""\n{self.comment or "SQLAlchemy model for " + self.name} table.\n\n'
        docstring += "Attributes:\n"
        for col in self.columns:
            docstring += f"    {col.name} ({col.get_sqlalchemy_type()}): "
            docstring += f"{col.comment or 'No description'}\n"
        docstring += '"""'
        parts.append(indent_text(docstring, "    "))

        # Table configuration
        parts.append(f"    __tablename__ = '{self.name}'")
        if self.schema != 'public':
            parts.append(f"    __schema__ = '{self.schema}'")

        # Table arguments
        table_args = self._get_table_args()
        if table_args:
            if len(table_args) == 1:
                parts.append(f"    __table_args__ = {table_args[0]}")
            else:
                args_str = ",\n        ".join(table_args)
                parts.append("    __table_args__ = (\n        " + args_str + "\n    )")

        # Columns
        parts.append("")  # Empty line before columns
        for col in self.columns:
            parts.append(f"    {col.name} = {self._get_sqlalchemy_column_definition(col)}")

        # Relationships
        if self.foreign_keys:
            parts.append("")  # Empty line before relationships
            for rel in self._generate_relationships():
                parts.append(f"    {rel}")

        # Add any hybrid properties
        hybrid_props = self._generate_hybrid_properties()
        if hybrid_props:
            parts.append("")  # Empty line before hybrid properties
            parts.extend(hybrid_props)

        # Add model-level methods
        parts.extend(self._generate_model_methods())

        return "\n".join(parts)

    def _get_table_args(self) -> List[str]:
        """Generate SQLAlchemy __table_args__ tuple contents."""
        args = []

        # Add schema
        if self.schema != 'public':
            args.append(f"schema='{self.schema}'")

        # Add constraints
        for constraint in self.constraints:
            args.append(constraint.get_sqlalchemy_args())

        # Add indexes
        for index in self.indexes:
            args.append(index.get_sqlalchemy_args())

        # Add tablespace
        if self.tablespace:
            args.append(f"postgresql_tablespace='{self.tablespace.name}'")

        # Add storage parameters
        if self.storage_params:
            params = ", ".join(f"{k}={repr(v)}" for k, v in self.storage_params.items())
            args.append(f"postgresql_with=({params})")

        # Add inheritance
        if self.inheritance:
            args.append(f"inherits={self.inheritance.parent_table}")

        # Add partitioning
        if self.partition_key:
            args.append(f"postgresql_partition_by={repr(str(self.partition_key))}")

        # Return formatted arguments
        return ["{" + ", ".join(args) + "}"] if args else []

    def _get_sqlalchemy_column_definition(self, column: 'ColumnInfo') -> str:
        """
        Generate SQLAlchemy Column() definition.

        Args:
            column (ColumnInfo): Column to generate definition for

        Returns:
            str: SQLAlchemy Column constructor call

        Example:
            "Column(Integer, primary_key=True, nullable=False)"
        """
        args = [column.get_sqlalchemy_type()]

        # Add column constraints
        if column.primary_key:
            args.append("primary_key=True")
        if not column.nullable:
            args.append("nullable=False")
        if column.unique:
            args.append("unique=True")
        if column.default is not None:
            args.append(f"default={repr(column.default)}")
        if column.server_default is not None:
            args.append(f"server_default=text({repr(column.server_default)})")

        # Add foreign key reference if it exists
        fk = self._get_foreign_key_for_column(column.name)
        if fk:
            args.append(f"ForeignKey('{fk.get_referred_key()}')")

        # Add index if column is indexed
        if any(column.name in idx.column_names for idx in self.indexes):
            args.append("index=True")

        # Add column comment if it exists
        if column.comment:
            args.append(f"comment={repr(column.comment)}")

        return f"Column({', '.join(args)})"

    def _get_foreign_key_for_column(self, column_name: str) -> Optional['ForeignKeyInfo']:
        """Find foreign key constraint for a column."""
        for fk in self.foreign_keys:
            if column_name in fk.constrained_columns:
                return fk
        return None

    def _generate_relationships(self) -> List[str]:
        """Generate SQLAlchemy relationship() definitions."""
        relationships = []

        for fk in self.foreign_keys:
            # Generate relationship name
            rel_name = self._get_relationship_name(fk)

            # Build relationship arguments
            args = [f"'{fk.referred_table}'"]

            # Add back reference if enabled
            if self.config.relationships.use_backref:
                backref_name = fk.get_backref_name()
                args.append(f"backref='{backref_name}'")

            # Add cascade options
            if fk.on_delete == ReferentialAction.CASCADE:
                args.append("cascade='all, delete-orphan'")

            # Add lazy loading option
            args.append(f"lazy='{self.config.relationships.lazy_loading}'")

            # Add any custom join conditions
            if len(fk.constrained_columns) > 1:
                join_cols = [
                    f"{self.name}.{col} == {fk.referred_table}.{ref}"
                    for col, ref in zip(fk.constrained_columns, fk.referred_columns)
                ]
                args.append(f"primaryjoin=and_({', '.join(join_cols)})")

            relationships.append(
                f"{rel_name} = relationship({', '.join(args)})"
            )

        return relationships

    def _get_relationship_name(self, fk: 'ForeignKeyInfo') -> str:
        """Generate appropriate relationship name."""
        # Use configured naming template
        template = self.config.relationships.relationship_naming_template

        # Determine relationship type
        rel_type = 'one_to_many' if len(fk.referred_columns) == 1 else 'many_to_many'

        # Apply template
        name = template.format(
            tablename=to_snake_case(fk.referred_table),
            reltype=rel_type
        )

        return name

    def _generate_hybrid_properties(self) -> List[str]:
        """Generate any needed hybrid properties."""
        properties = []

        # Generate properties for computed columns
        for col in self.columns:
            if col.generated:
                prop_name = f"{col.name}_computed"
                properties.extend([
                    "    @hybrid_property",
                    f"    def {prop_name}(self):",
                    f"        return {col.generated}"
                ])

        # Add custom properties based on column types
        for col in self.columns:
            if col.type_name.lower() == 'jsonb':
                properties.extend(self._generate_jsonb_properties(col))

        return properties

    def _generate_jsonb_properties(self, column: 'ColumnInfo') -> List[str]:
        """Generate convenience properties for JSONB columns."""
        properties = []
        prop_base = to_snake_case(column.name)

        # Add keys() property
        properties.extend([
            "    @hybrid_property",
            f"    def {prop_base}_keys(self):",
            f"        return list(self.{column.name}.keys()) if self.{column.name} else []"
        ])

        # Add convenience methods for common operations
        properties.extend([
            "    @hybrid_method",
            f"    def get_{prop_base}(self, key, default=None):",
            f"        return self.{column.name}.get(key, default) if self.{column.name} else default"
        ])

        return properties

    def _generate_model_methods(self) -> List[str]:
        """Generate standard model methods."""
        methods = []

        # Add __repr__ method
        methods.extend([
            "",
            "    def __repr__(self) -> str:",
            f"        return f\"{self.get_model_name()}({self._get_repr_attributes()})\"",
        ])

        # Add to_dict method
        methods.extend([
            "",
            "    def to_dict(self) -> Dict[str, Any]:",
            "        return {",
            "            " + ",\n            ".join(
                f"'{col.name}': self.{col.name}"
                for col in self.columns
            ),
            "        }"
        ])

        # Add class-level methods
        methods.extend([
            "",
            "    @classmethod",
            "    def get_by_id(cls, session: Session, id: Any) -> Optional['User']:",
            "        return session.query(cls).get(id)"
        ])

        return methods

    def _get_repr_attributes(self) -> str:
        """Get the attributes to show in __repr__."""
        # Always include primary key
        attrs = []
        for pk in self.primary_key:
            attrs.append(f"{pk}={{self.{pk}}}")

        # Add a few identifying columns if they exist
        ident_columns = {'name', 'title', 'email', 'username', 'code'}
        for col in self.columns:
            if col.name in ident_columns:
                attrs.append(f"{col.name}={{self.{col.name}}}")
                break

        return ", ".join(attrs)


@dataclass
class Relationship:
    """
    Comprehensive information about a database relationship.

    This class holds detailed information about relationships between database
    tables, including their type, constraints, and various options for
    SQLAlchemy relationship configuration.

    Attributes:
        source_table (str): Name of the source table
        target_table (str): Name of the target table
        relationship_type (RelationshipType): Type of relationship
        foreign_keys (List[str]): Foreign key column names
        backref_name (Optional[str]): Name for back reference
        is_nullable (bool): Whether relationship is nullable
        cascade_options (List[CascadeOption]): Cascade behavior
        lazy_load (LazyLoadOption): Lazy loading strategy
        join_conditions (List[JoinCondition]): Custom join conditions
        secondary_table (Optional[str]): Association table for many-to-many
        order_by (Optional[str]): ORDER BY clause
        primaryjoin (Optional[str]): Custom primary join condition
        secondaryjoin (Optional[str]): Custom secondary join condition
        post_update (bool): Use post update for circular dependencies
        viewonly (bool): Read-only relationship
        uselist (Optional[bool]): Force collection/single value
        remote_side (List[str]): Remote side for self-referential
        enable_typechecks (bool): Enable polymorphic type checking
        active_history (bool): Keep track of "previous" value
        sync_backref (bool): Synchronize backref operations
        doc (Optional[str]): Relationship documentation
        query_class (Optional[str]): Custom query class
        innerjoin (bool): Use INNER JOIN by default
        distinct_target (bool): Apply DISTINCT to lazy queries
        single_parent (bool): Single parent constraint
        collection_class (Optional[str]): Custom collection class
        load_on_pending (bool): Load on pending instances
        passive_deletes (bool): Enable passive deletes
        passive_updates (bool): Enable passive updates
        enable_typechecks (bool): Enable polymorphic type checking
        overlaps (Optional[str]): Related attribute name that overlaps
    """
    source_table: str
    target_table: str
    relationship_type: RelationshipType
    foreign_keys: List[str]
    backref_name: Optional[str] = None
    is_nullable: bool = True
    cascade_options: List[CascadeOption] = field(default_factory=lambda: [CascadeOption.SAVE_UPDATE])
    lazy_load: LazyLoadOption = LazyLoadOption.SELECT
    join_conditions: List[JoinCondition] = field(default_factory=list)
    secondary_table: Optional[str] = None
    order_by: Optional[str] = None
    primaryjoin: Optional[str] = None
    secondaryjoin: Optional[str] = None
    post_update: bool = False
    viewonly: bool = False
    uselist: Optional[bool] = None
    remote_side: List[str] = field(default_factory=list)
    enable_typechecks: bool = True
    active_history: bool = False
    sync_backref: bool = True
    doc: Optional[str] = None
    query_class: Optional[str] = None
    innerjoin: bool = False
    distinct_target: bool = False
    single_parent: bool = False
    collection_class: Optional[str] = None
    load_on_pending: bool = False
    passive_deletes: bool = False
    passive_updates: bool = True
    overlaps: Optional[str] = None

    def __post_init__(self):
        """
        Initialize relationship after creation.

        - Validates all attributes
        - Sets default cascade options
        - Ensures proper join conditions
        """
        # Set default cascade options based on relationship type
        if not self.cascade_options:
            self.cascade_options = self._get_default_cascade_options()

        # Set default uselist based on relationship type
        if self.uselist is None:
            self.uselist = self.relationship_type in {
                RelationshipType.ONE_TO_MANY,
                RelationshipType.MANY_TO_MANY,
                RelationshipType.ONE_TO_MANY_POLYMORPHIC,
                RelationshipType.MANY_TO_MANY_POLYMORPHIC
            }

        # Create default join conditions if none provided
        if not self.join_conditions and self.foreign_keys:
            self.join_conditions = self._create_default_join_conditions()

        # Validate
        self.validate()

    def validate(self) -> None:
        """
        Validate relationship attributes.

        This method performs comprehensive validation of all relationship attributes
        to ensure they are consistent and valid.

        Raises:
            ValidationError: If validation fails, with detailed error message.
        """
        errors = []

        # Validate table names
        if not validate_table_name(self.source_table):
            errors.append(f"Invalid source table name: {self.source_table}")
        if not validate_table_name(self.target_table):
            errors.append(f"Invalid target table name: {self.target_table}")

        # Validate foreign keys
        if not self.foreign_keys:
            errors.append("No foreign key columns specified")
        for fk in self.foreign_keys:
            if not validate_column_name(fk):
                errors.append(f"Invalid foreign key column name: {fk}")

        # Validate backref name if provided
        if self.backref_name and not validate_column_name(self.backref_name):
            errors.append(f"Invalid backref name: {self.backref_name}")

        # Validate many-to-many configuration
        if self.relationship_type in {RelationshipType.MANY_TO_MANY,
                                    RelationshipType.MANY_TO_MANY_POLYMORPHIC}:
            if not self.secondary_table:
                errors.append("Many-to-many relationship requires secondary table")
            elif not validate_table_name(self.secondary_table):
                errors.append(f"Invalid secondary table name: {self.secondary_table}")

        # Validate join conditions
        for join in self.join_conditions:
            if not validate_column_name(join.local_column):
                errors.append(f"Invalid local column in join condition: {join.local_column}")
            if not validate_column_name(join.remote_column):
                errors.append(f"Invalid remote column in join condition: {join.remote_column}")

        # Validate remote side columns
        for col in self.remote_side:
            if not validate_column_name(col):
                errors.append(f"Invalid remote side column: {col}")

        if errors:
            raise ValidationError("Relationship validation failed", errors=errors)

    def _get_default_cascade_options(self) -> List[CascadeOption]:
        """Get default cascade options based on relationship type."""
        if self.relationship_type in {RelationshipType.ONE_TO_MANY,
                                    RelationshipType.ONE_TO_MANY_POLYMORPHIC}:
            return [CascadeOption.ALL, CascadeOption.DELETE_ORPHAN]
        return [CascadeOption.SAVE_UPDATE]

    def _create_default_join_conditions(self) -> List[JoinCondition]:
        """Create default join conditions based on foreign keys."""
        conditions = []
        for fk in self.foreign_keys:
            conditions.append(JoinCondition(
                local_column=fk,
                remote_column=fk.replace('_id', ''),
                join_type=JoinType.INNER
            ))
        return conditions

    def get_relationship_name(self) -> str:
        """
        Generate appropriate relationship name.

        Returns:
            str: Generated relationship name

        Examples:
            >>> rel = Relationship("users", "posts", RelationshipType.ONE_TO_MANY, ["user_id"])
            >>> rel.get_relationship_name()
            'posts'
        """
        base_name = to_snake_case(self.target_table)
        if not self.uselist:
            return base_name
        return f"{base_name}s" if not base_name.endswith('s') else base_name

    def get_backref_name(self) -> str:
        """
        Generate appropriate backref name if not explicitly set.

        Returns:
            str: Generated backref name

        Examples:
            >>> rel = Relationship("users", "posts", RelationshipType.ONE_TO_MANY, ["user_id"])
            >>> rel.get_backref_name()
            'user'
        """
        if self.backref_name:
            return self.backref_name

        base_name = to_snake_case(self.source_table)
        if self.relationship_type in {RelationshipType.MANY_TO_ONE,
                                    RelationshipType.MANY_TO_ONE_POLYMORPHIC}:
            return f"{base_name}s" if not base_name.endswith('s') else base_name
        return base_name

    def get_sqlalchemy_relationship(self) -> str:
        """
        Generate SQLAlchemy relationship() definition.

        Returns:
            str: Complete relationship definition

        Examples:
            >>> rel = Relationship("users", "posts", RelationshipType.ONE_TO_MANY, ["user_id"])
            >>> print(rel.get_sqlalchemy_relationship())
            posts = relationship('Post',
                               backref='user',
                               lazy='select',
                               cascade='all, delete-orphan')
        """
        args = []

        # Add target class
        target_class = to_pascal_case(self.target_table)
        args.append(f"'{target_class}'")

        # Add backref if enabled
        if self.backref_name:
            backref_options = self._get_backref_options()
            if backref_options:
                args.append(f"backref=backref('{self.backref_name}', {backref_options})")
            else:
                args.append(f"backref='{self.backref_name}'")

        # Add secondary table for many-to-many
        if self.secondary_table:
            args.append(f"secondary='{self.secondary_table}'")

        # Add join conditions
        if self.primaryjoin:
            args.append(f"primaryjoin='{self.primaryjoin}'")
        elif self.join_conditions:
            args.append(f"primaryjoin='{self._format_join_conditions()}'")

        if self.secondaryjoin:
            args.append(f"secondaryjoin='{self.secondaryjoin}'")

        # Add cascade options
        if self.cascade_options:
            cascade = ", ".join(opt.value for opt in self.cascade_options)
            args.append(f"cascade='{cascade}'")

        # Add lazy loading option
        args.append(f"lazy='{self.lazy_load.value}'")

        # Add other common options
        if self.uselist is not None:
            args.append(f"uselist={str(self.uselist).lower()}")
        if self.remote_side:
            args.append(f"remote_side=[{', '.join(self.remote_side)}]")
        if self.order_by:
            args.append(f"order_by='{self.order_by}'")
        if self.post_update:
            args.append("post_update=True")
        if self.viewonly:
            args.append("viewonly=True")
        if not self.enable_typechecks:
            args.append("enable_typechecks=False")
        if self.active_history:
            args.append("active_history=True")
        if not self.sync_backref:
            args.append("sync_backref=False")
        if self.single_parent:
            args.append("single_parent=True")
        if self.collection_class:
            args.append(f"collection_class={self.collection_class}")
        if self.passive_deletes:
            args.append("passive_deletes=True")
        if not self.passive_updates:
            args.append("passive_updates=False")
        if self.overlaps:
            args.append(f"overlaps='{self.overlaps}'")
        if self.doc:
            args.append(f"doc={repr(self.doc)}")

        # Construct final relationship
        relationship_name = self.get_relationship_name()
        formatted_args = ',\n                     '.join(args)
        return f"{relationship_name} = relationship({formatted_args})"

    def _get_backref_options(self) -> Optional[str]:
        """Get options string for backref configuration."""
        options = []

        # Add uselist for backref
        if self.relationship_type in {RelationshipType.ONE_TO_MANY,
                                    RelationshipType.ONE_TO_MANY_POLYMORPHIC}:
            options.append("uselist=False")

        # Add other backref-specific options
        if self.order_by:
            options.append(f"order_by='{self.order_by}'")
        if self.query_class:
            options.append(f"query_class={self.query_class}")
        if self.innerjoin:
            options.append("innerjoin=True")
        if self.distinct_target:
            options.append("distinct=True")

        return ", ".join(options) if options else None

    def _format_join_conditions(self) -> str:
        """Format join conditions for SQLAlchemy."""
        conditions = []
        for join in self.join_conditions:
            cond = str(join)
            if join.where_clause:
                cond = f"and_({cond}, {join.where_clause})"
            conditions.append(cond)

        if len(conditions) == 1:
            return conditions[0]
        return f"and_({', '.join(conditions)})"

    def get_foreign_key_constraints(self) -> List[str]:
        """
        Generate SQLAlchemy ForeignKey constraints.

        Returns:
            List[str]: List of foreign key constraint definitions

        Examples:
            >>> rel = Relationship("users", "posts", RelationshipType.ONE_TO_MANY, ["user_id"])
            >>> rel.get_foreign_key_constraints()
            ["ForeignKey('users.id')"]
        """
        constraints = []
        for fk in self.foreign_keys:
            # Determine referenced column
            ref_col = fk.replace('_id', '')
            if not ref_col.endswith('id'):
                ref_col = 'id'

            # Build constraint options
            options = []
            if not self.is_nullable:
                options.append("nullable=False")

            # Add onupdate/ondelete actions
            if self.cascade_options:
                if CascadeOption.DELETE in self.cascade_options:
                    options.append("ondelete='CASCADE'")
                if CascadeOption.SAVE_UPDATE in self.cascade_options:
                    options.append("onupdate='CASCADE'")

            # Format constraint
            constraint = f"ForeignKey('{self.target_table}.{ref_col}'"
            if options:
                constraint += f", {', '.join(options)}"
            constraint += ")"
            constraints.append(constraint)

        return constraints

    def get_association_table(self) -> Optional[str]:
        """
        Generate SQLAlchemy association table definition for many-to-many relationships.

        Returns:
            Optional[str]: Association table definition if needed

        Examples:
            >>> rel = Relationship("users", "roles", RelationshipType.MANY_TO_MANY,
            ...                   ["user_id", "role_id"], secondary_table="user_roles")
            >>> print(rel.get_association_table())
            user_roles = Table('user_roles', Model.metadata,
                Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
                Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
            )
        """
        if not self.secondary_table:
            return None

        # Build column definitions
        columns = []
        seen_sources = set()

        for fk in self.foreign_keys:
            # Determine source and target tables
            if fk.startswith(self.source_table):
                source_table = self.source_table
                target_table = self.target_table
            else:
                source_table = self.target_table
                target_table = self.source_table

            if source_table in seen_sources:
                continue
            seen_sources.add(source_table)

            # Add column definition
            col_type = "Integer"  # Default type, could be made configurable
            columns.append(
                f"    Column('{fk}', {col_type}, "
                f"ForeignKey('{target_table}.id'), primary_key=True)"
            )

        # Build complete table definition
        return (
            f"{self.secondary_table} = Table(\n"
            f"    '{self.secondary_table}', Model.metadata,\n"
            f"{',\n'.join(columns)}\n"
            ")"
        )

    def get_documentation(self) -> str:
        """
        Generate documentation string for the relationship.

        Returns:
            str: Documentation string

        Examples:
            >>> rel = Relationship("users", "posts", RelationshipType.ONE_TO_MANY, ["user_id"])
            >>> print(rel.get_documentation())
            '''One-to-many relationship between User and Post.

            A user can have multiple posts, but each post belongs to one user.
            Foreign key: posts.user_id -> users.id
            '''
        """
        doc_lines = []

        # Basic relationship description
        rel_type = self.relationship_type.value.replace('_', '-')
        doc_lines.append(
            f"{rel_type.title()} relationship between "
            f"{to_pascal_case(self.source_table)} and {to_pascal_case(self.target_table)}."
        )
        doc_lines.append("")

        # Add relationship cardinality description
        if self.relationship_type == RelationshipType.ONE_TO_MANY:
            doc_lines.append(
                f"A {to_snake_case(self.source_table)} can have multiple "
                f"{to_snake_case(self.target_table)}s, but each "
                f"{to_snake_case(self.target_table)} belongs to one "
                f"{to_snake_case(self.source_table)}."
            )
        elif self.relationship_type == RelationshipType.MANY_TO_MANY:
            doc_lines.append(
                f"Many-to-many relationship using {self.secondary_table} "
                "as the association table."
            )

        # Add technical details
        doc_lines.append(f"Foreign key: {self._format_foreign_key_desc()}")

        if self.cascade_options:
            doc_lines.append(
                f"Cascade options: {', '.join(opt.value for opt in self.cascade_options)}"
            )

        if self.doc:
            doc_lines.extend(["", self.doc])

        return '\n'.join(doc_lines)

    def _format_foreign_key_desc(self) -> str:
        """Format foreign key description for documentation."""
        if len(self.foreign_keys) == 1:
            fk = self.foreign_keys[0]
            ref_col = fk.replace('_id', '.id')
            return f"{self.target_table}.{fk} -> {self.source_table}.{ref_col}"

        return ", ".join(
            f"{self.target_table}.{fk} -> {self.source_table}.{fk.replace('_id', '.id')}"
            for fk in self.foreign_keys
        )


class RelationshipResolver:
    """
    Handles relationship resolution and cycle detection/handling.

    This class is responsible for analyzing and resolving relationships between
    tables, particularly focusing on handling circular dependencies and ensuring
    proper relationship configurations.
    """

    def __init__(self, relationships: List[Relationship]):
        self.relationships = relationships
        self.dependency_graph = self._build_dependency_graph()
        self.cycles = []

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph from relationships."""
        graph = defaultdict(list)
        for rel in self.relationships:
            graph[rel.source_table].append(rel.target_table)
        return graph

    def _analyze_inheritance_relationships(self) -> None:
        """Analyze and resolve PostgreSQL table inheritance relationships."""
        pass

    def _analyze_partition_relationships(self) -> None:
        """Analyze and resolve PostgreSQL partition relationships."""
        pass

    def resolve_cycles(self) -> List[Relationship]:
        """
        Resolve circular dependencies in relationships.

        Returns:
            List[Relationship]: Modified relationships with resolved cycles
        """
        # Find all cycles
        self._detect_cycles()

        # Break cycles by modifying relationships
        return self._break_cycles()

    def _detect_cycles(self) -> None:
        """Detect cycles in the relationship graph."""
        visited = set()
        temp = set()

        def visit(node: str, path: List[str]) -> None:
            if node in temp:
                cycle_start = path.index(node)
                self.cycles.append(path[cycle_start:])
                return
            if node in visited:
                return

            temp.add(node)
            path.append(node)

            for neighbor in self.dependency_graph[node]:
                visit(neighbor, path.copy())

            temp.remove(node)
            visited.add(node)

        # Detect cycles starting from each node
        for node in self.dependency_graph:
            if node not in visited:
                visit(node, [])

    def _break_cycles(self) -> List[Relationship]:
        """
        Break detected cycles by modifying relationships.

        Returns:
            List[Relationship]: Modified relationships
        """
        modified_relationships = self.relationships.copy()

        for cycle in self.cycles:
            # Choose the best relationship to modify
            rel_to_modify = self._select_relationship_to_modify(cycle)

            # Modify the chosen relationship
            self._modify_relationship(rel_to_modify)

        return modified_relationships

    def _select_relationship_to_modify(self, cycle: List[str]) -> Relationship:
        """
        Select the best relationship to modify in a cycle.

        Args:
            cycle: List of table names forming a cycle

        Returns:
            Relationship: Selected relationship to modify
        """
        # Find all relationships involved in the cycle
        cycle_relationships = [
            rel for rel in self.relationships
            if rel.source_table in cycle and rel.target_table in cycle
        ]

        # Prioritize relationships based on:
        # 1. Many-to-one relationships (easier to make lazy)
        # 2. Non-required relationships (nullable foreign keys)
        # 3. Relationships without CASCADE options

        def get_relationship_score(rel: Relationship) -> int:
            score = 0
            if rel.relationship_type == RelationshipType.MANY_TO_ONE:
                score += 3
            if rel.is_nullable:
                score += 2
            if not any(opt == CascadeOption.CASCADE for opt in rel.cascade_options):
                score += 1
            return score

        return max(cycle_relationships, key=get_relationship_score)

    def _modify_relationship(self, relationship: Relationship) -> None:
        """
        Modify a relationship to break a cycle.

        Args:
            relationship: Relationship to modify
        """
        # Make relationship lazy loaded
        relationship.lazy_load = LazyLoadOption.SELECT

        # Remove cascade options
        relationship.cascade_options = [
            opt for opt in relationship.cascade_options
            if opt not in {CascadeOption.DELETE, CascadeOption.DELETE_ORPHAN}
        ]

        # Add post_update if needed
        relationship.post_update = True

        # Update relationship documentation
        if relationship.doc:
            relationship.doc += "\nNote: This relationship was modified to break a circular dependency."
        else:
            relationship.doc = "This relationship was modified to break a circular dependency."

    def get_relationship_order(self) -> List[str]:
        """
        Get optimal order for processing relationships.

        Returns:
            List[str]: Table names in processing order
        """
        # Use topological sort excluding back-references
        visited = set()
        temp = set()
        order = []

        def visit(node: str) -> None:
            if node in temp:
                return  # Skip cycles
            if node in visited:
                return

            temp.add(node)

            for neighbor in self.dependency_graph[node]:
                visit(neighbor)

            temp.remove(node)
            visited.add(node)
            order.append(node)

        for node in self.dependency_graph:
            if node not in visited:
                visit(node)

        return order[::-1]  # Reverse for correct order

    def get_cycle_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of detected cycles and resolutions.

        Returns:
            List[Dict[str, Any]]: Summary of each cycle and how it was resolved
        """
        return [
            {
                'cycle': cycle,
                'length': len(cycle),
                'tables_involved': set(cycle),
                'resolution': self._get_cycle_resolution(cycle)
            }
            for cycle in self.cycles
        ]

    def _get_cycle_resolution(self, cycle: List[str]) -> Dict[str, Any]:
        """Get resolution details for a specific cycle."""
        rel = self._select_relationship_to_modify(cycle)
        return {
            'modified_relationship': {
                'source': rel.source_table,
                'target': rel.target_table,
                'type': rel.relationship_type.value
            },
            'modifications': {
                'lazy_loading': rel.lazy_load.value,
                'post_update': rel.post_update,
                'removed_cascade_options': [
                    opt.value for opt in rel.cascade_options
                    if opt in {CascadeOption.DELETE, CascadeOption.DELETE_ORPHAN}
                ]
            }
        }

@dataclass
class GenerationContext:
    """
    Holds and manages the state and configuration for the model generation process.

    This context object maintains all necessary information and relationships during
    the database schema processing and model generation phases. It handles type mapping,
    relationship tracking, import management, and provides utility methods for model
    generation.

    Attributes:
        tables (List[TableInfo]): List of all tables being processed
        current_table (TableInfo): The table currently being processed
        config (GeneratorConfig): Configuration settings for generation process
        type_map (Dict[str, str]): Database to Python/SQLAlchemy type mappings
        relationships (List[Relationship]): Tracked table relationships
        imports (Set[str]): Required Python imports for generated models
        errors (List[str]): Validation and processing errors
        warnings (List[str]): Non-critical issues and warnings
        generated_code (Dict[str, str]): Generated model code by table name

    Example:
        >>> context = GenerationContext(
        ...     tables=[TableInfo("users"), TableInfo("posts")],
        ...     config=GeneratorConfig(),
        ... )
        >>> context.process_relationships()
        >>> print(context.get_model_code("users"))
    """

    tables: List[TableInfo]
    current_table: Optional[TableInfo] = None
    config: Optional[GeneratorConfig] = None
    type_map: Dict[str, str] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    generated_code: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default imports and validate configuration."""
        # Add default SQLAlchemy imports
        self.add_imports([
            "from sqlalchemy import Column, ForeignKey, Integer, String",
            "from sqlalchemy.orm import relationship",
            "from sqlalchemy.ext.declarative import declarative_base",
        ])

        # Validate configuration
        if self.config is None:
            self.config = GeneratorConfig()  # Use default configuration
            self.warnings.append("No configuration provided, using defaults")

    def add_import(self, import_stmt: str) -> None:
        """
        Add a single import statement to the context.

        Args:
            import_stmt (str): Import statement to add

        Example:
            >>> context.add_import("from datetime import datetime")
        """
        if import_stmt not in self.imports:
            self.imports.add(import_stmt)

    def add_imports(self, imports: List[str]) -> None:
        """
        Add multiple import statements to the context.

        Args:
            imports (List[str]): List of import statements to add

        Example:
            >>> context.add_imports([
            ...     "from typing import Optional",
            ...     "from datetime import date, datetime"
            ... ])
        """
        for import_stmt in imports:
            self.add_import(import_stmt)

    def add_relationship(self, relationship: Relationship) -> None:
        """
        Add and validate a relationship definition.

        Args:
            relationship (Relationship): Relationship to add

        Raises:
            ValidationError: If relationship is invalid

        Example:
            >>> rel = Relationship("users", "posts", RelationshipType.ONE_TO_MANY, ["user_id"])
            >>> context.add_relationship(rel)
        """
        try:
            relationship.validate()
            self.relationships.append(relationship)
        except ValidationError as e:
            self.errors.append(f"Invalid relationship: {str(e)}")
            raise

    def set_current_table(self, table: TableInfo) -> None:
        """
        Set the current table being processed.

        Args:
            table (TableInfo): Table to set as current

        Example:
            >>> context.set_current_table(TableInfo("users"))
        """
        self.current_table = table
        self.process_table_types()

    def process_table_types(self) -> None:
        """
        Process and add required imports for current table's column types.

        Example:
            >>> context.set_current_table(table_info)
            >>> context.process_table_types()
        """
        if not self.current_table:
            return

        for column in self.current_table.columns:
            sa_type = column.get_sqlalchemy_type()
            if sa_type not in {'Integer', 'String'}:  # These are in default imports
                self.add_import(f"from sqlalchemy import {sa_type}")

    def process_relationships(self) -> None:
        """
        Process and resolve all relationships between tables.

        This method handles relationship cycle detection and resolution.

        Example:
            >>> context.process_relationships()
        """
        resolver = RelationshipResolver(self.relationships)
        self.relationships = resolver.resolve_cycles()

        # Add any necessary relationship-specific imports
        if any(rel.relationship_type in {RelationshipType.MANY_TO_MANY,
                                       RelationshipType.MANY_TO_MANY_POLYMORPHIC}
               for rel in self.relationships):
            self.add_import("from sqlalchemy import Table")

    def get_model_name(self, table_name: Optional[str] = None) -> str:
        """
        Get the model class name for a table.

        Args:
            table_name (Optional[str]): Table name to get model name for.
                                      Uses current table if None.

        Returns:
            str: Model class name in PascalCase

        Example:
            >>> context.get_model_name("user_profiles")
            'UserProfile'
        """
        if table_name:
            return to_pascal_case(table_name)
        if self.current_table:
            return to_pascal_case(self.current_table.name)
        raise ValueError("No table specified and no current table set")

    def generate_models(self) -> Dict[str, str]:
        """
        Generate SQLAlchemy models for all tables.

        Returns:
            Dict[str, str]: Dictionary mapping table names to generated model code

        Example:
            >>> models = context.generate_models()
            >>> for table_name, model_code in models.items():
            ...     print(f"Generated model for {table_name}:")
            ...     print(model_code)
        """
        self.generated_code = {}

        # Process relationships first
        self.process_relationships()

        # Generate models for each table
        for table in self.tables:
            self.set_current_table(table)
            try:
                model_code = table.get_sqlalchemy_model()
                self.generated_code[table.name] = model_code
            except Exception as e:
                self.errors.append(f"Error generating model for {table.name}: {str(e)}")

        return self.generated_code

    def get_import_statements(self) -> str:
        """
        Get formatted import statements for generated models.

        Returns:
            str: Formatted import statements

        Example:
            >>> print(context.get_import_statements())
            from sqlalchemy import Column, Integer, String
            from sqlalchemy.orm import relationship
            # ... additional imports ...
        """
        return "\n".join(sorted(self.imports))

    def get_generation_summary(self) -> Dict[str, Any]:
        """
        Get summary of the generation process.

        Returns:
            Dict[str, Any]: Summary including statistics and any issues

        Example:
            >>> summary = context.get_generation_summary()
            >>> print(f"Generated {summary['model_count']} models")
            >>> if summary['errors']:
            ...     print("Errors encountered:", summary['errors'])
        """
        return {
            'model_count': len(self.generated_code),
            'relationship_count': len(self.relationships),
            'errors': self.errors,
            'warnings': self.warnings,
            'tables_processed': [table.name for table in self.tables],
            'import_count': len(self.imports),
            'status': 'failed' if self.errors else 'success'
        }
