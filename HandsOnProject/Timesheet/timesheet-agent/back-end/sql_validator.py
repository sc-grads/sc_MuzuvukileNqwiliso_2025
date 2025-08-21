"""
Comprehensive SQL query validation and safety checks system.
Implements query performance estimation, data access validation, complexity scoring,
and advanced SQL injection prevention.
"""

import re
import sqlparse
import logging
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"
    DANGEROUS = "dangerous"

class SecurityRisk(Enum):
    """Security risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PerformanceRisk(Enum):
    """Performance risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Comprehensive validation result"""
    is_valid: bool
    query: str
    errors: List[str]
    warnings: List[str]
    complexity: QueryComplexity
    security_risk: SecurityRisk
    performance_risk: PerformanceRisk
    estimated_execution_time: float  # in seconds
    estimated_rows_affected: int
    allowed_tables: Set[str]
    accessed_tables: Set[str]
    suggestions: List[str]
    
class QueryPerformanceEstimator:
    """Estimates query performance and execution time"""
    
    def __init__(self):
        # Base execution time estimates (in seconds)
        self.base_times = {
            'simple_select': 0.1,
            'filtered_select': 0.5,
            'join_operation': 1.0,
            'aggregation': 2.0,
            'subquery': 3.0,
            'complex_join': 5.0,
            'window_function': 4.0,
            'cte': 2.5
        }
        
        # Performance impact multipliers
        self.multipliers = {
            'no_where_clause': 10.0,
            'leading_wildcard': 5.0,
            'function_in_where': 3.0,
            'multiple_joins': 2.0,
            'nested_subquery': 4.0,
            'cross_join': 20.0,
            'no_indexes': 8.0
        }
    
    def estimate_performance(self, sql_query: str, schema_metadata: List[Dict]) -> Tuple[float, PerformanceRisk, List[str]]:
        """Estimate query performance and identify risks"""
        sql_upper = sql_query.upper()
        warnings = []
        base_time = 0.1
        multiplier = 1.0
        
        # Analyze query structure
        parsed = sqlparse.parse(sql_query)[0]
        
        # Check for basic SELECT
        if 'SELECT' in sql_upper:
            base_time += self.base_times['simple_select']
        
        # Check for WHERE clause - but be less aggressive for small result sets
        if 'WHERE' not in sql_upper:
            # Only apply heavy penalty if no TOP clause is present
            if 'TOP' not in sql_upper:
                multiplier *= self.multipliers['no_where_clause']
                warnings.append("Query lacks WHERE clause - may scan entire table(s)")
            else:
                # Lighter penalty if TOP clause limits results
                multiplier *= 2.0
                warnings.append("Query lacks WHERE clause but has TOP limit")
        
        # Count JOINs
        join_count = len(re.findall(r'\bJOIN\b', sql_upper))
        if join_count > 0:
            base_time += self.base_times['join_operation'] * join_count
            if join_count > 3:
                multiplier *= self.multipliers['multiple_joins']
                warnings.append(f"Query has {join_count} JOINs - consider optimization")
        
        # Check for CROSS JOIN (dangerous)
        if 'CROSS JOIN' in sql_upper:
            multiplier *= self.multipliers['cross_join']
            warnings.append("CROSS JOIN detected - extremely performance intensive")
        
        # Count subqueries
        subquery_count = len(re.findall(r'\bSELECT\b', sql_upper)) - 1
        if subquery_count > 0:
            base_time += self.base_times['subquery'] * subquery_count
            if subquery_count > 2:
                multiplier *= self.multipliers['nested_subquery']
                warnings.append(f"Query has {subquery_count} subqueries - may be slow")
        
        # Check for aggregations
        aggregations = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP BY']
        if any(agg in sql_upper for agg in aggregations):
            base_time += self.base_times['aggregation']
        
        # Check for window functions
        window_functions = ['ROW_NUMBER', 'RANK', 'DENSE_RANK', 'LAG', 'LEAD', 'OVER']
        if any(func in sql_upper for func in window_functions):
            base_time += self.base_times['window_function']
        
        # Check for CTEs
        if 'WITH' in sql_upper:
            base_time += self.base_times['cte']
        
        # Check for leading wildcards in LIKE
        like_patterns = re.findall(r"LIKE\s+['\"]%", sql_upper)
        if like_patterns:
            multiplier *= self.multipliers['leading_wildcard']
            warnings.append("Leading wildcard in LIKE clause prevents index usage")
        
        # Check for functions in WHERE clause
        where_functions = re.findall(r'WHERE.*?(?:UPPER|LOWER|SUBSTRING|LEFT|RIGHT|CONVERT)\s*\(', sql_upper)
        if where_functions:
            multiplier *= self.multipliers['function_in_where']
            warnings.append("Functions in WHERE clause may prevent index usage")
        
        # Calculate estimated time
        estimated_time = base_time * multiplier
        
        # Determine performance risk - be more lenient
        if estimated_time < 2.0:
            risk = PerformanceRisk.LOW
        elif estimated_time < 10.0:
            risk = PerformanceRisk.MEDIUM
        elif estimated_time < 60.0:  # Increased from 30 to 60 seconds
            risk = PerformanceRisk.HIGH
        else:
            risk = PerformanceRisk.CRITICAL
            warnings.append("Query estimated to take over 60 seconds - consider optimization")
        
        return estimated_time, risk, warnings

class DataAccessValidator:
    """Validates data access permissions and table restrictions"""
    
    def __init__(self, allowed_tables: Set[str]):
        self.allowed_tables = allowed_tables
        self.restricted_patterns = [
            r'.*password.*',
            r'.*secret.*',
            r'.*key.*',
            r'.*token.*',
            r'.*credential.*',
            r'.*auth.*',
            r'.*security.*'
        ]
    
    def validate_table_access(self, sql_query: str) -> Tuple[bool, Set[str], List[str]]:
        """Validate that query only accesses allowed tables"""
        errors = []
        accessed_tables = set()
        
        # Extract table references from SQL with improved patterns
        table_patterns = [
            r'FROM\s+\[?([^\s\[\],\)]+)\]?\.\[?([^\s\[\],\)]+)\]?',  # Schema.Table
            r'FROM\s+\[?([^\s\[\],\)]+)\]?(?!\.)(?:\s|$)',  # Just table name
            r'JOIN\s+\[?([^\s\[\],\)]+)\]?\.\[?([^\s\[\],\)]+)\]?',  # Schema.Table in JOIN
            r'JOIN\s+\[?([^\s\[\],\)]+)\]?(?!\.)(?:\s|$)',  # Just table name in JOIN
            r'UPDATE\s+\[?([^\s\[\],\)]+)\]?\.\[?([^\s\[\],\)]+)\]?',
            r'UPDATE\s+\[?([^\s\[\],\)]+)\]?(?!\.)(?:\s|$)',
            r'INSERT\s+INTO\s+\[?([^\s\[\],\)]+)\]?\.\[?([^\s\[\],\)]+)\]?',
            r'INSERT\s+INTO\s+\[?([^\s\[\],\)]+)\]?(?!\.)(?:\s|$)',
            r'DELETE\s+FROM\s+\[?([^\s\[\],\)]+)\]?\.\[?([^\s\[\],\)]+)\]?',
            r'DELETE\s+FROM\s+\[?([^\s\[\],\)]+)\]?(?!\.)(?:\s|$)'
        ]
        
        sql_upper = sql_query.upper()
        
        # Also check for CTE names (they shouldn't be validated as table access)
        cte_names = set()
        cte_pattern = r'WITH\s+([^\s\(]+)\s+AS\s*\('
        cte_matches = re.findall(cte_pattern, sql_upper)
        for cte_match in cte_matches:
            cte_names.add(cte_match.upper())
        
        for pattern in table_patterns:
            matches = re.findall(pattern, sql_upper)
            for match in matches:
                table_ref = None
                
                if isinstance(match, tuple):
                    if len(match) == 2 and match[1]:  # Schema.Table format
                        table_ref = f"{match[0]}.{match[1]}"
                    elif match[0]:  # Just table name
                        table_ref = match[0]
                else:
                    table_ref = match
                
                if table_ref and table_ref not in cte_names:
                    # Clean up table reference
                    table_ref = table_ref.strip('[](),')
                    accessed_tables.add(table_ref)
                    
                    # Check if table is allowed (case-insensitive)
                    table_found = False
                    for allowed_table in self.allowed_tables:
                        if table_ref.upper() == allowed_table.upper():
                            table_found = True
                            break
                        # Also check without schema prefix
                        if '.' in allowed_table:
                            allowed_table_name = allowed_table.split('.')[-1]
                            if table_ref.upper() == allowed_table_name.upper():
                                table_found = True
                                break
                    
                    if not table_found:
                        errors.append(f"Access denied to table '{table_ref}' - not in imported schema")
        
        # Check for potentially sensitive table access
        for table in accessed_tables:
            table_lower = table.lower()
            for pattern in self.restricted_patterns:
                if re.match(pattern, table_lower):
                    errors.append(f"Warning: Accessing potentially sensitive table '{table}'")
        
        is_valid = len([e for e in errors if not e.startswith("Warning:")]) == 0
        return is_valid, accessed_tables, errors

class QueryComplexityScorer:
    """Scores query complexity and identifies potential performance issues"""
    
    def __init__(self):
        self.complexity_weights = {
            'select_count': 2,
            'join_count': 3,
            'subquery_count': 4,
            'union_count': 2,
            'cte_count': 3,
            'window_function_count': 4,
            'aggregate_count': 2,
            'case_statement_count': 2,
            'nested_depth': 5
        }
    
    def calculate_complexity_score(self, sql_query: str) -> Tuple[int, QueryComplexity, List[str]]:
        """Calculate complexity score and determine complexity level"""
        sql_upper = sql_query.upper()
        warnings = []
        score = 0
        
        # Count various complexity indicators
        select_count = len(re.findall(r'\bSELECT\b', sql_upper))
        join_count = len(re.findall(r'\bJOIN\b', sql_upper))
        subquery_count = select_count - 1  # Main query doesn't count
        union_count = len(re.findall(r'\bUNION\b', sql_upper))
        cte_count = len(re.findall(r'\bWITH\b', sql_upper))
        window_function_count = len(re.findall(r'\bOVER\s*\(', sql_upper))
        aggregate_count = len(re.findall(r'\b(COUNT|SUM|AVG|MIN|MAX|STDEV|VAR)\s*\(', sql_upper))
        case_count = len(re.findall(r'\bCASE\b', sql_upper))
        
        # Calculate nested depth
        nested_depth = self._calculate_nested_depth(sql_query)
        
        # Apply weights
        score += select_count * self.complexity_weights['select_count']
        score += join_count * self.complexity_weights['join_count']
        score += subquery_count * self.complexity_weights['subquery_count']
        score += union_count * self.complexity_weights['union_count']
        score += cte_count * self.complexity_weights['cte_count']
        score += window_function_count * self.complexity_weights['window_function_count']
        score += aggregate_count * self.complexity_weights['aggregate_count']
        score += case_count * self.complexity_weights['case_statement_count']
        score += nested_depth * self.complexity_weights['nested_depth']
        
        # Generate warnings based on complexity indicators
        if join_count > 5:
            warnings.append(f"High number of JOINs ({join_count}) - consider breaking into smaller queries")
        
        if subquery_count > 3:
            warnings.append(f"Multiple subqueries ({subquery_count}) - may impact performance")
        
        if nested_depth > 3:
            warnings.append(f"Deep nesting level ({nested_depth}) - difficult to optimize")
        
        if window_function_count > 2:
            warnings.append(f"Multiple window functions ({window_function_count}) - resource intensive")
        
        # Determine complexity level
        if score <= 10:
            complexity = QueryComplexity.SIMPLE
        elif score <= 25:
            complexity = QueryComplexity.MODERATE
        elif score <= 50:
            complexity = QueryComplexity.COMPLEX
        elif score <= 100:
            complexity = QueryComplexity.VERY_COMPLEX
        else:
            complexity = QueryComplexity.DANGEROUS
            warnings.append("Query complexity is extremely high - execution not recommended")
        
        return score, complexity, warnings
    
    def _calculate_nested_depth(self, sql_query: str) -> int:
        """Calculate the maximum nesting depth of subqueries"""
        depth = 0
        max_depth = 0
        
        for char in sql_query:
            if char == '(':
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == ')':
                depth -= 1
        
        return max_depth

class AdvancedSQLInjectionPrevention:
    """Advanced SQL injection prevention beyond parameterized queries"""
    
    def __init__(self):
        # Dangerous SQL patterns that should never appear in generated queries
        self.dangerous_patterns = [
            r';\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|EXEC|EXECUTE)',
            r'(UNION|UNION\s+ALL).*SELECT.*FROM',
            r'(OR|AND)\s+1\s*=\s*1',
            r'(OR|AND)\s+\'.*\'\s*=\s*\'.*\'',
            r'--.*',
            r'/\*.*\*/',
            r'xp_cmdshell',
            r'sp_executesql',
            r'OPENROWSET',
            r'OPENDATASOURCE',
            r'INTO\s+OUTFILE',
            r'LOAD_FILE',
            r'BENCHMARK',
            r'SLEEP\s*\(',
            r'WAITFOR\s+DELAY'
        ]
        
        # Suspicious function calls
        self.suspicious_functions = [
            'EXEC', 'EXECUTE', 'EVAL', 'SYSTEM',
            'xp_cmdshell', 'sp_executesql', 'sp_makewebtask',
            'OPENROWSET', 'OPENDATASOURCE', 'BULK INSERT'
        ]
        
        # Character sequences that might indicate injection attempts
        self.suspicious_sequences = [
            r'[\'\"]\s*;\s*[\'\"]*',  # Quote followed by semicolon
            r'[\'\"]\s*\+\s*[\'\"]*',  # String concatenation
            r'[\'\"]\s*--',  # Quote followed by comment
            r'[\'\"]\s*/\*',  # Quote followed by comment
            r'0x[0-9a-fA-F]+',  # Hexadecimal values
            r'CHAR\s*\(\s*\d+\s*\)',  # CHAR function with numbers
            r'ASCII\s*\(\s*.*\s*\)',  # ASCII function
        ]
    
    def validate_against_injection(self, sql_query: str) -> Tuple[bool, SecurityRisk, List[str]]:
        """Validate query against SQL injection patterns"""
        errors = []
        warnings = []
        sql_upper = sql_query.upper()
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                errors.append(f"Dangerous SQL pattern detected: {pattern}")
        
        # Check for suspicious functions
        for func in self.suspicious_functions:
            if func in sql_upper:
                errors.append(f"Suspicious function detected: {func}")
        
        # Check for suspicious character sequences
        for pattern in self.suspicious_sequences:
            if re.search(pattern, sql_query, re.IGNORECASE):
                warnings.append(f"Suspicious character sequence detected: {pattern}")
        
        # Additional validation checks
        
        # Check for multiple statements (should not happen in generated queries)
        statements = sqlparse.split(sql_query)
        if len(statements) > 1:
            errors.append("Multiple SQL statements detected - only single statements allowed")
        
        # Check for dynamic SQL construction
        if re.search(r'[\'\"]\s*\+\s*[\'\"]*', sql_query):
            warnings.append("String concatenation detected - potential dynamic SQL")
        
        # Check for unusual quote usage
        single_quotes = sql_query.count("'")
        double_quotes = sql_query.count('"')
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            errors.append("Unmatched quotes detected - potential injection attempt")
        
        # Determine security risk level
        if errors:
            if any("Dangerous SQL pattern" in error for error in errors):
                risk = SecurityRisk.CRITICAL
            else:
                risk = SecurityRisk.HIGH
        elif warnings:
            risk = SecurityRisk.MEDIUM
        else:
            risk = SecurityRisk.LOW
        
        is_valid = len(errors) == 0
        all_issues = errors + warnings
        
        return is_valid, risk, all_issues

class ComprehensiveSQLValidator:
    """Main validator that coordinates all validation components"""
    
    def __init__(self, allowed_tables: Set[str]):
        self.performance_estimator = QueryPerformanceEstimator()
        self.access_validator = DataAccessValidator(allowed_tables)
        self.complexity_scorer = QueryComplexityScorer()
        self.injection_preventer = AdvancedSQLInjectionPrevention()
        self.validation_cache = {}
        
    def validate_query(self, sql_query: str, schema_metadata: List[Dict] = None) -> ValidationResult:
        """Perform comprehensive validation of SQL query"""
        
        # Check cache first
        query_hash = hashlib.md5(sql_query.encode()).hexdigest()
        if query_hash in self.validation_cache:
            cached_result = self.validation_cache[query_hash]
            # Check if cache is still valid (within 5 minutes)
            if time.time() - cached_result['timestamp'] < 300:
                return cached_result['result']
        
        errors = []
        warnings = []
        suggestions = []
        
        # Basic SQL parsing validation
        try:
            parsed = sqlparse.parse(sql_query)
            if not parsed:
                return ValidationResult(
                    is_valid=False,
                    query=sql_query,
                    errors=["Invalid SQL: Could not parse query"],
                    warnings=[],
                    complexity=QueryComplexity.SIMPLE,
                    security_risk=SecurityRisk.LOW,
                    performance_risk=PerformanceRisk.LOW,
                    estimated_execution_time=0.0,
                    estimated_rows_affected=0,
                    allowed_tables=self.access_validator.allowed_tables,
                    accessed_tables=set(),
                    suggestions=[]
                )
            
            statement = parsed[0]
            if statement.get_type() not in ("SELECT", "UNION", "WITH"):
                return ValidationResult(
                    is_valid=False,
                    query=sql_query,
                    errors=["Only SELECT, UNION, or WITH queries are allowed"],
                    warnings=[],
                    complexity=QueryComplexity.SIMPLE,
                    security_risk=SecurityRisk.HIGH,
                    performance_risk=PerformanceRisk.LOW,
                    estimated_execution_time=0.0,
                    estimated_rows_affected=0,
                    allowed_tables=self.access_validator.allowed_tables,
                    accessed_tables=set(),
                    suggestions=["Use SELECT statements to query data"]
                )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                query=sql_query,
                errors=[f"SQL parsing error: {str(e)}"],
                warnings=[],
                complexity=QueryComplexity.SIMPLE,
                security_risk=SecurityRisk.MEDIUM,
                performance_risk=PerformanceRisk.LOW,
                estimated_execution_time=0.0,
                estimated_rows_affected=0,
                allowed_tables=self.access_validator.allowed_tables,
                accessed_tables=set(),
                suggestions=["Check SQL syntax and structure"]
            )
        
        # 1. SQL Injection Prevention
        injection_valid, security_risk, injection_issues = self.injection_preventer.validate_against_injection(sql_query)
        if not injection_valid:
            errors.extend([issue for issue in injection_issues if not issue.startswith("Suspicious")])
        warnings.extend([issue for issue in injection_issues if issue.startswith("Suspicious")])
        
        # 2. Data Access Validation
        access_valid, accessed_tables, access_issues = self.access_validator.validate_table_access(sql_query)
        if not access_valid:
            errors.extend([issue for issue in access_issues if not issue.startswith("Warning:")])
        warnings.extend([issue for issue in access_issues if issue.startswith("Warning:")])
        
        # 3. Query Complexity Scoring
        complexity_score, complexity, complexity_warnings = self.complexity_scorer.calculate_complexity_score(sql_query)
        warnings.extend(complexity_warnings)
        
        # 4. Performance Estimation
        estimated_time, performance_risk, perf_warnings = self.performance_estimator.estimate_performance(
            sql_query, schema_metadata or []
        )
        warnings.extend(perf_warnings)
        
        # Generate suggestions based on findings
        if complexity == QueryComplexity.VERY_COMPLEX or complexity == QueryComplexity.DANGEROUS:
            suggestions.append("Consider breaking this query into smaller, simpler queries")
            suggestions.append("Use CTEs to improve readability and maintainability")
        
        if performance_risk == PerformanceRisk.HIGH or performance_risk == PerformanceRisk.CRITICAL:
            suggestions.append("Add WHERE clauses to limit the result set")
            suggestions.append("Consider adding appropriate indexes")
            suggestions.append("Use TOP clause to limit results during testing")
        
        if security_risk == SecurityRisk.HIGH or security_risk == SecurityRisk.CRITICAL:
            suggestions.append("Review query for potential security issues")
            suggestions.append("Ensure all user input is properly sanitized")
        
        # Estimate rows affected (simplified)
        estimated_rows = self._estimate_rows_affected(sql_query, accessed_tables)
        
        # Overall validation result
        is_valid = len(errors) == 0 and complexity != QueryComplexity.DANGEROUS
        
        result = ValidationResult(
            is_valid=is_valid,
            query=sql_query,
            errors=errors,
            warnings=warnings,
            complexity=complexity,
            security_risk=security_risk,
            performance_risk=performance_risk,
            estimated_execution_time=estimated_time,
            estimated_rows_affected=estimated_rows,
            allowed_tables=self.access_validator.allowed_tables,
            accessed_tables=accessed_tables,
            suggestions=suggestions
        )
        
        # Cache the result
        self.validation_cache[query_hash] = {
            'result': result,
            'timestamp': time.time()
        }
        
        return result
    
    def _estimate_rows_affected(self, sql_query: str, accessed_tables: Set[str]) -> int:
        """Estimate number of rows that might be affected by the query"""
        sql_upper = sql_query.upper()
        
        # Simple heuristic based on query structure
        if 'WHERE' not in sql_upper:
            return 10000  # Assume large result set without filtering
        elif 'TOP' in sql_upper:
            # Extract TOP value
            top_match = re.search(r'TOP\s+(\d+)', sql_upper)
            if top_match:
                return int(top_match.group(1))
        elif len(accessed_tables) == 1:
            return 1000  # Single table with WHERE clause
        else:
            return 5000  # Multiple tables with WHERE clause
        
        return 100  # Default conservative estimate
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """Generate a human-readable validation summary"""
        summary_parts = []
        
        # Overall status
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        summary_parts.append(f"Query Status: {status}")
        
        # Complexity and risk levels
        summary_parts.append(f"Complexity: {result.complexity.value.upper()}")
        summary_parts.append(f"Security Risk: {result.security_risk.value.upper()}")
        summary_parts.append(f"Performance Risk: {result.performance_risk.value.upper()}")
        
        # Performance estimates
        summary_parts.append(f"Estimated Execution Time: {result.estimated_execution_time:.2f} seconds")
        summary_parts.append(f"Estimated Rows Affected: {result.estimated_rows_affected:,}")
        
        # Tables accessed
        if result.accessed_tables:
            summary_parts.append(f"Tables Accessed: {', '.join(result.accessed_tables)}")
        
        # Errors
        if result.errors:
            summary_parts.append("\nErrors:")
            for error in result.errors:
                summary_parts.append(f"  ❌ {error}")
        
        # Warnings
        if result.warnings:
            summary_parts.append("\nWarnings:")
            for warning in result.warnings:
                summary_parts.append(f"  ⚠️ {warning}")
        
        # Suggestions
        if result.suggestions:
            summary_parts.append("\nSuggestions:")
            for suggestion in result.suggestions:
                summary_parts.append(f"  💡 {suggestion}")
        
        return "\n".join(summary_parts)

def create_validator_from_schema(schema_metadata: List[Dict]) -> ComprehensiveSQLValidator:
    """Create a validator instance from schema metadata"""
    allowed_tables = set()
    
    for table in schema_metadata:
        table_ref = f"{table['schema']}.{table['table']}"
        allowed_tables.add(table_ref)
        # Also add table name without schema for flexibility
        allowed_tables.add(table['table'])
    
    return ComprehensiveSQLValidator(allowed_tables)

# Example usage and testing functions
def test_validator():
    """Test the validator with sample queries"""
    
    # Sample schema metadata
    sample_schema = [
        {
            'schema': 'dbo',
            'table': 'Employees',
            'columns': [
                {'name': 'EmployeeID', 'type': 'int'},
                {'name': 'FirstName', 'type': 'varchar'},
                {'name': 'LastName', 'type': 'varchar'},
                {'name': 'HireDate', 'type': 'datetime'}
            ]
        },
        {
            'schema': 'dbo',
            'table': 'Orders',
            'columns': [
                {'name': 'OrderID', 'type': 'int'},
                {'name': 'EmployeeID', 'type': 'int'},
                {'name': 'OrderDate', 'type': 'datetime'},
                {'name': 'Total', 'type': 'decimal'}
            ]
        }
    ]
    
    validator = create_validator_from_schema(sample_schema)
    
    # Test queries
    test_queries = [
        "SELECT TOP 10 * FROM [dbo].[Employees]",  # Simple, should be valid
        "SELECT * FROM [dbo].[Employees]; DROP TABLE [dbo].[Orders];",  # SQL injection attempt
        "SELECT e.*, o.* FROM [dbo].[Employees] e JOIN [dbo].[Orders] o ON e.EmployeeID = o.EmployeeID",  # Complex join
        "SELECT * FROM [dbo].[NonExistentTable]",  # Invalid table
        "SELECT COUNT(*) FROM [dbo].[Employees] WHERE FirstName LIKE '%John%'"  # Performance concern
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n=== Test Query {i} ===")
        print(f"Query: {query}")
        result = validator.validate_query(query, sample_schema)
        print(validator.get_validation_summary(result))

if __name__ == "__main__":
    test_validator()