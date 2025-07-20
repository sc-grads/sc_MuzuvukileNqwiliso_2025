from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from config import OLLAMA_BASE_URL, LLM_MODEL
import sqlparse
import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Initialize the LLM once when the module is loaded
llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.0)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    'numeric_functions': [
        'ABS', 'CEILING', 'FLOOR', 'ROUND', 'POWER', 'SQRT', 'LOG', 'EXP',
        'RAND', 'SIGN', 'PI', 'DEGREES', 'RADIANS'
    ],
    'aggregate_functions': [
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'STDEV', 'VAR', 'GROUPING'
    ],
    'window_functions': [
        'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'NTILE', 'LAG', 'LEAD',
        'FIRST_VALUE', 'LAST_VALUE', 'PERCENT_RANK', 'CUME_DIST'
    ],
    'conditional_functions': [
        'CASE', 'IIF', 'CHOOSE', 'COALESCE', 'NULLIF', 'ISNULL'
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

def enhanced_validate_sql(sql_query: str, schema_metadata: List[Dict], column_map: Dict[str, List[str]]) -> ValidationResult:
    """Enhanced SQL validation with complexity assessment and SQL Server specific checks."""
    errors = []
    warnings = []
    
    try:
        # Basic parsing validation
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return ValidationResult(
                is_valid=False, query=sql_query, errors=["Invalid SQL: Could not parse query"],
                warnings=[], complexity=QueryComplexity.SIMPLE, estimated_performance="Unknown"
            )

        statement = parsed[0]
        if statement.get_type() not in ("SELECT", "UNION", "WITH"):
            return ValidationResult(
                is_valid=False, query=sql_query, errors=["Only SELECT, UNION, or WITH queries are allowed"],
                warnings=[], complexity=QueryComplexity.SIMPLE, estimated_performance="N/A"
            )

        # SQL Server syntax validation
        syntax_valid, syntax_errors = validate_sql_server_syntax(sql_query)
        errors.extend(syntax_errors)

        # Schema validation (simplified)
        all_table_keys = set(column_map.keys())
        used_tables = set()

        # Basic table validation
        for token in statement.tokens:
            if isinstance(token, sqlparse.sql.Identifier):
                raw = str(token)
                match = re.search(r'\[?(\w+)\]?\.\[?(\w+)\]?', raw, re.IGNORECASE)
                if match:
                    schema, table = match.groups()
                    table_key = f"{schema}.{table}"
                    if table_key in all_table_keys:
                        used_tables.add(table_key)
                    else:
                        errors.append(f"Table '{table_key}' not found in database schema")

        # Assess query complexity
        complexity, complexity_warnings = assess_query_complexity(sql_query)
        warnings.extend(complexity_warnings)

        # Estimate performance
        performance_estimate = "Good"
        if complexity == QueryComplexity.COMPLEX:
            performance_estimate = "Moderate - may require optimization"
        elif complexity == QueryComplexity.VERY_COMPLEX:
            performance_estimate = "Poor - likely requires optimization"

        return ValidationResult(
            is_valid=len(errors) == 0, query=sql_query, errors=errors,
            warnings=warnings, complexity=complexity, estimated_performance=performance_estimate
        )

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return ValidationResult(
            is_valid=False, query=sql_query, errors=[f"Validation error: {str(e)}"],
            warnings=[], complexity=QueryComplexity.SIMPLE, estimated_performance="Unknown"
        )

def validate_sql(sql_query, schema_metadata, column_map):
    """Legacy validation function for backward compatibility."""
    result = enhanced_validate_sql(sql_query, schema_metadata, column_map)
    if result.is_valid:
        return True, result.query
    else:
        error_msg = "; ".join(result.errors)
        if result.warnings:
            error_msg += " Warnings: " + "; ".join(result.warnings)
        return False, error_msg

def col_text(col):
    return f"{col['name']} ({col['type']}) - {col['description']}"

def relationships_text(rels):
    if not rels:
        return "None"
    return ", ".join([f"{fk['source_column']} -> {fk['target_table']}.{fk['target_column']}" for fk in rels])

def generate_sql_query(nl_query, schema_metadata, column_map, entities, vector_store=None, previous_sql_query=None, error_feedback=None):
    """Enhanced SQL query generation with improved accuracy and validation."""
    
    if not entities.get("is_database_related", False):
        return "This query is not related to the database. Please ask about data present in the connected database."

    # Enhanced schema context with better descriptions
    schema_text = "\n\n".join([
        (
            f"Table: [{m['schema']}].[{m['table']}]\n"
            f"Purpose: {m.get('description', 'No description')}\n"
            f"Columns: {', '.join([col_text(c) for c in m['columns']])}\n"
            f"Relationships: {relationships_text(m['relationships'])}\n"
            f"Primary Keys: {', '.join(m['primary_keys']) if m['primary_keys'] else 'None'}"
        )
        for m in schema_metadata
    ])

    # Build enhanced context
    context = []
    intent = entities.get("intent")
    if intent == "list":
        context.append("Generate a SELECT query to list records with appropriate columns and sorting.")
    elif intent == "count":
        context.append("Generate a COUNT query using COUNT(*) or COUNT(column) as appropriate.")
    elif intent == "sum":
        context.append("Generate aggregation queries using SUM, AVG, MIN, MAX with proper GROUP BY.")
    elif intent == "filter":
        context.append("Generate filtered SELECT with appropriate WHERE clauses.")

    if entities.get("names"):
        context.append(f"Filter for names: {', '.join(entities['names'])} using LIKE '%name%' for partial matches.")
    if entities.get("dates"):
        for date_range in entities["dates"]:
            if isinstance(date_range, tuple):
                context.append(f"Filter dates BETWEEN '{date_range[0]}' AND '{date_range[1]}'.")
            else:
                context.append(f"Filter date = '{date_range}'.")
    if entities.get("limit"):
        context.append(f"Limit results to {entities['limit']} rows using TOP.")
    if entities.get("suggested_tables"):
        context.append(f"Prioritize tables: {', '.join(entities['suggested_tables'])}.")

    context_str = "\n".join(context) if context else "No specific context provided."

    # Error feedback section
    feedback_section = ""
    if previous_sql_query and error_feedback:
        feedback_section = f"\nPrevious SQL: {previous_sql_query}\nError: {error_feedback}\nFix the errors and generate corrected SQL.\n"

    # Enhanced prompt template
    enhanced_prompt = f"""You are an expert SQL Server T-SQL developer. Generate precise, efficient T-SQL queries.

DATABASE SCHEMA:
{schema_text}

USER REQUEST: {nl_query}

CONTEXT:
{context_str}

{feedback_section}

REQUIREMENTS:
1. Use ONLY existing tables and columns from the schema
2. Use proper SQL Server syntax with square brackets: [schema].[table].[column]
3. Use SQL Server functions: {', '.join(SQL_SERVER_FUNCTIONS['date_functions'][:3])}, etc.
4. Use proper date formats: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
5. Use TOP instead of LIMIT for row limiting
6. Use appropriate JOINs based on relationships
7. Include proper WHERE clauses for filtering
8. Use GROUP BY with aggregations
9. Return ONLY the SQL query - no explanations

SQL QUERY:"""

    try:
        logger.info(f"Generating SQL for query: {nl_query}")
        response = llm.invoke(enhanced_prompt)
        sql_query = response.content.strip()
        
        # Clean up response
        sql_query = sql_query.replace("`", "").strip()
        if sql_query.endswith(';'):
            sql_query = sql_query[:-1]
        
        # Remove comments and non-SQL content
        lines = [line.strip() for line in sql_query.split('\n') 
                if line.strip() and not line.strip().startswith('--')]
        sql_query = '\n'.join(lines)
        
        # Enhanced validation
        validation_result = enhanced_validate_sql(sql_query, schema_metadata, column_map)
        
        if validation_result.is_valid:
            if validation_result.warnings:
                logger.warning(f"Query complexity: {validation_result.complexity.value}")
                for warning in validation_result.warnings:
                    logger.warning(f"Warning: {warning}")
            return validation_result.query
        else:
            error_details = "; ".join(validation_result.errors)
            logger.error(f"SQL validation failed: {error_details}")
            
            # Retry with simplified approach
            if not previous_sql_query:
                simplified_entities = {
                    "is_database_related": True,
                    "intent": entities.get("intent", "list"),
                    "suggested_tables": entities.get("suggested_tables", [])[:1]
                }
                return generate_sql_query(nl_query, schema_metadata, column_map, 
                                        simplified_entities, vector_store, sql_query, error_details)
            
            return f"Failed to generate valid SQL: {error_details}"
            
    except Exception as e:
        logger.error(f"Error in SQL generation: {str(e)}")
        return f"Error generating SQL: {str(e)}"

def get_query_performance_metrics(sql_query: str) -> Dict[str, any]:
    """Analyze query for performance metrics and suggestions."""
    validation_result = enhanced_validate_sql(sql_query, [], {})
    
    return {
        "complexity": validation_result.complexity.value,
        "estimated_performance": validation_result.estimated_performance,
        "warnings": validation_result.warnings,
        "suggestions": [
            "Consider adding appropriate indexes for WHERE clause columns",
            "Review JOIN conditions for optimal performance",
            "Consider using CTEs for complex subqueries",
            "Ensure date range filters use proper indexing"
        ]
    }