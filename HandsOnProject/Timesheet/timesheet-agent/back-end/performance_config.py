#!/usr/bin/env python3
"""
Performance Configuration - Settings for query performance optimization.
"""

# Query execution timeouts (in seconds)
QUERY_TIMEOUT_DEFAULT = 30
QUERY_TIMEOUT_COMPLEX = 60
QUERY_TIMEOUT_SIMPLE = 10

# Performance thresholds
SLOW_QUERY_THRESHOLD = 5.0  # seconds
VERY_SLOW_QUERY_THRESHOLD = 15.0  # seconds

# Result set limits
DEFAULT_TOP_LIMIT = 1000
MAX_RESULT_SET_SIZE = 10000

# Validation settings
ENABLE_PERFORMANCE_WARNINGS = True
ENABLE_QUERY_OPTIMIZATION = True
BLOCK_DANGEROUS_QUERIES = True

# Cache settings
ENABLE_QUERY_CACHING = True
CACHE_TTL_SECONDS = 300  # 5 minutes

# Monitoring settings
LOG_SLOW_QUERIES = True
LOG_FAILED_QUERIES = True
PERFORMANCE_METRICS_ENABLED = True

# Auto-optimization settings
AUTO_ADD_TOP_CLAUSE = True
AUTO_ADD_QUERY_TIMEOUT = True
AUTO_OPTIMIZE_JOINS = False  # Disabled by default as it's experimental

# Schema validation settings
STRICT_SCHEMA_VALIDATION = True
ALLOW_FUZZY_MATCHING = True
FUZZY_MATCH_THRESHOLD = 0.7

def get_performance_config():
    """Get current performance configuration"""
    return {
        'timeouts': {
            'default': QUERY_TIMEOUT_DEFAULT,
            'complex': QUERY_TIMEOUT_COMPLEX,
            'simple': QUERY_TIMEOUT_SIMPLE
        },
        'thresholds': {
            'slow_query': SLOW_QUERY_THRESHOLD,
            'very_slow_query': VERY_SLOW_QUERY_THRESHOLD
        },
        'limits': {
            'default_top': DEFAULT_TOP_LIMIT,
            'max_result_set': MAX_RESULT_SET_SIZE
        },
        'features': {
            'performance_warnings': ENABLE_PERFORMANCE_WARNINGS,
            'query_optimization': ENABLE_QUERY_OPTIMIZATION,
            'query_caching': ENABLE_QUERY_CACHING,
            'auto_optimization': {
                'add_top_clause': AUTO_ADD_TOP_CLAUSE,
                'add_timeout': AUTO_ADD_QUERY_TIMEOUT,
                'optimize_joins': AUTO_OPTIMIZE_JOINS
            }
        }
    }