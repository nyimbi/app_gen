from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import json
import logging
import time

import openai
from openai.error import OpenAIError, RateLimitError

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """Container for AI response data"""
    content: str
    timestamp: datetime
    success: bool
    error: Optional[str] = None

class RateLimiter:
    """Rate limiter for API calls"""
    def __init__(self, calls: int, period: int):
        self.calls = calls  # Number of calls allowed
        self.period = period  # Time period in seconds
        self.timestamps: List[datetime] = []

    def can_make_request(self) -> bool:
        """Check if a request can be made within rate limits"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.period)
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
        return len(self.timestamps) < self.calls

    def record_request(self) -> None:
        """Record a request timestamp"""
        self.timestamps.append(datetime.now())

class AICodeAssistant:
    """AI-powered code generation and correction assistant with improved functionality"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        cache_dir: Optional[Path] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize the AI Code Assistant.

        Args:
            api_key: OpenAI API key
            model: GPT model to use (default: "gpt-4")
            temperature: Creativity of responses (0.0-1.0)
            cache_dir: Directory to store response cache
            max_retries: Maximum retry attempts for failed API calls
            retry_delay: Delay between retries in seconds

        Raises:
            ValueError: If invalid parameters are provided
            OpenAIError: If API initialization fails
        """
        if not api_key:
            raise ValueError("API key is required")
        if not 0 <= temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")

        self.openai = openai
        self.openai.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "ai_assist"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conversation_history: List[Dict[str, str]] = []

        # Initialize rate limiter (3 requests per minute)
        self.rate_limiter = RateLimiter(calls=3, period=60)

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load_cache()

    def _load_cache(self) -> None:
        """Load response cache from disk"""
        self.cache_file = self.cache_dir / "response_cache.json"
        try:
            if self.cache_file.exists():
                self._cache = json.loads(self.cache_file.read_text())
            else:
                self._cache = {}
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            self._cache = {}

    def _save_cache(self) -> None:
        """Save response cache to disk"""
        try:
            self.cache_file.write_text(json.dumps(self._cache, indent=2))
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    @lru_cache(maxsize=100)
    def _get_cache_key(self, prompt: str, context: str = "") -> str:
        """Generate cache key for a prompt"""
        import hashlib
        content = f"{prompt}:{context}:{self.model}:{self.temperature}"
        return hashlib.md5(content.encode()).hexdigest()

    async def _make_api_call(
        self,
        messages: List[Dict[str, str]],
        cache_key: str
    ) -> AIResponse:
        """Make API call with retry logic and rate limiting"""
        retries = 0
        while retries < self.max_retries:
            try:
                if not self.rate_limiter.can_make_request():
                    logger.warning("Rate limit reached, waiting...")
                    time.sleep(self.retry_delay)
                    continue

                self.rate_limiter.record_request()
                response = await openai.ChatCompletion.acreate(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                )

                content = response.choices[0].message.content.strip()
                result = AIResponse(
                    content=content,
                    timestamp=datetime.now(),
                    success=True
                )

                # Cache successful response
                self._cache[cache_key] = result.__dict__
                self._save_cache()

                return result

            except RateLimitError:
                logger.warning("Rate limit exceeded, waiting...")
                time.sleep(self.retry_delay * (retries + 1))
                retries += 1
            except OpenAIError as e:
                logger.error(f"API call failed: {e}")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    return AIResponse(
                        content="",
                        timestamp=datetime.now(),
                        success=False,
                        error=str(e)
                    )

        return AIResponse(
            content="",
            timestamp=datetime.now(),
            success=False,
            error="Max retries exceeded"
        )

    async def improve_code(self, code: str, context: str = "") -> str:
        """
        Improve code quality with AI suggestions.

        Args:
            code: Source code to improve
            context: Additional context about the code

        Returns:
            Improved code or original if improvement fails
        """
        prompt = self._create_improvement_prompt(code, context)
        cache_key = self._get_cache_key(prompt, context)

        # Check cache first
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached["success"]:
                return cached["content"]

        response = await self._make_api_call([
            {"role": "system", "content": "You are a Python expert code reviewer."},
            {"role": "user", "content": prompt}
        ], cache_key)

        return response.content if response.success else code

    async def generate_docstring(self, code: str) -> str:
        """Generate comprehensive docstring for code"""
        prompt = self._create_docstring_prompt(code)
        cache_key = self._get_cache_key(prompt)

        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached["success"]:
                return cached["content"]

        response = await self._make_api_call([
            {"role": "system", "content": "You are a technical documentation expert."},
            {"role": "user", "content": prompt}
        ], cache_key)

        return response.content if response.success else '"""Documentation generation failed"""'

    def _create_improvement_prompt(self, code: str, context: str) -> str:
        """Create prompt for code improvement"""
        return f"""Given this Python code and context:
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

    def _create_docstring_prompt(self, code: str) -> str:
        """Create prompt for docstring generation"""
        return f"""Generate a detailed Python docstring for this code:
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

    # ... (similar improvements for other methods)

    def __enter__(self) -> 'AICodeAssistant':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._save_cache()
