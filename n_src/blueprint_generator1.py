import asyncio
import aiofiles
import os
import re
from typing import Dict, List, Optional
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, AIMessage
from rich import print
from rich.progress import Progress
import yaml
from ratelimit import limits, sleep_and_retry

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

API_KEY = config['anthropic_api_key']
RATE_LIMIT = config['rate_limit']
RATE_PERIOD = config['rate_period']
MODEL_NAME = config['model_name']
MAX_TOKENS = config['max_tokens']
TEMPERATURE = config['temperature']
OUTPUT_DIR = config['output_directory']

async def read_file(filename: str) -> str:
    async with aiofiles.open(filename, 'r') as f:
        return await f.read()

def camel_to_snake(name: str) -> str:
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def extract_blueprint_name(description: str) -> Optional[str]:
    match = re.search(r'^(\w+)Blueprint:', description)
    return match.group(1) if match else None

@sleep_and_retry
@limits(calls=RATE_LIMIT, period=RATE_PERIOD)
async def generate_content(chat: ChatAnthropic, prompt: str, context: str = "") -> str:
    messages = [
        ("system", "You are an expert Python developer specializing in Flask-AppBuilder and SQLAlchemy."),
        ("human", f"{prompt}\n\nContext: {context}"),
    ]

    full_content = ""
    while True:
        response = await chat.ainvoke(messages)
        content_chunk = response.content

        if "[CONTENT_CONTINUES]" in content_chunk:
            full_content += content_chunk.replace("[CONTENT_CONTINUES]", "").strip()
            print("\t continue")

            continue_prompt = f"""Please continue the implementation where you left off. Here are the last few lines for context:

            {full_content[-700:]}

            Continue the implementation, and remember to end with [CONTENT_CONTINUES] if you're not finished."""

            messages.append(AIMessage(content=content_chunk))
            messages.append(HumanMessage(content=continue_prompt))
        else:
            full_content += content_chunk
            break

    return full_content

async def create_directory(path: str):
    os.makedirs(path, exist_ok=True)

async def write_file(filename: str, content: str):
    async with aiofiles.open(filename, 'w') as f:
        await f.write(content)

async def generate_blueprint(description: str, progress: Progress, task: int):
    chat = ChatAnthropic(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        api_key=API_KEY,
        max_tokens=MAX_TOKENS
    )

    blueprint_name = extract_blueprint_name(description)
    if not blueprint_name:
        print(f"[bold red]Could not extract blueprint name from: {description}[/bold red]")
        return

    blueprint_dir = os.path.join(OUTPUT_DIR, camel_to_snake(blueprint_name))
    await create_directory(blueprint_dir)
    await create_directory(os.path.join(blueprint_dir, 'templates'))

    # Generate product specification
    print(f"[bold cyan]Generating product specification for {blueprint_name}Blueprint...[/bold cyan]")
    spec_prompt = f"""
    As an expert in Flask-AppBuilder and enterprise software architecture, create a comprehensive product specification for the following blueprint:

    {description}

    Your specification should include:
    1. Overview: A brief summary of the blueprint's purpose and main features.
    2. User Personas: Define the primary users and their needs.
    3. Functional Requirements: Detailed list of features and capabilities, organized by priority.
    4. Non-Functional Requirements: Performance, scalability, security, and usability considerations.
    5. Data Model: High-level description of key entities and their relationships.
    6. User Interface: Description of main views and user interactions.
    7. Integration Points: Any external systems or APIs the blueprint should interact with.
    8. Security Considerations: Authentication, authorization, and data protection measures.
    9. Compliance Requirements: Any industry-specific regulations or standards to adhere to.
    10. Performance Metrics: Key performance indicators and expected benchmarks.
    11. Future Extensibility: Areas for potential future enhancements.

    Ensure the specification is detailed, clear, and actionable for developers to implement the blueprint effectively.
    """
    spec_content = await generate_content(chat, spec_prompt)
    await write_file(os.path.join(blueprint_dir, 'specification.md'), spec_content)

    # Generate models.py
    print(f"[bold cyan]Generating models.py for {blueprint_name}Blueprint...[/bold cyan]")
    models_prompt = f"""
    As a senior Python developer with expertise in SQLAlchemy and PostgreSQL, create the models.py file for the following Flask-AppBuilder blueprint:

    {description}

    Use the following product specification as a guide:

    {spec_content}

    Your implementation should:
    1. Use SQLAlchemy's declarative base and latest features compatible with Flask-AppBuilder.
    2. Leverage PostgreSQL-specific features where appropriate (e.g., JSONB, array types, full-text search).
    3. Implement all necessary models, including association tables for many-to-many relationships.
    4. Use appropriate column types, ensuring efficient database design.
    5. Implement model relationships with correct backref and cascade settings.
    6. Include relevant indexes for optimizing query performance.
    7. Add check constraints and unique constraints where necessary.
    8. Implement hybrid properties and methods where they add value.
    9. Use mixins for shared functionality across models (e.g., TimestampMixin, UserMixin).
    10. Add comprehensive docstrings and type hints for better code understanding and maintenance.
    11. Implement any necessary event listeners or hooks (e.g., for data validation or preprocessing).
    12. Consider implementing custom model methods for complex business logic.

    Ensure your code follows PEP 8 style guidelines and best practices for SQLAlchemy model definition.
    """
    models_content = await generate_content(chat, models_prompt)
    await write_file(os.path.join(blueprint_dir, 'models.py'), models_content)

    # Generate views.py
    print(f"[bold cyan]Generating views.py for {blueprint_name}Blueprint...[/bold cyan]")
    views_prompt = f"""
    As an experienced Flask-AppBuilder developer, create the views.py file for the following blueprint:

    {description}

    Use the following product specification and models as a guide:

    Product Specification:
    {spec_content}

    Models:
    {models_content}

    Your implementation should include:
    1. All necessary view classes (ModelView, FormView, etc.) based on the blueprint requirements.
    2. Custom base view classes if needed for shared functionality.
    3. Proper use of Flask-AppBuilder decorators (@has_access, @action, etc.).
    4. Implementation of CRUD operations with appropriate permissions.
    5. Custom form_post, form_get, and other method overrides where necessary.
    6. Integration of any required charts or API endpoints.
    7. Implementation of custom actions and their related methods.
    8. Proper handling of file uploads if required.
    9. Integration of any necessary AJAX functionality.
    10. Implementation of search and filtering functionality.
    11. Custom widget types or field customizations if needed.
    12. Proper error handling and user feedback mechanisms.
    13. Any required API views for REST endpoints.
    14. Comprehensive docstrings and type hints for better code understanding and maintenance.

    Ensure your views are secure, efficient, and user-friendly. Follow Flask-AppBuilder best practices and conventions throughout your implementation.
    """
    views_content = await generate_content(chat, views_prompt)
    await write_file(os.path.join(blueprint_dir, 'views.py'), views_content)

    # Generate __init__.py
    print(f"[bold cyan]Generating __init__.py for {blueprint_name}Blueprint...[/bold cyan]")
    init_content = f"""
    from flask import Blueprint
    from flask_appbuilder import BaseView

    {blueprint_name.lower()} = Blueprint('{blueprint_name.lower()}', __name__, template_folder='templates')

    from . import views
    """
    await write_file(os.path.join(blueprint_dir, '__init__.py'), init_content)

    # Generate templates
    print(f"[bold cyan]Generating templates for {blueprint_name}Blueprint...[/bold cyan]")
    templates_prompt = f"""
    As a Flask-AppBuilder UI/UX expert, list and then create the necessary Jinja2 template files for the following blueprint:

    {description}

    Use the following specification, models, and views as a guide:

    Specification:
    {spec_content}

    Models:
    {models_content}

    Views:
    {views_content}

    For each template:
    1. Use proper template inheritance, extending from appropriate base templates.
    2. Implement responsive design using Bootstrap classes.
    3. Use Flask-AppBuilder's built-in macros and helpers where appropriate.
    4. Implement any necessary custom macros for reusable UI components.
    5. Ensure proper handling of form rendering and validation feedback.
    6. Implement CSRF protection on all forms.
    7. Use appropriate Jinja2 filters for data formatting and security (e.g., |safe, |escape).
    8. Optimize templates for performance, avoiding expensive operations in loops.
    9. Implement any required JavaScript for dynamic functionality.
    10. Ensure accessibility compliance (WCAG 2.1) in your HTML structure.
    11. Use Flask-Babel for internationalization if required.
    12. Implement proper error handling and user feedback mechanisms.

    Provide a list of all necessary template files, then create each one with detailed, well-structured HTML and Jinja2 code.
    """
    templates_list = await generate_content(chat, templates_prompt)

    for template in templates_list.split('\n'):
        if template.strip():
            template_name = template.strip()
            print(f"[bold cyan]Generating {template_name}...[/bold cyan]")
            template_prompt = f"""
            Create the content for the {template_name} template file for the following Flask-AppBuilder blueprint:

            {description}

            Use the following specification, models, and views as a guide:

            Specification:
            {spec_content}

            Models:
            {models_content}

            Views:
            {views_content}

            Ensure your template follows all best practices and guidelines mentioned in the previous prompt.
            """
            template_content = await generate_content(chat, template_prompt)
            await write_file(os.path.join(blueprint_dir, 'templates', template_name), template_content)

    # Generate test file
    print(f"[bold cyan]Generating test file for {blueprint_name}Blueprint...[/bold cyan]")
    test_prompt = f"""
    As a quality assurance engineer specializing in Python and Flask applications, create a comprehensive test file (test_{blueprint_name.lower()}.py) for the following Flask-AppBuilder blueprint:

    {description}

    Use the following specification, models, and views as a guide:

    Specification:
    {spec_content}

    Models:
    {models_content}

    Views:
    {views_content}

    Your test file should include:
    1. Unit tests for all models, covering:
       - Object creation and validation
       - Relationship integrity
       - Custom methods and properties
       - Edge cases and constraint violations
    2. Functional tests for all views, covering:
       - CRUD operations
       - Permission checks
       - Custom actions
       - Form submissions and validations
    3. Integration tests for:
       - API endpoints (if any)
       - Complex workflows involving multiple components
    4. Performance tests for any performance-critical operations
    5. Security tests, including:
       - Authentication and authorization checks
       - CSRF protection
       - Input validation and sanitization
    6. Mock external dependencies and services where necessary
    7. Use of fixtures and factories for test data generation
    8. Proper use of setup and teardown methods
    9. Clear, descriptive test method names and docstrings
    10. Coverage of both positive and negative test cases
    11. Use of parameterized tests for testing multiple scenarios efficiently

    Ensure your tests are comprehensive, maintainable, and follow Python testing best practices. Use pytest as the testing framework and include any necessary test utilities or helper functions.
    """
    test_content = await generate_content(chat, test_prompt)
    await write_file(os.path.join(blueprint_dir, f'test_{blueprint_name.lower()}.py'), test_content)

    progress.update(task, advance=1)

async def main():
    blueprints_list = (await read_file('blueprints_list.txt')).splitlines()

    with Progress() as progress:
        task = progress.add_task("[green]Generating blueprints...", total=len(blueprints_list))
        await asyncio.gather(*[generate_blueprint(description, progress, task) for description in blueprints_list if description.strip()])

if __name__ == "__main__":
    asyncio.run(main())
