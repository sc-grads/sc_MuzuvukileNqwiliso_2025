#!/usr/bin/env python3
"""
Simple, dynamic relationship detector that doesn't hardcode anything.
This replaces the complex hardcoded approach with a flexible one.
"""

import json
from typing import Dict, List

def detect_relationships_dynamically(schema_metadata: List[Dict]) -> List[Dict]:
    """
    Dynamically detect relationships without hardcoding anything.
    Uses simple heuristics that work for most databases.
    """
    # Create lookup of all tables and their primary keys
    tables = {}
    for table in schema_metadata:
        table_key = f"{table['schema']}.{table['table']}"
        tables[table_key] = {
            'primary_keys': table.get('primary_keys', []),
            'table_name': table['table']
        }
    
    # For each table, find potential foreign keys
    for table in schema_metadata:
        relationships = []
        
        for column in table['columns']:
            col_name = column['name']
            
            # Skip primary keys
            if col_name in table.get('primary_keys', []):
                continue
            
            # Look for foreign key pattern: ends with 'ID' and not the table's own ID
            if col_name.endswith('ID') and col_name != f"{table['table']}ID":
                # Find matching table
                referenced_table_name = col_name[:-2]  # Remove 'ID'
                
                for table_key, table_info in tables.items():
                    if table_info['table_name'].lower() == referenced_table_name.lower():
                        # Check if target has matching primary key
                        expected_pk = f"{referenced_table_name}ID"
                        if expected_pk in table_info['primary_keys']:
                            relationships.append({
                                'source_column': col_name,
                                'target_table': table_key,
                                'target_column': expected_pk
                            })
                            break
        
        table['relationships'] = relationships
    
    return schema_metadata

def update_schema_cache_simple():
    """Update schema cache with simple relationship detection"""
    try:
        with open('cache/schema_cache_TimesheetDB.json', 'r') as f:
            cache_data = json.load(f)
    except FileNotFoundError:
        print("Schema cache not found!")
        return False
    
    schema_metadata = cache_data.get('metadata', [])
    if not schema_metadata:
        print("No metadata found!")
        return False
    
    # Detect relationships dynamically
    updated_metadata = detect_relationships_dynamically(schema_metadata)
    
    # Count relationships
    total_rels = sum(len(table.get('relationships', [])) for table in updated_metadata)
    print(f"Detected {total_rels} relationships dynamically")
    
    # Update cache
    cache_data['metadata'] = updated_metadata
    
    with open('cache/schema_cache_TimesheetDB.json', 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    print("Schema cache updated with simple relationships!")
    return True

if __name__ == "__main__":
    update_schema_cache_simple()