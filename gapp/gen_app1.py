import json
import os
import asyncio
import ollama
from concurrent.futures import ThreadPoolExecutor

def create_project_directory(project_name):
    os.makedirs(project_name, exist_ok=True)

async def generate_code_async(file_info, model):
    """Asynchronously generates code for each file."""
    file_content_prompt = f"""Generate complete code for the following file:

    File Name: {file_info['name']}
    Purpose: {file_info['description']}
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(pool, lambda: ollama.generate(model=model, prompt=file_content_prompt))
    return file_info["name"], response["response"]

async def process_files_concurrently(files, project_name, model):
    tasks = [generate_code_async(file, model) for file in files]
    results = await asyncio.gather(*tasks)
    
    for filename, content in results:
        file_path = os.path.join(project_name, filename)
        with open(file_path, "w") as f:
            f.write(content)
        print(f"File {filename} created successfully.")

def generate_code(prompt, model='mistral'):
    """Main function that generates an entire application."""
    planning_prompt = f"""Analyze the request and generate a structured project plan:
    
    {prompt}
    
    Provide JSON output with:
    {{
        "summary": "...",
        "files": [{{"name": "...", "description": "..."}}]
    }}
    """
    
    plan_response = ollama.generate(model=model, prompt=planning_prompt)
    
    try:
        plan = json.loads(plan_response["response"])
    except json.JSONDecodeError:
        print("Failed to parse plan.")
        return

    project_name = "generated_project"
    create_project_directory(project_name)
    
    asyncio.run(process_files_concurrently(plan["files"], project_name, model))
    
    print("\nProject generation complete!")

if __name__ == "__main__":
    user_input = input("Describe the application you want to generate:\n")
    generate_code(user_input)
