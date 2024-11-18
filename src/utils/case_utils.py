#!/usr/bin/env python3
"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT

case_utils.py: Advanced case conversion and identifier management utilities.

A comprehensive module providing utilities for converting between different text case styles,
validating identifiers, and handling naming conventions commonly used in software development,
particularly for Flask-AppBuilder and database schema generation.

Key Features:
    1. Case Style Conversions:
        - PascalCase (e.g., HelloWorld)
        - camelCase (e.g., helloWorld)
        - snake_case (e.g., hello_world)
        - kebab-case (e.g., hello-world)
        - CONSTANT_CASE (e.g., HELLO_WORLD)
        - dot.case (e.g., hello.world)
        - Title Case (e.g., Hello World)

    2. Identifier Management:
        - Python identifier validation
        - Database identifier sanitization
        - Unique name generation
        - Length validation
        - Keyword handling

    3. Case Detection and Normalization:
        - Automatic case style detection
        - Case style normalization
        - Mixed case handling
        - Special character handling

    4. Text Processing:
        - Word splitting
        - Character replacement
        - Whitespace handling
        - Special case handling

Main Functions:
    Case Conversion:
        - to_pascal_case(): Convert to PascalCase
        - to_camel_case(): Convert to camelCase
        - to_snake_case(): Convert to snake_case
        - to_kebab_case(): Convert to kebab-case
        - to_constant_case(): Convert to CONSTANT_CASE
        - to_dot_case(): Convert to dot.case
        - to_title_case(): Convert to Title Case

    Direct Conversions:
        - snake_to_camel(): snake_case to camelCase
        - camel_to_snake(): camelCase to snake_case
        - snake_to_kebab(): snake_case to kebab-case
        - kebab_to_snake(): kebab-case to snake_case
        - camel_to_kebab(): camelCase to kebab-case
        - kebab_to_camel(): kebab-case to camelCase

    Identifier Management:
        - is_identifier(): Check valid Python identifier
        - make_identifier(): Create valid identifier
        - sanitize_name(): Sanitize database identifier
        - generate_unique_name(): Generate unique identifier
        - validate_identifier_length(): Check identifier length

    Utility Functions:
        - detect_case_style(): Detect text case style
        - normalize_case(): Normalize to target case
        - split_words(): Split text into words
        - convert_case(): Convert between case styles

Usage Examples:
    >>> from model_generator.utils.case_utils import to_snake_case, to_pascal_case

    # Convert to snake_case
    >>> to_snake_case('HelloWorld')
    'hello_world'

    # Convert to PascalCase
    >>> to_pascal_case('hello_world')
    'HelloWorld'

    # Generate valid identifier
    >>> make_identifier('2invalid-name')
    '_2invalid_name'

Features:
    - Comprehensive case style support
    - Consistent handling of edge cases
    - Support for special characters
    - Preservation of acronyms where appropriate
    - Database identifier compliance
    - Python keyword awareness

Dependencies:
    - re: Regular expression operations
    - keyword: Python keyword checking
    - typing: Type hints

Notes:
    - All functions handle empty input gracefully
    - Case conversions maintain consistency with common programming conventions
    - Database identifiers follow PostgreSQL naming conventions
    - Functions preserve meaningful character sequences
    - Special handling for programming language keywords

"""

import re
import keyword
from typing import List, Dict, Any, Optional, Union, Set, Tuple


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


def to_snake_case(text: str) -> str:
    """
    Convert a string to snake_case.

    Args:
        text (str): Input string (can be PascalCase, camelCase, or space separated)

    Returns:
        str: snake_case string

    Examples:
        >>> to_snake_case('HelloWorld')
        'hello_world'
        >>> to_snake_case('firstName')
        'first_name'
        >>> to_snake_case('API Endpoint')
        'api_endpoint'
    """
    if not text:
        return text

    # Add underscore before any uppercase letter and convert to lowercase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)

    # Replace spaces and hyphens with underscores, convert to lowercase
    return re.sub(r'[\s-]', '_', s2).lower()


def to_camel_case(text: str) -> str:
    """
    Convert a string to camelCase.

    Args:
        text (str): Input string (can be snake_case, PascalCase, or space separated)

    Returns:
        str: camelCase string

    Examples:
        >>> to_camel_case('hello_world')
        'helloWorld'
        >>> to_camel_case('HelloWorld')
        'helloWorld'
        >>> to_camel_case('first name')
        'firstName'
    """
    if not text:
        return text

    # First convert to PascalCase
    pascal = to_pascal_case(text)

    # Convert first character to lowercase
    return pascal[0].lower() + pascal[1:]

def to_kebab_case(text: str) -> str:
    """
    Convert a string to kebab-case.

    Args:
        text (str): Input string (any case style)

    Returns:
        str: kebab-case string

    Examples:
        >>> to_kebab_case('HelloWorld')
        'hello-world'
        >>> to_kebab_case('first_name')
        'first-name'
    """
    snake = to_snake_case(text)
    return snake.replace('_', '-')

def is_identifier(text: str) -> bool:
    """
    Check if a string is a valid Python identifier.

    Args:
        text (str): String to validate

    Returns:
        bool: True if string is a valid Python identifier, False otherwise

    Examples:
        >>> is_identifier('valid_name')
        True
        >>> is_identifier('2invalid')
        False
        >>> is_identifier('class')
        False
    """
    if not text or not isinstance(text, str):
        return False

    # Check if it's a Python keyword
    if keyword.iskeyword(text):
        return False

    # Check if it matches identifier pattern
    return text.isidentifier()

def camel_to_snake(text: str) -> str:
    """
    Convert CamelCase to snake_case.

    Args:
        text (str): CamelCase text

    Returns:
        str: snake_case text

    Examples:
        >>> camel_to_snake('CamelCase')
        'camel_case'
        >>> camel_to_snake('simpleXML')
        'simple_xml'
    """
    if not text:
        return ""

    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', text).lower()

def snake_to_camel(text: str, capitalize_first: bool = True) -> str:
    """
    Convert snake_case to CamelCase.

    Args:
        text (str): snake_case text
        capitalize_first (bool): Whether to capitalize first letter

    Returns:
        str: CamelCase text

    Examples:
        >>> snake_to_camel('snake_case')
        'SnakeCase'
        >>> snake_to_camel('snake_case', capitalize_first=False)
        'snakeCase'
    """
    if not text:
        return ""

    components = text.split('_')
    if capitalize_first:
        return ''.join(x.title() for x in components)
    return components[0] + ''.join(x.title() for x in components[1:])


def snake_to_kebab(text: str) -> str:
    """
    Convert snake_case to kebab-case.

    Args:
        text (str): snake_case text

    Returns:
        str: kebab-case text

    Examples:
        >>> snake_to_kebab('hello_world')
        'hello-world'
        >>> snake_to_kebab('api_endpoint_v1')
        'api-endpoint-v1'
        >>> snake_to_kebab('')
        ''
    """
    if not text:
        return ""

    # Simply replace underscores with hyphens
    return text.replace('_', '-')

def capitalize_words(words: list[str]) -> str:
    """
    Capitalizes each word in a list and joins them into a single string.

    :param words: A list of words to be capitalized.
    :return: A string with each word capitalized and joined.
    """
    return ''.join(word.capitalize() for word in words)


def snake_to_pascal(string: str, p=None) -> str:
    """
    Converts a snake_case string to PascalCase.

    :param string: The snake_case string to be converted.
    :return: The converted PascalCase string.

    Example:
    >>> snake_to_pascal('example_string')
    'ExampleString'

    Edge Case:
    >>> snake_to_pascal('')
    ''
    """
    if not isinstance(string, str):
        raise ValueError("Input must be a string.")
    if not string:
        return ''
    return capitalize_words(string.split('_'))


def snake_to_words_or_label(string: str, separator=" ") -> str:
    """
    Converts a snake_case string to a space-separated or other separator format.

    :param string: The snake_case string to be converted.
    :param separator: The separator to use between words (default is space).
    :return: The converted string with words separated by the chosen separator.

    Example:
    >>> snake_to_words_or_label('example_string', separator=' ')
    'Example String'
    """
    if not isinstance(string, str):
        raise ValueError("Input must be a string.")
    if not string:
        return ''
    return separator.join(word.capitalize() for word in string.split('_'))


def snake_to_words(string: str) -> str:
    """
    Converts a snake_case string to space-separated words.

    :param string: The snake_case string to be converted.
    :return: The converted string with space-separated words.
    """
    return snake_to_words_or_label(string, separator=" ")


def snake_to_label(string: str) -> str:
    """
    Converts a snake_case string to a label format (space-separated words with capitalized first letters).

    :param string: The snake_case string to be converted.
    :return: The converted label string.
    """
    return snake_to_words_or_label(string, separator=" ")



def camel_to_kebab(text: str) -> str:
    """
    Convert camelCase or PascalCase to kebab-case.

    Args:
        text (str): camelCase or PascalCase text

    Returns:
        str: kebab-case text

    Examples:
        >>> camel_to_kebab('helloWorld')
        'hello-world'
        >>> camel_to_kebab('APIEndpointV1')
        'api-endpoint-v1'
        >>> camel_to_kebab('SimpleXMLParser')
        'simple-xml-parser'
    """
    if not text:
        return ""

    # First convert to snake_case
    snake = camel_to_snake(text)
    # Then convert to kebab-case
    return snake_to_kebab(snake)

def kebab_to_snake(text: str) -> str:
    """
    Convert kebab-case to snake_case.

    Args:
        text (str): kebab-case text

    Returns:
        str: snake_case text

    Examples:
        >>> kebab_to_snake('hello-world')
        'hello_world'
        >>> kebab_to_snake('api-endpoint-v1')
        'api_endpoint_v1'
        >>> kebab_to_snake('')
        ''
    """
    if not text:
        return ""

    # Simply replace hyphens with underscores
    return text.replace('-', '_')

def kebab_to_camel(text: str, capitalize_first: bool = False) -> str:
    """
    Convert kebab-case to camelCase or PascalCase.

    Args:
        text (str): kebab-case text
        capitalize_first (bool): If True, converts to PascalCase; if False, to camelCase

    Returns:
        str: camelCase or PascalCase text

    Examples:
        >>> kebab_to_camel('hello-world')
        'helloWorld'
        >>> kebab_to_camel('api-endpoint-v1', capitalize_first=True)
        'ApiEndpointV1'
        >>> kebab_to_camel('simple-xml-parser')
        'simpleXmlParser'
    """
    if not text:
        return ""

    # First convert to snake_case
    snake = kebab_to_snake(text)
    # Then convert to camelCase or PascalCase
    return snake_to_camel(snake, capitalize_first)

def normalize_case(text: str, target_case: str = 'snake') -> str:
    """
    Normalize text to a specified case style.

    Args:
        text (str): Input text in any case style
        target_case (str): Target case style ('snake', 'kebab', 'camel', 'pascal')

    Returns:
        str: Text in target case style

    Examples:
        >>> normalize_case('helloWorld', 'kebab')
        'hello-world'
        >>> normalize_case('hello-world', 'pascal')
        'HelloWorld'
        >>> normalize_case('HelloWorld', 'snake')
        'hello_world'
    """
    if not text:
        return ""

    # First detect the current case style
    current_case = detect_case_style(text)

    # Convert to snake_case as an intermediate format
    if current_case == 'kebab':
        intermediate = kebab_to_snake(text)
    elif current_case in ['camel', 'pascal']:
        intermediate = camel_to_snake(text)
    else:
        intermediate = text if current_case == 'snake' else to_snake_case(text)

    # Convert to target case
    if target_case == 'kebab':
        return snake_to_kebab(intermediate)
    elif target_case == 'camel':
        return snake_to_camel(intermediate, capitalize_first=False)
    elif target_case == 'pascal':
        return snake_to_camel(intermediate, capitalize_first=True)
    else:  # snake case or default
        return intermediate

def is_kebab_case(text: str) -> bool:
    """
    Check if text is in valid kebab-case.

    Args:
        text (str): Text to check

    Returns:
        bool: True if text is in valid kebab-case

    Examples:
        >>> is_kebab_case('hello-world')
        True
        >>> is_kebab_case('HelloWorld')
        False
        >>> is_kebab_case('hello_world')
        False
    """
    if not text:
        return False

    # Check if text matches kebab-case pattern
    pattern = r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$'
    return bool(re.match(pattern, text))

def convert_case(text: str, source_case: str, target_case: str) -> str:
    """
    Convert text from one case style to another.

    Args:
        text (str): Input text
        source_case (str): Source case style ('snake', 'kebab', 'camel', 'pascal')
        target_case (str): Target case style ('snake', 'kebab', 'camel', 'pascal')

    Returns:
        str: Converted text

    Examples:
        >>> convert_case('hello-world', 'kebab', 'pascal')
        'HelloWorld'
        >>> convert_case('HelloWorld', 'pascal', 'kebab')
        'hello-world'
        >>> convert_case('hello_world', 'snake', 'camel')
        'helloWorld'
    """
    if not text:
        return ""

    # Convert to snake_case as intermediate format
    if source_case == 'kebab':
        intermediate = kebab_to_snake(text)
    elif source_case in ['camel', 'pascal']:
        intermediate = camel_to_snake(text)
    else:
        intermediate = text

    # Convert from snake_case to target case
    if target_case == 'kebab':
        return snake_to_kebab(intermediate)
    elif target_case == 'camel':
        return snake_to_camel(intermediate, capitalize_first=False)
    elif target_case == 'pascal':
        return snake_to_camel(intermediate, capitalize_first=True)
    else:  # snake case
        return intermediate


def make_identifier(text: str, suffix: Optional[str] = None) -> str:
    """
    Convert a string into a valid Python identifier.

    Args:
        text (str): String to convert
        suffix (Optional[str]): Optional suffix to append

    Returns:
        str: Valid Python identifier

    Examples:
        >>> make_identifier('2invalid')
        '_2invalid'
        >>> make_identifier('class')
        '_class'
        >>> make_identifier('hello-world', 'model')
        'hello_world_model'
    """
    if not text:
        return '_empty'

    # Convert to snake_case first
    identifier = to_snake_case(text)

    # Ensure it starts with a letter or underscore
    if not identifier[0].isalpha():
        identifier = f'_{identifier}'

    # Replace any invalid characters
    identifier = re.sub(r'[^a-zA-Z0-9_]', '_', identifier)

    # Add suffix if provided
    if suffix:
        identifier = f"{identifier}_{suffix}"

    # If it's a keyword, prefix with underscore
    if keyword.iskeyword(identifier):
        identifier = f'_{identifier}'

    return identifier


def split_words(text: str) -> List[str]:
    """
    Split a string into words regardless of its case style.

    Args:
        text (str): Input string (any case style)

    Returns:
        List[str]: List of words

    Examples:
        >>> split_words('helloWorld')
        ['hello', 'world']
        >>> split_words('hello_world')
        ['hello', 'world']
        >>> split_words('HelloWorld')
        ['hello', 'world']
    """
    if not text:
        return []

    # First convert to snake_case
    snake = to_snake_case(text)

    # Split on underscores and filter out empty strings
    return [word.lower() for word in snake.split('_') if word]



def to_constant_case(text: str) -> str:
    """
    Convert a string to CONSTANT_CASE.

    Args:
        text (str): Input string (any case style)

    Returns:
        str: CONSTANT_CASE string

    Examples:
        >>> to_constant_case('HelloWorld')
        'HELLO_WORLD'
        >>> to_constant_case('firstName')
        'FIRST_NAME'
    """
    snake = to_snake_case(text)
    return snake.upper()

def to_dot_case(text: str) -> str:
    """
    Convert a string to dot.case.

    Args:
        text (str): Input string (any case style)

    Returns:
        str: dot.case string

    Examples:
        >>> to_dot_case('HelloWorld')
        'hello.world'
        >>> to_dot_case('first_name')
        'first.name'
    """
    snake = to_snake_case(text)
    return snake.replace('_', '.')

def to_title_case(text: str) -> str:
    """
    Convert a string to Title Case.

    Args:
        text (str): Input string (any case style)

    Returns:
        str: Title Case string

    Examples:
        >>> to_title_case('HelloWorld')
        'Hello World'
        >>> to_title_case('first_name')
        'First Name'
    """
    words = split_words(text)
    return ' '.join(word.capitalize() for word in words)



def sanitize_name(text: str, max_length: int = 63) -> str:
    """
    Sanitize a name for use as a database identifier.

    Args:
        text (str): Input name
        max_length (int): Maximum allowed length

    Returns:
        str: Sanitized name

    Examples:
        >>> sanitize_name('User Account!!')
        'user_account'
        >>> sanitize_name('very_long_name', max_length=10)
        'very_long'
    """
    if not text:
        return 'unnamed'

    # Convert to snake_case and remove invalid characters
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', to_snake_case(text))

    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')

    # Truncate if necessary
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')

    return sanitized

def detect_case_style(text: str) -> str:
    """
    Detect the case style of a string.

    Args:
        text (str): Input string

    Returns:
        str: Detected case style

    Examples:
        >>> detect_case_style('HelloWorld')
        'pascal'
        >>> detect_case_style('hello_world')
        'snake'
        >>> detect_case_style('helloWorld')
        'camel'
    """
    if not text:
        return 'unknown'

    if '_' in text:
        return 'snake' if text.islower() else 'constant' if text.isupper() else 'mixed'
    elif '-' in text:
        return 'kebab'
    elif '.' in text:
        return 'dot'
    elif text.istitle():
        return 'title'
    elif text[0].isupper():
        return 'pascal'
    elif text[0].islower() and any(c.isupper() for c in text[1:]):
        return 'camel'
    else:
        return 'lower' if text.islower() else 'upper' if text.isupper() else 'mixed'

def validate_identifier_length(text: str, max_length: int = 63) -> bool:
    """
    Validate identifier length for database compatibility.

    Args:
        text (str): Input identifier
        max_length (int): Maximum allowed length

    Returns:
        bool: True if length is valid

    Examples:
        >>> validate_identifier_length('short_name')
        True
        >>> validate_identifier_length('very_long_name', max_length=10)
        False
    """
    return len(text) <= max_length

def generate_unique_name(base: str, existing_names: Set[str]) -> str:
    """
    Generate a unique name by appending a number if necessary.

    Args:
        base (str): Base name
        existing_names (Set[str]): Set of existing names

    Returns:
        str: Unique name

    Examples:
        >>> generate_unique_name('user', {'user', 'user_1'})
        'user_2'
    """
    if base not in existing_names:
        return base

    counter = 1
    while f"{base}_{counter}" in existing_names:
        counter += 1

    return f"{base}_{counter}"
