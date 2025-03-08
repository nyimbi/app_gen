"""
Advanced AI-Powered Application Generator using Ollama with Component-Based Generation

This program creates Python applications by generating code components iteratively
to circumvent LLM token limits and ensure plan conformance with a hierarchical component architecture,
verification mechanisms, and dependency resolution.
"""

import os
import re
import json
import ast
import logging
import hashlib
import asyncio
import traceback
import jsonschema
from time import sleep
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple, Set, Union, TypeVar, Generic, Callable
from enum import Enum, auto
import ollama
import networkx as nx  # For dependency resolution
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Type variables for generics
T = TypeVar('T')
U = TypeVar('U')

# Setup enhanced logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("appgen.log"),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger("appgen")


class GenerationStrategy(Enum):
    """Strategy enum for code generation approaches"""
    COMPONENT_WISE = auto()
    FILE_WISE = auto()
    MODULE_WISE = auto()


@dataclass
class ConfigOptions:
    """Configuration options for the generator"""
    model: str = "qwen2.5:32b"
    temperature: float = 0.2
    output_dir: str = "generated_project"
    max_retries: int = 3
    retry_delay: float = 2.0
    concurrency_limit: int = 3
    generation_strategy: GenerationStrategy = GenerationStrategy.COMPONENT_WISE
    verify_syntax: bool = True
    verify_structure: bool = True
    attempt_repair: bool = True
    cache_generations: bool = True
    cache_dir: str = ".generation_cache"
    prompt_templates_file: str = "prompt_templates.json"
    schema_validation: bool = True
    max_repair_attempts: int = 2


class Config:
    """Configuration singleton with defaults"""
    options = ConfigOptions()

    @classmethod
    def from_file(cls, config_file: str) -> None:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)

            # Handle enum conversion
            if 'generation_strategy' in config_data:
                config_data['generation_strategy'] = GenerationStrategy[config_data['generation_strategy']]

            # Update config with file values
            for key, value in config_data.items():
                if hasattr(cls.options, key):
                    setattr(cls.options, key, value)

            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")

    @classmethod
    def save_to_file(cls, config_file: str) -> None:
        """Save current configuration to JSON file"""
        try:
            # Convert enums to strings for JSON serialization
            config_dict = asdict(cls.options)
            if isinstance(config_dict.get('generation_strategy'), Enum):
                config_dict['generation_strategy'] = config_dict['generation_strategy'].name

            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)

            logger.info(f"Saved configuration to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")


class GenerationError(Exception):
    """Base exception for generation errors"""
    pass


class VerificationError(Exception):
    """Exception for verification failures"""
    pass


class DependencyError(Exception):
    """Exception for dependency resolution issues"""
    pass


@dataclass
class Component:
    """Component representation with extended attributes"""
    name: str
    type: str
    description: str
    requirements: str = ""
    dependencies: List[str] = field(default_factory=list)
    tests_required: bool = True
    priority: int = 0
    verification_criteria: List[str] = field(default_factory=list)
    generated_code: str = ""
    validated: bool = False


@dataclass
class File:
    """File representation with components"""
    path: str
    components: List[Component]
    description: str = ""
    imports: List[str] = field(default_factory=list)
    generated_code: str = ""
    is_entrypoint: bool = False


@dataclass
class Structure:
    """Project structure representation"""
    structure: Dict[str, Any]
    files: List[File]

    @classmethod
    def from_dict(cls, data: Dict) -> 'Structure':
        """Create Structure from dictionary with proper component conversion"""
        files = []
        for file_data in data.get("files", []):
            components = []
            for comp_data in file_data.get("components", []):
                components.append(Component(**comp_data))
            files.append(File(path=file_data["path"],
                              components=components,
                              description=file_data.get("description", ""),
                              imports=file_data.get("imports", []),
                              is_entrypoint=file_data.get("is_entrypoint", False)))
        return cls(structure=data.get("structure", {}), files=files)


class PromptTemplate:
    """Manager for prompt templates with context management"""
    _templates: Dict[str, str] = {}

    @classmethod
    def load_templates(cls, template_file: str = None) -> None:
        """Load prompt templates from file"""
        if template_file is None:
            template_file = Config.options.prompt_templates_file

        try:
            if os.path.exists(template_file):
                with open(template_file, 'r') as f:
                    cls._templates = json.load(f)
                logger.info(f"Loaded prompt templates from {template_file}")
            else:
                cls._initialize_default_templates()
                # Save defaults for future use
                with open(template_file, 'w') as f:
                    json.dump(cls._templates, f, indent=2)
                logger.info(f"Created default prompt templates at {template_file}")
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {str(e)}")
            cls._initialize_default_templates()

    @classmethod
    def _initialize_default_templates(cls) -> None:
        """Initialize default prompt templates with clear output formatting instructions"""
        cls._templates = {
            "plan": """
            Create a comprehensive development plan with:
            1. Component architecture (classes, functions, modules)
            2. File structure with logical organization
            3. Detailed component specifications with clear responsibilities
            4. Dependencies between components
            5. Testing requirements

            IMPORTANT: Your response must be ONLY valid JSON without explanations, commentary, or markdown formatting.

            Format your response as follows:
            {
              "architecture": { ... },
              "fileStructure": { ... },
              "components": [ ... ],
              "dependencies": [ ... ],
              "testing": { ... }
            }
            """,

            "structure": """
            Create detailed directory structure with:
            - File paths following Python best practices
            - Component types (class/function/module)
            - Component descriptions
            - Dependencies between components
            - Import requirements

            IMPORTANT: Your response must be ONLY valid JSON without explanations, commentary, or markdown formatting.

            Format your response as follows:
            {
              "structure": {
                "root": "project_root",
                "directories": [ ... ]
              },
              "files": [
                {
                  "path": "path/to/file.py",
                  "components": [ ... ],
                  "imports": [ ... ],
                  "description": "..."
                },
                ...
              ]
            }
            """,

            "component": """
            Generate Python {component_type} '{component_name}' for {file_path}:

            Description: {description}
            Requirements: {requirements}
            Dependencies: {dependencies}

            Include:
            - Type hints
            - Comprehensive docstrings
            - Proper error handling
            - Input validation
            - Performance considerations

            IMPORTANT FORMATTING INSTRUCTIONS:
            1. Return ONLY valid Python code without explanations or markdown formatting
            2. Do not include ```python or ``` markers around code
            3. Start directly with imports or the {component_type} definition
            4. End with just the code, no closing comments
            """,

            "test": """
            Create pytest cases for {component_type} '{component_name}' in {file_path}:

            Code:
            {component_code}

            Include:
            - Fixtures
            - Parameterization
            - Edge cases
            - Mocks for external dependencies
            - Assertions with clear failure messages
            - Coverage for both success and error paths

            IMPORTANT FORMATTING INSTRUCTIONS:
            1. Return ONLY valid Python code without explanations or markdown formatting
            2. Do not include ```python or ``` markers around code
            3. Start directly with imports or test function definitions
            4. End with just the code, no closing comments
            """
        }

    @classmethod
    def get(cls, template_name: str, **kwargs) -> str:
        """Get formatted template with replacements"""
        if not cls._templates:
            cls._initialize_default_templates()

        template = cls._templates.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")

        return template.format(**kwargs) if kwargs else template


class GenerationCache:
    """Cache for generation results to avoid redundant API calls"""
    _cache_dir: str = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize cache directory"""
        cls._cache_dir = Config.options.cache_dir
        if Config.options.cache_generations:
            os.makedirs(cls._cache_dir, exist_ok=True)
            logger.info(f"Initialized generation cache at {cls._cache_dir}")

    @classmethod
    def _get_cache_key(cls, prompt: str, context: str) -> str:
        """Generate unique cache key based on input"""
        combined = (prompt + context).encode('utf-8')
        return hashlib.md5(combined).hexdigest()

    @classmethod
    def get(cls, prompt: str, context: str) -> Optional[str]:
        """Retrieve cached generation result if available"""
        if not Config.options.cache_generations:
            return None

        key = cls._get_cache_key(prompt, context)
        cache_file = os.path.join(cls._cache_dir, f"{key}.txt")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read cache: {str(e)}")

        return None

    @classmethod
    def store(cls, prompt: str, context: str, result: str) -> None:
        """Store generation result in cache"""
        if not Config.options.cache_generations:
            return

        key = cls._get_cache_key(prompt, context)
        cache_file = os.path.join(cls._cache_dir, f"{key}.txt")

        try:
            with open(cache_file, 'w') as f:
                f.write(result)
        except Exception as e:
            logger.warning(f"Failed to write to cache: {str(e)}")


class CodeVerifier:
    """Verifies generated code for syntax and basic correctness"""

    @staticmethod
    def verify_syntax(code: str) -> Tuple[bool, str]:
        """Verify Python syntax without execution"""
        try:
            compile(code, '<string>', 'exec')
            return True, ""
        except SyntaxError as e:
            # Enhanced error reporting with line number and context
            line_num = e.lineno if hasattr(e, 'lineno') else '?'
            col_num = e.offset if hasattr(e, 'offset') else '?'
            error_type = type(e).__name__
            error_msg = str(e)

            # Get the problematic line and a few lines around it for context
            lines = code.split('\n')
            start_line = max(0, line_num - 3) if isinstance(line_num, int) else 0
            end_line = min(len(lines), line_num + 2) if isinstance(line_num, int) else min(5, len(lines))

            context_lines = []
            for i in range(start_line, end_line):
                if i < len(lines):  # Ensure we don't go out of bounds
                    prefix = ">>> " if i == line_num - 1 else "    "
                    context_lines.append(f"{prefix}{i+1}: {lines[i]}")

            error_context = "\n".join(context_lines)

            return False, f"Syntax error ({error_type}) at line {line_num}, column {col_num}: {error_msg}\nContext:\n{error_context}"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"

    @staticmethod
    def verify_imports(code: str) -> Tuple[bool, List[str], str]:
        """Verify imports by analyzing AST

        Returns:
            (is_valid, imported_modules, error_message)
        """
        try:
            tree = ast.parse(code)
            imports = []

            # Find all import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:  # 'from x import y' case
                        imports.append(node.module)

            return True, imports, ""
        except SyntaxError as e:
            return False, [], f"Import verification syntax error: {str(e)}"
        except Exception as e:
            return False, [], f"Import verification error: {str(e)}"

    @staticmethod
    def verify_component_structure(code: str, component_type: str, component_name: str) -> Tuple[bool, Dict[str, Any], str]:
        """Verify component structure using AST parsing

        Verifies that the component matches its intended type and extracts
        key structural elements for validation.

        Args:
            code: The Python code to verify
            component_type: Expected component type ("class", "function", "module")
            component_name: Expected component name

        Returns:
            (is_valid, component_info, error_message)
        """
        try:
            tree = ast.parse(code)

            # Check for expected component type
            if component_type.lower() == "class":
                # Find class definitions
                class_nodes = [node for node in tree.body if isinstance(node, ast.ClassDef)]

                if not class_nodes:
                    return False, {}, f"No class definitions found in the code"

                # Check if the expected class name exists
                target_class = None
                for cls in class_nodes:
                    if cls.name == component_name:
                        target_class = cls
                        break

                if not target_class:
                    class_names = [cls.name for cls in class_nodes]
                    return False, {"found_classes": class_names}, f"Expected class '{component_name}' not found. Found: {', '.join(class_names)}"

                # Extract class methods
                methods = []
                for node in target_class.body:
                    if isinstance(node, ast.FunctionDef):
                        methods.append({
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "is_static": any(isinstance(dec, ast.Name) and dec.id == 'staticmethod'
                                           for dec in node.decorator_list),
                            "is_class": any(isinstance(dec, ast.Name) and dec.id == 'classmethod'
                                          for dec in node.decorator_list),
                        })

                return True, {
                    "type": "class",
                    "name": target_class.name,
                    "methods": methods,
                    "has_init": any(m["name"] == "__init__" for m in methods),
                    "base_classes": [ast_unparse(base).strip() for base in target_class.bases],
                }, ""

            elif component_type.lower() == "function":
                # Find function definitions
                func_nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

                if not func_nodes:
                    return False, {}, f"No function definitions found in the code"

                # Check if the expected function name exists
                target_func = None
                for func in func_nodes:
                    if func.name == component_name:
                        target_func = func
                        break

                if not target_func:
                    func_names = [f.name for f in func_nodes]
                    return False, {"found_functions": func_names}, f"Expected function '{component_name}' not found. Found: {', '.join(func_names)}"

                # Extract function args and return annotation if available
                args = [arg.arg for arg in target_func.args.args]
                returns = ast_unparse(target_func.returns).strip() if target_func.returns else None

                return True, {
                    "type": "function",
                    "name": target_func.name,
                    "args": args,
                    "returns": returns,
                    "has_docstring": (isinstance(target_func.body[0], ast.Expr) and
                                     isinstance(target_func.body[0].value, ast.Constant) and
                                     isinstance(target_func.body[0].value.value, str))
                }, ""

            elif component_type.lower() == "module":
                # For modules, we just verify the overall structure
                top_level_items = []

                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        top_level_items.append({"type": "class", "name": node.name})
                    elif isinstance(node, ast.FunctionDef):
                        top_level_items.append({"type": "function", "name": node.name})
                    elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                        # Already covered by verify_imports
                        pass
                    elif isinstance(node, ast.Assign):
                        # Look for constants/variables
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                # Check if it looks like a constant (uppercase)
                                is_constant = target.id.isupper()
                                top_level_items.append({
                                    "type": "constant" if is_constant else "variable",
                                    "name": target.id
                                })

                return True, {
                    "type": "module",
                    "top_level_items": top_level_items,
                }, ""
            else:
                return False, {}, f"Unsupported component type: {component_type}"

        except SyntaxError as e:
            # If syntax error, don't double-report (syntax verification should catch this)
            return False, {}, f"Unable to verify structure due to syntax error"
        except Exception as e:
            return False, {}, f"Structure verification error: {str(e)}"

    @staticmethod
    def repair_syntax_errors(code: str, error_info: str) -> str:
        """Attempt to repair common syntax errors

        Args:
            code: The Python code with errors
            error_info: Error information from verify_syntax

        Returns:
            Potentially repaired code
        """
        # Extract line number from error message if possible
        line_match = re.search(r"line (\d+)", error_info)
        if not line_match:
            return code  # Can't determine error location

        line_num = int(line_match.group(1))
        lines = code.split('\n')

        if line_num <= 0 or line_num > len(lines):
            return code  # Invalid line number

        # Extract error type if possible
        error_type_match = re.search(r"\((.*?)\)", error_info)
        error_type = error_type_match.group(1) if error_type_match else "unknown"

        # The problematic line
        problem_line = lines[line_num - 1]

        # Apply repairs based on error types
        if "SyntaxError" in error_info:
            # Common syntax errors and their fixes

            # Missing closing parenthesis/bracket/brace
            if "unexpected EOF" in error_info or "unexpected end of file" in error_info:
                # Count opening and closing characters
                pairs = [('(', ')'), ('[', ']'), ('{', '}')]
                for open_char, close_char in pairs:
                    open_count = code.count(open_char)
                    close_count = code.count(close_char)
                    if open_count > close_count:
                        # Add missing closing characters
                        code += close_char * (open_count - close_count)

            # Missing colon at end of line
            elif "expected ':'" in error_info:
                if not problem_line.strip().endswith(':'):
                    lines[line_num - 1] = problem_line.rstrip() + ':'

            # Incorrect indentation
            elif "indentation" in error_info:
                # For indentation errors, we need surrounding context
                if line_num > 1:
                    prev_line = lines[line_num - 2]
                    # If previous line ends with ':', this line should be indented
                    if prev_line.strip().endswith(':') and not problem_line.startswith('    '):
                        lines[line_num - 1] = '    ' + problem_line

            # Unmatched string quote
            elif "unterminated string" in error_info or "EOL while scanning string" in error_info:
                # Check for unclosed quotes
                for quote in ['"', "'"]:
                    if problem_line.count(quote) % 2 == 1:
                        lines[line_num - 1] = problem_line + quote

            # Missing comma in collection
            elif "invalid syntax" in error_info and any(x in problem_line for x in ['[', '{', '(']):
                # Look for likely missing commas in collections
                if re.search(r'[\[\{\(][^\]\}\)]*?[\w\d\'"]+\s+[\w\d\'"]', problem_line):
                    # Find position between items without comma
                    match = re.search(r'([\w\d\'"])(\s+)([\w\d\'"])', problem_line)
                    if match:
                        start, spaces, end = match.groups()
                        fixed_line = problem_line.replace(f"{start}{spaces}{end}", f"{start},{spaces}{end}", 1)
                        lines[line_num - 1] = fixed_line

            # Invalid syntax in general - attempt to remove the problematic line
            else:
                # Add a comment explaining the removal
                lines[line_num - 1] = f"# Removed due to syntax error: {problem_line}"

        return '\n'.join(lines)

    @staticmethod
    def verify_component_dependencies(code: str, component_dependencies: List[str]) -> Tuple[bool, List[str], str]:
        """Verify that a component properly implements its dependencies

        Args:
            code: The Python code to verify
            component_dependencies: List of dependency component names

        Returns:
            (is_valid, missing_dependencies, error_message)
        """
        if not component_dependencies:
            return True, [], ""

        try:
            tree = ast.parse(code)

            # Look for references to dependencies in the code
            referenced_names = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    referenced_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # Handle attribute access (e.g., component.method)
                    if isinstance(node.value, ast.Name):
                        referenced_names.add(node.value.id)

            # Check for missing dependencies
            missing = []
            for dep in component_dependencies:
                # Split for nested dependencies (e.g. module.class)
                dep_parts = dep.split('.')
                if dep_parts[0] not in referenced_names:
                    missing.append(dep)

            if missing:
                return False, missing, f"Component does not reference dependencies: {', '.join(missing)}"

            return True, [], ""
        except Exception as e:
            return False, [], f"Dependency verification error: {str(e)}"


class OutputParser:
    """Parser for extracting and cleaning LLM-generated content"""

    @staticmethod
    def extract_code(raw_output: str) -> str:
        """Extract Python code from potentially mixed content

        Handles common formats including markdown code blocks, explanatory text, etc.
        Returns the cleanest version of the actual Python code.
        """
        # Try to find code blocks marked with Python markdown
        code_block_pattern = r"```(?:python)?\s*([\s\S]*?)```"
        code_blocks = re.findall(code_block_pattern, raw_output)

        if code_blocks:
            # Join multiple code blocks with newlines
            return "\n\n".join(block.strip() for block in code_blocks)

        # If no code blocks found, use more sophisticated analysis
        lines = raw_output.strip().split('\n')

        # First, check if the output has strong code indicators
        code_indicators = [
            r"^import\s+",
            r"^from\s+.*\s+import\s+",
            r"^def\s+",
            r"^class\s+",
            r"^if\s+__name__\s+==",
            r"^\s+[a-zA-Z0-9_]+\s*=", # Indented assignment
            r"^[a-zA-Z0-9_]+\s*=", # Assignment
            r"^@[a-zA-Z0-9_]+" # Decorator
        ]

        # Count lines that are very likely to be code
        strong_code_indicators = sum(
            1 for line in lines
            if any(re.match(pattern, line) for pattern in code_indicators)
        )

        # If we have strong code indicators, assume it's all code
        if strong_code_indicators > 0:
            return raw_output.strip()

        # Otherwise, look for clear markdown/explanation patterns that aren't typically code
        # (Be very conservative here to avoid filtering valid code)
        markdown_patterns = [
            r"^##\s+", # Multiple hash markdown headings are rarely code comments
            r"^>\s+", # Blockquotes
            r"^-\s+-\s+-", # Markdown horizontal rules
            r"^!\[.*\]\(.*\)", # Image links
            r"^Here's the code:", # Common explanatory phrases before code
            r"^The output will be:",
            r"^This implementation"
        ]

        filtered_lines = []
        in_explanation_block = False

        for line in lines:
            # Check if this line is clear markdown/explanation
            is_markdown = any(re.match(pattern, line) for pattern in markdown_patterns)

            # Lines that start with explanatory text and end with a colon often introduce code
            if is_markdown or (line.strip().endswith(':') and not re.match(r'^\s*[a-zA-Z0-9_]+\s*:', line)):
                in_explanation_block = True
                continue

            # If line is indented or looks like code, we're no longer in explanation
            if line.startswith('    ') or any(re.match(pattern, line) for pattern in code_indicators):
                in_explanation_block = False

            # Keep the line if it's not in an explanation block
            if not in_explanation_block:
                filtered_lines.append(line)

        # If we filtered everything, just return the original
        if not filtered_lines:
            return raw_output.strip()

        return "\n".join(filtered_lines)

    @staticmethod
    def extract_json(raw_output: str) -> str:
        """Extract JSON from potentially mixed content

        Handles cases where JSON is wrapped in explanatory text or markdown.
        Returns the cleanest version of the actual JSON structure.
        """
        # Try to find JSON blocks marked with markdown
        json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        json_blocks = re.findall(json_block_pattern, raw_output)

        if json_blocks:
            # Return the largest JSON block (most likely the complete one)
            return max(json_blocks, key=len).strip()

        # If no explicit JSON blocks, look for JSON-like structures
        json_pattern = r"(\{[\s\S]*\})"
        json_matches = re.findall(json_pattern, raw_output)

        if json_matches:
            # Return the largest JSON-like structure
            candidate = max(json_matches, key=len).strip()
            try:
                # Verify it's valid JSON
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                logger.warning("Found JSON-like structure but it's not valid JSON")

        # If we can't find valid JSON, return the raw output as a last resort
        logger.warning("Could not extract valid JSON, returning raw output")
        return raw_output

    @staticmethod
    def clean_and_verify_json(json_str: str) -> Dict:
        """Clean and verify JSON string, attempting to fix common issues"""
        # First try direct parsing
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parsing failed: {str(e)}")

            # Attempt to clean common issues
            clean_json = json_str

            # Replace single quotes with double quotes (common LLM mistake)
            clean_json = re.sub(r"'([^']*)':", r'"\1":', clean_json)

            # Fix trailing commas in arrays/objects (another common issue)
            clean_json = re.sub(r",\s*\}", "}", clean_json)
            clean_json = re.sub(r",\s*\]", "]", clean_json)

            try:
                return json.loads(clean_json)
            except json.JSONDecodeError:
                # If still failing, try a more aggressive approach - find the largest valid JSON subset
                logger.warning("Failed to parse JSON after cleaning, attempting to extract valid subset")

                # Extract all string patterns that look like valid JSON objects
                candidates = re.findall(r"(\{[\s\S]*?\})", clean_json)

                valid_candidates = []
                for candidate in candidates:
                    try:
                        parsed = json.loads(candidate)
                        valid_candidates.append((parsed, candidate))
                    except json.JSONDecodeError:
                        continue

                if valid_candidates:
                    # Use the largest valid JSON object found
                    valid_candidates.sort(key=lambda x: len(x[1]), reverse=True)
                    logger.warning("Found valid JSON subset")
                    return valid_candidates[0][0]

                raise GenerationError("Failed to parse JSON after multiple cleaning attempts")


class LLMClient:
    """Client for LLM API interactions with advanced features and output processing"""

    @staticmethod
    async def generate_async(prompt: str, context: str,
                            max_retries: int = None,
                            temperature: float = None,
                            expected_type: str = "code") -> str:
        """Asynchronous generation with retries, error handling, and output processing

        Args:
            prompt: The prompt to send to the LLM
            context: Context information to include with the prompt
            max_retries: Maximum number of retry attempts
            temperature: Temperature setting for generation
            expected_type: Expected output type ('code', 'json', or 'text')

        Returns:
            Processed output based on the expected_type
        """
        if max_retries is None:
            max_retries = Config.options.max_retries

        if temperature is None:
            temperature = Config.options.temperature

        # Check cache first
        cached = GenerationCache.get(prompt, context)
        if cached:
            logger.debug("Using cached generation result")
            return cached

        full_prompt = f"{context}\n\n{prompt}\nRespond with ONLY valid {'Python code' if expected_type == 'code' else 'JSON' if expected_type == 'json' else 'text'}, no markdown."

        for attempt in range(max_retries):
            try:
                # Convert to async call using asyncio.to_thread
                response = await asyncio.to_thread(
                    ollama.generate,
                    model=Config.options.model,
                    prompt=full_prompt,
                    options={"temperature": temperature}
                )

                raw_result = response["response"].strip()

                # Process the raw output based on expected type
                processed_result = LLMClient._process_raw_output(raw_result, expected_type)

                # Store processed result in cache
                GenerationCache.store(prompt, context, processed_result)

                return processed_result
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    retry_delay = Config.options.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {retry_delay:.2f} seconds...")
                    await asyncio.sleep(retry_delay)

        raise GenerationError(f"Failed to generate after {max_retries} attempts")

    @staticmethod
    def _process_raw_output(raw_output: str, expected_type: str) -> str:
        """Process raw LLM output based on expected content type

        Handles extraction and cleaning of code, JSON, or text.
        """
        if expected_type == "code":
            return OutputParser.extract_code(raw_output)
        elif expected_type == "json":
            return OutputParser.extract_json(raw_output)
        else:
            # For plain text, just return with minimal cleanup
            return raw_output.strip()

    @staticmethod
    def generate(prompt: str, context: str,
                max_retries: int = None,
                temperature: float = None,
                expected_type: str = "code") -> str:
        """Synchronous wrapper for generate_async"""
        return asyncio.run(LLMClient.generate_async(
            prompt, context, max_retries, temperature, expected_type
        ))


class DependencyResolver:
    """Resolves component dependencies and determines generation order"""

    @staticmethod
    def create_dependency_graph(structure: Structure) -> nx.DiGraph:
        """Create a directed graph of component dependencies"""
        G = nx.DiGraph()

        # Map component names to their file paths
        component_map = {}
        for file in structure.files:
            for component in file.components:
                component_id = f"{file.path}:{component.name}"
                component_map[component.name] = component_id
                G.add_node(component_id,
                           component=component,
                           file_path=file.path,
                           priority=component.priority)

        # Add dependency edges
        for file in structure.files:
            for component in file.components:
                component_id = f"{file.path}:{component.name}"

                for dep_name in component.dependencies:
                    if dep_name in component_map:
                        G.add_edge(component_map[dep_name], component_id)
                    else:
                        logger.warning(f"Dependency '{dep_name}' not found for component '{component.name}'")

        return G

    @staticmethod
    def get_generation_order(structure: Structure) -> List[Tuple[str, Component]]:
        """Get optimal generation order considering dependencies and priorities"""
        G = DependencyResolver.create_dependency_graph(structure)

        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                cycle_str = ", ".join(" -> ".join(c) for c in cycles)
                raise DependencyError(f"Circular dependencies detected: {cycle_str}")
        except nx.NetworkXNoCycle:
            pass  # No cycles found

        # Get topological sort (respects dependencies)
        try:
            # Sort by priority within same dependency level
            topo_order = list(nx.lexicographical_topological_sort(
                G,
                key=lambda n: (-G.nodes[n].get('priority', 0), n)
            ))

            # Convert to (file_path, component) tuples
            generation_order = []
            for component_id in topo_order:
                node = G.nodes[component_id]
                generation_order.append((node['file_path'], node['component']))

            return generation_order
        except nx.NetworkXUnfeasible:
            # Handle case where topo sort isn't possible (cycles)
            raise DependencyError("Cannot determine generation order due to circular dependencies")


class ProjectGenerator:
    """Manages the entire project generation process"""

    def __init__(self):
        """Initialize generator with default state"""
        self.plan = {}
        self.structure = None
        self.generated_code = {}
        self.generated_tests = {}

    async def generate_component_async(self, component: Component, file_path: str) -> str:
        """Generate a single component asynchronously with validation and recovery"""
        with console.status(f"Generating {component.type} '{component.name}'..."):
            prompt = PromptTemplate.get(
                "component",
                component_type=component.type,
                component_name=component.name,
                file_path=file_path,
                description=component.description,
                requirements=component.requirements,
                dependencies=", ".join(component.dependencies)
            )

            code = await LLMClient.generate_async(prompt, file_path, expected_type="code")

            # Enhanced verification and recovery
            valid, error_message = CodeVerifier.verify_syntax(code)
            if not valid:
                logger.warning(f"Syntax verification failed for {component.name}: {error_message}")

                # Attempt to repair common syntax errors
                logger.info(f"Attempting to repair syntax for {component.name}")
                repaired_code = CodeVerifier.repair_syntax_errors(code, error_message)

                # Verify the repaired code
                valid, error_message = CodeVerifier.verify_syntax(repaired_code)
                if valid:
                    logger.info(f"Successfully repaired syntax for {component.name}")
                    code = repaired_code
                else:
                    # If repair failed, try regeneration with error feedback
                    logger.warning(f"Repair failed, attempting regeneration with error feedback")

                    # Create regeneration prompt with specific error information
                    recovery_prompt = f"{prompt}\n\nThe previous code had the following syntax error:\n{error_message}\nPlease fix the issues and ensure the code is syntactically valid."

                    # Regenerate the component
                    code = await LLMClient.generate_async(recovery_prompt, file_path, expected_type="code")

                    # Final verification
                    valid, error_message = CodeVerifier.verify_syntax(code)
                    if not valid:
                        logger.error(f"Still encountering syntax issues after regeneration: {error_message}")

            # Perform AST-based validation to ensure component structure
            structure_valid, component_info, structure_error = CodeVerifier.verify_component_structure(
                code, component.type, component.name
            )

            if not structure_valid:
                logger.warning(f"Structure verification failed for {component.name}: {structure_error}")

                if component_info:
                    # Use the detected information to guide regeneration
                    structure_feedback = ""

                    if component.type.lower() == "class":
                        if "found_classes" in component_info:
                            found = component_info["found_classes"]
                            if found:
                                structure_feedback = f"The generated code contains class(es) named {', '.join(found)} instead of '{component.name}'."
                            else:
                                structure_feedback = "The generated code doesn't contain any class definitions."

                    elif component.type.lower() == "function":
                        if "found_functions" in component_info:
                            found = component_info["found_functions"]
                            if found:
                                structure_feedback = f"The generated code contains function(s) named {', '.join(found)} instead of '{component.name}'."
                            else:
                                structure_feedback = "The generated code doesn't contain any function definitions."

                    if structure_feedback:
                        # Regenerate with structural guidance
                        recovery_prompt = f"{prompt}\n\n{structure_feedback} Please ensure the {component.type} is named exactly '{component.name}'."

                        # Regenerate the component
                        code = await LLMClient.generate_async(recovery_prompt, file_path, expected_type="code")

            # Verify imports
            imports_valid, imported_modules, import_error = CodeVerifier.verify_imports(code)
            if imports_valid and imported_modules:
                logger.debug(f"Imports for {component.name}: {', '.join(imported_modules)}")

            return code snippet
                    error_lines = code.split('\n')
                    if len(error_lines) > 5:
                        error_context = '\n'.join(error_lines[:5]) + "\n..."
                    else:
                        error_context = code
                    logger.debug(f"Code with syntax error:\n{error_context}")

            return code

    async def generate_test_async(self, component: Component, file_path: str, code: str) -> str:
        """Generate tests for a component asynchronously with validation and recovery"""
        with console.status(f"Generating tests for '{component.name}'..."):
            prompt = PromptTemplate.get(
                "test",
                component_type=component.type,
                component_name=component.name,
                file_path=file_path,
                component_code=code
            )

            test_code = await LLMClient.generate_async(prompt, file_path, expected_type="code")

            # Verify and repair tests similar to components
            valid, error_message = CodeVerifier.verify_syntax(test_code)
            if not valid:
                logger.warning(f"Syntax verification failed for tests of {component.name}: {error_message}")

                # Attempt to repair common syntax errors
                logger.info(f"Attempting to repair test syntax for {component.name}")
                repaired_code = CodeVerifier.repair_syntax_errors(test_code, error_message)

                # Verify the repaired code
                valid, error_message = CodeVerifier.verify_syntax(repaired_code)
                if valid:
                    logger.info(f"Successfully repaired test syntax for {component.name}")
                    test_code = repaired_code
                else:
                    # If repair failed, try regeneration with error feedback
                    logger.warning(f"Test repair failed, attempting regeneration with error feedback")

                    # Create regeneration prompt with specific error information
                    recovery_prompt = f"{prompt}\n\nThe previous test code had the following syntax error:\n{error_message}\nPlease fix the issues and ensure the test code is syntactically valid."

                    # Regenerate the tests
                    test_code = await LLMClient.generate_async(recovery_prompt, file_path, expected_type="code")

            # Verify test structure - look for pytest patterns
            if "pytest" not in test_code.lower() and "test_" not in test_code:
                logger.warning(f"Generated test code for {component.name} may not be proper pytest tests")

                # Regenerate with more specific pytest instructions
                recovery_prompt = f"{prompt}\n\nPlease ensure tests follow pytest conventions with test_ prefixes for test functions and proper pytest assertions."
                test_code = await LLMClient.generate_async(recovery_prompt, file_path, expected_type="code")

            return test_code

    async def plan_development_async(self, description: str) -> Dict:
        """Generate detailed development plan with component breakdown"""
        with console.status("Planning development..."):
            prompt = PromptTemplate.get("plan")
            plan_json = await LLMClient.generate_async(prompt, description, expected_type="json")

            try:
                # Parse and clean JSON
                plan_data = OutputParser.clean_and_verify_json(plan_json)

                # Validate against schema
                is_valid, error_msg = JsonSchemaValidator.validate(plan_data, "plan")
                if not is_valid:
                    logger.warning(f"Plan validation failed: {error_msg}")

                    # Get missing fields for more specific feedback
                    missing_fields = JsonSchemaValidator.get_missing_required_fields(plan_data, "plan")
                    if missing_fields:
                        logger.warning(f"Missing required fields: {', '.join(missing_fields)}")

                        # Try to regenerate with more specific guidance
                        if len(missing_fields) <= 3:  # Only attempt fix if issues are limited
                            recovery_prompt = f"{prompt}\n\nYour previous response was missing these required fields: {', '.join(missing_fields)}. Please include them in the JSON structure."

                            # Regenerate with updated prompt
                            logger.info("Attempting to regenerate plan with fixed fields")
                            plan_json = await LLMClient.generate_async(recovery_prompt, description, expected_type="json")
                            plan_data = OutputParser.clean_and_verify_json(plan_json)

                            # Validate again
                            is_valid, error_msg = JsonSchemaValidator.validate(plan_data, "plan")
                            if not is_valid:
                                logger.warning(f"Regenerated plan still invalid: {error_msg}")

                return plan_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse plan JSON: {str(e)}")
                logger.debug(f"Raw plan output: {plan_json}")

                # More detailed error for debugging
                error_context = plan_json[:50] + "..." if len(plan_json) > 50 else plan_json
                raise GenerationError(f"Invalid plan JSON format near: {error_context}") from e

    async def create_directory_structure_async(self, plan: Dict) -> Structure:
        """Generate detailed directory structure with component specs"""
        with console.status("Creating directory structure..."):
            prompt = PromptTemplate.get("structure")
            structure_json = await LLMClient.generate_async(
                prompt, json.dumps(plan), expected_type="json"
            )

            try:
                # Parse and clean JSON
                structure_dict = OutputParser.clean_and_verify_json(structure_json)

                # Validate against schema
                is_valid, error_msg = JsonSchemaValidator.validate(structure_dict, "structure")
                if not is_valid:
                    logger.warning(f"Structure validation failed: {error_msg}")

                    # Get missing fields for more specific feedback
                    missing_fields = JsonSchemaValidator.get_missing_required_fields(structure_dict, "structure")
                    if missing_fields:
                        logger.warning(f"Missing required fields: {', '.join(missing_fields)}")

                        # Try to regenerate with more specific guidance
                        if len(missing_fields) <= 5:  # Only attempt fix if issues are limited
                            recovery_prompt = f"{prompt}\n\nYour previous response was missing these required fields: {', '.join(missing_fields)}. Please include them in the JSON structure."

                            # Regenerate with updated prompt
                            logger.info("Attempting to regenerate structure with fixed fields")
                            structure_json = await LLMClient.generate_async(recovery_prompt, json.dumps(plan), expected_type="json")
                            structure_dict = OutputParser.clean_and_verify_json(structure_json)

                # Continue with validation
                self._validate_structure(structure_dict)
                return Structure.from_dict(structure_dict)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse structure JSON: {str(e)}")
                logger.debug(f"Raw structure output: {structure_json}")

                # More detailed error for debugging
                error_context = structure_json[:50] + "..." if len(structure_json) > 50 else structure_json
                raise GenerationError(f"Invalid structure JSON format near: {error_context}") from e

    def _validate_structure(self, structure: Dict):
        """Validate component-based structure"""
        required = {"structure", "files"}
        if missing := required - structure.keys():
            raise ValueError(f"Missing required keys in structure: {missing}")

        for file in structure["files"]:
            required_file_keys = {"path", "components"}
            if missing := required_file_keys - file.keys():
                raise ValueError(f"Invalid file {file.get('path')}: missing {missing}")

            for comp in file["components"]:
                required_comp = {"name", "type", "description"}
                if missing := required_comp - comp.keys():
                    raise ValueError(f"Invalid component {comp.get('name')}: missing {missing}")

    async def generate_code_components_async(self, structure: Structure) -> Dict[str, str]:
        """Generate code components concurrently with dependency resolution"""
        code_files = {}

        # Get generation order respecting dependencies
        generation_order = DependencyResolver.get_generation_order(structure)

        # Group by file for component-wise or file-wise generation
        if Config.options.generation_strategy == GenerationStrategy.FILE_WISE:
            file_components = {}
            for file_path, component in generation_order:
                if file_path not in file_components:
                    file_components[file_path] = []
                file_components[file_path].append(component)

            # Generate file by file
            for file_path, components in file_components.items():
                file_content = []
                for component in components:
                    component.generated_code = await self.generate_component_async(component, file_path)
                    file_content.append(component.generated_code)

                code_files[file_path] = "\n\n".join(file_content)
        else:
            # Generate component by component with concurrency limit
            semaphore = asyncio.Semaphore(Config.options.concurrency_limit)

            async def generate_with_semaphore(component, file_path):
                async with semaphore:
                    return await self.generate_component_async(component, file_path)

            # Create tasks for all components
            tasks = []
            for file_path, component in generation_order:
                task = asyncio.create_task(generate_with_semaphore(component, file_path))
                tasks.append((file_path, component, task))

            # Wait for all tasks to complete
            for file_path, component, task in tasks:
                try:
                    component.generated_code = await task
                except Exception as e:
                    logger.error(f"Failed to generate {component.name}: {str(e)}")
                    component.generated_code = f"# ERROR: Generation failed for {component.name}\n# {str(e)}"

            # Combine components into files
            for file in structure.files:
                file_content = []
                for component in file.components:
                    if component.generated_code:
                        file_content.append(component.generated_code)

                code_files[file.path] = "\n\n".join(file_content)

        return code_files

    async def create_tests_async(self, structure: Structure) -> Dict[str, str]:
        """Generate component-specific test cases asynchronously"""
        tests = {}
        semaphore = asyncio.Semaphore(Config.options.concurrency_limit)

        async def generate_test_with_semaphore(component, file_path):
            async with semaphore:
                if not component.tests_required or not component.generated_code:
                    return None
                return await self.generate_test_async(component, file_path, component.generated_code)

        # Create test tasks for all components that need tests
        test_tasks = {}
        for file in structure.files:
            test_file = f"tests/test_{os.path.basename(file.path)}"
            test_tasks[test_file] = []

            for component in file.components:
                if component.tests_required:
                    task = asyncio.create_task(
                        generate_test_with_semaphore(component, file.path)
                    )
                    test_tasks[test_file].append((component, task))

        # Collect test results
        for test_file, tasks in test_tasks.items():
            test_content = []
            for component, task in tasks:
                try:
                    test_code = await task
                    if test_code:
                        test_content.append(test_code)
                except Exception as e:
                    logger.error(f"Failed to generate tests for {component.name}: {str(e)}")

            if test_content:
                tests[test_file] = "\n\n".join(test_content)

        return tests

    def build_project(self, code: Dict[str, str], tests: Dict[str, str], structure: Structure):
        """Build project with component files"""
        output_dir = Path(Config.options.output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Create files task
            files_task = progress.add_task("Creating project files...", total=len(code) + len(tests))

            # Write code files
            for path, content in code.items():
                self._write_file(output_dir, path, content)
                progress.update(files_task, advance=1)

            # Write test files
            for path, content in tests.items():
                self._write_file(output_dir, path, content)
                progress.update(files_task, advance=1)

            # Create setup.py if not already created
            if structure and not any(f.path == "setup.py" for f in structure.files):
                setup_content = self._generate_setup_py(structure)
                self._write_file(output_dir, "setup.py", setup_content)

        logger.info(f"Project built successfully in {output_dir}")

    def _write_file(self, base_dir: Path, path: str, content: str):
        """Write file with directory creation"""
        full_path = base_dir / path
        full_path.parent.mkdir(exist_ok=True, parents=True)

        full_path.write_text(content)
        logger.debug(f"Created: {full_path}")

    def _generate_setup_py(self, structure: Structure) -> str:
        """Generate setup.py based on project structure"""
        # Extract project name from output directory
        project_name = os.path.basename(Config.options.output_dir)
        if project_name == "generated_project":
            project_name = "generated_app"

        # Find packages
        packages = set()
        for file in structure.files:
            if file.path.endswith(".py") and "/" in file.path:
                package = file.path.split("/")[0]
                if package != "tests":
                    packages.add(package)

        # Find dependencies
        dependencies = set()
        for file in structure.files:
            for imp in file.imports:
                if imp not in ["os", "sys", "json", "logging", "typing", "collections", "pathlib"]:
                    dependencies.add(imp)

        setup_py = f"""
from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages={list(packages) if packages else "find_packages()"},
    install_requires={list(dependencies) if dependencies else "[]"},
    author="AI Generator",
    author_email="ai@example.com",
    description="Generated Python application",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
"""
        return setup_py

    async def iterative_development_async(self, description: str, max_iterations: int = 5):
        """Development loop with component verification and async execution"""
        iteration = 0
        approved = False

        GenerationCache.initialize()
        PromptTemplate.load_templates()

        while iteration < max_iterations and not approved:
            try:
                console.rule(f"[bold green]Iteration {iteration + 1}")

                self.plan = await self.plan_development_async(description)
                self.structure = await self.create_directory_structure_async(self.plan)

                # Generate code and tests concurrently
                self.generated_code = await self.generate_code_components_async(self.structure)
                self.generated_tests = await self.create_tests_async(self.structure)

                self.build_project(self.generated_code, self.generated_tests, self.structure)

                console.print("[bold green]Project generation complete!")
                console.print("Project files generated in:", Config.options.output_dir)

                user_input = input("Approve project? (y/n): ").lower()
                if user_input == "y":
                    approved = True
                    logger.info("Project approved!")
                else:
                    iteration += 1
                    feedback = input("Enter feedback (specific components to modify): ")
                    description += f"\nITERATION {iteration} FEEDBACK: {feedback}"

            except Exception as e:
                logger.error(f"Iteration failed: {traceback.format_exc()}")
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
                iteration += 1

                user_input = input("Continue to next iteration? (y/n): ").lower()
                if user_input != "y":
                    break

    def iterative_development(self, description: str, max_iterations: int = 5):
        """Synchronous wrapper for iterative_development_async"""
        asyncio.run(self.iterative_development_async(description, max_iterations))


async def main_async():
    """Asynchronous main entry point"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="AI-Powered Application Generator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output", help="Output directory for generated project")
    parser.add_argument("--model", help="Model to use for generation")
    parser.add_argument("--description", help="Application description")
    parser.add_argument("--max-iterations", type=int, default=5, help="Maximum iterations")
    args = parser.parse_args()

    # Load configuration
    if args.config:
        Config.from_file(args.config)

    # Override config with command line arguments
    if args.output:
        Config.options.output_dir = args.output
    if args.model:
        Config.options.model = args.model

    console.rule("[bold blue]AI-Powered Application Generator")
    console.print(f"Using model: {Config.options.model}")
    console.print(f"Output directory: {Config.options.output_dir}")

    # Create generator
    generator = ProjectGenerator()

    # Get description
    description = args.description
    if not description:
        description = input("Enter application description: ")

    # Run development loop
    await generator.iterative_development_async(description, args.max_iterations)


async def main_async():
    """Asynchronous main entry point"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="AI-Powered Application Generator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output", help="Output directory for generated project")
    parser.add_argument("--model", help="Model to use for generation")
    parser.add_argument("--description", help="Application description")
    parser.add_argument("--max-iterations", type=int, default=5, help="Maximum iterations")
    parser.add_argument("--skip-validation", action="store_true", help="Skip schema validation")
    parser.add_argument("--skip-structure-check", action="store_true", help="Skip component structure validation")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity")
    args = parser.parse_args()

    # Set logging level based on verbosity
    if args.verbose >= 2:
        logging.getLogger("appgen").setLevel(logging.DEBUG)
    elif args.verbose >= 1:
        logging.getLogger("appgen").setLevel(logging.INFO)

    # Load configuration
    if args.config:
        Config.from_file(args.config)

    # Override config with command line arguments
    if args.output:
        Config.options.output_dir = args.output
    if args.model:
        Config.options.model = args.model
    if args.skip_validation:
        Config.options.schema_validation = False
    if args.skip_structure_check:
        Config.options.verify_structure = False

    if rich_available:
        console.rule("[bold blue]AI-Powered Application Generator")
        console.print(f"Using model: {Config.options.model}")
        console.print(f"Output directory: {Config.options.output_dir}")
    else:
        print("=" * 40)
        print("AI-Powered Application Generator")
        print("=" * 40)
        print(f"Using model: {Config.options.model}")
        print(f"Output directory: {Config.options.output_dir}")

    # Check for compatibility issues
    _print_compatibility_warnings()

    # Create generator
    generator = ProjectGenerator()

    # Get description
    description = args.description
    if not description:
        description = input("Enter application description: ")

    # Run development loop
    await generator.iterative_development_async(description, args.max_iterations)


def _print_compatibility_warnings():
    """Print warnings about potential compatibility issues"""
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    if sys.version_info.major == 3 and sys.version_info.minor < 9:
        message = (f"[yellow]Warning: Using Python {python_version}. Some features may work better with Python 3.9+[/yellow]"
                   if rich_available else f"Warning: Using Python {python_version}. Some features may work better with Python 3.9+")
        console.print(message)

    # Check ollama version
    try:
        # We can't directly check ollama version, but we can check for known API endpoints
        ollama.models()
    except Exception as e:
        message = (f"[yellow]Warning: Could not verify Ollama installation. Make sure Ollama server is running.[/yellow]"
                   if rich_available else "Warning: Could not verify Ollama installation. Make sure Ollama server is running.")
        console.print(message)

    # Check for required network connectivity
    try:
        import socket
        socket.create_connection(("localhost", 11434), timeout=1)
    except Exception:
        message = (f"[red]Warning: Cannot connect to Ollama server on localhost:11434. Make sure it's running.[/red]"
                   if rich_available else "Warning: Cannot connect to Ollama server on localhost:11434. Make sure it's running.")
        console.print(message)





class ProjectValidator:
    """Validates the overall project structure and consistency"""

    @staticmethod
    def validate_project(structure: Structure, generated_code: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate overall project structure and detect potential issues

        Args:
            structure: The project structure
            generated_code: Dict of generated code files

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        # Check file completeness
        missing_files = set(f.path for f in structure.files) - set(generated_code.keys())
        if missing_files:
            issues.append(f"Missing files: {', '.join(missing_files)}")

        # Validate imports between files
        import_issues = ProjectValidator._validate_imports(structure, generated_code)
        issues.extend(import_issues)

        # Check for circular dependencies
        dependency_issues = ProjectValidator._check_circular_dependencies(structure)
        issues.extend(dependency_issues)

        # Validate entrypoint if specified
        entrypoint_issues = ProjectValidator._validate_entrypoint(structure, generated_code)
        issues.extend(entrypoint_issues)

        # Check package structure consistency
        package_issues = ProjectValidator._validate_package_structure(structure)
        issues.extend(package_issues)

        return len(issues) == 0, issues

    @staticmethod
    def _validate_imports(structure: Structure, generated_code: Dict[str, str]) -> List[str]:
        """Validate imports between files"""
        issues = []

        # Build a map of components to files
        component_map = {}
        for file in structure.files:
            for component in file.components:
                component_map[component.name] = file.path

        # Check imports for each file
        for file in structure.files:
            if file.path not in generated_code:
                continue

            code = generated_code[file.path]
            _, imported_modules, _ = CodeVerifier.verify_imports(code)

            # Map imported modules to files to check for missing imports
            for module in imported_modules:
                # Skip standard library and third-party modules
                if module in ["os", "sys", "logging", "json", "typing", "pathlib",
                              "asyncio", "dataclasses", "enum", "time", "traceback",
                              "ollama", "networkx", "rich", "re", "hashlib", "ast",
                              "jsonschema", "importlib"]:
                    continue

                # Check if this is a component that should be in another file
                module_parts = module.split('.')
                base_module = module_parts[0]

                if base_module in component_map and component_map[base_module] != file.path:
                    # Component exists in a different file - check if imported properly
                    target_file = component_map[base_module]

                    # Convert file paths to module paths
                    target_module = target_file.replace("/", ".").replace(".py", "")

                    # Check if the file explicitly imports from this module
                    if target_module not in imported_modules and base_module in imported_modules:
                        issues.append(f"File {file.path} may be using component {base_module} without proper import from {target_file}")

        return issues

    @staticmethod
    def _check_circular_dependencies(structure: Structure) -> List[str]:
        """Check for circular dependencies in project structure"""
        issues = []

        # Build a dependency graph
        G = nx.DiGraph()

        # Add files as nodes
        for file in structure.files:
            G.add_node(file.path)

        # Add edges for imports/dependencies
        for file in structure.files:
            file_components = {comp.name for comp in file.components}

            for component in file.components:
                for dep_name in component.dependencies:
                    # Find which file contains this dependency
                    for dep_file in structure.files:
                        if any(comp.name == dep_name for comp in dep_file.components):
                            if dep_file.path != file.path:  # Skip self-dependencies
                                G.add_edge(file.path, dep_file.path)

        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles:
                issues.append(f"Circular dependency detected: {' -> '.join(cycle)}")
        except nx.NetworkXNoCycle:
            # No cycles found
            pass

        return issues

    @staticmethod
    def _validate_entrypoint(structure: Structure, generated_code: Dict[str, str]) -> List[str]:
        """Validate project entrypoint if specified"""
        issues = []

        # Find entrypoint files
        entrypoint_files = [f for f in structure.files if f.is_entrypoint]

        if not entrypoint_files:
            issues.append("No entrypoint file marked in the project structure")
            return issues

        for entrypoint in entrypoint_files:
            if entrypoint.path not in generated_code:
                issues.append(f"Entrypoint file {entrypoint.path} not generated")
                continue

            code = generated_code[entrypoint.path]

            # Check for main block
            if "if __name__ == \"__main__\"" not in code and "if __name__ == '__main__'" not in code:
                issues.append(f"Entrypoint file {entrypoint.path} is missing a main block")

        return issues

    @staticmethod
    def _validate_package_structure(structure: Structure) -> List[str]:
        """Validate package structure consistency"""
        issues = []

        # Get unique directories
        directories = set()
        for file in structure.files:
            path = Path(file.path)
            if path.parent != Path("."):
                directories.add(str(path.parent))

        # Check for __init__.py in each directory
        for directory in directories:
            init_file = f"{directory}/__init__.py"
            if not any(f.path == init_file for f in structure.files):
                issues.append(f"Missing __init__.py in package directory {directory}")

        return issuesclass OutputParser:
    """Parser for extracting and cleaning LLM-generated content"""

    @staticmethod
    def extract_code(raw_output: str) -> str:
        """Extract Python code from potentially mixed content

        Handles common formats including markdown code blocks, explanatory text, etc.
        Returns the cleanest version of the actual Python code.
        """
        # Try to find code blocks marked with Python markdown
        code_block_pattern = r"```(?:python)?\s*([\s\S]*?)```"
        code_blocks = re.findall(code_block_pattern, raw_output)

        if code_blocks:
            # Join multiple code blocks with newlines
            return "\n\n".join(block.strip() for block in code_blocks)

        # If no code blocks found, use more sophisticated analysis
        lines = raw_output.strip().split('\n')

        # First, check if the output has strong code indicators
        code_indicators = [
            r"^import\s+",
            r"^from\s+.*\s+import\s+",
            r"^def\s+",
            r"^class\s+",
            r"^if\s+__name__\s+==",
            r"^\s+[a-zA-Z0-9_]+\s*=", # Indented assignment
            r"^[a-zA-Z0-9_]+\s*=", # Assignment
            r"^@[a-zA-Z0-9_]+" # Decorator
        ]

        # Count lines that are very likely to be code
        strong_code_indicators = sum(
            1 for line in lines
            if any(re.match(pattern, line) for pattern in code_indicators)
        )

        # If we have strong code indicators, assume it's all code
        if strong_code_indicators > 0:
            return raw_output.strip()

        # Otherwise, look for clear markdown/explanation patterns that aren't typically code
        # (Be very conservative here to avoid filtering valid code)
        markdown_patterns = [
            r"^##\s+", # Multiple hash markdown headings are rarely code comments
            r"^>\s+", # Blockquotes
            r"^-\s+-\s+-", # Markdown horizontal rules
            r"^!\[.*\]\(.*\)", # Image links
            r"^Here's the code:", # Common explanatory phrases before code
            r"^The output will be:",
            r"^This implementation"
        ]

        filtered_lines = []
        in_explanation_block = False

        for line in lines:
            # Check if this line is clear markdown/explanation
            is_markdown = any(re.match(pattern, line) for pattern in markdown_patterns)

            # Lines that start with explanatory text and end with a colon often introduce code
            if is_markdown or (line.strip().endswith(':') and not re.match(r'^\s*[a-zA-Z0-9_]+\s*:', line)):
                in_explanation_block = True
                continue

            # If line is indented or looks like code, we're no longer in explanation
            if line.startswith('    ') or any(re.match(pattern, line) for pattern in code_indicators):
                in_explanation_block = False

            # Keep the line if it's not in an explanation block
            if not in_explanation_block:
                filtered_lines.append(line)

        # If we filtered everything, just return the original
        if not filtered_lines:
            return raw_output.strip()

        return "\n".join(filtered_lines)

    @staticmethod
    def extract_json(raw_output: str) -> str:
        """Extract JSON from potentially mixed content

        Handles cases where JSON is wrapped in explanatory text or markdown.
        Returns the cleanest version of the actual JSON structure.
        """
        # Try to find JSON blocks marked with markdown
        json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        json_blocks = re.findall(json_block_pattern, raw_output)

        if json_blocks:
            # Return the largest JSON block (most likely the complete one)
            return max(json_blocks, key=len).strip()

        # If no explicit JSON blocks, look for JSON-like structures
        # More precise pattern - look for balanced braces
        json_content = raw_output.strip()

        # Try to find outermost JSON object with balanced braces
        open_brace_index = json_content.find('{')
        if open_brace_index >= 0:
            # Find matching closing brace
            brace_count = 0
            for i in range(open_brace_index, len(json_content)):
                if json_content[i] == '{':
                    brace_count += 1
                elif json_content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found balanced object
                        extracted_json = json_content[open_brace_index:i+1]
                        try:
                            # Verify it's valid JSON
                            json.loads(extracted_json)
                            return extracted_json
                        except json.JSONDecodeError:
                            # If not valid, continue searching
                            pass

        # Fallback to the original pattern
        json_pattern = r"(\{[\s\S]*\})"
        json_matches = re.findall(json_pattern, raw_output)

        if json_matches:
            # Try each match to find valid JSON
            for match in sorted(json_matches, key=len, reverse=True):
                try:
                    json.loads(match.strip())
                    return match.strip()
                except json.JSONDecodeError:
                    continue

        # If we can't find valid JSON, return the raw output as a last resort
        logger.warning("Could not extract valid JSON, returning raw output")
        return raw_output

    @staticmethod
    def clean_and_verify_json(json_str: str) -> Dict:
        """Clean and verify JSON string, attempting to fix common issues"""
        # First try direct parsing
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parsing failed: {str(e)}")

            # Attempt to clean common issues
            clean_json = json_str

            # Replace single quotes with double quotes (common LLM mistake)
            clean_json = re.sub(r"'([^']*)':", r'"\1":', clean_json)

            # Fix trailing commas in arrays/objects (another common issue)
            clean_json = re.sub(r",\s*\}", "}", clean_json)
            clean_json = re.sub(r",\s*\]", "]", clean_json)

            # Fix missing commas between objects in arrays
            clean_json = re.sub(r"}\s*{", "},{", clean_json)

            # Fix missing quotes around property names
            clean_json = re.sub(r"([{,])\s*([a-zA-Z0-9_]+)\s*:", r'\1"\2":', clean_json)

            try:
                return json.loads(clean_json)
            except json.JSONDecodeError:
                # If still failing, try a more aggressive approach - find the largest valid JSON subset
                logger.warning("Failed to parse JSON after cleaning, attempting to extract valid subset")

                # Try to find balanced JSON objects
                open_brace_index = clean_json.find('{')
                if open_brace_index >= 0:
                    # Find matching closing brace with proper nesting
                    brace_count = 0
                    for i in range(open_brace_index, len(clean_json)):
                        if clean_json[i] == '{':
                            brace_count += 1
                        elif clean_json[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                # Found balanced object
                                candidate = clean_json[open_brace_index:i+1]
                                try:
                                    return json.loads(candidate)
                                except json.JSONDecodeError:
                                    # Continue if this isn't valid
                                    pass

                # Extract all string patterns that look like valid JSON objects as fallback
                candidates = re.findall(r"(\{[\s\S]*?\})", clean_json)

                valid_candidates = []
                for candidate in candidates:
                    try:
                        parsed = json.loads(candidate)
                        valid_candidates.append((parsed, candidate))
                    except json.JSONDecodeError:
                        continue

                if valid_candidates:
                    # Use the largest valid JSON object found
                    valid_candidates.sort(key=lambda x: len(x[1]), reverse=True)
                    logger.warning("Found valid JSON subset")
                    return valid_candidates[0][0]

                raise GenerationError("Failed to parse JSON after multiple cleaning attempts")class JsonSchemaValidator:
    """JSON schema validation for structured outputs"""

    # Schema definitions for different output types
    SCHEMAS = {
        "plan": {
            "type": "object",
            "required": ["architecture", "components"],
            "properties": {
                "architecture": {
                    "type": "object",
                    "description": "Overall application architecture"
                },
                "components": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "type", "description"],
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "description": {"type": "string"},
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                },
                "fileStructure": {"type": "object"},
                "dependencies": {"type": "array", "items": {"type": "string"}},
                "testing": {"type": "object"}
            }
        },

        "structure": {
            "type": "object",
            "required": ["structure", "files"],
            "properties": {
                "structure": {
                    "type": "object",
                    "properties": {
                        "root": {"type": "string"},
                        "directories": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["path", "components"],
                        "properties": {
                            "path": {"type": "string"},
                            "description": {"type": "string"},
                            "is_entrypoint": {"type": "boolean"},
                            "imports": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "components": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "type", "description"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {"type": "string"},
                                        "description": {"type": "string"},
                                        "requirements": {"type": ["string", "null"]},
                                        "dependencies": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "tests_required": {"type": "boolean"},
                                        "priority": {"type": "integer"},
                                        "verification_criteria": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    @classmethod
    def validate(cls, data: Dict, schema_type: str) -> Tuple[bool, str]:
        """Validate data against a schema

        Args:
            data: The data to validate
            schema_type: The type of schema to use (e.g., "plan", "structure")

        Returns:
            Tuple of (is_valid, error_message)
        """
        schema = cls.SCHEMAS.get(schema_type)
        if not schema:
            return False, f"Unknown schema type: {schema_type}"

        try:
            jsonschema.validate(instance=data, schema=schema)
            return True, ""
        except jsonschema.exceptions.ValidationError as e:
            # Create a more readable error message
            path = " -> ".join([str(p) for p in e.path])
            message = f"At {path}: {e.message}" if path else e.message
            return False, message

    @classmethod
    def get_missing_required_fields(cls, data: Dict, schema_type: str) -> List[str]:
        """Get list of missing required fields

        Useful for providing specific guidance on what needs to be fixed
        """
        missing = []
        schema = cls.SCHEMAS.get(schema_type)
        if not schema:
            return [f"Unknown schema type: {schema_type}"]

        # Check top-level required fields
        for field in schema.get("required", []):
            if field not in data:
                missing.append(field)

        # For each required array, check its items if present
        for field, field_schema in schema.get("properties", {}).items():
            if field in data and field_schema.get("type") == "array":
                items = data[field]
                if not isinstance(items, list):
                    continue

                item_schema = field_schema.get("items", {})
                item_required = item_schema.get("required", [])

                for i, item in enumerate(items):
                    for req_field in item_required:
                        if req_field not in item:
                            missing.append(f"{field}[{i}].{req_field}")

        return missing

def main():
    """Main entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("[yellow]Generation interrupted by user.[/yellow]" if rich_available
                      else "Generation interrupted by user.")
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {str(e)}" if rich_available
                      else f"Fatal error: {str(e)}")
        if logging.getLogger("appgen").level <= logging.DEBUG:
            console.print(traceback.format_exc())
        sys.exit(1)

def main():
    """Main entry point"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
