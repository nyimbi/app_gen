"""
context.py: Generation context module.

This module defines the GenerationContext class, which serves as a central data structure
for holding and managing the information required during the model generation process.

The GenerationContext object is passed to the various handlers, allowing them to
update and share data as they process the database schema.
The GenerationContext class serves as a central data structure for holding and managing the information required during the model generation process. Here's a breakdown of its key components:

Data Structures: The class contains several dataclasses (ColumnInfo, ForeignKeyInfo, IndexInfo, ConstraintInfo, TableInfo, and Relationship) that represent the different elements of the database schema.
Generation Context: The GenerationContext class itself holds the following attributes:

table_info: The TableInfo object containing detailed information about the current table being processed.
config: The GeneratorConfig object with the configuration settings for the generation process.
type_map: A dictionary mapping database column types to their corresponding Python types.
relationships: A list of Relationship objects representing the relationships between tables.
imports: A set of import statements required for the model definitions.


Context Management: The class provides the following methods for managing the context:

add_import: Adds an import statement to the imports set.
add_relationship: Adds a Relationship object to the relationships list.
get_model_name: Generates the model name in PascalCase based on the table name.



The GenerationContext acts as a central repository for all the information required by the various handlers during the model generation process. By passing this context object to the handlers, they can update and share data as they process the database schema, ensuring a coordinated and consistent generation workflow.
The dataclasses defined in this module provide a structured representation of the different elements of the database schema, making it easier for the handlers to work with and manipulate the information.
This context.py file is an essential component of the model generation system, as it enables the various handlers to collaborate and produce the final SQLAlchemy model definitions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set
from sqlalchemy_model_generator.config.base_config import GeneratorConfig
from sqlalchemy_model_generator.utils.case_utils import to_pascal_case

@dataclass
class ColumnInfo:
    """
    Dataclass to hold information about a database column.

    Attributes:
        name (str): Name of the column.
        type (str): Data type of the column.
        nullable (bool): Whether the column allows null values.
        primary_key (bool): Whether the column is part of the primary key.
        default (any): Default value of the column.
        max_length (int): Maximum length of the column (for string types).
        precision (int): Precision for numeric types.
        scale (int): Scale for numeric types.
    """
    name: str
    type: str
    nullable: bool
    primary_key: bool
    default: any
    max_length: int
    precision: int
    scale: int


@dataclass
class ForeignKeyInfo:
    """
    Dataclass to hold information about a foreign key.

    Attributes:
        constrained_columns (List[str]): Names of the columns that make up the foreign key.
        referred_table (str): Name of the table the foreign key references.
        referred_columns (List[str]): Names of the columns in the referenced table.
    """
    constrained_columns: List[str]
    referred_table: str
    referred_columns: List[str]


@dataclass
class IndexInfo:
    """
    Dataclass to hold information about a database index.

    Attributes:
        name (str): Name of the index.
        column_names (List[str]): Names of the columns in the index.
        is_unique (bool): Whether the index is unique.
    """
    name: str
    column_names: List[str]
    is_unique: bool


@dataclass
class ConstraintInfo:
    """
    Dataclass to hold information about a database constraint.

    Attributes:
        name (str): Name of the constraint.
        constraint_type (str): Type of the constraint (e.g., "CHECK", "UNIQUE").
        definition (str): Definition of the constraint.
        columns (List[str]): Names of the columns involved in the constraint.
    """
    name: str
    constraint_type: str
    definition: str
    columns: List[str]


@dataclass
class TableInfo:
    """
    Dataclass to hold information about a database table.

    Attributes:
        name (str): Name of the table.
        columns (List[ColumnInfo]): List of column information.
        primary_key (List[str]): List of primary key column names.
        foreign_keys (List[ForeignKeyInfo]): List of foreign key information.
        indices (List[IndexInfo]): List of index information.
        constraints (List[ConstraintInfo]): List of constraint information.
    """
    name: str
    columns: List[ColumnInfo]
    primary_key: List[str]
    foreign_keys: List[ForeignKeyInfo]
    indices: List[IndexInfo]
    constraints: List[ConstraintInfo]


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


@dataclass
class GenerationContext:
    """
    Holds the information required during the model generation process.

    This context is passed to the various handlers, allowing them to update and share data
    as they process the database schema.

    Attributes:
        table_info (TableInfo): Information about the current table being processed.
        config (GeneratorConfig): Configuration for the generation process.
        type_map (Dict[str, str]): Mapping of database column types to Python types.
        relationships (List[Relationship]): List of relationship definitions.
        imports (Set[str]): Set of import statements required for the model definitions.
    """
    table_info: TableInfo
    config: GeneratorConfig
    type_map: Dict[str, str] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)

    def add_import(self, import_stmt: str) -> None:
        """
        Add an import statement to the generation context.

        Args:
            import_stmt (str): The import statement to be added.
        """
        self.imports.add(import_stmt)

    def add_relationship(self, relationship: Relationship) -> None:
        """
        Add a relationship definition to the generation context.

        Args:
            relationship (Relationship): The relationship to be added.
        """
        self.relationships.append(relationship)

    def get_model_name(self) -> str:
        """
        Get the model name based on the table name.

        Returns:
            str: The model name in PascalCase.
        """
        return to_pascal_case(self.table_info.name)
