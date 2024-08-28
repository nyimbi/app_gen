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

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import requests
from babel.numbers import format_currency
import json
import logging

logger = logging.getLogger(__name__)

class CurrencyMixin:
    """
    A mixin class for adding currency handling capabilities to SQLAlchemy models.

    This mixin provides methods for currency conversion, formatting, and arithmetic
    operations on monetary amounts.

    Class Attributes:
        __default_currency__ (str): The default currency code (e.g., 'USD').
        __exchange_rate_api_key__ (str): API key for exchange rate service.
        __exchange_rate_api_url__ (str): URL for exchange rate API.
    """

    __default_currency__ = 'USD'
    __exchange_rate_api_key__ = 'your_api_key_here'  # Replace with your actual API key
    __exchange_rate_api_url__ = 'https://openexchangerates.org/api/latest.json'

    @declared_attr
    def amount(cls):
        return Column(Numeric(precision=18, scale=6), nullable=False)

    @declared_attr
    def currency(cls):
        return Column(String(3), nullable=False, default=cls.__default_currency__)

    @classmethod
    def __declare_last__(cls):
        if not hasattr(cls, '__default_currency__'):
            raise ValueError(f"__default_currency__ must be defined for {cls.__name__}")

    @staticmethod
    def get_exchange_rates():
        """Fetch current exchange rates from the API."""
        try:
            response = requests.get(f"{CurrencyMixin.__exchange_rate_api_url__}?app_id={CurrencyMixin.__exchange_rate_api_key__}")
            response.raise_for_status()
            return response.json()['rates']
        except requests.RequestException as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            return None

    def convert_to(self, target_currency):
        """
        Convert the amount to the target currency.

        Args:
            target_currency (str): The currency code to convert to.

        Returns:
            Decimal: The converted amount.

        Raises:
            ValueError: If exchange rates are not available.
        """
        if self.currency == target_currency:
            return self.amount

        rates = self.get_exchange_rates()
        if not rates:
            raise ValueError("Exchange rates are not available")

        # Convert to USD first (base currency for the API)
        usd_amount = self.amount / Decimal(rates[self.currency])
        # Then convert to target currency
        return usd_amount * Decimal(rates[target_currency])

    def format(self, locale='en_US'):
        """
        Format the monetary amount for display.

        Args:
            locale (str): The locale to use for formatting.

        Returns:
            str: Formatted currency string.
        """
        return format_currency(self.amount, self.currency, locale=locale)

    def __add__(self, other):
        """
        Add two monetary amounts.

        Args:
            other (CurrencyMixin): Another instance to add.

        Returns:
            CurrencyMixin: A new instance with the sum.

        Raises:
            ValueError: If currencies don't match and conversion fails.
        """
        if self.currency == other.currency:
            return type(self)(amount=self.amount + other.amount, currency=self.currency)
        else:
            converted_amount = other.convert_to(self.currency)
            return type(self)(amount=self.amount + converted_amount, currency=self.currency)

    def __sub__(self, other):
        """
        Subtract two monetary amounts.

        Args:
            other (CurrencyMixin): Another instance to subtract.

        Returns:
            CurrencyMixin: A new instance with the difference.

        Raises:
            ValueError: If currencies don't match and conversion fails.
        """
        if self.currency == other.currency:
            return type(self)(amount=self.amount - other.amount, currency=self.currency)
        else:
            converted_amount = other.convert_to(self.currency)
            return type(self)(amount=self.amount - converted_amount, currency=self.currency)

    def __mul__(self, factor):
        """
        Multiply the monetary amount by a factor.

        Args:
            factor (float or int): The factor to multiply by.

        Returns:
            CurrencyMixin: A new instance with the product.
        """
        return type(self)(amount=self.amount * Decimal(str(factor)), currency=self.currency)

    def __truediv__(self, divisor):
        """
        Divide the monetary amount by a divisor.

        Args:
            divisor (float or int): The divisor.

        Returns:
            CurrencyMixin: A new instance with the quotient.

        Raises:
            ValueError: If the divisor is zero.
        """
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return type(self)(amount=self.amount / Decimal(str(divisor)), currency=self.currency)

    def round(self, places=2):
        """
        Round the monetary amount to a specified number of decimal places.

        Args:
            places (int): Number of decimal places to round to.

        Returns:
            CurrencyMixin: A new instance with the rounded amount.
        """
        rounded_amount = self.amount.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
        return type(self)(amount=rounded_amount, currency=self.currency)

class ExchangeRate(Model):
    """
    Model to store historical exchange rates.
    """
    __tablename__ = 'nx_exchange_rates'

    id = Column(Integer, primary_key=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(precision=18, scale=6), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def get_rate(cls, from_currency, to_currency, date=None):
        """
        Get the exchange rate for a specific date or the latest rate.

        Args:
            from_currency (str): The source currency code.
            to_currency (str): The target currency code.
            date (datetime, optional): The date for the exchange rate. If None, use the latest rate.

        Returns:
            Decimal: The exchange rate.
        """
        query = cls.query.filter_by(from_currency=from_currency, to_currency=to_currency)
        if date:
            query = query.filter(cls.date <= date)
        return query.order_by(cls.date.desc()).first().rate

    @classmethod
    def update_rates(cls, rates, session):
        """
        Update the database with new exchange rates.

        Args:
            rates (dict): Dictionary of currency rates.
            session: SQLAlchemy session.
        """
        for currency, rate in rates.items():
            if currency != 'USD':  # Assuming USD is the base currency
                exchange_rate = cls(
                    from_currency='USD',
                    to_currency=currency,
                    rate=Decimal(str(rate))
                )
                session.add(exchange_rate)
        session.commit()

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.currency_mixin import CurrencyMixin

class Product(CurrencyMixin, Model):
    __tablename__ = 'nx_products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    __default_currency__ = 'USD'

# In your application code:

# Create a new product
new_product = Product(name="Premium Widget", amount=Decimal('29.99'), currency='USD')
db.session.add(new_product)
db.session.commit()

# Convert to another currency
eur_price = new_product.convert_to('EUR')
print(f"Price in EUR: {eur_price}")

# Format for display
formatted_price = new_product.format(locale='en_US')
print(f"Formatted price: {formatted_price}")

# Arithmetic operations
discount_product = new_product * Decimal('0.9')  # 10% discount
print(f"Discounted price: {discount_product.format()}")

# Updating exchange rates
rates = CurrencyMixin.get_exchange_rates()
if rates:
    ExchangeRate.update_rates(rates, db.session)

# Using historical rates
historical_rate = ExchangeRate.get_rate('USD', 'EUR', date=datetime(2023, 1, 1))
print(f"Historical USD to EUR rate: {historical_rate}")
"""
