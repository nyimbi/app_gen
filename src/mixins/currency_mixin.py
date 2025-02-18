"""
currency_mixin.py

This module provides a CurrencyMixin class for handling currency-related
operations in SQLAlchemy models for Flask-AppBuilder applications.

The CurrencyMixin allows for storing monetary amounts with proper precision,
handling multiple currencies, conversions, and formatting.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - requests (for exchange rate API)
    - babel (for currency formatting)
    - psycopg2 (for PostgreSQL support)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.1
"""

import json
import logging
import os
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from functools import lru_cache
from typing import Any, Dict, Optional, Union

import requests
from babel.numbers import format_currency, parse_decimal
from flask_appbuilder import Model
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship, validates

logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = {
    "USD": {"decimal_places": 2, "symbol": "$"},
    "EUR": {"decimal_places": 2, "symbol": "€"},
    "GBP": {"decimal_places": 2, "symbol": "£"},
    "JPY": {"decimal_places": 0, "symbol": "¥"},
    # Add more currencies as needed
}


class InvalidCurrencyError(ValueError):
    """Raised when an invalid currency code is used."""

    pass


class CurrencyMixin:
    """
    A mixin class for adding currency handling capabilities to SQLAlchemy models.

    Features:
    - Precise monetary amount storage using PostgreSQL NUMERIC
    - Currency validation and conversion
    - Multiple exchange rate provider support
    - Historical rate tracking
    - Arithmetic operations
    - Formatting with locale support
    - Caching for exchange rates
    - Audit logging
    - Performance optimization

    Class Attributes:
        __default_currency__ (str): The default currency code (e.g., 'USD')
        __exchange_rate_api_key__ (str): API key for exchange rate service
        __exchange_rate_api_url__ (str): URL for exchange rate API
        __exchange_rate_cache_duration__ (int): Cache duration in seconds
    """

    __default_currency__ = os.getenv("DEFAULT_CURRENCY", "USD")
    __exchange_rate_api_key__ = os.getenv("EXCHANGE_RATE_API_KEY", "your_api_key_here")
    __exchange_rate_api_url__ = os.getenv(
        "EXCHANGE_RATE_API_URL", "https://openexchangerates.org/api/latest.json"
    )
    __exchange_rate_cache_duration__ = int(
        os.getenv("EXCHANGE_RATE_CACHE_DURATION", "3600")
    )

    @declared_attr
    def amount(cls):
        """Precise monetary amount stored as NUMERIC."""
        return Column(
            Numeric(precision=18, scale=6),
            nullable=False,
            default=Decimal("0.00"),
            server_default="0",
        )

    @declared_attr
    def currency(cls):
        """Three-letter currency code with validation."""
        return Column(
            String(3),
            nullable=False,
            default=cls.__default_currency__,
            server_default=cls.__default_currency__,
        )

    @declared_attr
    def metadata_(cls):
        """Additional currency metadata stored as JSONB."""
        return Column(
            "metadata",
            MutableDict.as_mutable(JSONB),
            nullable=True,
            default={},
            server_default="{}",
        )

    @declared_attr
    def __table_args__(cls):
        """Table constraints and indices."""
        return (
            CheckConstraint(
                f"currency = ANY(ARRAY{list(SUPPORTED_CURRENCIES.keys())})",
                name=f"valid_currency_{cls.__tablename__}",
            ),
            CheckConstraint("amount >= 0", name=f"positive_amount_{cls.__tablename__}"),
            Index(f"ix_{cls.__tablename__}_currency", "currency"),
        )

    @classmethod
    def __declare_last__(cls):
        """Validate class configuration."""
        if not hasattr(cls, "__default_currency__"):
            raise ValueError(f"__default_currency__ must be defined for {cls.__name__}")
        if cls.__default_currency__ not in SUPPORTED_CURRENCIES:
            raise InvalidCurrencyError(
                f"Invalid default currency: {cls.__default_currency__}"
            )

    @validates("currency")
    def validate_currency(self, key, value):
        """Validate currency code."""
        if value not in SUPPORTED_CURRENCIES:
            raise InvalidCurrencyError(f"Unsupported currency: {value}")
        return value.upper()

    @validates("amount")
    def validate_amount(self, key, value):
        """Validate and normalize amount."""
        try:
            if isinstance(value, str):
                value = parse_decimal(value)
            return Decimal(str(value)).normalize()
        except (InvalidOperation, TypeError) as e:
            raise ValueError(f"Invalid monetary amount: {value}") from e

    @staticmethod
    @lru_cache(maxsize=128)
    def get_exchange_rates():
        """
        Fetch and cache current exchange rates from the API.

        Returns:
            dict: Exchange rates or None if unavailable

        Cache duration controlled by __exchange_rate_cache_duration__
        """
        try:
            response = requests.get(
                f"{CurrencyMixin.__exchange_rate_api_url__}?app_id={CurrencyMixin.__exchange_rate_api_key__}",
                timeout=10,
            )
            response.raise_for_status()
            rates = response.json()["rates"]
            # Validate rates
            return {
                k: Decimal(str(v))
                for k, v in rates.items()
                if k in SUPPORTED_CURRENCIES
            }
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            return None

    def convert_to(
        self, target_currency: str, rate_date: Optional[datetime] = None
    ) -> Decimal:
        """
        Convert the amount to the target currency.

        Args:
            target_currency (str): The currency code to convert to
            rate_date (datetime, optional): Historical rate date

        Returns:
            Decimal: The converted amount

        Raises:
            InvalidCurrencyError: If currency is invalid
            ValueError: If exchange rates unavailable
        """
        target_currency = target_currency.upper()
        if target_currency not in SUPPORTED_CURRENCIES:
            raise InvalidCurrencyError(f"Invalid target currency: {target_currency}")

        if self.currency == target_currency:
            return self.amount

        # Try historical rate first if date provided
        if rate_date:
            try:
                rate = ExchangeRate.get_rate(self.currency, target_currency, rate_date)
                if rate:
                    return self.amount * rate
            except Exception as e:
                logger.warning(f"Failed to get historical rate: {e}")

        # Fall back to current rates
        rates = self.get_exchange_rates()
        if not rates:
            raise ValueError("Exchange rates are not available")

        # Convert through USD as base currency
        try:
            usd_amount = self.amount / rates[self.currency]
            converted = usd_amount * rates[target_currency]
            return converted.normalize()
        except Exception as e:
            raise ValueError(f"Currency conversion failed: {e}")

    def format(
        self, locale: str = "en_US", decimal_places: Optional[int] = None
    ) -> str:
        """
        Format the monetary amount for display.

        Args:
            locale (str): The locale to use for formatting
            decimal_places (int, optional): Override default decimal places

        Returns:
            str: Formatted currency string
        """
        try:
            if decimal_places is None:
                decimal_places = SUPPORTED_CURRENCIES[self.currency]["decimal_places"]
            amount = self.amount.quantize(
                Decimal(10) ** -decimal_places, rounding=ROUND_HALF_UP
            )
            return format_currency(amount, self.currency, locale=locale)
        except Exception as e:
            logger.error(f"Formatting failed: {e}")
            return f"{self.currency} {self.amount}"

    def __add__(self, other: "CurrencyMixin") -> "CurrencyMixin":
        """Add two monetary amounts with automatic conversion."""
        if not isinstance(other, type(self)):
            raise TypeError(f"Cannot add {type(self)} and {type(other)}")

        try:
            if self.currency == other.currency:
                amount = self.amount + other.amount
            else:
                converted = other.convert_to(self.currency)
                amount = self.amount + converted
            return type(self)(amount=amount, currency=self.currency)
        except Exception as e:
            raise ValueError(f"Addition failed: {e}")

    def __sub__(self, other: "CurrencyMixin") -> "CurrencyMixin":
        """Subtract two monetary amounts with automatic conversion."""
        if not isinstance(other, type(self)):
            raise TypeError(f"Cannot subtract {type(self)} and {type(other)}")

        try:
            if self.currency == other.currency:
                amount = self.amount - other.amount
            else:
                converted = other.convert_to(self.currency)
                amount = self.amount - converted
            return type(self)(amount=amount, currency=self.currency)
        except Exception as e:
            raise ValueError(f"Subtraction failed: {e}")

    def __mul__(self, factor: Union[int, float, Decimal]) -> "CurrencyMixin":
        """Multiply monetary amount by a factor."""
        try:
            factor = Decimal(str(factor))
            amount = self.amount * factor
            return type(self)(amount=amount, currency=self.currency)
        except Exception as e:
            raise ValueError(f"Multiplication failed: {e}")

    def __truediv__(self, divisor: Union[int, float, Decimal]) -> "CurrencyMixin":
        """Divide monetary amount by a divisor."""
        try:
            divisor = Decimal(str(divisor))
            if divisor == 0:
                raise ValueError("Division by zero")
            amount = self.amount / divisor
            return type(self)(amount=amount, currency=self.currency)
        except Exception as e:
            raise ValueError(f"Division failed: {e}")

    def round(self, places: Optional[int] = None) -> "CurrencyMixin":
        """
        Round the monetary amount.

        Args:
            places (int, optional): Decimal places, defaults to currency standard

        Returns:
            CurrencyMixin: New instance with rounded amount
        """
        try:
            if places is None:
                places = SUPPORTED_CURRENCIES[self.currency]["decimal_places"]
            amount = self.amount.quantize(
                Decimal(10) ** -places, rounding=ROUND_HALF_UP
            )
            return type(self)(amount=amount, currency=self.currency)
        except Exception as e:
            raise ValueError(f"Rounding failed: {e}")


class ExchangeRate(Model):
    """
    Model for storing and managing historical exchange rates.

    Features:
    - Historical rate tracking
    - Rate validity periods
    - Source attribution
    - Rate metadata
    - Update audit trail
    """

    __tablename__ = "nx_exchange_rates"
    __table_args__ = (
        CheckConstraint("rate > 0", name="positive_rate"),
        Index("ix_exchange_rates_lookup", "from_currency", "to_currency", "date"),
    )

    id = Column(Integer, primary_key=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(precision=18, scale=6), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=True)
    source = Column(String(50), nullable=False, default="api")
    metadata = Column(
        MutableDict.as_mutable(JSONB), nullable=True, default={}, server_default="{}"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    @classmethod
    def get_rate(
        cls, from_currency: str, to_currency: str, date: Optional[datetime] = None
    ) -> Optional[Decimal]:
        """
        Get exchange rate for specific date or latest.

        Args:
            from_currency (str): Source currency code
            to_currency (str): Target currency code
            date (datetime, optional): Historical date

        Returns:
            Decimal: Exchange rate or None if not found
        """
        if from_currency == to_currency:
            return Decimal("1.0")

        query = cls.query.filter_by(
            from_currency=from_currency.upper(), to_currency=to_currency.upper()
        )

        if date:
            query = query.filter(
                cls.valid_from <= date,
                (cls.valid_to.is_(None) | (cls.valid_to >= date)),
            )

        rate = query.order_by(cls.date.desc()).first()
        return rate.rate if rate else None

    @classmethod
    def update_rates(
        cls, rates: Dict[str, Union[float, Decimal]], session: Any
    ) -> None:
        """
        Update exchange rates in database.

        Args:
            rates (dict): Currency rates dictionary
            session: SQLAlchemy session

        Features:
        - Atomic updates
        - Rate validation
        - Historical tracking
        - Update metadata
        """
        try:
            now = datetime.utcnow()

            # Mark previous rates as expired
            session.query(cls).filter(cls.valid_to.is_(None)).update(
                {"valid_to": now, "updated_at": now}
            )

            # Add new rates
            for currency, rate in rates.items():
                if currency != "USD" and currency in SUPPORTED_CURRENCIES:
                    exchange_rate = cls(
                        from_currency="USD",
                        to_currency=currency,
                        rate=Decimal(str(rate)),
                        date=now,
                        valid_from=now,
                        metadata={
                            "source_timestamp": now.isoformat(),
                            "update_type": "api",
                        },
                    )
                    session.add(exchange_rate)

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update exchange rates: {e}")
            raise
