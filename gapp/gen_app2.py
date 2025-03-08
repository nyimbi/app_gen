import json
import os
import asyncio
import ollama
from concurrent.futures import ThreadPoolExecutor

# User-selectable LLM model (default to 'mistral')
DEFAULT_LLM = "mistral"

# Updated Python Project Templates
PYTHON_TEMPLATES = {
    "flask_api": {
        "description": "A Flask-based REST API.",
        "files": [
            {"name": "app.py", "description": "Main Flask application."},
            {
                "name": "requirements.txt",
                "description": "Dependencies for the Flask app.",
            },
            {
                "name": "tests/test_app.py",
                "description": "Unit tests for the Flask API.",
            },
        ],
    },
    "flask_appbuilder": {
        "description": "A full Flask-AppBuilder application with models, mixins, and blueprints.",
        "files": [
            {
                "name": "app/__init__.py",
                "description": "Initialize Flask-AppBuilder application.",
            },
            {
                "name": "app/models.py",
                "description": "Flask-AppBuilder models with SQLAlchemy relationships.",
            },
            {
                "name": "app/views.py",
                "description": "Flask-AppBuilder views and routes.",
            },
            {"name": "app/mixins.py", "description": "Custom mixins for models."},
            {
                "name": "app/blueprints/sample_blueprint.py",
                "description": "Sample Flask Blueprint.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for Flask-AppBuilder.",
            },
            {
                "name": "tests/test_app.py",
                "description": "Unit tests for the Flask-AppBuilder app.",
            },
        ],
    },
    "flask_appbuilder_mixins": {
        "description": "Flask-AppBuilder models with custom mixins for reusability.",
        "files": [
            {
                "name": "app/mixins.py",
                "description": "Custom mixins for Flask-AppBuilder models.",
            },
            {
                "name": "app/models.py",
                "description": "Flask-AppBuilder models using mixins.",
            },
        ],
    },
    "flask_appbuilder_blueprint": {
        "description": "A Flask-AppBuilder blueprint with multiple files.",
        "files": [
            {
                "name": "app/blueprints/<blueprint_name>/routes.py",
                "description": "API routes for the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/models.py",
                "description": "SQLAlchemy models for the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/views.py",
                "description": "Flask-AppBuilder views for the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/forms.py",
                "description": "WTForms forms for user input.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/tests.py",
                "description": "Unit tests for the blueprint.",
            },
        ],
    },
    "cli_tool": {
        "description": "A command-line Python application.",
        "files": [
            {"name": "main.py", "description": "Main entry point for CLI tool."},
            {"name": "requirements.txt", "description": "Dependencies."},
            {"name": "tests/test_main.py", "description": "Unit tests."},
        ],
    },
    "fastapi_service": {
        "description": "A FastAPI microservice.",
        "files": [
            {"name": "main.py", "description": "Main FastAPI application."},
            {"name": "requirements.txt", "description": "Dependencies."},
            {
                "name": "tests/test_main.py",
                "description": "Unit tests for FastAPI endpoints.",
            },
        ],
    },
}


def detect_project_type(prompt):
    """Determine the most suitable Python project type based on the user prompt."""
    prompt_lower = prompt.lower()
    if "mixin" in prompt_lower:
        return "flask_appbuilder_mixins"
    elif "blueprint" in prompt_lower or "flask blueprint" in prompt_lower:
        return "flask_appbuilder_blueprint"
    elif "flask appbuilder" in prompt_lower:
        return "flask_appbuilder"
    elif "api" in prompt_lower:
        return "flask_api"
    elif "cli" in prompt_lower or "command line" in prompt_lower:
        return "cli_tool"
    elif "fastapi" in prompt_lower:
        return "fastapi_service"
    else:
        return "flask_api"  # Default to Flask API


def create_project_directory(project_name, blueprint_name=None, include_docs=False, include_static=False):
    """Creates the main project directory structure for the project.

    Args:
        project_name (str): The name of the project.
        blueprint_name (str, optional): The name of the blueprint to create.
        include_docs (bool, optional): Whether to include a documentation directory.
        include_static (bool, optional): Whether to include a static files directory.
    """
    # Create the main project directory
    os.makedirs(project_name, exist_ok=True)

    # Create subdirectories
    os.makedirs(os.path.join(project_name, "app"), exist_ok=True)

    if blueprint_name:
        os.makedirs(os.path.join(project_name, f"app/blueprints/{blueprint_name}"), exist_ok=True)

    os.makedirs(os.path.join(project_name, "tests"), exist_ok=True)

    if include_docs:
        os.makedirs(os.path.join(project_name, "docs"), exist_ok=True)

    if include_static:
        os.makedirs(os.path.join(project_name, "app/static"), exist_ok=True)

    os.makedirs(os.path.join(project_name, "app/templates"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "app/models"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "app/routes"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "config"), exist_ok=True)

    print(f"Project '{project_name}' directory structure created successfully.")


async def identify_functions(file_info, model=DEFAULT_LLM):
    """Identifies all functions that need to be generated in a given Python file."""
    function_identification_prompt = f"""Analyze the purpose of this file and list the functions it should contain.

    File Name: {file_info["name"]}
    Purpose: {file_info["description"]}

    Provide output in JSON format:
    {{
        "functions": [
            {{
                "name": "function_name",
                "description": "What this function does"
            }}
        ]
    }}
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool,
            lambda: ollama.generate(model=model, prompt=function_identification_prompt),
        )

    try:
        function_data = json.loads(response["response"])
        return function_data["functions"]
    except json.JSONDecodeError:
        print(f"⚠ Error parsing function list for {file_info['name']}.")
        return []


async def generate_function(function_info, model=DEFAULT_LLM):
    """Generates an individual function."""
    function_prompt = f"""Generate a complete Python function.

    Function Name: {function_info["name"]}
    Purpose: {function_info["description"]}

    Ensure:
    - It follows PEP8 style guidelines.
    - It includes docstrings.
    - It uses appropriate error handling.
    - It is modular and reusable.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=function_prompt)
        )

    return response["response"]


async def review_code(file_content, model=DEFAULT_LLM):
    """Uses an LLM to review and improve generated code."""
    review_prompt = f"""Review the following Python code for correctness, best practices, and security issues:

    ```python
    {file_content}
    ```

    If improvements are needed, provide the corrected version.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=review_prompt)
        )

    return response["response"]


async def generate_code_async(
    file_info, project_name, model=DEFAULT_LLM, blueprint_name=None
):
    """Generates code for a Python file by first identifying functions, generating them, and then assembling the final file."""
    file_path = os.path.join(
        project_name,
        file_info["name"].replace(
            "<blueprint_name>", blueprint_name if blueprint_name else "blueprint"
        ),
    )

    print(f"🔍 Identifying functions for {file_info['name']}...")
    functions = await identify_functions(file_info, model)

    if not functions:
        print(
            f"⚠ No functions identified for {file_info['name']}. Skipping file generation."
        )
        return

    print(f"🚀 Generating functions for {file_info['name']}...")
    tasks = [generate_function(func, model) for func in functions]
    generated_functions = await asyncio.gather(*tasks)

    # Assemble and review the file
    raw_code = "\n\n".join(generated_functions)
    reviewed_code = await review_code(raw_code, model)

    with open(file_path, "w") as f:
        f.write(f'"""\n{file_info["description"]}\n"""\n\n')
        f.write(reviewed_code)

    print(f"✅ File {file_info['name']} created successfully.")


async def process_files_concurrently(files, project_name, model, blueprint_name=None):
    """Handles the generation of multiple files in parallel."""
    tasks = [
        generate_code_async(file, project_name, model, blueprint_name) for file in files
    ]
    await asyncio.gather(*tasks)


def generate_code(prompt, model=DEFAULT_LLM):
    """Main function that generates a structured Python project by generating each function separately before assembling files."""

    project_type = detect_project_type(prompt)
    project_template = PYTHON_TEMPLATES[project_type]

    # If the user is generating a blueprint, ask for the name
    blueprint_name = None
    if project_type == "flask_appbuilder_blueprint":
        blueprint_name = input("Enter the name of your blueprint: ")

    print(
        f"\n🔍 Detected Project Type: {project_type} ({project_template['description']})"
    )

    project_name = "generated_python_project"
    create_project_directory(project_name, blueprint_name)

    print("\n🚀 Generating project files...")
    asyncio.run(
        process_files_concurrently(
            project_template["files"], project_name, model, blueprint_name
        )
    )

    print(
        "\n🎉 Project generation complete! Files are in 'generated_python_project' directory."
    )


if __name__ == "__main__":
    user_input = input("Describe the Python application you want to generate:\n")
    chosen_model = input("Choose an LLM model (default is 'mistral'): ") or DEFAULT_LLM
    generate_code(user_input, chosen_model)
    asyncio.run(
        process_files_concurrently(
            project_template["files"], project_name, model, blueprint_name
        )
    )

    print(
        "\n🎉 Project generation complete! Files are in 'generated_python_project' directory."
    )

if __name__ == "__main__":
    user_input = input("Describe the Python application you want to generate:\n")
    chosen_model = input("Choose an LLM model (default is 'mistral'): ") or DEFAULT_LLM
    generate_code(user_input, chosen_model)
