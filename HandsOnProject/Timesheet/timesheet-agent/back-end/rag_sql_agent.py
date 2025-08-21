#!/usr/bin/env python3
import os
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass

# Import existing system components
from database import get_schema_metadata, execute_query, lazy_generator
import atexit
from config import USE_LIVE_DB, get_current_database

# Import RAG components
from vector_schema_store import VectorSchemaStore
from improved_semantic_intent_engine import ImprovedSemanticIntentEngine, QueryIntent
from llm import generate_sql_query
from adaptive_learning_engine import AdaptiveLearningEngine
from semantic_error_handler import SemanticErrorHandler, ErrorType, RecoveryPlan
from vector_config import VectorConfig
from sentence_transformers import SentenceTransformer
from nl_response_generator import generate_natural_language_response
# from query_intent_classifier import QueryIntentClassifier, QueryType  # Not needed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGQueryResult:
    """Result of RAG-based query processing"""
    success: bool
    sql_query: Optional[str]
    results: Optional[List[Any]]
    columns: Optional[List[str]]
    confidence: float
    processing_time: float
    error_message: Optional[str]
    recovery_plan: Optional[RecoveryPlan]
    metadata: Dict[str, Any]
    natural_language_response: Optional[str] = None
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


@dataclass
class SQLQuery:
    """Container for generated SQL and related metadata."""
    sql: str
    confidence: float
    clauses: List[str]
    tables_used: List[str]
    columns_used: List[str]
    joins: List[str]
    complexity_score: float
    generation_metadata: Dict[str, Any]


@dataclass
class RAGSystemStats:
    """Statistics about the RAG system performance"""
    total_queries_processed: int
    successful_queries: int
    failed_queries: int
    average_confidence: float
    average_processing_time: float
    vector_store_size: int
    learned_patterns_count: int
    error_recovery_rate: float
    last_updated: datetime


class RAGSQLAgent:
    """
    Main RAG-based SQL Agent that integrates all components.
    
    This class provides a unified interface for processing natural language
    queries using the RAG-first architecture with vector embeddings.
    """
    
    def __init__(self, 
                 vector_store_path: str = "vector_data",
                 enable_learning: bool = True,
                 enable_error_recovery: bool = True,
                 config_overrides: Dict[str, Any] = None):
        """
        Initialize the RAG SQL Agent.
        
        Args:
            vector_store_path: Path for vector storage
            enable_learning: Whether to enable adaptive learning
            enable_error_recovery: Whether to enable error recovery
            config_overrides: Configuration overrides
        """
        self.vector_store_path = vector_store_path
        self.enable_learning = enable_learning
        self.enable_error_recovery = enable_error_recovery
        self.config_overrides = config_overrides or {}
        
        # System statistics
        self.stats = RAGSystemStats(
            total_queries_processed=0,
            successful_queries=0,
            failed_queries=0,
            average_confidence=0.0,
            average_processing_time=0.0,
            vector_store_size=0,
            learned_patterns_count=0,
            error_recovery_rate=0.0,
            last_updated=datetime.now()
        )
        
        # Initialize components
        self._initialize_components()
        
        # Load schema into vector store
        # Cache for schema metadata to avoid repeated expensive loads per query
        self.schema_metadata: Optional[List[Dict[str, Any]]] = None
        self.column_map: Optional[Dict[str, List[str]]] = None
        self.enhanced_data: Optional[Dict[str, Any]] = None
        self._initialize_schema()
        
        logger.info("RAG SQL Agent initialized successfully")

    def shutdown(self):
        """Perform graceful shutdown of agent components."""
        logger.info("Shutting down RAG SQL Agent...")
        # Persist system state before shutting down
        try:
            self.save_system_state()
        except Exception as e:
            logger.warning(f"Failed to save system state on shutdown: {e}")
        lazy_generator.stop()
        logger.info("RAG SQL Agent shutdown complete.")
    
    def _initialize_components(self):
        """Initialize all RAG components"""
        logger.info("Initializing RAG components...")
        
        # Get configuration
        config = VectorConfig.get_config('schema_store')
        config.update(self.config_overrides)
        
        # Ensure vector directory exists
        VectorConfig.ensure_vector_dir()
        os.makedirs(self.vector_store_path, exist_ok=True)
        
        # Initialize embedder once
        self.embedder = SentenceTransformer('paraphrase-MiniLM-L3-v2')

        # Initialize vector schema store
        self.vector_store = VectorSchemaStore(
            vector_db_path=os.path.join(self.vector_store_path, "schema_vectors"),
            embedding_model=config['embedding_model']
        )
        
        # Initialize semantic intent engine
        self.intent_engine = ImprovedSemanticIntentEngine(
            vector_store=self.vector_store,
            embedding_model=config['embedding_model']
        )
        
        # Initialize query intent classifier
        # self.query_classifier = QueryIntentClassifier()  # Not needed with ImprovedSemanticIntentEngine
        
        # Initialize adaptive learning engine (if enabled)
        if self.enable_learning:
            self.learning_engine = AdaptiveLearningEngine(
                vector_store=self.vector_store,
                learning_data_path=os.path.join(self.vector_store_path, "learning_patterns")
            )
        else:
            self.learning_engine = None
        
        # Initialize semantic error handler (if enabled)
        if self.enable_error_recovery:
            self.error_handler = SemanticErrorHandler(
                vector_store=self.vector_store,
                intent_engine=self.intent_engine,
                learning_engine=self.learning_engine,
                error_data_path=os.path.join(self.vector_store_path, "error_patterns")
            )
        else:
            self.error_handler = None
        
        logger.info("RAG components initialized")
    
    def _initialize_schema(self):
        """Initialize schema in vector store"""
        logger.info("Loading database schema into vector store...")
        
        try:
            # Get schema metadata from existing system
            schema_result = get_schema_metadata()
            if isinstance(schema_result, tuple):
                schema_metadata = schema_result[0]
                column_map = schema_result[1] if len(schema_result) > 1 else {}
                enhanced_data = schema_result[3] if len(schema_result) > 3 else None
            else:
                schema_metadata = schema_result
                column_map = {}
                enhanced_data = None
            
            if schema_metadata:
                logger.info(f"Schema metadata type: {type(schema_metadata)}")
                if isinstance(schema_metadata, list) and len(schema_metadata) > 0:
                    logger.info(f"First item type: {type(schema_metadata[0])}")
                    # logger.info(f"First item: {schema_metadata[0]}")
                
                # Ingest schema into our vector store
                self.vector_store.ingest_schema(schema_metadata)
                # Persist schema vectors immediately so folders are populated
                try:
                    self.vector_store.save_to_disk()
                except Exception as e:
                    logger.warning(f"Failed to save vector store after schema ingest: {e}")
                
                # Update statistics
                self.stats.vector_store_size = len(self.vector_store.schema_vectors)
                # Cache for reuse
                self.schema_metadata = schema_metadata
                self.column_map = column_map
                self.enhanced_data = enhanced_data
                
                logger.info(f"Loaded {len(schema_metadata)} tables into vector store")
            else:
                logger.warning("No schema metadata available")
                
        except Exception as e:
            import traceback
            logger.error(f"Failed to initialize schema: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def process_query(self, natural_language_query: str, conversation_context: Optional[Dict[str, Any]] = None) -> RAGQueryResult:
        """
        Process a natural language query using the RAG system.
        
        Args:
            natural_language_query: The user's natural language query
            conversation_context: Optional dictionary with context from previous turn
            
        Returns:
            RAGQueryResult with processing results
        """
        start_time = time.time()
        self.stats.total_queries_processed += 1
        
        # Use the original query without context modification for intent analysis
        # Context will be used later in SQL generation if needed
        full_query = natural_language_query
        
        # Store context for later use
        has_context = conversation_context and conversation_context.get('sql_query')
        if has_context:
            logger.info(f"Conversational context available from previous query")

        logger.info(f"Processing query: {full_query[:100]}...")
        
        try:
            # Step 1: Analyze query intent
            query_intent = self.intent_engine.analyze_query(full_query)

            # Handle cases where intent analysis fails
            if query_intent is None:
                logger.warning("Intent analysis failed. Could not determine a clear intent from the query.")
                return RAGQueryResult(
                    success=False,
                    sql_query=None,
                    results=None,
                    columns=None,
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    error_message="Could not understand the query's intent. Please try rephrasing your question.",
                    recovery_plan=None,
                    metadata={'error_type': 'intent_analysis_failed'},
                    needs_clarification=True,
                    clarification_question="I'm sorry, I wasn't able to understand your request. Could you please rephrase it?"
                )

            logger.info(f"Query intent: {query_intent.intent_type.value} (confidence: {query_intent.confidence:.3f})")

            # Step 1.5: Check confidence and ask for clarification if needed
            CONFIDENCE_THRESHOLD = 0.3  # Lowered threshold to be less restrictive
            if query_intent.confidence < CONFIDENCE_THRESHOLD:
                logger.warning(f"Query confidence ({query_intent.confidence:.3f}) is below threshold ({CONFIDENCE_THRESHOLD}). Asking for clarification.")
                clarification_question = self.intent_engine.generate_clarification_question(query_intent)
                
                return RAGQueryResult(
                    success=False,
                    sql_query=None,
                    results=None,
                    columns=None,
                    confidence=query_intent.confidence,
                    processing_time=time.time() - start_time,
                    error_message="Low confidence in query interpretation.",
                    recovery_plan=None,
                    metadata={'intent_type': query_intent.intent_type.value},
                    needs_clarification=True,
                    clarification_question=clarification_question
                )

            # Step 3: Check for learned patterns (if learning is enabled)
            if self.learning_engine:
                recommendation = self.learning_engine.get_pattern_recommendation(
                    full_query, query_intent
                )
                if recommendation:
                    recommended_sql, recommendation_confidence = recommendation
                    if recommended_sql and recommendation_confidence > 0.85:  # High confidence threshold
                        logger.info(f"Using learned pattern with confidence: {recommendation_confidence:.3f}")
                        sql_query_obj = SQLQuery(
                            sql=recommended_sql,
                            confidence=recommendation_confidence,
                            # Simplified metadata for learned patterns
                            clauses=[], tables_used=[], columns_used=[], joins=[],
                            complexity_score=0.5, # Placeholder
                            generation_metadata={'source': 'learned_pattern'}
                        )
                    else:
                        # Step 4: Generate SQL using the LLM (use cached schema)
                        if not self.schema_metadata:
                            self._initialize_schema()
                        schema_metadata = self.schema_metadata or []
                        column_map = self.column_map or {}
                        enhanced_data = self.enhanced_data

                        sql_query_str = generate_sql_query(
                            nl_query=full_query,
                            schema_metadata=schema_metadata,
                            column_map=column_map,
                            entities={
                                "is_database_related": True,
                                "intent": query_intent.intent_type.value,
                                "suggested_tables": [table.name for table in query_intent.entities if table.entity_type.value == 'TABLE'],
                            },
                            conversation_context=conversation_context,
                            enhanced_data=enhanced_data
                        )
                        sql_query_obj = type('SQLQuery', (object,), {'sql': sql_query_str, 'confidence': query_intent.confidence, 'generation_metadata': {}, 'tables_used': []})()
                else:
                    # Step 4: Generate SQL using the LLM (use cached schema)
                    if not self.schema_metadata:
                        self._initialize_schema()
                    schema_metadata = self.schema_metadata or []
                    column_map = self.column_map or {}
                    enhanced_data = self.enhanced_data

                    sql_query_str = generate_sql_query(
                        nl_query=full_query,
                        schema_metadata=schema_metadata,
                        column_map=column_map,
                        entities={
                            "is_database_related": True,
                            "intent": query_intent.intent_type.value,
                            "suggested_tables": [table.name for table in query_intent.entities if table.entity_type.value == 'TABLE'],
                        },
                        conversation_context=conversation_context,
                        enhanced_data=enhanced_data
                    )
                    sql_query_obj = type('SQLQuery', (object,), {'sql': sql_query_str, 'confidence': query_intent.confidence, 'generation_metadata': {}, 'tables_used': []})()
            else:
                # Step 4: Generate SQL using the LLM (default path, use cached schema)
                if not self.schema_metadata:
                    self._initialize_schema()
                schema_metadata = self.schema_metadata or []
                column_map = self.column_map or {}
                enhanced_data = self.enhanced_data

                sql_query_str = generate_sql_query(
                    nl_query=full_query,
                    schema_metadata=schema_metadata,
                    column_map=column_map,
                    entities={
                        "is_database_related": True,
                        "intent": query_intent.intent_type.value,
                        "suggested_tables": [table.name for table in query_intent.entities if table.entity_type.value == 'TABLE'],
                    },
                    conversation_context=conversation_context,
                    enhanced_data=enhanced_data
                )
                sql_query_obj = type('SQLQuery', (object,), {'sql': sql_query_str, 'confidence': query_intent.confidence, 'generation_metadata': {}, 'tables_used': []})()
            
            logger.info(f"Generated SQL: {sql_query_obj.sql}")
            
            # Check if SQL generation resulted in validation error
            if sql_query_obj.sql.startswith("VALIDATION_ERROR:"):
                error_message = sql_query_obj.sql.replace("VALIDATION_ERROR:", "").strip()
                return self._handle_query_error(
                    natural_language_query,
                    "",  # No SQL was generated
                    error_message,
                    query_intent,
                    start_time
                )
            
            # Step 4: Execute query (if live DB is enabled)
            results = None
            columns = None
            db_error = None
            
            if USE_LIVE_DB:
                try:
                    # Add query timeout for performance
                    query_start_time = time.time()
                    results, columns, db_error = execute_query(sql_query_obj.sql)
                    query_execution_time = time.time() - query_start_time
                    
                    # Log performance metrics
                    if query_execution_time > 10.0:  # Log slow queries
                        logger.warning(f"Slow query execution: {query_execution_time:.2f}s for query: {natural_language_query[:100]}...")
                    
                except Exception as e:
                    db_error = str(e)
            
            # Step 5: Handle execution results
            if db_error is None:
                # Success case
                processing_time = time.time() - start_time
                self.stats.successful_queries += 1
                
                # Learn from success (if learning is enabled)
                if self.learning_engine:
                    self.learning_engine.learn_from_success(
                        natural_language_query,
                        sql_query_obj.sql,
                        {'row_count': len(results) if results else 0},
                        query_intent
                    )
                
                # Update statistics
                self._update_success_stats(sql_query_obj.confidence, processing_time)
                
                # Generate natural language response
                natural_language_response = generate_natural_language_response(
                    natural_language_query,
                    sql_query_obj.sql,
                    results,
                    columns
                )
                
                # Auto-save learned patterns and vectors after successful processing
                try:
                    self.save_system_state()
                except Exception as e:
                    logger.warning(f"Auto-save failed after successful query: {e}")
                return RAGQueryResult(
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
                        'database': get_current_database(),
                        'tables_used': sql_query_obj.tables_used
                    },
                    natural_language_response=natural_language_response
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
            self.stats.failed_queries += 1
            
            logger.error(f"Unexpected error processing query: {e}")
            
            return RAGQueryResult(
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
                           start_time: float) -> RAGQueryResult:
        """Handle query execution errors with recovery"""
        processing_time = time.time() - start_time
        self.stats.failed_queries += 1
        
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
                    # Handle other error types
                    recovery_plan = self.error_handler.handle_execution_error(mock_error, query_context)
                
                logger.info(f"Generated recovery plan with {len(recovery_plan.suggestions)} suggestions")
                
            except Exception as recovery_error:
                logger.error(f"Error recovery failed: {recovery_error}")
        
        # Auto-save learned error patterns and vectors after handling an error
        try:
            self.save_system_state()
        except Exception as e:
            logger.warning(f"Auto-save failed after error handling: {e}")
        return RAGQueryResult(
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
    
    def _update_success_stats(self, confidence: float, processing_time: float):
        """Update success statistics"""
        # Update average confidence
        total_successful = self.stats.successful_queries
        if total_successful <= 0:
            # Handle edge case where successful_queries is 0 or negative
            self.stats.average_confidence = 0.0
        elif total_successful == 1:
            self.stats.average_confidence = confidence
        else:
            self.stats.average_confidence = (
                (self.stats.average_confidence * (total_successful - 1) + confidence) / total_successful
            )
        
        # Update average processing time
        if total_successful <= 0:
            # Handle edge case where successful_queries is 0 or negative
            self.stats.average_processing_time = 0.0
        elif total_successful == 1:
            self.stats.average_processing_time = processing_time
        else:
            self.stats.average_processing_time = (
                (self.stats.average_processing_time * (total_successful - 1) + processing_time) / total_successful
            )
        
        # Update error recovery rate
        if self.stats.total_queries_processed > 0:
            self.stats.error_recovery_rate = self.stats.successful_queries / self.stats.total_queries_processed
        else:
            self.stats.error_recovery_rate = 0.0 # Ensure it's 0.0 if no queries processed
        
        # Update learned patterns count
        if self.learning_engine:
            self.stats.learned_patterns_count = len(self.learning_engine.success_patterns)
        
        self.stats.last_updated = datetime.now()
    
    def get_system_statistics(self) -> RAGSystemStats:
        """Get current system statistics"""
        # Update vector store size
        self.stats.vector_store_size = len(self.vector_store.schema_vectors)
        
        # Update learned patterns count
        if self.learning_engine:
            self.stats.learned_patterns_count = len(self.learning_engine.success_patterns)
        
        return self.stats
    
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
    
    def get_similar_queries(self, query: str, k: int = 5) -> List[Tuple[str, str, float]]:
        """
        Get similar queries from learned patterns.
        
        Args:
            query: Natural language query
            k: Number of similar queries to return
            
        Returns:
            List of tuples (nl_query, sql_query, similarity_score)
        """
        if not self.learning_engine:
            return []
        
        similar_patterns = self.learning_engine.find_similar_success_patterns(query, k=k)
        
        return [
            (pattern.natural_language_query, pattern.sql_query, similarity)
            for pattern, similarity in similar_patterns
        ]
    
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


def create_rag_agent(config_overrides: Dict[str, Any] = None) -> RAGSQLAgent:
    """
    Factory function to create a RAG SQL Agent.
    
    Args:
        config_overrides: Configuration overrides
        
    Returns:
        Initialized RAGSQLAgent instance
    """
    return RAGSQLAgent(config_overrides=config_overrides)


# Example usage and testing
if __name__ == "__main__":
    # Create RAG agent
    agent = create_rag_agent()
    atexit.register(agent.shutdown)
    
    # Test queries
    test_queries = [
        "How many employees are there?",
        "Show me all projects",
        "What is the average salary by department?",
        "List employees who worked more than 40 hours last month"
    ]
    
    print("=== RAG SQL Agent Test ===\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        result = agent.process_query(query)
        
        print(f"Success: {result.success}")
        print(f"SQL: {result.sql_query}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Processing Time: {result.processing_time:.3f}s")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        if result.recovery_plan:
            print(f"Recovery Suggestions: {len(result.recovery_plan.suggestions)}")
        
        print("-" * 50)
    
    # Show system statistics
    stats = agent.get_system_statistics()
    print(f"\nSystem Statistics:")
    print(f"Total Queries: {stats.total_queries_processed}")
    print(f"Success Rate: {stats.successful_queries / stats.total_queries_processed * 100:.1f}%")
    print(f"Average Confidence: {stats.average_confidence:.3f}")
    print(f"Vector Store Size: {stats.vector_store_size}")
    print(f"Learned Patterns: {stats.learned_patterns_count}")