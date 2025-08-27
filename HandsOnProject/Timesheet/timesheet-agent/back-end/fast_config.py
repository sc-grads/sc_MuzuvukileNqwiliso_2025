#!/usr/bin/env python3
"""
Fast Configuration - Performance optimization settings for the RAG SQL Agent
"""

from performance_optimizer import PerformanceConfig

# Performance optimization levels
PERFORMANCE_LEVELS = {
    'maximum_speed': PerformanceConfig(
        # Aggressive caching for maximum speed
        enable_aggressive_caching=True,
        cache_ttl_seconds=7200,  # 2 hours
        max_cache_entries=20000,
        
        # Maximum parallel processing
        max_workers=8,
        enable_parallel_processing=True,
        
        # Aggressive lazy loading
        enable_lazy_loading=True,
        lazy_load_threshold_ms=50,
        
        # Fast query optimization
        enable_query_optimization=True,
        max_query_timeout=15,  # Shorter timeout for speed
        
        # Extended schema caching
        enable_schema_caching=True,
        schema_cache_ttl=14400,  # 4 hours
        
        # Large vector cache
        enable_vector_caching=True,
        vector_cache_size=10000,
        
        # Aggressive LLM caching
        enable_llm_caching=True,
        llm_cache_size=2000,
        llm_timeout=10  # Shorter LLM timeout
    ),
    
    'balanced': PerformanceConfig(
        # Balanced caching
        enable_aggressive_caching=True,
        cache_ttl_seconds=3600,  # 1 hour
        max_cache_entries=10000,
        
        # Moderate parallel processing
        max_workers=4,
        enable_parallel_processing=True,
        
        # Standard lazy loading
        enable_lazy_loading=True,
        lazy_load_threshold_ms=100,
        
        # Standard query optimization
        enable_query_optimization=True,
        max_query_timeout=30,
        
        # Standard schema caching
        enable_schema_caching=True,
        schema_cache_ttl=7200,  # 2 hours
        
        # Moderate vector cache
        enable_vector_caching=True,
        vector_cache_size=5000,
        
        # Standard LLM caching
        enable_llm_caching=True,
        llm_cache_size=1000,
        llm_timeout=15
    ),
    
    'conservative': PerformanceConfig(
        # Conservative caching
        enable_aggressive_caching=True,
        cache_ttl_seconds=1800,  # 30 minutes
        max_cache_entries=5000,
        
        # Limited parallel processing
        max_workers=2,
        enable_parallel_processing=True,
        
        # Conservative lazy loading
        enable_lazy_loading=True,
        lazy_load_threshold_ms=200,
        
        # Basic query optimization
        enable_query_optimization=True,
        max_query_timeout=45,
        
        # Conservative schema caching
        enable_schema_caching=True,
        schema_cache_ttl=3600,  # 1 hour
        
        # Small vector cache
        enable_vector_caching=True,
        vector_cache_size=2000,
        
        # Conservative LLM caching
        enable_llm_caching=True,
        llm_cache_size=500,
        llm_timeout=20
    )
}

# Default performance level
DEFAULT_PERFORMANCE_LEVEL = 'maximum_speed'

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    'development': PERFORMANCE_LEVELS['balanced'],
    'testing': PERFORMANCE_LEVELS['conservative'],
    'production': PERFORMANCE_LEVELS['maximum_speed']
}

def get_performance_config(level: str = None, environment: str = None) -> PerformanceConfig:
    """
    Get performance configuration based on level or environment.
    
    Args:
        level: Performance level ('maximum_speed', 'balanced', 'conservative')
        environment: Environment ('development', 'testing', 'production')
        
    Returns:
        PerformanceConfig instance
    """
    if environment and environment in ENVIRONMENT_CONFIGS:
        return ENVIRONMENT_CONFIGS[environment]
    
    if level and level in PERFORMANCE_LEVELS:
        return PERFORMANCE_LEVELS[level]
    
    return PERFORMANCE_LEVELS[DEFAULT_PERFORMANCE_LEVEL]

def get_recommended_config() -> PerformanceConfig:
    """Get recommended configuration for current system"""
    import os
    import psutil
    
    # Get system resources
    cpu_count = os.cpu_count() or 4
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Adjust configuration based on system resources
    if memory_gb >= 16 and cpu_count >= 8:
        # High-end system
        config = PERFORMANCE_LEVELS['maximum_speed']
        config.max_workers = min(cpu_count, 8)
        config.max_cache_entries = 20000
        config.vector_cache_size = 10000
        
    elif memory_gb >= 8 and cpu_count >= 4:
        # Mid-range system
        config = PERFORMANCE_LEVELS['balanced']
        config.max_workers = min(cpu_count, 4)
        config.max_cache_entries = 10000
        config.vector_cache_size = 5000
        
    else:
        # Low-end system
        config = PERFORMANCE_LEVELS['conservative']
        config.max_workers = min(cpu_count, 2)
        config.max_cache_entries = 5000
        config.vector_cache_size = 2000
    
    return config

# Performance monitoring settings
MONITORING_CONFIG = {
    'enable_performance_logging': True,
    'log_slow_queries': True,
    'slow_query_threshold': 5.0,  # seconds
    'enable_metrics_collection': True,
    'metrics_retention_days': 7,
    'enable_performance_alerts': True,
    'alert_threshold_seconds': 10.0
}

# Cache warming settings
CACHE_WARMING_CONFIG = {
    'enable_cache_warming': True,
    'warm_on_startup': True,
    'common_queries': [
        "show me all employees",
        "how many projects are there",
        "what is the total hours",
        "list all clients",
        "show timesheet entries",
        "count active projects"
    ],
    'warm_schema_on_startup': True,
    'warm_intent_patterns': True
}

def get_monitoring_config() -> dict:
    """Get performance monitoring configuration"""
    return MONITORING_CONFIG.copy()

def get_cache_warming_config() -> dict:
    """Get cache warming configuration"""
    return CACHE_WARMING_CONFIG.copy()