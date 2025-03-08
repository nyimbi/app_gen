import asyncio
import ollama
from typing import Optional
import logging
from core.config import Config
from utils.cache import GenerationCache
from core.exceptions import GenerationError

logger = logging.getLogger("appgen")


class LLMClient:
    @staticmethod
    async def generate_async(
        prompt: str,
        context: str,
        max_retries: int = None,
        temperature: float = None,
        expected_type: str = "code",
    ) -> str:
        max_retries = max_retries or Config.options.max_retries
        temperature = temperature or Config.options.temperature
        cached = GenerationCache.get(prompt, context)
        if cached:
            logger.debug("Using cached generation result")
            return cached
        full_prompt = f"{context}\n\n{prompt}\nRespond with ONLY valid {'Python code' if expected_type == 'code' else 'JSON' if expected_type == 'json' else 'text'}, no markdown."
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    ollama.generate,
                    model=Config.options.model,
                    prompt=full_prompt,
                    options={"temperature": temperature},
                )
                result = response["response"].strip()
                from utils.parser import OutputParser

                processed = (
                    OutputParser.extract_code(result)
                    if expected_type == "code"
                    else OutputParser.extract_json(result)
                    if expected_type == "json"
                    else result
                )
                GenerationCache.store(prompt, context, processed)
                return processed
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(Config.options.retry_delay * (2**attempt))
                else:
                    raise GenerationError(
                        f"Failed to generate after {max_retries} attempts"
                    )

    @staticmethod
    def generate(
        prompt: str,
        context: str,
        max_retries: int = None,
        temperature: float = None,
        expected_type: str = "code",
    ) -> str:
        return asyncio.run(
            LLMClient.generate_async(
                prompt, context, max_retries, temperature, expected_type
            )
        )
