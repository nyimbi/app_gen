import asyncio
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ollama
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter

# User-selectable LLM model (default to 'mistral')
DEFAULT_LLM = "yi-coder"

# Updated Python Project Templates
PYTHON_TEMPLATES = {
    "flask_api": {
        "description": "A Flask-based REST API with structured endpoints, authentication and documentation.",
        "files": [
            {
                "name": "app.py",
                "description": "Main Flask application with configurations.",
            },
            {
                "name": "app/__init__.py",
                "description": "Application factory pattern implementation.",
            },
            {
                "name": "app/api/__init__.py",
                "description": "API package initialization.",
            },
            {"name": "app/api/routes.py", "description": "Main API route definitions."},
            {
                "name": "app/api/auth.py",
                "description": "Authentication and authorization handlers.",
            },
            {
                "name": "app/api/models.py",
                "description": "Data models for API resources.",
            },
            {
                "name": "app/api/schemas.py",
                "description": "Marshmallow schemas for serialization/validation.",
            },
            {
                "name": "app/api/utils.py",
                "description": "Utility functions for the API.",
            },
            {
                "name": "app/config.py",
                "description": "Configuration classes for different environments.",
            },
            {
                "name": "app/extensions.py",
                "description": "Flask extensions initialization.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for the Flask app with version constraints.",
            },
            {
                "name": "tests/conftest.py",
                "description": "Pytest fixtures and configuration.",
            },
            {
                "name": "tests/test_api.py",
                "description": "API endpoint tests with mocking.",
            },
            {
                "name": "tests/test_auth.py",
                "description": "Authentication functionality tests.",
            },
            {
                "name": "README.md",
                "description": "Project documentation with setup and usage instructions.",
            },
            {
                "name": "app/docs/swagger.json",
                "description": "OpenAPI/Swagger documentation for the API.",
            },
        ],
    },
    "flask_appbuilder": {
        "description": "A full Flask-AppBuilder application with models, mixins, blueprints, and admin interface.",
        "files": [
            {
                "name": "app/__init__.py",
                "description": "Initialize Flask-AppBuilder application with security and configuration management.",
            },
            {
                "name": "app/models/__init__.py",
                "description": "Models package initialization.",
            },
            {
                "name": "app/models/base.py",
                "description": "Base model class with common attributes and methods.",
            },
            {
                "name": "app/models/user.py",
                "description": "User and role models with custom authentication methods.",
            },
            {
                "name": "app/models/business.py",
                "description": "Primary business domain models with SQLAlchemy relationships and constraints.",
            },
            {
                "name": "app/views/__init__.py",
                "description": "Views package initialization.",
            },
            {
                "name": "app/views/base.py",
                "description": "Base view classes with common configuration and methods.",
            },
            {
                "name": "app/views/home.py",
                "description": "Index and dashboard view with custom widgets and charts.",
            },
            {
                "name": "app/views/master_detail.py",
                "description": "Master-detail views with related model relationships.",
            },
            {
                "name": "app/views/charts.py",
                "description": "Chart views with data visualization components.",
            },
            {
                "name": "app/api/__init__.py",
                "description": "API package initialization.",
            },
            {
                "name": "app/api/base.py",
                "description": "Base API class with common authentication and error handling.",
            },
            {
                "name": "app/api/endpoints.py",
                "description": "REST API endpoints using Flask-AppBuilder's ModelRestApi.",
            },
            {
                "name": "app/security/__init__.py",
                "description": "Security package initialization.",
            },
            {
                "name": "app/security/manager.py",
                "description": "Custom security manager with extended authorization features.",
            },
            {
                "name": "app/security/views.py",
                "description": "Custom security views for authentication and user management.",
            },
            {
                "name": "app/mixins/__init__.py",
                "description": "Mixins package initialization.",
            },
            {
                "name": "app/mixins/audit.py",
                "description": "Audit tracking mixin with created/modified timestamps and user references.",
            },
            {
                "name": "app/mixins/search.py",
                "description": "Full-text search mixins for enhanced model querying.",
            },
            {
                "name": "app/mixins/filters.py",
                "description": "Custom filter mixins for advanced view filtering.",
            },
            {
                "name": "app/forms/__init__.py",
                "description": "Forms package initialization.",
            },
            {
                "name": "app/forms/widgets.py",
                "description": "Custom form widgets with enhanced UI functionality.",
            },
            {
                "name": "app/forms/fields.py",
                "description": "Custom form fields with advanced validation.",
            },
            {
                "name": "app/forms/validators.py",
                "description": "Custom validators for form fields with complex business rules.",
            },
            {
                "name": "app/static/js/custom.js",
                "description": "JavaScript enhancements for the admin interface.",
            },
            {
                "name": "app/static/css/custom.css",
                "description": "Custom styling for the admin interface.",
            },
            {
                "name": "app/static/js/charts.js",
                "description": "JavaScript for interactive charts and dashboards.",
            },
            {
                "name": "app/templates/appbuilder/general/widgets/list.html",
                "description": "Custom list widget template override.",
            },
            {
                "name": "app/templates/appbuilder/general/widgets/chart.html",
                "description": "Custom chart widget template.",
            },
            {
                "name": "app/templates/custom_page.html",
                "description": "Custom Jinja2 template extending AppBuilder layout.",
            },
            {
                "name": "app/blueprints/__init__.py",
                "description": "Blueprints package initialization.",
            },
            {
                "name": "app/blueprints/sample_blueprint/__init__.py",
                "description": "Blueprint initialization with registration logic.",
            },
            {
                "name": "app/blueprints/sample_blueprint/views.py",
                "description": "Blueprint-specific views and endpoints.",
            },
            {
                "name": "app/blueprints/sample_blueprint/models.py",
                "description": "Blueprint-specific models with namespace isolation.",
            },
            {
                "name": "app/blueprints/sample_blueprint/api.py",
                "description": "Blueprint-specific API endpoints.",
            },
            {
                "name": "app/utils/__init__.py",
                "description": "Utils package initialization.",
            },
            {
                "name": "app/utils/decorators.py",
                "description": "Custom decorators for views and API endpoints.",
            },
            {
                "name": "app/utils/filters.py",
                "description": "Custom SQLAlchemy filters for advanced queries.",
            },
            {
                "name": "config.py",
                "description": "Configuration with environment variables support.",
            },
            {
                "name": "run.py",
                "description": "Application entry point with development server configuration.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies for Flask-AppBuilder with version constraints.",
            },
            {
                "name": "tests/conftest.py",
                "description": "Pytest fixtures with database session handling.",
            },
            {
                "name": "tests/test_models.py",
                "description": "Unit tests for SQLAlchemy models.",
            },
            {
                "name": "tests/test_views.py",
                "description": "Unit tests for Flask-AppBuilder views.",
            },
            {
                "name": "tests/test_api.py",
                "description": "Unit tests for REST API endpoints.",
            },
            {
                "name": "tests/test_security.py",
                "description": "Unit tests for security components.",
            },
            {
                "name": "migrations/README",
                "description": "Description of the migrations system.",
            },
            {
                "name": "migrations/env.py",
                "description": "Alembic environment configuration.",
            },
            {
                "name": "migrations/script.py.mako",
                "description": "Template for migration scripts.",
            },
            {
                "name": "migrations/versions/initial_migration.py",
                "description": "Alembic migration script for initial database schema.",
            },
            {
                "name": "Dockerfile",
                "description": "Docker configuration for containerized deployment.",
            },
            {
                "name": "docker-compose.yml",
                "description": "Multi-container Docker configuration with database.",
            },
        ],
    },
    "flask_appbuilder_mixins": {
        "description": "Flask-AppBuilder models with custom mixins for reusability, audit tracking, and data validation.",
        "files": [
            {
                "name": "app/mixins/__init__.py",
                "description": "Package initialization for mixins module.",
            },
            {
                "name": "app/mixins/audit.py",
                "description": "Audit tracking mixin with created/modified timestamps and user references.",
            },
            {
                "name": "app/mixins/history.py",
                "description": "History tracking mixin for model changes with versioning.",
            },
            {
                "name": "app/mixins/permission.py",
                "description": "Permission mixins for fine-grained access control.",
            },
            {
                "name": "app/mixins/validation.py",
                "description": "Data validation mixins with custom validators.",
            },
            {
                "name": "app/mixins/searchable.py",
                "description": "Full-text search mixin with indexing capabilities.",
            },
            {
                "name": "app/mixins/soft_delete.py",
                "description": "Soft delete mixin for logical record deletion.",
            },
            {
                "name": "app/mixins/tenant.py",
                "description": "Multi-tenancy mixin for data isolation.",
            },
            {
                "name": "app/mixins/timestamp.py",
                "description": "Timestamp tracking with timezone support.",
            },
            {
                "name": "app/mixins/view/__init__.py",
                "description": "View mixins package initialization.",
            },
            {
                "name": "app/mixins/view/filters.py",
                "description": "Custom filter mixins for ModelViews.",
            },
            {
                "name": "app/mixins/view/formatters.py",
                "description": "Custom formatters for displaying model data in views.",
            },
            {
                "name": "app/mixins/view/actions.py",
                "description": "Custom action mixins for ModelViews with bulk operations.",
            },
            {
                "name": "app/mixins/view/export.py",
                "description": "Export functionality mixins for data export in multiple formats.",
            },
            {
                "name": "app/mixins/view/widgets.py",
                "description": "Custom widget mixins for enhanced UI components.",
            },
            {
                "name": "app/models/base.py",
                "description": "Base model class implementing multiple mixins.",
            },
            {
                "name": "app/models/__init__.py",
                "description": "Models package initialization.",
            },
            {
                "name": "app/models/examples.py",
                "description": "Example models implementing the custom mixins.",
            },
            {
                "name": "app/views/__init__.py",
                "description": "Views package initialization.",
            },
            {
                "name": "app/views/examples.py",
                "description": "Example views utilizing the view mixins.",
            },
            {
                "name": "app/__init__.py",
                "description": "Flask-AppBuilder application initialization.",
            },
            {
                "name": "config.py",
                "description": "Application configuration.",
            },
            {
                "name": "tests/test_mixins_model.py",
                "description": "Unit tests for model mixins.",
            },
            {
                "name": "tests/test_mixins_view.py",
                "description": "Unit tests for view mixins.",
            },
            {
                "name": "tests/test_models.py",
                "description": "Integration tests for models using mixins.",
            },
            {
                "name": "tests/test_views.py",
                "description": "Integration tests for views using mixins.",
            },
            {
                "name": "tests/conftest.py",
                "description": "Test fixtures and configuration.",
            },
            {
                "name": "README.md",
                "description": "Documentation on how to use and extend the mixins.",
            },
            {
                "name": "docs/model_mixins.md",
                "description": "Detailed documentation for model mixins.",
            },
            {
                "name": "docs/view_mixins.md",
                "description": "Detailed documentation for view mixins.",
            },
        ],
    },
    "flask_appbuilder_blueprint": {
        "description": "A Flask-AppBuilder blueprint with complete functionality for a modular application section.",
        "files": [
            {
                "name": "app/blueprints/<blueprint_name>/__init__.py",
                "description": "Blueprint initialization with Flask-AppBuilder integration.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/manager.py",
                "description": "Blueprint manager class for lifecycle and configuration management.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/routes.py",
                "description": "API routes and endpoint handlers for the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/models/__init__.py",
                "description": "Models package initialization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/models/base.py",
                "description": "Base model class for the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/models/domain.py",
                "description": "Domain-specific SQLAlchemy models with relationships.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/views/__init__.py",
                "description": "Views package initialization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/views/base.py",
                "description": "Base view class for the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/views/master.py",
                "description": "Main model views with CRUD operations.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/views/charts.py",
                "description": "Chart views for data visualization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/views/custom.py",
                "description": "Custom views with specialized functionality.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/forms/__init__.py",
                "description": "Forms package initialization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/forms/base.py",
                "description": "Base form classes with common validation.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/forms/custom.py",
                "description": "Custom WTForms form definitions with validators.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/api/__init__.py",
                "description": "API package initialization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/api/v1.py",
                "description": "REST API v1 endpoints for the blueprint resources.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/schemas/__init__.py",
                "description": "Schemas package initialization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/schemas/base.py",
                "description": "Base schema classes.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/schemas/domain.py",
                "description": "Marshmallow schemas for API serialization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/utils/__init__.py",
                "description": "Utilities package initialization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/utils/helpers.py",
                "description": "Utility functions specific to the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/utils/security.py",
                "description": "Security utilities for the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/mixins/__init__.py",
                "description": "Blueprint-specific mixins initialization.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/mixins/domain.py",
                "description": "Domain-specific mixins for models and views.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/templates/index.html",
                "description": "Main template for blueprint-specific pages.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/templates/widgets/custom_widget.html",
                "description": "Custom widget templates for the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/templates/layouts/master.html",
                "description": "Master layout template for the blueprint.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/static/js/main.js",
                "description": "JavaScript for blueprint-specific frontend functionality.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/static/js/charts.js",
                "description": "JavaScript for data visualization components.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/static/css/style.css",
                "description": "CSS styles for blueprint-specific components.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/static/css/themes.css",
                "description": "Theme variations for the blueprint UI.",
            },
            {
                "name": "app/blueprints/<blueprint_name>/static/img/logo.png",
                "description": "Blueprint-specific branding assets.",
            },
            {
                "name": "tests/blueprints/<blueprint_name>/conftest.py",
                "description": "Blueprint-specific test fixtures.",
            },
            {
                "name": "tests/blueprints/<blueprint_name>/test_models.py",
                "description": "Unit tests for blueprint models.",
            },
            {
                "name": "tests/blueprints/<blueprint_name>/test_views.py",
                "description": "Unit tests for blueprint views.",
            },
            {
                "name": "tests/blueprints/<blueprint_name>/test_api.py",
                "description": "Unit tests for blueprint API endpoints.",
            },
            {
                "name": "tests/blueprints/<blueprint_name>/test_forms.py",
                "description": "Unit tests for blueprint forms.",
            },
            {
                "name": "tests/blueprints/<blueprint_name>/test_integration.py",
                "description": "Integration tests for the blueprint.",
            },
            {
                "name": "migrations/versions/<blueprint_name>_migration.py",
                "description": "Alembic migration for blueprint schema.",
            },
            {
                "name": "docs/blueprints/<blueprint_name>/README.md",
                "description": "Blueprint-specific documentation.",
            },
            {
                "name": "docs/blueprints/<blueprint_name>/api.md",
                "description": "API documentation for the blueprint.",
            },
        ],
    },
    "cli_tool": {
        "description": "A comprehensive command-line Python application with subcommands, configuration, and plugins.",
        "files": [
            {
                "name": "main.py",
                "description": "Main entry point with CLI argument parsing.",
            },
            {"name": "cli/__init__.py", "description": "CLI package initialization."},
            {
                "name": "cli/commands/__init__.py",
                "description": "Commands package initialization.",
            },
            {
                "name": "cli/commands/base.py",
                "description": "Base command class with common functionality.",
            },
            {
                "name": "cli/commands/command1.py",
                "description": "Implementation of first command.",
            },
            {
                "name": "cli/commands/command2.py",
                "description": "Implementation of second command.",
            },
            {
                "name": "cli/utils/__init__.py",
                "description": "Utilities package initialization.",
            },
            {
                "name": "cli/utils/helpers.py",
                "description": "Helper functions for the CLI.",
            },
            {
                "name": "cli/utils/formatters.py",
                "description": "Output formatting utilities.",
            },
            {
                "name": "cli/config.py",
                "description": "Configuration management with environment support.",
            },
            {
                "name": "cli/plugins/__init__.py",
                "description": "Plugin system for extensibility.",
            },
            {
                "name": "cli/plugins/example_plugin.py",
                "description": "Example plugin implementation.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies with version constraints.",
            },
            {
                "name": "tests/conftest.py",
                "description": "Pytest fixtures and configuration.",
            },
            {
                "name": "tests/test_commands.py",
                "description": "Unit tests for CLI commands.",
            },
            {
                "name": "tests/test_utils.py",
                "description": "Unit tests for utility functions.",
            },
            {
                "name": "tests/test_config.py",
                "description": "Unit tests for configuration handling.",
            },
            {
                "name": "tests/test_plugins.py",
                "description": "Unit tests for plugin system.",
            },
            {"name": "setup.py", "description": "Package installation configuration."},
            {"name": "README.md", "description": "Documentation with usage examples."},
            {
                "name": "docs/user_guide.md",
                "description": "Detailed user documentation.",
            },
            {
                "name": "docs/developer_guide.md",
                "description": "Guide for extending the CLI.",
            },
        ],
    },
    "fastapi_service": {
        "description": "A production-ready FastAPI microservice with async database, authentication, and Swagger docs.",
        "files": [
            {"name": "main.py", "description": "Main FastAPI application entry point."},
            {
                "name": "app/__init__.py",
                "description": "Application package initialization.",
            },
            {
                "name": "app/api/__init__.py",
                "description": "API package initialization.",
            },
            {
                "name": "app/api/v1/__init__.py",
                "description": "API v1 router initialization.",
            },
            {
                "name": "app/api/v1/endpoints/__init__.py",
                "description": "Endpoints package initialization.",
            },
            {
                "name": "app/api/v1/endpoints/items.py",
                "description": "Item resource endpoints.",
            },
            {
                "name": "app/api/v1/endpoints/users.py",
                "description": "User resource endpoints.",
            },
            {
                "name": "app/api/deps.py",
                "description": "Dependency injection functions.",
            },
            {
                "name": "app/core/__init__.py",
                "description": "Core package initialization.",
            },
            {
                "name": "app/core/config.py",
                "description": "Environment-based configuration with Pydantic.",
            },
            {
                "name": "app/core/security.py",
                "description": "JWT authentication and security utilities.",
            },
            {
                "name": "app/db/__init__.py",
                "description": "Database package initialization.",
            },
            {"name": "app/db/base.py", "description": "SQLAlchemy base models."},
            {
                "name": "app/db/session.py",
                "description": "Database session creation and dependency.",
            },
            {
                "name": "app/models/__init__.py",
                "description": "Models package initialization.",
            },
            {
                "name": "app/models/user.py",
                "description": "User model definition with authentication.",
            },
            {
                "name": "app/models/item.py",
                "description": "Item model definition with relationships.",
            },
            {
                "name": "app/schemas/__init__.py",
                "description": "Schemas package initialization.",
            },
            {
                "name": "app/schemas/user.py",
                "description": "User Pydantic schemas for validation.",
            },
            {
                "name": "app/schemas/item.py",
                "description": "Item Pydantic schemas for validation.",
            },
            {"name": "app/crud/__init__.py", "description": "CRUD operations package."},
            {
                "name": "app/crud/base.py",
                "description": "Base CRUD operations for models.",
            },
            {
                "name": "app/crud/user.py",
                "description": "User-specific CRUD operations.",
            },
            {
                "name": "app/crud/item.py",
                "description": "Item-specific CRUD operations.",
            },
            {
                "name": "app/utils.py",
                "description": "Utility functions for the application.",
            },
            {
                "name": "alembic.ini",
                "description": "Alembic configuration for migrations.",
            },
            {
                "name": "migrations/env.py",
                "description": "Alembic environment configuration.",
            },
            {
                "name": "migrations/versions/initial_migration.py",
                "description": "Initial database schema migration.",
            },
            {
                "name": "requirements.txt",
                "description": "Dependencies with version constraints.",
            },
            {
                "name": "Dockerfile",
                "description": "Docker configuration for deployment.",
            },
            {
                "name": "docker-compose.yml",
                "description": "Multi-container configuration with database.",
            },
            {
                "name": "tests/conftest.py",
                "description": "Pytest fixtures for testing.",
            },
            {
                "name": "tests/api/test_items.py",
                "description": "Tests for item endpoints.",
            },
            {
                "name": "tests/api/test_users.py",
                "description": "Tests for user endpoints.",
            },
            {
                "name": "tests/crud/test_user.py",
                "description": "Tests for user CRUD operations.",
            },
            {
                "name": "tests/crud/test_item.py",
                "description": "Tests for item CRUD operations.",
            },
            {
                "name": ".env.example",
                "description": "Example environment variables file.",
            },
            {
                "name": "README.md",
                "description": "Project documentation and setup guide.",
            },
        ],
    },
    "django_application": {
        "description": "A full Django web application with models, views, templates, and REST API.",
        "files": [
            {"name": "manage.py", "description": "Django management command script."},
            {
                "name": "project/__init__.py",
                "description": "Django project package initialization.",
            },
            {
                "name": "project/settings.py",
                "description": "Django project settings with environment support.",
            },
            {
                "name": "project/urls.py",
                "description": "Main URL routing configuration.",
            },
            {
                "name": "project/asgi.py",
                "description": "ASGI configuration for async servers.",
            },
            {
                "name": "project/wsgi.py",
                "description": "WSGI configuration for web servers.",
            },
            {
                "name": "app/__init__.py",
                "description": "Django app package initialization.",
            },
            {"name": "app/apps.py", "description": "Django app configuration."},
            {"name": "app/models.py", "description": "Django ORM model definitions."},
            {"name": "app/views.py", "description": "Django class-based views."},
            {
                "name": "app/admin.py",
                "description": "Django admin interface customizations.",
            },
            {"name": "app/urls.py", "description": "App-specific URL routing."},
            {
                "name": "app/forms.py",
                "description": "Django form classes for validation.",
            },
            {
                "name": "app/api/__init__.py",
                "description": "API package initialization.",
            },
            {
                "name": "app/api/serializers.py",
                "description": "DRF serializers for API endpoints.",
            },
            {
                "name": "app/api/views.py",
                "description": "DRF ViewSets for API endpoints.",
            },
            {"name": "app/api/urls.py", "description": "API URL routing."},
            {
                "name": "app/templates/app/index.html",
                "description": "Main template for app views.",
            },
            {
                "name": "app/templates/app/detail.html",
                "description": "Detail template for object views.",
            },
            {
                "name": "app/static/css/style.css",
                "description": "Custom CSS for the application.",
            },
            {
                "name": "app/static/js/main.js",
                "description": "Custom JavaScript for the application.",
            },
            {
                "name": "app/management/__init__.py",
                "description": "Management commands package.",
            },
            {
                "name": "app/management/commands/__init__.py",
                "description": "Commands package initialization.",
            },
            {
                "name": "app/management/commands/sample_command.py",
                "description": "Example custom management command.",
            },
            {
                "name": "app/templatetags/__init__.py",
                "description": "Template tags package.",
            },
            {
                "name": "app/templatetags/app_tags.py",
                "description": "Custom template tags and filters.",
            },
            {
                "name": "requirements.txt",
                "description": "Project dependencies with versions.",
            },
            {
                "name": "tests/__init__.py",
                "description": "Tests package initialization.",
            },
            {
                "name": "tests/test_models.py",
                "description": "Unit tests for Django models.",
            },
            {
                "name": "tests/test_views.py",
                "description": "Unit tests for Django views.",
            },
            {
                "name": "tests/test_forms.py",
                "description": "Unit tests for Django forms.",
            },
            {
                "name": "tests/test_api.py",
                "description": "Unit tests for API endpoints.",
            },
            {
                "name": "README.md",
                "description": "Project documentation and setup guide.",
            },
            {
                "name": "Dockerfile",
                "description": "Docker configuration for deployment.",
            },
            {
                "name": "docker-compose.yml",
                "description": "Multi-container setup with database.",
            },
        ],
    },
    "flask_socketio": {
        "description": "A Flask application with SocketIO for real-time communication.",
        "files": [
            {"name": "app.py", "description": "Main Flask and SocketIO application."},
            {
                "name": "app/__init__.py",
                "description": "Application factory with SocketIO initialization.",
            },
            {"name": "app/events.py", "description": "SocketIO event handlers."},
            {"name": "app/routes.py", "description": "HTTP route handlers."},
            {
                "name": "app/models.py",
                "description": "Data models for the application.",
            },
            {
                "name": "app/static/js/socket.js",
                "description": "Client-side SocketIO JavaScript.",
            },
            {
                "name": "app/templates/index.html",
                "description": "Main template with SocketIO integration.",
            },
            {"name": "app/config.py", "description": "Application configuration."},
            {
                "name": "requirements.txt",
                "description": "Dependencies including Flask-SocketIO.",
            },
            {"name": "tests/test_socketio.py", "description": "SocketIO event tests."},
            {"name": "tests/test_routes.py", "description": "HTTP route tests."},
            {"name": "README.md", "description": "Project documentation."},
        ],
    },
}


def print_code(code):
    """Prints syntax-highlighted Python code to the terminal."""
    highlighted_code = highlight(code, PythonLexer(), Terminal256Formatter())
    print(highlighted_code, end="")  # Prevent extra newline


def detect_project_type(prompt):
    """Determine the most suitable Python project type based on the user prompt."""
    prompt_lower = prompt.lower()
    if "mixin" in prompt_lower:
        return "flask_appbuilder_mixins"
    elif "blueprint" in prompt_lower or "flask blueprint" in prompt_lower:
        return "flask_appbuilder_blueprint"
    elif "flask appbuilder" in prompt_lower:
        return "flask_appbuilder"
    elif "fastapi" in prompt_lower:
        return "fastapi_service"
    elif "cli" in prompt_lower or "command line" in prompt_lower:
        return "cli_tool"
    elif "api" in prompt_lower:
        return "flask_api"
    else:
        return "flask_api"  # Default to Flask API


def create_project_directory(
    project_name, blueprint_name=None, include_docs=False, include_static=False
):
    """Creates the main project directory structure for the project.

    Args:
        project_name (str): The name of the project.
        blueprint_name (str, optional): The name of the blueprint to create.
        include_docs (bool, optional): Whether to include a documentation directory.
        include_static (bool, optional): Whether to include a static files directory.
    """
    # Create the main project directory
    os.makedirs(project_name, exist_ok=True)

    # Create subdirectories based on project structure
    os.makedirs(os.path.join(project_name, "app"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "tests"), exist_ok=True)

    if blueprint_name:
        os.makedirs(
            os.path.join(project_name, f"app/blueprints/{blueprint_name}"),
            exist_ok=True,
        )

    if include_docs:
        os.makedirs(os.path.join(project_name, "docs"), exist_ok=True)

    if include_static:
        os.makedirs(os.path.join(project_name, "app/static"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "app/static/css"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "app/static/js"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "app/static/img"), exist_ok=True)

    os.makedirs(os.path.join(project_name, "app/templates"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "app/models"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "app/routes"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "config"), exist_ok=True)

    # Create a pyproject.toml file for black configuration
    with open(os.path.join(project_name, "pyproject.toml"), "w") as f:
        f.write("""
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88
""")

    # Add a .gitignore file
    with open(os.path.join(project_name, ".gitignore"), "w") as f:
        f.write(
            """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE specific files
.idea/
.vscode/
*.swp
*.swo

# OS specific files
.DS_Store
Thumbs.db
"""
        )

    print(f"Project '{project_name}' directory structure created successfully.")


def ensure_dev_dependencies(project_name):
    """Ensure development dependencies are added to requirements.txt"""
    dev_requirements = [
        "black",
        "isort",
        "pytest",
        "pytest-cov",
        "mypy",
        "flake8",
        "autoflake",
    ]

    req_file = os.path.join(project_name, "requirements-dev.txt")
    with open(req_file, "w") as f:
        f.write("\n".join(dev_requirements))

    # Add reference to main requirements.txt file
    with open(os.path.join(project_name, "requirements.txt"), "a") as f:
        f.write("\n\n# For development dependencies, install requirements-dev.txt\n")


def check_tools_installed():
    """Check if required code formatting tools are installed."""
    required_tools = {
        "black": "black",
        "isort": "isort",
        "autoflake": "autoflake",
    }

    missing_tools = []

    for tool, package in required_tools.items():
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=False)
        except FileNotFoundError:
            missing_tools.append(package)

    if missing_tools:
        print(f"⚠️  Missing required tools: {', '.join(missing_tools)}")
        install = input("Would you like to install them now? (y/N): ").lower() == "y"
        if install:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + missing_tools, check=True
                )
                print("✅ Successfully installed required tools!")
            except subprocess.CalledProcessError:
                print("❌ Failed to install tools. Please install them manually:")
                print(f"pip install {' '.join(missing_tools)}")
        return False
    return True


async def identify_functions(file_info, model=DEFAULT_LLM):
    """Identifies all functions that need to be generated in a given Python file."""
    function_identification_prompt = f"""Analyze the purpose of this file and list the functions it should contain.

    File Name: {file_info["name"]}
    Purpose: {file_info["description"]}

    Provide output in JSON format:
    {{
        "functions": [
            {{
                "name": "function_name",
                "description": "What this function does",
                "parameters": [
                    {{"name": "param_name", "type": "param_type", "description": "param description"}}
                ],
                "return_type": "return type",
                "return_description": "what function returns"
            }}
        ]
    }}
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool,
            lambda: ollama.generate(model=model, prompt=function_identification_prompt),
        )

    try:
        # Extract JSON from the response, handling potential formatting issues
        response_text = response["response"]
        # Find JSON content between triple backticks if present
        if "```json" in response_text and "```" in response_text.split("```json", 1)[1]:
            json_str = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
            json_str = response_text.split("```", 1)[1].split("```", 1)[0].strip()
        else:
            json_str = response_text.strip()

        function_data = json.loads(json_str)
        return function_data["functions"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠ Error parsing function list for {file_info['name']}: {str(e)}")
        # Return a default function structure if parsing fails
        return [
            {
                "name": "main",
                "description": f"Main function for {file_info['name']}",
                "parameters": [],
                "return_type": "None",
                "return_description": "None",
            }
        ]


async def generate_function(function_info, file_info, model=DEFAULT_LLM):
    """Generates an individual function."""
    function_prompt = f"""Generate a complete Python function for a {file_info["name"]} file.

    Function Name: {function_info["name"]}
    Purpose: {function_info["description"]}
    Parameters: {json.dumps(function_info.get("parameters", []))}
    Return Type: {function_info.get("return_type", "None")}
    Return Description: {function_info.get("return_description", "None")}
    File Purpose: {file_info["description"]}

    Ensure:
    - It follows PEP8 style guidelines
    - It includes detailed docstrings with parameter and return types
    - It uses appropriate error handling
    - It is modular and reusable
    - It implements best practices for its purpose
    - It includes type hints
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=function_prompt)
        )

    # Clean up code response - extract code blocks if present
    response_text = response["response"]
    if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
        code = response_text.split("```python", 1)[1].split("```", 1)[0].strip()
    elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
        code = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    else:
        code = response_text

    print_code(code)
    return code


async def generate_file_imports(file_info, functions, model=DEFAULT_LLM):
    """Generates appropriate imports for a Python file based on its functions."""
    import_prompt = f"""Generate Python import statements for a file with the following details:

    File Name: {file_info["name"]}
    File Purpose: {file_info["description"]}

    Functions in the file:
    {json.dumps(functions, indent=2)}

    Provide only the import statements, nothing else.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=import_prompt)
        )

    # Clean up response - extract code blocks if present
    response_text = response["response"]
    if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
        imports = response_text.split("```python", 1)[1].split("```", 1)[0].strip()
    elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
        imports = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    else:
        imports = response_text

    # Ensure imports end with a newline
    if imports and not imports.endswith("\n"):
        imports += "\n"

    print_code(code)
    return imports


async def generate_tests_for_function(function_info, file_info, model=DEFAULT_LLM):
    """Generates test cases for an individual function."""
    test_prompt = f"""Generate comprehensive pytest test cases for the following Python function:

    Function Name: {function_info["name"]}
    Function Purpose: {function_info["description"]}
    Parameters: {json.dumps(function_info.get("parameters", []))}
    Return Type: {function_info.get("return_type", "None")}
    Return Description: {function_info.get("return_description", "None")}
    File Purpose: {file_info["description"]}

    Ensure:
    - Each test uses pytest fixtures when appropriate
    - Test cases cover normal usage scenarios
    - Test cases include edge cases
    - Test cases include error handling tests if applicable
    - Each test has a descriptive name and docstring
    - Tests include appropriate assertions
    - Each test is focused on a single aspect of functionality
    - Tests are organized in a logical way

    Generate at least 3 test functions.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=test_prompt)
        )

    # Clean up code response - extract code blocks if present
    response_text = response["response"]
    if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
        test_code = response_text.split("```python", 1)[1].split("```", 1)[0].strip()
    elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
        test_code = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    else:
        test_code = response_text

    print_code(test_code)
    return test_code


async def generate_tests_for_file(
    file_info, functions, project_name, model=DEFAULT_LLM, blueprint_name=None
):
    """Generates a test file for a given Python file."""
    if "test_" in file_info["name"] or file_info["name"].endswith(".txt"):
        return  # Skip generating tests for test files or non-Python files

    # Determine test file path
    source_file_path = file_info["name"].replace(
        "<blueprint_name>", blueprint_name if blueprint_name else "blueprint"
    )

    # Create test file name
    file_parts = os.path.splitext(os.path.basename(source_file_path))
    test_file_name = f"test_{file_parts[0]}{file_parts[1]}"

    # Get the directory part
    dir_path = os.path.dirname(source_file_path)

    # If file is in a subdirectory, create test in tests/subdirectory
    if dir_path:
        test_file_path = os.path.join("tests", dir_path, test_file_name)
    else:
        test_file_path = os.path.join("tests", test_file_name)

    full_test_path = os.path.join(project_name, test_file_path)

    # Ensure directory exists
    os.makedirs(os.path.dirname(full_test_path), exist_ok=True)

    # Generate test imports
    import_parts = []
    import_parts.append("import pytest")

    # Import the module to test
    module_path = (
        source_file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
    )
    if module_path.startswith("app."):
        import_parts.append(f"from {module_path} import *")
    else:
        import_parts.append(f"import {module_path}")

    imports = "\n".join(import_parts) + "\n\n"

    # Generate test fixtures
    fixtures_prompt = f"""Generate pytest fixtures for testing the following file:

    File Name: {file_info["name"]}
    File Purpose: {file_info["description"]}
    Functions: {json.dumps(functions, indent=2)}

    Create appropriate fixtures that would be useful for testing these functions.
    Include mocks if necessary.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=fixtures_prompt)
        )

    # Extract fixtures code
    response_text = response["response"]
    if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
        fixtures_code = (
            response_text.split("```python", 1)[1].split("```", 1)[0].strip()
        )
    elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
        fixtures_code = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    else:
        fixtures_code = response_text

    # Generate test functions for each function
    test_functions = []
    for func in functions:
        test_code = await generate_tests_for_function(func, file_info, model)
        test_functions.append(test_code)

    # Combine everything
    all_test_code = imports + fixtures_code + "\n\n" + "\n\n".join(test_functions)

    # Format the code
    formatted_code = await format_code(all_test_code)

    with open(full_test_path, "w") as f:
        f.write(
            f'"""\nTests for {file_info["name"]}: {file_info["description"]}\n"""\n\n'
        )
        f.write(formatted_code)

    print(f"✅ Test file {test_file_path} created successfully.")


async def review_code(file_content, file_info, model=DEFAULT_LLM):
    """Uses an LLM to review and improve generated code."""
    review_prompt = f"""Review the following Python code for {file_info["name"]} implementing {file_info["description"]}.
    Check for correctness, best practices, security issues, and completeness:

    ```python
    {file_content}
    ```

    Provide the improved version with any necessary corrections or enhancements.
    Return only the complete code without explanations.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=review_prompt)
        )

    # Clean up response - extract code blocks if present
    response_text = response["response"]
    if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
        reviewed_code = (
            response_text.split("```python", 1)[1].split("```", 1)[0].strip()
        )
    elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
        reviewed_code = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    else:
        reviewed_code = response_text

    return reviewed_code


async def format_code(code_content):
    """Format code using Black and isort."""
    if not code_content.strip():
        return code_content

    # Create a temporary file
    temp_file = Path("temp_format_file.py")
    try:
        # Write content to temp file
        temp_file.write_text(code_content)

        # Run autoflake to remove unused imports
        try:
            subprocess.run(
                [
                    "autoflake",
                    "--remove-all-unused-imports",
                    "--in-place",
                    str(temp_file),
                ],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Continue if autoflake fails
            pass

        # Run isort
        try:
            subprocess.run(["isort", str(temp_file)], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Continue if isort fails
            pass

        # Run black
        try:
            subprocess.run(
                ["black", "-q", str(temp_file)], check=True, capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Continue if black fails
            pass

        # Read the formatted content
        formatted_content = temp_file.read_text()
        return formatted_content

    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()


async def generate_code_async(
    file_info, project_name, model=DEFAULT_LLM, blueprint_name=None
):
    """Generates code for a Python file by first identifying functions, generating them, and then assembling the final file."""
    file_path = os.path.join(
        project_name,
        file_info["name"].replace(
            "<blueprint_name>", blueprint_name if blueprint_name else "blueprint"
        ),
    )

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Skip code generation for non-Python files (just create requirements.txt)
    if file_path.endswith(".txt"):
        if "requirements.txt" in file_path:
            print(f"📝 Generating {file_info['name']}...")
            requirements_prompt = f"""Generate a comprehensive requirements.txt file for a {project_name} project.
            The project description is: {file_info["description"]}

            List all required packages with appropriate version constraints.
            Include both production dependencies and development dependencies.
            """

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(
                    pool,
                    lambda: ollama.generate(model=model, prompt=requirements_prompt),
                )

            # Extract requirements
            response_text = response["response"]
            # Debugging: Print the raw response for inspection
            print_code(f"Raw LLM Response: {response_text}")
            if "```" in response_text:
                requirements = response_text.split("```")[1].strip()
                if requirements.startswith(
                    "requirements.txt"
                ) or requirements.startswith("python"):
                    requirements = "\n".join(requirements.split("\n")[1:])
            else:
                requirements = response_text.strip()

            with open(file_path, "w") as f:
                f.write(requirements)

            print(f"✅ File {file_info['name']} created successfully.")
        return

    print(f"🔍 Identifying functions for {file_info['name']}...")
    functions = await identify_functions(file_info, model)

    if not functions:
        print(
            f"⚠ No functions identified for {file_info['name']}. Generating default content."
        )
        functions = [
            {"name": "main", "description": f"Main function for {file_info['name']}"}
        ]

    print(f"📚 Generating imports for {file_info['name']}...")
    imports = await generate_file_imports(file_info, functions, model)

    print(f"🚀 Generating {len(functions)} functions for {file_info['name']}...")
    tasks = [generate_function(func, file_info, model) for func in functions]
    generated_functions = await asyncio.gather(*tasks)

    # Assemble the file
    raw_code = imports + "\n\n" + "\n\n".join(generated_functions)

    print(f"🔍 Reviewing code for {file_info['name']}...")
    reviewed_code = await review_code(raw_code, file_info, model)

    print(f"🔧 Formatting code for {file_info['name']}...")
    formatted_code = await format_code(reviewed_code)

    # Ensure directory exists before writing file
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as f:
        f.write(f'"""\n{file_info["description"]}\n"""\n\n')
        f.write(formatted_code)

    print(f"✅ File {file_info['name']} created successfully.")

    # Generate tests for the file
    print(f"🧪 Generating tests for {file_info['name']}...")
    await generate_tests_for_file(
        file_info, functions, project_name, model, blueprint_name
    )


async def process_files_concurrently(files, project_name, model, blueprint_name=None):
    """Handles the generation of multiple files in parallel."""
    tasks = [
        generate_code_async(file, project_name, model, blueprint_name) for file in files
    ]
    await asyncio.gather(*tasks)


async def generate_readme(project_name, project_type, description, model=DEFAULT_LLM):
    """Generates a README.md file for the project."""
    readme_prompt = f"""Generate a comprehensive README.md file for a Python project with the following details:

    Project Type: {project_type} ({PYTHON_TEMPLATES[project_type]["description"]})
    Project Description: {description}

    Include sections for:
    - Project overview
    - Installation instructions
    - Usage examples
    - Project structure
    - Configuration
    - Testing
    - Contributing guidelines

    Format it with proper Markdown syntax.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=readme_prompt)
        )

    readme_content = response["response"]

    # Clean up markdown content if needed
    if (
        "```markdown" in readme_content
        and "```" in readme_content.split("```markdown", 1)[1]
    ):
        readme_content = (
            readme_content.split("```markdown", 1)[1].split("```", 1)[0].strip()
        )
    elif "```md" in readme_content and "```" in readme_content.split("```md", 1)[1]:
        readme_content = readme_content.split("```md", 1)[1].split("```", 1)[0].strip()
    elif "```" in readme_content and "```" in readme_content.split("```", 1)[1]:
        readme_content = readme_content.split("```", 1)[1].split("```", 1)[0].strip()

    with open(os.path.join(project_name, "README.md"), "w") as f:
        f.write(readme_content)

    print(f"📝 README.md file created successfully.")


async def generate_makefile(project_name):
    """Generate a Makefile with useful commands for development."""
    makefile_content = """# Makefile for Python project

.PHONY: setup test lint format clean

# Setup development environment
setup:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Run tests
test:
	pytest tests/ --cov=app

# Run linting
lint:
	flake8 app/ tests/
	mypy app/ tests/

# Format code
format:
	isort app/ tests/
	black app/ tests/

# Clean build artifacts
clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
"""

    with open(os.path.join(project_name, "Makefile"), "w") as f:
        f.write(makefile_content)

    print(f"📝 Makefile created successfully.")


def generate_code(prompt, model=DEFAULT_LLM):
    """Main function that generates a structured Python project by generating each function separately before assembling files."""
    try:
        # Check if required tools are installed
        tools_available = check_tools_installed()

        project_type = detect_project_type(prompt)
        project_template = PYTHON_TEMPLATES[project_type]

        print(
            f"\n🔍 Detected Project Type: {project_type} ({project_template['description']})"
        )

        # Ask the user for more details about the project
        project_name = (
            input("Enter project name (default: generated_python_project): ")
            or "generated_python_project"
        )

        # If the user is generating a blueprint, ask for the name
        blueprint_name = None
        if project_type == "flask_appbuilder_blueprint":
            blueprint_name = input("Enter the name of your blueprint: ")

        # Ask for additional configuration
        include_docs = input("Include documentation directory? (y/N): ").lower() == "y"
        include_static = input("Include static files directory? (y/N): ").lower() == "y"

        # Create project directory structure
        create_project_directory(
            project_name, blueprint_name, include_docs, include_static
        )

        # Ensure development dependencies are added
        ensure_dev_dependencies(project_name)

        print("\n🚀 Generating project files...")
        asyncio.run(
            process_files_concurrently(
                project_template["files"], project_name, model, blueprint_name
            )
        )

        # Generate README.md
        print("\n📝 Generating README.md...")
        asyncio.run(generate_readme(project_name, project_type, prompt, model))

        # Generate Makefile
        print("\n📝 Generating Makefile...")
        asyncio.run(generate_makefile(project_name))

        # Format all Python files with black and isort if tools are available
        if tools_available:
            print("\n🔧 Formatting all project files...")
            try:
                subprocess.run(
                    ["isort", project_name], check=False, capture_output=True
                )
                subprocess.run(
                    ["black", project_name], check=False, capture_output=True
                )
                print("✅ All files formatted successfully!")
            except Exception as e:
                print(f"⚠️ Warning: Could not format all files: {str(e)}")

        print(
            f"\n🎉 Project generation complete! Files are in '{project_name}' directory."
        )
        print("\nNext steps:")
        print(f"  1. cd {project_name}")
        print("  2. pip install -r requirements.txt")
        print("  3. pip install -r requirements-dev.txt  # For development tools")
        print("  4. make test  # Run tests")

    except Exception as e:
        print(f"❌ An error occurred during project generation: {str(e)}")
        import traceback

        traceback.print_exc()


async def generate_gitignore(project_name):
    """Generate a comprehensive .gitignore file."""
    gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*\$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Project specific
.DS_Store
logs/
tmp/
"""

    with open(os.path.join(project_name, ".gitignore"), "w") as f:
        f.write(gitignore_content)

    print(f"📝 .gitignore file created successfully.")


async def generate_conftest(project_name, model=DEFAULT_LLM):
    """Generate a conftest.py file for pytest fixtures."""
    conftest_prompt = """Generate a comprehensive conftest.py file for pytest that includes:

    1. Common fixtures that could be used across multiple test files
    2. Appropriate pytest configuration
    3. Database fixture with appropriate cleanup if relevant
    4. Mock fixtures for external dependencies

    Make it well-structured with clear docstrings explaining each fixture.
    """

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool, lambda: ollama.generate(model=model, prompt=conftest_prompt)
        )

    # Extract code
    response_text = response["response"]
    if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
        conftest_code = (
            response_text.split("```python", 1)[1].split("```", 1)[0].strip()
        )
    elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
        conftest_code = response_text.split("```", 1)[1].split("```", 1)[0].strip()
    else:
        conftest_code = response_text

    # Format code
    formatted_code = await format_code(conftest_code)

    # Save to file
    conftest_path = os.path.join(project_name, "tests", "conftest.py")
    os.makedirs(os.path.dirname(conftest_path), exist_ok=True)

    with open(conftest_path, "w") as f:
        f.write('"""\nPytest fixtures for the project.\n"""\n\n')
        f.write(formatted_code)

    print(f"✅ conftest.py created successfully.")


if __name__ == "__main__":
    print("🔧 Python Application Generator 🔧")
    print("====================================")
    user_input = input("Describe the Python application you want to generate:\n")

    # List available models from Ollama
    try:
        models_list = ollama.list()
        available_models = [model["name"] for model in models_list.get("models", [])]
        if available_models:
            print(f"\nAvailable models: {', '.join(available_models)}")
        else:
            print(f"\nNo models found. Will use default: {DEFAULT_LLM}")
    except:
        print(f"\nCould not retrieve model list. Will use default: {DEFAULT_LLM}")

    chosen_model = (
        input(f"Choose an LLM model (default is '{DEFAULT_LLM}'): ") or DEFAULT_LLM
    )
    generate_code(user_input, chosen_model)
