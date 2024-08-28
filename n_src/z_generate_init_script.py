"""
generate_mixins_init.py

This script generates a new __init__.py file for a mixins package by analyzing
all Python files in the 'mixins' directory. It extracts information about mixin
classes, generates lazy loading code, and creates a comprehensive __init__.py
file with proper imports, documentation, and utility functions.

The script includes safeguards such as archiving the old __init__.py file and
validating the newly generated content before replacing the existing file.

Usage:
    python generate_mixins_init.py

The script should be run from the directory containing the 'mixins' folder.

Dependencies:
    - Python 3.6+
    - Standard library modules: os, ast, inspect, hashlib, shutil, tempfile, importlib

Author: [Your Name]
Date: [Current Date]
Version: 1.0
"""

import os
import ast
import inspect
import hashlib
import shutil
import tempfile
import importlib.util
from datetime import datetime
from typing import List, Dict, Any

def archive_old_init(mixins_dir: str) -> None:
    """
    Archive the existing __init__.py file with a timestamp.

    Args:
        mixins_dir (str): Path to the directory containing the __init__.py file.

    This function creates a backup of the existing __init__.py file by copying it
    to a new file with a timestamp in the name. This allows for easy rollback
    if the new generation process encounters any issues.
    """
    init_path = os.path.join(mixins_dir, '__init__.py')
    if os.path.exists(init_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_path = os.path.join(mixins_dir, f'__init___{timestamp}.py.bak')
        shutil.copy2(init_path, archive_path)
        print(f"Archived old __init__.py to {archive_path}")

def validate_generated_init(content: str, mixins_dir: str) -> bool:
    """
    Validate the newly generated __init__.py content.

    Args:
        content (str): The content of the generated __init__.py file.
        mixins_dir (str): Path to the mixins directory.

    Returns:
        bool: True if the content is valid, False otherwise.

    This function performs several checks on the generated content:
    1. Syntax check using ast.parse
    2. Attempts to import the content as a module
    3. Checks for the presence of expected attributes and mixins
    4. Ensures all mixins are importable

    The content is written to a temporary file for testing to avoid
    modifying the actual __init__.py file during validation.
    """
    # Syntax check
    try:
        ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in generated __init__.py: {e}")
        return False

    # Write to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Try to import the temporary module
        spec = importlib.util.spec_from_file_location("temp_init", temp_path)
        temp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(temp_module)

        # Check if all expected attributes are present
        expected_attrs = ['__all__', '_mixin_registry', 'get_mixin_info', 'init_app', '__version__']
        for attr in expected_attrs:
            if not hasattr(temp_module, attr):
                print(f"Generated __init__.py is missing expected attribute: {attr}")
                return False

        # Check if all mixins are importable
        for mixin in temp_module.__all__:
            if not hasattr(temp_module, mixin):
                print(f"Generated __init__.py is missing mixin: {mixin}")
                return False

        print("Generated __init__.py passed all validation checks.")
        return True
    except Exception as e:
        print(f"Error validating generated __init__.py: {e}")
        return False
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)

def analyze_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Analyze a Python file and extract information about mixin classes.

    Args:
        filepath (str): Path to the Python file to analyze.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing information about each mixin class.

    This function uses the ast module to parse the Python file and extract
    information about classes that are likely to be mixins (either ending with
    'Mixin' or inheriting from a class with 'Mixin' in its name).
    """
    with open(filepath, 'r') as file:
        content = file.read()

    tree = ast.parse(content)
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    mixins = []
    for cls in classes:
        if cls.name.endswith('Mixin') or any('Mixin' in base.id for base in cls.bases if isinstance(base, ast.Name)):
            docstring = ast.get_docstring(cls)
            mixins.append({
                'name': cls.name,
                'docstring': docstring,
                'dependencies': [base.id for base in cls.bases if isinstance(base, ast.Name)],
                'methods': [node.name for node in cls.body if isinstance(node, ast.FunctionDef)]
            })

    return mixins

def generate_lazy_import(mixin: Dict[str, Any]) -> str:
    """
    Generate lazy import code for a mixin.

    Args:
        mixin (Dict[str, Any]): Dictionary containing information about the mixin.

    Returns:
        str: String containing the lazy import code for the mixin.

    This function creates a lazy loading mechanism for each mixin to avoid
    circular imports and improve performance of the __init__.py file.
    """
    return f"""
class Lazy{mixin['name']}:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            from .{mixin['file']} import {mixin['name']}
            cls._instance = {mixin['name']}
        return cls._instance

{mixin['name']} = Lazy{mixin['name']}()
"""

def generate_init_content(mixins: List[Dict[str, Any]]) -> str:
    """
    Generate content for the __init__.py file.

    Args:
        mixins (List[Dict[str, Any]]): List of dictionaries containing information about each mixin.

    Returns:
        str: The complete content for the __init__.py file.

    This function generates the entire content of the __init__.py file, including:
    - Module docstring with usage instructions and available mixins
    - Import statements
    - Mixin registry
    - Utility functions (get_mixin_info, init_app)
    - Lazy loading code for each mixin
    - Version information
    """
    content = f'''
    """
mixins/__init__.py

This module exposes all mixins from the mixins directory.
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Available mixins:
{chr(10).join(f"- {mixin['name']}: {mixin['docstring'].split(chr(10))[0] if mixin['docstring'] else 'No description'}" for mixin in mixins)}

Usage:
from mixins import {', '.join(mixin['name'] for mixin in mixins)}
"""

import importlib
from typing import Any, Dict, List, Callable

__all__ = {[mixin['name'] for mixin in mixins]}

_mixin_registry: Dict[str, Dict[str, Any]] = {{
{chr(10).join(f"    '{mixin['name']}': {{'docstring': {repr(mixin['docstring'])}, 'dependencies': {mixin['dependencies']}, 'methods': {mixin['methods']}}}," for mixin in mixins)}
}}

def get_mixin_info(mixin_name: str) -> Dict[str, Any]:
    """Get information about a specific mixin."""
    return _mixin_registry.get(mixin_name, {})

{chr(10).join(generate_lazy_import(mixin) for mixin in mixins)}

def init_app(app: Any, mixins: List[str] = None) -> None:
    """Initialize the mixins with the Flask app."""
    mixins_to_init = mixins or list(_mixin_registry.keys())
    for mixin_name in mixins_to_init:
        mixin = globals()[mixin_name]
        if hasattr(mixin, 'init_app'):
            mixin.init_app(app)

__version__ = "{generate_version(mixins)}"

'''
    return content

def generate_version(mixins: List[Dict[str, Any]]) -> str:
    """
    Generate a version number based on the current state of mixins.

    Args:
        mixins (List[Dict[str, Any]]): List of dictionaries containing information about each mixin.

    Returns:
        str: A version string based on a hash of the mixin names.

    This function creates a version number that will change whenever the set of
    mixins changes, providing a simple way to track changes to the mixins package.
    """
    hash_input = ''.join(sorted(m['name'] for m in mixins))
    return hashlib.md5(hash_input.encode()).hexdigest()[:8]

def main():
    """
    Main function to orchestrate the generation of the __init__.py file.

    This function performs the following steps:
    1. Scans the mixins directory for Python files
    2. Analyzes each file to extract mixin information
    3. Generates new content for __init__.py
    4. Archives the old __init__.py file
    5. Validates the new content
    6. If validation passes, writes the new content to __init__.py
    """
    mixins_dir = 'mixins'
    mixins = []

    # Scan and analyze mixin files
    for filename in os.listdir(mixins_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(mixins_dir, filename)
            file_mixins = analyze_file(filepath)
            for mixin in file_mixins:
                mixin['file'] = filename[:-3]  # Remove .py extension
            mixins.extend(file_mixins)

    # Generate new __init__.py content
    init_content = generate_init_content(mixins)

    # Archive the old __init__.py file
    archive_old_init(mixins_dir)

    # Validate the new content
    if validate_generated_init(init_content, mixins_dir):
        # Write the new content only if validation passes
        with open(os.path.join(mixins_dir, '__init__.py'), 'w') as init_file:
            init_file.write(init_content)
        print(f"Generated new __init__.py with {len(mixins)} mixins.")
    else:
        print("Generation of new __init__.py failed validation. The old file remains unchanged.")

if __name__ == '__main__':
    main()
