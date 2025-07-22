#!/usr/bin/env python3
"""
Intelligent SQL Generator - Hybrid approach combining pattern matching with LLM intelligence
This replaces the rigid pattern-matching system with a more flexible, scalable solution.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

class QueryIntent(Enum):
    """Common query intents that can be handled intelligently"""
    LIST_RECORDS = "list_records"
    AGGREGATE_DATA = "aggregate_data"
    FILTER_BY_EMPLOYEE = "filter_by_employee"
    FILTER_BY_DATE = "filter_by_date"
    JOIN_TABLES = "join_tables"
    CALCULATE_METRICS = "calculate_metrics"
    UNKNOWN = "unknown"

@dataclass
class QueryContext:
    """Extracted context from natural language query"""
    intent: QueryIntent
    entities: Dict[str, Any]
    tables_needed: List[str]
    confidence: float
    suggested_sql_template: Optional[str] = None

class IntelligentSQLGenerator:
    """
    Intelligent SQL generator that uses semantic understanding rather than rigid patterns
    """
    
    def __init__(self):
        self.employee_cache = {'names': [], 'last_updated': 0}
        self.common_patterns = self._load_common_patterns()
        
    def _load_common_patterns(self) -> Dict[str, Any]:
        """Load flexible patterns for common query types"""
        return {
            'employee_queries': {
                'keywords': ['employee', 'staff', 'worker', 'person'],
                'actions': ['show', 'list', 'find', 'get', 'display'],
                'filters': ['for', 'by', 'of', 'from']
            },
            'time_queries': {
                'keywords': ['hours', 'time', 'work', 'timesheet'],
                'aggregations': ['total', 'sum', 'average', 'count'],
                'periods': ['day', 'week', 'month', 'year']
            },
            'leave_queries': {
                'keywords': ['leave', 'vacation', 'absence', 'off'],
                'types': ['sick', 'annual', 'personal', 'emergency'],
                'statuses': ['pending', 'approved', 'rejected']
            }
        }
    
    def analyze_query_intent(self, query: str, schema_metadata: List[Dict]) -> QueryContext:
        """
        Analyze query to understand intent and extract context
        This is much more flexible than rigid pattern matching
        """
        query_lower = query.lower().strip()
        
        # Extract entities dynamically
        entities = self._extract_entities(query_lower, schema_metadata)
        
        # Determine intent based on semantic analysis
        intent = self._determine_intent(query_lower, entities)
        
        # Identify required tables
        tables_needed = self._identify_required_tables(query_lower, entities, schema_metadata)
        
        # Calculate confidence based on entity extraction success
        confidence = self._calculate_confidence(entities, tables_needed)
        
        return QueryContext(
            intent=intent,
            entities=entities,
            tables_needed=tables_needed,
            confidence=confidence
        )
    
    def _extract_entities(self, query: str, schema_metadata: List[Dict]) -> Dict[str, Any]:
        """Extract entities using flexible, semantic-based approach"""
        entities = {
            'employees': [],
            'dates': [],
            'tables': [],
            'columns': [],
            'aggregations': [],
            'filters': [],
            'numbers': []
        }
        
        # Dynamic employee extraction
        employees = self._extract_employees_semantic(query, schema_metadata)
        if employees:
            entities['employees'] = employees
            
        # Date extraction with flexible patterns
        dates = self._extract_dates_flexible(query)
        if dates:
            entities['dates'] = dates
            
        # Table/column detection based on schema
        tables, columns = self._extract_schema_elements(query, schema_metadata)
        entities['tables'] = tables
        entities['columns'] = columns
        
        # Aggregation detection
        aggregations = self._detect_aggregations(query)
        entities['aggregations'] = aggregations
        
        # Number extraction
        numbers = self._extract_numbers(query)
        entities['numbers'] = numbers
        
        return entities
    
    def _extract_employees_semantic(self, query: str, schema_metadata: List[Dict]) -> List[str]:
        """Extract employee names using semantic understanding"""
        from complete_sql_trainer import get_dynamic_employee_names
        
        # Get all employees from database
        all_employees = get_dynamic_employee_names(schema_metadata)
        
        found_employees = []
        
        # Check for full names and partial matches
        for employee in all_employees:
            employee_parts = employee.split()
            
            # Full name match
            if employee in query:
                found_employees.append(employee.title())
                continue
                
            # Partial name match (first name or last name)
            for part in employee_parts:
                if len(part) > 3 and part in query:
                    # Verify it's not a false positive by checking context
                    if self._is_valid_employee_context(query, part):
                        found_employees.append(employee.title())
                        break
        
        return list(set(found_employees))  # Remove duplicates
    
    def _is_valid_employee_context(self, query: str, name_part: str) -> bool:
        """Check if the name part is in a valid employee context"""
        # Look for employee-related keywords near the name
        employee_indicators = ['employee', 'staff', 'worker', 'person', 'for', 'by', 'of']
        
        # Find position of name part
        name_pos = query.find(name_part)
        if name_pos == -1:
            return False
            
        # Check words around the name (within 3 words)
        words_before = query[:name_pos].split()[-3:]
        words_after = query[name_pos + len(name_part):].split()[:3]
        
        context_words = words_before + words_after
        
        return any(indicator in ' '.join(context_words) for indicator in employee_indicators)
    
    def _extract_dates_flexible(self, query: str) -> List[Dict[str, str]]:
        """Extract dates with flexible pattern matching"""
        dates = []
        
        # Month-year patterns
        month_year_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\b'
        matches = re.findall(month_year_pattern, query, re.IGNORECASE)
        
        for month, year in matches:
            dates.append({
                'type': 'month_year',
                'month': month,
                'year': year,
                'start_date': self._month_to_date_range(month, year)[0],
                'end_date': self._month_to_date_range(month, year)[1]
            })
        
        # Date range patterns
        range_patterns = [
            r'from\s+(\w+)\s+(\d{4})\s+to\s+(\w+)\s+(\d{4})',
            r'between\s+(\w+)\s+and\s+(\w+)\s+(\d{4})',
            r'(\w+)\s+to\s+(\w+)\s+(\d{4})'
        ]
        
        for pattern in range_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                dates.extend(self._process_date_range_matches(matches))
        
        return dates
    
    def _determine_intent(self, query: str, entities: Dict[str, Any]) -> QueryIntent:
        """Determine query intent using semantic analysis"""
        
        # List/Show queries
        if any(word in query for word in ['list', 'show', 'display', 'get', 'find']):
            if entities.get('aggregations'):
                return QueryIntent.AGGREGATE_DATA
            return QueryIntent.LIST_RECORDS
        
        # Aggregation queries
        if any(word in query for word in ['total', 'sum', 'count', 'average', 'how many']):
            return QueryIntent.AGGREGATE_DATA
        
        # Employee-specific queries
        if entities.get('employees'):
            return QueryIntent.FILTER_BY_EMPLOYEE
        
        # Date-specific queries
        if entities.get('dates'):
            return QueryIntent.FILTER_BY_DATE
        
        # Join queries (multiple table indicators)
        if len(entities.get('tables', [])) > 1:
            return QueryIntent.JOIN_TABLES
        
        return QueryIntent.UNKNOWN
    
    def generate_sql_intelligent(self, query: str, schema_metadata: List[Dict]) -> Optional[str]:
        """
        Generate SQL using intelligent analysis rather than rigid patterns
        """
        # Analyze the query
        context = self.analyze_query_intent(query, schema_metadata)
        
        # If confidence is too low, return None to trigger LLM fallback
        if context.confidence < 0.6:
            return None
        
        # Generate SQL based on intent and context
        sql = self._generate_sql_by_intent(context, schema_metadata)
        
        return sql
    
    def _generate_sql_by_intent(self, context: QueryContext, schema_metadata: List[Dict]) -> Optional[str]:
        """Generate SQL based on determined intent and extracted context"""
        
        if context.intent == QueryIntent.LIST_RECORDS:
            return self._generate_list_query(context, schema_metadata)
        
        elif context.intent == QueryIntent.AGGREGATE_DATA:
            return self._generate_aggregate_query(context, schema_metadata)
        
        elif context.intent == QueryIntent.FILTER_BY_EMPLOYEE:
            return self._generate_employee_query(context, schema_metadata)
        
        elif context.intent == QueryIntent.FILTER_BY_DATE:
            return self._generate_date_query(context, schema_metadata)
        
        elif context.intent == QueryIntent.JOIN_TABLES:
            return self._generate_join_query(context, schema_metadata)
        
        return None
    
    def _generate_list_query(self, context: QueryContext, schema_metadata: List[Dict]) -> Optional[str]:
        """Generate simple list queries"""
        if not context.tables_needed:
            return None
            
        table = self._find_table_by_name(context.tables_needed[0], schema_metadata)
        if not table:
            return None
            
        # Get primary columns for the table
        columns = self._get_primary_columns(table)
        column_list = ', '.join([f"[{col}]" for col in columns[:3]])
        
        return f"SELECT TOP 10 {column_list} FROM [{table['schema']}].[{table['table']}]"
    
    def _generate_employee_query(self, context: QueryContext, schema_metadata: List[Dict]) -> Optional[str]:
        """Generate employee-specific queries"""
        if not context.entities.get('employees'):
            return None
            
        employee_name = context.entities['employees'][0]
        
        # Find employee and related tables
        emp_table = self._find_table_by_name('employee', schema_metadata)
        if not emp_table:
            return None
        
        # Determine what data is being requested
        if any(word in str(context.entities) for word in ['timesheet', 'hours']):
            ts_table = self._find_table_by_name('timesheet', schema_metadata)
            if ts_table:
                return f"""SELECT t.[TimesheetID], t.[Date], t.[TotalHours]
FROM [{ts_table['schema']}].[{ts_table['table']}] t
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON t.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'"""
        
        elif any(word in str(context.entities) for word in ['leave', 'vacation']):
            lr_table = self._find_table_by_name('leaverequest', schema_metadata)
            if lr_table:
                return f"""SELECT lr.[LeaveRequestID], lr.[StartDate], lr.[EndDate], lr.[Status]
FROM [{lr_table['schema']}].[{lr_table['table']}] lr
JOIN [{emp_table['schema']}].[{emp_table['table']}] e ON lr.[EmployeeID] = e.[EmployeeID]
WHERE e.[EmployeeName] LIKE '%{employee_name}%'"""
        
        return None
    
    # Helper methods
    def _find_table_by_name(self, table_name: str, schema_metadata: List[Dict]) -> Optional[Dict]:
        """Find table by name (case insensitive)"""
        for table in schema_metadata:
            if table['table'].lower() == table_name.lower():
                return table
        return None
    
    def _get_primary_columns(self, table: Dict) -> List[str]:
        """Get primary columns for a table"""
        columns = []
        for col in table.get('columns', []):
            columns.append(col['name'])
            if len(columns) >= 3:
                break
        return columns
    
    def _calculate_confidence(self, entities: Dict[str, Any], tables_needed: List[str]) -> float:
        """Calculate confidence score based on extracted entities"""
        score = 0.0
        
        # Entity extraction success
        if entities.get('employees'):
            score += 0.3
        if entities.get('dates'):
            score += 0.2
        if entities.get('tables'):
            score += 0.2
        if entities.get('aggregations'):
            score += 0.1
        
        # Table identification success
        if tables_needed:
            score += 0.2
        
        return min(score, 1.0)
    
    # Additional helper methods would go here...
    def _month_to_date_range(self, month: str, year: str) -> Tuple[str, str]:
        """Convert month/year to date range"""
        months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        
        month_num = months.get(month.lower(), '01')
        start_date = f"{year}-{month_num}-01"
        
        # Calculate end date
        if month_num in ['01', '03', '05', '07', '08', '10', '12']:
            end_date = f"{year}-{month_num}-31"
        elif month_num in ['04', '06', '09', '11']:
            end_date = f"{year}-{month_num}-30"
        else:
            end_date = f"{year}-{month_num}-28"
        
        return start_date, end_date

# Global instance
intelligent_generator = IntelligentSQLGenerator()

def generate_intelligent_sql(query: str, schema_metadata: List[Dict]) -> Optional[str]:
    """Main entry point for intelligent SQL generation"""
    return intelligent_generator.generate_sql_intelligent(query, schema_metadata)