#!/usr/bin/env python3
"""
SemanticErrorHandler - Intelligent error recovery using vector similarity and semantic understanding.

This module implements advanced error handling that uses vector embeddings to provide
intelligent recovery suggestions, schema error correction, and adaptive error learning.
"""

import numpy as np
import re
import json
import os
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging
from sentence_transformers import SentenceTransformer
import difflib

# Import existing components
from vector_schema_store import VectorSchemaStore, TableMatch, ColumnMatch
from semantic_intent_engine import SemanticIntentEngine, QueryIntent, EntityType
from adaptive_learning_engine import AdaptiveLearningEngine, ErrorPattern

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can be handled"""
    SCHEMA_ERROR = "schema_error"
    SYNTAX_ERROR = "syntax_error"
    EXECUTION_ERROR = "execution_error"
    SEMANTIC_ERROR = "semantic_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Error recovery strategies"""
    SCHEMA_SUGGESTION = "schema_suggestion"
    QUERY_SIMPLIFICATION = "query_simplification"
    AUTOMATIC_CORRECTION = "automatic_correction"
    FUZZY_MATCHING = "fuzzy_matching"
    PATTERN_BASED = "pattern_based"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    error_id: str
    error_type: ErrorType
    error_message: str
    original_query: str
    failed_sql: Optional[str]
    severity: ErrorSeverity
    confidence: float
    timestamp: datetime
    context: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class RecoveryPlan:
    """Error recovery plan with suggestions"""
    recovery_id: str
    error_info: ErrorInfo
    strategy: RecoveryStrategy
    suggestions: List['RecoverySuggestion']
    confidence: float
    estimated_success_rate: float
    automatic_retry: bool
    metadata: Dict[str, Any]


@dataclass
class RecoverySuggestion:
    """Individual recovery suggestion"""
    suggestion_id: str
    suggestion_type: str
    description: str
    corrected_query: Optional[str]
    corrected_sql: Optional[str]
    confidence: float
    reasoning: str
    example: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class SchemaAlternative:
    """Alternative schema element suggestion"""
    element_type: str  # 'table' or 'column'
    original_name: str
    suggested_name: str
    similarity_score: float
    confidence: float
    schema_name: str
    metadata: Dict[str, Any]


class SemanticErrorHandler:
    """
    Intelligent error recovery using vector similarity and semantic understanding.
    
    This class provides advanced error handling capabilities that leverage vector
    embeddings to understand errors semantically and provide intelligent recovery
    suggestions.
    """
    
    def __init__(self,
                 vector_store: VectorSchemaStore,
                 intent_engine: SemanticIntentEngine,
                 learning_engine: AdaptiveLearningEngine,
                 error_data_path: str = "vector_data/error_patterns",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the SemanticErrorHandler.
        
        Args:
            vector_store: VectorSchemaStore instance for schema context
            intent_engine: SemanticIntentEngine for query understanding
            learning_engine: AdaptiveLearningEngine for pattern learning
            error_data_path: Path to store error patterns
            embedding_model: Sentence transformer model name
        """
        self.vector_store = vector_store
        self.intent_engine = intent_engine
        self.learning_engine = learning_engine
        self.error_data_path = error_data_path
        self.embedding_model_name = embedding_model
        self.embedder = SentenceTransformer(embedding_model)
        
        # Storage for error patterns and recovery strategies
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.recovery_history: Dict[str, RecoveryPlan] = {}
        self.schema_alternatives_cache: Dict[str, List[SchemaAlternative]] = {}
        
        # Error handling statistics
        self.error_stats = {
            'total_errors_handled': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'automatic_corrections': 0,
            'manual_interventions': 0,
            'last_error_session': None
        }
        
        # Ensure storage directory exists
        os.makedirs(error_data_path, exist_ok=True)
        
        # Load existing error patterns
        self._load_error_patterns_from_disk()
        
        logger.info(f"SemanticErrorHandler initialized with {len(self.error_patterns)} error patterns")
    
    def handle_schema_error(self, error: Exception, query_context: Dict[str, Any]) -> RecoveryPlan:
        """
        Handle schema-related errors using vector similarity.
        
        Args:
            error: The schema error exception
            query_context: Context information about the query
            
        Returns:
            RecoveryPlan with schema-based recovery suggestions
        """
        logger.info(f"Handling schema error: {str(error)[:100]}...")
        
        # Create error info
        error_info = self._create_error_info(
            error=error,
            error_type=ErrorType.SCHEMA_ERROR,
            query_context=query_context
        )
        
        # Detect missing schema elements
        missing_elements = self._detect_missing_schema_elements(str(error), query_context)
        
        # Generate recovery suggestions
        suggestions = []
        
        # 1. Find similar schema elements using vector similarity
        for element in missing_elements:
            similar_elements = self._find_similar_schema_elements(
                element['name'], 
                element['type'],
                query_context.get('original_query', '')
            )
            
            for similar_element in similar_elements:
                suggestions.append(RecoverySuggestion(
                    suggestion_id=f"schema_sim_{len(suggestions)}",
                    suggestion_type="schema_similarity",
                    description=f"Did you mean '{similar_element.suggested_name}' instead of '{element['name']}'?",
                    corrected_query=self._generate_corrected_query(
                        query_context.get('original_query', ''),
                        element['name'],
                        similar_element.suggested_name
                    ),
                    corrected_sql=self._generate_corrected_sql(
                        query_context.get('failed_sql', ''),
                        element['name'],
                        similar_element.suggested_name
                    ),
                    confidence=similar_element.confidence,
                    reasoning=f"Vector similarity score: {similar_element.similarity_score:.3f}",
                    example=f"Use [{similar_element.schema_name}].[{similar_element.suggested_name}]",
                    metadata={
                        'original_element': element['name'],
                        'suggested_element': similar_element.suggested_name,
                        'similarity_score': similar_element.similarity_score,
                        'element_type': element['type']
                    }
                ))
        
        # 2. Fuzzy matching for typos and variations
        fuzzy_suggestions = self._generate_fuzzy_matching_suggestions(missing_elements, query_context)
        suggestions.extend(fuzzy_suggestions)
        
        # 3. Context-aware schema recommendations
        context_suggestions = self._generate_context_aware_suggestions(missing_elements, query_context)
        suggestions.extend(context_suggestions)
        
        # Sort suggestions by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        # Create recovery plan
        recovery_plan = RecoveryPlan(
            recovery_id=f"schema_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            error_info=error_info,
            strategy=RecoveryStrategy.SCHEMA_SUGGESTION,
            suggestions=suggestions[:5],  # Top 5 suggestions
            confidence=max([s.confidence for s in suggestions]) if suggestions else 0.0,
            estimated_success_rate=self._estimate_recovery_success_rate(suggestions),
            automatic_retry=len(suggestions) > 0 and suggestions[0].confidence > 0.8,
            metadata={
                'missing_elements': missing_elements,
                'total_suggestions': len(suggestions),
                'recovery_strategy': 'vector_similarity_based'
            }
        )
        
        # Store recovery plan
        self.recovery_history[recovery_plan.recovery_id] = recovery_plan
        
        # Learn from this error
        self._learn_from_schema_error(error_info, recovery_plan)
        
        # Update statistics
        self.error_stats['total_errors_handled'] += 1
        self.error_stats['last_error_session'] = datetime.now().isoformat()
        
        logger.info(f"Generated {len(suggestions)} recovery suggestions for schema error")
        return recovery_plan
    
    def _detect_missing_schema_elements(self, error_message: str, query_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect missing tables, columns, or other schema elements from error message.
        
        Args:
            error_message: The error message string
            query_context: Query context information
            
        Returns:
            List of missing schema elements with their types
        """
        missing_elements = []
        error_lower = error_message.lower()
        
        # Common SQL Server error patterns
        patterns = [
            # Invalid object name (table/view)
            (r"invalid object name '([^']+)'", 'table'),
            (r"invalid object name \"([^\"]+)\"", 'table'),
            (r"invalid object name \[([^\]]+)\]", 'table'),
            
            # Invalid column name
            (r"invalid column name '([^']+)'", 'column'),
            (r"invalid column name \"([^\"]+)\"", 'column'),
            (r"invalid column name \[([^\]]+)\]", 'column'),
            
            # Object doesn't exist
            (r"object '([^']+)' doesn't exist", 'table'),
            (r"table '([^']+)' doesn't exist", 'table'),
            (r"column '([^']+)' doesn't exist", 'column'),
            
            # Cannot find object
            (r"cannot find the object \"([^\"]+)\"", 'table'),
            (r"cannot find column \"([^\"]+)\"", 'column'),
        ]
        
        for pattern, element_type in patterns:
            matches = re.finditer(pattern, error_message, re.IGNORECASE)
            for match in matches:
                element_name = match.group(1)
                
                # Clean up element name (remove schema prefix if present)
                if '.' in element_name:
                    parts = element_name.split('.')
                    element_name = parts[-1]  # Take the last part (actual table/column name)
                
                missing_elements.append({
                    'name': element_name,
                    'type': element_type,
                    'original_text': match.group(0),
                    'position': match.span()
                })
        
        # If no specific patterns matched, try to extract from SQL
        if not missing_elements and query_context.get('failed_sql'):
            missing_elements.extend(self._extract_elements_from_sql(query_context['failed_sql']))
        
        return missing_elements
    
    def _extract_elements_from_sql(self, sql_query: str) -> List[Dict[str, Any]]:
        """Extract potential missing elements from SQL query"""
        elements = []
        
        # Extract table names from FROM and JOIN clauses
        table_patterns = [
            r'FROM\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
            r'JOIN\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
            r'UPDATE\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
            r'INSERT\s+INTO\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)'
        ]
        
        for pattern in table_patterns:
            matches = re.finditer(pattern, sql_query, re.IGNORECASE)
            for match in matches:
                # Get the table name (second group if schema.table, first group if just table)
                table_name = match.group(2) if match.group(2) else match.group(1)
                if table_name:
                    elements.append({
                        'name': table_name,
                        'type': 'table',
                        'original_text': match.group(0),
                        'position': match.span()
                    })
        
        # Extract column names from SELECT, WHERE, ORDER BY clauses
        # This is more complex and might need refinement
        column_patterns = [
            r'SELECT\s+.*?(\w+)(?:\s*,|\s+FROM)',
            r'WHERE\s+.*?(\w+)\s*[=<>!]',
            r'ORDER\s+BY\s+(\w+)',
            r'GROUP\s+BY\s+(\w+)'
        ]
        
        for pattern in column_patterns:
            matches = re.finditer(pattern, sql_query, re.IGNORECASE | re.DOTALL)
            for match in matches:
                column_name = match.group(1)
                if column_name and column_name.upper() not in ['FROM', 'WHERE', 'ORDER', 'GROUP', 'BY']:
                    elements.append({
                        'name': column_name,
                        'type': 'column',
                        'original_text': match.group(0),
                        'position': match.span()
                    })
        
        return elements
    
    def _find_similar_schema_elements(self, 
                                    element_name: str, 
                                    element_type: str,
                                    original_query: str) -> List[SchemaAlternative]:
        """
        Find similar schema elements using vector similarity.
        
        Args:
            element_name: Name of the missing element
            element_type: Type of element ('table' or 'column')
            original_query: Original natural language query for context
            
        Returns:
            List of SchemaAlternative objects
        """
        # Check cache first
        cache_key = f"{element_type}:{element_name}"
        if cache_key in self.schema_alternatives_cache:
            return self.schema_alternatives_cache[cache_key]
        
        alternatives = []
        
        # Generate embedding for the missing element with context
        context_text = f"{element_name} {original_query}"
        query_vector = self._normalize_vector(self.embedder.encode(context_text))
        
        if element_type == 'table':
            # Find similar tables
            similar_tables = self.vector_store.find_similar_tables(query_vector, k=5)
            
            for table_match in similar_tables:
                # Calculate string similarity for additional confidence
                string_similarity = difflib.SequenceMatcher(
                    None, 
                    element_name.lower(), 
                    table_match.table_name.lower()
                ).ratio()
                
                # Combined confidence from vector similarity and string similarity
                combined_confidence = (table_match.similarity_score * 0.7 + string_similarity * 0.3)
                
                alternatives.append(SchemaAlternative(
                    element_type='table',
                    original_name=element_name,
                    suggested_name=table_match.table_name,
                    similarity_score=table_match.similarity_score,
                    confidence=combined_confidence,
                    schema_name=table_match.schema_name,
                    metadata={
                        'string_similarity': string_similarity,
                        'vector_similarity': table_match.similarity_score,
                        'context_relevance': table_match.context_relevance,
                        'business_priority': table_match.business_priority,
                        'table_metadata': table_match.metadata
                    }
                ))
        
        elif element_type == 'column':
            # Find similar columns
            similar_columns = self.vector_store.find_similar_columns(query_vector, k=5)
            
            for column_match in similar_columns:
                # Calculate string similarity
                string_similarity = difflib.SequenceMatcher(
                    None, 
                    element_name.lower(), 
                    column_match.column_name.lower()
                ).ratio()
                
                # Combined confidence
                combined_confidence = (column_match.similarity_score * 0.7 + string_similarity * 0.3)
                
                alternatives.append(SchemaAlternative(
                    element_type='column',
                    original_name=element_name,
                    suggested_name=column_match.column_name,
                    similarity_score=column_match.similarity_score,
                    confidence=combined_confidence,
                    schema_name=column_match.schema_name,
                    metadata={
                        'string_similarity': string_similarity,
                        'vector_similarity': column_match.similarity_score,
                        'context_relevance': column_match.context_relevance,
                        'table_name': column_match.table_name,
                        'data_type': column_match.data_type,
                        'column_metadata': column_match.metadata
                    }
                ))
        
        # Sort by confidence and filter low-confidence suggestions
        alternatives = [alt for alt in alternatives if alt.confidence > 0.3]
        alternatives.sort(key=lambda x: x.confidence, reverse=True)
        
        # Cache the results
        self.schema_alternatives_cache[cache_key] = alternatives[:5]  # Cache top 5
        
        return alternatives[:5]
    
    def _generate_fuzzy_matching_suggestions(self, 
                                           missing_elements: List[Dict[str, Any]], 
                                           query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """
        Generate suggestions using fuzzy string matching for typos and variations.
        
        Args:
            missing_elements: List of missing schema elements
            query_context: Query context information
            
        Returns:
            List of RecoverySuggestion objects
        """
        suggestions = []
        
        # Get all available schema elements
        all_tables = self.vector_store.get_all_vectors_by_type('table')
        all_columns = self.vector_store.get_all_vectors_by_type('column')
        
        for element in missing_elements:
            element_name = element['name']
            element_type = element['type']
            
            candidates = []
            
            if element_type == 'table':
                candidates = [(table.element_name, table.schema_name) for table in all_tables]
            elif element_type == 'column':
                candidates = [(column.element_name, column.metadata.get('table_name', '')) for column in all_columns]
            
            # Find fuzzy matches
            fuzzy_matches = []
            for candidate_name, context_name in candidates:
                similarity = difflib.SequenceMatcher(None, element_name.lower(), candidate_name.lower()).ratio()
                
                if similarity > 0.6:  # Threshold for fuzzy matching
                    fuzzy_matches.append((candidate_name, context_name, similarity))
            
            # Sort by similarity
            fuzzy_matches.sort(key=lambda x: x[2], reverse=True)
            
            # Create suggestions for top fuzzy matches
            for candidate_name, context_name, similarity in fuzzy_matches[:3]:
                suggestions.append(RecoverySuggestion(
                    suggestion_id=f"fuzzy_{element_type}_{len(suggestions)}",
                    suggestion_type="fuzzy_matching",
                    description=f"Fuzzy match: '{candidate_name}' (similarity: {similarity:.2f})",
                    corrected_query=self._generate_corrected_query(
                        query_context.get('original_query', ''),
                        element_name,
                        candidate_name
                    ),
                    corrected_sql=self._generate_corrected_sql(
                        query_context.get('failed_sql', ''),
                        element_name,
                        candidate_name
                    ),
                    confidence=similarity * 0.8,  # Slightly lower confidence for fuzzy matches
                    reasoning=f"String similarity: {similarity:.3f} - possible typo in '{element_name}'",
                    example=f"Try using '{candidate_name}' instead of '{element_name}'",
                    metadata={
                        'original_element': element_name,
                        'suggested_element': candidate_name,
                        'similarity_score': similarity,
                        'match_type': 'fuzzy_string',
                        'context_name': context_name
                    }
                ))
        
        return suggestions
    
    def _generate_context_aware_suggestions(self, 
                                          missing_elements: List[Dict[str, Any]], 
                                          query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """
        Generate context-aware suggestions based on query intent and semantic understanding.
        
        Args:
            missing_elements: List of missing schema elements
            query_context: Query context information
            
        Returns:
            List of RecoverySuggestion objects
        """
        suggestions = []
        
        # Analyze query intent if available
        original_query = query_context.get('original_query', '')
        if original_query:
            try:
                query_intent = self.intent_engine.analyze_query(original_query)
                
                # Use intent to suggest relevant schema elements
                for element in missing_elements:
                    context_suggestions = self._get_intent_based_suggestions(
                        element, query_intent, query_context
                    )
                    suggestions.extend(context_suggestions)
                    
            except Exception as e:
                logger.warning(f"Failed to analyze query intent for context suggestions: {e}")
        
        return suggestions
    
    def _get_intent_based_suggestions(self, 
                                    missing_element: Dict[str, Any], 
                                    query_intent: QueryIntent,
                                    query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """Get suggestions based on query intent analysis"""
        suggestions = []
        
        # Map intent types to likely schema elements
        intent_to_elements = {
            'count': ['id', 'count', 'total', 'number'],
            'sum': ['amount', 'total', 'sum', 'value', 'cost', 'price'],
            'average': ['amount', 'value', 'score', 'rating', 'cost'],
            'max': ['amount', 'value', 'date', 'score', 'max'],
            'min': ['amount', 'value', 'date', 'score', 'min'],
            'select': ['name', 'title', 'description', 'id'],
            'filter': ['status', 'type', 'category', 'active', 'enabled']
        }
        
        intent_type = query_intent.intent_type.value
        likely_elements = intent_to_elements.get(intent_type, [])
        
        if likely_elements:
            # Find schema elements that match the intent
            all_elements = []
            if missing_element['type'] == 'table':
                all_elements = self.vector_store.get_all_vectors_by_type('table')
            elif missing_element['type'] == 'column':
                all_elements = self.vector_store.get_all_vectors_by_type('column')
            
            for schema_element in all_elements:
                element_name_lower = schema_element.element_name.lower()
                
                # Check if element name contains intent-related keywords
                for keyword in likely_elements:
                    if keyword in element_name_lower:
                        confidence = 0.6 + (0.2 * query_intent.confidence)
                        
                        suggestions.append(RecoverySuggestion(
                            suggestion_id=f"intent_{missing_element['type']}_{len(suggestions)}",
                            suggestion_type="intent_based",
                            description=f"Based on your query intent ({intent_type}), try '{schema_element.element_name}'",
                            corrected_query=self._generate_corrected_query(
                                query_context.get('original_query', ''),
                                missing_element['name'],
                                schema_element.element_name
                            ),
                            corrected_sql=self._generate_corrected_sql(
                                query_context.get('failed_sql', ''),
                                missing_element['name'],
                                schema_element.element_name
                            ),
                            confidence=confidence,
                            reasoning=f"Query intent '{intent_type}' suggests '{keyword}'-related elements",
                            example=f"For {intent_type} queries, '{schema_element.element_name}' is commonly used",
                            metadata={
                                'intent_type': intent_type,
                                'intent_confidence': query_intent.confidence,
                                'matched_keyword': keyword,
                                'schema_element': schema_element.element_name
                            }
                        ))
                        break  # Only add one suggestion per element
        
        return suggestions[:3]  # Limit to top 3 intent-based suggestions
    
    def _generate_corrected_query(self, original_query: str, old_element: str, new_element: str) -> Optional[str]:
        """Generate corrected natural language query"""
        if not original_query:
            return None
        
        # Simple replacement - could be made more sophisticated
        corrected = original_query.replace(old_element, new_element)
        
        # If no replacement was made, try case-insensitive replacement
        if corrected == original_query:
            corrected = re.sub(re.escape(old_element), new_element, original_query, flags=re.IGNORECASE)
        
        return corrected if corrected != original_query else None
    
    def _generate_corrected_sql(self, original_sql: str, old_element: str, new_element: str) -> Optional[str]:
        """Generate corrected SQL query"""
        if not original_sql:
            return None
        
        # Replace element name in SQL, handling various SQL identifier formats
        patterns = [
            f"\\b{re.escape(old_element)}\\b",  # Bare identifier
            f"\\[{re.escape(old_element)}\\]",  # Bracketed identifier
            f"'{re.escape(old_element)}'",      # Quoted identifier
            f'"{re.escape(old_element)}"'       # Double-quoted identifier
        ]
        
        corrected = original_sql
        for pattern in patterns:
            corrected = re.sub(pattern, new_element, corrected, flags=re.IGNORECASE)
        
        return corrected if corrected != original_sql else None
    
    def _create_error_info(self, 
                          error: Exception, 
                          error_type: ErrorType,
                          query_context: Dict[str, Any]) -> ErrorInfo:
        """Create comprehensive error information"""
        error_message = str(error)
        
        # Determine severity based on error type and message
        severity = ErrorSeverity.MEDIUM
        if "critical" in error_message.lower() or "fatal" in error_message.lower():
            severity = ErrorSeverity.CRITICAL
        elif "warning" in error_message.lower():
            severity = ErrorSeverity.LOW
        elif "timeout" in error_message.lower() or "connection" in error_message.lower():
            severity = ErrorSeverity.HIGH
        
        # Calculate confidence based on error clarity
        confidence = 0.8
        if "invalid object name" in error_message.lower() or "invalid column name" in error_message.lower():
            confidence = 0.9  # Very clear schema errors
        elif "syntax error" in error_message.lower():
            confidence = 0.7  # Syntax errors can be ambiguous
        
        return ErrorInfo(
            error_id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            error_type=error_type,
            error_message=error_message,
            original_query=query_context.get('original_query', ''),
            failed_sql=query_context.get('failed_sql'),
            severity=severity,
            confidence=confidence,
            timestamp=datetime.now(),
            context=query_context,
            metadata={
                'error_class': error.__class__.__name__,
                'error_module': error.__class__.__module__
            }
        )
    
    def _estimate_recovery_success_rate(self, suggestions: List[RecoverySuggestion]) -> float:
        """Estimate the success rate of recovery based on suggestions"""
        if not suggestions:
            return 0.0
        
        # Base success rate on the confidence of the best suggestion
        best_confidence = max(s.confidence for s in suggestions)
        
        # Adjust based on number of suggestions (more options = higher chance)
        suggestion_bonus = min(0.2, len(suggestions) * 0.05)
        
        # Adjust based on suggestion types (some are more reliable)
        type_bonus = 0.0
        for suggestion in suggestions:
            if suggestion.suggestion_type == "schema_similarity":
                type_bonus += 0.1
            elif suggestion.suggestion_type == "fuzzy_matching":
                type_bonus += 0.05
        
        estimated_rate = min(0.95, best_confidence + suggestion_bonus + type_bonus)
        return estimated_rate
    
    def _learn_from_schema_error(self, error_info: ErrorInfo, recovery_plan: RecoveryPlan) -> None:
        """Learn from schema error for future improvements"""
        try:
            # Create error pattern for learning
            error_pattern = ErrorPattern(
                error_id=error_info.error_id,
                error_type=error_info.error_type.value,
                original_query=error_info.original_query,
                failed_sql=error_info.failed_sql or '',
                error_message=error_info.error_message,
                correction=recovery_plan.suggestions[0].corrected_sql if recovery_plan.suggestions else None,
                query_vector=self._normalize_vector(self.embedder.encode(error_info.original_query)),
                confidence=error_info.confidence,
                occurrence_count=1,
                last_occurred=error_info.timestamp,
                created_at=error_info.timestamp,
                metadata={
                    'recovery_strategy': recovery_plan.strategy.value,
                    'suggestions_count': len(recovery_plan.suggestions),
                    'estimated_success_rate': recovery_plan.estimated_success_rate
                }
            )
            
            # Store in learning engine if available
            if hasattr(self.learning_engine, 'learn_from_error'):
                self.learning_engine.learn_from_error(
                    error_info.original_query,
                    error_info,
                    recovery_plan.suggestions[0].corrected_sql if recovery_plan.suggestions else None
                )
            
            # Store locally
            self.error_patterns[error_info.error_id] = error_pattern
            
        except Exception as e:
            logger.warning(f"Failed to learn from schema error: {e}")
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector for cosine similarity"""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def _load_error_patterns_from_disk(self) -> None:
        """Load error patterns from disk"""
        try:
            error_patterns_path = os.path.join(self.error_data_path, "error_patterns.json")
            
            if os.path.exists(error_patterns_path):
                with open(error_patterns_path, 'r') as f:
                    error_patterns_data = json.load(f)
                
                for error_id, pattern_dict in error_patterns_data.items():
                    # Convert lists back to numpy arrays
                    pattern_dict['query_vector'] = np.array(pattern_dict['query_vector'])
                    pattern_dict['last_occurred'] = datetime.fromisoformat(pattern_dict['last_occurred'])
                    pattern_dict['created_at'] = datetime.fromisoformat(pattern_dict['created_at'])
                    
                    self.error_patterns[error_id] = ErrorPattern(**pattern_dict)
            
            logger.info(f"Loaded {len(self.error_patterns)} error patterns from disk")
            
        except Exception as e:
            logger.warning(f"Could not load error patterns from disk: {e}")
            self.error_patterns = {}
    
    def save_error_patterns_to_disk(self) -> None:
        """Save error patterns to disk"""
        try:
            error_patterns_data = {}
            for error_id, pattern in self.error_patterns.items():
                pattern_dict = asdict(pattern)
                # Convert numpy arrays to lists for JSON serialization
                pattern_dict['query_vector'] = pattern.query_vector.tolist()
                pattern_dict['last_occurred'] = pattern.last_occurred.isoformat()
                pattern_dict['created_at'] = pattern.created_at.isoformat()
                error_patterns_data[error_id] = pattern_dict
            
            error_patterns_path = os.path.join(self.error_data_path, "error_patterns.json")
            with open(error_patterns_path, 'w') as f:
                json.dump(error_patterns_data, f, indent=2)
            
            logger.info(f"Saved {len(self.error_patterns)} error patterns to disk")
            
        except Exception as e:
            logger.error(f"Error saving error patterns to disk: {e}")
            raise
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error handling statistics"""
        stats = self.error_stats.copy()
        
        # Add pattern statistics
        stats.update({
            'error_patterns_count': len(self.error_patterns),
            'recovery_plans_count': len(self.recovery_history),
            'cached_alternatives_count': len(self.schema_alternatives_cache),
            'success_rate': (
                self.error_stats['successful_recoveries'] / 
                max(1, self.error_stats['total_errors_handled'])
            ),
            'automatic_correction_rate': (
                self.error_stats['automatic_corrections'] / 
                max(1, self.error_stats['total_errors_handled'])
            )
        })
        
        return stats
    
    def handle_syntax_error(self, error: Exception, query_context: Dict[str, Any]) -> RecoveryPlan:
        """
        Handle SQL syntax errors with intelligent correction suggestions.
        
        Args:
            error: The syntax error exception
            query_context: Context information about the query
            
        Returns:
            RecoveryPlan with syntax correction suggestions
        """
        logger.info(f"Handling syntax error: {str(error)[:100]}...")
        
        # Create error info
        error_info = self._create_error_info(
            error=error,
            error_type=ErrorType.SYNTAX_ERROR,
            query_context=query_context
        )
        
        # Analyze the syntax error
        syntax_issues = self._analyze_syntax_error(str(error), query_context.get('failed_sql', ''))
        
        # Generate correction suggestions
        suggestions = []
        
        # 1. Pattern-based syntax corrections
        pattern_suggestions = self._generate_syntax_pattern_corrections(syntax_issues, query_context)
        suggestions.extend(pattern_suggestions)
        
        # 2. Common SQL syntax fixes
        common_fixes = self._generate_common_syntax_fixes(syntax_issues, query_context)
        suggestions.extend(common_fixes)
        
        # 3. Query simplification suggestions
        simplification_suggestions = self._generate_query_simplification_suggestions(query_context)
        suggestions.extend(simplification_suggestions)
        
        # Sort suggestions by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        # Create recovery plan
        recovery_plan = RecoveryPlan(
            recovery_id=f"syntax_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            error_info=error_info,
            strategy=RecoveryStrategy.AUTOMATIC_CORRECTION,
            suggestions=suggestions[:5],  # Top 5 suggestions
            confidence=max([s.confidence for s in suggestions]) if suggestions else 0.0,
            estimated_success_rate=self._estimate_recovery_success_rate(suggestions),
            automatic_retry=len(suggestions) > 0 and suggestions[0].confidence > 0.7,
            metadata={
                'syntax_issues': syntax_issues,
                'total_suggestions': len(suggestions),
                'recovery_strategy': 'syntax_correction'
            }
        )
        
        # Store recovery plan
        self.recovery_history[recovery_plan.recovery_id] = recovery_plan
        
        # Learn from this error
        self._learn_from_syntax_error(error_info, recovery_plan)
        
        # Update statistics
        self.error_stats['total_errors_handled'] += 1
        if recovery_plan.automatic_retry:
            self.error_stats['automatic_corrections'] += 1
        
        logger.info(f"Generated {len(suggestions)} syntax correction suggestions")
        return recovery_plan
    
    def handle_execution_error(self, error: Exception, query_context: Dict[str, Any]) -> RecoveryPlan:
        """
        Handle SQL execution errors with recovery suggestions.
        
        Args:
            error: The execution error exception
            query_context: Context information about the query
            
        Returns:
            RecoveryPlan with execution error recovery suggestions
        """
        logger.info(f"Handling execution error: {str(error)[:100]}...")
        
        # Create error info
        error_info = self._create_error_info(
            error=error,
            error_type=ErrorType.EXECUTION_ERROR,
            query_context=query_context
        )
        
        # Analyze the execution error
        execution_issues = self._analyze_execution_error(str(error), query_context)
        
        # Generate recovery suggestions
        suggestions = []
        
        # 1. Query optimization suggestions
        optimization_suggestions = self._generate_optimization_suggestions(execution_issues, query_context)
        suggestions.extend(optimization_suggestions)
        
        # 2. Permission and access error handling
        permission_suggestions = self._generate_permission_error_suggestions(execution_issues, query_context)
        suggestions.extend(permission_suggestions)
        
        # 3. Data type and constraint error handling
        constraint_suggestions = self._generate_constraint_error_suggestions(execution_issues, query_context)
        suggestions.extend(constraint_suggestions)
        
        # 4. Timeout and performance error handling
        performance_suggestions = self._generate_performance_error_suggestions(execution_issues, query_context)
        suggestions.extend(performance_suggestions)
        
        # Sort suggestions by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        # Create recovery plan
        recovery_plan = RecoveryPlan(
            recovery_id=f"execution_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            error_info=error_info,
            strategy=RecoveryStrategy.QUERY_SIMPLIFICATION,
            suggestions=suggestions[:5],  # Top 5 suggestions
            confidence=max([s.confidence for s in suggestions]) if suggestions else 0.0,
            estimated_success_rate=self._estimate_recovery_success_rate(suggestions),
            automatic_retry=len(suggestions) > 0 and suggestions[0].confidence > 0.6,
            metadata={
                'execution_issues': execution_issues,
                'total_suggestions': len(suggestions),
                'recovery_strategy': 'execution_optimization'
            }
        )
        
        # Store recovery plan
        self.recovery_history[recovery_plan.recovery_id] = recovery_plan
        
        # Learn from this error
        self._learn_from_execution_error(error_info, recovery_plan)
        
        # Update statistics
        self.error_stats['total_errors_handled'] += 1
        if recovery_plan.automatic_retry:
            self.error_stats['automatic_corrections'] += 1
        
        logger.info(f"Generated {len(suggestions)} execution error recovery suggestions")
        return recovery_plan
    
    def _analyze_syntax_error(self, error_message: str, failed_sql: str) -> List[Dict[str, Any]]:
        """
        Analyze syntax error to identify specific issues.
        
        Args:
            error_message: The error message string
            failed_sql: The failed SQL query
            
        Returns:
            List of identified syntax issues
        """
        issues = []
        error_lower = error_message.lower()
        
        # Common SQL Server syntax error patterns
        syntax_patterns = [
            # Missing commas
            (r"incorrect syntax near '(\w+)'", "missing_comma", "Missing comma before '{}'"),
            
            # Incorrect keywords
            (r"incorrect syntax near '(SELECT|FROM|WHERE|ORDER|GROUP)'", "keyword_error", "Incorrect keyword usage: '{}'"),
            
            # Missing parentheses
            (r"incorrect syntax near '\)'", "missing_opening_paren", "Missing opening parenthesis"),
            (r"incorrect syntax near '\('", "missing_closing_paren", "Missing closing parenthesis"),
            
            # Unclosed quotes
            (r"unclosed quotation mark", "unclosed_quote", "Unclosed quotation mark in string literal"),
            
            # Invalid identifiers
            (r"invalid column name", "invalid_identifier", "Invalid column or table identifier"),
            
            # Missing keywords
            (r"incorrect syntax near 'FROM'", "missing_select", "Missing SELECT keyword"),
            (r"incorrect syntax near 'WHERE'", "missing_from", "Missing FROM clause"),
        ]
        
        for pattern, issue_type, description_template in syntax_patterns:
            matches = re.finditer(pattern, error_message, re.IGNORECASE)
            for match in matches:
                issue_detail = match.group(1) if match.groups() else ""
                issues.append({
                    'type': issue_type,
                    'description': description_template.format(issue_detail),
                    'location': match.span(),
                    'detail': issue_detail,
                    'confidence': 0.8
                })
        
        # Analyze SQL structure for additional issues
        if failed_sql:
            structural_issues = self._analyze_sql_structure(failed_sql)
            issues.extend(structural_issues)
        
        return issues
    
    def _analyze_sql_structure(self, sql_query: str) -> List[Dict[str, Any]]:
        """Analyze SQL structure for common issues"""
        issues = []
        sql_upper = sql_query.upper()
        
        # Check for basic SQL structure
        if 'SELECT' not in sql_upper:
            issues.append({
                'type': 'missing_select',
                'description': 'Missing SELECT statement',
                'location': (0, 0),
                'detail': 'SELECT',
                'confidence': 0.9
            })
        
        if 'SELECT' in sql_upper and 'FROM' not in sql_upper:
            issues.append({
                'type': 'missing_from',
                'description': 'SELECT statement without FROM clause',
                'location': (0, 0),
                'detail': 'FROM',
                'confidence': 0.8
            })
        
        # Check for unmatched parentheses
        open_parens = sql_query.count('(')
        close_parens = sql_query.count(')')
        if open_parens != close_parens:
            issues.append({
                'type': 'unmatched_parentheses',
                'description': f'Unmatched parentheses: {open_parens} opening, {close_parens} closing',
                'location': (0, 0),
                'detail': f'{open_parens}-{close_parens}',
                'confidence': 0.9
            })
        
        # Check for unmatched quotes
        single_quotes = sql_query.count("'") % 2
        double_quotes = sql_query.count('"') % 2
        if single_quotes != 0 or double_quotes != 0:
            issues.append({
                'type': 'unmatched_quotes',
                'description': 'Unmatched quotation marks',
                'location': (0, 0),
                'detail': 'quotes',
                'confidence': 0.8
            })
        
        return issues
    
    def _generate_syntax_pattern_corrections(self, 
                                           syntax_issues: List[Dict[str, Any]], 
                                           query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """Generate syntax corrections based on identified patterns"""
        suggestions = []
        failed_sql = query_context.get('failed_sql', '')
        
        for issue in syntax_issues:
            issue_type = issue['type']
            confidence = issue['confidence']
            
            corrected_sql = None
            description = ""
            reasoning = ""
            
            if issue_type == 'missing_comma':
                # Try to add missing comma
                corrected_sql = self._fix_missing_comma(failed_sql, issue)
                description = "Add missing comma in SELECT list or column list"
                reasoning = "Detected missing comma between identifiers"
                
            elif issue_type == 'missing_opening_paren':
                corrected_sql = self._fix_missing_parenthesis(failed_sql, '(')
                description = "Add missing opening parenthesis"
                reasoning = "Detected unmatched closing parenthesis"
                
            elif issue_type == 'missing_closing_paren':
                corrected_sql = self._fix_missing_parenthesis(failed_sql, ')')
                description = "Add missing closing parenthesis"
                reasoning = "Detected unmatched opening parenthesis"
                
            elif issue_type == 'unclosed_quote':
                corrected_sql = self._fix_unclosed_quote(failed_sql)
                description = "Close unclosed quotation mark"
                reasoning = "Detected unclosed string literal"
                
            elif issue_type == 'missing_select':
                corrected_sql = f"SELECT * FROM ({failed_sql})"
                description = "Add missing SELECT statement"
                reasoning = "Query appears to be missing SELECT keyword"
                
            elif issue_type == 'missing_from':
                corrected_sql = self._fix_missing_from(failed_sql)
                description = "Add missing FROM clause"
                reasoning = "SELECT statement requires FROM clause"
            
            if corrected_sql and corrected_sql != failed_sql:
                suggestions.append(RecoverySuggestion(
                    suggestion_id=f"syntax_fix_{issue_type}_{len(suggestions)}",
                    suggestion_type="syntax_correction",
                    description=description,
                    corrected_query=None,  # Syntax fixes don't change natural language query
                    corrected_sql=corrected_sql,
                    confidence=confidence,
                    reasoning=reasoning,
                    example=f"Corrected SQL: {corrected_sql[:100]}...",
                    metadata={
                        'issue_type': issue_type,
                        'original_issue': issue,
                        'fix_applied': True
                    }
                ))
        
        return suggestions
    
    def _generate_common_syntax_fixes(self, 
                                    syntax_issues: List[Dict[str, Any]], 
                                    query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """Generate common SQL syntax fixes"""
        suggestions = []
        failed_sql = query_context.get('failed_sql', '')
        
        if not failed_sql:
            return suggestions
        
        # Common fixes that can be applied regardless of specific error
        common_fixes = [
            {
                'name': 'add_top_clause',
                'description': 'Add TOP clause to limit results',
                'fix': lambda sql: re.sub(r'SELECT\s+', 'SELECT TOP 100 ', sql, flags=re.IGNORECASE),
                'confidence': 0.6,
                'reasoning': 'Limiting results can prevent timeout and memory issues'
            },
            {
                'name': 'add_brackets_to_identifiers',
                'description': 'Add square brackets around identifiers',
                'fix': lambda sql: self._add_brackets_to_identifiers(sql),
                'confidence': 0.7,
                'reasoning': 'Square brackets prevent issues with reserved words and special characters'
            },
            {
                'name': 'fix_string_literals',
                'description': 'Fix string literal formatting',
                'fix': lambda sql: self._fix_string_literals(sql),
                'confidence': 0.8,
                'reasoning': 'Proper string literal formatting prevents syntax errors'
            },
            {
                'name': 'remove_trailing_semicolon',
                'description': 'Remove trailing semicolon if problematic',
                'fix': lambda sql: sql.rstrip(';').strip(),
                'confidence': 0.5,
                'reasoning': 'Some contexts do not allow trailing semicolons'
            }
        ]
        
        for fix_info in common_fixes:
            try:
                corrected_sql = fix_info['fix'](failed_sql)
                if corrected_sql != failed_sql:
                    suggestions.append(RecoverySuggestion(
                        suggestion_id=f"common_fix_{fix_info['name']}",
                        suggestion_type="common_syntax_fix",
                        description=fix_info['description'],
                        corrected_query=None,
                        corrected_sql=corrected_sql,
                        confidence=fix_info['confidence'],
                        reasoning=fix_info['reasoning'],
                        example=f"Fixed SQL: {corrected_sql[:100]}...",
                        metadata={
                            'fix_type': fix_info['name'],
                            'original_sql_length': len(failed_sql),
                            'corrected_sql_length': len(corrected_sql)
                        }
                    ))
            except Exception as e:
                logger.warning(f"Failed to apply common fix {fix_info['name']}: {e}")
        
        return suggestions
    
    def _generate_query_simplification_suggestions(self, query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """Generate query simplification suggestions for complex failed queries"""
        suggestions = []
        failed_sql = query_context.get('failed_sql', '')
        original_query = query_context.get('original_query', '')
        
        if not failed_sql:
            return suggestions
        
        # Simplification strategies
        simplifications = [
            {
                'name': 'remove_joins',
                'description': 'Simplify by removing JOIN clauses',
                'simplifier': lambda sql: self._remove_joins(sql),
                'confidence': 0.6,
                'reasoning': 'Complex JOINs can cause syntax and performance issues'
            },
            {
                'name': 'remove_subqueries',
                'description': 'Simplify by removing subqueries',
                'simplifier': lambda sql: self._remove_subqueries(sql),
                'confidence': 0.5,
                'reasoning': 'Subqueries can be complex and error-prone'
            },
            {
                'name': 'basic_select',
                'description': 'Create basic SELECT statement',
                'simplifier': lambda sql: self._create_basic_select(sql),
                'confidence': 0.8,
                'reasoning': 'Start with simple SELECT to verify table access'
            },
            {
                'name': 'remove_aggregations',
                'description': 'Remove aggregation functions',
                'simplifier': lambda sql: self._remove_aggregations(sql),
                'confidence': 0.7,
                'reasoning': 'Aggregations can cause GROUP BY and syntax issues'
            }
        ]
        
        for simplification in simplifications:
            try:
                simplified_sql = simplification['simplifier'](failed_sql)
                if simplified_sql and simplified_sql != failed_sql:
                    suggestions.append(RecoverySuggestion(
                        suggestion_id=f"simplify_{simplification['name']}",
                        suggestion_type="query_simplification",
                        description=simplification['description'],
                        corrected_query=self._simplify_natural_language_query(original_query),
                        corrected_sql=simplified_sql,
                        confidence=simplification['confidence'],
                        reasoning=simplification['reasoning'],
                        example=f"Simplified: {simplified_sql[:100]}...",
                        metadata={
                            'simplification_type': simplification['name'],
                            'complexity_reduction': len(failed_sql) - len(simplified_sql)
                        }
                    ))
            except Exception as e:
                logger.warning(f"Failed to apply simplification {simplification['name']}: {e}")
        
        return suggestions
    
    def _analyze_execution_error(self, error_message: str, query_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze execution error to identify specific issues"""
        issues = []
        error_lower = error_message.lower()
        
        # Common execution error patterns
        execution_patterns = [
            # Permission errors
            (r"permission denied|access denied|insufficient privileges", "permission_error", "Insufficient permissions to access resource"),
            
            # Timeout errors
            (r"timeout|query timeout|execution timeout", "timeout_error", "Query execution timeout"),
            
            # Data type errors
            (r"conversion failed|invalid cast|data type mismatch", "data_type_error", "Data type conversion or mismatch error"),
            
            # Constraint violations
            (r"constraint violation|foreign key|primary key|unique constraint", "constraint_error", "Database constraint violation"),
            
            # Resource errors
            (r"out of memory|insufficient memory|disk space", "resource_error", "Insufficient system resources"),
            
            # Connection errors
            (r"connection lost|connection timeout|network error", "connection_error", "Database connection issue"),
        ]
        
        for pattern, issue_type, description in execution_patterns:
            if re.search(pattern, error_message, re.IGNORECASE):
                issues.append({
                    'type': issue_type,
                    'description': description,
                    'confidence': 0.8,
                    'error_text': error_message
                })
        
        return issues
    
    def _generate_optimization_suggestions(self, 
                                         execution_issues: List[Dict[str, Any]], 
                                         query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """Generate query optimization suggestions"""
        suggestions = []
        failed_sql = query_context.get('failed_sql', '')
        
        if not failed_sql:
            return suggestions
        
        # Check for timeout issues
        has_timeout = any(issue['type'] == 'timeout_error' for issue in execution_issues)
        
        if has_timeout:
            # Optimization strategies for timeout issues
            optimizations = [
                {
                    'name': 'add_top_limit',
                    'description': 'Add TOP clause to limit result set',
                    'optimizer': lambda sql: self._add_top_clause(sql, 1000),
                    'confidence': 0.8,
                    'reasoning': 'Limiting results reduces execution time and memory usage'
                },
                {
                    'name': 'add_where_conditions',
                    'description': 'Add WHERE conditions to filter data',
                    'optimizer': lambda sql: self._suggest_where_conditions(sql),
                    'confidence': 0.6,
                    'reasoning': 'Filtering data early improves performance'
                },
                {
                    'name': 'remove_order_by',
                    'description': 'Remove ORDER BY clause',
                    'optimizer': lambda sql: re.sub(r'ORDER\s+BY\s+[^;]+', '', sql, flags=re.IGNORECASE),
                    'confidence': 0.7,
                    'reasoning': 'Sorting large result sets can be expensive'
                }
            ]
            
            for optimization in optimizations:
                try:
                    optimized_sql = optimization['optimizer'](failed_sql)
                    if optimized_sql and optimized_sql != failed_sql:
                        suggestions.append(RecoverySuggestion(
                            suggestion_id=f"optimize_{optimization['name']}",
                            suggestion_type="performance_optimization",
                            description=optimization['description'],
                            corrected_query=None,
                            corrected_sql=optimized_sql,
                            confidence=optimization['confidence'],
                            reasoning=optimization['reasoning'],
                            example=f"Optimized: {optimized_sql[:100]}...",
                            metadata={
                                'optimization_type': optimization['name'],
                                'target_issue': 'timeout_error'
                            }
                        ))
                except Exception as e:
                    logger.warning(f"Failed to apply optimization {optimization['name']}: {e}")
        
        return suggestions
    
    def _generate_permission_error_suggestions(self, 
                                             execution_issues: List[Dict[str, Any]], 
                                             query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """Generate suggestions for permission errors"""
        suggestions = []
        
        has_permission_error = any(issue['type'] == 'permission_error' for issue in execution_issues)
        
        if has_permission_error:
            suggestions.append(RecoverySuggestion(
                suggestion_id="permission_check",
                suggestion_type="permission_guidance",
                description="Check database permissions and access rights",
                corrected_query=None,
                corrected_sql=None,
                confidence=0.9,
                reasoning="Permission errors require administrative intervention",
                example="Contact your database administrator for access",
                metadata={
                    'requires_admin': True,
                    'issue_type': 'permission_error'
                }
            ))
        
        return suggestions
    
    def _generate_constraint_error_suggestions(self, 
                                             execution_issues: List[Dict[str, Any]], 
                                             query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """Generate suggestions for constraint errors"""
        suggestions = []
        
        has_constraint_error = any(issue['type'] == 'constraint_error' for issue in execution_issues)
        
        if has_constraint_error:
            suggestions.append(RecoverySuggestion(
                suggestion_id="constraint_check",
                suggestion_type="constraint_guidance",
                description="Review data constraints and relationships",
                corrected_query=None,
                corrected_sql=None,
                confidence=0.8,
                reasoning="Constraint violations indicate data integrity issues",
                example="Check foreign key relationships and unique constraints",
                metadata={
                    'requires_data_review': True,
                    'issue_type': 'constraint_error'
                }
            ))
        
        return suggestions
    
    def _generate_performance_error_suggestions(self, 
                                              execution_issues: List[Dict[str, Any]], 
                                              query_context: Dict[str, Any]) -> List[RecoverySuggestion]:
        """Generate suggestions for performance-related errors"""
        suggestions = []
        failed_sql = query_context.get('failed_sql', '')
        
        has_resource_error = any(issue['type'] == 'resource_error' for issue in execution_issues)
        
        if has_resource_error and failed_sql:
            suggestions.append(RecoverySuggestion(
                suggestion_id="reduce_memory_usage",
                suggestion_type="performance_optimization",
                description="Reduce memory usage by limiting result set",
                corrected_query=None,
                corrected_sql=self._add_top_clause(failed_sql, 100),
                confidence=0.7,
                reasoning="Large result sets can exhaust system memory",
                example="Use TOP 100 to limit results",
                metadata={
                    'optimization_target': 'memory_usage',
                    'issue_type': 'resource_error'
                }
            ))
        
        return suggestions
    
    # Helper methods for SQL manipulation
    def _fix_missing_comma(self, sql: str, issue: Dict[str, Any]) -> str:
        """Attempt to fix missing comma issues"""
        # This is a simplified implementation - could be more sophisticated
        # Look for patterns like "column1 column2" and insert comma
        pattern = r'(\w+)\s+(\w+)(?=\s+FROM|\s*$)'
        return re.sub(pattern, r'\1, \2', sql, flags=re.IGNORECASE)
    
    def _fix_missing_parenthesis(self, sql: str, paren_type: str) -> str:
        """Attempt to fix missing parenthesis"""
        if paren_type == '(':
            # Add opening parenthesis at the beginning of problematic sections
            return sql  # Simplified - would need more sophisticated logic
        else:  # paren_type == ')'
            # Add closing parenthesis at the end
            return sql + ')'
    
    def _fix_unclosed_quote(self, sql: str) -> str:
        """Attempt to fix unclosed quotes"""
        # Simple approach: add closing quote at the end
        if sql.count("'") % 2 == 1:
            sql += "'"
        if sql.count('"') % 2 == 1:
            sql += '"'
        return sql
    
    def _fix_missing_from(self, sql: str) -> str:
        """Add missing FROM clause"""
        # This is a placeholder - would need more sophisticated logic
        if 'FROM' not in sql.upper():
            # Try to identify table names and add FROM clause
            return sql + " FROM [table_name]"
        return sql
    
    def _add_brackets_to_identifiers(self, sql: str) -> str:
        """Add square brackets around identifiers"""
        # Simplified implementation
        return re.sub(r'\b([a-zA-Z_]\w*)\b', r'[\1]', sql)
    
    def _fix_string_literals(self, sql: str) -> str:
        """Fix string literal formatting"""
        # Ensure proper quoting of string literals
        return sql  # Placeholder implementation
    
    def _remove_joins(self, sql: str) -> str:
        """Remove JOIN clauses from SQL"""
        # Remove all JOIN clauses
        pattern = r'\s+(INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN\s+[^WHERE\s]+(?:\s+ON\s+[^WHERE\s]+)?'
        return re.sub(pattern, '', sql, flags=re.IGNORECASE)
    
    def _remove_subqueries(self, sql: str) -> str:
        """Remove subqueries from SQL"""
        # This is complex - simplified implementation
        return sql  # Placeholder
    
    def _create_basic_select(self, sql: str) -> str:
        """Create basic SELECT statement"""
        # Extract table name and create simple SELECT
        table_match = re.search(r'FROM\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)', sql, re.IGNORECASE)
        if table_match:
            table_name = table_match.group(2) if table_match.group(2) else table_match.group(1)
            return f"SELECT TOP 10 * FROM [{table_name}]"
        return "SELECT TOP 10 * FROM [table_name]"
    
    def _remove_aggregations(self, sql: str) -> str:
        """Remove aggregation functions"""
        # Remove common aggregation functions
        aggregations = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']
        for agg in aggregations:
            pattern = f'{agg}\\s*\\([^)]+\\)'
            sql = re.sub(pattern, '*', sql, flags=re.IGNORECASE)
        
        # Remove GROUP BY and HAVING clauses
        sql = re.sub(r'\s+GROUP\s+BY\s+[^HAVING\s]+', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\s+HAVING\s+[^ORDER\s]+', '', sql, flags=re.IGNORECASE)
        
        return sql
    
    def _add_top_clause(self, sql: str, limit: int) -> str:
        """Add TOP clause to SQL"""
        if 'TOP' not in sql.upper():
            return re.sub(r'SELECT\s+', f'SELECT TOP {limit} ', sql, flags=re.IGNORECASE)
        return sql
    
    def _suggest_where_conditions(self, sql: str) -> str:
        """Suggest WHERE conditions"""
        if 'WHERE' not in sql.upper():
            # Add a placeholder WHERE condition
            return sql + " WHERE 1=1"  # Placeholder condition
        return sql
    
    def _simplify_natural_language_query(self, query: str) -> Optional[str]:
        """Simplify natural language query"""
        if not query:
            return None
        
        # Simple simplification - remove complex phrases
        simplified = re.sub(r'\b(with|having|where|that|which)\b.*', '', query, flags=re.IGNORECASE)
        return simplified.strip() if simplified != query else None
    
    def _learn_from_syntax_error(self, error_info: ErrorInfo, recovery_plan: RecoveryPlan) -> None:
        """Learn from syntax error for future improvements"""
        try:
            # Similar to schema error learning but for syntax patterns
            if hasattr(self.learning_engine, 'learn_from_error'):
                self.learning_engine.learn_from_error(
                    error_info.original_query,
                    error_info,
                    recovery_plan.suggestions[0].corrected_sql if recovery_plan.suggestions else None
                )
        except Exception as e:
            logger.warning(f"Failed to learn from syntax error: {e}")
    
    def _learn_from_execution_error(self, error_info: ErrorInfo, recovery_plan: RecoveryPlan) -> None:
        """Learn from execution error for future improvements"""
        try:
            # Similar to other error learning
            if hasattr(self.learning_engine, 'learn_from_error'):
                self.learning_engine.learn_from_error(
                    error_info.original_query,
                    error_info,
                    recovery_plan.suggestions[0].corrected_sql if recovery_plan.suggestions else None
                )
        except Exception as e:
            logger.warning(f"Failed to learn from execution error: {e}")
    
    def clear_cache(self) -> None:
        """Clear cached schema alternatives"""
        self.schema_alternatives_cache.clear()
        logger.info("Schema alternatives cache cleared")