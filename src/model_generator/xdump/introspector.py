"""
introspector.py: Database schema introspection module.

This module contains the DatabaseIntrospector class, which is responsible for:
- Retrieving information about the tables in the database
- Detecting relationships between tables
- Identifying association tables used for many-to-many relationships
- Providing a unified interface to access schema information

The DatabaseIntrospector class utilizes the SQLAlchemy engine and inspector to
introspect the database schema and extract the required information.
"""

from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from sqlalchemy import create_engine, inspect, MetaData, Table, ForeignKeyConstraint
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.engine.url import URL
from model_generator.config.base_config import DatabaseConfig
from model_generator.utils.case_utils import to_snake_case
from model_generator.utils.validation_utils import validate_table_name, validate_column_name
from model_generator.exceptions import DatabaseIntrospectionError

@dataclass
class Relationship:
    """
    Dataclass to hold information about a relationship between tables.

    Attributes:
        source_table (str): Name of the table containing the foreign key.
        target_table (str): Name of the table being referenced.
        relationship_type (str): Type of the relationship (e.g., one-to-many, one-to-one, many-to-many).
        foreign_keys (List[str]): Names of the foreign key columns.
        backref_name (Optional[str]): Name of the backref attribute.
        is_nullable (bool): Whether the relationship is nullable.
        cascade_options (List[str]): Cascade options for the relationship.
    """
    source_table: str
    target_table: str
    relationship_type: str
    foreign_keys: List[str]
    backref_name: str
    is_nullable: bool
    cascade_options: List[str]


class DatabaseIntrospector:
    """
    Responsible for introspecting the database schema and providing information about the tables, columns, relationships, and other database artifacts.

    Args:
        config (DatabaseConfig): Configuration for the database connection.
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = create_engine(URL(**config.connection_info))
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)

    def get_tables(self) -> List[Table]:
        """
        Retrieve a list of all tables in the database.

        Returns:
            List[Table]: List of SQLAlchemy Table objects.
        """
        try:
            table_names = self.inspector.get_table_names(schema=self.config.schema)
            return [self.metadata.tables[name] for name in table_names]
        except Exception as e:
            raise DatabaseIntrospectionError(f"Error retrieving tables: {e}") from e

    def analyze_table(self, table_name: str) -> 'TableInfo':
        """
        Analyze a specific table and collect detailed information about its structure.

        Args:
            table_name (str): Name of the table to analyze.

        Returns:
            TableInfo: Dataclass containing information about the table.
        """
        if not validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        try:
            table = self.metadata.tables[table_name]
            columns = self.analyze_columns(table)
            primary_key = self.get_primary_key(table)
            foreign_keys = self.analyze_foreign_keys(table)
            indices = self.analyze_indices(table)
            constraints = self.analyze_constraints(table)

            return TableInfo(
                name=table_name,
                columns=columns,
                primary_key=primary_key,
                foreign_keys=foreign_keys,
                indices=indices,
                constraints=constraints
            )
        except Exception as e:
            raise DatabaseIntrospectionError(f"Error analyzing table '{table_name}': {e}") from e

    def analyze_columns(self, table: Table) -> List['ColumnInfo']:
        """
        Analyze the columns of a given table and collect detailed information about each column.

        Args:
            table (Table): SQLAlchemy Table object.

        Returns:
            List[ColumnInfo]: List of ColumnInfo dataclasses.
        """
        columns = []
        for column in table.columns:
            if not validate_column_name(column.name):
                raise ValueError(f"Invalid column name: {column.name}")
            columns.append(ColumnInfo(
                name=column.name,
                type=str(column.type),
                nullable=column.nullable,
                primary_key=column.primary_key,
                default=column.default.arg if column.default else None,
                max_length=getattr(column.type, 'length', None),
                precision=getattr(column.type, 'precision', None),
                scale=getattr(column.type, 'scale', None)
            ))
        return columns

    def get_primary_key(self, table: Table) -> List[str]:
        """
        Retrieve the names of the primary key columns for a given table.

        Args:
            table (Table): SQLAlchemy Table object.

        Returns:
            List[str]: List of primary key column names.
        """
        try:
            pk_constraint = self.inspector.get_pk_constraint(table.name, schema=self.config.schema)
            return pk_constraint['constrained_columns']
        except Exception as e:
            raise DatabaseIntrospectionError(f"Error retrieving primary key for table '{table.name}': {e}") from e

    def analyze_foreign_keys(self, table: Table) -> List['ForeignKeyInfo']:
        """
        Analyze the foreign keys of a given table and collect detailed information about each foreign key.

        Args:
            table (Table): SQLAlchemy Table object.

        Returns:
            List[ForeignKeyInfo]: List of ForeignKeyInfo dataclasses.
        """
        foreign_keys = []
        for fk in table.foreign_keys:
            foreign_keys.append(ForeignKeyInfo(
                constrained_columns=[col.name for col in fk.constraint.columns],
                referred_table=fk.referred_table.name,
                referred_columns=[col.name for col in fk.referred_table.primary_key]
            ))
        return foreign_keys

    def analyze_indices(self, table: Table) -> List['IndexInfo']:
        """
        Analyze the indices of a given table and collect detailed information about each index.

        Args:
            table (Table): SQLAlchemy Table object.

        Returns:
            List[IndexInfo]: List of IndexInfo dataclasses.
        """
        try:
            indices = []
            for index in self.inspector.get_indexes(table.name, schema=self.config.schema):
                indices.append(IndexInfo(
                    name=index['name'],
                    column_names=index['column_names'],
                    is_unique=index['unique']
                ))
            return indices
        except Exception as e:
            raise DatabaseIntrospectionError(f"Error analyzing indices for table '{table.name}': {e}") from e

    def analyze_constraints(self, table: Table) -> List['ConstraintInfo']:
        """
        Analyze the constraints of a given table and collect detailed information about each constraint.

        Args:
            table (Table): SQLAlchemy Table object.

        Returns:
            List[ConstraintInfo]: List of ConstraintInfo dataclasses.
        """
        try:
            constraints = []
            for constraint in self.inspector.get_constraints(table.name, schema=self.config.schema):
                constraints.append(ConstraintInfo(
                    name=constraint['name'],
                    constraint_type=constraint['type'],
                    definition=constraint['sqltext'],
                    columns=constraint['column_names']
                ))
            return constraints
        except Exception as e:
            raise DatabaseIntrospectionError(f"Error analyzing constraints for table '{table.name}': {e}") from e

    def get_relationships(self) -> Dict[str, List['Relationship']]:
        """
        Detect and analyze the relationships between tables in the database.

        Returns:
            Dict[str, List[Relationship]]: Dictionary mapping table names to a list of relationships.
        """
        relationships = {}
        for table in self.get_tables():
            table_name = table.name
            table_relationships = self.analyze_table_relationships(table)
            relationships[table_name] = table_relationships
        return relationships

    def analyze_table_relationships(self, table: Table) -> List['Relationship']:
        """
        Analyze the relationships for a given table.

        Args:
            table (Table): SQLAlchemy Table object.

        Returns:
            List[Relationship]: List of Relationship dataclasses.
        """
        relationships = []
        for fk in table.foreign_keys:
            relationships.append(Relationship(
                source_table=table.name,
                target_table=fk.referred_table.name,
                relationship_type="one-to-many",  # Assuming foreign key relationship
                foreign_keys=[col.name for col in fk.constraint.columns],
                backref_name=None,
                is_nullable=any(col.nullable for col in fk.constraint.columns),
                cascade_options=[]
            ))

        # Add code to detect other types of relationships (one-to-one, many-to-many, etc.)

        return relationships

    def detect_association_tables(self) -> Set[str]:
        """
        Detect any association tables used for many-to-many relationships in the database.

        Returns:
            Set[str]: Set of association table names.
        """
        association_tables = set()
        for table_name in self.inspector.get_table_names(schema=self.config.schema):
            if self.is_association_table(table_name):
                association_tables.add(table_name)
        return association_tables

    def is_association_table(self, table_name: str) -> bool:
        """
        Determine if a given table is an association table.

        Args:
            table_name (str): Name of the table to check.

        Returns:
            bool: True if the table is an association table, False otherwise.
        """
        try:
            # Heuristic: Association tables typically have at least two foreign keys
            foreign_keys = self.inspector.get_foreign_keys(table_name, schema=self.config.schema)
            return len(foreign_keys) >= 2
        except Exception as e:
            raise DatabaseIntrospectionError(f"Error checking if '{table_name}' is an association table: {e}") from e

    def get_table_info(self, table_name: str) -> 'TableInfo':
        """
        Retrieve detailed information about a specific table.

        Args:
            table_name (str): Name of the table.

        Returns:
            TableInfo: Dataclass containing information about the table.
        """
        if table_name not in self.metadata.tables:
            raise ValueError(f"Table '{table_name}' does not exist in the database.")
        return self.analyze_table(table_name)

    def get_schema_info(self) -> Dict[str, 'TableInfo']:
        """
        Retrieve detailed information about the entire database schema.

        Returns:
            Dict[str, TableInfo]: Dictionary mapping table names to TableInfo dataclasses.
        """
        schema_info = {}
        for table_name in self.get_tables():
            schema_info[table_name] = self.get_table_info(table_name)
        return schema_info
