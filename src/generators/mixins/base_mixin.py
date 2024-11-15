import io
import sys
import json
import humanize
import pandas as pd
from flask import g, Markup
from markupsafe import escape
from datetime import datetime
from typing import List, Dict, Any, Tuple, Type

# Work across both SQLAlchemy 1.x and 2.0
try:
    # SQLAlchemy 2.0
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
    from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, inspect, event, Text
    from sqlalchemy.sql import func
    SQLALCHEMY_2 = True
except ImportError:
    # SQLAlchemy 1.x
    from sqlalchemy.ext.declarative import declared_attr
    from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, inspect, event, Text
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    SQLALCHEMY_2 = False

from sqlalchemy.orm import declarative_base, class_mapper
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import sqltypes
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy

class BaseModelMixin:
    """
    A mixin class that provides functionality for managing view steps in SQLAlchemy models.

    This mixin automatically creates a related table for storing view step information,
    and provides methods for managing and querying these view steps.
    A mixin class that provides extended functionality for SQLAlchemy models,
    including data export and import capabilities.

    Mixin for models, adds 4 columns to stamp,
    time and user on creation and modification
    will create the following columns:

    :created on:
    :changed on:
    :created by:
    :changed by:

    :is_deleted:
    :deleted_at:
    :version:
    """

    """Audit Fields and Functionality"""

    if SQLALCHEMY_2:
        # id: Mapped[int] = mapped_column(primary_key=True)
        created_on: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), nullable=True)
        changed_on: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), onupdate=datetime.now(), nullable=True)
        """Soft Delete Functionality"""
        is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
        deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
        """Versioning Functionality"""
        # Versioning Columns
        version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
        completion_percentage: Mapped[integer] = mapped_column(Integer, default=0)
        unfilled_columns: Mapped[string] = mapped_column(Text)  # Store as JSON string
        track_completion: Mapped[boolean] = mapped_column(Boolean, default=True)
    else:
        # id = Column(Integer, primary_key=True)
        created_on = Column(DateTime, default=lambda: datetime.now(), nullable=True)
        changed_on = Column(DateTime, default=lambda: datetime.now(), onupdate=datetime.now(), nullable=True)
        """Soft Delete Functionality"""
        is_deleted = Column(Boolean, default=False)
        deleted_at = Column(DateTime, nullable=True)
        """Versioning Functionality"""
        # Versioning Columns
        version = Column(Integer, default=1, nullable=False)
        completion_percentage = Column(Integer, default=0)
        unfilled_columns = Column(Text)  # Store as JSON string
        track_completion = Column(Boolean, default=True)

    _columns_per_step: int = 5

    @declared_attr
    def created_by_fk(cls):
        if SQLALCHEMY_2:
            return mapped_column(Integer, ForeignKey("ab_user.id"), default=cls.get_user_id, nullable=True)
        else:
            return Column(Integer, ForeignKey("ab_user.id"), default=cls.get_user_id, nullable=True)

    @declared_attr
    def changed_by_fk(cls):
        if SQLALCHEMY_2:
            return mapped_column(Integer, ForeignKey("ab_user.id"), default=cls.get_user_id, onupdate=cls.get_user_id, nullable=True)
        else:
            return Column(Integer, ForeignKey("ab_user.id"), default=cls.get_user_id, onupdate=cls.get_user_id, nullable=True)

    @declared_attr
    def created_by(cls):
        return relationship(
            "User",
            foreign_keys=[cls.created_by_fk],
            backref=backref("created", uselist=True),
            remote_side="User.id",
            primaryjoin="User.id == %s.created_by_fk" % cls.__name__,
            uselist=False,
        )

    @declared_attr
    def changed_by(cls):
        return relationship(
            "User",
            foreign_keys=[cls.changed_by_fk],
            backref=backref("changed", uselist=True),
            remote_side="User.id",
            primaryjoin="User.id == %s.changed_by_fk" % cls.__name__,
            uselist=False,
        )

    @staticmethod
    def get_user_id():
        try:
            if hasattr(g, 'user') and g.user:
                return g.user.id
        except Exception:
            return None

    @staticmethod
    def get_current_user():
        if hasattr(g, 'user') and g.user:
            return f.user.id
        return None

    def _user_representation(self, user) -> str:
        if not user:
            return ""
        return f"{user.first_name} {user.last_name} ({user.username})"

    @property
    def creator(self) -> str:
        return self._user_representation(self.created_by)

    @property
    def modifier(self) -> str:
        return self._user_representation(self.changed_by)

    @property
    def changed_on_formatted(self) -> Markup:
        return Markup(f'<span class="no-wrap">{self.changed_on}</span>')

    @property
    def modified_relative(self) -> Markup:
        s = humanize.naturaltime(datetime.now() - self.changed_on)
        return Markup(f'<span class="no-wrap">{s}</span>')




    # Incase you want to use HTML returns
    # def _user_link(self, user) -> str:
    #     if not user:
    #         return ""
    #     full_name = f"{user.first_name} {user.last_name}"
    #     url = f"/prn/profile/{user.username}/"
    #     return Markup(f'<a href="{url}">{escape(full_name)} ({escape(user.username)})</a>')

    # @property
    # def creator(self) -> str:
    #     return self._user_link(self.created_by)

    # @property
    # def modifier(self) -> str:
    #     return self._user_link(self.changed_by)

    # @property
    # def changed_on_formatted(self) -> Markup:
    #     return Markup(f'<span class="no-wrap">{self.changed_on}</span>')




    """Soft Delete Functionality"""
    def soft_delete(self) -> None:
        self.deleted_at = func.now()
        self.is_deleted = True

    def restore(self) -> None:
        self.deleted_at = None
        self.is_deleted = False

    @classmethod
    def get_active(cls):
        """
        Returns a query that filters out soft-deleted records.
        """
        return cls.query.filter_by(is_deleted=False)

    def update_completion_status(self):
        """
        Updates the completion percentage and list of unfilled columns.
        """
        mapper = class_mapper(self.__class__)
        total_columns = len([c for c in mapper.columns if not c.primary_key and c.key not in [
            'created_by_fk',
            'changed_by_fk',
            'version',
            'completion_percentage',
            'unfilled_columns']])
        filled_columns = sum(
            1 for c in mapper.columns
            if not c.primary_key and c.key not in ['created_by_id', 'changed_by_fk', 'version', 'completion_percentage', 'unfilled_columns']
            and getattr(self, c.key) is not None
        )

        self.completion_percentage = int((filled_columns / total_columns) * 100)

        unfilled = [
            c.key for c in mapper.columns
            if not c.primary_key and c.key not in ['created_by_id', 'changed_by_fk', 'version', 'completion_percentage', 'unfilled_columns']
            and getattr(self, c.key) is None
        ]
        self.unfilled_columns = json.dumps(unfilled)

    @classmethod
    def prompt_incomplete_forms(cls, session):
        """
        Retrieves incomplete forms for prompting users who are currently logged in.

        Returns:
            List of tuples: Each tuple contains (form, user) where form is an incomplete form
                            and user is the User object who created the form.
        """
        if not current_user or current_user.is_anonymous:
            return []

        incomplete_forms = (
            session.query(cls, cls.created_by)
            .join(cls.created_by)
            .filter(cls.completion_percentage < 100)
            .filter(cls.created_by_id == current_user.id)
            .all()
        )



    @classmethod
    def __init_subclass__(cls):
        """
        Initializes the subclass by creating the view step table and setting up event listeners.

        This method is called automatically when a class inherits from BaseModelMixin.
        """
        super().__init_subclass__()
        cls.create_view_step_table()

        @event.listens_for(cls, "mapper_configured")
        def receive_mapper_configured(mapper, class_):
            cls.auto_assign_columns_to_steps()

        @event.listens_for(cls, "before_insert")
        def set_created_by(mapper, connection, target):
            target.created_by = cls.get_current_user()
            target.update_completion_status()

        @event.listens_for(cls, "before_update")
        def set_updated_by(mapper, connection, target):
            target.updated_by = cls.get_current_user()
            target.update_completion_status()
            target.version += 1



    """
    View Management Functionality
    The default number of columns to include in each view step."""



    @classmethod
    def create_view_step_table(cls):
        """
        Creates a dedicated table for storing view step information for the inheriting model.

        This method is called automatically during class initialization.
        """
        table_name = f"nx_{cls.__tablename__}_view_steps"

        class ViewStep(Base):
            @declared_attr
            def __tablename__(cls):
                return cls.table_name

            if SQLALCHEMY_2:
                id: Mapped[int] = mapped_column(Integer, primary_key=True)
                step_name: Mapped[str] = mapped_column(String(100), nullable=False)
                column_name: Mapped[str] = mapped_column(String(100), nullable=False)
                order: Mapped[int] = mapped_column(Integer, nullable=False)
            else:
                id = Column(Integer, primary_key=True)
                step_name = Column(String(100), nullable=False)
                column_name = Column(String(100), nullable=False)
                order = Column(Integer, nullable=False)

            @declared_attr
            def __table_args__(cls):
                return (
                    UniqueConstraint("step_name", "column_name", name=f"uix_{cls.table_name}"),
                )

        cls.ViewStep = ViewStep

        @declared_attr
        def view_steps(cls):
            return relationship(
                ViewStep, backref=cls.__tablename__, cascade="all, delete-orphan"
            )

        cls.view_steps = view_steps

    @classmethod
    def set_columns_per_step(cls, count: int):
        """
        Sets the number of columns per view step and reassigns columns to steps.

        Args:
            count (int): The new number of columns per step.
        """
        cls._columns_per_step = count
        cls.auto_assign_columns_to_steps()

    @classmethod
    def get_columns_per_step(cls) -> int:
        """
        Returns the current number of columns per view step.

        Returns:
            int: The number of columns per step.
        """
        return cls._columns_per_step

    @classmethod
    def define_view_step(cls, step_name: str, columns: List[str]) -> None:
        """
        Defines a view step with the given name and columns.

        If a step with the same name already exists, it updates the existing step.

        Args:
            step_name (str): The name of the view step.
            columns (List[str]): A list of column names to include in this step.
        """
        for idx, column in enumerate(columns):
            existing_step = next(
                (
                    vs
                    for vs in cls.view_steps
                    if vs.step_name == step_name and vs.column_name == column
                ),
                None,
            )
            if existing_step:
                existing_step.order = idx
            else:
                step = cls.ViewStep(step_name=step_name, column_name=column, order=idx)
                cls.view_steps.append(step)

    @classmethod
    def get_view_step(cls, step_name: str) -> List[str]:
        """
        Retrieves the list of column names for a specific view step.

        Args:
            step_name (str): The name of the view step.

        Returns:
            List[str]: A list of column names in the specified view step.
        """
        return [vs.column_name for vs in cls.view_steps if vs.step_name == step_name]

    @classmethod
    def get_all_view_steps(cls) -> Dict[str, List[str]]:
        """
        Retrieves all view steps and their associated columns.

        Returns:
            Dict[str, List[str]]: A dictionary where keys are step names and values are lists of column names.
        """
        steps = {}
        for vs in cls.view_steps:
            if vs.step_name not in steps:
                steps[vs.step_name] = []
            steps[vs.step_name].append(vs.column_name)
        return steps

    @classmethod
    def get_view_step_count(cls) -> int:
        """
        Returns the total number of view steps.

        Returns:
            int: The number of distinct view steps.
        """
        return len(set(vs.step_name for vs in cls.view_steps))

    @classmethod
    def column_in_step(cls, column_name: str, step_name: str) -> bool:
        """
        Checks if a specific column is part of a given view step.

        Args:
            column_name (str): The name of the column to check.
            step_name (str): The name of the view step to check.

        Returns:
            bool: True if the column is in the specified step, False otherwise.
        """
        return any(
            vs.column_name == column_name and vs.step_name == step_name
            for vs in cls.view_steps
        )

    @classmethod
    def get_column_step(cls, column_name: str) -> str:
        """
        Retrieves the step name for a given column.

        Args:
            column_name (str): The name of the column to look up.

        Returns:
            str: The name of the step containing the column, or None if not found.
        """
        for vs in cls.view_steps:
            if vs.column_name == column_name:
                return vs.step_name
        return None

    @classmethod
    def get_steps_for_columns(cls, columns: List[str]) -> Dict[str, List[str]]:
        """
        Retrieves the view steps that contain the specified columns.

        Args:
            columns (List[str]): A list of column names to look up.

        Returns:
            Dict[str, List[str]]: A dictionary where keys are step names and values are lists of matching column names.
        """
        steps = {}
        for vs in cls.view_steps:
            if vs.column_name in columns:
                if vs.step_name not in steps:
                    steps[vs.step_name] = []
                steps[vs.step_name].append(vs.column_name)
        return steps

    @classmethod
    def auto_assign_columns_to_steps(cls):
        """
        Automatically assigns columns to view steps based on the current columns_per_step setting.

        This method is called automatically during model initialization and when changing columns_per_step.
        """
        columns = cls.model_columns()
        pk_columns = [key.name for key in inspect(cls).primary_key]
        fk_columns = [
            column.name for column in cls.__table__.columns if column.foreign_keys
        ]

        # Clear existing view steps
        cls.view_steps = []

        # Assign primary and foreign key columns to steps 1 and 2
        step1_columns = (
            pk_columns + fk_columns[: cls._columns_per_step - len(pk_columns)]
        )
        step2_columns = (
            fk_columns[cls._columns_per_step - len(pk_columns) :]
            if len(fk_columns) > cls._columns_per_step - len(pk_columns)
            else []
        )

        cls.define_view_step("Step 1", step1_columns)
        if step2_columns:
            cls.define_view_step("Step 2", step2_columns)

        # Assign remaining columns to steps
        remaining_columns = [
            col for col in columns if col not in pk_columns and col not in fk_columns
        ]
        for i, column in enumerate(remaining_columns):
            step_number = (i // cls._columns_per_step) + (3 if step2_columns else 2)
            step_name = f"Step {step_number}"
            if not cls.column_in_step(column, step_name):
                cls.define_view_step(step_name, [column])

    @classmethod
    def model_columns(cls) -> List[str]:
        """
        Retrieves a list of all column names for the model.

        Returns:
            List[str]: A list of column names.
        """
        return [c.key for c in inspect(cls).mapper.column_attrs]

    @classmethod
    def mixin_columns(cls) -> List[str]:
        """
        Retrieves a list of column names defined in the mixin.

        Returns:
            List[str]: A list of column names defined in the mixin.
        """
        return [
            name
            for name, value in vars(cls).items()
            if isinstance(value, InstrumentedAttribute)
        ]

    @classmethod
    def mixin_methods(cls) -> List[str]:
        """
        Retrieves a list of method names defined in the mixin.

        Returns:
            List[str]: A list of method names defined in the mixin.
        """
        return [
            method
            for method in dir(cls)
            if callable(getattr(cls, method)) and not method.startswith("__")
        ]

    @classmethod
    def column_details(cls) -> List[Tuple[str, Any]]:
        """
        Retrieves detailed information about each column in the model.

        Returns:
            List[Tuple[str, Any]]: A list of tuples containing column names and their SQLAlchemy types.
        """
        return [(c.key, c.type) for c in inspect(cls).mapper.column_attrs]

    @classmethod
    def column_count(cls) -> int:
        """
        Returns the total number of columns in the model.

        Returns:
            int: The number of columns.
        """
        return len(cls.model_columns())

    """MODEL Shape Persisitence"""
    # Model Shape

    @classmethod
    def shape_to_dict(cls) -> Dict[str, Any]:
        """
        Creates a comprehensive dictionary representation of the model's structure and characteristics.
        This enhanced version of shape_to_dict (and consequently, the other shape_to_* methods) now includes the following additional information:

        * Model and Table Names: The name of the model class and the associated database table.
        * Detailed Column Information: For each column, we now include:

            - Nullability
            - Default value
            - Whether it's a primary key
            - Foreign key information (if applicable)


        * Primary Key: A list of primary key column names.
        * Unique Constraints: Information about any unique constraints on the table.
        * Indexes: Details about indexes on the table, including whether they're unique.
        * Relationships: Information about SQLAlchemy relationships, including the target model, direction, and whether it's a collection.
        * Inheritance: A list of base classes the model inherits from (excluding object).
        * Table Arguments: Any additional table arguments defined in the model.
        * Estimated Row Size: A rough estimate of the size of a single row in bytes. This is calculated based on the column types and can
        be useful for capacity planning.
        * Python Type Sizes: The size of common Python types, which can be helpful for understanding memory usage in the application.

        Returns:
            Dict[str, Any]: A dictionary containing detailed information about the model.
        """
        mapper = class_mapper(cls)
        inspector = inspect(cls)

        return {
            "model_name": cls.__name__,
            "table_name": cls.__tablename__,
            "columns": cls.model_columns(),
            "column_details": [
                {
                    "name": name,
                    "type": str(type),
                    "nullable": getattr(column, 'nullable', None),
                    "default": str(getattr(column, 'default', None)),
                    "primary_key": getattr(column, 'primary_key', False),
                    "foreign_key": str(list(column.foreign_keys)[0].target_fullname) if column.foreign_keys else None
                }
                for name, column, type in cls.column_details()
            ],
            "primary_key": [key.name for key in inspector.primary_key],
            "unique_constraints": [
                {
                    "name": constraint.name,
                    "columns": constraint.columns
                }
                for constraint in inspector.get_unique_constraints()
            ],
            "indexes": [
                {
                    "name": index.name,
                    "columns": index.columns,
                    "unique": index.unique
                }
                for index in inspector.get_indexes()
            ],
            "relationships": [
                {
                    "name": rel.key,
                    "target": rel.target.name,
                    "direction": rel.direction.name,
                    "uselist": rel.uselist
                }
                for rel in mapper.relationships
            ],
            "mixin_columns": cls.mixin_columns(),
            "mixin_methods": cls.mixin_methods(),
            "column_count": cls.column_count(),
            "view_steps": cls.get_all_view_steps(),
            "columns_per_step": cls.get_columns_per_step(),
            "view_step_count": cls.get_view_step_count(),
            "inheritance": [base.__name__ for base in cls.__bases__ if base != object],
            "table_args": getattr(cls, '__table_args__', None),
            "estimated_row_size": cls.estimate_row_size(),
            "python_type_sizes": cls.get_python_type_sizes(),
        }

    @classmethod
    def estimate_row_size(cls) -> int:
        """
        Estimates the size of a single row in bytes.
        This is a rough estimate and may not be exact for all database backends.

        Returns:
            int: Estimated size of a single row in bytes.
        """
        size = 0
        for column in cls.__table__.columns:
            if isinstance(column.type, sqltypes.String):
                size += column.type.length or 255  # Default to 255 if length not specified
            elif isinstance(column.type, sqltypes.Integer):
                size += 4  # Assuming 32-bit integer
            elif isinstance(column.type, sqltypes.BigInteger):
                size += 8  # 64-bit integer
            elif isinstance(column.type, sqltypes.Float):
                size += 8  # Assuming 64-bit float
            elif isinstance(column.type, sqltypes.Boolean):
                size += 1
            elif isinstance(column.type, sqltypes.Date):
                size += 3  # Typically 3 bytes for a date
            elif isinstance(column.type, sqltypes.DateTime):
                size += 8  # Typically 8 bytes for a datetime
            else:
                size += 8  # Default to 8 bytes for unknown types
        return size

    @staticmethod
    def get_python_type_sizes() -> Dict[str, int]:
        """
        Returns the size of common Python types.

        Returns:
            Dict[str, int]: A dictionary of Python types and their sizes in bytes.
        """
        return {
            "int": sys.getsizeof(0),
            "float": sys.getsizeof(0.0),
            "bool": sys.getsizeof(True),
            "str (empty)": sys.getsizeof(""),
            "list (empty)": sys.getsizeof([]),
            "dict (empty)": sys.getsizeof({}),
            "datetime": sys.getsizeof(datetime.datetime.now()),
        }


    @classmethod
    def shape_to_json(cls, indent: int = 2) -> str:
        """
        Creates a JSON representation of the model's structure.

        Args:
            indent (int): The number of spaces to use for indentation in the JSON output.

        Returns:
            str: A JSON string representing the model's structure.
        """
        return json.dumps(cls.shape_to_dict(), indent=indent)

    @classmethod
    def shape_to_csv(cls) -> str:
        """
        Creates a CSV representation of the model's structure.

        Returns:
            str: A CSV string representing the model's structure.
        """
        shape_dict = cls.shape_to_dict()
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Category", "Name", "Value"])

        # Write data
        for category, value in shape_dict.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, tuple):
                        writer.writerow([category, item[0], item[1]])
                    else:
                        writer.writerow([category, item, ""])
            elif isinstance(value, dict):
                for key, val in value.items():
                    writer.writerow([category, key, ", ".join(val) if isinstance(val, list) else val])
            else:
                writer.writerow([category, "", value])

        return output.getvalue()

    @classmethod
    def shape_to_text(cls) -> str:
        """
        Creates a human-readable text representation of the model's structure.

        Returns:
            str: A formatted string representing the model's structure.
        """
        shape_dict = cls.shape_to_dict()
        output = []

        for category, value in shape_dict.items():
            output.append(f"{category.upper()}:")
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, tuple):
                        output.append(f"  {item[0]}: {item[1]}")
                    else:
                        output.append(f"  {item}")
            elif isinstance(value, dict):
                for key, val in value.items():
                    output.append(f"  {key}: {', '.join(val) if isinstance(val, list) else val}")
            else:
                output.append(f"  {value}")
            output.append("")  # Add an empty line between categories

        return "\n".join(output)




    """Data Export/Import"""
    # Data Export and Import Functionality

    @classmethod
    def to_dataframe(cls) -> pd.DataFrame:
        """
        Converts all records of the model to a pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing all records of the model.
        """
        query = cls.query.all()
        data = [record.to_dict() for record in query]
        return pd.DataFrame(data)

    @classmethod
    def export_to_csv(cls, filename: str) -> None:
        """
        Exports all records of the model to a CSV file.

        Args:
            filename (str): The name of the file to export to.
        """
        df = cls.to_dataframe()
        df.to_csv(filename, index=False)

    @classmethod
    def export_to_excel(cls, filename: str) -> None:
        """
        Exports all records of the model to an Excel file.

        Args:
            filename (str): The name of the file to export to.
        """
        df = cls.to_dataframe()
        df.to_excel(filename, index=False)

    @classmethod
    def export_to_json(cls, filename: str) -> None:
        """
        Exports all records of the model to a JSON file.

        Args:
            filename (str): The name of the file to export to.
        """
        df = cls.to_dataframe()
        df.to_json(filename, orient="records")

    @classmethod
    def import_from_csv(cls, filename: str, session) -> List[Any]:
        """
        Imports records from a CSV file and creates new model instances.

        Args:
            filename (str): The name of the file to import from.
            session: SQLAlchemy session object.

        Returns:
            List[Any]: A list of newly created model instances.
        """
        df = pd.read_csv(filename)
        return cls._import_from_dataframe(df, session)

    @classmethod
    def import_from_excel(cls, filename: str, session) -> List[Any]:
        """
        Imports records from an Excel file and creates new model instances.

        Args:
            filename (str): The name of the file to import from.
            session: SQLAlchemy session object.

        Returns:
            List[Any]: A list of newly created model instances.
        """
        df = pd.read_excel(filename)
        return cls._import_from_dataframe(df, session)

    @classmethod
    def import_from_json(cls, filename: str, session) -> List[Any]:
        """
        Imports records from a JSON file and creates new model instances.

        Args:
            filename (str): The name of the file to import from.
            session: SQLAlchemy session object.

        Returns:
            List[Any]: A list of newly created model instances.
        """
        df = pd.read_json(filename)
        return cls._import_from_dataframe(df, session)

    @classmethod
    def _import_from_dataframe(cls, df: pd.DataFrame, session) -> List[Any]:
        """
        Helper method to import records from a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing the records to import.
            session: SQLAlchemy session object.

        Returns:
            List[Any]: A list of newly created model instances.
        """
        instances = []
        for _, row in df.iterrows():
            instance = cls(**row.to_dict())
            session.add(instance)
            instances.append(instance)
        session.commit()
        return instances

    @classmethod
    def bulk_insert_from_csv(cls, filename: str, session) -> None:
        """
        Performs a bulk insert of records from a CSV file.

        Args:
            filename (str): The name of the file to import from.
            session: SQLAlchemy session object.
        """
        df = pd.read_csv(filename)
        cls._bulk_insert_from_dataframe(df, session)

    @classmethod
    def bulk_insert_from_excel(cls, filename: str, session) -> None:
        """
        Performs a bulk insert of records from an Excel file.

        Args:
            filename (str): The name of the file to import from.
            session: SQLAlchemy session object.
        """
        df = pd.read_excel(filename)
        cls._bulk_insert_from_dataframe(df, session)

    @classmethod
    def bulk_insert_from_json(cls, filename: str, session) -> None:
        """
        Performs a bulk insert of records from a JSON file.

        Args:
            filename (str): The name of the file to import from.
            session: SQLAlchemy session object.
        """
        df = pd.read_json(filename)
        cls._bulk_insert_from_dataframe(df, session)

    @classmethod
    def _bulk_insert_from_dataframe(cls, df: pd.DataFrame, session) -> None:
        """
        Helper method to perform a bulk insert from a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing the records to insert.
            session: SQLAlchemy session object.
        """
        data = df.to_dict(orient="records")
        session.bulk_insert_mappings(cls, data)
        session.commit()


    @classmethod
    def write_step_templates(cls, directory="templates"):
        """
        Generates and writes HTML templates for each view step.

        Args:
            directory (str): The directory where templates will be written. Defaults to "templates".
        """
        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)

        # Set up Jinja2 environment
        env = Environment(loader=FileSystemLoader(directory))

        # Get all view steps
        all_steps = cls.get_all_view_steps()

        # Base template
        base_template = """
        {% extends 'appbuilder/baselayout.html' %}
        {% import 'appbuilder/baselib.html' as baselib with context %}

        {% block content %}
        <h1>{{ class_name }} - Step {{ step_number }}</h1>
        <form id="stepForm" method="post">
            {% for column in columns %}
            <div class="form-group">
                <label for="{{ column }}">{{ column|capitalize }}</label>
                {{ field_macro(column) }}
            </div>
            {% endfor %}
            <button type="button" class="btn btn-secondary" id="backBtn">Back</button>
            <button type="button" class="btn btn-primary" id="nextBtn">Next</button>
            <button type="submit" class="btn btn-success" id="laterBtn" disabled>Submit Later</button>
        </form>

        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var form = document.getElementById('stepForm');
            var laterBtn = document.getElementById('laterBtn');

            form.addEventListener('change', function() {
                var requiredFields = form.querySelectorAll('[required]');
                var allFilled = Array.from(requiredFields).every(field => field.value);
                laterBtn.disabled = !allFilled;
            });

            // Add logic for Back and Next buttons here
        });
        </script>
        {% endblock %}
        """

        # Create a template for each step
        for step_number, columns in all_steps.items():
            template = env.from_string(base_template)
            content = template.render(
                class_name=cls.__name__,
                step_number=step_number,
                columns=columns,
                generate_field_macro=lambda col_name: cls.generate_field_macro(col_name, getattr(cls, col_name).property.columns[0])
            )

            # Write the template to a file
            filename = f"{cls.__name__}_{step_number}_view.html"
            with open(os.path.join(directory, filename), 'w') as f:
                f.write(content)

        print(f"Templates generated in {directory}")

    @staticmethod
    def generate_field_macro(column_name, column):
        """
        Generates the appropriate input field based on the column type.

        Args:
            column_name (str): The name of the column.
            column (Column): The SQLAlchemy column object.

        Returns:
            str: HTML markup for the input field.
        """
        column_type = type(column.type)
        nullable = ' required' if not column.nullable else ''

        if column_type in (String, Text):
            max_length = getattr(column.type, 'length', None)
            if max_length and max_length > 255:
                return f'<textarea class="form-control" id="{column_name}" name="{column_name}"{nullable}></textarea>'
            else:
                return f'<input type="text" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'

        elif column_type in (Integer, BigInteger):
            return f'<input type="number" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'

        elif column_type in (Float, Numeric):
            return f'<input type="number" step="any" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'

        elif column_type == DateTime:
            return f'<input type="datetime-local" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'

        elif column_type == Date:
            return f'<input type="date" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'

        elif column_type == Time:
            return f'<input type="time" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'

        elif column_type == Boolean:
            return f'<input type="checkbox" class="form-check-input" id="{column_name}" name="{column_name}">'

        elif column_type == Enum:
            options = [f'<option value="{enum_value}">{enum_value}</option>' for enum_value in column.type.enums]
            return f'<select class="form-control" id="{column_name}" name="{column_name}"{nullable}>' + ''.join(options) + '</select>'

        elif column_type in (PickleType, JSON, JSONB):
            return f'<textarea class="form-control" id="{column_name}" name="{column_name}"{nullable}></textarea>'

        elif column_type == ARRAY:
            return f'<input type="text" class="form-control" id="{column_name}" name="{column_name}" placeholder="Comma-separated values"{nullable}>'

        elif column_type == HSTORE:
            return f'<textarea class="form-control" id="{column_name}" name="{column_name}" placeholder="Key-value pairs, one per line"{nullable}></textarea>'

        elif column_type == UUID:
            return f'<input type="text" class="form-control" id="{column_name}" name="{column_name}" pattern="[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}"{nullable}>'

        elif column_type == LargeBinary:
            return f'<input type="file" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'

        # Additional types often used in Flask-AppBuilder
        elif hasattr(column.type, 'python_type'):
            if column.type.python_type == str and getattr(column.type, 'widget', None) == ColorInput:
                return f'<input type="color" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'
            elif column.type.python_type == str and getattr(column.type, 'widget', None) == URLInput:
                return f'<input type="url" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'

        # Default fallback
        return f'<input type="text" class="form-control" id="{column_name}" name="{column_name}"{nullable}>'

    @classmethod
    def generate_field_sets(cls):
        """
        Generates field sets for Flask-AppBuilder views based on the view steps.
        """
        all_steps = cls.get_all_view_steps()
        field_sets = []

        for step_number, columns in all_steps.items():
            field_set = {
                "label": f"Step {step_number}",
                "fields": columns
            }
            field_sets.append(field_set)

        return field_sets




# Note: This demonstration function should be called after setting up the SQLAlchemy engine and session
# Example usage remains the same
# class ExampleModel(BaseModelMixin, Base):
#     __tablename__ = 'nx_example_models'

#     id: Mapped[int] = mapped_column(primary_key=True)
#     name: Mapped[str] = mapped_column(String(100), nullable=False)
#     description: Mapped[str] = mapped_column(Text, nullable=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
#     parent_id: Mapped[int] = mapped_column(ForeignKey('nx_example_models.id'), nullable=True)

# # Demonstration function remains the same
# def demonstrate_auto_init_base_model_mixin():
#     print("Model Columns:", ExampleModel.model_columns())
#     print("View Steps Table Name:", ExampleModel.ViewStep.__tablename__)
#     print("View Steps:", ExampleModel.get_all_view_steps())
#     print("Columns in 'Step 1':", ExampleModel.get_view_step('Step 1'))
#     print("View Step Count:", ExampleModel.get_view_step_count())
#     print("Columns per Step:", ExampleModel.get_columns_per_step())
#     print("Model Structure:", ExampleModel.shape_to_text())

#     # Demonstrating dynamic update
#     ExampleModel.set_columns_per_step(2)
#     print("\nAfter changing columns per step to 2:")
#     print("View Steps:", ExampleModel.get_all_view_steps())
#     print("View Step Count:", ExampleModel.get_view_step_count())

#     # Assume we have some data in the database
#     session = Session()  # You need to set up your SQLAlchemy session

#     # Export data
#     ExampleModel.export_to_csv('example_data.csv')
#     ExampleModel.export_to_excel('example_data.xlsx')
#     ExampleModel.export_to_json('example_data.json')

#     # Import data
#     new_instances = ExampleModel.import_from_csv('example_data.csv', session)
#     print(f"Imported {len(new_instances)} instances from CSV")

#     # Bulk insert
#     ExampleModel.bulk_insert_from_excel('example_data.xlsx', session)
#     print("Bulk inserted data from Excel")

#     # Query to check imported data
#     all_records = ExampleModel.query.all()
#     print(f"Total records after import: {len(all_records)}")
