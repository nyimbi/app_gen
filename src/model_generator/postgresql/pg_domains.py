"""
pg_domains.py: PostgreSQL domain type handling.

This module provides functionality for handling PostgreSQL domain types,
which are user-defined types that add constraints to existing types.
It works in conjunction with pg_types.py to provide domain type support.

Key Features:
    - Domain type introspection
    - Constraint handling
    - Validation rules
    - Default value management
    - Domain type creation and modification
    - SQLAlchemy integration

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union
import re

from sqlalchemy import TypeDecorator, CheckConstraint
from model_generator.postgresql.pg_exceptions import PostgreSQLTypeError
from model_generator.postgresql.pg_types import PostgreSQLBaseType, PostgreSQLTypeMap


@dataclass
class DomainConstraint:
    """Represents a constraint on a domain type."""

    name: str
    definition: str
    check_clause: str
    is_not_null: bool = False
    comment: Optional[str] = None

    def to_sql(self) -> str:
        """Convert constraint to SQL definition."""
        parts = [f"CONSTRAINT {self.name}"]
        if self.is_not_null:
            parts.append("NOT NULL")
        if self.check_clause:
            parts.append(f"CHECK ({self.check_clause})")
        return " ".join(parts)

    def to_sqlalchemy(self) -> str:
        """Convert to SQLAlchemy constraint."""
        if self.is_not_null:
            return "nullable=False"
        if self.check_clause:
            return f"CheckConstraint('{self.check_clause}')"
        return ""


@dataclass
class PostgreSQLDomain:
    """
    Represents a PostgreSQL domain type.

    Attributes:
        name: Domain name
        base_type: Underlying base type
        schema: Schema containing the domain
        constraints: Domain constraints
        default: Default value expression
        collation: Optional collation
        comment: Optional documentation
    """
    name: str
    base_type: str
    schema: str = 'public'
    constraints: List[DomainConstraint] = field(default_factory=list)
    default: Optional[str] = None
    collation: Optional[str] = None
    comment: Optional[str] = None

    def __post_init__(self):
        """Validate domain after initialization."""
        self._validate()

    def _validate(self):
        """Validate domain configuration."""
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.name):
            raise PostgreSQLTypeError(
                "Invalid domain name",
                type_name=self.name,
                details={'schema': self.schema}
            )

        # Ensure base type exists
        type_map = PostgreSQLTypeMap()
        try:
            type_map.get_type(self.base_type)
        except PostgreSQLTypeError as e:
            raise PostgreSQLTypeError(
                f"Invalid base type for domain: {self.base_type}",
                type_name=self.name,
                details={'base_type': self.base_type},
                cause=e
            )

    def to_sql(self) -> str:
        """Generate SQL CREATE DOMAIN statement."""
        parts = [f"CREATE DOMAIN {self.schema}.{self.name} AS {self.base_type}"]

        if self.collation:
            parts.append(f"COLLATE {self.collation}")

        if self.default:
            parts.append(f"DEFAULT {self.default}")

        for constraint in self.constraints:
            parts.append(constraint.to_sql())

        sql = [" ".join(parts) + ";"]

        if self.comment:
            sql.append(
                f"COMMENT ON DOMAIN {self.schema}.{self.name} "
                f"IS '{self.comment}';"
            )

        return "\n".join(sql)

    def to_sqlalchemy_type(self) -> str:
        """Generate SQLAlchemy custom type class."""
        type_map = PostgreSQLTypeMap()
        base_type = type_map.get_type(self.base_type)

        lines = [
            f"class {self.name}Type(TypeDecorator):",
            f"    impl = {base_type}",
            "",
            "    def process_bind_param(self, value, dialect):",
            "        if value is None:",
            "            return None",
            "        return self.impl.process_bind_param(value, dialect)",
            "",
            "    def process_result_value(self, value, dialect):",
            "        if value is None:",
            "            return None",
            "        return self.impl.process_result_value(value, dialect)"
        ]

        return "\n    ".join(lines)


class DomainManager:
    """
    Manages PostgreSQL domain types for a database.

    This class handles the introspection, creation, and management of
    domain types across the database schema.
    """

    def __init__(self):
        self.domains: Dict[str, PostgreSQLDomain] = {}
        self._query_template = """
            SELECT
                t.typname as domain_name,
                n.nspname as schema_name,
                base.typname as base_type,
                t.typdefault as default_value,
                t.typcollation as collation_id,
                obj_description(t.oid, 'pg_type') as comment,
                c.conname as constraint_name,
                pg_get_constraintdef(c.oid) as constraint_def
            FROM pg_type t
            JOIN pg_namespace n ON t.typnamespace = n.oid
            JOIN pg_type base ON t.typbasetype = base.oid
            LEFT JOIN pg_constraint c ON t.oid = c.contypid
            WHERE t.typtype = 'd'
            ORDER BY t.typname, c.conname;
        """

    def load_domains(self, connection) -> None:
        """
        Load domain types from database.

        Args:
            connection: Database connection
        """
        self.domains.clear()

        with connection.cursor() as cursor:
            cursor.execute(self._query_template)
            current_domain = None
            current_constraints = []

            for row in cursor.fetchall():
                domain_name = row[0]
                schema = row[1]
                base_type = row[2]
                default = row[3]
                collation_id = row[4]
                comment = row[5]
                constraint_name = row[6]
                constraint_def = row[7]

                if current_domain != domain_name:
                    # Save previous domain if exists
                    if current_domain and current_constraints:
                        self.domains[current_domain] = PostgreSQLDomain(
                            name=current_domain,
                            schema=schema,
                            base_type=base_type,
                            constraints=current_constraints,
                            default=default,
                            comment=comment
                        )
                    # Start new domain
                    current_domain = domain_name
                    current_constraints = []

                # Add constraint if present
                if constraint_name and constraint_def:
                    current_constraints.append(DomainConstraint(
                        name=constraint_name,
                        definition=constraint_def,
                        check_clause=self._extract_check_clause(constraint_def),
                        is_not_null='NOT NULL' in constraint_def
                    ))

            # Save last domain
            if current_domain and current_constraints:
                self.domains[current_domain] = PostgreSQLDomain(
                    name=current_domain,
                    schema=schema,
                    base_type=base_type,
                    constraints=current_constraints,
                    default=default,
                    comment=comment
                )

    def _extract_check_clause(self, constraint_def: str) -> str:
        """Extract CHECK clause from constraint definition."""
        match = re.search(r'CHECK\s*\((.*)\)', constraint_def)
        return match.group(1) if match else ""

    def get_domain(self, name: str, schema: str = 'public') -> Optional[PostgreSQLDomain]:
        """Get domain type by name."""
        qualified_name = f"{schema}.{name}"
        return self.domains.get(qualified_name)

    def create_domain(self, domain: PostgreSQLDomain, connection) -> None:
        """
        Create a new domain type in the database.

        Args:
            domain: Domain type definition
            connection: Database connection
        """
        if domain.name in self.domains:
            raise PostgreSQLTypeError(
                f"Domain type already exists: {domain.name}",
                type_name=domain.name,
                details={'schema': domain.schema}
            )

        with connection.cursor() as cursor:
            cursor.execute(domain.to_sql())
            self.domains[domain.name] = domain

    def drop_domain(self,
                   name: str,
                   schema: str = 'public',
                   connection,
                   cascade: bool = False) -> None:
        """
        Drop a domain type.

        Args:
            name: Domain type name
            schema: Schema name
            connection: Database connection
            cascade: Whether to cascade the drop
        """
        qualified_name = f"{schema}.{name}"
        if qualified_name not in self.domains:
            raise PostgreSQLTypeError(
                f"Domain type does not exist: {name}",
                type_name=name,
                details={'schema': schema}
            )

        with connection.cursor() as cursor:
            sql = f"DROP DOMAIN {qualified_name}"
            if cascade:
                sql += " CASCADE"
            cursor.execute(sql)
            del self.domains[qualified_name]


# Singleton instance for global use
domain_manager = DomainManager()

def get_domain(name: str, schema: str = 'public') -> Optional[PostgreSQLDomain]:
    """Convenience function to get domain type."""
    return domain_manager.get_domain(name, schema)

def create_domain(domain: PostgreSQLDomain, connection) -> None:
    """Convenience function to create domain type."""
    domain_manager.create_domain(domain, connection)

def drop_domain(name: str, schema: str = 'public', connection, cascade: bool = False) -> None:
    """Convenience function to drop domain type."""
    domain_manager.drop_domain(name, schema, connection, cascade)
