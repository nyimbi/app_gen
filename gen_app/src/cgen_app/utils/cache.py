import os
import hashlib
from typing import Optional
import logging
from core.config import Config

logger = logging.getLogger("appgen")


class GenerationCache:
    _cache_dir: str = None

    @classmethod
    def initialize(cls) -> None:
        cls._cache_dir = Config.options.cache_dir
        if Config.options.cache_generations:
            os.makedirs(cls._cache_dir, exist_ok=True)
            logger.info(f"Initialized generation cache at {cls._cache_dir}")

    @classmethod
    def _get_cache_key(cls, prompt: str, context: str) -> str:
        combined = (prompt + context).encode("utf-8")
        return hashlib.md5(combined).hexdigest()

    @classmethod
    def get(cls, prompt: str, context: str) -> Optional[str]:
        if not Config.options.cache_generations:
            return None
        key = cls._get_cache_key(prompt, context)
        cache_file = os.path.join(cls._cache_dir, f"{key}.txt")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read cache: {str(e)}")
        return None

    @classmethod
    def store(cls, prompt: str, context: str, result: str) -> None:
        if not Config.options.cache_generations:
            return
        key = cls._get_cache_key(prompt, context)
        cache_file = os.path.join(cls._cache_dir, f"{key}.txt")
        try:
            with open(cache_file, "w") as f:
                f.write(result)
        except Exception as e:
            logger.warning(f"Failed to write to cache: {str(e)}")
