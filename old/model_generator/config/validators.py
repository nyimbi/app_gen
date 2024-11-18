#!/usr/bin/env python3
"""
config/validators.py

This module contains the implementation of the `ConfigValidator` class, which is
responsible for validating the configuration settings for the Flask-AppBuilder
code generation subsystem.

The validation logic is divided into separate methods, each handling a specific
configuration section (database, generation, relationships, security, etc.). This
separation of concerns allows for better maintainability, testability, and
extensibility of the validation process.
"""

import re
import keyword
from typing import List, Dict, Any
from .types import DatabaseConfig, GenerationConfig, RelationshipsConfig, SecurityConfig, GeneratorConfig

class ConfigValidator:
    """
    Implements the validation logic for the various configuration sections.
    """

    def validate_database_config(self, config: DatabaseConfig) -> List[str]:
        """
        Validate the database configuration section.

        Args:
            config (DatabaseConfig): The database configuration to validate.

        Returns:
            List[str]: A list of error messages, if any.
        """
        errors = []

        if not config.uri:
            errors.append("Database URI is required.")
        if not config.schema:
            errors.append("Database schema is required.")

        for table in config.exclude_tables:
            if not self.validate_identifier(table):
                errors.append(f"Invalid table name in 'exclude_tables': {table}")

        for table in config.include_tables:
            if not self.validate_identifier(table):
                errors.append(f"Invalid table name in 'include_tables': {table}")

        for db_type, py_type in config.custom_type_mappings.items():
            if not self.validate_identifier(db_type):
                errors.append(f"Invalid database type in 'custom_type_mappings': {db_type}")
            if not self.validate_identifier(py_type):
                errors.append(f"Invalid Python type in 'custom_type_mappings': {py_type}")

        return errors

    def validate_generation_config(self, config: GenerationConfig) -> List[str]:
        """
        Validate the code generation configuration section.

        Args:
            config (GenerationConfig): The code generation configuration to validate.

        Returns:
            List[str]: A list of error messages, if any.
        """
        errors = []

        if not config.output_dir or not config.output_dir.is_dir():
            errors.append("Output directory is required and must be a valid directory.")

        if config.indent_size <= 0:
            errors.append("Indent size must be a positive integer.")

        if not config.template_dir.is_dir():
            errors.append("Template directory is required and must be a valid directory.")

        return errors

    def validate_relationships_config(self, config: RelationshipsConfig) -> List[str]:
        """
        Validate the relationships configuration section.

        Args:
            config (RelationshipsConfig): The relationships configuration to validate.

        Returns:
            List[str]: A list of error messages, if any.
        """
        errors = []

        for table_name, relationships in config.manual_relationships.items():
            if not self.validate_identifier(table_name):
                errors.append(f"Invalid table name in 'manual_relationships': {table_name}")

            for rel in relationships:
                if 'source_table' not in rel or not self.validate_identifier(rel['source_table']):
                    errors.append(f"Invalid source table name in 'manual_relationships': {rel['source_table']}")
                if 'target_table' not in rel or not self.validate_identifier(rel['target_table']):
                    errors.append(f"Invalid target table name in 'manual_relationships': {rel['target_table']}")
                if 'foreign_keys' not in rel or not isinstance(rel['foreign_keys'], list):
                    errors.append(f"Invalid foreign keys in 'manual_relationships' for table {table_name}")
                else:
                    for fk in rel['foreign_keys']:
                        if not self.validate_identifier(fk):
                            errors.append(f"Invalid foreign key in 'manual_relationships' for table {table_name}: {fk}")

        return errors

    def validate_security_config(self, config: SecurityConfig) -> List[str]:
        """
        Validate the security configuration section.

        Args:
            config (SecurityConfig): The security configuration to validate.

        Returns:
            List[str]: A list of error messages, if any.
        """
        errors = []

        for field in config.sensitive_fields:
            if not self.validate_identifier(field):
                errors.append(f"Invalid sensitive field name: {field}")

        for field in config.password_fields:
            if not self.validate_identifier(field):
                errors.append(f"Invalid password field name: {field}")

        return errors

    def validate_config(self, config: GeneratorConfig) -> List[str]:
        """
        Validate the entire configuration.

        Args:
            config (GeneratorConfig): The configuration to validate.

        Returns:
            List[str]: A list of error messages, if any.
        """
        errors = []
        errors.extend(self.validate_database_config(config.database))
        errors.extend(self.validate_generation_config(config.generation))
        errors.extend(self.validate_relationships_config(config.relationships))
        errors.extend(self.validate_security_config(config.security))
        errors.extend(self.check_config_consistency(config))
        return errors

    def check_config_consistency(self, config: GeneratorConfig) -> List[str]:
        """
        Check for consistency across the entire configuration.

        Args:
            config (GeneratorConfig): The configuration to validate.

        Returns:
            List[str]: A list of error messages, if any.
        """
        errors = []

        # Add any cross-section consistency checks here
        if config.database.include_tables and config.database.exclude_tables:
            errors.append("'include_tables' and 'exclude_tables' cannot both be specified.")

        return errors

    def validate_identifier(self, identifier: str) -> bool:
        """
        Validate a Python identifier.

        Args:
            identifier (str): The identifier to validate.

        Returns:
            bool: True if the identifier is valid, False otherwise.
        """
        if not isinstance(identifier, str) or not identifier.isidentifier():
            return False
        return identifier not in keyword.kwlist
