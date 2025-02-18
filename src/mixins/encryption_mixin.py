"""
encryption_mixin.py

This module provides an EncryptionMixin class for implementing field-level
encryption in SQLAlchemy models for Flask-AppBuilder applications.

The EncryptionMixin allows automatic encryption and decryption of specified
fields, enhancing data security for sensitive information stored in the database.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - cryptography
    - psycopg2-binary
    - SQLAlchemy-Utils

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.2
"""

import base64
import json
import logging
import os
from datetime import datetime, date
from typing import Any, Dict, Optional, Union, List, TypeVar, Generic, Callable
from functools import wraps

from cryptography.exceptions import InvalidKey, InvalidToken
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flask_appbuilder.models.mixins import AuditMixin
from sqlalchemy import (
    JSON, Column, DateTime, LargeBinary, String, Text, Integer,
    ForeignKey, Boolean, event, inspect
)
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.types import TypeDecorator, TypeEngine
from sqlalchemy_utils import EncryptedType, force_auto_coercion

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic type hints
T = TypeVar('T')

# Enable SQLAlchemy-Utils type coercion
force_auto_coercion()

class EncryptionMixin(AuditMixin):
    """
    A mixin class for adding field-level encryption to SQLAlchemy models.

    Provides comprehensive encryption features including:
    - Automatic encryption/decryption of fields
    - Key rotation and versioning
    - Data migration tools
    - Audit logging
    - Compression support
    - Custom field types
    - Batch operations
    - Recovery mechanisms

    Class Attributes:
        __encrypted_fields__ (list): List of field names to be encrypted
        __encryption_key__ (bytes): The encryption key used for Fernet
        __salt__ (bytes): Salt used for key derivation
        __key_iterations__ (int): Number of iterations for key derivation
        __key_version__ (int): Current encryption key version
        __key_history__ (dict): History of encryption keys for rotation
        __compression__ (bool): Enable compression for encrypted data
        __key_derivation__ (str): Key derivation method ('pbkdf2', 'argon2', etc)
        __error_handling__ (str): Error handling mode ('strict', 'lenient')

    Supported Field Types:
        - String / Text
        - JSON / JSONB
        - LargeBinary / BYTEA
        - Date / DateTime
        - Boolean
        - Numeric types
        - Custom field types via TypeDecorator
    """

    __encrypted_fields__: List[str] = []
    __encryption_key__: Optional[bytes] = None
    __salt__: Optional[bytes] = None
    __key_iterations__: int = 100000
    __key_version__: int = 1
    __key_history__: Dict[int, bytes] = {}
    __compression__: bool = True
    __key_derivation__: str = 'pbkdf2'
    __error_handling__: str = 'strict'

    # Metadata columns
    __encryption_metadata__ = Column(JSONB, nullable=True,
                                   default=lambda: {'version': 1, 'fields': {}})
    __key_version = Column(Integer, default=1, nullable=False)
    __last_rotated__ = Column(DateTime, default=datetime.utcnow,
                             nullable=False)
    __is_encrypted__ = Column(Boolean, default=True, nullable=False)
    __encryption_errors__ = Column(JSONB, nullable=True)

    @classmethod
    def __declare_last__(cls) -> None:
        """Set up event listeners for encryption and decryption."""
        if not cls.__encrypted_fields__:
            return

        if not hasattr(cls, "__encryption_metadata__"):
            cls.__encryption_metadata__ = Column(JSONB, nullable=True,
                                               default=lambda: {'version': 1, 'fields': {}})

        for field in cls.__encrypted_fields__:
            # Use BYTEA for optimal binary storage in PostgreSQL
            setattr(cls, f"{field}_encrypted", Column(BYTEA, nullable=True))

            # Set up SQLAlchemy event listeners
            event.listen(getattr(cls, field), "set", cls.encrypt_field)
            event.listen(getattr(cls, field), "get", cls.decrypt_field)

            # Add validation event listeners
            event.listen(cls, 'before_insert', cls.validate_encrypted_fields)
            event.listen(cls, 'before_update', cls.validate_encrypted_fields)

    @classmethod
    def validate_encrypted_fields(cls, mapper, connection, target) -> None:
        """Validate encrypted fields before database operations."""
        for field in cls.__encrypted_fields__:
            value = getattr(target, field, None)
            if value is not None:
                try:
                    # Validate field value type and format
                    cls._validate_field_value(field, value)

                    # Check encryption status
                    encrypted_value = getattr(target, f"{field}_encrypted", None)
                    if encrypted_value is None and value is not None:
                        raise ValueError(f"Field {field} is not properly encrypted")

                except Exception as e:
                    if cls.__error_handling__ == 'strict':
                        raise
                    else:
                        logger.warning(f"Validation error for {field}: {str(e)}")
                        cls._record_encryption_error(target, field, str(e))

    @classmethod
    def _validate_field_value(cls, field: str, value: Any) -> None:
        """Validate field value type and format."""
        field_type = type(value).__name__

        # Get expected type from model
        expected_type = cls._get_field_type(field)

        if not isinstance(value, expected_type):
            raise TypeError(f"Invalid type for {field}: expected {expected_type}, got {field_type}")

    @classmethod
    def _record_encryption_error(cls, target: Any, field: str, error: str) -> None:
        """Record encryption error in metadata."""
        errors = getattr(target, '__encryption_errors__', {}) or {}
        errors[field] = {
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat(),
            'version': cls.__key_version__
        }
        setattr(target, '__encryption_errors__', errors)

    @classmethod
    def set_encryption_key(cls, key: str, version: int = 1,
                         derivation: str = 'pbkdf2') -> None:
        """
        Set the encryption key for the model with advanced options.

        Args:
            key (str): The encryption key (min 32 chars)
            version (int): Key version number
            derivation (str): Key derivation method

        Raises:
            ValueError: If key is invalid or version exists
            InvalidKey: If key derivation fails
        """
        if not key or len(key) < 32:
            raise ValueError("Encryption key must be at least 32 characters")

        if version in cls.__key_history__:
            raise ValueError(f"Key version {version} already exists")

        # Generate new salt if none exists
        if not cls.__salt__:
            cls.__salt__ = os.urandom(16)

        try:
            # Derive key using selected method
            if derivation == 'pbkdf2':
                derived_key = cls._derive_key_pbkdf2(key)
            elif derivation == 'argon2':
                derived_key = cls._derive_key_argon2(key)
            else:
                raise ValueError(f"Unsupported key derivation method: {derivation}")

            # Validate derived key
            Fernet(derived_key)

            # Store key securely
            cls.__key_history__[version] = derived_key
            cls.__encryption_key__ = derived_key
            cls.__key_version__ = version
            cls.__key_derivation__ = derivation

            logger.info(f"Encryption key set successfully (version {version})")

        except Exception as e:
            logger.error(f"Error setting encryption key: {str(e)}")
            raise InvalidKey("Invalid encryption key") from e

    @classmethod
    def _derive_key_pbkdf2(cls, key: str) -> bytes:
        """Derive key using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=cls.__salt__,
            iterations=cls.__key_iterations__,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(key.encode()))

    @classmethod
    def _derive_key_argon2(cls, key: str) -> bytes:
        """Derive key using Argon2."""
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        hash = ph.hash(key)
        return base64.urlsafe_b64encode(hash.encode()[:32])

    @classmethod
    def encrypt_field(cls, target: Any, value: Any, oldvalue: Any,
                     initiator: Any) -> Any:
        """
        Encrypt a field value with comprehensive error handling.

        Args:
            target: The model instance
            value: The value to encrypt
            oldvalue: The previous value
            initiator: The initiator of the change

        Returns:
            Any: The original value (encrypted version stored separately)

        Raises:
            ValueError: If encryption fails
            TypeError: If value type is invalid
        """
        if value is None:
            setattr(target, f"{initiator.key}_encrypted", None)
            return None

        if cls.__encryption_key__ is None:
            raise ValueError("Encryption key not set")

        try:
            # Handle different value types
            if isinstance(value, (datetime, date)):
                json_value = value.isoformat()
            elif isinstance(value, (dict, list)):
                json_value = value
            else:
                json_value = str(value)

            # Convert to JSON string
            json_str = json.dumps(json_value)

            # Compress if enabled
            if cls.__compression__:
                import zlib
                json_str = zlib.compress(json_str.encode())

            # Encrypt the value
            f = Fernet(cls.__encryption_key__)
            encrypted_value = f.encrypt(
                json_str if isinstance(json_str, bytes) else json_str.encode()
            )

            # Store encryption metadata
            metadata = {
                "version": cls.__key_version__,
                "encrypted_at": datetime.utcnow().isoformat(),
                "field_type": type(value).__name__,
                "compressed": cls.__compression__,
                "checksum": cls._calculate_checksum(encrypted_value)
            }

            current_metadata = getattr(target, "__encryption_metadata__", {}) or {}
            current_metadata[initiator.key] = metadata
            setattr(target, "__encryption_metadata__", current_metadata)

            # Store encrypted value
            setattr(target, f"{initiator.key}_encrypted", encrypted_value)
            flag_modified(target, f"{initiator.key}_encrypted")

            return value

        except Exception as e:
            logger.error(f"Encryption error for {initiator.key}: {str(e)}")
            if cls.__error_handling__ == 'strict':
                raise ValueError(f"Failed to encrypt {initiator.key}: {str(e)}")
            else:
                cls._record_encryption_error(target, initiator.key, str(e))
                return value

    @classmethod
    def decrypt_field(cls, target: Any, value: Any, initiator: Any) -> Any:
        """
        Decrypt a field value with type conversion and error recovery.

        Args:
            target: The model instance
            value: The value to decrypt
            initiator: The initiator of the change

        Returns:
            Any: The decrypted value

        Raises:
            ValueError: If decryption fails
            InvalidToken: If encrypted data is corrupted
        """
        encrypted_value = getattr(target, f"{initiator.key}_encrypted")
        if encrypted_value is None:
            return None

        if cls.__encryption_key__ is None:
            raise ValueError("Encryption key not set")

        try:
            # Get metadata
            metadata = getattr(target, "__encryption_metadata__", {}) or {}
            field_metadata = metadata.get(initiator.key, {})
            field_type = field_metadata.get("field_type", "str")
            key_version = field_metadata.get("version", 1)
            is_compressed = field_metadata.get("compressed", False)

            # Verify checksum
            stored_checksum = field_metadata.get("checksum")
            if stored_checksum:
                current_checksum = cls._calculate_checksum(encrypted_value)
                if stored_checksum != current_checksum:
                    raise InvalidToken("Data integrity check failed")

            # Get correct key version
            key = cls.__key_history__.get(key_version, cls.__encryption_key__)
            f = Fernet(key)

            # Decrypt value
            decrypted_value = f.decrypt(encrypted_value)

            # Decompress if needed
            if is_compressed:
                import zlib
                decrypted_value = zlib.decompress(decrypted_value)

            # Parse JSON
            json_value = json.loads(decrypted_value.decode())

            # Convert to correct type
            if field_type == "datetime":
                return datetime.fromisoformat(json_value)
            elif field_type == "date":
                return date.fromisoformat(json_value)
            elif field_type in ("dict", "list"):
                return json_value
            elif field_type == "bool":
                return bool(json_value)
            elif field_type == "int":
                return int(json_value)
            elif field_type == "float":
                return float(json_value)
            else:
                return json_value

        except InvalidToken:
            logger.error(f"Invalid token for {initiator.key}")
            if cls.__error_handling__ == 'strict':
                raise
            return None
        except Exception as e:
            logger.error(f"Decryption error for {initiator.key}: {str(e)}")
            if cls.__error_handling__ == 'strict':
                raise ValueError(f"Failed to decrypt {initiator.key}: {str(e)}")
            return None

    @staticmethod
    def _calculate_checksum(data: bytes) -> str:
        """Calculate SHA-256 checksum of data."""
        return base64.b64encode(
            hashes.Hash(hashes.SHA256(), backend=default_backend())
            .update(data)
            .finalize()
        ).decode()

    @classmethod
    def migrate_unencrypted_data(cls, session, batch_size: int = 100,
                                dry_run: bool = False) -> Dict[str, Any]:
        """
        Migrate unencrypted data to encrypted format with detailed reporting.

        Args:
            session: SQLAlchemy session
            batch_size (int): Number of records per batch
            dry_run (bool): Simulate migration without changes

        Returns:
            dict: Migration statistics and results

        Raises:
            ValueError: If migration fails
        """
        stats = {
            'total': 0,
            'processed': 0,
            'encrypted': 0,
            'skipped': 0,
            'errors': [],
            'start_time': datetime.utcnow(),
            'end_time': None
        }

        try:
            stats['total'] = session.query(cls).count()
            processed = 0

            while processed < stats['total']:
                batch = session.query(cls).offset(processed).limit(batch_size).all()

                for instance in batch:
                    stats['processed'] += 1

                    for field in cls.__encrypted_fields__:
                        try:
                            if getattr(instance, f"{field}_encrypted") is None:
                                current_value = getattr(instance, field)
                                if current_value is not None:
                                    if not dry_run:
                                        setattr(instance, field, current_value)
                                    stats['encrypted'] += 1
                            else:
                                stats['skipped'] += 1

                        except Exception as e:
                            error = {
                                'instance_id': instance.id,
                                'field': field,
                                'error': str(e)
                            }
                            stats['errors'].append(error)
                            logger.error(f"Migration error: {error}")

                if not dry_run:
                    session.commit()
                processed += len(batch)

                # Progress logging
                progress = (processed / stats['total']) * 100
                logger.info(f"Migration progress: {progress:.1f}% complete")

            stats['end_time'] = datetime.utcnow()
            duration = stats['end_time'] - stats['start_time']
            logger.info(f"Migration completed in {duration}")

            return stats

        except Exception as e:
            session.rollback()
            logger.error(f"Migration failed: {str(e)}")
            raise

    @classmethod
    def rotate_encryption_key(cls, session, new_key: str, batch_size: int = 100,
                            dry_run: bool = False) -> Dict[str, Any]:
        """
        Rotate encryption key with detailed progress tracking and validation.

        Args:
            session: SQLAlchemy session
            new_key (str): New encryption key
            batch_size (int): Number of records per batch
            dry_run (bool): Simulate rotation without changes

        Returns:
            dict: Rotation statistics and results

        Raises:
            ValueError: If rotation fails
        """
        if not cls.__encryption_key__:
            raise ValueError("No current encryption key set")

        stats = {
            'total': 0,
            'processed': 0,
            'rotated': 0,
            'skipped': 0,
            'errors': [],
            'start_time': datetime.utcnow(),
            'end_time': None
        }

        try:
            # Set new key
            if not dry_run:
                new_version = cls.__key_version__ + 1
                cls.set_encryption_key(new_key, new_version)

            stats['total'] = session.query(cls).count()
            processed = 0

            while processed < stats['total']:
                batch = session.query(cls).offset(processed).limit(batch_size).all()

                for instance in batch:
                    stats['processed'] += 1

                    try:
                        for field in cls.__encrypted_fields__:
                            encrypted_value = getattr(instance, f"{field}_encrypted")
                            if encrypted_value is not None:
                                if not dry_run:
                                    # Re-encrypt using current value
                                    current_value = getattr(instance, field)
                                    setattr(instance, field, current_value)

                                    # Update metadata
                                    instance.__key_version = new_version
                                    instance.__last_rotated__ = datetime.utcnow()

                                stats['rotated'] += 1
                            else:
                                stats['skipped'] += 1

                    except Exception as e:
                        error = {
                            'instance_id': instance.id,
                            'error': str(e)
                        }
                        stats['errors'].append(error)
                        logger.error(f"Rotation error: {error}")

                if not dry_run:
                    session.commit()
                processed += len(batch)

                # Progress logging
                progress = (processed / stats['total']) * 100
                logger.info(f"Key rotation progress: {progress:.1f}% complete")

            stats['end_time'] = datetime.utcnow()
            duration = stats['end_time'] - stats['start_time']
            logger.info(f"Key rotation completed in {duration}")

            return stats

        except Exception as e:
            session.rollback()
            logger.error(f"Key rotation failed: {str(e)}")
            raise

    @staticmethod
    def encrypted_field(field_type: TypeEngine, **kwargs) -> Callable:
        """
        Enhanced decorator to mark a field as encrypted with extended options.

        Args:
            field_type: The SQLAlchemy field type
            **kwargs: Additional field configuration options including:
                - index: Enable indexing on encrypted field
                - unique: Enable unique constraint
                - nullable: Allow null values
                - default: Default value
                - onupdate: Update trigger
                - validate: Custom validation function

        Returns:
            function: Field setup function

        Example:
            @EncryptionMixin.encrypted_field(Text,
                index=True,
                validate=lambda x: len(x) > 8
            )
            def password(self):
                pass
        """
        def wrapper(func):
            @declared_attr
            def wrapped(cls):
                field_name = func.__name__

                # Add to encrypted fields list
                if field_name not in cls.__encrypted_fields__:
                    cls.__encrypted_fields__.append(field_name)

                # Add validation if specified
                validate_func = kwargs.pop('validate', None)
                if validate_func:
                    event.listen(
                        cls,
                        'before_insert',
                        lambda target, value, oldvalue, initiator: \
                            validate_func(getattr(target, field_name))
                    )

                return Column(field_type, **kwargs)
            return wrapped
        return wrapper


# Example usage with advanced features:
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from mixins.encryption_mixin import EncryptionMixin

class User(EncryptionMixin, Model):
    __tablename__ = 'nx_users'

    # Configure encryption options
    __compression__ = True
    __error_handling__ = 'lenient'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)

    @EncryptionMixin.encrypted_field(Text, nullable=False,
                                   validate=lambda x: '@' in x)
    def email(self):
        pass

    @EncryptionMixin.encrypted_field(String(100), index=True)
    def social_security_number(self):
        pass

    @EncryptionMixin.encrypted_field(JSONB)
    def sensitive_data(self):
        pass

# Application setup
app.config['ENCRYPTION_KEY'] = 'your-secure-encryption-key'
User.set_encryption_key(
    app.config['ENCRYPTION_KEY'],
    derivation='argon2'
)

# Usage examples
user = User(
    username="john_doe",
    email="john@example.com",
    social_security_number="123-45-6789",
    sensitive_data={"key": "value"}
)
db.session.add(user)
db.session.commit()

# Data retrieval
user = User.query.filter_by(username="john_doe").first()
print(user.email)  # Automatically decrypted

# Batch operations
stats = User.migrate_unencrypted_data(
    db.session,
    batch_size=500,
    dry_run=True
)
print(f"Migration stats: {stats}")

# Key rotation
rotation_stats = User.rotate_encryption_key(
    db.session,
    'new-secure-encryption-key',
    batch_size=1000
)
print(f"Rotation stats: {rotation_stats}")
"""
