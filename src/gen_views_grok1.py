"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024-2025
License: MIT

gen_views.py: Flask-AppBuilder View Generator

Generates Flask-AppBuilder view classes using a class-based structure for each view type.
Supports ModelView, MasterDetailView, and MultipleView with easy extension for new view types.
"""

import argparse
import logging
from typing import List, Dict, Set, Any, Optional
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

class BaseViewGenerator:
    """Base class for view generators"""
    
    def __init__(self, table_name: str, inspector: Any, relationships: Dict[str, Dict[str, str]]):
        self.table_name = table_name
        self.inspector = inspector
        self.relationships = relationships
        self.model_name = self._snake_to_pascal(table_name)
        
    def generate(self) -> List[str]:
        """Abstract method to generate view code"""
        raise NotImplementedError("Subclasses must implement generate()")
        
    def _snake_to_pascal(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))
        
    def _format_list(self, items: List[str]) -> str:
        """Format a list for Python code"""
        return "[" + ", ".join(f"'{item}'" if not item.endswith('View') else item for item in items) + "]"

class GenModelView(BaseViewGenerator):
    """Generator for ModelView classes"""
    
    def generate(self) -> List[str]:
        class_name = f"{self.model_name}View"
        columns = self.inspector.get_columns(self.table_name)
        
        # Determine display columns
        show_cols = [col['name'] for col in columns if col['name'] not in ['created', 'modified']]
        list_cols = show_cols[:5]  # Limit to 5 columns for list view
        
        return [
            f"class {class_name}(ModelView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}label_columns = {{'id': 'ID'}}",
            f"{INDENT}show_columns = {self._format_list(show_cols)}",
            f"{INDENT}list_columns = {self._format_list(list_cols)}",
            f"{INDENT}description_columns = {{}}",
            ""
        ]

class GenMasterDetailView(BaseViewGenerator):
    """Generator for MasterDetailView classes"""
    
    def __init__(self, table_name: str, fk: Dict, inspector: Any, relationships: Dict[str, Dict[str, str]]):
        super().__init__(table_name, inspector, relationships)
        self.fk = fk
        
    def generate(self) -> List[str]:
        master_table = self.fk['referred_table']
        detail_table = self.table_name
        
        master_class = self._snake_to_pascal(master_table)
        detail_class = self._snake_to_pascal(detail_table)
        
        rel_name = self._determine_relationship_name(self.fk['constrained_columns'])
        cardinality = self.relationships[self.table_name].get(master_table, 'many-to-one')
        
        if cardinality in ['many-to-one', 'one-to-one']:
            view_name = f"{detail_class}MasterDetailView"
            master_field = rel_name
            base_class = detail_class
        else:  # one-to-many or many-to-many
            view_name = f"{master_class}MasterDetailView"
            master_field = p.plural(detail_table.lower())
            base_class = master_class
            
        return [
            f"class {view_name}(MasterDetailView):",
            f"{INDENT}datamodel = SQLAInterface({base_class})",
            f"{INDENT}related_views = [{self._snake_to_pascal(detail_table if cardinality in ['many-to-one', 'one-to-one'] else master_table)}View]",
            f"{INDENT}master_field = '{master_field}'",
            ""
        ]
        
    def _determine_relationship_name(self, fk_cols: List[str]) -> str:
        """Determine relationship name"""
        return fk_cols[0].replace('_id', '')

class GenMultipleView(BaseViewGenerator):
    """Generator for MultipleView classes"""
    
    def __init__(self, table_name: str, fks: List[Dict], inspector: Any, relationships: Dict[str, Dict[str, str]]):
        super().__init__(table_name, inspector, relationships)
        self.fks = fks
        
    def generate(self) -> List[str]:
        class_name = f"{self.model_name}MultipleView"
        related_views = [f"{self._snake_to_pascal(fk['referred_table'])}View" for fk in self.fks]
        
        return [
            f"class {class_name}(MultipleView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}related_views = {self._format_list(related_views)}",
            ""
        ]

class ViewGenerator:
    """Main class for orchestrating view generation"""
    
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
            relationships = self._analyze_relationships()
            
            for table_name in self.inspector.get_table_names():
                fks = self.inspector.get_foreign_keys(table_name)
                
                # ModelView
                model_view_gen = GenModelView(table_name, self.inspector, relationships)
                view_code.extend(model_view_gen.generate())
                self.models.add(model_view_gen.model_name)
                
                # MasterDetailViews
                for fk in fks:
                    master_detail_gen = GenMasterDetailView(table_name, fk, self.inspector, relationships)
                    view_code.extend(master_detail_gen.generate())
                    self.models.add(self._snake_to_pascal(fk['referred_table']))
                    
                # MultipleView
                if len(fks) > 1:
                    multiple_view_gen = GenMultipleView(table_name, fks, self.inspector, relationships)
                    view_code.extend(multiple_view_gen.generate())
                    
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
        
    def _snake_to_pascal(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))

def generate_app_registration(view_code: List[str], models: Set[str]) -> List[str]:
    """Generate code to register views with the Flask-AppBuilder app"""
    registration_code = [
        "\n# View Registration",
        "def register_views(appbuilder):",
        f"{INDENT}\"\"\"Register all views with the Flask-AppBuilder application\"\"\""
    ]
    
    for model in models:
        registration_code.extend([
            f"{INDENT}appbuilder.add_view({model}View, '{model}', category='{model}')",
            f"{INDENT}appbuilder.add_view({model}MasterDetailView, '{model} Detail', category='{model}')"
        ])
        # Check if table has multiple FKs (simplified check)
        temp_inspector = inspect(create_engine('sqlite://'))
        if any(len(temp_inspector.get_foreign_keys(m.lower())) > 1 for m in [model.lower()]):
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