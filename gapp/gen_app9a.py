#!/usr/bin/env python3
"""
Enhanced LLM Code Generator

This script generates structured Python projects using an LLM model via Ollama for code snippets,
tests, documentation, and more. It supports multiple project types with modular components and
deployment artifacts.

Features:
- Supports various project types (API, CLI, Microservices, etc.)
- Asynchronous code generation with concurrency control
- Automated testing and formatting
- Custom component and artifact generation
- Interactive model selection from available Ollama models
- Comprehensive error handling and logging

Author: [Your Name]
Date: March 03, 2025
Version: 2.0
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ollama  # External dependency for LLM generation
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer

# Configure logging with file output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("code_generator.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

# Default configurations
DEFAULT_LLM = "mistral-nemo:12b-instruct-2407-q8_0"
MAX_CONCURRENCY = 5
SUPPORTED_TYPES = [
    "flask_api",
    "flask_appbuilder",
    "flask_appbuilder_mixins",
    "flask_appbuilder_blueprints",
    "data_science",
    "fastrtc_app",
    "chatbot_app",
    "speech_to_text_app",
    "text_to_speech_app",
    "microservice",
    "cli_tool",
    "dashboard_app",
    "utilities_app",
    "general_app",
]

# Project templates
PYTHON_TEMPLATES: Dict[str, Any] = {
    "flask_api": {
        "description": "A Flask-based REST API with structured endpoints, authentication, and documentation.",
        "files": [
            {
                "name": "app.py",
                "description": "Main Flask application with configurations.",
            },
            {
                "name": "app/__init__.py",
                "description": "Application factory pattern implementation.",
            },
            {
                "name": "app/api/__init__.py",
                "description": "API package initialization.",
            },
            {"name": "app/api/routes.py", "description": "Main API route definitions."},
            {
                "name": "app/api/auth.py",
                "description": "Authentication and authorization handlers.",
            },
            {
                "name": "app/api/models.py",
                "description": "Data models for API resources.",
            },
            {
                "name": "app/api/schemas.py",
                "description": "Marshmallow schemas for serialization/validation.",
            },
            {
                "name": "app/api/utils.py",
                "description": "Utility functions for the API.",
            },
            {
                "name": "app/config.py",
                "description": "Configuration classes for different environments.",
            },
            {
                "name": "app/extensions.py",
                "description": "Flask extensions initialization.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for the Flask app with version constraints.",
            },
            {
                "name": "tests/conftest.py",
                "description": "Pytest fixtures and configuration.",
            },
            {
                "name": "tests/test_api.py",
                "description": "API endpoint tests with mocking.",
            },
            {
                "name": "tests/test_auth.py",
                "description": "Authentication functionality tests.",
            },
            {
                "name": "README.md",
                "description": "Project documentation with setup and usage instructions.",
            },
            {
                "name": "app/docs/swagger.json",
                "description": "OpenAPI/Swagger documentation for the API.",
            },
        ],
    },
    "flask_appbuilder": {
        "description": "A full Flask-AppBuilder application with models, mixins, blueprints, and an admin interface.",
        "files": [
            {
                "name": "app/__init__.py",
                "description": "Initialize Flask-AppBuilder with security and configuration.",
            },
            {
                "name": "app/models/__init__.py",
                "description": "Models package initialization.",
            },
            {
                "name": "app/models/base.py",
                "description": "Base model class with common attributes and methods.",
            },
            {
                "name": "app/models/user.py",
                "description": "User and role models with custom authentication methods.",
            },
            {
                "name": "app/models/business.py",
                "description": "Primary business domain models with SQLAlchemy constraints.",
            },
            {
                "name": "app/views/__init__.py",
                "description": "Views package initialization.",
            },
            {
                "name": "app/views/base.py",
                "description": "Base view classes with common configuration.",
            },
            {
                "name": "app/views/home.py",
                "description": "Index and dashboard view with custom widgets.",
            },
            {
                "name": "app/views/master_detail.py",
                "description": "Master-detail views with related model relationships.",
            },
            {
                "name": "app/views/charts.py",
                "description": "Chart views with data visualization components.",
            },
            {
                "name": "app/api/__init__.py",
                "description": "API package initialization.",
            },
            {
                "name": "app/api/base.py",
                "description": "Base API class with common authentication and error handling.",
            },
            {
                "name": "app/api/endpoints.py",
                "description": "REST API endpoints using Flask-AppBuilder's ModelRestApi.",
            },
            {
                "name": "app/security/__init__.py",
                "description": "Security package initialization.",
            },
            {
                "name": "app/security/manager.py",
                "description": "Custom security manager with extended authorization.",
            },
            {
                "name": "app/security/views.py",
                "description": "Custom security views for user management.",
            },
        ],
    },
    "flask_appbuilder_mixins": {
        "description": "A collection of mixins for Flask-AppBuilder applications.",
        "files": [
            {
                "name": "app/mixins/audit.py",
                "description": "Audit tracking mixin with timestamps and user references.",
            },
            {
                "name": "app/mixins/search.py",
                "description": "Full-text search mixin for model querying.",
            },
            {
                "name": "app/mixins/logging.py",
                "description": "Logging mixin for standardized log output.",
            },
            {
                "name": "README.md",
                "description": "Documentation for mixins usage and integration.",
            },
        ],
    },
    "flask_appbuilder_blueprints": {
        "description": "Blueprints for Flask-AppBuilder applications to modularize views and models.",
        "files": [
            {
                "name": "app/blueprints/sample_blueprint/__init__.py",
                "description": "Initialize the blueprint.",
            },
            {
                "name": "app/blueprints/sample_blueprint/views.py",
                "description": "Define blueprint-specific views.",
            },
            {
                "name": "app/blueprints/sample_blueprint/models.py",
                "description": "Define blueprint-specific models.",
            },
            {
                "name": "app/blueprints/sample_blueprint/forms.py",
                "description": "Define blueprint-specific forms and validations.",
            },
            {
                "name": "README.md",
                "description": "Documentation for blueprint integration.",
            },
        ],
    },
    "data_science": {
        "description": "A data science project template with notebooks and scripts.",
        "files": [
            {
                "name": "notebooks/analysis.ipynb",
                "description": "Main analysis notebook.",
            },
            {
                "name": "src/data_loader.py",
                "description": "Script for data loading and preprocessing.",
            },
            {
                "name": "src/model.py",
                "description": "Machine learning model definition.",
            },
            {
                "name": "src/utils.py",
                "description": "Utility functions for data processing and visualization.",
            },
            {"name": "requirements.txt", "description": "Project dependencies."},
            {"name": "README.md", "description": "Project overview and instructions."},
        ],
    },
    "fastrtc_app": {
        "description": "A fast real-time communication application using WebRTC.",
        "files": [
            {
                "name": "app.py",
                "description": "Main application integrating fastRTC functionalities.",
            },
            {
                "name": "app/rtc_manager.py",
                "description": "Manages real-time communications and signaling.",
            },
            {
                "name": "app/config.py",
                "description": "Configuration for RTC settings and endpoints.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for the fastRTC application.",
            },
            {
                "name": "tests/test_rtc.py",
                "description": "Unit tests for real-time communication components.",
            },
        ],
    },
    "chatbot_app": {
        "description": "A chatbot application with NLP capabilities.",
        "files": [
            {
                "name": "app.py",
                "description": "Main chatbot application handling user interactions.",
            },
            {
                "name": "app/nlp.py",
                "description": "Natural language processing and intent parsing.",
            },
            {
                "name": "app/responses.py",
                "description": "Module for generating chatbot responses.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for the chatbot application.",
            },
            {
                "name": "tests/test_chatbot.py",
                "description": "Test suite for chatbot functionalities.",
            },
        ],
    },
    "speech_to_text_app": {
        "description": "A speech-to-text application leveraging speech recognition libraries.",
        "files": [
            {
                "name": "app.py",
                "description": "Main application for processing audio input.",
            },
            {
                "name": "app/speech_recognizer.py",
                "description": "Module implementing speech recognition.",
            },
            {
                "name": "app/config.py",
                "description": "Configuration for speech recognition settings.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for the speech-to-text application.",
            },
            {
                "name": "tests/test_speech.py",
                "description": "Unit tests for speech recognition functionality.",
            },
        ],
    },
    "text_to_speech_app": {
        "description": "A text-to-speech application that converts text into audio output.",
        "files": [
            {
                "name": "app.py",
                "description": "Main application for text-to-speech conversion.",
            },
            {
                "name": "app/tts_engine.py",
                "description": "Module interfacing with TTS libraries.",
            },
            {"name": "app/config.py", "description": "Configuration for TTS settings."},
            {
                "name": "requirements.txt",
                "description": "Dependencies for the text-to-speech application.",
            },
            {
                "name": "tests/test_tts.py",
                "description": "Unit tests for TTS functionalities.",
            },
        ],
    },
    "microservice": {
        "description": "A microservice-based Python service designed for scalable deployment.",
        "files": [
            {"name": "app.py", "description": "Entry point for the microservice."},
            {
                "name": "app/routes.py",
                "description": "API endpoints for the microservice.",
            },
            {"name": "app/models.py", "description": "Data models and business logic."},
            {
                "name": "app/config.py",
                "description": "Configuration for the microservice.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for the microservice.",
            },
            {
                "name": "Dockerfile",
                "description": "Docker configuration for containerizing the microservice.",
            },
            {
                "name": "tests/test_service.py",
                "description": "Test suite for microservice functionalities.",
            },
        ],
    },
    "cli_tool": {
        "description": "A command-line interface tool with argument parsing and utilities.",
        "files": [
            {"name": "cli.py", "description": "Entry point for the CLI tool."},
            {"name": "utils.py", "description": "Utility functions for the CLI."},
            {
                "name": "requirements.txt",
                "description": "Dependencies for the CLI tool.",
            },
            {
                "name": "README.md",
                "description": "Documentation for installing and using the CLI tool.",
            },
            {
                "name": "tests/test_cli.py",
                "description": "Unit tests for CLI functionalities.",
            },
        ],
    },
    "dashboard_app": {
        "description": "A dashboard application built with Dash/Plotly.",
        "files": [
            {
                "name": "app.py",
                "description": "Main application entry point for the dashboard.",
            },
            {
                "name": "dashboard.py",
                "description": "Dashboard layout and callbacks implementation.",
            },
            {
                "name": "assets/style.css",
                "description": "Custom CSS for dashboard styling.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for the dashboard application.",
            },
            {
                "name": "README.md",
                "description": "Documentation for the dashboard application.",
            },
            {
                "name": "tests/test_dashboard.py",
                "description": "Test suite for dashboard functionalities.",
            },
        ],
    },
    "utilities_app": {
        "description": "A utility library with common helper functions.",
        "files": [
            {
                "name": "utils.py",
                "description": "Common utility functions for the project.",
            },
            {"name": "logger.py", "description": "Custom logging setup and handlers."},
            {
                "name": "config.py",
                "description": "Configuration management for the application.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for the utilities library.",
            },
            {
                "name": "README.md",
                "description": "Documentation for using the utilities.",
            },
            {
                "name": "tests/test_utils.py",
                "description": "Unit tests for utility functions.",
            },
        ],
    },
    "general_app": {
        "description": "A general-purpose Python application with dynamic structure.",
        "files": [
            {"name": "main.py", "description": "Main entry point for the application."},
            {
                "name": "config.py",
                "description": "Configuration settings for the application.",
            },
            {"name": "utils.py", "description": "General utility functions."},
            {"name": "requirements.txt", "description": "Project dependencies."},
            {"name": "README.md", "description": "Documentation for the application."},
            {
                "name": "tests/test_main.py",
                "description": "Unit tests for core functionalities.",
            },
        ],
    },
}

# Artifact templates
ARTIFACT_TEMPLATES: Dict[str, Any] = {
    "docker_compose": {
        "description": "Docker Compose configuration for multi-container deployment.",
        "files": [
            {
                "name": "docker-compose.yml",
                "description": "Docker Compose file for orchestrating services.",
            },
            {
                "name": ".env.example",
                "description": "Example environment variables file.",
            },
        ],
    },
    "kubernetes": {
        "description": "Kubernetes deployment configuration.",
        "files": [
            {
                "name": "deployment.yaml",
                "description": "Kubernetes deployment configuration.",
            },
            {
                "name": "service.yaml",
                "description": "Kubernetes service configuration.",
            },
            {
                "name": "configmap.yaml",
                "description": "Configuration Map for environment variables.",
            },
        ],
    },
    "ci_cd": {
        "description": "CI/CD pipeline configuration.",
        "files": [
            {
                "name": ".github/workflows/test.yml",
                "description": "GitHub Actions workflow for testing.",
            },
        ],
    },
}


def print_code(code: str) -> None:
    """Prints syntax-highlighted Python code to the terminal."""
    try:
        highlighted_code = highlight(code, PythonLexer(), Terminal256Formatter())
        print('-' * 20)
        print(highlighted_code, end="")
        print('-' * 20)
    except Exception as e:
        logging.warning(f"Failed to highlight code: {e}")
        print(code)


def extract_code_block(response_text: str, language: str = "python") -> str:
    """Extracts code block from text enclosed in triple backticks."""
    marker = f"```{language}"
    try:
        if marker in response_text:
            content = response_text.split(marker, 1)[1]
            return content.split("```", 1)[0].strip()
        elif "```" in response_text:
            return response_text.split("```", 1)[1].split("```", 1)[0].strip()
        return response_text.strip()
    except IndexError:
        logging.warning("Failed to extract code block, returning raw text")
        return response_text.strip()


def detect_project_type(prompt: str) -> str:
    """Determines the most suitable project type based on user prompt."""
    prompt_lower = prompt.lower()
    type_mappings = {
        "fastrtc": "fastrtc_app",
        "chatbot": "chatbot_app",
        "speech to text|s2t|speech recognition": "speech_to_text_app",
        "text to speech|tts": "text_to_speech_app",
        "microservice": "microservice",
        "cli|command line|terminal": "cli_tool",
        "dashboard": "dashboard_app",
        "mixin.*flask appbuilder": "flask_appbuilder_mixins",
        "blueprint.*flask appbuilder": "flask_appbuilder_blueprints",
        "utility|utilities": "utilities_app",
        "data science|machine learning|ml": "data_science",
        "api|rest": "flask_api",
        "flask appbuilder": "flask_appbuilder",
    }
    for pattern, project_type in type_mappings.items():
        if any(keyword in prompt_lower for keyword in pattern.split("|")):
            return project_type
    return "general_app"


def create_project_directory(
    project_name: str,
    blueprint_name: Optional[str] = None,
    include_docs: bool = False,
    include_static: bool = False,
) -> None:
    """Creates project directory structure with additional common directories."""
    try:
        directories = [
            project_name,
            f"{project_name}/app",
            f"{project_name}/tests",
            f"{project_name}/logs",
        ]
        if blueprint_name:
            directories.append(f"{project_name}/app/blueprints/{blueprint_name}")
        if include_docs:
            directories.append(f"{project_name}/docs")
        if include_static:
            directories.extend(
                [
                    f"{project_name}/app/static/css",
                    f"{project_name}/app/static/js",
                    f"{project_name}/app/static/img",
                ]
            )
        directories.extend(
            [
                f"{project_name}/app/templates",
                f"{project_name}/app/models",
                f"{project_name}/app/views",
                f"{project_name}/config",
            ]
        )

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

        # Create configuration files
        with open(f"{project_name}/pyproject.toml", "w") as f:
            f.write(
                """
[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88
"""
            )

        with open(f"{project_name}/.editorconfig", "w") as f:
            f.write("[*.py]\nindent_style = space\nindent_size = 4\n")

        with open(f"{project_name}/.gitignore", "w") as f:
            f.write(
                """
# Byte-compiled files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
dist/
*.egg-info/

# Virtual environments
venv/
env/
ENV/

# IDE and OS files
.vscode/
.idea/
.DS_Store
"""
            )

        logging.info(f"Project directory structure created for {project_name}")
    except OSError as e:
        logging.error(f"Failed to create project directory: {e}")
        raise


def ensure_dev_dependencies(project_name: str) -> None:
    """Ensures development dependencies are properly configured."""
    try:
        dev_deps = [
            "black>=23.0",
            "isort>=5.0",
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "mypy>=1.0",
            "flake8>=6.0",
            "autoflake>=2.0",
            "pylint>=2.17",
        ]
        with open(f"{project_name}/requirements-dev.txt", "w") as f:
            f.write("# Development dependencies\n" + "\n".join(dev_deps))

        req_file = f"{project_name}/requirements.txt"
        if not os.path.exists(req_file):
            with open(req_file, "w") as f:
                f.write("# Main project dependencies\n")
        with open(req_file, "a") as f:
            f.write("\n# Development dependencies\n-r requirements-dev.txt\n")
        logging.info(f"Development dependencies configured for {project_name}")
    except IOError as e:
        logging.error(f"Failed to write dependencies: {e}")
        raise


def check_tools_installed() -> bool:
    """Verifies that required formatting tools are installed."""
    required_tools = {"black": "black", "isort": "isort", "autoflake": "autoflake"}
    missing_tools = []
    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            missing_tools.append(required_tools[tool])
    if missing_tools:
        logging.warning("Missing tools: %s", ", ".join(missing_tools))
        install = input("Install missing tools? (y/N): ").strip().lower() == "y"
        if install:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + missing_tools, check=True
                )
                logging.info("Tools installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install tools: {e}")
                return False
    return True


def get_available_models() -> List[str]:
    """Retrieves list of available Ollama models."""
    try:
        models_list = ollama.list()
        return [model["name"] for model in models_list.get("models", [])]
    except Exception as e:
        logging.warning(f"Failed to fetch models: {e}")
        return [DEFAULT_LLM]


async def identify_functions(
    file_info: Dict[str, str], model: str
) -> List[Dict[str, Any]]:
    """Identifies functions needed for a file using LLM."""
    if (
        os.path.splitext(file_info["name"])[1] not in [".py", ""]
        or "test_" in file_info["name"]
    ):
        return []

    prompt = f"""Analyze the purpose of this file and list the functions it should contain.

File Name: {file_info["name"]}
Purpose: {file_info["description"]}

Provide output in JSON format:
{{
    "functions": [
        {{
            "name": "function_name",
            "description": "What this function does",
            "parameters": [{{"name": "param_name", "type": "param_type", "description": "param description"}}],
            "return_type": "return type",
            "return_description": "what function returns"
        }}
    ]
}}
"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ollama.generate(model=model, prompt=prompt)
        )
        json_str = (
            extract_code_block(response["response"], "json")
            or response["response"].strip()
        )
        function_data = json.loads(json_str)
        return (
            function_data["functions"]
            if isinstance(function_data, dict)
            else function_data
        )
    except (json.JSONDecodeError, KeyError) as e:
        logging.warning(f"Function identification failed for {file_info['name']}: {e}")
        return [
            {
                "name": "main",
                "description": f"Main function for {file_info['name']}",
                "parameters": [],
                "return_type": "None",
                "return_description": "None",
            }
        ]


async def generate_function(
    function_info: Dict[str, Any], file_info: Dict[str, str], model: str
) -> str:
    """Generates an individual Python function using the LLM."""
    prompt = f"""Generate a complete Python function for the file {file_info["name"]}.

Function Name: {function_info["name"]}
Purpose: {function_info["description"]}
Parameters: {json.dumps(function_info.get("parameters", []))}
Return Type: {function_info.get("return_type", "None")}
Return Description: {function_info.get("return_description", "None")}
File Purpose: {file_info["description"]}

Ensure:
- PEP8 compliance
- Detailed docstrings with type annotations
- Error handling and modular design
- Use of type hints
"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ollama.generate(model=model, prompt=prompt)
        )
        code = extract_code_block(response["response"], "python")
        print_code(code)
        logging.info(f"Generated function: {function_info['name']}")
        return code
    except Exception as e:
        logging.error(f"Failed to generate function {function_info['name']}: {e}")
        return (
            f"def {function_info['name']}():\n    # TODO: Implement function\n    pass"
        )


async def generate_file_imports(
    file_info: Dict[str, str], functions: List[Dict[str, Any]], model: str
) -> str:
    """Generates import statements for a Python file."""
    if os.path.splitext(file_info["name"])[1] not in [".py", ""]:
        return ""
    prompt = f"""Generate Python import statements for:

File Name: {file_info["name"]}
File Purpose: {file_info["description"]}
Functions: {json.dumps(functions, indent=2)}

Provide only the import statements."""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ollama.generate(model=model, prompt=prompt)
        )
        imports = extract_code_block(response["response"], "python")
        return imports + "\n" if imports else ""
    except Exception as e:
        logging.warning(f"Failed to generate imports for {file_info['name']}: {e}")
        return ""


async def generate_tests_for_function(
    function_info: Dict[str, Any], file_info: Dict[str, str], model: str
) -> str:
    """Generates pytest test cases for a function."""
    prompt = f"""Generate comprehensive pytest test cases for:

Function Name: {function_info["name"]}
Purpose: {function_info["description"]}
Parameters: {json.dumps(function_info.get("parameters", []))}
Return Type: {function_info.get("return_type", "None")}
File Purpose: {file_info["description"]}

Ensure:
- Use of pytest fixtures
- Coverage of normal and edge cases
- At least 3 test functions"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ollama.generate(model=model, prompt=prompt)
        )
        return extract_code_block(response["response"], "python")
    except Exception as e:
        logging.warning(f"Failed to generate tests for {function_info['name']}: {e}")
        return f"# TODO: Add tests for {function_info['name']}"


async def generate_tests_for_file(
    file_info: Dict[str, str],
    functions: List[Dict[str, Any]],
    project_name: str,
    model: str,
    blueprint_name: Optional[str] = None,
) -> None:
    """Generates a test file for a Python file."""
    file_ext = os.path.splitext(file_info["name"])[1]
    if "test_" in file_info["name"] or file_ext not in [".py", ""]:
        return

    source_file_path = file_info["name"].replace(
        "<blueprint_name>", blueprint_name or "blueprint"
    )
    test_file_name = (
        f"test_{os.path.splitext(os.path.basename(source_file_path))[0]}.py"
    )
    test_file_path = os.path.join(
        "tests", os.path.dirname(source_file_path), test_file_name
    )
    full_test_path = os.path.join(project_name, test_file_path)
    os.makedirs(os.path.dirname(full_test_path), exist_ok=True)

    imports = "import pytest\n"
    module_path = (
        source_file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
    )
    imports += f"from {module_path} import *\n\n"

    if not functions:
        with open(full_test_path, "w") as f:
            f.write(
                f'"""\nTests for {file_info["name"]}\n"""\n\n{imports}# TODO: Add test cases\n'
            )
        return

    fixtures_prompt = f"""Generate pytest fixtures for:
File: {file_info["name"]}
Purpose: {file_info["description"]}
Functions: {json.dumps(functions, indent=2)}"""
    response = await asyncio.get_event_loop().run_in_executor(
        None, lambda: ollama.generate(model=model, prompt=fixtures_prompt)
    )
    fixtures_code = extract_code_block(response["response"], "python")

    test_functions = await asyncio.gather(
        *[generate_tests_for_function(func, file_info, model) for func in functions]
    )
    all_test_code = imports + fixtures_code + "\n\n" + "\n\n".join(test_functions)
    formatted_code = await format_code(all_test_code)

    with open(full_test_path, "w") as f:
        f.write(
            f'"""\nTests for {file_info["name"]}: {file_info["description"]}\n"""\n\n{formatted_code}'
        )
    logging.info(f"Test file {test_file_path} created")


async def review_code(file_content: str, file_info: Dict[str, str], model: str) -> str:
    """Reviews and improves generated code."""
    if os.path.splitext(file_info["name"])[1] not in [".py", ""]:
        return file_content
    prompt = f"""Review this Python code for {file_info["name"]}:
# ```python
{file_content}
Check for correctness, best practices, security, and completeness. Return improved code."""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ollama.generate(model=model, prompt=prompt)
        )
        return extract_code_block(response["response"], "python")
    except Exception as e:
        logging.warning(f"Code review failed for {file_info['name']}: {e}")
        return file_content


async def format_code(code_content: str) -> str:
    """Formats code using autoflake, isort, and black."""
    if not code_content.strip():
        return code_content
    temp_file = Path("temp_format_file.py")
    try:
        temp_file.write_text(code_content)
        for cmd in [
            ["autoflake", "--remove-all-unused-imports", "--in-place", str(temp_file)],
            ["isort", str(temp_file)],
            ["black", "-q", str(temp_file)],
        ]:
            subprocess.run(cmd, check=True, capture_output=True)
        return temp_file.read_text()
    except Exception as e:
        logging.warning(f"Code formatting failed: {e}")
        return code_content
    finally:
        if temp_file.exists():
            temp_file.unlink()


async def generate_non_python_file(
    file_info: Dict[str, str],
    project_name: str,
    model: str,
    blueprint_name: Optional[str] = None,
) -> None:
    """Generates content for non-Python files."""
    file_path = os.path.join(
        project_name,
        file_info["name"].replace("<blueprint_name>", blueprint_name or "blueprint"),
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_ext = os.path.splitext(file_info["name"])[1]
    prompts = {
        ".html": f"Generate HTML for {file_info['name']}: {file_info['description']}",
        ".css": f"Generate CSS for {file_info['name']}: {file_info['description']}",
        ".js": f"Generate JavaScript for {file_info['name']}: {file_info['description']}",
        ".json": f"Generate JSON for {file_info['name']}: {file_info['description']}",
        ".md": f"Generate Markdown for {file_info['name']}: {file_info['description']}",
    }
    prompt = prompts.get(
        file_ext,
        f"Generate content for {file_info['name']} ({file_ext}): {file_info['description']}",
    )

    response = await asyncio.get_event_loop().run_in_executor(
        None, lambda: ollama.generate(model=model, prompt=prompt)
    )
    content = (
        extract_code_block(response["response"], file_ext[1:])
        or response["response"].strip()
    )
    with open(file_path, "w") as f:
        f.write(content)
    logging.info(f"File {file_info['name']} created")


async def generate_code_async(
    file_info: Dict[str, str],
    project_name: str,
    model: str,
    blueprint_name: Optional[str] = None,
) -> None:
    """Generates code for a file."""
    file_path = os.path.join(
        project_name,
        file_info["name"].replace("<blueprint_name>", blueprint_name or "blueprint"),
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_ext = os.path.splitext(file_info["name"])[1]

    if file_ext not in [".py", ""]:
        if "requirements.txt" in file_path:
            prompt = f"Generate requirements.txt for {project_name}: {file_info['description']}"
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ollama.generate(model=model, prompt=prompt)
            )
            with open(file_path, "w") as f:
                f.write(
                    extract_code_block(response["response"])
                    or response["response"].strip()
                )
        else:
            await generate_non_python_file(
                file_info, project_name, model, blueprint_name
            )
        return

        functions = await identify_functions(file_info, model)
        imports = await generate_file_imports(file_info, functions, model)
        generated_functions = await asyncio.gather(
            *[generate_function(func, file_info, model) for func in functions]
        )
        raw_code = imports + "\n\n" + "\n\n".join(generated_functions)
        reviewed_code = await review_code(raw_code, file_info, model)
        formatted_code = await format_code(reviewed_code)

        with open(file_path, "w") as f:
            f.write(f'"""\n{file_info["description"]}\n"""\n\n{formatted_code}')
        await generate_tests_for_file(
            file_info, functions, project_name, model, blueprint_name
        )
        logging.info(f"File {file_info['name']} created")


async def process_files_concurrently(
    files: List[Dict[str, str]],
    project_name: str,
    model: str,
    blueprint_name: Optional[str] = None,
    max_concurrency: int = MAX_CONCURRENCY,
) -> None:
    """Processes multiple files concurrently."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_task(file_info: Dict[str, str]) -> None:
        async with semaphore:
            await generate_code_async(file_info, project_name, model, blueprint_name)

    await asyncio.gather(*(sem_task(f) for f in files))


async def generate_readme(
    project_name: str, project_type: str, description: str, model: str
) -> None:
    """Generates README.md."""
    prompt = f"""Generate README.md for:
Project Type: {project_type} ({PYTHON_TEMPLATES[project_type]["description"]})
Description: {description}
Include overview, installation, usage, structure, testing."""
    response = await asyncio.get_event_loop().run_in_executor(
        None, lambda: ollama.generate(model=model, prompt=prompt)
    )
    with open(f"{project_name}/README.md", "w") as f:
        f.write(
            extract_code_block(response["response"], "markdown")
            or response["response"].strip()
        )
    logging.info("README.md created")


async def generate_makefile(project_name: str) -> None:
    """Generates Makefile."""
    content = """# Makefile for Python project
.PHONY: setup test lint format clean
setup:
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
test:
    pytest tests/ --cov=app
lint:
    flake8 app/ tests/
    mypy app/ tests/
format:
    isort app/ tests/
    black app/ tests/
clean:
    rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info pycache *.pyc"""
    with open(f"{project_name}/Makefile", "w") as f:
        f.write(content)
    logging.info("Makefile created")


async def generate_gitignore(project_name: str) -> None:
    """Generates .gitignore."""
    content = """# Byte-compiled files
pycache/
*.py[cod]
*$py.class
C extensions
*.so
Distribution / packaging
.Python
build/
dist/
*.egg-info/
Environments
.env
.venv
env/
venv/
ENV/
IDE files
.idea/
.vscode/
.DS_Store"""
    with open(f"{project_name}/.gitignore", "w") as f:
        f.write(content)
    logging.info(".gitignore created")


async def generate_conftest(project_name: str, model: str) -> None:
    """Generates conftest.py."""
    prompt = """Generate conftest.py with pytest fixtures and configuration."""
    response = await asyncio.get_event_loop().run_in_executor(
        None, lambda: ollama.generate(model=model, prompt=prompt)
    )
    formatted_code = await format_code(
        extract_code_block(response["response"], "python")
    )
    with open(f"{project_name}/tests/conftest.py", "w") as f:
        f.write(f'"""\nPytest fixtures\n"""\n\n{formatted_code}')
    logging.info("conftest.py created")


async def generate_setup_py(
    project_name: str, project_type: str, description: str, model: str
) -> None:
    """Generates setup.py."""
    prompt = f"""Generate setup.py for:
Project Name: {project_name}
Type: {project_type}
Description: {description}"""
    response = await asyncio.get_event_loop().run_in_executor(
        None, lambda: ollama.generate(model=model, prompt=prompt)
    )
    formatted_code = await format_code(
        extract_code_block(response["response"], "python")
    )
    with open(f"{project_name}/setup.py", "w") as f:
        f.write(formatted_code)
    logging.info("setup.py created")


async def generate_component(component_info: Dict[str, str], model: str) -> str:
    """Generates a project component."""
    prompt = f"""Generate Python module for:
Component: {component_info["name"]}
Description: {component_info["description"]}
Ensure PEP8 and type hints."""
    response = await asyncio.get_event_loop().run_in_executor(
        None, lambda: ollama.generate(model=model, prompt=prompt)
    )
    return extract_code_block(response["response"], "python")


async def generate_artifact(
    artifact_info: Dict[str, str], project_name: str, model: str
) -> None:
    """Generates an artifact file."""
    file_path = os.path.join(project_name, artifact_info["name"])
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    prompt = f"""Generate {artifact_info["name"]}:
Description: {artifact_info["description"]}"""
    response = await asyncio.get_event_loop().run_in_executor(
        None, lambda: ollama.generate(model=model, prompt=prompt)
    )
    with open(file_path, "w") as f:
        f.write(
            extract_code_block(response["response"]) or response["response"].strip()
        )
    logging.info(f"Artifact {artifact_info['name']} created")


async def generate_project(
    project_name: str,
    project_type: str,
    description: str,
    model: str,
    blueprint_name: Optional[str] = None,
    include_docs: bool = False,
    include_static: bool = False,
    components: Optional[List[Dict[str, str]]] = None,
    artifacts: Optional[List[str]] = None,
) -> None:
    """Generates complete project."""
    try:
        create_project_directory(
            project_name, blueprint_name, include_docs, include_static
        )
        ensure_dev_dependencies(project_name)
        template = PYTHON_TEMPLATES.get(project_type, PYTHON_TEMPLATES["general_app"])
        await process_files_concurrently(
            template["files"], project_name, model, blueprint_name
        )

        await asyncio.gather(
            generate_readme(project_name, project_type, description, model),
            generate_makefile(project_name),
            generate_gitignore(project_name),
            generate_conftest(project_name, model),
            generate_setup_py(project_name, project_type, description, model),
        )

        if components:
            for comp in components:
                code = await generate_component(comp, model)
                with open(f"{project_name}/app/{comp['name']}.py", "w") as f:
                    f.write(await format_code(code))

        if artifacts:
            for artifact_type in artifacts:
                for file_info in ARTIFACT_TEMPLATES[artifact_type]["files"]:
                    await generate_artifact(file_info, project_name, model)

        if check_tools_installed():
            subprocess.run(["isort", project_name], check=False)
            subprocess.run(["black", project_name], check=False)

        logging.info(f"Project {project_name} generated")
    except Exception as e:
        logging.error(f"Project generation failed: {e}")
        raise


def main() -> None:
    """Main entry point."""
    print("\n=== Python Project Generator ===")
    print("Supported types:", ", ".join(SUPPORTED_TYPES))

    try:
        description = input("\nDescribe your project: ").strip()
        if not description:
            raise ValueError("Description required")

        project_type = detect_project_type(description)
        print(f"\nDetected type: {project_type}")

        project_name = (
            input("Project name (default: my_project): ").strip() or "my_project"
        )

        models = get_available_models()
        print("\nAvailable models:", ", ".join(models))
        model = input(f"Select model (default: {DEFAULT_LLM}): ").strip() or DEFAULT_LLM
        if model not in models:
            print(f"Warning: {model} not found, using {DEFAULT_LLM}")
            model = DEFAULT_LLM

        blueprint_name = input("Blueprint name (optional): ").strip() or None
        include_docs = input("Include docs? (y/N): ").lower() == "y"
        include_static = input("Include static files? (y/N): ").lower() == "y"

        components = []
        if input("Add components? (y/N): ").lower() == "y":
            while True:
                name = input("Component name (or Enter to finish): ").strip()
                if not name:
                    break
                desc = input("Description: ").strip()
                components.append({"name": name, "description": desc})

        artifacts = []
        if input("Generate artifacts? (y/N): ").lower() == "y":
            print("Available artifacts:", ", ".join(ARTIFACT_TEMPLATES.keys()))
            selected = input("Select artifacts (comma-separated): ").split(",")
            artifacts = [a.strip() for a in selected if a.strip() in ARTIFACT_TEMPLATES]

        asyncio.run(
            generate_project(
                project_name,
                project_type,
                description,
                model,
                blueprint_name,
                include_docs,
                include_static,
                components,
                artifacts,
            )
        )

        print(f"\n✅ Project generated in '{project_name}'")
        print("Next steps:")
        print(f"  cd {project_name}")
        print("  pip install -r requirements.txt")
        print("  make test")

    except Exception as e:
        logging.error(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
