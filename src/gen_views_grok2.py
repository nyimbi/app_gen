"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024-2025
License: MIT

gen_views.py: Flask-AppBuilder View Generator with REST and GraphQL

Generates Flask-AppBuilder view classes with general utility for ERP systems.
Includes REST and GraphQL endpoints, custom WizardView with tabbed navigation,
and extended features like offline support, chat, and logging.
"""

import argparse
import logging
from typing import List, Dict, Set, Any, Optional
import sys
from datetime import datetime

from sqlalchemy import create_engine, inspect, MetaData
import inflect

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
INDENT = "    "
p = inflect.engine()
VERSION = "1.0.0"


class BaseViewGenerator:
    """Base class for view generators with extended ERP features"""

    def __init__(
        self, table_name: str, inspector: Any, relationships: Dict[str, Dict[str, str]]
    ):
        self.table_name = table_name
        self.inspector = inspector
        self.relationships = relationships
        self.model_name = self._snake_to_pascal(table_name)

    def generate(self) -> List[str]:
        """Abstract method to generate view code"""
        raise NotImplementedError("Subclasses must implement generate()")

    def _add_common_features(self, code: List[str], class_name: str) -> List[str]:
        """Add extended features to view classes"""
        code.extend(
            [
                f"{INDENT}# Extended ERP Features",
                f"{INDENT}offline_support = True  # Enable offline field caching",
                f"{INDENT}active_users = []  # Track users on this page",
                "",
                f"{INDENT}def pre_render(self):",
                f'{INDENT}{INDENT}"""Log access and update active users"""',
                f"{INDENT}{INDENT}self.active_users.append(self.current_user.username)",
                f"{INDENT}{INDENT}self.logger.info(f'{{self.current_user.username}} accessed {class_name}')",
                "",
                f"{INDENT}def post_render(self):",
                f'{INDENT}{INDENT}"""Remove user from active list on exit"""',
                f"{INDENT}{INDENT}if self.current_user.username in self.active_users:",
                f"{INDENT}{INDENT}{INDENT}self.active_users.remove(self.current_user.username)",
                "",
                f"{INDENT}def render_chatbot_button(self):",
                f'{INDENT}{INDENT}"""Render chatbot/help button"""',
                f"{INDENT}{INDENT}return '<button onclick=\"openChatbot()\">Chat/Help</button>'",
                "",
                f"{INDENT}def get_footer(self):",
                f'{INDENT}{INDENT}"""Add version, time on page, and user info to footer"""',
                f"{INDENT}{INDENT}time_on_page = \"<span id='time-on-page'>0s</span>\"",
                f"{INDENT}{INDENT}return f'Version: {VERSION} | User: {{self.current_user.username}} | Time: {{time_on_page}}'",
                "",
                f"{INDENT}allow_import = True",
                f"{INDENT}allow_export = True",
                f"{INDENT}def switch_to_compact(self):",
                f"{INDENT}{INDENT}return self._get_view_instance(CompactView)",
                "",
            ]
        )
        return code

    def _snake_to_pascal(self, name: str) -> str:
        return "".join(word.capitalize() for word in name.split("_"))

    def _format_list(self, items: List[str]) -> str:
        return (
            "["
            + ", ".join(
                f"'{item}'" if not item.endswith("View") else item for item in items
            )
            + "]"
        )


class GenModelView(BaseViewGenerator):
    """Generator for ModelView classes"""

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}View"
        columns = self.inspector.get_columns(self.table_name)
        show_cols = [
            col["name"] for col in columns if col["name"] not in ["created", "modified"]
        ]
        list_cols = show_cols[:5]

        code = [
            f"class {class_name}(ModelView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}label_columns = {{'id': 'ID'}}",
            f"{INDENT}show_columns = {self._format_list(show_cols)}",
            f"{INDENT}list_columns = {self._format_list(list_cols)}",
            f"{INDENT}description_columns = {{}}",
        ]
        return self._add_common_features(code, class_name)


class GenMasterDetailView(BaseViewGenerator):
    """Generator for MasterDetailView classes"""

    def __init__(
        self,
        table_name: str,
        fk: Dict,
        inspector: Any,
        relationships: Dict[str, Dict[str, str]],
    ):
        super().__init__(table_name, inspector, relationships)
        self.fk = fk

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}MasterDetailView"
        master_table = self.fk["referred_table"]
        detail_table = self.table_name
        master_class = self._snake_to_pascal(master_table)
        detail_class = self._snake_to_pascal(detail_table)
        rel_name = self._determine_relationship_name(self.fk["constrained_columns"])
        cardinality = self.relationships[self.table_name].get(
            master_table, "many-to-one"
        )

        if cardinality in ["many-to-one", "one-to-one"]:
            master_field = rel_name
            base_class = detail_class
        else:
            master_field = p.plural(detail_table.lower())
            base_class = master_class

        code = [
            f"class {class_name}(MasterDetailView):",
            f"{INDENT}datamodel = SQLAInterface({base_class})",
            f"{INDENT}related_views = [{self._snake_to_pascal(detail_table if cardinality in ['many-to-one', 'one-to-one'] else master_table)}View]",
            f"{INDENT}master_field = '{master_field}'",
        ]
        return self._add_common_features(code, class_name)

    def _determine_relationship_name(self, fk_cols: List[str]) -> str:
        return fk_cols[0].replace("_id", "")


class GenMultipleView(BaseViewGenerator):
    """Generator for MultipleView classes"""

    def __init__(
        self,
        table_name: str,
        fks: List[Dict],
        inspector: Any,
        relationships: Dict[str, Dict[str, str]],
    ):
        super().__init__(table_name, inspector, relationships)
        self.fks = fks

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}MultipleView"
        related_views = [
            f"{self._snake_to_pascal(fk['referred_table'])}View" for fk in self.fks
        ]

        code = [
            f"class {class_name}(MultipleView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}related_views = {self._format_list(related_views)}",
        ]
        return self._add_common_features(code, class_name)


class GenCalendarView(BaseViewGenerator):
    """Generator for CalendarView classes"""

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}CalendarView"
        date_col = next(
            (
                col["name"]
                for col in self.inspector.get_columns(self.table_name)
                if "date" in col["name"].lower()
            ),
            "created",
        )

        code = [
            f"class {class_name}(CalendarView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}event_field = '{date_col}'",
            f"{INDENT}title_field = 'name' if 'name' in {self._format_list([c['name'] for c in self.inspector.get_columns(self.table_name)])} else 'id'",
        ]
        return self._add_common_features(code, class_name)


class GenChartView(BaseViewGenerator):
    """Generator for ChartView classes"""

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}ChartView"
        numeric_col = next(
            (
                col["name"]
                for col in self.inspector.get_columns(self.table_name)
                if "int" in str(col["type"]).lower()
                or "numeric" in str(col["type"]).lower()
            ),
            "id",
        )

        code = [
            f"class {class_name}(ChartView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}chart_title = '{self.model_name} Chart'",
            f"{INDENT}label_columns = {{'{numeric_col}': 'Value'}}",
            f"{INDENT}chart_type = 'BarChart'",
            f"{INDENT}group_by_columns = ['id']",
            f"{INDENT}value_columns = ['{numeric_col}']",
        ]
        return self._add_common_features(code, class_name)


class GenWizardView(BaseViewGenerator):
    """Generator for custom WizardView classes with tabbed navigation"""

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}WizardView"
        columns = self.inspector.get_columns(self.table_name)
        col_names = [col["name"] for col in columns]

        if len(col_names) > 7:
            # Tabbed wizard with 4 columns per tab
            tabs = [col_names[i : i + 4] for i in range(0, len(col_names), 4)]
            code = [
                f"class {class_name}(ModelView):",
                f"{INDENT}datamodel = SQLAInterface({self.model_name})",
                f"{INDENT}is_wizard = True",
                f"{INDENT}tabbed_steps = [",
            ]
            for i, tab_cols in enumerate(tabs, 1):
                code.append(
                    f"{INDENT}{INDENT}{{ 'title': 'Step {i}', 'columns': {self._format_list(tab_cols)} }},"
                )
            code.extend(
                [
                    f"{INDENT}]",
                    "",
                    f"{INDENT}def render_wizard(self):",
                    f'{INDENT}{INDENT}"""Render tabbed wizard with navigation"""',
                    f"{INDENT}{INDENT}html = '<div class=\"wizard-tabs\">'",
                    f"{INDENT}{INDENT}for i, step in enumerate(self.tabbed_steps, 1):",
                    f'{INDENT}{INDENT}{INDENT}html += f\'<div class="tab" id="tab{{i}}">{{self.render_tab(step)}}</div>\'',
                    f"{INDENT}{INDENT}html += f'<button onclick=\"prevTab()\">Back</button>'",
                    f"{INDENT}{INDENT}html += f'<button onclick=\"nextTab()\">Next</button>'",
                    f"{INDENT}{INDENT}html += '</div>'",
                    f"{INDENT}{INDENT}return html",
                    "",
                    f"{INDENT}def render_tab(self, step):",
                    f'{INDENT}{INDENT}"""Render individual tab content"""',
                    f"{INDENT}{INDENT}form = self._get_form(step['columns'])",
                    f"{INDENT}{INDENT}return f'<h3>{{step[\"title\"]}}</h3>{{form}}'",
                ]
            )
        else:
            # Simple form for fewer columns
            code = [
                f"class {class_name}(ModelView):",
                f"{INDENT}datamodel = SQLAInterface({self.model_name})",
                f"{INDENT}form_columns = {self._format_list(col_names)}",
            ]

        return self._add_common_features(code, class_name)


class GenReportView(BaseViewGenerator):
    """Generator for ReportView classes"""

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}ReportView"
        report_cols = [
            col["name"] for col in self.inspector.get_columns(self.table_name)
        ][:5]

        code = [
            f"class {class_name}(ReportView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}report_columns = {self._format_list(report_cols)}",
            f"{INDENT}report_title = '{self.model_name} Report'",
        ]
        return self._add_common_features(code, class_name)


class GenTreeView(BaseViewGenerator):
    """Generator for TreeView classes (hierarchical data)"""

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}TreeView"
        parent_col = next(
            (
                col["name"]
                for col in self.inspector.get_columns(self.table_name)
                if "parent" in col["name"].lower()
            ),
            "id",
        )

        code = [
            f"class {class_name}(TreeView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}parent_field = '{parent_col}'",
            f"{INDENT}label_field = 'name' if 'name' in {self._format_list([c['name'] for c in self.inspector.get_columns(self.table_name)])} else 'id'",
        ]
        return self._add_common_features(code, class_name)


class GenKanbanView(BaseViewGenerator):
    """Generator for KanbanView classes (workflow visualization)"""

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}KanbanView"
        status_col = next(
            (
                col["name"]
                for col in self.inspector.get_columns(self.table_name)
                if "status" in col["name"].lower()
            ),
            "id",
        )

        code = [
            f"class {class_name}(KanbanView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}status_field = '{status_col}'",
            f"{INDENT}title_field = 'name' if 'name' in {self._format_list([c['name'] for c in self.inspector.get_columns(self.table_name)])} else 'id'",
        ]
        return self._add_common_features(code, class_name)


class GenDashboardView(BaseViewGenerator):
    """Generator for DashboardView classes (overview with widgets)"""

    def generate(self) -> List[str]:
        class_name = f"{self.model_name}DashboardView"
        numeric_cols = [
            col["name"]
            for col in self.inspector.get_columns(self.table_name)
            if "int" in str(col["type"]).lower()
            or "numeric" in str(col["type"]).lower()
        ][:2]

        code = [
            f"class {class_name}(DashboardView):",
            f"{INDENT}datamodel = SQLAInterface({self.model_name})",
            f"{INDENT}widgets = {{",
            f"{INDENT}{INDENT}'count': 'CountWidget',",
            f"{INDENT}{INDENT}'numeric': {{'fields': {self._format_list(numeric_cols)}, 'type': 'SumWidget'}}",
            f"{INDENT}}}",
        ]
        return self._add_common_features(code, class_name)


class ViewGenerator:
    """Main class for orchestrating view generation with REST and GraphQL"""

    def __init__(self):
        self.metadata = MetaData()
        self.engine = None
        self.inspector = None
        self.models: Set[str] = set()

    def initialize_db_connection(self, uri: str) -> None:
        try:
            self.engine = create_engine(uri)
            self.inspector = inspect(self.engine)
            self.metadata.reflect(bind=self.engine)
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise

    def generate_views(self) -> List[str]:
        try:
            if not self.inspector or not self.metadata:
                raise ValueError("Database connection not initialized")

            view_code = self._generate_preamble()
            relationships = self._analyze_relationships()

            for table_name in self.inspector.get_table_names():
                fks = self.inspector.get_foreign_keys(table_name)

                # Generate all view types
                for view_gen_class in [
                    GenModelView,
                    GenMasterDetailView,
                    GenMultipleView,
                    GenCalendarView,
                    GenChartView,
                    GenWizardView,
                    GenReportView,
                    GenTreeView,
                    GenKanbanView,
                    GenDashboardView,
                ]:
                    if view_gen_class in [GenMasterDetailView, GenMultipleView]:
                        if view_gen_class == GenMasterDetailView:
                            for fk in fks:
                                gen = view_gen_class(
                                    table_name, fk, self.inspector, relationships
                                )
                                view_code.extend(gen.generate())
                        elif view_gen_class == GenMultipleView and len(fks) > 1:
                            gen = view_gen_class(
                                table_name, fks, self.inspector, relationships
                            )
                            view_code.extend(gen.generate())
                    else:
                        gen = view_gen_class(table_name, self.inspector, relationships)
                        view_code.extend(gen.generate())
                    self.models.add(gen.model_name)

            # Add REST and GraphQL endpoints
            view_code.extend(self._generate_rest_endpoints())
            view_code.extend(self._generate_graphql_schema())

            return view_code

        except Exception as e:
            logger.error(f"Error generating views: {str(e)}")
            raise

    def _generate_preamble(self) -> List[str]:
        return [
            "from flask_appbuilder import ModelView, MasterDetailView, MultipleView, CompactView",
            "from flask_appbuilder import CalendarView, ChartView, ReportView, TreeView, KanbanView, DashboardView",
            "from flask_appbuilder.models.sqla.interface import SQLAInterface",
            "from flask_appbuilder.api import ModelRestApi",
            "from graphene import ObjectType, String, Int, List, Schema",
            "from flask import request",
            "from .models import *",
            "import logging",
            "\n# Flask-AppBuilder Views with Extended Features",
            "\n",
        ]

    def _analyze_relationships(self) -> Dict[str, Dict[str, str]]:
        relationships = {}
        for table_name in self.inspector.get_table_names():
            relationships[table_name] = {}
            fks = self.inspector.get_foreign_keys(table_name)
            for fk in fks:
                ref_table = fk["referred_table"]
                cardinality = self._determine_cardinality(table_name, fk)
                relationships[table_name][ref_table] = cardinality
        return relationships

    def _determine_cardinality(self, table_name: str, fk: Dict) -> str:
        pk = self.inspector.get_pk_constraint(table_name)
        constrained_cols = set(fk["constrained_columns"])
        pk_cols = set(pk["constrained_columns"])
        fks = self.inspector.get_foreign_keys(table_name)
        is_assoc_table = len(fks) >= 2 and all(fk["constrained_columns"] for fk in fks)

        if is_assoc_table:
            return "many-to-many"
        if constrained_cols == pk_cols:
            return "one-to-one"
        return "many-to-one"

    def _snake_to_pascal(self, name: str) -> str:
        return "".join(word.capitalize() for word in name.split("_"))

    def _generate_rest_endpoints(self) -> List[str]:
        code = ["\n# REST API Endpoints"]
        for model in self.models:
            code.extend(
                [
                    f"class {model}RestApi(ModelRestApi):",
                    f"{INDENT}resource_name = '{model.lower()}'",
                    f"{INDENT}datamodel = SQLAInterface({model})",
                    f"{INDENT}allow_browser_login = True",
                    "",
                ]
            )
        return code

    def _generate_graphql_schema(self) -> List[str]:
        code = ["\n# GraphQL Schema"]
        for model in self.models:
            fields = [col["name"] for col in self.inspector.get_columns(model.lower())]
            code.extend(
                [
                    f"class {model}Type(ObjectType):",
                    f"{INDENT}class Meta:",
                    f"{INDENT}{INDENT}model = {model}",
                    f"{INDENT}{', '.join(f'{field} = String()' for field in fields)}",
                    "",
                ]
            )

        code.extend(
            [
                "class Query(ObjectType):",
                f"{INDENT}"
                + "\n".join(
                    f"{model.lower()} = List({model}Type)" for model in self.models
                ),
                "",
                f"{INDENT}"
                + "\n".join(
                    f"def resolve_{model.lower()}(root, info):\n"
                    f"{INDENT}{INDENT}return {model}.query.all()"
                    for model in self.models
                ),
                "",
                "schema = Schema(query=Query)",
            ]
        )
        return code


def generate_app_registration(view_code: List[str], models: Set[str]) -> List[str]:
    registration_code = [
        "\n# View Registration",
        "def register_views(appbuilder):",
        f'{INDENT}"""Register all views and APIs with the Flask-AppBuilder application"""',
    ]

    view_types = [
        "View",
        "MasterDetailView",
        "MultipleView",
        "CalendarView",
        "ChartView",
        "WizardView",
        "ReportView",
        "TreeView",
        "KanbanView",
        "DashboardView",
    ]

    for model in models:
        for view_type in view_types:
            registration_code.append(
                f"{INDENT}appbuilder.add_view({model}{view_type}, '{model} {view_type.replace('View', '')}', category='{model}')"
            )
        registration_code.append(f"{INDENT}appbuilder.add_api({model}RestApi)")

    registration_code.extend(
        [
            f"{INDENT}appbuilder.add_link('GraphQL', '/graphql', category='API')",
        ]
    )

    return registration_code


def main():
    parser = argparse.ArgumentParser(
        description="Generate Flask-AppBuilder views with REST and GraphQL"
    )
    parser.add_argument("--uri", type=str, required=True, help="Database URI")
    parser.add_argument(
        "--output", type=str, default="generated_views.py", help="Output file name"
    )
    args = parser.parse_args()

    try:
        generator = ViewGenerator()
        generator.initialize_db_connection(args.uri)

        view_code = generator.generate_views()
        view_code.extend(generate_app_registration(view_code, generator.models))

        with open(args.output, "w") as f:
            f.write("\n".join(view_code))

        logger.info(f"Views generated successfully. Output written to {args.output}")

    except Exception as e:
        logger.error(f"Failed to generate views: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
