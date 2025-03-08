import ollama
import os

def generate_code(prompt, model='mistral'):
    """
    Generates application files based on a text description. It first reviews the request, 
    makes a plan, identifies necessary files, and then generates them sequentially.
    
    :param prompt: Natural language description of the application to be created.
    :param model: The LLM model to use.
    :return: None (Creates project files in the directory).
    """

    # Step 1: Review the request and make a plan
    planning_prompt = f"""Analyze the following request and generate a structured development plan.
    Identify the key components, programming language, framework (if applicable), and necessary files.

    Request: {prompt}

    Provide output in the following JSON format:
    {{
        "summary": "Brief summary of the project",
        "files": [
            {{
                "name": "filename",
                "description": "Purpose of the file",
                "content": "High-level content structure or starter template"
            }}
        ]
    }}"""
    
    plan_response = ollama.generate(model=model, prompt=planning_prompt)
    
    try:
        plan = eval(plan_response['response'])  # Convert LLM output from string to dictionary (ensure safe parsing)
    except Exception as e:
        print("Error parsing AI response:", e)
        return

    print("\n=== Project Plan ===\n")
    print(plan["summary"])
    
    # Step 2: Create the project directory
    project_name = "generated_project"
    os.makedirs(project_name, exist_ok=True)

    # Step 3: Generate files one-by-one
    for file in plan["files"]:
        file_path = os.path.join(project_name, file["name"])
        
        print(f"\nCreating file: {file_path}")
        print(f"Description: {file['description']}\n")
        
        # Step 4: Generate detailed content for each file
        file_content_prompt = f"""Generate complete code for the following file:

        File Name: {file['name']}
        Purpose: {file['description']}
        Project Description: {plan['summary']}

        The code should be well-structured, follow best practices, and contain necessary comments.
        """
        
        file_content_response = ollama.generate(model=model, prompt=file_content_prompt)
        file_content = file_content_response['response']
        
        # Step 5: Write the generated content into the file
        with open(file_path, "w") as f:
            f.write(file_content)

        print(f"File {file['name']} created successfully.")

    print("\nProject generation complete! Your files are in the 'generated_project' directory.")

if __name__ == "__main__":
    user_input = input("\nDescribe the application you want to generate:\n")
    generate_code(user_input)
