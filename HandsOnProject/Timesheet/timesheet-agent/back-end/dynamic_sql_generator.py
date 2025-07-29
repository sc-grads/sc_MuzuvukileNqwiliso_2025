#!/usr/bin/env python3
"""
DynamicSQLGenerator - Vector-guided SQL generation from semantic understanding.

This module implements the core SQL generation system that creates SQL queries
using semantic understanding rather than hardcoded patterns or templates.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import re

# Import existing components
from semantic_intent_engine import (
    SemanticIntentEngine, QueryIntent, Entity, EntityType, IntentType,
    ComplexityLevel, AggregationType, TemporalContext, SchemaMapping
)
from vector_schema_store import (
    VectorSchemaStore, TableMatch, ColumnMatch, RelationshipGraph
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JoinType(Enum):
    """SQL join types"""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"
    CROSS = "CROSS JOIN"


class SQLClauseType(Enum):
    """SQL clause types for construction"""
    SELECT = "SELECT"
    FROM = "FROM"
    WHERE = "WHERE"
    JOIN = "JOIN"
    GROUP_BY = "GROUP BY"
    HAVING = "HAVING"
    ORDER_BY = "ORDER BY"


@dataclass
class SQLClause:
    """Represents a SQL clause component"""
    clause_type: SQLClauseType
    content: str
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class JoinCondition:
    """Represents a join condition between tables"""
    left_table: str
    right_table: str
    left_column: str
    right_column: str
    join_type: JoinType
    confidence: float


@dataclass
class SQLQuery:
    """Complete SQL query with metadata"""
    sql: str
    confidence: float
    clauses: List[SQLClause]
    tables_used: List[str]
    columns_used: List[str]
    joins: List[JoinCondition]
    complexity_score: float
    generation_metadata: Dict[str, Any]


class SemanticQueryBuilder:
    """
    Core SQL construction class using semantic understanding.
    
    This class builds SQL queries by analyzing semantic intent and using
    vector-guided table and column selection rather than hardcoded patterns.
    """
    
    def __init__(self, 
                 vector_store: VectorSchemaStore,
                 intent_engine: SemanticIntentEngine):
        """
        Initialize the SemanticQueryBuilder.
        
        Args:
            vector_store: VectorSchemaStore for schema context
            intent_engine: SemanticIntentEngine for query understanding
        """
        self.vector_store = vector_store
        self.intent_engine = intent_engine
        
        # SQL generation patterns learned from successful queries
        self.learned_patterns = {}
        
        # Common SQL functions and their semantic mappings
        self.function_mappings = {
            "count": "COUNT",
            "sum": "SUM", 
            "average": "AVG",
            "mean": "AVG",
            "maximum": "MAX",
            "minimum": "MIN",
            "total": "SUM"
        }
        
        logger.info("SemanticQueryBuilder initialized")
    
    def build_sql_query(self, query_intent: QueryIntent) -> SQLQuery:
        """
        Build a complete SQL query using pattern-based approach similar to the original system.
        
        Args:
            query_intent: QueryIntent object with extracted semantic information
            
        Returns:
            SQLQuery object with generated SQL and metadata
        """
        logger.info(f"Building SQL query for intent: {query_intent.intent_type.value}")
        
        # Use pattern-based generation similar to the original fast_sql_generator
        sql = self._generate_pattern_based_sql(query_intent)
        
        if not sql:
            # Fallback to the original vector-based approach
            sql = self._generate_vector_based_sql(query_intent)
        
        # Parse the generated SQL to extract metadata
        tables_used = self._extract_tables_from_sql(sql)
        columns_used = self._extract_columns_from_sql(sql)
        
        # Calculate confidence based on pattern matching success
        confidence = 0.9 if "Error" not in sql else 0.3
        
        sql_query = SQLQuery(
            sql=sql,
            confidence=confidence,
            clauses=[],  # Simplified for pattern-based approach
            tables_used=tables_used,
            columns_used=columns_used,
            joins=[],
            complexity_score=0.5,
            generation_metadata={
                "intent_type": query_intent.intent_type.value,
                "generation_method": "pattern_based",
                "generation_timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"SQL query generated with confidence: {confidence:.3f}")
        return sql_query
    
    def _generate_pattern_based_sql(self, query_intent: QueryIntent) -> str:
        """
        Generate SQL using enhanced RAG-powered pattern-based approach.
        """
        query_lower = query_intent.original_query.lower().strip()
        
        # Step 1: Retrieve relevant context using RAG
        rag_context = self._retrieve_relevant_context(query_intent)
        
        # Step 2: Get schema metadata (enhanced with RAG context)
        schema_metadata = self._get_enhanced_schema_metadata(rag_context)
        
        if not schema_metadata:
            return "Error: No schema available"
        
        # Step 3: Generate SQL using advanced pattern matching with RAG enhancement
        
        # Check for advanced SQL patterns first
        advanced_sql = self._generate_advanced_sql_patterns(query_lower, query_intent, schema_metadata, rag_context)
        if advanced_sql:
            return advanced_sql
        
        # 1. Count queries
        if query_intent.intent_type == IntentType.COUNT or any(word in query_lower for word in ['count', 'how many', 'number of']):
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                # Use RAG context to determine if we need GROUP BY
                if self._should_group_by_from_context(query_lower, rag_context):
                    group_col = self._find_grouping_column(target_table, query_lower, rag_context)
                    if group_col:
                        return f"SELECT {group_col}, COUNT(*) as RecordCount FROM {target_table['schema']}.{target_table['table']} GROUP BY {group_col}"
                
                return f"SELECT COUNT(*) as RecordCount FROM {target_table['schema']}.{target_table['table']}"
        
        # 2. Aggregation queries (SUM, AVG, MAX, MIN)
        elif query_intent.intent_type in [IntentType.SUM, IntentType.AVERAGE, IntentType.MAX, IntentType.MIN]:
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                # Use RAG to find the best numeric column
                numeric_col = self._find_best_numeric_column(target_table, query_lower, rag_context)
                if numeric_col:
                    agg_func = query_intent.intent_type.value.upper()
                    if agg_func == "AVERAGE":
                        agg_func = "AVG"
                    
                    # Check if grouping is needed
                    if self._should_group_by_from_context(query_lower, rag_context):
                        group_col = self._find_grouping_column(target_table, query_lower, rag_context)
                        if group_col:
                            return f"SELECT {group_col}, {agg_func}({numeric_col}) FROM {target_table['schema']}.{target_table['table']} GROUP BY {group_col}"
                    
                    return f"SELECT {agg_func}({numeric_col}) FROM {target_table['schema']}.{target_table['table']}"
        
        # 3. List/Show queries
        elif query_intent.intent_type == IntentType.SELECT or any(word in query_lower for word in ['list', 'show', 'display', 'get']):
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                # Use RAG to select most relevant columns
                columns = self._select_relevant_columns(target_table, query_lower, rag_context)
                column_list = ', '.join(columns)
                
                sql = f"SELECT TOP 10 {column_list} FROM {target_table['schema']}.{target_table['table']}"
                
                # Add WHERE clause using RAG-enhanced entity matching
                where_conditions = self._build_rag_enhanced_where_clause(query_intent, target_table, rag_context)
                
                if where_conditions:
                    sql += " WHERE " + " AND ".join(where_conditions)
                
                return sql
        
        # Default fallback with RAG enhancement
        if schema_metadata:
            first_table = schema_metadata[0]
            columns = self._select_relevant_columns(first_table, query_lower, rag_context)
            column_list = ', '.join(columns)
            return f"SELECT TOP 10 {column_list} FROM {first_table['schema']}.{first_table['table']}"
        
        return "Error: Unable to generate SQL"
    
    def _retrieve_relevant_context(self, query_intent: QueryIntent) -> Dict[str, Any]:
        """
        Retrieve relevant context using RAG from vector store.
        """
        try:
            # Generate query vector
            query_vector = self.intent_engine.embedder.encode(query_intent.original_query)
            query_vector = self.intent_engine._normalize_vector(query_vector)
            
            # Retrieve similar schema elements
            similar_tables = self.vector_store.find_similar_tables(query_vector, k=3)
            similar_columns = self.vector_store.find_similar_columns(query_vector, k=10)
            
            # Get relationship context
            table_names = [table.table_name for table in similar_tables]
            relationships = self.vector_store.get_relationship_context(table_names)
            
            return {
                'similar_tables': similar_tables,
                'similar_columns': similar_columns,
                'relationships': relationships,
                'query_vector': query_vector,
                'semantic_context': self._extract_semantic_context(query_intent)
            }
            
        except Exception as e:
            logger.warning(f"RAG context retrieval failed: {e}")
            return {}
    
    def _get_enhanced_schema_metadata(self, rag_context: Dict[str, Any]) -> List[Dict]:
        """
        Get schema metadata enhanced with RAG context.
        """
        schema_metadata = []
        
        # Prioritize tables from RAG context
        if rag_context.get('similar_tables'):
            for table_match in rag_context['similar_tables']:
                table_vector = self.vector_store.retrieve_schema_vector(
                    f"table:{table_match.schema_name}.{table_match.table_name}"
                )
                if table_vector:
                    # Get columns for this table
                    table_columns = []
                    all_columns = self.vector_store.get_all_vectors_by_type("column")
                    for col_vector in all_columns:
                        if col_vector.metadata.get('table_name') == table_vector.element_name:
                            table_columns.append({
                                'name': col_vector.element_name,
                                'type': col_vector.metadata.get('data_type', 'varchar'),
                                'description': col_vector.metadata.get('description', ''),
                                'relevance_score': self._calculate_column_relevance(col_vector, rag_context)
                            })
                    
                    # Sort columns by relevance
                    table_columns.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                    
                    schema_metadata.append({
                        'schema': table_vector.schema_name,
                        'table': table_vector.element_name,
                        'columns': table_columns,
                        'description': table_vector.metadata.get('description', ''),
                        'relevance_score': table_match.similarity_score
                    })
        
        # Fallback to all tables if RAG context is empty
        if not schema_metadata:
            all_tables = self.vector_store.get_all_vectors_by_type("table")
            for table_vector in all_tables:
                table_columns = []
                all_columns = self.vector_store.get_all_vectors_by_type("column")
                for col_vector in all_columns:
                    if col_vector.metadata.get('table_name') == table_vector.element_name:
                        table_columns.append({
                            'name': col_vector.element_name,
                            'type': col_vector.metadata.get('data_type', 'varchar'),
                            'description': col_vector.metadata.get('description', '')
                        })
                
                schema_metadata.append({
                    'schema': table_vector.schema_name,
                    'table': table_vector.element_name,
                    'columns': table_columns,
                    'description': table_vector.metadata.get('description', '')
                })
        
        return schema_metadata
    
    def _calculate_column_relevance(self, col_vector, rag_context: Dict[str, Any]) -> float:
        """Calculate column relevance based on RAG context."""
        relevance = 0.0
        
        # Check if column appears in similar columns from RAG
        if rag_context.get('similar_columns'):
            for col_match in rag_context['similar_columns']:
                if col_match.column_name == col_vector.element_name:
                    relevance += col_match.similarity_score
        
        # Boost relevance for common important columns
        col_name_lower = col_vector.element_name.lower()
        if any(keyword in col_name_lower for keyword in ['name', 'title', 'description']):
            relevance += 0.3
        elif any(keyword in col_name_lower for keyword in ['id', 'key']):
            relevance += 0.1
        
        return relevance
    
    def _should_group_by_from_context(self, query_lower: str, rag_context: Dict[str, Any]) -> bool:
        """Determine if GROUP BY is needed based on context."""
        # Check for grouping keywords
        grouping_keywords = ['by', 'per', 'each', 'group', 'breakdown', 'department', 'category']
        return any(keyword in query_lower for keyword in grouping_keywords)
    
    def _find_grouping_column(self, table: Dict, query_lower: str, rag_context: Dict[str, Any]) -> Optional[str]:
        """Find the best column for GROUP BY using RAG context."""
        # Look for department-related grouping
        if 'department' in query_lower:
            for col in table['columns']:
                if 'department' in col['name'].lower():
                    return col['name']
        
        # Look for categorical columns
        for col in table['columns']:
            col_name_lower = col['name'].lower()
            if any(keyword in col_name_lower for keyword in ['type', 'category', 'status', 'group']):
                return col['name']
        
        return None
    
    def _find_best_numeric_column(self, table: Dict, query_lower: str, rag_context: Dict[str, Any]) -> Optional[str]:
        """Find the best numeric column using RAG context and query semantics."""
        # Check for salary-related queries
        if any(keyword in query_lower for keyword in ['salary', 'pay', 'wage', 'compensation']):
            for col in table['columns']:
                if 'salary' in col['name'].lower():
                    return col['name']
        
        # Check for hours-related queries
        if any(keyword in query_lower for keyword in ['hours', 'time', 'duration']):
            for col in table['columns']:
                if any(keyword in col['name'].lower() for keyword in ['hours', 'time', 'duration']):
                    return col['name']
        
        # Fallback to first numeric column
        return self._find_numeric_column(table)
    
    def _select_relevant_columns(self, table: Dict, query_lower: str, rag_context: Dict[str, Any]) -> List[str]:
        """Select most relevant columns using RAG context."""
        # If we have relevance scores, use them
        if table['columns'] and 'relevance_score' in table['columns'][0]:
            sorted_columns = sorted(table['columns'], key=lambda x: x.get('relevance_score', 0), reverse=True)
            return [col['name'] for col in sorted_columns[:3]]
        
        # Fallback to first few columns
        return [col['name'] for col in table['columns'][:3]]
    
    def _build_rag_enhanced_where_clause(self, query_intent: QueryIntent, table: Dict, rag_context: Dict[str, Any]) -> List[str]:
        """Build WHERE clause using RAG-enhanced entity matching."""
        where_conditions = []
        
        for entity in query_intent.entities:
            if entity.entity_type == EntityType.PERSON and len(entity.name) > 2:
                # Use RAG to find the best name column
                name_col = self._find_best_name_column(table, rag_context)
                if name_col:
                    where_conditions.append(f"{name_col} LIKE '%{entity.name}%'")
        
        return where_conditions
    
    def _find_best_name_column(self, table: Dict, rag_context: Dict[str, Any]) -> Optional[str]:
        """Find the best name column using RAG context."""
        # Check similar columns from RAG for name-related columns
        if rag_context.get('similar_columns'):
            for col_match in rag_context['similar_columns']:
                if col_match.table_name == table['table'] and 'name' in col_match.column_name.lower():
                    return col_match.column_name
        
        # Fallback to keyword matching
        return self._find_name_column(table)
    
    def _extract_semantic_context(self, query_intent: QueryIntent) -> Dict[str, Any]:
        """Extract semantic context from query intent."""
        return {
            'intent_type': query_intent.intent_type.value,
            'complexity': query_intent.complexity_level.value,
            'has_temporal': query_intent.temporal_context is not None,
            'has_aggregation': query_intent.aggregation_type is not None,
            'entity_types': [entity.entity_type.value for entity in query_intent.entities]
        }
    
    def _generate_advanced_sql_patterns(self, query_lower: str, query_intent: QueryIntent, 
                                       schema_metadata: List[Dict], rag_context: Dict[str, Any]) -> Optional[str]:
        """
        Generate advanced SQL patterns including CTEs, window functions, conditional logic, etc.
        """
        
        # 1. Window Functions (ROW_NUMBER, RANK, DENSE_RANK, etc.)
        window_sql = self._generate_window_function_sql(query_lower, query_intent, schema_metadata, rag_context)
        if window_sql:
            return window_sql
        
        # 2. CTEs (Common Table Expressions)
        cte_sql = self._generate_cte_sql(query_lower, query_intent, schema_metadata, rag_context)
        if cte_sql:
            return cte_sql
        
        # 3. Conditional Logic (CASE WHEN, IIF)
        conditional_sql = self._generate_conditional_sql(query_lower, query_intent, schema_metadata, rag_context)
        if conditional_sql:
            return conditional_sql
        
        # 4. Advanced Date Functions
        date_sql = self._generate_advanced_date_sql(query_lower, query_intent, schema_metadata, rag_context)
        if date_sql:
            return date_sql
        
        # 5. String Functions
        string_sql = self._generate_string_function_sql(query_lower, query_intent, schema_metadata, rag_context)
        if string_sql:
            return string_sql
        
        # 6. Subqueries and EXISTS
        subquery_sql = self._generate_subquery_sql(query_lower, query_intent, schema_metadata, rag_context)
        if subquery_sql:
            return subquery_sql
        
        return None
    
    def _generate_window_function_sql(self, query_lower: str, query_intent: QueryIntent, 
                                     schema_metadata: List[Dict], rag_context: Dict[str, Any]) -> Optional[str]:
        """Generate SQL with window functions for ranking, running totals, etc."""
        
        # Ranking queries
        ranking_keywords = ['top', 'rank', 'ranking', 'highest', 'lowest', 'best', 'worst', 'first', 'last']
        if any(keyword in query_lower for keyword in ranking_keywords):
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                # Determine ranking column
                rank_col = self._find_ranking_column(target_table, query_lower, rag_context)
                if rank_col:
                    # Determine partition column if needed
                    partition_col = self._find_partition_column(target_table, query_lower, rag_context)
                    
                    # Select relevant columns
                    columns = self._select_relevant_columns(target_table, query_lower, rag_context)
                    column_list = ', '.join(columns)
                    
                    # Build window function
                    if 'dense' in query_lower:
                        window_func = "DENSE_RANK()"
                    elif any(word in query_lower for word in ['rank', 'ranking']):
                        window_func = "RANK()"
                    else:
                        window_func = "ROW_NUMBER()"
                    
                    # Build OVER clause
                    over_clause = f"ORDER BY {rank_col}"
                    if 'lowest' in query_lower or 'worst' in query_lower:
                        over_clause += " ASC"
                    else:
                        over_clause += " DESC"
                    
                    if partition_col:
                        over_clause = f"PARTITION BY {partition_col} " + over_clause
                    
                    return f"""SELECT {column_list}, {window_func} OVER ({over_clause}) as Ranking
FROM {target_table['schema']}.{target_table['table']}"""
        
        # Running totals / cumulative sums
        if any(phrase in query_lower for phrase in ['running total', 'cumulative', 'running sum']):
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                numeric_col = self._find_best_numeric_column(target_table, query_lower, rag_context)
                date_col = self._find_date_column(target_table)
                
                if numeric_col and date_col:
                    columns = self._select_relevant_columns(target_table, query_lower, rag_context)
                    column_list = ', '.join(columns)
                    
                    return f"""SELECT {column_list}, 
       SUM({numeric_col}) OVER (ORDER BY {date_col} ROWS UNBOUNDED PRECEDING) as RunningTotal
FROM {target_table['schema']}.{target_table['table']}
ORDER BY {date_col}"""
        
        # LAG/LEAD for previous/next values
        if any(phrase in query_lower for phrase in ['previous', 'prior', 'last', 'next', 'following']):
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                numeric_col = self._find_best_numeric_column(target_table, query_lower, rag_context)
                date_col = self._find_date_column(target_table)
                
                if numeric_col and date_col:
                    lag_or_lead = "LAG" if any(word in query_lower for word in ['previous', 'prior', 'last']) else "LEAD"
                    
                    return f"""SELECT *, 
       {lag_or_lead}({numeric_col}) OVER (ORDER BY {date_col}) as {lag_or_lead.title()}Value
FROM {target_table['schema']}.{target_table['table']}
ORDER BY {date_col}"""
        
        return None
    
    def _generate_cte_sql(self, query_lower: str, query_intent: QueryIntent, 
                         schema_metadata: List[Dict], rag_context: Dict[str, Any]) -> Optional[str]:
        """Generate SQL with CTEs for complex multi-step queries."""
        
        # Multi-step analysis keywords
        cte_keywords = ['step by step', 'first find', 'then calculate', 'breakdown', 'analysis']
        complex_aggregation = any(phrase in query_lower for phrase in ['total by', 'average by', 'breakdown by'])
        
        if any(keyword in query_lower for keyword in cte_keywords) or complex_aggregation:
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                # Example: "Show me total hours by employee and then rank them"
                if 'rank' in query_lower and any(word in query_lower for word in ['total', 'sum']):
                    numeric_col = self._find_best_numeric_column(target_table, query_lower, rag_context)
                    group_col = self._find_grouping_column(target_table, query_lower, rag_context)
                    
                    if numeric_col and group_col:
                        return f"""WITH EmployeeTotals AS (
    SELECT {group_col}, SUM({numeric_col}) as TotalValue
    FROM {target_table['schema']}.{target_table['table']}
    GROUP BY {group_col}
)
SELECT {group_col}, TotalValue,
       RANK() OVER (ORDER BY TotalValue DESC) as Ranking
FROM EmployeeTotals
ORDER BY Ranking"""
                
                # Example: "Show me departments with more than average employees"
                if 'more than average' in query_lower or 'above average' in query_lower:
                    group_col = self._find_grouping_column(target_table, query_lower, rag_context)
                    
                    if group_col:
                        return f"""WITH DepartmentCounts AS (
    SELECT {group_col}, COUNT(*) as EmployeeCount
    FROM {target_table['schema']}.{target_table['table']}
    GROUP BY {group_col}
),
AverageCount AS (
    SELECT AVG(CAST(EmployeeCount AS FLOAT)) as AvgCount
    FROM DepartmentCounts
)
SELECT dc.{group_col}, dc.EmployeeCount
FROM DepartmentCounts dc
CROSS JOIN AverageCount ac
WHERE dc.EmployeeCount > ac.AvgCount
ORDER BY dc.EmployeeCount DESC"""
        
        return None
    
    def _generate_conditional_sql(self, query_lower: str, query_intent: QueryIntent, 
                                 schema_metadata: List[Dict], rag_context: Dict[str, Any]) -> Optional[str]:
        """Generate SQL with conditional logic (CASE WHEN, IIF)."""
        
        # CASE WHEN patterns
        case_keywords = ['if', 'when', 'case', 'depending on', 'based on', 'categorize', 'classify']
        if any(keyword in query_lower for keyword in case_keywords):
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                columns = self._select_relevant_columns(target_table, query_lower, rag_context)
                column_list = ', '.join(columns)
                
                # Salary categorization example
                if 'salary' in query_lower and any(word in query_lower for word in ['high', 'low', 'category']):
                    salary_col = self._find_best_numeric_column(target_table, query_lower, rag_context)
                    if salary_col:
                        return f"""SELECT {column_list},
       CASE 
           WHEN {salary_col} >= 100000 THEN 'High'
           WHEN {salary_col} >= 50000 THEN 'Medium'
           ELSE 'Low'
       END as SalaryCategory
FROM {target_table['schema']}.{target_table['table']}"""
                
                # Status-based categorization
                status_col = self._find_status_column(target_table)
                if status_col:
                    return f"""SELECT {column_list},
       CASE 
           WHEN {status_col} = 'Active' THEN 'Current'
           WHEN {status_col} = 'Inactive' THEN 'Former'
           ELSE 'Unknown'
       END as EmployeeStatus
FROM {target_table['schema']}.{target_table['table']}"""
        
        return None
    
    def _generate_advanced_date_sql(self, query_lower: str, query_intent: QueryIntent, 
                                   schema_metadata: List[Dict], rag_context: Dict[str, Any]) -> Optional[str]:
        """Generate SQL with advanced date functions."""
        
        # Date calculation patterns
        date_calc_keywords = ['days ago', 'months ago', 'years ago', 'since', 'between dates', 'age', 'tenure']
        if any(keyword in query_lower for keyword in date_calc_keywords):
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                date_col = self._find_date_column(target_table)
                if date_col:
                    columns = self._select_relevant_columns(target_table, query_lower, rag_context)
                    column_list = ', '.join(columns)
                    
                    # Tenure/Age calculation
                    if any(word in query_lower for word in ['tenure', 'age', 'how long']):
                        return f"""SELECT {column_list},
       DATEDIFF(YEAR, {date_col}, GETDATE()) as YearsOfService,
       DATEDIFF(MONTH, {date_col}, GETDATE()) as MonthsOfService
FROM {target_table['schema']}.{target_table['table']}
WHERE {date_col} IS NOT NULL"""
                    
                    # Recent records (last N days/months)
                    if 'last' in query_lower:
                        if 'month' in query_lower:
                            return f"""SELECT {column_list}
FROM {target_table['schema']}.{target_table['table']}
WHERE {date_col} >= DATEADD(MONTH, -1, GETDATE())
ORDER BY {date_col} DESC"""
                        elif 'week' in query_lower:
                            return f"""SELECT {column_list}
FROM {target_table['schema']}.{target_table['table']}
WHERE {date_col} >= DATEADD(WEEK, -1, GETDATE())
ORDER BY {date_col} DESC"""
                        else:  # Default to days
                            return f"""SELECT {column_list}
FROM {target_table['schema']}.{target_table['table']}
WHERE {date_col} >= DATEADD(DAY, -30, GETDATE())
ORDER BY {date_col} DESC"""
        
        return None
    
    def _generate_string_function_sql(self, query_lower: str, query_intent: QueryIntent, 
                                     schema_metadata: List[Dict], rag_context: Dict[str, Any]) -> Optional[str]:
        """Generate SQL with string functions."""
        
        # String manipulation patterns
        string_keywords = ['contains', 'starts with', 'ends with', 'length', 'substring', 'first name', 'last name']
        if any(keyword in query_lower for keyword in string_keywords):
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                name_col = self._find_name_column(target_table)
                if name_col:
                    columns = self._select_relevant_columns(target_table, query_lower, rag_context)
                    column_list = ', '.join(columns)
                    
                    # Extract first/last name
                    if 'first name' in query_lower or 'last name' in query_lower:
                        return f"""SELECT {column_list},
       LEFT({name_col}, CHARINDEX(' ', {name_col} + ' ') - 1) as FirstName,
       LTRIM(SUBSTRING({name_col}, CHARINDEX(' ', {name_col} + ' '), LEN({name_col}))) as LastName
FROM {target_table['schema']}.{target_table['table']}
WHERE {name_col} IS NOT NULL"""
                    
                    # String length
                    if 'length' in query_lower:
                        return f"""SELECT {column_list}, LEN({name_col}) as NameLength
FROM {target_table['schema']}.{target_table['table']}
WHERE {name_col} IS NOT NULL"""
                    
                    # Contains pattern
                    if 'contains' in query_lower:
                        # Extract the search term (simplified)
                        search_term = "Smith"  # This would need more sophisticated extraction
                        return f"""SELECT {column_list}
FROM {target_table['schema']}.{target_table['table']}
WHERE {name_col} LIKE '%{search_term}%'"""
        
        return None
    
    def _generate_subquery_sql(self, query_lower: str, query_intent: QueryIntent, 
                              schema_metadata: List[Dict], rag_context: Dict[str, Any]) -> Optional[str]:
        """Generate SQL with subqueries and EXISTS clauses."""
        
        # Subquery patterns
        subquery_keywords = ['who also', 'that have', 'exists', 'not in', 'in the list', 'among', 'except']
        if any(keyword in query_lower for keyword in subquery_keywords):
            target_table = self._find_best_table_for_query(query_lower, schema_metadata)
            if target_table:
                columns = self._select_relevant_columns(target_table, query_lower, rag_context)
                column_list = ', '.join(columns)
                
                # EXISTS pattern
                if 'exists' in query_lower or 'who also' in query_lower:
                    # This would need more sophisticated relationship detection
                    return f"""SELECT {column_list}
FROM {target_table['schema']}.{target_table['table']} e
WHERE EXISTS (
    SELECT 1 FROM {target_table['schema']}.projects p 
    WHERE p.employee_id = e.id
)"""
                
                # NOT IN pattern
                if 'not in' in query_lower or 'except' in query_lower:
                    return f"""SELECT {column_list}
FROM {target_table['schema']}.{target_table['table']} e
WHERE e.id NOT IN (
    SELECT employee_id FROM {target_table['schema']}.projects 
    WHERE employee_id IS NOT NULL
)"""
        
        return None
    
    # Helper methods for advanced SQL generation
    def _find_ranking_column(self, table: Dict, query_lower: str, rag_context: Dict[str, Any]) -> Optional[str]:
        """Find the best column for ranking/ordering."""
        # Check for salary ranking
        if 'salary' in query_lower:
            for col in table['columns']:
                if 'salary' in col['name'].lower():
                    return col['name']
        
        # Check for date ranking
        if any(word in query_lower for word in ['recent', 'latest', 'newest', 'oldest']):
            date_col = self._find_date_column(table)
            if date_col:
                return date_col
        
        # Default to first numeric column
        return self._find_numeric_column(table)
    
    def _find_partition_column(self, table: Dict, query_lower: str, rag_context: Dict[str, Any]) -> Optional[str]:
        """Find column for PARTITION BY in window functions."""
        if 'by department' in query_lower:
            for col in table['columns']:
                if 'department' in col['name'].lower():
                    return col['name']
        return None
    
    def _find_date_column(self, table: Dict) -> Optional[str]:
        """Find a date column in the table."""
        date_indicators = ['date', 'time', 'created', 'updated', 'hire', 'start']
        for col in table['columns']:
            col_name_lower = col['name'].lower()
            if any(indicator in col_name_lower for indicator in date_indicators):
                return col['name']
        return None
    
    def _find_status_column(self, table: Dict) -> Optional[str]:
        """Find a status column in the table."""
        status_indicators = ['status', 'state', 'active', 'enabled']
        for col in table['columns']:
            col_name_lower = col['name'].lower()
            if any(indicator in col_name_lower for indicator in status_indicators):
                return col['name']
        return None
    
    def _find_best_table_for_query(self, query_lower: str, schema_metadata: List[Dict]) -> Optional[Dict]:
        """Find the best table match using hybrid approach: semantic search + keyword matching."""
        
        # Step 1: Use vector similarity search for semantic understanding
        semantic_matches = self._find_tables_by_semantic_similarity(query_lower)
        
        # Step 2: Use keyword matching as fallback/boost
        keyword_matches = self._find_tables_by_keywords(query_lower, schema_metadata)
        
        # Step 3: Combine scores for hybrid ranking
        combined_scores = {}
        
        # Add semantic scores
        for table_name, semantic_score in semantic_matches.items():
            combined_scores[table_name] = semantic_score * 0.6  # 60% weight for semantics
        
        # Add keyword scores
        for table_name, keyword_score in keyword_matches.items():
            if table_name in combined_scores:
                combined_scores[table_name] += keyword_score * 0.4  # 40% weight for keywords
            else:
                combined_scores[table_name] = keyword_score * 0.4
        
        # Find best match
        if combined_scores:
            best_table_name = max(combined_scores.keys(), key=lambda k: combined_scores[k])
            
            # Return the table metadata
            for table in schema_metadata:
                if f"{table['schema']}.{table['table']}" == best_table_name or table['table'] == best_table_name:
                    return table
        
        # Fallback to first table
        return schema_metadata[0] if schema_metadata else None
    
    def _find_tables_by_semantic_similarity(self, query: str) -> Dict[str, float]:
        """Use vector store to find semantically similar tables."""
        try:
            # Generate query vector
            query_vector = self.intent_engine.embedder.encode(query)
            query_vector = self.intent_engine._normalize_vector(query_vector)
            
            # Find similar tables using vector similarity
            similar_tables = self.vector_store.find_similar_tables(query_vector, k=5)
            
            semantic_scores = {}
            for table_match in similar_tables:
                table_key = f"{table_match.schema_name}.{table_match.table_name}"
                # Combine similarity, context relevance, and business priority
                combined_score = (
                    table_match.similarity_score * 0.5 +
                    table_match.context_relevance * 0.3 +
                    table_match.business_priority * 0.2
                )
                semantic_scores[table_key] = combined_score
            
            return semantic_scores
            
        except Exception as e:
            logger.warning(f"Semantic table search failed: {e}")
            return {}
    
    def _find_tables_by_keywords(self, query_lower: str, schema_metadata: List[Dict]) -> Dict[str, float]:
        """Find tables using keyword matching with expanded vocabulary."""
        # Enhanced table keywords mapping with more synonyms
        table_keywords = {
            'employee': ['employee', 'employees', 'staff', 'worker', 'workers', 'person', 'people', 
                        'personnel', 'team member', 'colleague', 'user', 'individual'],
            'project': ['project', 'projects', 'initiative', 'program', 'assignment', 'work', 'job'],
            'client': ['client', 'clients', 'customer', 'customers', 'account', 'company', 'organization'],
            'department': ['department', 'departments', 'dept', 'division', 'unit', 'team', 'group'],
            'timesheet': ['timesheet', 'timesheets', 'time sheet', 'time entry', 'hours', 'time tracking'],
            'leave': ['leave', 'vacation', 'holiday', 'time off', 'absence', 'pto', 'sick leave'],
            'activity': ['activity', 'activities', 'task', 'tasks', 'action', 'work item']
        }
        
        keyword_scores = {}
        
        for table in schema_metadata:
            score = 0
            table_name_lower = table['table'].lower()
            table_key = f"{table['schema']}.{table['table']}"
            
            # Direct table name match (highest score)
            if table_name_lower in query_lower:
                score += 10
            
            # Keyword-based matching
            for table_type, keywords in table_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    if table_type in table_name_lower:
                        score += 8
                    elif any(keyword in table_name_lower for keyword in keywords):
                        score += 6
            
            # Partial name matching
            for word in query_lower.split():
                if len(word) > 2 and word in table_name_lower:
                    score += 2
            
            # Check table description if available
            if 'description' in table and table['description']:
                desc_lower = table['description'].lower()
                for word in query_lower.split():
                    if len(word) > 3 and word in desc_lower:
                        score += 1
            
            if score > 0:
                keyword_scores[table_key] = score / 10.0  # Normalize to 0-1 range
        
        return keyword_scores
    
    def _find_numeric_column(self, table: Dict) -> Optional[str]:
        """Find a numeric column in the table."""
        numeric_types = ['int', 'integer', 'decimal', 'float', 'numeric', 'money']
        for col in table['columns']:
            if any(num_type in col['type'].lower() for num_type in numeric_types):
                return col['name']
        return None
    
    def _find_name_column(self, table: Dict) -> Optional[str]:
        """Find a name column in the table."""
        name_indicators = ['name', 'title', 'description']
        for col in table['columns']:
            if any(indicator in col['name'].lower() for indicator in name_indicators):
                return col['name']
        return None
    
    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """Extract table names from SQL."""
        tables = []
        # Simple regex to find table references
        table_pattern = r'FROM\s+(\w+\.\w+|\w+)'
        matches = re.findall(table_pattern, sql, re.IGNORECASE)
        tables.extend(matches)
        
        join_pattern = r'JOIN\s+(\w+\.\w+|\w+)'
        matches = re.findall(join_pattern, sql, re.IGNORECASE)
        tables.extend(matches)
        
        return list(set(tables))
    
    def _extract_columns_from_sql(self, sql: str) -> List[str]:
        """Extract column names from SQL."""
        columns = []
        # Simple approach - this could be enhanced
        if "SELECT *" in sql.upper():
            columns.append("*")
        else:
            # Extract column names between SELECT and FROM
            select_pattern = r'SELECT\s+(.*?)\s+FROM'
            match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)
            if match:
                column_part = match.group(1)
                # Split by comma and clean up
                cols = [col.strip() for col in column_part.split(',')]
                columns.extend(cols)
        
        return columns
    
    def _generate_vector_based_sql(self, query_intent: QueryIntent) -> str:
        """Fallback to original vector-based approach."""
        # This is the original complex approach - keep as fallback
        try:
            # Initialize SQL clauses
            clauses = []
            tables_used = []
            columns_used = []
            joins = []
            
            # Step 1: Determine relevant tables using vector similarity
            relevant_tables = self._select_tables_from_intent(query_intent)
            tables_used.extend([table.table_name for table in relevant_tables])
            
            # Step 2: Determine relevant columns using vector similarity
            relevant_columns = self._select_columns_from_intent(query_intent, relevant_tables)
            columns_used.extend([f"{col.table_name}.{col.column_name}" for col in relevant_columns])
            
            # Step 3: Build SELECT clause based on intent
            select_clause = self._build_select_clause(query_intent, relevant_columns)
            clauses.append(select_clause)
            
            # Step 4: Build FROM clause with primary table
            from_clause = self._build_from_clause(relevant_tables)
            clauses.append(from_clause)
            
            # Step 5: Build JOIN clauses if multiple tables are needed
            if len(relevant_tables) > 1:
                join_clauses, join_conditions = self._build_join_clauses(relevant_tables, query_intent)
                clauses.extend(join_clauses)
                joins.extend(join_conditions)
            
            # Step 6: Build WHERE clause from entities (but filter out query words)
            where_clause = self._build_where_clause(query_intent, relevant_columns)
            if where_clause:
                clauses.append(where_clause)
            
            # Step 7: Build GROUP BY clause if aggregation is needed
            if query_intent.aggregation_type:
                group_by_clause = self._build_group_by_clause(query_intent, relevant_columns)
                if group_by_clause:
                    clauses.append(group_by_clause)
            
            # Step 8: Build ORDER BY clause based on intent
            order_by_clause = self._build_order_by_clause(query_intent, relevant_columns)
            if order_by_clause:
                clauses.append(order_by_clause)
            
            # Step 9: Combine clauses into final SQL
            sql = self._combine_clauses(clauses)
            return sql
            
        except Exception as e:
            logger.error(f"Vector-based SQL generation failed: {e}")
            return "Error: Unable to generate SQL"
    
    def _select_tables_from_intent(self, query_intent: QueryIntent) -> List[TableMatch]:
        """
        Select relevant tables using vector similarity with query intent.
        
        Args:
            query_intent: QueryIntent object
            
        Returns:
            List of relevant TableMatch objects
        """
        # Use query vector to find similar tables
        similar_tables = self.vector_store.find_similar_tables(
            query_intent.query_vector, 
            k=5
        )
        
        # Filter tables based on entity mappings and confidence
        relevant_tables = []
        entity_table_names = set()
        
        # Collect table names from entity schema mappings
        for entity in query_intent.entities:
            if entity.schema_mapping and entity.schema_mapping.table:
                entity_table_names.add(entity.schema_mapping.table)
        
        # Look for key terms in the original query to guide table selection
        query_lower = query_intent.original_query.lower()
        
        # Prioritize tables mentioned in entities or matching query terms
        for table in similar_tables:
            # Check if table name appears in query
            table_name_match = table.table_name.lower() in query_lower
            
            # Check for semantic matches
            semantic_match = False
            if "employee" in query_lower and "employee" in table.table_name.lower():
                semantic_match = True
            elif "project" in query_lower and "project" in table.table_name.lower():
                semantic_match = True
            elif "department" in query_lower and "department" in table.table_name.lower():
                semantic_match = True
            
            if table.table_name in entity_table_names:
                table.business_priority += 0.4  # Boost priority for entity-mapped tables
                relevant_tables.append(table)
            elif table_name_match or semantic_match:
                table.business_priority += 0.3  # Boost for query term matches
                relevant_tables.append(table)
            elif table.similarity_score > 0.4:  # Higher threshold for relevance
                relevant_tables.append(table)
        
        # Ensure we have at least one table
        if not relevant_tables and similar_tables:
            relevant_tables.append(similar_tables[0])
        
        # Sort by combined relevance score
        relevant_tables.sort(
            key=lambda x: (x.similarity_score * 0.3 + x.context_relevance * 0.3 + x.business_priority * 0.4),
            reverse=True
        )
        
        # For simple aggregation queries, prefer single table
        simple_aggregation_patterns = [
            'how many', 'count all', 'show all', 'list all', 'get all',
            'what is the average', 'what is the total', 'what is the sum'
        ]
        
        query_lower = query_intent.original_query.lower()
        is_simple_aggregation = any(pattern in query_lower for pattern in simple_aggregation_patterns)
        
        if is_simple_aggregation or query_intent.complexity_level == ComplexityLevel.SIMPLE:
            return relevant_tables[:1]
        
        # Limit to most relevant tables (max 2 for better SQL quality)
        return relevant_tables[:2]
    
    def _select_columns_from_intent(self, 
                                   query_intent: QueryIntent, 
                                   relevant_tables: List[TableMatch]) -> List[ColumnMatch]:
        """
        Select relevant columns using vector similarity and intent analysis.
        
        Args:
            query_intent: QueryIntent object
            relevant_tables: List of relevant tables
            
        Returns:
            List of relevant ColumnMatch objects
        """
        relevant_columns = []
        
        # Get columns for each relevant table
        for table in relevant_tables:
            table_columns = self.vector_store.find_similar_columns(
                query_intent.query_vector,
                table_context=table.table_name,
                k=10
            )
            
            # Filter columns based on intent type and entities
            for column in table_columns:
                if self._is_column_relevant_to_intent(column, query_intent):
                    relevant_columns.append(column)
        
        # Add columns from entity mappings
        for entity in query_intent.entities:
            if entity.schema_mapping and entity.schema_mapping.column:
                # Find the specific column mentioned in entity mapping
                entity_columns = self.vector_store.find_similar_columns(
                    query_intent.query_vector,
                    table_context=entity.schema_mapping.table,
                    k=5
                )
                
                for column in entity_columns:
                    if column.column_name == entity.schema_mapping.column:
                        column.context_relevance += 0.4  # Boost for entity-mapped columns
                        relevant_columns.append(column)
        
        # Remove duplicates and sort by relevance
        unique_columns = self._deduplicate_columns(relevant_columns)
        unique_columns.sort(
            key=lambda x: (x.similarity_score * 0.6 + x.context_relevance * 0.4),
            reverse=True
        )
        
        return unique_columns
    
    def _is_column_relevant_to_intent(self, column: ColumnMatch, query_intent: QueryIntent) -> bool:
        """
        Determine if a column is relevant to the query intent.
        
        Args:
            column: ColumnMatch object
            query_intent: QueryIntent object
            
        Returns:
            True if column is relevant, False otherwise
        """
        # Base relevance from similarity score
        if column.similarity_score < 0.2:
            return False
        
        # Intent-specific relevance
        if query_intent.intent_type in [IntentType.COUNT, IntentType.SUM, IntentType.AVERAGE, IntentType.MAX, IntentType.MIN]:
            # For aggregation queries, prefer numeric columns
            if column.data_type.lower() in ['int', 'integer', 'decimal', 'float', 'numeric', 'money']:
                return True
            # Also include ID columns for counting
            if 'id' in column.column_name.lower() and query_intent.intent_type == IntentType.COUNT:
                return True
        
        # For SELECT queries, include high-similarity columns
        if query_intent.intent_type == IntentType.SELECT and column.similarity_score > 0.3:
            return True
        
        # Include columns mentioned in entities
        for entity in query_intent.entities:
            if entity.schema_mapping and entity.schema_mapping.column == column.column_name:
                return True
        
        # Include columns with high context relevance
        if column.context_relevance > 0.4:
            return True
        
        return False
    
    def _deduplicate_columns(self, columns: List[ColumnMatch]) -> List[ColumnMatch]:
        """Remove duplicate columns based on table and column name."""
        seen = set()
        unique_columns = []
        
        for column in columns:
            key = (column.table_name, column.column_name)
            if key not in seen:
                unique_columns.append(column)
                seen.add(key)
        
        return unique_columns
    
    def _build_select_clause(self, query_intent: QueryIntent, columns: List[ColumnMatch]) -> SQLClause:
        """
        Build SELECT clause based on intent and relevant columns.
        
        Args:
            query_intent: QueryIntent object
            columns: List of relevant columns
            
        Returns:
            SQLClause for SELECT
        """
        select_parts = []
        confidence = 0.8  # Base confidence
        
        # Handle aggregation intents
        if query_intent.aggregation_type:
            agg_function = query_intent.aggregation_type.function
            
            if query_intent.intent_type == IntentType.COUNT:
                # For COUNT, prefer ID columns or use COUNT(*)
                id_columns = [col for col in columns if 'id' in col.column_name.lower()]
                if id_columns:
                    select_parts.append(f"COUNT({id_columns[0].table_name}.{id_columns[0].column_name})")
                else:
                    select_parts.append("COUNT(*)")
            
            elif query_intent.intent_type in [IntentType.SUM, IntentType.AVERAGE, IntentType.MAX, IntentType.MIN]:
                # Find numeric columns for aggregation
                numeric_columns = [
                    col for col in columns 
                    if col.data_type.lower() in ['int', 'integer', 'decimal', 'float', 'numeric', 'money']
                ]
                
                if numeric_columns:
                    # Use the most relevant numeric column
                    target_column = numeric_columns[0]
                    select_parts.append(f"{agg_function}({target_column.table_name}.{target_column.column_name})")
                else:
                    # Fallback to first available column
                    if columns:
                        target_column = columns[0]
                        select_parts.append(f"{agg_function}({target_column.table_name}.{target_column.column_name})")
                    confidence *= 0.6  # Lower confidence for fallback
            
            # Add GROUP BY columns to SELECT if needed
            if query_intent.aggregation_type.group_by_columns:
                for group_col in query_intent.aggregation_type.group_by_columns:
                    # Find matching column
                    matching_cols = [col for col in columns if col.column_name == group_col]
                    if matching_cols:
                        col = matching_cols[0]
                        select_parts.append(f"{col.table_name}.{col.column_name}")
        
        else:
            # For non-aggregation queries, select relevant columns
            if query_intent.intent_type == IntentType.SELECT:
                # Select top relevant columns (limit to avoid overly complex queries)
                top_columns = columns[:5]
                for column in top_columns:
                    select_parts.append(f"{column.table_name}.{column.column_name}")
            
            # If no specific columns, select key columns
            if not select_parts:
                # Look for common key columns
                key_columns = [
                    col for col in columns 
                    if any(keyword in col.column_name.lower() 
                          for keyword in ['name', 'title', 'id', 'description'])
                ]
                
                if key_columns:
                    for column in key_columns[:3]:
                        select_parts.append(f"{column.table_name}.{column.column_name}")
                elif columns:
                    # Fallback to first few columns
                    for column in columns[:3]:
                        select_parts.append(f"{column.table_name}.{column.column_name}")
                    confidence *= 0.7
        
        # Default fallback
        if not select_parts:
            select_parts.append("*")
            confidence *= 0.5
        
        select_content = "SELECT " + ", ".join(select_parts)
        
        return SQLClause(
            clause_type=SQLClauseType.SELECT,
            content=select_content,
            confidence=confidence,
            metadata={"column_count": len(select_parts)}
        )
    
    def _build_from_clause(self, tables: List[TableMatch]) -> SQLClause:
        """
        Build FROM clause with the primary table.
        
        Args:
            tables: List of relevant tables
            
        Returns:
            SQLClause for FROM
        """
        if not tables:
            return SQLClause(
                clause_type=SQLClauseType.FROM,
                content="FROM unknown_table",
                confidence=0.1,
                metadata={"error": "No tables found"}
            )
        
        # Use the most relevant table as primary
        primary_table = tables[0]
        from_content = f"FROM {primary_table.schema_name}.{primary_table.table_name}"
        
        return SQLClause(
            clause_type=SQLClauseType.FROM,
            content=from_content,
            confidence=primary_table.similarity_score,
            metadata={"primary_table": primary_table.table_name}
        )
    
    def _build_join_clauses(self, 
                           tables: List[TableMatch], 
                           query_intent: QueryIntent) -> Tuple[List[SQLClause], List[JoinCondition]]:
        """
        Build JOIN clauses for multiple tables using relationship analysis.
        
        Args:
            tables: List of relevant tables
            query_intent: QueryIntent object
            
        Returns:
            Tuple of (join_clauses, join_conditions)
        """
        join_clauses = []
        join_conditions = []
        
        if len(tables) < 2:
            return join_clauses, join_conditions
        
        # Get relationship context between tables
        table_names = [table.table_name for table in tables]
        relationship_graph = self.vector_store.get_relationship_context(table_names)
        
        # Build joins based on relationships
        primary_table = tables[0]
        
        for i in range(1, len(tables)):
            secondary_table = tables[i]
            
            # Find relationship between primary and secondary table
            join_condition = self._find_join_condition(
                primary_table, secondary_table, relationship_graph, query_intent
            )
            
            if join_condition:
                # Determine join type based on intent
                join_type = self._determine_join_type(query_intent, join_condition)
                join_condition.join_type = join_type
                
                # Create JOIN clause
                join_content = (
                    f"{join_type.value} {secondary_table.schema_name}.{secondary_table.table_name} "
                    f"ON {primary_table.table_name}.{join_condition.left_column} = "
                    f"{secondary_table.table_name}.{join_condition.right_column}"
                )
                
                join_clause = SQLClause(
                    clause_type=SQLClauseType.JOIN,
                    content=join_content,
                    confidence=join_condition.confidence,
                    metadata={
                        "left_table": primary_table.table_name,
                        "right_table": secondary_table.table_name,
                        "join_type": join_type.value
                    }
                )
                
                join_clauses.append(join_clause)
                join_conditions.append(join_condition)
        
        return join_clauses, join_conditions
    
    def _find_join_condition(self, 
                            table1: TableMatch, 
                            table2: TableMatch, 
                            relationship_graph: RelationshipGraph,
                            query_intent: QueryIntent) -> Optional[JoinCondition]:
        """
        Find the best join condition between two tables.
        
        Args:
            table1: First table
            table2: Second table
            relationship_graph: Relationship context
            query_intent: Query intent for context
            
        Returns:
            JoinCondition or None if no suitable join found
        """
        # Look for explicit relationships in the graph
        for edge in relationship_graph.edges:
            if ((edge.source_table == table1.table_name and edge.target_table == table2.table_name) or
                (edge.source_table == table2.table_name and edge.target_table == table1.table_name)):
                
                # Extract join columns from relationship metadata
                left_col = edge.metadata.get('source_column', 'id')
                right_col = edge.metadata.get('target_column', f"{table1.table_name}_id")
                
                return JoinCondition(
                    left_table=table1.table_name,
                    right_table=table2.table_name,
                    left_column=left_col,
                    right_column=right_col,
                    join_type=JoinType.INNER,  # Will be determined later
                    confidence=edge.confidence
                )
        
        # Improved fallback: Look for realistic foreign key patterns
        # Common patterns for employee/project/department relationships
        if table1.table_name == "employees" and table2.table_name == "projects":
            return JoinCondition(
                left_table="employees",
                right_table="projects", 
                left_column="id",
                right_column="employee_id",
                join_type=JoinType.INNER,
                confidence=0.8
            )
        elif table1.table_name == "projects" and table2.table_name == "employees":
            return JoinCondition(
                left_table="employees",
                right_table="projects",
                left_column="id", 
                right_column="employee_id",
                join_type=JoinType.INNER,
                confidence=0.8
            )
        elif table1.table_name == "employees" and table2.table_name == "departments":
            return JoinCondition(
                left_table="employees",
                right_table="departments",
                left_column="department_id",
                right_column="id", 
                join_type=JoinType.INNER,
                confidence=0.8
            )
        elif table1.table_name == "departments" and table2.table_name == "employees":
            return JoinCondition(
                left_table="employees", 
                right_table="departments",
                left_column="department_id",
                right_column="id",
                join_type=JoinType.INNER,
                confidence=0.8
            )
        
        # Generic fallback patterns
        common_patterns = [
            ("id", f"{table2.table_name.rstrip('s')}_id"),  # employees.id = projects.employee_id
            (f"{table1.table_name.rstrip('s')}_id", "id")   # projects.employee_id = employees.id
        ]
        
        for left_pattern, right_pattern in common_patterns:
            return JoinCondition(
                left_table=table1.table_name,
                right_table=table2.table_name,
                left_column=left_pattern,
                right_column=right_pattern,
                join_type=JoinType.INNER,
                confidence=0.6  # Medium confidence for pattern-based joins
            )
        
        return None
    
    def _determine_join_type(self, query_intent: QueryIntent, join_condition: JoinCondition) -> JoinType:
        """
        Determine the appropriate join type based on query intent.
        
        Args:
            query_intent: QueryIntent object
            join_condition: JoinCondition object
            
        Returns:
            Appropriate JoinType
        """
        # Default to INNER JOIN for most cases
        if query_intent.intent_type in [IntentType.COUNT, IntentType.SUM, IntentType.AVERAGE]:
            # For aggregations, INNER JOIN is usually preferred to avoid nulls
            return JoinType.INNER
        
        # For SELECT queries, consider LEFT JOIN to include all records from primary table
        if query_intent.intent_type == IntentType.SELECT:
            return JoinType.LEFT
        
        # Default fallback
        return JoinType.INNER
    
    def _build_where_clause(self, query_intent: QueryIntent, columns: List[ColumnMatch]) -> Optional[SQLClause]:
        """
        Build WHERE clause from extracted entities.
        
        Args:
            query_intent: QueryIntent object
            columns: List of relevant columns
            
        Returns:
            SQLClause for WHERE or None if no conditions needed
        """
        where_conditions = []
        confidence = 0.8
        
        # Only process meaningful entities for WHERE conditions
        # Filter out common query words and table names
        skip_words = {
            'show', 'me', 'all', 'get', 'find', 'list', 'display', 'what', 'how', 'many',
            'count', 'total', 'sum', 'average', 'max', 'min', 'is', 'the', 'are', 'there',
            'of', 'with', 'by', 'from', 'to', 'in', 'on', 'at', 'for', 'and', 'or',
            'employees', 'employee', 'department', 'departments', 'project', 'projects',
            'salary', 'salaries', 'name', 'names', 'information', 'info', 'data'
        }
        
        meaningful_entities = [
            entity for entity in query_intent.entities
            if entity.entity_type in [EntityType.PERSON, EntityType.PROJECT, EntityType.DEPARTMENT, 
                                     EntityType.STATUS, EntityType.DATE, EntityType.NUMBER] and
            entity.name.lower() not in skip_words and
            len(entity.name) > 2 and  # Skip very short words
            not entity.name.lower().startswith(('what', 'how', 'show', 'get', 'find'))
        ]
        
        # Process meaningful entities to create WHERE conditions
        for entity in meaningful_entities:
            condition = self._create_condition_from_entity(entity, columns, query_intent)
            if condition:
                where_conditions.append(condition)
        
        # Process temporal context
        if query_intent.temporal_context:
            temporal_condition = self._create_temporal_condition(
                query_intent.temporal_context, columns
            )
            if temporal_condition:
                where_conditions.append(temporal_condition)
        
        # For simple queries like "How many employees are there?", don't add WHERE clause
        simple_query_patterns = [
            'how many', 'count all', 'show all', 'list all', 'get all',
            'what is the average', 'what is the total', 'what is the sum'
        ]
        
        query_lower = query_intent.original_query.lower()
        is_simple_query = any(pattern in query_lower for pattern in simple_query_patterns)
        
        if is_simple_query and not meaningful_entities:
            return None
        
        if not where_conditions:
            return None
        
        where_content = "WHERE " + " AND ".join(where_conditions)
        
        return SQLClause(
            clause_type=SQLClauseType.WHERE,
            content=where_content,
            confidence=confidence,
            metadata={"condition_count": len(where_conditions)}
        )
    
    def _create_condition_from_entity(self, 
                                     entity: Entity, 
                                     columns: List[ColumnMatch],
                                     query_intent: QueryIntent) -> Optional[str]:
        """
        Create a WHERE condition from an entity.
        
        Args:
            entity: Entity object
            columns: List of available columns
            query_intent: QueryIntent for context
            
        Returns:
            SQL condition string or None
        """
        # Skip entities that are not suitable for WHERE conditions
        if entity.entity_type in [EntityType.UNKNOWN]:
            return None
        
        # Skip common query words that shouldn't become WHERE conditions
        skip_words = {
            'show', 'me', 'all', 'get', 'find', 'list', 'display', 'what', 'how', 'many',
            'count', 'total', 'sum', 'average', 'max', 'min', 'is', 'the', 'are', 'there',
            'of', 'with', 'by', 'from', 'to', 'in', 'on', 'at', 'for', 'and', 'or'
        }
        
        if entity.name.lower() in skip_words:
            return None
        
        # Only create conditions for meaningful entities
        if entity.entity_type not in [EntityType.PERSON, EntityType.PROJECT, EntityType.DEPARTMENT, 
                                     EntityType.STATUS, EntityType.DATE, EntityType.NUMBER]:
            return None
        
        # Find the best column to match this entity
        target_column = None
        
        # First, check if entity has explicit schema mapping
        if entity.schema_mapping and entity.schema_mapping.column:
            matching_cols = [
                col for col in columns 
                if col.column_name == entity.schema_mapping.column and 
                   col.table_name == entity.schema_mapping.table
            ]
            if matching_cols:
                target_column = matching_cols[0]
        
        # If no explicit mapping, find best matching column by type
        if not target_column:
            target_column = self._find_best_column_for_entity(entity, columns)
        
        if not target_column:
            return None
        
        # Create condition based on entity type
        if entity.entity_type == EntityType.PERSON:
            # For person names, use LIKE for partial matching
            return f"{target_column.table_name}.{target_column.column_name} LIKE '%{entity.name}%'"
        
        elif entity.entity_type == EntityType.NUMBER:
            # For numbers, use exact match or comparison
            if self._is_numeric_column(target_column):
                return f"{target_column.table_name}.{target_column.column_name} = {entity.name}"
        
        elif entity.entity_type in [EntityType.PROJECT, EntityType.DEPARTMENT, EntityType.STATUS]:
            # For categorical entities, use LIKE for flexibility
            return f"{target_column.table_name}.{target_column.column_name} LIKE '%{entity.name}%'"
        
        elif entity.entity_type == EntityType.DATE:
            # For dates, create appropriate date conditions
            return self._create_date_condition(entity, target_column)
        
        return None  # Don't create generic conditions
    
    def _find_best_column_for_entity(self, entity: Entity, columns: List[ColumnMatch]) -> Optional[ColumnMatch]:
        """
        Find the best column to match an entity based on semantic similarity.
        
        Args:
            entity: Entity object
            columns: List of available columns
            
        Returns:
            Best matching ColumnMatch or None
        """
        if not columns:
            return None
        
        # Score columns based on entity type and column characteristics
        scored_columns = []
        
        for column in columns:
            score = 0.0
            column_name_lower = column.column_name.lower()
            
            # Type-specific scoring
            if entity.entity_type == EntityType.PERSON:
                if any(keyword in column_name_lower for keyword in ['name', 'employee', 'user', 'person']):
                    score += 0.8
                elif 'id' in column_name_lower and 'employee' in column_name_lower:
                    score += 0.6
            
            elif entity.entity_type == EntityType.PROJECT:
                if any(keyword in column_name_lower for keyword in ['project', 'task', 'assignment']):
                    score += 0.8
            
            elif entity.entity_type == EntityType.DATE:
                if any(keyword in column_name_lower for keyword in ['date', 'time', 'created', 'updated']):
                    score += 0.8
            
            elif entity.entity_type == EntityType.NUMBER:
                if column.data_type.lower() in ['int', 'integer', 'decimal', 'float', 'numeric']:
                    score += 0.7
            
            # Add base similarity score
            score += column.similarity_score * 0.3
            
            if score > 0:
                scored_columns.append((column, score))
        
        if not scored_columns:
            return columns[0]  # Fallback to first column
        
        # Return column with highest score
        scored_columns.sort(key=lambda x: x[1], reverse=True)
        return scored_columns[0][0]
    
    def _is_numeric_column(self, column: ColumnMatch) -> bool:
        """Check if a column contains numeric data."""
        return column.data_type.lower() in ['int', 'integer', 'decimal', 'float', 'numeric', 'money']
    
    def _create_date_condition(self, entity: Entity, column: ColumnMatch) -> str:
        """
        Create a date-based WHERE condition.
        
        Args:
            entity: Date entity
            column: Target column
            
        Returns:
            SQL date condition
        """
        # Simple date matching - could be enhanced with proper date parsing
        if entity.name.isdigit() and len(entity.name) == 4:
            # Year matching
            return f"YEAR({column.table_name}.{column.column_name}) = {entity.name}"
        else:
            # General date string matching
            return f"{column.table_name}.{column.column_name} LIKE '%{entity.name}%'"
    
    def _create_temporal_condition(self, 
                                  temporal_context: TemporalContext, 
                                  columns: List[ColumnMatch]) -> Optional[str]:
        """
        Create temporal WHERE conditions from temporal context.
        
        Args:
            temporal_context: TemporalContext object
            columns: List of available columns
            
        Returns:
            SQL temporal condition or None
        """
        # Find date/time columns
        date_columns = [
            col for col in columns
            if any(keyword in col.column_name.lower() 
                  for keyword in ['date', 'time', 'created', 'updated', 'modified'])
        ]
        
        if not date_columns:
            return None
        
        # Use the first date column found
        date_column = date_columns[0]
        column_ref = f"{date_column.table_name}.{date_column.column_name}"
        
        # Handle relative time references
        if temporal_context.relative:
            time_ref = temporal_context.time_reference.lower()
            
            if "last month" in time_ref:
                return f"{column_ref} >= DATEADD(month, -1, GETDATE())"
            elif "this year" in time_ref:
                return f"YEAR({column_ref}) = YEAR(GETDATE())"
            elif "last year" in time_ref:
                return f"YEAR({column_ref}) = YEAR(GETDATE()) - 1"
            else:
                # Generic recent time filter
                return f"{column_ref} >= DATEADD(day, -30, GETDATE())"
        
        # Handle absolute dates
        else:
            if temporal_context.time_reference.isdigit() and len(temporal_context.time_reference) == 4:
                # Year filter
                return f"YEAR({column_ref}) = {temporal_context.time_reference}"
        
        return None
    
    def _build_group_by_clause(self, 
                              query_intent: QueryIntent, 
                              columns: List[ColumnMatch]) -> Optional[SQLClause]:
        """
        Build GROUP BY clause for aggregation queries.
        
        Args:
            query_intent: QueryIntent object
            columns: List of relevant columns
            
        Returns:
            SQLClause for GROUP BY or None
        """
        if not query_intent.aggregation_type:
            return None
        
        group_by_columns = []
        query_lower = query_intent.original_query.lower()
        
        # Check if query explicitly mentions grouping
        if 'by department' in query_lower:
            # Find department-related columns
            dept_columns = [
                col for col in columns
                if 'department' in col.column_name.lower() or col.table_name.lower() == 'departments'
            ]
            if dept_columns:
                # Prefer department name over ID
                name_cols = [col for col in dept_columns if 'name' in col.column_name.lower()]
                if name_cols:
                    col = name_cols[0]
                    group_by_columns.append(f"{col.table_name}.{col.column_name}")
                else:
                    col = dept_columns[0]
                    group_by_columns.append(f"{col.table_name}.{col.column_name}")
        
        # If explicit group by columns are specified
        elif query_intent.aggregation_type.group_by_columns:
            for group_col in query_intent.aggregation_type.group_by_columns:
                matching_cols = [col for col in columns if col.column_name == group_col]
                if matching_cols:
                    col = matching_cols[0]
                    group_by_columns.append(f"{col.table_name}.{col.column_name}")
        
        # Auto-detect group by columns based on non-numeric columns in SELECT
        else:
            # Look for categorical columns that would make sense for grouping
            categorical_columns = [
                col for col in columns
                if not self._is_numeric_column(col) and
                   any(keyword in col.column_name.lower() 
                       for keyword in ['name', 'type', 'status', 'category', 'department'])
            ]
            
            # Add first categorical column for grouping
            if categorical_columns:
                col = categorical_columns[0]
                group_by_columns.append(f"{col.table_name}.{col.column_name}")
        
        if not group_by_columns:
            return None
        
        group_by_content = "GROUP BY " + ", ".join(group_by_columns)
        
        return SQLClause(
            clause_type=SQLClauseType.GROUP_BY,
            content=group_by_content,
            confidence=0.7,
            metadata={"group_columns": group_by_columns}
        )
    
    def _build_order_by_clause(self, 
                              query_intent: QueryIntent, 
                              columns: List[ColumnMatch]) -> Optional[SQLClause]:
        """
        Build ORDER BY clause based on query context.
        
        Args:
            query_intent: QueryIntent object
            columns: List of relevant columns
            
        Returns:
            SQLClause for ORDER BY or None
        """
        order_by_parts = []
        
        # Check for ordering keywords in the original query
        query_lower = query_intent.original_query.lower()
        
        # Determine sort direction
        sort_direction = "ASC"
        if any(keyword in query_lower for keyword in ['highest', 'most', 'top', 'maximum', 'descending']):
            sort_direction = "DESC"
        elif any(keyword in query_lower for keyword in ['lowest', 'least', 'bottom', 'minimum', 'ascending']):
            sort_direction = "ASC"
        
        # For aggregation queries, order by the aggregated value
        if query_intent.aggregation_type:
            if query_intent.intent_type in [IntentType.COUNT, IntentType.SUM, IntentType.AVERAGE, IntentType.MAX, IntentType.MIN]:
                # Order by the aggregated column (first column in SELECT typically)
                order_by_parts.append(f"1 {sort_direction}")  # Order by first column
        
        # For regular SELECT queries, order by relevant columns
        else:
            # Look for name or date columns for natural ordering
            name_columns = [col for col in columns if 'name' in col.column_name.lower()]
            date_columns = [col for col in columns if any(keyword in col.column_name.lower() 
                                                         for keyword in ['date', 'created', 'updated'])]
            
            if name_columns:
                col = name_columns[0]
                order_by_parts.append(f"{col.table_name}.{col.column_name} {sort_direction}")
            elif date_columns:
                col = date_columns[0]
                order_by_parts.append(f"{col.table_name}.{col.column_name} DESC")  # Recent first for dates
        
        if not order_by_parts:
            return None
        
        order_by_content = "ORDER BY " + ", ".join(order_by_parts)
        
        return SQLClause(
            clause_type=SQLClauseType.ORDER_BY,
            content=order_by_content,
            confidence=0.6,
            metadata={"sort_direction": sort_direction}
        )
    
    def _combine_clauses(self, clauses: List[SQLClause]) -> str:
        """
        Combine SQL clauses into a complete SQL query.
        
        Args:
            clauses: List of SQLClause objects
            
        Returns:
            Complete SQL query string
        """
        # Order clauses according to SQL syntax
        clause_order = {
            SQLClauseType.SELECT: 0,
            SQLClauseType.FROM: 1,
            SQLClauseType.JOIN: 2,
            SQLClauseType.WHERE: 3,
            SQLClauseType.GROUP_BY: 4,
            SQLClauseType.HAVING: 5,
            SQLClauseType.ORDER_BY: 6
        }
        
        # Sort clauses by SQL order
        sorted_clauses = sorted(clauses, key=lambda x: clause_order.get(x.clause_type, 999))
        
        # Combine clause contents
        sql_parts = []
        for clause in sorted_clauses:
            sql_parts.append(clause.content)
        
        return "\n".join(sql_parts)
    
    def _calculate_query_confidence(self, clauses: List[SQLClause], query_intent: QueryIntent) -> float:
        """
        Calculate overall confidence score for the generated query.
        
        Args:
            clauses: List of SQL clauses
            query_intent: Original query intent
            
        Returns:
            Confidence score between 0 and 1
        """
        if not clauses:
            return 0.0
        
        # Average confidence of all clauses
        clause_confidences = [clause.confidence for clause in clauses]
        avg_clause_confidence = sum(clause_confidences) / len(clause_confidences)
        
        # Boost confidence based on intent clarity
        intent_boost = query_intent.confidence * 0.2
        
        # Penalty for high complexity
        complexity_penalty = 0.0
        if query_intent.complexity_level == ComplexityLevel.VERY_COMPLEX:
            complexity_penalty = 0.2
        elif query_intent.complexity_level == ComplexityLevel.COMPLEX:
            complexity_penalty = 0.1
        
        final_confidence = avg_clause_confidence + intent_boost - complexity_penalty
        return max(0.0, min(1.0, final_confidence))
    
    def _calculate_complexity_score(self, clauses: List[SQLClause], joins: List[JoinCondition]) -> float:
        """
        Calculate complexity score for the generated query.
        
        Args:
            clauses: List of SQL clauses
            joins: List of join conditions
            
        Returns:
            Complexity score
        """
        complexity = 0.0
        
        # Base complexity from clause count
        complexity += len(clauses) * 0.1
        
        # Add complexity for joins
        complexity += len(joins) * 0.3
        
        # Add complexity for aggregations
        has_aggregation = any(
            'COUNT' in clause.content or 'SUM' in clause.content or 
            'AVG' in clause.content or 'MAX' in clause.content or 'MIN' in clause.content
            for clause in clauses
        )
        if has_aggregation:
            complexity += 0.2
        
        # Add complexity for GROUP BY
        has_group_by = any(clause.clause_type == SQLClauseType.GROUP_BY for clause in clauses)
        if has_group_by:
            complexity += 0.2
        
        return complexity


class DynamicSQLGenerator:
    """
    Main SQL generator class that orchestrates vector-guided SQL creation.
    
    This class uses semantic understanding to generate SQL queries without
    relying on hardcoded patterns or templates.
    """
    
    def __init__(self, 
                 vector_store: VectorSchemaStore,
                 intent_engine: SemanticIntentEngine):
        """
        Initialize the DynamicSQLGenerator.
        
        Args:
            vector_store: VectorSchemaStore for schema context
            intent_engine: SemanticIntentEngine for query understanding
        """
        self.vector_store = vector_store
        self.intent_engine = intent_engine
        self.query_builder = SemanticQueryBuilder(vector_store, intent_engine)
        
        # Track generation statistics
        self.generation_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "average_confidence": 0.0,
            "complexity_distribution": {}
        }
        
        logger.info("DynamicSQLGenerator initialized")
    
    def generate_sql(self, nl_query: str) -> SQLQuery:
        """
        Generate SQL query from natural language input.
        
        Args:
            nl_query: Natural language query string
            
        Returns:
            SQLQuery object with generated SQL and metadata
        """
        logger.info(f"Generating SQL for query: {nl_query}")
        
        # Step 1: Analyze query intent
        query_intent = self.intent_engine.analyze_query(nl_query)
        
        # Step 2: Generate SQL using semantic query builder
        sql_query = self.query_builder.build_sql_query(query_intent)
        
        # Step 3: Update statistics
        self._update_generation_stats(sql_query)
        
        logger.info(f"SQL generation complete. Confidence: {sql_query.confidence:.3f}")
        return sql_query
    
    def _update_generation_stats(self, sql_query: SQLQuery):
        """Update generation statistics."""
        self.generation_stats["total_queries"] += 1
        
        if sql_query.confidence > 0.7:
            self.generation_stats["successful_queries"] += 1
        
        # Update average confidence
        total = self.generation_stats["total_queries"]
        current_avg = self.generation_stats["average_confidence"]
        new_avg = ((current_avg * (total - 1)) + sql_query.confidence) / total
        self.generation_stats["average_confidence"] = new_avg
        
        # Update complexity distribution
        complexity_key = f"complexity_{sql_query.complexity_score:.1f}"
        self.generation_stats["complexity_distribution"][complexity_key] = \
            self.generation_stats["complexity_distribution"].get(complexity_key, 0) + 1
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get current generation statistics."""
        return self.generation_stats.copy()
    
    def learn_from_query(self, nl_query: str, sql_query: str, success: bool, feedback: str = None):
        """
        Learn from query execution results to improve future generation.
        
        Args:
            nl_query: Original natural language query
            sql_query: Generated SQL query
            success: Whether the query executed successfully
            feedback: Optional feedback about the query
        """
        # This would be implemented to store successful patterns
        # and learn from failures for continuous improvement
        logger.info(f"Learning from query result: success={success}")
        
        # Store in vector store for future reference
        if hasattr(self.vector_store, 'learn_from_query'):
            self.vector_store.learn_from_query(nl_query, sql_query, success)