import argparse
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import yaml
from sqlalchemy import (
    create_engine,
    MetaData,
    inspect,
    Table,
    Column,
    ForeignKey,
    types,
)
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship
from jinja2 import Environment, FileSystemLoader
import black
import isort
from oheaders import VIEW_IMPORTS
from autoimport import fix_files
import pylint.lint
from flask_babel import lazy_gettext as _


def to_pascal_case(text: str) -> str:
 """
 Convert a string to PascalCase.

 Args:
     text (str): Input string (can be snake_case, kebab-case, or space separated)

 Returns:
     str: PascalCase string

 Examples:
     >>> to_pascal_case('hello_world')
     'HelloWorld'
     >>> to_pascal_case('api-endpoint')
     'ApiEndpoint'
     >>> to_pascal_case('first name')
     'FirstName'
 """
 if not text:
     return text

 # Replace special characters with spaces
 text = re.sub(r'[_-]', ' ', text)

 # Split into words, capitalize each word, and join
 return ''.join(word.capitalize() for word in text.split())



class ViewGenerator:
    def __init__(
        self, db_uri: str, output_dir: str, config_file: str, single_file: bool
    ):
        self.db_uri = db_uri
        # Should ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir

        # Load configuration with defaults
        self.config = self.load_config(config_file)

        try:
            self.engine = create_engine(db_uri)
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)
            self.inspector = inspect(self.engine)
        except Exception as e:
            print(f"Database connection error: {e}")
            sys.exit(1)

        self.Base = automap_base(metadata=self.metadata)
        self.Base.prepare()
        try:
            self.jinja_env = Environment(loader=FileSystemLoader("templates"))
        except Exception as e:
            print(f"Error loading templates: {e}")
            sys.exit(1)

        self.relationships = self.get_all_relationships()
        self.single_file = single_file
        self.all_views_code = ""  # For single file mode

    def load_config(self, config_file: str) -> Dict[str, Any]:
        # Initialize default configuration
        default_config = {
            'icon': 'fa-link',
            "default_layout": "tabs",
            'chart': {
                'type': 'PieChart',
                'height': 400,
                'width': 400,
                'orientation': 'horizontal',
                'enable_3d': True,
                'enable_export': True,
                'colors': ['#FF0000', '#00FF00', '#0000FF'],
                    },
            'wizard': {
                'form_template': 'wizard_form.html',
                'allow_previous': True,
                'show_progress': True,
                'progress_template': 'wizard_progress.html',
                'enable_file_upload': False,
                'upload_folder': 'uploads/',
                'allowed_extensions': ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'],
                'max_content_length': 16 * 1024 * 1024,
                'enable_optional_steps': False,
                'optional_steps': [],
                'enable_conditional_steps': False,
                'icon': 'fa-magic'
            },
            "caching": {
                "enabled": False,
                "type": "simple",
                "redis_url": "redis://localhost:6379/0"
            },
            "security": {
                "custom": False
            }
        }

        if config_file:
            try:
                with open(config_file, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        return self._deep_update(default_config, user_config)
            except (yaml.YAMLError, IOError) as e:
                print(f"Error loading config file: {e}")

        return default_config

    def get_all_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        relationships = {}
        for table_name in self.metadata.tables:
            relationships[table_name] = self.get_relationship_info(
                self.metadata.tables[table_name]
            )
        return relationships

    def get_relationship_info(self, table: Table) -> List[Dict[str, Any]]:
        relationships = []
        for fk in table.foreign_keys:
            if fk.column.table.name.startswith('ab_'):
                continue
            relationships.append(
                {
                    "constrained_column": fk.parent.name,
                    "referred_table": fk.column.table.name,
                    "referred_column": fk.column.name,
                    "view_class": f"{fk.column.table.name.capitalize()}ModelView",  # Ensure proper case
                    "relationship_type": "many_to_one"  # Add relationship type
                }
            )
        return relationships

    def _deep_update(self, d1: dict, d2: dict) -> dict:
        """Deep update of nested dictionaries."""
        result = d1.copy()
        for k, v in d2.items():
            if isinstance(v, dict) and k in result and isinstance(result[k], dict):
                result[k] = self._deep_update(result[k], v)
            else:
                result[k] = v
        return result

    def generate_imports(self):
        imports = VIEW_IMPORTS
        self.all_views_code += imports

    def generate_model_view(self, table: Table):
        template = self.jinja_env.get_template("model_view.py.j2")
        columns = self.get_column_info(table)
        fieldsets = self.group_fields_into_fieldsets(columns)
        # Use the same fieldsets for show view
        show_fieldsets = fieldsets.copy()
        # Generate description columns
        description_columns = {}
        for col in columns:
            col_name = col["name"]
            description_columns[col_name] = f"Description for {col_name}"

        # Generate label columns
        label_columns = {}
        for col in columns:
            col_name = col["name"]
            # Convert snake_case to Title Case
            label = col_name.replace('_', ' ').title()
            label_columns[col_name] = label

        fieldset_icons = {
            'Basic Information': 'fa-info-circle',
            'Contact Details': 'fa-address-book',
            'Location': 'fa-map-marker',
            'Dates & Times': 'fa-calendar',
            'Financial': 'fa-dollar-sign',
            'Status & Settings': 'fa-cogs',
            'Media': 'fa-images',
            'Notes & Description': 'fa-sticky-note',
            'Relationships': 'fa-link',
            'System Fields': 'fa-database',
            'Additional Information': 'fa-plus-circle'
        }

        relationships = self.relationships.get(table.name, [])

        list_columns = [col["name"] for col in columns if not col["primary_key"]][:10]

        form_fields = {}
        for col in columns:
            if not col["primary_key"]:
                widget, extra_validators = self.get_widget_for_column(col, table)
                validators = self.get_validators_for_column(col) + extra_validators
                form_fields[col["name"]] = {"widget": widget, "validators": validators}

        view_code = template.render(
                table_name=table.name,
                columns=columns,
                fieldsets=fieldsets,
                show_fieldsets=show_fieldsets,
                fieldset_icons=fieldset_icons,
                relationships=relationships,
                list_columns=list_columns,
                form_fields=form_fields,
                config=self.config,
                single_file=self.single_file,
                description_columns=description_columns,  # Add this
                label_columns=label_columns,  # Add this
                add_columns=list_columns,  # Add this
                edit_columns=list_columns,  # Add this
                show_columns=list_columns,  # Add this
            )

        if self.single_file:
            self.all_views_code += view_code + "\n\n"
        else:
            self.write_view_file(f"{table.name}_model_view.py", view_code)

    def generate_multiple_view(self, table: Table):
        template = self.jinja_env.get_template("multiple_view.py.j2")
        related_views = self.get_related_views(table)

        view_code = template.render(
            table_name=table.name,
            related_views=related_views,
            config=self.config,
            single_file=self.single_file,
        )

        if self.single_file:
            self.all_views_code += view_code + "\n\n"
        else:
            self.write_view_file(f"{table.name}_multiple_view.py", view_code)

    def generate_master_detail_views(self, table: Table):
        template = self.jinja_env.get_template("master_detail_view.py.j2")
        for relationship in self.relationships.get(table.name, []):
            detail_table = self.metadata.tables[relationship["referred_table"]]
            # Ensure we have a config dictionary with defaults
            view_config = {
                'icon': 'fa-link',
                # Add other default configurations here
            }
            if self.config:
                view_config.update(self.config)
            view_code = template.render(
                master_table=table,
                detail_table=detail_table,
                relationship=relationship,
                config=view_config,
                single_file=self.single_file,
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(
                    f"{table.name}_{detail_table.name}_master_detail_view.py", view_code
                )

    def generate_chart_view(self, table: Table):
        template = self.jinja_env.get_template("chart_view.py.j2")
        numeric_columns = [
            col for col in table.columns
            if isinstance(col.type, (types.Integer, types.Numeric))
        ]
        date_columns = [
            col for col in table.columns
            if isinstance(col.type, (types.Date, types.DateTime))
        ]

        # Skip if required columns are not present
        if not numeric_columns or not date_columns:
            print(f"Skipping chart view for {table.name}: Missing required numeric or date columns")
            return

        if numeric_columns and date_columns:
            # Ensure we have at least one date column and one numeric column
            default_date_column = date_columns[0]
            default_numeric_column = numeric_columns[0]
            view_config = {
                        'icon': 'fa-bar-chart',
                        'chart_type': 'PieChart',
                        'chart_height': 400,
                        'chart_width': 400,
                        # Add other default chart configurations
                    }

            # Merge with user config if it exists
            if self.config:
                view_config.update(self.config)

            view_code = template.render(
                table_name=table.name,
                numeric_columns=numeric_columns,
                date_columns=date_columns,
                default_date_column=default_date_column,
                default_numeric_column=default_numeric_column,
                config=self.config,
                single_file=self.single_file
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table.name.lower()}_chart_view.py", view_code)

    def generate_wizard_view(self, table: Table):
        template = self.jinja_env.get_template("wizard_view.py.j2")
        columns = self.get_column_info(table)
        if len(columns) > 8:
                # Create default wizard configuration
            wizard_config = {
                'form_template': 'wizard_form.html',
                'allow_previous': True,
                'show_progress': True,
                'progress_template': 'wizard_progress.html',
                'enable_file_upload': False,
                'upload_folder': 'uploads/',
                'allowed_extensions': ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'],
                'max_content_length': 16 * 1024 * 1024,
                'enable_optional_steps': False,
                'optional_steps': [],
                'enable_conditional_steps': False,
                'icon': 'fa-magic'
            }
            # Merge with user config if it exists
            if self.config and 'wizard' in self.config:
                wizard_config.update(self.config.get('wizard', {}))


            steps = self.create_wizard_steps(columns)
            view_code = template.render(
                table_name=table.name,
                columns=columns,
                steps=steps,
                config=self.config,
                single_file=self.single_file,
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table.name}_wizard_view.py", view_code)

    def generate_report_view(self, table: Table):
        template = self.jinja_env.get_template("report_view.py.j2")
        columns = self.get_column_info(table)

        view_code = template.render(
            table_name=table.name,
            columns=columns,
            config=self.config,
            single_file=self.single_file,
        )

        if self.single_file:
            self.all_views_code += view_code + "\n\n"
        else:
            self.write_view_file(f"{table.name}_report_view.py", view_code)

    def generate_calendar_view(self, table: Table):
        template = self.jinja_env.get_template("calendar_view.py.j2")
        date_columns = [
            col.name
            for col in table.columns
            if isinstance(col.type, (types.Date, types.DateTime))
        ]

        if date_columns:
            view_code = template.render(
                table_name=table.name,
                columns=self.get_column_info(table),
                date_columns=date_columns,
                config=self.config,
                single_file=self.single_file,
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table.name}_calendar_view.py", view_code)

    def get_column_info(self, table: Table) -> List[Dict[str, Any]]:
        columns = []
        for column in table.columns:
            column_info = {
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
            }
            columns.append(column_info)
        return columns

    def get_widget_for_column(
        self, column: Column, table: Table
    ) -> Tuple[str, List[str]]:
        column_type = column["type"]
        column_name = column["name"].lower()

        # Check for foreign key relationships
        for rel in self.relationships.get(table.name, []):
            if rel["constrained_column"] == column["name"]:
                return (
                    f"Select2AJAXWidget(endpoint='/api/{rel['referred_table'].lower()}/api/column/{rel['referred_column']}')",
                    [],
                )

        # Check for specific column names
        if "password" in column_name:
            return "BS3PasswordFieldWidget()", []
        elif "email" in column_name:
            return "BS3TextFieldWidget()", ["Email()"]
        elif "url" in column_name:
            return "BS3TextFieldWidget()", ["URL()"]
        elif "color" in column_name:
            return "ColorPickerWidget()", []

        # Check column types
        if isinstance(column_type, types.String):
            if column_type.length > 200:
                return "BS3TextAreaFieldWidget()", []
            return "BS3TextFieldWidget()", []
        elif isinstance(column_type, types.Text):
            return "BS3TextAreaFieldWidget()", []
        elif isinstance(column_type, types.Integer):
            return "BS3TextFieldWidget()", ["IntegerValidator()"]
        elif isinstance(column_type, types.Numeric):
            return "BS3TextFieldWidget()", ["NumberValidator()"]
        elif isinstance(column_type, types.Date):
            return "BS3DateFieldWidget()", []
        elif isinstance(column_type, types.DateTime):
            return "BS3DateTimeFieldWidget()", []
        elif isinstance(column_type, types.Time):
            return "TimePickerWidget()", []
        elif isinstance(column_type, types.Boolean):
            return "CheckboxWidget()", []
        elif isinstance(column_type, types.Enum):
            choices = [(choice, choice) for choice in column_type.enums]
            return f"Select2Widget(choices={choices})", []
        elif isinstance(column_type, types.ARRAY):
            return "Select2ManyWidget()", []
        elif isinstance(column_type, types.JSON):
            return "JSONField()", []
        elif isinstance(column_type, types.LargeBinary):
            return "BS3FileUploadFieldWidget()", []

        # Default to text field if no specific type is matched
        return "BS3TextFieldWidget()", []

    def get_validators_for_column(self, column: Column) -> List[str]:
        validators = []
        if not column["nullable"]:
            validators.append("DataRequired()")

        column_type = column["type"]
        if isinstance(column_type, types.String):
            validators.append(f"Length(max={column_type.length})")
        elif isinstance(column_type, (types.Integer, types.Numeric)):
            validators.append("NumberRange()")

        return validators

    def get_related_views(self, table: Table) -> List[str]:
        """Get list of related view class names with relationship types."""
        related_views = []
        for relationship in self.relationships.get(table.name, []):
            view_name = f"{relationship['referred_table'].capitalize()}ModelView"
            if view_name not in related_views:
                related_views.append(view_name)
        return related_views

    def create_wizard_steps(
        self, columns: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        steps = []
        current_step = []
        for column in columns:
            if not column["primary_key"]:
                current_step.append(column)
                if len(current_step) == 5:
                    steps.append(current_step)
                    current_step = []
        if current_step:
            steps.append(current_step)
        return steps

    def write_view_file(self, filename: str, content: str):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
        self.format_and_lint_file(filepath)

    def format_and_lint_file(self, filepath: str):
        # Format the file using black
        path = Path(filepath)
        print('PRINT',path)
        fix_files([filepath])
        isort.file(filepath)
        black.format_file_in_place(path, fast=False, mode=black.FileMode())

        # Lint the file using pylint
        pylint_opts = ["--disable=C0111", filepath]
        pylint.lint.Run(pylint_opts, exit=False)


    def generate_init_file(self):
        """Generate __init__.py file with proper view imports."""
        template = self.jinja_env.get_template("init_template.py.j2")

        # Use views_info from generate_views
        views_info = []
        for table in self.metadata.tables.values():
            if table.name.startswith('ab_'):
                continue
            relationships = self.get_relationship_info(table)
            view_info = {
                'name': table.name,
                'has_model_view': True,  # Always generate model view
                'has_multiple_view': True,  # Always generate multiple view
                'has_chart_view': self.has_chart_columns(table),
                'has_wizard_view': len(self.get_column_info(table)) > 8,
                'has_calendar_view': self.has_date_columns(table),
                'has_report_view': True,  # Always generate report view
                'has_api_view': True,  # Always generate API view
                'capitalize_name': table.name.capitalize(),
                'relationships': relationships,
                'related_views': self.get_related_views(table)
            }
            views_info.append(view_info)
        # print('###',views_info)
        content = template.render(
            config=self.config,
            single_file=self.single_file,
            views_info=views_info,
            blueprint_name=self.config.get('blueprint_name', 'views')
        )

        self.write_view_file("__init__.py", content)

    def generate_main_app_file(self):
        template = self.jinja_env.get_template("main_app.py.j2")
        if self.single_file:
            views = ["views"]
            table_names = [table.name for table in self.metadata.tables.values()]
        else:
            views = [
                f[:-3] for f in os.listdir(self.output_dir) if f.endswith("_view.py")
            ]
            table_names = []

        content = template.render(
            views=views,
            table_names=table_names,
            config=self.config,
            single_file=self.single_file,
        )
        self.write_view_file("app.py", content)

    def generate_caching(self):
        """Generate caching configuration."""
        cache_config = self.config.get('caching', {})
        if cache_config.get('enabled', False):
            cache_type = cache_config.get('type', 'simple')
            if cache_type == 'redis':
                cache_code = f"""
    from flask_caching import Cache

    cache = Cache(app, config={{
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': '{cache_config.get('redis_url', 'redis://localhost:6379/0')}'
    }})
    """
            else:
                cache_code = """
    from flask_caching import Cache

    cache = Cache(app, config={'CACHE_TYPE': 'simple'})
    """

            if self.single_file:
                self.all_views_code += cache_code + "\n\n"
            else:
                self.write_view_file('cache_config.py', cache_code)

    def generate_security_manager(self):
        security_config = self.config.get("security", {})
        if security_config.get("custom", False):
            security_code = """
from flask_appbuilder.security.manager import SecurityManager
from flask_appbuilder.security.views import UserDBModelView
from flask_appbuilder.security.views import RoleModelView
from flask_appbuilder.security.registerviews import RegisterUserDBView

class MySecurityManager(SecurityManager):
    userdbmodelview = UserDBModelView
    rolemodelview = RoleModelView
    registeruserdbview = RegisterUserDBView

appbuilder.security_manager_class = MySecurityManager
"""
            if self.single_file:
                self.all_views_code += security_code + "\n\n"
            else:
                self.write_view_file("security_manager.py", security_code)

    def generate_api_views(self):
        template = self.jinja_env.get_template("api_view.py.j2")
        for table_name in self.metadata.tables:
            if table_name.startswith('ab_'):
                continue
            table = self.metadata.tables[table_name]
            columns = self.get_column_info(table)

            view_code = template.render(
                table_name=table.name,
                columns=columns,
                config=self.config,
                single_file=self.single_file,
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table.name}_api.py", view_code)

    def copy_templates(self, views_dir: str):
        """
        Copy template files to the templates directory in the blueprint.

        Args:
            views_dir: Path to the views directory
        """
        if not views_dir.endswith('/views'):
                raise ValueError("The provided views_dir must end with '/views'.")
        # Get the blueprint directory (parent of views directory)
        blueprint_dir = os.path.dirname(views_dir)

        # Create or use templates directory parallel to views
        templates_dir = views_dir.replace('/views', '/templates')
        os.makedirs(templates_dir, exist_ok=True)

        # Get the source templates directory from our package
        src_templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

        try:
            if not os.path.exists(src_templates_dir):
                        print(f"Source directory '{src_templates_dir}' does not exist.")
                        return
            # Copy each template
            for item in os.listdir(src_templates_dir):
                source_item = os.path.join(src_templates_dir, item)
                destination_item = os.path.join(templates_dir, item)

                if os.path.isdir(source_item):
                    shutil.copytree(source_item, destination_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(source_item, destination_item)
                    print(f"Templates successfully copied from '{src_templates_dir}' to '{templates_dir}'.")
        except Exception as e:
            print(f"Error copying templates: {str(e)}")
            raise

        print(f"Templates copied successfully to: {templates_dir}")


    def group_fields_into_fieldsets(self, columns):
        """Group fields into logical fieldsets based on naming patterns and types"""
        fieldsets = {
            'Basic Information': [],
            'Contact Details': [],
            'Location': [],
            'Dates & Times': [],
            'Financial': [],
            'Status & Settings': [],
            'Relationships': [],
            'Media': [],
            'Notes & Description': [],
            'System Fields': [],
            'Additional Information': []
        }

        for column in columns:
            name = column['name'].lower()

            # Skip primary keys and system fields
            if column['primary_key'] or name in ['created_at', 'updated_at', 'created_by', 'updated_by']:
                fieldsets['System Fields'].append(column['name'])
                continue

            # Contact details
            if any(word in name for word in ['email', 'phone', 'contact', 'mobile', 'fax']):
                fieldsets['Contact Details'].append(column['name'])

            # Location fields
            elif any(word in name for word in ['address', 'city', 'state', 'country', 'postal', 'zip']):
                fieldsets['Location'].append(column['name'])

            # Date and time fields
            elif any(word in name for word in ['date', 'time', 'schedule', 'deadline']):
                fieldsets['Dates & Times'].append(column['name'])

            # Financial fields
            elif any(word in name for word in ['amount', 'price', 'cost', 'fee', 'payment', 'balance']):
                fieldsets['Financial'].append(column['name'])

            # Status fields
            elif any(word in name for word in ['status', 'active', 'enabled', 'flag', 'type']):
                fieldsets['Status & Settings'].append(column['name'])

            # Media fields
            elif any(word in name for word in ['photo', 'image', 'file', 'document', 'attachment']):
                fieldsets['Media'].append(column['name'])

            # Description fields
            elif any(word in name for word in ['note', 'description', 'comment', 'detail']):
                fieldsets['Notes & Description'].append(column['name'])

            # Basic information (name, title, code etc)
            elif any(word in name for word in ['name', 'title', 'code', 'id', 'key', 'ref']):
                fieldsets['Basic Information'].append(column['name'])

            # Foreign key relationships
            elif name.endswith('_id'):
                fieldsets['Relationships'].append(column['name'])

            # Everything else
            else:
                fieldsets['Additional Information'].append(column['name'])

        # Remove empty fieldsets
        return {k: v for k, v in fieldsets.items() if v}

    def generate_views(self):
        views_info = []

        if self.single_file:
            self.generate_imports()

        # Copy templates first
        self.copy_templates(self.output_dir)

        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            if table_name.startswith('ab_'):
                continue
            relationships = self.get_relationship_info(table)
            view_info = {
                'name': table_name,
                'capitalize_name': table_name.capitalize(),
                'has_model_view': True,
                'has_multiple_view': True,
                'has_chart_view': self.has_chart_columns(table),
                'has_wizard_view': len(self.get_column_info(table)) > 8,
                'has_calendar_view': self.has_date_columns(table),
                'has_report_view': True,
                'has_api_view': True,
                'relationships': self.get_relationship_info(table),  # Include relationships
                'related_views': self.get_related_views(table)  # Add related views
            }
            views_info.append(view_info)
            self.generate_model_view(table)
            self.generate_multiple_view(table)
            self.generate_master_detail_views(table)

            # Only generate specialized views if table meets requirements
            if self.has_chart_columns(table):
                self.generate_chart_view(table)
            if len(self.get_column_info(table)) > 8:
                self.generate_wizard_view(table)

            self.generate_report_view(table)
            if self.has_date_columns(table):
                self.generate_calendar_view(table)


        self.generate_caching()
        self.generate_security_manager()
        self.generate_api_views()
        self.generate_init_file()

        if self.single_file:
            self.write_view_file("views.py", self.all_views_code)

        self.generate_main_app_file()


    def has_chart_columns(self, table: Table) -> bool:
        """Check if table has required columns for chart view."""
        numeric_columns = [col for col in table.columns
                            if isinstance(col.type, (types.Integer, types.Numeric))]
        date_columns = [col for col in table.columns
                        if isinstance(col.type, (types.Date, types.DateTime))]
        return bool(numeric_columns and date_columns)

    def has_date_columns(self, table: Table) -> bool:
        """Check if table has date columns for calendar view."""
        return any(isinstance(col.type, (types.Date, types.DateTime))
                    for col in table.columns)

def main():
    parser = argparse.ArgumentParser(
        description="Generate Flask-AppBuilder views from a PostgreSQL database"
    )
    parser.add_argument("--uri", required=True, help="PostgreSQL database URI")
    parser.add_argument(
        "--output-dir", required=True, help="Output directory for generated views"
    )
    parser.add_argument("--config", required=False, help="Configuration file path")
    parser.add_argument(
        "--single-file", action="store_true", help="Generate all views in a single file"
    )
    args = parser.parse_args()

    # Ensure the output directory is an absolute path
    output_dir = os.path.abspath(args.output_dir)
    generator = ViewGenerator(args.uri, args.output_dir, args.config, args.single_file)
    generator.generate_views()


if __name__ == "__main__":
    main()
