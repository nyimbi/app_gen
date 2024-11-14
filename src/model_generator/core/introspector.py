#!/usr/bin/env python3
"""
introspector.py: Database Schema Introspection Module

This module provides comprehensive database schema introspection capabilities for the
Flask-AppBuilder code generator. It analyzes database structure, relationships, and
constraints to provide detailed information needed for model generation.

Key Features:
    - Database schema analysis and introspection
    - Relationship detection and analysis
    - Association table detection
    - Column type mapping
    - Constraint analysis
    - Index management
    - Context generation for model creation

The module maintains context throughout the introspection process, ensuring that
all gathered information is properly organized and accessible for the model
generation phase.

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from sqlalchemy import (
    create_engine, inspect, MetaData, Table, Column,
    ForeignKeyConstraint, Index, UniqueConstraint
)
from sqlalchemy.engine import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.engine.url import URL
from sqlalchemy.sql.type_api import TypeEngine

from model_generator.config.base_config import DatabaseConfig
from model_generator.core.context import (
    GenerationContext, TableInfo, ColumnInfo,
    ForeignKeyInfo, IndexInfo, ConstraintInfo, Relationship
)
from model_generator.utils.case_utils import to_snake_case, to_pascal_case
from model_generator.utils.validation_utils import validate_table_name, validate_column_name
from model_generator.exceptions import DatabaseIntrospectionError

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseIntrospector:
    """
    Database schema introspector for SQLAlchemy model generation.

    This class handles the introspection of database schemas, providing detailed
    information about tables, relationships, and other database objects needed
    for model generation.

    Attributes:
        config: Database configuration
        engine: SQLAlchemy engine
        inspector: SQLAlchemy inspector
        metadata: Database metadata
        contexts: Dictionary of generation contexts per table
        type_map: Database to Python type mapping
    """

    def __init__(self, config: DatabaseConfig):
        """
        Initialize the introspector.

        Args:
            config: Database configuration object
        """
        self.config = config
        self.engine = self._create_engine()
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.contexts: Dict[str, GenerationContext] = {}
        self.type_map = self._initialize_type_map()

        try:
            self.metadata.reflect(bind=self.engine)
        except Exception as e:
            raise DatabaseIntrospectionError(f"Failed to reflect database metadata: {e}") from e

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine from configuration."""
        try:
            engine = create_engine(
                self.config.uri,
                pool_size=self.config.connection_pool_size,
                pool_timeout=self.config.connection_timeout,
                pool_pre_ping=True
            )
            return engine
        except Exception as e:
            raise DatabaseIntrospectionError(f"Failed to create database engine: {e}") from e

    def _initialize_type_map(self) -> Dict[str, str]:
        """Initialize the database to Python type mapping."""
        base_type_map = {
            'integer': 'Integer',
            'bigint': 'BigInteger',
            'smallint': 'SmallInteger',
            'varchar': 'String',
            'text': 'Text',
            'boolean': 'Boolean',
            'datetime': 'DateTime',
            'date': 'Date',
            'time': 'Time',
            'float': 'Float',
            'numeric': 'Numeric',
            'decimal': 'Decimal',
            'binary': 'LargeBinary',
            'json': 'JSON',
            'jsonb': 'JSONB',
            'uuid': 'UUID',
        }

        # Add custom type mappings from config
        base_type_map.update(self.config.custom_type_mappings)
        return base_type_map

    def introspect_schema(self) -> Dict[str, GenerationContext]:
        """
        Perform complete schema introspection.

        Returns:
            Dict[str, GenerationContext]: Dictionary of contexts for each table
        """
        try:
            logger.info("Beginning schema introspection...")

            # Get all tables
            tables = self.get_tables()

            # Create contexts for each table
            for table in tables:
                if not self._should_process_table(table.name):
                    continue

                context = self.analyze_table(table.name)
                self.contexts[table.name] = context

            # Process relationships after all contexts are created
            self._process_relationships()

            # Detect and mark association tables
            self._identify_association_tables()

            logger.info(f"Schema introspection completed. Processed {len(self.contexts)} tables.")
            return self.contexts

        except Exception as e:
            raise DatabaseIntrospectionError("Schema introspection failed") from e

    def get_tables(self) -> List[Table]:
        """
        Get all tables in the configured schema.

        Returns:
            List[Table]: List of SQLAlchemy Table objects
        """
        try:
            table_names = self.inspector.get_table_names(schema=self.config.schema)
            return [self.metadata.tables[name] for name in table_names]
        except Exception as e:
            raise DatabaseIntrospectionError(f"Failed to retrieve tables: {e}") from e

    def analyze_table(self, table_name: str) -> GenerationContext:
        """
        Analyze a table and create its generation context.

        Args:
            table_name: Name of the table to analyze

        Returns:
            GenerationContext: Context containing table analysis
        """
        logger.debug(f"Analyzing table: {table_name}")

        if not validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        try:
            table = self.metadata.tables[table_name]

            # Collect table information
            table_info = TableInfo(
                name=table_name,
                columns=self._analyze_columns(table),
                primary_key=self._get_primary_key(table),
                foreign_keys=self._analyze_foreign_keys(table),
                indices=self._analyze_indices(table),
                constraints=self._analyze_constraints(table)
            )

            # Create context
            context = GenerationContext(
                table_info=table_info,
                config=self.config,
                type_map=self.type_map.copy()
            )

            # Add basic imports
            self._add_basic_imports(context)

            return context

        except Exception as e:
            raise DatabaseIntrospectionError(f"Failed to analyze table '{table_name}': {e}") from e

    def _analyze_columns(self, table: Table) -> List[ColumnInfo]:
        """
        Analyze columns of a table.

        Args:
            table: SQLAlchemy Table object

        Returns:
            List[ColumnInfo]: List of column information
        """
        columns = []
        for column in table.columns:
            if not validate_column_name(column.name):
                logger.warning(f"Invalid column name in {table.name}: {column.name}")
                continue

            try:
                column_info = ColumnInfo(
                    name=column.name,
                    type=self._get_column_type(column),
                    nullable=column.nullable,
                    primary_key=column.primary_key,
                    default=self._get_column_default(column),
                    max_length=self._get_column_length(column),
                    precision=getattr(column.type, 'precision', None),
                    scale=getattr(column.type, 'scale', None)
                )
                columns.append(column_info)
            except Exception as e:
                logger.error(f"Error analyzing column {column.name} in {table.name}: {e}")

        return columns

    def _get_column_type(self, column: Column) -> str:
        """
        Get the Python type name for a column.

        Args:
            column: SQLAlchemy Column object

        Returns:
            str: Python type name
        """
        type_name = column.type.__class__.__name__.lower()
        return self.type_map.get(type_name, 'String')

    def _get_column_default(self, column: Column) -> Optional[Any]:
        """
        Get the default value for a column.

        Args:
            column: SQLAlchemy Column object

        Returns:
            Optional[Any]: Default value if exists
        """
        if column.default is None:
            return None

        if column.default.is_scalar:
            return column.default.arg

        # For server_default or complex defaults, return as string
        return str(column.default)

    def _get_column_length(self, column: Column) -> Optional[int]:
        """
        Get the length constraint for a column.

        Args:
            column: SQLAlchemy Column object

        Returns:
            Optional[int]: Length constraint if exists
        """
        if hasattr(column.type, 'length'):
            return column.type.length
        return None

    def _get_primary_key(self, table: Table) -> List[str]:
        """
        Get primary key column names for a table.

        Args:
            table: SQLAlchemy Table object

        Returns:
            List[str]: Names of primary key columns
        """
        try:
            pk_constraint = self.inspector.get_pk_constraint(table.name, schema=self.config.schema)
            return pk_constraint['constrained_columns']
        except Exception as e:
            logger.error(f"Error getting primary key for {table.name}: {e}")
            return []

    def _should_process_table(self, table_name: str) -> bool:
        """
        Determine if a table should be processed based on configuration.

        Args:
            table_name: Name of the table

        Returns:
            bool: True if table should be processed
        """
        if self.config.include_tables:
            return table_name in self.config.include_tables
        return table_name not in self.config.exclude_tables

    def _add_basic_imports(self, context: GenerationContext) -> None:
        """
        Add basic SQLAlchemy imports to context.

        Args:
            context: Generation context to update
        """
        context.add_import('from sqlalchemy import Column, Integer, String')
        context.add_import('from sqlalchemy.ext.declarative import declarative_base')

    def _analyze_foreign_keys(self, table: Table) -> List[ForeignKeyInfo]:
        """
        Analyze foreign key relationships for a table.

        Args:
            table: SQLAlchemy Table object

        Returns:
            List[ForeignKeyInfo]: Foreign key information
        """
        try:
            foreign_keys = []
            for fk in self.inspector.get_foreign_keys(table.name, schema=self.config.schema):
                foreign_keys.append(ForeignKeyInfo(
                    constrained_columns=fk['constrained_columns'],
                    referred_table=fk['referred_table'],
                    referred_columns=fk['referred_columns']
                ))
            return foreign_keys
        except Exception as e:
            logger.error(f"Error analyzing foreign keys for {table.name}: {e}")
            return []

    def _analyze_relationships(self) -> Dict[str, List[Relationship]]:
        """
        Analyze all relationships in the database schema.

        Returns:
            Dict[str, List[Relationship]]: Relationships by table
        """
        relationships = {}
        try:
            for table_name, context in self.contexts.items():
                rels = self._analyze_table_relationships(table_name)
                relationships[table_name] = rels

                # Update context with relationships
                for rel in rels:
                    context.add_relationship(rel)
                    self._add_relationship_imports(context)

            return relationships
        except Exception as e:
            logger.error(f"Error analyzing relationships: {e}")
            return relationships

    def _analyze_table_relationships(self, table_name: str) -> List[Relationship]:
        """
        Analyze relationships for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            List[Relationship]: List of relationships
        """
        relationships = []
        table = self.metadata.tables[table_name]

        try:
            # Analyze foreign key relationships
            for fk in table.foreign_keys:
                rel = self._create_foreign_key_relationship(table, fk)
                if rel:
                    relationships.append(rel)

            # Analyze many-to-many relationships
            if self._is_association_table(table_name):
                m2m_rels = self._create_many_to_many_relationships(table)
                relationships.extend(m2m_rels)

            return relationships
        except Exception as e:
            logger.error(f"Error analyzing relationships for {table_name}: {e}")
            return relationships

    def _create_foreign_key_relationship(self, table: Table, fk: ForeignKeyConstraint) -> Optional[Relationship]:
        """
        Create a relationship definition from a foreign key.

        Args:
            table: Source table
            fk: Foreign key constraint

        Returns:
            Optional[Relationship]: Created relationship
        """
        try:
            target_table = fk.column.table.name
            relationship_type = self._determine_relationship_type(table, fk)

            return Relationship(
                source_table=table.name,
                target_table=target_table,
                relationship_type=relationship_type,
                foreign_keys=[col.name for col in fk.constraint.columns],
                backref_name=self._generate_backref_name(table.name, target_table, relationship_type),
                is_nullable=any(col.nullable for col in fk.constraint.columns),
                cascade_options=self._get_cascade_options(relationship_type)
            )
        except Exception as e:
            logger.error(f"Error creating relationship for {table.name}: {e}")
            return None

    def _determine_relationship_type(self, table: Table, fk: ForeignKeyConstraint) -> str:
        """
        Determine the type of relationship based on the foreign key configuration.

        Args:
            table: Source table
            fk: Foreign key constraint

        Returns:
            str: Relationship type
        """
        # Check if this is part of a one-to-one relationship
        if self._is_one_to_one(table, fk):
            return 'one_to_one'

        # Check if the foreign key is part of the primary key
        if self._is_many_to_one(table, fk):
            return 'many_to_one'

        return 'one_to_many'

    def _is_one_to_one(self, table: Table, fk: ForeignKeyConstraint) -> bool:
        """
        Determine if a foreign key represents a one-to-one relationship.

        Args:
            table: Source table
            fk: Foreign key constraint

        Returns:
            bool: True if one-to-one
        """
        # Check if the foreign key columns are unique
        fk_cols = set(fk.constraint.columns)
        return any(
            set(idx['column_names']) == fk_cols
            for idx in self.inspector.get_indexes(table.name)
            if idx.get('unique', False)
        )

    def _is_many_to_one(self, table: Table, fk: ForeignKeyConstraint) -> bool:
        """
        Determine if a foreign key represents a many-to-one relationship.

        Args:
            table: Source table
            fk: Foreign key constraint

        Returns:
            bool: True if many-to-one
        """
        pk_cols = set(self._get_primary_key(table))
        fk_cols = set(col.name for col in fk.constraint.columns)
        return bool(fk_cols & pk_cols)

    def _generate_backref_name(self, source_table: str, target_table: str, relationship_type: str) -> str:
        """
        Generate an appropriate backref name for a relationship.

        Args:
            source_table: Source table name
            target_table: Target table name
            relationship_type: Type of relationship

        Returns:
            str: Generated backref name
        """
        if relationship_type == 'one_to_many':
            return f"{to_snake_case(source_table)}s"
        if relationship_type == 'many_to_one':
            return to_snake_case(source_table)
        if relationship_type == 'one_to_one':
            return to_snake_case(source_table)
        return f"{to_snake_case(source_table)}_collection"

    def _get_cascade_options(self, relationship_type: str) -> List[str]:
        """
        Get appropriate cascade options for a relationship type.

        Args:
            relationship_type: Type of relationship

        Returns:
            List[str]: Cascade options
        """
        if relationship_type in ('one_to_many', 'one_to_one'):
            return ['all, delete-orphan'] if self.config.cascade_deletions else ['save-update']
        return ['save-update']

    def _add_relationship_imports(self, context: GenerationContext) -> None:
        """
        Add imports required for relationships.

        Args:
            context: Generation context to update
        """
        context.add_import('from sqlalchemy.orm import relationship, backref')
        context.add_import('from sqlalchemy import ForeignKey')
    def _identify_association_tables(self) -> None:
            """
            Identify and mark association tables in the schema.
            Updates contexts to reflect many-to-many relationships.
            """
            try:
                for table_name in self.contexts:
                    if self._is_association_table(table_name):
                        self._process_association_table(table_name)
            except Exception as e:
                logger.error(f"Error identifying association tables: {e}")

    def _is_association_table(self, table_name: str) -> bool:
        """
        Determine if a table is an association table.

        Args:
            table_name: Name of the table to check

        Returns:
            bool: True if the table is an association table
        """
        try:
            table = self.metadata.tables[table_name]

            # Check criteria for association table:
            # 1. Has exactly two foreign keys
            # 2. All columns are either FK or PK
            # 3. No other unique constraints except PK

            foreign_keys = self._analyze_foreign_keys(table)
            if len(foreign_keys) != 2:
                return False

            columns = set(col.name for col in table.columns)
            fk_columns = set()
            for fk in foreign_keys:
                fk_columns.update(fk.constrained_columns)

            pk_columns = set(self._get_primary_key(table))
            non_key_columns = columns - (fk_columns | pk_columns)

            # All columns should be part of either FK or PK
            return len(non_key_columns) == 0
        except Exception as e:
            logger.error(f"Error checking association table {table_name}: {e}")
            return False

    def _process_association_table(self, table_name: str) -> None:
        """
        Process an association table and create many-to-many relationships.

        Args:
            table_name: Name of the association table
        """
        try:
            table = self.metadata.tables[table_name]
            foreign_keys = self._analyze_foreign_keys(table)

            if len(foreign_keys) != 2:
                return

            # Create many-to-many relationships in both directions
            left_table = foreign_keys[0].referred_table
            right_table = foreign_keys[1].referred_table

            self._create_many_to_many_relationship(
                left_table, right_table, table_name, foreign_keys[0], foreign_keys[1]
            )
            self._create_many_to_many_relationship(
                right_table, left_table, table_name, foreign_keys[1], foreign_keys[0]
            )
        except Exception as e:
            logger.error(f"Error processing association table {table_name}: {e}")

    def _create_many_to_many_relationship(
        self, source: str, target: str, association: str,
        source_fk: ForeignKeyInfo, target_fk: ForeignKeyInfo
    ) -> None:
        """
        Create a many-to-many relationship between two tables.

        Args:
            source: Source table name
            target: Target table name
            association: Association table name
            source_fk: Source foreign key info
            target_fk: Target foreign key info
        """
        try:
            if source not in self.contexts or target not in self.contexts:
                return

            relationship = Relationship(
                source_table=source,
                target_table=target,
                relationship_type='many_to_many',
                foreign_keys=[],  # No direct FKs for many-to-many
                backref_name=self._generate_backref_name(source, target, 'many_to_many'),
                is_nullable=True,
                cascade_options=['save-update'],
                secondary=association,
                secondary_join=self._generate_secondary_join(source_fk, target_fk)
            )

            self.contexts[source].add_relationship(relationship)
            self._add_many_to_many_imports(self.contexts[source])
        except Exception as e:
            logger.error(f"Error creating M2M relationship {source}-{target}: {e}")

    def _analyze_indices(self, table: Table) -> List[IndexInfo]:
        """
        Analyze indices for a table.

        Args:
            table: SQLAlchemy Table object

        Returns:
            List[IndexInfo]: List of index information
        """
        try:
            indices = []
            for idx in self.inspector.get_indexes(table.name, schema=self.config.schema):
                indices.append(IndexInfo(
                    name=idx['name'],
                    column_names=idx['column_names'],
                    is_unique=idx.get('unique', False)
                ))
            return indices
        except Exception as e:
            logger.error(f"Error analyzing indices for {table.name}: {e}")
            return []

    def _analyze_constraints(self, table: Table) -> List[ConstraintInfo]:
        """
        Analyze constraints for a table.

        Args:
            table: SQLAlchemy Table object

        Returns:
            List[ConstraintInfo]: List of constraint information
        """
        try:
            constraints = []
            for const in self.inspector.get_constraints(table.name, schema=self.config.schema):
                if const['name'] is None:  # Skip unnamed constraints
                    continue

                constraints.append(ConstraintInfo(
                    name=const['name'],
                    constraint_type=const['type'],
                    definition=const.get('sqltext', ''),
                    columns=const['column_names']
                ))
            return constraints
        except Exception as e:
            logger.error(f"Error analyzing constraints for {table.name}: {e}")
            return []

    def _generate_secondary_join(
        self, source_fk: ForeignKeyInfo, target_fk: ForeignKeyInfo
    ) -> Dict[str, Any]:
        """
        Generate the join condition for a secondary (association) table.

        Args:
            source_fk: Source foreign key info
            target_fk: Target foreign key info

        Returns:
            Dict[str, Any]: Join condition configuration
        """
        return {
            'primaryjoin': f"{source_fk.referred_table}.{source_fk.referred_columns[0]} == "
                            f"{source_fk.constrained_columns[0]}",
            'secondaryjoin': f"{target_fk.referred_table}.{target_fk.referred_columns[0]} == "
                            f"{target_fk.constrained_columns[0]}"
        }

    def _add_many_to_many_imports(self, context: GenerationContext) -> None:
        """
        Add imports required for many-to-many relationships.

        Args:
            context: Generation context to update
        """
        context.add_import('from sqlalchemy.orm import relationship, backref, secondary')
        context.add_import('from sqlalchemy import Table, Column, ForeignKey')

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.engine:
                self.engine.dispose()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __enter__(self) -> 'DatabaseIntrospector':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.cleanup()


"""
Usage:
config = DatabaseConfig(uri="postgresql://user:pass@localhost/dbname")

with DatabaseIntrospector(config) as introspector:
    # Get all contexts
    contexts = introspector.introspect_schema()

    # Process specific tables
    for table_name, context in contexts.items():
        print(f"Table: {table_name}")
        print(f"Relationships: {len(context.relationships)}")
        print(f"Required imports: {context.imports}")
"""
