from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Callable, AsyncGenerator
import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor

import openai
from openai.error import OpenAIError, RateLimitError

logger = logging.getLogger(__name__)

class AIModelType(Enum):
    """Supported AI model types"""
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    CODEX = "code-davinci-002"
    OLLAMA_QWEN = "qwen2.5-coder:32b"
    OLLAMA_DEEPSEEK = "deepseek-coder-v2"





@dataclass
class AIResponse:
    """Container for AI response data"""
    content: str
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)
    prompt_type: Optional[PromptType] = None
    token_usage: Optional[Dict[str, int]] = None




@dataclass
class CodeAnalysisResult:
    """Results of comprehensive code analysis including metrics, issues and recommendations"""
    # Complexity metrics
    complexity: int  # Cyclomatic complexity
    cognitive_complexity: int = 0
    nesting_depth: int = 0
    lines_of_code: int = 0

    # Maintainability metrics
    maintainability_index: float
    code_smells: List[str] = field(default_factory=list)
    duplicated_code: List[Tuple[str, str]] = field(default_factory=list)
    dependency_count: int = 0

    # Security analysis
    security_issues: List[str]
    security_score: float = 0.0
    vulnerability_details: Dict[str, Dict[str, str]] = field(default_factory=dict)
    sensitive_data_exposure: List[str] = field(default_factory=list)

    # Type system analysis
    type_issues: List[str]
    type_coverage: float = 0.0
    missing_type_hints: List[str] = field(default_factory=list)
    type_consistency_issues: List[str] = field(default_factory=list)

    # Code quality
    suggested_improvements: List[str]
    style_violations: List[str] = field(default_factory=list)
    documentation_coverage: float = 0.0
    test_coverage: float = 0.0

    # Performance metrics
    time_complexity: str = "O(1)"
    space_complexity: str = "O(1)"
    memory_usage: float = 0.0
    execution_time: float = 0.0

    # Architecture analysis
    architectural_issues: List[str] = field(default_factory=list)
    design_pattern_violations: List[str] = field(default_factory=list)
    solid_principle_violations: List[str] = field(default_factory=list)
    coupling_score: float = 0.0

    # Dependency analysis
    outdated_dependencies: List[str] = field(default_factory=list)
    dependency_vulnerabilities: List[str] = field(default_factory=list)
    license_issues: List[str] = field(default_factory=list)
    compatibility_issues: List[str] = field(default_factory=list)

class RateLimiter:
    """Enhanced rate limiter for API calls with token tracking"""

    def __init__(
        self,
        calls_per_minute: int,
        tokens_per_minute: int,
        burst_limit: int = 0,
        penalty_timeout: int = 60,
        adaptive_limit: bool = False
    ):
        self.calls_per_minute = calls_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.burst_limit = burst_limit
        self.penalty_timeout = penalty_timeout
        self.adaptive_limit = adaptive_limit
        self.call_timestamps: List[datetime] = []
        self.token_usage: Dict[datetime, int] = {}
        self.penalty_until: Optional[datetime] = None
        self.burst_count: int = 0
        self._lock = asyncio.Lock()
        self.rate_stats: Dict[str, float] = {
            'avg_tokens_per_call': 0,
            'peak_usage': 0,
            'violation_count': 0
        }

    async def can_make_request(self, estimated_tokens: int) -> bool:
        """Check if a request can be made within rate limits"""
        async with self._lock:
            now = datetime.now()

            # Check penalty timeout
            if self.penalty_until and now < self.penalty_until:
                return False

            cutoff = now - timedelta(minutes=1)

            # Clean up old timestamps
            self.call_timestamps = [
                ts for ts in self.call_timestamps
                if ts > cutoff
            ]
            self.token_usage = {
                ts: tokens for ts, tokens in self.token_usage.items()
                if ts > cutoff
            }

            # Check burst limit
            if self.burst_limit:
                recent_cutoff = now - timedelta(seconds=1)
                recent_calls = len([
                    ts for ts in self.call_timestamps
                    if ts > recent_cutoff
                ])
                if recent_calls >= self.burst_limit:
                    self._apply_penalty()
                    return False

            # Check both call and token limits
            current_tokens = sum(self.token_usage.values())
            calls_ok = len(self.call_timestamps) < self.calls_per_minute
            tokens_ok = (
                current_tokens + estimated_tokens <=
                self._get_adjusted_token_limit()
            )

            # Update stats
            if current_tokens > self.rate_stats['peak_usage']:
                self.rate_stats['peak_usage'] = current_tokens

            return calls_ok and tokens_ok

    async def record_request(self, tokens_used: int) -> None:
        """Record a request and its token usage"""
        async with self._lock:
            now = datetime.now()
            self.call_timestamps.append(now)
            self.token_usage[now] = tokens_used
            self._update_stats(tokens_used)

    def _apply_penalty(self) -> None:
        """Apply penalty timeout for burst limit violations"""
        self.penalty_until = datetime.now() + timedelta(
            seconds=self.penalty_timeout
        )
        self.rate_stats['violation_count'] += 1

    def _update_stats(self, tokens_used: int) -> None:
        """Update usage statistics"""
        total_calls = len(self.call_timestamps)
        if total_calls > 0:
            self.rate_stats['avg_tokens_per_call'] = (
                self.rate_stats['avg_tokens_per_call'] * (total_calls - 1) +
                tokens_used
            ) / total_calls

    def _get_adjusted_token_limit(self) -> int:
        """Get token limit adjusted for adaptive limiting"""
        if not self.adaptive_limit:
            return self.tokens_per_minute

        # Adjust limit based on recent usage patterns
        usage_factor = self.rate_stats['peak_usage'] / self.tokens_per_minute
        if usage_factor > 0.9:  # High usage
            return int(self.tokens_per_minute * 0.8)  # Reduce limit
        elif usage_factor < 0.5:  # Low usage
            return int(self.tokens_per_minute * 1.2)  # Increase limit
        return self.tokens_per_minute


class AICodeAssistant:
    """Enhanced AI-powered code generation and correction assistant"""

    def __init__(
        self,
        api_key: str,
        model: Union[str, AIModelType] = AIModelType.GPT4,
        temperature: float = 0.7,
        cache_dir: Optional[Path] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
        token_limit: int = 4096,
        parallel_requests: int = 3,
        context_window: int = 8192,
        template_dir: Optional[Path] = None,
        model_adapter: Optional[str] = None

    ):
        """Initialize the AI Code Assistant with enhanced capabilities."""
        if not api_key:
            raise ValueError("API key is required")
        if not 0 <= temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")

        self.openai = openai
        self.openai.api_key = api_key
        self.model = model.value if isinstance(model, AIModelType) else model
        self.temperature = temperature
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "ai_assist"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.token_limit = token_limit
        self.context_window = context_window
        self.template_dir = Path(template_dir) if template_dir else self.cache_dir / "templates"
        self.model_adapter = model_adapter
        self.conversation_history: List[Dict[str, str]] = []
        self._cache: Dict[str, Any] = {}
        self.custom_prompts: Dict[str, str] = {}
        self.prompt_manager = PromptManager()

        # Enhanced rate limiting
        self.rate_limiter = RateLimiter(
            calls_per_minute=parallel_requests,
            tokens_per_minute=token_limit,
            burst_limit=5,
            adaptive_limit=True
        )

        # Parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=parallel_requests)

        # Initialize caching
        self._setup_caching()

        # Load custom prompts
        self._load_custom_prompts()

    def _setup_caching(self) -> None:
        """Setup advanced caching system"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "response_cache.json"
        self.prompt_cache = self.cache_dir / "prompt_cache.json"
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cached responses and prompts"""
        try:
            if self.cache_file.exists():
                self._cache = json.loads(self.cache_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            self._cache = {}

    def _save_cache(self) -> None:
        """Save current cache to disk"""
        try:
            self.cache_file.write_text(json.dumps(self._cache, indent=2))
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _load_custom_prompts(self) -> None:
        """Load custom prompt templates"""
        try:
            if self.prompt_cache.exists():
                self.custom_prompts = json.loads(self.prompt_cache.read_text())
        except Exception as e:
            logger.error(f"Failed to load custom prompts: {e}")
            self.custom_prompts = {}

    def _save_custom_prompts(self) -> None:
        """Save custom prompts to disk"""
        try:
            self.prompt_cache.write_text(json.dumps(self.custom_prompts, indent=2))
        except Exception as e:
            logger.error(f"Failed to save custom prompts: {e}")

    async def analyze_code(self, code: str) -> CodeAnalysisResult:
        """Perform comprehensive code analysis"""
        result = CodeAnalysisResult(
            complexity=0,
            maintainability_index=0.0,
            security_issues=[],
            type_issues=[],
            suggested_improvements=[]
        )

        try:
            # Get AI analysis of code
            analysis_prompt = f"Analyze this Python code for issues:\n{code}"
            response = await self._get_ai_response(analysis_prompt, PromptType.IMPROVEMENT)

            if response:
                # Parse response into analysis result
                result.suggested_improvements = [s.strip() for s in response.split('\n') if s.strip()]

            return result
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return result

    async def generate_code_variants(
        self,
        code: str,
        n: int = 3
    ) -> AsyncGenerator[str, None]:
        """Generate multiple variants of the code"""
        for i in range(n):
            response = await self._get_ai_response(
                f"Generate variant {i+1} of:\n{code}",
                PromptType.IMPROVEMENT
            )
            if response:
                yield response
            await asyncio.sleep(0.1)

    async def improve_code(self, code: str, context: str = "") -> str:
        """Improve code quality with AI suggestions"""
        prompt = f"Improve this code:\nContext: {context}\nCode:\n{code}"
        return await self._get_ai_response(prompt, PromptType.IMPROVEMENT)

    def _create_security_prompt(self, code: str) -> str:
        """Create prompt for security analysis"""
        return f"""Analyze and fix security issues in this code:
```python
{code}
```
Focus on:
- Input validation
- Authentication/authorization
- Data sanitization
- Resource leaks
- Access control
"""

    def _create_type_hints_prompt(self, code: str) -> str:
        """Create prompt for adding type hints"""
        return f"""Add or improve type hints in this code:
```python
{code}
```
Use:
- Modern Python type hints
- Generic types where appropriate
- Optional and Union types
- Type aliases for complexity
"""

    def _create_explanation_prompt(self, code: str) -> str:
        """Create prompt for code explanation"""
        return f"""Explain this code in detail:
```python
{code}
```
Include:
- Purpose and functionality
- Key components
- Flow of execution
- Important design decisions
"""

    async def fix_security_issues(self, code: str) -> str:
        """Identify and fix security vulnerabilities"""
        prompt = self._create_security_prompt(code)
        return await self._get_ai_response(prompt, PromptType.SECURITY)

    async def add_type_hints(self, code: str) -> str:
        """Add or improve type hints in code"""
        prompt = self._create_type_hints_prompt(code)
        return await self._get_ai_response(prompt, PromptType.TYPE_HINTS)

    async def explain_code(self, code: str) -> str:
        """Generate detailed code explanation"""
        prompt = self._create_explanation_prompt(code)
        response = await self._make_api_call(
            [
                {"role": "system", "content": "You are a Python educator."},
                {"role": "user", "content": prompt}
            ],
            self._get_cache_key(prompt)
        )
        return response.content if response.success else "Explanation generation failed"

    async def _get_ai_response(self, code: str, prompt_type: PromptType, context: str = "") -> str:
        """Get AI response using managed prompts"""
        cache_key = self._get_cache_key(f"{prompt_type.value}:{code}:{context}")

        # Check cache
        cached = self._get_cached_response(cache_key, prompt_type)
        if cached:
            return cached

        # Get prompt from manager
        system_message, prompt = self.prompt_manager.get_prompt(prompt_type, code, context)

        # Get response
        response = await self._make_api_call([
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ], cache_key)

        if response.success:
            self._cache_response(cache_key, response, prompt_type)
            return response.content
        return ""

    async def improve_code(self, code: str, context: str = "") -> str:
        """Improve code using managed prompts"""
        return await self._get_ai_response(code, PromptType.IMPROVEMENT, context)

    async def add_security(self, code: str) -> str:
        """Add security improvements using managed prompts"""
        return await self._get_ai_response(code, PromptType.SECURITY)
    async def _make_api_call(
        self,
        messages: List[Dict[str, str]],
        cache_key: str
    ) -> AIResponse:
        """Make API call with retry logic"""
        retries = 0
        estimated_tokens = sum(len(m["content"]) // 4 for m in messages)

        while retries < self.max_retries:
            try:
                if not await self.rate_limiter.can_make_request(estimated_tokens):
                    await asyncio.sleep(self.retry_delay * (retries + 1))
                    continue

                # Select appropriate model adapter
                if self.model_adapter == "ollama":
                    response = await self._call_ollama(messages)
                else:
                    response = await self.openai.ChatCompletion.acreate(
                        model=self.model,
                        messages=messages,
                        temperature=self.temperature,
                    )

                content = response.choices[0].message.content.strip()
                token_usage = response.usage.total_tokens if hasattr(response, 'usage') else estimated_tokens

                await self.rate_limiter.record_request(token_usage)

                return AIResponse(
                    content=content,
                    timestamp=datetime.now(),
                    success=True,
                    token_usage={"total": token_usage}
                )

            except Exception as e:
                logger.error(f"API call failed: {e}")
                retries += 1
                if retries < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (retries + 1))

        return AIResponse(
            content="",
            timestamp=datetime.now(),
            success=False,
            error=f"Failed after {self.max_retries} retries"
        )

    def _get_cached_response(
        self,
        cache_key: str,
        prompt_type: PromptType
    ) -> Optional[str]:
        """Get cached response if available"""
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached.get("prompt_type") == prompt_type.value:
                return cached.get("content")
        return None

    def _cache_response(
        self,
        cache_key: str,
        response: AIResponse,
        prompt_type: PromptType
    ) -> None:
        """Cache API response"""
        self._cache[cache_key] = {
            "content": response.content,
            "timestamp": datetime.now().isoformat(),
            "prompt_type": prompt_type.value,
            "token_usage": response.token_usage
        }
        self._save_cache()

    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key for prompt"""
        import hashlib
        content = f"{prompt}:{self.model}:{self.temperature}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_system_prompt(self, prompt_type: PromptType) -> str:
        """Get system prompt based on prompt type"""
        prompts = {
            PromptType.IMPROVEMENT: "You are a Python expert code reviewer.",
            PromptType.DOCSTRING: "You are a technical documentation expert.",
            PromptType.TEST: "You are a Python testing expert.",
            PromptType.DEBUG: "You are a Python debugging expert.",
            PromptType.OPTIMIZATION: "You are a Python performance optimization expert.",
            PromptType.SECURITY: "You are a Python security expert.",
            PromptType.TYPE_HINTS: "You are a Python type system expert.",
        }
        return prompts.get(prompt_type, "You are a Python expert.")

    def add_custom_prompt(self, name: str, prompt_template: str) -> None:
        """Add a custom prompt template"""
        self.custom_prompts[name] = prompt_template
        self._save_custom_prompts()

    async def batch_process(
        self,
        codes: List[str],
        operation: Callable[[str], Awaitable[str]]
    ) -> List[str]:
        """Process multiple code snippets in parallel"""
        tasks = [operation(code) for code in codes]
        return await asyncio.gather(*tasks)

    async def _call_ollama(self, messages: List[Dict[str, str]]) -> Any:
        """Call Ollama API endpoint"""
        # Implement Ollama API call
        pass

    def __enter__(self) -> 'AICodeAssistant':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._save_cache()
        self.thread_pool.shutdown()

    async def __aenter__(self) -> 'AICodeAssistant':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._save_cache()
        self.thread_pool.shutdown()
