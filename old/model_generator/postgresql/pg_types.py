"""
pg_types.py: PostgreSQL type definitions and mappings.

This module defines PostgreSQL-specific type classes and mappings for database
introspection and model generation. It handles the full range of PostgreSQL
data types, including complex types, arrays, and custom types.

Key Features:
    - Complete PostgreSQL type system support
    - SQLAlchemy type mappings
    - Custom type handling
    - Array and composite types
    - Domain and enum support
    - Range and network types

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
import re

from model_generator.exceptions import DatabaseIntrospectionError
from model_generator.postgresql.pg_exceptions import PostgreSQLTypeError


class PostgreSQLTypeCategory(Enum):
    """PostgreSQL type categories."""
    ARRAY = 'A'
    BOOLEAN = 'B'
    COMPOSITE = 'C'
    DATE_TIME = 'D'
    ENUM = 'E'
    GEOMETRIC = 'G'
    NETWORK = 'I'  # inet, cidr
    NUMERIC = 'N'
    PSEUDO = 'P'  # pseudo-types like record, void
    RANGE = 'R'
    STRING = 'S'
    TIMESPAN = 'T'
    USER_DEFINED = 'U'
    BIT_STRING = 'V'
    UNKNOWN = 'X'


class PostgreSQLStorageType(Enum):
    """PostgreSQL storage types."""
    PLAIN = 'p'      # Default storage
    EXTERNAL = 'x'   # Extended storage
    MAIN = 'm'       # Main storage
    EXTERNAL_TOC = 'e'  # External with TOC


class PostgreSQLBaseType:
    """Base class for PostgreSQL types."""

    def __init__(self, 
                 name: str, 
                 oid: int,
                 schema: str = 'pg_catalog',
                 category: PostgreSQLTypeCategory = PostgreSQLTypeCategory.UNKNOWN):
        self.name = name
        self.oid = oid
        self.schema = schema
        self.category = category

    def to_sql(self) -> str:
        """Get SQL representation of the type."""
        return f"{self.schema}.{self.name}"

    def to_python_type(self) -> str:
        """Get Python type hint."""
        return "Any"

    def to_sqlalchemy_type(self) -> str:
        """Get SQLAlchemy type representation."""
        return "String"


@dataclass
class PostgreSQLArrayInfo:
    """Information about array types."""
    element_type: str
    dimensions: Optional[int] = None
    bounds: Optional[List[int]] = None
    
    def to_sql(self) -> str:
        base = f"{self.element_type}[]"
        if self.dimensions:
            base = f"{self.element_type}[{','.join([''] * self.dimensions)}]"
        return base


@dataclass
class PostgreSQLEnumType(PostgreSQLBaseType):
    """PostgreSQL enum type information."""
    values: List[str]
    ordered: bool = True
    
    def to_sql(self) -> str:
        values = "', '".join(self.values)
        return f"ENUM('{values}')"
    
    def to_python_type(self) -> str:
        return "str"
    
    def to_sqlalchemy_type(self) -> str:
        values = ", ".join(repr(v) for v in self.values)
        return f"Enum({values}, name='{self.name}')"


@dataclass
class PostgreSQLRangeType(PostgreSQLBaseType):
    """PostgreSQL range type information."""
    subtype: str
    subtype_opclass: Optional[str] = None
    collation: Optional[str] = None
    canonical: Optional[str] = None  # Canonicalization function
    subtype_diff: Optional[str] = None  # Difference function
    
    def to_sql(self) -> str:
        return f"{self.subtype} RANGE"
    
    def to_python_type(self) -> str:
        return f"Tuple[Optional[{self.subtype}], Optional[{self.subtype}]]"
    
    def to_sqlalchemy_type(self) -> str:
        return f"postgresql.RANGE({self.subtype})"


@dataclass
class PostgreSQLCompositeType(PostgreSQLBaseType):
    """PostgreSQL composite type information."""
    attributes: List[Dict[str, Any]]
    delimiter: str = ','
    
    def to_sql(self) -> str:
        attrs = ", ".join(f"{attr['name']} {attr['type']}" for attr in self.attributes)
        return f"({attrs})"
    
    def to_python_type(self) -> str:
        return "Dict[str, Any]"
    
    def to_sqlalchemy_type(self) -> str:
        return "JSON"  # Convert to JSON for simplicity


@dataclass
class PostgreSQLDomainType(PostgreSQLBaseType):
    """PostgreSQL domain type information."""
    base_type: str
    constraints: List[str] = field(default_factory=list)
    default: Optional[str] = None
    collation: Optional[str] = None
    nullable: bool = True
    
    def to_sql(self) -> str:
        sql = [f"DOMAIN {self.name} AS {self.base_type}"]
        if not self.nullable:
            sql.append("NOT NULL")
        if self.default:
            sql.append(f"DEFAULT {self.default}")
        for constraint in self.constraints:
            sql.append(f"CONSTRAINT {constraint}")
        return " ".join(sql)
    
    def to_python_type(self) -> str:
        return "Any"  # Use base type's Python equivalent
    
    def to_sqlalchemy_type(self) -> str:
        return "String"  # Use base type's SQLAlchemy equivalent


class PostgreSQLTypeMap:
    """Maps PostgreSQL types to SQLAlchemy types."""
    
    # Basic type mappings
    BASIC_TYPES = {
        # Numeric types
        'smallint': 'SmallInteger',
        'integer': 'Integer',
        'bigint': 'BigInteger',
        'decimal': 'Numeric',
        'numeric': 'Numeric',
        'real': 'Float',
        'double precision': 'Float',
        'serial': 'Integer',
        'bigserial': 'BigInteger',
        
        # Character types
        'character varying': 'String',
        'varchar': 'String',
        'character': 'String',
        'char': 'String',
        'text': 'Text',
        
        # Date/Time types
        'timestamp': 'DateTime',
        'timestamp with time zone': 'DateTime(timezone=True)',
        'date': 'Date',
        'time': 'Time',
        'time with time zone': 'Time(timezone=True)',
        'interval': 'Interval',
        
        # Boolean type
        'boolean': 'Boolean',
        
        # Network types
        'inet': 'postgresql.INET',
        'cidr': 'postgresql.CIDR',
        'macaddr': 'postgresql.MACADDR',
        'macaddr8': 'postgresql.MACADDR8',
        
        # UUID type
        'uuid': 'UUID',
        
        # JSON types
        'json': 'JSON',
        'jsonb': 'JSONB',
        
        # Binary data
        'bytea': 'LargeBinary',
        
        # Money
        'money': 'Numeric',
        
        # Full text search
        'tsvector': 'postgresql.TSVECTOR',
        'tsquery': 'postgresql.TSQUERY',
        
        # Bit strings
        'bit': 'postgresql.BIT',
        'bit varying': 'postgresql.BIT_VARYING',
    }
    
    # Geometry types (if PostGIS is available)
    GEOMETRY_TYPES = {
        'geometry': 'Geometry',
        'geography': 'Geography',
        'box2d': 'Box2D',
        'box3d': 'Box3D',
    }
    
    def __init__(self, custom_mappings: Optional[Dict[str, str]] = None):
        """Initialize type map with optional custom mappings."""
        self.mappings = self.BASIC_TYPES.copy()
        if custom_mappings:
            self.mappings.update(custom_mappings)
    
    def get_type(self, pg_type: str, **options) -> str:
        """
        Get SQLAlchemy type for PostgreSQL type.
        
        Args:
            pg_type: PostgreSQL type name
            **options: Type-specific options

        Returns:
            str: SQLAlchemy type string
        
        Raises:
            PostgreSQLTypeError: If type cannot be mapped
        """
        # Handle array types
        if pg_type.endswith('[]'):
            return self._handle_array_type(pg_type, **options)
        
        # Handle types with precision/scale
        if '(' in pg_type:
            return self._handle_parameterized_type(pg_type, **options)
        
        # Look up basic type
        base_type = pg_type.lower()
        if base_type in self.mappings:
            return self._apply_type_options(self.mappings[base_type], **options)
        
        # Try geometry types if options indicate PostGIS is available
        if options.get('has_postgis') and base_type in self.GEOMETRY_TYPES:
            return self._handle_geometry_type(base_type, **options)
        
        raise PostgreSQLTypeError(
            f"Unsupported PostgreSQL type: {pg_type}",
            type_name=pg_type
        )
    
    def _handle_array_type(self, pg_type: str, **options) -> str:
        """Handle PostgreSQL array types."""
        base_type = pg_type[:-2]  # Remove []
        try:
            element_type = self.get_type(base_type, **options)
            return f"ARRAY({element_type})"
        except PostgreSQLTypeError as e:
            raise PostgreSQLTypeError(
                f"Unable to map array type: {pg_type}",
                type_name=pg_type,
                cause=e
            )
    
    def _handle_parameterized_type(self, pg_type: str, **options) -> str:
        """Handle types with parameters (e.g., varchar(50))."""
        match = re.match(r'(\w+)\s*\((.*)\)', pg_type)
        if not match:
            raise PostgreSQLTypeError(
                f"Invalid parameterized type: {pg_type}",
                type_name=pg_type
            )
        
        base_type = match.group(1).lower()
        params = match.group(2).split(',')
        
        if base_type in ('varchar', 'character varying', 'char', 'character'):
            length = int(params[0])
            return f"String({length})"
        
        if base_type in ('numeric', 'decimal'):
            precision = int(params[0])
            scale = int(params[1]) if len(params) > 1 else 0
            return f"Numeric(precision={precision}, scale={scale})"
        
        raise PostgreSQLTypeError(
            f"Unsupported parameterized type: {pg_type}",
            type_name=pg_type
        )
    
    def _handle_geometry_type(self, pg_type: str, **options) -> str:
        """Handle PostGIS geometry types."""
        geom_type = self.GEOMETRY_TYPES[pg_type]
        srid = options.get('srid')
        if srid:
            return f"Geometry(geometry_type='{geom_type}', srid={srid})"
        return f"Geometry(geometry_type='{geom_type}')"
    
    def _apply_type_options(self, type_str: str, **options) -> str:
        """Apply type-specific options."""
        if options.get('array_dimensions'):
            type_str = f"ARRAY({type_str})"
            
        if options.get('timezone') and type_str in ('DateTime', 'Time'):
            type_str = f"{type_str}(timezone=True)"
            
        return type_str


# Create default type map instance
default_type_map = PostgreSQLTypeMap()

def get_type(pg_type: str, **options) -> str:
    """Convenience function to get SQLAlchemy type."""
    return default_type_map.get_type(pg_type, **options)
