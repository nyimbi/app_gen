# File: gen_app/templates/flask_appbuilder.py
"""
Flask-AppBuilder project template.

This template defines the file structure and descriptions for a Flask-AppBuilder project,
including models, views, security, and configuration.
"""

TEMPLATE = {
    "description": "A Flask-AppBuilder application with models, views, and an admin interface.",
    "files": [
        {
            "name": "app/__init__.py",
            "description": "Initialize the Flask-AppBuilder application.",
        },
        {
            "name": "app/models.py",
            "description": "Define data models using SQLAlchemy.",
        },
        {
            "name": "app/views.py",
            "description": "Define view classes for the admin interface.",
        },
        {
            "name": "app/security.py",
            "description": "Configure security and authentication.",
        },
        {
            "name": "requirements.txt",
            "description": "Project dependencies for the Flask-AppBuilder project.",
        },
        {
            "name": "README.md",
            "description": "Documentation with setup and usage instructions.",
        },
    ],
}
