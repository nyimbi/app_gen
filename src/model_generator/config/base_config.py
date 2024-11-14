#!/usr/bin/env python3
"""
filename: base_config.py
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT
File Description: Base configuration classes using dataclasses for type-safe configuration management.

config/base_config.py

This module provides the core functionality for loading, validating, and
managing the configuration for the Flask-AppBuilder code generation subsystem.

The main components in this module are:

1. ConfigLoader: Responsible for loading the configuration from various sources
   (e.g., YAML files, environment variables) and merging it with default values.

2. ConfigValidator: Implements the validation logic for the various configuration
   sections, ensuring that the provided settings are valid and consistent.

3. ConfigManager: Serves as the central entry point for accessing and working
   with the configuration, handling the loading, validation, and merging of
   configuration data.
"""

import os
import yaml
from typing import Dict, Any, List
from pathlib import Path
from .types import GeneratorConfig, DatabaseConfig, GenerationConfig, RelationshipsConfig, SecurityConfig
from .validators import ConfigValidator

class ConfigLoader:
    """
    Responsible for loading the configuration from various sources and merging
    it with default values.
    """

    def load(self, config_path: Path) -> GeneratorConfig:
        """
        Load the configuration from a YAML file.

        Args:
            config_path (Path): The path to the YAML configuration file.

        Returns:
            GeneratorConfig: The loaded and validated configuration.

        Raises:
            FileNotFoundError: If the specified configuration file does not exist.
            yaml.YAMLError: If there is an error parsing the YAML configuration file.
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with config_path.open('r') as file:
                config_data = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            raise ValueError(f"Error parsing configuration file: {exc}") from exc

        return self.load_from_dict(config_data)

    def load_from_dict(self, config_data: Dict[str, Any]) -> GeneratorConfig:
        """
        Load the configuration from a dictionary.

        Args:
            config_data (Dict[str, Any]): The configuration data as a dictionary.

        Returns:
            GeneratorConfig: The loaded and validated configuration.
        """
        validator = ConfigValidator()

        database_config = DatabaseConfig(**config_data.get('database', {}))
        generation_config = GenerationConfig(**config_data.get('generation', {}))
        relationships_config = RelationshipsConfig(**config_data.get('relationships', {}))
        security_config = SecurityConfig(**config_data.get('security', {}))

        validator.validate_database_config(database_config)
        validator.validate_generation_config(generation_config)
        validator.validate_relationships_config(relationships_config)
        validator.validate_security_config(security_config)

        return GeneratorConfig(
            database=database_config,
            generation=generation_config,
            relationships=relationships_config,
            security=security_config
        )

    def merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge the provided configuration with default values.

        Args:
            config (Dict[str, Any]): The configuration data as a dictionary.

        Returns:
            Dict[str, Any]: The merged configuration with default values.
        """
        defaults = self.get_default_config()
        merged_config = defaults.copy()
        merged_config.update(config)
        return merged_config

    def get_default_config(self) -> Dict[str, Any]:
        """
        Retrieve the default configuration.

        Returns:
            Dict[str, Any]: The default configuration.
        """
        return {
            'database': {
                'uri': os.getenv('DATABASE_URI', 'postgresql://user:password@localhost/database'),
                'schema': os.getenv('DATABASE_SCHEMA', 'public'),
                'exclude_tables': [],
                'include_tables': [],
                'custom_type_mappings': {}
            },
            'generation': {
                'output_dir': Path('generated_models'),
                'output_style': 'multiple_files',
                'indent_size': 4,
                'template_dir': Path('templates'),
                'include_views': False,
                'include_procedures': False
            },
            'relationships': {
                'auto_detect': True,
                'manual_relationships': {},
                'handle_circular_dependencies': True,
                'use_backref': True
            },
            'security': {
                'enable_permissions': True,
                'sensitive_fields': [],
                'password_fields': []
            }
        }

class ConfigValidator:
    """
    Implements the validation logic for the various configuration sections.
    """

    def validate_database_config(self, config: DatabaseConfig) -> List[str]:
        """
        Validate the database configuration.

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
        Validate the code generation configuration.

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
        Validate the relationships configuration.

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
        Validate the security configuration.

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

class ConfigManager:
    """
    Serves as the central entry point for accessing and working with the
    configuration, handling the loading, validation, and merging of
    configuration data.
    """

    def __init__(self, config_path: Path = Path('config.yml')):
        self.config_path = config_path
        self.config_loader = ConfigLoader()
        self.config_validator = ConfigValidator()
        self.config: GeneratorConfig = self.load_config()

    def load_config(self) -> GeneratorConfig:
        """
        Load the configuration from the specified file path.

        Returns:
            GeneratorConfig: The loaded and validated configuration.

        Raises:
            ValueError: If there are any errors in the configuration.
        """
        config_data = self.config_loader.load(self.config_path)
        errors = self.config_validator.validate_config(config_data)
        if errors:
            raise ValueError("Invalid configuration:\n" + "\n".join(errors))
        return config_data

    def get_config(self) -> GeneratorConfig:
        """
        Retrieve the loaded and validated configuration.

        Returns:
            GeneratorConfig: The configuration.
        """
        return self.config

    def reload_config(self) -> GeneratorConfig:
        """
            Reload the configuration from the specified file path.

        Returns:
            GeneratorConfig: The reloaded and validated configuration.

        Raises:
            ValueError: If there are any errors in the configuration.
        """
        self.config = self.load_config()
        return self.config

    def update_config(self, new_config: Dict[str, Any]) -> GeneratorConfig:
        """
        Update the configuration with new values.

        Args:
            new_config (Dict[str, Any]): The new configuration data.

        Returns:
            GeneratorConfig: The updated and validated configuration.

        Raises:
            ValueError: If there are any errors in the updated configuration.
        """
        merged_config = self.config_loader.merge_with_defaults(new_config)
        errors = self.config_validator.validate_config(merged_config)
        if errors:
            raise ValueError("Invalid configuration:\n" + "\n".join(errors))
        self.config = GeneratorConfig(**merged_config)
        return self.config
