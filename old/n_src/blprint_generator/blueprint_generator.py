import os
import asyncio
import yaml
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain.graphs import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, AIMessage
from rich.console import Console
from rich.progress import Progress, TaskID
import subprocess
import ast

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup Rich console for pretty printing
console = Console()

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Load prompts
with open("prompts.yaml", "r") as f:
    prompts = yaml.safe_load(f)

# Initialize the LLM
llm = ChatAnthropic(
    model=config['model_name'],
    anthropic_api_key=config['anthropic_api_key']
)

# Define the StateGraph
graph = StateGraph()

# Helper function to run shell commands
async def run_command(cmd: List[str]) -> str:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Command {cmd} failed: {stderr.decode()}")
    return stdout.decode()

# Node functions
async def domain_research(state: Dict[str, Any]) -> Dict[str, Any]:
    """Perform domain research and identify best practices."""
    response = await llm.ainvoke(prompts['domain_research'].format(blueprint=state['blueprint']))
    return {"domain_knowledge": response.content}

async def architecture_planning(state: Dict[str, Any]) -> Dict[str, Any]:
    """Plan the architecture considering scalability and maintainability."""
    response = await llm.ainvoke(prompts['architecture_planning'].format(
        blueprint=state['blueprint'],
        domain_knowledge=state['domain_knowledge']
    ))
    return {"architecture": response.content}

async def product_specification(state: Dict[str, Any]) -> Dict[str, Any]:
    """Develop a detailed product specification."""
    response = await llm.ainvoke(prompts['product_specification'].format(
        blueprint=state['blueprint'],
        architecture=state['architecture']
    ))
    return {"specification": response.content}

async def file_structure_planning(state: Dict[str, Any]) -> Dict[str, Any]:
    """Plan the file structure and component organization."""
    response = await llm.ainvoke(prompts['file_structure_planning'].format(
        specification=state['specification']
    ))
    return {"file_structure": response.content}

async def generate_code(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code for each component."""
    generated_code = {}
    for file in state['file_structure'].split('\n'):
        if file.endswith('.py'):
            response = await llm.ainvoke(prompts['generate_code'].format(
                file=file,
                specification=state['specification'],
                file_structure=state['file_structure']
            ))
            generated_code[file] = response.content
    return {"generated_code": generated_code}

async def test_code(state: Dict[str, Any]) -> Dict[str, Any]:
    """Implement comprehensive testing."""
    test_results = {}
    for file, code in state['generated_code'].items():
        test_results[file] = {}
        test_results[file]['pylint'] = await run_command(['pylint', file])
        test_results[file]['mypy'] = await run_command(['mypy', file])
        test_file = f"test_{file}"
        test_code = await llm.ainvoke(prompts['generate_tests'].format(code=code))
        with open(test_file, 'w') as f:
            f.write(test_code.content)
        test_results[file]['pytest'] = await run_command(['pytest', test_file])
    return {"test_results": test_results}

async def refine_code(state: Dict[str, Any]) -> Dict[str, Any]:
    """Refine code based on test results."""
    refined_code = state['generated_code'].copy()
    max_iterations = 3
    for iteration in range(max_iterations):
        issues_found = False
        for file, code in refined_code.items():
            if state['test_results'][file]['pylint'] != '10.00/10' or 'error:' in state['test_results'][file]['mypy']:
                response = await llm.ainvoke(prompts['refine_code'].format(
                    code=code,
                    pylint_results=state['test_results'][file]['pylint'],
                    mypy_results=state['test_results'][file]['mypy']
                ))
                refined_code[file] = response.content
                issues_found = True
        if not issues_found:
            break
        state['generated_code'] = refined_code
        state = await test_code(state)
    return {"refined_code": refined_code}

async def generate_documentation(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate documentation, including API docs if applicable."""
    response = await llm.ainvoke(prompts['generate_documentation'].format(
        specification=state['specification'],
        generated_code=state['generated_code']
    ))
    return {"documentation": response.content}

async def create_configurations(state: Dict[str, Any]) -> Dict[str, Any]:
    """Create containerization and CI/CD configurations."""
    response = await llm.ainvoke(prompts['create_configurations'].format(
        specification=state['specification'],
        file_structure=state['file_structure']
    ))
    return {"configurations": response.content}

async def save_generated_code(state: Dict[str, Any]) -> Dict[str, Any]:
    """Save generated code to files in a structured directory."""
    blueprint_dir = f"generated_blueprints/{state['blueprint']['name']}"
    os.makedirs(blueprint_dir, exist_ok=True)
    for file, code in state['generated_code'].items():
        with open(f"{blueprint_dir}/{file}", 'w') as f:
            f.write(code)
    return state

async def generate_requirements(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate requirements.txt file."""
    response = await llm.ainvoke(prompts['generate_requirements'].format(
        specification=state['specification'],
        generated_code=state['generated_code']
    ))
    state['requirements'] = response.content
    return state

async def security_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a security review of the generated code."""
    response = await llm.ainvoke(prompts['security_review'].format(
        generated_code=state['generated_code']
    ))
    state['security_review'] = response.content
    return state

async def performance_test(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate performance tests for critical paths."""
    response = await llm.ainvoke(prompts['performance_test'].format(
        specification=state['specification'],
        generated_code=state['generated_code']
    ))
    state['performance_tests'] = response.content
    return state

async def generate_api_docs(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate OpenAPI/Swagger documentation for APIs."""
    if 'api' in state['blueprint']:
        response = await llm.ainvoke(prompts['generate_api_docs'].format(
            specification=state['specification'],
            generated_code=state['generated_code']
        ))
        state['api_docs'] = response.content
    return state

async def generate_migrations(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate initial database migration scripts."""
    if 'database' in state['blueprint']:
        response = await llm.ainvoke(prompts['generate_migrations'].format(
            models=state['generated_code'].get('models.py', '')
        ))
        state['migrations'] = response.content
    return state

# Add nodes to the graph
graph.add_node("domain_research", domain_research)
graph.add_node("architecture_planning", architecture_planning)
graph.add_node("product_specification", product_specification)
graph.add_node("file_structure_planning", file_structure_planning)
graph.add_node("generate_code", generate_code)
graph.add_node("test_code", test_code)
graph.add_node("refine_code", refine_code)
graph.add_node("generate_documentation", generate_documentation)
graph.add_node("create_configurations", create_configurations)
graph.add_node("save_generated_code", save_generated_code)
graph.add_node("generate_requirements", generate_requirements)
graph.add_node("security_review", security_review)
graph.add_node("performance_test", performance_test)
graph.add_node("generate_api_docs", generate_api_docs)
graph.add_node("generate_migrations", generate_migrations)

# Define edges
graph.add_edge("domain_research", "architecture_planning")
graph.add_edge("architecture_planning", "product_specification")
graph.add_edge("product_specification", "file_structure_planning")
graph.add_edge("file_structure_planning", "generate_code")
graph.add_edge("generate_code", "test_code")
graph.add_edge("test_code", "refine_code")
graph.add_edge("refine_code", "test_code")
graph.add_edge("test_code", "generate_documentation")
graph.add_edge("generate_documentation", "create_configurations")
graph.add_edge("create_configurations", "save_generated_code")
graph.add_edge("save_generated_code", "generate_requirements")
graph.add_edge("generate_requirements", "security_review")
graph.add_edge("security_review", "performance_test")
graph.add_edge("performance_test", "generate_api_docs")
graph.add_edge("generate_api_docs", "generate_migrations")

# Set the entry point
graph.set_entry_point("domain_research")

# Compile the graph
workflow = graph.compile()

async def generate_blueprint(blueprint: Dict[str, Any], progress: Progress, task: TaskID):
    """Generate a single blueprint."""
    try:
        result = await workflow.ainvoke({"blueprint": blueprint})
        progress.update(task, advance=1)
        return result
    except Exception as e:
        logger.error(f"Error generating blueprint {blueprint['name']}: {str(e)}")
        progress.update(task, advance=1)
        return None

async def main():
    # Load blueprints from YAML file
    with open("blueprints.yaml", "r") as f:
        blueprints = yaml.safe_load(f)

    with Progress() as progress:
        overall_task = progress.add_task("[green]Generating blueprints...", total=len(blueprints))
        tasks = [generate_blueprint(bp, progress, overall_task) for bp in blueprints]
        results = await asyncio.gather(*tasks)

    for blueprint, result in zip(blueprints, results):
        if result:
            console.print(f"[green]Successfully generated blueprint: {blueprint['name']}[/green]")
        else:
            console.print(f"[red]Failed to generate blueprint: {blueprint['name']}[/red]")

if __name__ == "__main__":
    asyncio.run(main())

