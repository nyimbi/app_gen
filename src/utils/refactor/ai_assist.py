class AICodeAssistant:
    """AI-powered code generation and correction assistant"""

    def __init__(self, api_key: str):
        import openai
        self.openai = openai
        self.openai.api_key = api_key
        self.model = "gpt-4"  # or "gpt-3.5-turbo" based on needs
        self.conversation_history = []
        self.temperature = 0.7

    def improve_code(self, code: str, context: str = "") -> str:
        """Improve code quality with AI suggestions"""
        prompt = f"""Given this Python code and context:
Context: {context}
Code:
```python
{code}
```
Suggest improvements while maintaining the core functionality. Focus on:
1. Code clarity and readability
2. Performance optimizations
3. Best practices
4. Error handling
5. Type hints
Please provide the improved code only, no explanations."""

        try:
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Python expert code reviewer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI code improvement failed: {e}")
            return code  # Return original code if AI fails

    def generate_docstring(self, code: str) -> str:
        """Generate comprehensive docstring for code"""
        prompt = f"""Generate a detailed Python docstring for this code:
```python
{code}
```
Include:
- Description
- Parameters
- Returns
- Raises
- Examples
Use Google style format."""

        try:
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical documentation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI docstring generation failed: {e}")
            return '"""Documentation generation failed"""'

    def generate_tests(self, code: str) -> str:
        """Generate comprehensive test cases"""
        prompt = f"""Generate pytest test cases for this Python code:
```python
{code}
```
Include:
- Edge cases
- Error cases
- Parameterized tests
- Mocking where appropriate
- Fixtures
Use pytest best practices."""

        try:
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Python testing expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI test generation failed: {e}")
            return "# Test generation failed"

    def fix_code_issues(self, code: str, error_message: str) -> str:
        """Fix code issues based on error messages"""
        prompt = f"""Fix this Python code that has the following error:
Error: {error_message}

Code:
```python
{code}
```
Provide the fixed code only, no explanations."""

        try:
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Python debugging expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI code fixing failed: {e}")
            return code

    def suggest_optimizations(self, code: str) -> str:
        """Suggest code optimizations"""
        prompt = f"""Optimize this Python code for better performance:
```python
{code}
```
Focus on:
1. Algorithm efficiency
2. Memory usage
3. CPU usage
4. I/O operations
Provide optimized code only, no explanations."""

        try:
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Python performance optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI optimization failed: {e}")
            return code
