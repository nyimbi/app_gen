#!/usr/bin/env python3
"""
writer.py: Output management module.

This module contains the ModelWriter class, which is responsible for:
- Writing the generated model definitions to files
- Creating a 'models/' directory and writing each model to a file within it
- Creating an '__init__.py' file for the 'models/' directory
- Formatting the generated code using the Black code formatter
- Organizing and deduplicating the import statements
- Providing backup and versioning capabilities for the output files

The ModelWriter class uses the file system and various utility functions to handle
the output generation and management tasks.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List
from model_generator.utils.file_utils import (
    safe_write_file,
    create_backup
)
from model_generator.utils.string_utils import (
    normalize_line_endings
)
from model_generator.utils.file_utils import ensure_directory
from model_generator.utils.import_utils import (
    deduplicate_imports,
    format_imports,
    sort_imports,
)
from model_generator.config.base_config import GenerationConfig
from model_generator.exceptions import OutputWriterError
import black

class ModelWriter:
    """
    Responsible for writing the generated SQLAlchemy models to output files.

    Args:
        config (GenerationConfig): Configuration for the generation process.
    """

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.models_dir = self.output_dir / "models"

    def write_single_file(self, models: List[str]) -> None:
        """
        Write all generated models to a single output file.

        Args:
            models (List[str]): List of model definitions as strings.
        """
        try:
            output_file = self.output_dir / self.config.single_file_name
            self.create_output_directories()
            content = self.format_output("\n\n".join(models))
            safe_write_file(output_file, content, backup=self.config.create_backups)
        except Exception as e:
            raise OutputWriterError(f"Error writing models to single file: {e}") from e

    def write_multiple_files(self, models: Dict[str, str]) -> None:
        """
        Write each generated model to a separate output file.

        Args:
            models (Dict[str, str]): Dictionary mapping model names to their definitions.
        """
        try:
            self.create_output_directories()
            for model_name, model_definition in models.items():
                output_file = self.models_dir / f"{model_name.lower()}.py"
                content = self.format_output(model_definition)
                safe_write_file(output_file, content, backup=self.config.create_backups)

            # Create the __init__.py file for the models/ directory
            init_file = self.models_dir / "__init__.py"
            safe_write_file(init_file, "")
        except Exception as e:
            raise OutputWriterError(f"Error writing models to multiple files: {e}") from e

    def format_code(self, code: str) -> str:
        """
        Format the generated Python code using the Black code formatter.

        Args:
            code (str): The generated code to be formatted.

        Returns:
            str: The formatted code.
        """
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
            return normalize_line_endings(formatted_code)
        except Exception as e:
            raise OutputWriterError(f"Error formatting code: {e}") from e

    def organize_imports(self, code: str) -> str:
        """
        Organize and deduplicate the import statements in the generated code.

        Args:
            code (str): The generated code with import statements.

        Returns:
            str: The code with organized and deduplicated import statements.
        """
        try:
            imports = [line for line in code.split("\n") if line.startswith("import") or line.startswith("from")]
            sorted_imports = sort_imports(imports)
            deduped_imports = deduplicate_imports(sorted_imports)
            import_block = format_imports(deduped_imports)
            return import_block + "\n\n" + "\n".join(
                line for line in code.split("\n") if not line.startswith("import") and not line.startswith("from")
            )
        except Exception as e:
            raise OutputWriterError(f"Error organizing imports: {e}") from e

    def format_output(self, code: str) -> str:
        """
        Format the generated code, including organizing imports.

        Args:
            code (str): The generated code to be formatted.

        Returns:
            str: The formatted code.
        """
        formatted_code = self.format_code(code)
        return self.organize_imports(formatted_code)

    def create_output_directories(self) -> None:
        """
        Ensure that the output directory and the models/ directory exist and create them if necessary.
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.models_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OutputWriterError(f"Error creating output directories: {e}") from e

    def backup_existing(self, path: Path) -> None:
        """
        Create a backup of an existing file.

        Args:
            path (Path): Path to the file to be backed up.
        """
        try:
            create_backup(path)
        except Exception as e:
            raise OutputWriterError(f"Error creating backup for '{path}': {e}") from e
