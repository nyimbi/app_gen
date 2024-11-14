#!/usr/bin/env python3
"""
filename: setup.py
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT
File Description: Package setup configuration for installation.

This module is part of the SQLAlchemy Model Generator project.
"""

from typing import List, Dict, Any, Optional, Union, Set, Tuple
from pathlib import Path

from setuptools import setup, find_packages

setup(
    name="appgen-model-generator",
    version="0.1.0",
    author="Nyimbi Odero",
    author_email="nyimbi@gmail.com",
    description="Advanced Flask-Appbuilder SQLAlchemy model generator",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'SQLAlchemy>=1.4.0',
        'Jinja2>=3.0.0',
        'PyYAML>=5.4.0',
        'inflect>=5.3.0',
    ],
    entry_points={
        'console_scripts': [
            'generate-models=model_generator.cli:main',
        ],
    },
)
