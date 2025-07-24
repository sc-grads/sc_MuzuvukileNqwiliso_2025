import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

HISTORY_FILE = "cache/query_history.json"
CONVERSATION_FILE = "cache/conversation_context.json"

@dataclass
class QueryEntry:
    """Enhanced query entry with conversation context"""
    timestamp: str
    natural_language_query: str
    sql_query: Optional[str]
    success: bool
    error: Optional[str] = None
    conversation_id: Optional[str] = None
    entities_extracted: Optional[Dict] = None
    query_results_summary: Optional[str] = None
    context_references: Optional[List[str]] = None
    retry_count: int = 0
    parent_query_id: Optional[str] = None
    query_id: Optional[str] = None

@dataclass
class ConversationContext:
    """Manages conversation state and context"""
    conversation_id: str
    start_time: str
    last_activity: str
    active_entities: Dict[str, any] = None
    referenced_tables: Set[str] = None
    referenced_columns: Set[str] = None
    topic_keywords: Set[str] = None
    successful_queries: List[str] = None
    failed_patterns: List[str] = None
    user_preferences: Dict[str, any] = None
    
    def __post_init__(self):
        if self.active_entities is None:
            self.active_entities = {}
        if self.referenced_tables is None:
            self.referenced_tables = set()
        if self.referenced_columns is None:
            self.referenced_columns = set()
        if self.topic_keywords is None:
            self.topic_keywords = set()
        if self.successful_queries is None:
            self.successful_queries = []
        if self.failed_patterns is None:
            self.failed_patterns = []
        if self.user_preferences is None:
            self.user_preferences = {}

class ConversationManager:
    """Manages conversation context and multi-turn interactions"""
    
    def __init__(self):
        self.current_conversation_id = None
        self.context_window_size = 10  # Number of recent queries to maintain in context
        self.max_conversation_age_hours = 2  # Auto-reset conversation after 2 hours
        
    def get_or_create_conversation_id(self) -> str:
        """Get current conversation ID or create a new one"""
        if self.current_conversation_id is None:
            self.current_conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.current_conversation_id
    
    def should_start_new_conversation(self, query: str, last_activity: Optional[str] = None) -> bool:
        """Determine if we should start a new conversation based on context shift"""
        if last_activity is None:
            return True
            
        # Check time gap
        try:
            last_time = datetime.fromisoformat(last_activity)
            if datetime.now() - last_time > timedelta(hours=self.max_conversation_age_hours):
                return True
        except:
            return True
            
        # Check for conversation reset indicators
        reset_patterns = [
            r'\b(new|different|another|switch|change)\s+(topic|subject|question)\b',
            r'\b(start\s+over|begin\s+again|fresh\s+start)\b',
            r'\b(forget|ignore|nevermind)\s+(that|previous|earlier)\b'
        ]
        
        query_lower = query.lower()
        for pattern in reset_patterns:
            if re.search(pattern, query_lower):
                return True
                
        return False
    
    def extract_context_references(self, query: str) -> List[str]:
        """Extract references to previous context (that, those, it, etc.)"""
        references = []
        
        # Pronoun references
        pronoun_patterns = [
            r'\b(that|those|this|these)\s+(\w+)',
            r'\b(it|they|them)\b',
            r'\b(the\s+same|similar)\b',
            r'\b(previous|earlier|last|recent)\s+(\w+)',
            r'\b(above|mentioned)\s+(\w+)'
        ]
        
        query_lower = query.lower()
        for pattern in pronoun_patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                references.append(match.group())
                
        return references
    
    def update_conversation_context(self, query_entry: QueryEntry, entities: Dict) -> ConversationContext:
        """Update conversation context with new query information"""
        context = self.get_conversation_context()
        
        # Update activity timestamp
        context.last_activity = query_entry.timestamp
        
        # Update entities and references
        if entities:
            # Update active entities
            for key, value in entities.items():
                if value and key not in ['intent', 'is_database_related']:
                    context.active_entities[key] = value
            
            # Track referenced tables and columns
            if 'tables' in entities and entities['tables']:
                context.referenced_tables.update(entities['tables'])
            if 'columns' in entities and entities['columns']:
                context.referenced_columns.update(entities['columns'])
        
        # Extract and store topic keywords
        topic_words = self._extract_topic_keywords(query_entry.natural_language_query)
        context.topic_keywords.update(topic_words)
        
        # Track successful patterns
        if query_entry.success and query_entry.sql_query:
            context.successful_queries.append(query_entry.sql_query)
            # Keep only recent successful queries
            if len(context.successful_queries) > 5:
                context.successful_queries = context.successful_queries[-5:]
        
        # Track failed patterns for learning
        if not query_entry.success and query_entry.error:
            context.failed_patterns.append({
                'query': query_entry.natural_language_query,
                'error': query_entry.error,
                'timestamp': query_entry.timestamp
            })
            # Keep only recent failures
            if len(context.failed_patterns) > 3:
                context.failed_patterns = context.failed_patterns[-3:]
        
        self.save_conversation_context(context)
        return context
    
    def _extract_topic_keywords(self, query: str) -> Set[str]:
        """Extract meaningful keywords from query for topic tracking"""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'show', 'find', 'get', 'give', 'tell', 'me', 'i', 'you', 'we', 'they', 'it', 'this', 'that', 'these', 'those'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        return {word for word in words if word not in stop_words}
    
    def get_conversation_context(self) -> ConversationContext:
        """Get current conversation context"""
        if not os.path.exists(CONVERSATION_FILE):
            return ConversationContext(
                conversation_id=self.get_or_create_conversation_id(),
                start_time=datetime.now().isoformat(),
                last_activity=datetime.now().isoformat()
            )
        
        try:
            with open(CONVERSATION_FILE, 'r') as f:
                data = json.load(f)
                # Convert sets back from lists
                if 'referenced_tables' in data:
                    data['referenced_tables'] = set(data['referenced_tables'])
                if 'referenced_columns' in data:
                    data['referenced_columns'] = set(data['referenced_columns'])
                if 'topic_keywords' in data:
                    data['topic_keywords'] = set(data['topic_keywords'])
                return ConversationContext(**data)
        except Exception as e:
            print(f"Error loading conversation context: {e}")
            return ConversationContext(
                conversation_id=self.get_or_create_conversation_id(),
                start_time=datetime.now().isoformat(),
                last_activity=datetime.now().isoformat()
            )
    
    def save_conversation_context(self, context: ConversationContext):
        """Save conversation context to file"""
        try:
            # Convert sets to lists for JSON serialization
            data = asdict(context)
            data['referenced_tables'] = list(context.referenced_tables)
            data['referenced_columns'] = list(context.referenced_columns)
            data['topic_keywords'] = list(context.topic_keywords)
            
            with open(CONVERSATION_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving conversation context: {e}")
    
    def reset_conversation(self):
        """Start a new conversation"""
        self.current_conversation_id = None
        if os.path.exists(CONVERSATION_FILE):
            os.remove(CONVERSATION_FILE)
    
    def get_context_for_query(self, current_query: str) -> Dict:
        """Get relevant context for current query processing"""
        context = self.get_conversation_context()
        recent_history = get_recent_queries(limit=self.context_window_size)
        
        # Check for context references in current query
        references = self.extract_context_references(current_query)
        
        return {
            'conversation_id': context.conversation_id,
            'active_entities': context.active_entities,
            'referenced_tables': list(context.referenced_tables),
            'referenced_columns': list(context.referenced_columns),
            'topic_keywords': list(context.topic_keywords),
            'recent_queries': recent_history,
            'context_references': references,
            'successful_patterns': context.successful_queries[-3:] if context.successful_queries else [],
            'failed_patterns': context.failed_patterns
        }

# Global conversation manager instance
conversation_manager = ConversationManager()

def save_query(nl_query: str, sql_query: Optional[str], timestamp: str, success: bool, 
               error: Optional[str] = None, entities: Optional[Dict] = None,
               query_results_summary: Optional[str] = None, retry_count: int = 0,
               parent_query_id: Optional[str] = None) -> str:
    """Enhanced save_query with conversation context support"""
    
    # Check if we should start a new conversation
    context = conversation_manager.get_conversation_context()
    if conversation_manager.should_start_new_conversation(nl_query, context.last_activity):
        conversation_manager.reset_conversation()
    
    # Generate unique query ID
    query_id = f"q_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Extract context references
    context_references = conversation_manager.extract_context_references(nl_query)
    
    # Create enhanced query entry
    entry = QueryEntry(
        query_id=query_id,
        timestamp=timestamp,
        natural_language_query=nl_query,
        sql_query=sql_query,
        success=success,
        error=error,
        conversation_id=conversation_manager.get_or_create_conversation_id(),
        entities_extracted=entities,
        query_results_summary=query_results_summary,
        context_references=context_references,
        retry_count=retry_count,
        parent_query_id=parent_query_id
    )
    
    # Update conversation context
    conversation_manager.update_conversation_context(entry, entities or {})
    
    # Save to history
    history = get_query_history()
    history.append(asdict(entry))
    
    # Maintain history size limit
    if len(history) > 100:
        history = history[-100:]
    
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving query history: {e}")
    
    return query_id

def get_query_history() -> List[Dict]:
    """Get complete query history"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading query history: {e}")
    return []

def get_recent_queries(limit: int = 5, conversation_id: Optional[str] = None) -> List[Dict]:
    """Get recent queries, optionally filtered by conversation"""
    history = get_query_history()
    
    if conversation_id:
        # Filter by conversation ID
        filtered_history = [entry for entry in history if entry.get('conversation_id') == conversation_id]
    else:
        filtered_history = history
    
    return filtered_history[-limit:] if filtered_history else []

def get_conversation_context_for_query(current_query: str) -> Dict:
    """Get conversation context for processing current query"""
    return conversation_manager.get_context_for_query(current_query)

def find_similar_successful_queries(current_query: str, limit: int = 3) -> List[Dict]:
    """Find similar successful queries for learning from past successes"""
    history = get_query_history()
    successful_queries = [entry for entry in history if entry.get('success', False)]
    
    if not successful_queries:
        return []
    
    # Simple keyword-based similarity (can be enhanced with vector similarity)
    current_keywords = set(re.findall(r'\b[a-zA-Z]{3,}\b', current_query.lower()))
    
    scored_queries = []
    for entry in successful_queries:
        entry_keywords = set(re.findall(r'\b[a-zA-Z]{3,}\b', entry['natural_language_query'].lower()))
        similarity = len(current_keywords.intersection(entry_keywords)) / len(current_keywords.union(entry_keywords)) if current_keywords.union(entry_keywords) else 0
        
        if similarity > 0.1:  # Minimum similarity threshold
            scored_queries.append((similarity, entry))
    
    # Sort by similarity and return top matches
    scored_queries.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored_queries[:limit]]

def get_failed_query_patterns(current_query: str) -> List[Dict]:
    """Get patterns of failed queries to avoid repeating mistakes"""
    context = conversation_manager.get_conversation_context()
    return context.failed_patterns

def resolve_context_references(query: str, context: Dict) -> str:
    """Resolve context references in query using conversation history"""
    resolved_query = query
    
    # Get recent successful queries for context
    recent_queries = context.get('recent_queries', [])
    active_entities = context.get('active_entities', {})
    
    if not recent_queries:
        return resolved_query
    
    # Find the most recent successful query with results
    last_successful = None
    for entry in reversed(recent_queries):
        if entry.get('success', False) and entry.get('sql_query'):
            last_successful = entry
            break
    
    if not last_successful:
        return resolved_query
    
    # Replace common reference patterns
    reference_replacements = {
        r'\bthat\s+employee\b': _extract_employee_reference(last_successful),
        r'\bthose\s+projects?\b': _extract_project_reference(last_successful),
        r'\bthat\s+table\b': _extract_table_reference(last_successful),
        r'\bthe\s+same\s+period\b': _extract_period_reference(last_successful),
        r'\bsimilar\s+data\b': _extract_data_reference(last_successful)
    }
    
    for pattern, replacement in reference_replacements.items():
        if replacement:
            resolved_query = re.sub(pattern, replacement, resolved_query, flags=re.IGNORECASE)
    
    return resolved_query

def _extract_employee_reference(query_entry: Dict) -> Optional[str]:
    """Extract employee reference from previous query"""
    sql = query_entry.get('sql_query', '')
    if not sql:
        return None
    
    # Look for employee names or IDs in WHERE clauses
    employee_patterns = [
        r"WHERE\s+.*employee.*=\s*'([^']+)'",
        r"WHERE\s+.*name.*=\s*'([^']+)'",
        r"employee_id\s*=\s*(\d+)"
    ]
    
    for pattern in employee_patterns:
        match = re.search(pattern, sql, re.IGNORECASE)
        if match:
            return f"employee '{match.group(1)}'"
    
    return None

def _extract_project_reference(query_entry: Dict) -> Optional[str]:
    """Extract project reference from previous query"""
    sql = query_entry.get('sql_query', '')
    if not sql:
        return None
    
    # Look for project names or IDs in WHERE clauses
    project_patterns = [
        r"WHERE\s+.*project.*=\s*'([^']+)'",
        r"project_id\s*=\s*(\d+)"
    ]
    
    for pattern in project_patterns:
        match = re.search(pattern, sql, re.IGNORECASE)
        if match:
            return f"project '{match.group(1)}'"
    
    return None

def _extract_table_reference(query_entry: Dict) -> Optional[str]:
    """Extract table reference from previous query"""
    sql = query_entry.get('sql_query', '')
    if not sql:
        return None
    
    # Extract table name from FROM clause
    from_match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
    if from_match:
        return f"table {from_match.group(1)}"
    
    return None

def _extract_period_reference(query_entry: Dict) -> Optional[str]:
    """Extract time period reference from previous query"""
    sql = query_entry.get('sql_query', '')
    if not sql:
        return None
    
    # Look for date ranges in WHERE clauses
    date_patterns = [
        r"date.*BETWEEN\s*'([^']+)'\s*AND\s*'([^']+)'",
        r"date.*>=\s*'([^']+)'",
        r"YEAR\([^)]+\)\s*=\s*(\d{4})",
        r"MONTH\([^)]+\)\s*=\s*(\d+)"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, sql, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                return f"period from {match.group(1)} to {match.group(2)}"
            else:
                return f"period {match.group(1)}"
    
    return None

def _extract_data_reference(query_entry: Dict) -> Optional[str]:
    """Extract general data reference from previous query"""
    entities = query_entry.get('entities_extracted', {})
    if entities and 'tables' in entities:
        tables = entities['tables']
        if tables:
            return f"data from {', '.join(tables)}"
    
    return None
