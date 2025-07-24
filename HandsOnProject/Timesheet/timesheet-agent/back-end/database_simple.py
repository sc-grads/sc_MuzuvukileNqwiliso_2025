#!/usr/bin/env python3
"""
Simplified database module to fix immediate issues
"""

from sqlalchemy import create_engine, inspect, text
from config import (
    CHROMADB_DIR, CHROMADB_COLLECTION, OLLAMA_BASE_URL, 
    LLM_MODEL, EXCLUDE_TABLE_PATTERNS, get_schema_cache_file, 
    get_column_map_file, get_enhanced_schema_cache_file, get_current_database
)
import os
import json
import re
from typing import Dict, List, Tuple, Optional
import urllib.parse

# Disable ChromaDB telemetry
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "false"

def convert_odbc_to_sqlalchemy_url(odbc_string):
    """Convert ODBC connection string to SQLAlchemy-compatible format using URL encoding."""
    encoded = urllib.parse.quote_plus(odbc_string)
    return f"mssql+pyodbc:///?odbc_connect={encoded}"

def get_engine():
    try:
        # Import connection string dynamically to get updated value
        from config import MSSQL_CONNECTION
        sqlalchemy_url = convert_odbc_to_sqlalchemy_url(MSSQL_CONNECTION)
        return create_engine(sqlalchemy_url, echo=False)
    except Exception as e:
        print(f"Failed to create database engine: {e}")
        raise

def should_exclude_table(table_name, exclude_patterns):
    return any(re.compile(pattern, re.IGNORECASE).search(table_name) for pattern in exclude_patterns)

def generate_simple_description(schema, table, columns):
    """Generate simple description without LLM"""
    col_names = [col['name'] for col in columns[:3]]
    return f"This table, named '{table}' within the '{schema}' schema, contains columns like {', '.join(col_names)}."

def generate_simple_column_description(column):
    """Generate simple column description without LLM"""
    return f"The '{column['name']}' column is of type {column['type']}."

def get_schema_metadata():
    # Use database-specific cache files
    cache_file = get_schema_cache_file()
    column_map_file = get_column_map_file()
    enhanced_cache_file = get_enhanced_schema_cache_file()
    
    current_db = get_current_database()
    print(f"📊 Using schema cache for database: {current_db}")
    
    # Import connection string dynamically to get updated value
    from config import MSSQL_CONNECTION
    cache_key = hash(MSSQL_CONNECTION)

    # Check if cache exists and is valid
    if os.path.exists(cache_file) and os.path.exists(column_map_file):
        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)
            if cached_data.get("cache_key") == cache_key:
                print("✅ Schema cache found and valid. Loading from cache...")
                with open(column_map_file, "r") as f:
                    column_map = json.load(f)
                
                # Create simple enhanced data
                enhanced_data = {
                    'business_patterns': [],
                    'table_priorities': [],
                    'inferred_relationships': []
                }
                
                return cached_data["metadata"], column_map, None, enhanced_data
            else:
                print("🔄 Schema cache found but invalid (connection string changed). Regenerating...")
        except Exception as e:
            print(f"⚠️ Failed to load cache: {e}. Regenerating schema...")

    print("🔄 Generating schema metadata from database...")

    engine = get_engine()
    schema_metadata = []
    column_map = {}

    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            excluded_schemas = ["INFORMATION_SCHEMA", "guest", "sys", "db_owner", "db_accessadmin", 
                                "db_securityadmin", "db_ddladmin", "db_backupoperator", 
                                "db_datareader", "db_datawriter", "db_denydatareader", "db_denydatawriter"]
            
            schemas = [s for s in inspector.get_schema_names() if s not in excluded_schemas]
            
            for schema in schemas:
                table_names = [t for t in inspector.get_table_names(schema=schema)
                               if not should_exclude_table(t, EXCLUDE_TABLE_PATTERNS)]
                
                for table_name in table_names:
                    print(f"  📋 Processing table: {schema}.{table_name}")
                    
                    columns = inspector.get_columns(table_name, schema=schema)
                    fks = inspector.get_foreign_keys(table_name, schema=schema)
                    pks = inspector.get_pk_constraint(table_name, schema=schema)

                    col_details = []
                    for col in columns:
                        col_info = {
                            "name": col['name'],
                            "type": str(col["type"]).lower(),
                            "nullable": col.get("nullable", True),
                            "default": str(col["default"]).strip("()") if col.get("default") else None,
                            "primary_key": col['name'] in pks.get('constrained_columns', []),
                            "description": generate_simple_column_description({
                                "name": col['name'], 
                                "type": str(col["type"]).lower()
                            }),
                            "business_patterns": []  # Empty for now
                        }
                        col_details.append(col_info)

                    # Store column mapping
                    column_map[f"{schema}.{table_name}"] = [col["name"] for col in columns]

                    # Process foreign keys
                    fk_info = []
                    for fk in fks:
                        fk_info.append({
                            "source_column": fk['constrained_columns'][0],
                            "target_table": f"{fk['referred_schema']}.{fk['referred_table']}",
                            "target_column": fk['referred_columns'][0]
                        })

                    # Generate simple description
                    description = generate_simple_description(schema, table_name, col_details)

                    table_metadata = {
                        "schema": schema,
                        "table": table_name,
                        "description": description,
                        "columns": col_details,
                        "relationships": fk_info,
                        "primary_keys": pks.get('constrained_columns', []),
                        "sample_query": f"SELECT TOP 5 * FROM [{schema}].[{table_name}]",
                        "inferred_relationships": [],  # Empty for now
                        "priority": {
                            "score": 0.5,
                            "business_importance": "medium",
                            "relevance_factors": []
                        }
                    }

                    schema_metadata.append(table_metadata)

        # Create enhanced data structure
        enhanced_data = {
            'business_patterns': [],
            'table_priorities': [
                {
                    'table_name': table['table'],
                    'schema_name': table['schema'],
                    'priority_score': 0.5,
                    'business_importance': 'medium',
                    'relevance_factors': []
                }
                for table in schema_metadata
            ],
            'inferred_relationships': []
        }

        # Save to cache
        cache_data = {
            "cache_key": cache_key,
            "metadata": schema_metadata
        }

        try:
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            with open(column_map_file, "w") as f:
                json.dump(column_map, f, indent=2)
            with open(enhanced_cache_file, "w") as f:
                json.dump(enhanced_data, f, indent=2)
            
            print(f"💾 Schema cache saved to: {cache_file}")
            print(f"💾 Column map saved to: {column_map_file}")
            print(f"💾 Enhanced cache saved to: {enhanced_cache_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to save cache: {e}")

        return schema_metadata, column_map, None, enhanced_data

    except Exception as e:
        print(f"❌ Error generating schema metadata: {e}")
        return [], {}, None, {'business_patterns': [], 'table_priorities': [], 'inferred_relationships': []}

def execute_query(query):
    """Execute SQL query and return results in expected format: (rows, columns, error)"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(query))
            
            # Handle different result types
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())
                
                # Convert to list of dictionaries for compatibility
                data = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    data.append(row_dict)
                
                # Return in expected format: (rows, columns, error)
                return data, columns, None
            else:
                # For non-SELECT queries
                return [], [], None
                
    except Exception as e:
        # Return error in expected format: (rows, columns, error)
        return [], [], str(e)

def refresh_schema_cache():
    """Refresh all database-specific schema cache files and regenerate enhanced metadata"""
    try:
        # Use database-specific cache files
        cache_files = [
            get_schema_cache_file(),
            get_column_map_file(),
            get_enhanced_schema_cache_file()
        ]
        
        current_db = get_current_database()
        print(f"🔄 Refreshing schema cache for database: {current_db}")
        
        for file in cache_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"   🗑️ Removed: {file}")
                
    except FileNotFoundError:
        pass
    
    return get_schema_metadata()