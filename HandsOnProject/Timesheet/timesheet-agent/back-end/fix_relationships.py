#!/usr/bin/env python3
"""
Script to fix the schema cache by properly detecting and adding table relationships.
This addresses the core issue where the agent can't understand table relationships.
"""

import json
import re
from typing import Dict, List, Tuple

def detect_foreign_key_relationships(schema_metadata: List[Dict]) -> List[Dict]:
    """
    Detect foreign key relationships based on column names and patterns.
    This fixes the missing relationships in the schema cache.
    """
    # Create a lookup for all tables and their primary keys
    table_lookup = {}
    for table in schema_metadata:
        table_key = f"{table['schema']}.{table['table']}"
        table_lookup[table_key] = {
            'primary_keys': table.get('primary_keys', []),
            'columns': {col['name']: col for col in table['columns']}
        }
    
    # Update each table with detected relationships
    for table in schema_metadata:
        relationships = []
        table_key = f"{table['schema']}.{table['table']}"
        
        # Special handling for Description table (polymorphic relationships)
        if table['table'] == 'Description':
            # Description table has polymorphic relationships via SourceID
            relationships.append({
                'source_column': 'SourceID',
                'target_table': 'POLYMORPHIC',
                'target_column': 'ID',
                'relationship_type': 'polymorphic',
                'confidence': 1.0,
                'description': 'SourceID references different tables based on DescriptionType: Activity->ActivityID, Leave->LeaveTypeID, etc.'
            })
            
            # Update SourceID column description
            for column in table['columns']:
                if column['name'] == 'SourceID':
                    column['description'] = "Polymorphic foreign key - references different tables based on DescriptionType (Activity->ActivityID, Leave->LeaveTypeID, etc.)"
                    break
        
        # Standard foreign key detection
        for column in table['columns']:
            col_name = column['name']
            
            # Skip if already marked as primary key
            if col_name in table.get('primary_keys', []):
                continue
            
            # Skip SourceID in Description table (handled above)
            if table['table'] == 'Description' and col_name == 'SourceID':
                continue
            
            # Look for foreign key patterns
            if col_name.endswith('ID') and col_name != f"{table['table']}ID":
                # Extract the referenced table name
                referenced_table_name = col_name[:-2]  # Remove 'ID' suffix
                
                # Look for matching table
                for target_table_key, target_info in table_lookup.items():
                    target_schema, target_table = target_table_key.split('.')
                    
                    # Check if this could be the referenced table
                    if (target_table.lower() == referenced_table_name.lower() or 
                        referenced_table_name.lower() in target_table.lower()):
                        
                        # Check if target table has matching primary key
                        expected_pk = f"{referenced_table_name}ID"
                        if expected_pk in target_info['primary_keys']:
                            relationships.append({
                                'source_column': col_name,
                                'target_table': target_table_key,
                                'target_column': expected_pk,
                                'relationship_type': 'foreign_key',
                                'confidence': 0.9
                            })
                            
                            # Update column description to indicate foreign key
                            column['description'] = f"A foreign key that links this record to the '{target_table}' table, identifying the associated {referenced_table_name.lower()}."
                            break
        
        # Update the table's relationships
        table['relationships'] = relationships
        
        # Also add inferred relationships for better context
        table['inferred_relationships'] = relationships.copy()
    
    return schema_metadata

def fix_schema_cache():
    """Fix the schema cache file with proper relationships"""
    
    # Load the current schema cache
    try:
        with open('back-end/cache/schema_cache_TimesheetDB.json', 'r') as f:
            cache_data = json.load(f)
    except FileNotFoundError:
        print("Schema cache file not found!")
        return False
    
    # Extract metadata
    schema_metadata = cache_data.get('metadata', [])
    
    if not schema_metadata:
        print("No metadata found in schema cache!")
        return False
    
    print(f"Processing {len(schema_metadata)} tables...")
    
    # Detect and add relationships
    updated_metadata = detect_foreign_key_relationships(schema_metadata)
    
    # Count relationships found
    total_relationships = sum(len(table.get('relationships', [])) for table in updated_metadata)
    print(f"Detected {total_relationships} relationships")
    
    # Update the cache data
    cache_data['metadata'] = updated_metadata
    
    # Save the updated cache
    with open('back-end/cache/schema_cache_TimesheetDB.json', 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    print("Schema cache updated successfully!")
    
    # Print detected relationships for verification
    print("\nDetected Relationships:")
    for table in updated_metadata:
        table_name = f"{table['schema']}.{table['table']}"
        for rel in table.get('relationships', []):
            print(f"  {table_name}.{rel['source_column']} → {rel['target_table']}.{rel['target_column']}")
    
    return True

if __name__ == "__main__":
    fix_schema_cache()