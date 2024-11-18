"""
pg_type_values.py: PostgreSQL value handling and formatting.

This module provides functionality for handling PostgreSQL literal values,
parsing text representations, and formatting values for SQL output. It works
in conjunction with pg_types.py to provide complete type handling capabilities.

Key Features:
    - Parse PostgreSQL literal values
    - Format Python values for PostgreSQL
    - Handle complex type literals
    - Convert between PostgreSQL and Python values
    - Support for all PostgreSQL data types
    - Array and composite value handling

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

import re
import json
import uuid
import datetime
import ipaddress
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
from model_generator.postgresql.pg_exceptions import PostgreSQLTypeError

class PostgreSQLLiteral:
    """Base class for PostgreSQL literal value handling."""
    
    def __init__(self, value: Any):
        self.value = value
    
    def to_sql(self) -> str:
        """Convert value to SQL-safe literal string."""
        if self.value is None:
            return 'NULL'
        return str(self.value)
    
    def to_python(self) -> Any:
        """Convert PostgreSQL value to Python value."""
        return self.value
    
    @staticmethod
    def escape_string(value: str) -> str:
        """Escape a string for PostgreSQL."""
        return "'" + value.replace("'", "''") + "'"


class NumericLiteral(PostgreSQLLiteral):
    """Handle numeric literals (integer, decimal, float)."""
    
    def to_sql(self) -> str:
        if isinstance(self.value, (int, float, Decimal)):
            return str(self.value)
        raise PostgreSQLTypeError(
            "Invalid numeric value",
            type_name="numeric",
            details={'value': self.value}
        )
    
    def to_python(self) -> Union[int, float, Decimal]:
        if isinstance(self.value, str):
            try:
                if '.' in self.value:
                    return Decimal(self.value)
                return int(self.value)
            except ValueError as e:
                raise PostgreSQLTypeError(
                    "Invalid numeric string",
                    type_name="numeric",
                    details={'value': self.value},
                    cause=e
                )
        return self.value


class StringLiteral(PostgreSQLLiteral):
    """Handle string literals."""
    
    def to_sql(self) -> str:
        return self.escape_string(str(self.value))
    
    def to_python(self) -> str:
        return str(self.value)


class DateTimeLiteral(PostgreSQLLiteral):
    """Handle date/time literals."""
    
    def to_sql(self) -> str:
        if isinstance(self.value, datetime.datetime):
            return f"TIMESTAMP '{self.value.isoformat()}'"
        if isinstance(self.value, datetime.date):
            return f"DATE '{self.value.isoformat()}'"
        if isinstance(self.value, datetime.time):
            return f"TIME '{self.value.isoformat()}'"
        if isinstance(self.value, datetime.timedelta):
            return f"INTERVAL '{self.value}'"
        raise PostgreSQLTypeError(
            "Invalid date/time value",
            type_name="timestamp",
            details={'value': self.value}
        )
    
    @staticmethod
    def parse_datetime(value: str) -> datetime.datetime:
        """Parse PostgreSQL timestamp string."""
        try:
            return datetime.datetime.fromisoformat(value)
        except ValueError as e:
            raise PostgreSQLTypeError(
                "Invalid timestamp format",
                type_name="timestamp",
                details={'value': value},
                cause=e
            )
    
    @staticmethod
    def parse_date(value: str) -> datetime.date:
        """Parse PostgreSQL date string."""
        try:
            return datetime.date.fromisoformat(value)
        except ValueError as e:
            raise PostgreSQLTypeError(
                "Invalid date format",
                type_name="date",
                details={'value': value},
                cause=e
            )
    
    @staticmethod
    def parse_time(value: str) -> datetime.time:
        """Parse PostgreSQL time string."""
        try:
            return datetime.time.fromisoformat(value)
        except ValueError as e:
            raise PostgreSQLTypeError(
                "Invalid time format",
                type_name="time",
                details={'value': value},
                cause=e
            )
    
    @staticmethod
    def parse_interval(value: str) -> datetime.timedelta:
        """Parse PostgreSQL interval string."""
        # Simple interval parsing - could be more comprehensive
        units = {
            'years': 365 * 24 * 60 * 60,  # Simplified
            'months': 30 * 24 * 60 * 60,   # Simplified
            'days': 24 * 60 * 60,
            'hours': 60 * 60,
            'minutes': 60,
            'seconds': 1
        }
        
        total_seconds = 0
        for part in value.split():
            try:
                amount = float(part[:-1])
                unit = part[-1].lower()
                if unit == 'y':
                    total_seconds += amount * units['years']
                elif unit == 'm':
                    total_seconds += amount * units['months']
                elif unit == 'd':
                    total_seconds += amount * units['days']
                elif unit == 'h':
                    total_seconds += amount * units['hours']
                elif unit == 'm':
                    total_seconds += amount * units['minutes']
                elif unit == 's':
                    total_seconds += amount
            except ValueError:
                continue
        
        return datetime.timedelta(seconds=total_seconds)


class BooleanLiteral(PostgreSQLLiteral):
    """Handle boolean literals."""
    
    _true_values = {'t', 'true', 'y', 'yes', 'on', '1'}
    _false_values = {'f', 'false', 'n', 'no', 'off', '0'}
    
    def to_sql(self) -> str:
        return 'true' if bool(self.value) else 'false'
    
    def to_python(self) -> bool:
        if isinstance(self.value, str):
            value = self.value.lower()
            if value in self._true_values:
                return True
            if value in self._false_values:
                return False
            raise PostgreSQLTypeError(
                "Invalid boolean value",
                type_name="boolean",
                details={'value': self.value}
            )
        return bool(self.value)


class ArrayLiteral(PostgreSQLLiteral):
    """Handle array literals."""
    
    def __init__(self, value: List[Any], item_literal_class: type = PostgreSQLLiteral):
        super().__init__(value)
        self.item_literal_class = item_literal_class
    
    def to_sql(self) -> str:
        if not isinstance(self.value, (list, tuple)):
            raise PostgreSQLTypeError(
                "Invalid array value",
                type_name="array",
                details={'value': self.value}
            )
        
        items = [
            self.item_literal_class(item).to_sql()
            for item in self.value
        ]
        return f"ARRAY[{', '.join(items)}]"
    
    def to_python(self) -> List[Any]:
        if isinstance(self.value, str):
            # Parse PostgreSQL array literal string
            # Remove ARRAY[] wrapper if present
            value = re.sub(r'^ARRAY\[(.+)\]$', r'\1', self.value)
            # Split on commas, handling nested arrays
            return [
                self.item_literal_class(item.strip()).to_python()
                for item in self._split_array(value)
            ]
        return list(self.value)
    
    @staticmethod
    def _split_array(array_str: str) -> List[str]:
        """Split array string handling nested arrays and quoted strings."""
        items = []
        current = []
        in_quotes = False
        bracket_level = 0
        
        for char in array_str:
            if char == '"' and current[-1:] != ['\\']:
                in_quotes = not in_quotes
                current.append(char)
            elif char == '{' and not in_quotes:
                bracket_level += 1
                current.append(char)
            elif char == '}' and not in_quotes:
                bracket_level -= 1
                current.append(char)
            elif char == ',' and not in_quotes and bracket_level == 0:
                items.append(''.join(current))
                current = []
            else:
                current.append(char)
        
        if current:
            items.append(''.join(current))
        
        return items


class JSONLiteral(PostgreSQLLiteral):
    """Handle JSON/JSONB literals."""
    
    def to_sql(self) -> str:
        try:
            json_str = json.dumps(self.value)
            return f"'{json_str}'"
        except (TypeError, ValueError) as e:
            raise PostgreSQLTypeError(
                "Invalid JSON value",
                type_name="json",
                details={'value': self.value},
                cause=e
            )
    
    def to_python(self) -> Union[Dict, List]:
        if isinstance(self.value, str):
            try:
                return json.loads(self.value)
            except json.JSONDecodeError as e:
                raise PostgreSQLTypeError(
                    "Invalid JSON string",
                    type_name="json",
                    details={'value': self.value},
                    cause=e
                )
        return self.value


class UUIDLiteral(PostgreSQLLiteral):
    """Handle UUID literals."""
    
    def to_sql(self) -> str:
        try:
            uuid_val = uuid.UUID(str(self.value))
            return f"'{str(uuid_val)}'"
        except ValueError as e:
            raise PostgreSQLTypeError(
                "Invalid UUID value",
                type_name="uuid",
                details={'value': self.value},
                cause=e
            )
    
    def to_python(self) -> uuid.UUID:
        try:
            return uuid.UUID(str(self.value))
        except ValueError as e:
            raise PostgreSQLTypeError(
                "Invalid UUID string",
                type_name="uuid",
                details={'value': self.value},
                cause=e
            )


class NetworkLiteral(PostgreSQLLiteral):
    """Handle network address literals (inet, cidr)."""
    
    def to_sql(self) -> str:
        try:
            # Handle both IPv4 and IPv6
            addr = ipaddress.ip_interface(str(self.value))
            return f"'{str(addr)}'"
        except ValueError as e:
            raise PostgreSQLTypeError(
                "Invalid network address",
                type_name="inet",
                details={'value': self.value},
                cause=e
            )
    
    def to_python(self) -> Union[ipaddress.IPv4Interface, ipaddress.IPv6Interface]:
        try:
            return ipaddress.ip_interface(str(self.value))
        except ValueError as e:
            raise PostgreSQLTypeError(
                "Invalid network address string",
                type_name="inet",
                details={'value': self.value},
                cause=e
            )


# Type to Literal class mapping
LITERAL_HANDLERS = {
    'integer': NumericLiteral,
    'bigint': NumericLiteral,
    'smallint': NumericLiteral,
    'decimal': NumericLiteral,
    'numeric': NumericLiteral,
    'real': NumericLiteral,
    'double precision': NumericLiteral,
    'character varying': StringLiteral,
    'varchar': StringLiteral,
    'text': StringLiteral,
    'char': StringLiteral,
    'timestamp': DateTimeLiteral,
    'timestamp with time zone': DateTimeLiteral,
    'date': DateTimeLiteral,
    'time': DateTimeLiteral,
    'interval': DateTimeLiteral,
    'boolean': BooleanLiteral,
    'json': JSONLiteral,
    'jsonb': JSONLiteral,
    'uuid': UUIDLiteral,
    'inet': NetworkLiteral,
    'cidr': NetworkLiteral,
}

def get_literal_handler(pg_type: str) -> type:
    """Get appropriate literal handler for PostgreSQL type."""
    # Handle array types
    if pg_type.endswith('[]'):
        base_type = pg_type[:-2]
        base_handler = get_literal_handler(base_type)
        return lambda value: ArrayLiteral(value, base_handler)
    
    # Handle types with parameters
    base_type = re.sub(r'\(.*\)', '', pg_type).lower()
    return LITERAL_HANDLERS.get(base_type, PostgreSQLLiteral)

def format_value(value: Any, pg_type: str) -> str:
    """Format a Python value for PostgreSQL."""
    handler = get_literal_handler(pg_type)
    return handler(value).to_sql()

def parse_value(value: str, pg_type: str) -> Any:
    """Parse a PostgreSQL value into Python."""
    handler = get_literal_handler(pg_type)
    return handler(value).to_python()
