"""
formatters.py: Custom formatters for Flask-AppBuilder fields

This module provides formatters for displaying field values in various formats,
with support for different data types, localization, and custom rendering options.

Features:
- Currency formatting
- Phone number formatting
- Address formatting
- JSON prettification
- Color value rendering
- Custom formatting rules
"""

from typing import Any, Optional
from flask import Markup
import json
import phonenumbers
from babel.numbers import format_currency
import pycountry
import html

def currency_formatter(value: Any,
                      currency: str = 'USD',
                      locale: str = 'en_US',
                      format: str = '#,##0.00',
                      symbol: bool = True) -> str:
    """
    Format currency values.

    Args:
        value: Amount to format
        currency: Currency code
        locale: Locale for formatting
        format: Number format pattern
        symbol: Include currency symbol

    Returns:
        str: Formatted currency string
    """
    if value is None:
        return ''

    try:
        return format_currency(
            value,
            currency,
            format=format,
            locale=locale,
            currency_digits=True,
            symbol=symbol
        )
    except Exception:
        return str(value)

def phone_formatter(value: Any,
                   region: Optional[str] = None,
                   format: str = 'INTERNATIONAL',
                   html_links: bool = True) -> str:
    """
    Format phone numbers.

    Args:
        value: Phone number to format
        region: Default region code
        format: Output format (INTERNATIONAL, NATIONAL, E164)
        html_links: Generate clickable links

    Returns:
        str: Formatted phone number
    """
    if not value:
        return ''

    try:
        number = phonenumbers.parse(str(value), region)
        if not phonenumbers.is_valid_number(number):
            return str(value)

        format_map = {
            'INTERNATIONAL': phonenumbers.PhoneNumberFormat.INTERNATIONAL,
            'NATIONAL': phonenumbers.PhoneNumberFormat.NATIONAL,
            'E164': phonenumbers.PhoneNumberFormat.E164
        }

        formatted = phonenumbers.format_number(
            number,
            format_map.get(format, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        )

        if html_links:
            return Markup(f'<a href="tel:{formatted}">{formatted}</a>')
        return formatted

    except Exception:
        return str(value)

def address_formatter(value: Any,
                     format: Optional[str] = None,
                     html: bool = True) -> str:
    """
    Format address components.

    Args:
        value: Address data to format
        format: Custom format string
        html: Generate HTML output

    Returns:
        str: Formatted address
    """
    if not value:
        return ''

    try:
        data = json.loads(value) if isinstance(value, str) else value

        # Get country name
        country_code = data.get('country', '')
        country = pycountry.countries.get(alpha_2=country_code)
        country_name = country.name if country else country_code

        # Build address parts
        parts = []
        if data.get('street'):
            parts.append(data['street'])
        if data.get('city'):
            city_parts = [data['city']]
            if data.get('state'):
                city_parts.append(data['state'])
            if data.get('postal_code'):
                city_parts.append(data['postal_code'])
            parts.append(', '.join(city_parts))
        if country_name:
            parts.append(country_name)

        # Format address
        if format:
            formatted = format.format(**data)
        else:
            formatted = '\n'.join(parts)

        if html:
            formatted = formatted.replace('\n', '<br>')
            return Markup(f'<address>{formatted}</address>')
        return formatted

    except Exception:
        return str(value)

def json_formatter(value: Any,
                  indent: int = 2,
                  sort_keys: bool = True,
                  highlight: bool = True,
                  max_length: Optional[int] = None) -> str:
    """
    Format JSON data.

    Args:
        value: JSON data to format
        indent: Indentation level
        sort_keys: Sort dictionary keys
        highlight: Apply syntax highlighting
        max_length: Truncate long values

    Returns:
        str: Formatted JSON
    """
    if not value:
        return ''

    try:
        # Parse if string
        if isinstance(value, str):
            value = json.loads(value)

        # Format JSON
        formatted = json.dumps(
            value,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=False
        )

        # Truncate if needed
        if max_length and len(formatted) > max_length:
            formatted = formatted[:max_length] + '...'

        if highlight:
            # Simple syntax highlighting
            formatted = formatted.replace(
                '"', '<span class="json-string">"</span>'
            ).replace(
                ': ', ': <span class="json-value">'
            ).replace(
                ',', '</span>,'
            )
            return Markup(f'<pre class="json">{formatted}</pre>')

        return formatted

    except Exception:
        return str(value)

def color_formatter(value: Any,
                   show_sample: bool = True,
                   show_value: bool = True,
                   size: str = '1em') -> str:
    """
    Format color values.

    Args:
        value: Color value to format
        show_sample: Show color sample
        show_value: Show color value
        size: Sample size

    Returns:
        str: Formatted color value
    """
    if not value:
        return ''

    try:
        color = str(value).strip()
        elements = []

        if show_sample:
            elements.append(
                f'<span class="color-sample" style="'
                f'display:inline-block;width:{size};height:{size};'
                f'background-color:{html.escape(color)};border:1px solid #ccc;'
                f'vertical-align:middle;margin-right:5px"></span>'
            )

        if show_value:
            elements.append(html.escape(color))

        return Markup(''.join(elements))

    except Exception:
        return str(value)

# Additional formatters for specific use cases
def file_size_formatter(value: int) -> str:
    """Format file size in bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"

def duration_formatter(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return ' '.join(parts)

def status_formatter(value: str) -> str:
    """Format status with appropriate styling."""
    status_classes = {
        'active': 'success',
        'inactive': 'danger',
        'pending': 'warning',
        'completed': 'info'
    }
    status_class = status_classes.get(value.lower(), 'secondary')
    return Markup(
        f'<span class="badge badge-{status_class}">{html.escape(value)}</span>'
    )
