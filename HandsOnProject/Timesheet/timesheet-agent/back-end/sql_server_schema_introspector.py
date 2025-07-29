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

from config import MSSQL_CONNECTION, get_current_database, update_mssql_connection

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

cla
ss SQLServerSchemaIntrospector:
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
        
        try:
            for schema in schemas:
                query = """
                SELECT 
                    t.TABLE_SCHEMA as schema_name,
                    t.TABLE_NAME as table_name,
                    t.TABLE_TYPE as table_type,
                    o.create_date,
                    o.modify_date,
                    ISNULL(p.rows, 0) as row_count,
                    CAST(ROUND(((SUM(ISNULL(a.total_pages, 0)) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS data_space_mb,
                    CAST(ROUND(((SUM(ISNULL(a.used_pages, 0)) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS index_space_mb,
                    ep.value as description,
                    CASE WHEN r.object_id IS NOT NULL THEN 1 ELSE 0 END as is_replicated,
                    CASE WHEN cdc.object_id IS NOT NULL THEN 1 ELSE 0 END as is_tracked_by_cdc,
                    ISNULL(tt.temporal_type_desc, 'NON_TEMPORAL_TABLE') as temporal_type
                FROM INFORMATION_SCHEMA.TABLES t
                LEFT JOIN sys.objects o ON o.name = t.TABLE_NAME AND o.schema_id = SCHEMA_ID(t.TABLE_SCHEMA)
                LEFT JOIN sys.dm_db_partition_stats p ON p.object_id = o.object_id AND p.index_id < 2
                LEFT JOIN sys.allocation_units a ON p.partition_id = a.container_id
                LEFT JOIN sys.extended_properties ep ON ep.major_id = o.object_id AND ep.minor_id = 0 AND ep.name = 'MS_Description'
                LEFT JOIN sys.tables r ON r.object_id = o.object_id AND r.is_replicated = 1
                LEFT JOIN cdc.change_tables cdc ON cdc.source_object_id = o.object_id
                LEFT JOIN sys.tables tt ON tt.object_id = o.object_id
                WHERE t.TABLE_SCHEMA = :schema_name
                GROUP BY t.TABLE_SCHEMA, t.TABLE_NAME, t.TABLE_TYPE, o.create_date, o.modify_date, 
                         p.rows, ep.value, r.object_id, cdc.object_id, tt.temporal_type_desc
                ORDER BY t.TABLE_NAME
                """
                
                query_result = conn.execute(text(query), {'schema_name': schema})
                
                for row in query_result:
                    # Apply table filter if provided
                    if table_filter and not any(pattern.lower() in row.table_name.lower() for pattern in table_filter):
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