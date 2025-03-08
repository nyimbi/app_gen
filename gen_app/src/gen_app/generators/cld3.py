"""
Advanced AI-Powered Application Generator using Ollama with Component-Based Generation

This program creates Python applications by generating code components iteratively
to circumvent LLM token limits and ensure plan conformance with a hierarchical component architecture,
verification mechanisms, and dependency resolution.
"""

import os
import re
import json
import logging
import hashlib
import asyncio
import traceback
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
    cache_generations: bool = True
    cache_dir: str = ".generation_cache"
    prompt_templates_file: str = "prompt_templates.json"


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
            return False, f"Syntax error: {str(e)}"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"
    
    @staticmethod
    def verify_imports(code: str) -> Tuple[bool, str]:
        """Verify imports by analyzing AST"""
        import ast
        
        try:
            tree = ast.parse(code)
            imports = []
            
            # Find all import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module)
                    
            # Here we could verify against a known set of available packages
            # For now, just return the list for logging
            return True, ", ".join(imports) if imports else "No imports found"
        except Exception as e:
            return False, f"Import verification error: {str(e)}"


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
        """Generate a single component asynchronously"""
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
            
            # Verify syntax if enabled
            if Config.options.verify_syntax:
                valid, message = CodeVerifier.verify_syntax(code)
                if not valid:
                    logger.warning(f"Syntax verification failed for {component.name}: {message}")
                    # Enhanced error logging with code snippet
                    error_lines = code.split('\n')
                    if len(error_lines) > 5:
                        error_context = '\n'.join(error_lines[:5]) + "\n..."
                    else:
                        error_context = code
                    logger.debug(f"Code with syntax error:\n{error_context}")
                
            return code
    
    async def generate_test_async(self, component: Component, file_path: str, code: str) -> str:
        """Generate tests for a component asynchronously"""
        with console.status(f"Generating tests for '{component.name}'..."):
            prompt = PromptTemplate.get(
                "test",
                component_type=component.type,
                component_name=component.name,
                file_path=file_path,
                component_code=code
            )
            
            return await LLMClient.generate_async(prompt, file_path, expected_type="code")
    
    async def plan_development_async(self, description: str) -> Dict:
        """Generate detailed development plan with component breakdown"""
        with console.status("Planning development..."):
            prompt = PromptTemplate.get("plan")
            plan_json = await LLMClient.generate_async(prompt, description, expected_type="json")
            
            try:
                # Use the enhanced JSON parser to handle potential issues
                return OutputParser.clean_and_verify_json(plan_json)
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
                # Use the enhanced JSON parser to handle potential issues
                structure_dict = OutputParser.clean_and_verify_json(structure_json)
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


def main():
    """Main entry point"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
