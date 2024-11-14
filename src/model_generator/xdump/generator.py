#!/usr/bin/env python3
"""
generator.py: Model generation orchestrator module.

This module contains the ModelGenerator class, which is responsible for:
- Coordinating the overall model generation process
- Invoking the appropriate handlers to process the database schema
- Handling circular dependencies between tables and relationships
- Providing a unified interface for the model generation workflow

The ModelGenerator class utilizes the DatabaseIntrospector, various Handlers,
and the TemplateManager to generate the final SQLAlchemy model definitions.
"""

from typing import Dict, List, Set, Tuple
from sqlalchemy import Table
from model_generator.config.base_config import GeneratorConfig
from model_generator.core.introspector import DatabaseIntrospector
from model_generator.core.registry import HandlerRegistry
from model_generator.core.writer import ModelWriter
from model_generator.templates.manager import TemplateManager
from model_generator.exceptions import GenerationError, CircularDependencyError

class ModelGenerator:
    """
    Responsible for orchestrating the SQLAlchemy model generation process.

    Args:
        config (GeneratorConfig): Configuration for the generation process.
    """

    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.introspector = DatabaseIntrospector(config.database)
        self.handlers = HandlerRegistry(config)
        self.template_manager = TemplateManager(config.templates.directory)
        self.writer = ModelWriter(config.output)

    def generate_models(self) -> None:
        """
        Execute the model generation process.

        This method coordinates the overall workflow, including:
        1. Retrieving the database schema information
        2. Processing each table through the relevant handlers
        3. Generating the final model definitions
        4. Writing the models to the output files
        """
        try:
            # Retrieve the database schema information
            schema_info = self.introspector.get_schema_info()

            # Process each table through the handlers
            model_definitions = {}
            for table_name, table_info in schema_info.items():
                model_definition = self.process_table(table_info)
                if model_definition:
                    model_definitions[table_name] = model_definition

            # Handle circular dependencies
            self.handle_circular_dependencies(model_definitions)

            # Write the models to output files
            self.writer.write_multiple_files(model_definitions)
        except Exception as e:
            self.handle_errors([GenerationError.from_exception(e)])

    def process_table(self, table_info: 'TableInfo') -> str:
        """
        Process a single table and generate the corresponding SQLAlchemy model definition.

        Args:
            table_info (TableInfo): Detailed information about the table.

        Returns:
            str: The generated model definition as a string.
        """
        try:
            # Invoke the handlers to process the table
            context = self.handlers.process_table(table_info)

            # Render the model template with the processed context
            model_definition = self.template_manager.render_model(context)
            return model_definition
        except Exception as e:
            error = GenerationError.from_exception(e, table_name=table_info.name)
            self.handle_errors([error])
            return ""

    def handle_circular_dependencies(self, model_definitions: Dict[str, str]) -> None:
        """
        Detect and handle circular dependencies between generated models.

        Args:
            model_definitions (Dict[str, str]): Dictionary of model definitions, keyed by table name.
        """
        try:
            # Detect circular dependencies
            relationships = self.introspector.get_relationships()
            cycles = self.detect_circular_dependencies(relationships)

            if cycles:
                # Resolve circular dependencies
                self.resolve_circular_dependencies(cycles, model_definitions)
        except Exception as e:
            error = GenerationError.from_exception(e)
            self.handle_errors([error])

    def detect_circular_dependencies(self, relationships: Dict[str, List['Relationship']]) -> Set[Tuple[str, str]]:
        """
        Detect circular dependencies in the database schema.

        Args:
            relationships (Dict[str, List[Relationship]]): Dictionary of relationships, keyed by table name.

        Returns:
            Set[Tuple[str, str]]: Set of table name pairs that form circular dependencies.
        """
        try:
            return self.handlers.get_handler('relationship').detect_cycles(relationships)
        except Exception as e:
            error = GenerationError.from_exception(e)
            self.handle_errors([error])
            return set()

    def resolve_circular_dependencies(self, cycles: Set[Tuple[str, str]],
                                     model_definitions: Dict[str, str]) -> None:
        """
        Resolve circular dependencies in the generated model definitions.

        Args:
            cycles (Set[Tuple[str, str]]): Set of table name pairs that form circular dependencies.
            model_definitions (Dict[str, str]): Dictionary of model definitions, keyed by table name.
        """
        try:
            self.handlers.get_handler('relationship').resolve_circular_dependencies(
                cycles, model_definitions
            )
        except Exception as e:
            error = GenerationError.from_exception(e)
            self.handle_errors([error])

    def handle_errors(self, errors: List[GenerationError]) -> None:
        """
        Handle errors that occur during the model generation process.

        This method logs the errors and raises a consolidated exception.

        Args:
            errors (List[GenerationError]): List of errors that occurred.
        """
        if errors:
            # Log the errors
            for error in errors:
                self.log_error(error)

            # Raise a consolidated exception
            raise CircularDependencyError(
                "Errors occurred during the model generation process.",
                errors=errors
            )

    def log_error(self, error: GenerationError) -> None:
        """
        Log a model generation error.

        Args:
            error (GenerationError): The error to be logged.
        """
        # TODO: Implement error logging
        pass
