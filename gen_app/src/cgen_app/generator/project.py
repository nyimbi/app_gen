import asyncio
from pathlib import Path
import os
import json
from typing import Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import logging
from core.config import Config
from models.components import Structure, Component
from utils.prompts import PromptTemplate
from clients.llm import LLMClient
from utils.verifier import CodeVerifier
from generator.resolver import DependencyResolver

console = Console()
logger = logging.getLogger("appgen")


class ProjectGenerator:
    def __init__(self):
        self.plan = {}
        self.structure = None
        self.generated_code = {}
        self.generated_tests = {}

    async def generate_component_async(
        self, component: Component, file_path: str
    ) -> str:
        with console.status(f"Generating {component.type} '{component.name}'..."):
            prompt = PromptTemplate.get(
                "component",
                component_type=component.type,
                component_name=component.name,
                file_path=file_path,
                description=component.description,
                requirements=component.requirements,
                dependencies=", ".join(component.dependencies),
            )
            code = await LLMClient.generate_async(
                prompt, file_path, expected_type="code"
            )
            valid, error = CodeVerifier.verify_syntax(code)
            if not valid and Config.options.attempt_repair:
                code = CodeVerifier.repair_syntax_errors(code, error)
                valid, error = CodeVerifier.verify_syntax(code)
            return code

    async def generate_test_async(
        self, component: Component, file_path: str, code: str
    ) -> str:
        with console.status(f"Generating tests for '{component.name}'..."):
            prompt = PromptTemplate.get(
                "test",
                component_type=component.type,
                component_name=component.name,
                file_path=file_path,
                component_code=code,
            )
            return await LLMClient.generate_async(
                prompt, file_path, expected_type="code"
            )

    async def plan_development_async(self, description: str) -> Dict:
        with console.status("Planning development..."):
            prompt = PromptTemplate.get("plan")
            plan_json = await LLMClient.generate_async(
                prompt, description, expected_type="json"
            )
            from utils.parser import OutputParser

            return OutputParser.clean_and_verify_json(plan_json)

    async def create_directory_structure_async(self, plan: Dict) -> Structure:
        with console.status("Creating directory structure..."):
            prompt = PromptTemplate.get("structure")
            structure_json = await LLMClient.generate_async(
                prompt, json.dumps(plan), expected_type="json"
            )
            from utils.parser import OutputParser

            return Structure.from_dict(
                OutputParser.clean_and_verify_json(structure_json)
            )

    async def generate_code_components_async(
        self, structure: Structure
    ) -> Dict[str, str]:
        code_files = {}
        generation_order = DependencyResolver.get_generation_order(structure)
        semaphore = asyncio.Semaphore(Config.options.concurrency_limit)

        async def generate_with_semaphore(file_path, component):
            async with semaphore:
                return await self.generate_component_async(component, file_path)

        tasks = [
            (
                file_path,
                comp,
                asyncio.create_task(generate_with_semaphore(file_path, comp)),
            )
            for file_path, comp in generation_order
        ]
        for file_path, component, task in tasks:
            component.generated_code = await task
        for file in structure.files:
            code_files[file.path] = "\n\n".join(
                comp.generated_code for comp in file.components if comp.generated_code
            )
        return code_files

    async def create_tests_async(self, structure: Structure) -> Dict[str, str]:
        tests = {}
        semaphore = asyncio.Semaphore(Config.options.concurrency_limit)

        async def generate_test_with_semaphore(component, file_path):
            async with semaphore:
                if component.tests_required and component.generated_code:
                    return await self.generate_test_async(
                        component, file_path, component.generated_code
                    )
                return None

        test_tasks = {}
        for file in structure.files:
            test_file = f"tests/test_{os.path.basename(file.path)}"
            test_tasks[test_file] = [
                (
                    comp,
                    asyncio.create_task(generate_test_with_semaphore(comp, file.path)),
                )
                for comp in file.components
                if comp.tests_required
            ]
        for test_file, tasks in test_tasks.items():
            test_content = [await task for _, task in tasks if await task]
            if test_content:
                tests[test_file] = "\n\n".join(test_content)
        return tests

    def build_project(
        self, code: Dict[str, str], tests: Dict[str, str], structure: Structure
    ):
        output_dir = Path(Config.options.output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            files_task = progress.add_task(
                "Creating project files...", total=len(code) + len(tests)
            )
            for path, content in code.items():
                self._write_file(output_dir, path, content)
                progress.update(files_task, advance=1)
            for path, content in tests.items():
                self._write_file(output_dir, path, content)
                progress.update(files_task, advance=1)
            if not any(f.path == "setup.py" for f in structure.files):
                self._write_file(
                    output_dir, "setup.py", self._generate_setup_py(structure)
                )

    def _write_file(self, base_dir: Path, path: str, content: str):
        full_path = base_dir / path
        full_path.parent.mkdir(exist_ok=True, parents=True)
        full_path.write_text(content)
        logger.debug(f"Created: {full_path}")

    def _generate_setup_py(self, structure: Structure) -> str:
        project_name = (
            os.path.basename(Config.options.output_dir)
            if Config.options.output_dir != "generated_project"
            else "generated_app"
        )
        packages = {
            file.path.split("/")[0]
            for file in structure.files
            if file.path.endswith(".py")
            and "/" in file.path
            and file.path.split("/")[0] != "tests"
        }
        return f"""
from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages={list(packages) if packages else "find_packages()"},
    install_requires=[],
    author="AI Generator",
    description="Generated Python application",
    python_requires='>=3.8',
)
"""

    async def iterative_development_async(
        self, description: str, max_iterations: int = 5
    ):
        from utils.cache import GenerationCache

        GenerationCache.initialize()
        PromptTemplate.load_templates()
        iteration = 0
        while iteration < max_iterations:
            console.rule(f"[bold green]Iteration {iteration + 1}")
            self.plan = await self.plan_development_async(description)
            self.structure = await self.create_directory_structure_async(self.plan)
            self.generated_code = await self.generate_code_components_async(
                self.structure
            )
            self.generated_tests = await self.create_tests_async(self.structure)
            self.build_project(
                self.generated_code, self.generated_tests, self.structure
            )
            if input("Approve project? (y/n): ").lower() == "y":
                break
            iteration += 1
            feedback = input("Enter feedback: ")
            description += f"\nITERATION {iteration} FEEDBACK: {feedback}"

    def iterative_development(self, description: str, max_iterations: int = 5):
        asyncio.run(self.iterative_development_async(description, max_iterations))
