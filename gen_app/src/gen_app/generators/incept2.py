import os
import ollama
import json
import subprocess
from pathlib import Path

# Initialize the Ollama client
client = ollama.Client()

class ApplicationGenerator:
    def __init__(self, description, config=None):
        self.description = description
        self.config = config or {}
        self.plan = {}
        self.directory_structure = {}
        self.code_structure = {}
        self.capabilities = []
        self.errors = []

    def plan_development(self):
        try:
            response = client.generate(f"Create a comprehensive plan for developing the application based on the following description: {self.description}")
            self.plan = eval(response.text)
        except Exception as e:
            self.errors.append(f"Error in plan development: {str(e)}")

    def define_directory_structure(self):
        try:
            response = client.generate(f"Define the necessary files and directory structure for the application based on the following description: {self.description}")
            self.directory_structure = eval(response.text)
        except Exception as e:
            self.errors.append(f"Error in directory structure: {str(e)}")

    def identify_code_structure(self):
        try:
            response = client.generate(f"Identify the required functions, classes, and methods for each file based on the following description: {self.description}")
            self.code_structure = eval(response.text)
        except Exception as e:
            self.errors.append(f"Error in code structure: {str(e)}")

    def generate_code(self):
        try:
            for file_path, code in self.code_structure.items():
                file_path = Path(file_path)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as file:
                    file.write(code)
        except Exception as e:
            self.errors.append(f"Error in code generation: {str(e)}")

    def write_tests(self):
        try:
            for file_path, tests in self.code_structure.items():
                test_file_path = Path(file_path).with_suffix('_test.py')
                with open(test_file_path, 'w') as test_file:
                    test_file.write(tests)
        except Exception as e:
            self.errors.append(f"Error in test generation: {str(e)}")

    def document_code(self):
        try:
            for file_path, doc in self.code_structure.items():
                with open(Path(file_path), 'a') as file:
                    file.write('\n' + doc)
        except Exception as e:
            self.errors.append(f"Error in documentation: {str(e)}")

    def refine_application(self):
        # Placeholder for iterative refinement
        pass

    def outline_capabilities(self):
        try:
            response = client.generate(f"Clearly outline the application's capabilities based on the following description: {self.description}")
            self.capabilities = response.text.split('\n')
        except Exception as e:
            self.errors.append(f"Error in capabilities outlining: {str(e)}")

    def ensure_compliance(self):
        # Placeholder for compliance checks
        pass

    def run(self):
        self.plan_development()
        self.define_directory_structure()
        self.identify_code_structure()
        self.generate_code()
        self.write_tests()
        self.document_code()
        self.refine_application()
        self.outline_capabilities()
        self.ensure_compliance()

    def initialize_version_control(self):
        try:
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Error in version control initialization: {str(e)}")

    def install_dependencies(self):
        try:
            if 'dependencies' in self.config:
                for dep in self.config['dependencies']:
                    subprocess.run(['pip', 'install', dep], check=True)
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Error in dependency installation: {str(e)}")

    def setup_ci_cd(self):
        try:
            if 'ci_cd' in self.config:
                ci_cd_config = self.config['ci_cd']
                with open('.github/workflows/ci.yml', 'w') as ci_file:
                    ci_file.write(yaml.dump(ci_cd_config))
        except Exception as e:
            self.errors.append(f"Error in CI/CD setup: {str(e)}")

    def main(self):
        self.run()
        self.initialize_version_control()
        self.install_dependencies()
        self.setup_ci_cd()

        print("Application generated successfully!")
        print("Capabilities:")
        for capability in self.capabilities:
            print(f"- {capability}")

        if self.errors:
            print("\nErrors encountered:")
            for error in self.errors:
                print(f"- {error}")

# Example usage
if __name__ == "__main__":
    description = """
    Develop a simple web application using Flask that allows users to create, read, update, and delete (CRUD) notes.
    The application should have a user authentication system and a database to store notes.
    """

    config = {
        "dependencies": ["flask", "flask_sqlalchemy", "flask_migrate", "flask_login"],
        "ci_cd": {
            "name": "CI/CD Pipeline",
            "on": ["push", "pull_request"],
            "jobs": {
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v2"},
                        {"name": "Set up Python", "uses": "actions/setup-python@v2", "with": {"python-version": "3.8"}},
                        {"name": "Install dependencies", "run": "pip install -r requirements.txt"},
                        {"name": "Test with pytest", "run": "pytest"}
                    ]
                }
            }
        }
    }

    generator = ApplicationGenerator(description, config)
    generator.main()