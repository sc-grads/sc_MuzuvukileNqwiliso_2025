#!/usr/bin/env python3
"""
Query Intent Classifier - Systematic approach to classify user queries
and determine appropriate SQL generation strategy.
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

class QueryType(Enum):
    """Types of queries that require different handling"""
    GREETING = "greeting"
    LIST_ALL = "list_all"  # "Show all employees", "List all projects"
    SPECIFIC_SEARCH = "specific_search"  # "Show John's timesheets"
    COUNT_ALL = "count_all"  # "How many employees?"
    COUNT_SPECIFIC = "count_specific"  # "How many hours did John work?"
    AGGREGATION = "aggregation"  # "Average salary", "Total hours"
    COMPLEX_QUERY = "complex_query"  # Multi-table joins, complex conditions

@dataclass
class QueryClassification:
    """Result of query classification"""
    query_type: QueryType
    confidence: float
    requires_where_clause: bool
    target_entities: List[str]  # Actual searchable entities (not query words)
    suggested_columns: List[str]  # Columns to include in SELECT
    explanation: str

class QueryIntentClassifier:
    """
    Classifies user queries to determine the appropriate SQL generation strategy.
    This prevents issues like adding WHERE clauses to "show all" queries.
    """
    
    def __init__(self):
        # Common stop words that should never become WHERE conditions
        self.stop_words = {
            'show', 'me', 'all', 'get', 'find', 'list', 'display', 'what', 'how', 'many',
            'count', 'total', 'sum', 'average', 'max', 'min', 'is', 'the', 'are', 'there',
            'of', 'with', 'by', 'from', 'to', 'in', 'on', 'at', 'for', 'and', 'or',
            'employees', 'employee', 'clients', 'client', 'projects', 'project', 'types',
            'system', 'available', 'data', 'information', 'records', 'entries', 'items',
            'hello', 'hi', 'hey', 'world', 'wolrd', 'good', 'morning', 'afternoon', 'evening'
        }
        
        # Patterns for different query types
        self.greeting_patterns = [
            r'\b(hi|hello|hey|good\s+(morning|afternoon|evening))\b',
            r'\bhow\s+are\s+you\b',
            r'\bwhat\s+can\s+you\s+do\b'
        ]
        
        self.list_all_patterns = [
            r'\b(show|list|display|get|retrieve|find)\s+all\s+\w+',
            r'\ball\s+(employees|clients|projects|types|data)',
            r'\b(show|list)\s+(employees|clients|projects|types)\b(?!\s+for|\s+with|\s+where)',
            r'\bwhat\s+(employees|clients|projects|types)\s+do\s+we\s+have\b'
        ]
        
        self.count_all_patterns = [
            r'\bhow\s+many\s+\w+\s+(are\s+there|do\s+we\s+have)\b',
            r'\bcount\s+all\s+\w+',
            r'\btotal\s+number\s+of\s+\w+'
        ]
        
        self.specific_search_patterns = [
            r'\b(show|find|get)\s+\w+\'s\s+\w+',  # "Show John's timesheets"
            r'\b\w+\s+(worked|hours|timesheet|leave)',  # "John worked", "John hours"
            r'\bfor\s+\w+\s+\w+',  # "for John Smith"
            r'\b(where|with|by)\s+\w+',  # "where John", "with John"
        ]
    
    def classify_query(self, query: str) -> QueryClassification:
        """
        Classify a query and determine how it should be handled.
        
        Args:
            query: Natural language query
            
        Returns:
            QueryClassification with handling strategy
        """
        query_lower = query.lower().strip()
        
        # 1. Check for greetings
        if self._matches_patterns(query_lower, self.greeting_patterns):
            return QueryClassification(
                query_type=QueryType.GREETING,
                confidence=0.95,
                requires_where_clause=False,
                target_entities=[],
                suggested_columns=['Message'],
                explanation="Conversational greeting - return friendly response"
            )
        
        # 2. Check for "list all" queries
        if self._matches_patterns(query_lower, self.list_all_patterns):
            target_table = self._extract_target_table(query_lower)
            return QueryClassification(
                query_type=QueryType.LIST_ALL,
                confidence=0.9,
                requires_where_clause=False,
                target_entities=[],
                suggested_columns=self._get_default_columns_for_table(target_table),
                explanation=f"List all records from {target_table} - no WHERE clause needed"
            )
        
        # 3. Check for "count all" queries
        if self._matches_patterns(query_lower, self.count_all_patterns):
            return QueryClassification(
                query_type=QueryType.COUNT_ALL,
                confidence=0.9,
                requires_where_clause=False,
                target_entities=[],
                suggested_columns=['COUNT(*)'],
                explanation="Count all records - no WHERE clause needed"
            )
        
        # 4. Check for specific searches
        if self._matches_patterns(query_lower, self.specific_search_patterns):
            entities = self._extract_meaningful_entities(query)
            return QueryClassification(
                query_type=QueryType.SPECIFIC_SEARCH,
                confidence=0.8,
                requires_where_clause=len(entities) > 0,
                target_entities=entities,
                suggested_columns=['*'],
                explanation=f"Specific search for entities: {entities}"
            )
        
        # 5. Default to complex query
        entities = self._extract_meaningful_entities(query)
        return QueryClassification(
            query_type=QueryType.COMPLEX_QUERY,
            confidence=0.6,
            requires_where_clause=len(entities) > 0,
            target_entities=entities,
            suggested_columns=['*'],
            explanation="Complex query - analyze entities for WHERE conditions"
        )
    
    def _matches_patterns(self, query: str, patterns: List[str]) -> bool:
        """Check if query matches any of the given patterns"""
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)
    
    def _extract_target_table(self, query_lower: str) -> str:
        """Extract the target table from query"""
        table_keywords = {
            'employee': 'employees',
            'client': 'clients', 
            'project': 'projects',
            'leave': 'leave_types',
            'timesheet': 'timesheets'
        }
        
        for keyword, table in table_keywords.items():
            if keyword in query_lower:
                return table
        
        return 'unknown'
    
    def _get_default_columns_for_table(self, table: str) -> List[str]:
        """Get default columns for listing queries"""
        column_mapping = {
            'employees': ['EmployeeName'],
            'clients': ['ClientName'],
            'projects': ['ProjectName'],
            'leave_types': ['LeaveTypeID', 'LeaveTypeName'],
            'timesheets': ['Date', 'EmployeeName', 'ProjectName', 'TotalHours']
        }
        
        return column_mapping.get(table, ['*'])
    
    def _extract_meaningful_entities(self, query: str) -> List[str]:
        """
        Extract meaningful entities that should become WHERE conditions.
        This filters out common query words and focuses on actual searchable terms.
        """
        words = query.split()
        entities = []
        
        for word in words:
            # Skip stop words
            if word.lower() in self.stop_words:
                continue
            
            # Skip very short words
            if len(word) < 3:
                continue
            
            # Look for potential person names (capitalized, not at start of sentence)
            if word[0].isupper() and word.isalpha():
                # Additional validation - check if it's likely a person name
                if self._is_likely_person_name(word, query):
                    entities.append(word)
            
            # Look for quoted strings (explicit search terms)
            if word.startswith('"') and word.endswith('"'):
                entities.append(word.strip('"'))
        
        return entities
    
    def _is_likely_person_name(self, word: str, full_query: str) -> bool:
        """
        Determine if a capitalized word is likely a person name.
        Uses context clues from the full query.
        """
        query_lower = full_query.lower()
        
        # Person-related context indicators
        person_indicators = [
            'employee', 'person', 'user', 'staff', 'worker', 'member',
            'hours', 'worked', 'timesheet', 'leave', 'vacation', 'sick',
            'project', 'assigned', 'billable', 'overtime'
        ]
        
        # Check if query contains person-related context
        has_person_context = any(indicator in query_lower for indicator in person_indicators)
        
        # Check if word appears in a person-name context
        word_lower = word.lower()
        word_index = query_lower.find(word_lower)
        
        if word_index > 0:
            # Check words before and after
            context_start = max(0, word_index - 20)
            context_end = min(len(query_lower), word_index + len(word) + 20)
            context = query_lower[context_start:context_end]
            
            person_context_patterns = [
                r'\b(for|by|with|from)\s+' + re.escape(word_lower),
                re.escape(word_lower) + r'\'s\s+',
                r'\b' + re.escape(word_lower) + r'\s+(worked|hours|timesheet|leave)'
            ]
            
            if any(re.search(pattern, context) for pattern in person_context_patterns):
                return True
        
        return has_person_context and len(word) > 3

    def should_add_where_clause(self, query: str, extracted_entities: List[str]) -> bool:
        """
        Determine if a WHERE clause should be added based on query classification.
        
        Args:
            query: Natural language query
            extracted_entities: List of entities extracted by other systems
            
        Returns:
            True if WHERE clause should be added, False otherwise
        """
        classification = self.classify_query(query)
        
        # Never add WHERE clause for these query types
        if classification.query_type in [QueryType.GREETING, QueryType.LIST_ALL, QueryType.COUNT_ALL]:
            return False
        
        # Only add WHERE clause if we have meaningful entities
        meaningful_entities = [
            entity for entity in extracted_entities 
            if entity.lower() not in self.stop_words and len(entity) > 2
        ]
        
        return len(meaningful_entities) > 0

# Example usage
if __name__ == "__main__":
    classifier = QueryIntentClassifier()
    
    test_queries = [
        "Show all employees",
        "List all clients in the system",
        "What projects do we have?",
        "Show timesheet files for Karabo Tsaoane",
        "How many employees are there?",
        "Hello world",
        "Hi there",
        "Show Pascal Govender's billable hours"
    ]
    
    for query in test_queries:
        classification = classifier.classify_query(query)
        print(f"\nQuery: {query}")
        print(f"Type: {classification.query_type.value}")
        print(f"Requires WHERE: {classification.requires_where_clause}")
        print(f"Entities: {classification.target_entities}")
        print(f"Explanation: {classification.explanation}")