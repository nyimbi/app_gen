from __future__ import annotations

from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean, String, Integer, ForeignKey, Table, event
from sqlalchemy.orm import declared_attr, relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from sqlalchemy.ext.associationproxy import association_proxy

class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps to a model."""
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Mixin for adding soft delete functionality to a model."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    @hybrid_property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = func.now()

    def restore(self) -> None:
        self.deleted_at = None


class VersioningMixin:
    """Mixin for tracking changes to model instances over time."""
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'before_update')
        def bump_version(mapper, connection, target):
            target.version += 1


class TaggableMixin:
    """Mixin for adding tagging capabilities to a model."""
    @declared_attr
    def tags(cls) -> Mapped[List["Tag"]]:
        return relationship("Tag", secondary=f"{cls.__name__.lower()}_tags", back_populates="tagged_items")

    def add_tag(self, tag: str) -> None:
        from .models import Tag  # Avoid circular import
        tag_instance = Tag.query.filter_by(name=tag).first()
        if not tag_instance:
            tag_instance = Tag(name=tag)
        if tag_instance not in self.tags:
            self.tags.append(tag_instance)

    def remove_tag(self, tag: str) -> None:
        tag_instance = next((t for t in self.tags if t.name == tag), None)
        if tag_instance:
            self.tags.remove(tag_instance)

    def get_tags(self) -> List[str]:
        return [tag.name for tag in self.tags]


class CommentableMixin:
    """Mixin for allowing comments to be added to model instances."""
    @declared_attr
    def comments(cls) -> Mapped[List["Comment"]]:
        return relationship("Comment", back_populates="commentable")

    def add_comment(self, content: str, user_id: int) -> None:
        from .models import Comment  # Avoid circular import
        comment = Comment(content=content, user_id=user_id)
        self.comments.append(comment)

    def get_comments(self) -> List["Comment"]:
        return self.comments


class RatableMixin:
    """Mixin for adding rating functionality to models."""
    @declared_attr
    def ratings(cls) -> Mapped[List["Rating"]]:
        return relationship("Rating", back_populates="ratable")

    def add_rating(self, value: int, user_id: int) -> None:
        from .models import Rating  # Avoid circular import
        rating = Rating(value=value, user_id=user_id)
        self.ratings.append(rating)

    @hybrid_property
    def average_rating(self) -> float:
        if not self.ratings:
            return 0
        return sum(r.value for r in self.ratings) / len(self.ratings)


class OrderableMixin:
    """Mixin for allowing model instances to be ordered."""
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'before_insert')
        def set_order(mapper, connection, target):
            if target.order is None:
                max_order = connection.scalar(
                    select(func.max(cls.order)).select_from(cls)
                )
                target.order = (max_order or 0) + 1


class TreeMixin:
    """Mixin for implementing hierarchical structures."""
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('%(class)s.id'), nullable=True)
    children: Mapped[List["TreeMixin"]] = relationship("TreeMixin", back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped[Optional["TreeMixin"]] = relationship("TreeMixin", back_populates="children", remote_side="TreeMixin.id")


class SearchableMixin:
    """Mixin for enhancing full-text search capabilities."""
    search_vector: Mapped[Any] = mapped_column(TSVectorType('name', 'description'))  # Adjust fields as needed

    @classmethod
    def search(cls, query: str) -> List[Any]:
        return cls.query.filter(cls.search_vector.match(query)).all()


class CacheMixin:
    """Mixin for implementing caching strategies on model queries."""
    @classmethod
    def get_or_cache(cls, id: int) -> Any:
        key = f"{cls.__name__}:{id}"
        instance = cache.get(key)
        if instance is None:
            instance = cls.query.get(id)
            if instance:
                cache.set(key, instance)
        return instance


class StateMachineMixin:
    """Mixin for implementing state machine behavior."""
    state: Mapped[str] = mapped_column(String(50), nullable=False)

    def change_state(self, new_state: str) -> None:
        if new_state in self.valid_states():
            self.state = new_state
        else:
            raise ValueError(f"Invalid state: {new_state}")

    @classmethod
    def valid_states(cls) -> List[str]:
        raise NotImplementedError("Subclasses must implement valid_states()")


class EncryptionMixin:
    """Mixin for handling encryption and decryption of sensitive model fields."""
    @declared_attr
    def encrypted_fields(cls):
        return []

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'before_insert')
        @event.listens_for(cls, 'before_update')
        def encrypt_fields(mapper, connection, target):
            for field in target.encrypted_fields:
                value = getattr(target, field)
                if value is not None:
                    setattr(target, field, encrypt(value))

        @event.listens_for(cls, 'after_load')
        def decrypt_fields(target, context):
            for field in target.encrypted_fields:
                value = getattr(target, field)
                if value is not None:
                    setattr(target, field, decrypt(value))


class ValidationMixin:
    """Mixin for adding custom validation rules to models."""
    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'before_insert')
        @event.listens_for(cls, 'before_update')
        def validate(mapper, connection, target):
            target.perform_validation()

    def perform_validation(self):
        raise NotImplementedError("Subclasses must implement perform_validation()")


class ExportableMixin:
    """Mixin for adding export functionality to models."""
    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def to_csv(cls, instances: List[Any]) -> str:
        if not instances:
            return ""
        headers = [c.name for c in instances[0].__table__.columns]
        csv_data = ",".join(headers) + "\n"
        for instance in instances:
            csv_data += ",".join(str(getattr(instance, h)) for h in headers) + "\n"
        return csv_data


class ImportableMixin:
    """Mixin for handling importing data from various formats into models."""
    @classmethod
    def from_dict(cls, data: dict) -> Any:
        return cls(**data)

    @classmethod
    def from_csv(cls, csv_data: str) -> List[Any]:
        lines = csv_data.strip().split("\n")
        headers = lines[0].split(",")
        return [cls(**dict(zip(headers, line.split(",")))) for line in lines[1:]]


class AuditLogMixin:
    """Mixin for detailed tracking of all changes made to model instances."""
    @declared_attr
    def audit_logs(cls) -> Mapped[List["AuditLog"]]:
        return relationship("AuditLog", back_populates="audited_object")

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'after_update')
        def log_update(mapper, connection, target):
            AuditLog.create_log(target, 'update')

        @event.listens_for(cls, 'after_delete')
        def log_delete(mapper, connection, target):
            AuditLog.create_log(target, 'delete')


class PermissionMixin:
    """Mixin for handling fine-grained permissions on model instances."""
    @declared_attr
    def permissions(cls) -> Mapped[List["Permission"]]:
        return relationship("Permission", back_populates="permissioned_object")

    def has_permission(self, user: Any, permission_type: str) -> bool:
        return any(p.user_id == user.id and p.permission_type == permission_type for p in self.permissions)

    def grant_permission(self, user: Any, permission_type: str) -> None:
        from .models import Permission  # Avoid circular import
        if not self.has_permission(user, permission_type):
            permission = Permission(user_id=user.id, permission_type=permission_type)
            self.permissions.append(permission)


class LocalizationMixin:
    """Mixin for handling multi-language content in models."""
    @declared_attr
    def translations(cls) -> Mapped[List["Translation"]]:
        return relationship("Translation", back_populates="translated_object")

    def set_translation(self, field: str, language: str, value: str) -> None:
        from .models import Translation  # Avoid circular import
        translation = next((t for t in self.translations if t.field == field and t.language == language), None)
        if translation:
            translation.value = value
        else:
            translation = Translation(field=field, language=language, value=value)
            self.translations.append(translation)

    def get_translation(self, field: str, language: str) -> Optional[str]:
        translation = next((t for t in self.translations if t.field == field and t.language == language), None)
        return translation.value if translation else None


class MetadataMixin:
    """Mixin for allowing arbitrary metadata to be attached to model instances."""
    @declared_attr
    def metadata_items(cls) -> Mapped[List["Metadata"]]:
        return relationship("Metadata", back_populates="metadata_object")

    def set_metadata(self, key: str, value: Any) -> None:
        from .models import Metadata  # Avoid circular import
        metadata = next((m for m in self.metadata_items if m.key == key), None)
        if metadata:
            metadata.value = value
        else:
            metadata = Metadata(key=key, value=value)
            self.metadata_items.append(metadata)

    def get_metadata(self, key: str) -> Optional[Any]:
        metadata = next((m for m in self.metadata_items if m.key == key), None)
        return metadata.value if metadata else None


class AttachmentMixin:
    """Mixin for handling file attachments on model instances."""
    @declared_attr
    def attachments(cls) -> Mapped[List["Attachment"]]:
        return relationship("Attachment", back_populates="attached_to")

    def add_attachment(self, filename: str, file_path: str) -> None:
        from .models import Attachment  # Avoid circular import
        attachment = Attachment(filename=filename, file_path=file_path)
        self.attachments.append(attachment)

    def get_attachments(self) -> List["Attachment"]:
        return self.attachments

# Note: The following models would typically be defined in a separate file (e.g., models.py)

class Tag:
    __tablename__ = 'tags'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    tagged_items = association_proxy('taggings', 'tagged_item')

class Comment:
    __tablename__ = 'comments'
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    commentable_id: Mapped[int] = mapped_column(Integer, nullable=False)
    commentable_type: Mapped[str] = mapped_column(String(50), nullable=False)

class Rating:
    