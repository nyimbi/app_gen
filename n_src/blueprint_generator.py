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

async def read_file(filename: str) -> str:
    """
    Asynchronously read the content of a file.

    Args:
        filename (str): The name of the file to read.

    Returns:
        str: The content of the file.
    """
    async with aiofiles.open(filename, 'r') as f:
        return await f.read()

def camel_to_snake(name: str) -> str:
    """
    Convert a camelCase or PascalCase string to snake_case.

    Args:
        name (str): The string to convert.

    Returns:
        str: The converted snake_case string.
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def extract_blueprint_name(description: str) -> Optional[str]:
    """
    Extract the blueprint name from the description.

    Args:
        description (str): The blueprint description.

    Returns:
        Optional[str]: The extracted blueprint name, or None if not found.
    """
    match = re.search(r'^(\w+)Blueprint:', description)
    return match.group(1) if match else None

@sleep_and_retry
@limits(calls=RATE_LIMIT, period=RATE_PERIOD)
async def generate_content(chat: ChatAnthropic, prompt: str, context: str = "") -> str:
    """
    Generate content using the ChatAnthropic model.

    Args:
        chat (ChatAnthropic): The ChatAnthropic instance.
        prompt (str): The prompt to send to the model.
        context (str, optional): Additional context for the prompt.

    Returns:
        str: The generated content.
    """
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
    """
    Create a directory if it doesn't exist.

    Args:
        path (str): The path of the directory to create.
    """
    os.makedirs(path, exist_ok=True)

async def write_file(filename: str, content: str):
    """
    Asynchronously write content to a file.

    Args:
        filename (str): The name of the file to write.
        content (str): The content to write to the file.
    """
    async with aiofiles.open(filename, 'w') as f:
        await f.write(content)

async def generate_blueprint(description: str, progress: Progress, task: int):
    """
    Generate a complete Flask-AppBuilder blueprint based on the given description.

    Args:
        description (str): The blueprint description.
        progress (Progress): The progress bar instance.
        task (int): The task ID for updating the progress bar.
    """
    chat = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        temperature=0,
        api_key=API_KEY,
        max_tokens=8192
    )

    blueprint_name = extract_blueprint_name(description)
    if not blueprint_name:
        print(f"[bold red]Could not extract blueprint name from: {description}[/bold red]")
        return

    blueprint_dir = camel_to_snake(blueprint_name)
    await create_directory(blueprint_dir)
    await create_directory(os.path.join(blueprint_dir, 'templates'))

    # Generate product specification
    print(f"[bold cyan]Generating product specification for {blueprint_name}Blueprint...[/bold cyan]")
    spec_prompt = f"Create a detailed product specification for the following Flask-AppBuilder blueprint:\n\n{description}\n\nInclude all necessary features, user stories, and technical requirements."
    spec_content = await generate_content(chat, spec_prompt)
    await write_file(os.path.join(blueprint_dir, 'specification.md'), spec_content)

    # Generate models.py
    print(f"[bold cyan]Generating models.py for {blueprint_name}Blueprint...[/bold cyan]")
    models_prompt = f"Create the models.py file for the following Flask-AppBuilder blueprint, targeting PostgreSQL:\n\n{description}\n\nUse the following specification as a guide:\n\n{spec_content}"
    models_content = await generate_content(chat, models_prompt)
    await write_file(os.path.join(blueprint_dir, 'models.py'), models_content)

    # Generate views.py
    print(f"[bold cyan]Generating views.py for {blueprint_name}Blueprint...[/bold cyan]")
    views_prompt = f"Create the views.py file for the following Flask-AppBuilder blueprint:\n\n{description}\n\nUse the following specification and models as a guide:\n\n{spec_content}\n\n{models_content}"
    views_content = await generate_content(chat, views_prompt)
    await write_file(os.path.join(blueprint_dir, 'views.py'), views_content)

    # Generate __init__.py
    print(f"[bold cyan]Generating __init__.py for {blueprint_name}Blueprint...[/bold cyan]")
    init_content = f"from flask import Blueprint\nfrom flask_appbuilder import BaseView\n\n{blueprint_name.lower()} = Blueprint('{blueprint_name.lower()}', __name__, template_folder='templates')\n\nfrom . import views"
    await write_file(os.path.join(blueprint_dir, '__init__.py'), init_content)

    # Generate templates
    print(f"[bold cyan]Generating templates for {blueprint_name}Blueprint...[/bold cyan]")
    templates_prompt = f"List the necessary template files for the following Flask-AppBuilder blueprint:\n\n{description}\n\nUse the following specification, models, and views as a guide:\n\n{spec_content}\n\n{models_content}\n\n{views_content}"
    templates_list = await generate_content(chat, templates_prompt)

    for template in templates_list.split('\n'):
        if template.strip():
            template_name = template.strip()
            print(f"[bold cyan]Generating {template_name}...[/bold cyan]")
            template_prompt = f"Create the content for the {template_name} template file for the following Flask-AppBuilder blueprint:\n\n{description}\n\nUse the following specification, models, and views as a guide:\n\n{spec_content}\n\n{models_content}\n\n{views_content}"
            template_content = await generate_content(chat, template_prompt)
            await write_file(os.path.join(blueprint_dir, 'templates', template_name), template_content)

    # Generate test file
    print(f"[bold cyan]Generating test file for {blueprint_name}Blueprint...[/bold cyan]")
    test_prompt = f"Create a test file (test_{blueprint_name.lower()}.py) for the following Flask-AppBuilder blueprint:\n\n{description}\n\nInclude tests for models, views, and any complex logic. Use the following specification, models, and views as a guide:\n\n{spec_content}\n\n{models_content}\n\n{views_content}"
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

