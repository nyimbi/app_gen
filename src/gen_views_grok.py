"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024-2025
License: MIT

gen_views.py: Flask-AppBuilder View Generator

Generates Flask-AppBuilder view classes based on database schema introspection.
Creates ModelViews for all tables, MasterDetailViews for relationships, and
MultipleViews for tables with multiple foreign keys.
"""

import argparse
import logging
from typing import List, Dict, Set, Any
import sys

from sqlalchemy import create_engine, inspect, MetaData
import inflect

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INDENT = "    "
p = inflect.engine()

class ViewGenerator:
    """Class for generating Flask-AppBuilder view definitions"""
    
    def __init__(self):
        self.metadata = MetaData()
        self.engine = None
        self.inspector = None
        self.models: Set[str] = set()
        
    def initialize_db_connection(self, uri: str) -> None:
        """Initialize database connection and inspection"""
        try:
            self.engine = create_engine(uri)
            self.inspector = inspect(self.engine)
            self.metadata.reflect(bind=self.engine)
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise
            
    def generate_views(self) -> List[str]:
        """Generate complete view code"""
        try:
            if not self.inspector or not self.metadata:
                raise ValueError("Database connection not initialized")
                
            view_code = self._generate_preamble()
            table_relationships = self._analyze_relationships()
            
            # Generate views for each table
            for table_name in self.inspector.get_table_names():
                fks = self.inspector.get_foreign_keys(table_name)
                columns = self.inspector.get_columns(table_name)
                
                # Generate ModelView
                model_view = self._generate_model_view(table_name, columns)
                view_code.extend(model_view)
                
                # Generate MasterDetailView for each relationship
                for fk in fks:
                    master_detail = self._generate_master_detail_view(
                        table_name, fk, table_relationships
                    )
                    view_code.extend(master_detail)
                
                # Generate MultipleView for tables with multiple FKs
                if len(fks) > 1:
                    multiple_view = self._generate_multiple_view(table_name, fks)
                    view_code.extend(multiple_view)
                    
            return view_code
            
        except Exception as e:
            logger.error(f"Error generating views: {str(e)}")
            raise
            
    def _generate_preamble(self) -> List[str]:
        """Generate file header and imports"""
        return [
            "from flask_appbuilder import ModelView, MasterDetailView, MultipleView",
            "from flask_appbuilder.models.sqla.interface import SQLAInterface",
            "from .models import *  # Import all models from generated models file",
            "\n# Flask-AppBuilder Views",
            "\n"
        ]
        
    def _analyze_relationships(self) -> Dict[str, Dict[str, str]]:
        """Analyze table relationships and their cardinality"""
        relationships = {}
        for table_name in self.inspector.get_table_names():
            relationships[table_name] = {}
            fks = self.inspector.get_foreign_keys(table_name)
            for fk in fks:
                ref_table = fk['referred_table']
                cardinality = self._determine_cardinality(table_name, fk)
                relationships[table_name][ref_table] = cardinality
        return relationships
        
    def _generate_model_view(self, table_name: str, columns: List[Dict]) -> List[str]:
        """Generate a basic ModelView for a table"""
        class_name = self._snake_to_pascal(table_name) + "View"
        model_name = self._snake_to_pascal(table_name)
        self.models.add(model_name)
        
        # Determine display columns
        show_cols = [col['name'] for col in columns if col['name'] not in ['created', 'modified']]
        list_cols = show_cols[:5]  # Limit to 5 columns for list view
        
        view_code = [
            f"class {class_name}(ModelView):",
            f"{INDENT}datamodel = SQLAInterface({model_name})",
            f"{INDENT}label_columns = {{'id': 'ID'}}",
            f"{INDENT}show_columns = {self._format_list(show_cols)}",
            f"{INDENT}list_columns = {self._format_list(list_cols)}",
            f"{INDENT}description_columns = {{}}",
            ""
        ]
        
        return view_code
        
    def _generate_master_detail_view(self, table_name: str, fk: Dict, 
                                  relationships: Dict[str, Dict[str, str]]) -> List[str]:
        """Generate a MasterDetailView for a relationship"""
        master_table = fk['referred_table']
        detail_table = table_name
        
        master_class = self._snake_to_pascal(master_table)
        detail_class = self._snake_to_pascal(detail_table)
        self.models.add(master_class)
        self.models.add(detail_class)
        
        rel_name = self._determine_relationship_name(fk['constrained_columns'], detail_table, master_table)
        cardinality = relationships[table_name].get(master_table, 'many-to-one')
        
        if cardinality in ['many-to-one', 'one-to-one']:
            view_name = f"{detail_class}MasterDetailView"
            master_field = rel_name
        else:  # one-to-many or many-to-many
            view_name = f"{master_class}MasterDetailView"
            master_field = p.plural(detail_table.lower())
            
        view_code = [
            f"class {view_name}(MasterDetailView):",
            f"{INDENT}datamodel = SQLAInterface({master_class})",
            f"{INDENT}related_views = [{detail_class}View]",
            f"{INDENT}master_field = '{master_field}'",
            ""
        ]
        
        return view_code
        
    def _generate_multiple_view(self, table_name: str, fks: List[Dict]) -> List[str]:
        """Generate a MultipleView for tables with multiple foreign keys"""
        class_name = self._snake_to_pascal(table_name) + "MultipleView"
        model_name = self._snake_to_pascal(table_name)
        self.models.add(model_name)
        
        related_views = []
        for fk in fks:
            ref_table = fk['referred_table']
            related_views.append(f"{self._snake_to_pascal(ref_table)}View")
            
        view_code = [
            f"class {class_name}(MultipleView):",
            f"{INDENT}datamodel = SQLAInterface({model_name})",
            f"{INDENT}related_views = {self._format_list(related_views)}",
            ""
        ]
        
        return view_code
        
    def _snake_to_pascal(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))
        
    def _format_list(self, items: List[str]) -> str:
        """Format a list for Python code"""
        return "[" + ", ".join(f"'{item}'" if not item.endswith('View') else item for item in items) + "]"
        
    def _determine_cardinality(self, table_name: str, fk: Dict) -> str:
        """Determine relationship cardinality"""
        pk = self.inspector.get_pk_constraint(table_name)
        constrained_cols = set(fk['constrained_columns'])
        pk_cols = set(pk['constrained_columns'])
        
        fks = self.inspector.get_foreign_keys(table_name)
        is_assoc_table = len(fks) >= 2 and all(fk['constrained_columns'] for fk in fks)
        
        if is_assoc_table:
            return 'many-to-many'
        if constrained_cols == pk_cols:
            return 'one-to-one'
        return 'many-to-one'
        
    def _determine_relationship_name(self, fk_cols: List[str], table_name: str, 
                                   ref_table: str) -> str:
        """Determine relationship name"""
        base_name = fk_cols[0].replace('_id', '')
        return base_name

def generate_app_registration(view_code: List[str], models: Set[str]) -> List[str]:
    """Generate code to register views with the Flask-AppBuilder app"""
    registration_code = [
        "\n# View Registration",
        "def register_views(appbuilder):",
        f"{INDENT}\"\"\"Register all views with the Flask-AppBuilder application\"\"\""
    ]
    
    for model in models:
        registration_code.append(
            f"{INDENT}appbuilder.add_view({model}View, '{model}', category='{model}')"
        )
        registration_code.append(
            f"{INDENT}appbuilder.add_view({model}MasterDetailView, '{model} Detail', category='{model}')"
        )
        if any(len(v.get_foreign_keys(m.lower())) > 1 for v in [inspect(create_engine('sqlite://'))] for m in [model]):
            registration_code.append(
                f"{INDENT}appbuilder.add_view({model}MultipleView, '{model} Multiple', category='{model}')"
            )
            
    return registration_code

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Generate Flask-AppBuilder views')
    parser.add_argument('--uri', type=str, required=True, help='Database URI')
    parser.add_argument('--output', type=str, default='generated_views.py', help='Output file name')
    args = parser.parse_args()
    
    try:
        generator = ViewGenerator()
        generator.initialize_db_connection(args.uri)
        
        view_code = generator.generate_views()
        view_code.extend(generate_app_registration(view_code, generator.models))
        
        with open(args.output, 'w') as f:
            f.write("\n".join(view_code))
            
        logger.info(f"Views generated successfully. Output written to {args.output}")
        
    except Exception as e:
        logger.error(f"Failed to generate views: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()