#!/usr/bin/env python3
"""
exceptions.py: Custom exception classes for the Flask-AppBuilder model generator.

This module defines a hierarchy of custom exceptions used throughout the model generator,
providing specific error types for different failure scenarios and ensuring consistent
error handling across the application.

Key Features:
    - Hierarchical exception structure
    - Detailed error context
    - Support for nested exceptions
    - Error categorization
    - Formatted error messages
    - Source location tracking
    - Error code support

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

from typing import Optional, Any, Dict, List
from pathlib import Path
import traceback
from datetime import datetime

class GeneratorBaseException(Exception):
    """
    Base exception class for all model generator exceptions.

    Attributes:
        message: Error message
        cause: Original exception that caused this error
        context: Additional error context
        timestamp: When the error occurred
        traceback: Stack trace when error occurred
    """
    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.cause = cause
        self.context = context or {}
        self.code = code
        self.timestamp = datetime.now()
        self.traceback = traceback.extract_stack()[:-1]  # Exclude this frame

    def __str__(self) -> str:
        """Format the error message."""
        parts = [f"[{self.code}] " if self.code else "", self.message]
        if self.cause:
            parts.append(f"\nCaused by: {str(self.cause)}")
        if self.context:
            parts.append("\nContext:")
            for key, value in self.context.items():
                parts.append(f"  {key}: {value}")
        return "".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'code': self.code,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
            'cause': str(self.cause) if self.cause else None,
            'traceback': self.get_traceback()
        }

    def get_traceback(self) -> List[str]:
        """Get formatted traceback."""
        return [f"{filename}:{lineno} in {name}"
                for filename, lineno, name, _ in self.traceback]

class ConfigurationError(GeneratorBaseException):
    """Raised when there are configuration-related errors."""
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if config_key:
            context['config_key'] = config_key
        super().__init__(message, context=context, code='CONFIG_ERROR', **kwargs)

class ValidationError(GeneratorBaseException):
    """Raised when validation fails."""
    def __init__(
        self,
        message: str,
        errors: Optional[List[str]] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if errors:
            context['validation_errors'] = errors
        super().__init__(message, context=context, code='VALIDATION_ERROR', **kwargs)

class DatabaseError(GeneratorBaseException):
    """Base class for database-related errors."""
    def __init__(
        self,
        message: str,
        table_name: Optional[str] = None,
        schema: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if table_name:
            context['table_name'] = table_name
        if schema:
            context['schema'] = schema
        super().__init__(message, context=context, code='DB_ERROR', **kwargs)

class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    def __init__(self, message: str, uri: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if uri:
            # Sanitize URI to remove sensitive information
            sanitized_uri = self._sanitize_uri(uri)
            context['connection_uri'] = sanitized_uri
        super().__init__(message, context=context, code='DB_CONN_ERROR', **kwargs)

    @staticmethod
    def _sanitize_uri(uri: str) -> str:
        """Remove sensitive information from database URI."""
        import re
        # Replace password in URI with '***'
        return re.sub(r'://[^:]+:([^@]+)@', r'://***:***@', uri)

class DatabaseIntrospectionError(DatabaseError):
    """Raised when database introspection fails."""
    pass

class GenerationError(GeneratorBaseException):
    """Raised when code generation fails."""
    def __init__(
        self,
        message: str,
        table_name: Optional[str] = None,
        template: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if table_name:
            context['table_name'] = table_name
        if template:
            context['template'] = template
        super().__init__(message, context=context, code='GEN_ERROR', **kwargs)

class TemplateError(GeneratorBaseException):
    """Raised when template processing fails."""
    def __init__(
        self,
        message: str,
        template_name: Optional[str] = None,
        template_dir: Optional[Path] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if template_name:
            context['template_name'] = template_name
        if template_dir:
            context['template_dir'] = str(template_dir)
        super().__init__(message, context=context, code='TEMPLATE_ERROR', **kwargs)

class OutputError(GeneratorBaseException):
    """Raised when output operations fail."""
    def __init__(
        self,
        message: str,
        output_path: Optional[Path] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if output_path:
            context['output_path'] = str(output_path)
        super().__init__(message, context=context, code='OUTPUT_ERROR', **kwargs)

class CircularDependencyError(GeneratorBaseException):
    """Raised when circular dependencies are detected."""
    def __init__(
        self,
        message: str,
        tables: Optional[List[str]] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if tables:
            context['tables'] = tables
        super().__init__(message, context=context, code='CIRCULAR_DEP_ERROR', **kwargs)

class HandlerError(GeneratorBaseException):
    """Raised when a handler fails."""
    def __init__(
        self,
        message: str,
        handler_name: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if handler_name:
            context['handler_name'] = handler_name
        super().__init__(message, context=context, code='HANDLER_ERROR', **kwargs)

class ResourceError(GeneratorBaseException):
    """Raised when resource management fails."""
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if resource_type:
            context['resource_type'] = resource_type
        if resource_name:
            context['resource_name'] = resource_name
        super().__init__(message, context=context, code='RESOURCE_ERROR', **kwargs)

def format_exception(exc: Exception) -> str:
    """Format an exception for display or logging."""
    if isinstance(exc, GeneratorBaseException):
        return str(exc)
    return f"{exc.__class__.__name__}: {str(exc)}"

def handle_exception(exc: Exception, logger: Any) -> None:
    """
    Handle an exception with appropriate logging.

    Args:
        exc: Exception to handle
        logger: Logger instance to use
    """
    if isinstance(exc, GeneratorBaseException):
        logger.error(str(exc))
        if exc.cause:
            logger.debug(f"Caused by: {exc.cause}", exc_info=exc.cause)
    else:
        logger.error(format_exception(exc))
        logger.debug("Exception details:", exc_info=exc)

"""
Usage example:

try:
    # Some operation that might fail
    raise DatabaseConnectionError(
        "Failed to connect to database",
        uri="postgresql://user:pass@localhost/db",
        cause=original_exception
    )
except GeneratorBaseException as e:
    # Handle the error
    logger.error(str(e))
    # Access additional information
    print(e.to_dict())
"""
