"""
pg_enums.py: PostgreSQL enumerated type handling.

This module provides comprehensive support for PostgreSQL enumerated types,
including type introspection, value validation, and SQLAlchemy mapping.
It handles both built-in and custom enum types.

Key Features:
    - Enum type introspection
    - Value validation and conversion
    - SQLAlchemy enum type generation
    - Custom enum type support
    - Enum value ordering
    - Default value handling
    - Migration support

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
import re

from sqlalchemy import Enum as SQLAEnum
from model_generator.postgresql.pg_exceptions import PostgreSQLTypeError

@dataclass
class EnumValue:
    """
    Represents a single enum value.
    
    Attributes:
        name: The enum value name
        ordinal: Position in the enum (0-based)
        alias: Optional alternative name
        comment: Optional documentation
    """
    name: str
    ordinal: int
    alias: Optional[str] = None
    comment: Optional[str] = None

    def __str__(self) -> str:
        return self.name

    def to_sql(self) -> str:
        """Get SQL representation of enum value."""
        return f"'{self.name}'"

    def to_python(self) -> str:
        """Get Python representation of enum value."""
        # Convert to valid Python identifier
        return re.sub(r'\W|^(?=\d)', '_', self.name).upper()


@dataclass
class PostgreSQLEnum:
    """
    Represents a PostgreSQL enumerated type.
    
    Attributes:
        name: Name of the enum type
        values: List of enum values
        schema: Schema containing the enum
        ordered: Whether order is significant
        comment: Optional documentation
        owner: Enum type owner
    """
    name: str
    values: List[EnumValue]
    schema: str = 'public'
    ordered: bool = True
    comment: Optional[str] = None
    owner: Optional[str] = None
    
    def __post_init__(self):
        """Validate enum after initialization."""
        self._validate()
        self._value_map = {v.name: v for v in self.values}
    
    def _validate(self) -> None:
        """Validate enum configuration."""
        if not self.values:
            raise PostgreSQLTypeError(
                "Enum must have at least one value",
                type_name=self.name,
                details={'schema': self.schema}
            )
        
        # Check for duplicate values
        seen = set()
        for value in self.values:
            if value.name in seen:
                raise PostgreSQLTypeError(
                    f"Duplicate enum value: {value.name}",
                    type_name=self.name,
                    details={'value': value.name}
                )
            seen.add(value.name)
    
    def get_value(self, name: str) -> Optional[EnumValue]:
        """Get enum value by name."""
        return self._value_map.get(name)
    
    def contains(self, value: str) -> bool:
        """Check if value exists in enum."""
        return value in self._value_map
    
    def to_sql_type(self) -> str:
        """Get SQL type definition."""
        values = ", ".join(v.to_sql() for v in self.values)
        return f"CREATE TYPE {self.schema}.{self.name} AS ENUM ({values})"
    
    def to_sqlalchemy_type(self) -> str:
        """Get SQLAlchemy type definition."""
        values = ", ".join(f"'{v.name}'" for v in self.values)
        return f"Enum({values}, name='{self.name}', schema='{self.schema}')"
    
    def to_python_enum(self) -> str:
        """Generate Python Enum class definition."""
        lines = [f"class {self.name}(Enum):"]
        if self.comment:
            lines.append(f"    \"\"\"{self.comment}\"\"\"")
        
        # Add enum values
        for value in self.values:
            line = f"    {value.to_python()} = '{value.name}'"
            if value.comment:
                line += f"  # {value.comment}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def get_migrations(self, 
                      previous_version: Optional['PostgreSQLEnum'] = None
                      ) -> List[str]:
        """
        Generate migration SQL for enum changes.
        
        Args:
            previous_version: Previous version of the enum for migrations
            
        Returns:
            List of SQL statements for migration
        """
        if not previous_version:
            # New enum type
            return [self.to_sql_type()]
        
        migrations = []
        
        # Check for removed values
        removed = set(v.name for v in previous_version.values) - \
                 set(v.name for v in self.values)
        if removed:
            # Cannot remove values without dropping and recreating
            migrations.extend([
                f"DROP TYPE {self.schema}.{self.name}",
                self.to_sql_type()
            ])
            return migrations
        
        # Add new values
        current_values = set(v.name for v in previous_version.values)
        for value in self.values:
            if value.name not in current_values:
                migrations.append(
                    f"ALTER TYPE {self.schema}.{self.name} "
                    f"ADD VALUE {value.to_sql()}"
                )
        
        return migrations


class EnumManager:
    """
    Manages PostgreSQL enum types for a database.
    
    This class handles the introspection, creation, and management of
    enum types across the database schema.
    """
    
    def __init__(self):
        self.enums: Dict[str, PostgreSQLEnum] = {}
        self._query_template = """
            SELECT 
                t.typname as enum_name,
                n.nspname as schema_name,
                e.enumlabel as enum_value,
                e.enumsortorder as value_order,
                obj_description(t.oid, 'pg_type') as enum_comment,
                pg_get_userbyid(t.typowner) as enum_owner
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace n ON t.typnamespace = n.oid
            WHERE t.typtype = 'e'
            ORDER BY t.typname, e.enumsortorder;
        """
    
    def load_enums(self, connection) -> None:
        """
        Load enum types from database.
        
        Args:
            connection: Database connection
        """
        self.enums.clear()
        
        with connection.cursor() as cursor:
            cursor.execute(self._query_template)
            current_enum = None
            current_values = []
            
            for row in cursor.fetchall():
                enum_name = row[0]
                schema = row[1]
                value = row[2]
                ordinal = row[3]
                comment = row[4]
                owner = row[5]
                
                if current_enum != enum_name:
                    # Save previous enum if exists
                    if current_enum and current_values:
                        self.enums[current_enum] = PostgreSQLEnum(
                            name=current_enum,
                            values=current_values,
                            schema=schema,
                            comment=comment,
                            owner=owner
                        )
                    # Start new enum
                    current_enum = enum_name
                    current_values = []
                
                # Add value to current enum
                current_values.append(EnumValue(
                    name=value,
                    ordinal=ordinal
                ))
            
            # Save last enum
            if current_enum and current_values:
                self.enums[current_enum] = PostgreSQLEnum(
                    name=current_enum,
                    values=current_values,
                    schema=schema,
                    comment=comment,
                    owner=owner
                )
    
    def get_enum(self, name: str, schema: str = 'public') -> Optional[PostgreSQLEnum]:
        """Get enum type by name."""
        qualified_name = f"{schema}.{name}"
        return self.enums.get(qualified_name)
    
    def create_enum(self, enum_def: PostgreSQLEnum, connection) -> None:
        """
        Create a new enum type in the database.
        
        Args:
            enum_def: Enum type definition
            connection: Database connection
        """
        if enum_def.name in self.enums:
            raise PostgreSQLTypeError(
                f"Enum type already exists: {enum_def.name}",
                type_name=enum_def.name,
                details={'schema': enum_def.schema}
            )
        
        with connection.cursor() as cursor:
            # Create the enum type
            cursor.execute(enum_def.to_sql_type())
            
            # Add comment if provided
            if enum_def.comment:
                cursor.execute(
                    f"COMMENT ON TYPE {enum_def.schema}.{enum_def.name} IS %s",
                    [enum_def.comment]
                )
            
            # Add to local cache
            self.enums[enum_def.name] = enum_def
    
    def update_enum(self, 
                   enum_def: PostgreSQLEnum, 
                   connection,
                   fail_on_remove: bool = True) -> None:
        """
        Update an existing enum type.
        
        Args:
            enum_def: New enum definition
            connection: Database connection
            fail_on_remove: Whether to fail if values would be removed
        """
        existing = self.get_enum(enum_def.name, enum_def.schema)
        if not existing:
            raise PostgreSQLTypeError(
                f"Enum type does not exist: {enum_def.name}",
                type_name=enum_def.name,
                details={'schema': enum_def.schema}
            )
        
        # Get migration SQL
        migrations = enum_def.get_migrations(existing)
        if not migrations:
            return  # No changes needed
        
        # Check for value removal if needed
        if fail_on_remove:
            removed = set(v.name for v in existing.values) - \
                     set(v.name for v in enum_def.values)
            if removed:
                raise PostgreSQLTypeError(
                    f"Cannot remove enum values: {removed}",
                    type_name=enum_def.name,
                    details={'removed_values': list(removed)}
                )
        
        # Execute migrations
        with connection.cursor() as cursor:
            for sql in migrations:
                cursor.execute(sql)
            
            # Update comment if changed
            if enum_def.comment != existing.comment:
                cursor.execute(
                    f"COMMENT ON TYPE {enum_def.schema}.{enum_def.name} IS %s",
                    [enum_def.comment]
                )
        
        # Update local cache
        self.enums[enum_def.name] = enum_def
    
    def drop_enum(self, 
                 name: str, 
                 schema: str = 'public',
                 connection,
                 cascade: bool = False) -> None:
        """
        Drop an enum type.
        
        Args:
            name: Enum type name
            schema: Schema name
            connection: Database connection
            cascade: Whether to cascade the drop
        """
        if name not in self.enums:
            raise PostgreSQLTypeError(
                f"Enum type does not exist: {name}",
                type_name=name,
                details={'schema': schema}
            )
        
        with connection.cursor() as cursor:
            sql = f"DROP TYPE {schema}.{name}"
            if cascade:
                sql += " CASCADE"
            cursor.execute(sql)
        
        # Remove from local cache
        del self.enums[name]


# Singleton instance for global use
enum_manager = EnumManager()

def get_enum(name: str, schema: str = 'public') -> Optional[PostgreSQLEnum]:
    """Convenience function to get enum type."""
    return enum_manager.get_enum(name, schema)

def create_enum(enum_def: PostgreSQLEnum, connection) -> None:
    """Convenience function to create enum type."""
    enum_manager.create_enum(enum_def, connection)

def update_enum(enum_def: PostgreSQLEnum, connection, fail_on_remove: bool = True) -> None:
    """Convenience function to update enum type."""
    enum_manager.update_enum(enum_def, connection, fail_on_remove)

def drop_enum(name: str, schema: str = 'public', connection, cascade: bool = False) -> None:
    """Convenience function to drop enum type."""
    enum_manager.drop_enum(name, schema, connection, cascade)
