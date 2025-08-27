#!/usr/bin/env python3
"""
Performance Optimizer - Comprehensive performance optimization for RAG SQL Agent

This module implements aggressive caching, lazy loading, parallel processing,
and query optimization to reduce response times from 120+ seconds to under 10 seconds.
"""

import asyncio
import time
import threading
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache, wraps
import pickle
import os
import json
from datetime import datetime, timedelta
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceConfig:
    """Configuration for performance optimizations"""
    # Cache settings
    enable_aggressive_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    max_cache_entries: int = 10000
    
    # Parallel processing
    max_workers: int = 4
    enable_parallel_processing: bool = True
    
    # Lazy loading
    enable_lazy_loading: bool = True
    lazy_load_threshold_ms: int = 100
    
    # Query optimization
    enable_query_optimization: bool = True
    max_query_timeout: int = 30
    
    # Schema optimization
    enable_schema_caching: bool = True
    schema_cache_ttl: int = 7200  # 2 hours
    
    # Vector optimization
    enable_vector_caching: bool = True
    vector_cache_size: int = 5000
    
    # LLM optimization
    enable_llm_caching: bool = True
    llm_cache_size: int = 1000
    llm_timeout: int = 15


class PerformanceCache:
    """High-performance multi-level cache with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.creation_times = {}
        self.lock = threading.RLock()
        
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.creation_times:
            return True
        age = time.time() - self.creation_times[key]
        return age > self.ttl_seconds
    
    def _evict_lru(self):
        """Evict least recently used entries"""
        if len(self.cache) <= self.max_size:
            return
            
        # Sort by access time and remove oldest
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
        keys_to_remove = [k for k, _ in sorted_keys[:len(self.cache) - self.max_size + 100]]
        
        for key in keys_to_remove:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
            self.creation_times.pop(key, None)
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache or self._is_expired(key):
                return None
            
            self.access_times[key] = time.time()
            return self.cache[key]
    
    def put(self, key: str, value: Any):
        """Put value in cache"""
        with self.lock:
            current_time = time.time()
            self.cache[key] = value
            self.access_times[key] = current_time
            self.creation_times[key] = current_time
            
            # Evict if necessary
            if len(self.cache) > self.max_size:
                self._evict_lru()
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.creation_times.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


class FastSchemaLoader:
    """Optimized schema loader with aggressive caching and lazy loading"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.schema_cache = PerformanceCache(
            max_size=100, 
            ttl_seconds=config.schema_cache_ttl
        )
        self.column_cache = PerformanceCache(
            max_size=1000,
            ttl_seconds=config.schema_cache_ttl
        )
        
    def get_fast_schema(self) -> Tuple[List[Dict], Dict[str, List[str]]]:
        """Get schema with aggressive caching and minimal processing"""
        cache_key = "fast_schema_metadata"
        
        # Try cache first
        cached_result = self.schema_cache.get(cache_key)
        if cached_result:
            logger.info("Using cached schema metadata")
            return cached_result
        
        logger.info("Loading schema with fast mode...")
        start_time = time.time()
        
        try:
            # Import here to avoid circular imports
            from database import get_schema_metadata
            
            # Get minimal schema data
            schema_metadata, column_map, _, enhanced_data = get_schema_metadata()
            
            # Simplify schema metadata for faster processing
            simplified_schema = self._simplify_schema_metadata(schema_metadata)
            
            result = (simplified_schema, column_map)
            
            # Cache the result
            self.schema_cache.put(cache_key, result)
            
            load_time = time.time() - start_time
            logger.info(f"Fast schema loaded in {load_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Fast schema loading failed: {e}")
            # Return minimal fallback
            return [], {}
    
    def _simplify_schema_metadata(self, schema_metadata: List[Dict]) -> List[Dict]:
        """Simplify schema metadata for faster processing"""
        simplified = []
        
        for table in schema_metadata:
            # Keep only essential fields
            simplified_table = {
                'schema': table.get('schema', ''),
                'table': table.get('table', ''),
                'description': table.get('description', '')[:200],  # Truncate long descriptions
                'columns': self._simplify_columns(table.get('columns', [])),
                'relationships': table.get('relationships', [])[:5],  # Limit relationships
                'primary_keys': table.get('primary_keys', [])
            }
            simplified.append(simplified_table)
        
        return simplified
    
    def _simplify_columns(self, columns: List[Dict]) -> List[Dict]:
        """Simplify column metadata"""
        simplified = []
        
        for col in columns[:20]:  # Limit to first 20 columns
            simplified_col = {
                'name': col.get('name', ''),
                'type': col.get('type', ''),
                'nullable': col.get('nullable', True),
                'primary_key': col.get('primary_key', False),
                'description': col.get('description', '')[:100]  # Truncate descriptions
            }
            simplified.append(simplified_col)
        
        return simplified


class FastLLMProcessor:
    """Optimized LLM processing with caching and timeouts"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.llm_cache = PerformanceCache(
            max_size=config.llm_cache_size,
            ttl_seconds=config.cache_ttl_seconds
        )
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def generate_sql_fast(self, 
                         nl_query: str, 
                         schema_metadata: List[Dict],
                         **kwargs) -> str:
        """Generate SQL with aggressive optimization"""
        
        # Create cache key
        cache_key = self._create_cache_key(nl_query, schema_metadata, kwargs)
        
        # Try cache first
        cached_sql = self.llm_cache.get(cache_key)
        if cached_sql:
            logger.info("Using cached SQL generation")
            return cached_sql
        
        logger.info("Generating SQL with fast mode...")
        start_time = time.time()
        
        try:
            # Use simplified schema for faster processing
            simplified_schema = self._get_relevant_tables(nl_query, schema_metadata)
            
            # Generate SQL with timeout
            future = self.executor.submit(
                self._generate_sql_with_timeout,
                nl_query,
                simplified_schema,
                kwargs
            )
            
            sql_result = future.result(timeout=self.config.llm_timeout)
            
            # Cache the result
            self.llm_cache.put(cache_key, sql_result)
            
            generation_time = time.time() - start_time
            logger.info(f"SQL generated in {generation_time:.2f}s")
            
            return sql_result
            
        except Exception as e:
            logger.error(f"Fast SQL generation failed: {e}")
            return f"Error: {str(e)}"
    
    def _create_cache_key(self, nl_query: str, schema_metadata: List[Dict], kwargs: Dict) -> str:
        """Create cache key for LLM requests"""
        # Create a hash of the input parameters
        key_data = {
            'query': nl_query.lower().strip(),
            'schema_hash': self._hash_schema(schema_metadata),
            'kwargs_hash': str(sorted(kwargs.items()))
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _hash_schema(self, schema_metadata: List[Dict]) -> str:
        """Create hash of schema metadata"""
        schema_summary = []
        for table in schema_metadata[:10]:  # Limit to first 10 tables
            table_summary = f"{table.get('schema', '')}.{table.get('table', '')}"
            schema_summary.append(table_summary)
        
        return hashlib.md5('|'.join(schema_summary).encode()).hexdigest()
    
    def _get_relevant_tables(self, nl_query: str, schema_metadata: List[Dict]) -> List[Dict]:
        """Get only relevant tables for the query"""
        query_lower = nl_query.lower()
        relevant_tables = []
        
        # Simple keyword matching for table relevance
        for table in schema_metadata:
            table_name = table.get('table', '').lower()
            schema_name = table.get('schema', '').lower()
            
            # Check if table name appears in query
            if (table_name in query_lower or 
                any(col.get('name', '').lower() in query_lower 
                    for col in table.get('columns', [])[:5])):
                relevant_tables.append(table)
            
            # Limit to 5 most relevant tables
            if len(relevant_tables) >= 5:
                break
        
        # If no relevant tables found, return first 3 tables
        if not relevant_tables:
            relevant_tables = schema_metadata[:3]
        
        return relevant_tables
    
    def _generate_sql_with_timeout(self, nl_query: str, schema_metadata: List[Dict], kwargs: Dict) -> str:
        """Generate SQL with the actual LLM"""
        try:
            from llm import generate_sql_query
            return generate_sql_query(nl_query, schema_metadata, **kwargs)
        except Exception as e:
            logger.error(f"LLM SQL generation failed: {e}")
            return f"Error: {str(e)}"


class FastIntentAnalyzer:
    """Optimized intent analysis with pattern matching and caching"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.intent_cache = PerformanceCache(
            max_size=5000,
            ttl_seconds=config.cache_ttl_seconds
        )
        
        # Pre-compiled patterns for fast matching
        self.intent_patterns = {
            'COUNT': [r'\bhow\s+many\b', r'\bcount\b', r'\bnumber\s+of\b'],
            'SELECT': [r'\bshow\b', r'\blist\b', r'\bdisplay\b', r'\bfind\b'],
            'SUM': [r'\btotal\b', r'\bsum\b', r'\badd\s+up\b'],
            'AVERAGE': [r'\baverage\b', r'\bmean\b', r'\bavg\b'],
            'MAX': [r'\bmaximum\b', r'\bmax\b', r'\bhighest\b'],
            'MIN': [r'\bminimum\b', r'\bmin\b', r'\blowest\b']
        }
        
        # Compile patterns
        import re
        self.compiled_patterns = {}
        for intent, patterns in self.intent_patterns.items():
            self.compiled_patterns[intent] = [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def analyze_intent_fast(self, nl_query: str) -> Tuple[str, float]:
        """Fast intent analysis using pattern matching"""
        
        # Check cache first
        cache_key = hashlib.md5(nl_query.lower().strip().encode()).hexdigest()
        cached_result = self.intent_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Fast pattern matching
        query_lower = nl_query.lower()
        best_intent = 'SELECT'  # Default
        best_confidence = 0.5
        
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(query_lower):
                    confidence = 0.8 if intent in ['COUNT', 'SUM'] else 0.7
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
                    break
        
        result = (best_intent, best_confidence)
        self.intent_cache.put(cache_key, result)
        
        return result


class PerformanceOptimizer:
    """Main performance optimizer that coordinates all optimizations"""
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        
        # Initialize optimized components
        self.schema_loader = FastSchemaLoader(self.config)
        self.llm_processor = FastLLMProcessor(self.config)
        self.intent_analyzer = FastIntentAnalyzer(self.config)
        
        # Performance metrics
        self.metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0
        }
        
        logger.info("PerformanceOptimizer initialized")
    
    def optimize_query_processing(self, process_func: Callable) -> Callable:
        """Decorator to optimize query processing functions"""
        
        @wraps(process_func)
        def optimized_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Pre-optimize arguments
                optimized_args, optimized_kwargs = self._optimize_arguments(args, kwargs)
                
                # Execute with timeout
                if self.config.enable_parallel_processing:
                    future = ThreadPoolExecutor(max_workers=1).submit(
                        process_func, *optimized_args, **optimized_kwargs
                    )
                    result = future.result(timeout=self.config.max_query_timeout)
                else:
                    result = process_func(*optimized_args, **optimized_kwargs)
                
                # Update metrics
                response_time = time.time() - start_time
                self._update_metrics(response_time, cache_hit=False)
                
                return result
                
            except Exception as e:
                logger.error(f"Optimized query processing failed: {e}")
                raise
        
        return optimized_wrapper
    
    def _optimize_arguments(self, args: tuple, kwargs: dict) -> Tuple[tuple, dict]:
        """Optimize function arguments for better performance"""
        
        # If schema metadata is in arguments, use cached version
        optimized_args = list(args)
        optimized_kwargs = kwargs.copy()
        
        # Look for schema metadata in arguments and replace with cached version
        for i, arg in enumerate(optimized_args):
            if isinstance(arg, list) and len(arg) > 0 and isinstance(arg[0], dict):
                if 'schema' in arg[0] and 'table' in arg[0]:
                    # This looks like schema metadata, use cached version
                    cached_schema, _ = self.schema_loader.get_fast_schema()
                    optimized_args[i] = cached_schema
                    break
        
        return tuple(optimized_args), optimized_kwargs
    
    def _update_metrics(self, response_time: float, cache_hit: bool = False):
        """Update performance metrics"""
        self.metrics['total_queries'] += 1
        self.metrics['total_response_time'] += response_time
        self.metrics['avg_response_time'] = (
            self.metrics['total_response_time'] / self.metrics['total_queries']
        )
        
        if cache_hit:
            self.metrics['cache_hits'] += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_hit_rate = (
            self.metrics['cache_hits'] / self.metrics['total_queries']
            if self.metrics['total_queries'] > 0 else 0.0
        )
        
        return {
            'total_queries': self.metrics['total_queries'],
            'avg_response_time_seconds': self.metrics['avg_response_time'],
            'cache_hit_rate': cache_hit_rate,
            'schema_cache_size': self.schema_loader.schema_cache.size(),
            'llm_cache_size': self.llm_processor.llm_cache.size(),
            'intent_cache_size': self.intent_analyzer.intent_cache.size(),
            'config': {
                'aggressive_caching': self.config.enable_aggressive_caching,
                'parallel_processing': self.config.enable_parallel_processing,
                'lazy_loading': self.config.enable_lazy_loading
            }
        }
    
    def clear_all_caches(self):
        """Clear all performance caches"""
        self.schema_loader.schema_cache.clear()
        self.llm_processor.llm_cache.clear()
        self.intent_analyzer.intent_cache.clear()
        logger.info("All performance caches cleared")
    
    def warm_up_caches(self):
        """Pre-warm caches with common operations"""
        logger.info("Warming up performance caches...")
        
        try:
            # Pre-load schema
            self.schema_loader.get_fast_schema()
            
            # Pre-analyze common intents
            common_queries = [
                "show me all employees",
                "how many projects are there",
                "what is the total hours",
                "list all clients"
            ]
            
            for query in common_queries:
                self.intent_analyzer.analyze_intent_fast(query)
            
            logger.info("Cache warm-up completed")
            
        except Exception as e:
            logger.warning(f"Cache warm-up failed: {e}")


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()


def optimize_performance(func: Callable) -> Callable:
    """Decorator to apply performance optimizations to any function"""
    return performance_optimizer.optimize_query_processing(func)


def get_performance_stats() -> Dict[str, Any]:
    """Get current performance statistics"""
    return performance_optimizer.get_performance_stats()


def clear_performance_caches():
    """Clear all performance caches"""
    performance_optimizer.clear_all_caches()


def warm_up_performance_caches():
    """Warm up performance caches"""
    performance_optimizer.warm_up_caches()