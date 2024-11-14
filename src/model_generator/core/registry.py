"""
registry.py: Handler registry module.

This module contains the HandlerRegistry class, which is responsible for:
- Providing a central registry of all available handlers
- Allowing the ModelGenerator to retrieve the appropriate handlers
- Coordinating the processing of the database schema through the handlers
"""

from typing import Dict, Type, Optional
from model_generator.handlers.base import BaseHandler
from model_generator.config.base_config import GeneratorConfig
from model_generator.core.context import GenerationContext
from model_generator.handlers.type_handler import TypeHandler
from model_generator.handlers.relationship_handler import RelationshipHandler
from model_generator.handlers.security_handler import SecurityHandler
from model_generator.handlers.index_handler import IndexHandler
from model_generator.handlers.constraint_handler import ConstraintHandler
from model_generator.handlers.association_handler import AssociationHandler

HandlerType = Type[BaseHandler]

HANDLER_REGISTRY = {
    'type': TypeHandler,
    'relationship': RelationshipHandler,
    'security': SecurityHandler,
    'index': IndexHandler,
    'constraint': ConstraintHandler,
    'association': AssociationHandler
}

class HandlerRegistry:
    """
    Responsible for managing the registration and retrieval of model generation handlers.

    Args:
        config (GeneratorConfig): Configuration for the generation process.
    """

    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.handlers: Dict[str, BaseHandler] = self._initialize_handlers()

    def _initialize_handlers(self) -> Dict[str, BaseHandler]:
        """
        Initialize the registered handlers with the provided configuration.

        Returns:
            Dict[str, BaseHandler]: Dictionary of initialized handlers, keyed by handler type.
        """
        handlers = {}
        for handler_type, handler_class in HANDLER_REGISTRY.items():
            handlers[handler_type] = handler_class(self.config)
        return handlers

    def get_handler(self, handler_type: str) -> BaseHandler:
        """
        Retrieve the registered handler of the specified type.

        Args:
            handler_type (str): The type of the handler to retrieve.

        Returns:
            BaseHandler: The requested handler instance.
        """
        if handler_type not in self.handlers:
            raise ValueError(f"Handler of type '{handler_type}' not found.")
        return self.handlers[handler_type]

    def process_table(self, table_info: 'TableInfo') -> GenerationContext:
        """
        Process a table through all registered handlers.

        Args:
            table_info (TableInfo): Information about the table to be processed.

        Returns:
            GenerationContext: The updated generation context after processing the table.
        """
        context = GenerationContext(
            table_info=table_info,
            config=self.config,
            type_map={},
            relationships=[],
            imports=set()
        )

        for handler_type, handler in self.handlers.items():
            handler.process(context)

        return context
