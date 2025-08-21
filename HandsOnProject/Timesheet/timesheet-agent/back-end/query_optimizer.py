#!/usr/bin/env python3
"""
Simple Query Optimizer - Basic SQL query optimization utilities.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def optimize_sql_query(sql_query: str, performance_hints: Optional[Dict] = None) -> str:
    """
    Apply basic optimizations to SQL queries.
    
    Args:
        sql_query: Original SQL query
        performance_hints: Optional performance hints from validation
        
    Returns:
        Optimized SQL query
    """
    optimized = sql_query.strip()
    
    # 1. Add TOP clause if missing and no WHERE clause
    if not re.search(r'\bTOP\s+\d+', optimized, re.IGNORECASE):
        if not re.search(r'\bWHERE\b', optimized, re.IGNORECASE):
            # Add TOP 1000 for queries without WHERE clause
            optimized = re.sub(
                r'(\bSELECT\b)\s+',
                r'\1 TOP 1000 ',
                optimized,
                count=1,
                flags=re.IGNORECASE
            )
            logger.info("Added TOP 1000 clause for performance")
    
    # 2. Add query timeout for complex queries
    if not re.search(r'\bOPTION\b', optimized, re.IGNORECASE):
        # Check if query is complex (multiple JOINs, subqueries, etc.)
        complexity_indicators = [
            len(re.findall(r'\bJOIN\b', optimized, re.IGNORECASE)),
            len(re.findall(r'\bSELECT\b', optimized, re.IGNORECASE)) - 1,  # Subqueries
            len(re.findall(r'\bUNION\b', optimized, re.IGNORECASE))
        ]
        
        if sum(complexity_indicators) > 2:  # Complex query
            optimized += " OPTION (QUERY_TIMEOUT 30)"
            logger.info("Added query timeout for complex query")
    
    # 3. Optimize JOIN order (basic heuristic)
    optimized = _optimize_join_order(optimized)
    
    return optimized


def _optimize_join_order(sql_query: str) -> str:
    """
    Basic JOIN order optimization.
    This is a simplified version - production systems would use cost-based optimization.
    """
    # For now, just ensure we're using explicit JOIN syntax
    # Replace old-style comma joins with explicit JOINs where possible
    
    # This is a placeholder for more sophisticated JOIN optimization
    return sql_query


def add_performance_hints(sql_query: str, table_sizes: Optional[Dict[str, int]] = None) -> str:
    """
    Add SQL Server performance hints based on estimated table sizes.
    
    Args:
        sql_query: Original SQL query
        table_sizes: Optional dictionary of table names to estimated row counts
        
    Returns:
        SQL query with performance hints
    """
    if not table_sizes:
        return sql_query
    
    # Add FORCESEEK hint for small tables
    # Add FORCESCAN hint for large tables without good WHERE clauses
    # This is a simplified implementation
    
    return sql_query


def estimate_query_cost(sql_query: str) -> Dict[str, any]:
    """
    Estimate query execution cost based on query structure.
    
    Returns:
        Dictionary with cost estimates and recommendations
    """
    sql_upper = sql_query.upper()
    
    cost_factors = {
        'base_cost': 1.0,
        'join_cost': len(re.findall(r'\bJOIN\b', sql_upper)) * 2.0,
        'subquery_cost': (len(re.findall(r'\bSELECT\b', sql_upper)) - 1) * 3.0,
        'aggregation_cost': len(re.findall(r'\b(COUNT|SUM|AVG|MIN|MAX)\b', sql_upper)) * 1.5,
        'sorting_cost': len(re.findall(r'\bORDER BY\b', sql_upper)) * 2.0,
        'grouping_cost': len(re.findall(r'\bGROUP BY\b', sql_upper)) * 2.0
    }
    
    total_cost = sum(cost_factors.values())
    
    # Generate recommendations based on cost
    recommendations = []
    if cost_factors['join_cost'] > 6.0:
        recommendations.append("Consider reducing number of JOINs or breaking into smaller queries")
    
    if cost_factors['subquery_cost'] > 9.0:
        recommendations.append("Consider using CTEs instead of nested subqueries")
    
    if 'WHERE' not in sql_upper:
        recommendations.append("Add WHERE clause to filter results")
        total_cost *= 2.0  # Penalty for full table scans
    
    if 'TOP' not in sql_upper and 'WHERE' not in sql_upper:
        recommendations.append("Add TOP clause to limit result set")
    
    return {
        'estimated_cost': total_cost,
        'cost_level': 'low' if total_cost < 5 else 'medium' if total_cost < 15 else 'high',
        'cost_factors': cost_factors,
        'recommendations': recommendations
    }


def suggest_indexes(sql_query: str) -> List[str]:
    """
    Suggest indexes that might improve query performance.
    
    Returns:
        List of index suggestions
    """
    suggestions = []
    
    # Extract WHERE clause columns
    where_columns = re.findall(r'WHERE\s+.*?(\w+)\s*[=<>]', sql_query, re.IGNORECASE)
    for col in where_columns:
        suggestions.append(f"Consider index on column: {col}")
    
    # Extract JOIN columns
    join_columns = re.findall(r'ON\s+\w+\.(\w+)\s*=\s*\w+\.(\w+)', sql_query, re.IGNORECASE)
    for col1, col2 in join_columns:
        suggestions.append(f"Consider indexes on JOIN columns: {col1}, {col2}")
    
    # Extract ORDER BY columns
    order_columns = re.findall(r'ORDER BY\s+(\w+)', sql_query, re.IGNORECASE)
    for col in order_columns:
        suggestions.append(f"Consider index on ORDER BY column: {col}")
    
    return suggestions[:5]  # Limit to top 5 suggestions