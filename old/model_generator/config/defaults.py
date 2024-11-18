#!/usr/bin/env python3
"""
config/defaults.py

This module defines the default configuration values for the various sections of
the Flask-AppBuilder code generation subsystem. These default values provide a
starting point for the configuration and can be overridden by the user in their
own configuration files or environment variables.

The default values are organized into the same configuration sections as defined
in the `config/types.py` module, ensuring a consistent and coherent structure
throughout the configuration management system.
"""

from pathlib import Path

DATABASE_URI = "postgresql://user:password@localhost/database"
DATABASE_SCHEMA = "public"
DATABASE_EXCLUDE_TABLES = []
DATABASE_INCLUDE_TABLES = []
DATABASE_CUSTOM_TYPE_MAPPINGS = {}

GENERATION_OUTPUT_DIR = Path("generated_models")
GENERATION_OUTPUT_STYLE = "multiple_files"
GENERATION_INDENT_SIZE = 4
GENERATION_TEMPLATE_DIR = Path("templates")
GENERATION_INCLUDE_VIEWS = False
GENERATION_INCLUDE_PROCEDURES = False

RELATIONSHIPS_AUTO_DETECT = True
RELATIONSHIPS_MANUAL = {}
RELATIONSHIPS_HANDLE_CIRCULAR = True
RELATIONSHIPS_USE_BACKREF = True

SECURITY_ENABLE_PERMISSIONS = True
SECURITY_SENSITIVE_FIELDS = []
SECURITY_PASSWORD_FIELDS = []

DEFAULT_CONFIG = {
    "database": {
        "uri": DATABASE_URI,
        "schema": DATABASE_SCHEMA,
        "exclude_tables": DATABASE_EXCLUDE_TABLES,
        "include_tables": DATABASE_INCLUDE_TABLES,
        "custom_type_mappings": DATABASE_CUSTOM_TYPE_MAPPINGS,
    },
    "generation": {
        "output_dir": GENERATION_OUTPUT_DIR,
        "output_style": GENERATION_OUTPUT_STYLE,
        "indent_size": GENERATION_INDENT_SIZE,
        "template_dir": GENERATION_TEMPLATE_DIR,
        "include_views": GENERATION_INCLUDE_VIEWS,
        "include_procedures": GENERATION_INCLUDE_PROCEDURES,
    },
    "relationships": {
        "auto_detect": RELATIONSHIPS_AUTO_DETECT,
        "manual_relationships": RELATIONSHIPS_MANUAL,
        "handle_circular_dependencies": RELATIONSHIPS_HANDLE_CIRCULAR,
        "use_backref": RELATIONSHIPS_USE_BACKREF,
    },
    "security": {
        "enable_permissions": SECURITY_ENABLE_PERMISSIONS,
        "sensitive_fields": SECURITY_SENSITIVE_FIELDS,
        "password_fields": SECURITY_PASSWORD_FIELDS,
    },
}
