#!/usr/bin/env python3
"""
Simple RAG SQL Agent - Simplified version without monitoring overhead.

This module provides the core RAG functionality without complex monitoring
that will be replaced by OpenTelemetry later.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass

# Import existing system components
from database import get_schema_metadata, execute_query
from config import USE_LIVE_DB, get_current_database

# Import core RAG components (without monitoring)
from vector_schema_store import VectorSchemaStore
from semantic_intent_engine import SemanticIntentEngine, QueryIntent
from dynamic_sql_generator import DynamicSQLGenerator, SQLQuery
from adaptive_learning_engine import AdaptiveLearningEngine
from semantic_error_handler import SemanticErrorHandler, ErrorType, RecoveryPlan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SimpleRAGResult:
    """Simplified result of RAG-based query processing"""
    success: bool
    sql_query: Optional[str]
    results: Optional[List[Any]]
    columns: Optional[List[str]]
    confidence: float
    processing_time: float
    error_message: Optional[str]
    recovery_plan: Optional[RecoveryPlan]
    metadata: Dict[str, Any]


class SimpleRAGAgent:
    """
    Simplified RAG-based SQL Agent without monitoring overhead.
    
    This class provides the core RAG functionality for processing natural language
    queries using vector embeddings and semantic understanding.
    """
    
    def __init__(self, 
                 vector_store_path: str = "vector_data/simple_rag",
                 enable_learning: bool = True,
                 enable_error_recovery: bool = True):
        """
        Initialize the Simple RAG Agent.
        
        Args:
            vector_store_path: Path for vector storage
            enable_learning: Whether to enable adaptive learning
            enable_error_recovery: Whether to enable error recovery
        """
        self.vector_store_path = vector_store_path
        self.enable_learning = enable_learning
        self.enable_error_recovery = enable_error_recovery
        
        # Simple statistics
        self.query_count = 0
        self.success_count = 0
        
        # Initialize components
        self._initialize_components()
        
        # Load schema into vector store
        self._initialize_schema()
        
        logger.info("Simple RAG Agent initialized successfully")
    
    def _initialize_components(self):
        """Initialize core RAG components"""
        logger.info("Initializing RAG components...")
        
        # Ensure vector directory exists
        os.makedirs(self.vector_store_path, exist_ok=True)
        
        # Initialize vector schema store
        self.vector_store = VectorSchemaStore(
            vector_db_path=os.path.join(self.vector_store_path, "schema_vectors"),
            embedding_model="all-MiniLM-L6-v2"
        )
        
        # Initialize semantic intent engine
        self.intent_engine = SemanticIntentEngine(
            vector_store=self.vector_store,
            embedding_model="all-MiniLM-L6-v2"
        )
        
        # Initialize dynamic SQL generator
        self.sql_generator = DynamicSQLGenerator(
            vector_store=self.vector_store,
            intent_engine=self.intent_engine
        )
        
        # Initialize adaptive learning engine (if enabled)
        if self.enable_learning:
            self.learning_engine = AdaptiveLearningEngine(
                vector_store=self.vector_store,
                learning_data_path=os.path.join(self.vector_store_path, "learning_patterns"),
                embedding_model="all-MiniLM-L6-v2"
            )
        else:
            self.learning_engine = None
        
        # Initialize semantic error handler (if enabled)
        if self.enable_error_recovery:
            self.error_handler = SemanticErrorHandler(
                vector_store=self.vector_store,
                intent_engine=self.intent_engine,
                learning_engine=self.learning_engine,
                error_data_path=os.path.join(self.vector_store_path, "error_patterns"),
                embedding_model="all-MiniLM-L6-v2"
            )
        else:
            self.error_handler = None
        
        logger.info("RAG components initialized")
    
    def _initialize_schema(self):
        """Initialize schema in vector store"""
        logger.info("Loading database schema into vector store...")
        
        try:
            # Get schema metadata from existing system
            schema_metadata, column_map, existing_vector_store, enhanced_data = get_schema_metadata()
            
            if schema_metadata:
                # Ingest schema into our vector store
                self.vector_store.ingest_schema(schema_metadata)
                
                logger.info(f"Loaded {len(schema_metadata)} tables into vector store")
            else:
                logger.warning("No schema metadata available")
                
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
    
    def process_query(self, natural_language_query: str) -> SimpleRAGResult:
        """
        Process a natural language query using the RAG system.
        
        Args:
            natural_language_query: The user's natural language query
            
        Returns:
            SimpleRAGResult with processing results
        """
        start_time = time.time()
        self.query_count += 1
        
        logger.info(f"Processing query: {natural_language_query[:100]}...")
        
        try:
            # Step 1: Analyze query intent
            query_intent = self.intent_engine.analyze_query(natural_language_query)
            logger.info(f"Query intent: {query_intent.intent_type.value} (confidence: {query_intent.confidence:.3f})")
            
            # Step 2: Check for learned patterns (if learning is enabled)
            recommended_sql = None
            recommendation_confidence = 0.0
            if self.learning_engine:
                recommendation = self.learning_engine.get_pattern_recommendation(
                    natural_language_query, query_intent
                )
                if recommendation:
                    recommended_sql, recommendation_confidence = recommendation
                    logger.info(f"Found learned pattern with confidence: {recommendation_confidence:.3f}")
            
            # Step 3: Generate SQL query
            if recommended_sql and recommendation_confidence > 0.8:
                # Use learned pattern
                sql_query_obj = SQLQuery(
                    sql=recommended_sql,
                    confidence=recommendation_confidence,
                    clauses=[],
                    tables_used=[],
                    columns_used=[],
                    joins=[],
                    complexity_score=0.5,
                    generation_metadata={
                        "source": "learned_pattern",
                        "recommendation_confidence": recommendation_confidence
                    }
                )
            else:
                # Generate new SQL using dynamic generator
                sql_query_obj = self.sql_generator.query_builder.build_sql_query(query_intent)
            
            logger.info(f"Generated SQL: {sql_query_obj.sql}")
            
            # Step 4: Execute query (if live DB is enabled)
            results = None
            columns = None
            db_error = None
            
            if USE_LIVE_DB:
                try:
                    results, columns, db_error = execute_query(sql_query_obj.sql)
                except Exception as e:
                    db_error = str(e)
            
            # Step 5: Handle execution results
            if db_error is None:
                # Success case
                processing_time = time.time() - start_time
                self.success_count += 1
                
                # Learn from success (if learning is enabled)
                if self.learning_engine:
                    execution_result = {
                        'success': True,
                        'execution_time': processing_time,
                        'row_count': len(results) if results else 0,
                        'tables_used': sql_query_obj.tables_used,
                        'columns_used': sql_query_obj.columns_used
                    }
                    self.learning_engine.learn_from_success(
                        natural_language_query,
                        sql_query_obj.sql,
                        execution_result,
                        query_intent
                    )
                
                return SimpleRAGResult(
                    success=True,
                    sql_query=sql_query_obj.sql,
                    results=results,
                    columns=columns,
                    confidence=sql_query_obj.confidence,
                    processing_time=processing_time,
                    error_message=None,
                    recovery_plan=None,
                    metadata={
                        'intent_type': query_intent.intent_type.value,
                        'complexity_level': query_intent.complexity_level.value,
                        'generation_method': sql_query_obj.generation_metadata.get('source', 'dynamic'),
                        'database': get_current_database()
                    }
                )
            
            else:
                # Error case - attempt recovery
                return self._handle_query_error(
                    natural_language_query,
                    sql_query_obj.sql,
                    db_error,
                    query_intent,
                    start_time
                )
        
        except Exception as e:
            # Unexpected error
            processing_time = time.time() - start_time
            
            logger.error(f"Unexpected error processing query: {e}")
            
            return SimpleRAGResult(
                success=False,
                sql_query=None,
                results=None,
                columns=None,
                confidence=0.0,
                processing_time=processing_time,
                error_message=f"Unexpected error: {str(e)}",
                recovery_plan=None,
                metadata={
                    'error_type': 'unexpected_error',
                    'database': get_current_database()
                }
            )
    
    def _handle_query_error(self, 
                           natural_language_query: str,
                           failed_sql: str,
                           error_message: str,
                           query_intent: QueryIntent,
                           start_time: float) -> SimpleRAGResult:
        """Handle query execution errors with recovery"""
        processing_time = time.time() - start_time
        
        logger.warning(f"Query execution failed: {error_message}")
        
        recovery_plan = None
        
        # Attempt error recovery (if enabled)
        if self.error_handler:
            try:
                query_context = {
                    'original_query': natural_language_query,
                    'failed_sql': failed_sql,
                    'query_intent': query_intent
                }
                
                # Determine error type
                error_type = self._classify_error_type(error_message)
                
                # Create mock exception for error handler
                mock_error = Exception(error_message)
                
                if error_type == ErrorType.SCHEMA_ERROR:
                    recovery_plan = self.error_handler.handle_schema_error(mock_error, query_context)
                else:
                    # Handle other error types - simplified for now
                    recovery_plan = None
                
                if recovery_plan:
                    logger.info(f"Generated recovery plan with {len(recovery_plan.suggestions)} suggestions")
                
            except Exception as recovery_error:
                logger.error(f"Error recovery failed: {recovery_error}")
        
        return SimpleRAGResult(
            success=False,
            sql_query=failed_sql,
            results=None,
            columns=None,
            confidence=0.0,
            processing_time=processing_time,
            error_message=error_message,
            recovery_plan=recovery_plan,
            metadata={
                'intent_type': query_intent.intent_type.value,
                'error_type': self._classify_error_type(error_message).value,
                'database': get_current_database()
            }
        )
    
    def _classify_error_type(self, error_message: str) -> ErrorType:
        """Classify error type based on error message"""
        error_lower = error_message.lower()
        
        if any(keyword in error_lower for keyword in ['invalid object', 'invalid column', 'object doesn\'t exist']):
            return ErrorType.SCHEMA_ERROR
        elif any(keyword in error_lower for keyword in ['syntax error', 'incorrect syntax']):
            return ErrorType.SYNTAX_ERROR
        elif any(keyword in error_lower for keyword in ['permission', 'access denied']):
            return ErrorType.EXECUTION_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def get_simple_statistics(self) -> Dict[str, Any]:
        """Get simple system statistics"""
        success_rate = (self.success_count / max(self.query_count, 1)) * 100
        
        return {
            'total_queries': self.query_count,
            'successful_queries': self.success_count,
            'success_rate_percent': success_rate,
            'vector_store_size': len(self.vector_store.schema_vectors),
            'learned_patterns_count': len(self.learning_engine.success_patterns) if self.learning_engine else 0,
            'database': get_current_database()
        }
    
    def explain_query_processing(self, query: str) -> Dict[str, Any]:
        """
        Explain how a query would be processed (without executing).
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with processing explanation
        """
        try:
            # Analyze intent
            query_intent = self.intent_engine.analyze_query(query)
            
            # Check for learned patterns
            learned_recommendation = None
            if self.learning_engine:
                recommendation = self.learning_engine.get_pattern_recommendation(query, query_intent)
                if recommendation:
                    learned_recommendation = {
                        'sql': recommendation[0],
                        'confidence': recommendation[1]
                    }
            
            # Get similar schema elements
            query_vector = self.intent_engine.embedder.encode(query)
            query_vector = self.intent_engine._normalize_vector(query_vector)
            
            similar_tables = self.vector_store.find_similar_tables(query_vector, k=3)
            similar_columns = self.vector_store.find_similar_columns(query_vector, k=5)
            
            return {
                'query': query,
                'intent_analysis': {
                    'intent_type': query_intent.intent_type.value,
                    'confidence': query_intent.confidence,
                    'complexity_level': query_intent.complexity_level.value,
                    'entities': [
                        {
                            'name': entity.name,
                            'type': entity.entity_type.value,
                            'confidence': entity.confidence
                        }
                        for entity in query_intent.entities
                    ]
                },
                'learned_recommendation': learned_recommendation,
                'similar_schema_elements': {
                    'tables': [
                        {
                            'name': table.table_name,
                            'schema': table.schema_name,
                            'similarity': table.similarity_score
                        }
                        for table in similar_tables
                    ],
                    'columns': [
                        {
                            'name': column.column_name,
                            'table': column.table_name,
                            'similarity': column.similarity_score
                        }
                        for column in similar_columns
                    ]
                },
                'processing_strategy': 'learned_pattern' if learned_recommendation else 'dynamic_generation'
            }
            
        except Exception as e:
            return {
                'query': query,
                'error': f"Failed to explain query processing: {str(e)}"
            }
    
    def refresh_schema(self):
        """Refresh schema in vector store"""
        logger.info("Refreshing schema in vector store...")
        
        try:
            # Clear existing vectors
            self.vector_store.clear_all_vectors()
            
            # Reload schema
            self._initialize_schema()
            
            logger.info("Schema refreshed successfully")
            
        except Exception as e:
            logger.error(f"Failed to refresh schema: {e}")
            raise
    
    def save_system_state(self):
        """Save system state to disk"""
        logger.info("Saving RAG system state...")
        
        try:
            # Save vector store
            self.vector_store.save_to_disk()
            
            # Save learning patterns (if enabled)
            if self.learning_engine:
                self.learning_engine.save_patterns_to_disk()
            
            # Save error patterns (if enabled)
            if self.error_handler:
                self.error_handler.save_error_patterns_to_disk()
            
            logger.info("System state saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save system state: {e}")
            raise


def create_simple_rag_agent() -> SimpleRAGAgent:
    """
    Factory function to create a Simple RAG Agent.
    
    Returns:
        Initialized SimpleRAGAgent instance
    """
    return SimpleRAGAgent()


# Example usage and testing
if __name__ == "__main__":
    # Create simple RAG agent
    agent = create_simple_rag_agent()
    
    # Test queries
    test_queries = [
        "How many employees are there?",
        "Show me all projects",
        "What is the average salary by department?"
    ]
    
    print("=== Simple RAG Agent Test ===\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        result = agent.process_query(query)
        
        print(f"Success: {result.success}")
        print(f"SQL: {result.sql_query}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Processing Time: {result.processing_time:.3f}s")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        print("-" * 50)
    
    # Show system statistics
    stats = agent.get_simple_statistics()
    print(f"\nSystem Statistics:")
    print(f"Total Queries: {stats['total_queries']}")
    print(f"Success Rate: {stats['success_rate_percent']:.1f}%")
    print(f"Vector Store Size: {stats['vector_store_size']}")
    print(f"Learned Patterns: {stats['learned_patterns_count']}")