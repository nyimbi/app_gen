import os
import json
import requests
from pathlib import Path

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MAX_ITERATIONS = 5


def call_llm(prompt, model="llama2"):
    payload = {"model": model, "prompt": prompt, "temperature": 0.2, "stream": False}
    response = requests.post(OLLAMA_API_URL, json=payload)
    return response.json()["response"]


def get_development_plan(app_description, feedback=""):
    prompt = f"""Generate a detailed development plan for an application that:
{app_description}

Consider this feedback from previous attempts:
{feedback}

Format your response as JSON with the following structure:
{{
  "steps": [
    {{
      "description": "Step description",
      "implementation": "Code implementation details",
      "verification": "Verification criteria"
    }}
  ]
}}"""
    response = call_llm(prompt)
    return json.loads(response)


def execute_step(step, project_dir):
    code = call_llm(f"Generate Python code to implement: {step['description']}")

    # Create code file
    filename = f"{step['description'].lower().replace(' ', '_')}.py"
    filepath = project_dir / filename
    with open(filepath, "w") as f:
        f.write(code)

    return code


def verify_step(step, code):
    verification_prompt = f"""Verify if the following code satisfies the requirements:
Step: {step["description"]}
Code:
{code}

Check for:
- Correct implementation of requirements
- Error handling
- Code quality

Respond with 'PASS' if all criteria are met, otherwise explain the issues."""
    response = call_llm(verification_prompt)
    return "PASS" in response.upper()


def evaluate_plan(app_description, plan, code_history):
    evaluation_prompt = f"""Evaluate if the following plan and code meet the requirements:
Application Description: {app_description}
Plan: {json.dumps(plan)}
Code: {code_history}

Does this fully satisfy the requirements? If not, provide detailed feedback."""
    response = call_llamav(evaluation_prompt)
    return "SUCCESS" in response.upper(), response


def main():
    app_description = input("Enter application description: ")

    project_dir = Path(f"./{app_description.replace(' ', '_')}_project")
    project_dir.mkdir(exist_ok=True)

    for iteration in range(MAX_ITERATIONS):
        print(f"\nIteration {iteration + 1}/{MAX_ITERATIONS}")

        # Get development plan
        plan = get_development_plan(app_description)
        print("Plan generated:", plan)

        code_history = []
        all_steps_passed = True

        # Execute plan
        for step in plan["steps"]:
            print(f"\nExecuting step: {step['description']}")

            # Generate and save code
            code = execute_step(step, project_dir)
            code_history.append(code)

            # Verify step
            if not verify_step(step, code):
                print(f"Step verification failed: {step['description']}")
                all_steps_passed = False
                break

        if not all_steps_passed:
            print("\nPlan execution failed. Generating new plan...")
            continue

        # Evaluate complete plan
        success, feedback = evaluate_plan(app_description, plan, code_history)
        if success:
            print("\nApplication development completed successfully!")
            return

        print(f"\nPlan evaluation failed. Feedback: {feedback}")

    print("\nMaximum iterations reached. Development process incomplete.")


if __name__ == "__main__":
    main()
