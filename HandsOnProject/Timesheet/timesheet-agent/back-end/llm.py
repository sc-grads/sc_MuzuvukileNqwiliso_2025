from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from config import OLLAMA_BASE_URL, LLM_MODEL
import sqlparse
import re
import logging
import time
import hashlib
import json
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
from error_handler import ErrorType
from sql_validator import (
    ComprehensiveSQLValidator, 
    create_validator_from_schema,
    QueryComplexity,
    SecurityRisk,
    PerformanceRisk
)
import requests
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced LLM Manager with model fallback and health checking
class OllamaManager:
    def __init__(self):
        self.primary_model = LLM_MODEL
        self.fallback_models = self._get_fallback_models()
        self.base_url = OLLAMA_BASE_URL
        self.current_model = self.primary_model
        self.llm_instance = None
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutes
        self.prompt_cache = {}
        self.cache_max_size = 100
        self._initialize_llm()
    
    def _get_fallback_models(self) -> List[str]:
        """Define fallback models based on primary model"""
        if "mistral" in LLM_MODEL.lower():
            return ["llama2:7b", "llama2:13b", "codellama:7b"]
        elif "llama2" in LLM_MODEL.lower():
            return ["mistral:7b", "codellama:7b", "llama2:13b"]
        else:
            return ["mistral:7b", "llama2:7b"]
    
    def _initialize_llm(self):
        """Initialize LLM with current model"""
        try:
            self.llm_instance = ChatOllama(
                model=self.current_model, 
                base_url=self.base_url, 
                temperature=0.0,
                timeout=60
            )
            logger.info(f"Initialized LLM with model: {self.current_model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM with {self.current_model}: {e}")
            self.llm_instance = None
    
    def check_ollama_health(self) -> bool:
        """Check if Ollama service is healthy and model is available"""
        try:
            # Check if Ollama service is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code != 200:
                return False
            
            # Check if current model is available
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if self.current_model not in model_names:
                logger.warning(f"Current model {self.current_model} not found in available models: {model_names}")
                return False
            
            # Test model with a simple query
            test_response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": "SELECT 1",
                    "stream": False
                },
                timeout=30
            )
            
            return test_response.status_code == 200
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def _should_check_health(self) -> bool:
        """Determine if health check is needed"""
        return time.time() - self.last_health_check > self.health_check_interval
    
    def _attempt_model_fallback(self) -> bool:
        """Try to switch to a fallback model"""
        for fallback_model in self.fallback_models:
            try:
                logger.info(f"Attempting fallback to model: {fallback_model}")
                
                # Check if fallback model is available
                response = requests.get(f"{self.base_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_names = [model['name'] for model in models]
                    
                    if fallback_model in model_names:
                        self.current_model = fallback_model
                        self._initialize_llm()
                        
                        if self.check_ollama_health():
                            logger.info(f"Successfully switched to fallback model: {fallback_model}")
                            return True
                        
            except Exception as e:
                logger.error(f"Failed to switch to fallback model {fallback_model}: {e}")
                continue
        
        logger.error("All fallback models failed")
        return False
    
    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key for prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available"""
        if cache_key in self.prompt_cache:
            cached_item = self.prompt_cache[cache_key]
            # Check if cache is still valid (1 hour)
            if time.time() - cached_item['timestamp'] < 3600:
                logger.info("Using cached response")
                return cached_item['response']
            else:
                # Remove expired cache
                del self.prompt_cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response: str):
        """Cache response with timestamp"""
        # Implement LRU-like behavior
        if len(self.prompt_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = min(self.prompt_cache.keys(), 
                           key=lambda k: self.prompt_cache[k]['timestamp'])
            del self.prompt_cache[oldest_key]
        
        self.prompt_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
    
    def invoke(self, prompt: str, use_cache: bool = True) -> str:
        """Invoke LLM with fallback and caching support"""
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(prompt)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
        
        # Health check if needed
        if self._should_check_health():
            if not self.check_ollama_health():
                logger.warning("Health check failed, attempting model fallback")
                if not self._attempt_model_fallback():
                    raise Exception("Ollama service is not available and all fallback models failed")
            self.last_health_check = time.time()
        
        # Attempt to invoke with current model
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.llm_instance:
                    self._initialize_llm()
                
                if not self.llm_instance:
                    raise Exception("LLM instance not available")
                
                response = self.llm_instance.invoke(prompt)
                result = response.content.strip()
                
                # Cache successful response
                if use_cache:
                    self._cache_response(cache_key, result)
                
                return result
                
            except Exception as e:
                logger.error(f"LLM invocation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Try fallback model on failure
                    if not self._attempt_model_fallback():
                        time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise Exception(f"All LLM invocation attempts failed. Last error: {e}")
    
    def get_model_info(self) -> Dict[str, any]:
        """Get information about current model and health status"""
        return {
            "current_model": self.current_model,
            "primary_model": self.primary_model,
            "fallback_models": self.fallback_models,
            "base_url": self.base_url,
            "health_status": self.check_ollama_health(),
            "cache_size": len(self.prompt_cache),
            "last_health_check": self.last_health_check
        }

# Initialize the enhanced LLM manager
llm_manager = OllamaManager()

# Legacy compatibility - create a wrapper that mimics the old llm interface
class LLMWrapper:
    def invoke(self, prompt):
        class Response:
            def __init__(self, content):
                self.content = content
        
        result = llm_manager.invoke(prompt)
        return Response(result)

llm = LLMWrapper()

# Legacy ValidationResult for backward compatibility
@dataclass
class LegacyValidationResult:
    is_valid: bool
    query: str
    errors: List[str]
    warnings: List[str]
    complexity: QueryComplexity
    estimated_performance: str

# SQL Server specific functions and patterns - Enhanced for advanced query features
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
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'STDEV', 'VAR', 'GROUPING',
        'COUNT_BIG', 'CHECKSUM_AGG', 'VARP', 'STDEVP'
    ],
    'window_functions': [
        'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'NTILE', 'LAG', 'LEAD',
        'FIRST_VALUE', 'LAST_VALUE', 'PERCENT_RANK', 'CUME_DIST',
        'PERCENTILE_CONT', 'PERCENTILE_DISC'
    ],
    'conditional_functions': [
        'CASE', 'IIF', 'CHOOSE', 'COALESCE', 'NULLIF', 'ISNULL'
    ],
    'advanced_aggregates': [
        'GROUPING SETS', 'ROLLUP', 'CUBE', 'PIVOT', 'UNPIVOT'
    ],
    'cte_functions': [
        'WITH', 'RECURSIVE'
    ]
}

# Advanced query patterns and templates for complex scenarios
ADVANCED_QUERY_PATTERNS = {
    'complex_aggregation': {
        'description': 'Complex aggregations with GROUP BY, HAVING, and window functions',
        'examples': [
            'GROUP BY ... HAVING COUNT(*) > 5',
            'SUM(...) OVER (PARTITION BY ... ORDER BY ...)',
            'RANK() OVER (ORDER BY SUM(...) DESC)'
        ]
    },
    'subqueries': {
        'description': 'Correlated and non-correlated subqueries',
        'examples': [
            'WHERE column IN (SELECT ...)',
            'WHERE EXISTS (SELECT 1 FROM ... WHERE ...)',
            'SELECT ..., (SELECT ... FROM ... WHERE ...) AS subquery_result'
        ]
    },
    'cte': {
        'description': 'Common Table Expressions for complex queries',
        'examples': [
            'WITH cte_name AS (SELECT ...) SELECT ... FROM cte_name',
            'WITH RECURSIVE cte AS (... UNION ALL ...) SELECT ...'
        ]
    },
    'conditional_logic': {
        'description': 'CASE statements and conditional expressions',
        'examples': [
            'CASE WHEN condition THEN value ELSE other_value END',
            'IIF(condition, true_value, false_value)',
            'COALESCE(column1, column2, default_value)'
        ]
    },
    'advanced_joins': {
        'description': 'Optimized joins based on relationships',
        'examples': [
            'INNER JOIN with proper ON conditions',
            'LEFT JOIN for optional relationships',
            'Multiple table joins with proper order'
        ]
    }
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

def enhanced_validate_sql(sql_query: str, schema_metadata: List[Dict], column_map: Dict[str, List[str]]) -> LegacyValidationResult:
    """Enhanced SQL validation with complexity assessment and SQL Server specific checks."""
    errors = []
    warnings = []
    
    try:
        # Basic parsing validation
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return LegacyValidationResult(
                is_valid=False, query=sql_query, errors=["Invalid SQL: Could not parse query"],
                warnings=[], complexity=QueryComplexity.SIMPLE, estimated_performance="Unknown"
            )

        statement = parsed[0]
        if statement.get_type() not in ("SELECT", "UNION", "WITH"):
            return LegacyValidationResult(
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

        return LegacyValidationResult(
            is_valid=len(errors) == 0, query=sql_query, errors=errors,
            warnings=warnings, complexity=complexity, estimated_performance=performance_estimate
        )

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return LegacyValidationResult(
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

def provide_sql_generation_feedback(error_feedback: str, previous_sql: str = None) -> str:
    """Provide specific feedback for SQL generation improvements"""
    feedback_parts = []
    
    if "invalid object name" in error_feedback.lower():
        feedback_parts.append("The table name in the query does not exist. Check spelling and schema.")
        if previous_sql:
            # Extract table names from previous SQL
            table_matches = re.findall(r'\[([^\]]+)\]\.\[([^\]]+)\]', previous_sql)
            if table_matches:
                feedback_parts.append(f"Previous query used tables: {', '.join([f'{s}.{t}' for s, t in table_matches])}")
    
    elif "invalid column name" in error_feedback.lower():
        feedback_parts.append("One or more column names in the query do not exist. Verify column names against the schema.")
    
    elif "syntax error" in error_feedback.lower():
        feedback_parts.append("SQL syntax error detected. Check for proper T-SQL syntax, brackets, and keywords.")
    
    elif "timeout" in error_feedback.lower():
        feedback_parts.append("Query execution timed out. Simplify the query or add more specific WHERE conditions.")
    
    elif "permission" in error_feedback.lower():
        feedback_parts.append("Access denied to one or more database objects. Use only accessible tables.")
    
    else:
        feedback_parts.append("General error occurred. Review the query structure and try a simpler approach.")
    
    return " ".join(feedback_parts)

def analyze_query_requirements(nl_query: str, entities: Dict) -> Dict[str, bool]:
    """Analyze natural language query to determine advanced features needed"""
    query_lower = nl_query.lower()
    requirements = {
        'needs_aggregation': False,
        'needs_grouping': False,
        'needs_having': False,
        'needs_window_functions': False,
        'needs_subquery': False,
        'needs_cte': False,
        'needs_conditional_logic': False,
        'needs_advanced_joins': False,
        'complexity_level': 'simple'
    }
    
    # Aggregation indicators
    aggregation_keywords = ['total', 'sum', 'average', 'avg', 'count', 'maximum', 'max', 'minimum', 'min', 'aggregate']
    if any(keyword in query_lower for keyword in aggregation_keywords):
        requirements['needs_aggregation'] = True
    
    # Grouping indicators
    grouping_keywords = ['by', 'per', 'each', 'group', 'category', 'breakdown', 'department', 'month', 'year']
    if any(keyword in query_lower for keyword in grouping_keywords) and requirements['needs_aggregation']:
        requirements['needs_grouping'] = True
    
    # HAVING clause indicators
    having_keywords = ['groups with', 'categories with', 'departments with', 'where total', 'where sum', 'where count']
    if any(keyword in query_lower for keyword in having_keywords):
        requirements['needs_having'] = True
    
    # Window function indicators
    window_keywords = ['rank', 'ranking', 'top', 'bottom', 'running total', 'cumulative', 'previous', 'next', 'lag', 'lead']
    if any(keyword in query_lower for keyword in window_keywords):
        requirements['needs_window_functions'] = True
    
    # Subquery indicators
    subquery_keywords = ['who also', 'that have', 'with', 'exists', 'not in', 'in the list', 'among']
    if any(keyword in query_lower for keyword in subquery_keywords):
        requirements['needs_subquery'] = True
    
    # CTE indicators (complex queries that benefit from CTEs)
    cte_keywords = ['step by step', 'first find', 'then calculate', 'complex calculation', 'multiple steps']
    if any(keyword in query_lower for keyword in cte_keywords) or len(query_lower.split()) > 15:
        requirements['needs_cte'] = True
    
    # Conditional logic indicators
    conditional_keywords = ['if', 'when', 'case', 'depending on', 'based on', 'different', 'varies']
    if any(keyword in query_lower for keyword in conditional_keywords):
        requirements['needs_conditional_logic'] = True
    
    # Advanced joins indicators
    join_keywords = ['related', 'associated', 'linked', 'connected', 'along with', 'together with']
    if any(keyword in query_lower for keyword in join_keywords):
        requirements['needs_advanced_joins'] = True
    
    # Determine complexity level
    feature_count = sum(1 for v in requirements.values() if isinstance(v, bool) and v)
    if feature_count >= 4:
        requirements['complexity_level'] = 'very_complex'
    elif feature_count >= 2:
        requirements['complexity_level'] = 'complex'
    elif feature_count >= 1:
        requirements['complexity_level'] = 'moderate'
    
    return requirements

def generate_advanced_query_context(requirements: Dict[str, bool], entities: Dict, schema_metadata: List[Dict]) -> str:
    """Generate enhanced context for advanced query features"""
    context_parts = []
    
    if requirements['needs_aggregation']:
        context_parts.append("Use appropriate aggregate functions (SUM, COUNT, AVG, MIN, MAX) for calculations.")
    
    if requirements['needs_grouping']:
        context_parts.append("Use GROUP BY clause to group results by relevant columns.")
        context_parts.append("Ensure all non-aggregate columns in SELECT are included in GROUP BY.")
    
    if requirements['needs_having']:
        context_parts.append("Use HAVING clause to filter grouped results based on aggregate conditions.")
        context_parts.append("Remember: WHERE filters rows before grouping, HAVING filters after grouping.")
    
    if requirements['needs_window_functions']:
        context_parts.append("Use window functions like ROW_NUMBER(), RANK(), DENSE_RANK() with OVER clause.")
        context_parts.append("Use PARTITION BY in window functions to group calculations.")
        context_parts.append("Use ORDER BY in window functions to define ranking/ordering.")
    
    if requirements['needs_subquery']:
        context_parts.append("Use subqueries in WHERE clause with IN, EXISTS, or comparison operators.")
        context_parts.append("Consider correlated subqueries when referencing outer query columns.")
        context_parts.append("Use EXISTS for better performance when checking for related records.")
    
    if requirements['needs_cte']:
        context_parts.append("Use Common Table Expressions (WITH clause) for complex multi-step queries.")
        context_parts.append("Break complex logic into readable CTE steps.")
        context_parts.append("Use multiple CTEs when query has multiple logical components.")
    
    if requirements['needs_conditional_logic']:
        context_parts.append("Use CASE WHEN statements for conditional logic in SELECT clause.")
        context_parts.append("Use IIF() function for simple true/false conditions.")
        context_parts.append("Use COALESCE() to handle NULL values with defaults.")
    
    if requirements['needs_advanced_joins']:
        context_parts.append("Use appropriate JOIN types based on relationships:")
        context_parts.append("- INNER JOIN for required relationships")
        context_parts.append("- LEFT JOIN for optional relationships")
        context_parts.append("- Use proper ON conditions based on foreign key relationships")
        context_parts.append("Order JOINs efficiently: start with main table, then related tables")
    
    # Add complexity-specific guidance
    if requirements['complexity_level'] == 'very_complex':
        context_parts.append("COMPLEXITY GUIDANCE: This is a very complex query.")
        context_parts.append("- Consider using CTEs to break down the logic")
        context_parts.append("- Test with smaller result sets first using TOP clause")
        context_parts.append("- Ensure proper indexing on JOIN and WHERE columns")
    elif requirements['complexity_level'] == 'complex':
        context_parts.append("COMPLEXITY GUIDANCE: This is a complex query.")
        context_parts.append("- Use appropriate WHERE clauses to limit result sets")
        context_parts.append("- Consider performance implications of multiple JOINs")
    
    return "\n".join(context_parts)

def optimize_join_order(schema_metadata: List[Dict], suggested_tables: List[str]) -> List[str]:
    """Optimize JOIN order based on table relationships and sizes"""
    if not suggested_tables or len(suggested_tables) <= 1:
        return suggested_tables
    
    # Create a map of table relationships
    relationship_map = {}
    table_info = {}
    
    for table in schema_metadata:
        table_key = f"{table['schema']}.{table['table']}"
        if table_key in suggested_tables:
            table_info[table_key] = table
            relationship_map[table_key] = []
            
            # Add explicit foreign key relationships
            for rel in table.get('relationships', []):
                target_table = rel['target_table']
                if target_table in suggested_tables:
                    relationship_map[table_key].append({
                        'target': target_table,
                        'type': 'foreign_key',
                        'strength': 1.0
                    })
            
            # Add inferred relationships
            for rel in table.get('inferred_relationships', []):
                target_table = rel['target_table']
                if target_table in suggested_tables and rel['confidence'] > 0.7:
                    relationship_map[table_key].append({
                        'target': target_table,
                        'type': 'inferred',
                        'strength': rel['confidence']
                    })
    
    # Find the best starting table (most connected or highest priority)
    table_scores = {}
    for table_key in suggested_tables:
        score = 0
        
        # Score based on number of relationships
        score += len(relationship_map.get(table_key, [])) * 2
        
        # Score based on business priority
        table_data = table_info.get(table_key, {})
        priority = table_data.get('priority', {})
        if priority.get('business_importance') == 'high':
            score += 5
        elif priority.get('business_importance') == 'medium':
            score += 3
        
        # Prefer tables with primary keys (usually main entities)
        if table_data.get('primary_keys'):
            score += 2
        
        table_scores[table_key] = score
    
    # Sort tables by score (highest first)
    optimized_order = sorted(suggested_tables, key=lambda t: table_scores.get(t, 0), reverse=True)
    
    return optimized_order

def generate_fallback_query(nl_query: str, schema_metadata: List[Dict], intent: str = "list") -> str:
    """Generate a simple fallback query when complex generation fails"""
    if not schema_metadata:
        return "Error: No schema metadata available"
    
    # Find the highest priority table
    high_priority_table = None
    for table in schema_metadata:
        if table.get('priority', {}).get('business_importance') == 'high':
            high_priority_table = table
            break
    
    # If no high priority table, use the first available table
    if not high_priority_table:
        high_priority_table = schema_metadata[0]
    
    schema = high_priority_table['schema']
    table_name = high_priority_table['table']
    
    if intent == "count":
        return f"SELECT COUNT(*) as RecordCount FROM [{schema}].[{table_name}]"
    else:
        return f"SELECT TOP 10 * FROM [{schema}].[{table_name}]"

def get_model_specific_prompt_template(model_name: str) -> str:
    """Get optimized prompt template based on the specific model being used"""
    
    if "mistral" in model_name.lower():
        # Mistral 7B optimized prompt - more structured and explicit with advanced features
        return """<s>[INST] You are an expert SQL Server T-SQL developer specializing in advanced query features. Your task is to generate precise, efficient T-SQL queries with complex aggregations, subqueries, CTEs, and optimized joins.

DATABASE SCHEMA:
{schema_text}

USER REQUEST: {nl_query}

CONTEXT AND REQUIREMENTS:
{context_str}

{conversation_section}

{feedback_section}

ADVANCED T-SQL CAPABILITIES:
- Complex Aggregations: GROUP BY, HAVING, ROLLUP, CUBE, GROUPING SETS
- Window Functions: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD(), SUM() OVER()
- Subqueries: Correlated and non-correlated, EXISTS, IN, scalar subqueries
- CTEs: WITH clause for complex multi-step queries, recursive CTEs when needed
- Conditional Logic: CASE WHEN, IIF(), COALESCE(), NULLIF()
- Advanced Joins: Optimized join order, proper ON conditions, multiple table joins

STRICT REQUIREMENTS:
1. Use ONLY existing tables and columns from the schema above
2. Use proper SQL Server syntax with square brackets: [schema].[table].[column]
3. Use SQL Server functions: {sql_server_functions}
4. Use proper date formats: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
5. Use TOP instead of LIMIT for row limiting
6. Use appropriate JOINs based on relationships shown in schema
7. Include proper WHERE clauses for filtering
8. Use GROUP BY with aggregations when needed
9. Apply advanced features (CTEs, window functions, subqueries) when appropriate
10. Optimize join order based on table relationships
11. Return ONLY the SQL query - no explanations or comments

Generate the advanced T-SQL query now: [/INST]

"""
    
    elif "llama2" in model_name.lower():
        # Llama2 optimized prompt - more conversational but structured with advanced features
        return """### System: You are an expert SQL Server database developer specializing in advanced T-SQL features.

### Human: I need you to write an advanced T-SQL query for SQL Server based on this information:

DATABASE SCHEMA:
{schema_text}

USER REQUEST: {nl_query}

CONTEXT:
{context_str}

{conversation_section}

{feedback_section}

ADVANCED T-SQL FEATURES AVAILABLE:
- Complex Aggregations: GROUP BY, HAVING, ROLLUP, CUBE, GROUPING SETS
- Window Functions: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD(), SUM() OVER()
- Subqueries: Correlated and non-correlated, EXISTS, IN, scalar subqueries
- CTEs: WITH clause for complex multi-step queries
- Conditional Logic: CASE WHEN, IIF(), COALESCE(), NULLIF()
- Advanced Joins: Optimized join order, proper ON conditions

Please follow these rules:
- Only use tables and columns that exist in the schema
- Use SQL Server T-SQL syntax with square brackets
- Use SQL Server functions like: {sql_server_functions}
- Apply advanced features (CTEs, window functions, subqueries) when appropriate
- Use TOP not LIMIT
- Optimize join order based on table relationships
- Return only the SQL query, no explanations

### Assistant: Here is the advanced T-SQL query:

"""
    
    elif "codellama" in model_name.lower():
        # CodeLlama optimized prompt - code-focused with advanced features
        return """// Task: Generate advanced SQL Server T-SQL query with complex features
// Database Schema:
{schema_text}

// User Request: {nl_query}
// Context: {context_str}

{conversation_section}

{feedback_section}

/* Advanced T-SQL Features Available:
 * - Complex Aggregations: GROUP BY, HAVING, ROLLUP, CUBE, GROUPING SETS
 * - Window Functions: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD(), SUM() OVER()
 * - Subqueries: Correlated and non-correlated, EXISTS, IN, scalar subqueries
 * - CTEs: WITH clause for complex multi-step queries
 * - Conditional Logic: CASE WHEN, IIF(), COALESCE(), NULLIF()
 * - Advanced Joins: Optimized join order, proper ON conditions
 */

/* Requirements:
 * - Use only existing schema tables/columns
 * - SQL Server T-SQL syntax with [brackets]
 * - Functions: {sql_server_functions}
 * - Apply advanced features when appropriate
 * - Use TOP not LIMIT
 * - Optimize join order based on relationships
 * - Return query only
 */

-- Advanced SQL Query:
"""
    
    else:
        # Default/generic prompt template with advanced features
        return """You are an expert SQL Server T-SQL developer specializing in advanced query features. Generate precise, efficient T-SQL queries with complex aggregations, subqueries, CTEs, and optimized joins.

DATABASE SCHEMA:
{schema_text}

USER REQUEST: {nl_query}

CONTEXT:
{context_str}

{conversation_section}

{feedback_section}

ADVANCED T-SQL CAPABILITIES:
- Complex Aggregations: GROUP BY, HAVING, ROLLUP, CUBE, GROUPING SETS
- Window Functions: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD(), SUM() OVER()
- Subqueries: Correlated and non-correlated, EXISTS, IN, scalar subqueries
- CTEs: WITH clause for complex multi-step queries
- Conditional Logic: CASE WHEN, IIF(), COALESCE(), NULLIF()
- Advanced Joins: Optimized join order, proper ON conditions

REQUIREMENTS:
1. Use ONLY existing tables and columns from the schema
2. Use proper SQL Server syntax with square brackets: [schema].[table].[column]
3. Use SQL Server functions: {sql_server_functions}
4. Use proper date formats: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
5. Use TOP instead of LIMIT for row limiting
6. Use appropriate JOINs based on relationships
7. Include proper WHERE clauses for filtering
8. Use GROUP BY with aggregations
9. Apply advanced features (CTEs, window functions, subqueries) when appropriate
10. Optimize join order based on table relationships
11. Return ONLY the SQL query - no explanations

ADVANCED SQL QUERY:"""

def generate_sql_query(nl_query, schema_metadata, column_map, entities, vector_store=None, previous_sql_query=None, error_feedback=None, enhanced_data=None, conversation_context=None):
    """Enhanced SQL query generation with improved accuracy, validation, and conversation context support."""
    
    if not entities.get("is_database_related", False):
        return "This query is not related to the database. Please ask about data present in the connected database."

    # Use enhanced schema understanding to prioritize and contextualize tables
    prioritized_tables = schema_metadata
    if enhanced_data:
        # Get contextual priorities based on the query
        from database import get_contextual_table_priorities
        try:
            contextual_priorities = get_contextual_table_priorities(nl_query, schema_metadata, enhanced_data)
            # Sort schema_metadata by priority scores
            priority_map = {f"{p.schema_name}.{p.table_name}": p.priority_score for p in contextual_priorities}
            prioritized_tables = sorted(schema_metadata, 
                                      key=lambda t: priority_map.get(f"{t['schema']}.{t['table']}", 0.4), 
                                      reverse=True)
        except Exception as e:
            logger.warning(f"Could not apply contextual priorities: {e}")
            prioritized_tables = schema_metadata

    # Enhanced schema context with business patterns and priorities
    schema_text_parts = []
    for m in prioritized_tables[:10]:  # Limit to top 10 most relevant tables
        # Get business patterns for this table
        business_patterns = []
        if enhanced_data and 'business_patterns' in enhanced_data:
            table_patterns = [p for p in enhanced_data['business_patterns'] 
                            if p['schema_name'] == m['schema'] and p['table_name'] == m['table']]
            business_patterns = [f"{p['pattern_type']} ({p['confidence']:.1f})" for p in table_patterns if p['confidence'] > 0.6]
        
        # Get priority information
        priority_info = ""
        if 'priority' in m:
            priority_info = f" [Priority: {m['priority']['business_importance']}]"
        
        # Enhanced column descriptions with business patterns
        enhanced_columns = []
        for col in m['columns']:
            col_desc = col_text(col)
            if 'business_patterns' in col:
                patterns = [p['type'] for p in col['business_patterns'] if p['confidence'] > 0.7]
                if patterns:
                    col_desc += f" ({', '.join(patterns)})"
            enhanced_columns.append(col_desc)
        
        # Get inferred relationships
        inferred_rels = []
        if 'inferred_relationships' in m:
            inferred_rels = [f"{rel['source_column']} -> {rel['target_table']}.{rel['target_column']} (inferred)" 
                           for rel in m['inferred_relationships'] if rel['confidence'] > 0.7]
        
        all_relationships = relationships_text(m['relationships'])
        if inferred_rels:
            if all_relationships != "None":
                all_relationships += ", " + ", ".join(inferred_rels)
            else:
                all_relationships = ", ".join(inferred_rels)
        
        table_text = (
            f"Table: [{m['schema']}].[{m['table']}]{priority_info}\n"
            f"Purpose: {m.get('description', 'No description')}\n"
            f"Business Patterns: {', '.join(business_patterns) if business_patterns else 'None'}\n"
            f"Columns: {', '.join(enhanced_columns)}\n"
            f"Relationships: {all_relationships}\n"
            f"Primary Keys: {', '.join(m['primary_keys']) if m['primary_keys'] else 'None'}"
        )
        schema_text_parts.append(table_text)
    
    schema_text = "\n\n".join(schema_text_parts)

    # Analyze query requirements for advanced features
    query_requirements = analyze_query_requirements(nl_query, entities)
    
    # Build enhanced context with advanced query capabilities
    context = []
    intent = entities.get("intent")
    
    # Basic intent handling
    if intent == "list":
        context.append("Generate a SELECT query to list records with appropriate columns and sorting.")
    elif intent == "count":
        context.append("Generate a COUNT query using COUNT(*) or COUNT(column) as appropriate.")
    elif intent == "sum":
        context.append("Generate aggregation queries using SUM, AVG, MIN, MAX with proper GROUP BY.")
    elif intent == "filter":
        context.append("Generate filtered SELECT with appropriate WHERE clauses.")

    # Add advanced query context based on requirements analysis
    advanced_context = generate_advanced_query_context(query_requirements, entities, schema_metadata)
    if advanced_context:
        context.append("\nADVANCED QUERY FEATURES NEEDED:")
        context.append(advanced_context)

    # Optimize table join order if multiple tables are involved
    suggested_tables = entities.get("suggested_tables", [])
    if len(suggested_tables) > 1:
        optimized_tables = optimize_join_order(schema_metadata, suggested_tables)
        context.append(f"\nOPTIMIZED TABLE JOIN ORDER: {' -> '.join(optimized_tables)}")
        entities["suggested_tables"] = optimized_tables

    # Entity-specific context
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

    # Add numeric and comparison context
    if entities.get("numeric_values"):
        numeric_info = entities["numeric_values"]
        if numeric_info.get("values"):
            context.append(f"Numeric values mentioned: {numeric_info['values']}")
        if numeric_info.get("ranges"):
            context.append(f"Numeric ranges: {numeric_info['ranges']}")
        if numeric_info.get("currencies"):
            context.append(f"Currency amounts: {numeric_info['currencies']}")
        if numeric_info.get("hours"):
            context.append(f"Hour values: {numeric_info['hours']}")
    
    if entities.get("comparisons"):
        comparison_context = []
        for comp in entities["comparisons"]:
            if comp["type"] == "between":
                comparison_context.append(f"BETWEEN {comp['value'][0]} AND {comp['value'][1]}")
            else:
                comparison_context.append(f"{comp['operator']} {comp['value']}")
        if comparison_context:
            context.append(f"Comparison operators needed: {', '.join(comparison_context)}")

    context_str = "\n".join(context) if context else "No specific context provided."

    # Add conversation context to the prompt
    conversation_section = ""
    if conversation_context:
        conversation_parts = []
        
        # Add active entities from conversation
        if conversation_context.get('active_entities'):
            active_entities_str = ", ".join([f"{k}: {v}" for k, v in conversation_context['active_entities'].items() if v])
            if active_entities_str:
                conversation_parts.append(f"Active Context: {active_entities_str}")
        
        # Add recent successful patterns
        if conversation_context.get('successful_patterns'):
            recent_patterns = conversation_context['successful_patterns'][-2:]  # Last 2 successful patterns
            if recent_patterns:
                conversation_parts.append(f"Recent Successful Query Patterns: {'; '.join(recent_patterns)}")
        
        # Add context references if detected
        if conversation_context.get('context_references'):
            conversation_parts.append(f"Context References Detected: {', '.join(conversation_context['context_references'])}")
        
        # Add recent query context
        if conversation_context.get('recent_queries'):
            recent_queries = conversation_context['recent_queries'][-2:]  # Last 2 queries
            recent_context = []
            for query in recent_queries:
                if query.get('success') and query.get('sql_query'):
                    recent_context.append(f"Previous: '{query['natural_language_query']}' -> {query['sql_query']}")
            if recent_context:
                conversation_parts.append("Recent Query Context:\n" + "\n".join(recent_context))
        
        if conversation_parts:
            conversation_section = f"""
CONVERSATION CONTEXT:
{chr(10).join(conversation_parts)}

CONTEXT INSTRUCTIONS:
- Use the active context to understand entity references
- Learn from recent successful query patterns
- Resolve context references (that, those, it, etc.) using recent queries
- Maintain consistency with previous successful approaches
"""

    # Enhanced error feedback section
    feedback_section = ""
    if previous_sql_query and error_feedback:
        specific_feedback = provide_sql_generation_feedback(error_feedback, previous_sql_query)
        feedback_section = f"""
PREVIOUS ATTEMPT FAILED:
Previous SQL: {previous_sql_query}
Error: {error_feedback}
Specific Guidance: {specific_feedback}

CORRECTION INSTRUCTIONS:
- Fix the identified issues above
- Use only tables and columns that exist in the schema
- Ensure proper SQL Server T-SQL syntax
- Test with a simpler query if the current approach is too complex
"""

    # Get model-specific prompt template
    current_model = llm_manager.current_model
    prompt_template = get_model_specific_prompt_template(current_model)
    
    # Prepare comprehensive SQL Server functions string for the template
    all_functions = []
    for category, functions in SQL_SERVER_FUNCTIONS.items():
        if category != 'advanced_aggregates' and category != 'cte_functions':
            all_functions.extend(functions[:4])  # Take first 4 from each category
    
    # Add advanced features if needed
    if query_requirements.get('needs_aggregation') or query_requirements.get('needs_grouping'):
        all_functions.extend(SQL_SERVER_FUNCTIONS['advanced_aggregates'])
    
    if query_requirements.get('needs_cte'):
        all_functions.extend(SQL_SERVER_FUNCTIONS['cte_functions'])
    
    sql_server_functions = ", ".join(all_functions)
    
    # Format the enhanced prompt using the model-specific template
    enhanced_prompt = prompt_template.format(
        schema_text=schema_text,
        nl_query=nl_query,
        context_str=context_str,
        conversation_section=conversation_section,
        feedback_section=feedback_section,
        sql_server_functions=sql_server_functions
    )

    try:
        logger.info(f"Generating SQL for query: {nl_query}")
        logger.info(f"Using model: {llm_manager.current_model}")
        
        # Use the enhanced LLM manager directly for better control
        sql_query = llm_manager.invoke(enhanced_prompt, use_cache=True)
        
        # Clean up response
        sql_query = sql_query.replace("`", "").strip()
        if sql_query.endswith(';'):
            sql_query = sql_query[:-1]
        
        # Remove comments and non-SQL content
        lines = [line.strip() for line in sql_query.split('\n') 
                if line.strip() and not line.strip().startswith('--')]
        sql_query = '\n'.join(lines)
        
        # Comprehensive validation using the new validator
        validator = create_validator_from_schema(schema_metadata)
        validation_result = validator.validate_query(sql_query, schema_metadata)
        
        # Log validation details
        logger.info(f"Query validation summary:")
        logger.info(validator.get_validation_summary(validation_result))
        
        if validation_result.is_valid:
            # Log performance and security information
            if validation_result.performance_risk != PerformanceRisk.LOW:
                logger.warning(f"Performance risk: {validation_result.performance_risk.value}")
                logger.warning(f"Estimated execution time: {validation_result.estimated_execution_time:.2f} seconds")
            
            if validation_result.security_risk != SecurityRisk.LOW:
                logger.warning(f"Security risk: {validation_result.security_risk.value}")
            
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Warning: {warning}")
            
            # Check if query should be blocked due to high risk
            if validation_result.complexity == QueryComplexity.DANGEROUS:
                return f"Query blocked: Complexity level is dangerous. {'; '.join(validation_result.suggestions)}"
            
            if validation_result.performance_risk == PerformanceRisk.CRITICAL:
                return f"Query blocked: Critical performance risk detected. Estimated execution time: {validation_result.estimated_execution_time:.2f} seconds. {'; '.join(validation_result.suggestions)}"
            
            return validation_result.query
        else:
            error_details = "; ".join(validation_result.errors)
            logger.error(f"SQL validation failed: {error_details}")
            
            # Include suggestions in error message
            if validation_result.suggestions:
                error_details += f" Suggestions: {'; '.join(validation_result.suggestions)}"
            
            # Retry with simplified approach
            if not previous_sql_query:
                simplified_entities = {
                    "is_database_related": True,
                    "intent": entities.get("intent", "list"),
                    "suggested_tables": entities.get("suggested_tables", [])[:1]
                }
                return generate_sql_query(nl_query, schema_metadata, column_map, 
                                        simplified_entities, vector_store, sql_query, error_details, enhanced_data)
            
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

def comprehensive_validate_query(sql_query: str, schema_metadata: List[Dict]) -> Dict[str, any]:
    """
    Perform comprehensive validation of SQL query with safety checks.
    
    This function implements all the safety checks required by task 5:
    - Query performance estimation to prevent long-running queries
    - Data access validation to ensure queries only access imported tables
    - Query complexity scoring to warn about potentially slow queries
    - SQL injection prevention beyond parameterized queries
    
    Args:
        sql_query: The SQL query to validate
        schema_metadata: Database schema metadata for validation
        
    Returns:
        Dictionary containing validation results and safety information
    """
    validator = create_validator_from_schema(schema_metadata)
    validation_result = validator.validate_query(sql_query, schema_metadata)
    
    return {
        "is_valid": validation_result.is_valid,
        "query": validation_result.query,
        "errors": validation_result.errors,
        "warnings": validation_result.warnings,
        "complexity": {
            "level": validation_result.complexity.value,
            "description": _get_complexity_description(validation_result.complexity)
        },
        "security_risk": {
            "level": validation_result.security_risk.value,
            "description": _get_security_risk_description(validation_result.security_risk)
        },
        "performance_risk": {
            "level": validation_result.performance_risk.value,
            "description": _get_performance_risk_description(validation_result.performance_risk),
            "estimated_execution_time": validation_result.estimated_execution_time,
            "estimated_rows_affected": validation_result.estimated_rows_affected
        },
        "data_access": {
            "allowed_tables": list(validation_result.allowed_tables),
            "accessed_tables": list(validation_result.accessed_tables),
            "access_violations": [error for error in validation_result.errors if "Access denied" in error]
        },
        "suggestions": validation_result.suggestions,
        "should_block": _should_block_query(validation_result),
        "validation_summary": validator.get_validation_summary(validation_result)
    }

def _get_complexity_description(complexity: QueryComplexity) -> str:
    """Get human-readable description of query complexity level."""
    descriptions = {
        QueryComplexity.SIMPLE: "Simple query with minimal complexity",
        QueryComplexity.MODERATE: "Moderately complex query with some optimization considerations",
        QueryComplexity.COMPLEX: "Complex query that may require optimization",
        QueryComplexity.VERY_COMPLEX: "Very complex query with significant performance implications",
        QueryComplexity.DANGEROUS: "Extremely complex query that should not be executed"
    }
    return descriptions.get(complexity, "Unknown complexity level")

def _get_security_risk_description(risk: SecurityRisk) -> str:
    """Get human-readable description of security risk level."""
    descriptions = {
        SecurityRisk.LOW: "Low security risk - query appears safe",
        SecurityRisk.MEDIUM: "Medium security risk - some suspicious patterns detected",
        SecurityRisk.HIGH: "High security risk - potentially dangerous patterns found",
        SecurityRisk.CRITICAL: "Critical security risk - query should be blocked"
    }
    return descriptions.get(risk, "Unknown security risk level")

def _get_performance_risk_description(risk: PerformanceRisk) -> str:
    """Get human-readable description of performance risk level."""
    descriptions = {
        PerformanceRisk.LOW: "Low performance risk - query should execute quickly",
        PerformanceRisk.MEDIUM: "Medium performance risk - query may take some time",
        PerformanceRisk.HIGH: "High performance risk - query may be slow",
        PerformanceRisk.CRITICAL: "Critical performance risk - query may timeout or consume excessive resources"
    }
    return descriptions.get(risk, "Unknown performance risk level")

def _should_block_query(validation_result) -> bool:
    """Determine if query should be blocked based on validation results."""
    return (
        not validation_result.is_valid or
        validation_result.complexity == QueryComplexity.DANGEROUS or
        validation_result.security_risk == SecurityRisk.CRITICAL or
        validation_result.performance_risk == PerformanceRisk.CRITICAL
    )

# Additional utility functions for Ollama optimization

def get_ollama_model_info() -> Dict[str, any]:
    """Get comprehensive information about Ollama models and health status"""
    return llm_manager.get_model_info()

def check_ollama_connection() -> Dict[str, any]:
    """Check Ollama connection and return detailed status"""
    try:
        health_status = llm_manager.check_ollama_health()
        model_info = llm_manager.get_model_info()
        
        # Get available models from Ollama
        available_models = []
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
        
        return {
            "status": "healthy" if health_status else "unhealthy",
            "current_model": model_info["current_model"],
            "primary_model": model_info["primary_model"],
            "fallback_models": model_info["fallback_models"],
            "available_models": available_models,
            "base_url": model_info["base_url"],
            "cache_size": model_info["cache_size"],
            "last_health_check": model_info["last_health_check"],
            "health_check_interval": llm_manager.health_check_interval
        }
    except Exception as e:
        logger.error(f"Error checking Ollama connection: {e}")
        return {
            "status": "error",
            "error": str(e),
            "current_model": LLM_MODEL,
            "base_url": OLLAMA_BASE_URL
        }

def force_model_reconnection() -> Dict[str, any]:
    """Force reconnection to Ollama and reinitialize models"""
    try:
        logger.info("Forcing model reconnection...")
        
        # Reset health check timestamp to force immediate check
        llm_manager.last_health_check = 0
        
        # Reinitialize LLM instance
        llm_manager._initialize_llm()
        
        # Perform health check
        health_status = llm_manager.check_ollama_health()
        
        if not health_status:
            # Try fallback models
            fallback_success = llm_manager._attempt_model_fallback()
            if fallback_success:
                health_status = True
        
        return {
            "success": health_status,
            "current_model": llm_manager.current_model,
            "message": "Reconnection successful" if health_status else "Reconnection failed"
        }
        
    except Exception as e:
        logger.error(f"Error during forced reconnection: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Reconnection failed with error"
        }

def clear_prompt_cache() -> Dict[str, any]:
    """Clear the prompt cache to free memory"""
    try:
        cache_size_before = len(llm_manager.prompt_cache)
        llm_manager.prompt_cache.clear()
        
        logger.info(f"Cleared prompt cache. Removed {cache_size_before} cached items.")
        
        return {
            "success": True,
            "items_cleared": cache_size_before,
            "message": f"Successfully cleared {cache_size_before} cached prompts"
        }
        
    except Exception as e:
        logger.error(f"Error clearing prompt cache: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to clear prompt cache"
        }

def get_cache_statistics() -> Dict[str, any]:
    """Get detailed statistics about the prompt cache"""
    try:
        cache = llm_manager.prompt_cache
        current_time = time.time()
        
        # Calculate cache statistics
        total_items = len(cache)
        expired_items = 0
        oldest_timestamp = current_time
        newest_timestamp = 0
        
        for item in cache.values():
            timestamp = item['timestamp']
            if current_time - timestamp > 3600:  # 1 hour expiry
                expired_items += 1
            
            if timestamp < oldest_timestamp:
                oldest_timestamp = timestamp
            if timestamp > newest_timestamp:
                newest_timestamp = timestamp
        
        cache_age_hours = (current_time - oldest_timestamp) / 3600 if total_items > 0 else 0
        
        return {
            "total_items": total_items,
            "expired_items": expired_items,
            "valid_items": total_items - expired_items,
            "max_size": llm_manager.cache_max_size,
            "utilization_percent": (total_items / llm_manager.cache_max_size) * 100,
            "oldest_cache_age_hours": cache_age_hours,
            "cache_hit_potential": "high" if total_items > 10 else "low"
        }
        
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        return {
            "error": str(e),
            "total_items": 0
        }

def optimize_model_performance() -> Dict[str, any]:
    """Perform various optimizations to improve model performance"""
    try:
        optimizations_performed = []
        
        # 1. Clear expired cache entries
        cache = llm_manager.prompt_cache
        current_time = time.time()
        expired_keys = []
        
        for key, item in cache.items():
            if current_time - item['timestamp'] > 3600:  # 1 hour expiry
                expired_keys.append(key)
        
        for key in expired_keys:
            del cache[key]
        
        if expired_keys:
            optimizations_performed.append(f"Cleared {len(expired_keys)} expired cache entries")
        
        # 2. Force health check and model reconnection if needed
        if not llm_manager.check_ollama_health():
            reconnection_result = force_model_reconnection()
            if reconnection_result["success"]:
                optimizations_performed.append("Reconnected to healthy model")
            else:
                optimizations_performed.append("Attempted model reconnection (failed)")
        
        # 3. Reset health check interval if it's been a while
        if time.time() - llm_manager.last_health_check > llm_manager.health_check_interval * 2:
            llm_manager.last_health_check = time.time()
            optimizations_performed.append("Reset health check timer")
        
        return {
            "success": True,
            "optimizations_performed": optimizations_performed,
            "current_model": llm_manager.current_model,
            "cache_size": len(llm_manager.prompt_cache),
            "message": f"Performed {len(optimizations_performed)} optimizations"
        }
        
    except Exception as e:
        logger.error(f"Error during performance optimization: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Performance optimization failed"
        }