"""
pg_queries.py: PostgreSQL query management and introspection.

This module provides functionality for managing PostgreSQL queries, including:
- Database schema introspection
- Query building and optimization
- Common query templates
- Query analysis and validation
- Performance monitoring
- Query plan inspection

Key Features:
    - Schema introspection queries
    - Query building helpers
    - Query plan analysis
    - Query optimization hints
    - Security validation
    - Performance monitoring

Author: Nyimbi Odero
Copyright: 2024
License: MIT

pg_queries.py: PostgreSQL query management and introspection.

This module provides functionality for managing PostgreSQL queries, including:
- Database schema introspection
- Query building and optimization
- Common query templates
- Query analysis and validation
- Performance monitoring
- Query plan inspection

Key Features:
    - Schema introspection queries
    - Query building helpers
    - Query plan analysis
    - Query optimization hints
    - Security validation
    - Performance monitoring

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
import re

from model_generator.postgresql.pg_exceptions import PostgreSQLQueryError


@dataclass
class QueryMetrics:
    """Holds query execution metrics."""

    execution_time: float
    rows_affected: int
    plan_time: Optional[float] = None
    actual_time: Optional[float] = None
    planning_time: Optional[float] = None
    execution_time_ms: Optional[float] = None
    total_cost: Optional[float] = None

    def __str__(self) -> str:
        return (
            f"Execution: {self.execution_time:.2f}s, "
            f"Rows: {self.rows_affected}, "
            f"Total Cost: {self.total_cost or 'N/A'}"
        )


class QueryBuilder:
    """Builds PostgreSQL queries with proper escaping and validation."""

    def __init__(self):
        self.params: List[Any] = []
        self.query_parts: List[str] = []

    def add(self, sql: str, *params: Any) -> 'QueryBuilder':
        """Add SQL fragment with parameters."""
        self.query_parts.append(sql)
        self.params.extend(params)
        return self

    def where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """Add WHERE clause."""
        if self.query_parts:
            self.query_parts.append("WHERE")
        self.query_parts.append(condition)
        self.params.extend(params)
        return self

    def and_where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """Add AND condition to WHERE clause."""
        self.query_parts.append("AND")
        self.query_parts.append(condition)
        self.params.extend(params)
        return self

    def or_where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """Add OR condition to WHERE clause."""
        self.query_parts.append("OR")
        self.query_parts.append(condition)
        self.params.extend(params)
        return self

    def order_by(self, *columns: str) -> 'QueryBuilder':
        """Add ORDER BY clause."""
        self.query_parts.append("ORDER BY")
        self.query_parts.append(", ".join(columns))
        return self

    def limit(self, limit: int) -> 'QueryBuilder':
        """Add LIMIT clause."""
        self.query_parts.append("LIMIT %s")
        self.params.append(limit)
        return self

    def offset(self, offset: int) -> 'QueryBuilder':
        """Add OFFSET clause."""
        self.query_parts.append("OFFSET %s")
        self.params.append(offset)
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """Build final query and parameters."""
        return " ".join(self.query_parts), self.params


class SchemaQueries:
    """PostgreSQL schema introspection queries."""

    @staticmethod
    def get_schemas() -> str:
        """Get all schemas."""
        return """
            SELECT
                nspname AS schema_name,
                pg_get_userbyid(nspowner) AS owner,
                obj_description(oid, 'pg_namespace') AS description
            FROM pg_namespace
            WHERE nspname NOT LIKE 'pg_%'
                AND nspname != 'information_schema'
            ORDER BY nspname;
        """

    @staticmethod
    def get_tables(schema: str = 'public') -> str:
        """Get tables in schema."""
        return """
            SELECT
                schemaname AS schema_name,
                tablename AS table_name,
                tableowner AS owner,
                obj_description(
                    (quote_ident(schemaname) || '.' ||
                     quote_ident(tablename))::regclass,
                    'pg_class'
                ) AS description
            FROM pg_tables
            WHERE schemaname = %s
            ORDER BY tablename;
        """

    @staticmethod
    def get_columns(table_name: str, schema: str = 'public') -> str:
        """Get column information for table."""
        return """
            SELECT
                a.attname AS column_name,
                pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
                (SELECT col_description(a.attrelid, a.attnum)) AS description,
                a.attnotnull AS not_null,
                pg_get_expr(d.adbin, d.adrelid) AS default_value,
                CASE
                    WHEN pk.contype = 'p' THEN true
                    ELSE false
                END AS is_primary_key,
                CASE
                    WHEN fk.contype = 'f' THEN true
                    ELSE false
                END AS is_foreign_key
            FROM pg_attribute a
            LEFT JOIN pg_attrdef d ON a.attrelid = d.adrelid AND a.attnum = d.adnum
            LEFT JOIN pg_constraint pk
                ON pk.conrelid = a.attrelid
                AND pk.contype = 'p'
                AND a.attnum = ANY(pk.conkey)
            LEFT JOIN pg_constraint fk
                ON fk.conrelid = a.attrelid
                AND fk.contype = 'f'
                AND a.attnum = ANY(fk.conkey)
            WHERE a.attrelid = %s::regclass
                AND a.attnum > 0
                AND NOT a.attisdropped
            ORDER BY a.attnum;
        """

    @staticmethod
    def get_constraints(table_name: str, schema: str = 'public') -> str:
        """Get table constraints."""
        return """
            SELECT
                con.conname AS constraint_name,
                con.contype AS constraint_type,
                pg_get_constraintdef(con.oid) AS definition,
                obj_description(con.oid, 'pg_constraint') AS description
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE nsp.nspname = %s
                AND rel.relname = %s
            ORDER BY con.contype, con.conname;
        """

    @staticmethod
    def get_indexes(table_name: str, schema: str = 'public') -> str:
        """Get table indexes."""
        return """
            SELECT
                i.relname AS index_name,
                am.amname AS index_type,
                pg_get_indexdef(i.oid) AS definition,
                idx_scan AS usage_count,
                obj_description(i.oid, 'pg_class') AS description
            FROM pg_index x
            JOIN pg_class i ON i.oid = x.indexrelid
            JOIN pg_class t ON t.oid = x.indrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_am am ON i.relam = am.oid
            LEFT JOIN pg_stat_user_indexes sui
                ON sui.indexrelid = i.oid
            WHERE n.nspname = %s
                AND t.relname = %s
            ORDER BY i.relname;
        """

    @staticmethod
    def get_foreign_keys(table_name: str, schema: str = 'public') -> str:
        """Get foreign key relationships."""
        return """
            SELECT
                con.conname AS constraint_name,
                pg_get_constraintdef(con.oid) AS definition,
                ns2.nspname AS referenced_schema,
                cl2.relname AS referenced_table,
                arr.attname AS referenced_column,
                del.deltype AS delete_rule,
                upd.updtype AS update_rule
            FROM pg_constraint con
            JOIN pg_namespace ns1 ON ns1.oid = con.connamespace
            JOIN pg_class cl1 ON cl1.oid = con.conrelid
            JOIN pg_namespace ns2 ON ns2.oid = cl1.relnamespace
            JOIN pg_class cl2 ON cl2.oid = con.confrelid
            JOIN pg_attribute arr ON arr.attrelid = cl2.oid
                AND arr.attnum = ANY(con.confkey)
            LEFT JOIN pg_constraint del ON del.oid = con.oid
                AND del.confdeltype != 'a'
            LEFT JOIN pg_constraint upd ON upd.oid = con.oid
                AND upd.confupdtype != 'a'
            WHERE ns1.nspname = %s
                AND cl1.relname = %s
                AND con.contype = 'f'
            ORDER BY con.conname;
        """


class QueryAnalyzer:
    """Analyzes and optimizes PostgreSQL queries."""

    def __init__(self, connection):
        self.connection = connection

    def explain(self, query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Get query execution plan."""
        explain_query = f"EXPLAIN (ANALYZE, VERBOSE, FORMAT JSON) {query}"

        with self.connection.cursor() as cursor:
            cursor.execute(explain_query, params or [])
            return cursor.fetchone()[0]

    def analyze_performance(self, query: str,
                          params: Optional[List[Any]] = None) -> QueryMetrics:
        """Analyze query performance."""
        plan = self.explain(query, params)

        # Extract metrics from plan
        metrics = QueryMetrics(
            execution_time=plan[0]['Execution Time'] / 1000,  # Convert to seconds
            rows_affected=plan[0]['Plan']['Actual Rows'],
            plan_time=plan[0]['Planning Time'],
            actual_time=plan[0]['Execution Time'],
            total_cost=plan[0]['Plan']['Total Cost']
        )

        return metrics

    def suggest_improvements(self, query: str,
                           params: Optional[List[Any]] = None) -> List[str]:
        """Suggest query improvements."""
        plan = self.explain(query, params)
        suggestions = []

        # Analyze plan nodes
        self._analyze_plan_node(plan[0]['Plan'], suggestions)

        return suggestions

    def _analyze_plan_node(self, node: Dict[str, Any],
                          suggestions: List[str], depth: int = 0) -> None:
        """Recursively analyze plan node for potential improvements."""

        # Check for sequential scans on large tables
        if node['Node Type'] == 'Seq Scan' and node['Actual Rows'] > 1000:
            suggestions.append(
                f"Consider adding an index for table '{node['Relation Name']}' "
                f"to avoid sequential scan"
            )

        # Check for high-cost sorts
        if node['Node Type'] == 'Sort' and node['Actual Total Time'] > 1000:
            suggestions.append(
                "High-cost sort operation detected. Consider adding an index "
                "to avoid sorting"
            )

        # Check for nested loops with many rows
        if node['Node Type'] == 'Nested Loop' and node['Actual Rows'] > 1000:
            suggestions.append(
                "Expensive nested loop detected. Consider using JOIN HINTS "
                "or restructuring the query"
            )

        # Recurse into child nodes
        for child in node.get('Plans', []):
            self._analyze_plan_node(child, suggestions, depth + 1)


class QueryValidator:
    """Validates PostgreSQL queries for security and correctness."""

    def __init__(self):
        self.dangerous_patterns = [
            r';\s*DROP\s+',
            r';\s*DELETE\s+',
            r';\s*TRUNCATE\s+',
            r';\s*ALTER\s+',
            r'--',
            r'/\*.*?\*/',
        ]

    def validate(self, query: str) -> List[str]:
        """Validate query for potential issues."""
        issues = []

        # Check for SQL injection vulnerabilities
        for pattern in self.dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                issues.append(
                    f"Potential SQL injection vulnerability: "
                    f"matched pattern '{pattern}'"
                )

        # Check for proper quoting
        if query.count("'") % 2 != 0:
            issues.append("Unmatched single quotes")

        # Check for common mistakes
        if 'SELECT *' in query.upper():
            issues.append(
                "Using SELECT * is discouraged. "
                "Specify needed columns explicitly"
            )

        if 'WHERE' not in query.upper() and any(
            word in query.upper() for word in ['UPDATE', 'DELETE']
        ):
            issues.append("Missing WHERE clause in UPDATE/DELETE")

        return issues


class QueryMonitor:
    """Monitors query execution and performance."""

    def __init__(self, connection):
        self.connection = connection
        self.slow_query_threshold = 1.0  # seconds

    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow query information."""
        return self.connection.execute("""
            SELECT
                query,
                calls,
                total_time / 1000 AS total_seconds,
                mean_time / 1000 AS mean_seconds,
                rows
            FROM pg_stat_statements
            WHERE mean_time > %s
            ORDER BY mean_time DESC
            LIMIT 10;
        """, [self.slow_query_threshold * 1000])

    def get_query_stats(self) -> Dict[str, Any]:
        """Get overall query statistics."""
        return self.connection.execute("""
            SELECT
                sum(calls) AS total_queries,
                sum(total_time) / 1000 AS total_seconds,
                sum(rows) AS total_rows,
                avg(mean_time) / 1000 AS avg_query_time
            FROM pg_stat_statements;
        """)


def build_query(table: str,
                columns: Optional[List[str]] = None,
                conditions: Optional[Dict[str, Any]] = None,
                order_by: Optional[List[str]] = None,
                limit: Optional[int] = None,
                offset: Optional[int] = None) -> Tuple[str, List[Any]]:
    """
    Build a SELECT query with parameters.

    Args:
        table: Table name
        columns: List of columns to select
        conditions: WHERE conditions as dict
        order_by: ORDER BY columns
        limit: LIMIT value
        offset: OFFSET value

    Returns:
        Tuple of query string and parameters
    """
    builder = QueryBuilder()

    # Build SELECT clause
    select_cols = '*' if not columns else ', '.join(columns)
    builder.add(f"SELECT {select_cols} FROM {table}")

    # Add WHERE conditions
    if conditions:
        where_parts = []
        for key, value in conditions.items():
            where_parts.append(f"{key} = %s")
            builder.params.append(value)
        if where_parts:
            builder.where(' AND '.join(where_parts))

    # Add ORDER BY
    if order_by:
        builder.order_by(*order_by)

    # Add LIMIT/OFFSET
    if limit is not None:
        builder.limit(limit)
    if offset is not None:
        builder.offset(offset)

    return builder.build()


class QueryTemplates:
    """Common PostgreSQL query templates."""

    @staticmethod
    def insert(table: str,
              data: Dict[str, Any],
              returning: Optional[List[str]] = None) -> Tuple[str, List[Any]]:
        """Build INSERT query."""
        columns = list(data.keys())
        values = list(data.values())
        placeholders = [f"%s" for _ in values]

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        if returning:
            query += f" RETURNING {', '.join(returning)}"

        return query, values

    @staticmethod
    def update(table: str,
              data: Dict[str, Any],
              conditions: Dict[str, Any],
              returning: Optional[List[str]] = None) -> Tuple[str, List[Any]]:
        """Build UPDATE query."""
        set_parts = [f"{k} = %s" for k in data.keys()]
        where_parts = [f"{k} = %s" for k in conditions.keys()]

        query = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"

        if returning:
            query += f" RETURNING {', '.join(returning)}"

        values = list(data.values()) + list(conditions.values())
        return query, values

    @staticmethod
    def delete(table: str,
              conditions: Dict[str, Any],
              returning: Optional[List[str]] = None) -> Tuple[str, List[Any]]:
        """Build DELETE query."""
        where_parts = [f"{k} = %s" for k in conditions.keys()]

        query = f"DELETE FROM {table} WHERE {' AND '.join(where_parts)}"

        if returning:
            query += f" RETURNING {', '.join(returning)}"

        return query, list(conditions.values())



from typing import Dict, List, Optional, Set, Tuple, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum
import re

from model_generator.postgresql.pg_types import PostgreSQLTypeMap, PostgreSQLBaseType
from model_generator.postgresql.pg_exceptions import PostgreSQLQueryError


class ObjectType(Enum):
    """PostgreSQL object types for introspection."""
    SCHEMA = 'SCHEMA'
    TABLE = 'TABLE'
    VIEW = 'VIEW'
    MATERIALIZED_VIEW = 'MATERIALIZED VIEW'
    FOREIGN_TABLE = 'FOREIGN TABLE'
    SEQUENCE = 'SEQUENCE'
    FUNCTION = 'FUNCTION'
    PROCEDURE = 'PROCEDURE'
    TYPE = 'TYPE'
    DOMAIN = 'DOMAIN'
    CONSTRAINT = 'CONSTRAINT'
    TRIGGER = 'TRIGGER'
    RULE = 'RULE'
    POLICY = 'POLICY'
    EXTENSION = 'EXTENSION'


@dataclass
class CatalogQuery:
    """Represents a PostgreSQL catalog query."""

    query: str
    params: Optional[List[Any]] = None
    description: Optional[str] = None
    result_processor: Optional[callable] = None


class CatalogQueries:
    """PostgreSQL system catalog queries."""

    # Schema Queries
    SCHEMAS = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            r.rolname AS owner,
            obj_description(n.oid, 'pg_namespace') AS description,
            n.nspacl AS privileges
        FROM pg_namespace n
        JOIN pg_roles r ON r.oid = n.nspowner
        WHERE n.nspname NOT LIKE 'pg_%'
            AND n.nspname != 'information_schema'
        ORDER BY n.nspname;
    """)

    # Table Queries
    TABLES = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            c.relname AS table_name,
            r.rolname AS owner,
            obj_description(c.oid, 'pg_class') AS description,
            c.relacl AS privileges,
            c.relkind AS table_type,
            c.relpersistence AS persistence,
            c.relispartition AS is_partition,
            c.relhassubclass AS has_inheritance,
            c.reltuples::bigint AS estimated_rows,
            pg_total_relation_size(c.oid) AS total_size,
            pg_table_size(c.oid) AS table_size,
            age(c.relfrozenxid) AS xid_age
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_roles r ON r.oid = c.relowner
        WHERE c.relkind IN ('r', 'p')
            AND n.nspname = ANY(%s)
        ORDER BY n.nspname, c.relname;
    """)

    # Column Queries
    COLUMNS = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            c.relname AS table_name,
            a.attname AS column_name,
            t.typname AS data_type,
            t.typtype AS type_type,
            t.typnamespace::regnamespace AS type_schema,
            a.attnum AS ordinal_position,
            a.attnotnull AS not_null,
            pg_get_expr(d.adbin, d.adrelid) AS default_value,
            col_description(a.attrelid, a.attnum) AS description,
            a.attinhcount AS inheritance_count,
            a.attidentity AS identity_type,
            a.attgenerated AS generated_type,
            CASE
                WHEN t.typtype = 'd' THEN
                    (SELECT dt.typname
                     FROM pg_type dt
                     WHERE dt.oid = t.typbasetype)
                ELSE NULL
            END AS domain_base_type,
            format_type(a.atttypid, a.atttypmod) AS full_data_type
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_type t ON t.oid = a.atttypid
        LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
        WHERE a.attnum > 0
            AND NOT a.attisdropped
            AND n.nspname = ANY(%s)
            AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
        ORDER BY n.nspname, c.relname, a.attnum;
    """)

    # Constraint Queries
    CONSTRAINTS = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            c.relname AS table_name,
            con.conname AS constraint_name,
            con.contype AS constraint_type,
            pg_get_constraintdef(con.oid) AS definition,
            obj_description(con.oid, 'pg_constraint') AS description,
            con.convalidated AS is_validated,
            con.condeferrable AS is_deferrable,
            con.condeferred AS is_deferred,
            array_agg(a.attname ORDER BY array_position(con.conkey, a.attnum))
                FILTER (WHERE a.attnum IS NOT NULL) AS constrained_columns,
            array_agg(DISTINCT format_type(t.oid, NULL))
                FILTER (WHERE t.oid IS NOT NULL) AS involved_types
        FROM pg_constraint con
        JOIN pg_class c ON c.oid = con.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_attribute a ON a.attrelid = c.oid
            AND a.attnum = ANY(con.conkey)
        LEFT JOIN pg_type t ON t.oid = a.atttypid
        WHERE n.nspname = ANY(%s)
        GROUP BY n.nspname, c.relname, con.conname, con.contype, con.oid,
                 con.convalidated, con.condeferrable, con.condeferred
        ORDER BY n.nspname, c.relname, con.conname;
    """)

    # Index Queries
    INDEXES = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            c.relname AS table_name,
            i.relname AS index_name,
            am.amname AS index_method,
            pg_get_indexdef(i.oid) AS definition,
            obj_description(i.oid, 'pg_class') AS description,
            i.relpages AS page_count,
            i.reltuples::bigint AS row_estimate,
            s.idx_scan AS scan_count,
            s.idx_tup_read AS tuples_read,
            s.idx_tup_fetch AS tuples_fetched,
            pg_relation_size(i.oid) AS index_size,
            x.indisunique AS is_unique,
            x.indisprimary AS is_primary,
            x.indisexclusion AS is_exclusion,
            x.indimmediate AS is_immediate,
            x.indisclustered AS is_clustered,
            array_agg(a.attname ORDER BY array_position(x.indkey, a.attnum))
                AS indexed_columns,
            pg_get_expr(x.indexprs, x.indrelid) AS expression,
            pg_get_expr(x.indpred, x.indrelid) AS predicate
        FROM pg_index x
        JOIN pg_class i ON i.oid = x.indexrelid
        JOIN pg_class c ON c.oid = x.indrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_am am ON am.oid = i.relam
        LEFT JOIN pg_stat_user_indexes s ON s.indexrelid = i.oid
        LEFT JOIN pg_attribute a ON a.attrelid = c.oid
            AND a.attnum = ANY(x.indkey)
        WHERE n.nspname = ANY(%s)
        GROUP BY n.nspname, c.relname, i.relname, am.amname, i.oid, x.indexrelid,
                 x.indrelid, x.indisunique, x.indisprimary, x.indisexclusion,
                 x.indimmediate, x.indisclustered, s.idx_scan, s.idx_tup_read,
                 s.idx_tup_fetch, x.indexprs, x.indpred
        ORDER BY n.nspname, c.relname, i.relname;
    """)

    # Foreign Key Queries
    FOREIGN_KEYS = CatalogQuery("""
        SELECT
            n1.nspname AS schema_name,
            c1.relname AS table_name,
            con.conname AS constraint_name,
            n2.nspname AS referenced_schema,
            c2.relname AS referenced_table,
            pg_get_constraintdef(con.oid) AS definition,
            obj_description(con.oid, 'pg_constraint') AS description,
            array_agg(a1.attname ORDER BY array_position(con.conkey, a1.attnum))
                AS constraint_columns,
            array_agg(a2.attname ORDER BY array_position(con.confkey, a2.attnum))
                AS referenced_columns,
            con.confupdtype AS update_action,
            con.confdeltype AS delete_action,
            con.confmatchtype AS match_type
        FROM pg_constraint con
        JOIN pg_class c1 ON c1.oid = con.conrelid
        JOIN pg_namespace n1 ON n1.oid = c1.relnamespace
        JOIN pg_class c2 ON c2.oid = con.confrelid
        JOIN pg_namespace n2 ON n2.oid = c2.relnamespace
        JOIN pg_attribute a1 ON a1.attrelid = c1.oid
            AND a1.attnum = ANY(con.conkey)
        JOIN pg_attribute a2 ON a2.attrelid = c2.oid
            AND a2.attnum = ANY(con.confkey)
        WHERE con.contype = 'f'
            AND n1.nspname = ANY(%s)
        GROUP BY n1.nspname, c1.relname, con.conname, n2.nspname, c2.relname,
                 con.oid, con.confupdtype, con.confdeltype, con.confmatchtype
        ORDER BY n1.nspname, c1.relname, con.conname;
    """)

    # Trigger Queries
    TRIGGERS = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            c.relname AS table_name,
            t.tgname AS trigger_name,
            p.proname AS function_name,
            pn.nspname AS function_schema,
            obj_description(t.oid, 'pg_trigger') AS description,
            pg_get_triggerdef(t.oid) AS definition,
            t.tgenabled AS enabled,
            t.tgtype AS type,
            t.tgconstraint AS constraint_trigger,
            array_to_string(t.tgattr, ',') AS column_numbers,
            t.tgqual AS condition,
            t.tginitdeferred AS initially_deferred,
            t.tgnargs AS num_args,
            t.tgoldtable AS old_table,
            t.tgnewtable AS new_table
        FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_proc p ON p.oid = t.tgfoid
        JOIN pg_namespace pn ON pn.oid = p.pronamespace
        WHERE n.nspname = ANY(%s)
            AND NOT t.tgisinternal
        ORDER BY n.nspname, c.relname, t.tgname;
    """)

    # View Queries
    VIEWS = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            c.relname AS view_name,
            r.rolname AS owner,
            obj_description(c.oid, 'pg_class') AS description,
            c.relacl AS privileges,
            c.relkind AS view_type,
            pg_get_viewdef(c.oid) AS definition,
            array_agg(col.attname ORDER BY col.attnum) AS columns
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_roles r ON r.oid = c.relowner
        LEFT JOIN pg_attribute col ON col.attrelid = c.oid
            AND col.attnum > 0
            AND NOT col.attisdropped
        WHERE c.relkind IN ('v', 'm')
            AND n.nspname = ANY(%s)
        GROUP BY n.nspname, c.relname, r.rolname, c.oid, c.relacl, c.relkind
        ORDER BY n.nspname, c.relname;
    """)

    # Function/Procedure Queries
    ROUTINES = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            p.proname AS routine_name,
            r.rolname AS owner,
            obj_description(p.oid, 'pg_proc') AS description,
            p.proacl AS privileges,
            p.prokind AS routine_type,
            pg_get_function_arguments(p.oid) AS arguments,
            pg_get_function_result(p.oid) AS result_type,
            p.provolatile AS volatility,
            p.proparallel AS parallel_safety,
            p.prosecdef AS security_definer,
            p.proleakproof AS leakproof,
            p.proisstrict AS strict,
            p.proretset AS returns_set,
            p.pronargs AS num_args,
            p.pronargdefaults AS num_defaults,
            pg_get_functiondef(p.oid) AS definition
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        JOIN pg_roles r ON r.oid = p.proowner
        WHERE n.nspname = ANY(%s)
        ORDER BY n.nspname, p.proname, pg_get_function_arguments(p.oid);
    """)

    # Type Queries
    TYPES = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            t.typname AS type_name,
            r.rolname AS owner,
            obj_description(t.oid, 'pg_type') AS description,
            t.typtype AS type_type,
            t.typcategory AS type_category,
            t.typdelim AS delimiter,
            t.typnotnull AS not_null,
            t.typdefault AS default_value,
            t.typelem AS array_element_type,
            format_type(t.typbasetype, t.typtypmod) AS base_type,
            CASE t.typtype
                WHEN 'e' THEN (
                    SELECT array_agg(e.enumlabel ORDER BY e.enumsortorder)
                    FROM pg_enum e
                    WHERE e.enumtypid = t.oid
                )
                WHEN 'c' THEN (
                    SELECT array_agg(a.attname || ' ' || format_type(a.atttypid, a.atttypmod)
                                   ORDER BY a.attnum)
                    FROM pg_attribute a
                    WHERE a.attrelid = t.typrelid AND a.attnum > 0
                )
                ELSE NULL
            END AS type_definition
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        JOIN pg_roles r ON r.oid = t.typowner
        WHERE n.nspname = ANY(%s)
            AND (t.typrelid = 0 OR (
                SELECT c.relkind FROM pg_class c WHERE c.oid = t.typrelid
            ) != 'r')
        ORDER BY n.nspname, t.typname;
    """)

    # Extension Queries
    EXTENSIONS = CatalogQuery("""
        SELECT
            e.extname AS extension_name,
            n.nspname AS schema_name,
            r.rolname AS owner,
            e.extversion AS version,
            obj_description(e.oid, 'pg_extension') AS description,
            x.extconfig AS config_tables,
            x.extcondition AS config_conditions
        FROM pg_extension e
        JOIN pg_namespace n ON n.oid = e.extnamespace
        JOIN pg_roles r ON r.oid = e.extowner
        LEFT JOIN pg_extension x ON x.oid = e.oid
        ORDER BY e.extname;
    """)

    # Policy Queries
    POLICIES = CatalogQuery("""
        SELECT
            n.nspname AS schema_name,
            c.relname AS table_name,
            pol.polname AS policy_name,
            r.rolname AS owner,
            pol.polcmd AS command,
            pol.polpermissive AS permissive,
            pg_get_expr(pol.polqual, pol.polrelid) AS using_qual,
            pg_get_expr(pol.polwithcheck, pol.polrelid) AS check_qual,
            array_to_string(ARRAY(
                SELECT pg_authid.rolname
                FROM pg_authid
                WHERE pg_authid.oid = ANY(pol.polroles)
            ), ',') AS roles
        FROM pg_policy pol
        JOIN pg_class c ON c.oid = pol.polrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_roles r ON r.oid = c.relowner
        WHERE n.nspname = ANY(%s)
        ORDER BY n.nspname, c.relname, pol.polname;
    """)

    # Dependency Queries
    DEPENDENCIES = CatalogQuery("""
        SELECT
            d.classid::regclass AS dep_class,
            d.objid AS dep_id,
            d.objsubid AS dep_subid,
            d.refclassid::regclass AS ref_class,
            d.refobjid AS ref_id,
            d.refobjsubid AS ref_subid,
            d.deptype AS dependency_type
        FROM pg_depend d
        JOIN pg_class c ON c.oid = CASE
            WHEN d.classid = 'pg_class'::regclass THEN d.objid
            WHEN d.refclassid = 'pg_class'::regclass THEN d.refobjid
            ELSE 0
        END
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = ANY(%s)
        ORDER BY d.classid, d.objid, d.objsubid;
    """)


class QueryResults:
    """Process and transform query results."""

    @staticmethod
    def process_columns(rows: List[Dict]) -> Dict[str, List[Dict]]:
        """Process column query results."""
        columns_by_table = {}
        for row in rows:
            table_key = f"{row['schema_name']}.{row['table_name']}"
            if table_key not in columns_by_table:
                columns_by_table[table_key] = []

            column = {
                'name': row['column_name'],
                'type': row['data_type'],
                'position': row['ordinal_position'],
                'nullable': not row['not_null'],
                'default': row['default_value'],
                'description': row['description'],
                'full_type': row['full_data_type']
            }

            # Add domain info if applicable
            if row['type_type'] == 'd':
                column['domain_base_type'] = row['domain_base_type']

            # Add identity/generated column info
            if row['identity_type'] != ' ':
                column['identity'] = row['identity_type']
            if row['generated_type'] != ' ':
                column['generated'] = row['generated_type']

            columns_by_table[table_key].append(column)

        return columns_by_table

    @staticmethod
    def process_constraints(rows: List[Dict]) -> Dict[str, List[Dict]]:
        """Process constraint query results."""
        constraints_by_table = {}
        for row in rows:
            table_key = f"{row['schema_name']}.{row['table_name']}"
            if table_key not in constraints_by_table:
                constraints_by_table[table_key] = []

            constraint = {
                'name': row['constraint_name'],
                'type': row['constraint_type'],
                'definition': row['definition'],
                'description': row['description'],
                'columns': row['constrained_columns'],
                'validated': row['is_validated'],
                'deferrable': row['is_deferrable'],
                'deferred': row['is_deferred']
            }

            constraints_by_table[table_key].append(constraint)

        return constraints_by_table

    @staticmethod
    def process_foreign_keys(rows: List[Dict]) -> Dict[str, List[Dict]]:
        """Process foreign key query results."""
        fkeys_by_table = {}
        for row in rows:
            table_key = f"{row['schema_name']}.{row['table_name']}"
            if table_key not in fkeys_by_table:
                fkeys_by_table[table_key] = []

            fkey = {
                'name': row['constraint_name'],
                'referenced_table': f"{row['referenced_schema']}.{row['referenced_table']}",
                'columns': row['constraint_columns'],
                'referenced_columns': row['referenced_columns'],
                'update_action': row['update_action'],
                'delete_action': row['delete_action'],
                'match_type': row['match_type'],
                'definition': row['definition'],
                'description': row['description']
            }

            fkeys_by_table[table_key].append(fkey)

        return fkeys_by_table

    @staticmethod
    def process_indexes(rows: List[Dict]) -> Dict[str, List[Dict]]:
        """Process index query results."""
        indexes_by_table = {}
        for row in rows:
            table_key = f"{row['schema_name']}.{row['table_name']}"
            if table_key not in indexes_by_table:
                indexes_by_table[table_key] = []

            index = {
                'name': row['index_name'],
                'method': row['index_method'],
                'definition': row['definition'],
                'columns': row['indexed_columns'],
                'unique': row['is_unique'],
                'primary': row['is_primary'],
                'clustered': row['is_clustered'],
                'expression': row['expression'],
                'predicate': row['predicate'],
                'size': row['index_size'],
                'scans': row['scan_count'],
                'tuples_read': row['tuples_read'],
                'tuples_fetched': row['tuples_fetched']
            }

            indexes_by_table[table_key].append(index)

        return indexes_by_table


class DatabaseIntrospector:
    """PostgreSQL database introspector using catalog queries."""

    def __init__(self, connection, schemas: List[str] = None):
        self.connection = connection
        self.schemas = schemas or ['public']
        self.type_map = PostgreSQLTypeMap()

    def introspect_database(self) -> Dict[str, Any]:
        """Introspect entire database structure."""
        return {
            'schemas': self.get_schemas(),
            'tables': self.get_tables(),
            'views': self.get_views(),
            'types': self.get_types(),
            'functions': self.get_routines(),
            'extensions': self.get_extensions()
        }

    def get_schemas(self) -> List[Dict]:
        """Get database schemas."""
        with self.connection.cursor() as cursor:
            cursor.execute(CatalogQueries.SCHEMAS.query)
            return cursor.fetchall()

    def get_tables(self) -> Dict[str, Dict]:
        """Get database tables with their structure."""
        tables = {}

        with self.connection.cursor() as cursor:
            # Get basic table information
            cursor.execute(CatalogQueries.TABLES.query, [self.schemas])
            for row in cursor.fetchall():
                table_key = f"{row['schema_name']}.{row['table_name']}"
                tables[table_key] = {
                    'schema': row['schema_name'],
                    'name': row['table_name'],
                    'owner': row['owner'],
                    'description': row['description'],
                    'type': row['table_type'],
                    'is_partition': row['is_partition'],
                    'estimated_rows': row['estimated_rows'],
                    'total_size': row['total_size']
                }

            # Get columns
            cursor.execute(CatalogQueries.COLUMNS.query, [self.schemas])
            columns = QueryResults.process_columns(cursor.fetchall())

            # Get constraints
            cursor.execute(CatalogQueries.CONSTRAINTS.query, [self.schemas])
            constraints = QueryResults.process_constraints(cursor.fetchall())

            # Get foreign keys
            cursor.execute(CatalogQueries.FOREIGN_KEYS.query, [self.schemas])
            foreign_keys = QueryResults.process_foreign_keys(cursor.fetchall())

            # Get indexes
            cursor.execute(CatalogQueries.INDEXES.query, [self.schemas])
            indexes = QueryResults.process_indexes(cursor.fetchall())

            # Combine all information
            for table_key in tables:
                tables[table_key].update({
                    'columns': columns.get(table_key, []),
                    'constraints': constraints.get(table_key, []),
                    'foreign_keys': foreign_keys.get(table_key, []),
                    'indexes': indexes.get(table_key, [])
                })

        return tables

    def get_views(self) -> Dict[str, Dict]:
        """Get database views."""
        views = {}

        with self.connection.cursor() as cursor:
            cursor.execute(CatalogQueries.VIEWS.query, [self.schemas])
            for row in cursor.fetchall():
                view_key = f"{row['schema_name']}.{row['view_name']}"
                views[view_key] = {
                    'schema': row['schema_name'],
                    'name': row['view_name'],
                    'owner': row['owner'],
                    'description': row['description'],
                    'type': row['view_type'],
                    'definition': row['definition'],
                    'columns': row['columns']
                }

        return views

    def get_types(self) -> Dict[str, Dict]:
        """Get database types."""
        types = {}

        with self.connection.cursor() as cursor:
            cursor.execute(CatalogQueries.TYPES.query, [self.schemas])
            for row in cursor.fetchall():
                type_key = f"{row['schema_name']}.{row['type_name']}"
                types[type_key] = {
                    'schema': row['schema_name'],
                    'name': row['type_name'],
                    'owner': row['owner'],
                    'description': row['description'],
                    'type': row['type_type'],
                    'category': row['type_category'],
                    'base_type': row['base_type'],
                    'definition': row['type_definition']
                }

        return types

    def get_routines(self) -> Dict[str, Dict]:
        """Get database functions and procedures."""
        routines = {}

        with self.connection.cursor() as cursor:
            cursor.execute(CatalogQueries.ROUTINES.query, [self.schemas])
            for row in cursor.fetchall():
                routine_key = (
                    f"{row['schema_name']}.{row['routine_name']}"
                    f"({row['arguments']})"
                )
                routines[routine_key] = {
                    'schema': row['schema_name'],
                    'name': row['routine_name'],
                    'owner': row['owner'],
                    'description': row['description'],
                    'type': row['routine_type'],
                    'arguments': row['arguments'],
                    'result_type': row['result_type'],
                    'definition': row['definition'],
                    'volatility': row['volatility'],
                    'security_definer': row['security_definer']
                }

        return routines

    def get_extensions(self) -> List[Dict]:
        """Get installed extensions."""
        with self.connection.cursor() as cursor:
            cursor.execute(CatalogQueries.EXTENSIONS.query)
            return cursor.fetchall()

    def get_dependencies(self) -> List[Dict]:
        """Get object dependencies."""
        with self.connection.cursor() as cursor:
            cursor.execute(CatalogQueries.DEPENDENCIES.query, [self.schemas])
            return cursor.fetchall()


def get_introspection_data(connection, schemas: List[str] = None) -> Dict[str, Any]:
    """Convenience function to get complete database introspection."""
    introspector = DatabaseIntrospector(connection, schemas)
    return introspector.introspect_database()

"""

This enhanced version provides:

1. Comprehensive Catalog Queries:
   - Schema information
   - Tables and columns
   - Constraints and indexes
   - Views and materialized views
   - Functions and procedures
   - Types and domains
   - Extensions and policies
   - Dependencies

2. Result Processing:
   - Structured data transformation
   - Relationship mapping
   - Type system integration
   - Object grouping and organization

3. Integration Features:
   - Works with pg_types module
   - Supports introspection needs
   - Handles complex relationships
   - Maintains type consistency

4. Enhanced Functionality:
   - Complete database structure
   - Object dependencies
   - Performance statistics
   - Security information

5. Utility Features:
   - Schema filtering
   - Result transformation
   - Error handling
   - Documentation

The module is designed to be the central source for all database introspection needs, providing detailed information about database structure and relationships.
"""



#===
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
import re

from model_generator.postgresql.pg_exceptions import PostgreSQLQueryError


@dataclass
class QueryMetrics:
    """Holds query execution metrics."""

    execution_time: float
    rows_affected: int
    plan_time: Optional[float] = None
    actual_time: Optional[float] = None
    planning_time: Optional[float] = None
    execution_time_ms: Optional[float] = None
    total_cost: Optional[float] = None

    def __str__(self) -> str:
        return (
            f"Execution: {self.execution_time:.2f}s, "
            f"Rows: {self.rows_affected}, "
            f"Total Cost: {self.total_cost or 'N/A'}"
        )


class QueryBuilder:
    """Builds PostgreSQL queries with proper escaping and validation."""

    def __init__(self):
        self.params: List[Any] = []
        self.query_parts: List[str] = []

    def add(self, sql: str, *params: Any) -> 'QueryBuilder':
        """Add SQL fragment with parameters."""
        self.query_parts.append(sql)
        self.params.extend(params)
        return self

    def where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """Add WHERE clause."""
        if self.query_parts:
            self.query_parts.append("WHERE")
        self.query_parts.append(condition)
        self.params.extend(params)
        return self

    def and_where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """Add AND condition to WHERE clause."""
        self.query_parts.append("AND")
        self.query_parts.append(condition)
        self.params.extend(params)
        return self

    def or_where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """Add OR condition to WHERE clause."""
        self.query_parts.append("OR")
        self.query_parts.append(condition)
        self.params.extend(params)
        return self

    def order_by(self, *columns: str) -> 'QueryBuilder':
        """Add ORDER BY clause."""
        self.query_parts.append("ORDER BY")
        self.query_parts.append(", ".join(columns))
        return self

    def limit(self, limit: int) -> 'QueryBuilder':
        """Add LIMIT clause."""
        self.query_parts.append("LIMIT %s")
        self.params.append(limit)
        return self

    def offset(self, offset: int) -> 'QueryBuilder':
        """Add OFFSET clause."""
        self.query_parts.append("OFFSET %s")
        self.params.append(offset)
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """Build final query and parameters."""
        return " ".join(self.query_parts), self.params


class SchemaQueries:
    """PostgreSQL schema introspection queries."""

    @staticmethod
    def get_schemas() -> str:
        """Get all schemas."""
        return """
            SELECT
                nspname AS schema_name,
                pg_get_userbyid(nspowner) AS owner,
                obj_description(oid, 'pg_namespace') AS description
            FROM pg_namespace
            WHERE nspname NOT LIKE 'pg_%'
                AND nspname != 'information_schema'
            ORDER BY nspname;
        """

    @staticmethod
    def get_tables(schema: str = 'public') -> str:
        """Get tables in schema."""
        return """
            SELECT
                schemaname AS schema_name,
                tablename AS table_name,
                tableowner AS owner,
                obj_description(
                    (quote_ident(schemaname) || '.' ||
                     quote_ident(tablename))::regclass,
                    'pg_class'
                ) AS description
            FROM pg_tables
            WHERE schemaname = %s
            ORDER BY tablename;
        """

    @staticmethod
    def get_columns(table_name: str, schema: str = 'public') -> str:
        """Get column information for table."""
        return """
            SELECT
                a.attname AS column_name,
                pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
                (SELECT col_description(a.attrelid, a.attnum)) AS description,
                a.attnotnull AS not_null,
                pg_get_expr(d.adbin, d.adrelid) AS default_value,
                CASE
                    WHEN pk.contype = 'p' THEN true
                    ELSE false
                END AS is_primary_key,
                CASE
                    WHEN fk.contype = 'f' THEN true
                    ELSE false
                END AS is_foreign_key
            FROM pg_attribute a
            LEFT JOIN pg_attrdef d ON a.attrelid = d.adrelid AND a.attnum = d.adnum
            LEFT JOIN pg_constraint pk
                ON pk.conrelid = a.attrelid
                AND pk.contype = 'p'
                AND a.attnum = ANY(pk.conkey)
            LEFT JOIN pg_constraint fk
                ON fk.conrelid = a.attrelid
                AND fk.contype = 'f'
                AND a.attnum = ANY(fk.conkey)
            WHERE a.attrelid = %s::regclass
                AND a.attnum > 0
                AND NOT a.attisdropped
            ORDER BY a.attnum;
        """

    @staticmethod
    def get_constraints(table_name: str, schema: str = 'public') -> str:
        """Get table constraints."""
        return """
            SELECT
                con.conname AS constraint_name,
                con.contype AS constraint_type,
                pg_get_constraintdef(con.oid) AS definition,
                obj_description(con.oid, 'pg_constraint') AS description
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE nsp.nspname = %s
                AND rel.relname = %s
            ORDER BY con.contype, con.conname;
        """

    @staticmethod
    def get_indexes(table_name: str, schema: str = 'public') -> str:
        """Get table indexes."""
        return """
            SELECT
                i.relname AS index_name,
                am.amname AS index_type,
                pg_get_indexdef(i.oid) AS definition,
                idx_scan AS usage_count,
                obj_description(i.oid, 'pg_class') AS description
            FROM pg_index x
            JOIN pg_class i ON i.oid = x.indexrelid
            JOIN pg_class t ON t.oid = x.indrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_am am ON i.relam = am.oid
            LEFT JOIN pg_stat_user_indexes sui
                ON sui.indexrelid = i.oid
            WHERE n.nspname = %s
                AND t.relname = %s
            ORDER BY i.relname;
        """

    @staticmethod
    def get_foreign_keys(table_name: str, schema: str = 'public') -> str:
        """Get foreign key relationships."""
        return """
            SELECT
                con.conname AS constraint_name,
                pg_get_constraintdef(con.oid) AS definition,
                ns2.nspname AS referenced_schema,
                cl2.relname AS referenced_table,
                arr.attname AS referenced_column,
                del.deltype AS delete_rule,
                upd.updtype AS update_rule
            FROM pg_constraint con
            JOIN pg_namespace ns1 ON ns1.oid = con.connamespace
            JOIN pg_class cl1 ON cl1.oid = con.conrelid
            JOIN pg_namespace ns2 ON ns2.oid = cl1.relnamespace
            JOIN pg_class cl2 ON cl2.oid = con.confrelid
            JOIN pg_attribute arr ON arr.attrelid = cl2.oid
                AND arr.attnum = ANY(con.confkey)
            LEFT JOIN pg_constraint del ON del.oid = con.oid
                AND del.confdeltype != 'a'
            LEFT JOIN pg_constraint upd ON upd.oid = con.oid
                AND upd.confupdtype != 'a'
            WHERE ns1.nspname = %s
                AND cl1.relname = %s
                AND con.contype = 'f'
            ORDER BY con.conname;
        """


class QueryAnalyzer:
    """Analyzes and optimizes PostgreSQL queries."""

    def __init__(self, connection):
        self.connection = connection

    def explain(self, query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Get query execution plan."""
        explain_query = f"EXPLAIN (ANALYZE, VERBOSE, FORMAT JSON) {query}"

        with self.connection.cursor() as cursor:
            cursor.execute(explain_query, params or [])
            return cursor.fetchone()[0]

    def analyze_performance(self, query: str,
                          params: Optional[List[Any]] = None) -> QueryMetrics:
        """Analyze query performance."""
        plan = self.explain(query, params)

        # Extract metrics from plan
        metrics = QueryMetrics(
            execution_time=plan[0]['Execution Time'] / 1000,  # Convert to seconds
            rows_affected=plan[0]['Plan']['Actual Rows'],
            plan_time=plan[0]['Planning Time'],
            actual_time=plan[0]['Execution Time'],
            total_cost=plan[0]['Plan']['Total Cost']
        )

        return metrics

    def suggest_improvements(self, query: str,
                           params: Optional[List[Any]] = None) -> List[str]:
        """Suggest query improvements."""
        plan = self.explain(query, params)
        suggestions = []

        # Analyze plan nodes
        self._analyze_plan_node(plan[0]['Plan'], suggestions)

        return suggestions

    def _analyze_plan_node(self, node: Dict[str, Any],
                          suggestions: List[str], depth: int = 0) -> None:
        """Recursively analyze plan node for potential improvements."""

        # Check for sequential scans on large tables
        if node['Node Type'] == 'Seq Scan' and node['Actual Rows'] > 1000:
            suggestions.append(
                f"Consider adding an index for table '{node['Relation Name']}' "
                f"to avoid sequential scan"
            )

        # Check for high-cost sorts
        if node['Node Type'] == 'Sort' and node['Actual Total Time'] > 1000:
            suggestions.append(
                "High-cost sort operation detected. Consider adding an index "
                "to avoid sorting"
            )

        # Check for nested loops with many rows
        if node['Node Type'] == 'Nested Loop' and node['Actual Rows'] > 1000:
            suggestions.append(
                "Expensive nested loop detected. Consider using JOIN HINTS "
                "or restructuring the query"
            )

        # Recurse into child nodes
        for child in node.get('Plans', []):
            self._analyze_plan_node(child, suggestions, depth + 1)


class QueryValidator:
    """Validates PostgreSQL queries for security and correctness."""

    def __init__(self):
        self.dangerous_patterns = [
            r';\s*DROP\s+',
            r';\s*DELETE\s+',
            r';\s*TRUNCATE\s+',
            r';\s*ALTER\s+',
            r'--',
            r'/\*.*?\*/',
        ]

    def validate(self, query: str) -> List[str]:
        """Validate query for potential issues."""
        issues = []

        # Check for SQL injection vulnerabilities
        for pattern in self.dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                issues.append(
                    f"Potential SQL injection vulnerability: "
                    f"matched pattern '{pattern}'"
                )

        # Check for proper quoting
        if query.count("'") % 2 != 0:
            issues.append("Unmatched single quotes")

        # Check for common mistakes
        if 'SELECT *' in query.upper():
            issues.append(
                "Using SELECT * is discouraged. "
                "Specify needed columns explicitly"
            )

        if 'WHERE' not in query.upper() and any(
            word in query.upper() for word in ['UPDATE', 'DELETE']
        ):
            issues.append("Missing WHERE clause in UPDATE/DELETE")

        return issues


class QueryMonitor:
    """Monitors query execution and performance."""

    def __init__(self, connection):
        self.connection = connection
        self.slow_query_threshold = 1.0  # seconds

    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow query information."""
        return self.connection.execute("""
            SELECT
                query,
                calls,
                total_time / 1000 AS total_seconds,
                mean_time / 1000 AS mean_seconds,
                rows
            FROM pg_stat_statements
            WHERE mean_time > %s
            ORDER BY mean_time DESC
            LIMIT 10;
        """, [self.slow_query_threshold * 1000])

    def get_query_stats(self) -> Dict[str, Any]:
        """Get overall query statistics."""
        return self.connection.execute("""
            SELECT
                sum(calls) AS total_queries,
                sum(total_time) / 1000 AS total_seconds,
                sum(rows) AS total_rows,
                avg(mean_time) / 1000 AS avg_query_time
            FROM pg_stat_statements;
        """)


def build_query(table: str,
                columns: Optional[List[str]] = None,
                conditions: Optional[Dict[str, Any]] = None,
                order_by: Optional[List[str]] = None,
                limit: Optional[int] = None,
                offset: Optional[int] = None) -> Tuple[str, List[Any]]:
    """
    Build a SELECT query with parameters.

    Args:
        table: Table name
        columns: List of columns to select
        conditions: WHERE conditions as dict
        order_by: ORDER BY columns
        limit: LIMIT value
        offset: OFFSET value

    Returns:
        Tuple of query string and parameters
    """
    builder = QueryBuilder()

    # Build SELECT clause
    select_cols = '*' if not columns else ', '.join(columns)
    builder.add(f"SELECT {select_cols} FROM {table}")

    # Add WHERE conditions
    if conditions:
        where_parts = []
        for key, value in conditions.items():
            where_parts.append(f"{key} = %s")
            builder.params.append(value)
        if where_parts:
            builder.where(' AND '.join(where_parts))

    # Add ORDER BY
    if order_by:
        builder.order_by(*order_by)

    # Add LIMIT/OFFSET
    if limit is not None:
        builder.limit(limit)
    if offset is not None:
        builder.offset(offset)

    return builder.build()


class QueryTemplates:
    """Common PostgreSQL query templates."""

    @staticmethod
    def insert(table: str,
              data: Dict[str, Any],
              returning: Optional[List[str]] = None) -> Tuple[str, List[Any]]:
        """Build INSERT query."""
        columns = list(data.keys())
        values = list(data.values())
        placeholders = [f"%s" for _ in values]

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        if returning:
            query += f" RETURNING {', '.join(returning)}"

        return query, values

    @staticmethod
    def update(table: str,
              data: Dict[str, Any],
              conditions: Dict[str, Any],
              returning: Optional[List[str]] = None) -> Tuple[str, List[Any]]:
        """Build UPDATE query."""
        set_parts = [f"{k} = %s" for k in data.keys()]
        where_parts = [f"{k} = %s" for k in conditions.keys()]

        query = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"

        if returning:
            query += f" RETURNING {', '.join(returning)}"

        values = list(data.values()) + list(conditions.values())
        return query, values

    @staticmethod
    def delete(table: str,
              conditions: Dict[str, Any],
              returning: Optional[List[str]] = None) -> Tuple[str, List[Any]]:
        """Build DELETE query."""
        where_parts = [f"{k} = %s" for k in conditions.keys()]

        query = f"DELETE FROM {table} WHERE {' AND '.join(where_parts)}"

        if returning:
            query += f" RETURNING {', '.join(returning)}"

        return query, list(conditions.values())

"""

This module provides comprehensive support for PostgreSQL query handling:

1. Query Building:
   - Fluent query builder interface
   - Parameter binding and escaping
   - Common query templates

2. Schema Introspection:
   - Queries for schemas, tables, columns
   - Constraint and index information
   - Foreign key relationships

3. Query Analysis:
   - Execution plan analysis
   - Performance metrics
   - Optimization suggestions

4. Query Validation:
   - Security checks
   - SQL injection prevention
   - Common mistake detection

5. Performance Monitoring:
   - Slow query tracking
   - Query statistics
   - Performance metrics

6. Helper Functions:
   - Common query building
   - Parameter handling
   - Query templates

The code is designed to work with both raw SQL and higher-level abstractions,
providing comprehensive tools for working with PostgreSQL queries safely and efficiently.

This module provides comprehensive support for PostgreSQL query handling:

1. Query Building:
   - Fluent query builder interface
   - Parameter binding and escaping
   - Common query templates

2. Schema Introspection:
   - Queries for schemas, tables, columns
   - Constraint and index information
   - Foreign key relationships

3. Query Analysis:
   - Execution plan analysis
   - Performance metrics
   - Optimization suggestions

4. Query Validation:
   - Security checks
   - SQL injection prevention
   - Common mistake detection

5. Performance Monitoring:
   - Slow query tracking
   - Query statistics
   - Performance metrics

6. Helper Functions:
   - Common query building
   - Parameter handling
   - Query templates

The code is designed to work with both raw SQL and higher-level abstractions, providing comprehensive tools for working with PostgreSQL queries safely and efficiently.

Enhance pg_queries.py so that:
Contains all PostgreSQL catalog queries
Defines query templates and result processing functions
Depends on pg_types
Used by the introspector for database inspection

Here's an enhanced version of `pg_queries.py` with comprehensive catalog queries and introspection support:

pg_queries.py: PostgreSQL catalog queries and introspection.

This module provides comprehensive catalog queries and result processing for
PostgreSQL database introspection. It contains all queries needed to inspect
database objects and their relationships.

Key Features:
    - Complete catalog query collection
    - Result processing functions
    - Type system integration
    - Introspection support
    - Relationship mapping
    - Object dependencies

Author: Nyimbi Odero
Copyright: 2024
License: MIT
"""
