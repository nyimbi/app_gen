"""
mixins/__init__.py

This module exposes all mixins and related classes from the mixins directory
in a safe and organized manner for use in Flask-AppBuilder blueprints or apps.

Available mixins and classes:
- From base_mixin: BaseModelMixin
- From doc_mixin: DocMixin
- From notification_system: Notification, NotificationManager
- From place_mixin: PlaceMixin
- From project_mixin: ProjectMixin
- From statemachine_mixin: StateMachineMixin, State, Transition, Workflow

Usage:
from mixins import BaseModelMixin, DocMixin, PlaceMixin, ProjectMixin, StateMachineMixin
from mixins import Notification, NotificationManager
from mixins import State, Transition, Workflow

For detailed documentation on each mixin, use the `get_mixin_info` function.
"""

from typing import Dict, Any, List, Callable
import importlib
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Version information
__version__ = '1.1.0'

# Lazy loading setup
_lazy_imports = {
    'BaseModelMixin': ('.base_mixin', 'BaseModelMixin'),
    'DocMixin': ('.doc_mixin', 'DocMixin'),
    'Notification': ('.notification_system', 'Notification'),
    'NotificationManager': ('.notification_system', 'NotificationManager'),
    'PlaceMixin': ('.place_mixin', 'PlaceMixin'),
    'ProjectMixin': ('.project_mixin', 'ProjectMixin'),
    'StateMachineMixin': ('.statemachine_mixin', 'StateMachineMixin'),
    'State': ('.statemachine_mixin', 'State'),
    'Transition': ('.statemachine_mixin', 'Transition'),
    'Workflow': ('.statemachine_mixin', 'Workflow'),
}


def __getattr__(name: str) -> Any:
    """Lazy import handler"""
    if name in _lazy_imports:
        module_name, class_name = _lazy_imports[name]
        module = importlib.import_module(module_name, package=__name__)
        return getattr(module, class_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Define __all__ to explicitly specify what gets imported with "from mixins import *"
__all__ = list(_lazy_imports.keys()) + ['init_app', 'get_mixin_info', 'register_mixin']

# Mixin registry for additional information
_mixin_registry: Dict[str, Dict[str, Any]] = {}


def register_mixin(name: str, description: str, dependencies: List[str] = None) -> None:
    """
    Register a mixin with additional information.

    Args:
        name (str): Name of the mixin
        description (str): Brief description of the mixin
        dependencies (List[str], optional): List of other mixins this one depends on
    """
    _mixin_registry[name] = {
        'description': description,
        'dependencies': dependencies or []
    }


def get_mixin_info(mixin_name: str) -> Dict[str, Any]:
    """
    Get information about a specific mixin.

    Args:
        mixin_name (str): Name of the mixin

    Returns:
        Dict[str, Any]: Information about the mixin
    """
    if mixin_name not in _mixin_registry:
        raise ValueError(f"No information available for mixin: {mixin_name}")
    return _mixin_registry[mixin_name]


def init_app(app: Any, mixins: List[str] = None) -> None:
    """
    Initialize the mixins with the Flask app.

    Args:
        app: Flask application instance
        mixins (List[str], optional): List of mixin names to initialize. If None, initialize all.
    """
    mixins_to_init = mixins or list(_lazy_imports.keys())
    for mixin_name in mixins_to_init:
        try:
            mixin = __getattr__(mixin_name)
            if hasattr(mixin, 'init_app'):
                mixin.init_app(app)
                logger.info(f"Initialized mixin: {mixin_name}")
            else:
                logger.debug(f"Mixin {mixin_name} has no init_app method")
        except Exception as e:
            logger.error(f"Error initializing mixin {mixin_name}: {str(e)}")


# Register mixins with their information
register_mixin('BaseModelMixin', 'Provides base functionality for all models')
register_mixin('DocMixin', 'Adds document management capabilities to models')
register_mixin('PlaceMixin', 'Adds geographical information to models')
register_mixin('ProjectMixin', 'Adds project management features to models')
register_mixin('StateMachineMixin', 'Implements state machine functionality for models',
               dependencies=['BaseModelMixin'])

# Cleanup namespace
del Dict, Any, List, Callable, importlib, logging
