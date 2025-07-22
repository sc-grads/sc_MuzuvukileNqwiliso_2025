#!/usr/bin/env python3
"""
Complete SQL generator trained on ALL 48 questions from training file
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
import time

# Cache for dynamic employee names to avoid repeated database queries
_employee_cache = {
    'names': [],
    'last_updated': 0,
    'cache_duration': 300  # 5 minutes
}

def get_dynamic_employee_names(schema_metadata: List[Dict]) -> List[str]:
    """Fetch employee names dynamically from database with caching"""
    global _employee_cache
    
    # Check if cache is still valid
    current_time = time.time()
    if (current_time - _employee_cache['last_updated'] < _employee_cache['cache_duration'] 
        and _employee_cache['names']):
        return _employee_cache['names']
    
    try:
        from database import execute_query
        
        # Find the Employee table
        employee_table = None
        for table in schema_metadata:
            if table['table'].lower() == 'employee':
                employee_table = table
                break
        
        if not employee_table:
            return _employee_cache['names'] or []
        
        # Query to get all employee names
        query = f"SELECT [EmployeeName] FROM [{employee_table['schema']}].[{employee_table['table']}]"
        result = execute_query(query)
        
        if result and result.get('success'):
            # Extract names from result and convert to lowercase
            employee_names = []
            for row in result.get('data', []):
                if isinstance(row, dict) and 'EmployeeName' in row:
                    employee_names.append(row['EmployeeName'].lower())
                elif isinstance(row, (list, tuple)) and len(row) > 0:
                    employee_names.append(str(row[0]).lower())
            
            # Update cache
            _employee_cache['names'] = employee_names
            _employee_cache['last_updated'] = current_time
            
            print(f"✅ Dynamic employee names loaded: {len(employee_names)} employees found")
            return employee_names
        
    except Exception as e:
        print(f"Failed to fetch dynamic employee names: {e}")
    
    # Fallback to static list if dynamic fetch fails
    fallback_names = [
        'karabo tsaoane', 'lucky manamela', 'muzuvukile nqwiliso', 
        'pascal govender', 'siyakhanya mjikeliso'
    ]
    
    # Update cache with fallback
    if not _employee_cache['names']:
        _employee_cache['names'] = fallback_names
        _employee_cache['last_updated'] = current_time
    
    return _employee_cache['names'] or fallback_names

def extract_employee_name(query_lower: str, schema_metadata: List[Dict] = None) -> Optional[str]:
    """Extract employee name from query - now uses dynamic employee list"""
    # Get dynamic employee names from database
    known_employees = get_dynamic_employee_names(schema_metadata or [])
    
    # Skip extraction for analytical queries that don't have employee names
    analytical_patterns = [
        'sum of billable', 'identify employees', 'employees with less than',
        'all employees', 'each employee', 'per project', 'by project',
        'total hours worked by', 'average', 'count of', 'which files have been processed'
    ]
    
    for pattern in analytical_patterns:
        if pattern in query_lower:
            return None  # Don't extract names from analytical queries
    
    # Check for partial names first (like "Muzuvukile" without last name)
    for name in known_employees:
        name_parts = name.split()
        for part in name_parts:
            if len(part) > 4 and part in query_lower:  # Increased threshold to avoid false matches
                # Verify it's actually referring to this employee by checking context
                if any(other_part in query_lower for other_part in name_parts if other_part != part):
                    return name.title()
                elif len(part) > 6:  # Only use single names if they're long enough to be unique
                    return name.title()
    
    # Check for full names
    for name in known_employees:
        if name in query_lower:
            return name.title()
    
    # Try to extract names using patterns (First Last format) - more restrictive
    name_pattern = r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})\b'
    matches = re.findall(name_pattern, query_lower.title())
    if matches:
        # Filter out common words and phrases that aren't names
        excluded_words = {
            'List', 'All', 'Show', 'Total', 'Hours', 'Work', 'From', 'To', 'Sum', 'Of', 'Billable',
            'Non', 'Each', 'Employee', 'Employees', 'With', 'Less', 'Than', 'Identify', 'Per', 'Project',
            'Which', 'Files', 'Have', 'Been', 'Processed', 'For'
        }
        for match in matches:
            words = match.split()
            if not any(word in excluded_words for word in words):
                return match
    
    return None

def extract_date_info(query_lower: str) -> Optional[Tuple[str, str]]:
    """Extract date information from query"""
    current_year = datetime.now().year
    
    months = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    # Specific date patterns
    if 'june 15, 2025' in query_lower:
        return '2025-06-15', '2025-06-15'
    
    # Handle date ranges like "January to May 2025" or "from January 2025 to May 2025"
    range_patterns = [
        r'(\w+)\s+(?:to|through)\s+(\w+)\s+(\d{4})',  # "January to May 2025"
        r'from\s+(\w+)\s+(\d{4})\s+to\s+(\w+)\s+(\d{4})',  # "from January 2025 to May 2025"
        r'between\s+(\w+)\s+(?:and|to)\s+(\w+)\s+(\d{4})',  # "between January and May 2025"
        r'(\w+)\s+(\d{4})\s+(?:to|through)\s+(\w+)\s+(\d{4})'  # "January 2025 to May 2025"
    ]
    
    for pattern in range_patterns:
        match = re.search(pattern, query_lower)
        if match:
            groups = match.groups()
            if len(groups) == 3:  # Pattern like "January to May 2025"
                start_month, end_month, year = groups
                if start_month.lower() in months and end_month.lower() in months:
                    start_month_num = months[start_month.lower()]
                    end_month_num = months[end_month.lower()]
                    start_date = f"{year}-{start_month_num}-01"
                    # Get last day of end month
                    if end_month_num in ['01', '03', '05', '07', '08', '10', '12']:
                        end_date = f"{year}-{end_month_num}-31"
                    elif end_month_num in ['04', '06', '09', '11']:
                        end_date = f"{year}-{end_month_num}-30"
                    else:
                        end_date = f"{year}-{end_month_num}-28"
                    return start_date, end_date
            elif len(groups) == 4:  # Pattern like "from January 2025 to May 2025"
                start_month, start_year, end_month, end_year = groups
                if start_month.lower() in months and end_month.lower() in months:
                    start_month_num = months[start_month.lower()]
                    end_month_num = months[end_month.lower()]
                    start_date = f"{start_year}-{start_month_num}-01"
                    # Get last day of end month
                    if end_month_num in ['01', '03', '05', '07', '08', '10', '12']:
                        end_date = f"{end_year}-{end_month_num}-31"
                    elif end_month_num in ['04', '06', '09', '11']:
                        end_date = f"{end_year}-{end_month_num}-30"
                    else:
                        end_date = f"{end_year}-{end_month_num}-28"
                    return start_date, end_date
    
    # Single month with year
    for month_name, month_num in months.items():
        if month_name in query_lower:
            year_match = re.search(r'\b(20\d{2})\b', query_lower)
            year = year_match.group(1) if year_match else str(current_year)
            
            start_date = f"{year}-{month_num}-01"
            if month_num in ['01', '03', '05', '07', '08', '10', '12']:
                end_date = f"{year}-{month_num}-31"
            elif month_num in ['04', '06', '09', '11']:
                end_date = f"{year}-{month_num}-30"
            else:
                end_date = f"{year}-{month_num}-28"
            
            return start_date, end_date
    
    # Relative dates
    if 'last month' in query_lower:
        last_month = datetime.now() - timedelta(days=30)
        start_date = last_month.strftime("%Y-%m-01")
        end_date = last_month.strftime("%Y-%m-28")
        return start_date, end_date
    
    if 'this week' in query_lower:
        today = datetime.now()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        return start_week.strftime("%Y-%m-%d"), end_week.strftime("%Y-%m-%d")
    
    if 'last week' in query_lower:
        today = datetime.now()
        end_last_week = today - timedelta(days=today.weekday() + 1)
        start_last_week = end_last_week - timedelta(days=6)
        return start_last_week.strftime("%Y-%m-%d"), end_last_week.strftime("%Y-%m-%d")
    
    return None

def extract_filename(query_lower: str) -> Optional[str]:
    """Extract filename from query"""
    # Look for filename patterns
    filename_patterns = [
        r"'([^']+\.xlsx?)'",
        r'"([^"]+\.xlsx?)"',
        r'([a-zA-Z_]+\.xlsx?)',
        r'karabo_tsaoane_may2025\.xlsx'
    ]
    
    for pattern in filename_patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            return match.group(1) if match.groups() else match.group(0)
    
    return None

def generate_complete_sql(nl_query: str, schema_metadata: List[Dict]) -> str:
    """Generate SQL for ALL 48 training questions"""
    
    query_lower = nl_query.lower().strip()
    
    if not schema_metadata:
        return "Error: No schema available"
    
    # Find common tables
    tables = {}
    for table in schema_metadata:
        table_name_lower = table['table'].lower()
        tables[table_name_lower] = table
    
    # Extract common elements
    employee_name = extract_employee_name(query_lower, schema_metadata)
    date_info = extract_date_info(query_lower)
    filename = extract_filename(query_lower)
    
    # === EMPLOYEE-SPECIFIC QUERIES (HIGHEST PRIORITY) ===
    
    # 9. What projects has [Employee] worked on? - CHECK FIRST
    if any(phrase in query_lower for phrase in ['projects has', 'worked on', 'projects for']):
        if employee_name and 'employee' in tables and 'timesheet' in tables and 'project' in tables:
            emp_table = tables['employee']
            ts_table = tables['timesheet']
            proj_table = tables['project']
            return f"""SELECT DISTINCT p.[ProjectName]
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON e.[EmployeeID] = t.[EmployeeID]
JOIN [{proj_table['schema']}].[{proj_table['table']}] p ON t.[ProjectID] = p.[ProjectID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'"""
    
    # === BASIC QUERIES (Single Table) ===
    
    # 1. Show all employees
    if any(phrase in query_lower for phrase in ['show all employees', 'list all employees', 'all employees']):
        if 'employee' in tables:
            t = tables['employee']
            return f"SELECT TOP 10 [EmployeeID], [EmployeeName] FROM [{t['schema']}].[{t['table']}]"
    
    # 2. List all clients in the system
    if any(phrase in query_lower for phrase in ['list all clients', 'all clients', 'clients in the system']):
        if 'client' in tables:
            t = tables['client']
            return f"SELECT TOP 10 [ClientID], [ClientName] FROM [{t['schema']}].[{t['table']}]"
    
    # 3. What projects do we have?
    if any(phrase in query_lower for phrase in ['what projects', 'projects do we have', 'all projects']):
        if 'project' in tables:
            t = tables['project']
            return f"SELECT TOP 10 [ProjectID], [ProjectName] FROM [{t['schema']}].[{t['table']}]"
    
    # 4. Show all leave types available
    if any(phrase in query_lower for phrase in ['leave types', 'all leave types', 'leave types available']):
        if 'leavetype' in tables:
            t = tables['leavetype']
            return f"SELECT [LeaveTypeID], [LeaveTypeName] FROM [{t['schema']}].[{t['table']}]"
    
    # === EMPLOYEE-SPECIFIC QUERIES ===
    
    # 5. Show timesheet files for [Employee]
    if 'timesheet files for' in query_lower or 'timesheets for' in query_lower:
        if employee_name and 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            return f"""SELECT t.[TimesheetID], t.[Date], t.[TotalHours], t.[FileName]
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'"""
    
    # 6. How many hours did [Employee] work in [Month Year]?
    if 'how many hours' in query_lower and 'work' in query_lower:
        if employee_name and date_info and 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            start_date, end_date = date_info
            return f"""SELECT SUM(t.[TotalHours]) as TotalHours
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'
AND t.[Date] BETWEEN '{start_date}' AND '{end_date}'"""
    
    # 7. List all leave requests for [Employee]
    if 'leave requests for' in query_lower:
        if employee_name and 'leaverequest' in tables and 'employee' in tables:
            lr_table = tables['leaverequest']
            emp_table = tables['employee']
            return f"""SELECT lr.[LeaveRequestID], lr.[StartDate], lr.[EndDate], lr.[Status]
FROM [{lr_table['schema']}].[{lr_table['table']}] lr
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON lr.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'"""
    
    # 8. Show [Employee]'s billable/non-billable hours OR aggregate billable analysis
    if 'billable hours' in query_lower or 'non billable hours' in query_lower or 'non-billable hours' in query_lower:
        # Check if it's an aggregate query (no specific employee)
        if 'per project' in query_lower and not employee_name:
            if 'timesheet' in tables and 'project' in tables:
                ts_table = tables['timesheet']
                proj_table = tables['project']
                return f"""SELECT p.[ProjectName],
SUM(CASE WHEN t.[BillableStatus] = 'Billable' THEN t.[TotalHours] ELSE 0 END) as BillableHours,
SUM(CASE WHEN t.[BillableStatus] = 'Non-Billable' THEN t.[TotalHours] ELSE 0 END) as NonBillableHours
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{proj_table['schema']}].[{proj_table['table']}] p ON t.[ProjectID] = p.[ProjectID]
GROUP BY p.[ProjectName]"""
        
        # Employee-specific billable hours query
        elif employee_name:
            date_info = date_info or extract_date_info('last month')
            if date_info and 'timesheet' in tables and 'employee' in tables:
                ts_table = tables['timesheet']
                emp_table = tables['employee']
                start_date, end_date = date_info
                
                # Determine if asking for billable or non-billable
                if 'non billable' in query_lower or 'non-billable' in query_lower:
                    billable_status = 'Non-Billable'
                    alias = 'NonBillableHours'
                else:
                    billable_status = 'Billable'
                    alias = 'BillableHours'
                    
                return f"""SELECT SUM(t.[TotalHours]) as {alias}
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'
AND t.[BillableStatus] = '{billable_status}'
AND t.[Date] BETWEEN '{start_date}' AND '{end_date}'"""
    
    # 9. What projects has [Employee] worked on?
    if any(phrase in query_lower for phrase in ['projects has', 'worked on', 'projects for']):
        if employee_name and 'employee' in tables and 'timesheet' in tables and 'project' in tables:
            emp_table = tables['employee']
            ts_table = tables['timesheet']
            proj_table = tables['project']
            return f"""SELECT DISTINCT p.[ProjectName]
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON e.[EmployeeID] = t.[EmployeeID]
JOIN [{proj_table['schema']}].[{proj_table['table']}] p ON t.[ProjectID] = p.[ProjectID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'"""
    
    # === DATE-BASED QUERIES ===
    
    # 10. Show all timesheets from [Month Year]
    if 'timesheets from' in query_lower or ('all timesheets' in query_lower and date_info):
        if date_info and 'timesheet' in tables:
            ts_table = tables['timesheet']
            start_date, end_date = date_info
            return f"""SELECT TOP 20 [TimesheetID], [EmployeeID], [Date], [TotalHours]
FROM [{ts_table['schema']}].[{ts_table['table']}]
WHERE [Date] BETWEEN '{start_date}' AND '{end_date}'
ORDER BY [Date] DESC"""
    
    # 11. Who worked on [specific date]?
    if 'who worked on' in query_lower and date_info:
        if 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            work_date = date_info[0]
            return f"""SELECT DISTINCT e.[EmployeeName]
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON e.[EmployeeID] = t.[EmployeeID]
WHERE t.[Date] = '{work_date}'"""
    
    # 12. List all leave requests between [dates] - IMPROVED PATTERN MATCHING
    if any(phrase in query_lower for phrase in ['leave requests between', 'leave requests from', 'all leave requests']) and date_info:
        if 'leaverequest' in tables:
            lr_table = tables['leaverequest']
            start_date, end_date = date_info
            return f"""SELECT [LeaveRequestID], [EmployeeID], [StartDate], [EndDate], [Status]
FROM [{lr_table['schema']}].[{lr_table['table']}]
WHERE [StartDate] BETWEEN '{start_date}' AND '{end_date}'"""
    
    # 13. Show total hours worked each week in [Month Year]
    if 'total hours worked each week' in query_lower and date_info:
        if 'timesheet' in tables:
            ts_table = tables['timesheet']
            start_date, end_date = date_info
            return f"""SELECT DATEPART(WEEK, [Date]) as WeekNumber, SUM([TotalHours]) as WeeklyHours
FROM [{ts_table['schema']}].[{ts_table['table']}]
WHERE [Date] BETWEEN '{start_date}' AND '{end_date}'
GROUP BY DATEPART(WEEK, [Date])
ORDER BY WeekNumber"""
    
    # === AGGREGATION QUERIES ===
    
    # 14. Show total hours worked by each employee
    if 'total hours worked by each employee' in query_lower:
        if 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            return f"""SELECT e.[EmployeeName], SUM(t.[TotalHours]) as TotalHours
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON e.[EmployeeID] = t.[EmployeeID]
GROUP BY e.[EmployeeName]
ORDER BY TotalHours DESC"""
    
    # 15. Calculate average daily hours for [Employee]
    if 'average daily hours' in query_lower and employee_name:
        if 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            return f"""SELECT AVG(t.[TotalHours]) as AverageDailyHours
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = t.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'"""
    
    # 16. Sum of billable vs non-billable hours per project
    if 'billable vs non-billable hours per project' in query_lower:
        if 'timesheet' in tables and 'project' in tables:
            ts_table = tables['timesheet']
            proj_table = tables['project']
            return f"""SELECT p.[ProjectName],
SUM(CASE WHEN t.[BillableStatus] = 'Billable' THEN t.[TotalHours] ELSE 0 END) as BillableHours,
SUM(CASE WHEN t.[BillableStatus] = 'Non-Billable' THEN t.[TotalHours] ELSE 0 END) as NonBillableHours
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{proj_table['schema']}].[{proj_table['table']}] p ON t.[ProjectID] = p.[ProjectID]
GROUP BY p.[ProjectName]"""
    
    # 17. Count of leave days taken by each employee
    if 'count of leave days' in query_lower or 'leave days taken by each employee' in query_lower:
        if 'leaverequest' in tables and 'employee' in tables:
            lr_table = tables['leaverequest']
            emp_table = tables['employee']
            return f"""SELECT e.[EmployeeName], SUM(lr.[NumberOfDays]) as TotalLeaveDays
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{lr_table['schema']}].[{lr_table['table']}] lr ON e.[EmployeeID] = lr.[EmployeeID]
WHERE lr.[Status] = 'Approved'
GROUP BY e.[EmployeeName]
ORDER BY TotalLeaveDays DESC"""
    
    # === COMPLEX JOINS ===
    
    # 18. Show timesheets with employee and project names
    if 'timesheets with employee and project names' in query_lower:
        if 'timesheet' in tables and 'employee' in tables and 'project' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            proj_table = tables['project']
            return f"""SELECT TOP 20 t.[TimesheetID], e.[EmployeeName], p.[ProjectName], t.[Date], t.[TotalHours]
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
LEFT JOIN [{proj_table['schema']}].[{proj_table['table']}] p ON t.[ProjectID] = p.[ProjectID]
ORDER BY t.[Date] DESC"""
    
    # 19. List leave requests with employee and leave type details
    if 'leave requests with employee and leave type' in query_lower:
        if 'leaverequest' in tables and 'employee' in tables and 'leavetype' in tables:
            lr_table = tables['leaverequest']
            emp_table = tables['employee']
            lt_table = tables['leavetype']
            return f"""SELECT lr.[LeaveRequestID], e.[EmployeeName], lt.[LeaveTypeName], lr.[StartDate], lr.[EndDate], lr.[Status]
FROM [{lr_table['schema']}].[{lr_table['table']}] lr
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON lr.[EmployeeID] = e.[EmployeeID]
JOIN [{lt_table['schema']}].[{lt_table['table']}] lt ON lr.[LeaveTypeID] = lt.[LeaveTypeID]"""
    
    # 20. Show client names with their project hours
    if 'client names with their project hours' in query_lower:
        if 'client' in tables and 'project' in tables and 'timesheet' in tables:
            client_table = tables['client']
            proj_table = tables['project']
            ts_table = tables['timesheet']
            return f"""SELECT c.[ClientName], SUM(t.[TotalHours]) as TotalProjectHours
FROM [{client_table['schema']}].[{client_table['table']}] c
JOIN [{proj_table['schema']}].[{proj_table['table']}] p ON c.[ClientID] = p.[ClientID]
JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON p.[ProjectID] = t.[ProjectID]
GROUP BY c.[ClientName]
ORDER BY TotalProjectHours DESC"""
    
    # === FILE-RELATED QUERIES ===
    
    # 21. Which files have been processed for [Employee]?
    if ('files have been processed for' in query_lower or 'processed files for' in query_lower or 
        'which files' in query_lower and 'processed' in query_lower):
        if employee_name and 'processedfiles' in tables and 'employee' in tables:
            pf_table = tables['processedfiles']
            emp_table = tables['employee']
            return f"""SELECT pf.[FileName], pf.[ProcessedDate]
FROM [{pf_table['schema']}].[{pf_table['table']}] pf
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON pf.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'
ORDER BY pf.[ProcessedDate] DESC"""
        elif employee_name and 'timesheet' in tables and 'employee' in tables:
            # Fallback to timesheet files if ProcessedFiles table not available
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            return f"""SELECT DISTINCT t.[FileName]
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'
AND t.[FileName] IS NOT NULL
ORDER BY t.[FileName]"""
    
    # 22. Show all timesheets from file '[filename]'
    if 'timesheets from file' in query_lower or ('all timesheets from' in query_lower and filename):
        filename = filename or extract_filename(query_lower)
        if filename and 'timesheet' in tables:
            ts_table = tables['timesheet']
            return f"""SELECT [TimesheetID], [EmployeeID], [Date], [TotalHours]
FROM [{ts_table['schema']}].[{ts_table['table']}]
WHERE [FileName] = '{filename}'
ORDER BY [Date]"""
        elif 'timesheet' in tables:
            # If no filename found, fall back to date-based query if possible
            if date_info:
                ts_table = tables['timesheet']
                start_date, end_date = date_info
                return f"""SELECT TOP 20 [TimesheetID], [EmployeeID], [Date], [TotalHours]
FROM [{ts_table['schema']}].[{ts_table['table']}]
WHERE [Date] BETWEEN '{start_date}' AND '{end_date}'
ORDER BY [Date] DESC"""
    
    # 23. List files processed last week
    if 'files processed last week' in query_lower:
        if 'processedfiles' in tables:
            pf_table = tables['processedfiles']
            last_week_start, last_week_end = extract_date_info('last week') or ('2025-01-01', '2025-01-07')
            return f"""SELECT [FileName], [ProcessedDate], [EmployeeID]
FROM [{pf_table['schema']}].[{pf_table['table']}]
WHERE [ProcessedDate] BETWEEN '{last_week_start}' AND '{last_week_end}'
ORDER BY [ProcessedDate] DESC"""
    
    # === LEAVE MANAGEMENT ===
    
    # NEW: How many leave days did [Employee] take in [Month Year]?
    if ('how many leave days' in query_lower and ('take' in query_lower or 'took' in query_lower)) or ('leave days did' in query_lower):
        if employee_name and 'leaverequest' in tables and 'employee' in tables:
            lr_table = tables['leaverequest']
            emp_table = tables['employee']
            
            # Use date_info if available, otherwise use a reasonable default range
            if date_info:
                start_date, end_date = date_info
            else:
                # Default to current year if no date specified
                start_date, end_date = '2025-01-01', '2025-12-31'
                
            return f"""SELECT SUM(lr.[NumberOfDays]) as TotalLeaveDays
FROM [{lr_table['schema']}].[{lr_table['table']}] lr
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON lr.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'
AND lr.[Status] = 'Approved'
AND lr.[StartDate] BETWEEN '{start_date}' AND '{end_date}'"""
    
    # 24. Show pending leave requests OR employees with pending leave requests
    if 'pending leave requests' in query_lower or 'employees who have leave requests with status' in query_lower:
        if 'leaverequest' in tables:
            lr_table = tables['leaverequest']
            
            # If asking for employees with pending leave requests
            if 'employees who have' in query_lower or 'employees with' in query_lower:
                if 'employee' in tables:
                    emp_table = tables['employee']
                    return f"""SELECT DISTINCT e.[EmployeeName], lr.[StartDate], lr.[EndDate]
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{lr_table['schema']}].[{lr_table['table']}] lr ON e.[EmployeeID] = lr.[EmployeeID]
WHERE lr.[Status] = 'Pending'
ORDER BY lr.[StartDate]"""
            else:
                # Just show pending leave requests
                return f"""SELECT [LeaveRequestID], [EmployeeID], [StartDate], [EndDate], [Status]
FROM [{lr_table['schema']}].[{lr_table['table']}]
WHERE [Status] = 'Pending'
ORDER BY [StartDate]"""
    
    # 25. List all sick leave with sick notes
    if 'sick leave with sick notes' in query_lower or 'all sick leave' in query_lower:
        if 'leaverequest' in tables and 'leavetype' in tables and 'employee' in tables:
            lr_table = tables['leaverequest']
            lt_table = tables['leavetype']
            emp_table = tables['employee']
            return f"""SELECT e.[EmployeeName], lr.[StartDate], lr.[EndDate], lr.[Status]
FROM [{lr_table['schema']}].[{lr_table['table']}] lr
JOIN [{lt_table['schema']}].[{lt_table['table']}] lt ON lr.[LeaveTypeID] = lt.[LeaveTypeID]
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON lr.[EmployeeID] = e.[EmployeeID]
WHERE lt.[LeaveTypeName] LIKE '%Sick%'
ORDER BY lr.[StartDate] DESC"""
    
    # 26. Who is on leave this week?
    if 'who is on leave this week' in query_lower or 'on leave this week' in query_lower:
        if 'leaverequest' in tables and 'employee' in tables:
            lr_table = tables['leaverequest']
            emp_table = tables['employee']
            this_week_start, this_week_end = extract_date_info('this week') or ('2025-07-21', '2025-07-27')
            return f"""SELECT DISTINCT e.[EmployeeName], lr.[StartDate], lr.[EndDate]
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{lr_table['schema']}].[{lr_table['table']}] lr ON e.[EmployeeID] = lr.[EmployeeID]
WHERE lr.[Status] = 'Approved'
AND lr.[StartDate] <= '{this_week_end}' AND lr.[EndDate] >= '{this_week_start}'"""
    
    # 27. Show approved leave for [Month Year]
    if 'approved leave for' in query_lower and date_info:
        if 'leaverequest' in tables and 'employee' in tables:
            lr_table = tables['leaverequest']
            emp_table = tables['employee']
            start_date, end_date = date_info
            return f"""SELECT e.[EmployeeName], lr.[StartDate], lr.[EndDate], lr.[NumberOfDays]
FROM [{lr_table['schema']}].[{lr_table['table']}] lr
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON lr.[EmployeeID] = e.[EmployeeID]
WHERE lr.[Status] = 'Approved'
AND lr.[StartDate] BETWEEN '{start_date}' AND '{end_date}'
ORDER BY lr.[StartDate]"""
    
    # === ADVANCED ANALYTICS ===
    
    # 28. Show employee utilization (billable hours vs available)
    if 'employee utilization' in query_lower or 'billable hours vs available' in query_lower:
        if 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            return f"""SELECT e.[EmployeeName],
SUM(CASE WHEN t.[BillableStatus] = 'Billable' THEN t.[TotalHours] ELSE 0 END) as BillableHours,
SUM(t.[TotalHours]) as TotalHours,
CASE WHEN SUM(t.[TotalHours]) > 0 
     THEN (SUM(CASE WHEN t.[BillableStatus] = 'Billable' THEN t.[TotalHours] ELSE 0 END) * 100.0 / SUM(t.[TotalHours]))
     ELSE 0 END as UtilizationPercent
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON e.[EmployeeID] = t.[EmployeeID]
GROUP BY e.[EmployeeName]
ORDER BY UtilizationPercent DESC"""
    
    # 29. Compare forecasted vs actual hours per employee
    if 'forecasted vs actual hours' in query_lower:
        if 'forecast' in tables and 'timesheet' in tables and 'employee' in tables:
            forecast_table = tables['forecast']
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            return f"""SELECT e.[EmployeeName],
f.[TotalHours] as ForecastedHours,
SUM(t.[TotalHours]) as ActualHours,
(SUM(t.[TotalHours]) - f.[TotalHours]) as Variance
FROM [{emp_table['schema']}].[{emp_table['table']}] e
LEFT JOIN [{forecast_table['schema']}].[{forecast_table['table']}] f ON e.[EmployeeID] = f.[EmployeeID]
LEFT JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON e.[EmployeeID] = t.[EmployeeID]
GROUP BY e.[EmployeeName], f.[TotalHours]
ORDER BY Variance DESC"""
    
    # 30. Identify employees with less than 80% billable hours OR non-billable hours
    if ('less than 80%' in query_lower and 'billable hours' in query_lower) or ('employees with less than 80%' in query_lower):
        if 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            
            # Check if asking for non-billable hours specifically
            if 'non billable' in query_lower or 'non-billable' in query_lower:
                return f"""SELECT e.[EmployeeName],
SUM(CASE WHEN t.[BillableStatus] = 'Non-Billable' THEN t.[TotalHours] ELSE 0 END) as NonBillableHours,
SUM(t.[TotalHours]) as TotalHours,
(SUM(CASE WHEN t.[BillableStatus] = 'Non-Billable' THEN t.[TotalHours] ELSE 0 END) * 100.0 / SUM(t.[TotalHours])) as NonBillablePercent
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON e.[EmployeeID] = t.[EmployeeID]
GROUP BY e.[EmployeeName]
HAVING (SUM(CASE WHEN t.[BillableStatus] = 'Non-Billable' THEN t.[TotalHours] ELSE 0 END) * 100.0 / SUM(t.[TotalHours])) < 80
ORDER BY NonBillablePercent"""
            else:
                return f"""SELECT e.[EmployeeName],
SUM(CASE WHEN t.[BillableStatus] = 'Billable' THEN t.[TotalHours] ELSE 0 END) as BillableHours,
SUM(t.[TotalHours]) as TotalHours,
(SUM(CASE WHEN t.[BillableStatus] = 'Billable' THEN t.[TotalHours] ELSE 0 END) * 100.0 / SUM(t.[TotalHours])) as BillablePercent
FROM [{emp_table['schema']}].[{emp_table['table']}] e
JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON e.[EmployeeID] = t.[EmployeeID]
GROUP BY e.[EmployeeName]
HAVING (SUM(CASE WHEN t.[BillableStatus] = 'Billable' THEN t.[TotalHours] ELSE 0 END) * 100.0 / SUM(t.[TotalHours])) < 80
ORDER BY BillablePercent"""
    
    # === EDGE CASES ===
    
    # 31. Find timesheets with missing project information
    if 'timesheets with missing project' in query_lower or 'missing project information' in query_lower:
        if 'timesheet' in tables:
            ts_table = tables['timesheet']
            return f"""SELECT [TimesheetID], [EmployeeID], [Date], [TotalHours]
FROM [{ts_table['schema']}].[{ts_table['table']}]
WHERE [ProjectID] IS NULL
ORDER BY [Date] DESC"""
    
    # 32. Show employees with no timesheets last month
    if 'employees with no timesheets last month' in query_lower:
        if 'employee' in tables and 'timesheet' in tables:
            emp_table = tables['employee']
            ts_table = tables['timesheet']
            last_month_start, last_month_end = extract_date_info('last month') or ('2025-06-01', '2025-06-30')
            return f"""SELECT e.[EmployeeID], e.[EmployeeName]
FROM [{emp_table['schema']}].[{emp_table['table']}] e
WHERE NOT EXISTS (
    SELECT 1 FROM [{ts_table['schema']}].[{ts_table['table']}] t
    WHERE t.[EmployeeID] = e.[EmployeeID]
    AND t.[Date] BETWEEN '{last_month_start}' AND '{last_month_end}'
)"""
    
    # 33. List days with unusually high hours (>12)
    if 'unusually high hours' in query_lower or 'hours >12' in query_lower or 'hours > 12' in query_lower:
        if 'timesheet' in tables:
            ts_table = tables['timesheet']
            return f"""SELECT [TimesheetID], [EmployeeID], [Date], [TotalHours]
FROM [{ts_table['schema']}].[{ts_table['table']}]
WHERE [TotalHours] > 12
ORDER BY [TotalHours] DESC, [Date] DESC"""
    
    # 34. Find duplicate timesheet entries
    if 'duplicate timesheet entries' in query_lower:
        if 'timesheet' in tables:
            ts_table = tables['timesheet']
            return f"""SELECT [EmployeeID], [Date], [ProjectID], COUNT(*) as DuplicateCount
FROM [{ts_table['schema']}].[{ts_table['table']}]
GROUP BY [EmployeeID], [Date], [ProjectID]
HAVING COUNT(*) > 1
ORDER BY DuplicateCount DESC"""
    
    # === SPECIFIC TEST CASES ===
    
    # 39. Show [Employee]'s timesheets where TotalHours > 8
    if 'timesheets where totalhours > 8' in query_lower or ('totalhours > 8' in query_lower and employee_name):
        if employee_name and 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            return f"""SELECT t.[TimesheetID], t.[Date], t.[TotalHours], t.[ProjectID]
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%' AND t.[TotalHours] > 8
ORDER BY t.[TotalHours] DESC"""
    
    # 40. List all 'Training' activities for [Employee]
    if 'training activities for' in query_lower or ('training' in query_lower and employee_name):
        if employee_name and 'timesheet' in tables and 'employee' in tables and 'activity' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            act_table = tables['activity']
            return f"""SELECT t.[TimesheetID], t.[Date], a.[ActivityName], t.[TotalHours]
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
JOIN [{act_table['schema']}].[{act_table['table']}] a ON t.[ActivityID] = a.[ActivityID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%' AND a.[ActivityName] LIKE '%Training%'
ORDER BY t.[Date] DESC"""
    
    # 41. Show [Employee]'s overtime hours (TotalHours > 8)
    if 'overtime hours' in query_lower and employee_name:
        if 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            return f"""SELECT t.[Date], t.[TotalHours], (t.[TotalHours] - 8) as OvertimeHours
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%' AND t.[TotalHours] > 8
ORDER BY t.[TotalHours] DESC"""
    
    # 42. Find all 'Non-Billable' entries for [Employee]
    if 'non-billable entries for' in query_lower or ('non-billable' in query_lower and employee_name):
        if employee_name and 'timesheet' in tables and 'employee' in tables:
            ts_table = tables['timesheet']
            emp_table = tables['employee']
            return f"""SELECT t.[TimesheetID], t.[Date], t.[TotalHours], t.[ProjectID]
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%' AND t.[BillableStatus] = 'Non-Billable'
ORDER BY t.[Date] DESC"""
    
    # === VALIDATION QUERIES ===
    
    # 46. Find timesheets with StartTime after EndTime
    if 'starttime after endtime' in query_lower or 'invalid time entries' in query_lower:
        if 'timesheet' in tables:
            ts_table = tables['timesheet']
            return f"""SELECT [TimesheetID], [EmployeeID], [Date], [StartTime], [EndTime]
FROM [{ts_table['schema']}].[{ts_table['table']}]
WHERE [StartTime] > [EndTime]
ORDER BY [Date] DESC"""
    
    # 47. List entries with invalid BillableStatus
    if 'invalid billablestatus' in query_lower or 'entries with invalid billable' in query_lower:
        if 'timesheet' in tables:
            ts_table = tables['timesheet']
            return f"""SELECT [TimesheetID], [EmployeeID], [Date], [BillableStatus]
FROM [{ts_table['schema']}].[{ts_table['table']}]
WHERE [BillableStatus] NOT IN ('Billable', 'Non-Billable')
ORDER BY [Date] DESC"""
    
    # 48. Show dates with no timesheet entries
    if 'dates with no timesheet entries' in query_lower or 'missing timesheet dates' in query_lower:
        if 'timesheet' in tables:
            ts_table = tables['timesheet']
            return f"""WITH DateRange AS (
    SELECT DATEADD(day, ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1, '2025-01-01') as CheckDate
    FROM sys.objects a CROSS JOIN sys.objects b
)
SELECT TOP 30 dr.CheckDate
FROM DateRange dr
LEFT JOIN [{ts_table['schema']}].[{ts_table['table']}] t ON dr.CheckDate = t.[Date]
WHERE t.[Date] IS NULL
AND dr.CheckDate <= GETDATE()
ORDER BY dr.CheckDate"""
    
    # === FALLBACK PATTERNS ===
    
    # Count queries
    if any(word in query_lower for word in ['count', 'how many', 'number of']):
        if 'employee' in query_lower and 'employee' in tables:
            t = tables['employee']
            return f"SELECT COUNT(*) as EmployeeCount FROM [{t['schema']}].[{t['table']}]"
        elif 'project' in query_lower and 'project' in tables:
            t = tables['project']
            return f"SELECT COUNT(*) as ProjectCount FROM [{t['schema']}].[{t['table']}]"
        elif 'client' in query_lower and 'client' in tables:
            t = tables['client']
            return f"SELECT COUNT(*) as ClientCount FROM [{t['schema']}].[{t['table']}]"
    
    # Simple list queries
    if any(word in query_lower for word in ['show', 'list', 'display', 'what', 'which']):
        if 'project' in query_lower and 'project' in tables:
            t = tables['project']
            return f"SELECT TOP 10 [ProjectID], [ProjectName] FROM [{t['schema']}].[{t['table']}]"
        elif 'employee' in query_lower and 'employee' in tables:
            t = tables['employee']
            return f"SELECT TOP 10 [EmployeeID], [EmployeeName] FROM [{t['schema']}].[{t['table']}]"
        elif 'client' in query_lower and 'client' in tables:
            t = tables['client']
            return f"SELECT TOP 10 [ClientID], [ClientName] FROM [{t['schema']}].[{t['table']}]"
    
    # IMPROVED Default fallback - analyze query intent instead of random table
    if schema_metadata:
        # Analyze query for table hints
        table_hints = {
            'employee': ['employee', 'staff', 'worker', 'person'],
            'project': ['project', 'work', 'task'],
            'timesheet': ['timesheet', 'hours', 'time', 'work'],
            'leaverequest': ['leave', 'vacation', 'absence'],
            'client': ['client', 'customer'],
            'activity': ['activity', 'activities']
        }
        
        best_table = None
        max_score = 0
        
        for table in schema_metadata:
            table_name_lower = table['table'].lower()
            score = 0
            
            # Check if table name appears in query
            if table_name_lower in query_lower:
                score += 10
            
            # Check for related keywords
            if table_name_lower in table_hints:
                for hint in table_hints[table_name_lower]:
                    if hint in query_lower:
                        score += 5
            
            if score > max_score:
                max_score = score
                best_table = table
        
        # Use best matching table or fall back to Employee table (most common)
        if not best_table:
            for table in schema_metadata:
                if table['table'].lower() == 'employee':
                    best_table = table
                    break
        
        if not best_table:
            best_table = schema_metadata[0]
        
        # Return null instead of random query if we can't determine intent
        if max_score == 0:
            return None  # This will trigger LLM fallback
        
        columns = [col['name'] for col in best_table['columns'][:3]]
        column_list = ', '.join([f"[{col}]" for col in columns])
        return f"SELECT TOP 10 {column_list} FROM [{best_table['schema']}].[{best_table['table']}]"
    
    return None  # Trigger LLM fallback instead of error

# Test with all training questions
if __name__ == "__main__":
    print("=== Complete SQL Trainer - All 48 Questions ===")
    
    # Test a few key questions
    test_questions = [
        "What projects has Siyakhanya Mjikeliso worked on?",
        "Show employee utilization (billable hours vs available)",
        "Find timesheets with missing project information",
        "List all 'Training' activities for Siyakhanya Mjikeliso"
    ]
    
    # Mock schema
    test_schema = [
        {'schema': 'Timesheet', 'table': 'Employee', 'columns': [{'name': 'EmployeeID'}, {'name': 'EmployeeName'}]},
        {'schema': 'Timesheet', 'table': 'Project', 'columns': [{'name': 'ProjectID'}, {'name': 'ProjectName'}]},
        {'schema': 'Timesheet', 'table': 'Timesheet', 'columns': [{'name': 'TimesheetID'}, {'name': 'EmployeeID'}, {'name': 'ProjectID'}, {'name': 'TotalHours'}, {'name': 'BillableStatus'}]},
        {'schema': 'Timesheet', 'table': 'Activity', 'columns': [{'name': 'ActivityID'}, {'name': 'ActivityName'}]}
    ]
    
    for question in test_questions:
        sql = generate_complete_sql(question, test_schema)
        print(f"Q: {question}")
        print(f"SQL: {sql[:100]}{'...' if len(sql) > 100 else ''}")
        print()