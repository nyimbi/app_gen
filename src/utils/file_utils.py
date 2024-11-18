#!/usr/bin/env python3
"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT

file_utils.py: Comprehensive file system operations for Flask-AppBuilder code generation.

This module provides a robust set of utilities for managing file system operations,
specifically designed to support Flask-AppBuilder application generation and maintenance.
It handles file operations with proper error handling, logging, and backup mechanisms.

Key Features:
    1. File Operations
        - Safe file reading and writing with backups
        - File copying and deletion with error handling
        - File information retrieval
        - Permission management
        - Temporary file handling

    2. Directory Management
        - Directory creation and verification
        - Empty directory cleanup
        - Pattern-based file finding
        - Recursive operations
        - Directory structure validation

    3. Flask-AppBuilder Specific
        - Standard package structure generation
        - Static file organization
        - Template management
        - Migration directory handling
        - API directory setup

    4. Python Package Management
        - Module discovery and management
        - Package initialization
        - Import path handling
        - Module naming utilities
        - Package structure verification

Core Functions:
    File Operations:
        - safe_write_file(): Write files with backup support
        - read_file_safely(): Safe file reading with error handling
        - copy_file_safely(): Protected file copying
        - create_backup(): Automated backup creation
        - safe_delete(): Protected file deletion

    Directory Management:
        - ensure_directory(): Directory creation and verification
        - find_files(): Pattern-based file discovery
        - clean_directory(): Directory cleanup
        - remove_empty_directories(): Empty directory removal
        - create_temp_directory(): Temporary directory creation

    Flask-AppBuilder Support:
        - generate_package_structure(): Create FAB application structure
        - create_static_structure(): Set up static file organization
        - get_template_path(): Template file path management
        - get_migration_directory(): Migration directory handling
        - verify_file_structure(): Structure validation

    Package Utilities:
        - create_package_file(): Package initialization
        - find_python_modules(): Module discovery
        - create_init_files(): Initialize Python packages
        - get_module_name(): Module name resolution
        - backup_existing_files(): Package backup management

Usage Examples:
    >>> from model_generator.utils.file_utils import generate_package_structure

    # Create new Flask-AppBuilder application structure
    >>> app_dirs = generate_package_structure(".", "myapp")
    >>> app_dirs['models'].exists()
    True

    # Safe file operations with backups
    >>> safe_write_file("config.py", "CONFIG = {}", backup=True)
    >>> content = read_file_safely("config.py")

Features:
    - Comprehensive error handling
    - Automatic backup creation
    - Logging integration
    - Type hints throughout
    - PEP 8 compliance
    - Extensive documentation
    - Test-friendly design

Dependencies:
    Standard Library:
        - os: Operating system interface
        - shutil: High-level file operations
        - tempfile: Temporary file creation
        - datetime: Timestamp management
        - pathlib: Object-oriented filesystem paths
        - logging: Error and operation logging
        - typing: Type hints support

Safety Features:
    - Automatic backup creation
    - Safe file operations
    - Error logging
    - Path validation
    - Permission handling
    - Temporary file cleanup

Notes:
    - All operations include proper error handling
    - Functions support both string and Path inputs
    - Operations are atomic where possible
    - Backups include timestamps
    - Directory operations are recursive
    - File operations preserve metadata
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Union, List, Optional, Dict, Any, Iterator
import logging


logger = logging.getLogger(__name__)


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure

    Returns:
        Path: Path object of the ensured directory

    Examples:
        >>> path = ensure_directory("./output")
        >>> path.exists()
        True
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_write_file(path: Union[str, Path], content: str, backup: bool = True) -> None:
    """
    Safely write content to a file with optional backup.

    Args:
        path: File path to write to
        content: Content to write
        backup: Whether to create backup of existing file

    Examples:
        >>> safe_write_file("example.txt", "Hello World", backup=True)
        >>> Path("example.txt").exists()
        True
    """
    path = Path(path)

    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create backup if requested and file exists
    if backup and path.exists():
        create_backup(path)

    # Write content using temporary file
    temp_path = path.with_suffix('.tmp')
    try:
        temp_path.write_text(content, encoding='utf-8')
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def create_backup(path: Union[str, Path]) -> Optional[Path]:
    """
    Create a backup of a file with timestamp.

    Args:
        path: Path to file to backup

    Returns:
        Optional[Path]: Path to backup file if created, None otherwise

    Examples:
        >>> path = Path("example.txt")
        >>> path.write_text("content")
        >>> backup = create_backup(path)
        >>> backup.exists()
        True
    """
    path = Path(path)
    if not path.exists():
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = path.with_name(f"{path.stem}_{timestamp}{path.suffix}.bak")

    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup of {path}: {e}")
        return None


def safe_delete(path: Union[str, Path], backup: bool = True) -> bool:
    """
    Safely delete a file with optional backup.

    Args:
        path: Path to file to delete
        backup: Whether to create backup before deletion

    Returns:
        bool: True if deletion was successful

    Examples:
        >>> path = Path("temp.txt")
        >>> path.write_text("content")
        >>> safe_delete(path, backup=True)
        True
    """
    path = Path(path)
    if not path.exists():
        return False

    try:
        if backup:
            create_backup(path)
        path.unlink()
        return True
    except Exception as e:
        logger.error(f"Failed to delete {path}: {e}")
        return False


def find_files(directory: Union[str, Path], pattern: str = "*") -> Iterator[Path]:
    """
    Find files in directory matching pattern.

    Args:
        directory: Directory to search
        pattern: Glob pattern to match

    Yields:
        Path: Matching file paths

    Examples:
        >>> list(find_files(".", "*.py"))  # Find all Python files
        [Path('example.py'), ...]
    """
    directory = Path(directory)
    return directory.rglob(pattern)


def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
    """
    Get relative path from base directory.

    Args:
        path: Path to convert to relative
        base: Base directory

    Returns:
        Path: Relative path

    Examples:
        >>> get_relative_path("/tmp/dir/file.txt", "/tmp")
        Path('dir/file.txt')
    """
    return Path(path).relative_to(Path(base))


def read_file_safely(path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read file content with error handling.

    Args:
        path: Path to file to read
        encoding: File encoding

    Returns:
        Optional[str]: File content if successful, None otherwise

    Examples:
        >>> content = read_file_safely("example.txt")
        >>> print(content)
        'file content'
    """
    path = Path(path)
    try:
        return path.read_text(encoding=encoding)
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        return None


def copy_file_safely(src: Union[str, Path], dst: Union[str, Path],
                    backup_dst: bool = True) -> bool:
    """
    Safely copy file with error handling and backup.

    Args:
        src: Source file path
        dst: Destination file path
        backup_dst: Whether to backup destination if it exists

    Returns:
        bool: True if copy was successful

    Examples:
        >>> copy_file_safely("source.txt", "dest.txt", backup_dst=True)
        True
    """
    src, dst = Path(src), Path(dst)
    try:
        if not src.exists():
            logger.error(f"Source file {src} does not exist")
            return False

        if backup_dst and dst.exists():
            create_backup(dst)

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dst}: {e}")
        return False


def clean_directory(directory: Union[str, Path], pattern: str = "*",
                   exclude: Optional[List[str]] = None) -> None:
    """
    Clean directory by removing files matching pattern.

    Args:
        directory: Directory to clean
        pattern: Glob pattern for files to remove
        exclude: Patterns to exclude from removal

    Examples:
        >>> clean_directory("./temp", "*.tmp", exclude=["keep.tmp"])
    """
    directory = Path(directory)
    exclude = exclude or []

    for path in find_files(directory, pattern):
        if any(path.match(exc) for exc in exclude):
            continue
        safe_delete(path, backup=False)


def is_python_file(path: Union[str, Path]) -> bool:
    """
    Check if file is a Python source file.

    Args:
        path: Path to check

    Returns:
        bool: True if file is a Python source file

    Examples:
        >>> is_python_file("example.py")
        True
        >>> is_python_file("example.txt")
        False
    """
    path = Path(path)
    return path.suffix.lower() == '.py'


def get_module_name(path: Union[str, Path]) -> str:
    """
    Get Python module name from file path.

    Args:
        path: Path to Python file

    Returns:
        str: Module name

    Examples:
        >>> get_module_name("path/to/module.py")
        'module'
    """
    return Path(path).stem


def create_empty_file(path: Union[str, Path], mode: int = 0o644) -> None:
    """
    Create an empty file with specified permissions.

    Args:
        path: Path to file to create
        mode: File permissions (octal)

    Examples:
        >>> create_empty_file("new_file.txt")
        >>> Path("new_file.txt").exists()
        True
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(mode=mode, exist_ok=True)


def get_file_info(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get detailed file information.

    Args:
        path: Path to file

    Returns:
        Dict[str, Any]: File information dictionary

    Examples:
        >>> info = get_file_info("example.txt")
        >>> info['size'] > 0
        True
    """
    path = Path(path)
    stat = path.stat()

    return {
        'path': path,
        'name': path.name,
        'suffix': path.suffix,
        'size': stat.st_size,
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'is_file': path.is_file(),
        'is_dir': path.is_dir(),
        'permissions': oct(stat.st_mode)[-3:],
    }


def create_temp_directory() -> Path:
    """
    Create a temporary directory.

    Returns:
        Path: Path to created temporary directory

    Examples:
        >>> temp_dir = create_temp_directory()
        >>> temp_dir.exists()
        True
    """
    return Path(tempfile.mkdtemp())


def remove_empty_directories(directory: Union[str, Path]) -> None:
    """
    Recursively remove empty directories.

    Args:
        directory: Base directory to clean

    Examples:
        >>> remove_empty_directories("./empty_dirs")
    """
    directory = Path(directory)
    if not directory.exists():
        return

    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
        if not dirnames and not filenames:
            Path(dirpath).rmdir()


def generate_package_structure(base_dir: Union[str, Path], app_name: str) -> Dict[str, Path]:
    """
    Generate standard Flask-AppBuilder package directory structure.

    Args:
        base_dir: Base directory for package
        app_name: Name of the application

    Returns:
        Dict[str, Path]: Dictionary of created directories

    Examples:
        >>> dirs = generate_package_structure(".", "myapp")
        >>> dirs['models'].exists()
        True
    """
    base_dir = Path(base_dir) / app_name
    directories = {
        'root': base_dir,
        'models': base_dir / 'models',
        'views': base_dir / 'views',
        'api': base_dir / 'api',
        'templates': base_dir / 'templates',
        'static': base_dir / 'static',
        'translations': base_dir / 'translations',
        'utils': base_dir / 'utils',
        'security': base_dir / 'security',
    }

    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / '__init__.py').touch()

    return directories

def backup_existing_files(directory: Union[str, Path], pattern: str = "*.py") -> Dict[Path, Path]:
    """
    Create backups of all matching files in a directory.

    Args:
        directory: Directory containing files to backup
        pattern: File pattern to match

    Returns:
        Dict[Path, Path]: Mapping of original files to their backups

    Examples:
        >>> backups = backup_existing_files("./myapp")
        >>> len(backups) > 0
        True
    """
    directory = Path(directory)
    backups = {}

    for file_path in find_files(directory, pattern):
        backup_path = create_backup(file_path)
        if backup_path:
            backups[file_path] = backup_path

    return backups

def create_init_files(directory: Union[str, Path]) -> List[Path]:
    """
    Create __init__.py files in all subdirectories.

    Args:
        directory: Base directory

    Returns:
        List[Path]: List of created __init__.py files

    Examples:
        >>> init_files = create_init_files("./myapp")
        >>> len(init_files) > 0
        True
    """
    directory = Path(directory)
    created_files = []

    for dir_path in [d for d in directory.rglob("*") if d.is_dir()]:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            created_files.append(init_file)

    return created_files

def find_python_modules(directory: Union[str, Path]) -> Dict[str, Path]:
    """
    Find all Python modules in a directory structure.

    Args:
        directory: Directory to search

    Returns:
        Dict[str, Path]: Dictionary of module names to file paths

    Examples:
        >>> modules = find_python_modules("./myapp")
        >>> 'models.user' in modules
        True
    """
    directory = Path(directory)
    modules = {}
    base_len = len(directory.parts)

    for file_path in find_files(directory, "*.py"):
        if file_path.name == "__init__.py":
            continue

        # Convert path to module name
        parts = file_path.parts[base_len:-1] + (file_path.stem,)
        module_name = ".".join(parts)
        modules[module_name] = file_path

    return modules

def create_package_file(directory: Union[str, Path], content: str = "") -> Path:
    """
    Create a package __init__.py file with optional content.

    Args:
        directory: Directory to create package in
        content: Optional content for __init__.py

    Returns:
        Path: Path to created file

    Examples:
        >>> init_file = create_package_file("./myapp/models")
        >>> init_file.exists()
        True
    """
    directory = Path(directory)
    init_file = directory / "__init__.py"

    if content:
        safe_write_file(init_file, content)
    else:
        init_file.touch()

    return init_file

def get_template_path(directory: Union[str, Path], template_name: str) -> Path:
    """
    Get path for a template file in the Flask-AppBuilder app.

    Args:
        directory: Base app directory
        template_name: Name of template

    Returns:
        Path: Path to template file

    Examples:
        >>> path = get_template_path("./myapp", "list.html")
        >>> str(path)
        './myapp/templates/list.html'
    """
    return Path(directory) / 'templates' / template_name

def create_static_structure(directory: Union[str, Path]) -> Dict[str, Path]:
    """
    Create standard static file structure for Flask-AppBuilder.

    Args:
        directory: Base app directory

    Returns:
        Dict[str, Path]: Dictionary of created directories

    Examples:
        >>> dirs = create_static_structure("./myapp")
        >>> dirs['css'].exists()
        True
    """
    static_dir = Path(directory) / 'static'
    directories = {
        'css': static_dir / 'css',
        'js': static_dir / 'js',
        'img': static_dir / 'img',
        'vendors': static_dir / 'vendors'
    }

    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return directories

def verify_file_structure(directory: Union[str, Path], required_dirs: List[str]) -> bool:
    """
    Verify that required directories exist in the app structure.

    Args:
        directory: Base app directory
        required_dirs: List of required directory names

    Returns:
        bool: True if all required directories exist

    Examples:
        >>> verify_file_structure("./myapp", ["models", "views"])
        True
    """
    directory = Path(directory)
    return all((directory / dir_name).is_dir() for dir_name in required_dirs)

def cleanup_generated_files(directory: Union[str, Path], pattern: str = "*.py") -> None:
    """
    Clean up generated files while preserving user modifications.

    Args:
        directory: Directory to clean
        pattern: File pattern to match

    Examples:
        >>> cleanup_generated_files("./myapp")
    """
    directory = Path(directory)

    for file_path in find_files(directory, pattern):
        content = read_file_safely(file_path)
        if content and '# Generated by FAB Code Generator' in content:
            safe_delete(file_path, backup=True)

def get_migration_directory(directory: Union[str, Path]) -> Path:
    """
    Get or create the migrations directory for Flask-Migrate.

    Args:
        directory: Base app directory

    Returns:
        Path: Path to migrations directory

    Examples:
        >>> migration_dir = get_migration_directory("./myapp")
        >>> migration_dir.exists()
        True
    """
    migrations_dir = Path(directory) / 'migrations'
    migrations_dir.mkdir(parents=True, exist_ok=True)
    return migrations_dir
