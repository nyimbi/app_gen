# File: gen_app/generators/project_generator.py
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time

from gen_app.config import load_config
from gen_app.utils.formatting import (
    format_code,
    validate_python_code,
    extract_code_block,
)
from gen_app.utils.llm import LLMProvider, OllamaProvider


class GenerationError(Exception):
    """Base exception for generation errors."""

    pass


class ValidationError(GenerationError):
    """Raised when input validation fails."""

    pass


def validate_project_name(name: str) -> str:
    """Ensure project name is valid."""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        raise ValidationError(
            "Project name must start with a letter and contain only letters, numbers, underscores, and hyphens"
        )
    return name


class ProjectGenerator:
    """
    ProjectGenerator orchestrates the generation of a Python project.

    Parameters
    ----------
    project_name : str
        The name of the project.
    project_type : str
        The project type (e.g., 'flask_api', 'sqlalchemy_models').
    description : str
        A brief description of the project.
    model : str
        The LLM model identifier.
    llm_provider : LLMProvider
        An instance of an LLM provider.
    formatter : callable
        A function to format code.
    config : dict
        Configuration dictionary.
    options : dict
        Additional options (e.g., blueprint name, include docs).
    """

    def __init__(
        self,
        project_name: str,
        project_type: str,
        description: str,
        model: str,
        llm_provider: LLMProvider,
        formatter: callable,
        config: dict,
        **options,
    ):
        self.project_name = validate_project_name(project_name)
        self.project_type = project_type
        self.description = description.strip()
        self.model = model
        self.llm_provider = llm_provider
        self.formatter = formatter
        self.config = config
        self.options = options
        self.components = []
        self.artifacts = []

    def add_component(self, name: str, description: str) -> None:
        """Add a custom component to the project."""
        self.components.append({"name": name, "description": description.strip()})

    def add_artifact(self, artifact_type: str) -> None:
        """Add an artifact to the project."""
        self.artifacts.append(artifact_type)

    async def generate(self) -> None:
        """
        Generate the project by performing the following steps:

        1. Create the project directory structure.
        2. Generate source files, tests, and artifacts.
        3. Apply code formatting.
        4. Optionally, set up a virtual environment.
        """
        try:
            logging.info(f"Creating project structure for {self.project_name}")
            self._create_project_structure()
            await self._generate_files()
            if self.config.get("format_code", True):
                self._apply_formatting()
            if self.config.get("setup_virtualenv", False):
                await self._setup_virtual_env()
            logging.info(f"Project {self.project_name} generated successfully")
        except Exception as e:
            logging.error(f"Project generation failed: {e}")
            raise GenerationError(f"Failed to generate project: {e}") from e

    def _create_project_structure(self) -> None:
        """Create the base directory structure for the project."""
        os.makedirs(self.project_name, exist_ok=True)
        os.makedirs(os.path.join(self.project_name, "app"), exist_ok=True)
        os.makedirs(os.path.join(self.project_name, "tests"), exist_ok=True)
        with open(os.path.join(self.project_name, ".gitignore"), "w") as f:
            f.write("# Auto-generated .gitignore\n__pycache__/\n*.pyc\n")
        logging.info("Project structure created")

    async def _generate_files(self) -> None:
        """Generate all necessary project files using asynchronous tasks."""
        tasks = []
        tasks.append(asyncio.create_task(self._generate_readme()))
        # Additional file generation tasks would be added here.
        await asyncio.gather(*tasks)
        logging.info("All files generated")

    async def _generate_readme(self) -> None:
        """Generate a comprehensive README.md using the LLM."""
        prompt = f"""Generate a comprehensive README.md for the project:
Name: {self.project_name}
Type: {self.project_type}
Description: {self.description}
Include an overview, installation instructions, usage examples, and contribution guidelines.
"""
        response = await self._generate_with_retry(prompt)
        readme_content = self._extract_and_format(response, language="markdown")
        with open(os.path.join(self.project_name, "README.md"), "w") as f:
            f.write(readme_content)
        logging.info("README.md generated")

    async def _generate_with_retry(
        self, prompt: str, max_retries: int = 3, backoff_factor: float = 1.5
    ) -> dict:
        """Generate content with retry logic."""
        retries = 0
        while retries < max_retries:
            try:
                return await self.llm_provider.generate_with_retry(prompt, self.model)
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    logging.error(
                        f"LLM generation failed after {max_retries} attempts: {e}"
                    )
                    raise e
                wait_time = backoff_factor**retries
                logging.warning(f"Retry {retries} in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
        raise GenerationError("Max retries exceeded")

    def _extract_and_format(self, response: dict, language: str = "python") -> str:
        """Extract a code block from the LLM response and format it if needed."""
        code = extract_code_block(response.get("response", ""), language=language)
        if language == "python" and validate_python_code(code):
            return asyncio.run(self.formatter(code))
        return code

    def _apply_formatting(self) -> None:
        """Apply code formatting to the entire project using isort and black."""
        try:
            subprocess.run(["isort", self.project_name], check=False)
            subprocess.run(["black", self.project_name], check=False)
            logging.info("Code formatted successfully.")
        except Exception as e:
            logging.warning(f"Formatting failed: {e}")

    async def _setup_virtual_env(self) -> None:
        """Set up a virtual environment for the project."""
        env_dir = os.path.join(self.project_name, "venv")
        try:
            subprocess.run([sys.executable, "-m", "venv", env_dir], check=True)
            pip_path = (
                os.path.join(env_dir, "bin", "pip")
                if os.name != "nt"
                else os.path.join(env_dir, "Scripts", "pip")
            )
            req_path = os.path.join(self.project_name, "requirements.txt")
            if os.path.exists(req_path):
                subprocess.run([pip_path, "install", "-r", req_path], check=True)
            logging.info(f"Virtual environment created at {env_dir}")
        except Exception as e:
            logging.error(f"Virtual environment setup failed: {e}")


# Example usage:
if __name__ == "__main__":
    import asyncio

    config = load_config()
    llm_provider = OllamaProvider()
    generator = ProjectGenerator(
        project_name="my_project",
        project_type="flask_api",
        description="An example Flask API project",
        model=config.get("default_model", "mistral-nemo:12b-instruct-2407-q8_0"),
        llm_provider=llm_provider,
        formatter=format_code,
        config=config,
    )
    asyncio.run(generator.generate())
