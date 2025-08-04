#!/usr/bin/env python3
"""
AdaptiveLearningEngine - Continuous improvement through pattern learning and adaptation.

This module implements the learning system that captures successful query patterns,
learns from errors, and adapts to schema changes using vector embeddings.
"""

import numpy as np
import json
import os
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from sentence_transformers import SentenceTransformer

# Import existing components
from vector_schema_store import VectorSchemaStore, SchemaVector
from semantic_intent_engine import QueryIntent, IntentType, EntityType, ComplexityLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be learned"""
    SUCCESS_PATTERN = "success"
    ERROR_PATTERN = "error"
    SCHEMA_PATTERN = "schema"
    OPTIMIZATION_PATTERN = "optimization"


class LearningConfidence(Enum):
    """Confidence levels for learned patterns"""
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.9


@dataclass
class QueryPattern:
    """Represents a learned query pattern"""
    pattern_id: str
    pattern_type: PatternType
    natural_language_query: str
    sql_query: str
    query_vector: np.ndarray
    sql_vector: np.ndarray
    intent_type: IntentType
    complexity_level: ComplexityLevel
    confidence: float
    usage_count: int
    success_rate: float
    last_used: datetime
    created_at: datetime
    metadata: Dict[str, Any]
    semantic_tags: List[str]


@dataclass
class ErrorPattern:
    """Represents a learned error pattern"""
    error_id: str
    error_type: str
    original_query: str
    failed_sql: str
    error_message: str
    correction: Optional[str]
    query_vector: np.ndarray
    confidence: float
    occurrence_count: int
    last_occurred: datetime
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class SchemaEvolutionPattern:
    """Represents schema evolution patterns"""
    evolution_id: str
    schema_name: str
    change_type: str  # 'table_added', 'column_added', 'relationship_changed'
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    affected_patterns: List[str]
    adaptation_strategy: str
    confidence: float
    created_at: datetime
    metadata: Dict[str, Any]


class AdaptiveLearningEngine:
    """
    Learn and adapt from query patterns for continuous improvement.
    
    This class implements the learning system that captures successful patterns,
    learns from errors, and adapts to schema changes using vector embeddings.
    """
    
    def __init__(self, 
                 vector_store: VectorSchemaStore,
                 learning_data_path: str = "vector_data/learning_patterns",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the AdaptiveLearningEngine.
        
        Args:
            vector_store: VectorSchemaStore instance for schema context
            learning_data_path: Path to store learning patterns
            embedding_model: Sentence transformer model name
        """
        self.vector_store = vector_store
        self.learning_data_path = learning_data_path
        self.embedding_model_name = embedding_model
        self.embedder = SentenceTransformer(embedding_model)
        
        # Storage for learned patterns
        self.success_patterns: Dict[str, QueryPattern] = {}
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.schema_evolution_patterns: Dict[str, SchemaEvolutionPattern] = {}
        
        # Learning statistics
        self.learning_stats = {
            'total_patterns_learned': 0,
            'successful_applications': 0,
            'failed_applications': 0,
            'schema_adaptations': 0,
            'last_learning_session': None
        }
        
        # Ensure storage directory exists
        os.makedirs(learning_data_path, exist_ok=True)
        
        # Load existing patterns
        self._load_patterns_from_disk()
        self._load_error_patterns_from_disk()
        self._load_schema_evolution_patterns_from_disk()
        
        logger.info(f"AdaptiveLearningEngine initialized with {len(self.success_patterns)} success patterns")
    
    def learn_from_success(self, 
                          nl_query: str, 
                          sql_query: str, 
                          execution_result: Dict[str, Any],
                          query_intent: Optional[QueryIntent] = None) -> str:
        """
        Learn from successful query executions.
        
        Args:
            nl_query: Natural language query
            sql_query: Generated SQL query
            execution_result: Result of SQL execution
            query_intent: Optional QueryIntent object
            
        Returns:
            Pattern ID of the learned pattern
        """
        logger.info(f"Learning from successful query: {nl_query[:50]}...")
        
        # Generate embeddings
        nl_vector = self._normalize_vector(self.embedder.encode(nl_query))
        sql_vector = self._normalize_vector(self.embedder.encode(sql_query))
        
        # Generate pattern ID
        pattern_id = self._generate_pattern_id(nl_query, sql_query)
        
        # Check if pattern already exists
        if pattern_id in self.success_patterns:
            # Update existing pattern
            pattern = self.success_patterns[pattern_id]
            pattern.usage_count += 1
            pattern.last_used = datetime.now()
            
            # Update success rate based on execution result
            if execution_result.get('success', True):
                pattern.success_rate = (pattern.success_rate * (pattern.usage_count - 1) + 1.0) / pattern.usage_count
            else:
                pattern.success_rate = (pattern.success_rate * (pattern.usage_count - 1) + 0.0) / pattern.usage_count
            
            # Update confidence based on usage and success rate
            pattern.confidence = min(0.95, pattern.confidence + 0.05 * pattern.success_rate)
            
            logger.info(f"Updated existing pattern {pattern_id} (usage: {pattern.usage_count})")
            
        else:
            # Create new pattern
            intent_type = query_intent.intent_type if query_intent else IntentType.UNKNOWN
            complexity = query_intent.complexity_level if query_intent else ComplexityLevel.SIMPLE
            
            pattern = QueryPattern(
                pattern_id=pattern_id,
                pattern_type=PatternType.SUCCESS_PATTERN,
                natural_language_query=nl_query,
                sql_query=sql_query,
                query_vector=nl_vector,
                sql_vector=sql_vector,
                intent_type=intent_type,
                complexity_level=complexity,
                confidence=0.7,  # Initial confidence
                usage_count=1,
                success_rate=1.0 if execution_result.get('success', True) else 0.0,
                last_used=datetime.now(),
                created_at=datetime.now(),
                metadata={
                    'execution_time': execution_result.get('execution_time', 0),
                    'row_count': execution_result.get('row_count', 0),
                    'tables_used': execution_result.get('tables_used', []),
                    'columns_used': execution_result.get('columns_used', [])
                },
                semantic_tags=self._extract_semantic_tags(nl_query, sql_query)
            )
            
            self.success_patterns[pattern_id] = pattern
            self.learning_stats['total_patterns_learned'] += 1
            
            logger.info(f"Created new success pattern {pattern_id}")
        
        # Store pattern in vector store for similarity search
        self._store_pattern_in_vector_store(pattern)
        
        # Update learning statistics
        self.learning_stats['last_learning_session'] = datetime.now().isoformat()
        
        return pattern_id
    
    def find_similar_success_patterns(self, 
                                    nl_query: str, 
                                    k: int = 5,
                                    min_confidence: float = 0.5) -> List[Tuple[QueryPattern, float]]:
        """
        Find similar successful patterns for a given query.
        
        Args:
            nl_query: Natural language query to find patterns for
            k: Number of similar patterns to return
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of tuples (QueryPattern, similarity_score)
        """
        if not self.success_patterns:
            return []
        
        # Generate query vector
        query_vector = self._normalize_vector(self.embedder.encode(nl_query))
        
        # Calculate similarities with all success patterns
        similarities = []
        for pattern in self.success_patterns.values():
            if pattern.confidence >= min_confidence:
                # Calculate semantic similarity
                similarity = np.dot(query_vector, pattern.query_vector)
                
                # Boost similarity based on pattern confidence and usage
                boosted_similarity = similarity * (1 + 0.1 * pattern.confidence + 0.05 * min(pattern.usage_count, 10))
                
                similarities.append((pattern, float(boosted_similarity)))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
    
    def get_pattern_recommendation(self, 
                                 nl_query: str,
                                 query_intent: Optional[QueryIntent] = None) -> Optional[Tuple[str, float]]:
        """
        Get SQL recommendation based on learned patterns.
        
        Args:
            nl_query: Natural language query
            query_intent: Optional QueryIntent object
            
        Returns:
            Tuple of (recommended_sql, confidence) or None
        """
        similar_patterns = self.find_similar_success_patterns(nl_query, k=3, min_confidence=0.6)
        
        if not similar_patterns:
            return None
        
        # Get the best matching pattern
        best_pattern, similarity = similar_patterns[0]
        
        # Calculate recommendation confidence
        recommendation_confidence = similarity * best_pattern.confidence * best_pattern.success_rate
        
        # Apply intent type matching bonus
        if query_intent and best_pattern.intent_type == query_intent.intent_type:
            recommendation_confidence *= 1.2
        
        # Apply complexity matching bonus
        if query_intent and best_pattern.complexity_level == query_intent.complexity_level:
            recommendation_confidence *= 1.1
        
        # Ensure confidence doesn't exceed 1.0
        recommendation_confidence = min(1.0, recommendation_confidence)
        
        if recommendation_confidence > 0.7:
            logger.info(f"Recommending SQL from pattern {best_pattern.pattern_id} with confidence {recommendation_confidence:.3f}")
            return best_pattern.sql_query, recommendation_confidence
        
        return None
    
    def learn_query_to_sql_mapping(self, 
                                  nl_query: str, 
                                  sql_query: str,
                                  execution_success: bool = True,
                                  execution_metadata: Dict[str, Any] = None) -> None:
        """
        Build query-to-SQL mapping learning pipeline.
        
        Args:
            nl_query: Natural language query
            sql_query: Corresponding SQL query
            execution_success: Whether the SQL executed successfully
            execution_metadata: Additional execution metadata
        """
        execution_result = {
            'success': execution_success,
            'execution_time': execution_metadata.get('execution_time', 0) if execution_metadata else 0,
            'row_count': execution_metadata.get('row_count', 0) if execution_metadata else 0,
            'tables_used': execution_metadata.get('tables_used', []) if execution_metadata else [],
            'columns_used': execution_metadata.get('columns_used', []) if execution_metadata else []
        }
        
        # Learn from this mapping
        pattern_id = self.learn_from_success(nl_query, sql_query, execution_result)
        
        # Update mapping statistics
        if execution_success:
            self.learning_stats['successful_applications'] += 1
        else:
            self.learning_stats['failed_applications'] += 1
        
        logger.info(f"Learned query-to-SQL mapping: {pattern_id}")
    
    def create_pattern_similarity_matching(self, 
                                         query_patterns: List[QueryPattern]) -> Dict[str, List[str]]:
        """
        Create pattern similarity matching for future queries.
        
        Args:
            query_patterns: List of query patterns to analyze
            
        Returns:
            Dictionary mapping pattern IDs to similar pattern IDs
        """
        similarity_map = {}
        
        for i, pattern1 in enumerate(query_patterns):
            similar_patterns = []
            
            for j, pattern2 in enumerate(query_patterns):
                if i != j:
                    # Calculate similarity between patterns
                    similarity = np.dot(pattern1.query_vector, pattern2.query_vector)
                    
                    # Consider patterns similar if similarity > threshold
                    if similarity > 0.7:
                        similar_patterns.append((pattern2.pattern_id, similarity))
            
            # Sort by similarity and store top similar patterns
            similar_patterns.sort(key=lambda x: x[1], reverse=True)
            similarity_map[pattern1.pattern_id] = [pid for pid, _ in similar_patterns[:5]]
        
        return similarity_map
    
    def apply_incremental_learning(self, 
                                 new_patterns: List[QueryPattern],
                                 learning_rate: float = 0.1) -> None:
        """
        Add incremental learning from execution results.
        
        Args:
            new_patterns: New patterns to learn from
            learning_rate: Rate of learning (0.0 to 1.0)
        """
        logger.info(f"Applying incremental learning to {len(new_patterns)} new patterns")
        
        for pattern in new_patterns:
            existing_pattern_id = self._find_similar_existing_pattern(pattern)
            
            if existing_pattern_id:
                # Update existing pattern with incremental learning
                existing_pattern = self.success_patterns[existing_pattern_id]
                
                # Weighted average of vectors
                existing_pattern.query_vector = (
                    (1 - learning_rate) * existing_pattern.query_vector + 
                    learning_rate * pattern.query_vector
                )
                existing_pattern.sql_vector = (
                    (1 - learning_rate) * existing_pattern.sql_vector + 
                    learning_rate * pattern.sql_vector
                )
                
                # Update confidence
                existing_pattern.confidence = min(0.95, existing_pattern.confidence + learning_rate * 0.1)
                existing_pattern.usage_count += 1
                existing_pattern.last_used = datetime.now()
                
                logger.debug(f"Updated existing pattern {existing_pattern_id} with incremental learning")
                
            else:
                # Add as new pattern
                self.success_patterns[pattern.pattern_id] = pattern
                self._store_pattern_in_vector_store(pattern)
                
                logger.debug(f"Added new pattern {pattern.pattern_id} through incremental learning")
        
        self.learning_stats['total_patterns_learned'] += len(new_patterns)
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive learning statistics.
        
        Returns:
            Dictionary with learning statistics
        """
        stats = self.learning_stats.copy()
        
        # Add pattern statistics
        stats.update({
            'success_patterns_count': len(self.success_patterns),
            'error_patterns_count': len(self.error_patterns),
            'schema_evolution_patterns_count': len(self.schema_evolution_patterns),
            'average_pattern_confidence': self._calculate_average_confidence(),
            'most_used_patterns': self._get_most_used_patterns(5),
            'recent_patterns': self._get_recent_patterns(10),
            'pattern_types_distribution': self._get_pattern_type_distribution()
        })
        
        return stats
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector for cosine similarity"""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def _generate_pattern_id(self, nl_query: str, sql_query: str) -> str:
        """Generate unique pattern ID"""
        combined = f"{nl_query}|{sql_query}"
        return f"pattern_{hash(combined) & 0x7FFFFFFF}"
    
    def _extract_semantic_tags(self, nl_query: str, sql_query: str) -> List[str]:
        """Extract semantic tags from query and SQL"""
        tags = []
        
        nl_lower = nl_query.lower()
        sql_upper = sql_query.upper()
        
        # Intent-based tags
        if any(word in nl_lower for word in ['count', 'how many']):
            tags.append('count_query')
        if any(word in nl_lower for word in ['total', 'sum']):
            tags.append('sum_query')
        if any(word in nl_lower for word in ['average', 'mean']):
            tags.append('average_query')
        if any(word in nl_lower for word in ['maximum', 'max', 'highest']):
            tags.append('max_query')
        if any(word in nl_lower for word in ['minimum', 'min', 'lowest']):
            tags.append('min_query')
        
        # SQL feature tags
        if 'JOIN' in sql_upper:
            tags.append('join_query')
        if 'GROUP BY' in sql_upper:
            tags.append('group_by_query')
        if 'ORDER BY' in sql_upper:
            tags.append('order_by_query')
        if 'HAVING' in sql_upper:
            tags.append('having_query')
        if any(func in sql_upper for func in ['ROW_NUMBER', 'RANK', 'DENSE_RANK']):
            tags.append('window_function_query')
        if 'CASE WHEN' in sql_upper:
            tags.append('conditional_query')
        
        return tags
    
    def _store_pattern_in_vector_store(self, pattern: QueryPattern) -> None:
        """Store pattern in vector store for similarity search"""
        try:
            # Store as a special pattern element in vector store
            element_id = f"pattern:{pattern.pattern_id}"
            
            metadata = {
                'pattern_type': pattern.pattern_type.value,
                'intent_type': pattern.intent_type.value,
                'complexity_level': pattern.complexity_level.value,
                'confidence': pattern.confidence,
                'usage_count': pattern.usage_count,
                'success_rate': pattern.success_rate,
                'sql_query': pattern.sql_query,
                'semantic_tags': pattern.semantic_tags
            }
            
            self.vector_store.store_schema_vector(
                element_type="pattern",
                schema_name="learned_patterns",
                element_name=pattern.pattern_id,
                metadata=metadata,
                semantic_tags=pattern.semantic_tags,
                business_context={'source': 'adaptive_learning'}
            )
            
        except Exception as e:
            logger.warning(f"Failed to store pattern in vector store: {e}")
    
    def _find_similar_existing_pattern(self, new_pattern: QueryPattern) -> Optional[str]:
        """Find similar existing pattern for incremental learning"""
        for pattern_id, existing_pattern in self.success_patterns.items():
            # Calculate similarity
            similarity = np.dot(new_pattern.query_vector, existing_pattern.query_vector)
            
            # Consider patterns similar if high similarity and same intent
            if (similarity > 0.85 and 
                new_pattern.intent_type == existing_pattern.intent_type and
                new_pattern.complexity_level == existing_pattern.complexity_level):
                return pattern_id
        
        return None
    
    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence of all success patterns"""
        if not self.success_patterns:
            return 0.0
        
        total_confidence = sum(pattern.confidence for pattern in self.success_patterns.values())
        return total_confidence / len(self.success_patterns)
    
    def _get_most_used_patterns(self, limit: int) -> List[Dict[str, Any]]:
        """Get most frequently used patterns"""
        sorted_patterns = sorted(
            self.success_patterns.values(),
            key=lambda p: p.usage_count,
            reverse=True
        )
        
        return [
            {
                'pattern_id': p.pattern_id,
                'usage_count': p.usage_count,
                'confidence': p.confidence,
                'success_rate': p.success_rate,
                'natural_language_query': p.natural_language_query[:100] + '...' if len(p.natural_language_query) > 100 else p.natural_language_query
            }
            for p in sorted_patterns[:limit]
        ]
    
    def _get_recent_patterns(self, limit: int) -> List[Dict[str, Any]]:
        """Get most recently created patterns"""
        sorted_patterns = sorted(
            self.success_patterns.values(),
            key=lambda p: p.created_at,
            reverse=True
        )
        
        return [
            {
                'pattern_id': p.pattern_id,
                'created_at': p.created_at.isoformat(),
                'confidence': p.confidence,
                'natural_language_query': p.natural_language_query[:100] + '...' if len(p.natural_language_query) > 100 else p.natural_language_query
            }
            for p in sorted_patterns[:limit]
        ]
    
    def _get_pattern_type_distribution(self) -> Dict[str, int]:
        """Get distribution of pattern types"""
        distribution = {}
        
        for pattern in self.success_patterns.values():
            intent_type = pattern.intent_type.value
            distribution[intent_type] = distribution.get(intent_type, 0) + 1
        
        return distribution
    
    def save_patterns_to_disk(self) -> None:
        """Save all learned patterns to disk"""
        try:
            # Save success patterns
            success_patterns_data = {}
            for pattern_id, pattern in self.success_patterns.items():
                pattern_dict = asdict(pattern)
                # Convert numpy arrays to lists for JSON serialization
                pattern_dict['query_vector'] = pattern.query_vector.tolist()
                pattern_dict['sql_vector'] = pattern.sql_vector.tolist()
                pattern_dict['created_at'] = pattern.created_at.isoformat()
                pattern_dict['last_used'] = pattern.last_used.isoformat()
                pattern_dict['intent_type'] = pattern.intent_type.value
                pattern_dict['complexity_level'] = pattern.complexity_level.value
                pattern_dict['pattern_type'] = pattern.pattern_type.value
                success_patterns_data[pattern_id] = pattern_dict
            
            success_patterns_path = os.path.join(self.learning_data_path, "success_patterns.json")
            with open(success_patterns_path, 'w') as f:
                json.dump(success_patterns_data, f, indent=2)
            
            # Save error patterns
            self.save_error_patterns_to_disk()
            
            # Save schema evolution patterns
            self.save_schema_evolution_patterns_to_disk()
            
            # Save learning statistics
            stats_path = os.path.join(self.learning_data_path, "learning_stats.json")
            with open(stats_path, 'w') as f:
                json.dump(self.learning_stats, f, indent=2)
            
            logger.info(f"Saved {len(self.success_patterns)} success patterns, {len(self.error_patterns)} error patterns, and {len(self.schema_evolution_patterns)} evolution patterns to disk")
            
        except Exception as e:
            logger.error(f"Error saving patterns to disk: {e}")
            raise
    
    def _load_patterns_from_disk(self) -> None:
        """Load learned patterns from disk"""
        try:
            success_patterns_path = os.path.join(self.learning_data_path, "success_patterns.json")
            stats_path = os.path.join(self.learning_data_path, "learning_stats.json")
            
            # Load success patterns
            if os.path.exists(success_patterns_path):
                with open(success_patterns_path, 'r') as f:
                    success_patterns_data = json.load(f)
                
                for pattern_id, pattern_dict in success_patterns_data.items():
                    # Convert lists back to numpy arrays
                    pattern_dict['query_vector'] = np.array(pattern_dict['query_vector'])
                    pattern_dict['sql_vector'] = np.array(pattern_dict['sql_vector'])
                    pattern_dict['created_at'] = datetime.fromisoformat(pattern_dict['created_at'])
                    pattern_dict['last_used'] = datetime.fromisoformat(pattern_dict['last_used'])
                    pattern_dict['intent_type'] = IntentType(pattern_dict['intent_type'])
                    pattern_dict['complexity_level'] = ComplexityLevel(pattern_dict['complexity_level'])
                    pattern_dict['pattern_type'] = PatternType(pattern_dict['pattern_type'])
                    
                    self.success_patterns[pattern_id] = QueryPattern(**pattern_dict)
            
            # Load learning statistics
            if os.path.exists(stats_path):
                with open(stats_path, 'r') as f:
                    self.learning_stats.update(json.load(f))
            
            logger.info(f"Loaded {len(self.success_patterns)} patterns from disk")
            
        except Exception as e:
            logger.warning(f"Could not load patterns from disk: {e}")
            # Initialize empty structures
            self.success_patterns = {}
            self.error_patterns = {}
            self.schema_evolution_patterns = {}
    
    def clear_all_patterns(self) -> None:
        """Clear all learned patterns"""
        self.success_patterns.clear()
        self.error_patterns.clear()
        self.schema_evolution_patterns.clear()
        
        # Reset statistics
        self.learning_stats = {
            'total_patterns_learned': 0,
            'successful_applications': 0,
            'failed_applications': 0,
            'schema_adaptations': 0,
            'last_learning_session': None
        }
        
        logger.info("All learned patterns cleared")
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[QueryPattern]:
        """Get a specific pattern by ID"""
        return self.success_patterns.get(pattern_id)
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """Remove a specific pattern"""
        if pattern_id in self.success_patterns:
            del self.success_patterns[pattern_id]
            logger.info(f"Removed pattern {pattern_id}")
            return True
        return False
    
    def update_pattern_confidence(self, pattern_id: str, new_confidence: float) -> bool:
        """Update confidence of a specific pattern"""
        if pattern_id in self.success_patterns:
            self.success_patterns[pattern_id].confidence = max(0.0, min(1.0, new_confidence))
            self.success_patterns[pattern_id].last_used = datetime.now()
            logger.info(f"Updated confidence for pattern {pattern_id} to {new_confidence}")
            return True
        return False
    
    def get_patterns_by_intent(self, intent_type: IntentType) -> List[QueryPattern]:
        """Get all patterns for a specific intent type"""
        return [
            pattern for pattern in self.success_patterns.values()
            if pattern.intent_type == intent_type
        ]
    
    def get_patterns_by_complexity(self, complexity_level: ComplexityLevel) -> List[QueryPattern]:
        """Get all patterns for a specific complexity level"""
        return [
            pattern for pattern in self.success_patterns.values()
            if pattern.complexity_level == complexity_level
        ]
    
    def get_high_confidence_patterns(self, min_confidence: float = 0.8) -> List[QueryPattern]:
        """Get patterns with high confidence scores"""
        return [
            pattern for pattern in self.success_patterns.values()
            if pattern.confidence >= min_confidence
        ]
    
    def optimize_pattern_storage(self) -> None:
        """Optimize pattern storage by removing low-value patterns"""
        # Remove patterns with very low confidence and usage
        patterns_to_remove = []
        
        for pattern_id, pattern in self.success_patterns.items():
            # Remove patterns that are old, low confidence, and rarely used
            age_days = (datetime.now() - pattern.created_at).days
            if (pattern.confidence < 0.3 and 
                pattern.usage_count < 2 and 
                age_days > 30):
                patterns_to_remove.append(pattern_id)
        
        for pattern_id in patterns_to_remove:
            del self.success_patterns[pattern_id]
        
        logger.info(f"Optimized pattern storage: removed {len(patterns_to_remove)} low-value patterns")
    
    def export_patterns_for_analysis(self, output_path: str) -> None:
        """Export patterns in a format suitable for analysis"""
        analysis_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_patterns': len(self.success_patterns),
            'patterns': []
        }
        
        for pattern in self.success_patterns.values():
            pattern_data = {
                'pattern_id': pattern.pattern_id,
                'natural_language_query': pattern.natural_language_query,
                'sql_query': pattern.sql_query,
                'intent_type': pattern.intent_type.value,
                'complexity_level': pattern.complexity_level.value,
                'confidence': pattern.confidence,
                'usage_count': pattern.usage_count,
                'success_rate': pattern.success_rate,
                'created_at': pattern.created_at.isoformat(),
                'last_used': pattern.last_used.isoformat(),
                'semantic_tags': pattern.semantic_tags,
                'metadata': pattern.metadata
            }
            analysis_data['patterns'].append(pattern_data)
        
        with open(output_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        logger.info(f"Exported {len(self.success_patterns)} patterns to {output_path}")
   
 # Error Pattern Recognition and Correction Methods
    
    def learn_from_error(self, 
                        nl_query: str, 
                        failed_sql: str, 
                        error_message: str,
                        correction: Optional[str] = None,
                        query_intent: Optional[QueryIntent] = None) -> str:
        """
        Learn from failed query executions to build error patterns.
        
        Args:
            nl_query: Natural language query that failed
            failed_sql: SQL query that caused the error
            error_message: Error message from SQL execution
            correction: Optional corrected SQL query
            query_intent: Optional QueryIntent object
            
        Returns:
            Error pattern ID
        """
        logger.info(f"Learning from error: {error_message[:100]}...")
        
        # Generate query vector
        query_vector = self._normalize_vector(self.embedder.encode(nl_query))
        
        # Classify error type
        error_type = self._classify_error_type(error_message)
        
        # Generate error pattern ID
        error_id = self._generate_error_id(nl_query, failed_sql, error_message)
        
        # Check if error pattern already exists
        if error_id in self.error_patterns:
            # Update existing error pattern
            error_pattern = self.error_patterns[error_id]
            error_pattern.occurrence_count += 1
            error_pattern.last_occurred = datetime.now()
            
            # Update correction if provided
            if correction:
                error_pattern.correction = correction
                error_pattern.confidence = min(0.95, error_pattern.confidence + 0.1)
            
            logger.info(f"Updated existing error pattern {error_id} (occurrences: {error_pattern.occurrence_count})")
            
        else:
            # Create new error pattern
            error_pattern = ErrorPattern(
                error_id=error_id,
                error_type=error_type,
                original_query=nl_query,
                failed_sql=failed_sql,
                error_message=error_message,
                correction=correction,
                query_vector=query_vector,
                confidence=0.8 if correction else 0.5,
                occurrence_count=1,
                last_occurred=datetime.now(),
                created_at=datetime.now(),
                metadata={
                    'intent_type': query_intent.intent_type.value if query_intent else 'unknown',
                    'complexity_level': query_intent.complexity_level.value if query_intent else 'unknown',
                    'error_category': self._categorize_error(error_message)
                }
            )
            
            self.error_patterns[error_id] = error_pattern
            logger.info(f"Created new error pattern {error_id}")
        
        # Store error pattern in vector store
        self._store_error_pattern_in_vector_store(error_pattern)
        
        # Update learning statistics
        self.learning_stats['failed_applications'] += 1
        
        return error_id
    
    def _classify_error_type(self, error_message: str) -> str:
        """Classify the type of SQL error"""
        error_lower = error_message.lower()
        
        # Check for aggregation errors first (more specific)
        if any(phrase in error_lower for phrase in ['aggregate function', 'group by clause', 'not contained in either an aggregate']):
            return 'aggregation_error'
        elif any(keyword in error_lower for keyword in ['invalid column', 'column', 'does not exist']) and 'object' not in error_lower:
            return 'column_error'
        elif any(keyword in error_lower for keyword in ['invalid object', 'table', 'does not exist']):
            return 'table_error'
        elif any(keyword in error_lower for keyword in ['syntax error', 'incorrect syntax']):
            return 'syntax_error'
        elif any(keyword in error_lower for keyword in ['permission', 'access denied', 'unauthorized']):
            return 'permission_error'
        elif any(keyword in error_lower for keyword in ['timeout', 'deadlock']):
            return 'execution_error'
        elif any(keyword in error_lower for keyword in ['data type', 'conversion', 'cast']):
            return 'type_error'
        else:
            return 'unknown_error'
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error for metadata"""
        error_type = self._classify_error_type(error_message)
        
        categories = {
            'column_error': 'schema_mismatch',
            'table_error': 'schema_mismatch',
            'syntax_error': 'sql_syntax',
            'permission_error': 'access_control',
            'execution_error': 'runtime',
            'type_error': 'data_type',
            'aggregation_error': 'query_logic',
            'unknown_error': 'unclassified'
        }
        
        return categories.get(error_type, 'unclassified')
    
    def _generate_error_id(self, nl_query: str, failed_sql: str, error_message: str) -> str:
        """Generate unique error pattern ID"""
        combined = f"{nl_query}|{failed_sql}|{error_message}"
        return f"error_{hash(combined) & 0x7FFFFFFF}"
    
    def find_similar_error_patterns(self, 
                                   nl_query: str, 
                                   error_message: str = None,
                                   k: int = 5) -> List[Tuple[ErrorPattern, float]]:
        """
        Find similar error patterns for a given query or error.
        
        Args:
            nl_query: Natural language query
            error_message: Optional error message to match
            k: Number of similar patterns to return
            
        Returns:
            List of tuples (ErrorPattern, similarity_score)
        """
        if not self.error_patterns:
            return []
        
        # Generate query vector
        query_vector = self._normalize_vector(self.embedder.encode(nl_query))
        
        # Calculate similarities with all error patterns
        similarities = []
        for error_pattern in self.error_patterns.values():
            # Calculate semantic similarity
            similarity = np.dot(query_vector, error_pattern.query_vector)
            
            # Boost similarity if error messages are similar
            if error_message:
                error_type_match = self._classify_error_type(error_message) == error_pattern.error_type
                if error_type_match:
                    similarity *= 1.3
            
            # Boost similarity based on pattern confidence and occurrence
            boosted_similarity = similarity * (1 + 0.1 * error_pattern.confidence + 0.05 * min(error_pattern.occurrence_count, 5))
            
            similarities.append((error_pattern, float(boosted_similarity)))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
    
    def get_error_correction_suggestion(self, 
                                      nl_query: str, 
                                      failed_sql: str,
                                      error_message: str) -> Optional[Tuple[str, float]]:
        """
        Get correction suggestion based on learned error patterns.
        
        Args:
            nl_query: Natural language query
            failed_sql: Failed SQL query
            error_message: Error message
            
        Returns:
            Tuple of (suggested_correction, confidence) or None
        """
        # Find similar error patterns
        similar_errors = self.find_similar_error_patterns(nl_query, error_message, k=3)
        
        if not similar_errors:
            return None
        
        # Look for patterns with corrections
        for error_pattern, similarity in similar_errors:
            if error_pattern.correction and similarity > 0.6:
                # Calculate suggestion confidence
                suggestion_confidence = similarity * error_pattern.confidence
                
                # Boost confidence if error types match exactly
                if self._classify_error_type(error_message) == error_pattern.error_type:
                    suggestion_confidence *= 1.2
                
                suggestion_confidence = min(1.0, suggestion_confidence)
                
                if suggestion_confidence > 0.7:
                    logger.info(f"Suggesting correction from error pattern {error_pattern.error_id} with confidence {suggestion_confidence:.3f}")
                    return error_pattern.correction, suggestion_confidence
        
        # If no direct correction, try to suggest based on successful patterns
        return self._suggest_correction_from_success_patterns(nl_query, failed_sql, error_message)
    
    def _suggest_correction_from_success_patterns(self, 
                                                nl_query: str, 
                                                failed_sql: str,
                                                error_message: str) -> Optional[Tuple[str, float]]:
        """
        Suggest correction based on similar successful patterns.
        
        Args:
            nl_query: Natural language query
            failed_sql: Failed SQL query
            error_message: Error message
            
        Returns:
            Tuple of (suggested_correction, confidence) or None
        """
        # Find similar successful patterns
        similar_success = self.find_similar_success_patterns(nl_query, k=3, min_confidence=0.7)
        
        if not similar_success:
            return None
        
        # Get the best matching successful pattern
        best_pattern, similarity = similar_success[0]
        
        # Only suggest if similarity is high
        if similarity > 0.8:
            suggestion_confidence = similarity * best_pattern.confidence * 0.8  # Reduce confidence since it's indirect
            
            if suggestion_confidence > 0.6:
                logger.info(f"Suggesting correction from success pattern {best_pattern.pattern_id} with confidence {suggestion_confidence:.3f}")
                return best_pattern.sql_query, suggestion_confidence
        
        return None
    
    def implement_error_pattern_vectorization(self) -> Dict[str, np.ndarray]:
        """
        Implement error pattern vectorization and storage.
        
        Returns:
            Dictionary mapping error pattern IDs to their vectors
        """
        error_vectors = {}
        
        for error_id, error_pattern in self.error_patterns.items():
            # Create combined text for vectorization
            combined_text = f"{error_pattern.original_query} {error_pattern.error_message} {error_pattern.error_type}"
            
            # Generate and normalize vector
            error_vector = self._normalize_vector(self.embedder.encode(combined_text))
            error_vectors[error_id] = error_vector
            
            # Update the pattern's vector if it's different
            if not np.array_equal(error_pattern.query_vector, error_vector):
                error_pattern.query_vector = error_vector
        
        logger.info(f"Vectorized {len(error_vectors)} error patterns")
        return error_vectors
    
    def create_error_type_classification(self) -> Dict[str, List[str]]:
        """
        Create error type classification using embeddings.
        
        Returns:
            Dictionary mapping error types to pattern IDs
        """
        error_classification = {}
        
        for error_id, error_pattern in self.error_patterns.items():
            error_type = error_pattern.error_type
            
            if error_type not in error_classification:
                error_classification[error_type] = []
            
            error_classification[error_type].append(error_id)
        
        # Sort by confidence within each type
        for error_type in error_classification:
            error_classification[error_type].sort(
                key=lambda eid: self.error_patterns[eid].confidence,
                reverse=True
            )
        
        logger.info(f"Classified errors into {len(error_classification)} types")
        return error_classification
    
    def build_correction_suggestion_system(self) -> Dict[str, Any]:
        """
        Build correction suggestion system using similar successful queries.
        
        Returns:
            Dictionary with correction system metadata
        """
        correction_system = {
            'error_type_corrections': {},
            'pattern_based_corrections': {},
            'success_pattern_mappings': {},
            'confidence_thresholds': {
                'high_confidence': 0.8,
                'medium_confidence': 0.6,
                'low_confidence': 0.4
            }
        }
        
        # Build error type specific corrections
        for error_id, error_pattern in self.error_patterns.items():
            if error_pattern.correction:
                error_type = error_pattern.error_type
                
                if error_type not in correction_system['error_type_corrections']:
                    correction_system['error_type_corrections'][error_type] = []
                
                correction_system['error_type_corrections'][error_type].append({
                    'error_id': error_id,
                    'correction': error_pattern.correction,
                    'confidence': error_pattern.confidence,
                    'occurrence_count': error_pattern.occurrence_count
                })
        
        # Build pattern-based corrections by finding success patterns similar to error patterns
        for error_id, error_pattern in self.error_patterns.items():
            similar_success = self.find_similar_success_patterns(
                error_pattern.original_query, k=3, min_confidence=0.6
            )
            
            if similar_success:
                correction_system['pattern_based_corrections'][error_id] = [
                    {
                        'success_pattern_id': pattern.pattern_id,
                        'suggested_sql': pattern.sql_query,
                        'similarity': similarity,
                        'confidence': pattern.confidence
                    }
                    for pattern, similarity in similar_success
                ]
        
        # Build success pattern mappings for common error scenarios
        common_error_types = ['column_error', 'table_error', 'syntax_error', 'aggregation_error']
        for error_type in common_error_types:
            error_patterns_of_type = [
                ep for ep in self.error_patterns.values() 
                if ep.error_type == error_type
            ]
            
            if error_patterns_of_type:
                # Find success patterns that could help with this error type
                success_mappings = []
                for error_pattern in error_patterns_of_type[:5]:  # Limit to top 5
                    similar_success = self.find_similar_success_patterns(
                        error_pattern.original_query, k=2, min_confidence=0.7
                    )
                    success_mappings.extend(similar_success)
                
                correction_system['success_pattern_mappings'][error_type] = [
                    {
                        'pattern_id': pattern.pattern_id,
                        'sql_query': pattern.sql_query,
                        'confidence': pattern.confidence,
                        'similarity': similarity
                    }
                    for pattern, similarity in success_mappings[:3]  # Top 3
                ]
        
        logger.info("Built correction suggestion system")
        return correction_system
    
    def apply_adaptive_error_recovery(self, 
                                    nl_query: str, 
                                    failed_sql: str,
                                    error_message: str,
                                    max_attempts: int = 3) -> Optional[Tuple[str, float, List[str]]]:
        """
        Add adaptive error recovery based on learned patterns.
        
        Args:
            nl_query: Natural language query
            failed_sql: Failed SQL query
            error_message: Error message
            max_attempts: Maximum recovery attempts
            
        Returns:
            Tuple of (recovered_sql, confidence, recovery_steps) or None
        """
        recovery_steps = []
        current_sql = failed_sql
        
        for attempt in range(max_attempts):
            recovery_steps.append(f"Attempt {attempt + 1}: Analyzing error pattern")
            
            # Get correction suggestion
            suggestion = self.get_error_correction_suggestion(nl_query, current_sql, error_message)
            
            if suggestion:
                suggested_sql, confidence = suggestion
                recovery_steps.append(f"Found correction suggestion with confidence {confidence:.3f}")
                
                # Apply error-type specific recovery strategies
                error_type = self._classify_error_type(error_message)
                recovered_sql = self._apply_error_type_recovery(
                    suggested_sql, error_type, recovery_steps
                )
                
                if recovered_sql != current_sql:
                    recovery_steps.append(f"Applied {error_type} recovery strategy")
                    return recovered_sql, confidence, recovery_steps
                
                current_sql = suggested_sql
            else:
                recovery_steps.append("No correction suggestion found")
                break
        
        recovery_steps.append("Error recovery failed after all attempts")
        return None
    
    def _apply_error_type_recovery(self, 
                                 suggested_sql: str, 
                                 error_type: str,
                                 recovery_steps: List[str]) -> str:
        """
        Apply error-type specific recovery strategies.
        
        Args:
            suggested_sql: Suggested SQL correction
            error_type: Type of error
            recovery_steps: List to append recovery steps to
            
        Returns:
            Recovered SQL query
        """
        recovered_sql = suggested_sql
        
        if error_type == 'column_error':
            # Try to fix column name issues
            recovery_steps.append("Applying column name recovery")
            # This would involve schema-aware column name correction
            # For now, return as-is
            
        elif error_type == 'table_error':
            # Try to fix table name issues
            recovery_steps.append("Applying table name recovery")
            # This would involve schema-aware table name correction
            
        elif error_type == 'syntax_error':
            # Try to fix common syntax issues
            recovery_steps.append("Applying syntax error recovery")
            recovered_sql = self._fix_common_syntax_errors(suggested_sql)
            
        elif error_type == 'aggregation_error':
            # Try to fix GROUP BY issues
            recovery_steps.append("Applying aggregation error recovery")
            recovered_sql = self._fix_aggregation_errors(suggested_sql)
        
        return recovered_sql
    
    def _fix_common_syntax_errors(self, sql: str) -> str:
        """Fix common SQL syntax errors"""
        # Remove extra commas
        sql = re.sub(r',\s*FROM', ' FROM', sql, flags=re.IGNORECASE)
        sql = re.sub(r',\s*WHERE', ' WHERE', sql, flags=re.IGNORECASE)
        
        # Fix missing spaces around operators
        sql = re.sub(r'(\w)=(\w)', r'\1 = \2', sql)
        sql = re.sub(r'(\w)<(\w)', r'\1 < \2', sql)
        sql = re.sub(r'(\w)>(\w)', r'\1 > \2', sql)
        
        return sql
    
    def _fix_aggregation_errors(self, sql: str) -> str:
        """Fix common aggregation errors"""
        # If there's an aggregate function but no GROUP BY, and there are non-aggregate columns
        if any(func in sql.upper() for func in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']):
            if 'GROUP BY' not in sql.upper():
                # This is a simplified fix - in practice, would need more sophisticated analysis
                pass
        
        return sql
    
    def _store_error_pattern_in_vector_store(self, error_pattern: ErrorPattern) -> None:
        """Store error pattern in vector store for similarity search"""
        try:
            element_id = f"error_pattern:{error_pattern.error_id}"
            
            metadata = {
                'pattern_type': 'error_pattern',
                'error_type': error_pattern.error_type,
                'error_message': error_pattern.error_message,
                'failed_sql': error_pattern.failed_sql,
                'correction': error_pattern.correction,
                'confidence': error_pattern.confidence,
                'occurrence_count': error_pattern.occurrence_count,
                'error_category': error_pattern.metadata.get('error_category', 'unknown')
            }
            
            self.vector_store.store_schema_vector(
                element_type="error_pattern",
                schema_name="learned_errors",
                element_name=error_pattern.error_id,
                metadata=metadata,
                semantic_tags=[error_pattern.error_type, 'error_pattern'],
                business_context={'source': 'adaptive_learning_errors'}
            )
            
        except Exception as e:
            logger.warning(f"Failed to store error pattern in vector store: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive error pattern statistics.
        
        Returns:
            Dictionary with error statistics
        """
        if not self.error_patterns:
            return {'total_error_patterns': 0}
        
        # Error type distribution
        error_type_dist = {}
        for error_pattern in self.error_patterns.values():
            error_type = error_pattern.error_type
            error_type_dist[error_type] = error_type_dist.get(error_type, 0) + 1
        
        # Patterns with corrections
        patterns_with_corrections = sum(
            1 for ep in self.error_patterns.values() if ep.correction
        )
        
        # Most common errors
        most_common_errors = sorted(
            self.error_patterns.values(),
            key=lambda ep: ep.occurrence_count,
            reverse=True
        )[:5]
        
        # Recent errors
        recent_errors = sorted(
            self.error_patterns.values(),
            key=lambda ep: ep.last_occurred,
            reverse=True
        )[:5]
        
        return {
            'total_error_patterns': len(self.error_patterns),
            'patterns_with_corrections': patterns_with_corrections,
            'correction_rate': patterns_with_corrections / len(self.error_patterns) if self.error_patterns else 0,
            'error_type_distribution': error_type_dist,
            'most_common_errors': [
                {
                    'error_id': ep.error_id,
                    'error_type': ep.error_type,
                    'occurrence_count': ep.occurrence_count,
                    'has_correction': ep.correction is not None,
                    'original_query': ep.original_query[:100] + '...' if len(ep.original_query) > 100 else ep.original_query
                }
                for ep in most_common_errors
            ],
            'recent_errors': [
                {
                    'error_id': ep.error_id,
                    'error_type': ep.error_type,
                    'last_occurred': ep.last_occurred.isoformat(),
                    'has_correction': ep.correction is not None,
                    'original_query': ep.original_query[:100] + '...' if len(ep.original_query) > 100 else ep.original_query
                }
                for ep in recent_errors
            ]
        }
    
    def save_error_patterns_to_disk(self) -> None:
        """Save error patterns to disk"""
        try:
            # Save error patterns
            error_patterns_data = {}
            for error_id, error_pattern in self.error_patterns.items():
                error_dict = {
                    'error_id': error_pattern.error_id,
                    'error_type': error_pattern.error_type,
                    'original_query': error_pattern.original_query,
                    'failed_sql': error_pattern.failed_sql,
                    'error_message': error_pattern.error_message,
                    'correction': error_pattern.correction,
                    'query_vector': error_pattern.query_vector.tolist(),
                    'confidence': error_pattern.confidence,
                    'occurrence_count': error_pattern.occurrence_count,
                    'last_occurred': error_pattern.last_occurred.isoformat(),
                    'created_at': error_pattern.created_at.isoformat(),
                    'metadata': error_pattern.metadata
                }
                error_patterns_data[error_id] = error_dict
            
            error_patterns_path = os.path.join(self.learning_data_path, "error_patterns.json")
            with open(error_patterns_path, 'w') as f:
                json.dump(error_patterns_data, f, indent=2)
            
            logger.info(f"Saved {len(self.error_patterns)} error patterns to disk")
            
        except Exception as e:
            logger.error(f"Error saving error patterns to disk: {e}")
            raise
    
    def _load_error_patterns_from_disk(self) -> None:
        """Load error patterns from disk"""
        try:
            error_patterns_path = os.path.join(self.learning_data_path, "error_patterns.json")
            
            if os.path.exists(error_patterns_path):
                with open(error_patterns_path, 'r') as f:
                    error_patterns_data = json.load(f)
                
                for error_id, error_dict in error_patterns_data.items():
                    # Convert lists back to numpy arrays
                    error_dict['query_vector'] = np.array(error_dict['query_vector'])
                    error_dict['created_at'] = datetime.fromisoformat(error_dict['created_at'])
                    error_dict['last_occurred'] = datetime.fromisoformat(error_dict['last_occurred'])
                    
                    self.error_patterns[error_id] = ErrorPattern(**error_dict)
            
            logger.info(f"Loaded {len(self.error_patterns)} error patterns from disk")
            
        except Exception as e:
            logger.warning(f"Could not load error patterns from disk: {e}")
            self.error_patterns = {} 
   # Schema Evolution Adaptation Methods
    
    def detect_schema_changes(self, 
                            new_schema_metadata: List[Dict],
                            previous_schema_metadata: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        Implement incremental schema update handling and change detection.
        
        Args:
            new_schema_metadata: New schema metadata
            previous_schema_metadata: Previous schema metadata for comparison
            
        Returns:
            List of detected schema changes
        """
        logger.info("Detecting schema changes...")
        
        if previous_schema_metadata is None:
            # Get previous schema from vector store
            previous_schema_metadata = self._get_current_schema_from_vector_store()
        
        changes = []
        
        # Convert to dictionaries for easier comparison
        new_schema_dict = self._schema_list_to_dict(new_schema_metadata)
        prev_schema_dict = self._schema_list_to_dict(previous_schema_metadata)
        
        # Detect table changes
        table_changes = self._detect_table_changes(new_schema_dict, prev_schema_dict)
        changes.extend(table_changes)
        
        # Detect column changes
        column_changes = self._detect_column_changes(new_schema_dict, prev_schema_dict)
        changes.extend(column_changes)
        
        # Detect relationship changes
        relationship_changes = self._detect_relationship_changes(new_schema_dict, prev_schema_dict)
        changes.extend(relationship_changes)
        
        logger.info(f"Detected {len(changes)} schema changes")
        return changes
    
    def _schema_list_to_dict(self, schema_metadata: List[Dict]) -> Dict[str, Dict]:
        """Convert schema metadata list to dictionary for easier comparison"""
        schema_dict = {}
        
        for table_meta in schema_metadata:
            schema_name = table_meta.get('schema', 'default')
            table_name = table_meta.get('table_name', table_meta.get('table', ''))
            key = f"{schema_name}.{table_name}"
            
            schema_dict[key] = {
                'schema': schema_name,
                'table': table_name,
                'columns': {col.get('name', ''): col for col in table_meta.get('columns', [])},
                'metadata': table_meta
            }
        
        return schema_dict
    
    def _detect_table_changes(self, new_schema: Dict, prev_schema: Dict) -> List[Dict[str, Any]]:
        """Detect table-level changes"""
        changes = []
        
        # Tables added
        for table_key in new_schema:
            if table_key not in prev_schema:
                changes.append({
                    'change_type': 'table_added',
                    'table_key': table_key,
                    'schema_name': new_schema[table_key]['schema'],
                    'table_name': new_schema[table_key]['table'],
                    'before_state': None,
                    'after_state': new_schema[table_key]['metadata'],
                    'timestamp': datetime.now()
                })
        
        # Tables removed
        for table_key in prev_schema:
            if table_key not in new_schema:
                changes.append({
                    'change_type': 'table_removed',
                    'table_key': table_key,
                    'schema_name': prev_schema[table_key]['schema'],
                    'table_name': prev_schema[table_key]['table'],
                    'before_state': prev_schema[table_key]['metadata'],
                    'after_state': None,
                    'timestamp': datetime.now()
                })
        
        return changes
    
    def _detect_column_changes(self, new_schema: Dict, prev_schema: Dict) -> List[Dict[str, Any]]:
        """Detect column-level changes"""
        changes = []
        
        # Check common tables for column changes
        common_tables = set(new_schema.keys()) & set(prev_schema.keys())
        
        for table_key in common_tables:
            new_columns = new_schema[table_key]['columns']
            prev_columns = prev_schema[table_key]['columns']
            
            # Columns added
            for col_name in new_columns:
                if col_name not in prev_columns:
                    changes.append({
                        'change_type': 'column_added',
                        'table_key': table_key,
                        'schema_name': new_schema[table_key]['schema'],
                        'table_name': new_schema[table_key]['table'],
                        'column_name': col_name,
                        'before_state': None,
                        'after_state': new_columns[col_name],
                        'timestamp': datetime.now()
                    })
            
            # Columns removed
            for col_name in prev_columns:
                if col_name not in new_columns:
                    changes.append({
                        'change_type': 'column_removed',
                        'table_key': table_key,
                        'schema_name': prev_schema[table_key]['schema'],
                        'table_name': prev_schema[table_key]['table'],
                        'column_name': col_name,
                        'before_state': prev_columns[col_name],
                        'after_state': None,
                        'timestamp': datetime.now()
                    })
            
            # Columns modified
            common_columns = set(new_columns.keys()) & set(prev_columns.keys())
            for col_name in common_columns:
                new_col = new_columns[col_name]
                prev_col = prev_columns[col_name]
                
                # Check for type changes
                if new_col.get('type') != prev_col.get('type'):
                    changes.append({
                        'change_type': 'column_type_changed',
                        'table_key': table_key,
                        'schema_name': new_schema[table_key]['schema'],
                        'table_name': new_schema[table_key]['table'],
                        'column_name': col_name,
                        'before_state': prev_col,
                        'after_state': new_col,
                        'timestamp': datetime.now()
                    })
        
        return changes
    
    def _detect_relationship_changes(self, new_schema: Dict, prev_schema: Dict) -> List[Dict[str, Any]]:
        """Detect relationship changes (simplified implementation)"""
        changes = []
        
        # This is a simplified implementation
        # In practice, would need more sophisticated relationship detection
        # For now, we'll detect potential relationship changes based on foreign key patterns
        
        for table_key in new_schema:
            if table_key in prev_schema:
                new_columns = new_schema[table_key]['columns']
                prev_columns = prev_schema[table_key]['columns']
                
                # Look for foreign key pattern changes
                for col_name, col_info in new_columns.items():
                    if col_name.lower().endswith('_id') or col_name.lower().endswith('id'):
                        if col_name not in prev_columns:
                            changes.append({
                                'change_type': 'relationship_added',
                                'table_key': table_key,
                                'schema_name': new_schema[table_key]['schema'],
                                'table_name': new_schema[table_key]['table'],
                                'column_name': col_name,
                                'before_state': None,
                                'after_state': col_info,
                                'timestamp': datetime.now()
                            })
        
        return changes
    
    def _get_current_schema_from_vector_store(self) -> List[Dict]:
        """Get current schema metadata from vector store"""
        try:
            # Get all table vectors from vector store
            table_vectors = self.vector_store.get_all_vectors_by_type("table")
            column_vectors = self.vector_store.get_all_vectors_by_type("column")
            
            # Reconstruct schema metadata
            schema_metadata = []
            table_dict = {}
            
            # Group columns by table
            for table_vector in table_vectors:
                table_key = f"{table_vector.schema_name}.{table_vector.element_name}"
                table_dict[table_key] = {
                    'schema': table_vector.schema_name,
                    'table_name': table_vector.element_name,
                    'columns': [],
                    'metadata': table_vector.metadata
                }
            
            # Add columns to tables
            for column_vector in column_vectors:
                table_name = column_vector.metadata.get('table_name', '')
                table_key = f"{column_vector.schema_name}.{table_name}"
                
                if table_key in table_dict:
                    table_dict[table_key]['columns'].append({
                        'name': column_vector.element_name,
                        'type': column_vector.metadata.get('data_type', 'varchar'),
                        'description': column_vector.metadata.get('description', ''),
                        **column_vector.metadata
                    })
            
            # Convert to list format
            for table_info in table_dict.values():
                schema_metadata.append({
                    'schema': table_info['schema'],
                    'table_name': table_info['table_name'],
                    'columns': table_info['columns'],
                    **table_info['metadata']
                })
            
            return schema_metadata
            
        except Exception as e:
            logger.warning(f"Could not get current schema from vector store: {e}")
            return []
    
    def update_vector_embeddings_for_changes(self, schema_changes: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Build schema change detection and vector updates.
        
        Args:
            schema_changes: List of detected schema changes
            
        Returns:
            Dictionary with update statistics
        """
        logger.info(f"Updating vector embeddings for {len(schema_changes)} schema changes...")
        
        update_stats = {
            'vectors_added': 0,
            'vectors_updated': 0,
            'vectors_removed': 0,
            'patterns_affected': 0
        }
        
        for change in schema_changes:
            change_type = change['change_type']
            
            if change_type == 'table_added':
                # Add new table vector
                self._add_table_vector(change)
                update_stats['vectors_added'] += 1
                
            elif change_type == 'table_removed':
                # Remove table vector
                self._remove_table_vector(change)
                update_stats['vectors_removed'] += 1
                
            elif change_type == 'column_added':
                # Add new column vector
                self._add_column_vector(change)
                update_stats['vectors_added'] += 1
                
            elif change_type == 'column_removed':
                # Remove column vector
                self._remove_column_vector(change)
                update_stats['vectors_removed'] += 1
                
            elif change_type == 'column_type_changed':
                # Update column vector
                self._update_column_vector(change)
                update_stats['vectors_updated'] += 1
            
            # Update affected patterns
            affected_patterns = self._find_patterns_affected_by_change(change)
            update_stats['patterns_affected'] += len(affected_patterns)
            
            # Store schema evolution pattern
            self._store_schema_evolution_pattern(change, affected_patterns)
        
        logger.info(f"Vector update complete: {update_stats}")
        return update_stats
    
    def _add_table_vector(self, change: Dict[str, Any]) -> None:
        """Add vector for new table"""
        try:
            table_metadata = change['after_state']
            
            self.vector_store.store_schema_vector(
                element_type="table",
                schema_name=change['schema_name'],
                element_name=change['table_name'],
                metadata=table_metadata,
                semantic_tags=["table", "schema", "new"],
                business_context={'source': 'schema_evolution', 'change_type': 'table_added'}
            )
            
            logger.debug(f"Added vector for new table: {change['table_key']}")
            
        except Exception as e:
            logger.error(f"Failed to add table vector: {e}")
    
    def _remove_table_vector(self, change: Dict[str, Any]) -> None:
        """Remove vector for deleted table"""
        try:
            element_id = f"table:{change['schema_name']}.{change['table_name']}"
            self.vector_store.delete_schema_vector(element_id)
            
            logger.debug(f"Removed vector for deleted table: {change['table_key']}")
            
        except Exception as e:
            logger.error(f"Failed to remove table vector: {e}")
    
    def _add_column_vector(self, change: Dict[str, Any]) -> None:
        """Add vector for new column"""
        try:
            column_metadata = change['after_state'].copy()
            column_metadata['table_name'] = change['table_name']
            column_metadata['schema_name'] = change['schema_name']
            
            self.vector_store.store_schema_vector(
                element_type="column",
                schema_name=change['schema_name'],
                element_name=change['column_name'],
                metadata=column_metadata,
                semantic_tags=["column", "schema", "new"],
                business_context={'source': 'schema_evolution', 'change_type': 'column_added'}
            )
            
            logger.debug(f"Added vector for new column: {change['table_key']}.{change['column_name']}")
            
        except Exception as e:
            logger.error(f"Failed to add column vector: {e}")
    
    def _remove_column_vector(self, change: Dict[str, Any]) -> None:
        """Remove vector for deleted column"""
        try:
            element_id = f"column:{change['schema_name']}.{change['column_name']}"
            self.vector_store.delete_schema_vector(element_id)
            
            logger.debug(f"Removed vector for deleted column: {change['table_key']}.{change['column_name']}")
            
        except Exception as e:
            logger.error(f"Failed to remove column vector: {e}")
    
    def _update_column_vector(self, change: Dict[str, Any]) -> None:
        """Update vector for modified column"""
        try:
            element_id = f"column:{change['schema_name']}.{change['column_name']}"
            
            updated_metadata = change['after_state'].copy()
            updated_metadata['table_name'] = change['table_name']
            updated_metadata['schema_name'] = change['schema_name']
            updated_metadata['change_history'] = {
                'previous_type': change['before_state'].get('type'),
                'new_type': change['after_state'].get('type'),
                'changed_at': change['timestamp'].isoformat()
            }
            
            self.vector_store.update_schema_vector(
                element_id=element_id,
                metadata=updated_metadata,
                semantic_tags=["column", "schema", "modified"],
                business_context={'source': 'schema_evolution', 'change_type': 'column_modified'}
            )
            
            logger.debug(f"Updated vector for modified column: {change['table_key']}.{change['column_name']}")
            
        except Exception as e:
            logger.error(f"Failed to update column vector: {e}")
    
    def _find_patterns_affected_by_change(self, change: Dict[str, Any]) -> List[str]:
        """Find patterns affected by schema change"""
        affected_patterns = []
        
        # Check success patterns
        for pattern_id, pattern in self.success_patterns.items():
            if self._is_pattern_affected_by_change(pattern, change):
                affected_patterns.append(pattern_id)
        
        # Check error patterns
        for error_id, error_pattern in self.error_patterns.items():
            if self._is_error_pattern_affected_by_change(error_pattern, change):
                affected_patterns.append(error_id)
        
        return affected_patterns
    
    def _is_pattern_affected_by_change(self, pattern: QueryPattern, change: Dict[str, Any]) -> bool:
        """Check if a success pattern is affected by schema change"""
        # Check if pattern references the changed table/column
        table_name = change['table_name']
        column_name = change.get('column_name', '')
        
        # Check SQL query for references
        sql_upper = pattern.sql_query.upper()
        
        if table_name.upper() in sql_upper:
            return True
        
        if column_name and column_name.upper() in sql_upper:
            return True
        
        # Check metadata for table/column references
        tables_used = pattern.metadata.get('tables_used', [])
        columns_used = pattern.metadata.get('columns_used', [])
        
        if table_name in tables_used:
            return True
        
        if column_name in columns_used:
            return True
        
        return False
    
    def _is_error_pattern_affected_by_change(self, error_pattern: ErrorPattern, change: Dict[str, Any]) -> bool:
        """Check if an error pattern is affected by schema change"""
        table_name = change['table_name']
        column_name = change.get('column_name', '')
        
        # Check failed SQL for references
        if table_name.upper() in error_pattern.failed_sql.upper():
            return True
        
        if column_name and column_name.upper() in error_pattern.failed_sql.upper():
            return True
        
        # Check error message for references
        if table_name in error_pattern.error_message:
            return True
        
        if column_name and column_name in error_pattern.error_message:
            return True
        
        return False
    
    def _store_schema_evolution_pattern(self, change: Dict[str, Any], affected_patterns: List[str]) -> None:
        """Store schema evolution pattern"""
        evolution_id = f"evolution_{hash(str(change)) & 0x7FFFFFFF}"
        
        evolution_pattern = SchemaEvolutionPattern(
            evolution_id=evolution_id,
            schema_name=change['schema_name'],
            change_type=change['change_type'],
            before_state=change['before_state'],
            after_state=change['after_state'],
            affected_patterns=affected_patterns,
            adaptation_strategy=self._determine_adaptation_strategy(change),
            confidence=0.8,
            created_at=datetime.now(),
            metadata={
                'table_name': change['table_name'],
                'column_name': change.get('column_name'),
                'timestamp': change['timestamp'].isoformat(),
                'affected_pattern_count': len(affected_patterns)
            }
        )
        
        self.schema_evolution_patterns[evolution_id] = evolution_pattern
        logger.debug(f"Stored schema evolution pattern: {evolution_id}")
    
    def _determine_adaptation_strategy(self, change: Dict[str, Any]) -> str:
        """Determine adaptation strategy for schema change"""
        change_type = change['change_type']
        
        strategies = {
            'table_added': 'extend_patterns',
            'table_removed': 'deprecate_patterns',
            'column_added': 'extend_column_patterns',
            'column_removed': 'update_column_patterns',
            'column_type_changed': 'adapt_type_patterns',
            'relationship_added': 'extend_join_patterns',
            'relationship_removed': 'update_join_patterns'
        }
        
        return strategies.get(change_type, 'manual_review')
    
    def create_backward_compatibility(self, schema_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create backward compatibility for existing patterns.
        
        Args:
            schema_changes: List of schema changes
            
        Returns:
            Dictionary with compatibility information
        """
        logger.info("Creating backward compatibility for existing patterns...")
        
        compatibility_info = {
            'compatible_patterns': [],
            'incompatible_patterns': [],
            'migration_suggestions': [],
            'deprecated_patterns': []
        }
        
        for change in schema_changes:
            affected_patterns = self._find_patterns_affected_by_change(change)
            
            for pattern_id in affected_patterns:
                if pattern_id in self.success_patterns:
                    pattern = self.success_patterns[pattern_id]
                    compatibility = self._assess_pattern_compatibility(pattern, change)
                    
                    if compatibility['is_compatible']:
                        compatibility_info['compatible_patterns'].append({
                            'pattern_id': pattern_id,
                            'change_type': change['change_type'],
                            'compatibility_level': compatibility['level']
                        })
                    else:
                        compatibility_info['incompatible_patterns'].append({
                            'pattern_id': pattern_id,
                            'change_type': change['change_type'],
                            'reason': compatibility['reason']
                        })
                        
                        # Generate migration suggestion
                        migration = self._generate_migration_suggestion(pattern, change)
                        if migration:
                            compatibility_info['migration_suggestions'].append(migration)
                
                elif pattern_id in self.error_patterns:
                    # Error patterns might become obsolete with schema changes
                    error_pattern = self.error_patterns[pattern_id]
                    if self._should_deprecate_error_pattern(error_pattern, change):
                        compatibility_info['deprecated_patterns'].append({
                            'pattern_id': pattern_id,
                            'pattern_type': 'error',
                            'reason': 'Schema change resolves error condition'
                        })
        
        logger.info(f"Backward compatibility analysis complete: {len(compatibility_info['compatible_patterns'])} compatible, {len(compatibility_info['incompatible_patterns'])} incompatible")
        return compatibility_info
    
    def _assess_pattern_compatibility(self, pattern: QueryPattern, change: Dict[str, Any]) -> Dict[str, Any]:
        """Assess if a pattern is compatible with schema change"""
        change_type = change['change_type']
        
        if change_type == 'table_added':
            # New tables don't break existing patterns
            return {'is_compatible': True, 'level': 'full', 'reason': 'New table addition'}
        
        elif change_type == 'table_removed':
            # Check if pattern uses the removed table
            if change['table_name'].upper() in pattern.sql_query.upper():
                return {'is_compatible': False, 'level': 'none', 'reason': 'References removed table'}
            return {'is_compatible': True, 'level': 'full', 'reason': 'Does not reference removed table'}
        
        elif change_type == 'column_added':
            # New columns don't break existing patterns
            return {'is_compatible': True, 'level': 'full', 'reason': 'New column addition'}
        
        elif change_type == 'column_removed':
            # Check if pattern uses the removed column
            column_name = change['column_name']
            if column_name.upper() in pattern.sql_query.upper():
                return {'is_compatible': False, 'level': 'none', 'reason': f'References removed column {column_name}'}
            return {'is_compatible': True, 'level': 'full', 'reason': 'Does not reference removed column'}
        
        elif change_type == 'column_type_changed':
            # Type changes might affect patterns depending on usage
            return {'is_compatible': True, 'level': 'partial', 'reason': 'Column type change may affect operations'}
        
        else:
            return {'is_compatible': True, 'level': 'unknown', 'reason': 'Unknown change type'}
    
    def _generate_migration_suggestion(self, pattern: QueryPattern, change: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate migration suggestion for incompatible pattern"""
        change_type = change['change_type']
        
        if change_type == 'table_removed':
            # Suggest alternative table if available
            return {
                'pattern_id': pattern.pattern_id,
                'migration_type': 'table_replacement',
                'original_sql': pattern.sql_query,
                'suggestion': f"Replace references to '{change['table_name']}' with alternative table",
                'confidence': 0.6
            }
        
        elif change_type == 'column_removed':
            # Suggest alternative column if available
            return {
                'pattern_id': pattern.pattern_id,
                'migration_type': 'column_replacement',
                'original_sql': pattern.sql_query,
                'suggestion': f"Replace references to '{change['column_name']}' with alternative column",
                'confidence': 0.6
            }
        
        return None
    
    def _should_deprecate_error_pattern(self, error_pattern: ErrorPattern, change: Dict[str, Any]) -> bool:
        """Check if error pattern should be deprecated due to schema change"""
        # If the error was about a missing table/column that now exists, deprecate the error pattern
        if change['change_type'] in ['table_added', 'column_added']:
            if change['table_name'] in error_pattern.error_message:
                return True
            if change.get('column_name') and change['column_name'] in error_pattern.error_message:
                return True
        
        return False
    
    def apply_automatic_retraining(self, schema_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add automatic retraining on schema changes.
        
        Args:
            schema_changes: List of schema changes
            
        Returns:
            Dictionary with retraining results
        """
        logger.info(f"Applying automatic retraining for {len(schema_changes)} schema changes...")
        
        retraining_results = {
            'patterns_retrained': 0,
            'patterns_updated': 0,
            'patterns_deprecated': 0,
            'new_patterns_suggested': 0,
            'retraining_errors': []
        }
        
        for change in schema_changes:
            try:
                affected_patterns = self._find_patterns_affected_by_change(change)
                
                for pattern_id in affected_patterns:
                    if pattern_id in self.success_patterns:
                        pattern = self.success_patterns[pattern_id]
                        
                        # Attempt to retrain pattern
                        retrain_result = self._retrain_success_pattern(pattern, change)
                        
                        if retrain_result['success']:
                            retraining_results['patterns_retrained'] += 1
                            
                            # Update pattern with retrained version
                            if retrain_result.get('updated_pattern'):
                                self.success_patterns[pattern_id] = retrain_result['updated_pattern']
                                retraining_results['patterns_updated'] += 1
                        else:
                            # Mark pattern for manual review
                            pattern.metadata['needs_manual_review'] = True
                            pattern.metadata['review_reason'] = f"Schema change: {change['change_type']}"
                    
                    elif pattern_id in self.error_patterns:
                        error_pattern = self.error_patterns[pattern_id]
                        
                        # Check if error pattern should be deprecated
                        if self._should_deprecate_error_pattern(error_pattern, change):
                            error_pattern.metadata['deprecated'] = True
                            error_pattern.metadata['deprecation_reason'] = f"Schema change resolved: {change['change_type']}"
                            retraining_results['patterns_deprecated'] += 1
                
                # Suggest new patterns based on schema additions
                if change['change_type'] in ['table_added', 'column_added']:
                    new_pattern_suggestions = self._suggest_new_patterns_for_addition(change)
                    retraining_results['new_patterns_suggested'] += len(new_pattern_suggestions)
                
            except Exception as e:
                retraining_results['retraining_errors'].append({
                    'change': change,
                    'error': str(e)
                })
                logger.error(f"Retraining error for change {change['change_type']}: {e}")
        
        # Update learning statistics
        self.learning_stats['schema_adaptations'] += len(schema_changes)
        
        logger.info(f"Automatic retraining complete: {retraining_results}")
        return retraining_results
    
    def _retrain_success_pattern(self, pattern: QueryPattern, change: Dict[str, Any]) -> Dict[str, Any]:
        """Retrain a success pattern based on schema change"""
        try:
            # This is a simplified retraining approach
            # In practice, would need more sophisticated pattern adaptation
            
            updated_sql = pattern.sql_query
            needs_update = False
            
            if change['change_type'] == 'column_type_changed':
                # Update any type-specific operations
                old_type = change['before_state'].get('type', '')
                new_type = change['after_state'].get('type', '')
                
                if old_type != new_type:
                    # This would need more sophisticated type conversion logic
                    needs_update = True
            
            elif change['change_type'] == 'table_removed':
                # Pattern is incompatible, cannot retrain automatically
                return {'success': False, 'reason': 'Table removed, manual intervention required'}
            
            elif change['change_type'] == 'column_removed':
                # Pattern is incompatible, cannot retrain automatically
                return {'success': False, 'reason': 'Column removed, manual intervention required'}
            
            if needs_update:
                # Create updated pattern
                updated_pattern = QueryPattern(
                    pattern_id=pattern.pattern_id,
                    pattern_type=pattern.pattern_type,
                    natural_language_query=pattern.natural_language_query,
                    sql_query=updated_sql,
                    query_vector=pattern.query_vector,  # Keep same vector for now
                    sql_vector=self._normalize_vector(self.embedder.encode(updated_sql)),
                    intent_type=pattern.intent_type,
                    complexity_level=pattern.complexity_level,
                    confidence=max(0.5, pattern.confidence - 0.1),  # Reduce confidence slightly
                    usage_count=pattern.usage_count,
                    success_rate=pattern.success_rate,
                    last_used=pattern.last_used,
                    created_at=pattern.created_at,
                    metadata={
                        **pattern.metadata,
                        'retrained_at': datetime.now().isoformat(),
                        'retrained_for_change': change['change_type']
                    },
                    semantic_tags=pattern.semantic_tags + ['retrained']
                )
                
                return {'success': True, 'updated_pattern': updated_pattern}
            
            return {'success': True, 'reason': 'No retraining needed'}
            
        except Exception as e:
            return {'success': False, 'reason': f'Retraining failed: {e}'}
    
    def _suggest_new_patterns_for_addition(self, change: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest new patterns for schema additions"""
        suggestions = []
        
        if change['change_type'] == 'table_added':
            table_name = change['table_name']
            
            # Suggest basic patterns for new table
            suggestions.extend([
                {
                    'pattern_type': 'count_query',
                    'natural_language': f"How many records are in {table_name}?",
                    'suggested_sql': f"SELECT COUNT(*) FROM {change['schema_name']}.{table_name}",
                    'confidence': 0.7
                },
                {
                    'pattern_type': 'select_all',
                    'natural_language': f"Show me all {table_name} records",
                    'suggested_sql': f"SELECT TOP 10 * FROM {change['schema_name']}.{table_name}",
                    'confidence': 0.7
                }
            ])
        
        elif change['change_type'] == 'column_added':
            table_name = change['table_name']
            column_name = change['column_name']
            
            # Suggest patterns for new column
            suggestions.append({
                'pattern_type': 'column_query',
                'natural_language': f"Show me {column_name} from {table_name}",
                'suggested_sql': f"SELECT {column_name} FROM {change['schema_name']}.{table_name}",
                'confidence': 0.6
            })
        
        return suggestions
    
    def get_schema_evolution_statistics(self) -> Dict[str, Any]:
        """Get schema evolution statistics"""
        if not self.schema_evolution_patterns:
            return {'total_evolution_patterns': 0}
        
        # Change type distribution
        change_type_dist = {}
        for pattern in self.schema_evolution_patterns.values():
            change_type = pattern.change_type
            change_type_dist[change_type] = change_type_dist.get(change_type, 0) + 1
        
        # Recent changes
        recent_changes = sorted(
            self.schema_evolution_patterns.values(),
            key=lambda ep: ep.created_at,
            reverse=True
        )[:5]
        
        return {
            'total_evolution_patterns': len(self.schema_evolution_patterns),
            'change_type_distribution': change_type_dist,
            'total_affected_patterns': sum(len(ep.affected_patterns) for ep in self.schema_evolution_patterns.values()),
            'recent_changes': [
                {
                    'evolution_id': ep.evolution_id,
                    'change_type': ep.change_type,
                    'schema_name': ep.schema_name,
                    'affected_patterns_count': len(ep.affected_patterns),
                    'created_at': ep.created_at.isoformat()
                }
                for ep in recent_changes
            ]
        }
    
    def save_schema_evolution_patterns_to_disk(self) -> None:
        """Save schema evolution patterns to disk"""
        try:
            evolution_patterns_data = {}
            for evolution_id, pattern in self.schema_evolution_patterns.items():
                pattern_dict = {
                    'evolution_id': pattern.evolution_id,
                    'schema_name': pattern.schema_name,
                    'change_type': pattern.change_type,
                    'before_state': pattern.before_state,
                    'after_state': pattern.after_state,
                    'affected_patterns': pattern.affected_patterns,
                    'adaptation_strategy': pattern.adaptation_strategy,
                    'confidence': pattern.confidence,
                    'created_at': pattern.created_at.isoformat(),
                    'metadata': pattern.metadata
                }
                evolution_patterns_data[evolution_id] = pattern_dict
            
            evolution_patterns_path = os.path.join(self.learning_data_path, "schema_evolution_patterns.json")
            with open(evolution_patterns_path, 'w') as f:
                json.dump(evolution_patterns_data, f, indent=2)
            
            logger.info(f"Saved {len(self.schema_evolution_patterns)} schema evolution patterns to disk")
            
        except Exception as e:
            logger.error(f"Error saving schema evolution patterns to disk: {e}")
            raise
    
    def _load_schema_evolution_patterns_from_disk(self) -> None:
        """Load schema evolution patterns from disk"""
        try:
            evolution_patterns_path = os.path.join(self.learning_data_path, "schema_evolution_patterns.json")
            
            if os.path.exists(evolution_patterns_path):
                with open(evolution_patterns_path, 'r') as f:
                    evolution_patterns_data = json.load(f)
                
                for evolution_id, pattern_dict in evolution_patterns_data.items():
                    pattern_dict['created_at'] = datetime.fromisoformat(pattern_dict['created_at'])
                    
                    self.schema_evolution_patterns[evolution_id] = SchemaEvolutionPattern(**pattern_dict)
            
            logger.info(f"Loaded {len(self.schema_evolution_patterns)} schema evolution patterns from disk")
            
        except Exception as e:
            logger.warning(f"Could not load schema evolution patterns from disk: {e}")
            self.schema_evolution_patterns = {}