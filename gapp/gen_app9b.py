#!/usr/bin/env python3
"""
Enhanced LLM Code Generator

This script generates structured Python projects using an LLM model via Ollama for code snippets,
tests, documentation, and more. It supports multiple project types with modular components and
deployment artifacts, with special focus on SQLAlchemy and PostgreSQL database model generation.

Features:
- Supports various project types (API, CLI, Microservices, etc.)
- Database introspection for SQLAlchemy model generation
- Flask-AppBuilder view generation
- Asynchronous code generation with concurrency control and task dependencies
- Automated testing and formatting
- Custom component and artifact generation
- Interactive model selection from available Ollama models
- Comprehensive error handling and logging with retry logic
- Configuration management via config files

Author: [Your Name]
Date: March 04, 2025
Version: 3.0
"""

import asyncio
import ast
import json
import logging
import os
import re
import subprocess
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Callable, Union, TypeVar

import ollama  # External dependency for LLM generation
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import get_lexer_by_name, PythonLexer

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
# DEFAULT_LLM = "mistral-nemo:12b-instruct-2407-q8_0"
DEFAULT_LLM = "phi4-mini"
MAX_CONCURRENCY = 5
DEFAULT_CONFIG_PATH = "~/.gen_app/config.json"

# Type variables for generics
T = TypeVar("T")

#######################################################
# Exception Classes
#######################################################


class GenerationError(Exception):
    """Base exception for generation errors."""

    pass


class LLMError(GenerationError):
    """Error when interacting with LLM."""

    pass


class ValidationError(GenerationError):
    """Error when validating generated code."""

    pass


class ConfigurationError(GenerationError):
    """Error with configuration values."""

    pass


class DatabaseError(GenerationError):
    """Error when interacting with database."""

    pass


#######################################################
# Configuration Management
#######################################################


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Load configuration from file with sensible defaults.

    Parameters
    ----------
    config_path : str, optional
        Path to the configuration file, by default "~/.gen_app/config.json"

    Returns
    -------
    Dict[str, Any]
        Dictionary containing configuration values

    Examples
    --------
    >>> config = load_config()
    >>> model = config["default_model"]
    """
    config_path = os.path.expanduser(config_path)
    default_config = {
        "default_model": DEFAULT_LLM,
        "max_concurrency": MAX_CONCURRENCY,
        "templates_dir": "~/.gen_app/templates",
        "format_code": True,
        "auto_install_tools": False,
        "retry_attempts": 3,
        "backoff_factor": 1.5,
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                user_config = json.load(f)
                return {**default_config, **user_config}
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Error loading config from {config_path}: {e}")
            logging.info("Using default configuration")
    return default_config


def save_config(config: Dict[str, Any], config_path: str = DEFAULT_CONFIG_PATH) -> bool:
    """
    Save configuration to file.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary to save
    config_path : str, optional
        Path to save the configuration, by default "~/.gen_app/config.json"

    Returns
    -------
    bool
        True if configuration was saved successfully, False otherwise
    """
    config_path = os.path.expanduser(config_path)
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        logging.error(f"Failed to save configuration to {config_path}: {e}")
        return False


#######################################################
# Input Validation
#######################################################


def validate_project_name(name: str) -> str:
    """
    Ensure project name is valid.

    Parameters
    ----------
    name : str
        The project name to validate

    Returns
    -------
    str
        The validated project name

    Raises
    ------
    ValidationError
        If the project name is invalid
    """
    if not name:
        raise ValidationError("Project name cannot be empty")

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        raise ValidationError(
            "Project name must start with a letter and contain only letters, numbers, underscores, and hyphens"
        )

    return name


def sanitize_input(user_input: str) -> str:
    """
    Sanitize user input to prevent prompt injection.

    Parameters
    ----------
    user_input : str
        User input to sanitize

    Returns
    -------
    str
        Sanitized input
    """
    # Remove control characters and other potentially dangerous sequences
    sanitized = re.sub(r"[^\x20-\x7E]", "", user_input)
    return sanitized.strip()


def validate_python_code(code: str) -> bool:
    """
    Validate Python code by attempting to parse it.

    Parameters
    ----------
    code : str
        Python code to validate

    Returns
    -------
    bool
        True if the code is valid Python, False otherwise
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logging.warning(f"Generated code has syntax errors: {e}")
        return False


#######################################################
# LLM Providers
#######################################################


class LLMProvider:
    """
    Abstract base class for LLM providers.

    This class defines the interface for different LLM providers,
    allowing for easy switching between providers.
    """

    def generate(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Generate text from the LLM.

        Parameters
        ----------
        prompt : str
            The prompt to send to the LLM
        model : str
            The model identifier to use

        Returns
        -------
        Dict[str, Any]
            The LLM response

        Raises
        ------
        NotImplementedError
            This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement generate()")

    async def generate_async(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Generate text from the LLM asynchronously.

        Parameters
        ----------
        prompt : str
            The prompt to send to the LLM
        model : str
            The model identifier to use

        Returns
        -------
        Dict[str, Any]
            The LLM response

        Notes
        -----
        Default implementation runs the synchronous version in an executor.
        Subclasses may override for native async support.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.generate(prompt, model))

    async def generate_with_retry(
        self, prompt: str, model: str, max_retries: int = 3, backoff_factor: float = 1.5
    ) -> Dict[str, Any]:
        """
        Generate text with exponential backoff retries.

        Parameters
        ----------
        prompt : str
            The prompt to send to the LLM
        model : str
            The model identifier to use
        max_retries : int, optional
            Maximum number of retries, by default 3
        backoff_factor : float, optional
            Factor for exponential backoff, by default 1.5

        Returns
        -------
        Dict[str, Any]
            The LLM response

        Raises
        ------
        LLMError
            If all retry attempts fail
        """
        retries = 0
        last_exception = None

        while retries <= max_retries:
            try:
                return await self.generate_async(prompt, model)
            except Exception as e:
                last_exception = e
                retries += 1
                if retries > max_retries:
                    break

                wait_time = backoff_factor**retries
                logging.warning(
                    f"Retry {retries}/{max_retries} after {wait_time:.1f}s: {e}"
                )
                await asyncio.sleep(wait_time)

        raise LLMError(f"Failed after {max_retries} attempts: {last_exception}")


class OllamaProvider(LLMProvider):
    """
    LLM provider implementation for Ollama.
    """

    def generate(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Generate text using Ollama.

        Parameters
        ----------
        prompt : str
            The prompt to send to Ollama
        model : str
            The model identifier to use

        Returns
        -------
        Dict[str, Any]
            The Ollama response

        Raises
        ------
        LLMError
            If the Ollama call fails
        """
        try:
            return ollama.generate(model=model, prompt=prompt)
        except Exception as e:
            raise LLMError(f"Ollama generation failed: {e}")

    def get_available_models(self) -> List[str]:
        """
        Get a list of available Ollama models.

        Returns
        -------
        List[str]
            List of model names
        """
        try:
            models_list = ollama.list()
            return [model["name"] for model in models_list.get("models", [])]
        except Exception as e:
            logging.warning(f"Failed to fetch Ollama models: {e}")
            return [DEFAULT_LLM]


#######################################################
# Code Generation Utilities
#######################################################


def print_code(code: str, language: str = "python") -> None:
    """
    Print syntax-highlighted code to the terminal.

    Parameters
    ----------
    code : str
        The code to print
    language : str, optional
        The language for syntax highlighting, by default "python"
    """
    try:
        lexer = get_lexer_by_name(language)
        highlighted_code = highlight(code, lexer, Terminal256Formatter())
        print(highlighted_code, end="")
    except Exception as e:
        logging.warning(f"Failed to highlight code: {e}")
        print(code)


def extract_code_block(response_text: str, language: str = "python") -> str:
    """
    Extract code block from text enclosed in triple backticks.

    Parameters
    ----------
    response_text : str
        The raw text response from the LLM
    language : str, optional
        The programming language to extract, by default "python"

    Returns
    -------
    str
        The extracted code block with whitespace trimmed

    Examples
    --------
    >>> text = "Here is some code:\\n```python\\nprint('hello')\\n```\\nEnd."
    >>> extract_code_block(text)
    "print('hello')"
    """
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


async def format_code(code_content: str) -> str:
    """
    Format code using autoflake, isort, and black.

    Parameters
    ----------
    code_content : str
        The code to format

    Returns
    -------
    str
        The formatted code
    """
    if not code_content.strip():
        return code_content

    temp_file = Path("temp_format_file.py")
    try:
        temp_file.write_text(code_content)
        format_commands = [
            ["autoflake", "--remove-all-unused-imports", "--in-place", str(temp_file)],
            ["isort", str(temp_file)],
            ["black", "-q", str(temp_file)],
        ]

        for cmd in format_commands:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.SubprocessError as e:
                logging.warning(f"Command {cmd[0]} failed: {e}")

        return temp_file.read_text()
    except Exception as e:
        logging.warning(f"Code formatting failed: {e}")
        return code_content
    finally:
        if temp_file.exists():
            temp_file.unlink()


def check_tools_installed() -> Dict[str, bool]:
    """
    Check if required formatting tools are installed.

    Returns
    -------
    Dict[str, bool]
        Dictionary mapping tool names to boolean indicating if they're installed
    """
    required_tools = {
        "black": "black",
        "isort": "isort",
        "autoflake": "autoflake",
        "flake8": "flake8",
        "mypy": "mypy",
    }

    tool_status = {}

    for cmd, tool_name in required_tools.items():
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            tool_status[tool_name] = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            tool_status[tool_name] = False

    return tool_status


def install_missing_tools(missing_tools: List[str]) -> bool:
    """
    Install missing development tools.

    Parameters
    ----------
    missing_tools : List[str]
        List of tool names to install

    Returns
    -------
    bool
        True if all tools were installed successfully, False otherwise
    """
    if not missing_tools:
        return True

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade"] + missing_tools,
            check=True,
        )
        logging.info(f"Successfully installed: {', '.join(missing_tools)}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install tools: {e}")
        return False


#######################################################
# Task Management
#######################################################


class Task:
    """
    Represents a task in the generation process with dependencies.
    """

    def __init__(
        self,
        coroutine: Callable[..., Any],
        args: Tuple[Any, ...] = (),
        kwargs: Dict[str, Any] = None,
        dependencies: List["Task"] = None,
        name: str = None,
    ):
        """
        Initialize a Task.

        Parameters
        ----------
        coroutine : Callable
            The coroutine function to execute
        args : Tuple, optional
            Positional arguments for the coroutine, by default ()
        kwargs : Dict, optional
            Keyword arguments for the coroutine, by default None
        dependencies : List[Task], optional
            Tasks that must complete before this one, by default None
        name : str, optional
            Name for the task (for logging), by default None
        """
        self.coroutine = coroutine
        self.args = args
        self.kwargs = kwargs or {}
        self.dependencies = dependencies or []
        self.name = name or coroutine.__name__
        self.result = None
        self.completed = False
        self.started = False
        self.failed = False
        self.error = None

    async def execute(self) -> Any:
        """
        Execute the task coroutine.

        Returns
        -------
        Any
            The result of the coroutine

        Raises
        ------
        Exception
            Any exception raised by the coroutine
        """
        self.started = True
        try:
            self.result = await self.coroutine(*self.args, **self.kwargs)
            self.completed = True
            return self.result
        except Exception as e:
            self.failed = True
            self.error = e
            raise


async def run_task_graph(
    tasks: List[Task], max_concurrency: int = MAX_CONCURRENCY
) -> Dict[str, Any]:
    """
    Execute tasks respecting dependencies.

    Parameters
    ----------
    tasks : List[Task]
        List of tasks to execute
    max_concurrency : int, optional
        Maximum number of tasks to run concurrently, by default MAX_CONCURRENCY

    Returns
    -------
    Dict[str, Any]
        Dictionary mapping task names to their results

    Notes
    -----
    This function implements a topological sort and execution of the task graph.
    """
    results = {}
    pending_tasks = tasks.copy()
    running_tasks = set()
    completed_tasks = set()
    failed_tasks = set()

    semaphore = asyncio.Semaphore(max_concurrency)

    async def execute_task(task: Task) -> None:
        async with semaphore:
            try:
                result = await task.execute()
                results[task.name] = result
                completed_tasks.add(task)
            except Exception as e:
                logging.error(f"Task {task.name} failed: {e}")
                failed_tasks.add(task)
            finally:
                running_tasks.remove(task)

    while pending_tasks or running_tasks:
        # Find tasks whose dependencies are satisfied
        ready_tasks = [
            task
            for task in pending_tasks
            if all(dep in completed_tasks for dep in task.dependencies)
            and task not in running_tasks
            and task not in failed_tasks
        ]

        if not ready_tasks and not running_tasks and pending_tasks:
            # Circular dependency or all remaining tasks depend on failed tasks
            unexecutable = [t.name for t in pending_tasks]
            logging.error(f"Cannot execute tasks due to dependencies: {unexecutable}")
            break

        # Start ready tasks
        for task in ready_tasks:
            pending_tasks.remove(task)
            running_tasks.add(task)
            asyncio.create_task(execute_task(task))

        await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning

    return results


#######################################################
# Project Templates
#######################################################

# Supported project types
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
    "sqlalchemy_models",  # New project type for SQLAlchemy model generation
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
                "name": "config.py",
                "description": "Configuration file for Flask-AppBuilder with database connection and security settings.",
            },
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
            {
                "name": "app/templates/layout.html",
                "description": "Base layout template for the application.",
            },
            {
                "name": "run.py",
                "description": "Application entry point with development server configuration.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for the Flask-AppBuilder application.",
            },
            {
                "name": "setup.py",
                "description": "Setup script for the package.",
            },
            {
                "name": "README.md",
                "description": "Project documentation with installation and usage instructions.",
            },
        ],
    },
    "flask_appbuilder_mixins": {
        "description": "A collection of mixins for Flask-AppBuilder applications.",
        "files": [
            {
                "name": "app/mixins/__init__.py",
                "description": "Mixins package initialization.",
            },
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
                "name": "app/mixins/permissions.py",
                "description": "Enhanced permission handling mixins.",
            },
            {
                "name": "app/mixins/file_handling.py",
                "description": "File and image upload handling mixins.",
            },
            {
                "name": "app/mixins/geo.py",
                "description": "Geospatial data handling mixin.",
            },
            {
                "name": "app/mixins/view_steps.py",
                "description": "Multi-step view mixins for complex forms.",
            },
            {
                "name": "README.md",
                "description": "Documentation for mixins usage and integration.",
            },
            {
                "name": "tests/test_mixins.py",
                "description": "Unit tests for the mixins.",
            },
        ],
    },
    "flask_appbuilder_blueprints": {
        "description": "Blueprints for Flask-AppBuilder applications to modularize views and models.",
        "files": [
            {
                "name": "app/blueprints/__init__.py",
                "description": "Blueprints package initialization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/__init__.py",
                "description": "Initialize the blueprint and register with app.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/views.py",
                "description": "Define blueprint-specific views.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/models.py",
                "description": "Define blueprint-specific models.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/forms.py",
                "description": "Define blueprint-specific forms and validations.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/api.py",
                "description": "Blueprint-specific API endpoints.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/schemas.py",
                "description": "Serialization schemas for the blueprint API.",
            },
            {
                "name": "README.md",
                "description": "Documentation for blueprint integration.",
            },
            {
                "name": "tests/test_blueprints.py",
                "description": "Unit tests for the blueprints.",
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
    "sqlalchemy_models": {
        "description": "A project focused on generating SQLAlchemy models from database introspection.",
        "files": [
            {
                "name": "models/__init__.py",
                "description": "Package initialization that imports all models.",
            },
            {
                "name": "models/base.py",
                "description": "Base model class and shared utilities.",
            },
            {
                "name": "models/mixins.py",
                "description": "Reusable model mixins for common functionality.",
            },
            {
                "name": "models/types.py",
                "description": "Custom column types and type utilities.",
            },
            {
                "name": "generate_models.py",
                "description": "Script to generate models from database introspection.",
            },
            {
                "name": "alembic/env.py",
                "description": "Alembic environment configuration for migrations.",
            },
            {
                "name": "alembic/script.py.mako",
                "description": "Alembic migration script template.",
            },
            {
                "name": "alembic/versions/.keep",
                "description": "Directory for migration versions.",
            },
            {
                "name": "alembic.ini",
                "description": "Alembic configuration file.",
            },
            {
                "name": "config.py",
                "description": "Database configuration settings.",
            },
            {
                "name": "requirements.txt",
                "description": "Project dependencies including SQLAlchemy and alembic.",
            },
            {
                "name": "README.md",
                "description": "Documentation for using the models and running migrations.",
            },
            {
                "name": "tests/test_models.py",
                "description": "Unit tests for the generated models.",
            },
        ],
    },
    # Additional project templates remain unchanged
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
            {
                "name": "Dockerfile",
                "description": "Docker configuration for building application image.",
            },
        ],
    },
    "kubernetes": {
        "description": "Kubernetes deployment configuration.",
        "files": [
            {
                "name": "kubernetes/deployment.yaml",
                "description": "Kubernetes deployment configuration.",
            },
            {
                "name": "kubernetes/service.yaml",
                "description": "Kubernetes service configuration.",
            },
            {
                "name": "kubernetes/configmap.yaml",
                "description": "Configuration Map for environment variables.",
            },
            {
                "name": "kubernetes/secrets.yaml",
                "description": "Secrets configuration template.",
            },
            {
                "name": "kubernetes/ingress.yaml",
                "description": "Ingress configuration for external access.",
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
            {
                "name": ".github/workflows/build.yml",
                "description": "GitHub Actions workflow for building and pushing containers.",
            },
            {
                "name": ".github/workflows/deploy.yml",
                "description": "GitHub Actions workflow for deployment.",
            },
        ],
    },
    "alembic": {
        "description": "Alembic database migration configuration.",
        "files": [
            {
                "name": "alembic.ini",
                "description": "Alembic configuration file.",
            },
            {
                "name": "alembic/env.py",
                "description": "Alembic environment configuration.",
            },
            {
                "name": "alembic/script.py.mako",
                "description": "Migration script template.",
            },
            {
                "name": "alembic/versions/.keep",
                "description": "Directory for migration scripts.",
            },
        ],
    },
    "documentation": {
        "description": "Comprehensive documentation using MkDocs or Sphinx.",
        "files": [
            {
                "name": "docs/index.md",
                "description": "Main documentation page.",
            },
            {
                "name": "docs/installation.md",
                "description": "Installation instructions.",
            },
            {
                "name": "docs/usage.md",
                "description": "Usage guide and examples.",
            },
            {
                "name": "docs/api.md",
                "description": "API documentation.",
            },
            {
                "name": "mkdocs.yml",
                "description": "MkDocs configuration file.",
            },
            {
                "name": "docs/requirements.txt",
                "description": "Documentation dependencies.",
            },
        ],
    },
}


def detect_project_type(prompt: str) -> str:
    """
    Determines the most suitable project type based on user prompt.

    Parameters
    ----------
    prompt : str
        User description of the project

    Returns
    -------
    str
        Detected project type from SUPPORTED_TYPES
    """
    prompt_lower = prompt.lower()

    # Add new pattern for SQLAlchemy models
    if any(
        keyword in prompt_lower
        for keyword in [
            "database model",
            "sqlalchemy model",
            "orm",
            "database introspection",
            "generate model",
            "database schema",
            "postgres model",
        ]
    ):
        return "sqlalchemy_models"

    # Existing patterns
    type_mappings = {
        "fastrtc|webrtc|real.?time communication": "fastrtc_app",
        "chatbot|chat.?bot|conversational ai": "chatbot_app",
        "speech to text|s2t|speech recognition": "speech_to_text_app",
        "text to speech|tts": "text_to_speech_app",
        "microservice|micro.?service": "microservice",
        "cli|command.?line|terminal": "cli_tool",
        "dashboard|visuali[sz]ation|charts": "dashboard_app",
        "mixin.*flask.?appbuilder": "flask_appbuilder_mixins",
        "blueprint.*flask.?appbuilder": "flask_appbuilder_blueprints",
        "utility|utilities": "utilities_app",
        "data science|machine learning|ml|prediction|classification": "data_science",
        "api|rest|flask.?api": "flask_api",
        "flask.?appbuilder|fab": "flask_appbuilder",
    }

    for pattern, project_type in type_mappings.items():
        if any(re.search(keyword, prompt_lower) for keyword in pattern.split("|")):
            return project_type

    return "general_app"


#######################################################
# Project Structure Generation
#######################################################


def create_project_directory(
    project_name: str,
    blueprint_name: Optional[str] = None,
    include_docs: bool = False,
    include_static: bool = False,
    include_migrations: bool = False,
) -> None:
    """
    Creates project directory structure with additional common directories.

    Parameters
    ----------
    project_name : str
        Name of the project to create
    blueprint_name : str, optional
        Name of Flask-AppBuilder blueprint to create, by default None
    include_docs : bool, optional
        Whether to include documentation directories, by default False
    include_static : bool, optional
        Whether to include static asset directories, by default False
    include_migrations : bool, optional
        Whether to include migration directories, by default False

    Raises
    ------
    OSError
        If there is an error creating directories
    """
    try:
        # Base directories
        directories = [
            project_name,
            f"{project_name}/app",
            f"{project_name}/tests",
            f"{project_name}/logs",
        ]

        # Add blueprint directories if requested
        if blueprint_name:
            blueprint_base = f"{project_name}/app/blueprints/{blueprint_name}"
            directories.extend(
                [
                    f"{project_name}/app/blueprints",
                    blueprint_base,
                    f"{blueprint_base}/views",
                    f"{blueprint_base}/models",
                    f"{blueprint_base}/api",
                ]
            )

        # Add documentation directories if requested
        if include_docs:
            directories.extend(
                [
                    f"{project_name}/docs",
                    f"{project_name}/docs/api",
                    f"{project_name}/docs/user_guide",
                ]
            )

        # Add static asset directories if requested
        if include_static:
            directories.extend(
                [
                    f"{project_name}/app/static",
                    f"{project_name}/app/static/css",
                    f"{project_name}/app/static/js",
                    f"{project_name}/app/static/img",
                    f"{project_name}/app/static/vendor",
                ]
            )

        # Add migration directories if requested
        if include_migrations:
            directories.extend(
                [
                    f"{project_name}/migrations",
                    f"{project_name}/migrations/versions",
                ]
            )

        # Add standard directories
        directories.extend(
            [
                f"{project_name}/app/templates",
                f"{project_name}/app/models",
                f"{project_name}/app/views",
                f"{project_name}/config",
            ]
        )

        # Create all directories
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

        # Create configuration files
        with open(f"{project_name}/pyproject.toml", "w") as f:
            f.write(
                """[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310']
include = '\\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
pythonpath = ["."]
"""
            )

        with open(f"{project_name}/.editorconfig", "w") as f:
            f.write(
                """# EditorConfig helps maintain consistent coding styles
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{json,yml,yaml,html,css,js}]
indent_style = space
indent_size = 2
"""
            )

        with open(f"{project_name}/.gitignore", "w") as f:
            f.write(
                """# Byte-compiled files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Virtual environments
venv/
env/
ENV/
.env

# IDE and OS files
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store

# Application specific
logs/
*.log
"""
            )

        logging.info(f"Project directory structure created for {project_name}")
    except OSError as e:
        logging.error(f"Failed to create project directory: {e}")
        raise


def ensure_dev_dependencies(project_name: str) -> None:
    """
    Ensures development dependencies are properly configured.

    Parameters
    ----------
    project_name : str
        Name of the project

    Raises
    ------
    IOError
        If there is an error writing the files
    """
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
            "pre-commit>=3.0",
        ]
        with open(f"{project_name}/requirements-dev.txt", "w") as f:
            f.write("# Development dependencies\n" + "\n".join(dev_deps))

        req_file = f"{project_name}/requirements.txt"
        if not os.path.exists(req_file):
            with open(req_file, "w") as f:
                f.write("# Main project dependencies\n")

        # Create pre-commit configuration
        with open(f"{project_name}/.pre-commit-config.yaml", "w") as f:
            f.write(
                """repos:
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.4.0
  hooks:
    - id: trailing-whitespace
    - id: end-of-file-fixer
    - id: check-yaml
    - id: check-added-large-files

- repo: https://github.com/pycqa/isort
  rev: 5.12.0
  hooks:
    - id: isort

- repo: https://github.com/psf/black
  rev: 23.3.0
  hooks:
    - id: black

- repo: https://github.com/pycqa/flake8
  rev: 6.0.0
  hooks:
    - id: flake8
      additional_dependencies: [flake8-docstrings]
"""
            )

        logging.info(f"Development dependencies configured for {project_name}")
    except IOError as e:
        logging.error(f"Failed to write dependencies: {e}")
        raise


async def setup_virtual_env(project_name: str) -> bool:
    """
    Set up a virtual environment for the project.

    Parameters
    ----------
    project_name : str
        Name of the project

    Returns
    -------
    bool
        True if the virtual environment was created successfully, False otherwise
    """
    env_dir = os.path.join(project_name, "venv")
    try:
        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", env_dir], check=True)

        # Use the venv pip to install dependencies
        pip_path = os.path.join(env_dir, "bin" if os.name != "nt" else "Scripts", "pip")

        req_path = os.path.join(project_name, "requirements.txt")
        if os.path.exists(req_path):
            subprocess.run([pip_path, "install", "-r", req_path], check=True)

        dev_req_path = os.path.join(project_name, "requirements-dev.txt")
        if os.path.exists(dev_req_path):
            subprocess.run([pip_path, "install", "-r", dev_req_path], check=True)

        # Install pre-commit hooks
        pre_commit_path = os.path.join(
            env_dir, "bin" if os.name != "nt" else "Scripts", "pre-commit"
        )
        if os.path.exists(pre_commit_path):
            pre_commit_config = os.path.join(project_name, ".pre-commit-config.yaml")
            if os.path.exists(pre_commit_config):
                subprocess.run(
                    [pre_commit_path, "install"], cwd=project_name, check=True
                )

        logging.info(f"Virtual environment created at {env_dir}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set up virtual environment: {e}")
        return False


#######################################################
# Database Introspection and Model Generation
#######################################################


async def generate_db_models(
    database_url: str,
    output_dir: str,
    model: str,
    llm_provider: LLMProvider,
    schema: str = "public",
    include_views: bool = False,
    include_triggers: bool = False,
) -> None:
    """
    Generate SQLAlchemy models by introspecting a PostgreSQL database.

    Parameters
    ----------
    database_url : str
        SQLAlchemy connection URL (postgresql://user:pass@host/dbname)
    output_dir : str
        Directory to save generated models
    model : str
        LLM model to use for generation
    llm_provider : LLMProvider
        Provider for LLM interactions
    schema : str, optional
        Database schema to introspect, by default "public"
    include_views : bool, optional
        Include database views, by default False
    include_triggers : bool, optional
        Generate trigger functions, by default False

    Raises
    ------
    DatabaseError
        If database introspection fails
    ValidationError
        If generated code is invalid
    """
    try:
        # Import SQLAlchemy components
        try:
            from sqlalchemy import create_engine, MetaData, inspect
        except ImportError:
            logging.error("SQLAlchemy is required for database introspection")
            raise DatabaseError(
                "SQLAlchemy is not installed. Please install it with: pip install sqlalchemy"
            )

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Connect to database
        engine = create_engine(database_url)
        inspector = inspect(engine)
        metadata = MetaData(schema=schema)

        try:
            metadata.reflect(engine, views=include_views)
        except Exception as e:
            raise DatabaseError(f"Failed to reflect database schema: {e}")

        # Get table information
        tables_info = []
        for table_name in inspector.get_table_names(schema=schema):
            try:
                columns = inspector.get_columns(table_name, schema=schema)
                pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
                fk_constraints = inspector.get_foreign_keys(table_name, schema=schema)
                unique_constraints = inspector.get_unique_constraints(
                    table_name, schema=schema
                )
                indices = inspector.get_indexes(table_name, schema=schema)
                comment = inspector.get_table_comment(table_name, schema=schema)

                tables_info.append(
                    {
                        "name": table_name,
                        "comment": comment.get("text", ""),
                        "columns": [
                            {
                                "name": col["name"],
                                "type": str(col["type"]),
                                "nullable": col["nullable"],
                                "default": str(col.get("default", "")),
                                "comment": col.get("comment", ""),
                                "primary_key": col["name"]
                                in pk_constraint.get("constrained_columns", []),
                            }
                            for col in columns
                        ],
                        "primary_key": {
                            "name": pk_constraint.get("name"),
                            "columns": pk_constraint.get("constrained_columns", []),
                        },
                        "foreign_keys": [
                            {
                                "name": fk.get("name"),
                                "constrained_columns": fk["constrained_columns"],
                                "referred_schema": fk.get("referred_schema"),
                                "referred_table": fk["referred_table"],
                                "referred_columns": fk["referred_columns"],
                                "options": fk.get("options", {}),
                            }
                            for fk in fk_constraints
                        ],
                        "unique_constraints": [
                            {
                                "name": uq["name"],
                                "columns": uq["column_names"],
                            }
                            for uq in unique_constraints
                        ],
                        "indices": [
                            {
                                "name": idx["name"],
                                "columns": idx["column_names"],
                                "unique": idx["unique"],
                            }
                            for idx in indices
                        ],
                    }
                )
            except Exception as e:
                logging.warning(f"Error processing table {table_name}: {e}")

        # Generate base model
        base_model_prompt = """Generate a SQLAlchemy base model class for these tables:

Schema Information:
```json
{schema_info}
```

Implement:
1. A Base class with SQLAlchemy declarative base
2. A BaseModel mixin with common columns (id, created_at, updated_at)
3. Use SQLAlchemy 2.0 style (annotated declarative style)
4. Include proper type annotations and docstrings

Return the Python code for models/base.py.""".format(
            schema_info=json.dumps(tables_info[:3], indent=2)
        )

        base_response = await llm_provider.generate_with_retry(base_model_prompt, model)
        base_code = extract_code_block(base_response["response"], "python")
        if validate_python_code(base_code):
            formatted_base = await format_code(base_code)
            with open(os.path.join(output_dir, "base.py"), "w") as f:
                f.write(formatted_base)
            logging.info("Generated base model class")
        else:
            logging.error("Failed to generate valid base model code")

        # Generate models for each table
        for i, table_info in enumerate(tables_info):
            logging.info(
                f"Generating model for {table_info['name']} ({i + 1}/{len(tables_info)})"
            )

            model_prompt = f"""Generate a SQLAlchemy ORM model for this PostgreSQL table:

Table Name: {table_info["name"]}
Comment: {table_info["comment"]}

Columns:
```json
{json.dumps(table_info["columns"], indent=2)}
```

Primary Key:
```json
{json.dumps(table_info["primary_key"], indent=2)}
```

Foreign Keys:
```json
{json.dumps(table_info["foreign_keys"], indent=2)}
```

Unique Constraints:
```json
{json.dumps(table_info["unique_constraints"], indent=2)}
```

Indices:
```json
{json.dumps(table_info["indices"], indent=2)}
```

Generate a complete SQLAlchemy model with:
1. Proper imports (from models.base import Base, BaseModel)
2. Type annotations using SQLAlchemy 2.0 style (from sqlalchemy.orm import Mapped, mapped_column)
3. Relationships based on foreign keys with appropriate backref names
4. A __repr__ method
5. All constraints and indices included
6. Meaningful docstrings explaining each column
7. Include column comments as doc attribute
8. Include any check constraints
9. Ensure compatibility with both SQLAlchemy 1.4 and 2.0
"""

            response = await llm_provider.generate_with_retry(model_prompt, model)
            code = extract_code_block(response["response"], "python")

            # Validate and format the code
            if validate_python_code(code):
                formatted_code = await format_code(code)
                snake_name = table_info["name"]
                model_file = os.path.join(output_dir, f"{snake_name}.py")
                with open(model_file, "w") as f:
                    f.write(formatted_code)
                logging.info(f"Generated model for {table_info['name']}")
            else:
                logging.error(
                    f"Failed to generate valid model for {table_info['name']}"
                )

        # Generate __init__.py to import all models
        init_content = """\"\"\"
SQLAlchemy ORM models generated from database introspection.

These models are auto-generated and should not be modified directly.
\"\"\"

from .base import Base, BaseModel

"""

        # Add imports for each table
        for table_info in tables_info:
            snake_name = table_info["name"]
            class_name = "".join(word.capitalize() for word in snake_name.split("_"))
            init_content += f"from .{snake_name} import {class_name}\n"

        # Add __all__ declaration
        init_content += "\n__all__ = [\n"
        init_content += "    'Base',\n"
        init_content += "    'BaseModel',\n"
        for table_info in tables_info:
            class_name = "".join(
                word.capitalize() for word in table_info["name"].split("_")
            )
            init_content += f"    '{class_name}',\n"
        init_content += "]\n"

        with open(os.path.join(output_dir, "__init__.py"), "w") as f:
            f.write(init_content)

        # Generate types.py for custom types
        types_prompt = """Generate a Python module with custom SQLAlchemy column types.

Include:
1. Common PostgreSQL types (UUID, JSONB, Array, etc.)
2. Helper functions for type compatibility
3. Any custom type handling needed for the database

The module should be comprehensive and handle both SQLAlchemy 1.4 and 2.0 compatibility."""

        types_response = await llm_provider.generate_with_retry(types_prompt, model)
        types_code = extract_code_block(types_response["response"], "python")

        if validate_python_code(types_code):
            formatted_types = await format_code(types_code)
            with open(os.path.join(output_dir, "types.py"), "w") as f:
                f.write(formatted_types)
            logging.info("Generated types module")

        # Generate alembic env.py for migrations
        if include_triggers:
            logging.info("Generating database triggers and functions")
            # Generate database trigger functions
            triggers_prompt = f"""Generate a Python module that creates database triggers and functions for these tables:

Schema Information:
```json
{json.dumps([t["name"] for t in tables_info], indent=2)}
```

Include:
1. Functions to create appropriate triggers (updated_at, audit logging, etc.)
2. SQLAlchemy event listeners
3. Implementation of common database trigger patterns

Return the Python code."""

            triggers_response = await llm_provider.generate_with_retry(
                triggers_prompt, model
            )
            triggers_code = extract_code_block(triggers_response["response"], "python")

            if validate_python_code(triggers_code):
                formatted_triggers = await format_code(triggers_code)
                with open(os.path.join(output_dir, "triggers.py"), "w") as f:
                    f.write(formatted_triggers)
                logging.info("Generated database triggers module")

        logging.info(f"Generated {len(tables_info)} models in {output_dir}")

    except Exception as e:
        logging.error(f"Database introspection failed: {e}")
        raise DatabaseError(f"Failed to generate models: {str(e)}") from e


async def generate_fab_views(
    models_dir: str,
    output_dir: str,
    model: str,
    llm_provider: LLMProvider,
) -> None:
    """
    Generate Flask-AppBuilder views for SQLAlchemy models.

    Parameters
    ----------
    models_dir : str
        Directory containing the SQLAlchemy models
    output_dir : str
        Directory to save generated views
    model : str
        LLM model to use for generation
    llm_provider : LLMProvider
        Provider for LLM interactions

    Raises
    ------
    ValueError
        If models directory doesn't exist
    """
    if not os.path.exists(models_dir):
        raise ValueError(f"Models directory {models_dir} does not exist")

    os.makedirs(output_dir, exist_ok=True)

    # Read model files
    model_files = [
        f
        for f in os.listdir(models_dir)
        if f.endswith(".py") and f != "__init__.py" and f != "base.py"
    ]

    for model_file in model_files:
        model_path = os.path.join(models_dir, model_file)
        with open(model_path, "r") as f:
            model_code = f.read()

        # Extract model name and information
        model_name = os.path.splitext(model_file)[0]
        class_name = "".join(word.capitalize() for word in model_name.split("_"))

        view_prompt = f"""Generate a Flask-AppBuilder ModelView for this SQLAlchemy model:

```python
{model_code}
```

Create a view with:
1. Appropriate list_columns, show_columns, and edit_columns
2. Form validation and widgets
3. Search columns setup
4. Related views configuration
5. Custom formatting for dates, relationships, etc.
6. Proper route_base setup

The view should follow Flask-AppBuilder best practices and be ready to use in a FAB application."""

        response = await llm_provider.generate_with_retry(view_prompt, model)
        view_code = extract_code_block(response["response"], "python")

        if validate_python_code(view_code):
            formatted_view = await format_code(view_code)
            view_file = os.path.join(output_dir, f"{model_name}_view.py")
            with open(view_file, "w") as f:
                f.write(formatted_view)
            logging.info(f"Generated view for {class_name}")

    # Generate __init__.py to import and register all views
    init_prompt = f"""Generate an __init__.py file that registers all Flask-AppBuilder views.

The views are in these files:
{", ".join([os.path.splitext(f)[0] + "_view.py" for f in model_files])}

The __init__.py should:
1. Import all view classes
2. Have a register_views function that adds all views to an AppBuilder instance
3. Include proper type annotations and docstrings
4. Support FAB security integration"""

    response = await llm_provider.generate_with_retry(init_prompt, model)
    init_code = extract_code_block(response["response"], "python")

    if validate_python_code(init_code):
        formatted_init = await format_code(init_code)
        with open(os.path.join(output_dir, "__init__.py"), "w") as f:
            f.write(formatted_init)
        logging.info("Generated views __init__.py")

    logging.info(f"Generated views for {len(model_files)} models in {output_dir}")


async def setup_alembic(
    project_dir: str,
    models_package: str,
    database_url: str,
    model: str,
    llm_provider: LLMProvider,
) -> None:
    """
    Set up Alembic migrations for SQLAlchemy models.

    Parameters
    ----------
    project_dir : str
        Project root directory
    models_package : str
        Python package path to the models (e.g., "app.models")
    database_url : str
        Database connection URL
    model : str
        LLM model to use for generation
    llm_provider : LLMProvider
        Provider for LLM interactions

    Returns
    -------
    None
    """
    # Create alembic directory structure
    alembic_dir = os.path.join(project_dir, "migrations")
    versions_dir = os.path.join(alembic_dir, "versions")
    os.makedirs(versions_dir, exist_ok=True)

    # Generate alembic.ini
    alembic_ini_prompt = f"""Generate an alembic.ini configuration file for SQLAlchemy migrations.

Database URL: {database_url}
Script location: migrations
"""

    alembic_ini_response = await llm_provider.generate_with_retry(
        alembic_ini_prompt, model
    )
    alembic_ini = extract_code_block(alembic_ini_response["response"], "ini")

    with open(os.path.join(project_dir, "alembic.ini"), "w") as f:
        f.write(alembic_ini)

    # Generate env.py
    env_py_prompt = f"""Generate an Alembic env.py file to configure migration environment.

Models package: {models_package}
Database URL: {database_url}

The file should:
1. Import all models from the package
2. Set up target_metadata correctly
3. Handle both offline and online migration contexts
4. Include SQLAlchemy 2.0 compatibility
"""

    env_py_response = await llm_provider.generate_with_retry(env_py_prompt, model)
    env_py = extract_code_block(env_py_response["response"], "python")

    if validate_python_code(env_py):
        formatted_env = await format_code(env_py)
        with open(os.path.join(alembic_dir, "env.py"), "w") as f:
            f.write(formatted_env)

    # Generate script.py.mako
    script_mako_prompt = (
        """Generate an Alembic script.py.mako template file for migration scripts."""
    )

    script_mako_response = await llm_provider.generate_with_retry(
        script_mako_prompt, model
    )
    script_mako = extract_code_block(script_mako_response["response"], "mako")

    with open(os.path.join(alembic_dir, "script.py.mako"), "w") as f:
        f.write(script_mako)

    # Create an initial migration
    init_migration_prompt = f"""Generate an initial Alembic migration script that creates all tables.

The migration should:
1. Use revision identifiers
2. Include docstring with description
3. Have both upgrade() and downgrade() functions
4. Be compatible with both SQLAlchemy 1.4 and 2.0
"""

    init_migration_response = await llm_provider.generate_with_retry(
        init_migration_prompt, model
    )
    init_migration = extract_code_block(init_migration_response["response"], "python")

    if validate_python_code(init_migration):
        formatted_migration = await format_code(init_migration)
        timestamp = int(time.time())
        with open(
            os.path.join(versions_dir, f"{timestamp}_initial_migration.py"), "w"
        ) as f:
            f.write(formatted_migration)

    logging.info(f"Alembic migrations set up in {alembic_dir}")


async def identify_functions(
    file_info: Dict[str, str], model: str, llm_provider: LLMProvider
) -> List[Dict[str, Any]]:
    """
    Identifies functions needed for a file using LLM.

    Parameters
    ----------
    file_info : Dict[str, str]
        Information about the file
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions

    Returns
    -------
    List[Dict[str, Any]]
        List of function information dictionaries
    """
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
        response = await llm_provider.generate_with_retry(prompt, model)
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
    function_info: Dict[str, Any],
    file_info: Dict[str, str],
    model: str,
    llm_provider: LLMProvider,
) -> str:
    """
    Generates an individual Python function using the LLM.

    Parameters
    ----------
    function_info : Dict[str, Any]
        Information about the function to generate
    file_info : Dict[str, str]
        Information about the file
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions

    Returns
    -------
    str
        Generated function code
    """
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
        response = await llm_provider.generate_with_retry(prompt, model)
        code = extract_code_block(response["response"], "python")
        logging.info(f"Generated function: {function_info['name']}")
        return code
    except Exception as e:
        logging.error(f"Failed to generate function {function_info['name']}: {e}")
        return (
            f"def {function_info['name']}():\n    # TODO: Implement function\n    pass"
        )


async def generate_file_imports(
    file_info: Dict[str, str],
    functions: List[Dict[str, Any]],
    model: str,
    llm_provider: LLMProvider,
) -> str:
    """
    Generates import statements for a Python file.

    Parameters
    ----------
    file_info : Dict[str, str]
        Information about the file
    functions : List[Dict[str, Any]]
        List of functions in the file
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions

    Returns
    -------
    str
        Generated import statements
    """
    if os.path.splitext(file_info["name"])[1] not in [".py", ""]:
        return ""

    prompt = f"""Generate Python import statements for:

File Name: {file_info["name"]}
File Purpose: {file_info["description"]}
Functions: {json.dumps(functions, indent=2)}

Provide only the import statements."""
    try:
        response = await llm_provider.generate_with_retry(prompt, model)
        imports = extract_code_block(response["response"], "python")
        return imports + "\n" if imports else ""
    except Exception as e:
        logging.warning(f"Failed to generate imports for {file_info['name']}: {e}")
        return ""


async def generate_tests_for_function(
    function_info: Dict[str, Any],
    file_info: Dict[str, str],
    model: str,
    llm_provider: LLMProvider,
) -> str:
    """
    Generates pytest test cases for a function.

    Parameters
    ----------
    function_info : Dict[str, Any]
        Information about the function to test
    file_info : Dict[str, str]
        Information about the file
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions

    Returns
    -------
    str
        Generated test code
    """
    prompt = f"""Generate comprehensive pytest test cases for:

Function Name: {function_info["name"]}
Purpose: {function_info["description"]}
Parameters: {json.dumps(function_info.get("parameters", []))}
Return Type: {function_info.get("return_type", "None")}
File Purpose: {file_info["description"]}

Ensure:
- Use of pytest fixtures
- Coverage of normal and edge cases
- At least 3 test functions
- Proper mocking of external dependencies
- Parameterized tests where appropriate
- Testing of error conditions
"""
    try:
        response = await llm_provider.generate_with_retry(prompt, model)
        return extract_code_block(response["response"], "python")
    except Exception as e:
        logging.warning(f"Failed to generate tests for {function_info['name']}: {e}")
        return f"# TODO: Add tests for {function_info['name']}"


async def generate_tests_for_file(
    file_info: Dict[str, str],
    functions: List[Dict[str, Any]],
    project_name: str,
    model: str,
    llm_provider: LLMProvider,
    blueprint_name: Optional[str] = None,
) -> None:
    """
    Generates a test file for a Python file.

    Parameters
    ----------
    file_info : Dict[str, str]
        Information about the file
    functions : List[Dict[str, Any]]
        List of functions in the file
    project_name : str
        Name of the project
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions
    blueprint_name : str, optional
        Name of the blueprint, by default None
    """
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
Functions: {json.dumps(functions, indent=2)}

Include:
- Setup and teardown fixtures
- Parameterized fixtures
- Mock fixtures for external dependencies
- Fixtures for database interactions if needed
- Session, module, and function scoped fixtures as appropriate
"""
    response = await llm_provider.generate_with_retry(fixtures_prompt, model)
    fixtures_code = extract_code_block(response["response"], "python")

    test_functions = await asyncio.gather(
        *[
            generate_tests_for_function(func, file_info, model, llm_provider)
            for func in functions
        ]
    )
    all_test_code = imports + fixtures_code + "\n\n" + "\n\n".join(test_functions)
    formatted_code = await format_code(all_test_code)

    with open(full_test_path, "w") as f:
        f.write(
            f'"""\nTests for {file_info["name"]}: {file_info["description"]}\n"""\n\n{formatted_code}'
        )
    logging.info(f"Test file {test_file_path} created")


async def review_code(
    file_content: str, file_info: Dict[str, str], model: str, llm_provider: LLMProvider
) -> str:
    """
    Reviews and improves generated code.

    Parameters
    ----------
    file_content : str
        Original code content
    file_info : Dict[str, str]
        Information about the file
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions

    Returns
    -------
    str
        Improved code content
    """
    if os.path.splitext(file_info["name"])[1] not in [".py", ""]:
        return file_content

    prompt = f"""Review this Python code for {file_info["name"]}:

```python
{file_content}
```

Check for:
1. Correctness and functionality
2. Python best practices and PEP8 compliance
3. Security vulnerabilities or anti-patterns
4. Completeness based on the file purpose
5. Proper error handling
6. Appropriate logging
7. Type hints correctness
8. Documentation completeness

Return improved code with your enhancements.
"""
    try:
        response = await llm_provider.generate_with_retry(prompt, model)
        return extract_code_block(response["response"], "python")
    except Exception as e:
        logging.warning(f"Code review failed for {file_info['name']}: {e}")
        return file_content


async def generate_code_async(
    file_info: Dict[str, str],
    project_name: str,
    model: str,
    llm_provider: LLMProvider,
    blueprint_name: Optional[str] = None,
) -> None:
    """
    Generates code for a file.

    Parameters
    ----------
    file_info : Dict[str, str]
        Information about the file
    project_name : str
        Name of the project
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions
    blueprint_name : str, optional
        Name of the blueprint, by default None
    """
    file_path = os.path.join(
        project_name,
        file_info["name"].replace("<blueprint_name>", blueprint_name or "blueprint"),
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_ext = os.path.splitext(file_info["name"])[1]

    if file_ext not in [".py", ""]:
        if "requirements.txt" in file_path:
            prompt = f"Generate requirements.txt for {project_name}: {file_info['description']}"
            response = await llm_provider.generate_with_retry(prompt, model)
            with open(file_path, "w") as f:
                f.write(
                    extract_code_block(response["response"])
                    or response["response"].strip()
                )
        else:
            await generate_non_python_file(
                file_info, project_name, model, llm_provider, blueprint_name
            )
        return

    functions = await identify_functions(file_info, model, llm_provider)
    imports = await generate_file_imports(file_info, functions, model, llm_provider)

    generated_functions = await asyncio.gather(
        *[generate_function(func, file_info, model, llm_provider) for func in functions]
    )

    raw_code = imports + "\n\n" + "\n\n".join(generated_functions)
    reviewed_code = await review_code(raw_code, file_info, model, llm_provider)
    formatted_code = await format_code(reviewed_code)

    with open(file_path, "w") as f:
        f.write(f'"""\n{file_info["description"]}\n"""\n\n{formatted_code}')

    await generate_tests_for_file(
        file_info, functions, project_name, model, llm_provider, blueprint_name
    )

    logging.info(f"File {file_info['name']} created")


async def generate_non_python_file(
    file_info: Dict[str, str],
    project_name: str,
    model: str,
    llm_provider: LLMProvider,
    blueprint_name: Optional[str] = None,
) -> None:
    """
    Generates content for non-Python files.

    Parameters
    ----------
    file_info : Dict[str, str]
        Information about the file
    project_name : str
        Name of the project
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions
    blueprint_name : str, optional
        Name of the blueprint, by default None
    """
    file_path = os.path.join(
        project_name,
        file_info["name"].replace("<blueprint_name>", blueprint_name or "blueprint"),
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_ext = os.path.splitext(file_info["name"])[1]

    file_type_prompts = {
        ".html": (
            f"Generate HTML for {file_info['name']}: {file_info['description']}\n\n"
            f"Include proper DOCTYPE, head with meta tags, responsive design, and semantic markup."
        ),
        ".css": (
            f"Generate CSS for {file_info['name']}: {file_info['description']}\n\n"
            f"Include responsive design, variables for colors and sizes, and comments for sections."
        ),
        ".js": (
            f"Generate JavaScript for {file_info['name']}: {file_info['description']}\n\n"
            f"Use modern ES6+ syntax, proper error handling, and clear commenting."
        ),
        ".json": (
            f"Generate JSON for {file_info['name']}: {file_info['description']}\n\n"
            f"Ensure valid JSON structure with appropriate nesting and types."
        ),
        ".md": (
            f"Generate Markdown for {file_info['name']}: {file_info['description']}\n\n"
            f"Include proper headings, lists, code blocks, and formatting."
        ),
        ".yaml": (
            f"Generate YAML for {file_info['name']}: {file_info['description']}\n\n"
            f"Ensure valid YAML structure with appropriate indentation and comments."
        ),
        ".toml": (
            f"Generate TOML for {file_info['name']}: {file_info['description']}\n\n"
            f"Include appropriate sections, key-value pairs, and comments."
        ),
        ".sh": (
            f"Generate Bash script for {file_info['name']}: {file_info['description']}\n\n"
            f"Include proper shebang, error handling, command-line argument parsing, and comments."
        ),
    }

    prompt = file_type_prompts.get(
        file_ext,
        f"Generate content for {file_info['name']} ({file_ext}): {file_info['description']}\n\n"
        f"Ensure appropriate formatting, structure, and completeness for this file type.",
    )

    response = await llm_provider.generate_with_retry(prompt, model)

    if file_ext in [".py", ".js", ".sh", ".html", ".css"]:
        content = (
            extract_code_block(response["response"], file_ext[1:])
            or response["response"].strip()
        )
    else:
        content = response["response"].strip()

    with open(file_path, "w") as f:
        f.write(content)

    logging.info(f"File {file_info['name']} created")


async def process_files_concurrently(
    files: List[Dict[str, str]],
    project_name: str,
    model: str,
    llm_provider: LLMProvider,
    blueprint_name: Optional[str] = None,
    max_concurrency: int = MAX_CONCURRENCY,
) -> None:
    """
    Processes multiple files concurrently.

    Parameters
    ----------
    files : List[Dict[str, str]]
        List of file information dictionaries
    project_name : str
        Name of the project
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions
    blueprint_name : str, optional
        Name of the blueprint, by default None
    max_concurrency : int, optional
        Maximum number of concurrent tasks, by default MAX_CONCURRENCY
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_task(file_info: Dict[str, str]) -> None:
        async with semaphore:
            await generate_code_async(
                file_info, project_name, model, llm_provider, blueprint_name
            )

    # Group files by type for better generation (models first, then views, etc.)
    file_groups = {
        "models": [],
        "base": [],
        "config": [],
        "views": [],
        "api": [],
        "utils": [],
        "other": [],
    }

    for file_info in files:
        name = file_info["name"].lower()
        if "model" in name:
            file_groups["models"].append(file_info)
        elif "base" in name:
            file_groups["base"].append(file_info)
        elif "config" in name:
            file_groups["config"].append(file_info)
        elif "view" in name:
            file_groups["views"].append(file_info)
        elif "api" in name:
            file_groups["api"].append(file_info)
        elif "util" in name:
            file_groups["utils"].append(file_info)
        else:
            file_groups["other"].append(file_info)

    # Process files in order of dependency
    for group in ["base", "config", "models", "utils", "views", "api", "other"]:
        if file_groups[group]:
            await asyncio.gather(*(sem_task(f) for f in file_groups[group]))
            logging.info(f"Completed {group} files")


async def generate_readme(
    project_name: str,
    project_type: str,
    description: str,
    model: str,
    llm_provider: LLMProvider,
) -> None:
    """
    Generates README.md.

    Parameters
    ----------
    project_name : str
        Name of the project
    project_type : str
        Type of the project
    description : str
        Project description
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions
    """
    prompt = f"""Generate a comprehensive README.md for:
Project Name: {project_name}
Project Type: {project_type} ({PYTHON_TEMPLATES[project_type]["description"]})
Description: {description}

Include:
1. Project overview and purpose
2. Installation instructions (pip, virtualenv)
3. Usage examples with code snippets
4. Project structure explanation
5. Development and testing guidelines
6. Contribution guidelines
7. License information
8. Proper Markdown formatting with headings, code blocks, and lists

Make it comprehensive, professional, and well-structured."""

    response = await llm_provider.generate_with_retry(prompt, model)
    with open(f"{project_name}/README.md", "w") as f:
        f.write(
            extract_code_block(response["response"], "markdown")
            or response["response"].strip()
        )
    logging.info("README.md created")


async def generate_setup_py(
    project_name: str,
    project_type: str,
    description: str,
    model: str,
    llm_provider: LLMProvider,
) -> None:
    """
    Generates setup.py.

    Parameters
    ----------
    project_name : str
        Name of the project
    project_type : str
        Type of the project
    description : str
        Project description
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions
    """
    prompt = f"""Generate a setup.py file for:
Project Name: {project_name}
Project Type: {project_type}
Description: {description}

Include:
1. Proper project metadata (name, version, description, author)
2. Dependencies from requirements.txt
3. Entry points if applicable
4. Package discovery
5. Classifiers for PyPI
6. Python version requirements (3.8+)
"""
    response = await llm_provider.generate_with_retry(prompt, model)
    formatted_code = await format_code(
        extract_code_block(response["response"], "python")
    )
    with open(f"{project_name}/setup.py", "w") as f:
        f.write(formatted_code)
    logging.info("setup.py created")


async def generate_makefile(project_name: str) -> None:
    """
    Generates Makefile.

    Parameters
    ----------
    project_name : str
        Name of the project
    """
    content = """# Makefile for Python project management

.PHONY: setup test lint format clean docs migrate

# Installation and setup
setup:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

venv:
	python -m venv venv
	@echo "Run 'source venv/bin/activate' to activate the virtual environment"

# Testing
test:
	pytest tests/ --cov=app

test-verbose:
	pytest tests/ -v --cov=app --cov-report=term-missing

# Code quality
lint:
	flake8 app/ tests/
	mypy app/ tests/

format:
	isort app/ tests/
	black app/ tests/

# Cleaning
clean:
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info __pycache__ *.pyc
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Documentation
docs:
	mkdocs build

docs-serve:
	mkdocs serve

# Database
migrate:
	flask db migrate -m "Auto-generated migration"

upgrade:
	flask db upgrade

# Docker
docker-build:
	docker build -t $(project_name) .

docker-run:
	docker run -p 5000:5000 $(project_name)

# Default target
all: format lint test
"""
    with open(f"{project_name}/Makefile", "w") as f:
        f.write(content)
    logging.info("Makefile created")


async def generate_component(
    component_info: Dict[str, str], model: str, llm_provider: LLMProvider
) -> str:
    """
    Generates a project component.

    Parameters
    ----------
    component_info : Dict[str, str]
        Information about the component
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions

    Returns
    -------
    str
        Generated component code
    """
    prompt = f"""Generate a complete Python module for:
Component Name: {component_info["name"]}
Description: {component_info["description"]}

Requirements:
- PEP8 compliance and type hints throughout
- Comprehensive docstrings and comments
- Error handling and logging
- Unit testability
- Modular design with single responsibility principle

Create a fully-featured, production-ready implementation.
"""
    response = await llm_provider.generate_with_retry(prompt, model)
    return extract_code_block(response["response"], "python")


async def generate_artifact(
    artifact_info: Dict[str, str],
    project_name: str,
    model: str,
    llm_provider: LLMProvider,
) -> None:
    """
    Generates an artifact file.

    Parameters
    ----------
    artifact_info : Dict[str, str]
        Information about the artifact
    project_name : str
        Name of the project
    model : str
        LLM model to use
    llm_provider : LLMProvider
        Provider for LLM interactions
    """
    file_path = os.path.join(project_name, artifact_info["name"])
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    prompt = f"""Generate {artifact_info["name"]} for project {project_name}:
Description: {artifact_info["description"]}

Ensure it is:
1. Complete and production-ready
2. Well-commented and documented
3. Following best practices for this file type
"""
    response = await llm_provider.generate_with_retry(prompt, model)

    file_ext = os.path.splitext(artifact_info["name"])[1]
    if file_ext in [".py", ".js", ".sh", ".html", ".css", ".yml", ".yaml"]:
        content = (
            extract_code_block(response["response"], file_ext[1:])
            or response["response"].strip()
        )
    else:
        content = response["response"].strip()

    with open(file_path, "w") as f:
        f.write(content)

    logging.info(f"Artifact {artifact_info['name']} created")


#######################################################
# Project Generator Class
#######################################################


class ProjectGenerator:
    """
    Main class for generating projects using LLM.

    This class provides a cohesive interface for generating projects
    with various configurations and options.
    """

    def __init__(
        self,
        project_name: str,
        project_type: str,
        description: str,
        model: str,
        llm_provider: LLMProvider,
        config: Dict[str, Any],
        blueprint_name: Optional[str] = None,
        include_docs: bool = False,
        include_static: bool = False,
        include_migrations: bool = False,
        database_url: Optional[str] = None,
    ):
        """
        Initialize the project generator.

        Parameters
        ----------
        project_name : str
            Name of the project
        project_type : str
            Type of the project (from SUPPORTED_TYPES)
        description : str
            Project description
        model : str
            LLM model to use
        llm_provider : LLMProvider
            Provider for LLM interactions
        config : Dict[str, Any]
            Configuration dictionary
        blueprint_name : str, optional
            Name of Flask-AppBuilder blueprint, by default None
        include_docs : bool, optional
            Whether to include documentation, by default False
        include_static : bool, optional
            Whether to include static assets, by default False
        include_migrations : bool, optional
            Whether to include database migrations, by default False
        database_url : str, optional
            Database connection URL for model generation, by default None
        """
        self.project_name = validate_project_name(project_name)
        self.project_type = project_type
        self.description = sanitize_input(description)
        self.model = model
        self.llm_provider = llm_provider
        self.config = config
        self.blueprint_name = blueprint_name
        self.include_docs = include_docs
        self.include_static = include_static
        self.include_migrations = include_migrations
        self.database_url = database_url
        self.max_concurrency = config.get("max_concurrency", MAX_CONCURRENCY)
        self.components = []
        self.artifacts = []

    def add_component(self, name: str, description: str) -> None:
        """
        Add a custom component to the project.

        Parameters
        ----------
        name : str
            Name of the component
        description : str
            Description of the component
        """
        self.components.append(
            {"name": name, "description": sanitize_input(description)}
        )

    def add_artifact(self, artifact_type: str) -> None:
        """
        Add an artifact to the project.

        Parameters
        ----------
        artifact_type : str
            Type of artifact (from ARTIFACT_TEMPLATES)

        Raises
        ------
        ValueError
            If the artifact type is invalid
        """
        if artifact_type not in ARTIFACT_TEMPLATES:
            raise ValueError(f"Invalid artifact type: {artifact_type}")
        self.artifacts.append(artifact_type)

    async def generate(self) -> None:
        """
        Generate the complete project.

        This method orchestrates the generation of all project components,
        files, and artifacts.

        Raises
        ------
        GenerationError
            If project generation fails
        """
        try:
            # 1. Create project structure
            logging.info(f"Creating project structure for {self.project_name}")
            create_project_directory(
                self.project_name,
                self.blueprint_name,
                self.include_docs,
                self.include_static,
                self.include_migrations,
            )
            ensure_dev_dependencies(self.project_name)

            # 2. Setup task objects
            tasks = []

            # 3. Create base tasks
            template = PYTHON_TEMPLATES.get(
                self.project_type, PYTHON_TEMPLATES["general_app"]
            )

            # 4. Handle special projects
            if self.project_type == "sqlalchemy_models" and self.database_url:
                # Generate models from database
                logging.info(
                    f"Generating SQLAlchemy models from database: {self.database_url}"
                )
                models_dir = os.path.join(self.project_name, "models")
                tasks.append(
                    Task(
                        generate_db_models,
                        args=(
                            self.database_url,
                            models_dir,
                            self.model,
                            self.llm_provider,
                        ),
                        name="generate_models",
                    )
                )

                if self.include_migrations:
                    # Add alembic migration setup
                    tasks.append(
                        Task(
                            setup_alembic,
                            args=(
                                self.project_name,
                                "models",
                                self.database_url,
                                self.model,
                                self.llm_provider,
                            ),
                            dependencies=[Task(lambda: None, name="generate_models")],
                            name="setup_alembic",
                        )
                    )

                if "flask_appbuilder" in self.project_type:
                    # Generate Flask-AppBuilder views for models
                    views_dir = os.path.join(self.project_name, "app", "views")
                    tasks.append(
                        Task(
                            generate_fab_views,
                            args=(models_dir, views_dir, self.model, self.llm_provider),
                            dependencies=[Task(lambda: None, name="generate_models")],
                            name="generate_views",
                        )
                    )
            else:
                # Generate files from template
                tasks.append(
                    Task(
                        process_files_concurrently,
                        args=(
                            template["files"],
                            self.project_name,
                            self.model,
                            self.llm_provider,
                            self.blueprint_name,
                            self.max_concurrency,
                        ),
                        name="process_files",
                    )
                )

            # 5. Add common files
            common_files = [
                Task(
                    generate_readme,
                    args=(
                        self.project_name,
                        self.project_type,
                        self.description,
                        self.model,
                        self.llm_provider,
                    ),
                    name="generate_readme",
                ),
                Task(
                    generate_makefile,
                    args=(self.project_name,),
                    name="generate_makefile",
                ),
                Task(
                    generate_setup_py,
                    args=(
                        self.project_name,
                        self.project_type,
                        self.description,
                        self.model,
                        self.llm_provider,
                    ),
                    name="generate_setup",
                ),
            ]

            tasks.extend(common_files)

            # 6. Add custom components
            if self.components:
                for comp in self.components:
                    comp_name = comp["name"]
                    tasks.append(
                        Task(
                            self._generate_component,
                            args=(comp,),
                            name=f"generate_component_{comp_name}",
                        )
                    )

            # 7. Add artifacts
            if self.artifacts:
                for artifact_type in self.artifacts:
                    for file_info in ARTIFACT_TEMPLATES[artifact_type]["files"]:
                        tasks.append(
                            Task(
                                generate_artifact,
                                args=(
                                    file_info,
                                    self.project_name,
                                    self.model,
                                    self.llm_provider,
                                ),
                                name=f"generate_artifact_{file_info['name']}",
                            )
                        )

            # 8. Execute all tasks
            logging.info("Starting project generation")
            await run_task_graph(tasks, self.max_concurrency)

            # 9. Apply code formatting to the entire project
            if self.config.get("format_code", True):
                logging.info("Formatting generated code")
                tool_status = check_tools_installed()
                missing_tools = [
                    name for name, installed in tool_status.items() if not installed
                ]

                if missing_tools and self.config.get("auto_install_tools", False):
                    install_missing_tools(missing_tools)

                if all(installed for _, installed in tool_status.items()):
                    subprocess.run(["isort", self.project_name], check=False)
                    subprocess.run(["black", self.project_name], check=False)

            # 10. Setup virtual environment if requested
            if self.config.get("setup_virtualenv", False):
                logging.info("Setting up virtual environment")
                await setup_virtual_env(self.project_name)

            logging.info(f"Project {self.project_name} generated successfully")

        except Exception as e:
            logging.error(f"Project generation failed: {str(e)}")
            raise GenerationError(f"Failed to generate project: {str(e)}") from e

    async def _generate_component(self, comp: Dict[str, str]) -> None:
        """
        Generate a custom component.

        Parameters
        ----------
        comp : Dict[str, str]
            Component information dictionary
        """
        code = await generate_component(comp, self.model, self.llm_provider)
        formatted_code = await format_code(code)

        with open(f"{self.project_name}/app/{comp['name']}.py", "w") as f:
            f.write(formatted_code)

        logging.info(f"Generated component {comp['name']}")


#######################################################
# CLI Implementation
#######################################################


async def interactive_project_setup() -> ProjectGenerator:
    """
    Interactive setup for project generation.

    Returns
    -------
    ProjectGenerator
        Configured project generator
    """
    print("\n=== Enhanced Python Project Generator ===")
    print(
        "This tool generates structured Python projects with SQLAlchemy and Flask-AppBuilder support"
    )
    print("Supported types:", ", ".join(SUPPORTED_TYPES))

    try:
        # 1. Load configuration
        config = load_config()

        # 2. Get project description
        description = input("\nDescribe your project: ").strip()
        if not description:
            raise ValueError("Description required")

        # 3. Detect or select project type
        project_type = detect_project_type(description)
        print(f"\nDetected type: {project_type}")

        choice = input(f"Use {project_type}? (Y/n/list): ").strip().lower()
        if choice == "list":
            print("\nAvailable project types:")
            for i, ptype in enumerate(SUPPORTED_TYPES, 1):
                print(f"{i}. {ptype} - {PYTHON_TEMPLATES[ptype]['description']}")

            choice = input("\nSelect project type (number): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(SUPPORTED_TYPES):
                    project_type = SUPPORTED_TYPES[idx]
                else:
                    print(f"Invalid selection, using {project_type}")
            except ValueError:
                print(f"Invalid input, using {project_type}")
        elif choice and choice != "y":
            custom_type = input("Enter project type: ").strip()
            if custom_type in SUPPORTED_TYPES:
                project_type = custom_type
            else:
                print(f"Invalid project type, using {project_type}")

        # 4. Get project name
        project_name = (
            input("\nProject name (default: my_project): ").strip() or "my_project"
        )
        project_name = validate_project_name(project_name)

        # 5. Setup LLM provider
        llm_provider = OllamaProvider()

        # 6. Select model
        models = llm_provider.get_available_models()
        print("\nAvailable models:", ", ".join(models))
        default_model = config.get("default_model", DEFAULT_LLM)
        model = (
            input(f"Select model (default: {default_model}): ").strip() or default_model
        )

        if model not in models:
            print(f"Warning: {model} not found, using {default_model}")
            model = default_model

        # 7. Get additional options
        blueprint_name = None
        if "blueprint" in project_type:
            blueprint_name = input("Blueprint name: ").strip() or "main"

        include_docs = input("Include docs? (y/N): ").lower() == "y"
        include_static = input("Include static files? (y/N): ").lower() == "y"

        # 8. Database configuration for SQLAlchemy models
        database_url = None
        include_migrations = False

        if "sqlalchemy" in project_type or "flask_appbuilder" in project_type:
            db_config = input("Configure database connection? (y/N): ").lower() == "y"
            if db_config:
                db_type = (
                    input("Database type (postgresql/mysql/sqlite) [postgresql]: ")
                    .strip()
                    .lower()
                    or "postgresql"
                )

                if db_type == "sqlite":
                    db_path = (
                        input("SQLite database path [app.db]: ").strip() or "app.db"
                    )
                    database_url = f"sqlite:///{db_path}"
                else:
                    db_host = (
                        input("Database host [localhost]: ").strip() or "localhost"
                    )
                    db_port = input(
                        f"Database port [{5432 if db_type == 'postgresql' else 3306}]: "
                    ).strip() or (5432 if db_type == "postgresql" else 3306)
                    db_name = input("Database name: ").strip()
                    db_user = input("Database user: ").strip()
                    db_pass = input("Database password: ").strip()

                    if db_type == "postgresql":
                        database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
                    else:  # mysql
                        database_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

                include_migrations = (
                    input("Include database migrations setup? (Y/n): ").lower() != "n"
                )

        # 9. Configure custom components
        components = []
        if input("Add custom components? (y/N): ").lower() == "y":
            while True:
                name = input("Component name (or Enter to finish): ").strip()
                if not name:
                    break
                desc = input("Component description: ").strip()
                components.append({"name": name, "description": desc})

        # 10. Configure artifacts
        artifacts = []
        if input("Generate deployment artifacts? (y/N): ").lower() == "y":
            print("Available artifacts:", ", ".join(ARTIFACT_TEMPLATES.keys()))
            selected = input("Select artifacts (comma-separated): ").split(",")
            artifacts = [a.strip() for a in selected if a.strip() in ARTIFACT_TEMPLATES]

        # 11. Create generator
        generator = ProjectGenerator(
            project_name=project_name,
            project_type=project_type,
            description=description,
            model=model,
            llm_provider=llm_provider,
            config=config,
            blueprint_name=blueprint_name,
            include_docs=include_docs,
            include_static=include_static,
            include_migrations=include_migrations,
            database_url=database_url,
        )

        # 12. Add components and artifacts
        for comp in components:
            generator.add_component(comp["name"], comp["description"])

        for artifact in artifacts:
            generator.add_artifact(artifact)

        return generator

    except (ValueError, ValidationError) as e:
        print(f"Error: {str(e)}")
        raise


async def main() -> None:
    """
    Main entry point for the application.
    """
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="Enhanced LLM-powered Python project generator"
        )
        parser.add_argument("--project", help="Project name")
        parser.add_argument("--type", choices=SUPPORTED_TYPES, help="Project type")
        parser.add_argument("--description", help="Project description")
        parser.add_argument("--model", help="LLM model to use")
        parser.add_argument(
            "--blueprint", help="Blueprint name for Flask-AppBuilder projects"
        )
        parser.add_argument("--database-url", help="Database URL for SQLAlchemy models")
        parser.add_argument(
            "--components",
            help="Custom components (comma-separated name:description pairs)",
        )
        parser.add_argument(
            "--artifacts", help="Deployment artifacts (comma-separated)"
        )
        parser.add_argument(
            "--include-docs",
            action="store_true",
            help="Include documentation directories",
        )
        parser.add_argument(
            "--include-static",
            action="store_true",
            help="Include static asset directories",
        )
        parser.add_argument(
            "--include-migrations",
            action="store_true",
            help="Include database migration setup",
        )
        parser.add_argument(
            "--max-concurrency", type=int, help="Maximum concurrent generation tasks"
        )
        parser.add_argument("--config", help="Path to configuration file")
        parser.add_argument(
            "--interactive", action="store_true", help="Run in interactive mode"
        )

        args = parser.parse_args()

        # Load configuration
        config_path = args.config or DEFAULT_CONFIG_PATH
        config = load_config(config_path)

        if args.max_concurrency:
            config["max_concurrency"] = args.max_concurrency

        # Create LLM provider
        llm_provider = OllamaProvider()

        # Run in interactive mode or with command line arguments
        if args.interactive or not (args.project and args.description):
            generator = await interactive_project_setup()
        else:
            # Use command line arguments
            project_type = args.type or detect_project_type(args.description)
            model = args.model or config.get("default_model", DEFAULT_LLM)

            generator = ProjectGenerator(
                project_name=args.project,
                project_type=project_type,
                description=args.description,
                model=model,
                llm_provider=llm_provider,
                config=config,
                blueprint_name=args.blueprint,
                include_docs=args.include_docs,
                include_static=args.include_static,
                include_migrations=args.include_migrations,
                database_url=args.database_url,
            )

            # Add components if specified
            if args.components:
                for comp_str in args.components.split(","):
                    parts = comp_str.split(":")
                    if len(parts) == 2:
                        name, desc = parts
                        generator.add_component(name.strip(), desc.strip())

            # Add artifacts if specified
            if args.artifacts:
                for artifact in args.artifacts.split(","):
                    artifact = artifact.strip()
                    if artifact in ARTIFACT_TEMPLATES:
                        generator.add_artifact(artifact)

        # Generate the project
        await generator.generate()

        print(f"\n✅ Project generated in '{generator.project_name}'")
        print("Next steps:")
        print(f"  cd {generator.project_name}")
        print("  pip install -r requirements.txt")
        print("  make test")

    except Exception as e:
        logging.error(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    asyncio.run(main())
