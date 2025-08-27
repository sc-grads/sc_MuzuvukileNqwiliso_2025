#!/usr/bin/env python3
"""
Fast RAG SQL Agent - Performance-optimized version of the RAG SQL Agent

This module implements aggressive performance optimizations to reduce query processing
time from 120+ seconds to under 10 seconds while maintaining accuracy.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass

# Import performance optimizations
from performance_optimizer import (
    PerformanceOptimizer, PerformanceConfig, optimize_performance,
    FastSchemaLoader, FastLLMProcessor, FastIntentAnalyzer
)
from fast_config import get_performance_config, get_cache_warming_config

# Import existing components (we'll optimize their usage)
from rag_sql_agent import RAGQueryResult, RAGSQLAgent
from database import get_schema_metadata, execute_query
from config import USE_LIVE_DB, get_current_database
from nl_response_generator import generate_natural_language_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FastQueryResult:
    """Optimized query result with performance metrics"""
    success: bool
    sql_query: Optional[str]
    results: Optional[List[Any]]
    columns: Optional[List[str]]
    confidence: float
    processing_time: float
    error_message: Optional[str]
    natural_language_response: Optional[str] = None
    performance_metrics: Dict[str, Any] = None
    cache_hits: Dict[str, bool] = None


class FastRAGSQLAgent:
    """
    Performance-optimized RAG SQL Agent that reduces response time dramatically
    while maintaining query accuracy and functionality.
    """
    
    def __init__(self, 
                 performance_config: PerformanceConfig = None,
                 enable_fallback: bool = True,
                 performance_level: str = 'maximum_speed'):
        """
        Initialize the Fast RAG SQL Agent.
        
        Args:
            performance_config: Performance optimization configuration
            enable_fallback: Whether to fallback to original agent on errors
            performance_level: Performance level ('maximum_speed', 'balanced', 'conservative')
        """
        self.performance_config = performance_config or get_performance_config(performance_level)
        self.enable_fallback = enable_fallback
        
        # Initialize performance optimizer
        self.optimizer = PerformanceOptimizer(self.performance_config)
        
        # Initialize fast components
        self.schema_loader = FastSchemaLoader(self.performance_config)
        self.llm_processor = FastLLMProcessor(self.performance_config)
        self.intent_analyzer = FastIntentAnalyzer(self.performance_config)
        
        # Fallback to original agent if needed
        self.fallback_agent = None
        if enable_fallback:
            try:
                self.fallback_agent = RAGSQLAgent()
            except Exception as e:
                logger.warning(f"Fallback agent initialization failed: {e}")
        
        # Performance metrics
        self.stats = {
            'total_queries': 0,
            'fast_queries': 0,
            'fallback_queries': 0,
            'avg_fast_time': 0.0,
            'avg_fallback_time': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # Pre-warm caches
        self._warm_up_caches()
        
        logger.info("FastRAGSQLAgent initialized successfully")
    
    def _warm_up_caches(self):
        """Pre-warm caches for better initial performance"""
        try:
            cache_config = get_cache_warming_config()
            
            if not cache_config.get('enable_cache_warming', True):
                return
            
            logger.info("Warming up caches...")
            
            # Pre-load schema if enabled
            if cache_config.get('warm_schema_on_startup', True):
                self.schema_loader.get_fast_schema()
            
            # Pre-analyze common query patterns if enabled
            if cache_config.get('warm_intent_patterns', True):
                common_patterns = cache_config.get('common_queries', [
                    "show me all employees",
                    "how many projects",
                    "total hours worked",
                    "list clients"
                ])
                
                for pattern in common_patterns:
                    self.intent_analyzer.analyze_intent_fast(pattern)
            
            logger.info("Cache warm-up completed")
            
        except Exception as e:
            logger.warning(f"Cache warm-up failed: {e}")
    
    def process_query_fast(self, 
                          natural_language_query: str,
                          conversation_context: Optional[Dict[str, Any]] = None,
                          force_fast: bool = False) -> FastQueryResult:
        """
        Process query with aggressive performance optimizations.
        
        Args:
            natural_language_query: User's natural language query
            conversation_context: Optional conversation context
            force_fast: Force fast processing even if it might reduce accuracy
            
        Returns:
            FastQueryResult with processing results and performance metrics
        """
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        cache_hits = {
            'schema': False,
            'intent': False,
            'llm': False,
            'query': False
        }
        
        performance_metrics = {
            'schema_load_time': 0.0,
            'intent_analysis_time': 0.0,
            'sql_generation_time': 0.0,
            'query_execution_time': 0.0,
            'response_generation_time': 0.0
        }
        
        try:
            logger.info(f"Processing query (fast mode): {natural_language_query[:100]}...")
            
            # Step 1: Fast intent analysis
            intent_start = time.time()
            intent_type, confidence = self.intent_analyzer.analyze_intent_fast(natural_language_query)
            performance_metrics['intent_analysis_time'] = (time.time() - intent_start) * 1000
            
            logger.info(f"Intent: {intent_type} (confidence: {confidence:.3f})")
            
            # Step 2: Fast schema loading
            schema_start = time.time()
            schema_metadata, column_map = self.schema_loader.get_fast_schema()
            performance_metrics['schema_load_time'] = (time.time() - schema_start) * 1000
            cache_hits['schema'] = performance_metrics['schema_load_time'] < 100  # Assume cache hit if very fast
            
            # Step 3: Fast SQL generation
            sql_start = time.time()
            sql_query = self.llm_processor.generate_sql_fast(
                natural_language_query,
                schema_metadata,
                column_map=column_map,
                entities={
                    "is_database_related": True,
                    "intent": intent_type,
                    "suggested_tables": []
                },
                conversation_context=conversation_context
            )
            performance_metrics['sql_generation_time'] = (time.time() - sql_start) * 1000
            cache_hits['llm'] = performance_metrics['sql_generation_time'] < 1000  # Assume cache hit if under 1s
            
            logger.info(f"Generated SQL: {sql_query}")
            
            # Check for SQL generation errors
            if sql_query.startswith("Error:") or sql_query.startswith("VALIDATION_ERROR:"):
                return self._handle_fast_error(
                    natural_language_query, sql_query, start_time, 
                    performance_metrics, cache_hits
                )
            
            # Step 4: Query execution
            execution_start = time.time()
            results, columns, db_error = None, None, None
            
            if USE_LIVE_DB:
                try:
                    results, columns, db_error = execute_query(sql_query)
                except Exception as e:
                    db_error = str(e)
            
            performance_metrics['query_execution_time'] = (time.time() - execution_start) * 1000
            
            # Step 5: Handle results
            if db_error is None:
                # Success case
                response_start = time.time()
                
                # Generate natural language response (with timeout)
                try:
                    natural_language_response = self._generate_response_fast(
                        natural_language_query, sql_query, results, columns
                    )
                except Exception as e:
                    logger.warning(f"Response generation failed: {e}")
                    natural_language_response = self._generate_simple_response(results, columns)
                
                performance_metrics['response_generation_time'] = (time.time() - response_start) * 1000
                
                # Update stats
                processing_time = time.time() - start_time
                self.stats['fast_queries'] += 1
                self._update_fast_stats(processing_time)
                
                return FastQueryResult(
                    success=True,
                    sql_query=sql_query,
                    results=results,
                    columns=columns,
                    confidence=confidence,
                    processing_time=processing_time,
                    error_message=None,
                    natural_language_response=natural_language_response,
                    performance_metrics=performance_metrics,
                    cache_hits=cache_hits
                )
            
            else:
                # Error case - try fast recovery or fallback
                return self._handle_query_error_fast(
                    natural_language_query, sql_query, db_error,
                    start_time, performance_metrics, cache_hits
                )
        
        except Exception as e:
            logger.error(f"Fast query processing failed: {e}")
            
            # Fallback to original agent if enabled and not forced fast
            if self.fallback_agent and not force_fast:
                return self._fallback_to_original(
                    natural_language_query, conversation_context, start_time
                )
            
            # Return error result
            processing_time = time.time() - start_time
            return FastQueryResult(
                success=False,
                sql_query=None,
                results=None,
                columns=None,
                confidence=0.0,
                processing_time=processing_time,
                error_message=f"Fast processing failed: {str(e)}",
                performance_metrics=performance_metrics,
                cache_hits=cache_hits
            )
    
    def _generate_response_fast(self, 
                               nl_query: str, 
                               sql_query: str, 
                               results: List[Any], 
                               columns: List[str]) -> str:
        """Generate natural language response with timeout"""
        try:
            # Use existing response generator with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Response generation timeout")
            
            # Set timeout (only on Unix systems)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)  # 5 second timeout
            
            try:
                response = generate_natural_language_response(nl_query, sql_query, results, columns)
                return response
            finally:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)  # Cancel timeout
            
        except (TimeoutError, Exception) as e:
            logger.warning(f"Fast response generation failed: {e}")
            return self._generate_simple_response(results, columns)
    
    def _generate_simple_response(self, results: List[Any], columns: List[str]) -> str:
        """Generate simple response without LLM"""
        if not results:
            return "No results found for your query."
        
        result_count = len(results)
        if result_count == 1:
            return f"Found 1 result with {len(columns)} columns."
        else:
            return f"Found {result_count} results with {len(columns)} columns."
    
    def _handle_fast_error(self, 
                          nl_query: str, 
                          error_msg: str, 
                          start_time: float,
                          performance_metrics: Dict[str, Any],
                          cache_hits: Dict[str, bool]) -> FastQueryResult:
        """Handle errors in fast processing"""
        processing_time = time.time() - start_time
        
        return FastQueryResult(
            success=False,
            sql_query=None,
            results=None,
            columns=None,
            confidence=0.0,
            processing_time=processing_time,
            error_message=error_msg,
            performance_metrics=performance_metrics,
            cache_hits=cache_hits
        )
    
    def _handle_query_error_fast(self, 
                                nl_query: str,
                                sql_query: str,
                                db_error: str,
                                start_time: float,
                                performance_metrics: Dict[str, Any],
                                cache_hits: Dict[str, bool]) -> FastQueryResult:
        """Handle database query errors with fast recovery"""
        
        logger.warning(f"Query execution failed: {db_error}")
        
        # Try simple error recovery
        recovery_suggestions = self._get_fast_recovery_suggestions(db_error)
        
        processing_time = time.time() - start_time
        
        return FastQueryResult(
            success=False,
            sql_query=sql_query,
            results=None,
            columns=None,
            confidence=0.0,
            processing_time=processing_time,
            error_message=f"Query failed: {db_error}. Suggestions: {'; '.join(recovery_suggestions)}",
            performance_metrics=performance_metrics,
            cache_hits=cache_hits
        )
    
    def _get_fast_recovery_suggestions(self, error_msg: str) -> List[str]:
        """Get fast recovery suggestions based on error message"""
        error_lower = error_msg.lower()
        suggestions = []
        
        if 'invalid object' in error_lower or 'invalid column' in error_lower:
            suggestions.append("Check table and column names")
        elif 'syntax error' in error_lower:
            suggestions.append("Review query syntax")
        elif 'permission' in error_lower:
            suggestions.append("Check database permissions")
        else:
            suggestions.append("Try rephrasing your question")
        
        return suggestions
    
    def _fallback_to_original(self, 
                             nl_query: str,
                             conversation_context: Optional[Dict[str, Any]],
                             start_time: float) -> FastQueryResult:
        """Fallback to original RAG agent"""
        
        logger.info("Falling back to original RAG agent...")
        
        try:
            # Use original agent
            original_result = self.fallback_agent.process_query(nl_query, conversation_context)
            
            # Convert to FastQueryResult
            processing_time = time.time() - start_time
            self.stats['fallback_queries'] += 1
            self._update_fallback_stats(processing_time)
            
            return FastQueryResult(
                success=original_result.success,
                sql_query=original_result.sql_query,
                results=original_result.results,
                columns=original_result.columns,
                confidence=original_result.confidence,
                processing_time=processing_time,
                error_message=original_result.error_message,
                natural_language_response=original_result.natural_language_response,
                performance_metrics={'fallback': True},
                cache_hits={'fallback': True}
            )
            
        except Exception as e:
            logger.error(f"Fallback to original agent failed: {e}")
            
            processing_time = time.time() - start_time
            return FastQueryResult(
                success=False,
                sql_query=None,
                results=None,
                columns=None,
                confidence=0.0,
                processing_time=processing_time,
                error_message=f"Both fast and fallback processing failed: {str(e)}",
                performance_metrics={'fallback_failed': True},
                cache_hits={}
            )
    
    def _update_fast_stats(self, processing_time: float):
        """Update statistics for fast queries"""
        if self.stats['fast_queries'] == 1:
            self.stats['avg_fast_time'] = processing_time
        else:
            self.stats['avg_fast_time'] = (
                (self.stats['avg_fast_time'] * (self.stats['fast_queries'] - 1) + processing_time) /
                self.stats['fast_queries']
            )
    
    def _update_fallback_stats(self, processing_time: float):
        """Update statistics for fallback queries"""
        if self.stats['fallback_queries'] == 1:
            self.stats['avg_fallback_time'] = processing_time
        else:
            self.stats['avg_fallback_time'] = (
                (self.stats['avg_fallback_time'] * (self.stats['fallback_queries'] - 1) + processing_time) /
                self.stats['fallback_queries']
            )
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        
        # Calculate cache hit rate
        optimizer_stats = self.optimizer.get_performance_stats()
        
        return {
            'query_stats': {
                'total_queries': self.stats['total_queries'],
                'fast_queries': self.stats['fast_queries'],
                'fallback_queries': self.stats['fallback_queries'],
                'fast_success_rate': (
                    self.stats['fast_queries'] / self.stats['total_queries']
                    if self.stats['total_queries'] > 0 else 0.0
                )
            },
            'performance_stats': {
                'avg_fast_time_seconds': self.stats['avg_fast_time'],
                'avg_fallback_time_seconds': self.stats['avg_fallback_time'],
                'performance_improvement': (
                    (self.stats['avg_fallback_time'] - self.stats['avg_fast_time']) / 
                    self.stats['avg_fallback_time'] * 100
                    if self.stats['avg_fallback_time'] > 0 else 0.0
                )
            },
            'cache_stats': optimizer_stats,
            'config': {
                'aggressive_caching': self.performance_config.enable_aggressive_caching,
                'parallel_processing': self.performance_config.enable_parallel_processing,
                'lazy_loading': self.performance_config.enable_lazy_loading,
                'max_workers': self.performance_config.max_workers
            }
        }
    
    def clear_caches(self):
        """Clear all performance caches"""
        self.optimizer.clear_all_caches()
        logger.info("All caches cleared")
    
    def optimize_performance(self):
        """Run performance optimization routines"""
        logger.info("Running performance optimization...")
        
        try:
            # Clear old cache entries
            self.optimizer.clear_all_caches()
            
            # Warm up caches
            self._warm_up_caches()
            
            logger.info("Performance optimization completed")
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")


# Create global fast agent instance
fast_agent = None

def get_fast_agent() -> FastRAGSQLAgent:
    """Get or create the global fast agent instance"""
    global fast_agent
    if fast_agent is None:
        fast_agent = FastRAGSQLAgent()
    return fast_agent


def process_query_fast(natural_language_query: str, 
                      conversation_context: Optional[Dict[str, Any]] = None) -> FastQueryResult:
    """Process query using the fast RAG agent"""
    agent = get_fast_agent()
    return agent.process_query_fast(natural_language_query, conversation_context)


def get_fast_performance_stats() -> Dict[str, Any]:
    """Get performance statistics from the fast agent"""
    agent = get_fast_agent()
    return agent.get_performance_statistics()