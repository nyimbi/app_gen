import io
import json
import humanize
import pandas as pd
from flask import g, Markup
from markupsafe import escape
from datetime import datetime
from typing import List, Dict, Any, Tuple, Type
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, event
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
    event,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import relationship, declared_attr, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import inspect
from sqlalchemy.sql import func


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
    """

    # New Audit Trail Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[str] = mapped_column(String(100), nullable=True)

    # Soft Delete columns
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    """The default number of columns to include in each view step."""
    _columns_per_step: int = 5

    def soft_delete(self) -> None:
        self.deleted_at = func.now()
        self.is_deleted = True

    def restore(self) -> None:
        self.deleted_at = None
        self.is_deleted = False

    @classmethod
    def get_user_id(cls):
        try:
            return g.user.id
        except Exception:
            return None

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

        @event.listens_for(cls, "before_update")
        def set_updated_by(mapper, connection, target):
            target.updated_by = cls.get_current_user()

    """
    Audit functionality to be added to BaseModelMixin.
    """

    created_on: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )

    changed_on: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    @declared_attr
    def created_by_fk(cls) -> Mapped[Optional[int]]:
        return mapped_column(
            Integer, ForeignKey("ab_user.id"), default=cls.get_user_id, nullable=True
        )

    @declared_attr
    def changed_by_fk(cls) -> Mapped[Optional[int]]:
        return mapped_column(
            Integer,
            ForeignKey("ab_user.id"),
            default=cls.get_user_id,
            onupdate=cls.get_user_id,
            nullable=True,
        )

    @declared_attr
    def changed_by(cls) -> Mapped["User"]:
        return relationship(
            "User",
            primaryjoin=lambda: cls.changed_by_fk == User.id,
            remote_side="User.id",
        )

    @declared_attr
    def created_by(cls) -> Mapped["User"]:
        return relationship(
            "User",
            primaryjoin=lambda: cls.created_by_fk == User.id,
            remote_side="User.id",
        )

    @classmethod
    def create_view_step_table(cls):
        """
        Creates a dedicated table for storing view step information for the inheriting model.

        This method is called automatically during class initialization.
        """
        table_name = f"nx_{cls.__tablename__}_view_steps"

        class ViewStep(Base):
            __tablename__ = table_name

            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            step_name: Mapped[str] = mapped_column(String(100), nullable=False)
            column_name: Mapped[str] = mapped_column(String(100), nullable=False)
            order: Mapped[int] = mapped_column(Integer, nullable=False)

            __table_args__ = (
                UniqueConstraint("step_name", "column_name", name=f"uix_{table_name}"),
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

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Creates a dictionary representation of the model's structure and view steps.

        Returns:
            Dict[str, Any]: A dictionary containing comprehensive information about the model and its view steps.
        """
        return {
            "columns": cls.model_columns(),
            "column_details": [
                (name, str(type)) for name, type in cls.column_details()
            ],
            "mixin_columns": cls.mixin_columns(),
            "mixin_methods": cls.mixin_methods(),
            "column_count": cls.column_count(),
            "view_steps": cls.get_all_view_steps(),
            "columns_per_step": cls.get_columns_per_step(),
            "view_step_count": cls.get_view_step_count(),
        }

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
#     print("Model Structure:", ExampleModel.to_dict())

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
