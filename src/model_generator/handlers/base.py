from abc import ABC, abstractmethod
from typing import Set, Dict, Any
from model_generator.core.context import GenerationContext
from model_generator.config.base_config import GeneratorConfig

class BaseHandler(ABC):
    """
    Abstract base class for all model generation handlers.

    Handlers are responsible for processing specific aspects of the database schema
    and contributing to the overall model generation process.
    """

    def __init__(self, config: GeneratorConfig):
        self.config = config

    @abstractmethod
    def validate_config(self) -> List[str]:
        """
        Validate the configuration settings for the handler.

        Returns:
            List[str]: List of validation error messages.
        """
        pass

    @abstractmethod
    def process(self, context: GenerationContext) -> None:
        """
        Process the provided generation context and update it accordingly.

        Args:
            context (GenerationContext): The current generation context.
        """
        pass

    @abstractmethod
    def get_imports(self) -> Set[str]:
        """
        Retrieve the set of import statements required by the handler.

        Returns:
            Set[str]: Set of import statements.
        """
        pass
