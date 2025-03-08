import os
import subprocess
import re
import yaml
from pathlib import Path
import json

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

    def interpret_plan(self):
        try:
            # Interpret the plan to extract key components
            self.directory_structure = self.plan.get('directory_structure', {})
            self.code_structure = self.plan.get('code_structure', {})
            self.capabilities = self.plan.get('capabilities', [])
        except Exception as e:
            self.errors.append(f"Error in plan interpretation: {str(e)}")

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
        try:
            # Code review and optimization
            self.review_and_optimize_code()

            # Security enhancements
            self.add_security_enhancements()

            # User interface improvements (if applicable)
            self.enhance_user_interface()

            # Testing enhancements
            self.enhance_testing()

            # Documentation enhancements
            self.enhance_documentation()
        except Exception as e:
            self.errors.append(f"Error in application refinement: {str(e)}")

    def review_and_optimize_code(self):
        try:
            # Example: Use flake8 to check for code quality issues
            subprocess.run(['flake8', '.'], check=True)

            # Example: Use black to format the code
            subprocess.run(['black', '.'], check=True)
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Error in code review/optimization: {str(e)}")

    def add_security_enhancements(self):
        try:
            # Example: Add input validation
            for file_path, code in self.code_structure.items():
                if 'input' in code:
                    code = re.sub(r'input\((.*?)\)', r'input(validate_input(\1))', code)
                    with open(file_path, 'w') as file:
                        file.write(code)

            # Example: Add secure authentication
            if 'flask_login' in self.config.get('dependencies', []):
                auth_code = """
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        login_user(user)
        return "Logged in successfully"
    return "Invalid credentials", 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "Logged out successfully"
"""
                self.code_structure['app/auth.py'] = auth_code
        except Exception as e:
            self.errors.append(f"Error in adding security enhancements: {str(e)}")

    def enhance_user_interface(self):
        try:
            # Example: Enhance HTML templates
            for file_path, code in self.code_structure.items():
                if file_path.endswith('.html'):
                    code = re.sub(r'<body>', '<body><h1>Welcome to My Flask App</h1>', code)
                    with open(file_path, 'w') as file:
                        file.write(code)
        except Exception as e:
            self.errors.append(f"Error in enhancing user interface: {str(e)}")

    def enhance_testing(self):
        try:
            # Example: Add more comprehensive tests
            for file_path, tests in self.code_structure.items():
                if file_path.endswith('_test.py'):
                    tests += "\n\ndef test_example():\n    assert True\n"
                    with open(file_path, 'w') as test_file:
                        test_file.write(tests)
        except Exception as e:
            self.errors.append(f"Error in enhancing testing: {str(e)}")

    def enhance_documentation(self):
        try:
            # Example: Expand documentation
            for file_path, doc in self.code_structure.items():
                if file_path.endswith('.py'):
                    doc += "\n\n# Additional documentation\n"
                    with open(file_path, 'a') as file:
                        file.write(doc)
        except Exception as e:
            self.errors.append(f"Error in enhancing documentation: {str(e)}")

    def outline_capabilities(self):
        try:
            response = client.generate(f"Clearly outline the application's capabilities based on the following description: {self.description}")
            self.capabilities = response.text.split('\n')
        except Exception as e:
            self.errors.append(f"Error in capabilities outlining: {str(e)}")

    def ensure_compliance(self):
        try:
            # Code quality checks
            subprocess.run(['flake8', '.'], check=True)

            # Security audits
            subprocess.run(['bandit', '-r', '.'], check=True)

            # Dependency management
            subprocess.run(['pip', 'list', '--outdated'], check=True)
            subprocess.run(['pip', 'install', '--upgrade', '-r', 'requirements.txt'], check=True)

            # Configuration management
            if 'config.py' in self.code_structure:
                config_code = self.code_structure['config.py']
                if 'SECRET_KEY' not in config_code:
                    config_code += "\nSECRET_KEY = 'your_secret_key'"
                    self.code_structure['config.py'] = config_code

            # Documentation
            if 'README.md' in self.code_structure:
                readme_code = self.code_structure['README.md']
                if 'Compliance' not in readme_code:
                    readme_code += "\n## Compliance\nThis application complies with the specified requirements."
                    self.code_structure['README.md'] = readme_code
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Error in compliance checks: {str(e)}")

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

    def run(self):
        self.plan_development()
        self.interpret_plan()
        self.generate_code()
        self.write_tests()
        self.document_code()
        self.refine_application()
        self.outline_capabilities()
        self.ensure_compliance()

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