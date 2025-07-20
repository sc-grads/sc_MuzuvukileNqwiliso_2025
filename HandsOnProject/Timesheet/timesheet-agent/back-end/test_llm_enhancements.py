#!/usr/bin/env python3
"""
Test script for enhanced LLM functionality
This tests the SQL validation and complexity assessment without requiring external dependencies
"""

import re
from enum import Enum
from typing import Dict, List, Tuple
from dataclasses import dataclass

class QueryComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"

@dataclass
class ValidationResult:
    is_valid: bool
    query: str
    errors: List[str]
    warnings: List[str]
    complexity: QueryComplexity
    estimated_performance: str

# SQL Server specific functions and patterns
SQL_SERVER_FUNCTIONS = {
    'string_functions': [
        'LEN', 'LEFT', 'RIGHT', 'SUBSTRING', 'CHARINDEX', 'PATINDEX', 'REPLACE', 'STUFF',
        'UPPER', 'LOWER', 'LTRIM', 'RTRIM', 'TRIM', 'CONCAT', 'STRING_AGG', 'FORMAT'
    ],
    'date_functions': [
        'GETDATE', 'GETUTCDATE', 'DATEADD', 'DATEDIFF', 'DATEPART', 'DATENAME', 
        'YEAR', 'MONTH', 'DAY', 'EOMONTH', 'DATEFROMPARTS', 'ISDATE'
    ],
    'window_functions': [
        'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'NTILE', 'LAG', 'LEAD',
        'FIRST_VALUE', 'LAST_VALUE', 'PERCENT_RANK', 'CUME_DIST'
    ]
}

def assess_query_complexity(sql_query: str) -> Tuple[QueryComplexity, List[str]]:
    """Assess the complexity of a SQL query and provide performance warnings."""
    warnings = []
    sql_upper = sql_query.upper()
    
    # Count complexity indicators
    join_count = len(re.findall(r'\bJOIN\b', sql_upper))
    subquery_count = len(re.findall(r'\bSELECT\b', sql_upper)) - 1
    union_count = len(re.findall(r'\bUNION\b', sql_upper))
    cte_count = len(re.findall(r'\bWITH\b', sql_upper))
    
    # Calculate complexity score
    complexity_score = join_count * 2 + subquery_count * 3 + union_count * 2 + cte_count * 2
    
    # Add warnings for complex patterns
    if 'EXISTS' in sql_upper or 'NOT EXISTS' in sql_upper:
        complexity_score += 4
        warnings.append("Correlated subqueries can be performance intensive")
    
    if 'LIKE' in sql_upper and '%' in sql_query and sql_query.find('%') < sql_query.find('LIKE') + 10:
        warnings.append("Leading wildcard in LIKE clause will prevent index usage")
    
    if join_count > 5:
        warnings.append(f"Query has {join_count} JOINs - consider breaking into smaller queries")
    
    # Determine complexity level
    if complexity_score <= 3:
        return QueryComplexity.SIMPLE, warnings
    elif complexity_score <= 8:
        return QueryComplexity.MODERATE, warnings
    elif complexity_score <= 15:
        return QueryComplexity.COMPLEX, warnings
    else:
        return QueryComplexity.VERY_COMPLEX, warnings

def validate_sql_server_syntax(sql_query: str) -> Tuple[bool, List[str]]:
    """Validate SQL Server specific syntax and functions."""
    errors = []
    sql_upper = sql_query.upper()
    
    # Check for TOP clause syntax
    if 'TOP' in sql_upper:
        top_pattern = r'\bTOP\s+(\d+|\([^)]+\))'
        if not re.search(top_pattern, sql_upper):
            errors.append("TOP clause requires a numeric value")
    
    # Check for unsupported functions
    mysql_functions = ['CONCAT_WS', 'GROUP_CONCAT', 'IFNULL']
    oracle_functions = ['NVL', 'DECODE', 'ROWNUM']
    
    for func in mysql_functions + oracle_functions:
        if func in sql_upper:
            errors.append(f"Function {func} is not supported in SQL Server")
    
    return len(errors) == 0, errors

def test_enhancements():
    """Test the enhanced SQL validation and complexity assessment."""
    
    print("Testing Enhanced SQL Generation and Validation")
    print("=" * 50)
    
    # Test cases
    test_queries = [
        {
            "name": "Simple SELECT",
            "query": "SELECT TOP 10 * FROM [dbo].[Employees]",
            "expected_complexity": QueryComplexity.SIMPLE
        },
        {
            "name": "Complex JOIN with subquery",
            "query": """
            SELECT e.Name, d.DepartmentName, 
                   (SELECT COUNT(*) FROM Projects p WHERE p.EmployeeId = e.Id) as ProjectCount
            FROM Employees e 
            JOIN Departments d ON e.DepartmentId = d.Id 
            JOIN Projects pr ON e.Id = pr.EmployeeId
            WHERE e.HireDate > '2020-01-01'
            """,
            "expected_complexity": QueryComplexity.MODERATE
        },
        {
            "name": "Very complex with CTE and window functions",
            "query": """
            WITH EmployeeStats AS (
                SELECT e.Id, e.Name, 
                       ROW_NUMBER() OVER (PARTITION BY e.DepartmentId ORDER BY e.Salary DESC) as Rank,
                       AVG(e.Salary) OVER (PARTITION BY e.DepartmentId) as AvgSalary
                FROM Employees e
                WHERE EXISTS (SELECT 1 FROM Projects p WHERE p.EmployeeId = e.Id)
            )
            SELECT * FROM EmployeeStats 
            UNION ALL
            SELECT * FROM (SELECT Id, Name, 1, 0 FROM Employees WHERE Id NOT IN (SELECT EmployeeId FROM Projects))
            """,
            "expected_complexity": QueryComplexity.VERY_COMPLEX
        },
        {
            "name": "Query with performance issues",
            "query": "SELECT * FROM Employees WHERE Name LIKE '%John%' ORDER BY Name",
            "expected_warnings": ["Leading wildcard in LIKE clause will prevent index usage"]
        },
        {
            "name": "Invalid MySQL function",
            "query": "SELECT CONCAT_WS(',', FirstName, LastName) FROM Employees",
            "should_have_errors": True
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        
        query = test_case["query"].strip()
        print(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
        
        # Test complexity assessment
        complexity, warnings = assess_query_complexity(query)
        print(f"Complexity: {complexity.value}")
        
        if warnings:
            print(f"Warnings: {', '.join(warnings)}")
        
        # Test SQL Server syntax validation
        is_valid, errors = validate_sql_server_syntax(query)
        if errors:
            print(f"Syntax Errors: {', '.join(errors)}")
        
        # Verify expectations
        if "expected_complexity" in test_case:
            if complexity == test_case["expected_complexity"]:
                print("✓ Complexity assessment correct")
            else:
                print(f"✗ Expected {test_case['expected_complexity'].value}, got {complexity.value}")
        
        if "expected_warnings" in test_case:
            expected_warnings = test_case["expected_warnings"]
            if any(expected in warning for expected in expected_warnings for warning in warnings):
                print("✓ Expected warnings detected")
            else:
                print(f"✗ Expected warnings not found: {expected_warnings}")
        
        if "should_have_errors" in test_case and test_case["should_have_errors"]:
            if errors:
                print("✓ Expected errors detected")
            else:
                print("✗ Expected errors but none found")
    
    print("\n" + "=" * 50)
    print("Enhanced SQL Server Functions Available:")
    for category, functions in SQL_SERVER_FUNCTIONS.items():
        print(f"  {category}: {len(functions)} functions")
        print(f"    Examples: {', '.join(functions[:3])}...")
    
    print(f"\nTotal SQL Server functions supported: {sum(len(funcs) for funcs in SQL_SERVER_FUNCTIONS.values())}")
    print("\nEnhancement testing completed!")

if __name__ == "__main__":
    test_enhancements()