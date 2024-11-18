#!/usr/bin/env python3
"""
PostgreSQL Database Schema Introspector
=====================================

This module provides comprehensive PostgreSQL-specific database schema introspection for the
Flask-AppBuilder code generator. It analyzes database structure, relationships, and
constraints to provide detailed information needed for model generation.

Key Features:
    - Full PostgreSQL type system support
    - Extended index types (B-tree, GiST, GIN, BRIN, etc.)
    - Inheritance and partitioning
    - JSONB and array types
    - Materialized views and foreign tables
    - RLS policies and security
    - Custom types and domains
    - Table spaces and storage parameters
    - Extended constraints and exclusion support
    - Performance optimization using native catalog queries

The module maintains context throughout the introspection process, ensuring that
all gathered information is properly organized and accessible for the model
generation phase.

PostgreSQL-Specific Features:
    - Native enum types
    - Array types
    - Range types
    - Composite types
    - Domains
    - Inheritance
    - Partitioning
    - Tablespaces
    - RLS policies
    - Foreign tables
    - Materialized views
    - Custom procedures
    - Extensions

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

import logging
from typing import List, Dict, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from collections import defaultdict

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.engine.url import URL
from sqlalchemy.sql.type_api import TypeEngine

from model_generator.config.base_config import DatabaseConfig
from model_generator.core.context import (
    GenerationContext,
    TableInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    ConstraintInfo,
    Relationship,
    DatabaseType,
    AutoIncrementType,
    TableType,
    IndexMethod,
    PartitionBoundSpec,
    IndexColumnInfo,
    ExclusionElement,
    TablespaceInfo,
    InheritanceInfo,
    RelationshipType,
    JoinCondition,
    OnUpdateAction,
    MatchType,
    DeferrableType,
    ForeignTableInfo,
    ForeignServerInfo,
    FDWInfo,
    FDWValidation,
)
from model_generator.utils.type_utils import get_sqlalchemy_type_name
from model_generator.utils.case_utils import to_snake_case, to_pascal_case
from model_generator.utils.validation_utils import (
    validate_table_name,
    validate_column_name,
)
from model_generator.exceptions import DatabaseIntrospectionError

# Configure logging
logger = logging.getLogger(__name__)

# PostgreSQL catalog query templates
PG_QUERIES = {
    "table_info": """
        SELECT c.relname as table_name,
               c.relkind as table_type,
               obj_description(c.oid) as comment,
               c.relpersistence as persistence,
               c.relispartition as is_partition,
               c.relpartbound as partition_bound,
               c.reltablespace as tablespace_oid,
               c.relhassubclass as has_children,
               c.relhasoids as has_oids,
               c.relrowsecurity as row_security,
               c.relforcerowsecurity as force_row_security
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s
          AND c.relkind IN ('r', 'p', 'f', 'm', 'v')
    """,
    "column_info": """
        SELECT a.attname as name,
               pg_catalog.format_type(a.atttypid, a.atttypmod) as type_name,
               a.attnotnull as not_null,
               a.atthasdef as has_default,
               pg_get_expr(d.adbin, d.adrelid) as default_value,
               col_description(a.attrelid, a.attnum) as comment,
               a.attidentity as identity,
               a.attgenerated as generated,
               a.attstorage as storage,
               a.attcompression as compression,
               a.attisdropped as is_dropped,
               a.attmissingval as missing_val,
               a.atttypmod as type_modifier,
               t.typtype as type_type,
               t.typarray as array_type,
               t.typcategory as type_category
        FROM pg_attribute a
        JOIN pg_type t ON t.oid = a.atttypid
        LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
        WHERE a.attrelid = %s::regclass
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY a.attnum
    """,
    "constraint_info": """
        SELECT c.conname as name,
               c.contype as type,
               c.conkey as column_numbers,
               c.confkey as foreign_key_numbers,
               c.confrelid as foreign_table_oid,
               c.conrelid as table_oid,
               c.condeferrable as deferrable,
               c.condeferred as deferred,
               c.confupdtype as update_action,
               c.confdeltype as delete_action,
               c.confmatchtype as match_type,
               pg_get_constraintdef(c.oid) as definition
        FROM pg_constraint c
        WHERE c.conrelid = %s::regclass
    """,
    "index_info": """
        SELECT i.relname as name,
               am.amname as method,
               ix.indisunique as is_unique,
               ix.indisprimary as is_primary,
               ix.indkey as column_numbers,
               ix.indclass as opclass_oids,
               pg_get_indexdef(i.oid) as definition,
               obj_description(i.oid) as comment,
               i.reltablespace as tablespace_oid,
               ix.indpred as predicate,
               ix.indnkeyatts as key_columns
        FROM pg_index ix
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_am am ON am.oid = i.relam
        WHERE ix.indrelid = %s::regclass
    """,
    "inheritance_info": """
        SELECT c.relname as parent_name,
               obj_description(c.oid) as comment
        FROM pg_inherits i
        JOIN pg_class c ON c.oid = i.inhparent
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE i.inhrelid = %s::regclass
    """,
    "partition_info": """
        SELECT pg_get_partkeydef(%s::regclass) as partition_key,
               c.relname as parent_name
        FROM pg_class c
        WHERE c.oid = %s::regclass
          AND (c.relispartition OR c.relkind = 'p')
    """,
    "foreign_key_info": """
        SELECT n.nspname as schema_name,
               cl.relname as table_name,
               a.attname as column_name,
               ct.conname as constraint_name,
               f.relname as foreign_table_name,
               fa.attname as foreign_column_name,
               ct.confupdtype as update_action,
               ct.confdeltype as delete_action,
               ct.confmatchtype as match_type
        FROM pg_constraint ct
        JOIN pg_class cl ON cl.oid = ct.conrelid
        JOIN pg_namespace n ON n.oid = cl.relnamespace
        JOIN pg_attribute a ON a.attrelid = ct.conrelid AND a.attnum = ANY(ct.conkey)
        JOIN pg_class f ON f.oid = ct.confrelid
        JOIN pg_attribute fa ON fa.attrelid = ct.confrelid AND fa.attnum = ANY(ct.confkey)
        WHERE ct.contype = 'f'
          AND ct.conrelid = %s::regclass
    """,
    "trigger_info": """
        SELECT t.tgname as name,
               pg_get_triggerdef(t.oid) as definition,
               t.tgenabled as enabled,
               t.tgisinternal as is_internal
        FROM pg_trigger t
        WHERE t.tgrelid = %s::regclass
          AND NOT t.tgisinternal
    """,
    "policy_info": """
        SELECT polname as name,
               polcmd as command,
               polpermissive as permissive,
               polroles as roles,
               polqual as qualifier,
               polwithcheck as with_check
        FROM pg_policy
        WHERE polrelid = %s::regclass
    """,
    "extension_info": """
        SELECT e.extname as name,
               e.extversion as version,
               n.nspname as schema,
               e.extrelocatable as relocatable
        FROM pg_extension e
        JOIN pg_namespace n ON n.oid = e.extnamespace
        WHERE e.extname IN ('postgis', 'hstore', 'uuid-ossp', 'ltree')
    """,
    "rls_policies": """
            SELECT pol.polname as name,
                   pol.polcmd as command,
                   pol.polpermissive as permissive,
                   ARRAY(
                       SELECT rol.rolname
                       FROM pg_roles rol
                       WHERE rol.oid = ANY(pol.polroles)
                   ) as roles,
                   pg_get_expr(pol.polqual, pol.polrelid) as using_expr,
                   pg_get_expr(pol.polwithcheck, pol.polrelid) as with_check_expr,
                   pol.polstart as start_expr,
                   pol.polend as end_expr
            FROM pg_policy pol
            WHERE pol.polrelid = %s::regclass
        """,
    "tablespace_info": """
            SELECT spcname as name,
                   pg_get_userbyid(spcowner) as owner,
                   pg_tablespace_location(oid) as location,
                   spcacl as acl,
                   spcoptions as options
            FROM pg_tablespace
            WHERE oid = %s
        """,
    "storage_params": """
            SELECT reloptions as options,
                   relkind as kind,
                   relpersistence as persistence,
                   relhasoids as has_oids,
                   relam as access_method
            FROM pg_class
            WHERE oid = %s::regclass
        """,
    "extensions": """
            SELECT e.extname as name,
                   e.extversion as version,
                   n.nspname as schema,
                   e.extrelocatable as relocatable,
                   pg_get_userbyid(e.extowner) as owner,
                   e.extconfig as config_tables,
                   e.extcondition as conditions
            FROM pg_extension e
            JOIN pg_namespace n ON n.oid = e.extnamespace
        """,
    "procedures": """
            SELECT p.proname as name,
                   n.nspname as schema,
                   p.prokind as kind,
                   p.provolatile as volatile,
                   p.prorettype::regtype as return_type,
                   p.proargnames as arg_names,
                   p.proargtypes as arg_types,
                   p.proargmodes as arg_modes,
                   p.prosrc as source,
                   d.description as comment,
                   p.proacl as acl,
                   p.proconfig as config
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            LEFT JOIN pg_description d ON d.objoid = p.oid
            WHERE n.nspname = %s
        """,
    "views": """
            SELECT c.relname as name,
                   c.relkind as kind,
                   pg_get_viewdef(c.oid) as definition,
                   c.reloptions as options,
                   d.description as comment,
                   c.relacl as acl,
                   n.nspname as schema
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_description d ON d.objoid = c.oid
            WHERE c.relkind IN ('v', 'm')
              AND n.nspname = %s
        """,
    "sequences": """
            SELECT c.relname as name,
                   s.seqstart as start_value,
                   s.seqincrement as increment,
                   s.seqmin as min_value,
                   s.seqmax as max_value,
                   s.seqcache as cache_size,
                   s.seqcycle as cycles,
                   d.description as comment,
                   c.relacl as acl,
                   pg_get_serial_sequence(
                       a.attrelid::regclass::text,
                       a.attname
                   ) as owned_by
            FROM pg_class c
            JOIN pg_sequence s ON s.seqrelid = c.oid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_depend d_dep ON d_dep.objid = c.oid
            LEFT JOIN pg_attribute a ON
                d_dep.refobjid = a.attrelid AND
                d_dep.refobjsubid = a.attnum
            LEFT JOIN pg_description d ON d.objoid = c.oid
            WHERE c.relkind = 'S'
              AND n.nspname = %s
        """,
    "text_search_config": """
               SELECT
                   c.cfgname as name,
                   p.prsname as parser,
                   d.dictname as dictionary,
                   m.mapdict::regdictionary as target_dict,
                   t.alias as token_type,
                   obj_description(c.oid, 'pg_ts_config') as comment
               FROM pg_ts_config c
               JOIN pg_ts_parser p ON c.cfgparser = p.oid
               LEFT JOIN pg_ts_config_map m ON c.oid = m.mapcfg
               LEFT JOIN pg_ts_dict d ON c.oid = d.dictowner
               LEFT JOIN token_type t ON t.tokid = m.maptokentype
               WHERE c.cfgnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
           """,
    "operator_info": """
               SELECT
                   o.oprname as name,
                   lt.typname as left_type,
                   rt.typname as right_type,
                   rt.typname as result_type,
                   p.proname as procedure_name,
                   com.oprname as commutator,
                   neg.oprname as negator,
                   o.oprrest as restrict_function,
                   o.oprjoin as join_function,
                   o.oprcanhash as can_hash,
                   o.oprcanmerge as can_merge,
                   obj_description(o.oid, 'pg_operator') as comment
               FROM pg_operator o
               LEFT JOIN pg_type lt ON o.oprleft = lt.oid
               LEFT JOIN pg_type rt ON o.oprright = rt.oid
               LEFT JOIN pg_type res ON o.oprresult = res.oid
               LEFT JOIN pg_proc p ON o.oprcode = p.oid
               LEFT JOIN pg_operator com ON o.oprcom = com.oid
               LEFT JOIN pg_operator neg ON o.oprnegate = neg.oid
               WHERE o.oprnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
           """,
    "operator_class_info": """
               SELECT
                   oc.opcname as name,
                   am.amname as index_method,
                   op.oprname as operator_name,
                   p.proname as support_function,
                   oc.opcdefault as is_default,
                   st.typname as storage_type,
                   f.opfname as family_name
               FROM pg_opclass oc
               JOIN pg_am am ON oc.opcmethod = am.oid
               LEFT JOIN pg_operator op ON op.oid = ANY(
                   SELECT objid FROM pg_depend
                   WHERE refobjid = oc.oid AND deptype = 'n'
               )
               LEFT JOIN pg_proc p ON p.oid = ANY(
                   SELECT objid FROM pg_depend
                   WHERE refobjid = oc.oid AND deptype = 'n'
               )
               LEFT JOIN pg_type st ON oc.opcintype = st.oid
               LEFT JOIN pg_opfamily f ON oc.opcfamily = f.oid
               WHERE oc.opcnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
           """,
    "event_triggers": """
               SELECT
                   t.evtname as name,
                   t.evtevent as event_type,
                   t.evtowner::regrole as owner,
                   p.proname as function_name,
                   t.evttags as tags,
                   t.evtenabled as enabled,
                   obj_description(t.oid, 'pg_event_trigger') as comment
               FROM pg_event_trigger t
               JOIN pg_proc p ON t.evtfoid = p.oid
           """,
    "foreign_data_wrappers": """
               SELECT
                   f.fdwname as name,
                   f.fdwhandler::regproc as handler_function,
                   f.fdwvalidator::regproc as validator_function,
                   f.fdwoptions as options,
                   f.fdwacl as acl,
                   obj_description(f.oid, 'pg_foreign_data_wrapper') as comment
               FROM pg_foreign_data_wrapper f
           """,
    "foreign_servers": """
               SELECT
                   s.srvname as name,
                   w.fdwname as wrapper_name,
                   s.srvtype as type,
                   s.srvversion as version,
                   s.srvoptions as options,
                   s.srvacl as acl,
                   obj_description(s.oid, 'pg_foreign_server') as comment
               FROM pg_foreign_server s
               JOIN pg_foreign_data_wrapper w ON s.srvfdw = w.oid
           """,
    "foreign_tables": """
               SELECT
                   c.relname as name,
                   s.srvname as server_name,
                   f.ftoptions as options,
                   array_agg(a.attname) as columns,
                   obj_description(c.oid, 'pg_class') as comment
               FROM pg_foreign_table f
               JOIN pg_class c ON f.ftrelid = c.oid
               JOIN pg_foreign_server s ON f.ftserver = s.oid
               JOIN pg_attribute a ON c.oid = a.attrelid
               WHERE c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
                 AND a.attnum > 0
               GROUP BY c.relname, s.srvname, f.ftoptions, c.oid
           """,
    "full_text_search": """
               SELECT cfgname, cfgparser, dictname, alias
               FROM pg_ts_config
               JOIN pg_ts_parser ON cfgparser = oid
               JOIN pg_ts_dict ON dictname = dictname
               WHERE nspname = %s
           """,
    "custom_operators": """
               SELECT oprname, oprleft, oprright, oprresult, oprcode, oprcom, oprnegate
               FROM pg_operator
               WHERE oprnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
           """,
    "custom_operators": """
               SELECT oprname, oprleft, oprright, oprresult, oprcode, oprcom, oprnegate
               FROM pg_operator
               WHERE oprnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
           """,
    "foreign_data_wrappers": """
               SELECT fdwname, fdwhandler, fdwoptions
               FROM pg_foreign_data_wrapper
           """,
    "foreign_servers": """
               SELECT srvname, srvtype, srvversion, srvoptions
               FROM pg_foreign_server
           """,
    "column_privileges": """
               SELECT grantee, privilege_type, is_grantable
               FROM information_schema.column_privileges
               WHERE table_name = %s
           """,
    "security_labels": """
               SELECT obj_description, security_label
               FROM pg_security_label
               WHERE relname = %s
           """,
    "role_settings": """
               SELECT rolname, rolcanlogin, rolconnlimit
               FROM pg_roles
           """,
}


class PostgreSQLIntrospector:
    """
    PostgreSQL-specific database schema introspector.

    This class provides comprehensive introspection of PostgreSQL databases,
    including advanced features like inheritance, partitioning, and custom types.
    """

    def __init__(self, config: DatabaseConfig):
        """Initialize the PostgreSQL introspector."""
        self.config = config
        self.engine = self._create_engine()
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.contexts: Dict[str, GenerationContext] = {}

        # Initialize native connection for optimized catalog queries
        self.connection = None
        self._init_connection()

        try:
            self.metadata.reflect(bind=self.engine)
        except Exception as e:
            raise DatabaseIntrospectionError(
                f"Failed to reflect database metadata: {e}"
            ) from e

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with PostgreSQL-specific configurations."""
        try:
            connect_args = {
                "client_encoding": "utf8",
                "application_name": "FAB Model Generator",
            }

            return create_engine(
                self.config.uri,
                pool_size=self.config.connection_pool_size,
                pool_timeout=self.config.connection_timeout,
                pool_pre_ping=True,
                connect_args=connect_args,
                isolation_level="REPEATABLE READ",  # Ensure consistent reads
            )
        except Exception as e:
            raise DatabaseIntrospectionError(
                f"Failed to create database engine: {e}"
            ) from e

    def _init_connection(self) -> None:
        """Initialize native psycopg2 connection for catalog queries."""
        try:
            self.connection = psycopg2.connect(
                str(self.config.uri), cursor_factory=RealDictCursor
            )
            self.connection.set_session(readonly=True, autocommit=True)
        except Exception as e:
            raise DatabaseIntrospectionError(
                f"Failed to create native connection: {e}"
            ) from e

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursors."""
        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def _execute_catalog_query(self, query_name: str, params: tuple) -> List[Dict]:
        """Execute a predefined catalog query."""
        with self._get_cursor() as cur:
            try:
                cur.execute(PG_QUERIES[query_name], params)
                return cur.fetchall()
            except Exception as e:
                logger.error(f"Error executing catalog query {query_name}: {e}")
                return []

    def introspect_schema(self) -> Dict[str, GenerationContext]:
        """Perform complete schema introspection."""
        try:
            logger.info("Beginning PostgreSQL schema introspection...")

            # Get all tables and their types
            tables = self._get_tables()

            # Process each table
            for table_info in tables:
                if not self._should_process_table(table_info["table_name"]):
                    continue

                context = self.analyze_table(table_info)
                self.contexts[table_info["table_name"]] = context

            # Process relationships after all contexts are created
            self._process_relationships()

            # Detect and mark association tables
            self._identify_association_tables()

            # Process advanced features
            self._process_inheritance()
            self._process_partitioning()
            self._process_policies()

            logger.info(
                f"Schema introspection completed. Processed {len(self.contexts)} tables."
            )
            return self.contexts

        except Exception as e:
            raise DatabaseIntrospectionError("Schema introspection failed") from e

    def _get_tables(self) -> List[Dict]:
        """Get all tables in the schema with their types."""
        return self._execute_catalog_query("table_info", (self.config.schema,))

    def analyze_table(self, table_info: Dict) -> GenerationContext:
        """Analyze a table and create its generation context."""
        table_name = table_info["table_name"]
        logger.debug(f"Analyzing table: {table_name}")

        try:
            # Create TableInfo instance
            table = TableInfo(
                name=table_name,
                schema=self.config.schema,
                type=self._get_table_type(table_info),
                columns=self._analyze_columns(table_name),
                primary_key=self._get_primary_key(table_name),
                foreign_keys=self._analyze_foreign_keys(table_name),
                indexes=self._analyze_indices(table_name),
                constraints=self._analyze_constraints(table_name),
                comment=table_info["comment"],
                tablespace=self._get_tablespace_info(table_info),
                inheritance=self._get_inheritance_info(table_name),
                partition_key=self._get_partition_info(table_name, table_info),
                partition_bound=self._get_partition_bound(table_info),
                storage_params=self._get_storage_params(table_name),
                row_security=table_info["row_security"],
                force_row_security=table_info["force_row_security"],
                triggers=self._get_triggers(table_name),
            )

            # Create context
            context = GenerationContext(
                tables=[table], current_table=table, config=self.config
            )

            # Add required imports
            self._add_table_imports(context, table)

            return context

        except Exception as e:
            raise DatabaseIntrospectionError(
                f"Failed to analyze table '{table_name}': {e}"
            ) from e

    def _get_table_type(self, table_info: Dict) -> TableType:
        """Determine the table type from PostgreSQL relkind."""
        kind_mapping = {
            "r": TableType.REGULAR,
            "p": TableType.PARTITIONED,
            "f": TableType.FOREIGN,
            "m": TableType.MATERIALIZED,
            "t": TableType.TEMPORARY,
        }

        if table_info["persistence"] == "u":
            return TableType.UNLOGGED

        return kind_mapping.get(table_info["table_type"], TableType.REGULAR)

    def _analyze_columns(self, table_name: str) -> List[ColumnInfo]:
        """Analyze columns with PostgreSQL-specific features."""
        columns = []
        column_data = self._execute_catalog_query("column_info", (table_name,))

        for col in column_data:
            try:
                auto_increment = self._get_auto_increment_type(col)

                column = ColumnInfo(
                    name=col["name"],
                    type_name=col["type_name"],
                    nullable=not col["not_null"],
                    primary_key=False,  # Set later when processing constraints
                    default=self._parse_default_value(col["default_value"]),
                    max_length=self._get_type_length(col["type_modifier"]),
                    precision=self._get_type_precision(col["type_modifier"]),
                    scale=self._get_type_scale(col["type_modifier"]),
                    comment=col["comment"],
                    auto_increment=auto_increment,
                    generated=col["generated"] if col["generated"] != " " else None,
                    collation=self._get_column_collation(table_name, col["name"]),
                    storage_params={"storage": col["storage"]}
                    if col["storage"] != "p"
                    else {},
                )

                # Handle array types
                if col["array_type"]:
                    column.type_name += "[]"

                columns.append(column)

            except Exception as e:
                logger.error(f"Error processing column {col['name']}: {e}")
                continue

        return columns

    def _get_auto_increment_type(self, column_data: Dict) -> AutoIncrementType:
        """Determine auto-increment type for a column."""
        if column_data["identity"]:
            return AutoIncrementType.IDENTITY
        if "nextval" in (column_data["default_value"] or ""):
            return AutoIncrementType.SERIAL
        return AutoIncrementType.NONE

    def _parse_default_value(self, default: Optional[str]) -> Optional[Any]:
        """Parse PostgreSQL default value expression."""
        if not default:
            return None

        # Handle common cases
        if default.startswith("nextval("):
            return None  # Skip sequence defaults
        if default == "CURRENT_TIMESTAMP":
            return "func.now()"
        if default == "CURRENT_DATE":
            return "func.current_date()"
        if default.startswith("'") and default.endswith("'"):
            return default[1:-1]  # Strip quotes

        return default

    def _get_type_length(self, type_modifier: int) -> Optional[int]:
        """Extract length from type modifier."""
        if type_modifier == -1:
            return None
        return (type_modifier - 4) & 0xFFFF

    def _get_type_precision(self, type_modifier: int) -> Optional[int]:
        """Extract precision from type modifier."""
        if type_modifier == -1:
            return None
        return ((type_modifier - 4) >> 16) & 0xFFFF

    def _get_type_scale(self, type_modifier: int) -> Optional[int]:
        """Extract scale from type modifier."""
        if type_modifier == -1:
            return None
        return (type_modifier - 4) & 0xFFFF

    def _get_column_collation(self, table_name: str, column_name: str) -> Optional[str]:
        """Get column collation if not default."""
        with self._get_cursor() as cur:
            cur.execute(
                """
                SELECT c.collname
                FROM pg_attribute a
                JOIN pg_collation c ON a.attcollation = c.oid
                WHERE a.attrelid = %s::regclass
                  AND a.attname = %s
                  AND c.collname != 'default'
            """,
                (table_name, column_name),
            )
            result = cur.fetchone()
            return result["collname"] if result else None

    def _analyze_constraints(self, table_name: str) -> List[ConstraintInfo]:
        """Analyze PostgreSQL constraints with full feature support."""
        constraints = []
        constraint_data = self._execute_catalog_query("constraint_info", (table_name,))

        for const in constraint_data:
            try:
                constraint = ConstraintInfo(
                    name=const["name"],
                    constraint_type=self._get_constraint_type(const["type"]),
                    columns=self._get_constraint_columns(
                        table_name, const["column_numbers"]
                    ),
                    definition=const["definition"],
                    deferrable=self._get_deferrable_status(const),
                    validated=True,  # Always true for PostgreSQL
                    enabled=True,
                    comment=None,  # PostgreSQL doesn't support constraint comments
                    index_tablespace=None,  # Set during index analysis
                    exclusion_elements=self._get_exclusion_elements(const)
                    if const["type"] == "x"
                    else [],
                )
                constraints.append(constraint)

            except Exception as e:
                logger.error(f"Error processing constraint {const['name']}: {e}")
                continue

        return constraints

    def _get_constraint_type(self, pg_type: str) -> str:
        """Map PostgreSQL constraint type to ConstraintType."""
        type_map = {
            "p": "PRIMARY KEY",
            "u": "UNIQUE",
            "f": "FOREIGN KEY",
            "c": "CHECK",
            "x": "EXCLUDE",
        }
        return type_map.get(pg_type, "CHECK")

    def _get_constraint_columns(
        self, table_name: str, column_numbers: List[int]
    ) -> List[str]:
        """Get column names from constraint column numbers."""
        with self._get_cursor() as cur:
            cur.execute(
                """
                SELECT attname
                FROM pg_attribute
                WHERE attrelid = %s::regclass
                  AND attnum = ANY(%s)
                ORDER BY array_position(%s, attnum)
            """,
                (table_name, column_numbers, column_numbers),
            )
            return [row["attname"] for row in cur.fetchall()]

    def _get_deferrable_status(self, constraint_data: Dict) -> DeferrableType:
        """Determine constraint deferrable status."""
        if not constraint_data["deferrable"]:
            return DeferrableType.NOT_DEFERRABLE
        return (
            DeferrableType.DEFERRED
            if constraint_data["deferred"]
            else DeferrableType.IMMEDIATE
        )

    def _get_exclusion_elements(self, constraint_data: Dict) -> List[ExclusionElement]:
        """Parse exclusion constraint elements."""
        # This requires parsing the constraint definition
        # Example: EXCLUDE USING gist (circle WITH &&)
        elements = []
        if "EXCLUDE" in constraint_data["definition"]:
            # Parse the definition to extract elements
            # This is a simplified version - real implementation would need
            # more robust parsing
            pass
        return elements

    def _analyze_indices(self, table_name: str) -> List[IndexInfo]:
        """Analyze PostgreSQL indices with all supported types."""
        indices = []
        index_data = self._execute_catalog_query("index_info", (table_name,))

        for idx in index_data:
            try:
                method = self._get_index_method(idx["method"])

                index = IndexInfo(
                    name=idx["name"],
                    column_names=self._get_index_columns(
                        table_name, idx["column_numbers"]
                    ),
                    is_unique=idx["is_unique"],
                    method=method,
                    index_type=self._get_index_type(idx),
                    columns=self._get_index_column_info(table_name, idx),
                    include_columns=self._get_index_included_columns(idx["definition"]),
                    tablespace=self._get_index_tablespace(idx["tablespace_oid"]),
                    where_clause=self._get_index_predicate(idx["predicate"]),
                    concurrent=False,  # Set during creation, not stored
                    fillfactor=self._get_index_fillfactor(idx["definition"]),
                    comment=idx["comment"],
                )

                indices.append(index)

            except Exception as e:
                logger.error(f"Error processing index {idx['name']}: {e}")
                continue

        return indices

    def _get_index_method(self, pg_method: str) -> IndexMethod:
        """Map PostgreSQL index method to IndexMethod."""
        method_map = {
            "btree": IndexMethod.BTREE,
            "hash": IndexMethod.HASH,
            "gist": IndexMethod.GIST,
            "gin": IndexMethod.GIN,
            "spgist": IndexMethod.SPGIST,
            "brin": IndexMethod.BRIN,
            "bloom": IndexMethod.BLOOM,
        }
        return method_map.get(pg_method, IndexMethod.BTREE)

    def _get_index_type(self, index_data: Dict) -> IndexType:
        """Determine index type from PostgreSQL index properties."""
        if index_data["is_primary"]:
            return IndexType.PRIMARY
        if index_data["is_unique"]:
            return IndexType.UNIQUE
        if index_data["predicate"]:
            return IndexType.PARTIAL
        return IndexType.NORMAL

    def _get_index_column_info(
        self, table_name: str, index_data: Dict
    ) -> List[IndexColumnInfo]:
        """Create detailed IndexColumnInfo objects for index columns."""
        columns = []
        col_names = self._get_index_columns(table_name, index_data["column_numbers"])

        for col_name in col_names:
            columns.append(
                IndexColumnInfo(
                    name=col_name,
                    ascending=True,  # Would need additional catalog query for sort direction
                    nulls_order=NullsOrder.DEFAULT,
                    collation=None,  # Would need additional catalog query
                    opclass=None,  # Would need additional catalog query
                )
            )

        return columns

    def _get_inheritance_info(self, table_name: str) -> Optional[InheritanceInfo]:
        """Get table inheritance information."""
        inheritance_data = self._execute_catalog_query(
            "inheritance_info", (table_name,)
        )

        if inheritance_data:
            parent = inheritance_data[0]
            return InheritanceInfo(
                parent_table=parent["parent_name"],
                columns=self._get_inherited_columns(table_name),
                constraints=self._get_inherited_constraints(table_name),
                storage_params={},  # Would need additional queries for storage params
            )

        return None

    def _get_partition_info(
        self, table_name: str, table_info: Dict
    ) -> Optional[PartitionBoundSpec]:
        """Get table partitioning information."""
        if not table_info["is_partition"] and "p" != table_info["table_type"]:
            return None

        partition_data = self._execute_catalog_query(
            "partition_info", (table_name, table_name)
        )

        if partition_data:
            data = partition_data[0]
            # Parse partition key definition to determine strategy and bounds
            # This is a simplified version - real implementation would need more parsing
            return PartitionBoundSpec(
                strategy=PartitioningStrategy.RANGE,  # Would need parsing to determine
                columns=[],  # Would need parsing to extract
                bounds=[],  # Would need parsing to extract
            )

        return None

    def _process_relationships(self) -> None:
        """Process and resolve all relationships between tables."""
        try:
            relationships = []

            # Process foreign key relationships
            for table_name, context in self.contexts.items():
                fk_relationships = self._analyze_table_relationships(table_name)
                relationships.extend(fk_relationships)

                # Add relationships to context
                for rel in fk_relationships:
                    context.add_relationship(rel)

            # Resolve cycles
            resolver = RelationshipResolver(relationships)
            resolved = resolver.resolve_cycles()

            # Update contexts with resolved relationships
            for table_name, context in self.contexts.items():
                context.relationships = [
                    rel for rel in resolved if rel.source_table == table_name
                ]

        except Exception as e:
            logger.error(f"Error processing relationships: {e}")

    def _analyze_table_relationships(self, table_name: str) -> List[Relationship]:
        """Analyze relationships for a specific table."""
        relationships = []
        fk_data = self._execute_catalog_query("foreign_key_info", (table_name,))

        for fk in fk_data:
            try:
                rel = Relationship(
                    source_table=table_name,
                    target_table=fk["foreign_table_name"],
                    relationship_type=self._determine_relationship_type(fk),
                    foreign_keys=[fk["column_name"]],
                    backref_name=self._generate_backref_name(
                        table_name, fk["foreign_table_name"], fk["column_name"]
                    ),
                    is_nullable=self._is_nullable_fk(table_name, fk["column_name"]),
                    join_conditions=[
                        JoinCondition(
                            local_column=fk["column_name"],
                            remote_column=fk["foreign_column_name"],
                        )
                    ],
                )
                relationships.append(rel)

            except Exception as e:
                logger.error(f"Error analyzing relationship in {table_name}: {e}")

        return relationships

    def _determine_relationship_type(self, fk_data: Dict) -> RelationshipType:
        """Determine relationship type from foreign key metadata."""
        # Check if part of unique constraint
        is_unique = self._is_unique_constraint(
            fk_data["table_name"], fk_data["column_name"]
        )

        if is_unique:
            return RelationshipType.ONE_TO_ONE

        # Check if part of primary key
        is_pk = self._is_primary_key(fk_data["table_name"], fk_data["column_name"])

        if is_pk:
            return RelationshipType.MANY_TO_ONE

        return RelationshipType.ONE_TO_MANY

    def _process_rls_policies(self, table_name: str) -> List[PostgreSQLPolicyInfo]:
        """Process RLS (Row Level Security) policies for a table."""
        policies = []
        policy_data = self._execute_catalog_query("rls_policies", (table_name,))

        for policy in policy_data:
            try:
                policy_info = PostgreSQLPolicyInfo(
                    name=policy["name"],
                    command=policy["command"],
                    permissive=policy["permissive"],
                    roles=policy["roles"],
                    qualifier=policy["using_expr"],
                    with_check=policy["with_check_expr"],
                    timing=("session" if policy["start_expr"] else "static"),
                    using_clause=policy["using_expr"],
                    check_clause=policy["with_check_expr"],
                )
                policies.append(policy_info)
            except Exception as e:
                logger.error(f"Error processing RLS policy {policy['name']}: {e}")
                continue

        return policies

    def _get_tablespace_info(self, table_info: Dict) -> Optional[TablespaceInfo]:
        """Get tablespace information for a table."""
        if not table_info["tablespace_oid"]:
            return None

        try:
            tablespace_data = self._execute_catalog_query(
                "tablespace_info", (table_info["tablespace_oid"],)
            )

            if not tablespace_data:
                return None

            ts_info = tablespace_data[0]
            return TablespaceInfo(
                name=ts_info["name"],
                options=self._parse_tablespace_options(ts_info["options"]),
                index_tablespace=None,  # Set during index analysis if different
            )
        except Exception as e:
            logger.error(f"Error getting tablespace info: {e}")
            return None

    def _get_storage_params(self, table_name: str) -> Dict[str, Any]:
        """Get storage parameters for a table."""
        try:
            storage_data = self._execute_catalog_query("storage_params", (table_name,))

            if not storage_data:
                return {}

            params = storage_data[0]
            return self._parse_storage_options(params["options"], params["kind"])
        except Exception as e:
            logger.error(f"Error getting storage parameters for {table_name}: {e}")
            return {}

    def _process_extensions(self) -> Dict[str, PostgreSQLExtensionInfo]:
        """Process installed PostgreSQL extensions."""
        extensions = {}
        extension_data = self._execute_catalog_query("extensions", tuple())

        for ext in extension_data:
            try:
                ext_info = PostgreSQLExtensionInfo(
                    name=ext["name"],
                    version=ext["version"],
                    schema=ext["schema"],
                    relocatable=ext["relocatable"],
                    config_tables=self._get_extension_config_tables(
                        ext["config_tables"]
                    ),
                    owner=ext["owner"],
                )
                extensions[ext["name"]] = ext_info
            except Exception as e:
                logger.error(f"Error processing extension {ext['name']}: {e}")
                continue

        return extensions

    def _process_procedures(self) -> Dict[str, List[PostgreSQLProcedureInfo]]:
        """Process stored procedures and functions."""
        procedures = defaultdict(list)
        proc_data = self._execute_catalog_query("procedures", (self.config.schema,))

        for proc in proc_data:
            try:
                proc_info = PostgreSQLProcedureInfo(
                    name=proc["name"],
                    schema=proc["schema"],
                    kind=proc["kind"],
                    return_type=proc["return_type"],
                    arguments=self._parse_procedure_arguments(
                        proc["arg_names"], proc["arg_types"], proc["arg_modes"]
                    ),
                    source=proc["source"],
                    comment=proc["comment"],
                    volatility=proc["volatile"],
                    config=proc["config"],
                )
                procedures[proc["schema"]].append(proc_info)
            except Exception as e:
                logger.error(f"Error processing procedure {proc['name']}: {e}")
                continue

        return procedures

    def _process_views(self) -> Dict[str, PostgreSQLViewInfo]:
        """Process views and materialized views."""
        views = {}
        view_data = self._execute_catalog_query("views", (self.config.schema,))

        for view in view_data:
            try:
                view_info = PostgreSQLViewInfo(
                    name=view["name"],
                    definition=view["definition"],
                    materialized=view["kind"] == "m",
                    with_data=True,  # Default for materialized views
                    check_option=self._get_view_check_option(view["options"]),
                    security_barrier="security_barrier" in (view["options"] or []),
                    security_invoker="security_invoker" in (view["options"] or []),
                    comment=view["comment"],
                )
                views[view["name"]] = view_info
            except Exception as e:
                logger.error(f"Error processing view {view['name']}: {e}")
                continue

        return views

    def _process_sequences(self) -> Dict[str, PostgreSQLSequenceInfo]:
        """Process sequences including those used by identity/serial columns."""
        sequences = {}
        seq_data = self._execute_catalog_query("sequences", (self.config.schema,))

        for seq in seq_data:
            try:
                seq_info = PostgreSQLSequenceInfo(
                    name=seq["name"],
                    start_value=seq["start_value"],
                    increment=seq["increment"],
                    min_value=seq["min_value"],
                    max_value=seq["max_value"],
                    cache_size=seq["cache_size"],
                    cycle=seq["cycles"],
                    owned_by=seq["owned_by"],
                )
                sequences[seq["name"]] = seq_info
            except Exception as e:
                logger.error(f"Error processing sequence {seq['name']}: {e}")
                continue

        return sequences

    # Utility methods for parsing and processing

    def _parse_tablespace_options(self, options: List[str]) -> Dict[str, str]:
        """Parse tablespace options into a dictionary."""
        if not options:
            return {}

        result = {}
        for opt in options:
            if "=" in opt:
                key, value = opt.split("=", 1)
                result[key.strip()] = value.strip()
        return result

    def _parse_storage_options(self, options: List[str], kind: str) -> Dict[str, Any]:
        """Parse storage options based on object kind."""
        if not options:
            return {}

        result = {}
        for opt in options:
            if "=" in opt:
                key, value = opt.split("=", 1)
                # Convert values to appropriate types
                if value.isdigit():
                    value = int(value)
                elif value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                result[key.strip()] = value

        # Add kind-specific default parameters
        if kind == "r":  # Regular table
            result.setdefault("fillfactor", 100)
            result.setdefault("toast_tuple_target", 2048)

        return result

    def _get_extension_config_tables(self, config_tables: List[int]) -> List[str]:
        """Get table names configured for an extension."""
        if not config_tables:
            return []

        with self._get_cursor() as cur:
            cur.execute(
                """
                SELECT relname
                FROM pg_class
                WHERE oid = ANY(%s)
            """,
                (config_tables,),
            )
            return [row["relname"] for row in cur.fetchall()]

    def _parse_procedure_arguments(
        self, names: List[str], types: List[int], modes: List[str]
    ) -> List[Dict[str, Any]]:
        """Parse procedure argument information."""
        if not names:
            return []

        arguments = []
        for name, type_oid, mode in zip(names, types, modes or ["i"] * len(names)):
            with self._get_cursor() as cur:
                cur.execute("SELECT pg_catalog.format_type(%s, NULL)", (type_oid,))
                type_name = cur.fetchone()["format_type"]

            arguments.append(
                {
                    "name": name,
                    "type": type_name,
                    "mode": {
                        "i": "IN",
                        "o": "OUT",
                        "b": "INOUT",
                        "v": "VARIADIC",
                        "t": "TABLE",
                    }.get(mode, "IN"),
                }
            )

        return arguments

    def _get_view_check_option(self, options: List[str]) -> Optional[str]:
        """Get view CHECK OPTION if specified."""
        if not options:
            return None

        for opt in options:
            if opt.startswith("check_option="):
                return opt.split("=", 1)[1]
        return None

    # Integration with main introspection flow

    def introspect_schema(self) -> Dict[str, GenerationContext]:
        """Perform complete schema introspection including advanced features."""
        try:
            logger.info("Beginning PostgreSQL schema introspection...")

            # Process basic schema elements
            contexts = super().introspect_schema()

            # Process advanced features
            extensions = self._process_extensions()
            procedures = self._process_procedures()
            views = self._process_views()
            sequences = self._process_sequences()

            # Update contexts with advanced feature information
            for table_name, context in contexts.items():
                # Add RLS policies
                if context.current_table.row_security:
                    context.current_table.policies = self._process_rls_policies(
                        table_name
                    )

                # Add sequences used by the table
                used_sequences = self._get_table_sequences(table_name)
                if used_sequences:
                    context.sequences = {
                        name: sequences[name]
                        for name in used_sequences
                        if name in sequences
                    }

                # Add related procedures
                context.procedures = self._get_table_procedures(table_name, procedures)

                # Add extensions if relevant
                context.extensions = self._get_table_extensions(table_name, extensions)

            logger.info("Advanced feature introspection completed.")
            return contexts

        except Exception as e:
            raise DatabaseIntrospectionError("Schema introspection failed") from e

    def _get_table_sequences(self, table_name: str) -> Set[str]:
        """Get sequences used by a table."""
        with self._get_cursor() as cur:
            cur.execute(
                """
                SELECT d.refobjid::regclass::text as sequence_name
                FROM pg_depend d
                JOIN pg_class c ON c.oid = d.objid
                WHERE d.refobjid::regclass::text LIKE %s
                  AND d.deptype = 'a'
            """,
                (f"{self.config.schema}.%",),
            )
            return {row["sequence_name"] for row in cur.fetchall()}

    def _get_table_procedures(
        self, table_name: str, procedures: Dict[str, List[PostgreSQLProcedureInfo]]
    ) -> List[PostgreSQLProcedureInfo]:
        """Get procedures related to a table."""
        table_procedures = []
        schema_procedures = procedures.get(self.config.schema, [])

        for proc in schema_procedures:
            if table_name.lower() in proc.source.lower():
                table_procedures.append(proc)

        return table_procedures

    def _get_table_extensions(
        self, table_name: str, extensions: Dict[str, PostgreSQLExtensionInfo]
    ) -> List[PostgreSQLExtensionInfo]:
        """Get extensions related to a table."""
        table_extensions = []

        for ext in extensions.values():
            if table_name in ext.config_tables:
                table_extensions.append(ext)

        return table_extensions

    def _process_text_search(self) -> Dict[str, TextSearchInfo]:
        """
        Process full text search configurations.

        Returns:
            Dict[str, TextSearchInfo]: Dictionary of text search configurations
        """
        configs = {}
        try:
            ts_data = self._execute_catalog_query(
                "text_search_config", (self.config.schema,)
            )

            for row in ts_data:
                name = row["name"]
                if name not in configs:
                    configs[name] = TextSearchInfo(
                        name=name,
                        parser=row["parser"],
                        configuration=TextSearchConfiguration(row["parser"]),
                        dictionary=row["dictionary"],
                        mappings={},
                        weights={},
                    )

                # Add token type mapping if present
                if row["token_type"] and row["target_dict"]:
                    configs[name].mappings[row["token_type"]] = row["target_dict"]

            # Get weight configurations
            for config in configs.values():
                weights = self._get_ts_weights(config.name)
                config.weights.update(weights)

        except Exception as e:
            logger.error(f"Error processing text search configurations: {e}")

        return configs

    def _get_ts_weights(self, config_name: str) -> Dict[str, float]:
        """Get text search weights for a configuration."""
        weights = {}
        try:
            with self._get_cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        t.alias as token_type,
                        w.weight as weight
                    FROM pg_ts_config c
                    JOIN pg_ts_config_map m ON c.oid = m.mapcfg
                    JOIN token_type t ON t.tokid = m.maptokentype
                    JOIN ts_weight w ON m.mapseqno = w.ws_num
                    WHERE c.cfgname = %s
                """,
                    (config_name,),
                )
                for row in cur:
                    weights[row["token_type"]] = row["weight"]
        except Exception as e:
            logger.error(f"Error getting text search weights for {config_name}: {e}")

        return weights

    def _process_operators(self) -> Dict[str, OperatorInfo]:
        """
        Process custom operators and operator classes.

        Returns:
            Dict[str, OperatorInfo]: Dictionary of operator information
        """
        operators = {}
        try:
            op_data = self._execute_catalog_query(
                "operator_info", (self.config.schema,)
            )

            for row in op_data:
                name = row["name"]
                operators[name] = OperatorInfo(
                    name=name,
                    left_arg=row["left_type"],
                    right_arg=row["right_type"],
                    result_type=row["result_type"],
                    function=row["procedure_name"],
                    commutator=row["commutator"],
                    negator=row["negator"],
                    restrict=row["restrict_function"],
                    join=row["join_function"],
                    hashes=row["can_hash"],
                    merges=row["can_merge"],
                )

                # Add operator strategies
                strategies = self._get_operator_strategies(name)
                operators[name].strategies = strategies

        except Exception as e:
            logger.error(f"Error processing operators: {e}")

        return operators

    def _get_operator_strategies(self, operator_name: str) -> List[OperatorStrategy]:
        """Get strategies for an operator."""
        strategies = []
        try:
            with self._get_cursor() as cur:
                cur.execute(
                    """
                    SELECT amopstrategy
                    FROM pg_amop
                    WHERE amopopr = (
                        SELECT oid FROM pg_operator WHERE oprname = %s
                    )
                """,
                    (operator_name,),
                )

                strategy_map = {
                    1: OperatorStrategy.SUPPORT,
                    2: OperatorStrategy.RESTRICT,
                    3: OperatorStrategy.JOIN,
                    4: OperatorStrategy.RECHECK,
                }

                for row in cur:
                    if row["amopstrategy"] in strategy_map:
                        strategies.append(strategy_map[row["amopstrategy"]])

        except Exception as e:
            logger.error(f"Error getting operator strategies for {operator_name}: {e}")

        return strategies

    def _process_event_triggers(self) -> Dict[str, EventTriggerInfo]:
        """
        Process event triggers and their configurations.

        Returns:
            Dict[str, EventTriggerInfo]: Dictionary of event trigger information
        """
        triggers = {}
        try:
            trigger_data = self._execute_catalog_query("event_triggers", tuple())

            for row in trigger_data:
                name = row["name"]
                triggers[name] = EventTriggerInfo(
                    name=name,
                    event=TriggerEvent(row["event_type"].lower()),
                    timing=self._get_trigger_timing(name),
                    function=row["function_name"],
                    enabled=row["enabled"] != "D",  # 'D' means disabled
                    roles=self._get_trigger_roles(name),
                    tags=row["tags"] if row["tags"] else [],
                )

                # Get trigger condition if exists
                condition = self._get_trigger_condition(name)
                if condition:
                    triggers[name].condition = condition

        except Exception as e:
            logger.error(f"Error processing event triggers: {e}")

        return triggers

    def _get_trigger_timing(self, trigger_name: str) -> TriggerTiming:
        """Get the timing for an event trigger."""
        try:
            with self._get_cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        CASE
                            WHEN t.tgtype & 2 = 2 THEN 'BEFORE'
                            WHEN t.tgtype & 16 = 16 THEN 'INSTEAD OF'
                            ELSE 'AFTER'
                        END as timing
                    FROM pg_trigger t
                    JOIN pg_event_trigger et ON t.tgname = et.evtname
                    WHERE et.evtname = %s
                """,
                    (trigger_name,),
                )
                row = cur.fetchone()
                return TriggerTiming(row["timing"]) if row else TriggerTiming.AFTER

        except Exception as e:
            logger.error(f"Error getting trigger timing for {trigger_name}: {e}")
            return TriggerTiming.AFTER

    def _get_trigger_roles(self, trigger_name: str) -> List[str]:
        """Get roles that can execute an event trigger."""
        roles = []
        try:
            with self._get_cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        r.rolname
                    FROM pg_event_trigger et
                    JOIN pg_auth_members am ON et.evtowner = am.member
                    JOIN pg_roles r ON am.roleid = r.oid
                    WHERE et.evtname = %s
                """,
                    (trigger_name,),
                )
                roles = [row["rolname"] for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error getting trigger roles for {trigger_name}: {e}")

        return roles

    def _get_trigger_condition(self, trigger_name: str) -> Optional[str]:
        """Get the WHEN condition for an event trigger if it exists."""
        try:
            with self._get_cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        pg_get_triggerdef(t.oid) as definition
                    FROM pg_trigger t
                    JOIN pg_event_trigger et ON t.tgname = et.evtname
                    WHERE et.evtname = %s
                """,
                    (trigger_name,),
                )
                row = cur.fetchone()
                if row:
                    # Extract WHEN clause from trigger definition
                    definition = row["definition"]
                    when_idx = definition.upper().find("WHEN")
                    if when_idx != -1:
                        return definition[when_idx:].split("EXECUTE")[0].strip()

        except Exception as e:
            logger.error(f"Error getting trigger condition for {trigger_name}: {e}")

        return None

    def _process_operator_classes(self) -> Dict[str, OperatorClassInfo]:
        """
        Process operator classes and their details.

        Returns:
            Dict[str, OperatorClassInfo]: Dictionary of operator class information
        """
        op_classes = {}
        try:
            class_data = self._execute_catalog_query(
                "operator_class_info", (self.config.schema,)
            )

            for row in class_data:
                name = row["name"]
                if name not in op_classes:
                    op_classes[name] = OperatorClassInfo(
                        name=name,
                        index_method=row["index_method"],
                        operators=[],
                        functions=[],
                        default=row["is_default"],
                        storage=row["storage_type"],
                        family=row["family_name"],
                    )

                # Add operator if present
                if row["operator_name"]:
                    op_classes[name].operators.append(
                        self.operators.get(row["operator_name"])
                    )

                # Add support function if present
                if row["support_function"]:
                    op_classes[name].functions.append(row["support_function"])

            # Process additional operator class details
            for op_class in op_classes.values():
                self._process_opclass_details(op_class)

        except Exception as e:
            logger.error(f"Error processing operator classes: {e}")

        return op_classes

    def _process_opclass_details(self, op_class: OperatorClassInfo) -> None:
        """Process additional details for an operator class."""
        try:
            with self._get_cursor() as cur:
                # Get operator class properties
                cur.execute(
                    """
                    SELECT
                        opcdefault,
                        opckeytype,
                        array_agg(DISTINCT amproc.amproc::regproc) as support_procs,
                        array_agg(DISTINCT amop.amopopr::regoperator) as operators
                    FROM pg_opclass opc
                    LEFT JOIN pg_amproc amproc ON opc.oid = amproc.amprocfamily
                    LEFT JOIN pg_amop amop ON opc.opcfamily = amop.amopfamily
                    WHERE opc.opcname = %s
                    GROUP BY opcdefault, opckeytype
                """,
                    (op_class.name,),
                )

                row = cur.fetchone()
                if row:
                    # Add support procedures
                    if row["support_procs"]:
                        op_class.functions.extend(
                            proc
                            for proc in row["support_procs"]
                            if proc not in op_class.functions
                        )

                    # Add operators
                    if row["operators"]:
                        new_operators = [
                            self.operators.get(op.split("(")[0])
                            for op in row["operators"]
                            if "(" in op
                        ]
                        op_class.operators.extend(
                            op
                            for op in new_operators
                            if op and op not in op_class.operators
                        )

                # Get operator class options
                cur.execute(
                    """
                    SELECT
                        reloptions
                    FROM pg_class c
                    JOIN pg_opclass opc ON c.relname = opc.opcname
                    WHERE opc.opcname = %s
                """,
                    (op_class.name,),
                )

                row = cur.fetchone()
                if row and row["reloptions"]:
                    # Parse operator class options
                    options = dict(
                        opt.split("=") for opt in row["reloptions"] if "=" in opt
                    )

                    # Update operator class with parsed options
                    if options:
                        op_class.options = options

        except Exception as e:
            logger.error(
                f"Error processing operator class details for {op_class.name}: {e}"
            )

    def analyze_operator_dependencies(self) -> Dict[str, Set[str]]:
        """
        Analyze operator dependencies and relationships.

        Returns:
            Dict[str, Set[str]]: Dictionary mapping operators to their dependencies
        """
        dependencies = defaultdict(set)
        try:
            with self._get_cursor() as cur:
                cur.execute(
                    """
                    WITH RECURSIVE op_deps AS (
                        -- Direct dependencies
                        SELECT
                            o1.oprname as op_name,
                            o2.oprname as dep_name
                        FROM pg_operator o1
                        LEFT JOIN pg_operator o2 ON (
                            o1.oprcom = o2.oid OR
                            o1.oprnegate = o2.oid OR
                            o1.oprrest::regprocedure::text LIKE '%' || o2.oprname || '%' OR
                            o1.oprjoin::regprocedure::text LIKE '%' || o2.oprname || '%'
                        )
                        WHERE o1.oprnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)

                        UNION

                        -- Recursive dependencies
                        SELECT
                            d.op_name,
                            o2.oprname as dep_name
                        FROM op_deps d
                        JOIN pg_operator o1 ON o1.oprname = d.dep_name
                        LEFT JOIN pg_operator o2 ON (
                            o1.oprcom = o2.oid OR
                            o1.oprnegate = o2.oid
                        )
                        WHERE o2.oprname IS NOT NULL
                    )
                    SELECT
                        op_name,
                        array_agg(DISTINCT dep_name) as dependencies
                    FROM op_deps
                    WHERE dep_name IS NOT NULL
                    GROUP BY op_name
                """,
                    (self.config.schema,),
                )

                for row in cur:
                    dependencies[row["op_name"]] = set(row["dependencies"])

        except Exception as e:
            logger.error(f"Error analyzing operator dependencies: {e}")

        return dependencies

    def get_operator_usage(self, operator_name: str) -> Dict[str, Any]:
        """
        Get detailed usage information for an operator.

        Args:
            operator_name: Name of the operator to analyze

        Returns:
            Dict[str, Any]: Dictionary containing operator usage information
        """
        usage = {
            "operator_classes": [],
            "indexes": [],
            "constraints": [],
            "views": [],
            "functions": [],
        }

        try:
            with self._get_cursor() as cur:
                # Find operator classes using this operator
                cur.execute(
                    """
                    SELECT DISTINCT
                        opc.opcname as opclass_name,
                        am.amname as index_method
                    FROM pg_operator o
                    JOIN pg_amop amop ON amop.amopopr = o.oid
                    JOIN pg_opclass opc ON amop.amopfamily = opc.opcfamily
                    JOIN pg_am am ON opc.opcmethod = am.oid
                    WHERE o.oprname = %s
                """,
                    (operator_name,),
                )
                usage["operator_classes"] = [
                    {"name": row["opclass_name"], "method": row["index_method"]}
                    for row in cur
                ]

                # Find indexes using this operator
                cur.execute(
                    """
                    SELECT DISTINCT
                        i.relname as index_name,
                        t.relname as table_name
                    FROM pg_operator o
                    JOIN pg_amop amop ON amop.amopopr = o.oid
                    JOIN pg_index ix ON ix.indclass && ARRAY[amop.amopfamily]
                    JOIN pg_class i ON i.oid = ix.indexrelid
                    JOIN pg_class t ON t.oid = ix.indrelid
                    WHERE o.oprname = %s
                """,
                    (operator_name,),
                )
                usage["indexes"] = [
                    {"index": row["index_name"], "table": row["table_name"]}
                    for row in cur
                ]

                # Find constraints using this operator
                cur.execute(
                    """
                    SELECT DISTINCT
                        con.conname as constraint_name,
                        t.relname as table_name,
                        pg_get_constraintdef(con.oid) as definition
                    FROM pg_operator o
                    JOIN pg_constraint con ON
                        con.conexclop && ARRAY[o.oid] OR
                        con.conpfeqop && ARRAY[o.oid]
                    JOIN pg_class t ON t.oid = con.conrelid
                    WHERE o.oprname = %s
                """,
                    (operator_name,),
                )
                usage["constraints"] = [
                    {
                        "name": row["constraint_name"],
                        "table": row["table_name"],
                        "definition": row["definition"],
                    }
                    for row in cur
                ]

                # Find views using this operator
                cur.execute(
                    """
                    SELECT DISTINCT
                        c.relname as view_name,
                        pg_get_viewdef(c.oid) as definition
                    FROM pg_operator o
                    JOIN pg_depend d ON d.refobjid = o.oid
                    JOIN pg_rewrite r ON r.oid = d.objid
                    JOIN pg_class c ON c.oid = r.ev_class
                    WHERE o.oprname = %s
                    AND c.relkind IN ('v', 'm')
                """,
                    (operator_name,),
                )
                usage["views"] = [
                    {"name": row["view_name"], "definition": row["definition"]}
                    for row in cur
                ]

                # Find functions using this operator
                cur.execute(
                    """
                    SELECT DISTINCT
                        p.proname as function_name,
                        pg_get_functiondef(p.oid) as definition
                    FROM pg_operator o
                    JOIN pg_depend d ON d.refobjid = o.oid
                    JOIN pg_proc p ON p.oid = d.objid
                    WHERE o.oprname = %s
                """,
                    (operator_name,),
                )
                usage["functions"] = [
                    {"name": row["function_name"], "definition": row["definition"]}
                    for row in cur
                ]

        except Exception as e:
            logger.error(f"Error getting operator usage for {operator_name}: {e}")

        return usage

    def _process_foreign_data_wrappers(self) -> Dict[str, FDWInfo]:
        """
        Process foreign data wrappers and their configurations.

        Returns:
            Dict[str, FDWInfo]: Dictionary of foreign data wrapper information
        """
        fdws = {}
        try:
            fdw_data = self._execute_catalog_query("foreign_data_wrappers", tuple())

            for row in fdw_data:
                name = row["name"]
                fdws[name] = FDWInfo(
                    name=name,
                    handler=row["handler_function"],
                    validator=row["validator_function"],
                    options=self._parse_fdw_options(row["options"]),
                    validation=self._get_fdw_validation_level(name),
                )

                # Get servers for this FDW
                servers = self._get_fdw_servers(name)
                fdws[name].servers = servers

        except Exception as e:
            logger.error(f"Error processing foreign data wrappers: {e}")

        return fdws

    def _parse_fdw_options(self, options: List[str]) -> Dict[str, str]:
        """Parse foreign data wrapper options."""
        if not options:
            return {}

        parsed = {}
        try:
            for opt in options:
                if "=" in opt:
                    key, value = opt.split("=", 1)
                    parsed[key.strip()] = value.strip()
        except Exception as e:
            logger.error(f"Error parsing FDW options: {e}")

        return parsed

    def _get_fdw_validation_level(self, fdw_name: str) -> FDWValidation:
        """Determine the validation level for a foreign data wrapper."""
        try:
            with self._get_cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        fdwvalidator IS NOT NULL as has_validator,
                        fdwhandler IS NOT NULL as has_handler
                    FROM pg_foreign_data_wrapper
                    WHERE fdwname = %s
                """,
                    (fdw_name,),
                )
                row = cur.fetchone()

                if row:
                    if row["has_validator"] and row["has_handler"]:
                        return FDWValidation.IMPORT
                    elif row["has_validator"]:
                        return FDWValidation.IMPORT_ONLY

        except Exception as e:
            logger.error(f"Error getting FDW validation level for {fdw_name}: {e}")

        return FDWValidation.NONE

    def _get_fdw_servers(self, fdw_name: str) -> List[ForeignServerInfo]:
        """Get foreign servers associated with a foreign data wrapper."""
        servers = []
        try:
            server_data = self._execute_catalog_query("foreign_servers", tuple())

            for row in server_data:
                if row["wrapper_name"] == fdw_name:
                    server = ForeignServerInfo(
                        name=row["name"],
                        wrapper=fdw_name,
                        type=row["type"],
                        version=row["version"],
                        options=self._parse_fdw_options(row["options"]),
                    )

                    # Get tables using this server
                    tables = self._get_foreign_tables(server.name)
                    server.tables = tables

                    servers.append(server)

        except Exception as e:
            logger.error(f"Error getting FDW servers for {fdw_name}: {e}")

        return servers

    def _get_foreign_tables(self, server_name: str) -> List[ForeignTableInfo]:
        """Get foreign tables associated with a foreign server."""
        tables = []
        try:
            table_data = self._execute_catalog_query(
                "foreign_tables", (self.config.schema,)
            )

            for row in table_data:
                if row["server_name"] == server_name:
                    table = ForeignTableInfo(
                        name=row["name"],
                        server=server_name,
                        columns=row["columns"],
                        options=self._parse_fdw_options(row["options"]),
                    )

                    # Get additional table information
                    self._enhance_foreign_table_info(table)
                    tables.append(table)

        except Exception as e:
            logger.error(f"Error getting foreign tables for server {server_name}: {e}")

        return tables

    def _enhance_foreign_table_info(self, table: ForeignTableInfo) -> None:
        """Enhance foreign table information with constraints and triggers."""
        try:
            with self._get_cursor() as cur:
                # Get constraints
                cur.execute(
                    """
                    SELECT
                        c.conname as name,
                        pg_get_constraintdef(c.oid) as definition
                    FROM pg_constraint c
                    JOIN pg_class t ON c.conrelid = t.oid
                    WHERE t.relname = %s
                      AND t.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
                """,
                    (table.name, self.config.schema),
                )

                table.constraints = [row["definition"] for row in cur.fetchall()]

                # Get triggers
                cur.execute(
                    """
                    SELECT
                        t.tgname as name
                    FROM pg_trigger t
                    JOIN pg_class c ON t.tgrelid = c.oid
                    WHERE c.relname = %s
                      AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
                      AND NOT t.tgisinternal
                """,
                    (table.name, self.config.schema),
                )

                table.triggers = [row["name"] for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error enhancing foreign table info for {table.name}: {e}")

    def get_user_mappings(self, server_name: str) -> Dict[str, Dict[str, str]]:
        """
        Get user mappings for a foreign server.

        Args:
            server_name: Name of the foreign server

        Returns:
            Dict[str, Dict[str, str]]: Dictionary mapping usernames to their options
        """
        mappings = {}
        try:
            with self._get_cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        r.rolname as username,
                        um.umoptions as options
                    FROM pg_user_mapping um
                    JOIN pg_foreign_server s ON um.umserver = s.oid
                    JOIN pg_roles r ON um.umuser = r.oid
                    WHERE s.srvname = %s
                """,
                    (server_name,),
                )

                for row in cur:
                    mappings[row["username"]] = self._parse_fdw_options(row["options"])

        except Exception as e:
            logger.error(f"Error getting user mappings for server {server_name}: {e}")

        return mappings

    def analyze_foreign_table_usage(self, table_name: str) -> Dict[str, Any]:
        """
        Analyze usage of a foreign table (continued from previous part).

        Args:
            table_name: Name of the foreign table

        Returns:
            Dict[str, Any]: Dictionary containing usage information
        """
        usage = {
            "dependencies": [],
            "referencing_views": [],
            "permissions": [],
            "statistics": {},
            "performance_metrics": {},
            "sync_status": {},
        }

        try:
            with self._get_cursor() as cur:
                # Get permissions
                cur.execute(
                    """
                    SELECT
                        r.rolname as grantee,
                        array_agg(privilege_type) as privileges
                    FROM information_schema.role_table_grants g
                    JOIN pg_roles r ON r.rolname = g.grantee
                    WHERE table_schema = %s
                      AND table_name = %s
                    GROUP BY r.rolname
                """,
                    (self.config.schema, table_name),
                )

                usage["permissions"] = [
                    {"role": row["grantee"], "privileges": row["privileges"]}
                    for row in cur
                ]

                # Get table statistics
                cur.execute(
                    """
                    SELECT
                        s.n_live_tup as row_count,
                        s.n_dead_tup as dead_rows,
                        s.last_analyze as last_analyzed,
                        s.last_autoanalyze as last_autoanalyzed,
                        pg_size_pretty(pg_total_relation_size(%s)) as total_size
                    FROM pg_stat_all_tables s
                    WHERE s.relname = %s
                      AND s.schemaname = %s
                """,
                    (table_name, table_name, self.config.schema),
                )

                row = cur.fetchone()
                if row:
                    usage["statistics"] = {
                        "row_count": row["row_count"],
                        "dead_rows": row["dead_rows"],
                        "last_analyzed": row["last_analyzed"],
                        "last_autoanalyzed": row["last_autoanalyzed"],
                        "total_size": row["total_size"],
                    }

                # Get performance metrics
                usage["performance_metrics"] = self._get_foreign_table_metrics(
                    table_name
                )

                # Get synchronization status
                usage["sync_status"] = self._get_foreign_table_sync_status(table_name)

        except Exception as e:
            logger.error(f"Error analyzing foreign table usage for {table_name}: {e}")

        return usage


    def _get_foreign_table_metrics(self, table_name: str) -> Dict[str, Any]:
        """Get performance metrics for a foreign table."""
        metrics = {}
        try:
            with self._get_cursor() as cur:
                # Get scan statistics
                cur.execute("""
                    SELECT
                        seq_scan,
                        seq_tup_read,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_live_tup,
                        n_dead_tup,
                        last_vacuum,
                        last_autovacuum,
                        vacuum_count,
                        autovacuum_count
                    FROM pg_stat_all_tables
                    WHERE relname = %s
                      AND schemaname = %s
                """, (table_name, self.config.schema))

                row = cur.fetchone()
                if row:
                    metrics['scan_stats'] = {
                        'sequential_scans': row['seq_scan'],
                        'tuples_read': row['seq_tup_read'],
                        'inserts': row['n_tup_ins'],
                        'updates': row['n_tup_upd'],
                        'deletes': row['n_tup_del'],
                        'live_tuples': row['n_live_tup'],
                        'dead_tuples': row['n_dead_tup'],
                        'last_vacuum': row['last_vacuum'],
                        'last_autovacuum': row['last_autovacuum'],
                        'vacuum_count': row['vacuum_count'],
                        'autovacuum_count': row['autovacuum_count']
                    }

                # Get I/O statistics
                cur.execute("""
                    SELECT
                        heap_blks_read,
                        heap_blks_hit,
                        idx_blks_read,
                        idx_blks_hit,
                        toast_blks_read,
                        toast_blks_hit
                    FROM pg_statio_all_tables
                    WHERE relname = %s
                      AND schemaname = %s
                """, (table_name, self.config.schema))

                row = cur.fetchone()
                if row:
                    metrics['io_stats'] = {
                        'heap_blocks_read': row['heap_blks_read'],
                        'heap_blocks_hit': row['heap_blks_hit'],
                        'index_blocks_read': row['idx_blks_read'],
                        'index_blocks_hit': row['idx_blks_hit'],
                        'toast_blocks_read': row['toast_blks_read'],
                        'toast_blocks_hit': row['toast_blks_hit']
                    }

                # Calculate cache hit ratios
                if metrics.get('io_stats'):
                    io = metrics['io_stats']
                    total_reads = (io['heap_blocks_read'] + io['index_blocks_read'] +
                                 io['toast_blocks_read'])
                    total_hits = (io['heap_blocks_hit'] + io['index_blocks_hit'] +
                                io['toast_blocks_hit'])
                    total_accesses = total_reads + total_hits

                    if total_accesses > 0:
                        metrics['cache_hit_ratio'] = total_hits / total_accesses

        except Exception as e:
            logger.error(f"Error getting foreign table metrics for {table_name}: {e}")

        return metrics

    def _get_foreign_table_sync_status(self, table_name: str) -> Dict[str, Any]:
        """Get synchronization status for a foreign table."""
        status = {}
        try:
            with self._get_cursor() as cur:
                # Get foreign table options
                cur.execute("""
                    SELECT ftoptions
                    FROM pg_foreign_table ft
                    JOIN pg_class c ON ft.ftrelid = c.oid
                    WHERE c.relname = %s
                      AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
                """, (table_name, self.config.schema))

                row = cur.fetchone()
                if row:
                    options = self._parse_fdw_options(row['ftoptions'])

                    # Check for various sync-related options
                    status['updatable'] = (
                        options.get('updatable', 'false').lower() == 'true'
                    )
                    status['insert_only'] = (
                        options.get('insert_only', 'false').lower() == 'true'
                    )

                    # Get modification timestamp if available
                    if 'modified' in options:
                        status['last_modified'] = options['modified']

                # Get foreign server status
                cur.execute("""
                    SELECT
                        fs.srvname,
                        fs.srvoptions,
                        fdw.fdwname,
                        fdw.fdwoptions
                    FROM pg_foreign_table ft
                    JOIN pg_class c ON ft.ftrelid = c.oid
                    JOIN pg_foreign_server fs ON ft.ftserver = fs.oid
                    JOIN pg_foreign_data_wrapper fdw ON fs.srvfdw = fdw.oid
                    WHERE c.relname = %s
                      AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
                """, (table_name, self.config.schema))

                row = cur.fetchone()
                if row:
                    status['server'] = {
                        'name': row['srvname'],
                        'options': self._parse_fdw_options(row['srvoptions']),
                        'wrapper': {
                            'name': row['fdwname'],
                            'options': self._parse_fdw_options(row['fdwoptions'])
                        }
                    }

                    # Check server connectivity
                    status['connection_status'] = self._check_server_connection(
                        row['srvname']
                    )

        except Exception as e:
            logger.error(f"Error getting foreign table sync status for {table_name}: {e}")

        return status

    def _check_server_connection(self, server_name: str) -> Dict[str, Any]:
        """Check connection status to a foreign server."""
        status = {
            'connected': False,
            'latency': None,
            'errors': None
        }

        try:
            with self._get_cursor() as cur:
                # Try to validate the connection
                start_time = datetime.now()

                cur.execute("""
                    SELECT 1
                    FROM pg_foreign_server fs
                    WHERE fs.srvname = %s
                      AND EXISTS (
                        SELECT 1
                        FROM pg_foreign_server_test(%s)
                      )
                """, (server_name, server_name))

                end_time = datetime.now()
                status['connected'] = bool(cur.fetchone())
                status['latency'] = (end_time - start_time).total_seconds()

        except Exception as e:
            status['errors'] = str(e)
            logger.error(f"Error checking server connection for {server_name}: {e}")

        return status

    # ---------- Advanced Security Features ----------
    def _get_column_privileges(self, table_name: str) -> Dict[str, ColumnPrivilegeInfo]:
        """Get column-level privileges for a table."""
        privileges = {}
        try:
            priv_data = self._execute_catalog_query("column_privileges", (table_name,))
            for row in priv_data:
                privileges[row["column_name"]] = ColumnPrivilegeInfo(
                    column=row["column_name"],
                    privilege_type=row["privilege_type"],
                    grantee=row["grantee"],
                )
        except Exception as e:
            logger.error(f"Error retrieving column privileges for {table_name}: {e}")
        return privileges

    def _get_security_labels(self, table_name: str) -> List[SecurityLabelInfo]:
        """Get security labels associated with the table."""
        labels = []
        try:
            label_data = self._execute_catalog_query("security_labels", (table_name,))
            for row in label_data:
                labels.append(
                    SecurityLabelInfo(label=row["label"], provider=row["provider"])
                )
        except Exception as e:
            logger.error(f"Error retrieving security labels for {table_name}: {e}")
        return labels

    # ---------- Performance and Monitoring ----------
    def _estimate_table_bloat(self, table_name: str) -> Optional[float]:
        """Estimate table bloat using pgstattuple extension."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute(f"SELECT pgstattuple('{table_name}') AS bloat_estimate")
                result = cursor.fetchone()
                return result["bloat_estimate"] if result else None
        except Exception as e:
            logger.error(f"Error estimating table bloat for {table_name}: {e}")
            return None

    def _get_autovacuum_settings(self, table_name: str) -> Dict[str, Any]:
        """Get autovacuum settings for the table if configured."""
        autovacuum_settings = {}
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT reloptions
                    FROM pg_class
                    WHERE relname = %s
                """,
                    (table_name,),
                )
                row = cursor.fetchone()
                if row and row["reloptions"]:
                    autovacuum_settings = dict(
                        opt.split("=") for opt in row["reloptions"] if "=" in opt
                    )
        except Exception as e:
            logger.error(f"Error retrieving autovacuum settings for {table_name}: {e}")
        return autovacuum_settings

    def _get_table_lock_info(self, table_name: str) -> List[TableLockInfo]:
        """Get lock information for a table."""
        locks = []
        try:
            lock_data = self._execute_catalog_query("table_locks", (table_name,))
            for row in lock_data:
                locks.append(
                    TableLockInfo(
                        lock_type=row["lock_type"],
                        granted=row["granted"],
                        pid=row["pid"],
                        transactionid=row["transactionid"],
                    )
                )
        except Exception as e:
            logger.error(f"Error retrieving locks for {table_name}: {e}")
        return locks

    # ---------- Extended Features ----------
    def _get_toast_config(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve TOAST configuration details for a table."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT reloptions
                    FROM pg_class
                    WHERE relname = pg_table_toastrelid(%s)
                """,
                    (table_name,),
                )
                row = cursor.fetchone()
                if row and row["reloptions"]:
                    return dict(
                        opt.split("=") for opt in row["reloptions"] if "=" in opt
                    )
        except Exception as e:
            logger.error(f"Error retrieving TOAST configuration for {table_name}: {e}")
        return None

    def _get_collations(self) -> Dict[str, CollationInfo]:
        """Get all available collations in the schema."""
        collations = {}
        try:
            collation_data = self._execute_catalog_query(
                "collations", (self.config.schema,)
            )
            for row in collation_data:
                collations[row["name"]] = CollationInfo(
                    name=row["name"], locale=row["locale"], provider=row["provider"]
                )
        except Exception as e:
            logger.error(f"Error retrieving collations: {e}")
        return collations

    def _get_access_methods(self) -> Dict[str, AccessMethodInfo]:
        """Get access methods available in the schema."""
        methods = {}
        try:
            access_method_data = self._execute_catalog_query(
                "access_methods", (self.config.schema,)
            )
            for row in access_method_data:
                methods[row["name"]] = AccessMethodInfo(
                    name=row["name"], type=row["type"]
                )
        except Exception as e:
            logger.error(f"Error retrieving access methods: {e}")
        return methods

    def _get_advanced_constraints(
        self, table_name: str
    ) -> List[AdvancedConstraintInfo]:
        """Retrieve advanced constraints, including exclusion and check constraints."""
        constraints = []
        try:
            constraint_data = self._execute_catalog_query(
                "advanced_constraints", (table_name,)
            )
            for row in constraint_data:
                constraints.append(
                    AdvancedConstraintInfo(
                        name=row["name"],
                        constraint_type=row["type"],
                        definition=row["definition"],
                    )
                )
        except Exception as e:
            logger.error(f"Error retrieving advanced constraints for {table_name}: {e}")
        return constraints

    def cleanup(self) -> None:
        """Clean up database resources."""
        try:
            if self.connection:
                self.connection.close()
            if self.engine:
                self.engine.dispose()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")











    def __enter__(self) -> "PostgreSQLIntrospector":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.cleanup()
