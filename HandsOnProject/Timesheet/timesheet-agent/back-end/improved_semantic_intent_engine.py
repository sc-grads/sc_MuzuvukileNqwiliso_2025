#!/usr/bin/env python3
"""
Improved Semantic Intent Engine with better entity extraction and confidence scoring
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import re
import logging
from datetime import datetime

# Import the original classes we need
from semantic_intent_engine import (
    IntentType, EntityType, ComplexityLevel, Entity, QueryIntent,
    TemporalContext, AggregationType, SchemaMapping
)

# We'll use the existing EntityType and add business logic for classification
# The existing EntityType already has STATUS, so we'll work with what we have

logger = logging.getLogger(__name__)


class ImprovedSemanticIntentEngine:
    """
    Improved semantic intent engine with better entity extraction and confidence scoring
    """
    
    def __init__(self, vector_store, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize the improved semantic intent engine"""
        self.vector_store = vector_store
        self.embedding_model_name = embedding_model
        
        # Initialize embedder
        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer(embedding_model)
        
        # Initialize improved patterns
        self._initialize_improved_patterns()
        
        # Initialize entity filters
        self._initialize_entity_filters()
        
        logger.info(f"ImprovedSemanticIntentEngine initialized with model: {embedding_model}")
    
    def _initialize_improved_patterns(self):
        """Initialize improved intent patterns with better confidence scoring"""
        
        # Define intent patterns with more nuanced confidence thresholds
        intent_examples = {
            IntentType.GREETING: {
                'examples': ["hello", "hi", "hey", "good morning", "good afternoon", "how are you"],
                'confidence_threshold': 0.3,
                'boost_patterns': [r'\b(hi|hello|hey)\b', r'\bgood\s+(morning|afternoon|evening)\b']
            },
            IntentType.SELECT: {
                'examples': [
                    "show me", "list all", "get", "find", "display", "what are",
                    "who are", "which", "retrieve", "fetch", "show", "list"
                ],
                'confidence_threshold': 0.25,
                'boost_patterns': [
                    r'\b(show|list|display|get|find)\b',
                    r'\bwhat\s+(are|is)\b',
                    r'\bwho\s+(is|are)\b'
                ]
            },
            IntentType.COUNT: {
                'examples': [
                    "how many", "count", "number of", "total number", "quantity",
                    "how much", "amount of"
                ],
                'confidence_threshold': 0.3,
                'boost_patterns': [
                    r'\bhow\s+many\b',
                    r'\bcount\b',
                    r'\bnumber\s+of\b'
                ]
            },
            IntentType.SUM: {
                'examples': [
                    "total", "sum", "add up", "total amount", "sum of",
                    "altogether", "combined"
                ],
                'confidence_threshold': 0.3,
                'boost_patterns': [
                    r'\btotal\b',
                    r'\bsum\b',
                    r'\badd\s+up\b'
                ]
            },
            IntentType.AVERAGE: {
                'examples': [
                    "average", "mean", "avg", "typical", "on average"
                ],
                'confidence_threshold': 0.35,
                'boost_patterns': [r'\b(average|mean|avg)\b']
            },
            IntentType.MAX: {
                'examples': [
                    "maximum", "max", "highest", "largest", "most", "top"
                ],
                'confidence_threshold': 0.3,
                'boost_patterns': [r'\b(maximum|max|highest|most|top)\b']
            },
            IntentType.MIN: {
                'examples': [
                    "minimum", "min", "lowest", "smallest", "least", "bottom"
                ],
                'confidence_threshold': 0.3,
                'boost_patterns': [r'\b(minimum|min|lowest|least|bottom)\b']
            }
        }
        
        # Create embeddings for intent patterns
        self.intent_patterns = {}
        for intent_type, data in intent_examples.items():
            combined_text = " ".join(data['examples'])
            embedding = self.embedder.encode(combined_text)
            
            self.intent_patterns[intent_type] = {
                'embedding': self._normalize_vector(embedding),
                'confidence_threshold': data['confidence_threshold'],
                'boost_patterns': data.get('boost_patterns', []),
                'examples': data['examples']
            }
    
    def _initialize_entity_filters(self):
        """Initialize filters to remove noise from entity extraction"""
        
        # Command phrases that should NOT be entities
        self.command_phrases = {
            'show me', 'list all', 'find all', 'get all', 'display all',
            'show', 'list', 'find', 'get', 'display', 'retrieve',
            'how many', 'what are', 'who is', 'who are', 'which',
            'tell me', 'give me', 'let me see'
        }
        
        # Stop words that should be filtered out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'that', 'this', 'these', 'those', 'there', 'here'
        }
        
        # Phrases that indicate relationships but aren't entities themselves
        self.relationship_phrases = {
            'for the', 'with the', 'in the', 'on the', 'at the',
            'from the', 'to the', 'by the', 'of the', 'are considered',
            'that are', 'which are', 'entries from', 'types of'
        }
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector for cosine similarity"""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def analyze_query(self, nl_query: str) -> QueryIntent:
        """
        Analyze natural language query with improved intent and entity extraction
        """
        logger.info(f"Analyzing query: {nl_query}")
        
        # Fast-path for greetings
        query_lower = nl_query.lower().strip()
        if self._is_greeting(query_lower):
            return self._create_greeting_intent(nl_query)
        
        # Generate query vector
        query_vector = self._normalize_vector(self.embedder.encode(nl_query))
        
        # Improved intent classification
        intent_type, intent_confidence = self._classify_intent_improved(nl_query, query_vector)
        
        # Improved entity extraction
        entities = self._extract_entities_improved(nl_query, query_vector)
        
        # Extract other components
        temporal_context = self._extract_temporal_context(nl_query)
        aggregation_type = self._determine_aggregation_type(nl_query, intent_type)
        complexity_level = self._assess_complexity(nl_query, intent_type, entities)
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
    
    def _classify_intent_improved(self, query: str, query_vector: np.ndarray) -> Tuple[IntentType, float]:
        """
        Improved intent classification with dynamic confidence scoring
        """
        query_lower = query.lower().strip()
        best_intent = IntentType.UNKNOWN
        best_score = 0.0
        
        # Vector-based similarity scoring
        vector_scores = {}
        for intent_type, pattern_data in self.intent_patterns.items():
            pattern_embedding = pattern_data['embedding']
            similarity = np.dot(query_vector, pattern_embedding)
            
            if similarity > pattern_data['confidence_threshold']:
                vector_scores[intent_type] = similarity
        
        # Rule-based pattern matching with dynamic confidence
        rule_scores = {}
        
        # COUNT patterns
        count_patterns = [
            (r'\bhow\s+many\b', 0.9),
            (r'\bcount\b', 0.8),
            (r'\bnumber\s+of\b', 0.85),
            (r'\btotal\s+number\b', 0.9)
        ]
        for pattern, confidence in count_patterns:
            if re.search(pattern, query_lower):
                rule_scores[IntentType.COUNT] = max(rule_scores.get(IntentType.COUNT, 0), confidence)
        
        # SELECT patterns
        select_patterns = [
            (r'\b(show|list|display)\s+(me\s+)?(all\s+)?\w+', 0.85),
            (r'\bwhat\s+(are|is)\s+the\b', 0.8),
            (r'\bwho\s+(is|are)\b', 0.8),
            (r'\bfind\s+(all\s+)?\w+', 0.8),
            (r'\bget\s+(all\s+)?\w+', 0.75)
        ]
        for pattern, confidence in select_patterns:
            if re.search(pattern, query_lower):
                # Avoid SELECT if it's clearly a COUNT query
                if not any(word in query_lower for word in ['how many', 'count', 'number of']):
                    rule_scores[IntentType.SELECT] = max(rule_scores.get(IntentType.SELECT, 0), confidence)
        
        # SUM patterns - improved to catch more cases
        sum_patterns = [
            (r'\btotal\s+(billable\s+)?hours\b', 0.95),  # "total billable hours"
            (r'\btotal\s+number\s+of\s+hours\b', 0.9),   # "total number of hours"
            (r'\btotal\s+(hours|amount|cost)\b', 0.9),
            (r'\bsum\s+of\b', 0.9),
            (r'\badd\s+up\b', 0.8),
            (r'\bwhat\s+(are|is)\s+the\s+total\b', 0.85)  # "what are the total..."
        ]
        for pattern, confidence in sum_patterns:
            if re.search(pattern, query_lower):
                rule_scores[IntentType.SUM] = max(rule_scores.get(IntentType.SUM, 0), confidence)
        
        # AVERAGE patterns
        avg_patterns = [
            (r'\baverage\b', 0.9),
            (r'\bmean\b', 0.85),
            (r'\bavg\b', 0.8)
        ]
        for pattern, confidence in avg_patterns:
            if re.search(pattern, query_lower):
                rule_scores[IntentType.AVERAGE] = max(rule_scores.get(IntentType.AVERAGE, 0), confidence)
        
        # MAX/MIN patterns
        if any(word in query_lower for word in ['highest', 'maximum', 'max', 'most', 'top']):
            rule_scores[IntentType.MAX] = 0.85
        if any(word in query_lower for word in ['lowest', 'minimum', 'min', 'least', 'bottom']):
            rule_scores[IntentType.MIN] = 0.85
        
        # Combine vector and rule scores
        combined_scores = {}
        
        # Add vector scores
        for intent, score in vector_scores.items():
            combined_scores[intent] = score * 0.4  # Weight vector scores at 40%
        
        # Add rule scores
        for intent, score in rule_scores.items():
            combined_scores[intent] = combined_scores.get(intent, 0) + score * 0.6  # Weight rule scores at 60%
        
        # Find best intent
        if combined_scores:
            best_intent = max(combined_scores.items(), key=lambda x: x[1])
            return best_intent[0], min(best_intent[1], 0.98)  # Cap at 0.98
        
        # Fallback for unknown intents - give them a reasonable confidence
        return IntentType.UNKNOWN, 0.2
    
    def _extract_entities_improved(self, query: str, query_vector: np.ndarray) -> List[Entity]:
        """
        Improved entity extraction with better filtering and classification
        """
        entities = []
        query_lower = query.lower()
        
        # Extract different types of entities
        entities.extend(self._extract_named_entities_improved(query))
        entities.extend(self._extract_numeric_entities_improved(query))
        entities.extend(self._extract_table_column_entities(query, query_vector))
        entities.extend(self._extract_business_entities(query, query_vector))
        entities.extend(self._extract_compound_phrases(query))  # New method for missing entities
        
        # Filter out noise
        filtered_entities = self._filter_noise_entities(entities, query_lower)
        
        # Improve entity types
        improved_entities = self._improve_entity_types(filtered_entities, query_lower)
        
        # Remove duplicates and sort by confidence
        unique_entities = self._deduplicate_entities(improved_entities)
        unique_entities.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_entities[:10]  # Limit to top 10 entities
    
    def _extract_named_entities_improved(self, query: str) -> List[Entity]:
        """Extract named entities with better classification"""
        entities = []
        
        # Use spaCy for named entity recognition
        try:
            import spacy
            nlp = spacy.load("en_core_web_md")
            doc = nlp(query)
            
            for ent in doc.ents:
                # Map spaCy entity types to our entity types
                entity_type = self._map_spacy_entity_type(ent.label_)
                
                if entity_type != EntityType.UNKNOWN:
                    entities.append(Entity(
                        name=ent.text,
                        entity_type=entity_type,
                        confidence=0.8,  # High confidence for spaCy entities
                        original_text=ent.text,
                        position=(ent.start_char, ent.end_char)
                    ))
        except Exception as e:
            logger.warning(f"spaCy entity extraction failed: {e}")
        
        return entities
    
    def _extract_numeric_entities_improved(self, query: str) -> List[Entity]:
        """Extract numeric entities with better context understanding"""
        entities = []
        
        # Extract numbers with context
        number_patterns = [
            (r'\b(\d+)\s*(?:hours?|hrs?)\b', EntityType.NUMBER, 'hours'),
            (r'\$(\d+(?:\.\d+)?)\b', EntityType.NUMBER, 'currency'),
            (r'\b(\d+(?:\.\d+)?)%\b', EntityType.NUMBER, 'percentage'),
            (r'\bID\s+(\d+)\b', EntityType.NUMBER, 'id'),
            (r'\b(\d+)\b', EntityType.NUMBER, 'number')
        ]
        
        for pattern, entity_type, context in number_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities.append(Entity(
                    name=match.group(1),
                    entity_type=entity_type,
                    confidence=0.9 if context in ['hours', 'currency', 'id'] else 0.7,
                    original_text=match.group(0),
                    position=match.span(),
                    metadata={'context': context}
                ))
        
        return entities
    
    def _extract_table_column_entities(self, query: str, query_vector: np.ndarray) -> List[Entity]:
        """Extract entities that map to database tables and columns"""
        entities = []
        query_lower = query.lower()
        
        # Common database entity patterns using existing EntityType
        db_patterns = {
            'employee': (EntityType.PERSON, ['employee', 'employees', 'staff', 'worker', 'workers']),
            'client': (EntityType.CLIENT, ['client', 'clients', 'customer', 'customers']),
            'project': (EntityType.PROJECT, ['project', 'projects']),
            'timesheet': (EntityType.TIMESHEET_CONCEPT, ['timesheet', 'timesheets', 'time sheet']),
            'activity': (EntityType.TIMESHEET_CONCEPT, ['activity', 'activities', 'task', 'tasks', 'meeting', 'standup']),
            'leave': (EntityType.TIMESHEET_CONCEPT, ['leave', 'vacation', 'holiday', 'time off']),
            'leave_type': (EntityType.STATUS, ['annual leave', 'sick leave', 'personal leave']),  # Use STATUS for leave types
            'status': (EntityType.STATUS, ['billable', 'non-billable', 'status']),
            'time_field': (EntityType.TIMESHEET_CONCEPT, ['start time', 'end time', 'duration'])  # Use TIMESHEET_CONCEPT for time fields
        }
        
        for concept, (entity_type, keywords) in db_patterns.items():
            for keyword in keywords:
                if keyword in query_lower:
                    # Find the position of the keyword
                    start_pos = query_lower.find(keyword)
                    end_pos = start_pos + len(keyword)
                    
                    entities.append(Entity(
                        name=keyword,
                        entity_type=entity_type,
                        confidence=0.8,
                        original_text=keyword,
                        position=(start_pos, end_pos),
                        metadata={'concept': concept}
                    ))
        
        return entities
    
    def _extract_business_entities(self, query: str, query_vector: np.ndarray) -> List[Entity]:
        """Extract business-specific entities with comprehensive word coverage"""
        entities = []
        
        # Extract quoted strings with better type classification
        quoted_pattern = r"['\"]([^'\"]+)['\"]"
        matches = re.finditer(quoted_pattern, query)
        for match in matches:
            quoted_text = match.group(1).lower()
            
            # Classify quoted strings based on content - EXPANDED
            # Project-related terms
            if any(word in quoted_text for word in [
                'program', 'project', 'initiative', 'campaign', 'development', 'implementation',
                'system', 'application', 'software', 'platform', 'solution', 'framework',
                'module', 'component', 'feature', 'enhancement', 'upgrade', 'migration',
                'integration', 'deployment', 'maintenance', 'support', 'training',
                'graduate', 'internship', 'research', 'study', 'analysis', 'assessment'
            ]):
                entity_type = EntityType.PROJECT
            
            # Leave/Status-related terms
            elif any(word in quoted_text for word in [
                'leave', 'annual', 'sick', 'personal', 'vacation', 'holiday', 'time off',
                'maternity', 'paternity', 'bereavement', 'compassionate', 'study leave',
                'sabbatical', 'unpaid', 'paid', 'emergency', 'medical', 'family',
                'mental health', 'wellness', 'recovery', 'quarantine', 'isolation'
            ]):
                entity_type = EntityType.STATUS
            
            # Activity/Meeting-related terms
            elif any(word in quoted_text for word in [
                'meeting', 'standup', 'review', 'call', 'conference', 'workshop',
                'training', 'session', 'presentation', 'demo', 'demonstration',
                'planning', 'retrospective', 'sprint', 'scrum', 'daily', 'weekly',
                'monthly', 'quarterly', 'annual', 'one-on-one', '1:1', 'team meeting',
                'client meeting', 'stakeholder', 'interview', 'discussion', 'brainstorm',
                'sync', 'catch-up', 'check-in', 'follow-up', 'kickoff', 'wrap-up',
                'ceremony', 'ritual', 'huddle', 'briefing', 'debriefing', 'consultation'
            ]):
                entity_type = EntityType.TIMESHEET_CONCEPT
            
            # Client/Company-related terms
            elif any(word in quoted_text for word in [
                'company','client', 'corporation', 'enterprise', 'organization', 'firm', 'agency',
                'business', 'startup', 'venture', 'partnership', 'consortium', 'group',
                'holdings', 'limited', 'ltd', 'inc', 'incorporated', 'llc', 'plc',
                'co', 'corp', 'pty', 'gmbh', 'sa', 'bv', 'ab', 'as', 'oy'
            ]):
                entity_type = EntityType.CLIENT
            
            else:
                entity_type = EntityType.CLIENT  # Default for unknown quoted strings
            
            entities.append(Entity(
                name=match.group(1),
                entity_type=entity_type,
                confidence=0.9,
                original_text=match.group(0),
                position=match.span(),
                metadata={'source': 'quoted_string'}
            ))
        
        # Extract proper nouns that might be names - EXPANDED
        proper_noun_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.finditer(proper_noun_pattern, query)
        for match in matches:
            name = match.group(0)
            
            # Skip common words that start with capital letters - EXPANDED
            skip_words = {
                'show', 'list', 'find', 'display', 'what', 'who', 'how', 'when', 'where',
                'why', 'which', 'get', 'give', 'tell', 'let', 'make', 'take', 'come',
                'go', 'see', 'know', 'think', 'look', 'use', 'work', 'call', 'try',
                'ask', 'need', 'feel', 'become', 'leave', 'put', 'mean', 'keep',
                'start', 'seem', 'help', 'talk', 'turn', 'move', 'play', 'run',
                'begin', 'believe', 'bring', 'happen', 'write', 'provide', 'sit',
                'stand', 'lose', 'pay', 'meet', 'include', 'continue', 'set',
                'learn', 'change', 'lead', 'understand', 'watch', 'follow', 'stop',
                'create', 'speak', 'read', 'allow', 'add', 'spend', 'grow', 'open',
                'walk', 'win', 'offer', 'remember', 'love', 'consider', 'appear',
                'buy', 'wait', 'serve', 'die', 'send', 'expect', 'build', 'stay',
                'fall', 'cut', 'reach', 'kill', 'remain', 'suggest', 'raise', 'pass',
                'sell', 'require', 'report', 'decide', 'pull'
            }
            
            if name.lower() not in skip_words:
                # Try to classify proper nouns better
                confidence = 0.6
                entity_type = EntityType.PERSON
                
                # If it looks like a company name (multiple words with certain patterns)
                if len(name.split()) > 1:
                    name_lower = name.lower()
                    if any(indicator in name_lower for indicator in [
                        'systems', 'solutions', 'technologies', 'consulting', 'services',
                        'group', 'company', 'corporation', 'enterprises', 'international',
                        'global', 'worldwide', 'associates', 'partners', 'holdings',
                        'industries', 'manufacturing', 'development', 'research',
                        'institute', 'foundation', 'center', 'centre'
                    ]):
                        entity_type = EntityType.CLIENT
                        confidence = 0.8
                
                entities.append(Entity(
                    name=name,
                    entity_type=entity_type,
                    confidence=confidence,
                    original_text=name,
                    position=match.span(),
                    metadata={'source': 'proper_noun'}
                ))
        
        return entities
    
    def _extract_compound_phrases(self, query: str) -> List[Entity]:
        """Extract compound phrases that might be missed by other methods"""
        entities = []
        query_lower = query.lower()
        
        # Define compound phrase patterns using existing EntityType - GREATLY EXPANDED
        compound_patterns = [
            # Status-related phrases
            (r'billable\s+status', EntityType.STATUS, 0.85),
            (r'non-billable', EntityType.STATUS, 0.8),
            (r'billing\s+status', EntityType.STATUS, 0.85),
            (r'approval\s+status', EntityType.STATUS, 0.8),
            (r'work\s+status', EntityType.STATUS, 0.75),
            (r'project\s+status', EntityType.STATUS, 0.8),
            (r'task\s+status', EntityType.STATUS, 0.8),
            
            # Time-related phrases  
            (r'start\s+time', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'end\s+time', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'break\s+time', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'lunch\s+time', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'total\s+time', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'elapsed\s+time', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'work\s+time', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'overtime\s+hours', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'regular\s+hours', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'billable\s+hours', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'non-billable\s+hours', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'logged\s+hours', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'tracked\s+hours', EntityType.TIMESHEET_CONCEPT, 0.85),
            
            # Activity phrases - EXPANDED
            (r'standup\s+meeting', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'daily\s+standup', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'team\s+meeting', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'client\s+meeting', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'project\s+meeting', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'status\s+meeting', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'planning\s+meeting', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'review\s+meeting', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'one-on-one', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'1:1\s+meeting', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'video\s+call', EntityType.TIMESHEET_CONCEPT, 0.8),
            (r'phone\s+call', EntityType.TIMESHEET_CONCEPT, 0.8),
            (r'conference\s+call', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'code\s+review', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'pair\s+programming', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'sprint\s+planning', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'sprint\s+review', EntityType.TIMESHEET_CONCEPT, 0.9),
            (r'retrospective\s+meeting', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'training\s+session', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'workshop\s+session', EntityType.TIMESHEET_CONCEPT, 0.85),
            
            # Leave type phrases - EXPANDED
            (r'annual\s+leave', EntityType.STATUS, 0.9),
            (r'sick\s+leave', EntityType.STATUS, 0.9),
            (r'personal\s+leave', EntityType.STATUS, 0.85),
            (r'vacation\s+leave', EntityType.STATUS, 0.85),
            (r'holiday\s+leave', EntityType.STATUS, 0.85),
            (r'maternity\s+leave', EntityType.STATUS, 0.9),
            (r'paternity\s+leave', EntityType.STATUS, 0.9),
            (r'parental\s+leave', EntityType.STATUS, 0.9),
            (r'family\s+leave', EntityType.STATUS, 0.85),
            (r'bereavement\s+leave', EntityType.STATUS, 0.9),
            (r'compassionate\s+leave', EntityType.STATUS, 0.85),
            (r'emergency\s+leave', EntityType.STATUS, 0.85),
            (r'medical\s+leave', EntityType.STATUS, 0.9),
            (r'study\s+leave', EntityType.STATUS, 0.85),
            (r'sabbatical\s+leave', EntityType.STATUS, 0.85),
            (r'unpaid\s+leave', EntityType.STATUS, 0.85),
            (r'paid\s+leave', EntityType.STATUS, 0.8),
            (r'time\s+off', EntityType.STATUS, 0.8),
            (r'pto', EntityType.STATUS, 0.85),
            (r'paid\s+time\s+off', EntityType.STATUS, 0.9),
            
            # Project phrases - EXPANDED
            (r'graduate\s+program', EntityType.PROJECT, 0.9),
            (r'training\s+program', EntityType.PROJECT, 0.85),
            (r'development\s+project', EntityType.PROJECT, 0.9),
            (r'software\s+project', EntityType.PROJECT, 0.9),
            (r'system\s+project', EntityType.PROJECT, 0.85),
            (r'implementation\s+project', EntityType.PROJECT, 0.9),
            (r'migration\s+project', EntityType.PROJECT, 0.9),
            (r'upgrade\s+project', EntityType.PROJECT, 0.85),
            (r'maintenance\s+project', EntityType.PROJECT, 0.85),
            (r'research\s+project', EntityType.PROJECT, 0.85),
            (r'pilot\s+project', EntityType.PROJECT, 0.85),
            (r'proof\s+of\s+concept', EntityType.PROJECT, 0.85),
            (r'poc\s+project', EntityType.PROJECT, 0.8),
            (r'client\s+project', EntityType.PROJECT, 0.85),
            (r'internal\s+project', EntityType.PROJECT, 0.8),
            
            # Time period phrases - EXPANDED
            (r'first\s+week\s+of\s+\w+', EntityType.TIME_PERIOD, 0.8),
            (r'last\s+week\s+of\s+\w+', EntityType.TIME_PERIOD, 0.8),
            (r'second\s+week\s+of\s+\w+', EntityType.TIME_PERIOD, 0.8),
            (r'third\s+week\s+of\s+\w+', EntityType.TIME_PERIOD, 0.8),
            (r'fourth\s+week\s+of\s+\w+', EntityType.TIME_PERIOD, 0.8),
            (r'any\s+single\s+week', EntityType.TIME_PERIOD, 0.75),
            (r'current\s+week', EntityType.TIME_PERIOD, 0.8),
            (r'this\s+week', EntityType.TIME_PERIOD, 0.8),
            (r'last\s+week', EntityType.TIME_PERIOD, 0.8),
            (r'next\s+week', EntityType.TIME_PERIOD, 0.8),
            (r'current\s+month', EntityType.TIME_PERIOD, 0.8),
            (r'this\s+month', EntityType.TIME_PERIOD, 0.8),
            (r'last\s+month', EntityType.TIME_PERIOD, 0.8),
            (r'next\s+month', EntityType.TIME_PERIOD, 0.8),
            (r'current\s+year', EntityType.TIME_PERIOD, 0.8),
            (r'this\s+year', EntityType.TIME_PERIOD, 0.8),
            (r'last\s+year', EntityType.TIME_PERIOD, 0.8),
            (r'next\s+year', EntityType.TIME_PERIOD, 0.8),
            (r'current\s+quarter', EntityType.TIME_PERIOD, 0.8),
            (r'this\s+quarter', EntityType.TIME_PERIOD, 0.8),
            (r'last\s+quarter', EntityType.TIME_PERIOD, 0.8),
            (r'next\s+quarter', EntityType.TIME_PERIOD, 0.8),
            
            # Work measurement phrases
            (r'\d+\s+hours', EntityType.TIMESHEET_CONCEPT, 0.8),
            (r'\d+\s+minutes', EntityType.TIMESHEET_CONCEPT, 0.75),
            (r'\d+\s+days', EntityType.TIME_PERIOD, 0.8),
            (r'\d+\s+weeks', EntityType.TIME_PERIOD, 0.8),
            (r'\d+\s+months', EntityType.TIME_PERIOD, 0.8),
            (r'more\s+than\s+\d+\s+hours', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'less\s+than\s+\d+\s+hours', EntityType.TIMESHEET_CONCEPT, 0.85),
            (r'at\s+least\s+\d+\s+hours', EntityType.TIMESHEET_CONCEPT, 0.8),
            (r'exactly\s+\d+\s+hours', EntityType.TIMESHEET_CONCEPT, 0.8),
            
            # Department/Team phrases
            (r'development\s+team', EntityType.PERSON, 0.8),
            (r'project\s+team', EntityType.PERSON, 0.8),
            (r'support\s+team', EntityType.PERSON, 0.8),
            (r'qa\s+team', EntityType.PERSON, 0.8),
            (r'testing\s+team', EntityType.PERSON, 0.8),
            (r'design\s+team', EntityType.PERSON, 0.8),
            (r'marketing\s+team', EntityType.PERSON, 0.8),
            (r'sales\s+team', EntityType.PERSON, 0.8),
            (r'hr\s+team', EntityType.PERSON, 0.8),
            (r'finance\s+team', EntityType.PERSON, 0.8),
            (r'it\s+team', EntityType.PERSON, 0.8),
            (r'operations\s+team', EntityType.PERSON, 0.8)
        ]
        
        for pattern, entity_type, confidence in compound_patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                entities.append(Entity(
                    name=match.group(0),
                    entity_type=entity_type,
                    confidence=confidence,
                    original_text=match.group(0),
                    position=match.span(),
                    metadata={'source': 'compound_phrase'}
                ))
        
        return entities
    
    def _filter_noise_entities(self, entities: List[Entity], query_lower: str) -> List[Entity]:
        """Filter out noise entities"""
        filtered = []
        
        for entity in entities:
            entity_lower = entity.name.lower()
            
            # Skip command phrases
            if entity_lower in self.command_phrases:
                continue
            
            # Skip stop words
            if entity_lower in self.stop_words:
                continue
            
            # Skip relationship phrases
            if entity_lower in self.relationship_phrases:
                continue
            
            # Skip very short entities (less than 2 characters) unless they're numbers
            if len(entity.name) < 2 and entity.entity_type != EntityType.NUMBER:
                continue
            
            # Skip entities that are just punctuation or whitespace
            if not re.search(r'[a-zA-Z0-9]', entity.name):
                continue
            
            filtered.append(entity)
        
        return filtered
    
    def _improve_entity_types(self, entities: List[Entity], query_lower: str) -> List[Entity]:
        """Improve entity type classification with comprehensive business domain understanding"""
        improved = []
        
        for entity in entities:
            entity_lower = entity.name.lower()
            
            # Improve entity type based on context
            new_type = entity.entity_type
            
            # Numbers - EXPANDED patterns
            if re.match(r'^\d+(\.\d+)?$', entity.name):
                new_type = EntityType.NUMBER
            
            # Dates - EXPANDED with more date formats and terms
            elif any(word in entity_lower for word in [
                # Months
                'january', 'february', 'march', 'april', 'may', 'june',
                'july', 'august', 'september', 'october', 'november', 'december',
                'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                # Days of week
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
                # Time periods
                'today', 'yesterday', 'tomorrow', 'week', 'month', 'year', 'quarter',
                'weekend', 'weekday', 'morning', 'afternoon', 'evening', 'night'
            ]):
                new_type = EntityType.DATE
            
            # Person/Employee terms - GREATLY EXPANDED
            elif any(word in entity_lower for word in [
                # Job roles and titles
                'employee', 'staff', 'worker', 'team member', 'colleague', 'associate',
                'developer', 'programmer', 'engineer', 'analyst', 'consultant', 'specialist',
                'manager', 'supervisor', 'lead', 'senior', 'junior', 'intern', 'trainee',
                'director', 'executive', 'officer', 'administrator', 'coordinator', 'assistant',
                'secretary', 'clerk', 'representative', 'agent', 'advisor', 'counselor',
                'designer', 'architect', 'planner', 'researcher', 'scientist', 'technician',
                'operator', 'mechanic', 'maintenance', 'support', 'help desk', 'customer service',
                'sales', 'marketing', 'finance', 'accounting', 'hr', 'human resources',
                'legal', 'compliance', 'audit', 'quality', 'testing', 'qa', 'qc',
                'project manager', 'product manager', 'scrum master', 'team lead',
                'tech lead', 'solution architect', 'business analyst', 'data analyst',
                'system admin', 'network admin', 'database admin', 'devops', 'sre',
                # Departments and roles
                'it', 'information technology', 'engineering', 'development', 'operations',
                'production', 'manufacturing', 'logistics', 'procurement', 'purchasing',
                'facilities', 'security', 'safety', 'training', 'learning', 'education'
            ]):
                new_type = EntityType.PERSON
            
            # Client/Customer terms - EXPANDED
            elif any(word in entity_lower for word in [
                'client', 'customer', 'patron', 'buyer', 'purchaser', 'consumer',
                'user', 'end user', 'stakeholder', 'partner', 'vendor', 'supplier',
                'contractor', 'subcontractor', 'freelancer', 'consultant', 'agency',
                'firm', 'company', 'corporation', 'enterprise', 'organization', 'business',
                'startup', 'venture', 'nonprofit', 'ngo', 'government', 'public sector',
                'private sector', 'institution', 'university', 'college', 'school',
                'hospital', 'clinic', 'practice', 'office', 'store', 'shop', 'retail'
            ]) and 'program' not in entity_lower:
                new_type = EntityType.CLIENT
            
            # Project identification - GREATLY EXPANDED
            elif any(word in entity_lower for word in [
                # Project types
                'program', 'project', 'initiative', 'campaign', 'effort', 'endeavor',
                'venture', 'undertaking', 'assignment', 'task', 'job', 'work', 'engagement',
                # Development projects
                'development', 'implementation', 'deployment', 'rollout', 'launch',
                'migration', 'upgrade', 'enhancement', 'improvement', 'optimization',
                'integration', 'automation', 'digitization', 'transformation',
                # System/Software projects
                'system', 'application', 'app', 'software', 'platform', 'solution',
                'framework', 'library', 'module', 'component', 'service', 'api',
                'website', 'portal', 'dashboard', 'interface', 'ui', 'ux',
                # Research/Analysis projects
                'research', 'study', 'analysis', 'assessment', 'evaluation', 'review',
                'audit', 'investigation', 'survey', 'report', 'documentation',
                # Training/Education projects
                'training', 'education', 'learning', 'course', 'workshop', 'seminar',
                'certification', 'onboarding', 'orientation', 'mentoring', 'coaching',
                # Maintenance/Support projects
                'maintenance', 'support', 'helpdesk', 'troubleshooting', 'bug fixing',
                'patch', 'update', 'monitoring', 'backup', 'recovery', 'disaster recovery'
            ]) or 'graduate program' in entity_lower:
                new_type = EntityType.PROJECT
            
            # Leave/Status types - GREATLY EXPANDED
            elif any(phrase in entity_lower for phrase in [
                # Leave types
                'annual leave', 'sick leave', 'personal leave', 'vacation', 'holiday',
                'time off', 'pto', 'paid time off', 'unpaid leave', 'leave without pay',
                'maternity leave', 'paternity leave', 'parental leave', 'family leave',
                'bereavement leave', 'compassionate leave', 'emergency leave',
                'medical leave', 'disability leave', 'study leave', 'sabbatical',
                'mental health leave', 'wellness leave', 'recovery leave',
                'quarantine', 'isolation', 'work from home', 'remote work',
                # Status types
                'billable', 'non-billable', 'chargeable', 'non-chargeable',
                'productive', 'non-productive', 'overhead', 'administrative',
                'internal', 'external', 'client work', 'internal work',
                'approved', 'pending', 'rejected', 'submitted', 'draft',
                'active', 'inactive', 'completed', 'in progress', 'on hold',
                'cancelled', 'postponed', 'scheduled', 'unscheduled'
            ]):
                new_type = EntityType.STATUS
            
            # Activities/Tasks - GREATLY EXPANDED
            elif any(word in entity_lower for word in [
                # Meeting types
                'meeting', 'standup', 'review', 'call', 'conference', 'video call',
                'phone call', 'zoom', 'teams', 'skype', 'webex', 'hangouts',
                'workshop', 'training', 'session', 'presentation', 'demo', 'demonstration',
                'planning', 'retrospective', 'sprint', 'scrum', 'daily', 'weekly',
                'monthly', 'quarterly', 'annual', 'one-on-one', '1:1', 'team meeting',
                'client meeting', 'stakeholder meeting', 'board meeting', 'all hands',
                'town hall', 'kick-off', 'kickoff', 'wrap-up', 'follow-up', 'check-in',
                'sync', 'catch-up', 'huddle', 'briefing', 'debriefing', 'consultation',
                # Development activities
                'coding', 'programming', 'development', 'debugging', 'testing',
                'code review', 'pair programming', 'refactoring', 'optimization',
                'documentation', 'commenting', 'deployment', 'release', 'build',
                'integration', 'configuration', 'setup', 'installation', 'maintenance',
                # Analysis activities
                'analysis', 'research', 'investigation', 'troubleshooting', 'diagnosis',
                'planning', 'design', 'architecture', 'modeling', 'prototyping',
                'requirements', 'specification', 'estimation', 'assessment', 'evaluation',
                # Administrative activities
                'administration', 'paperwork', 'reporting', 'filing', 'organizing',
                'scheduling', 'coordination', 'communication', 'email', 'correspondence',
                'phone calls', 'travel', 'commute', 'break', 'lunch', 'training',
                'learning', 'reading', 'studying', 'certification', 'course'
            ]):
                new_type = EntityType.TIMESHEET_CONCEPT
            
            # Status/Billing fields - EXPANDED
            elif any(word in entity_lower for word in [
                'billable', 'non-billable', 'chargeable', 'non-chargeable', 'status',
                'billing', 'invoicing', 'charging', 'cost', 'expense', 'budget',
                'rate', 'hourly', 'fixed', 'contract', 'retainer', 'milestone',
                'approved', 'pending', 'rejected', 'submitted', 'draft', 'final'
            ]):
                new_type = EntityType.STATUS
            
            # Time fields - EXPANDED
            elif any(phrase in entity_lower for phrase in [
                'start time', 'end time', 'duration', 'elapsed time', 'total time',
                'break time', 'lunch time', 'overtime', 'regular time', 'extra time',
                'time spent', 'time logged', 'time tracked', 'time recorded',
                'clock in', 'clock out', 'punch in', 'punch out', 'check in', 'check out',
                'timestamp', 'time stamp', 'time entry', 'time sheet entry'
            ]):
                new_type = EntityType.TIMESHEET_CONCEPT
            
            # General timesheet concepts - EXPANDED
            elif any(word in entity_lower for word in [
                'timesheet', 'time sheet', 'hours', 'time', 'work', 'labor', 'effort',
                'productivity', 'utilization', 'capacity', 'workload', 'schedule',
                'shift', 'roster', 'rota', 'calendar', 'agenda', 'timeline',
                'tracking', 'logging', 'recording', 'reporting', 'monitoring'
            ]):
                new_type = EntityType.TIMESHEET_CONCEPT
            
            # Create improved entity with enhanced metadata
            metadata = entity.metadata or {}
            if new_type != entity.entity_type:
                metadata['type_improved'] = True
                metadata['original_type'] = entity.entity_type.value
            
            improved_entity = Entity(
                name=entity.name,
                entity_type=new_type,
                confidence=entity.confidence,
                original_text=entity.original_text,
                position=entity.position,
                schema_mapping=entity.schema_mapping,
                metadata=metadata
            )
            
            improved.append(improved_entity)
        
        return improved
    
    def _map_spacy_entity_type(self, spacy_label: str) -> EntityType:
        """Map spaCy entity labels to our entity types"""
        mapping = {
            'PERSON': EntityType.PERSON,
            'ORG': EntityType.CLIENT,
            'DATE': EntityType.DATE,
            'TIME': EntityType.TIME_PERIOD,
            'MONEY': EntityType.NUMBER,
            'CARDINAL': EntityType.NUMBER,
            'ORDINAL': EntityType.NUMBER,
            'PERCENT': EntityType.NUMBER
        }
        return mapping.get(spacy_label, EntityType.UNKNOWN)
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities with improved similarity detection"""
        unique = []
        seen_names = set()
        
        # Sort by confidence first to keep highest confidence entities
        entities_sorted = sorted(entities, key=lambda x: x.confidence, reverse=True)
        
        for entity in entities_sorted:
            entity_name_lower = entity.name.lower().strip()
            
            # Skip if we've seen this exact name
            if entity_name_lower in seen_names:
                continue
            
            # Check for similar names (substring matching)
            is_duplicate = False
            for seen_name in seen_names:
                # If current entity is a substring of a seen entity, skip it
                if entity_name_lower in seen_name and len(entity_name_lower) < len(seen_name):
                    is_duplicate = True
                    break
                # If a seen entity is a substring of current entity, remove the seen one
                elif seen_name in entity_name_lower and len(seen_name) < len(entity_name_lower):
                    # Remove the shorter entity from unique list
                    unique = [e for e in unique if e.name.lower().strip() != seen_name]
                    seen_names.discard(seen_name)
                    break
            
            if not is_duplicate:
                unique.append(entity)
                seen_names.add(entity_name_lower)
        
        return unique
    
    def _is_greeting(self, query_lower: str) -> bool:
        """Check if query is a greeting"""
        greeting_patterns = [
            r'\b(hi|hello|hey)\b',
            r'\bgood\s+(morning|afternoon|evening)\b',
            r'\bhow\s+are\s+you\b'
        ]
        return any(re.search(pattern, query_lower) for pattern in greeting_patterns)
    
    def _create_greeting_intent(self, query: str) -> QueryIntent:
        """Create a greeting intent"""
        return QueryIntent(
            intent_type=IntentType.GREETING,
            confidence=0.99,
            entities=[],
            temporal_context=None,
            aggregation_type=None,
            complexity_level=ComplexityLevel.SIMPLE,
            original_query=query,
            query_vector=np.array([]),
            semantic_features={'query_length': len(query.split())}
        )
    
    # Placeholder methods for compatibility (implement as needed)
    def _extract_temporal_context(self, query: str) -> Optional[TemporalContext]:
        """Extract temporal context - placeholder"""
        return None
    
    def _determine_aggregation_type(self, query: str, intent_type: IntentType) -> Optional[AggregationType]:
        """Determine aggregation type - placeholder"""
        return None
    
    def _assess_complexity(self, query: str, intent_type: IntentType, entities: List[Entity]) -> ComplexityLevel:
        """Assess query complexity"""
        if len(entities) > 5 or len(query.split()) > 10:
            return ComplexityLevel.COMPLEX
        elif len(entities) > 2 or len(query.split()) > 6:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.SIMPLE
    
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
            table_name = primary_entity.name
            clarification += f"Did you mean to ask 'how many {table_name} are there'?"
        
        elif intent == IntentType.SELECT and primary_entity:
            table_name = primary_entity.name
            clarification += f"Are you trying to list all '{table_name}'?"
            
        elif intent in [IntentType.SUM, IntentType.AVERAGE, IntentType.MAX, IntentType.MIN] and primary_entity:
            # Find the most likely aggregation function
            agg_type = intent.value.lower()
            table_name = primary_entity.name
            clarification += f"Are you asking for the '{agg_type}' of something in '{table_name}'?"
            
        elif primary_entity:
            # Generic fallback if intent is less clear but an entity was found
            entity_name = primary_entity.name
            clarification += f"Is your question related to '{entity_name}'?"
            
        else:
            # Very low confidence fallback
            clarification += "Could you please rephrase your question?"
            
        return clarification

    def _extract_semantic_features(self, query: str, query_vector: np.ndarray) -> Dict[str, Any]:
        """Extract semantic features"""
        return {
            'query_length': len(query.split()),
            'has_negation': 'not' in query.lower() or "n't" in query.lower(),
            'has_comparison': any(word in query.lower() for word in ['more', 'less', 'greater', 'higher', 'lower']),
            'has_temporal': any(word in query.lower() for word in ['today', 'yesterday', 'last', 'this', 'next']),
            'has_aggregation': any(word in query.lower() for word in ['total', 'sum', 'average', 'count']),
            'question_type': 'question' if query.strip().endswith('?') else 'statement',
            'semantic_density': min(len([w for w in query.split() if len(w) > 3]) / len(query.split()), 1.0)
        }


# Test the improved engine
if __name__ == "__main__":
    print("🧪 Testing Improved Semantic Intent Engine")
    print("=" * 50)
    
    # Mock vector store for testing
    class MockVectorStore:
        pass
    
    # Initialize improved engine
    engine = ImprovedSemanticIntentEngine(MockVectorStore())
    
    # Test queries
    test_queries = [
        "How many employees are in the system?",
        "List all available clients.",
        "Show me all projects for the client 'C. Steinweg'.",
        "What are the different types of leave available?",
        "Find all activities that are considered 'Non-Billable'.",
        "Who is employee with ID 1000?",
        "Display the first 5 entries from the timesheet table.",
        "How many projects are there in total?",
        "List all employees."
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        try:
            result = engine.analyze_query(query)
            print(f"   Intent: {result.intent_type.value} (confidence: {result.confidence:.3f})")
            print(f"   Entities: {len(result.entities)} found")
            
            for j, entity in enumerate(result.entities[:3], 1):
                print(f"     {j}. Name: '{entity.name}' | Type: {entity.entity_type.value} | Confidence: {entity.confidence:.3f}")
            
            if len(result.entities) > 3:
                print(f"     ... and {len(result.entities) - 3} more entities")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🏁 Testing Complete!")