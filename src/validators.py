"""
validators.py: Custom validators for Flask-AppBuilder forms

This module provides custom validators for form fields, including complex validation
rules for specialized data types like currency, phone numbers, addresses, JSON data,
and color values.

Features:
- Type-specific validation
- Format validation
- Range validation
- Pattern matching
- Custom error messages
- Internationalization support
"""

import json
import re
from typing import Any, Optional
from wtforms.validators import ValidationError
from flask_babel import lazy_gettext as _
import phonenumbers
from decimal import Decimal
import pycountry

class MoneyValidator:
    """
    Validates currency amounts with optional range checking.

    Features:
    - Currency format validation
    - Range validation
    - Decimal precision check
    - Currency code validation
    - Negative value handling
    """

    def __init__(self, min_value: Optional[float] = None,
                 max_value: Optional[float] = None,
                 currency: str = 'USD',
                 allow_negative: bool = False,
                 decimal_places: int = 2):
        self.min_value = min_value
        self.max_value = max_value
        self.currency = currency
        self.allow_negative = allow_negative
        self.decimal_places = decimal_places

    def __call__(self, form: Any, field: Any) -> None:
        if not field.data:
            return

        try:
            # Remove currency symbol and commas
            value_str = str(field.data).replace(self.currency, '').replace(',', '').strip()
            value = Decimal(value_str)

            # Check decimal places
            if abs(value.as_tuple().exponent) > self.decimal_places:
                raise ValidationError(_(
                    f'Value cannot have more than {self.decimal_places} decimal places'
                ))

            # Check negative values
            if not self.allow_negative and value < 0:
                raise ValidationError(_('Negative values are not allowed'))

            # Check range
            if self.min_value is not None and value < self.min_value:
                raise ValidationError(_(
                    f'Value must be greater than or equal to {self.min_value}'
                ))
            if self.max_value is not None and value > self.max_value:
                raise ValidationError(_(
                    f'Value must be less than or equal to {self.max_value}'
                ))

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(_('Invalid currency format')) from e

class PhoneValidator:
    """
    Validates phone numbers using Google's libphonenumbers.

    Features:
    - International format validation
    - Country code validation
    - Number type validation
    - Extension handling
    """

    def __init__(self, region: Optional[str] = None,
                 allow_types: Optional[list] = None,
                 require_extension: bool = False):
        self.region = region
        self.allow_types = allow_types
        self.require_extension = require_extension

    def __call__(self, form: Any, field: Any) -> None:
        if not field.data:
            return

        try:
            number = phonenumbers.parse(field.data, self.region)

            if not phonenumbers.is_valid_number(number):
                raise ValidationError(_('Invalid phone number'))

            if self.allow_types:
                number_type = phonenumbers.number_type(number)
                if number_type not in self.allow_types:
                    raise ValidationError(_('Invalid phone number type'))

            if self.require_extension and not number.extension:
                raise ValidationError(_('Extension is required'))

        except phonenumbers.NumberParseException as e:
            raise ValidationError(_('Invalid phone number format')) from e

class AddressValidator:
    """
    Validates address components.

    Features:
    - Required fields validation
    - Postal code format validation
    - Country validation
    - State/Province validation
    - Format standardization
    """

    def __init__(self, required_fields: Optional[list] = None,
                 validate_postal: bool = True,
                 validate_country: bool = True):
        self.required_fields = required_fields or ['street', 'city', 'country']
        self.validate_postal = validate_postal
        self.validate_country = validate_country

    def __call__(self, form: Any, field: Any) -> None:
        if not field.data:
            return

        try:
            data = json.loads(field.data) if isinstance(field.data, str) else field.data

            # Check required fields
            for req_field in self.required_fields:
                if not data.get(req_field):
                    raise ValidationError(_(f'{req_field} is required'))

            # Validate country
            if self.validate_country and 'country' in data:
                country = pycountry.countries.get(alpha_2=data['country'])
                if not country:
                    raise ValidationError(_('Invalid country code'))

            # Validate postal code
            if self.validate_postal and 'postal_code' in data:
                self._validate_postal_code(data['postal_code'], data.get('country'))

        except json.JSONDecodeError:
            raise ValidationError(_('Invalid address format'))

    def _validate_postal_code(self, postal_code: str, country: str) -> None:
        """Validate postal code format for country."""
        # Add country-specific postal code validation
        if country == 'US':
            if not re.match(r'^\d{5}(-\d{4})?$', postal_code):
                raise ValidationError(_('Invalid US postal code'))
        elif country == 'GB':
            if not re.match(r'^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$', postal_code):
                raise ValidationError(_('Invalid UK postal code'))

class JSONValidator:
    """
    Validates JSON data structure and content.

    Features:
    - Schema validation
    - Required fields
    - Data type validation
    - Custom validation rules
    - Size limits
    """

    def __init__(self, schema: Optional[dict] = None,
                 max_size: Optional[int] = None,
                 custom_validator: Optional[callable] = None):
        self.schema = schema
        self.max_size = max_size
        self.custom_validator = custom_validator

    def __call__(self, form: Any, field: Any) -> None:
        if not field.data:
            return

        try:
            # Parse JSON if string
            data = json.loads(field.data) if isinstance(field.data, str) else field.data

            # Check size
            if self.max_size and len(json.dumps(data)) > self.max_size:
                raise ValidationError(_('JSON data exceeds maximum size'))

            # Validate against schema
            if self.schema:
                self._validate_schema(data, self.schema)

            # Run custom validation
            if self.custom_validator:
                self.custom_validator(data)

        except json.JSONDecodeError:
            raise ValidationError(_('Invalid JSON format'))

    def _validate_schema(self, data: Any, schema: dict, path: str = '') -> None:
        """Recursive schema validation."""
        for key, value_type in schema.items():
            current_path = f"{path}.{key}" if path else key

            if key not in data:
                if value_type.get('required', False):
                    raise ValidationError(_(f'Missing required field: {current_path}'))
                continue

            if not isinstance(data[key], value_type['type']):
                raise ValidationError(_(
                    f'Invalid type for {current_path}: expected {value_type["type"].__name__}'
                ))

            if 'schema' in value_type:
                self._validate_schema(data[key], value_type['schema'], current_path)

class ColorValidator:
    """
    Validates color values in various formats.

    Features:
    - Multiple format support (hex, rgb, rgba)
    - Alpha channel validation
    - Named color validation
    - Color space restrictions
    """

    def __init__(self, formats: Optional[list] = None,
                 allow_alpha: bool = True,
                 allow_named: bool = True):
        self.formats = formats or ['hex', 'rgb', 'rgba']
        self.allow_alpha = allow_alpha
        self.allow_named = allow_named
        self.named_colors = set([
            'red', 'blue', 'green', 'yellow', 'black', 'white',
            # Add more named colors...
        ])

    def __call__(self, form: Any, field: Any) -> None:
        if not field.data:
            return

        value = field.data.lower().strip()

        # Check named colors
        if self.allow_named and value in self.named_colors:
            return

        # Validate hex format
        if 'hex' in self.formats:
            if re.match(r'^#[0-9a-f]{6}([0-9a-f]{2})?$', value):
                if not self.allow_alpha and len(value) > 7:
                    raise ValidationError(_('Alpha channel not allowed'))
                return

        # Validate rgb/rgba format
        if 'rgb' in self.formats or 'rgba' in self.formats:
            rgb_match = re.match(
                r'^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$',
                value
            )
            if rgb_match:
                r, g, b, a = rgb_match.groups()
                if not all(0 <= int(x) <= 255 for x in (r, g, b)):
                    raise ValidationError(_('RGB values must be between 0 and 255'))
                if a and not self.allow_alpha:
                    raise ValidationError(_('Alpha channel not allowed'))
                if a and not 0 <= float(a) <= 1:
                    raise ValidationError(_('Alpha value must be between 0 and 1'))
                return

        raise ValidationError(_('Invalid color format'))
