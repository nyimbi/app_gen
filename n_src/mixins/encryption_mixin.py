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

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder.models.mixins import AuditMixin
from sqlalchemy import event, Column, LargeBinary, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import flag_modified
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import base64
import json
from functools import partial

class EncryptionMixin(AuditMixin):
    """
    A mixin class for adding field-level encryption to SQLAlchemy models.

    This mixin provides automatic encryption and decryption of specified fields,
    key management, and utilities for data migration and key rotation.

    Class Attributes:
        __encrypted_fields__ (list): List of field names to be encrypted.
        __encryption_key__ (bytes): The encryption key used for Fernet.
    """

    __encrypted_fields__ = []  # List of fields to be encrypted
    __encryption_key__ = None  # Encryption key

    @classmethod
    def __declare_last__(cls):
        """Set up event listeners for encryption and decryption."""
        for field in cls.__encrypted_fields__:
            setattr(cls, f'{field}_encrypted', Column(LargeBinary))
            event.listen(getattr(cls, field), 'set', cls.encrypt_field)
            event.listen(getattr(cls, field), 'get', cls.decrypt_field)

    @classmethod
    def set_encryption_key(cls, key):
        """
        Set the encryption key for the model.

        Args:
            key (str): The encryption key.
        """
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        cls.__encryption_key__ = base64.urlsafe_b64encode(kdf.derive(key.encode()))

    @classmethod
    def encrypt_field(cls, target, value, oldvalue, initiator):
        """
        Encrypt a field value.

        Args:
            target: The model instance.
            value: The value to encrypt.
            oldvalue: The previous value.
            initiator: The initiator of the change.

        Returns:
            str: The encrypted value.
        """
        if value is None:
            return None
        if cls.__encryption_key__ is None:
            raise ValueError("Encryption key not set. Call set_encryption_key() first.")
        f = Fernet(cls.__encryption_key__)
        encrypted_value = f.encrypt(json.dumps(value).encode())
        setattr(target, f'{initiator.key}_encrypted', encrypted_value)
        flag_modified(target, f'{initiator.key}_encrypted')
        return value

    @classmethod
    def decrypt_field(cls, target, value, initiator):
        """
        Decrypt a field value.

        Args:
            target: The model instance.
            value: The value to decrypt.
            initiator: The initiator of the change.

        Returns:
            The decrypted value.
        """
        encrypted_value = getattr(target, f'{initiator.key}_encrypted')
        if encrypted_value is None:
            return None
        if cls.__encryption_key__ is None:
            raise ValueError("Encryption key not set. Call set_encryption_key() first.")
        f = Fernet(cls.__encryption_key__)
        decrypted_value = f.decrypt(encrypted_value)
        return json.loads(decrypted_value.decode())

    @classmethod
    def migrate_unencrypted_data(cls, session):
        """
        Migrate unencrypted data to encrypted format.

        Args:
            session: SQLAlchemy session.
        """
        for instance in session.query(cls).all():
            for field in cls.__encrypted_fields__:
                if getattr(instance, f'{field}_encrypted') is None:
                    setattr(instance, field, getattr(instance, field))
            session.commit()

    @classmethod
    def rotate_encryption_key(cls, session, new_key):
        """
        Rotate the encryption key and re-encrypt all data.

        Args:
            session: SQLAlchemy session.
            new_key (str): The new encryption key.
        """
        old_key = cls.__encryption_key__
        cls.set_encryption_key(new_key)
        for instance in session.query(cls).all():
            for field in cls.__encrypted_fields__:
                encrypted_value = getattr(instance, f'{field}_encrypted')
                if encrypted_value is not None:
                    f_old = Fernet(old_key)
                    f_new = Fernet(cls.__encryption_key__)
                    decrypted_value = f_old.decrypt(encrypted_value)
                    new_encrypted_value = f_new.encrypt(decrypted_value)
                    setattr(instance, f'{field}_encrypted', new_encrypted_value)
                    flag_modified(instance, f'{field}_encrypted')
        session.commit()

    @staticmethod
    def encrypted_field(field_type):
        """
        Decorator to mark a field as encrypted.

        Args:
            field_type: The SQLAlchemy field type.

        Returns:
            function: A function that sets up the encrypted field.
        """
        def wrapper(func):
            @declared_attr
            def wrapped(cls):
                field_name = func.__name__
                if field_name not in cls.__encrypted_fields__:
                    cls.__encrypted_fields__.append(field_name)
                return Column(field_type)
            return wrapped
        return wrapper

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.encryption_mixin import EncryptionMixin

class User(EncryptionMixin, Model):
    __tablename__ = 'nx_users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)

    @EncryptionMixin.encrypted_field(String(100))
    def email(self):
        pass

    @EncryptionMixin.encrypted_field(String(100))
    def social_security_number(self):
        pass

# In your application initialization:
User.set_encryption_key('your-secure-encryption-key')

# In your application code:
user = User(username="john_doe", email="john@example.com", social_security_number="123-45-6789")
db.session.add(user)
db.session.commit()

# Retrieving the user
retrieved_user = User.query.filter_by(username="john_doe").first()
print(retrieved_user.email)  # Automatically decrypted

# Migrating unencrypted data
User.migrate_unencrypted_data(db.session)

# Rotating encryption key
User.rotate_encryption_key(db.session, 'new-secure-encryption-key')
"""
