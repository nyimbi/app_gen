from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, Table, Text
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin
from flask_appbuilder.security.sqla.models import User
from sqlalchemy.sql import func
from datetime import datetime, timedelta

class ProjectMixin:
    """
        A mixin class that provides comprehensive project management functionality for SQLAlchemy models.

        This mixin dynamically creates several related tables prefixed with 'nx_pj_' to manage various aspects of a project,
        including project details, steps, deliverables, equipment, and team assignments. It integrates with Flask-AppBuilder's
        User model for assigning responsibilities and tracking project team members.

        Key Features:
        1. Dynamic table creation for projects, steps, deliverables, equipment, and assignments.
        2. Integration with Flask-AppBuilder's User model for team management.
        3. Comprehensive project timeline tracking with early start and late end capabilities.
        4. Equipment management and allocation to projects.
        5. Deliverable tracking with due dates and status.
        6. Mermaid.js Gantt chart generation for visual project representation.

        Main Tables Created:
        - nx_pj_{tablename}_projects: Stores main project information.
        - nx_pj_{tablename}_steps: Manages individual project steps or phases.
        - nx_pj_{tablename}_deliverables: Tracks project deliverables.
        - nx_pj_{tablename}_equipment: Manages equipment inventory.
        - nx_pj_{tablename}_assignments: Links users to projects with roles and durations.

        Usage:
        To use this mixin, create a model class that inherits from both ProjectMixin and your SQLAlchemy Base:

        ```python
        from sqlalchemy.ext.declarative import declarative_base
        from project_mixin import ProjectMixin

        Base = declarative_base()

        class ProjectItem(ProjectMixin, Base):
            __tablename__ = 'project_items'
            # Add any additional columns or methods specific to ProjectItem
        ```

        Attributes:
        project_id (Column): Foreign key linking to the main project table.
        project (relationship): Relationship to the main Project model.

        Class Methods:
        create_project_tables(): Dynamically creates all necessary project-related tables.
        get_project_items(project_id): Retrieves all items associated with a specific project.
        get_active_projects(): Returns all active projects.
        assign_user_to_project(project_id, user_id, role, start_date, end_date): Assigns a user to a project.
        add_equipment_to_project(project_id, equipment_id, quantity_required): Adds equipment to a project.
        get_project_timeline(project_id): Retrieves the timeline for a specific project.
        update_project_status(project_id, new_status): Updates the status of a project.
        get_project_resources(project_id): Retrieves all resources (team and equipment) assigned to a project.
        render_mermaid(project_id): Generates a Mermaid.js Gantt chart code for the entire project.

        Instance Methods:
        to_dict(): Converts the project item to a dictionary representation.

        Note:
        This mixin is designed to be flexible and can be customized further based on specific project management needs.
        It provides a solid foundation for building a robust project management system within a Flask-AppBuilder application.

        Example:
        ```python
        # Create a new project
        new_project = ProjectItem.Project(name="New Project", description="A sample project")
        db.session.add(new_project)
        db.session.commit()

        # Assign a user to the project
        assignment = ProjectItem.assign_user_to_project(new_project.id, user_id=1, role="Project Manager")
        db.session.add(assignment)
        db.session.commit()

        # Generate a Gantt chart for the project
        gantt_chart = ProjectItem.render_mermaid(new_project.id)
        ```

        See individual method docstrings for more detailed information on usage and parameters.

        To render gantt_chart in a Flask template:
        <div class="mermaid">
            {{ mermaid_code | safe }}
        </div>

            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <script>mermaid.initialize({startOnLoad:true});</script>
        """

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.create_project_tables()

    @classmethod
    def render_mermaid(cls, project_id):
        """
        Generates a Mermaid.js Gantt chart code for the entire project.

        Args:
            project_id (int): The ID of the project to render.

        Returns:
            str: Mermaid.js Gantt chart code.
        """
        project = cls.Project.query.get(project_id)
        if not project:
            return "Error: Project not found"

        mermaid_code = [
            "gantt",
            f"    title {project.name}",
            "    dateFormat  YYYY-MM-DD",
            "    axisFormat %Y-%m-%d",
            f"    section Project",
            f"    {project.name}: {project.start_date.strftime('%Y-%m-%d')}, {project.end_date.strftime('%Y-%m-%d')}"
        ]

        for step in project.steps:
            step_start = step.start_date or project.start_date
            step_end = step.end_date or project.end_date
            duration = (step_end - step_start).days

            mermaid_code.extend([
                f"    section {step.name}",
                f"    {step.name}: {step_start.strftime('%Y-%m-%d')}, {duration}d"
            ])

            if step.early_start:
                early_start_diff = (step.early_start - step_start).days
                mermaid_code.append(
                    f"    Early Start: crit, {step.early_start.strftime('%Y-%m-%d')}, {abs(early_start_diff)}d")

            if step.late_end:
                late_end_diff = (step.late_end - step_end).days
                mermaid_code.append(f"    Late End: crit, {step_end.strftime('%Y-%m-%d')}, {abs(late_end_diff)}d")

        # Add milestones for deliverables
        mermaid_code.append("    section Deliverables")
        for deliverable in project.deliverables:
            mermaid_code.append(f"    {deliverable.name}: milestone, {deliverable.due_date.strftime('%Y-%m-%d')}, 0d")

        # Add resource allocation
        mermaid_code.append("    section Resource Allocation")
        for assignment in project.assignments:
            assignment_start = assignment.start_date or project.start_date
            assignment_end = assignment.end_date or project.end_date
            duration = (assignment_end - assignment_start).days
            mermaid_code.append(
                f"    {assignment.user.username} ({assignment.role}): {assignment_start.strftime('%Y-%m-%d')}, {duration}d")

        return "\n".join(mermaid_code)

    @classmethod
    def create_project_tables(cls):
        class Project(Model, AuditMixin):
            __tablename__ = f'nx_pj_{cls.__tablename__}_projects'

            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False)
            description = Column(Text)
            start_date = Column(DateTime, default=func.now())
            end_date = Column(DateTime)
            status = Column(String(50), default='Planning')
            priority = Column(Integer, default=1)
            budget = Column(Float, default=0.0)

            @hybrid_property
            def duration(self):
                if self.end_date:
                    return (self.end_date - self.start_date).days
                return None

            @hybrid_property
            def is_active(self):
                return self.status not in ['Completed', 'Cancelled']

            def __repr__(self):
                return f"<Project {self.name}>"

        class ProjectStep(Model, AuditMixin):
            __tablename__ = f'nx_pj_{cls.__tablename__}_steps'

            id = Column(Integer, primary_key=True)
            project_id = Column(Integer, ForeignKey(f'{Project.__tablename__}.id'))
            name = Column(String(100), nullable=False)
            description = Column(Text)
            sequence = Column(Integer)
            start_date = Column(DateTime)
            end_date = Column(DateTime)
            early_start = Column(DateTime)
            late_end = Column(DateTime)
            status = Column(String(50), default='Not Started')

            project = relationship('Project', backref='steps')

            @hybrid_property
            def duration(self):
                if self.end_date and self.start_date:
                    return (self.end_date - self.start_date).days
                return None

            def __repr__(self):
                return f"<ProjectStep {self.name}>"

        class Deliverable(Model, AuditMixin):
            __tablename__ = f'nx_pj_{cls.__tablename__}_deliverables'

            id = Column(Integer, primary_key=True)
            project_id = Column(Integer, ForeignKey(f'{Project.__tablename__}.id'))
            name = Column(String(100), nullable=False)
            description = Column(Text)
            due_date = Column(DateTime)
            status = Column(String(50), default='Pending')

            project = relationship('Project', backref='deliverables')

            def __repr__(self):
                return f"<Deliverable {self.name}>"

        class Equipment(Model, AuditMixin):
            __tablename__ = f'nx_pj_{cls.__tablename__}_equipment'

            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False)
            description = Column(Text)
            quantity = Column(Integer, default=1)
            availability_status = Column(String(50), default='Available')

            def __repr__(self):
                return f"<Equipment {self.name}>"

        project_equipment = Table(
            f'nx_pj_{cls.__tablename__}_project_equipment',
            Model.metadata,
            Column('project_id', Integer, ForeignKey(f'{Project.__tablename__}.id')),
            Column('equipment_id', Integer, ForeignKey(f'{Equipment.__tablename__}.id')),
            Column('quantity_required', Integer, default=1)
        )

        class ProjectAssignment(Model, AuditMixin):
            __tablename__ = f'nx_pj_{cls.__tablename__}_assignments'

            id = Column(Integer, primary_key=True)
            project_id = Column(Integer, ForeignKey(f'{Project.__tablename__}.id'))
            user_id = Column(Integer, ForeignKey('ab_user.id'))
            role = Column(String(50))
            start_date = Column(DateTime)
            end_date = Column(DateTime)

            project = relationship('Project', backref='assignments')
            user = relationship('User', backref='project_assignments')

            def __repr__(self):
                return f"<ProjectAssignment {self.user.username} - {self.role}>"

        cls.Project = Project
        cls.ProjectStep = ProjectStep
        cls.Deliverable = Deliverable
        cls.Equipment = Equipment
        cls.ProjectAssignment = ProjectAssignment

    @declared_attr
    def project_id(cls):
        return Column(Integer, ForeignKey(f'nx_pj_{cls.__tablename__}_projects.id'))

    @declared_attr
    def project(cls):
        return relationship('Project', backref=cls.__tablename__)

    @classmethod
    def get_project_items(cls, project_id):
        return cls.query.filter_by(project_id=project_id).all()

    @classmethod
    def get_active_projects(cls):
        return cls.Project.query.filter(cls.Project.status.notin_(['Completed', 'Cancelled'])).all()

    @classmethod
    def assign_user_to_project(cls, project_id, user_id, role, start_date=None, end_date=None):
        assignment = cls.ProjectAssignment(
            project_id=project_id,
            user_id=user_id,
            role=role,
            start_date=start_date or datetime.now(),
            end_date=end_date
        )
        return assignment

    @classmethod
    def add_equipment_to_project(cls, project_id, equipment_id, quantity_required):
        project = cls.Project.query.get(project_id)
        equipment = cls.Equipment.query.get(equipment_id)
        if project and equipment:
            project.equipment.append(equipment)
            project_equipment = next(pe for pe in project.project_equipment if pe.equipment_id == equipment_id)
            project_equipment.quantity_required = quantity_required
            return True
        return False

    @classmethod
    def get_project_timeline(cls, project_id):
        project = cls.Project.query.get(project_id)
        if not project:
            return None

        timeline = {
            'project_start': project.start_date,
            'project_end': project.end_date,
            'steps': []
        }

        for step in project.steps:
            timeline['steps'].append({
                'name': step.name,
                'start': step.start_date,
                'end': step.end_date,
                'early_start': step.early_start,
                'late_end': step.late_end
            })

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

        resources = {
            'team': [],
            'equipment': []
        }

        for assignment in project.assignments:
            resources['team'].append({
                'user': assignment.user.username,
                'role': assignment.role,
                'start_date': assignment.start_date,
                'end_date': assignment.end_date
            })

        for equipment in project.equipment:
            resources['equipment'].append({
                'name': equipment.name,
                'quantity': next(pe.quantity_required for pe in project.project_equipment if pe.equipment_id == equipment.id)
            })

        return resources

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name,
            'status': self.project.status,
            'start_date': self.project.start_date.isoformat() if self.project.start_date else None,
            'end_date': self.project.end_date.isoformat() if self.project.end_date else None,
            'duration': self.project.duration,
            'is_active': self.project.is_active
        }
