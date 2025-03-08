import json
from dataclasses import dataclass, asdict
from enum import Enum, auto
import logging
from typing import Optional

logger = logging.getLogger("appgen")


class GenerationStrategy(Enum):
    COMPONENT_WISE = auto()
    FILE_WISE = auto()
    MODULE_WISE = auto()


@dataclass
class ConfigOptions:
    model: str = "qwen2.5:72b"
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
    options = ConfigOptions()

    @classmethod
    def from_file(cls, config_file: str) -> None:
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)
            if "generation_strategy" in config_data:
                config_data["generation_strategy"] = GenerationStrategy[
                    config_data["generation_strategy"]
                ]
            for key, value in config_data.items():
                if hasattr(cls.options, key):
                    setattr(cls.options, key, value)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")

    @classmethod
    def save_to_file(cls, config_file: str) -> None:
        try:
            config_dict = asdict(cls.options)
            if isinstance(config_dict.get("generation_strategy"), Enum):
                config_dict["generation_strategy"] = config_dict[
                    "generation_strategy"
                ].name
            with open(config_file, "w") as f:
                json.dump(config_dict, f, indent=2)
            logger.info(f"Saved configuration to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
