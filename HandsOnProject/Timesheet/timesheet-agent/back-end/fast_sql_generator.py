#!/usr/bin/env python3
"""
Fast, lightweight SQL generator to replace the complex LLM system
"""

import re
from typing import Dict, List, Optional

def extract_employee_name(query_lower: str) -> Optional[str]:
    """Extract employee name from query"""
    # Common employee names from your training data
    known_employees = [
        'karabo tsaoane', 'lucky manamela', 'muzuvukile nqwiliso', 
        'pascal govender', 'siyakhanya mjikeliso'
    ]
    
    for name in known_employees:
        if name in query_lower:
            return name.title()  # Return with proper capitalization
    
    # Try to extract names using patterns (First Last format)
    name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
    matches = re.findall(name_pattern, query_lower.title())
    if matches:
        return matches[0]
    
    return None

def generate_fast_sql(nl_query: str, schema_metadata: List[Dict]) -> str:
    """Generate SQL using the new hybrid intelligent system"""
    
    # Use the new hybrid system that can handle unlimited query variations
    try:
        from hybrid_sql_system import generate_hybrid_sql
        result = generate_hybrid_sql(nl_query, schema_metadata)
        if result:
            return result
    except Exception as e:
        print(f"Hybrid system failed: {e}")
    
    # Fallback to complete trainer for backward compatibility
    try:
        
        result = generate_complete_sql(nl_query, schema_metadata)
        if result and not result.startswith("Error") and result is not None:
            return result
    except Exception as e:
        print(f"Complete trainer failed: {e}")
    
    # Final fallback to original fast generation
    query_lower = nl_query.lower().strip()
    
    # Get the first few tables for simple queries
    if not schema_metadata:
        return "Error: No schema available"
    
    # Simple pattern matching for common queries
    
    # 1. Employee-Project queries (complex JOINs) - Check this FIRST before general queries
    if any(phrase in query_lower for phrase in ['projects has', 'worked on', 'projects for']) or \
       ('project' in query_lower and any(name in query_lower for name in ['has', 'worked', 'employee'])):
        
        # Extract employee name from query
        employee_name = extract_employee_name(query_lower)
        
        # This needs a JOIN between Employee, Timesheet, and Project tables
        employee_table = None
        timesheet_table = None
        project_table = None
        
        for table in schema_metadata:
            table_name_lower = table['table'].lower()
            if 'employee' in table_name_lower:
                employee_table = table
            elif 'timesheet' in table_name_lower:
                timesheet_table = table
            elif 'project' in table_name_lower:
                project_table = table
        
        if employee_table and timesheet_table and project_table:
            base_query = f"""SELECT DISTINCT p.[ProjectName] 
FROM [{employee_table['schema']}].[{employee_table['table']}] e
JOIN [{timesheet_table['schema']}].[{timesheet_table['table']}] t ON e.[EmployeeID] = t.[EmployeeID]
JOIN [{project_table['schema']}].[{project_table['table']}] p ON t.[ProjectID] = p.[ProjectID]"""
            
            # Add WHERE clause for specific employee if name found
            if employee_name:
                base_query += f"\nWHERE e.[EmployeeName] LIKE '%{employee_name}%'"
            
            return base_query
    
    # 2. List/Show queries
    elif any(word in query_lower for word in ['list', 'show', 'display', 'get', 'what', 'which']):
        
        # Check for specific table mentions with better matching
        table_keywords = {
            'project': ['project', 'projects'],
            'employee': ['employee', 'employees', 'staff', 'worker', 'workers'],
            'client': ['client', 'clients', 'customer', 'customers'],
            'leave': ['leave', 'vacation', 'holiday', 'time off'],
            'timesheet': ['timesheet', 'timesheets', 'time sheet', 'time sheets'],
            'activity': ['activity', 'activities', 'task', 'tasks']
        }
        
        # Find best matching table
        best_match = None
        for table in schema_metadata:
            table_name_lower = table['table'].lower()
            
            # Direct table name match
            if table_name_lower in query_lower:
                best_match = table
                break
            
            # Keyword-based matching
            for table_type, keywords in table_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    if table_type in table_name_lower or any(keyword in table_name_lower for keyword in keywords):
                        best_match = table
                        break
            
            if best_match:
                break
        
        if best_match:
            schema_name = best_match['schema']
            table_full = best_match['table']
            columns = [col['name'] for col in best_match['columns'][:3]]
            column_list = ', '.join([f"[{col}]" for col in columns])
            return f"SELECT TOP 10 {column_list} FROM [{schema_name}].[{table_full}]"
        
        # Default: use first table
        first_table = schema_metadata[0]
        schema_name = first_table['schema']
        table_name = first_table['table']
        columns = [col['name'] for col in first_table['columns'][:3]]
        column_list = ', '.join([f"[{col}]" for col in columns])
        
        return f"SELECT TOP 10 {column_list} FROM [{schema_name}].[{table_name}]"
    
    # 2. Count queries
    elif any(word in query_lower for word in ['count', 'how many', 'number of']):
        
        # Check for specific table mentions
        for table in schema_metadata:
            table_name = table['table'].lower()
            if table_name in query_lower:
                schema_name = table['schema']
                table_full = table['table']
                return f"SELECT COUNT(*) as RecordCount FROM [{schema_name}].[{table_full}]"
        
        # Default: use first table
        first_table = schema_metadata[0]
        return f"SELECT COUNT(*) as RecordCount FROM [{first_table['schema']}].[{first_table['table']}]"
    
    # 3. Employee queries
    elif 'employee' in query_lower:
        for table in schema_metadata:
            if 'employee' in table['table'].lower():
                schema_name = table['schema']
                table_name = table['table']
                columns = [col['name'] for col in table['columns'][:3]]
                column_list = ', '.join([f"[{col}]" for col in columns])
                return f"SELECT TOP 10 {column_list} FROM [{schema_name}].[{table_name}]"
    
    # 4. Leave queries
    elif any(word in query_lower for word in ['leave', 'vacation', 'time off']):
        for table in schema_metadata:
            if any(keyword in table['table'].lower() for keyword in ['leave', 'vacation']):
                schema_name = table['schema']
                table_name = table['table']
                columns = [col['name'] for col in table['columns'][:3]]
                column_list = ', '.join([f"[{col}]" for col in columns])
                return f"SELECT TOP 10 {column_list} FROM [{schema_name}].[{table_name}]"
        
        # If no leave table found, look for LeaveType specifically
        for table in schema_metadata:
            if 'leavetype' in table['table'].lower():
                schema_name = table['schema']
                table_name = table['table']
                columns = [col['name'] for col in table['columns'][:3]]
                column_list = ', '.join([f"[{col}]" for col in columns])
                return f"SELECT TOP 10 {column_list} FROM [{schema_name}].[{table_name}]"
    
    # 5. Timesheet queries
    elif 'timesheet' in query_lower:
        for table in schema_metadata:
            if 'timesheet' in table['table'].lower():
                schema_name = table['schema']
                table_name = table['table']
                columns = [col['name'] for col in table['columns'][:3]]
                column_list = ', '.join([f"[{col}]" for col in columns])
                return f"SELECT TOP 10 {column_list} FROM [{schema_name}].[{table_name}]"
    

    
    # Default fallback - use first table
    first_table = schema_metadata[0]
    schema_name = first_table['schema']
    table_name = first_table['table']
    columns = [col['name'] for col in first_table['columns'][:3]]
    column_list = ', '.join([f"[{col}]" for col in columns])
    
    return f"SELECT TOP 10 {column_list} FROM [{schema_name}].[{table_name}]"

def validate_fast_sql(sql_query: str, schema_metadata: List[Dict]) -> tuple[bool, str]:
    """Quick validation of generated SQL"""
    
    # Basic checks
    if not sql_query or not sql_query.strip():
        return False, "Empty query"
    
    if not sql_query.upper().startswith('SELECT'):
        return False, "Only SELECT queries allowed"
    
    # Check for system tables
    blocked_keywords = ['sys.', 'information_schema.', 'master.', 'msdb.']
    sql_lower = sql_query.lower()
    
    for blocked in blocked_keywords:
        if blocked in sql_lower:
            return False, f"System table access blocked: {blocked}"
    
    return True, "Valid"

# Test the fast generator
if __name__ == "__main__":
    # Mock schema for testing
    test_schema = [
        {
            'schema': 'Timesheet',
            'table': 'Employee',
            'columns': [
                {'name': 'EmployeeID', 'type': 'integer'},
                {'name': 'EmployeeName', 'type': 'varchar(100)'},
                {'name': 'Department', 'type': 'varchar(50)'}
            ]
        },
        {
            'schema': 'Timesheet',
            'table': 'Project',
            'columns': [
                {'name': 'ProjectID', 'type': 'integer'},
                {'name': 'ProjectName', 'type': 'varchar(100)'},
                {'name': 'ClientID', 'type': 'integer'}
            ]
        },
        {
            'schema': 'Timesheet',
            'table': 'Client',
            'columns': [
                {'name': 'ClientID', 'type': 'integer'},
                {'name': 'ClientName', 'type': 'varchar(100)'}
            ]
        },
        {
            'schema': 'Timesheet',
            'table': 'Timesheet',
            'columns': [
                {'name': 'TimesheetID', 'type': 'integer'},
                {'name': 'EmployeeID', 'type': 'integer'},
                {'name': 'ProjectID', 'type': 'integer'}
            ]
        },
        {
            'schema': 'Timesheet',
            'table': 'LeaveType',
            'columns': [
                {'name': 'LeaveTypeID', 'type': 'integer'},
                {'name': 'LeaveTypeName', 'type': 'varchar(50)'}
            ]
        }
    ]
    
    test_queries = [
        "Show all employees",
        "List leave types", 
        "What projects do we have?",
        "Count employees",
        "What projects has Siyakhanya Mjikeliso worked on?",
        "Show all clients",
        "Display timesheet data"
    ]
    
    print("=== Fast SQL Generator Test ===")
    for query in test_queries:
        sql = generate_fast_sql(query, test_schema)
        is_valid, validation_msg = validate_fast_sql(sql, test_schema)
        status = "[PASS]" if is_valid else "[FAIL]"
        print(f"{status} {query}")
        print(f"   SQL: {sql}")
        print(f"   Validation: {validation_msg}")
        print()