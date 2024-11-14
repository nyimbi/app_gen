class Rating:
    __tablename__ = 'ratings'
    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    ratable_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ratable_type: Mapped[str] = mapped_column(String(50), nullable=False)

class AuditLog:
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    object_id: Mapped[int] = mapped_column(Integer, nullable=False)
    object_type: Mapped[str] = mapped_column(String(50), nullable=False)

    @classmethod
    def create_log(cls, target: Any, action: str) -> None:
        log = cls(action=action, object_id=target.id, object_type=target.__class__.__name__)
        db.session.add(log)
        db.session.commit()

class Permission:
    __tablename__ = 'permissions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    permission_type: Mapped[str] = mapped_column(String(50), nullable=False)
    permissioned_id: Mapped[int] = mapped_column(Integer, nullable=False)
    permissioned_type: Mapped[str] = mapped_column(String(50), nullable=False)

class Translation:
    __tablename__ = 'translations'
    id: Mapped[int] = mapped_column(primary_key=True)
    field: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    translated_id: Mapped[int] = mapped_column(Integer, nullable=False)
    translated_type: Mapped[str] = mapped_column(String(50), nullable=False)

class Metadata:
    __tablename__ = 'metadata'
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_object_id: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_object_type: Mapped[str] = mapped_column(String(50), nullable=False)

class Attachment:
    __tablename__ = 'attachments'
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    attached_to_id: Mapped[int] = mapped_column(Integer, nullable=False)
    attached_to_type: Mapped[str] = mapped_column(String(50), nullable=False)

# Usage examples

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(TimestampMixin, Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

class Post(TimestampMixin, SoftDeleteMixin, TaggableMixin, CommentableMixin, RatableMixin, SearchableMixin, Base):
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    author: Mapped[User] = relationship(User, back_populates="posts")

class Category(TreeMixin, OrderableMixin, Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

class Product(VersioningMixin, LocalizationMixin, MetadataMixin, AttachmentMixin, Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    def perform_validation(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")

class SensitiveData(EncryptionMixin, Base):
    __tablename__ = 'sensitive_data'
    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_fields = ['data']

# Example usage

def create_post(db_session, user, title, content):
    post = Post(title=title, content=content, author=user)
    post.add_tag("example")
    post.add_comment("This is a comment", user.id)
    post.add_rating(5, user.id)
    db_session.add(post)
    db_session.commit()
    return post

def create_product(db_session, name, price):
    product = Product(name=name, price=price)
    product.set_translation("name", "es", "Nombre en español")
    product.set_metadata("color", "red")
    product.add_attachment("manual.pdf", "/path/to/manual.pdf")
    db_session.add(product)
    db_session.commit()
    return product

# Note: In a real application, you would need to set up the SQLAlchemy engine,
# create a session, and handle database connections appropriately.
