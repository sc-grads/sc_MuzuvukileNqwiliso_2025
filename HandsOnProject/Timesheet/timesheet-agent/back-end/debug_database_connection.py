#!/usr/bin/env python3
"""
Debug script to verify database connection switching
"""

import sys
import logging
from sqlalchemy import create_engine, text
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from sql_server_schema_introspector import SQLServerSchemaIntrospector
    from config import MSSQL_CONNECTION, update_mssql_connection
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)


def debug_database_connection():
    """Debug database connection and switching"""
    print("=" * 60)
    print("DATABASE CONNECTION DEBUG")
    print("=" * 60)
    
    try:
        # Test 1: Check initial connection
        print("🔍 Test 1: Initial Connection")
        introspector = SQLServerSchemaIntrospector()
        
        with introspector.engine.connect() as conn:
            result = conn.execute(text("SELECT DB_NAME() as current_db, @@SERVERNAME as server"))
            row = result.fetchone()
            print(f"  Current Database: {row.current_db}")
            print(f"  Server: {row.server}")
        
        # Test 2: Switch to BikeStores and verify
        print(f"\n🔄 Test 2: Switch to BikeStores")
        success = introspector.switch_database("BikeStores")
        print(f"  Switch Success: {success}")
        
        with introspector.engine.connect() as conn:
            result = conn.execute(text("SELECT DB_NAME() as current_db"))
            row = result.fetchone()
            print(f"  Current Database After Switch: {row.current_db}")
            
            # Check what schemas exist in this database
            result = conn.execute(text("""
                SELECT schema_name 
                FROM INFORMATION_SCHEMA.SCHEMATA 
                WHERE schema_name NOT IN ('INFORMATION_SCHEMA', 'sys', 'guest', 'db_owner', 'db_accessadmin',
                                         'db_securityadmin', 'db_ddladmin', 'db_backupoperator', 
                                         'db_datareader', 'db_datawriter', 'db_denydatareader', 'db_denydatawriter')
                ORDER BY schema_name
            """))
            schemas = [row.schema_name for row in result]
            print(f"  Schemas in current database: {schemas}")
            
            # Check what tables exist
            result = conn.execute(text("""
                SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA', 'sys')
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """))
            tables = [(row.TABLE_SCHEMA, row.TABLE_NAME, row.TABLE_TYPE) for row in result]
            print(f"  Tables in current database: {len(tables)} tables")
            
            if tables:
                print("  Sample tables:")
                for schema, table, table_type in tables[:5]:
                    print(f"    - {schema}.{table} ({table_type})")
                if len(tables) > 5:
                    print(f"    ... and {len(tables) - 5} more tables")
        
        # Test 3: Direct connection to BikeStores
        print(f"\n🔗 Test 3: Direct Connection to BikeStores")
        
        # Update connection string directly
        update_mssql_connection("BikeStores")
        from config import MSSQL_CONNECTION
        
        # Create new engine with BikeStores
        encoded_conn = urllib.parse.quote_plus(MSSQL_CONNECTION)
        sqlalchemy_url = f"mssql+pyodbc:///?odbc_connect={encoded_conn}"
        direct_engine = create_engine(sqlalchemy_url, echo=False)
        
        with direct_engine.connect() as conn:
            result = conn.execute(text("SELECT DB_NAME() as current_db"))
            row = result.fetchone()
            print(f"  Direct Connection Database: {row.current_db}")
            
            # Check schemas in BikeStores
            result = conn.execute(text("""
                SELECT schema_name 
                FROM INFORMATION_SCHEMA.SCHEMATA 
                WHERE schema_name NOT IN ('INFORMATION_SCHEMA', 'sys', 'guest', 'db_owner', 'db_accessadmin',
                                         'db_securityadmin', 'db_ddladmin', 'db_backupoperator', 
                                         'db_datareader', 'db_datawriter', 'db_denydatareader', 'db_denydatawriter')
                ORDER BY schema_name
            """))
            schemas = [row.schema_name for row in result]
            print(f"  BikeStores Schemas: {schemas}")
            
            # Check tables in BikeStores
            result = conn.execute(text("""
                SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA', 'sys')
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """))
            tables = [(row.TABLE_SCHEMA, row.TABLE_NAME, row.TABLE_TYPE) for row in result]
            print(f"  BikeStores Tables: {len(tables)} tables")
            
            if tables:
                print("  BikeStores sample tables:")
                for schema, table, table_type in tables[:10]:
                    print(f"    - {schema}.{table} ({table_type})")
                if len(tables) > 10:
                    print(f"    ... and {len(tables) - 10} more tables")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False


if __name__ == "__main__":
    success = debug_database_connection()
    sys.exit(0 if success else 1)