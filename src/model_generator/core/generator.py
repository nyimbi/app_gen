#!/usr/bin/env python3
"""
generator.py: SQLAlchemy Model Generation Orchestrator

This module provides the core model generation functionality, coordinating the
introspection, processing, and output of SQLAlchemy models. It handles the complete
workflow of analyzing database schemas and generating corresponding Python code.

Key Features:
    - Orchestrates the complete model generation process
    - Manages database introspection and schema analysis
    - Coordinates template rendering and code generation
    - Handles relationship and dependency management
    - Provides error handling and logging
    - Manages file output and backups
    - Supports customization through hooks and handlers

The ModelGenerator class serves as the main entry point for the code generation
process, coordinating between various components like the DatabaseIntrospector,
TemplateManager, and different handlers.

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from datetime import datetime

from sqlalchemy import Table
from jinja2 import Environment, FileSystemLoader, Template

from model_generator.config.types import GeneratorConfig
from model_generator.core.introspector import DatabaseIntrospector
from model_generator.core.context import GenerationContext, TableInfo
from model_generator.templates.manager import TemplateManager
from model_generator.core.writer import ModelWriter
from model_generator.handlers.base import BaseHandler
from model_generator.handlers.model import ModelHandler
from model_generator.handlers.relationship import RelationshipHandler
from model_generator.handlers.view import ViewHandler
from model_generator.exceptions import (
    GenerationError, CircularDependencyError,
    TemplateError, ValidationError
)

# Configure logging
logger = logging.getLogger(__name__)

class ModelGenerator:
    """
    Main orchestrator for SQLAlchemy model generation.

    This class coordinates the entire model generation process, from database
    introspection to file output, managing all intermediate steps and ensuring
    proper error handling and logging.

    Attributes:
        config: Generator configuration
        introspector: Database schema introspector
        template_manager: Template rendering manager
        writer: Output file writer
        handlers: Dictionary of registered handlers
        contexts: Generation contexts by table
        errors: List of encountered errors
    """

    def __init__(self, config: GeneratorConfig):
        """
        Initialize the model generator.

        Args:
            config: Generator configuration
        """
        self.config = config
        self.introspector = DatabaseIntrospector(config.database)
        self.template_manager = TemplateManager(config.generation.template_dir)
        self.writer = ModelWriter(config.generation.output_dir)

        # Initialize handlers
        self.handlers = self._initialize_handlers()

        # State tracking
        self.contexts: Dict[str, GenerationContext] = {}
        self.errors: List[GenerationError] = []

        # Set up logging
        self._setup_logging()

    def _initialize_handlers(self) -> Dict[str, BaseHandler]:
        """Initialize and configure all handlers."""
        return {
            'model': ModelHandler(self.config),
            'relationship': RelationshipHandler(self.config),
            'view': ViewHandler(self.config)
        }

    def _setup_logging(self) -> None:
        """Configure logging for the generator."""
        log_config = self.config.logging
        if not log_config.enabled:
            return

        # Create formatter
        formatter = logging.Formatter(log_config.format)

        # Add file handler if specified
        if log_config.file:
            if log_config.rotate:
                handler = logging.handlers.RotatingFileHandler(
                    log_config.file,
                    maxBytes=log_config.max_size,
                    backupCount=log_config.backup_count
                )
            else:
                handler = logging.FileHandler(log_config.file)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # Add console handler if enabled
        if log_config.console_output:
            console = logging.StreamHandler()
            console.setFormatter(formatter)
            logger.addHandler(console)

        logger.setLevel(log_config.level)

    def generate(self) -> bool:
        """
        Execute the complete model generation process.

        Returns:
            bool: True if generation was successful, False otherwise
        """
        try:
            logger.info("Starting model generation process...")

            # Run pre-generation hooks
            self._run_hooks('pre_generation')

            # Introspect database schema
            self.contexts = self.introspect_schema()

            # Validate configuration and contexts
            self._validate()

            # Process each context through handlers
            self._process_contexts()

            # Handle relationships and dependencies
            self._process_relationships()

            # Generate the code
            generated_files = self._generate_code()

            # Write output files
            self._write_output(generated_files)

            # Run post-generation hooks
            self._run_hooks('post_generation', {'files': generated_files})

            logger.info("Model generation completed successfully.")
            return True

        except Exception as e:
            self._handle_error(e)
            return False
        finally:
            self.cleanup()

    def introspect_schema(self) -> Dict[str, GenerationContext]:
        """
        Introspect the database schema and create generation contexts.

        Returns:
            Dict[str, GenerationContext]: Contexts for each table
        """
        logger.info("Introspecting database schema...")
        try:
            # Get contexts from introspector
            contexts = self.introspector.introspect_schema()

            # Filter based on configuration
            filtered_contexts = self._filter_contexts(contexts)

            logger.info(f"Schema introspection complete. Found {len(filtered_contexts)} tables.")
            return filtered_contexts

        except Exception as e:
            raise GenerationError("Schema introspection failed", cause=e)

    def _filter_contexts(self, contexts: Dict[str, GenerationContext]) -> Dict[str, GenerationContext]:
        """
        Filter contexts based on configuration.

        Args:
            contexts: All generation contexts

        Returns:
            Dict[str, GenerationContext]: Filtered contexts
        """
        if self.config.database.include_tables:
            return {
                name: ctx for name, ctx in contexts.items()
                if name in self.config.database.include_tables
            }
        return {
            name: ctx for name, ctx in contexts.items()
            if name not in self.config.database.exclude_tables
        }

    def _validate(self) -> None:
        """
        Validate configuration and contexts.

        Raises:
            ValidationError: If validation fails
        """
        logger.debug("Validating configuration and contexts...")

        # Run pre-validation hooks
        self._run_hooks('pre_validation')

        errors = []

        # Validate configuration
        errors.extend(self.config.validate())

        # Validate contexts
        for table_name, context in self.contexts.items():
            context_errors = self._validate_context(context)
            if context_errors:
                errors.extend(f"Table {table_name}: {error}" for error in context_errors)

        # Run post-validation hooks
        self._run_hooks('post_validation', {'errors': errors})

        if errors:
            raise ValidationError("Validation failed", errors=errors)

    def _validate_context(self, context: GenerationContext) -> List[str]:
        """
        Validate a single generation context.

        Args:
            context: Context to validate

        Returns:
            List[str]: List of validation errors
        """
        errors = []

        # Validate table info
        if not context.table_info.name:
            errors.append("Missing table name")

        # Validate columns
        if not context.table_info.columns:
            errors.append("No columns defined")

        # Validate relationships
        for rel in context.relationships:
            if not rel.target_table:
                errors.append(f"Missing target table in relationship")
            if rel.source_table != context.table_info.name:
                errors.append(f"Invalid source table in relationship")

        return errors

    def _process_contexts(self) -> None:
        """Process all contexts through registered handlers."""
        logger.info("Processing contexts through handlers...")

        for table_name, context in self.contexts.items():
            try:
                logger.debug(f"Processing table: {table_name}")

                # Run pre-process hooks
                self._run_hooks('pre_process_table', {'table_name': table_name})

                # Process through each handler
                for handler_name, handler in self.handlers.items():
                    logger.debug(f"Running handler: {handler_name}")
                    context = handler.process(context)

                # Update processed context
                self.contexts[table_name] = context

                # Run post-process hooks
                self._run_hooks('post_process_table', {
                    'table_name': table_name,
                    'context': context
                })

            except Exception as e:
                self._handle_error(e, table_name=table_name)


    def _process_relationships(self) -> None:
        """Process and validate relationships between tables."""
        logger.info("Processing relationships...")
        try:
            # Detect circular dependencies
            cycles = self._detect_circular_dependencies()
            if cycles:
                logger.warning(f"Found circular dependencies: {cycles}")
                self._resolve_circular_dependencies(cycles)

            # Process relationships in each context
            for table_name, context in self.contexts.items():
                self._process_context_relationships(context)

        except Exception as e:
            raise GenerationError("Failed to process relationships", cause=e)

    def _detect_circular_dependencies(self) -> Set[Tuple[str, str]]:
        """
        Detect circular dependencies in relationships.

        Returns:
            Set[Tuple[str, str]]: Pairs of tables with circular dependencies
        """
        cycles = set()
        visited = set()
        path = []

        def visit(table_name: str) -> None:
            if table_name in path:
                cycle_start = path.index(table_name)
                cycle = path[cycle_start:]
                for i in range(len(cycle) - 1):
                    cycles.add((cycle[i], cycle[i + 1]))
                return

            if table_name in visited:
                return

            visited.add(table_name)
            path.append(table_name)

            context = self.contexts.get(table_name)
            if context:
                for rel in context.relationships:
                    visit(rel.target_table)

            path.pop()

        for table_name in self.contexts:
            visit(table_name)

        return cycles

    def _resolve_circular_dependencies(self, cycles: Set[Tuple[str, str]]) -> None:
        """
        Resolve circular dependencies by modifying relationship configurations.

        Args:
            cycles: Set of table pairs with circular dependencies
        """
        for source, target in cycles:
            logger.debug(f"Resolving circular dependency: {source} <-> {target}")

            # Get the contexts
            source_ctx = self.contexts.get(source)
            target_ctx = self.contexts.get(target)

            if source_ctx and target_ctx:
                # Modify relationships to break the cycle
                self._modify_relationship_for_cycle(source_ctx, target)
                self._modify_relationship_for_cycle(target_ctx, source)

    def _modify_relationship_for_cycle(self, context: GenerationContext, target: str) -> None:
        """
        Modify relationships in a context to handle circular dependencies.

        Args:
            context: Context to modify
            target: Target table name
        """
        for rel in context.relationships:
            if rel.target_table == target:
                # Convert to lazy loading
                rel.lazy = 'select'
                # Add necessary imports
                context.add_import('from sqlalchemy.orm import relationship, backref')
                break

    def _process_context_relationships(self, context: GenerationContext) -> None:
        """
        Process relationships for a single context.

        Args:
            context: Context to process
        """
        for relationship in context.relationships:
            # Validate relationship
            if not self._validate_relationship(relationship):
                continue

            # Add necessary imports
            self._add_relationship_imports(context, relationship)

            # Process backref if needed
            if relationship.backref_name:
                self._setup_backref(context, relationship)

    def _generate_code(self) -> Dict[str, str]:
        """
        Generate code for all contexts.

        Returns:
            Dict[str, str]: Generated code by filename
        """
        logger.info("Generating code...")
        generated_files = {}

        try:
            for table_name, context in self.contexts.items():
                # Run pre-generation hooks for this table
                self._run_hooks('pre_generate_table', {
                    'table_name': table_name,
                    'context': context
                })

                # Generate model code
                model_code = self._generate_model_code(context)
                if model_code:
                    filename = self._get_output_filename(context)
                    generated_files[filename] = model_code

                # Generate view code if needed
                if self.config.generation.include_views:
                    view_code = self._generate_view_code(context)
                    if view_code:
                        view_filename = self._get_view_filename(context)
                        generated_files[view_filename] = view_code

                # Run post-generation hooks for this table
                self._run_hooks('post_generate_table', {
                    'table_name': table_name,
                    'context': context,
                    'generated_code': model_code
                })

        except Exception as e:
            raise GenerationError("Code generation failed", cause=e)

        return generated_files

    def _generate_model_code(self, context: GenerationContext) -> str:
        """
        Generate model code for a context.

        Args:
            context: Context to generate code for

        Returns:
            str: Generated model code
        """
        try:
            # Get the appropriate template
            template = self.template_manager.get_template('model.py.jinja2')

            # Render the template
            return template.render(
                context=context,
                config=self.config,
                timestamp=datetime.now().isoformat(),
                generator_version="1.0.0"  # TODO: Get from package
            )
        except Exception as e:
            raise TemplateError(f"Failed to generate model code for {context.table_info.name}", cause=e)

    def _write_output(self, generated_files: Dict[str, str]) -> None:
        """
        Write generated code to output files.

        Args:
            generated_files: Dictionary of filenames to generated code
        """
        logger.info("Writing output files...")
        try:
            # Ensure output directory exists
            self.writer.ensure_output_directory()

            # Create backup if needed
            if self.config.generation.backup_existing:
                self.writer.backup_existing_files()

            # Write each file
            for filename, content in generated_files.items():
                self.writer.write_file(filename, content)

            logger.info(f"Successfully wrote {len(generated_files)} files")

        except Exception as e:
            raise GenerationError("Failed to write output files", cause=e)

    def _handle_error(self, error: Exception, table_name: Optional[str] = None) -> None:
        """
        Handle and log an error during generation.

        Args:
            error: Exception that occurred
            table_name: Optional table name for context
        """
        if isinstance(error, GenerationError):
            err = error
        else:
            err = GenerationError(
                str(error),
                cause=error,
                table_name=table_name
            )

        self.errors.append(err)
        logger.error(f"Error during generation: {err}")

        # Run error hooks
        self._run_hooks('on_error', {
            'error': err,
            'table_name': table_name
        })

        if self.config.generation.fail_fast:
            raise err

    def _run_hooks(self, hook_point: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Run registered hooks for a specific point in the generation process.

        Args:
            hook_point: Name of the hook point
            context: Optional context data for hooks
        """
        hooks = self.config.hooks.get(hook_point, [])
        if not hooks:
            return

        logger.debug(f"Running {len(hooks)} hooks for {hook_point}")
        context = context or {}

        for hook in hooks:
            try:
                hook(context)
            except Exception as e:
                logger.error(f"Error in hook {hook.__name__} at {hook_point}: {e}")
                if self.config.generation.strict_hooks:
                    raise

    def _get_output_filename(self, context: GenerationContext) -> str:
        """
        Generate output filename for a model.

        Args:
            context: Generation context

        Returns:
            str: Output filename
        """
        table_name = context.table_info.name
        if self.config.generation.output_style == 'single_file':
            return 'models.py'

        base_name = self._to_snake_case(table_name)
        if self.config.generation.timestamp_files:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"model_{base_name}_{timestamp}.py"

        return f"model_{base_name}.py"

    def _get_view_filename(self, context: GenerationContext) -> str:
        """
        Generate output filename for a view.

        Args:
            context: Generation context

        Returns:
            str: View filename
        """
        table_name = context.table_info.name
        base_name = self._to_snake_case(table_name)
        if self.config.generation.timestamp_files:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"view_{base_name}_{timestamp}.py"
        return f"view_{base_name}.py"

    def _validate_relationship(self, relationship: 'Relationship') -> bool:
        """
        Validate a relationship definition.

        Args:
            relationship: Relationship to validate

        Returns:
            bool: True if relationship is valid
        """
        # Check source and target tables exist
        if relationship.source_table not in self.contexts:
            logger.warning(f"Source table {relationship.source_table} not found")
            return False

        if relationship.target_table not in self.contexts:
            logger.warning(f"Target table {relationship.target_table} not found")
            return False

        # Validate relationship type
        if not hasattr(relationship, 'relationship_type'):
            logger.warning("Missing relationship type")
            return False

        return True

    def _add_relationship_imports(self, context: GenerationContext, relationship: 'Relationship') -> None:
        """
        Add necessary imports for a relationship.

        Args:
            context: Generation context
            relationship: Relationship definition
        """
        context.add_import('from sqlalchemy.orm import relationship')
        if relationship.backref_name:
            context.add_import('from sqlalchemy.orm import backref')
        context.add_import('from sqlalchemy import ForeignKey')

        # Add any type-specific imports
        if relationship.relationship_type == 'many_to_many':
            context.add_import('from sqlalchemy import Table, Column')

    def _setup_backref(self, context: GenerationContext, relationship: 'Relationship') -> None:
        """
        Setup backref for a relationship.

        Args:
            context: Generation context
            relationship: Relationship definition
        """
        target_context = self.contexts.get(relationship.target_table)
        if not target_context:
            return

        # Add backref import to target context
        target_context.add_import('from sqlalchemy.orm import backref')

    def cleanup(self) -> None:
        """Clean up resources and perform final operations."""
        try:
            # Clean up introspector
            if self.introspector:
                self.introspector.cleanup()

            # Clean up template manager
            if self.template_manager:
                self.template_manager.cleanup()

            # Run cleanup hooks
            self._run_hooks('cleanup')

            logger.info("Cleanup completed successfully")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __enter__(self) -> 'ModelGenerator':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.cleanup()

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """
        Convert a string to snake_case.

        Args:
            name: String to convert

        Returns:
            str: Converted string
        """
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def generate_models(config: GeneratorConfig) -> bool:
    """
    Convenience function to generate models from configuration.

    Args:
        config: Generator configuration

    Returns:
        bool: True if generation was successful
    """
    with ModelGenerator(config) as generator:
        return generator.generate()


"""
Usage example:

```python
from model_generator.config.types import GeneratorConfig

# Create configuration
config = GeneratorConfig(
    database=DatabaseConfig(uri="postgresql://user:pass@localhost/dbname"),
    generation=GenerationConfig(output_dir=Path("./generated")),
    # ... other config options ...
)

# Generate models
success = generate_models(config)
if success:
    print("Models generated successfully!")
else:
    print("Model generation failed!")
"""
