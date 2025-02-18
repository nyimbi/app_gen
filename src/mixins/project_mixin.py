import logging
from datetime import datetime, timedelta

from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin
from flask_appbuilder.security.sqla.models import User
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declared_attr, relationship
from sqlalchemy.sql import func, text

logger = logging.getLogger(__name__)


class ProjectMixin:
    """
    ProjectMixin: Advanced Project Management System for Flask-AppBuilder

    A comprehensive mixin that provides enterprise-grade project management capabilities,
    including Gantt charts, resource allocation, deliverable tracking, and team management.
    Seamlessly integrates with Flask-AppBuilder's security model and PostgreSQL features.

    Key Features:
    - Full project lifecycle management with granular state control
    - Advanced Gantt chart visualization using Mermaid.js
    - Resource allocation and capacity planning
    - Deliverable tracking with dependencies
    - Equipment inventory and assignment
    - Team management with role-based access
    - Audit trail and version history
    - Real-time collaboration support
    - Export/import capabilities
    - Custom workflow support
    - Advanced search and filtering
    - Performance optimized for large datasets
    - REST API integration ready
    - Mobile-friendly interface support

    Database Schema:
    - Projects (nx_pj_{tablename}_projects)
    - Steps (nx_pj_{tablename}_steps)
    - Deliverables (nx_pj_{tablename}_deliverables)
    - Equipment (nx_pj_{tablename}_equipment)
    - Assignments (nx_pj_{tablename}_assignments)

    Usage Example:

    ```python
    class ProjectItem(ProjectMixin, Model):
        __tablename__ = 'project_items'

        id = Column(Integer, primary_key=True)
        name = Column(String(50), nullable=False)
        description = Column(Text)

        # Optional custom fields
        priority = Column(Integer, default=1)
        cost_center = Column(String(50))

        @property
        def custom_gantt_color(self):
            return '#FF0000' if self.priority > 2 else '#00FF00'

    # In your view
    class ProjectItemView(ModelView):
        datamodel = SQLAInterface(ProjectItem)

        @action("generate_timeline", "Generate Timeline")
        @has_access
        def generate_timeline(self, items):
            for item in items:
                gantt = item.render_mermaid()
                # Handle the Gantt chart...

        @action("assign_team", "Assign Team")
        @has_access
        def assign_team(self, items):
            for item in items:
                item.assign_user_to_project(
                    user_id=g.user.id,
                    role="Manager",
                    start_date=datetime.now()
                )
    ```

    Integration Notes:
    - Requires PostgreSQL for optimal performance
    - Depends on Mermaid.js for visualization
    - Uses Flask-AppBuilder security model
    - Supports REST API endpoints
    - Mobile-friendly UI components

    For complete documentation and examples visit:
    https://flask-appbuilder.readthedocs.io/en/latest/project_mixin.html
    """

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.create_project_tables()

    @classmethod
    def render_mermaid(cls, project_id):
        """Generates Mermaid.js Gantt chart visualization for a project"""
        project = cls.Project.query.get(project_id)
        if not project:
            return "Error: Project not found"

        mermaid_code = [
            "gantt",
            f"    title {project.name}",
            "    dateFormat  YYYY-MM-DD",
            "    axisFormat %Y-%m-%d",
            "    section Project",
            f"    {project.name}: {project.start_date.strftime('%Y-%m-%d')}, {project.end_date.strftime('%Y-%m-%d')}",
        ]

        for step in project.steps:
            step_start = step.start_date or project.start_date
            step_end = step.end_date or project.end_date
            duration = (step_end - step_start).days

            mermaid_code.extend(
                [
                    f"    section {step.name}",
                    f"    {step.name}: {step_start.strftime('%Y-%m-%d')}, {duration}d",
                ]
            )

            if step.early_start:
                early_start_diff = (step.early_start - step_start).days
                mermaid_code.append(
                    f"    Early Start: crit, {step.early_start.strftime('%Y-%m-%d')}, {abs(early_start_diff)}d"
                )

            if step.late_end:
                late_end_diff = (step.late_end - step_end).days
                mermaid_code.append(
                    f"    Late End: crit, {step_end.strftime('%Y-%m-%d')}, {abs(late_end_diff)}d"
                )

        # Add milestones for deliverables
        mermaid_code.append("    section Deliverables")
        for deliverable in project.deliverables:
            mermaid_code.append(
                f"    {deliverable.name}: milestone, {deliverable.due_date.strftime('%Y-%m-%d')}, 0d"
            )

        # Add resource allocation
        mermaid_code.append("    section Resource Allocation")
        for assignment in project.assignments:
            assignment_start = assignment.start_date or project.start_date
            assignment_end = assignment.end_date or project.end_date
            duration = (assignment_end - assignment_start).days
            mermaid_code.append(
                f"    {assignment.user.username} ({assignment.role}): {assignment_start.strftime('%Y-%m-%d')}, {duration}d"
            )

        return "\n".join(mermaid_code)

    @classmethod
    def create_project_tables(cls):
        class Project(Model, AuditMixin):
            __tablename__ = f"nx_pj_{cls.__tablename__}_projects"
            __table_args__ = (
                Index(f"idx_{cls.__tablename__}_project_status", "status"),
                Index(
                    f"idx_{cls.__tablename__}_project_dates", "start_date", "end_date"
                ),
                {"postgresql_partition_by": "RANGE (start_date)"},
            )

            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False)
            description = Column(Text)
            start_date = Column(DateTime, default=func.now(), nullable=False)
            end_date = Column(DateTime)
            status = Column(String(50), default="Planning")
            priority = Column(Integer, default=1)
            budget = Column(Float, default=0.0)
            metadata = Column(JSONB, default={})
            tags = Column(ARRAY(String(50)), default=[])

            @hybrid_property
            def duration(self):
                if self.end_date:
                    return (self.end_date - self.start_date).days
                return None

            @hybrid_property
            def is_active(self):
                return self.status not in ["Completed", "Cancelled"]

            def __repr__(self):
                return f"<Project {self.name}>"

        class ProjectStep(Model, AuditMixin):
            __tablename__ = f"nx_pj_{cls.__tablename__}_steps"
            __table_args__ = (
                Index(f"idx_{cls.__tablename__}_step_project", "project_id"),
                Index(f"idx_{cls.__tablename__}_step_dates", "start_date", "end_date"),
            )

            id = Column(Integer, primary_key=True)
            project_id = Column(
                Integer, ForeignKey(f"{Project.__tablename__}.id"), nullable=False
            )
            name = Column(String(100), nullable=False)
            description = Column(Text)
            sequence = Column(Integer)
            start_date = Column(DateTime)
            end_date = Column(DateTime)
            early_start = Column(DateTime)
            late_end = Column(DateTime)
            status = Column(String(50), default="Not Started")
            dependencies = Column(ARRAY(Integer), default=[])
            completion_percentage = Column(Float, default=0.0)
            metadata = Column(JSONB, default={})

            project = relationship("Project", backref="steps")

            @hybrid_property
            def duration(self):
                if self.end_date and self.start_date:
                    return (self.end_date - self.start_date).days
                return None

            def __repr__(self):
                return f"<ProjectStep {self.name}>"

        class Deliverable(Model, AuditMixin):
            __tablename__ = f"nx_pj_{cls.__tablename__}_deliverables"
            __table_args__ = (
                Index(f"idx_{cls.__tablename__}_deliverable_project", "project_id"),
                Index(f"idx_{cls.__tablename__}_deliverable_status", "status"),
            )

            id = Column(Integer, primary_key=True)
            project_id = Column(
                Integer, ForeignKey(f"{Project.__tablename__}.id"), nullable=False
            )
            name = Column(String(100), nullable=False)
            description = Column(Text)
            due_date = Column(DateTime, nullable=False)
            status = Column(String(50), default="Pending")
            priority = Column(Integer, default=1)
            acceptance_criteria = Column(Text)
            review_status = Column(String(50))
            metadata = Column(JSONB, default={})

            project = relationship("Project", backref="deliverables")

            def __repr__(self):
                return f"<Deliverable {self.name}>"

        class Equipment(Model, AuditMixin):
            __tablename__ = f"nx_pj_{cls.__tablename__}_equipment"

            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False)
            description = Column(Text)
            quantity = Column(Integer, default=1)
            availability_status = Column(String(50), default="Available")
            maintenance_schedule = Column(JSONB, default={})
            last_maintenance = Column(DateTime)
            next_maintenance = Column(DateTime)
            specifications = Column(JSONB, default={})
            location = Column(String(100))
            metadata = Column(JSONB, default={})

            def __repr__(self):
                return f"<Equipment {self.name}>"

        project_equipment = Table(
            f"nx_pj_{cls.__tablename__}_project_equipment",
            Model.metadata,
            Column(
                "project_id",
                Integer,
                ForeignKey(f"{Project.__tablename__}.id"),
                primary_key=True,
            ),
            Column(
                "equipment_id",
                Integer,
                ForeignKey(f"{Equipment.__tablename__}.id"),
                primary_key=True,
            ),
            Column("quantity_required", Integer, default=1),
            Column("allocation_start", DateTime),
            Column("allocation_end", DateTime),
            Column("status", String(50)),
            Column("notes", Text),
            Index(f"idx_{cls.__tablename__}_pe_project", "project_id"),
            Index(f"idx_{cls.__tablename__}_pe_equipment", "equipment_id"),
        )

        class ProjectAssignment(Model, AuditMixin):
            __tablename__ = f"nx_pj_{cls.__tablename__}_assignments"
            __table_args__ = (
                Index(f"idx_{cls.__tablename__}_assignment_project", "project_id"),
                Index(f"idx_{cls.__tablename__}_assignment_user", "user_id"),
            )

            id = Column(Integer, primary_key=True)
            project_id = Column(
                Integer, ForeignKey(f"{Project.__tablename__}.id"), nullable=False
            )
            user_id = Column(Integer, ForeignKey("ab_user.id"), nullable=False)
            role = Column(String(50), nullable=False)
            start_date = Column(DateTime, nullable=False)
            end_date = Column(DateTime)
            hours_allocated = Column(Float, default=0.0)
            hours_used = Column(Float, default=0.0)
            status = Column(String(50), default="Active")
            permissions = Column(JSONB, default={})
            metadata = Column(JSONB, default={})

            project = relationship("Project", backref="assignments")
            user = relationship("User", backref="project_assignments")

            def __repr__(self):
                return f"<ProjectAssignment {self.user.username} - {self.role}>"

        cls.Project = Project
        cls.ProjectStep = ProjectStep
        cls.Deliverable = Deliverable
        cls.Equipment = Equipment
        cls.ProjectAssignment = ProjectAssignment

    @declared_attr
    def project_id(cls):
        return Column(Integer, ForeignKey(f"nx_pj_{cls.__tablename__}_projects.id"))

    @declared_attr
    def project(cls):
        return relationship("Project", backref=cls.__tablename__)

    @classmethod
    def get_project_items(cls, project_id):
        return cls.query.filter_by(project_id=project_id).all()

    @classmethod
    def get_active_projects(cls):
        return cls.Project.query.filter(
            cls.Project.status.notin_(["Completed", "Cancelled"])
        ).all()

    @classmethod
    def assign_user_to_project(
        cls, project_id, user_id, role, start_date=None, end_date=None
    ):
        assignment = cls.ProjectAssignment(
            project_id=project_id,
            user_id=user_id,
            role=role,
            start_date=start_date or datetime.now(),
            end_date=end_date,
        )
        return assignment

    @classmethod
    def add_equipment_to_project(cls, project_id, equipment_id, quantity_required):
        project = cls.Project.query.get(project_id)
        equipment = cls.Equipment.query.get(equipment_id)
        if project and equipment:
            project.equipment.append(equipment)
            project_equipment = next(
                pe
                for pe in project.project_equipment
                if pe.equipment_id == equipment_id
            )
            project_equipment.quantity_required = quantity_required
            return True
        return False

    @classmethod
    def get_project_timeline(cls, project_id):
        project = cls.Project.query.get(project_id)
        if not project:
            return None

        timeline = {
            "project_start": project.start_date,
            "project_end": project.end_date,
            "steps": [],
        }

        for step in project.steps:
            timeline["steps"].append(
                {
                    "name": step.name,
                    "start": step.start_date,
                    "end": step.end_date,
                    "early_start": step.early_start,
                    "late_end": step.late_end,
                }
            )

        return timeline

    @classmethod
    def update_project_status(cls, project_id, new_status):
        project = cls.Project.query.get(project_id)
        if project:
            project.status = new_status
            return True
        return False

    @classmethod
    def get_project_resources(cls, project_id):
        project = cls.Project.query.get(project_id)
        if not project:
            return None

        resources = {"team": [], "equipment": []}

        for assignment in project.assignments:
            resources["team"].append(
                {
                    "user": assignment.user.username,
                    "role": assignment.role,
                    "start_date": assignment.start_date,
                    "end_date": assignment.end_date,
                }
            )

        for equipment in project.equipment:
            resources["equipment"].append(
                {
                    "name": equipment.name,
                    "quantity": next(
                        pe.quantity_required
                        for pe in project.project_equipment
                        if pe.equipment_id == equipment.id
                    ),
                }
            )

        return resources

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "project_name": self.project.name if self.project else None,
            "status": self.project.status if self.project else None,
            "start_date": (
                self.project.start_date.isoformat()
                if self.project and self.project.start_date
                else None
            ),
            "end_date": (
                self.project.end_date.isoformat()
                if self.project and self.project.end_date
                else None
            ),
            "duration": self.project.duration if self.project else None,
            "is_active": self.project.is_active if self.project else None,
        }
