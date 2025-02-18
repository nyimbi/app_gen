"""
internationalization_mixin.py

This module provides an InternationalizationMixin class for implementing
multi-language support in SQLAlchemy models for Flask-AppBuilder applications.

The InternationalizationMixin allows for storing and retrieving translated
content for specified fields, with support for fallback languages and
integration with Flask-Babel.

Key Features:
    - Field-level translations using PostgreSQL JSONB
    - Automatic fallback language support
    - Translation import/export
    - Translation status reporting
    - Automatic translation detection
    - Versioning support
    - Translation validation
    - Bulk operations
    - Caching integration
    - Migration helpers

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - Flask-Babel
    - psycopg2-binary
    - Flask-Caching (optional)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0.1
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from flask import current_app, g
from flask_appbuilder import Model
from flask_babel import get_locale
from flask_babel import gettext as _
from sqlalchemy import Column, Integer, String, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Query, Session
from sqlalchemy.types import TypeDecorator

logger = logging.getLogger(__name__)


class TranslationJSONB(TypeDecorator):
    """Custom type for handling translation JSON data with validation"""

    impl = JSONB

    def process_bind_param(self, value: dict, dialect) -> dict:
        """Validate and process translation data before saving"""
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("Translation data must be a dictionary")
        return value

    def process_result_value(self, value: dict, dialect) -> dict:
        """Process translation data after loading"""
        return value if value else {}


class InternationalizationMixin:
    """
    A mixin class for adding internationalization support to SQLAlchemy models.

    Features:
        - Field-level translations
        - Automatic fallback language handling
        - Translation validation
        - Import/export capabilities
        - Translation status tracking
        - Version control
        - Cache integration
        - Bulk operations

    Class Attributes:
        __translatable__ (list): List of field names that should be translatable
        __fallback_locale__ (str): Fallback locale to use when translation missing
        __translation_versioning__ (bool): Enable translation version tracking
        __translation_cache_enabled__ (bool): Enable translation caching
        __translation_cache_timeout__ (int): Cache timeout in seconds
        __translation_validators__ (dict): Custom validation functions by field

    Example:
        class Product(InternationalizationMixin, Model):
            __tablename__ = 'nx_products'
            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False)
            description = Column(String(500))

            __translatable__ = ['name', 'description']
            __fallback_locale__ = 'en'
            __translation_versioning__ = True
    """

    __translatable__ = []
    __fallback_locale__ = "en"
    __translation_versioning__ = False
    __translation_cache_enabled__ = False
    __translation_cache_timeout__ = 300
    __translation_validators__ = {}

    @declared_attr
    def translations(cls):
        """Store translations in JSONB column with validation"""
        return Column(
            TranslationJSONB,
            default=dict,
            nullable=False,
            server_default="{}",
            comment="Field translations in format {field: {locale: value}}",
        )

    @declared_attr
    def translation_versions(cls):
        """Store translation version history if enabled"""
        if cls.__translation_versioning__:
            return Column(
                JSONB,
                default=list,
                nullable=False,
                server_default="[]",
                comment="Translation version history",
            )
        return None

    @classmethod
    def __declare_last__(cls):
        """Setup translation handling and validation"""
        if not cls.__translatable__:
            raise ValueError(f"__translatable__ must be defined for {cls.__name__}")

        # Create hybrid properties for each translatable field
        for field in cls.__translatable__:
            setattr(
                cls,
                f"{field}_translations",
                hybrid_property(
                    fget=lambda self, field=field: self._get_translation(field),
                    fset=lambda self, value, field=field: self._set_translation(
                        field, value
                    ),
                ),
            )

        # Register event listeners
        event.listen(cls, "before_insert", cls._before_save)
        event.listen(cls, "before_update", cls._before_save)

        # Initialize cache if enabled
        if cls.__translation_cache_enabled__:
            if not hasattr(current_app, "cache"):
                raise RuntimeError(
                    "Flask-Caching not configured but translation caching enabled"
                )

    def _get_cache_key(self, field: str, locale: str) -> str:
        """Generate cache key for translation"""
        return f"trans_{self.__class__.__name__}_{self.id}_{field}_{locale}"

    def _get_translation(self, field: str) -> str:
        """
        Get translated value with caching and validation.

        Args:
            field: Field name to translate

        Returns:
            Translated value or original
        """
        locale = str(get_locale())

        # Check cache first
        if self.__translation_cache_enabled__:
            cache_key = self._get_cache_key(field, locale)
            cached = current_app.cache.get(cache_key)
            if cached is not None:
                return cached

        translations = self.translations.get(field, {})

        # Try current locale
        if locale in translations:
            value = translations[locale]
        # Try fallback locale
        elif self.__fallback_locale__ in translations:
            value = translations[self.__fallback_locale__]
        # Use original value
        else:
            value = getattr(self, field)

        # Cache translation if enabled
        if self.__translation_cache_enabled__:
            current_app.cache.set(
                cache_key, value, timeout=self.__translation_cache_timeout__
            )

        return value

    def _set_translation(self, field: str, value: Union[str, Dict[str, str]]) -> None:
        """
        Set translation with validation and versioning.

        Args:
            field: Field to translate
            value: Translation string or {locale: translation} dict
        """
        if field not in self.__translatable__:
            raise ValueError(f"Field '{field}' is not translatable")

        if isinstance(value, str):
            # Single translation - use current locale
            locale = str(get_locale())
            translations = {locale: value}
        elif isinstance(value, dict):
            # Multiple translations
            translations = value
        else:
            raise ValueError("Translation must be string or locale dict")

        # Validate translations
        if field in self.__translation_validators__:
            validator = self.__translation_validators__[field]
            for locale, trans in translations.items():
                if not validator(trans):
                    raise ValueError(f"Invalid translation for {field} ({locale})")

        # Store version if enabled
        if self.__translation_versioning__:
            version = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": getattr(g, "user", {}).get("id"),
                "field": field,
                "translations": translations,
                "checksum": hashlib.md5(
                    json.dumps(translations, sort_keys=True).encode()
                ).hexdigest(),
            }
            if not hasattr(self, "translation_versions"):
                self.translation_versions = []
            self.translation_versions.append(version)

        # Update translations
        if field not in self.translations:
            self.translations[field] = {}
        self.translations[field].update(translations)

        # Invalidate cache
        if self.__translation_cache_enabled__:
            for locale in translations:
                cache_key = self._get_cache_key(field, locale)
                current_app.cache.delete(cache_key)

    @classmethod
    def _before_save(cls, mapper, connection, target):
        """Validate all translations before save"""
        if not isinstance(target.translations, dict):
            raise ValueError("translations must be a dictionary")

        for field, translations in target.translations.items():
            if field not in cls.__translatable__:
                raise ValueError(f"Field '{field}' is not translatable")

            if not isinstance(translations, dict):
                raise ValueError(
                    f"Translations for {field} must be a locale dictionary"
                )

            # Validate translations
            if field in cls.__translation_validators__:
                validator = cls.__translation_validators__[field]
                for locale, value in translations.items():
                    if not validator(value):
                        raise ValueError(f"Invalid translation for {field} ({locale})")

    def set_translation(self, field: str, locale: str, value: str) -> None:
        """
        Set translation for specific field and locale.

        Args:
            field: Field name to translate
            locale: Locale code
            value: Translated value
        """
        self._set_translation(field, {locale: value})

    def get_translation(self, field: str, locale: Optional[str] = None) -> str:
        """
        Get translation for specific field and locale.

        Args:
            field: Field name to translate
            locale: Optional locale code (default: current locale)

        Returns:
            Translated value or original
        """
        if locale is None:
            locale = str(get_locale())

        if field not in self.__translatable__:
            raise ValueError(f"Field '{field}' is not translatable")

        translations = self.translations.get(field, {})

        if locale in translations:
            return translations[locale]
        elif self.__fallback_locale__ in translations:
            return translations[self.__fallback_locale__]
        else:
            return getattr(self, field)

    @classmethod
    def export_translations(cls, session: Session) -> Dict[int, dict]:
        """
        Export all translations with metadata.

        Args:
            session: SQLAlchemy session

        Returns:
            Dict of translations by instance ID
        """
        result = {}
        for instance in session.query(cls).all():
            result[instance.id] = {
                "translations": instance.translations,
                "metadata": {
                    "updated_at": datetime.utcnow().isoformat(),
                    "version": "1.0",
                },
            }
            if cls.__translation_versioning__:
                result[instance.id]["versions"] = instance.translation_versions
        return result

    @classmethod
    def import_translations(
        cls,
        session: Session,
        translations_data: Dict[int, dict],
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """
        Import translations with validation.

        Args:
            session: SQLAlchemy session
            translations_data: Translations by instance ID
            overwrite: Whether to overwrite existing translations

        Returns:
            Dict with import statistics
        """
        stats = {"updated": 0, "failed": 0, "skipped": 0}

        for instance_id, data in translations_data.items():
            try:
                instance = session.query(cls).get(instance_id)
                if not instance:
                    stats["failed"] += 1
                    continue

                translations = data.get("translations", {})

                if not overwrite:
                    # Merge with existing
                    for field, trans in translations.items():
                        if field not in instance.translations:
                            instance.translations[field] = {}
                        instance.translations[field].update(trans)
                else:
                    # Replace existing
                    instance.translations = translations

                if cls.__translation_versioning__:
                    versions = data.get("versions", [])
                    if versions:
                        instance.translation_versions = versions

                stats["updated"] += 1

            except Exception as e:
                logger.error(f"Failed to import translations for {instance_id}: {e}")
                stats["failed"] += 1

        session.commit()
        return stats

    @classmethod
    def get_missing_translations(
        cls, session: Session, locales: List[str]
    ) -> Dict[int, Dict[str, List[str]]]:
        """
        Get report of missing translations.

        Args:
            session: SQLAlchemy session
            locales: List of locale codes to check

        Returns:
            Dict of missing translations by instance ID
        """
        missing = {}
        for instance in session.query(cls).all():
            instance_missing = {}
            for field in cls.__translatable__:
                translations = instance.translations.get(field, {})
                missing_locales = [loc for loc in locales if loc not in translations]
                if missing_locales:
                    instance_missing[field] = missing_locales
            if instance_missing:
                missing[instance.id] = instance_missing
        return missing

    @classmethod
    def bulk_translate(
        cls,
        session: Session,
        translations: Dict[int, Dict[str, Dict[str, str]]],
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Bulk update translations efficiently.

        Args:
            session: SQLAlchemy session
            translations: {id: {field: {locale: value}}}
            validate: Whether to validate translations

        Returns:
            Dict with operation statistics
        """
        stats = {"updated": 0, "failed": 0}

        for instance_id, fields in translations.items():
            try:
                instance = session.query(cls).get(instance_id)
                if not instance:
                    stats["failed"] += 1
                    continue

                for field, trans in fields.items():
                    instance._set_translation(field, trans)

                stats["updated"] += 1

            except Exception as e:
                logger.error(f"Bulk translation failed for {instance_id}: {e}")
                stats["failed"] += 1

        session.commit()
        return stats

    @classmethod
    def get_translation_stats(
        cls, session: Session, locales: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get translation coverage statistics.

        Args:
            session: SQLAlchemy session
            locales: Optional list of locales to check

        Returns:
            Translation statistics
        """
        stats = {
            "total_records": 0,
            "total_fields": len(cls.__translatable__),
            "by_locale": {},
            "by_field": {},
            "complete": 0,
            "partial": 0,
            "missing": 0,
        }

        if locales is None:
            # Get all used locales
            locales = set()
            for instance in session.query(cls).all():
                for field in cls.__translatable__:
                    locales.update(instance.translations.get(field, {}).keys())
            locales = sorted(locales)

        query = session.query(cls)
        stats["total_records"] = query.count()

        for instance in query.all():
            has_translations = False
            missing_translations = False

            for field in cls.__translatable__:
                translations = instance.translations.get(field, {})

                # Update field stats
                if field not in stats["by_field"]:
                    stats["by_field"][field] = {
                        "total": 0,
                        "by_locale": {loc: 0 for loc in locales},
                    }

                for locale in locales:
                    # Update locale stats
                    if locale not in stats["by_locale"]:
                        stats["by_locale"][locale] = 0

                    if locale in translations:
                        has_translations = True
                        stats["by_locale"][locale] += 1
                        stats["by_field"][field]["by_locale"][locale] += 1
                        stats["by_field"][field]["total"] += 1
                    else:
                        missing_translations = True

            if has_translations and missing_translations:
                stats["partial"] += 1
            elif has_translations:
                stats["complete"] += 1
            else:
                stats["missing"] += 1

        return stats


# Example usage with all features:
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import validates
from mixins.internationalization_mixin import InternationalizationMixin

class Product(InternationalizationMixin, Model):
    __tablename__ = 'nx_products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))

    __translatable__ = ['name', 'description']
    __fallback_locale__ = 'en'
    __translation_versioning__ = True
    __translation_cache_enabled__ = True
    __translation_cache_timeout__ = 300

    # Custom translation validators
    @classmethod
    def validate_name(cls, value):
        return len(value) <= 100

    @classmethod
    def validate_description(cls, value):
        return len(value) <= 500

    __translation_validators__ = {
        'name': validate_name,
        'description': validate_description
    }

# Usage examples:

# Basic translation
product = Product(name="Laptop", description="A powerful laptop")
product.set_translation('name', 'es', 'Portátil')
product.set_translation('name', 'fr', 'Ordinateur portable')

# Bulk translation
product.name_translations = {
    'de': 'Laptop',
    'it': 'Computer portatile'
}

# Translation with versions
product.set_translation('description', 'es', 'Un portátil potente')
print(product.translation_versions) # Shows version history

# Get translation
print(product.get_translation('name', 'es')) # Portátil
print(product.name_translations) # Current locale translation

# Export/Import
translations = Product.export_translations(db.session)
stats = Product.import_translations(db.session, translations)

# Missing translations report
missing = Product.get_missing_translations(
    db.session,
    ['en', 'es', 'fr', 'de', 'it']
)

# Translation statistics
stats = Product.get_translation_stats(
    db.session,
    ['en', 'es', 'fr', 'de', 'it']
)

# Bulk operations
translations = {
    1: {
        'name': {'pl': 'Laptop'},
        'description': {'pl': 'Mocny laptop'}
    },
    2: {
        'name': {'pl': 'Mysz'},
        'description': {'pl': 'Bezprzewodowa mysz'}
    }
}
stats = Product.bulk_translate(db.session, translations)
"""
