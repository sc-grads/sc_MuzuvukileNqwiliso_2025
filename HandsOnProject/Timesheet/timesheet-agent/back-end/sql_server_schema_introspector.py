#!/usr/bin/env python3
"""
SQL Server Schema Introspection System

This module implements SQL Server-specific schema discovery utilities for the RAG-based SQL agent.
It provides comprehensive database schema introspection, metadata extraction, relationship detection,
and constraint/index information gathering specifically optimized for SQL Server databases.

Implements task 7.1: Implement SQL Server schema introspection
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from datetime import datetime
import json
import re
from sqlalchemy import create_engine, inspect, text, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import urllib.parse

from config import MSSQL_CONNECTION, get_current_database, update_mssql_connection, EXCLUDE_TABLE_PATTERNS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SQLServerTableInfo:
    """Comprehensive SQL Server table information"""
    schema_name: str
    table_name: str
    table_type: str  # 'BASE TABLE', 'VIEW', 'SYSTEM TABLE'
    created_date: Optional[datetime]
    modified_date: Optional[datetime]
    row_count: Optional[int]
    data_space_kb: Optional[int]
    index_space_kb: Optional[int]
    description: Optional[str]
    is_replicated: bool
    is_tracked_by_cdc: bool  # Change Data Capture
    temporal_type: Optional[str]  # For temporal tables


@dataclass
class SQLServerColumnInfo:
    """Comprehensive SQL Server column information"""
    column_name: str
    ordinal_position: int
    data_type: str
    max_length: Optional[int]
    precision: Optional[int]
    scale: Optional[int]
    is_nullable: bool
    default_value: Optional[str]
    is_identity: bool
    identity_seed: Optional[int]
    identity_increment: Optional[int]
    is_computed: bool
    computed_definition: Optional[str]
    is_primary_key: bool
    is_foreign_key: bool
    is_unique: bool
    is_indexed: bool
    collation_name: Optional[str]
    description: Optional[str]
    is_sparse: bool
    is_column_set: bool
    is_filestream: bool


@dataclass
class SQLServerConstraintInfo:
    """SQL Server constraint information"""
    constraint_name: str
    constraint_type: str  # 'PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CHECK', 'DEFAULT'
    table_schema: str
    table_name: str
    column_names: List[str]
    referenced_schema: Optional[str]
    referenced_table: Optional[str]
    referenced_columns: Optional[List[str]]
    constraint_definition: Optional[str]
    is_disabled: bool
    is_not_trusted: bool


@dataclass
class SQLServerIndexInfo:
    """SQL Server index information"""
    index_name: str
    table_schema: str
    table_name: str
    index_type: str  # 'CLUSTERED', 'NONCLUSTERED', 'COLUMNSTORE', etc.
    is_unique: bool
    is_primary_key: bool
    is_unique_constraint: bool
    key_columns: List[str]
    included_columns: List[str]
    filter_definition: Optional[str]
    fill_factor: Optional[int]
    is_disabled: bool
    compression_type: Optional[str]


@dataclass
class SQLServerRelationshipInfo:
    """SQL Server relationship information with enhanced metadata"""
    constraint_name: str
    parent_schema: str
    parent_table: str
    parent_columns: List[str]
    referenced_schema: str
    referenced_table: str
    referenced_columns: List[str]
    delete_rule: str  # 'CASCADE', 'SET NULL', 'SET DEFAULT', 'NO ACTION'
    update_rule: str
    is_disabled: bool
    is_not_trusted: bool
    relationship_type: str  # 'one_to_one', 'one_to_many', 'many_to_many'


@dataclass
class SQLServerSchemaIntrospectionResult:
    """Result of SQL Server schema introspection"""
    database_name: str
    server_name: str
    introspection_timestamp: datetime
    tables: List[SQLServerTableInfo]
    columns: Dict[str, List[SQLServerColumnInfo]]  # table_key -> columns
    constraints: List[SQLServerConstraintInfo]
    indexes: List[SQLServerIndexInfo]
    relationships: List[SQLServerRelationshipInfo]
    schemas: List[str]
    total_tables: int
    total_columns: int
    total_relationships: int
    processing_time_seconds: float
    errors: List[str]


class SQLServerSchemaIntrospector:
    """
    Comprehensive SQL Server schema introspection system.
    
    This class provides detailed schema discovery capabilities specifically
    optimized for SQL Server databases, including T-SQL specific features,
    constraints, indexes, and relationships.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize SQL Server schema introspector.
        
        Args:
            connection_string: Optional SQL Server connection string. 
                             Uses config default if not provided.
        """
        self.connection_string = connection_string or MSSQL_CONNECTION
        self.engine: Optional[Engine] = None
        self.current_database = get_current_database()
        
        # SQL Server system schemas to exclude by default
        self.system_schemas = {
            'INFORMATION_SCHEMA', 'sys', 'guest', 'db_owner', 'db_accessadmin',
            'db_securityadmin', 'db_ddladmin', 'db_backupoperator', 
            'db_datareader', 'db_datawriter', 'db_denydatareader', 'db_denydatawriter'
        }
        
        # Initialize database connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize SQL Server database connection"""
        try:
            # Convert ODBC connection string to SQLAlchemy format
            encoded_conn = urllib.parse.quote_plus(self.connection_string)
            sqlalchemy_url = f"mssql+pyodbc:///?odbc_connect={encoded_conn}"
            
            self.engine = create_engine(sqlalchemy_url, echo=False)
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT @@SERVERNAME as server_name, DB_NAME() as database_name"))
                row = result.fetchone()
                logger.info(f"Connected to SQL Server: {row.server_name}, Database: {row.database_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize SQL Server connection: {e}")
            raise
    
    def introspect_database_schema(self, 
                                 include_system_objects: bool = False,
                                 schema_filter: Optional[List[str]] = None,
                                 table_filter: Optional[List[str]] = None) -> SQLServerSchemaIntrospectionResult:
        """
        Perform comprehensive SQL Server database schema introspection.
        
        Args:
            include_system_objects: Whether to include system tables and views
            schema_filter: Optional list of schema names to include
            table_filter: Optional list of table name patterns to include
            
        Returns:
            SQLServerSchemaIntrospectionResult with complete schema information
        """
        start_time = datetime.now()
        
        result = SQLServerSchemaIntrospectionResult(
            database_name=self.current_database,
            server_name="",
            introspection_timestamp=start_time,
            tables=[],
            columns={},
            constraints=[],
            indexes=[],
            relationships=[],
            schemas=[],
            total_tables=0,
            total_columns=0,
            total_relationships=0,
            processing_time_seconds=0.0,
            errors=[]
        )
        
        try:
            with self.engine.connect() as conn:
                # Get server information
                server_info = conn.execute(text("SELECT @@SERVERNAME as server_name")).fetchone()
                result.server_name = server_info.server_name
                
                logger.info(f"Starting SQL Server schema introspection for database: {self.current_database}")
                
                # Phase 1: Discover schemas
                result.schemas = self._discover_schemas(conn, include_system_objects, schema_filter)
                
                # Phase 2: Discover tables
                result.tables = self._discover_tables(conn, result.schemas, table_filter, result)
                
                # Phase 3: Discover columns
                result.columns = self._discover_columns(conn, result.tables, result)
                
                # Phase 4: Discover constraints
                result.constraints = self._discover_constraints(conn, result.schemas, result)
                
                # Phase 5: Discover indexes
                result.indexes = self._discover_indexes(conn, result.schemas, result)
                
                # Phase 6: Discover relationships
                result.relationships = self._discover_relationships(conn, result.schemas, result)
                
                # Update statistics
                result.total_tables = len(result.tables)
                result.total_columns = sum(len(cols) for cols in result.columns.values())
                result.total_relationships = len(result.relationships)
                
                end_time = datetime.now()
                result.processing_time_seconds = (end_time - start_time).total_seconds()
                
                logger.info(f"Schema introspection completed: {result.total_tables} tables, "
                          f"{result.total_columns} columns, {result.total_relationships} relationships "
                          f"in {result.processing_time_seconds:.2f}s")
                
        except Exception as e:
            error_msg = f"Schema introspection failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return result    

    def _discover_schemas(self, conn, include_system_objects: bool, schema_filter: Optional[List[str]]) -> List[str]:
        """Discover database schemas"""
        try:
            query = """
            SELECT schema_name
            FROM INFORMATION_SCHEMA.SCHEMATA
            ORDER BY schema_name
            """
            
            result = conn.execute(text(query))
            schemas = [row.schema_name for row in result]
            
            # Filter out system schemas unless requested
            if not include_system_objects:
                schemas = [s for s in schemas if s not in self.system_schemas]
            
            # Apply schema filter if provided
            if schema_filter:
                schemas = [s for s in schemas if s in schema_filter]
            
            logger.info(f"Discovered {len(schemas)} schemas: {', '.join(schemas)}")
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to discover schemas: {e}")
            return []
    
    def _discover_tables(self, conn, schemas: List[str], table_filter: Optional[List[str]], 
                        result: SQLServerSchemaIntrospectionResult) -> List[SQLServerTableInfo]:
        """Discover tables with comprehensive metadata"""
        tables = []
        if not schemas:
            return tables
            
        try:
            # PERFORMANCE: Fetch all tables for all schemas in a single query
            schema_placeholders = ', '.join([f"'{s}'" for s in schemas])
            query = f"""
            SELECT 
                t.TABLE_SCHEMA as schema_name,
                t.TABLE_NAME as table_name,
                t.TABLE_TYPE as table_type,
                o.create_date,
                o.modify_date,
                ISNULL(p.row_count, 0) as row_count,
                CAST(ROUND(((SUM(ISNULL(a.total_pages, 0)) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS data_space_mb,
                CAST(ROUND(((SUM(ISNULL(a.used_pages, 0)) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS index_space_mb,
                CAST(ep.value AS VARCHAR(MAX)) as description,
                CASE WHEN r.object_id IS NOT NULL THEN 1 ELSE 0 END as is_replicated,
                CASE WHEN ctt.object_id IS NOT NULL THEN 1 ELSE 0 END as is_tracked_by_cdc,
                ISNULL(tt.temporal_type_desc, 'NON_TEMPORAL_TABLE') as temporal_type
            FROM INFORMATION_SCHEMA.TABLES t
            LEFT JOIN sys.objects o ON o.name = t.TABLE_NAME AND o.schema_id = SCHEMA_ID(t.TABLE_SCHEMA)
            LEFT JOIN sys.dm_db_partition_stats p ON p.object_id = o.object_id AND p.index_id < 2
            LEFT JOIN sys.allocation_units a ON p.partition_id = a.container_id
            LEFT JOIN sys.extended_properties ep ON ep.major_id = o.object_id AND ep.minor_id = 0 AND ep.name = 'MS_Description'
            LEFT JOIN sys.tables r ON r.object_id = o.object_id AND r.is_replicated = 1
            LEFT JOIN sys.change_tracking_tables ctt ON ctt.object_id = o.object_id
            LEFT JOIN sys.tables tt ON tt.object_id = o.object_id
            WHERE t.TABLE_SCHEMA IN ({schema_placeholders})
            GROUP BY t.TABLE_SCHEMA, t.TABLE_NAME, t.TABLE_TYPE, o.create_date, o.modify_date, 
                     p.row_count, ep.value, r.object_id, ctt.object_id, tt.temporal_type_desc
            ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME
            """
            
            query_result = conn.execute(text(query))
            
            for row in query_result:
                # Apply table filter if provided
                if table_filter and not any(pattern.lower() in row.table_name.lower() for pattern in table_filter):
                    continue

                # Exclude tables based on patterns from config
                table_name = row.table_name
                if any(re.search(pattern, table_name, re.IGNORECASE) for pattern in EXCLUDE_TABLE_PATTERNS):
                    logger.debug(f"Excluding table '{table_name}' due to exclusion pattern.")
                    continue
                
                table_info = SQLServerTableInfo(
                    schema_name=row.schema_name,
                    table_name=row.table_name,
                    table_type=row.table_type,
                    created_date=row.create_date,
                    modified_date=row.modify_date,
                    row_count=row.row_count or 0,
                    data_space_kb=int((row.data_space_mb or 0) * 1024),
                    index_space_kb=int((row.index_space_mb or 0) * 1024),
                    description=row.description,
                    is_replicated=bool(row.is_replicated),
                    is_tracked_by_cdc=bool(row.is_tracked_by_cdc),
                    temporal_type=row.temporal_type
                )
                
                tables.append(table_info)
            
            logger.info(f"Discovered {len(tables)} tables")
            return tables
            
        except Exception as e:
            error_msg = f"Failed to discover tables: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return []    
 
    def _discover_columns(self, conn, tables: List[SQLServerTableInfo], 
                          result: SQLServerSchemaIntrospectionResult) -> Dict[str, List[SQLServerColumnInfo]]:
        """Discover columns with comprehensive metadata"""
        columns_dict = {}
        if not tables:
            return columns_dict

        table_schemas = tuple(set(t.schema_name for t in tables))
        
        try:
            # Use a simpler approach - get basic column info without complex joins to avoid ODBC issues
            for table in tables:
                table_key = f"{table.schema_name}.{table.table_name}"
                columns_dict[table_key] = []
                
                try:
                    # Simplified query to avoid ODBC type conversion issues
                    # Use string formatting to avoid parameter binding issues with pyodbc
                    query = f"""
                    SELECT 
                        c.name as column_name,
                        c.column_id as ordinal_position,
                        t.name as data_type,
                        CASE WHEN c.max_length = -1 THEN NULL ELSE c.max_length END as max_length,
                        CASE WHEN c.precision = 0 THEN NULL ELSE c.precision END as precision,
                        CASE WHEN c.scale = 0 THEN NULL ELSE c.scale END as scale,
                        c.is_nullable,
                        c.is_identity,
                        c.is_computed,
                        c.collation_name,
                        c.is_sparse,
                        c.is_column_set,
                        c.is_filestream
                    FROM sys.columns c
                    JOIN sys.objects o ON c.object_id = o.object_id
                    JOIN sys.schemas s ON o.schema_id = s.schema_id
                    JOIN sys.types t ON c.user_type_id = t.user_type_id
                    WHERE s.name = '{table.schema_name}' AND o.name = '{table.table_name}' AND o.type = 'U'
                    ORDER BY c.column_id
                    """
                    
                    # Execute query without parameter binding to avoid pyodbc issues
                    query_result = conn.execute(text(query))
                    
                    # Fetch all results to avoid connection busy issues
                    rows = query_result.fetchall()
                    
                    for row in rows:
                        column_info = SQLServerColumnInfo(
                            column_name=row.column_name,
                            ordinal_position=row.ordinal_position,
                            data_type=row.data_type,
                            max_length=row.max_length,
                            precision=row.precision,
                            scale=row.scale,
                            is_nullable=bool(row.is_nullable),
                            default_value=None,  # Simplified to avoid ODBC issues
                            is_identity=bool(row.is_identity),
                            identity_seed=None,  # Simplified to avoid ODBC issues
                            identity_increment=None,  # Simplified to avoid ODBC issues
                            is_computed=bool(row.is_computed),
                            computed_definition=None,  # Simplified to avoid ODBC issues
                            is_primary_key=False,  # Will be determined separately if needed
                            is_foreign_key=False,  # Will be determined separately if needed
                            is_unique=False,  # Will be determined separately if needed
                            is_indexed=False,  # Will be determined separately if needed
                            collation_name=row.collation_name,
                            description=None,  # Simplified to avoid ODBC issues
                            is_sparse=bool(row.is_sparse),
                            is_column_set=bool(row.is_column_set),
                            is_filestream=bool(row.is_filestream)
                        )
                        columns_dict[table_key].append(column_info)
                
                except Exception as table_error:
                    # Log error for this specific table but continue with others
                    error_msg = f"Failed to discover columns for table {table_key}: {table_error}"
                    logger.warning(error_msg)
                    result.errors.append(error_msg)
                    # Keep empty list for this table
            
            total_columns = sum(len(cols) for cols in columns_dict.values())
            logger.info(f"Discovered {total_columns} columns across {len(columns_dict)} tables")
            return columns_dict
            
        except Exception as e:
            error_msg = f"Failed to discover columns: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return {}    

    def _discover_constraints(self, conn, schemas: List[str], 
                            result: SQLServerSchemaIntrospectionResult) -> List[SQLServerConstraintInfo]:
        """Discover database constraints"""
        constraints = []
        if not schemas:
            return constraints

        try:
            # PERFORMANCE: Fetch all constraints for all schemas in a single query
            # BUGFIX: Correctly identify the referenced table name for foreign keys
            schema_placeholders = ', '.join([f"'{s}'" for s in schemas])
            query = f"""
            WITH ConstraintColumns AS (
                SELECT 
                    CONSTRAINT_NAME, 
                    TABLE_SCHEMA, 
                    TABLE_NAME, 
                    STRING_AGG(COLUMN_NAME, ', ') WITHIN GROUP (ORDER BY ORDINAL_POSITION) as column_names
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                GROUP BY CONSTRAINT_NAME, TABLE_SCHEMA, TABLE_NAME
            )
            SELECT 
                tc.CONSTRAINT_NAME as constraint_name,
                tc.CONSTRAINT_TYPE as constraint_type,
                tc.TABLE_SCHEMA as table_schema,
                tc.TABLE_NAME as table_name,
                cc_agg.column_names,
                rc_tc.TABLE_SCHEMA as referenced_schema,
                rc_tc.TABLE_NAME as referenced_table,
                rc_agg.column_names as referenced_columns,
                cc.CHECK_CLAUSE as constraint_definition,
                CASE WHEN sc.is_disabled = 1 THEN 1 ELSE 0 END as is_disabled,
                CASE WHEN sc.is_not_trusted = 1 THEN 1 ELSE 0 END as is_not_trusted
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            LEFT JOIN ConstraintColumns cc_agg 
                ON tc.CONSTRAINT_NAME = cc_agg.CONSTRAINT_NAME 
                AND tc.TABLE_SCHEMA = cc_agg.TABLE_SCHEMA 
                AND tc.TABLE_NAME = cc_agg.TABLE_NAME
            LEFT JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc 
                ON tc.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            LEFT JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS rc_tc
                ON rc.UNIQUE_CONSTRAINT_NAME = rc_tc.CONSTRAINT_NAME
            LEFT JOIN ConstraintColumns rc_agg
                ON rc.UNIQUE_CONSTRAINT_NAME = rc_agg.CONSTRAINT_NAME
            LEFT JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS cc 
                ON tc.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
            LEFT JOIN sys.objects sc_obj ON sc_obj.name = tc.CONSTRAINT_NAME
            LEFT JOIN sys.foreign_keys sc ON sc.object_id = sc_obj.object_id
            WHERE tc.TABLE_SCHEMA IN ({schema_placeholders})
            ORDER BY tc.TABLE_SCHEMA, tc.TABLE_NAME, tc.CONSTRAINT_TYPE
            """
            
            query_result = conn.execute(text(query))
            
            for row in query_result:
                constraint_info = SQLServerConstraintInfo(
                    constraint_name=row.constraint_name,
                    constraint_type=row.constraint_type,
                    table_schema=row.table_schema,
                    table_name=row.table_name,
                    column_names=row.column_names.split(', ') if row.column_names else [],
                    referenced_schema=row.referenced_schema,
                    referenced_table=row.referenced_table,
                    referenced_columns=row.referenced_columns.split(', ') if row.referenced_columns else None,
                    constraint_definition=row.constraint_definition,
                    is_disabled=bool(row.is_disabled) if row.is_disabled is not None else False,
                    is_not_trusted=bool(row.is_not_trusted) if row.is_not_trusted is not None else False
                )
                constraints.append(constraint_info)
            
            logger.info(f"Discovered {len(constraints)} constraints")
            return constraints
            
        except Exception as e:
            error_msg = f"Failed to discover constraints: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return []
    
    def _discover_indexes(self, conn, schemas: List[str], 
                         result: SQLServerSchemaIntrospectionResult) -> List[SQLServerIndexInfo]:
        """Discover database indexes"""
        indexes = []
        if not schemas:
            return indexes
            
        try:
            # PERFORMANCE: Fetch all indexes for all schemas in a single query
            schema_placeholders = ', '.join([f"'{s}'" for s in schemas])
            query = f"""
            SELECT 
                i.name as index_name,
                s.name as table_schema,
                t.name as table_name,
                i.type_desc as index_type,
                CASE WHEN i.is_unique = 1 THEN 1 ELSE 0 END as is_unique,
                CASE WHEN i.is_primary_key = 1 THEN 1 ELSE 0 END as is_primary_key,
                CASE WHEN i.is_unique_constraint = 1 THEN 1 ELSE 0 END as is_unique_constraint,
                STRING_AGG(CASE WHEN ic.is_included_column = 0 THEN c.name END, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) as key_columns,
                STRING_AGG(CASE WHEN ic.is_included_column = 1 THEN c.name END, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) as included_columns,
                i.filter_definition,
                i.fill_factor,
                CASE WHEN i.is_disabled = 1 THEN 1 ELSE 0 END as is_disabled,
                p.data_compression_desc as compression_type
            FROM sys.indexes i
            JOIN sys.tables t ON i.object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            LEFT JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            LEFT JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            LEFT JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
            WHERE s.name IN ({schema_placeholders}) AND i.type > 0  -- Exclude heaps
            GROUP BY i.name, s.name, t.name, i.type_desc, i.is_unique, i.is_primary_key, 
                     i.is_unique_constraint, i.filter_definition, i.fill_factor, i.is_disabled,
                     p.data_compression_desc
            ORDER BY s.name, t.name, i.name
            """
            
            query_result = conn.execute(text(query))
            
            for row in query_result:
                index_info = SQLServerIndexInfo(
                    index_name=row.index_name,
                    table_schema=row.table_schema,
                    table_name=row.table_name,
                    index_type=row.index_type,
                    is_unique=bool(row.is_unique),
                    is_primary_key=bool(row.is_primary_key),
                    is_unique_constraint=bool(row.is_unique_constraint),
                    key_columns=row.key_columns.split(', ') if row.key_columns else [],
                    included_columns=row.included_columns.split(', ') if row.included_columns else [],
                    filter_definition=row.filter_definition,
                    fill_factor=row.fill_factor,
                    is_disabled=bool(row.is_disabled),
                    compression_type=row.compression_type
                )
                indexes.append(index_info)
            
            logger.info(f"Discovered {len(indexes)} indexes")
            return indexes
            
        except Exception as e:
            error_msg = f"Failed to discover indexes: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return []   
 
    def _discover_relationships(self, conn, schemas: List[str], 
                              result: SQLServerSchemaIntrospectionResult) -> List[SQLServerRelationshipInfo]:
        """Discover foreign key relationships with enhanced metadata"""
        relationships = []
        if not schemas:
            return relationships
            
        try:
            # PERFORMANCE: Fetch all relationships for all schemas in a single query
            schema_placeholders = ', '.join([f"'{s}'" for s in schemas])
            query = f"""
            SELECT 
                fk.name as constraint_name,
                ps.name as parent_schema,
                pt.name as parent_table,
                STRING_AGG(pc.name, ', ') WITHIN GROUP (ORDER BY fkc.constraint_column_id) as parent_columns,
                rs.name as referenced_schema,
                rt.name as referenced_table,
                STRING_AGG(rc.name, ', ') WITHIN GROUP (ORDER BY fkc.constraint_column_id) as referenced_columns,
                fk.delete_referential_action_desc as delete_rule,
                fk.update_referential_action_desc as update_rule,
                CASE WHEN fk.is_disabled = 1 THEN 1 ELSE 0 END as is_disabled,
                CASE WHEN fk.is_not_trusted = 1 THEN 1 ELSE 0 END as is_not_trusted
            FROM sys.foreign_keys fk
            JOIN sys.tables pt ON fk.parent_object_id = pt.object_id
            JOIN sys.schemas ps ON pt.schema_id = ps.schema_id
            JOIN sys.tables rt ON fk.referenced_object_id = rt.object_id
            JOIN sys.schemas rs ON rt.schema_id = rs.schema_id
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            JOIN sys.columns pc ON fkc.parent_object_id = pc.object_id AND fkc.parent_column_id = pc.column_id
            JOIN sys.columns rc ON fkc.referenced_object_id = rc.object_id AND fkc.referenced_column_id = rc.column_id
            WHERE ps.name IN ({schema_placeholders}) OR rs.name IN ({schema_placeholders})
            GROUP BY fk.name, ps.name, pt.name, rs.name, rt.name, 
                     fk.delete_referential_action_desc, fk.update_referential_action_desc,
                     fk.is_disabled, fk.is_not_trusted
            ORDER BY ps.name, pt.name, fk.name
            """
            
            query_result = conn.execute(text(query)).fetchall()
            
            for row in query_result:
                # Determine relationship type based on constraints and indexes
                relationship_type = self._determine_relationship_type(
                    conn, row.parent_schema, row.parent_table, row.parent_columns.split(', '),
                    row.referenced_schema, row.referenced_table, row.referenced_columns.split(', ')
                )
                
                relationship_info = SQLServerRelationshipInfo(
                    constraint_name=row.constraint_name,
                    parent_schema=row.parent_schema,
                    parent_table=row.parent_table,
                    parent_columns=row.parent_columns.split(', '),
                    referenced_schema=row.referenced_schema,
                    referenced_table=row.referenced_table,
                    referenced_columns=row.referenced_columns.split(', '),
                    delete_rule=row.delete_rule,
                    update_rule=row.update_rule,
                    is_disabled=bool(row.is_disabled),
                    is_not_trusted=bool(row.is_not_trusted),
                    relationship_type=relationship_type
                )
                relationships.append(relationship_info)
            
            logger.info(f"Discovered {len(relationships)} relationships")
            return relationships
            
        except Exception as e:
            error_msg = f"Failed to discover relationships: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return []
    
    def _determine_relationship_type(self, conn, parent_schema: str, parent_table: str, parent_columns: List[str],
                                   referenced_schema: str, referenced_table: str, referenced_columns: List[str]) -> str:
        """Determine the type of relationship (one-to-one, one-to-many, many-to-many)"""
        try:
            # Check if parent columns form a unique constraint or are part of primary key
            parent_columns_placeholders = ', '.join([f"'{c}'" for c in parent_columns])
            parent_unique_query = f"""
            SELECT COUNT(*) as unique_count
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            JOIN sys.tables t ON i.object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = :s_name AND t.name = :t_name 
                  AND c.name IN ({parent_columns_placeholders}) AND (i.is_unique = 1 OR i.is_primary_key = 1)
            """
            
            parent_result = conn.execute(text(parent_unique_query), {"s_name": parent_schema, "t_name": parent_table}).fetchone()
            
            parent_is_unique = parent_result.unique_count > 0
            
            # Check if this is a junction table (many-to-many indicator)
            junction_query = """
            SELECT COUNT(*) as fk_count
            FROM sys.foreign_keys fk
            JOIN sys.tables t ON fk.parent_object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = :s_name AND t.name = :t_name
            """
            
            junction_result = conn.execute(text(junction_query), {"s_name": parent_schema, "t_name": parent_table}).fetchone()
            
            fk_count = junction_result.fk_count
            
            # Determine relationship type
            if fk_count >= 2:  # Junction table with multiple FKs
                return 'many_to_many'
            elif parent_is_unique:
                return 'one_to_one'
            else:
                return 'one_to_many'
                
        except Exception as e:
            logger.warning(f"Failed to determine relationship type: {e}")
            return 'one_to_many'  # Default assumption
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            with self.engine.connect() as conn:
                stats_query = """
                SELECT 
                    DB_NAME() as database_name,
                    @@SERVERNAME as server_name,
                    (SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped = 0) as user_table_count,
                    (SELECT COUNT(*) FROM sys.views WHERE is_ms_shipped = 0) as user_view_count,
                    (SELECT COUNT(*) FROM sys.schemas WHERE schema_id > 4) as user_schema_count,
                    (SELECT COUNT(*) FROM sys.foreign_keys) as foreign_key_count,
                    (SELECT COUNT(*) FROM sys.indexes WHERE type > 0) as index_count,
                    (SELECT SUM(rows) FROM sys.partitions WHERE index_id < 2) as total_rows,
                    CAST(SUM(size) * 8.0 / 1024 AS DECIMAL(10,2)) as database_size_mb
                FROM sys.database_files
                WHERE type = 0  -- Data files only
                """
                
                result = conn.execute(text(stats_query)).fetchone()
                
                return {
                    'database_name': result.database_name,
                    'server_name': result.server_name,
                    'user_table_count': result.user_table_count,
                    'user_view_count': result.user_view_count,
                    'user_schema_count': result.user_schema_count,
                    'foreign_key_count': result.foreign_key_count,
                    'index_count': result.index_count,
                    'total_rows': result.total_rows or 0,
                    'database_size_mb': float(result.database_size_mb or 0)
                }
                
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {}
    
    def switch_database(self, database_name: str) -> bool:
        """
        Switch to a different database on the same SQL Server instance.
        
        Args:
            database_name: Name of the database to switch to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Dispose of the old engine if it exists
            if self.engine:
                self.engine.dispose()
                self.engine = None
            
            # Update connection string
            update_mssql_connection(database_name)
            # Import the updated connection string
            from config import MSSQL_CONNECTION
            self.connection_string = MSSQL_CONNECTION
            self.current_database = database_name
            
            # Reinitialize connection with new database
            self._initialize_connection()
            
            logger.info(f"Successfully switched to database: {database_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to database {database_name}: {e}")
            return False
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """List all databases on the SQL Server instance"""
        try:
            with self.engine.connect() as conn:
                query = """
                SELECT 
                    name as database_name,
                    database_id,
                    create_date,
                    collation_name,
                    state_desc as state,
                    recovery_model_desc as recovery_model,
                    compatibility_level,
                    is_read_only,
                    is_auto_close_on,
                    is_auto_shrink_on
                FROM sys.databases
                WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')
                ORDER BY name
                """
                
                result = conn.execute(text(query))
                databases = []
                
                for row in result:
                    databases.append({
                        'database_name': row.database_name,
                        'database_id': row.database_id,
                        'create_date': row.create_date,
                        'collation_name': row.collation_name,
                        'state': row.state,
                        'recovery_model': row.recovery_model,
                        'compatibility_level': row.compatibility_level,
                        'is_read_only': bool(row.is_read_only),
                        'is_auto_close_on': bool(row.is_auto_close_on),
                        'is_auto_shrink_on': bool(row.is_auto_shrink_on)
                    })
                
                return databases
                
        except Exception as e:
            logger.error(f"Failed to list databases: {e}")
            return []


def main():
    """Main function for testing SQL Server schema introspection"""
    try:
        # Initialize introspector
        introspector = SQLServerSchemaIntrospector()
        
        # --- ADD THIS LINE TO TEST A DIFFERENT DATABASE ---
        # Replace "YourTestDatabaseName" with the actual name of the database you want to test.
        # introspector.switch_database("YourTestDatabaseName")
        
        # Get database statistics
        stats = introspector.get_database_statistics()
        print(f"Database Statistics: {json.dumps(stats, indent=2)}")
        
        # Perform schema introspection
        result = introspector.introspect_database_schema()
        
        print(f"\nSchema Introspection Results:")
        print(f"Database: {result.database_name}")
        print(f"Server: {result.server_name}")
        print(f"Tables: {result.total_tables}")
        print(f"Columns: {result.total_columns}")
        print(f"Relationships: {result.total_relationships}")
        print(f"Processing Time: {result.processing_time_seconds:.2f}s")
        
        if result.errors:
            print(f"Errors: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        # Show sample table information
        if result.tables:
            print(f"\nSample Tables:")
            for table in result.tables[:3]:  # Show first 3 tables
                print(f"  {table.schema_name}.{table.table_name} ({table.table_type}) - {table.row_count} rows")
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")


if __name__ == "__main__":
    main()