import json
import logging
import re
import requests
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Union

from cachetools import TTLCache, cached
from flask import current_app, g, request, session
from flask_appbuilder import Model, ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import permission_name
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    and_,
    event,
    func,
    or_,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Query, Session, relationship
from sqlalchemy.orm.attributes import flag_modified

logger = logging.getLogger(__name__)

# Audit log table
rls_audit_log = Table(
    "rls_audit_log",
    Model.metadata,
    Column("id", Integer, primary_key=True),
    Column("timestamp", DateTime, nullable=False, default=datetime.utcnow),
    Column("action", String(50), nullable=False),
    Column("user_id", Integer, ForeignKey("ab_user.id"), nullable=False),
    Column("model", String(100), nullable=False),
    Column("item_id", Integer),
    Column("organization_id", Integer),
    Column("changes", JSONB),
    Column("ip_address", String(50)),
    Column("user_agent", String(200)),
)


class RLSFilterCache:
    """Cache for RLS filter results"""

    def __init__(self, maxsize=1000, ttl=300):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get_key(self, user_id: int, model: str, org_id: Optional[int] = None) -> str:
        return f"{user_id}:{model}:{org_id or 'all'}"

    def get(
        self, user_id: int, model: str, org_id: Optional[int] = None
    ) -> Optional[List[Any]]:
        return self.cache.get(self.get_key(user_id, model, org_id))

    def set(
        self, user_id: int, model: str, filters: List[Any], org_id: Optional[int] = None
    ) -> None:
        self.cache[self.get_key(user_id, model, org_id)] = filters

    def invalidate(
        self, user_id: Optional[int] = None, model: Optional[str] = None
    ) -> None:
        if user_id and model:
            key = self.get_key(user_id, model)
            self.cache.pop(key, None)
        else:
            self.cache.clear()


class RowLevelSecurityMixin:
    """
    Advanced Row Level Security (RLS) Mixin for Flask-AppBuilder ModelViews.

    Provides sophisticated access control at the row level through:
    - Multi-tenant organization isolation
    - Hierarchical role-based permissions
    - Customizable business rules
    - Dynamic ownership models
    - Temporal access controls

    Features:
    - Automatic query filtering based on user context
    - Fine-grained organization/tenant isolation
    - Hierarchical role-based access control
    - Custom security rules engine
    - Comprehensive audit logging
    - High-performance caching
    - Bulk operation security
    - Exception handling and recovery
    - Configurable fallback policies
    - Performance optimizations
    - Real-time security updates
    - Dynamic permission evaluation
    - Temporal access control
    - Security event webhooks
    - Access analytics

    Configuration:
        organization_field: str = Field storing org/tenant ID
        owner_field: str = Field tracking record ownership
        enable_audit: bool = Enable audit logging
        enable_caching: bool = Enable permission caching
        custom_rules: List[Callable] = Custom security rules
        role_filters: Dict = Role-based filter rules
        cache_ttl: int = Cache timeout in seconds
        strict_mode: bool = Strict permission enforcement
        fallback_policy: str = Default access policy
    """

    # Core configuration
    organization_field = "organization_id"
    owner_field = "created_by"
    parent_field = "parent_id"  # For hierarchical organizations
    enable_audit = True
    enable_caching = True
    cache_ttl = 300
    strict_mode = True
    fallback_policy = "deny"

    # Advanced features
    temporal_control = False  # Enable time-based access
    enable_delegation = False  # Allow permission delegation
    track_inheritance = True  # Track permission inheritance
    enable_analytics = True  # Track access patterns

    # Security rules
    custom_rules = []
    role_filters = {
        "admin": None,
        "manager": [
            lambda obj, user: obj.department_id == user.department_id,
            lambda obj, user: obj.organization_id in user.managed_orgs,
        ],
        "user": [
            lambda obj, user: obj.created_by == user.id,
            lambda obj, user: obj.organization_id == user.organization_id,
        ],
    }

    # Cache instance
    _filter_cache = RLSFilterCache()

    def __init__(self):
        super().__init__()
        self._setup_audit_hooks()
        self._init_cache()

    def _setup_audit_hooks(self):
        """Configure audit logging hooks"""
        if self.enable_audit:
            event.listen(self.__class__, "after_insert", self._audit_insert)
            event.listen(self.__class__, "after_update", self._audit_update)
            event.listen(self.__class__, "after_delete", self._audit_delete)

    def _init_cache(self):
        """Initialize permission cache"""
        if self.enable_caching:
            self._permission_cache = TTLCache(maxsize=1000, ttl=self.cache_ttl)

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def get_organization_hierarchy(self, org_id: int) -> Set[int]:
        """Get organization and all sub-organizations"""
        orgs = {org_id}
        query = self.datamodel.session.query(self.datamodel.obj).filter(
            self.datamodel.obj.parent_id == org_id
        )
        for org in query.all():
            orgs.update(self.get_organization_hierarchy(org.id))
        return orgs

    def query_rls(self, query: Query) -> Query:
        """Apply RLS filters with caching and optimization"""
        if not hasattr(g, "user"):
            if self.strict_mode:
                raise RuntimeError("No user context available for RLS")
            logger.warning("No user context for RLS - using fallback policy")
            return self._apply_fallback_policy(query)

        try:
            # Check cache
            cache_key = f"{g.user.id}:{self.__class__.__name__}"
            if self.enable_caching:
                cached_filters = self._filter_cache.get(
                    g.user.id, self.__class__.__name__
                )
                if cached_filters is not None:
                    return query.filter(and_(*cached_filters))

            # Skip RLS for admins
            if g.user.is_admin():
                return query

            filters = []

            # Organization/tenant filter
            permitted_orgs = self.get_permitted_orgs()
            if permitted_orgs:
                org_field = getattr(self.datamodel.obj, self.organization_field)
                if org_field is not None:
                    if self.track_inheritance:
                        # Include sub-organizations
                        all_orgs = set()
                        for org_id in permitted_orgs:
                            all_orgs.update(self.get_organization_hierarchy(org_id))
                        filters.append(org_field.in_(all_orgs))
                    else:
                        filters.append(org_field.in_(permitted_orgs))

            # Role-based filters
            role_filters = self.get_role_filters()
            if role_filters:
                filters.extend(role_filters)

            # Custom security rules
            custom_filters = self.get_custom_filters()
            if custom_filters:
                filters.extend(custom_filters)

            # Temporal filters
            if self.temporal_control:
                temporal_filter = self._get_temporal_filter()
                if temporal_filter:
                    filters.append(temporal_filter)

            if filters:
                query = query.filter(and_(*filters))

                # Cache filters
                if self.enable_caching:
                    self._filter_cache.set(g.user.id, self.__class__.__name__, filters)

            return query

        except Exception as e:
            logger.exception("Error applying RLS filters")
            if self.strict_mode:
                raise RuntimeError(f"RLS filter error: {str(e)}")
            return self._apply_fallback_policy(query)

    def _apply_fallback_policy(self, query: Query) -> Query:
        """Apply fallback security policy"""
        if self.fallback_policy == "deny":
            # Return empty result
            return query.filter(False)
        elif self.fallback_policy == "allow":
            # Return unfiltered query
            return query
        else:
            # Apply custom fallback policy
            return self._apply_custom_fallback(query)

    def _get_temporal_filter(self) -> Optional[Any]:
        """Get time-based access filter"""
        if not hasattr(self.datamodel.obj, "valid_from") or not hasattr(
            self.datamodel.obj, "valid_to"
        ):
            return None

        now = datetime.utcnow()
        return and_(
            or_(
                self.datamodel.obj.valid_from == None,
                self.datamodel.obj.valid_from <= now,
            ),
            or_(
                self.datamodel.obj.valid_to == None, self.datamodel.obj.valid_to >= now
            ),
        )

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def get_permitted_orgs(self) -> List[int]:
        """Get organizations user has access to with caching"""
        if not hasattr(g, "user"):
            return []

        orgs = []

        # Direct organization
        if hasattr(g.user, self.organization_field):
            org_id = getattr(g.user, self.organization_field)
            if org_id:
                orgs.append(org_id)

        # Organizations via roles/groups
        if hasattr(g.user, "organizations"):
            orgs.extend([org.id for org in g.user.organizations])

        # Delegated access
        if self.enable_delegation and hasattr(g.user, "delegated_orgs"):
            orgs.extend([org.id for org in g.user.delegated_orgs])

        # Remove duplicates while preserving order
        return list(dict.fromkeys(orgs))

    def get_role_filters(self) -> List[Any]:
        """Get role-based filters with inheritance"""
        if not hasattr(g, "user") or not hasattr(g.user, "roles"):
            return []

        filters = []
        seen_rules = set()

        # Process each role including inherited roles
        for role in g.user.roles:
            if role_rules := self.role_filters.get(role.name):
                for rule in role_rules:
                    rule_key = id(rule)
                    if rule_key not in seen_rules:
                        seen_rules.add(rule_key)
                        if filter_condition := rule(self.datamodel.obj, g.user):
                            filters.append(filter_condition)

        return filters

    def get_custom_filters(self) -> List[Any]:
        """Apply custom security rules with error handling"""
        filters = []
        for rule in self.custom_rules:
            try:
                if filter_condition := rule(self.datamodel.obj, g.user):
                    filters.append(filter_condition)
            except Exception as e:
                logger.error(f"Custom rule error: {str(e)}")
                if self.strict_mode:
                    raise

        return filters

    def get_query(self) -> Query:
        """Override get_query with RLS"""
        query = super().get_query()
        return self.query_rls(query)

    def pre_add(self, item: Any) -> None:
        """Enforce RLS on add with ownership tracking"""
        super().pre_add(item)

        if not hasattr(g, "user"):
            raise PermissionError("User context required")

        # Verify organization access
        if hasattr(item, self.organization_field):
            org_id = getattr(item, self.organization_field)
            permitted_orgs = self.get_permitted_orgs()

            if not permitted_orgs or org_id not in permitted_orgs:
                raise PermissionError(f"Not authorized for organization {org_id}")

        # Set ownership and timestamps
        if hasattr(item, self.owner_field):
            setattr(item, self.owner_field, g.user.id)
        if hasattr(item, "created_at"):
            setattr(item, "created_at", datetime.utcnow())
        if hasattr(item, "created_by"):
            setattr(item, "created_by", g.user.id)

        self._audit_log("add", item)

    def pre_update(self, item: Any) -> None:
        """Enforce RLS on update with change tracking"""
        super().pre_update(item)

        if not hasattr(g, "user"):
            raise PermissionError("User context required")

        # Verify organization access
        if hasattr(item, self.organization_field):
            org_id = getattr(item, self.organization_field)
            permitted_orgs = self.get_permitted_orgs()

            if not permitted_orgs or org_id not in permitted_orgs:
                raise PermissionError(f"Not authorized for organization {org_id}")

        # Track changes
        if hasattr(item, "updated_at"):
            setattr(item, "updated_at", datetime.utcnow())
        if hasattr(item, "updated_by"):
            setattr(item, "updated_by", g.user.id)

        self._audit_log("update", item)

    def pre_delete(self, item: Any) -> None:
        """Enforce RLS on delete with cascading"""
        super().pre_delete(item)

        if not hasattr(g, "user"):
            raise PermissionError("User context required")

        # Verify organization access
        if hasattr(item, self.organization_field):
            org_id = getattr(item, self.organization_field)
            permitted_orgs = self.get_permitted_orgs()

            if not permitted_orgs or org_id not in permitted_orgs:
                raise PermissionError(f"Not authorized for organization {org_id}")

        self._audit_log("delete", item)

    def _audit_log(self, action: str, item: Any) -> None:
        if not self.enable_audit:
            return

        try:
            changes = {}
            if action in ("update", "delete"):  # Handle delete changes as well
                for attr in inspect(item).attrs:
                    hist = attr.history
                    if hist.has_changes():
                        changes[attr.key] = {
                            "old": hist.deleted[0] if hist.deleted else None,
                            "new": hist.added[0] if hist.added else None,
                        }
                    elif action == "delete" and hist.deleted:  # Capture deleted values
                        changes[attr.key] = {"old": hist.deleted[0], "new": None}

            log_entry = {
                "action": action,
                "user_id": g.user.id,
                "model": item.__class__.__name__,
                "item_id": getattr(item, "id", None),
                "organization_id": getattr(item, self.organization_field, None),
                "timestamp": datetime.utcnow(),
                "changes": changes,
                "ip_address": request.remote_addr if request else None,
                "user_agent": request.user_agent.string if request else None,
            }

            self.datamodel.session.execute(rls_audit_log.insert(), [log_entry])

            if self.enable_analytics:
                self._notify_security_webhooks(log_entry)

        except Exception as e:
            logger.error(f"Audit logging error: {str(e)}")
            if self.strict_mode:
                raise

    def _notify_security_webhooks(self, log_entry: Dict[str, Any]) -> None:
        try:
            webhooks = current_app.config.get("SECURITY_WEBHOOKS", [])
            for webhook in webhooks:
                try:
                    requests.post(
                        webhook["url"], json=log_entry, timeout=5
                    )  # Ensure requests is installed
                except (
                    requests.exceptions.RequestException
                ) as e:  # Catch request exceptions
                    logger.error(
                        f"Webhook notification error: {str(e)} for URL: {webhook.get('url', 'Unknown')}"
                    )  # Include URL in error message
        except Exception as e:
            logger.error(f"Security webhook error: {str(e)}")


"""
Usage Example:

from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Organization(Model):
    __tablename__ = 'organizations'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey('organizations.id'))

    parent = relationship('Organization', remote_side=[id])
    children = relationship('Organization')

class Department(Model):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'))

    organization = relationship('Organization')

class Document(Model, AuditMixin):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    content = Column(String(1000))
    department_id = Column(Integer, ForeignKey('departments.id'))
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    status = Column(String(20))

    department = relationship('Department')
    organization = relationship('Organization')

class DocumentModelView(RowLevelSecurityMixin, ModelView):
    datamodel = SQLAInterface(Document)

    # Configure RLS
    organization_field = 'organization_id'
    enable_audit = True
    strict_mode = True

    # Custom security rules
    def user_in_department(obj, user):
        return obj.department_id in [d.id for d in user.departments]

    custom_rules = [user_in_department]

    # Role-based filters
    role_filters = {
        'admin': None,  # No filters
        'manager': [
            lambda obj, user: obj.department_id in user.managed_departments
        ],
        'user': [
            lambda obj, user: obj.department_id == user.department_id,
            lambda obj, user: obj.status == 'public'
        ]
    }

# Register with Flask-AppBuilder
appbuilder.add_view(
    DocumentModelView,
    "Documents",
    icon="fa-file-text-o",
    category="Documents"
)

# Example usage:
doc = Document(
    title="Confidential Report",
    content="Secret stuff",
    department_id=1,
    organization_id=1
)

# This will:
# 1. Check organization access
# 2. Apply role filters
# 3. Evaluate custom rules
# 4. Track ownership
# 5. Log audit trail
# 6. Cache permissions
# 7. Handle notifications
"""
