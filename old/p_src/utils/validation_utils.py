#!/usr/bin/env python3
"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT

validation_utils.py: A comprehensive utility module for data and schema validation.

This module provides a robust set of validation functions for checking data types, constraints,
and conventions used in database schema generation and Python code generation.

Key Features:
    - Type validation and verification
    - String and numeric constraint checking
    - Database naming convention validation
    - Path and filesystem validation
    - Python identifier validation
    - Custom validation support
    - Regular expression pattern matching

Core Validation Categories:
    1. Type Validation:
        - Basic type checking
        - Required field validation
        - Custom type validation

    2. String Validation:
        - Length constraints
        - Pattern matching
        - Identifier validation
        - Module name validation

    3. Numeric Validation:
        - Range checking
        - Boundary validation

    4. Database Schema Validation:
        - Table name validation
        - Column name validation
        - Identifier conventions

    5. System Validation:
        - Path validation
        - File existence checking

    6. General Utilities:
        - Unique value validation
        - Custom validation function support
        - List validation

Main Functions:
    - validate_type(): Type checking for values
    - validate_required_fields(): Check for required dictionary fields
    - validate_string_length(): String length constraint validation
    - validate_numeric_range(): Numeric value range validation
    - validate_regex_pattern(): Regular expression pattern matching
    - validate_path(): Filesystem path validation
    - validate_identifier_list(): Python identifier validation
    - validate_unique_values(): List uniqueness checking
    - validate_table_name(): Database table name validation
    - validate_column_name(): Database column name validation
    - validate_module_name(): Python module name validation

Usage Examples:
    >>> from validation_utils import validate_type, validate_string_length
    >>> validate_type("test", str)
    True
    >>> validate_string_length("test", min_length=2, max_length=10)
    True
    >>> validate_table_name("valid_table")
    True

Dependencies:
    - re
    - keyword
    - typing
    - pathlib

Note:
    This module is designed to be used as part of a larger model generation system,
    providing essential validation capabilities for ensuring data integrity and
    proper naming conventions throughout the generation process.


"""

import re
import keyword
from typing import Any, List, Dict, Set, Type, Union, Optional, Callable
from pathlib import Path


def validate_type(value: Any, expected_type: Union[Type, tuple]) -> bool:
    """
    Validate that a value is of the expected type.

    Args:
        value: Value to validate
        expected_type: Expected type or tuple of types

    Returns:
        bool: True if value matches expected type(s)

    Examples:
        >>> validate_type("hello", str)
        True
        >>> validate_type(42, (int, float))
        True
        >>> validate_type(None, str)
        False
    """
    return isinstance(value, expected_type)


def validate_required_fields(data: Dict[str, Any], required_fields: Set[str]) -> List[str]:
    """
    Validate that all required fields are present in a dictionary.

    Args:
        data: Dictionary to validate
        required_fields: Set of required field names

    Returns:
        List[str]: List of missing field names

    Examples:
        >>> validate_required_fields({'name': 'test'}, {'name', 'age'})
        ['age']
        >>> validate_required_fields({'name': 'test', 'age': 25}, {'name', 'age'})
        []
    """
    return [field for field in required_fields if field not in data]


def validate_string_length(text: str, min_length: int = 0, max_length: Optional[int] = None) -> bool:
    """
    Validate string length constraints.

    Args:
        text: String to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length (if None, no maximum)

    Returns:
        bool: True if string length is within constraints

    Examples:
        >>> validate_string_length("test", min_length=2, max_length=6)
        True
        >>> validate_string_length("", min_length=1)
        False
    """
    if not isinstance(text, str):
        return False

    length = len(text)
    if length < min_length:
        return False
    if max_length is not None and length > max_length:
        return False
    return True


def validate_numeric_range(value: Union[int, float],
                         min_value: Optional[Union[int, float]] = None,
                         max_value: Optional[Union[int, float]] = None) -> bool:
    """
    Validate numeric value range constraints.

    Args:
        value: Numeric value to validate
        min_value: Minimum allowed value (if None, no minimum)
        max_value: Maximum allowed value (if None, no maximum)

    Returns:
        bool: True if value is within range constraints

    Examples:
        >>> validate_numeric_range(5, min_value=0, max_value=10)
        True
        >>> validate_numeric_range(-1, min_value=0)
        False
    """
    if not isinstance(value, (int, float)):
        return False

    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return True


def validate_regex_pattern(text: str, pattern: str) -> bool:
    """
    Validate text against a regex pattern.

    Args:
        text: Text to validate
        pattern: Regex pattern string

    Returns:
        bool: True if text matches pattern

    Examples:
        >>> validate_regex_pattern("test123", r"^[a-z]+\d+$")
        True
        >>> validate_regex_pattern("Test123", r"^[a-z]+\d+$")
        False
    """
    try:
        return bool(re.match(pattern, text))
    except re.error:
        return False


def validate_path(path: Union[str, Path], must_exist: bool = True) -> bool:
    """
    Validate a file system path.

    Args:
        path: Path to validate
        must_exist: If True, path must exist

    Returns:
        bool: True if path is valid

    Examples:
        >>> validate_path("/tmp", must_exist=True)  # Assumes /tmp exists
        True
        >>> validate_path("/nonexistent/path", must_exist=True)
        False
    """
    try:
        path = Path(path)
        return not must_exist or path.exists()
    except Exception:
        return False


def validate_identifier_list(identifiers: List[str]) -> List[str]:
    """
    Validate a list of Python identifiers.

    Args:
        identifiers: List of strings to validate

    Returns:
        List[str]: List of invalid identifiers

    Examples:
        >>> validate_identifier_list(["valid_name", "123invalid", "class"])
        ['123invalid', 'class']
        >>> validate_identifier_list(["valid_name", "also_valid"])
        []
    """
    invalid = []
    for identifier in identifiers:
        if not identifier.isidentifier() or keyword.iskeyword(identifier):
            invalid.append(identifier)
    return invalid


def validate_unique_values(values: List[Any]) -> bool:
    """
    Validate that all values in a list are unique.

    Args:
        values: List of values to check

    Returns:
        bool: True if all values are unique

    Examples:
        >>> validate_unique_values([1, 2, 3])
        True
        >>> validate_unique_values([1, 2, 2])
        False
    """
    return len(values) == len(set(values))


def validate_with_custom_fn(value: Any, validation_fn: Callable[[Any], bool]) -> bool:
    """
    Validate a value using a custom validation function.

    Args:
        value: Value to validate
        validation_fn: Function that takes a value and returns bool

    Returns:
        bool: Result of validation function

    Examples:
        >>> is_positive = lambda x: x > 0
        >>> validate_with_custom_fn(5, is_positive)
        True
        >>> validate_with_custom_fn(-5, is_positive)
        False
    """
    try:
        return validation_fn(value)
    except Exception:
        return False


def validate_table_name(table_name: str) -> bool:
    """
    Validate a database table name.

    Args:
        table_name: Table name to validate

    Returns:
        bool: True if table name is valid

    Examples:
        >>> validate_table_name("valid_table")
        True
        >>> validate_table_name("invalid.table")
        False
    """
    # Common rules for table names:
    # - Must start with a letter or underscore
    # - Can only contain letters, numbers, and underscores
    # - Cannot be a SQL reserved word
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, table_name))


def validate_column_name(column_name: str) -> bool:
    """
    Validate a database column name.

    Args:
        column_name: Column name to validate

    Returns:
        bool: True if column name is valid

    Examples:
        >>> validate_column_name("valid_column")
        True
        >>> validate_column_name("invalid.column")
        False
    """
    # Similar rules as table names
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, column_name))


def validate_module_name(module_name: str) -> bool:
    """
    Validate a Python module name.

    Args:
        module_name: Module name to validate

    Returns:
        bool: True if module name is valid

    Examples:
        >>> validate_module_name("valid_module")
        True
        >>> validate_module_name("invalid-module")
        False
    """
    if not module_name or not isinstance(module_name, str):
        return False

    # Must be a valid identifier and not a keyword
    if not module_name.isidentifier() or keyword.iskeyword(module_name):
        return False

    # Additional module name constraints
    if '-' in module_name:
        return False

    return True
