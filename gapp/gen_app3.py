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
    elif "fastapi" in prompt_lower:
        return "fastapi_service"
    elif "cli" in prompt_lower or "command line" in prompt_lower:
        return "cli_tool"
    elif "api" in prompt_lower:
        return "flask_api"
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

    # Create subdirectories based on project structure
    os.makedirs(os.path.join(project_name, "app"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "tests"), exist_ok=True)
    
    if blueprint_name:
        os.makedirs(os.path.join(project_name, f"app/blueprints/{blueprint_name}"), exist_ok=True)

    if include_docs:
        os.makedirs(os.path.join(project_name, "docs"), exist_ok=True)

    if include_static:
        os.makedirs(os.path.join(project_name, "app/static"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "app/static/css"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "app/static/js"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "app/static/img"), exist_ok=True)

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
        # Extract JSON from the response, handling potential formatting issues
        response_text = response["response"]
        # Find JSON content between triple backticks if present
        if "```json" in response_text and "```" in response_text.split("```json", 1)[1]:
            json_str = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
            json_str = response_text.split("```", 1)[1].split("```", 1)[0].strip()
        else:
            json_str = response_text.strip()
            
        function_data = json.loads(json_str)
        return function_data["functions"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠ Error parsing function list for {file_info['name']}: {str(e)}")
        # Return a default function structure if parsing fails
        return [{"name": "main", "description": f"Main function for {file_info['name']}"}]


async def generate_function(function_info, file_info, model=DEFAULT_LLM):
    """Generates an individual function."""
    function_prompt = f"""Generate a complete Python function for a {file_info['name']} file.

    Function Name: {function_info["name"]}
    Purpose: {function_info["description"]}
    File Purpose: {file_info["description"]}

    Ensure:
    - It follows PEP8 style guidelines
    - It includes detailed docstrings with parameter and return types
    - It uses appropriate error handling
    - It is modular and reusable
    - It implements best practices for its purpose
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=function_prompt)
        )

    # Clean up code response - extract code blocks if present
    response_text = response["response"]
    if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
        code = response_text.split("```python", 1)[1].split("```", 1)[0].strip()
    elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
        code = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    else:
        code = response_text

    return code


async def generate_file_imports(file_info, functions, model=DEFAULT_LLM):
    """Generates appropriate imports for a Python file based on its functions."""
    import_prompt = f"""Generate Python import statements for a file with the following details:

    File Name: {file_info["name"]}
    File Purpose: {file_info["description"]}
    
    Functions in the file:
    {json.dumps(functions, indent=2)}
    
    Provide only the import statements, nothing else.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=import_prompt)
        )

    # Clean up response - extract code blocks if present
    response_text = response["response"]
    if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
        imports = response_text.split("```python", 1)[1].split("```", 1)[0].strip()
    elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
        imports = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    else:
        imports = response_text
        
    # Ensure imports end with a newline
    if imports and not imports.endswith("\n"):
        imports += "\n"
    
    return imports


async def review_code(file_content, file_info, model=DEFAULT_LLM):
    """Uses an LLM to review and improve generated code."""
    review_prompt = f"""Review the following Python code for {file_info['name']} implementing {file_info['description']}.
    Check for correctness, best practices, security issues, and completeness:

    ```python
    {file_content}
    ```

    Provide the improved version with any necessary corrections or enhancements.
    Return only the complete code without explanations.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=review_prompt)
        )

    # Clean up response - extract code blocks if present
    response_text = response["response"]
    if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
        reviewed_code = response_text.split("```python", 1)[1].split("```", 1)[0].strip()
    elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
        reviewed_code = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    else:
        reviewed_code = response_text

    return reviewed_code


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

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    print(f"🔍 Identifying functions for {file_info['name']}...")
    functions = await identify_functions(file_info, model)

    if not functions:
        print(
            f"⚠ No functions identified for {file_info['name']}. Generating default content."
        )
        functions = [{"name": "main", "description": f"Main function for {file_info['name']}"}]

    print(f"📚 Generating imports for {file_info['name']}...")
    imports = await generate_file_imports(file_info, functions, model)

    print(f"🚀 Generating {len(functions)} functions for {file_info['name']}...")
    tasks = [generate_function(func, file_info, model) for func in functions]
    generated_functions = await asyncio.gather(*tasks)

    # Assemble the file
    raw_code = imports + "\n\n" + "\n\n".join(generated_functions)
    
    print(f"🔍 Reviewing code for {file_info['name']}...")
    reviewed_code = await review_code(raw_code, file_info, model)

    # Ensure directory exists before writing file
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
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


async def generate_readme(project_name, project_type, description, model=DEFAULT_LLM):
    """Generates a README.md file for the project."""
    readme_prompt = f"""Generate a comprehensive README.md file for a Python project with the following details:

    Project Type: {project_type} ({PYTHON_TEMPLATES[project_type]['description']})
    Project Description: {description}
    
    Include sections for:
    - Project overview
    - Installation instructions
    - Usage examples
    - Project structure
    - Configuration
    - Testing
    - Contributing guidelines
    
    Format it with proper Markdown syntax.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=readme_prompt)
        )
    
    readme_content = response["response"]
    
    # Clean up markdown content if needed
    if "```markdown" in readme_content and "```" in readme_content.split("```markdown", 1)[1]:
        readme_content = readme_content.split("```markdown", 1)[1].split("```", 1)[0].strip()
    elif "```md" in readme_content and "```" in readme_content.split("```md", 1)[1]:
        readme_content = readme_content.split("```md", 1)[1].split("```", 1)[0].strip()
    elif "```" in readme_content and "```" in readme_content.split("```", 1)[1]:
        readme_content = readme_content.split("```", 1)[1].split("```", 1)[0].strip()
    
    with open(os.path.join(project_name, "README.md"), "w") as f:
        f.write(readme_content)
    
    print(f"📝 README.md file created successfully.")


def generate_code(prompt, model=DEFAULT_LLM):
    """Main function that generates a structured Python project by generating each function separately before assembling files."""
    try:
        project_type = detect_project_type(prompt)
        project_template = PYTHON_TEMPLATES[project_type]

        print(f"\n🔍 Detected Project Type: {project_type} ({project_template['description']})")

        # Ask the user for more details about the project
        project_name = input("Enter project name (default: generated_python_project): ") or "generated_python_project"
        
        # If the user is generating a blueprint, ask for the name
        blueprint_name = None
        if project_type == "flask_appbuilder_blueprint":
            blueprint_name = input("Enter the name of your blueprint: ")
            
        # Ask for additional configuration
        include_docs = input("Include documentation directory? (y/N): ").lower() == 'y'
        include_static = input("Include static files directory? (y/N): ").lower() == 'y'

        # Create project directory structure
        create_project_directory(project_name, blueprint_name, include_docs, include_static)

        print("\n🚀 Generating project files...")
        asyncio.run(
            process_files_concurrently(
                project_template["files"], project_name, model, blueprint_name
            )
        )
        
        # Generate README.md
        print("\n📝 Generating README.md...")
        asyncio.run(generate_readme(project_name, project_type, prompt, model))

        print(f"\n🎉 Project generation complete! Files are in '{project_name}' directory.")
        
    except Exception as e:
        print(f"❌ An error occurred during project generation: {str(e)}")


if __name__ == "__main__":
    print("🔧 Python Application Generator 🔧")
    print("====================================")
    user_input = input("Describe the Python application you want to generate:\n")
    
    # List available models from Ollama
    try:
        models_list = ollama.list()
        available_models = [model['name'] for model in models_list.get('models', [])]
        if available_models:
            print(f"\nAvailable models: {', '.join(available_models)}")
        else:
            print(f"\nNo models found. Will use default: {DEFAULT_LLM}")
    except:
        print(f"\nCould not retrieve model list. Will use default: {DEFAULT_LLM}")
    
    chosen_model = input(f"Choose an LLM model (default is '{DEFAULT_LLM}'): ") or DEFAULT_LLM
    generate_code(user_input, chosen_model)