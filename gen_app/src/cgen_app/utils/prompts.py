import json
import os
from typing import Dict
import logging

logger = logging.getLogger("appgen")


class PromptTemplate:
    _templates: Dict[str, str] = {}

    @classmethod
    def load_templates(cls, template_file: str = None) -> None:
        from core.config import Config

        if template_file is None:
            template_file = Config.options.prompt_templates_file
        try:
            if os.path.exists(template_file):
                with open(template_file, "r") as f:
                    cls._templates = json.load(f)
                logger.info(f"Loaded prompt templates from {template_file}")
            else:
                cls._initialize_default_templates()
                with open(template_file, "w") as f:
                    json.dump(cls._templates, f, indent=2)
                logger.info(f"Created default prompt templates at {template_file}")
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {str(e)}")
            cls._initialize_default_templates()

    @classmethod
    def _initialize_default_templates(cls) -> None:
        cls._templates = {
            "plan": """
            Create a comprehensive development plan with:
            1. Component architecture (classes, functions, modules)
            2. File structure with logical organization
            3. Detailed component specifications with clear responsibilities
            4. Dependencies between components
            5. Testing requirements

            IMPORTANT: Your response must be ONLY valid JSON without explanations, commentary, or markdown formatting.

            Format your response as follows:
            {
              "architecture": { ... },
              "fileStructure": { ... },
              "components": [ ... ],
              "dependencies": [ ... ],
              "testing": { ... }
            }
            """,
            "structure": """
            Create detailed directory structure with:
            - File paths following Python best practices
            - Component types (class/function/module)
            - Component descriptions
            - Dependencies between components
            - Import requirements

            IMPORTANT: Your response must be ONLY valid JSON without explanations, commentary, or markdown formatting.

            Format your response as follows:
            {
              "structure": {
                "root": "project_root",
                "directories": [ ... ]
              },
              "files": [
                {
                  "path": "path/to/file.py",
                  "components": [ ... ],
                  "imports": [ ... ],
                  "description": "..."
                },
                ...
              ]
            }
            """,
            "component": """
            Generate Python {component_type} '{component_name}' for {file_path}:

            Description: {description}
            Requirements: {requirements}
            Dependencies: {dependencies}

            Include:
            - Type hints
            - Comprehensive docstrings
            - Proper error handling
            - Input validation
            - Performance considerations

            IMPORTANT FORMATTING INSTRUCTIONS:
            1. Return ONLY valid Python code without explanations or markdown formatting
            2. Do not include ```python or ``` markers around code
            3. Start directly with imports or the {component_type} definition
            4. End with just the code, no closing comments
            """,
            "test": """
            Create pytest cases for {component_type} '{component_name}' in {file_path}:

            Code:
            {component_code}

            Include:
            - Fixtures
            - Parameterization
            - Edge cases
            - Mocks for external dependencies
            - Assertions with clear failure messages
            - Coverage for both success and error paths

            IMPORTANT FORMATTING INSTRUCTIONS:
            1. Return ONLY valid Python code without explanations or markdown formatting
            2. Do not include ```python or ``` markers around code
            3. Start directly with imports or test function definitions
            4. End with just the code, no closing comments
            """,
        }

    @classmethod
    def get(cls, template_name: str, **kwargs) -> str:
        if not cls._templates:
            cls._initialize_default_templates()
        template = cls._templates.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        return template.format(**kwargs) if kwargs else template
