#!/usr/bin/env python3
"""
Demonstration of SQL Server Context Management System

This script demonstrates the SQL Server-specific context management capabilities
including vector namespace management, database switching, schema isolation,
and T-SQL dialect handling with real database introspection.

Demonstrates task 7.2: Build SQL Server-specific context management
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from sql_server_context_manager import SQLServerContextManager, get_context_manager
    from sql_server_schema_introspector import SQLServerSchemaIntrospector
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


def demonstrate_context_management():
    """Demonstrate SQL Server context management capabilities"""
    print("=" * 80)
    print("SQL SERVER CONTEXT MANAGEMENT DEMONSTRATION")
    print("=" * 80)
    
    try:
        # Initialize context manager
        context_manager = get_context_manager()
        
        print(f"\n🔧 Context Manager Initialized")
        print(f"   Base Vector Path: {context_manager.base_vector_path}")
        print(f"   Active Context: {context_manager.active_context}")
        
        # Demonstrate T-SQL dialect features
        print(f"\n📝 T-SQL Dialect Features:")
        tsql_operations = [
            'limit', 'date_current', 'string_length', 'string_substring',
            'row_number', 'schema_table_notation', 'case_when'
        ]
        
        for operation in tsql_operations:
            syntax = context_manager.get_tsql_syntax_for_operation(operation)
            print(f"   {operation:20} -> {syntax}")
        
        # Demonstrate query validation
        print(f"\n✅ T-SQL Query Validation:")
        test_queries = [
            "SELECT TOP 10 * FROM employees",
            "SELECT * FROM employees LIMIT 10",  # Invalid for T-SQL
            "SELECT GETDATE() as current_time",
            "SELECT NOW() as current_time",  # Invalid for T-SQL
        ]
        
        for query in test_queries:
            is_valid, suggestions = context_manager.validate_tsql_query(query)
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"   {status}: {query}")
            if suggestions:
                for suggestion in suggestions:
                    print(f"      💡 {suggestion}")
        
        # List available databases
        print(f"\n🗄️  Available Databases:")
        introspector = SQLServerSchemaIntrospector()
        databases = introspector.list_databases()
        
        available_dbs = []
        for db in databases:
            if db['state'] == 'ONLINE' and db['database_name'] not in ['master', 'model', 'msdb', 'tempdb']:
                available_dbs.append(db['database_name'])
                status_icon = "🟢"
                print(f"   {status_icon} {db['database_name']:<20} (State: {db['state']})")
        
        # Demonstrate context switching and schema introspection
        if len(available_dbs) >= 2:
            db1, db2 = available_dbs[0], available_dbs[1]
            
            print(f"\n🔄 Demonstrating Context Switching:")
            print(f"   Switching between {db1} and {db2}")
            
            # Switch to first database
            print(f"\n   📊 Introspecting {db1}:")
            success = context_manager.introspect_database_schema(db1, force_refresh=True)
            
            if success:
                context1 = context_manager.get_context(db1)
                if context1 and context1.schema_introspection_result:
                    result = context1.schema_introspection_result
                    print(f"      ✅ Tables: {result.total_tables}")
                    print(f"      ✅ Columns: {result.total_columns}")
                    print(f"      ✅ Relationships: {result.total_relationships}")
                    print(f"      ✅ Processing Time: {result.processing_time_seconds:.2f}s")
                    print(f"      ✅ Vector Namespace: {context1.vector_namespace}")
                    
                    # Show sample tables
                    if result.tables:
                        print(f"      📋 Sample Tables:")
                        for table in result.tables[:3]:
                            print(f"         - {table.schema_name}.{table.table_name} ({table.row_count:,} rows)")
            
            # Switch to second database
            print(f"\n   📊 Introspecting {db2}:")
            success = context_manager.introspect_database_schema(db2, force_refresh=True)
            
            if success:
                context2 = context_manager.get_context(db2)
                if context2 and context2.schema_introspection_result:
                    result = context2.schema_introspection_result
                    print(f"      ✅ Tables: {result.total_tables}")
                    print(f"      ✅ Columns: {result.total_columns}")
                    print(f"      ✅ Relationships: {result.total_relationships}")
                    print(f"      ✅ Processing Time: {result.processing_time_seconds:.2f}s")
                    print(f"      ✅ Vector Namespace: {context2.vector_namespace}")
                    
                    # Show sample tables
                    if result.tables:
                        print(f"      📋 Sample Tables:")
                        for table in result.tables[:3]:
                            print(f"         - {table.schema_name}.{table.table_name} ({table.row_count:,} rows)")
            
            # Demonstrate vector namespace isolation
            print(f"\n🔒 Vector Namespace Isolation:")
            context1 = context_manager.get_context(db1)
            context2 = context_manager.get_context(db2)
            
            if context1 and context2:
                stats1 = context1.vector_store.get_schema_statistics() if context1.vector_store else {}
                stats2 = context2.vector_store.get_schema_statistics() if context2.vector_store else {}
                
                print(f"   {db1}:")
                print(f"      Namespace: {context1.vector_namespace}")
                print(f"      Vectors: {stats1.get('total_vectors', 0)}")
                print(f"      Vector Path: {context1.vector_store.vector_db_path if context1.vector_store else 'N/A'}")
                
                print(f"   {db2}:")
                print(f"      Namespace: {context2.vector_namespace}")
                print(f"      Vectors: {stats2.get('total_vectors', 0)}")
                print(f"      Vector Path: {context2.vector_store.vector_db_path if context2.vector_store else 'N/A'}")
            
            # Demonstrate semantic search within contexts
            print(f"\n🔍 Semantic Search Demonstration:")
            
            # Search in first database context
            context_manager.switch_context(db1)
            context = context_manager.get_active_context()
            
            if context and context.vector_store:
                query_vector = context.vector_store.embedder.encode("employee information table")
                similar_tables = context.vector_store.find_similar_tables(query_vector, k=3)
                
                print(f"   Search in {db1} for 'employee information':")
                for i, table in enumerate(similar_tables, 1):
                    print(f"      {i}. {table.table_name} (similarity: {table.similarity_score:.3f})")
            
            # Search in second database context
            context_manager.switch_context(db2)
            context = context_manager.get_active_context()
            
            if context and context.vector_store:
                query_vector = context.vector_store.embedder.encode("customer sales data")
                similar_tables = context.vector_store.find_similar_tables(query_vector, k=3)
                
                print(f"   Search in {db2} for 'customer sales data':")
                for i, table in enumerate(similar_tables, 1):
                    print(f"      {i}. {table.table_name} (similarity: {table.similarity_score:.3f})")
            
            # Demonstrate temporary context switching
            print(f"\n⏱️  Temporary Context Switching:")
            original_context = context_manager.active_context
            print(f"   Original context: {original_context}")
            
            temp_db = db1 if original_context != db1 else db2
            print(f"   Temporarily switching to: {temp_db}")
            
            with context_manager.temporary_context(temp_db) as temp_context:
                print(f"   Inside temporary context: {temp_context.database_name}")
                print(f"   Vector namespace: {temp_context.vector_namespace}")
            
            print(f"   Back to original context: {context_manager.active_context}")
        
        # Show context statistics
        print(f"\n📈 Context Statistics:")
        stats = context_manager.get_context_statistics()
        
        print(f"   Total Contexts: {stats['total_contexts']}")
        print(f"   Active Context: {stats['active_context']}")
        
        for db_name, context_stats in stats['contexts'].items():
            print(f"\n   📊 {db_name}:")
            print(f"      Server: {context_stats['server_name']}")
            print(f"      Namespace: {context_stats['vector_namespace']}")
            print(f"      Active: {context_stats['is_active']}")
            print(f"      Last Updated: {context_stats['last_updated']}")
            print(f"      Has Schema Data: {context_stats['has_schema_data']}")
            
            if context_stats['vector_store_stats']:
                vs_stats = context_stats['vector_store_stats']
                print(f"      Vector Store:")
                print(f"         Total Vectors: {vs_stats.get('total_vectors', 0)}")
                print(f"         FAISS Index Size: {vs_stats.get('faiss_index_size', 0)}")
                
                by_type = vs_stats.get('by_type', {})
                if by_type:
                    print(f"         By Type: {dict(by_type)}")
            
            if context_stats.get('schema_stats'):
                schema_stats = context_stats['schema_stats']
                print(f"      Schema Stats:")
                print(f"         Tables: {schema_stats.get('total_tables', 0)}")
                print(f"         Columns: {schema_stats.get('total_columns', 0)}")
                print(f"         Relationships: {schema_stats.get('total_relationships', 0)}")
                print(f"         Schemas: {', '.join(schema_stats.get('schemas', []))}")
        
        # Demonstrate schema conflict resolution
        print(f"\n🔧 Schema Conflict Resolution:")
        test_elements = ["employees", "projects", "customers", "orders"]
        resolved = context_manager.resolve_schema_conflicts(test_elements)
        
        print(f"   Original elements: {test_elements}")
        print(f"   Resolved elements:")
        for original, resolved_name in resolved.items():
            print(f"      {original} -> {resolved_name}")
        
        print(f"\n✅ SQL Server Context Management Demonstration Complete!")
        return True
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        return False


def main():
    """Main demonstration function"""
    print("SQL Server Context Management System Demonstration")
    print("This demo shows real-world usage of the context management system")
    
    success = demonstrate_context_management()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("✅ SQL Server Context Management System is fully operational")
        print("\nKey Features Demonstrated:")
        print("  • Vector namespace isolation for multiple databases")
        print("  • Database context switching with schema introspection")
        print("  • T-SQL dialect handling and query validation")
        print("  • Semantic search within isolated contexts")
        print("  • Temporary context switching")
        print("  • Schema conflict resolution")
        print("  • Comprehensive context statistics")
    else:
        print("❌ DEMONSTRATION FAILED!")
        print("⚠️  Check the error messages above for details")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)