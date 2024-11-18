"""
pg_exceptions.py: PostgreSQL-specific exceptions.

This module defines custom exceptions specific to PostgreSQL database introspection
and model generation. It provides a hierarchy of exception classes that map to
different types of errors that can occur during PostgreSQL introspection and handling.

Key Features:
    - Database connection errors
    - Schema introspection errors
    - Type handling errors
    - Security errors
    - Feature-specific errors

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

from typing import Optional, Any, List, Dict
from model_generator.exceptions import DatabaseIntrospectionError

class PostgreSQLError(DatabaseIntrospectionError):
    """Base class for PostgreSQL-specific errors."""
    
    def __init__(self, 
                 message: str, 
                 code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None) -> None:
        """
        Initialize PostgreSQL error.

        Args:
            message: Error message
            code: PostgreSQL error code (e.g., '42P01' for undefined table)
            details: Additional error details
            cause: Original exception that caused this error
        """
        self.code = code
        self.details = details or {}
        super().__init__(message, cause=cause)

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"[Error Code: {self.code}]")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " ".join(parts)


class PostgreSQLConnectionError(PostgreSQLError):
    """Raised when connection to PostgreSQL database fails."""
    
    def __init__(self, 
                 message: str, 
                 host: str, 
                 port: int, 
                 database: str,
                 user: Optional[str] = None,
                 **kwargs) -> None:
        """
        Initialize connection error.

        Args:
            message: Error message
            host: Database host
            port: Database port
            database: Database name
            user: Optional username
            **kwargs: Additional connection details
        """
        details = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            **kwargs
        }
        super().__init__(message, details=details)


class PostgreSQLSchemaError(PostgreSQLError):
    """Raised when schema introspection fails."""
    
    def __init__(self, 
                 message: str, 
                 schema_name: str,
                 object_name: Optional[str] = None,
                 object_type: Optional[str] = None,
                 **kwargs) -> None:
        """
        Initialize schema error.

        Args:
            message: Error message
            schema_name: Name of the schema being introspected
            object_name: Optional name of the problematic object
            object_type: Optional type of the problematic object
            **kwargs: Additional schema details
        """
        details = {
            'schema': schema_name,
            'object_name': object_name,
            'object_type': object_type,
            **kwargs
        }
        super().__init__(message, details=details)


class PostgreSQLTypeError(PostgreSQLError):
    """Raised when handling PostgreSQL types."""
    
    def __init__(self, 
                 message: str, 
                 type_name: str,
                 column_name: Optional[str] = None,
                 table_name: Optional[str] = None,
                 **kwargs) -> None:
        """
        Initialize type error.

        Args:
            message: Error message
            type_name: Name of the problematic type
            column_name: Optional name of the column using the type
            table_name: Optional name of the table containing the column
            **kwargs: Additional type details
        """
        details = {
            'type': type_name,
            'column': column_name,
            'table': table_name,
            **kwargs
        }
        super().__init__(message, details=details)


class PostgreSQLConstraintError(PostgreSQLError):
    """Raised when handling PostgreSQL constraints."""
    
    def __init__(self, 
                 message: str,
                 constraint_name: str,
                 constraint_type: str,
                 table_name: str,
                 **kwargs) -> None:
        """
        Initialize constraint error.

        Args:
            message: Error message
            constraint_name: Name of the constraint
            constraint_type: Type of the constraint
            table_name: Name of the table with the constraint
            **kwargs: Additional constraint details
        """
        details = {
            'constraint': constraint_name,
            'type': constraint_type,
            'table': table_name,
            **kwargs
        }
        super().__init__(message, details=details)


class PostgreSQLRelationshipError(PostgreSQLError):
    """Raised when handling PostgreSQL relationships."""
    
    def __init__(self, 
                 message: str,
                 source_table: str,
                 target_table: str,
                 relationship_type: str,
                 **kwargs) -> None:
        """
        Initialize relationship error.

        Args:
            message: Error message
            source_table: Source table name
            target_table: Target table name
            relationship_type: Type of relationship
            **kwargs: Additional relationship details
        """
        details = {
            'source_table': source_table,
            'target_table': target_table,
            'relationship_type': relationship_type,
            **kwargs
        }
        super().__init__(message, details=details)


class PostgreSQLSecurityError(PostgreSQLError):
    """Raised when handling PostgreSQL security features."""
    
    def __init__(self, 
                 message: str,
                 feature_type: str,
                 object_name: str,
                 schema_name: Optional[str] = None,
                 **kwargs) -> None:
        """
        Initialize security error.

        Args:
            message: Error message
            feature_type: Type of security feature (e.g., 'RLS', 'GRANT')
            object_name: Name of the secured object
            schema_name: Optional schema name
            **kwargs: Additional security details
        """
        details = {
            'feature_type': feature_type,
            'object': object_name,
            'schema': schema_name,
            **kwargs
        }
        super().__init__(message, details=details)


class PostgreSQLExtensionError(PostgreSQLError):
    """Raised when handling PostgreSQL extensions."""
    
    def __init__(self, 
                 message: str,
                 extension_name: str,
                 required: bool = False,
                 **kwargs) -> None:
        """
        Initialize extension error.

        Args:
            message: Error message
            extension_name: Name of the extension
            required: Whether the extension is required
            **kwargs: Additional extension details
        """
        details = {
            'extension': extension_name,
            'required': required,
            **kwargs
        }
        super().__init__(message, details=details)


class PostgreSQLFeatureError(PostgreSQLError):
    """Raised when handling PostgreSQL-specific features."""
    
    def __init__(self, 
                 message: str,
                 feature_name: str,
                 object_name: Optional[str] = None,
                 **kwargs) -> None:
        """
        Initialize feature error.

        Args:
            message: Error message
            feature_name: Name of the PostgreSQL feature
            object_name: Optional name of related object
            **kwargs: Additional feature details
        """
        details = {
            'feature': feature_name,
            'object': object_name,
            **kwargs
        }
        super().__init__(message, details=details)


class PostgreSQLQueryError(PostgreSQLError):
    """Raised when a PostgreSQL query fails."""
    
    def __init__(self, 
                 message: str,
                 query: str,
                 parameters: Optional[Dict[str, Any]] = None,
                 **kwargs) -> None:
        """
        Initialize query error.

        Args:
            message: Error message
            query: The failed SQL query
            parameters: Query parameters
            **kwargs: Additional query details
        """
        details = {
            'query': query,
            'parameters': parameters,
            **kwargs
        }
        super().__init__(message, details=details)


class PostgreSQLCatalogError(PostgreSQLError):
    """Raised when accessing PostgreSQL system catalogs."""
    
    def __init__(self, 
                 message: str,
                 catalog_name: str,
                 query: Optional[str] = None,
                 **kwargs) -> None:
        """
        Initialize catalog error.

        Args:
            message: Error message
            catalog_name: Name of the system catalog
            query: Optional catalog query
            **kwargs: Additional catalog details
        """
        details = {
            'catalog': catalog_name,
            'query': query,
            **kwargs
        }
        super().__init__(message, details=details)
