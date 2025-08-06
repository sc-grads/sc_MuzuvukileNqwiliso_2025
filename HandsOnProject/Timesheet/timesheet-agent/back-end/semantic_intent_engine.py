#!/usr/bin/env python3
"""
SemanticIntentEngine - Query understanding through vector similarity and intent classification.

This module implements the core semantic understanding system that processes natural language
queries and extracts intent, entities, and context using vector embeddings.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
from sentence_transformers import SentenceTransformer
import re
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Enumeration of query intent types"""
    GREETING = "greeting"
    SELECT = "select"
    AGGREGATE = "aggregate"
    JOIN = "join"
    FILTER = "filter"
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MAX = "max"
    MIN = "min"
    GROUP_BY = "group_by"
    ORDER_BY = "order_by"
    TEMPORAL = "temporal"
    COMPARISON = "comparison"
    UNKNOWN = "unknown"


class EntityType(Enum):
    """Enumeration of entity types that can be extracted from queries"""
    PERSON = "person"
    PROJECT = "project"
    CLIENT = "client"
    TIMESHEET_CONCEPT = "timesheet_concept"
    DATE = "date"
    TIME_PERIOD = "time_period"
    NUMBER = "number"
    STATUS = "status"
    DEPARTMENT = "department"
    LOCATION = "location"
    SKILL = "skill"
    ROLE = "role"
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"          # Single table, basic conditions
    MODERATE = "moderate"      # Multiple tables, joins
    COMPLEX = "complex"        # Multiple joins, aggregations, subqueries
    VERY_COMPLEX = "very_complex"  # Complex nested queries, multiple aggregations


@dataclass
class Entity:
    """Semantically extracted entity from query"""
    name: str
    entity_type: EntityType
    confidence: float
    original_text: str
    position: Tuple[int, int]  # Start and end position in query
    schema_mapping: Optional['SchemaMapping'] = None
    context_vector: Optional[np.ndarray] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SchemaMapping:
    """Dynamic mapping to database schema elements"""
    table: str
    column: Optional[str]
    relationship_path: List[str]
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class TemporalContext:
    """Temporal context extracted from queries"""
    time_reference: str  # "last month", "2023", "this year", etc.
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    relative: bool  # True for relative dates like "last month"
    confidence: float


@dataclass
class AggregationType:
    """Aggregation type and parameters"""
    function: str  # COUNT, SUM, AVG, MAX, MIN
    column: Optional[str]
    group_by_columns: List[str]
    having_conditions: List[str]


@dataclass
class QueryIntent:
    """Semantic representation of query intent"""
    intent_type: IntentType
    confidence: float
    entities: List[Entity]
    temporal_context: Optional[TemporalContext]
    aggregation_type: Optional[AggregationType]
    complexity_level: ComplexityLevel
    original_query: str
    query_vector: np.ndarray
    semantic_features: Dict[str, Any]


class SemanticIntentEngine:
    """
    Understand query intent through vector similarity and semantic analysis.
    
    This class processes natural language queries and extracts semantic meaning,
    intent classification, and entity recognition using vector embeddings.
    """
    
    def __init__(self, 
                 vector_store: 'VectorSchemaStore',
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the SemanticIntentEngine.
        
        Args:
            vector_store: VectorSchemaStore instance for schema context
            embedding_model: Sentence transformer model name
        """
        self.vector_store = vector_store
        self.embedding_model_name = embedding_model
        self.embedder = SentenceTransformer(embedding_model)
        
        # Intent classification patterns stored as vectors
        self.intent_patterns = {}
        self._initialize_intent_patterns()
        
        # Entity extraction patterns
        self.entity_patterns = {}
        self._initialize_entity_patterns()
        
        # Temporal patterns for date/time extraction
        self.temporal_patterns = self._initialize_temporal_patterns()
        
        self.greeting_patterns = [
            r'\b(hi|hello|hey|good\s+(morning|afternoon|evening))\b',
            r'\bhow\s+are\s+you\b',
            r'\bwhat\s+can\s+you\s+do\b'
        ]
        
        logger.info(f"SemanticIntentEngine initialized with model: {embedding_model}")
    
    def _initialize_intent_patterns(self):
        """Initialize intent classification patterns with vector embeddings"""
        intent_examples = {
            IntentType.GREETING: [
                "hello", "hi", "hey", "good morning", "good afternoon", 
                "how are you", "what can you do"
            ],
            IntentType.SELECT: [
                "show me", "list all", "get", "find", "display", "what are",
                "who are", "which", "retrieve", "fetch"
            ],
            IntentType.AGGREGATE: [
                "total", "sum", "count", "average", "mean", "maximum", "minimum",
                "how many", "how much", "aggregate", "summarize"
            ],
            IntentType.COUNT: [
                "how many", "count", "number of", "total number", "quantity"
            ],
            IntentType.SUM: [
                "total", "sum", "add up", "total amount", "sum of"
            ],
            IntentType.AVERAGE: [
                "average", "mean", "avg", "typical", "on average"
            ],
            IntentType.MAX: [
                "maximum", "max", "highest", "largest", "most", "top"
            ],
            IntentType.MIN: [
                "minimum", "min", "lowest", "smallest", "least", "bottom"
            ],
            IntentType.FILTER: [
                "where", "with", "having", "that have", "filter", "only",
                "exclude", "include", "matching"
            ],
            IntentType.JOIN: [
                "and", "with", "along with", "together with", "including",
                "combined with", "related to"
            ],
            IntentType.GROUP_BY: [
                "by", "grouped by", "per", "for each", "broken down by",
                "categorized by", "organized by"
            ],
            IntentType.ORDER_BY: [
                "sorted", "ordered", "ranked", "arranged", "top", "bottom",
                "ascending", "descending"
            ],
            IntentType.TEMPORAL: [
                "when", "during", "in", "last", "this", "next", "between",
                "from", "to", "since", "until", "before", "after"
            ],
            IntentType.COMPARISON: [
                "more than", "less than", "greater than", "smaller than",
                "equal to", "not equal", "compare", "versus", "vs"
            ]
        }
        
        # Create vector embeddings for each intent type
        for intent_type, examples in intent_examples.items():
            # Combine examples into a single text for embedding
            combined_text = " ".join(examples)
            embedding = self.embedder.encode(combined_text)
            self.intent_patterns[intent_type] = {
                'embedding': self._normalize_vector(embedding),
                'examples': examples,
                'confidence_threshold': 0.3
            }
    
    def _initialize_entity_patterns(self):
        """Initialize entity extraction patterns"""
        entity_examples = {
            EntityType.PERSON: [
                "employee", "person", "user", "staff", "worker", "member",
                "developer", "manager", "analyst", "consultant",
                # Examples from training data
                "Karabo Tsaoane", "Pascal Govender", "Bongani"
            ],
            EntityType.PROJECT: [
                "project", "task", "assignment", "work", "job", "initiative",
                "program", "campaign", "effort",
                # Examples from training data
                "Graduate Program"
            ],
            EntityType.CLIENT: [
                "client", "customer", "account",
                # Examples from training data
                "C. Steinweg"
            ],
            EntityType.TIMESHEET_CONCEPT: [
                "timesheet", "hours", "billable", "non-billable", "overtime",
                "leave", "vacation", "sick time", "work log", "standup meeting",
                "soft skills", "progress check", "database", "training", "finalweek"
            ],
            EntityType.DATE: [
                "date", "day", "month", "year", "time", "when", "during",
                # Examples from training data
                "April", "March"
            ],
            EntityType.TIME_PERIOD: [
                "week", "month", "quarter", "year", "period", "duration",
                "timeframe", "span", "range"
            ],
            EntityType.NUMBER: [
                "hours", "amount", "quantity", "count", "number", "total",
                "sum", "value"
            ],
            EntityType.STATUS: [
                "status", "state", "condition", "phase", "stage", "level",
                # Examples from training data
                "Billable", "Non-Billable", "Pending", "Approved", "Rejected"
            ],
            EntityType.DEPARTMENT: [
                "department", "team", "group", "division", "unit", "section"
            ],
            EntityType.LOCATION: [
                "location", "place", "site", "office", "building", "city"
            ],
            EntityType.SKILL: [
                "skill", "expertise", "ability", "competency", "knowledge",
                # Examples from training data
                "soft skills", "Linux"
            ],
            EntityType.ROLE: [
                "role", "position", "title", "job", "function", "responsibility"
            ]
        }
        
        # Create vector embeddings for each entity type
        for entity_type, examples in entity_examples.items():
            # This check ensures we don't re-calculate embeddings unnecessarily,
            # but for this operation, it will add all the new ones.
            if entity_type not in self.entity_patterns:
                combined_text = " ".join(examples)
                embedding = self.embedder.encode(combined_text)
                self.entity_patterns[entity_type] = {
                    'embedding': self._normalize_vector(embedding),
                    'examples': examples,
                    'confidence_threshold': 0.25
                }
    
    def _initialize_temporal_patterns(self) -> Dict[str, Any]:
        """Initialize temporal pattern recognition"""
        return {
            'relative_patterns': [
                r'\b(last|past|previous)\s+(week|month|quarter|year)\b',
                r'\b(this|current)\s+(week|month|quarter|year)\b',
                r'\b(next|coming|upcoming)\s+(week|month|quarter|year)\b',
                r'\b(yesterday|today|tomorrow)\b',
                r'\b(\d+)\s+(days?|weeks?|months?|years?)\s+ago\b'
            ],
            'absolute_patterns': [
                r'\b(\d{4})\b',  # Year
                r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # MM/DD/YYYY
                r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',  # YYYY-MM-DD
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b',
                r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b'
            ],
            'range_patterns': [
                r'\bbetween\s+(.+?)\s+and\s+(.+?)\b',
                r'\bfrom\s+(.+?)\s+to\s+(.+?)\b',
                r'\bsince\s+(.+?)\b',
                r'\buntil\s+(.+?)\b'
            ]
        }
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector for cosine similarity"""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def analyze_query(self, nl_query: str) -> QueryIntent:
        """
        Analyze natural language query and extract semantic intent.
        
        Args:
            nl_query: Natural language query string
            
        Returns:
            QueryIntent object with extracted semantic information
        """
        logger.info(f"Analyzing query: {nl_query}")
        
        # Fast-path for simple greetings
        query_lower = nl_query.lower().strip()
        if any(re.search(pattern, query_lower) for pattern in self.greeting_patterns):
            return QueryIntent(
                intent_type=IntentType.GREETING,
                confidence=0.99,
                entities=[],
                temporal_context=None,
                aggregation_type=None,
                complexity_level=ComplexityLevel.SIMPLE,
                original_query=nl_query,
                query_vector=np.array([]),
                semantic_features={'query_length': len(nl_query.split())}
            )
        
        # Generate query vector
        query_vector = self._normalize_vector(self.embedder.encode(nl_query))
        
        # Classify intent
        intent_type, intent_confidence = self._classify_intent(nl_query, query_vector)
        
        # Extract entities
        entities = self._extract_entities(nl_query, query_vector)
        
        # Extract temporal context
        temporal_context = self._extract_temporal_context(nl_query)
        
        # Determine aggregation type
        aggregation_type = self._determine_aggregation_type(nl_query, intent_type)
        
        # Assess complexity
        complexity_level = self._assess_complexity(nl_query, intent_type, entities)
        
        # Extract semantic features
        semantic_features = self._extract_semantic_features(nl_query, query_vector)
        
        query_intent = QueryIntent(
            intent_type=intent_type,
            confidence=intent_confidence,
            entities=entities,
            temporal_context=temporal_context,
            aggregation_type=aggregation_type,
            complexity_level=complexity_level,
            original_query=nl_query,
            query_vector=query_vector,
            semantic_features=semantic_features
        )
        
        logger.info(f"Query analysis complete: Intent={intent_type.value}, Confidence={intent_confidence:.3f}")
        return query_intent
    
    def _classify_intent(self, query: str, query_vector: np.ndarray) -> Tuple[IntentType, float]:
        """
        Classify query intent using vector similarity.
        
        Args:
            query: Natural language query
            query_vector: Normalized query vector
            
        Returns:
            Tuple of (IntentType, confidence_score)
        """
        best_intent = IntentType.UNKNOWN
        best_score = 0.0
        
        # Calculate similarity with each intent pattern
        for intent_type, pattern_data in self.intent_patterns.items():
            pattern_embedding = pattern_data['embedding']
            similarity = np.dot(query_vector, pattern_embedding)
            
            # Apply confidence threshold
            if similarity > pattern_data['confidence_threshold'] and similarity > best_score:
                best_score = similarity
                best_intent = intent_type
        
        # Additional rule-based classification for better accuracy
        query_lower = query.lower()
        
        # Override with rule-based patterns for high-confidence cases
        if any(word in query_lower for word in ['how many', 'count', 'number of']):
            if best_score < 0.8:  # Only override if vector similarity is not very high
                best_intent = IntentType.COUNT
                best_score = max(best_score, 0.8)
        
        elif any(word in query_lower for word in ['show me', 'list', 'display', 'get all', 'find all']) and not any(word in query_lower for word in ['how many', 'count', 'total', 'sum']):
            if best_score < 0.8:
                best_intent = IntentType.SELECT
                best_score = max(best_score, 0.8)
        
        elif any(word in query_lower for word in ['total', 'sum of', 'add up']):
            if best_score < 0.8:
                best_intent = IntentType.SUM
                best_score = max(best_score, 0.8)
        
        elif any(word in query_lower for word in ['average', 'mean', 'avg']):
            if best_score < 0.8:
                best_intent = IntentType.AVERAGE
                best_score = max(best_score, 0.8)
        
        elif any(word in query_lower for word in ['maximum', 'max', 'highest', 'most']):
            if best_score < 0.8:
                best_intent = IntentType.MAX
                best_score = max(best_score, 0.8)
        
        elif any(word in query_lower for word in ['minimum', 'min', 'lowest', 'least']):
            if best_score < 0.8:
                best_intent = IntentType.MIN
                best_score = max(best_score, 0.8)
        
        return best_intent, float(best_score)
    
    def _extract_entities(self, query: str, query_vector: np.ndarray) -> List[Entity]:
        """
        Extract entities from query using vector-based semantic matching.
        
        Args:
            query: Natural language query
            query_vector: Normalized query vector
            
        Returns:
            List of extracted Entity objects
        """
        entities = []
        query_lower = query.lower()
        words = query.split()
        
        # Use vector similarity to identify potential entities
        for entity_type, pattern_data in self.entity_patterns.items():
            pattern_embedding = pattern_data['embedding']
            similarity = np.dot(query_vector, pattern_embedding)
            
            if similarity > pattern_data['confidence_threshold']:
                # Look for specific entity instances in the query
                entity_instances = self._find_entity_instances(
                    query, entity_type, similarity
                )
                entities.extend(entity_instances)
        
        # Enhanced entity extraction methods
        entities.extend(self._extract_named_entities(query))
        entities.extend(self._extract_numeric_entities(query))
        entities.extend(self._extract_date_entities(query))
        entities.extend(self._extract_dynamic_entities(query, query_vector))
        entities.extend(self._extract_contextual_entities(query, query_vector))
        
        # Map entities to schema elements if vector store is available
        entities = self._map_entities_to_schema(entities, query_vector)
        
        # Remove duplicates and sort by confidence
        unique_entities = self._deduplicate_entities(entities)
        unique_entities.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_entities
    
    def _find_entity_instances(self, query: str, entity_type: EntityType, base_confidence: float) -> List[Entity]:
        """Find specific instances of an entity type in the query"""
        entities = []
        query_lower = query.lower()
        
        # Define entity-specific patterns
        if entity_type == EntityType.PERSON:
            # Look for potential person names (capitalized words)
            words = query.split()
            for i, word in enumerate(words):
                if word[0].isupper() and len(word) > 2:
                    # Check if it's likely a person name (not at start of sentence)
                    if i > 0 or any(indicator in query_lower for indicator in ['employee', 'person', 'user']):
                        start_pos = query.find(word)
                        end_pos = start_pos + len(word)
                        
                        entities.append(Entity(
                            name=word,
                            entity_type=entity_type,
                            confidence=base_confidence * 0.8,
                            original_text=word,
                            position=(start_pos, end_pos)
                        ))
        
        elif entity_type == EntityType.PROJECT:
            # Look for project-related terms
            project_indicators = ['project', 'task', 'assignment']
            for indicator in project_indicators:
                if indicator in query_lower:
                    start_pos = query_lower.find(indicator)
                    end_pos = start_pos + len(indicator)
                    
                    entities.append(Entity(
                        name=indicator,
                        entity_type=entity_type,
                        confidence=base_confidence,
                        original_text=query[start_pos:end_pos],
                        position=(start_pos, end_pos)
                    ))
        
        return entities
    
    def _extract_named_entities(self, query: str) -> List[Entity]:
        """Extract named entities using pattern matching"""
        entities = []
        
        # Comprehensive stop words list for query filtering
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'show', 'list', 'all', 'me', 'what', 
            'how', 'many', 'get', 'find', 'display', 'who', 'which', 'retrieve', 'fetch', 'system', 
            'clients', 'employees', 'projects', 'data', 'information', 'records', 'entries', 'items',
            'available', 'types', 'from', 'with', 'by', 'of', 'is', 'are', 'was', 'were', 'have', 'has',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must',
            'give', 'provide', 'return', 'select', 'choose', 'pick', 'take', 'bring', 'send', 'tell',
            'hello', 'hi', 'hey', 'world', 'wolrd'  # Common greetings and typos
        }
        
        # Simple capitalized word detection for person names
        words = query.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2 and word.isalpha():
                # Skip stop words and common query terms
                if word.lower() not in stop_words:
                    # Additional validation: must be a potential person name
                    # Check if it appears in context that suggests it's a person
                    context_words = []
                    if i > 0:
                        context_words.append(words[i-1].lower())
                    if i < len(words) - 1:
                        context_words.append(words[i+1].lower())
                    
                    # Only consider as person if there are person-related context clues
                    person_indicators = {'employee', 'person', 'user', 'staff', 'worker', 'member', 'hours', 'worked', 'timesheet', 'leave'}
                    if any(indicator in ' '.join(context_words) for indicator in person_indicators) or \
                       any(indicator in query.lower() for indicator in person_indicators):
                        start_pos = query.find(word)
                        end_pos = start_pos + len(word)
                        
                        entities.append(Entity(
                        name=word,
                        entity_type=EntityType.PERSON,
                        confidence=0.6,
                        original_text=word,
                        position=(start_pos, end_pos)
                    ))
        
        return entities
    
    def _extract_numeric_entities(self, query: str) -> List[Entity]:
        """Extract numeric entities from query using advanced NLP"""
        entities = []
        
        # Use the sophisticated numeric extraction from nlp.py
        from nlp import extract_numeric_values, extract_comparison_operators
        
        # Extract numeric values with context
        numeric_info = extract_numeric_values(query)
        
        # Process different types of numeric values
        for value in numeric_info.get('values', []):
            entities.append(Entity(
                name=str(value),
                entity_type=EntityType.NUMBER,
                confidence=0.9,
                original_text=str(value),
                position=(0, 0),  # Position would need to be tracked separately
                metadata={'context': 'general_number'}
            ))
        
        for value in numeric_info.get('hours', []):
            entities.append(Entity(
                name=str(value),
                entity_type=EntityType.NUMBER,
                confidence=0.95,
                original_text=str(value),
                position=(0, 0),
                metadata={'context': 'hours', 'unit': 'hours'}
            ))
        
        for value in numeric_info.get('currencies', []):
            entities.append(Entity(
                name=str(value),
                entity_type=EntityType.NUMBER,
                confidence=0.95,
                original_text=str(value),
                position=(0, 0),
                metadata={'context': 'currency', 'unit': 'currency'}
            ))
        
        # Extract comparison operators
        comparisons = extract_comparison_operators(query)
        for comp in comparisons:
            entities.append(Entity(
                name=f"{comp['operator']} {comp['value']}",
                entity_type=EntityType.NUMBER,
                confidence=0.9,
                original_text=comp['original_text'],
                position=(0, 0),
                metadata={'context': 'comparison', 'operator': comp['operator'], 'value': comp['value']}
            ))
        
        return entities
    
    def _extract_date_entities(self, query: str) -> List[Entity]:
        """Extract date-related entities from query using advanced NLP"""
        entities = []
        
        # Use the sophisticated date parsing from nlp.py
        from nlp import normalize_date
        
        # Advanced date patterns that nlp.py can handle
        date_patterns = [
            r'\b(?:today|yesterday|tomorrow)\b',
            r'\b(?:this|last|next)\s+(?:week|month|quarter|year)\b',
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b\d{1,2}\s+days?\s+ago\b',
            r'\bin\s+\d{1,2}\s+days?\b',
            r'\b\d{1,2}\s+weeks?\s+ago\b',
            r'\bin\s+\d{1,2}\s+weeks?\b',
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}-\d{1,2}-\d{1,2}'
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, query, re.IGNORECASE):
                date_text = match.group()
                start_pos, end_pos = match.span()
                
                # Use nlp.py's advanced date normalization
                normalized_date = normalize_date(date_text)
                
                if normalized_date:
                    # Determine entity type based on the normalized result
                    entity_type = EntityType.TIME_PERIOD if normalized_date[0] != normalized_date[1] else EntityType.DATE
                    
                    entities.append(Entity(
                        name=date_text,
                        entity_type=entity_type,
                        confidence=0.9,  # Higher confidence due to advanced parsing
                        original_text=date_text,
                        position=(start_pos, end_pos),
                        metadata={'normalized_date': normalized_date}
                    ))
        
        return entities
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities based on position and type"""
        unique_entities = []
        seen_positions = set()
        
        for entity in entities:
            position_key = (entity.position, entity.entity_type)
            if position_key not in seen_positions:
                unique_entities.append(entity)
                seen_positions.add(position_key)
        
        return unique_entities
    
    def _extract_temporal_context(self, query: str) -> Optional[TemporalContext]:
        """Extract temporal context from query"""
        query_lower = query.lower()
        
        # Check for relative time references
        for pattern in self.temporal_patterns['relative_patterns']:
            match = re.search(pattern, query_lower)
            if match:
                time_reference = match.group()
                return TemporalContext(
                    time_reference=time_reference,
                    start_date=None,
                    end_date=None,
                    relative=True,
                    confidence=0.8
                )
        
        # Check for absolute dates
        for pattern in self.temporal_patterns['absolute_patterns']:
            match = re.search(pattern, query)
            if match:
                time_reference = match.group()
                return TemporalContext(
                    time_reference=time_reference,
                    start_date=None,  # Would need date parsing logic
                    end_date=None,
                    relative=False,
                    confidence=0.9
                )
        
        return None
    
    def _determine_aggregation_type(self, query: str, intent_type: IntentType) -> Optional[AggregationType]:
        """Determine aggregation type based on query and intent"""
        query_lower = query.lower()
        
        if intent_type in [IntentType.COUNT, IntentType.SUM, IntentType.AVERAGE, IntentType.MAX, IntentType.MIN]:
            function_map = {
                IntentType.COUNT: "COUNT",
                IntentType.SUM: "SUM",
                IntentType.AVERAGE: "AVG",
                IntentType.MAX: "MAX",
                IntentType.MIN: "MIN"
            }
            
            return AggregationType(
                function=function_map[intent_type],
                column=None,  # Would be determined later with schema context
                group_by_columns=[],
                having_conditions=[]
            )
        
        return None
    
    def _assess_complexity(self, query: str, intent_type: IntentType, entities: List[Entity]) -> ComplexityLevel:
        """Assess query complexity based on various factors"""
        complexity_score = 0
        query_lower = query.lower()
        
        # Base complexity from intent type
        if intent_type in [IntentType.SELECT, IntentType.FILTER]:
            complexity_score += 1
        elif intent_type in [IntentType.COUNT, IntentType.SUM, IntentType.AVERAGE]:
            complexity_score += 2
        elif intent_type in [IntentType.JOIN, IntentType.GROUP_BY]:
            complexity_score += 3
        
        # Add complexity for multiple entities
        complexity_score += min(len(entities), 3)
        
        # Add complexity for temporal context
        if any(word in query_lower for word in ['between', 'from', 'to', 'during']):
            complexity_score += 1
        
        # Add complexity for multiple conditions
        condition_words = ['and', 'or', 'where', 'having', 'with']
        condition_count = sum(1 for word in condition_words if word in query_lower)
        complexity_score += min(condition_count, 2)
        
        # Map score to complexity level
        if complexity_score <= 2:
            return ComplexityLevel.SIMPLE
        elif complexity_score <= 4:
            return ComplexityLevel.MODERATE
        elif complexity_score <= 6:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX
    
    def _extract_semantic_features(self, query: str, query_vector: np.ndarray) -> Dict[str, Any]:
        """Extract additional semantic features from query"""
        query_lower = query.lower()
        
        features = {
            'query_length': len(query.split()),
            'has_negation': any(neg in query_lower for neg in ['not', 'no', 'none', 'never']),
            'has_comparison': any(comp in query_lower for comp in ['more', 'less', 'greater', 'smaller', 'equal']),
            'has_temporal': any(temp in query_lower for temp in ['when', 'during', 'last', 'this', 'next']),
            'has_aggregation': any(agg in query_lower for agg in ['total', 'sum', 'count', 'average', 'max', 'min']),
            'question_type': self._determine_question_type(query_lower),
            'semantic_density': float(np.linalg.norm(query_vector))
        }
        
        return features
    
    def _determine_question_type(self, query_lower: str) -> str:
        """Determine the type of question being asked"""
        if query_lower.startswith(('what', 'which')):
            return 'what'
        elif query_lower.startswith('who'):
            return 'who'
        elif query_lower.startswith('when'):
            return 'when'
        elif query_lower.startswith('where'):
            return 'where'
        elif query_lower.startswith('how'):
            return 'how'
        elif query_lower.startswith('why'):
            return 'why'
        else:
            return 'statement'
    
    def _extract_dynamic_entities(self, query: str, query_vector: np.ndarray) -> List[Entity]:
        """
        Extract entities dynamically using vector similarity with schema context.
        
        Args:
            query: Natural language query
            query_vector: Normalized query vector
            
        Returns:
            List of dynamically extracted entities
        """
        entities = []
        words = query.split()
        
        # Look for potential entity words by checking similarity with schema elements
        if hasattr(self.vector_store, 'find_similar_tables'):
            # Find similar tables to identify potential table entities
            try:
                similar_tables = self.vector_store.find_similar_tables(query_vector, k=3)
                for table_match in similar_tables:
                    if table_match.similarity_score > 0.3:  # Threshold for relevance
                        # Check if table name or related terms appear in query
                        table_name_lower = table_match.table_name.lower()
                        if any(word.lower() in table_name_lower or table_name_lower in word.lower() 
                               for word in words):
                            start_pos = query.lower().find(table_name_lower)
                            if start_pos != -1:
                                end_pos = start_pos + len(table_name_lower)
                                entities.append(Entity(
                                    name=table_match.table_name,
                                    entity_type=self._infer_entity_type_from_table(table_match.table_name),
                                    confidence=table_match.similarity_score,
                                    original_text=query[start_pos:end_pos],
                                    position=(start_pos, end_pos),
                                    schema_mapping=SchemaMapping(
                                        table=table_match.table_name,
                                        column=None,
                                        relationship_path=[],
                                        confidence=table_match.similarity_score,
                                        metadata=table_match.metadata
                                    )
                                ))
            except Exception as e:
                logger.warning(f"Error in dynamic table entity extraction: {e}")
        
        if hasattr(self.vector_store, 'find_similar_columns'):
            # Find similar columns to identify potential column entities
            try:
                similar_columns = self.vector_store.find_similar_columns(query_vector, k=5)
                for column_match in similar_columns:
                    if column_match.similarity_score > 0.3:
                        column_name_lower = column_match.column_name.lower()
                        if any(word.lower() in column_name_lower or column_name_lower in word.lower() 
                               for word in words):
                            start_pos = query.lower().find(column_name_lower)
                            if start_pos != -1:
                                end_pos = start_pos + len(column_name_lower)
                                entities.append(Entity(
                                    name=column_match.column_name,
                                    entity_type=self._infer_entity_type_from_column(
                                        column_match.column_name, column_match.data_type
                                    ),
                                    confidence=column_match.similarity_score,
                                    original_text=query[start_pos:end_pos],
                                    position=(start_pos, end_pos),
                                    schema_mapping=SchemaMapping(
                                        table=column_match.table_name,
                                        column=column_match.column_name,
                                        relationship_path=[],
                                        confidence=column_match.similarity_score,
                                        metadata=column_match.metadata
                                    )
                                ))
            except Exception as e:
                logger.warning(f"Error in dynamic column entity extraction: {e}")
        
        return entities
    
    def _extract_contextual_entities(self, query: str, query_vector: np.ndarray) -> List[Entity]:
        """
        Extract entities based on contextual understanding and domain knowledge.
        
        Args:
            query: Natural language query
            query_vector: Normalized query vector
            
        Returns:
            List of contextually extracted entities
        """
        entities = []
        query_lower = query.lower()
        words = query.split()
        
        # Context-aware entity patterns
        contextual_patterns = {
            # Employee/Person patterns
            'employee_patterns': [
                r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',  # Full names
                r'\b(employee|staff|worker|person)\s+([A-Z][a-z]+)\b',  # employee John
                r'\b([A-Z][a-z]+)\s+(worked|assigned|completed)\b',  # John worked
            ],
            # Project patterns
            'project_patterns': [
                r'\bproject\s+([A-Z][a-zA-Z0-9\s]+)\b',  # project Alpha
                r'\b([A-Z][a-zA-Z0-9]+)\s+project\b',  # Alpha project
                r'\btask\s+([A-Z][a-zA-Z0-9\s]+)\b',  # task Beta
            ],
            # Department patterns
            'department_patterns': [
                r'\b(IT|HR|Finance|Marketing|Sales|Engineering|Development)\b',
                r'\b(department|team|group|division)\s+([A-Z][a-z]+)\b',
            ],
            # Status patterns
            'status_patterns': [
                r'\b(active|inactive|completed|pending|in progress|cancelled)\b',
                r'\bstatus\s+(active|inactive|completed|pending)\b',
            ]
        }
        
        for pattern_type, patterns in contextual_patterns.items():
            entity_type = self._pattern_type_to_entity_type(pattern_type)
            
            for pattern in patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    entity_text = match.group(1) if match.groups() else match.group()
                    start_pos, end_pos = match.span()
                    
                    # Calculate confidence based on context
                    confidence = self._calculate_contextual_confidence(
                        entity_text, pattern_type, query_lower
                    )
                    
                    entities.append(Entity(
                        name=entity_text,
                        entity_type=entity_type,
                        confidence=confidence,
                        original_text=entity_text,
                        position=(start_pos, end_pos),
                        context_vector=self._generate_entity_context_vector(entity_text, query)
                    ))
        
        return entities
    
    def _map_entities_to_schema(self, entities: List[Entity], query_vector: np.ndarray) -> List[Entity]:
        """
        Map extracted entities to schema elements using vector similarity.
        
        Args:
            entities: List of extracted entities
            query_vector: Normalized query vector
            
        Returns:
            List of entities with schema mappings
        """
        if not hasattr(self.vector_store, 'find_similar_tables'):
            return entities
        
        mapped_entities = []
        
        for entity in entities:
            if entity.schema_mapping is None:
                # Try to find schema mapping for this entity
                entity_vector = self.embedder.encode(entity.name)
                entity_vector = self._normalize_vector(entity_vector)
                
                # Find similar tables and columns
                try:
                    similar_tables = self.vector_store.find_similar_tables(entity_vector, k=3)
                    similar_columns = self.vector_store.find_similar_columns(entity_vector, k=5)
                    
                    best_mapping = None
                    best_score = 0.0
                    
                    # Check table mappings
                    for table_match in similar_tables:
                        if table_match.similarity_score > best_score and table_match.similarity_score > 0.2:
                            best_mapping = SchemaMapping(
                                table=table_match.table_name,
                                column=None,
                                relationship_path=[],
                                confidence=table_match.similarity_score,
                                metadata=table_match.metadata
                            )
                            best_score = table_match.similarity_score
                    
                    # Check column mappings
                    for column_match in similar_columns:
                        if column_match.similarity_score > best_score and column_match.similarity_score > 0.2:
                            best_mapping = SchemaMapping(
                                table=column_match.table_name,
                                column=column_match.column_name,
                                relationship_path=[],
                                confidence=column_match.similarity_score,
                                metadata=column_match.metadata
                            )
                            best_score = column_match.similarity_score
                    
                    if best_mapping:
                        entity.schema_mapping = best_mapping
                        # Boost entity confidence if we found a good schema mapping
                        entity.confidence = min(1.0, entity.confidence + (best_score * 0.2))
                
                except Exception as e:
                    logger.warning(f"Error mapping entity to schema: {e}")
            
            mapped_entities.append(entity)
        
        return mapped_entities
    
    def _infer_entity_type_from_table(self, table_name: str) -> EntityType:
        """Infer entity type from table name"""
        table_lower = table_name.lower()
        
        if any(word in table_lower for word in ['employee', 'person', 'user', 'staff', 'worker']):
            return EntityType.PERSON
        elif any(word in table_lower for word in ['project', 'task', 'assignment']):
            return EntityType.PROJECT
        elif any(word in table_lower for word in ['department', 'team', 'group']):
            return EntityType.DEPARTMENT
        elif any(word in table_lower for word in ['location', 'office', 'site']):
            return EntityType.LOCATION
        elif any(word in table_lower for word in ['skill', 'competency', 'expertise']):
            return EntityType.SKILL
        elif any(word in table_lower for word in ['role', 'position', 'title']):
            return EntityType.ROLE
        else:
            return EntityType.UNKNOWN
    
    def _infer_entity_type_from_column(self, column_name: str, data_type: str) -> EntityType:
        """Infer entity type from column name and data type"""
        column_lower = column_name.lower()
        data_type_lower = data_type.lower()
        
        # Date/time columns
        if any(word in column_lower for word in ['date', 'time', 'created', 'updated', 'start', 'end']):
            return EntityType.DATE
        elif any(word in data_type_lower for word in ['date', 'time', 'timestamp']):
            return EntityType.DATE
        
        # Numeric columns
        elif any(word in data_type_lower for word in ['int', 'float', 'decimal', 'numeric']):
            if any(word in column_lower for word in ['hour', 'amount', 'cost', 'salary', 'count']):
                return EntityType.NUMBER
        
        # Status columns
        elif any(word in column_lower for word in ['status', 'state', 'active', 'enabled']):
            return EntityType.STATUS
        
        # Person-related columns
        elif any(word in column_lower for word in ['name', 'employee', 'user', 'person']):
            return EntityType.PERSON
        
        # Project-related columns
        elif any(word in column_lower for word in ['project', 'task', 'assignment']):
            return EntityType.PROJECT
        
        return EntityType.UNKNOWN
    
    def _pattern_type_to_entity_type(self, pattern_type: str) -> EntityType:
        """Convert pattern type to entity type"""
        mapping = {
            'employee_patterns': EntityType.PERSON,
            'project_patterns': EntityType.PROJECT,
            'department_patterns': EntityType.DEPARTMENT,
            'status_patterns': EntityType.STATUS
        }
        return mapping.get(pattern_type, EntityType.UNKNOWN)
    
    def _calculate_contextual_confidence(self, entity_text: str, pattern_type: str, query_lower: str) -> float:
        """Calculate confidence score based on context"""
        base_confidence = 0.7
        
        # Boost confidence for specific patterns
        if pattern_type == 'employee_patterns':
            if any(word in query_lower for word in ['employee', 'person', 'staff', 'worker']):
                base_confidence += 0.2
        elif pattern_type == 'project_patterns':
            if any(word in query_lower for word in ['project', 'task', 'assignment']):
                base_confidence += 0.2
        elif pattern_type == 'department_patterns':
            if any(word in query_lower for word in ['department', 'team', 'group']):
                base_confidence += 0.2
        
        # Reduce confidence for very short entities
        if len(entity_text) < 3:
            base_confidence -= 0.2
        
        return min(1.0, max(0.1, base_confidence))
    
    def _generate_entity_context_vector(self, entity_text: str, query: str) -> np.ndarray:
        """Generate context vector for entity based on surrounding text"""
        # Create context by combining entity with surrounding words
        words = query.split()
        entity_words = entity_text.split()
        
        # Find entity position in query
        entity_start = -1
        for i in range(len(words) - len(entity_words) + 1):
            if words[i:i+len(entity_words)] == entity_words:
                entity_start = i
                break
        
        if entity_start == -1:
            # Entity not found as exact match, use entity text alone
            context_text = entity_text
        else:
            # Include surrounding context (2 words before and after)
            start_idx = max(0, entity_start - 2)
            end_idx = min(len(words), entity_start + len(entity_words) + 2)
            context_words = words[start_idx:end_idx]
            context_text = ' '.join(context_words)
        
        # Generate and normalize context vector
        context_vector = self.embedder.encode(context_text)
        return self._normalize_vector(context_vector)
    
    def get_intent_confidence_scores(self, query: str) -> Dict[IntentType, float]:
        """
        Get confidence scores for all intent types for a given query.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary mapping IntentType to confidence scores
        """
        query_vector = self._normalize_vector(self.embedder.encode(query))
        scores = {}
        
        for intent_type, pattern_data in self.intent_patterns.items():
            pattern_embedding = pattern_data['embedding']
            similarity = np.dot(query_vector, pattern_embedding)
            scores[intent_type] = float(similarity)
        
        return scores
    
    def update_intent_patterns(self, intent_type: IntentType, new_examples: List[str]):
        """
        Update intent patterns with new examples for improved classification.
        
        Args:
            intent_type: Intent type to update
            new_examples: List of new example phrases
        """
        if intent_type in self.intent_patterns:
            # Add new examples
            current_examples = self.intent_patterns[intent_type]['examples']
            updated_examples = list(set(current_examples + new_examples))
            
            # Regenerate embedding
            combined_text = " ".join(updated_examples)
            new_embedding = self.embedder.encode(combined_text)
            
            self.intent_patterns[intent_type]['examples'] = updated_examples
            self.intent_patterns[intent_type]['embedding'] = self._normalize_vector(new_embedding)
            
            logger.info(f"Updated intent patterns for {intent_type.value} with {len(new_examples)} new examples")
    
    def resolve_entity_ambiguity(self, entities: List[Entity], query_context: Dict[str, Any]) -> List[Entity]:
        """
        Resolve ambiguous entities using context and schema information.
        
        Args:
            entities: List of potentially ambiguous entities
            query_context: Additional context information
            
        Returns:
            List of resolved entities
        """
        resolved_entities = []
        
        for entity in entities:
            if entity.confidence < 0.5:  # Low confidence entities need resolution
                resolved_entity = self._resolve_single_entity(entity, entities, query_context)
                resolved_entities.append(resolved_entity)
            else:
                resolved_entities.append(entity)
        
        return resolved_entities
    
    def _resolve_single_entity(self, entity: Entity, all_entities: List[Entity], context: Dict[str, Any]) -> Entity:
        """Resolve a single ambiguous entity"""
        # Try to resolve using schema mapping
        if entity.schema_mapping and entity.schema_mapping.confidence > 0.3:
            # Schema mapping provides good confidence, boost entity confidence
            entity.confidence = min(1.0, entity.confidence + 0.3)
            return entity
        
        # Try to resolve using other entities in the query
        for other_entity in all_entities:
            if other_entity != entity and other_entity.schema_mapping:
                # Check if entities are related through schema
                if self._entities_are_related(entity, other_entity):
                    entity.confidence = min(1.0, entity.confidence + 0.2)
                    break
        
        # Try to resolve using query context
        if 'temporal_context' in context and entity.entity_type == EntityType.DATE:
            entity.confidence = min(1.0, entity.confidence + 0.2)
        
        return entity
    
    def _entities_are_related(self, entity1: Entity, entity2: Entity) -> bool:
        """Check if two entities are related through schema"""
        if not entity1.schema_mapping or not entity2.schema_mapping:
            return False
        
        # Same table relationship
        if entity1.schema_mapping.table == entity2.schema_mapping.table:
            return True
        
        # Check for foreign key relationships (would need schema metadata)
        # This is a simplified check
        return False
    
    def extract_entity_relationships(self, entities: List[Entity]) -> Dict[str, List[str]]:
        """
        Extract relationships between entities based on schema and context.
        
        Args:
            entities: List of extracted entities
            
        Returns:
            Dictionary mapping entity names to related entity names
        """
        relationships = {}
        
        for entity in entities:
            related_entities = []
            
            for other_entity in entities:
                if entity != other_entity and self._entities_are_related(entity, other_entity):
                    related_entities.append(other_entity.name)
            
            if related_entities:
                relationships[entity.name] = related_entities
        
        return relationships
    
    def get_entity_context_suggestions(self, entity: Entity, query: str) -> List[str]:
        """
        Get context-based suggestions for entity disambiguation.
        
        Args:
            entity: Entity to get suggestions for
            query: Original query
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        if entity.entity_type == EntityType.PERSON:
            suggestions.extend([
                f"Did you mean employee '{entity.name}'?",
                f"Are you looking for user '{entity.name}'?",
                f"Is this referring to staff member '{entity.name}'?"
            ])
        elif entity.entity_type == EntityType.PROJECT:
            suggestions.extend([
                f"Did you mean project '{entity.name}'?",
                f"Are you referring to task '{entity.name}'?",
                f"Is this about assignment '{entity.name}'?"
            ])
        elif entity.entity_type == EntityType.DEPARTMENT:
            suggestions.extend([
                f"Did you mean department '{entity.name}'?",
                f"Are you referring to team '{entity.name}'?",
                f"Is this about group '{entity.name}'?"
            ])
        
        # Add schema-based suggestions if available
        if entity.schema_mapping:
            if entity.schema_mapping.column:
                suggestions.append(
                    f"Found column '{entity.schema_mapping.column}' in table '{entity.schema_mapping.table}'"
                )
            else:
                suggestions.append(
                    f"Found table '{entity.schema_mapping.table}'"
                )
        
        return suggestions[:3]  # Return top 3 suggestions

    def generate_clarification_question(self, query_intent: QueryIntent) -> str:
        """
        Generate a clarification question based on a low-confidence intent.
        
        Args:
            query_intent: The low-confidence QueryIntent object
            
        Returns:
            A string with a user-facing clarification question.
        """
        # Start with a generic prompt
        clarification = "I'm not completely sure what you're asking. "
        
        # Extract the most likely entities
        entities = sorted(query_intent.entities, key=lambda x: x.confidence, reverse=True)
        primary_entity = entities[0] if entities else None
        
        intent = query_intent.intent_type
        
        # Build a question based on intent and primary entity
        if intent == IntentType.COUNT and primary_entity:
            # Try to find a plausible table name from schema mapping
            table_name = primary_entity.schema_mapping.table if primary_entity.schema_mapping else primary_entity.name
            clarification += f"Did you mean to ask 'how many {table_name} are there'?"
        
        elif intent == IntentType.SELECT and primary_entity:
            table_name = primary_entity.schema_mapping.table if primary_entity.schema_mapping else primary_entity.name
            clarification += f"Are you trying to list all '{table_name}'?"
            
        elif intent == IntentType.AGGREGATE and primary_entity:
            # Find the most likely aggregation function
            agg_type = query_intent.aggregation_type.function if query_intent.aggregation_type else "total"
            table_name = primary_entity.schema_mapping.table if primary_entity.schema_mapping else primary_entity.name
            clarification += f"Are you asking for the '{agg_type}' of something in '{table_name}'?"
            
        elif primary_entity:
            # Generic fallback if intent is less clear but an entity was found
            entity_name = primary_entity.name
            clarification += f"Is your question related to '{entity_name}'?"
            
        else:
            # Very low confidence fallback
            clarification += "Could you please rephrase your question?"
            
        return clarification
    
    def update_entity_patterns(self, entity_type: EntityType, new_examples: List[str]):
        """
        Update entity patterns with new examples for improved extraction.
        
        Args:
            entity_type: Entity type to update
            new_examples: List of new example phrases
        """
        if entity_type in self.entity_patterns:
            # Add new examples
            current_examples = self.entity_patterns[entity_type]['examples']
            updated_examples = list(set(current_examples + new_examples))
            
            # Regenerate embedding
            combined_text = " ".join(updated_examples)
            new_embedding = self.embedder.encode(combined_text)
            
            self.entity_patterns[entity_type]['examples'] = updated_examples
            self.entity_patterns[entity_type]['embedding'] = self._normalize_vector(new_embedding)
            
            logger.info(f"Updated entity patterns for {entity_type.value} with {len(new_examples)} new examples")
    
    def get_entity_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about entity extraction patterns and performance.
        
        Returns:
            Dictionary with entity extraction statistics
        """
        stats = {
            'entity_types': len(self.entity_patterns),
            'patterns_by_type': {},
            'confidence_thresholds': {}
        }
        
        for entity_type, pattern_data in self.entity_patterns.items():
            stats['patterns_by_type'][entity_type.value] = len(pattern_data['examples'])
            stats['confidence_thresholds'][entity_type.value] = pattern_data['confidence_threshold']
        
        return stats
    
    def resolve_ambiguity(self, query_intent: QueryIntent, context: Dict[str, Any]) -> QueryIntent:
        """
        Resolve ambiguous queries using context and multi-step reasoning.
        
        Args:
            query_intent: Initial query intent with potential ambiguities
            context: Additional context including query history and user preferences
            
        Returns:
            Resolved QueryIntent with reduced ambiguity
        """
        logger.info(f"Resolving ambiguity for query: {query_intent.original_query}")
        
        # Create context vector from query history
        context_vector = self._generate_context_vector(context)
        
        # Detect ambiguity in the query
        ambiguity_score = self._detect_ambiguity(query_intent)
        
        if ambiguity_score > 0.3:  # Significant ambiguity detected
            # Apply context-aware disambiguation
            resolved_intent = self._apply_context_disambiguation(query_intent, context_vector, context)
            
            # Apply multi-step reasoning for complex queries
            if resolved_intent.complexity_level in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
                resolved_intent = self._apply_multi_step_reasoning(resolved_intent, context)
            
            # Resolve entity ambiguities
            resolved_intent.entities = self.resolve_entity_ambiguity(resolved_intent.entities, context)
            
            logger.info(f"Ambiguity resolved: score reduced from {ambiguity_score:.3f} to {self._detect_ambiguity(resolved_intent):.3f}")
            return resolved_intent
        
        return query_intent
    
    def _generate_context_vector(self, context: Dict[str, Any]) -> np.ndarray:
        """
        Generate context vector from query history and user preferences.
        
        Args:
            context: Context information including query history
            
        Returns:
            Normalized context vector
        """
        context_texts = []
        
        # Add recent query history
        if 'query_history' in context:
            recent_queries = context['query_history'][-5:]  # Last 5 queries
            context_texts.extend([q.get('query', '') for q in recent_queries])
        
        # Add user preferences or domain context
        if 'domain_context' in context:
            context_texts.append(context['domain_context'])
        
        # Add current session context
        if 'session_context' in context:
            context_texts.append(context['session_context'])
        
        if not context_texts:
            # Return zero vector if no context available
            return np.zeros(self.embedder.get_sentence_embedding_dimension())
        
        # Combine context texts and generate embedding
        combined_context = " ".join(context_texts)
        context_embedding = self.embedder.encode(combined_context)
        return self._normalize_vector(context_embedding)
    
    def _detect_ambiguity(self, query_intent: QueryIntent) -> float:
        """
        Detect ambiguity in query intent based on various factors.
        
        Args:
            query_intent: Query intent to analyze
            
        Returns:
            Ambiguity score (0.0 = no ambiguity, 1.0 = highly ambiguous)
        """
        ambiguity_score = 0.0
        
        # Low confidence in intent classification
        if query_intent.confidence < 0.5:
            ambiguity_score += 0.3
        
        # Multiple entities with low confidence
        low_confidence_entities = [e for e in query_intent.entities if e.confidence < 0.6]
        if len(low_confidence_entities) > 1:
            ambiguity_score += 0.2
        
        # Ambiguous entity types (multiple possible interpretations)
        entity_types = [e.entity_type for e in query_intent.entities]
        if EntityType.UNKNOWN in entity_types:
            ambiguity_score += 0.1 * entity_types.count(EntityType.UNKNOWN)
        
        # Vague or incomplete temporal context
        if query_intent.temporal_context and query_intent.temporal_context.confidence < 0.5:
            ambiguity_score += 0.1
        
        # Complex queries without clear structure
        if query_intent.complexity_level == ComplexityLevel.VERY_COMPLEX and query_intent.confidence < 0.6:
            ambiguity_score += 0.2
        
        # Semantic features indicating ambiguity
        if query_intent.semantic_features.get('has_negation', False):
            ambiguity_score += 0.1
        
        return min(1.0, ambiguity_score)
    
    def _apply_context_disambiguation(self, query_intent: QueryIntent, context_vector: np.ndarray, context: Dict[str, Any]) -> QueryIntent:
        """
        Apply context-aware disambiguation to resolve ambiguous queries.
        
        Args:
            query_intent: Ambiguous query intent
            context_vector: Context vector from query history
            context: Full context information
            
        Returns:
            Disambiguated query intent
        """
        # Create a copy to avoid modifying the original
        resolved_intent = QueryIntent(
            intent_type=query_intent.intent_type,
            confidence=query_intent.confidence,
            entities=query_intent.entities.copy(),
            temporal_context=query_intent.temporal_context,
            aggregation_type=query_intent.aggregation_type,
            complexity_level=query_intent.complexity_level,
            original_query=query_intent.original_query,
            query_vector=query_intent.query_vector,
            semantic_features=query_intent.semantic_features.copy()
        )
        
        # Improve intent classification using context
        if resolved_intent.confidence < 0.5:
            resolved_intent = self._improve_intent_with_context(resolved_intent, context_vector, context)
        
        # Resolve temporal ambiguities
        if resolved_intent.temporal_context and resolved_intent.temporal_context.confidence < 0.5:
            resolved_intent.temporal_context = self._resolve_temporal_ambiguity(
                resolved_intent.temporal_context, context
            )
        
        # Disambiguate entities using context
        resolved_intent.entities = self._disambiguate_entities_with_context(
            resolved_intent.entities, context_vector, context
        )
        
        return resolved_intent
    
    def _apply_multi_step_reasoning(self, query_intent: QueryIntent, context: Dict[str, Any]) -> QueryIntent:
        """
        Apply multi-step reasoning for complex queries.
        
        Args:
            query_intent: Complex query intent
            context: Context information
            
        Returns:
            Query intent with improved understanding through multi-step reasoning
        """
        # Break down complex queries into sub-components
        sub_intents = self._decompose_complex_query(query_intent)
        
        # Resolve each sub-component
        resolved_sub_intents = []
        for sub_intent in sub_intents:
            if self._detect_ambiguity(sub_intent) > 0.2:
                sub_context_vector = self._generate_context_vector(context)
                resolved_sub = self._apply_context_disambiguation(sub_intent, sub_context_vector, context)
                resolved_sub_intents.append(resolved_sub)
            else:
                resolved_sub_intents.append(sub_intent)
        
        # Combine resolved sub-intents back into main intent
        combined_intent = self._combine_sub_intents(resolved_sub_intents, query_intent)
        
        return combined_intent
    
    def _improve_intent_with_context(self, query_intent: QueryIntent, context_vector: np.ndarray, context: Dict[str, Any]) -> QueryIntent:
        """
        Improve intent classification using context information.
        
        Args:
            query_intent: Query intent with low confidence
            context_vector: Context vector
            context: Full context information
            
        Returns:
            Query intent with improved classification
        """
        # Combine query vector with context vector
        combined_vector = (query_intent.query_vector + context_vector * 0.3) / 1.3
        combined_vector = self._normalize_vector(combined_vector)
        
        # Re-classify intent with combined vector
        new_intent_type, new_confidence = self._classify_intent_with_vector(combined_vector)
        
        # Use the better classification
        if new_confidence > query_intent.confidence:
            query_intent.intent_type = new_intent_type
            query_intent.confidence = new_confidence
        
        # Check context for intent hints
        if 'recent_intents' in context:
            recent_intents = context['recent_intents']
            if len(recent_intents) > 0:
                # Boost confidence if similar intent was used recently
                most_recent_intent = recent_intents[-1]
                if most_recent_intent == query_intent.intent_type:
                    query_intent.confidence = min(1.0, query_intent.confidence + 0.1)
        
        return query_intent
    
    def _classify_intent_with_vector(self, query_vector: np.ndarray) -> Tuple[IntentType, float]:
        """
        Classify intent using a given vector (used for context-enhanced classification).
        
        Args:
            query_vector: Vector to classify
            
        Returns:
            Tuple of (IntentType, confidence_score)
        """
        best_intent = IntentType.UNKNOWN
        best_score = 0.0
        
        # Calculate similarity with each intent pattern
        for intent_type, pattern_data in self.intent_patterns.items():
            pattern_embedding = pattern_data['embedding']
            similarity = np.dot(query_vector, pattern_embedding)
            
            if similarity > pattern_data['confidence_threshold'] and similarity > best_score:
                best_score = similarity
                best_intent = intent_type
        
        return best_intent, float(best_score)
    
    def _resolve_temporal_ambiguity(self, temporal_context: TemporalContext, context: Dict[str, Any]) -> TemporalContext:
        """
        Resolve temporal ambiguities using context.
        
        Args:
            temporal_context: Ambiguous temporal context
            context: Context information
            
        Returns:
            Resolved temporal context
        """
        # Use current date/time from context if available
        current_time = context.get('current_time', datetime.now())
        
        # Resolve relative time references
        if temporal_context.relative and temporal_context.time_reference:
            time_ref = temporal_context.time_reference.lower()
            
            if 'last' in time_ref:
                if 'month' in time_ref:
                    # Calculate last month dates
                    temporal_context.confidence = min(1.0, temporal_context.confidence + 0.3)
                elif 'week' in time_ref:
                    # Calculate last week dates
                    temporal_context.confidence = min(1.0, temporal_context.confidence + 0.3)
                elif 'year' in time_ref:
                    # Calculate last year dates
                    temporal_context.confidence = min(1.0, temporal_context.confidence + 0.3)
            
            elif 'this' in time_ref:
                if 'month' in time_ref or 'week' in time_ref or 'year' in time_ref:
                    temporal_context.confidence = min(1.0, temporal_context.confidence + 0.3)
        
        return temporal_context
    
    def _disambiguate_entities_with_context(self, entities: List[Entity], context_vector: np.ndarray, context: Dict[str, Any]) -> List[Entity]:
        """
        Disambiguate entities using context information.
        
        Args:
            entities: List of potentially ambiguous entities
            context_vector: Context vector
            context: Full context information
            
        Returns:
            List of disambiguated entities
        """
        disambiguated_entities = []
        
        for entity in entities:
            if entity.confidence < 0.6:  # Low confidence entity needs disambiguation
                # Try to improve entity classification using context
                if entity.context_vector is not None:
                    # Combine entity context with query context
                    combined_context = (entity.context_vector + context_vector * 0.4) / 1.4
                    combined_context = self._normalize_vector(combined_context)
                    
                    # Re-evaluate entity type with combined context
                    improved_entity = self._reclassify_entity_with_context(entity, combined_context, context)
                    disambiguated_entities.append(improved_entity)
                else:
                    disambiguated_entities.append(entity)
            else:
                disambiguated_entities.append(entity)
        
        return disambiguated_entities
    
    def _reclassify_entity_with_context(self, entity: Entity, context_vector: np.ndarray, context: Dict[str, Any]) -> Entity:
        """
        Reclassify entity using context information.
        
        Args:
            entity: Entity to reclassify
            context_vector: Combined context vector
            context: Full context information
            
        Returns:
            Entity with improved classification
        """
        # Check if recent queries provide hints about entity type
        if 'query_history' in context:
            recent_queries = context['query_history'][-3:]  # Last 3 queries
            
            for recent_query in recent_queries:
                if 'entities' in recent_query:
                    for recent_entity in recent_query['entities']:
                        # If similar entity name was used recently, use that type
                        if (recent_entity.get('name', '').lower() == entity.name.lower() and
                            recent_entity.get('confidence', 0) > entity.confidence):
                            entity.entity_type = EntityType(recent_entity.get('type', entity.entity_type.value))
                            entity.confidence = min(1.0, entity.confidence + 0.2)
                            break
        
        # Use domain context to improve classification
        if 'domain_context' in context:
            domain = context['domain_context'].lower()
            
            if 'employee' in domain or 'hr' in domain:
                if entity.entity_type == EntityType.UNKNOWN and len(entity.name.split()) == 2:
                    # Likely a person name in HR context
                    entity.entity_type = EntityType.PERSON
                    entity.confidence = min(1.0, entity.confidence + 0.2)
            
            elif 'project' in domain or 'task' in domain:
                if entity.entity_type == EntityType.UNKNOWN:
                    # Likely a project name in project context
                    entity.entity_type = EntityType.PROJECT
                    entity.confidence = min(1.0, entity.confidence + 0.2)
        
        return entity
    
    def _decompose_complex_query(self, query_intent: QueryIntent) -> List[QueryIntent]:
        """
        Decompose complex queries into simpler sub-components.
        
        Args:
            query_intent: Complex query intent
            
        Returns:
            List of simpler sub-intents
        """
        sub_intents = []
        query = query_intent.original_query.lower()
        
        # Split on conjunctions and complex operators
        conjunctions = ['and', 'or', 'but', 'with', 'having']
        
        # Simple decomposition based on conjunctions
        parts = [query]
        for conjunction in conjunctions:
            new_parts = []
            for part in parts:
                if f' {conjunction} ' in part:
                    split_parts = part.split(f' {conjunction} ')
                    new_parts.extend(split_parts)
                else:
                    new_parts.append(part)
            parts = new_parts
        
        # Create sub-intents for each part
        for part in parts:
            if len(part.strip()) > 3:  # Ignore very short parts
                sub_intent = self.analyze_query(part.strip())
                sub_intents.append(sub_intent)
        
        # If no meaningful decomposition, return original
        if len(sub_intents) <= 1:
            return [query_intent]
        
        return sub_intents
    
    def _combine_sub_intents(self, sub_intents: List[QueryIntent], original_intent: QueryIntent) -> QueryIntent:
        """
        Combine resolved sub-intents back into main intent.
        
        Args:
            sub_intents: List of resolved sub-intents
            original_intent: Original complex intent
            
        Returns:
            Combined intent with improved understanding
        """
        if not sub_intents:
            return original_intent
        
        # Use the highest confidence intent as primary
        primary_intent = max(sub_intents, key=lambda x: x.confidence)
        
        # Combine entities from all sub-intents
        all_entities = []
        for sub_intent in sub_intents:
            all_entities.extend(sub_intent.entities)
        
        # Remove duplicates
        unique_entities = self._deduplicate_entities(all_entities)
        
        # Combine temporal contexts (use the most specific one)
        combined_temporal = None
        for sub_intent in sub_intents:
            if sub_intent.temporal_context:
                if not combined_temporal or sub_intent.temporal_context.confidence > combined_temporal.confidence:
                    combined_temporal = sub_intent.temporal_context
        
        # Create combined intent
        combined_intent = QueryIntent(
            intent_type=primary_intent.intent_type,
            confidence=min(1.0, primary_intent.confidence + 0.1),  # Slight boost for successful decomposition
            entities=unique_entities,
            temporal_context=combined_temporal or original_intent.temporal_context,
            aggregation_type=primary_intent.aggregation_type or original_intent.aggregation_type,
            complexity_level=original_intent.complexity_level,
            original_query=original_intent.original_query,
            query_vector=original_intent.query_vector,
            semantic_features=original_intent.semantic_features
        )
        
        return combined_intent
    
    def create_disambiguation_suggestions(self, query_intent: QueryIntent) -> List[str]:
        """
        Create suggestions to help users disambiguate their queries.
        
        Args:
            query_intent: Ambiguous query intent
            
        Returns:
            List of disambiguation suggestions
        """
        suggestions = []
        ambiguity_score = self._detect_ambiguity(query_intent)
        
        if ambiguity_score > 0.3:
            # Suggest more specific queries
            if query_intent.confidence < 0.5:
                suggestions.append(
                    f"Your query '{query_intent.original_query}' could be interpreted in multiple ways. "
                    "Could you be more specific about what you're looking for?"
                )
            
            # Suggest entity clarifications
            low_conf_entities = [e for e in query_intent.entities if e.confidence < 0.6]
            if low_conf_entities:
                entity_names = [e.name for e in low_conf_entities]
                suggestions.append(
                    f"I'm not sure about these terms: {', '.join(entity_names)}. "
                    "Could you clarify what they refer to?"
                )
            
            # Suggest temporal clarifications
            if query_intent.temporal_context and query_intent.temporal_context.confidence < 0.5:
                suggestions.append(
                    f"The time reference '{query_intent.temporal_context.time_reference}' is ambiguous. "
                    "Could you specify exact dates or a clearer time period?"
                )
            
            # Suggest breaking down complex queries
            if query_intent.complexity_level == ComplexityLevel.VERY_COMPLEX:
                suggestions.append(
                    "Your query is quite complex. Consider breaking it down into simpler questions "
                    "or asking about one thing at a time."
                )
        
        return suggestions[:3]  # Return top 3 suggestions