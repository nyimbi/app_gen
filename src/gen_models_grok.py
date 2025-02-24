"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024-2025
License: MIT

gen_models.py: Flask-AppBuilder SQLAlchemy Model Generator

Generates SQLAlchemy ORM models for Flask-AppBuilder by introspecting an existing database schema.
Supports PostgreSQL databases and generates Python code representing the database structure.
"""

import argparse
import logging
from typing import List, Dict, Optional, Set, Any, Tuple
import sys
import enum

from sqlalchemy import (
    create_engine, inspect, MetaData, Column, ForeignKey,
    CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, Index,
    func, text, String, LargeBinary, DateTime, Enum
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import sqltypes

import inflect

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants and globals
Base = declarative_base()
p = inflect.engine()
INDENT = "    "
AB_PREFIX = 'ab_'

# Intelligent defaults
CONFIG = {
    "indent_size": 4,
    "naming_convention": "snake_case",
    "relationship_style": "back_populates",
    "fab_integration": True
}

class ModelGenerator:
    """Main class for generating Flask-AppBuilder compatible SQLAlchemy models"""
    
    def __init__(self):
        self.processed_relationships: Set[tuple] = set()
        self.metadata = MetaData()
        self.engine = None
        self.inspector = None
        
    def initialize_db_connection(self, uri: str) -> None:
        """Initialize database connection and inspection"""
        try:
            self.engine = create_engine(uri)
            self.inspector = inspect(self.engine)
            self.metadata.reflect(bind=self.engine)
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise
            
    def generate_models(self) -> List[str]:
        """Generate complete model code"""
        try:
            if not self.inspector or not self.metadata:
                raise ValueError("Database connection not initialized")
                
            model_code = []
            reverse_relationships: Dict[str, List[str]] = {}
            association_tables = self._identify_association_tables()
            
            # Generate preamble
            model_code.extend(self._generate_preamble())
            
            # Generate model definitions
            for table_name in self.inspector.get_table_names():
                table = self.metadata.tables[table_name]
                if table_name in association_tables:
                    table_code = self._generate_association_table(table)
                else:
                    table_code, reverse_rels = self._generate_table(table, association_tables)
                    for rev_rel in reverse_rels:
                        reverse_relationships.setdefault(rev_rel['table'], []).append(rev_rel['code'])
                model_code.extend(table_code)
                
            # Add reverse relationships
            self._add_reverse_relationships(model_code, reverse_relationships)
            
            # Add Flask-AppBuilder integrations
            if CONFIG["fab_integration"]:
                model_code.extend(self._generate_fab_integrations())
                
            return model_code
            
        except Exception as e:
            logger.error(f"Error generating models: {str(e)}")
            raise
            
    def _identify_association_tables(self) -> List[str]:
        """Identify many-to-many association tables"""
        assoc_tables = []
        for table_name in self.inspector.get_table_names():
            fks = self.inspector.get_foreign_keys(table_name)
            if len(fks) >= 2 and all(fk['constrained_columns'] for fk in fks):
                assoc_tables.append(table_name)
        return assoc_tables
        
    def _generate_preamble(self) -> List[str]:
        """Generate file header and supporting definitions"""
        preamble = [
            "from flask_appbuilder import Model",
            "from sqlalchemy import Column, ForeignKey, DateTime, String, LargeBinary",
            "from sqlalchemy.orm import relationship",
            "from sqlalchemy.sql import func",
            "import enum",
            "\n"
        ]
        preamble.extend(self._generate_enums())
        preamble.extend(self._generate_misc_tables())
        return preamble
        
    def _generate_enums(self) -> List[str]:
        """Generate enum definitions"""
        enum_code = ['# Database Enums']
        try:
            for enum in self.inspector.get_enums():
                enum_code.append(f"\nclass {enum['name'].title()}(enum.Enum):")
                for label in enum["labels"]:
                    enum_code.append(f"{INDENT}{label.upper()} = '{label}'")
        except Exception as e:
            logger.warning(f"Failed to generate enums: {str(e)}")
        enum_code.append("\n")
        return enum_code
        
    def _generate_table(self, table, association_tables: List[str]) -> Tuple[List[str], List[Dict]]:
        """Generate code for a regular table"""
        try:
            table_code = []
            reverse_relationships = []
            
            table_class = self._snake_to_pascal(table.name)
            table_code.append(f"class {table_class}(Model):")
            table_code.append(f"{INDENT}__tablename__ = '{table.name}'")
            
            # Table properties
            columns = self.inspector.get_columns(table.name)
            fks = self.inspector.get_foreign_keys(table.name)
            pk = self.inspector.get_pk_constraint(table.name)
            uqs = self.inspector.get_unique_constraints(table.name)
            indexes = self.inspector.get_indexes(table.name)
            table_comment = self.inspector.get_table_comment(table.name)
            
            # Generate table arguments and columns
            table_code.extend(self._generate_table_args(pk, uqs, indexes, table_comment))
            table_code.extend(self._generate_columns(columns, pk, fks, uqs, table.name))
            
            # Generate relationships
            relationship_info = self._prepare_relationship_info(association_tables)
            for fk in fks:
                local_rel, reverse_rel = self._generate_relationship(
                    fk, table.name, table_class, relationship_info, association_tables
                )
                table_code.extend(local_rel)
                if reverse_rel:
                    reverse_relationships.append(reverse_rel)
                    
            # Add table methods
            table_code.extend(self._generate_check_constraints(table.name))
            table_code.extend(self._generate_repr_method(columns, pk))
            table_code.append("\n")
            
            return table_code, reverse_relationships
            
        except Exception as e:
            logger.error(f"Error generating table {table.name}: {str(e)}")
            return [], []
            
    def _generate_association_table(self, table) -> List[str]:
        """Generate code for an association table"""
        table_code = []
        table_name = table.name
        columns = self.inspector.get_columns(table_name)
        fks = self.inspector.get_foreign_keys(table_name)
        pk = self.inspector.get_pk_constraint(table_name)
        uqs = self.inspector.get_unique_constraints(table_name)
        table_comment = self.inspector.get_table_comment(table_name)
        
        table_class = self._snake_to_pascal(table_name)
        table_code.append(f"class {table_class}(Model):")
        table_code.append(f"{INDENT}__tablename__ = '{table_name}'")
        
        # Generate columns
        table_code.extend(self._generate_columns(columns, pk, fks, uqs, table_name, is_association=True))
        
        # Add table args if comment exists
        if table_comment['text']:
            table_code.append(f"{INDENT}__table_args__ = {{'comment': \"{table_comment['text']}\"}}")
            
        table_code.append("\n")
        return table_code
        
    def _generate_columns(self, columns: List[Dict], pk: Dict, fks: List[Dict], 
                         uqs: List[Dict], table_name: str, is_association: bool = False) -> List[str]:
        """Generate column definitions"""
        column_code = []
        pk_columns = pk['constrained_columns']
        
        for column in columns:
            col_name = column["name"]
            col_type = self._map_pgsql_datatypes(str(column['type']).lower())
            attributes = []
            
            # Foreign key handling
            for fk in fks:
                if col_name in fk["constrained_columns"]:
                    ref_table = fk["referred_table"]
                    ref_col = fk["referred_columns"][0]
                    attributes.append(f"ForeignKey('{ref_table}.{ref_col}')")
                    
            # Primary key and constraints
            if col_name in pk_columns:
                attributes.append("primary_key=True")
            if not column.get("nullable", True):
                attributes.append("nullable=False")
            if any(col_name in uq["column_names"] for uq in uqs):
                attributes.append("unique=True")
            if column.get('default') is not None:
                default = self._process_default_value(col_name, col_type, column['default'])
                if default:
                    attributes.append(f"default={default}")
            if column.get("comment"):
                attributes.append(f"comment=\"{column['comment']}\"")
                
            # Column definition
            attrs_str = ", ".join(attributes)
            if attrs_str:
                column_code.append(f"{INDENT}{col_name} = Column({col_type}, {attrs_str})")
            else:
                column_code.append(f"{INDENT}{col_name} = Column({col_type})")
                
        return column_code
        
    def _generate_relationship(self, fk: Dict, table_name: str, table_class: str,
                            relationship_info: Dict, association_tables: List[str]) -> Tuple[List[str], Optional[Dict]]:
        """Generate relationship definitions"""
        rel_code = []
        fk_cols = fk["constrained_columns"]
        ref_table = fk["referred_table"]
        ref_class = self._snake_to_pascal(ref_table)
        
        rel_key = (table_name, ref_table)
        if rel_key in self.processed_relationships:
            return [], None
            
        cardinality = relationship_info.get(table_name, {}).get(ref_table, 'many-to-one')
        local_name = self._determine_relationship_name(fk_cols, table_name, ref_table, cardinality)
        remote_name = self._determine_remote_relationship_name(cardinality, table_name, ref_table)
        
        if cardinality == 'many-to-many':
            assoc_table = self._find_association_table(table_name, ref_table, association_tables)
            rel_args = [f"'{ref_class}'", f"secondary='{assoc_table}'", f"back_populates='{remote_name}'"]
        else:
            rel_args = [f"'{ref_class}'", f"back_populates='{remote_name}'",
                       f"foreign_keys='[{table_class}.{fk_cols[0]}]'"]
                       
        rel_code.append(f"{INDENT}{local_name} = relationship({', '.join(rel_args)})")
        
        rev_args = [f"'{table_class}'", f"back_populates='{local_name}'",
                   f"foreign_keys='[{table_class}.{fk_cols[0]}]'"]
        reverse_rel = {'table': ref_table, 'code': f"{remote_name} = relationship({', '.join(rev_args)})"}
        
        self.processed_relationships.add(rel_key)
        return rel_code, reverse_rel
        
    def _generate_table_args(self, pk: Dict, uqs: List[Dict], indexes: List[Dict], 
                           table_comment: Dict) -> List[str]:
        """Generate table arguments"""
        args = []
        if len(pk['constrained_columns']) > 1:
            cols = ", ".join(f"'{col}'" for col in pk['constrained_columns'])
            args.append(f"PrimaryKeyConstraint({cols})")
            
        for uq in uqs:
            cols = ", ".join(f"'{col}'" for col in uq["column_names"])
            args.append(f"UniqueConstraint({cols}, name='{uq['name']}')")
            
        for idx in indexes:
            cols = ", ".join(f"'{col}'" for col in idx["column_names"])
            unique = ", unique=True" if idx["unique"] else ""
            args.append(f"Index('{idx['name']}', {cols}{unique})")
            
        if table_comment.get('text'):
            args.append(f"{{'comment': \"{table_comment['text']}\"}}")
            
        if args:
            return [f"{INDENT}__table_args__ = ({', '.join(args)},)"]
        return []
        
    def _generate_check_constraints(self, table_name: str) -> List[str]:
        """Generate check constraints"""
        constraints = self.inspector.get_check_constraints(table_name)
        if not constraints:
            return []
            
        code = []
        for cc in constraints:
            code.append(f"{INDENT}__table_args__ = (CheckConstraint('{cc['sqltext']}', name='{cc['name']}'),)")
        return code
        
    def _generate_repr_method(self, columns: List[Dict], pk: Dict) -> List[str]:
        """Generate repr method"""
        repr_cols = [col['name'] for col in columns if col['name'] in ['name', 'title', 'id']][:2]
        if not repr_cols:
            repr_cols = pk['constrained_columns'][:2]
            
        attrs = ", ".join(f"{col}={{self.{col}}}" for col in repr_cols)
        return [
            f"{INDENT}def __repr__(self):",
            f"{INDENT}{INDENT}return f'<{{self.__class__.__name__}} {attrs}>'"
        ]
        
    def _generate_fab_integrations(self) -> List[str]:
        """Generate Flask-AppBuilder specific integrations"""
        return [
            "\n# Flask-AppBuilder Security Integration",
            "from flask_appbuilder.security.sqla.models import User",
            "\n"
        ]
        
    def _generate_misc_tables(self) -> List[str]:
        """Generate miscellaneous tables like FlaskSession"""
        return [
            "class FlaskSession(Model):",
            f"{INDENT}__tablename__ = 'nx_sessions'",
            f"{INDENT}id = Column(String(256), primary_key=True)",
            f"{INDENT}data = Column(LargeBinary)",
            f"{INDENT}expiry = Column(DateTime, nullable=False)",
            f"{INDENT}created = Column(DateTime, default=func.now())",
            f"{INDENT}modified = Column(DateTime, default=func.now(), onupdate=func.now())",
            f"{INDENT}def __repr__(self):",
            f"{INDENT}{INDENT}return f'<Session {{self.id}}>'",
            "\n"
        ]
        
    def _add_reverse_relationships(self, model_code: List[str], reverse_relationships: Dict[str, List[str]]) -> None:
        """Add reverse relationships to appropriate tables"""
        for table_name, relationships in reverse_relationships.items():
            table_index = next(
                (i for i, line in enumerate(model_code) if line.startswith(f"class {self._snake_to_pascal(table_name)}(")),
                None
            )
            if table_index is not None:
                insert_index = self._find_insertion_index(model_code, table_index)
                for rel in relationships:
                    model_code.insert(insert_index, f"{INDENT}{rel}")
                    model_code.insert(insert_index + 1, "")
                    
    def _find_insertion_index(self, model_code: List[str], table_start: int) -> int:
        """Find appropriate insertion point for relationships"""
        for i, line in enumerate(model_code[table_start + 1:], start=table_start + 1):
            if line.strip().startswith("def ") or line.startswith("class "):
                return i
        return len(model_code)
        
    def _snake_to_pascal(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))
        
    def _map_pgsql_datatypes(self, pg_type: str) -> str:
        """Map PostgreSQL types to SQLAlchemy types"""
        type_map = {
            'integer': 'Integer',
            'bigint': 'BigInteger',
            'character varying': 'String',
            'text': 'Text',
            'timestamp': 'DateTime',
            'boolean': 'Boolean',
            'json': 'JSON'
        }
        return type_map.get(pg_type, 'String')
        
    def _process_default_value(self, col_name: str, col_type: str, default: Any) -> Optional[str]:
        """Process default values"""
        if default is None:
            return None
        if isinstance(default, str):
            if default.lower() in ('now()', 'current_timestamp'):
                return 'func.now()'
            if default.startswith("'") and default.endswith("'"):
                return default
        return str(default)
        
    def _determine_relationship_name(self, fk_cols: List[str], table_name: str, 
                                   ref_table: str, cardinality: str) -> str:
        """Determine relationship name"""
        base_name = fk_cols[0].replace('_id', '')
        if cardinality in ['one-to-many', 'many-to-many']:
            return p.plural(base_name)
        return base_name
        
    def _determine_remote_relationship_name(self, cardinality: str, table_name: str, 
                                          ref_table: str) -> str:
        """Determine remote relationship name"""
        if cardinality in ['one-to-many', 'many-to-many']:
            return p.plural(table_name)
        return table_name
        
    def _prepare_relationship_info(self, association_tables: List[str]) -> Dict:
        """Prepare relationship cardinality information"""
        info = {}
        for table_name in self.inspector.get_table_names():
            if table_name not in association_tables:
                info[table_name] = {}
                for fk in self.inspector.get_foreign_keys(table_name):
                    ref_table = fk['referred_table']
                    info[table_name][ref_table] = self._analyze_cardinality(table_name, fk, association_tables)
        return info
        
    def _analyze_cardinality(self, table_name: str, fk: Dict, association_tables: List[str]) -> str:
        """Analyze relationship cardinality"""
        ref_table = fk["referred_table"]
        if table_name in association_tables or ref_table in association_tables:
            return 'many-to-many'
        pk = self.inspector.get_pk_constraint(table_name)
        if set(fk["constrained_columns"]) == set(pk['constrained_columns']):
            return 'one-to-one'
        return 'many-to-one'
        
    def _find_association_table(self, table1: str, table2: str, association_tables: List[str]) -> Optional[str]:
        """Find association table between two tables"""
        for assoc_table in association_tables:
            fks = self.inspector.get_foreign_keys(assoc_table)
            if len(fks) == 2 and {fk['referred_table'] for fk in fks} == {table1, table2}:
                return assoc_table
        return None

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Generate Flask-AppBuilder SQLAlchemy models')
    parser.add_argument('--uri', type=str, required=True, help='Database URI')
    parser.add_argument('--output', type=str, default='generated_models.py', help='Output file name')
    args = parser.parse_args()
    
    try:
        generator = ModelGenerator()
        generator.initialize_db_connection(args.uri)
        
        model_code = generator.generate_models()
        
        with open(args.output, 'w') as f:
            f.write("\n".join(model_code))
            
        logger.info(f"Models generated successfully. Output written to {args.output}")
        
    except Exception as e:
        logger.error(f"Failed to generate models: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()