#!/usr/bin/env python3
"""
SQL Server Context Management System

This module implements SQL Server-specific context management for the RAG-based SQL agent.
It provides vector namespace management, database connection switching, schema isolation,
and T-SQL dialect handling for multiple SQL Server database scenarios.

Implements task 7.2: Build SQL Server-specific context management
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import threading
from contextlib import contextmanager

from vector_schema_store import VectorSchemaStore, SchemaVector
from sql_server_schema_introspector import SQLServerSchemaIntrospector, SQLServerSchemaIntrospectionResult
from vector_config import VectorConfig
from config import get_current_database, update_mssql_connection, VECTOR_STORE_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SQLServerDatabaseContext:
    """Context information for a specific SQL Server database"""
    database_name: str
    server_name: str
    connection_string: str
    vector_namespace: str
    schema_introspection_result: Optional[SQLServerSchemaIntrospectionResult] = None
    vector_store: Optional[VectorSchemaStore] = None
    last_updated: Optional[datetime] = None
    is_active: bool = False
    dialect_features: Dict[str, Any] = field(default_factory=dict)
    schema_isolation_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TSQLDialectFeatures:
    """T-SQL specific dialect features and syntax patterns"""
    supports_top_clause: bool = True
    supports_cte: bool = True
    supports_window_functions: bool = True
    supports_merge_statement: bool = True
    supports_try_catch: bool = True
    date_functions: List[str] = field(default_factory=lambda: [
        'GETDATE()', 'DATEADD', 'DATEDIFF', 'DATEPART', 'DATENAME', 'YEAR', 'MONTH', 'DAY'
    ])
    string_functions: List[str] = field(default_factory=lambda: [
        'CHARINDEX', 'SUBSTRING', 'LEFT', 'RIGHT', 'LEN', 'LTRIM', 'RTRIM', 'UPPER', 'LOWER'
    ])
    aggregate_functions: List[str] = field(default_factory=lambda: [
        'SUM', 'AVG', 'COUNT', 'MAX', 'MIN', 'STDEV', 'VAR', 'STRING_AGG'
    ])
    system_functions: List[str] = field(default_factory=lambda: [
        '@@SERVERNAME', '@@VERSION', 'DB_NAME()', 'USER_NAME()', 'SUSER_NAME()'
    ])
    schema_notation: str = "[schema].[table]"
    identity_syntax: str = "IDENTITY(1,1)"
    auto_increment_syntax: str = "IDENTITY"


class SQLServerContextManager:
    """
    SQL Server-specific context management system.
    
    This class manages multiple SQL Server database contexts, providing
    vector namespace isolation, connection switching, and T-SQL dialect handling.
    """
    
    def __init__(self, base_vector_path: str = None):
        """
        Initialize SQL Server context manager.
        
        Args:
            base_vector_path: Base path for vector storage (uses config default if None)
        """
        self.base_vector_path = base_vector_path or VECTOR_STORE_DIR
        self.contexts: Dict[str, SQLServerDatabaseContext] = {}
        self.active_context: Optional[str] = None
        self.introspector: Optional[SQLServerSchemaIntrospector] = None
        self.tsql_features = TSQLDialectFeatures()
        self._context_lock = threading.RLock()
        
        # Ensure base vector directory exists
        Path(self.base_vector_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize with current database context
        self._initialize_current_context()
        
        logger.info(f"SQLServerContextManager initialized with base path: {self.base_vector_path}")
    
    def _initialize_current_context(self):
        """Initialize context for the currently configured database"""
        try:
            current_db = get_current_database()
            if current_db:
                self.introspector = SQLServerSchemaIntrospector()
                self._create_database_context(current_db)
                self.switch_context(current_db)
                logger.info(f"Initialized context for current database: {current_db}")
        except Exception as e:
            logger.error(f"Failed to initialize current context: {e}")
    
    def _create_database_context(self, database_name: str) -> SQLServerDatabaseContext:
        """
        Create a new database context with isolated vector namespace.
        
        Args:
            database_name: Name of the database
            
        Returns:
            SQLServerDatabaseContext object
        """
        with self._context_lock:
            if database_name in self.contexts:
                return self.contexts[database_name]
            
            # Create vector namespace for this database
            vector_namespace = f"sqlserver_{database_name.lower()}"
            vector_path = os.path.join(self.base_vector_path, vector_namespace)
            
            # Get server name and connection string
            server_name = "localhost"  # Default, will be updated during introspection
            connection_string = ""
            
            if self.introspector:
                try:
                    stats = self.introspector.get_database_statistics()
                    if stats:
                        server_name = stats.get('server_name', 'localhost')
                        connection_string = self.introspector.connection_string
                except Exception as e:
                    logger.warning(f"Could not get server info for {database_name}: {e}")
            
            # Create vector store with database-specific configuration
            vector_config = VectorConfig.get_config('schema_store')
            vector_store = VectorSchemaStore(
                vector_db_path=vector_path,
                embedding_model=vector_config['embedding_model'],
                dimension=384  # Default for all-MiniLM-L6-v2
            )
            
            # Create context
            context = SQLServerDatabaseContext(
                database_name=database_name,
                server_name=server_name,
                connection_string=connection_string,
                vector_namespace=vector_namespace,
                vector_store=vector_store,
                last_updated=datetime.now(),
                is_active=False,
                dialect_features=self._get_tsql_dialect_features(),
                schema_isolation_config=self._get_schema_isolation_config(database_name)
            )
            
            self.contexts[database_name] = context
            logger.info(f"Created context for database: {database_name} with namespace: {vector_namespace}")
            
            return context
    
    def _get_tsql_dialect_features(self) -> Dict[str, Any]:
        """Get T-SQL dialect features configuration"""
        return {
            'supports_top_clause': self.tsql_features.supports_top_clause,
            'supports_cte': self.tsql_features.supports_cte,
            'supports_window_functions': self.tsql_features.supports_window_functions,
            'supports_merge_statement': self.tsql_features.supports_merge_statement,
            'supports_try_catch': self.tsql_features.supports_try_catch,
            'date_functions': self.tsql_features.date_functions,
            'string_functions': self.tsql_features.string_functions,
            'aggregate_functions': self.tsql_features.aggregate_functions,
            'system_functions': self.tsql_features.system_functions,
            'schema_notation': self.tsql_features.schema_notation,
            'identity_syntax': self.tsql_features.identity_syntax,
            'auto_increment_syntax': self.tsql_features.auto_increment_syntax
        }
    
    def _get_schema_isolation_config(self, database_name: str) -> Dict[str, Any]:
        """Get schema isolation configuration for a database"""
        return {
            'namespace_prefix': f"db_{database_name.lower()}",
            'vector_isolation': True,
            'schema_conflict_resolution': 'namespace_prefix',
            'cross_database_queries': False,
            'isolated_caching': True,
            'separate_learning_context': True
        }
    
    def switch_context(self, database_name: str) -> bool:
        """
        Switch to a different database context.
        
        Args:
            database_name: Name of the database to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        with self._context_lock:
            try:
                # Create context if it doesn't exist
                if database_name not in self.contexts:
                    self._create_database_context(database_name)
                
                # Update database connection
                update_mssql_connection(database_name)
                
                # Update introspector if needed
                if not self.introspector:
                    self.introspector = SQLServerSchemaIntrospector()
                else:
                    # Switch the introspector to the new database
                    switch_success = self.introspector.switch_database(database_name)
                    if not switch_success:
                        logger.error(f"Failed to switch introspector to database: {database_name}")
                        return False
                
                # Deactivate current context
                if self.active_context and self.active_context in self.contexts:
                    self.contexts[self.active_context].is_active = False
                
                # Activate new context
                context = self.contexts[database_name]
                context.is_active = True
                context.last_updated = datetime.now()
                self.active_context = database_name
                
                logger.info(f"Switched to database context: {database_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to switch context to {database_name}: {e}")
                return False
    
    def get_active_context(self) -> Optional[SQLServerDatabaseContext]:
        """
        Get the currently active database context.
        
        Returns:
            SQLServerDatabaseContext object or None if no active context
        """
        if self.active_context and self.active_context in self.contexts:
            return self.contexts[self.active_context]
        return None
    
    def get_context(self, database_name: str) -> Optional[SQLServerDatabaseContext]:
        """
        Get context for a specific database.
        
        Args:
            database_name: Name of the database
            
        Returns:
            SQLServerDatabaseContext object or None if not found
        """
        return self.contexts.get(database_name)
    
    def list_contexts(self) -> List[str]:
        """
        List all available database contexts.
        
        Returns:
            List of database names
        """
        return list(self.contexts.keys())
    
    def introspect_database_schema(self, database_name: str = None, force_refresh: bool = False) -> bool:
        """
        Perform schema introspection for a database and populate its vector store.
        
        Args:
            database_name: Database to introspect (uses active context if None)
            force_refresh: Force refresh even if schema was recently introspected
            
        Returns:
            True if introspection was successful, False otherwise
        """
        target_db = database_name or self.active_context
        if not target_db:
            logger.error("No database specified and no active context")
            return False
        
        with self._context_lock:
            try:
                # Ensure context exists
                if target_db not in self.contexts:
                    self._create_database_context(target_db)
                
                context = self.contexts[target_db]
                
                # Check if refresh is needed
                if not force_refresh and context.schema_introspection_result:
                    time_since_update = datetime.now() - context.last_updated
                    if time_since_update.total_seconds() < 3600:  # 1 hour cache
                        logger.info(f"Schema for {target_db} is recent, skipping introspection")
                        return True
                
                # Switch to target database if not already active
                if self.active_context != target_db:
                    if not self.switch_context(target_db):
                        return False
                
                # Perform introspection
                logger.info(f"Starting schema introspection for database: {target_db}")
                result = self.introspector.introspect_database_schema()
                
                if result.errors:
                    logger.warning(f"Introspection completed with {len(result.errors)} errors")
                    for error in result.errors[:3]:  # Log first 3 errors
                        logger.warning(f"  Error: {error}")
                
                # Store introspection result
                context.schema_introspection_result = result
                context.last_updated = datetime.now()
                
                # Populate vector store with schema information
                self._populate_vector_store(context, result)
                
                logger.info(f"Schema introspection completed for {target_db}: "
                          f"{result.total_tables} tables, {result.total_columns} columns, "
                          f"{result.total_relationships} relationships")
                
                return True
                
            except Exception as e:
                logger.error(f"Schema introspection failed for {target_db}: {e}")
                return False
    
    def _populate_vector_store(self, context: SQLServerDatabaseContext, 
                             result: SQLServerSchemaIntrospectionResult):
        """
        Populate vector store with schema introspection results.
        
        Args:
            context: Database context
            result: Schema introspection result
        """
        try:
            vector_store = context.vector_store
            if not vector_store:
                logger.error(f"No vector store available for context: {context.database_name}")
                return
            
            # Clear existing vectors for this database
            vector_store.clear_all_vectors()
            
            # Convert schema metadata to vector format
            schema_metadata = []
            
            # Process tables
            for table in result.tables:
                table_metadata = {
                    'schema': table.schema_name,
                    'table_name': table.table_name,
                    'table_type': table.table_type,
                    'description': table.description or f"Table {table.table_name} in schema {table.schema_name}",
                    'row_count': table.row_count,
                    'data_space_kb': table.data_space_kb,
                    'created_date': table.created_date.isoformat() if table.created_date else None,
                    'is_replicated': table.is_replicated,
                    'temporal_type': table.temporal_type,
                    'columns': []
                }
                
                # Add columns for this table
                table_key = f"{table.schema_name}.{table.table_name}"
                if table_key in result.columns:
                    for column in result.columns[table_key]:
                        column_metadata = {
                            'name': column.column_name,
                            'data_type': column.data_type,
                            'is_nullable': column.is_nullable,
                            'is_primary_key': column.is_primary_key,
                            'is_foreign_key': column.is_foreign_key,
                            'is_identity': column.is_identity,
                            'is_computed': column.is_computed,
                            'description': column.description or f"Column {column.column_name} of type {column.data_type}",
                            'max_length': column.max_length,
                            'precision': column.precision,
                            'scale': column.scale
                        }
                        table_metadata['columns'].append(column_metadata)
                
                schema_metadata.append(table_metadata)
            
            # Ingest schema into vector store
            vector_store.ingest_schema(schema_metadata)
            
            # Store relationships in vector store
            for relationship in result.relationships:
                relationship_metadata = {
                    'constraint_name': relationship.constraint_name,
                    'parent_table': f"{relationship.parent_schema}.{relationship.parent_table}",
                    'referenced_table': f"{relationship.referenced_schema}.{relationship.referenced_table}",
                    'parent_columns': relationship.parent_columns,
                    'referenced_columns': relationship.referenced_columns,
                    'relationship_type': relationship.relationship_type,
                    'delete_rule': relationship.delete_rule,
                    'update_rule': relationship.update_rule
                }
                
                # Store relationship as vector
                vector_store.store_schema_vector(
                    element_type="relationship",
                    schema_name=relationship.parent_schema,
                    element_name=relationship.constraint_name,
                    metadata=relationship_metadata,
                    semantic_tags=["relationship", "foreign_key"],
                    business_context={"database": context.database_name}
                )
            
            # Save vector store to disk
            vector_store.save_to_disk()
            
            logger.info(f"Populated vector store for {context.database_name} with "
                       f"{len(schema_metadata)} tables and {len(result.relationships)} relationships")
            
        except Exception as e:
            logger.error(f"Failed to populate vector store for {context.database_name}: {e}")
    
    def resolve_schema_conflicts(self, query_elements: List[str]) -> Dict[str, str]:
        """
        Resolve schema conflicts when elements exist in multiple databases.
        
        Args:
            query_elements: List of schema elements (tables, columns) to resolve
            
        Returns:
            Dictionary mapping elements to their resolved names with namespace prefixes
        """
        resolved_elements = {}
        active_context = self.get_active_context()
        
        if not active_context:
            logger.warning("No active context for schema conflict resolution")
            return resolved_elements
        
        isolation_config = active_context.schema_isolation_config
        namespace_prefix = isolation_config.get('namespace_prefix', '')
        
        for element in query_elements:
            if isolation_config.get('schema_conflict_resolution') == 'namespace_prefix':
                # Add namespace prefix to avoid conflicts
                resolved_name = f"{namespace_prefix}_{element}" if namespace_prefix else element
                resolved_elements[element] = resolved_name
            else:
                # Default: use element as-is
                resolved_elements[element] = element
        
        return resolved_elements
    
    def get_tsql_syntax_for_operation(self, operation: str) -> Optional[str]:
        """
        Get T-SQL specific syntax for a database operation.
        
        Args:
            operation: Type of operation (e.g., 'limit', 'date_current', 'string_length')
            
        Returns:
            T-SQL syntax string or None if not supported
        """
        tsql_syntax_map = {
            'limit': 'TOP {n}',
            'date_current': 'GETDATE()',
            'date_add': 'DATEADD({interval}, {number}, {date})',
            'date_diff': 'DATEDIFF({interval}, {start_date}, {end_date})',
            'string_length': 'LEN({string})',
            'string_substring': 'SUBSTRING({string}, {start}, {length})',
            'string_position': 'CHARINDEX({substring}, {string})',
            'string_upper': 'UPPER({string})',
            'string_lower': 'LOWER({string})',
            'string_trim': 'LTRIM(RTRIM({string}))',
            'concat': 'CONCAT({string1}, {string2})',
            'coalesce': 'ISNULL({value}, {default})',
            'case_when': 'CASE WHEN {condition} THEN {value1} ELSE {value2} END',
            'row_number': 'ROW_NUMBER() OVER (ORDER BY {column})',
            'rank': 'RANK() OVER (ORDER BY {column})',
            'dense_rank': 'DENSE_RANK() OVER (ORDER BY {column})',
            'lag': 'LAG({column}, {offset}) OVER (ORDER BY {order_column})',
            'lead': 'LEAD({column}, {offset}) OVER (ORDER BY {order_column})',
            'schema_table_notation': '[{schema}].[{table}]',
            'column_notation': '[{column}]',
            'identity_column': '{column} IDENTITY(1,1)',
            'auto_increment': 'IDENTITY(1,1)'
        }
        
        return tsql_syntax_map.get(operation)
    
    def validate_tsql_query(self, query: str) -> Tuple[bool, List[str]]:
        """
        Validate T-SQL query syntax and provide suggestions.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, list_of_suggestions)
        """
        suggestions = []
        is_valid = True
        
        query_upper = query.upper()
        
        # Check for common T-SQL patterns
        if 'LIMIT' in query_upper:
            suggestions.append("Use 'TOP n' instead of 'LIMIT n' in T-SQL")
            is_valid = False
        
        if 'NOW()' in query_upper:
            suggestions.append("Use 'GETDATE()' instead of 'NOW()' in T-SQL")
            is_valid = False
        
        if 'LENGTH(' in query_upper:
            suggestions.append("Use 'LEN()' instead of 'LENGTH()' in T-SQL")
            is_valid = False
        
        if 'SUBSTR(' in query_upper:
            suggestions.append("Use 'SUBSTRING()' instead of 'SUBSTR()' in T-SQL")
            is_valid = False
        
        if 'INSTR(' in query_upper:
            suggestions.append("Use 'CHARINDEX()' instead of 'INSTR()' in T-SQL")
            is_valid = False
        
        # Check for proper schema notation
        if '.' in query and not ('[' in query and ']' in query):
            suggestions.append("Consider using bracket notation [schema].[table] for T-SQL")
        
        return is_valid, suggestions
    
    @contextmanager
    def temporary_context(self, database_name: str):
        """
        Context manager for temporarily switching database context.
        
        Args:
            database_name: Database to switch to temporarily
            
        Yields:
            SQLServerDatabaseContext object
        """
        original_context = self.active_context
        
        try:
            if self.switch_context(database_name):
                yield self.get_active_context()
            else:
                raise RuntimeError(f"Failed to switch to temporary context: {database_name}")
        finally:
            if original_context and original_context != database_name:
                self.switch_context(original_context)
    
    def get_context_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about all database contexts.
        
        Returns:
            Dictionary with context statistics
        """
        stats = {
            'total_contexts': len(self.contexts),
            'active_context': self.active_context,
            'contexts': {}
        }
        
        for db_name, context in self.contexts.items():
            context_stats = {
                'database_name': context.database_name,
                'server_name': context.server_name,
                'vector_namespace': context.vector_namespace,
                'is_active': context.is_active,
                'last_updated': context.last_updated.isoformat() if context.last_updated else None,
                'has_schema_data': context.schema_introspection_result is not None,
                'vector_store_stats': None
            }
            
            # Get vector store statistics
            if context.vector_store:
                try:
                    vector_stats = context.vector_store.get_schema_statistics()
                    context_stats['vector_store_stats'] = vector_stats
                except Exception as e:
                    logger.warning(f"Could not get vector stats for {db_name}: {e}")
            
            # Get schema introspection statistics
            if context.schema_introspection_result:
                result = context.schema_introspection_result
                context_stats['schema_stats'] = {
                    'total_tables': result.total_tables,
                    'total_columns': result.total_columns,
                    'total_relationships': result.total_relationships,
                    'schemas': result.schemas,
                    'processing_time_seconds': result.processing_time_seconds,
                    'error_count': len(result.errors)
                }
            
            stats['contexts'][db_name] = context_stats
        
        return stats
    
    def cleanup_context(self, database_name: str) -> bool:
        """
        Clean up resources for a database context.
        
        Args:
            database_name: Database context to clean up
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        with self._context_lock:
            try:
                if database_name not in self.contexts:
                    logger.warning(f"Context {database_name} not found for cleanup")
                    return False
                
                context = self.contexts[database_name]
                
                # Save vector store before cleanup
                if context.vector_store:
                    try:
                        context.vector_store.save_to_disk()
                        logger.info(f"Saved vector store for {database_name}")
                    except Exception as e:
                        logger.warning(f"Failed to save vector store for {database_name}: {e}")
                
                # Remove from active context if it's the active one
                if self.active_context == database_name:
                    self.active_context = None
                
                # Remove context
                del self.contexts[database_name]
                
                logger.info(f"Cleaned up context for database: {database_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to cleanup context for {database_name}: {e}")
                return False
    
    def save_all_contexts(self):
        """Save all vector stores to disk"""
        with self._context_lock:
            for db_name, context in self.contexts.items():
                if context.vector_store:
                    try:
                        context.vector_store.save_to_disk()
                        logger.debug(f"Saved vector store for {db_name}")
                    except Exception as e:
                        logger.warning(f"Failed to save vector store for {db_name}: {e}")
            
            logger.info(f"Saved all {len(self.contexts)} context vector stores")


# Global context manager instance
_context_manager: Optional[SQLServerContextManager] = None


def get_context_manager() -> SQLServerContextManager:
    """Get the global SQL Server context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = SQLServerContextManager()
    return _context_manager


def initialize_context_manager(base_vector_path: str = None) -> SQLServerContextManager:
    """Initialize the global SQL Server context manager"""
    global _context_manager
    _context_manager = SQLServerContextManager(base_vector_path)
    return _context_manager