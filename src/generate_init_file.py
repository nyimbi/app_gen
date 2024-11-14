"""
__init__.py Generator

This script generates an `__init__.py` file for a Python package, automatically
exporting all classes and functions defined in the package's modules.

The script takes the package directory as a command-line argument and generates
the `__init__.py` file in the specified directory.

Usage:
    python generate_init.py /path/to/package/directory
"""

import os
import re
import inspect
from pathlib import Path
import argparse

def generate_init_file(package_dir):
    """
    Generate the `__init__.py` file for the given Python package directory.

    The script iterates through all Python files in the package directory,
    extracts the classes and functions defined in each module, and writes them
    to the `__init__.py` file.

    Args:
        package_dir (str): The path to the Python package directory.
    """
    package_dir = Path(package_dir)
    init_file = package_dir / '__init__.py'

    with init_file.open('w') as f:
        f.write('"""Auto-generated `__init__.py` file."""\n\n')

        for py_file in package_dir.glob('*.py'):
            if py_file.name != '__init__.py':
                module_name = py_file.stem
                module_contents = extract_module_contents(py_file)
                if module_contents:
                    f.write(f'from .{module_name} import {", ".join(module_contents)}\n')

        f.write('\n')

def extract_module_contents(py_file):
    """
    Extract the names of the classes and functions defined in a Python module.

    The function ignores any members that start with an underscore (`_`), as they
    are typically considered private or internal.

    Args:
        py_file (Path): The path to the Python file.

    Returns:
        List[str]: A list of the names of the classes and functions defined in the module.
    """
    module_contents = []
    with py_file.open('r') as f:
        module_code = f.read()

    for line in module_code.split('\n'):
        match = re.match(r'^(class|def)\s+(\w+)', line.strip())
        if match:
            member_type, member_name = match.groups()
            if not member_name.startswith('_'):
                module_contents.append(member_name)

    return module_contents

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate __init__.py file')
    parser.add_argument('package_dir', type=str, help='Path to the Python package directory')
    args = parser.parse_args()

    if not os.path.isdir(args.package_dir):
        print(f"Error: {args.package_dir} is not a valid directory.")
        exit(1)

    generate_init_file(args.package_dir)
    print(f'__init__.py file generated in {args.package_dir}')
