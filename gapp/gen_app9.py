#!/usr/bin/env python3
"""
Enhanced LLM Code Generator

This script generates a structured Python project using an LLM model for generating code
snippets, tests, documentation, and more. It now supports multiple project types including:
- Flask-based REST APIs, Flask-AppBuilder applications (including mixins and blueprints),
- Data science projects,
- fastRTC applications,
- Chatbots,
- Speech-to-text and Text-to-speech applications,
- Microservices,
- CLI tools,
- Dashboard applications,
- Utility libraries, and a general-purpose application.

For a general application not otherwise specified, the code generator will decide the
appropriate files and functions to generate based on LLM prompts.

The design leverages asynchronous I/O ([PEP 492](https://www.python.org/dev/peps/pep-0492/)),
modular decomposition, and best practices in code formatting (Black, isort, autoflake).

Author: [Your Name]
Date: [Date]
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
from typing import Any, Dict, List, Optional

import ollama  # External dependency for LLM generation
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Default LLM model
DEFAULT_LLM = "mistral-nemo:12b-instruct-2407-q8_0"

# Updated Python Project Templates including new types and components
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
        "description": "A collection of mixins for Flask-AppBuilder applications, providing audit, search, and logging functionality.",
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
    "cli_tool": {
        "description": "A command-line interface (CLI) tool with argument parsing, logging, and utility functions.",
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
        "description": "A dashboard application built with Dash/Plotly for interactive data visualization.",
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
        "description": "A utility library containing common helper functions, logging, and configuration management.",
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
    "data_science": {
        "description": "A data science project template with notebooks, data processing scripts, and visualization components.",
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
        "description": "A fast real-time communication (fastRTC) application using WebRTC and asynchronous processing.",
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
        "description": "A chatbot application with NLP capabilities for conversational AI.",
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
        "description": "A command-line interface (CLI) tool with argument parsing, logging, and utility functions.",
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
        "description": "A dashboard application built with Dash/Plotly for interactive data visualization.",
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
        "description": "A utility library containing common helper functions, logging, and configuration management.",
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
        "description": "A general-purpose Python application where the code generator decides the optimal structure, files, and functions based on the prompt.",
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


def print_code(code: str) -> None:
    """Prints syntax-highlighted Python code to the terminal."""
    try:
        highlighted_code = highlight(code, PythonLexer(), Terminal256Formatter())
        print(highlighted_code, end="")  # Prevent extra newline
    except Exception:
        print(code)


def extract_code_block(response_text: str, language: str = "python") -> str:
    """Extracts a code block from a response text enclosed in triple backticks."""
    marker = f"```{language}"
    if marker in response_text:
        try:
            content = response_text.split(marker, 1)[1]
            code = content.split("```", 1)[0].strip()
            return code
        except IndexError:
            return response_text.strip()
    if "```" in response_text:
        try:
            return response_text.split("```", 1)[1].split("```", 1)[0].strip()
        except IndexError:
            return response_text.strip()
    return response_text.strip()


def detect_project_type(prompt: str) -> str:
    """Determines the most suitable project type based on the user prompt."""
    prompt_lower = prompt.lower()
    if "fastrtc" in prompt_lower:
        return "fastrtc_app"
    elif "chatbot" in prompt_lower:
        return "chatbot_app"
    elif "speech to text" in prompt_lower or "speech recognition" in prompt_lower:
        return "speech_to_text_app"
    elif "text to speech" in prompt_lower or "tts" in prompt_lower:
        return "text_to_speech_app"
    elif "microservice" in prompt_lower:
        return "microservice"
    elif (
        "cli" in prompt_lower
        or "command line" in prompt_lower
        or "terminal" in prompt_lower
    ):
        return "cli_tool"
    elif "dashboard" in prompt_lower:
        return "dashboard_app"
    elif "mixin" in prompt_lower and "flask appbuilder" in prompt_lower:
        return "flask_appbuilder_mixins"
    elif "blueprint" in prompt_lower and "flask appbuilder" in prompt_lower:
        return "flask_appbuilder_blueprints"
    elif "utility" in prompt_lower or "utilities" in prompt_lower:
        return "utilities_app"
    elif "data science" in prompt_lower:
        return "data_science"
    elif "api" in prompt_lower:
        return "flask_api"
    elif "flask appbuilder" in prompt_lower or "blueprint" in prompt_lower:
        return "flask_appbuilder"
    else:
        return "general_app"  # Default to a general application type


def create_project_directory(
    project_name: str,
    blueprint_name: Optional[str] = None,
    include_docs: bool = False,
    include_static: bool = False,
) -> None:
    """Creates the main project directory structure."""
    os.makedirs(project_name, exist_ok=True)
    os.makedirs(os.path.join(project_name, "app"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "tests"), exist_ok=True)

    if blueprint_name:
        os.makedirs(
            os.path.join(project_name, f"app/blueprints/{blueprint_name}"),
            exist_ok=True,
        )
    if include_docs:
        os.makedirs(os.path.join(project_name, "docs"), exist_ok=True)
    if include_static:
        os.makedirs(os.path.join(project_name, "app/static/css"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "app/static/js"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "app/static/img"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "app/templates"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "app/models"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "app/routes"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "config"), exist_ok=True)

    with open(os.path.join(project_name, "pyproject.toml"), "w") as f:
        f.write("""
[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88
""")
    with open(os.path.join(project_name, ".gitignore"), "w") as f:
        f.write("""
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
Thumbs.db
""")
    logging.info("Project directory structure created successfully.")


def ensure_dev_dependencies(project_name: str) -> None:
    """Adds development dependencies to requirements-dev.txt and references them in requirements.txt."""
    dev_requirements = [
        "black",
        "isort",
        "pytest",
        "pytest-cov",
        "mypy",
        "flake8",
        "autoflake",
    ]
    with open(os.path.join(project_name, "requirements-dev.txt"), "w") as f:
        f.write("\n".join(dev_requirements))
    req_main_file = os.path.join(project_name, "requirements.txt")
    if not os.path.exists(req_main_file):
        with open(req_main_file, "w") as f:
            f.write("# Main project dependencies\n")
    with open(req_main_file, "a") as f:
        f.write("\n\n# For development dependencies, see requirements-dev.txt\n")


def check_tools_installed() -> bool:
    """Verifies that required formatting tools are installed."""
    required_tools = {"black": "black", "isort": "isort", "autoflake": "autoflake"}
    missing_tools = []
    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=False)
        except FileNotFoundError:
            missing_tools.append(required_tools[tool])
    if missing_tools:
        logging.warning("Missing required tools: %s", ", ".join(missing_tools))
        install = input("Install missing tools now? (y/N): ").strip().lower() == "y"
        if install:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + missing_tools, check=True
                )
                logging.info("Required tools installed successfully.")
            except subprocess.CalledProcessError:
                logging.error(
                    "Failed to install tools. Please install manually: pip install %s",
                    " ".join(missing_tools),
                )
        return False
    return True


async def identify_functions(
    file_info: Dict[str, str], model: str = DEFAULT_LLM
) -> List[Dict[str, Any]]:
    """Identifies functions for a Python file using the LLM."""
    file_ext = os.path.splitext(file_info["name"])[1]
    if file_ext not in [".py", ""] or file_info["name"].startswith("test_"):
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
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    try:
        response_text = response["response"]
        json_str = (
            extract_code_block(response_text, language="json") or response_text.strip()
        )
        function_data = json.loads(json_str)
        if isinstance(function_data, dict) and "functions" in function_data:
            return function_data["functions"]
        elif isinstance(function_data, list):
            return function_data
        else:
            logging.warning("Unexpected response format for %s", file_info["name"])
            return []
    except (json.JSONDecodeError, KeyError) as e:
        logging.warning(
            "Error parsing function list for %s: %s", file_info["name"], str(e)
        )
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
    function_info: Dict[str, Any], file_info: Dict[str, str], model: str = DEFAULT_LLM
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
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    code = extract_code_block(response["response"], language="python")
    logging.info("Generated function: %s", function_info["name"])
    return code


async def generate_file_imports(
    file_info: Dict[str, str], functions: List[Dict[str, Any]], model: str = DEFAULT_LLM
) -> str:
    """Generates import statements for a Python file using the LLM."""
    file_ext = os.path.splitext(file_info["name"])[1]
    if file_ext not in [".py", ""]:
        return ""
    prompt = f"""Generate Python import statements for a file with the following details:

File Name: {file_info["name"]}
File Purpose: {file_info["description"]}

Functions in the file:
{json.dumps(functions, indent=2)}

Provide only the import statements.
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    imports = extract_code_block(response["response"], language="python")
    if imports and not imports.endswith("\n"):
        imports += "\n"
    return imports


async def generate_tests_for_function(
    function_info: Dict[str, Any], file_info: Dict[str, str], model: str = DEFAULT_LLM
) -> str:
    """Generates pytest test cases for an individual function using the LLM."""
    prompt = f"""Generate comprehensive pytest test cases for the following function:

Function Name: {function_info["name"]}
Function Purpose: {function_info["description"]}
Parameters: {json.dumps(function_info.get("parameters", []))}
Return Type: {function_info.get("return_type", "None")}
Return Description: {function_info.get("return_description", "None")}
File Purpose: {file_info["description"]}

Ensure:
- Use of pytest fixtures where appropriate
- Coverage of normal and edge cases
- Clear test naming and assertions
Generate at least 3 test functions.
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    test_code = extract_code_block(response["response"], language="python")
    logging.info("Generated tests for function: %s", function_info["name"])
    return test_code


async def generate_tests_for_file(
    file_info: Dict[str, str],
    functions: List[Dict[str, Any]],
    project_name: str,
    model: str = DEFAULT_LLM,
    blueprint_name: Optional[str] = None,
) -> None:
    """Generates a test file for a given Python file using the LLM."""
    file_ext = os.path.splitext(file_info["name"])[1]
    if "test_" in file_info["name"] or file_ext not in [".py", ""]:
        return
    source_file_path = file_info["name"].replace(
        "<blueprint_name>", blueprint_name if blueprint_name else "blueprint"
    )
    base_name, ext = os.path.splitext(os.path.basename(source_file_path))
    test_file_name = f"test_{base_name}{ext if ext else '.py'}"
    dir_path = os.path.dirname(source_file_path)
    test_file_path = (
        os.path.join("tests", dir_path, test_file_name)
        if dir_path
        else os.path.join("tests", test_file_name)
    )
    full_test_path = os.path.join(project_name, test_file_path)
    os.makedirs(os.path.dirname(full_test_path), exist_ok=True)

    imports = "import pytest\n"
    module_path = (
        source_file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
    )
    if module_path.startswith("app."):
        imports += f"from {module_path} import *\n"
    else:
        imports += f"import {module_path}\n\n"

    if not functions:
        with open(full_test_path, "w") as f:
            f.write(
                f'"""\nTests for {file_info["name"]}: {file_info["description"]}\n"""\n\n'
            )
            f.write(imports)
            f.write("# TODO: Add test cases\n")
        logging.info("Skeleton test file %s created successfully.", test_file_path)
        return

    fixtures_prompt = f"""Generate pytest fixtures for testing the file:

File Name: {file_info["name"]}
File Purpose: {file_info["description"]}
Functions: {json.dumps(functions, indent=2)}

Create appropriate fixtures including mocks if needed.
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=fixtures_prompt)
        )
    fixtures_code = extract_code_block(response["response"], language="python")

    test_functions = []
    for func in functions:
        test_functions.append(await generate_tests_for_function(func, file_info, model))

    all_test_code = imports + fixtures_code + "\n\n" + "\n\n".join(test_functions)
    formatted_code = await format_code(all_test_code)
    with open(full_test_path, "w") as f:
        f.write(
            f'"""\nTests for {file_info["name"]}: {file_info["description"]}\n"""\n\n'
        )
        f.write(formatted_code)
    logging.info("Test file %s created successfully.", test_file_path)


async def review_code(
    file_content: str, file_info: Dict[str, str], model: str = DEFAULT_LLM
) -> str:
    """Reviews and improves generated code using the LLM."""
    file_ext = os.path.splitext(file_info["name"])[1]
    if file_ext not in [".py", ""]:
        return file_content
    prompt = f"""Review the following Python code for {file_info["name"]} implementing {file_info["description"]}.
Check for correctness, best practices, security issues, and completeness.

```python
{file_content}
```

Return only the improved code without explanations.
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    reviewed_code = extract_code_block(response["response"], language="python")
    return reviewed_code


async def format_code(code_content: str) -> str:
    """Formats code using autoflake, isort, and black."""
    if not code_content.strip():
        return code_content
    temp_file = Path("temp_format_file.py")
    try:
        temp_file.write_text(code_content)
        try:
            subprocess.run(
                [
                    "autoflake",
                    "--remove-all-unused-imports",
                    "--in-place",
                    str(temp_file),
                ],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        try:
            subprocess.run(["isort", str(temp_file)], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        try:
            subprocess.run(
                ["black", "-q", str(temp_file)], check=True, capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        formatted_content = temp_file.read_text()
        return formatted_content
    finally:
        if temp_file.exists():
            temp_file.unlink()


async def generate_non_python_file(
    file_info: Dict[str, str],
    project_name: str,
    model: str = DEFAULT_LLM,
    blueprint_name: Optional[str] = None,
) -> None:
    """Generates content for non-Python files (HTML, CSS, JS, JSON, Markdown, etc.) using the LLM."""
    file_path = os.path.join(
        project_name,
        file_info["name"].replace(
            "<blueprint_name>", blueprint_name if blueprint_name else "blueprint"
        ),
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_ext = os.path.splitext(file_info["name"])[1]
    if file_ext == ".html":
        prompt = f"""Generate HTML content for file:
File Name: {file_info["name"]}
File Purpose: {file_info["description"]}
Create a well-structured HTML document with head and body tags.
"""
    elif file_ext == ".css":
        prompt = f"""Generate CSS content for file:
File Name: {file_info["name"]}
File Purpose: {file_info["description"]}
Create organized CSS with appropriate selectors and comments.
"""
    elif file_ext == ".js":
        prompt = f"""Generate JavaScript content for file:
File Name: {file_info["name"]}
File Purpose: {file_info["description"]}
Create well-structured JavaScript code with functions and comments.
"""
    elif file_ext == ".json":
        prompt = f"""Generate JSON content for file:
File Name: {file_info["name"]}
File Purpose: {file_info["description"]}
Create valid JSON with appropriate structure and sample data.
"""
    elif file_ext == ".md":
        prompt = f"""Generate Markdown content for file:
File Name: {file_info["name"]}
File Purpose: {file_info["description"]}
Create structured Markdown with headings and lists.
"""
    else:
        prompt = f"""Generate content for file:
File Name: {file_info["name"]}
File Extension: {file_ext}
File Purpose: {file_info["description"]}
Create content appropriate for this file type.
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    content = (
        extract_code_block(response["response"], language=file_ext[1:])
        or response["response"].strip()
    )
    with open(file_path, "w") as f:
        f.write(content)
    logging.info("File %s created successfully.", file_info["name"])


async def generate_code_async(
    file_info: Dict[str, str],
    project_name: str,
    model: str,
    blueprint_name: Optional[str] = None,
) -> None:
    """Generates code for a file by combining function identification, generation, review, and test generation."""
    file_path = os.path.join(
        project_name,
        file_info["name"].replace(
            "<blueprint_name>", blueprint_name if blueprint_name else "blueprint"
        ),
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_ext = os.path.splitext(file_info["name"])[1]
    if file_ext not in [".py", ""]:
        if file_ext == ".txt" and "requirements.txt" in file_path:
            logging.info("Generating %s...", file_info["name"])
            prompt = f"""Generate a comprehensive requirements.txt for project {project_name}.
Project Description: {file_info["description"]}
List production dependencies with version constraints.
"""
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(
                    pool, lambda: ollama.generate(model=model, prompt=prompt)
                )
            requirements = (
                extract_code_block(response["response"]) or response["response"].strip()
            )
            with open(file_path, "w") as f:
                f.write(requirements)
            logging.info("File %s created successfully.", file_info["name"])
            return
        else:
            await generate_non_python_file(
                file_info, project_name, model, blueprint_name
            )
            return
    logging.info("Identifying functions for %s...", file_info["name"])
    functions = await identify_functions(file_info, model)
    if not functions:
        logging.warning(
            "No functions identified for %s. Using default.", file_info["name"]
        )
        functions = [
            {
                "name": "main",
                "description": f"Main function for {file_info['name']}",
                "parameters": [],
                "return_type": "None",
                "return_description": "None",
            }
        ]
    logging.info("Generating imports for %s...", file_info["name"])
    imports = await generate_file_imports(file_info, functions, model)
    logging.info("Generating %d functions for %s...", len(functions), file_info["name"])
    tasks = [generate_function(func, file_info, model) for func in functions]
    generated_functions = await asyncio.gather(*tasks)
    raw_code = imports + "\n\n" + "\n\n".join(generated_functions)
    logging.info("Reviewing code for %s...", file_info["name"])
    reviewed_code = await review_code(raw_code, file_info, model)
    logging.info("Formatting code for %s...", file_info["name"])
    formatted_code = await format_code(reviewed_code)
    with open(file_path, "w") as f:
        f.write(f'"""\n{file_info["description"]}\n"""\n\n')
        f.write(formatted_code)
    logging.info("File %s created successfully.", file_info["name"])
    logging.info("Generating tests for %s...", file_info["name"])
    await generate_tests_for_file(
        file_info, functions, project_name, model, blueprint_name
    )


async def process_files_concurrently(
    files: List[Dict[str, str]],
    project_name: str,
    model: str,
    blueprint_name: Optional[str] = None,
    max_concurrency: int = 5,
) -> None:
    """Processes multiple files concurrently with controlled concurrency."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_task(file_info: Dict[str, str]) -> None:
        async with semaphore:
            await generate_code_async(file_info, project_name, model, blueprint_name)

    await asyncio.gather(*(sem_task(f) for f in files))


async def generate_readme(
    project_name: str, project_type: str, description: str, model: str = DEFAULT_LLM
) -> None:
    """Generates a comprehensive README.md using the LLM."""
    prompt = f"""Generate a comprehensive README.md for a Python project.

Project Type: {project_type} ({PYTHON_TEMPLATES.get(project_type, {}).get("description", "")})
Project Description: {description}

Include sections for project overview, installation, usage, structure, configuration, testing, and contributing.
Format with proper Markdown syntax.
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    readme_content = (
        extract_code_block(response["response"], language="markdown")
        or response["response"].strip()
    )
    with open(os.path.join(project_name, "README.md"), "w") as f:
        f.write(readme_content)
    logging.info("README.md created successfully.")


async def generate_makefile(project_name: str) -> None:
    """Generates a Makefile with common development commands."""
    makefile_content = """# Makefile for Python project

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
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
"""
    with open(os.path.join(project_name, "Makefile"), "w") as f:
        f.write(makefile_content)
    logging.info("Makefile created successfully.")


async def generate_gitignore(project_name: str) -> None:
    """Generates a .gitignore file."""
    gitignore_content = """# Byte-compiled / optimized files
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

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.cache
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/

# IDE files
.idea/
.vscode/
.DS_Store
logs/
tmp/
"""
    with open(os.path.join(project_name, ".gitignore"), "w") as f:
        f.write(gitignore_content)
    logging.info(".gitignore created successfully.")


async def generate_conftest(project_name: str, model: str = DEFAULT_LLM) -> None:
    """Generates a conftest.py file with pytest fixtures using the LLM."""
    prompt = """Generate a comprehensive conftest.py for pytest that includes:
- Common fixtures for multiple test files
- Pytest configuration
- Database fixture with cleanup (if applicable)
- Mock fixtures for external dependencies
Provide clear docstrings for each fixture.
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    conftest_code = extract_code_block(response["response"], language="python")
    formatted_code = await format_code(conftest_code)
    conftest_path = os.path.join(project_name, "tests", "conftest.py")
    os.makedirs(os.path.dirname(conftest_path), exist_ok=True)
    with open(conftest_path, "w") as f:
        f.write('"""\nPytest fixtures for the project.\n"""\n\n')
        f.write(formatted_code)
    logging.info("conftest.py created successfully.")


async def generate_setup_py(
    project_name: str, project_type: str, description: str, model: str = DEFAULT_LLM
) -> None:
    """Generates a setup.py file for package installation using the LLM."""
    prompt = f"""Generate a setup.py file for a Python project.

Project Name: {project_name}
Project Type: {project_type}
Project Description: {description}

Include classifiers, dependencies, and entry points if applicable.
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    setup_code = extract_code_block(response["response"], language="python")
    formatted_code = await format_code(setup_code)
    with open(os.path.join(project_name, "setup.py"), "w") as f:
        f.write(formatted_code)
    logging.info("setup.py created successfully.")


# Additional functions for generating specialized components and deployment artifacts


async def generate_component(
    component_info: Dict[str, str], model: str = DEFAULT_LLM
) -> str:
    """Generates code for a specific project component using the LLM.

    Parameters:
        component_info: Dictionary with keys 'name' and 'description'
        model: LLM model to use
    Returns:
        Generated Python code for the component.
    """
    prompt = f"""Generate a Python module for the component:
Component Name: {component_info["name"]}
Description: {component_info["description"]}

Ensure:
- PEP8 compliance
- Detailed docstrings with type annotations
- Modular and reusable design
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    component_code = extract_code_block(response["response"], language="python")
    logging.info("Generated component: %s", component_info["name"])
    return component_code


ARTIFACT_TEMPLATES: Dict[str, Any] = {
    "docker_compose": {
        "description": "Docker Compose configuration for multi-container deployment.",
        "files": [
            {
                "name": "docker-compose.yml",
                "description": "Docker Compose file for orchestrating services.",
            }
        ],
    },
    "kubernetes": {
        "description": "Kubernetes deployment configuration for the microservice.",
        "files": [
            {
                "name": "deployment.yaml",
                "description": "Kubernetes deployment configuration.",
            },
            {
                "name": "service.yaml",
                "description": "Kubernetes service configuration.",
            },
        ],
    },
}


async def generate_artifact(
    artifact_info: Dict[str, str], project_name: str, model: str = DEFAULT_LLM
) -> None:
    """Generates an artifact file (e.g., Docker Compose or Kubernetes config) using the LLM."""
    file_path = os.path.join(project_name, artifact_info["name"])
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    prompt = f"""Generate a {artifact_info["name"]} file.
File Description: {artifact_info["description"]}
Ensure the configuration is valid and ready for deployment.
"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=prompt)
        )
    artifact_content = (
        extract_code_block(response["response"]) or response["response"].strip()
    )
    with open(file_path, "w") as f:
        f.write(artifact_content)
    logging.info("Artifact %s created successfully.", artifact_info["name"])


# Extend the main function to optionally generate components and deployment artifacts.
def main() -> None:
    """Main entry point for the enhanced LLM code generator with component and artifact generation."""
    print("🔧 Python Application Generator 🔧")
    print("====================================")
    user_input = input("Describe the Python application you want to generate:\n")
    try:
        models_list = ollama.list()
        available_models = [model["name"] for model in models_list.get("models", [])]
        if available_models:
            print(f"\nAvailable models: {', '.join(available_models)}")
        else:
            print(f"\nNo models found. Using default: {DEFAULT_LLM}")
    except Exception as e:
        print(
            f"\nCould not retrieve model list ({str(e)}). Using default: {DEFAULT_LLM}"
        )
    chosen_model = (
        input(f"Choose an LLM model (default is '{DEFAULT_LLM}'): ") or DEFAULT_LLM
    )
    project_type = detect_project_type(user_input)
    project_template = PYTHON_TEMPLATES.get(project_type, {})
    if not project_template:
        print(f"❌ Unknown project type: {project_type}")
        return
    print(
        f"\nDetected Project Type: {project_type} ({project_template.get('description', '')})"
    )
    project_name = (
        input("Enter project name (default: generated_python_project): ")
        or "generated_python_project"
    )
    blueprint_name = None
    if project_type in [
        "flask_appbuilder",
        "flask_appbuilder_blueprints",
        "flask_appbuilder_mixins",
    ]:
        blueprint_name = input("Enter blueprint name (if applicable): ").strip() or None
    include_docs = (
        input("Include documentation directory? (y/N): ").strip().lower() == "y"
    )
    include_static = (
        input("Include static files directory? (y/N): ").strip().lower() == "y"
    )
    create_project_directory(project_name, blueprint_name, include_docs, include_static)
    ensure_dev_dependencies(project_name)
    asyncio.run(
        process_files_concurrently(
            project_template.get("files", []),
            project_name,
            chosen_model,
            blueprint_name,
            max_concurrency=3,
        )
    )
    asyncio.run(generate_readme(project_name, project_type, user_input, chosen_model))
    asyncio.run(generate_makefile(project_name))
    if project_type in ["cli_tool", "fastapi_service"]:
        asyncio.run(
            generate_setup_py(project_name, project_type, user_input, chosen_model)
        )
    asyncio.run(generate_conftest(project_name, chosen_model))

    # Optional: Generate additional components if desired
    generate_components = (
        input(
            "Would you like to generate additional components (e.g., messaging, logging modules, dashboards, utilities)? (y/N): "
        )
        .strip()
        .lower()
        == "y"
    )
    if generate_components:
        num_components = int(input("How many components would you like to generate? "))
        for i in range(num_components):
            comp_name = input(f"Component {i+1} name: ")
            comp_desc = input(f"Component {i+1} description: ")
            component_info = {"name": comp_name, "description": comp_desc}
            comp_code = asyncio.run(generate_component(component_info, chosen_model))
            comp_file_path = os.path.join(project_name, "app", f"{comp_name}.py")
            with open(comp_file_path, "w") as f:
                f.write(comp_code)
            logging.info("Component file %s created successfully.", comp_file_path)

    # Optional: Generate deployment artifacts
    generate_artifacts = (
        input("Generate deployment artifacts (docker-compose, kubernetes)? (y/N): ")
        .strip()
        .lower()
        == "y"
    )
    if generate_artifacts:
        for artifact_key, artifact_template in ARTIFACT_TEMPLATES.items():
            for file_info in artifact_template["files"]:
                asyncio.run(generate_artifact(file_info, project_name, chosen_model))

    if check_tools_installed():
        try:
            subprocess.run(["isort", project_name], check=False, capture_output=True)
            subprocess.run(["black", project_name], check=False, capture_output=True)
            logging.info("All files formatted successfully.")
        except Exception as e:
            logging.warning("Could not format all files: %s", str(e))
    print(f"\n🎉 Project generation complete! Files are in '{project_name}' directory.")
    print("\nNext steps:")
    print(f"  1. cd {project_name}")
    print("  2. pip install -r requirements.txt")
    print("  3. pip install -r requirements-dev.txt  # For development tools")
    print("  4. make test  # Run tests")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        traceback.print_exc()
