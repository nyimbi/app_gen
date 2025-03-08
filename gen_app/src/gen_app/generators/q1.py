"""
AI-Powered Application Generator using Ollama with Component-Based Generation

This program creates Python applications by generating code components iteratively
to circumvent LLM token limits and ensure plan conformance.
"""

import os
import json
import logging
from time import sleep
import ollama
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("appgen.log"), logging.StreamHandler()],
)


class Config:
    MODEL = "qwen2.5:32b"
    TEMPERATURE = 0.2
    OUTPUT_DIR = "generated_project"
    MAX_RETRIES = 3


def generate_component(prompt: str, context: str) -> str:
    """Generate component with error handling and retries"""
    full_prompt = f"{context}\n\n{prompt}\nRespond with ONLY valid Python code or JSON, no markdown."

    for attempt in range(Config.MAX_RETRIES):
        try:
            response = ollama.generate(
                model=Config.MODEL,
                prompt=full_prompt,
                options={"temperature": Config.TEMPERATURE},
            )
            return response["response"].strip()
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            sleep(2**attempt)

    raise Exception("Failed to generate component")


def plan_development(description: str) -> Dict:
    """Generate detailed development plan with component breakdown"""
    prompt = """
    Create a development plan with:
    1. Component architecture
    2. File structure
    3. Detailed component specifications
    4. Dependencies
    Return strict JSON without markdown."""

    plan = generate_component(prompt, description)
    return json.loads(plan)


def create_directory_structure(plan: Dict) -> Dict:
    """Generate detailed directory structure with component specs"""
    prompt = """
    Create directory structure with:
    - File paths
    - Component types (class/function/module)
    - Component descriptions
    - Dependencies between components
    Return JSON with 'structure' and 'files' keys."""

    structure = generate_component(prompt, json.dumps(plan))
    structure = json.loads(structure)
    validate_structure(structure)
    return structure


def validate_structure(structure: Dict):
    """Validate component-based structure"""
    required = {"structure", "files"}
    if missing := required - structure.keys():
        raise ValueError(f"Missing: {missing}")

    for file in structure["files"]:
        required_file_keys = {"path", "components"}
        if missing := required_file_keys - file.keys():
            raise ValueError(f"Invalid file {file.get('path')}: missing {missing}")

        for comp in file["components"]:
            required_comp = {"name", "type", "description"}
            if missing := required_comp - comp.keys():
                raise ValueError(
                    f"Invalid component {comp.get('name')}: missing {missing}"
                )


def generate_code_components(structure: Dict) -> Dict[str, str]:
    """Generate code components iteratively and combine into files"""
    code_files = {}

    for file in structure["files"]:
        file_content = []
        for comp in file["components"]:
            prompt = f"""
            Generate Python {comp["type"]} '{comp["name"]}' for {file["path"]}:
            Description: {comp["description"]}
            Requirements: {comp.get("requirements", "")}
            Dependencies: {comp.get("dependencies", "")}
            Include:
            - Type hints
            - Docstrings
            - Error handling
            Return ONLY valid Python code."""

            component_code = generate_component(prompt, file["path"])
            file_content.append(component_code.strip())

        code_files[file["path"]] = "\n\n".join(file_content)

    return code_files


def create_tests(structure: Dict, code_components: Dict) -> Dict[str, str]:
    """Generate component-specific test cases"""
    tests = {}

    for file in structure["files"]:
        test_file = f"tests/test_{os.path.basename(file['path'])}"
        test_content = []

        for comp in file["components"]:
            prompt = f"""
            Create pytest cases for {comp["type"]} '{comp["name"]}' in {file["path"]}:
            Code:
            {code_components[file["path"]]}
            Include:
            - Fixtures
            - Parameterization
            - Edge cases
            - Mocks if needed
            - Assertions
            Return ONLY valid Python code."""

            test_code = generate_component(prompt, comp["description"])
            test_content.append(test_code.strip())

        tests[test_file] = "\n\n".join(test_content)

    return tests


def build_project(code: Dict, tests: Dict, structure: Dict):
    """Build project with component files"""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    for path, content in code.items():
        write_file(Config.OUTPUT_DIR, path, content)

    for path, content in tests.items():
        write_file(Config.OUTPUT_DIR, path, content)


def write_file(base_dir: str, path: str, content: str):
    """Write file with directory creation"""
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w") as f:
        f.write(content)
    logging.info(f"Created: {full_path}")


def iterative_development(description: str, max_iterations: int = 5):
    """Development loop with component verification"""
    iteration = 0
    approved = False

    while iteration < max_iterations and not approved:
        try:
            logging.info(f"Iteration {iteration + 1}")
            plan = plan_development(description)
            structure = create_directory_structure(plan)

            code = generate_code_components(structure)
            tests = create_tests(structure, code)

            build_project(code, tests, structure)

            user_input = input("Approve project? (y/n): ").lower()
            if user_input == "y":
                approved = True
                logging.info("Project approved!")
            else:
                iteration += 1
                feedback = input("Enter feedback (specific components to modify): ")
                description += f"\nITERATION {iteration} FEEDBACK: {feedback}"

        except Exception as e:
            logging.error(f"Iteration failed: {str(e)}")
            iteration += 1


if __name__ == "__main__":
    description = input("Enter application description: ")
    iterative_development(description)
