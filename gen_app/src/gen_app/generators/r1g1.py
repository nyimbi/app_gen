"""
AI-Powered Application Generator using Ollama

This program creates Python applications based on natural language descriptions
by leveraging LLM capabilities through Ollama's API.
"""

import os
import json
import subprocess
from time import sleep
import ollama

def generate_component(prompt, context, max_retries=3):
    """
    Generate content using Ollama with error handling and retries
    
    Args:
        prompt (str): The generation prompt
        context (str): Contextual information for the LLM
        max_retries (int): Number of retry attempts
        
    Returns:
        str: Generated content
    """
    full_prompt = f"{context}\n\n{prompt} Respond with only the requested content without additional commentary."
    
    for _ in range(max_retries):
        try:
            response = ollama.generate(
                model='mistral',
                prompt=full_prompt,
                format='json',
                options={'temperature': 0.2}
            )
            return response['response'].strip()
        except Exception as e:
            print(f"Error generating content: {e}. Retrying...")
            sleep(2)
    
    raise Exception("Failed to generate content after multiple attempts")

def plan_development(description):
    """
    Generate development plan based on user description
    
    Args:
        description (str): User's application description
        
    Returns:
        dict: Structured development plan
    """
    prompt = """Create a comprehensive development plan including:
1. Key components and technologies
2. Main architecture decisions
3. Development phases
4. Potential challenges
5. Recommended testing strategy"""

    plan = generate_component(prompt, description)
    return json.loads(plan)

def create_directory_structure(plan):
    """
    Generate directory structure based on development plan
    
    Args:
        plan (dict): Development plan
        
    Returns:
        dict: Directory structure configuration
    """
    prompt = """Create a directory structure configuration including:
- Python package structure
- Required modules
- Test directory
- Documentation files
- Configuration files
Format as JSON with 'structure' and 'files' keys"""

    return json.loads(generate_component(prompt, json.dumps(plan)))

def generate_code_components(structure):
    """
    Generate code components iteratively
    
    Args:
        structure (dict): Directory structure configuration
        
    Returns:
        dict: Generated code components with file paths
    """
    code_components = {}
    
    for file in structure['files']:
        prompt = f"""Generate Python code for {file['path']} including:
- Required imports
- Classes and functions with type hints
- Docstrings
- Error handling
- Entry points if applicable
Format as plain Python code with Markdown code fences"""
        
        code = generate_component(prompt, file['description'])
        code_components[file['path']] = code.replace('```python', '').replace('```', '').strip()
    
    return code_components

def create_tests(code_components):
    """
    Generate test suite for generated code
    
    Args:
        code_components (dict): Generated code components
        
    Returns:
        dict: Test files with test cases
    """
    tests = {}
    
    for path, code in code_components.items():
        prompt = f"""Create pytest test cases for this code:
{code}
Include:
- Test fixtures
- Parameterized tests
- Edge cases
- Mocking where appropriate
- Assertion statements"""
        
        test_code = generate_component(prompt, code)
        test_path = f"tests/test_{os.path.basename(path)}"
        tests[test_path] = test_code.replace('```python', '').replace('```', '').strip()
    
    return tests

def generate_documentation(plan, structure, code_components):
    """
    Generate project documentation
    
    Args:
        plan (dict): Development plan
        structure (dict): Directory structure
        code_components (dict): Generated code
        
    Returns:
        dict: Documentation files
    """
    docs = {}
    
    # Generate README
    prompt = """Create a comprehensive README.md including:
- Project overview
- Installation instructions
- Usage examples
- API documentation
- Contributing guidelines
- License information"""
    
    docs['README.md'] = generate_component(prompt, json.dumps(plan)))

    # Generate API documentation
    for path, code in code_components.items():
        prompt = f"""Create API documentation for this code:
{code}
Include:
- Module-level docstring
- Class and method documentation
- Examples of usage
- Parameters and return values"""
        
        docs[path + '.md'] = generate_component(prompt, code)
    
    return docs

def validate_structure(structure):
    """Validate directory structure configuration"""
    required_keys = {'structure', 'files'}
    if not all(key in structure for key in required_keys):
        raise ValueError("Invalid directory structure format")
    
    for file in structure['files']:
        if not all(k in file for k in ('path', 'description')):
            raise ValueError("Invalid file entry format")

def build_project(components, tests, docs, structure):
    """
    Create project files on disk
    
    Args:
        components (dict): Code components
        tests (dict): Test files
        docs (dict): Documentation files
        structure (dict): Directory structure
    """
    # Create directories
    for dir in structure['structure']:
        os.makedirs(dir, exist_ok=True)
    
    # Create files
    file_creators = [
        (components, "Source code"),
        (tests, "Tests"),
        (docs, "Documentation")
    ]
    
    for file_group, group_name in file_creators:
        for path, content in file_group.items():
            with open(path, 'w') as f:
                f.write(content)
            print(f"Created {group_name} file: {path}")

def iterative_development(description, max_iterations=5):
    """
    Main development loop with iterative refinement
    
    Args:
        description (str): User's application description
        max_iterations (int): Maximum refinement cycles
    """
    iteration = 0
    approved = False
    
    while iteration < max_iterations and not approved:
        # Generate project components
        plan = plan_development(description)
        structure = create_directory_structure(plan)
        validate_structure(structure)
        code = generate_code_components(structure)
        tests = create_tests(code)
        docs = generate_documentation(plan, structure, code)
        
        # Build project
        build_project(code, tests, docs, structure)
        
        # User verification
        user_input = input("Does the generated project meet requirements? (y/n): ").lower()
        if user_input == 'y':
            approved = True
            print("Project generation complete!")
        else:
            iteration += 1
            description += "\n\nAdditional requirements from user feedback: " + input("Please enter required changes: ")
    
    if not approved:
        print("Maximum iterations reached. Please refine your requirements.")

if __name__ == "__main__":
    user_description = input("Enter your application description: ")
    iterative_development(user_description)