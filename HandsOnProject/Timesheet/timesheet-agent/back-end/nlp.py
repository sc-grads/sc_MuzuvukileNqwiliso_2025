import spacy
from fuzzywuzzy import process, fuzz
from datetime import datetime, timedelta
import re
from typing import List, Dict, Tuple, Optional, Union
from dateutil.parser import parse as parse_date
import calendar
import numpy as np

def initialize_nlp():
    global nlp
    nlp = None
    try:
        nlp = spacy.load("en_core_web_md")
        return True
    except OSError:
        return False

if not initialize_nlp():
    nlp = None

def normalize_date(date_str: str) -> Optional[Tuple[str, str]]:
    """Enhanced date parsing to handle more natural language date expressions"""
    date_str = date_str.strip().lower()
    today = datetime.now()
    
    try:
        # Relative date expressions
        if "today" in date_str:
            return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        
        if "yesterday" in date_str:
            yesterday = today - timedelta(days=1)
            return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
        
        if "tomorrow" in date_str:
            tomorrow = today + timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d")
        
        # Week-based expressions
        if "this week" in date_str:
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")
        
        if "last week" in date_str:
            end_of_last_week = today - timedelta(days=today.weekday() + 1)
            start_of_last_week = end_of_last_week - timedelta(days=6)
            return start_of_last_week.strftime("%Y-%m-%d"), end_of_last_week.strftime("%Y-%m-%d")
        
        if "next week" in date_str:
            start_of_next_week = today + timedelta(days=(7 - today.weekday()))
            end_of_next_week = start_of_next_week + timedelta(days=6)
            return start_of_next_week.strftime("%Y-%m-%d"), end_of_next_week.strftime("%Y-%m-%d")
        
        # Month-based expressions
        if "this month" in date_str:
            start_of_month = today.replace(day=1)
            next_month = start_of_month.replace(day=28) + timedelta(days=4)
            end_of_month = next_month - timedelta(days=next_month.day)
            return start_of_month.strftime("%Y-%m-%d"), end_of_month.strftime("%Y-%m-%d")
        
        if "last month" in date_str:
            end_of_last_month = today.replace(day=1) - timedelta(days=1)
            start_of_last_month = end_of_last_month.replace(day=1)
            return start_of_last_month.strftime("%Y-%m-%d"), end_of_last_month.strftime("%Y-%m-%d")
        
        if "next month" in date_str:
            start_of_next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
            end_of_next_month = (start_of_next_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            return start_of_next_month.strftime("%Y-%m-%d"), end_of_next_month.strftime("%Y-%m-%d")
        
        # Quarter-based expressions
        current_quarter = (today.month - 1) // 3 + 1
        if "this quarter" in date_str or "current quarter" in date_str:
            start_month = (current_quarter - 1) * 3 + 1
            start_of_quarter = today.replace(month=start_month, day=1)
            end_month = start_month + 2
            end_of_quarter = today.replace(month=end_month, day=calendar.monthrange(today.year, end_month)[1])
            return start_of_quarter.strftime("%Y-%m-%d"), end_of_quarter.strftime("%Y-%m-%d")
        
        if "last quarter" in date_str:
            last_quarter = current_quarter - 1 if current_quarter > 1 else 4
            year = today.year if current_quarter > 1 else today.year - 1
            start_month = (last_quarter - 1) * 3 + 1
            start_of_quarter = datetime(year, start_month, 1)
            end_month = start_month + 2
            end_of_quarter = datetime(year, end_month, calendar.monthrange(year, end_month)[1])
            return start_of_quarter.strftime("%Y-%m-%d"), end_of_quarter.strftime("%Y-%m-%d")
        
        # Year-based expressions
        if "this year" in date_str or "current year" in date_str:
            start_of_year = today.replace(month=1, day=1)
            end_of_year = today.replace(month=12, day=31)
            return start_of_year.strftime("%Y-%m-%d"), end_of_year.strftime("%Y-%m-%d")
        
        if "last year" in date_str:
            last_year = today.year - 1
            start_of_year = datetime(last_year, 1, 1)
            end_of_year = datetime(last_year, 12, 31)
            return start_of_year.strftime("%Y-%m-%d"), end_of_year.strftime("%Y-%m-%d")
        
        # Days of the week
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(weekdays):
            if day in date_str:
                days_ahead = i - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                if "last" in date_str:
                    target_date = today - timedelta(days=(7 - days_ahead))
                return target_date.strftime("%Y-%m-%d"), target_date.strftime("%Y-%m-%d")
        
        # Month names
        months = ['january', 'february', 'march', 'april', 'may', 'june',
                 'july', 'august', 'september', 'october', 'november', 'december']
        for i, month in enumerate(months, 1):
            if month in date_str:
                year = today.year
                if "last" in date_str and i > today.month:
                    year -= 1
                elif "next" in date_str and i < today.month:
                    year += 1
                start_of_month = datetime(year, i, 1)
                end_of_month = datetime(year, i, calendar.monthrange(year, i)[1])
                return start_of_month.strftime("%Y-%m-%d"), end_of_month.strftime("%Y-%m-%d")
        
        # Relative days (e.g., "3 days ago", "in 5 days")
        days_pattern = re.search(r'(\d+)\s+days?\s+(ago|back)', date_str)
        if days_pattern:
            days = int(days_pattern.group(1))
            target_date = today - timedelta(days=days)
            return target_date.strftime("%Y-%m-%d"), target_date.strftime("%Y-%m-%d")
        
        days_pattern = re.search(r'(in\s+)?(\d+)\s+days?', date_str)
        if days_pattern:
            days = int(days_pattern.group(2))
            target_date = today + timedelta(days=days)
            return target_date.strftime("%Y-%m-%d"), target_date.strftime("%Y-%m-%d")
        
        # Relative weeks
        weeks_pattern = re.search(r'(\d+)\s+weeks?\s+(ago|back)', date_str)
        if weeks_pattern:
            weeks = int(weeks_pattern.group(1))
            target_date = today - timedelta(weeks=weeks)
            return target_date.strftime("%Y-%m-%d"), target_date.strftime("%Y-%m-%d")
        
        weeks_pattern = re.search(r'(in\s+)?(\d+)\s+weeks?', date_str)
        if weeks_pattern:
            weeks = int(weeks_pattern.group(2))
            target_date = today + timedelta(weeks=weeks)
            return target_date.strftime("%Y-%m-%d"), target_date.strftime("%Y-%m-%d")
        
        # Try to parse with dateutil as fallback
        parsed_date = parse_date(date_str)
        return parsed_date.strftime("%Y-%m-%d"), parsed_date.strftime("%Y-%m-%d")
        
    except (ValueError, OverflowError):
        return None

def extract_numeric_values(query: str) -> Dict[str, Union[float, int, List[float]]]:
    """Enhanced numeric value extraction with context understanding"""
    numeric_info = {
        "values": [],
        "ranges": [],
        "percentages": [],
        "currencies": [],
        "hours": [],
        "context": []
    }
    
    # Extract basic numbers with context
    number_patterns = [
        (r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)', 'hours'),
        (r'\$(\d+(?:\.\d+)?)', 'currency'),
        (r'(\d+(?:\.\d+)?)%', 'percentage'),
        (r'(\d+(?:\.\d+)?)', 'value')
    ]
    
    for pattern, context in number_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            value = float(match.group(1))
            if context == 'currency':
                numeric_info['currencies'].append(value)
            elif context == 'percentage':
                numeric_info['percentages'].append(value)
            elif context == 'hours':
                numeric_info['hours'].append(value)
            else:
                numeric_info['values'].append(value)
            numeric_info['context'].append(context)
    
    # Extract ranges (e.g., "between 10 and 20", "from 5 to 15")
    range_patterns = [
        r'between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)',
        r'from\s+(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)'
    ]
    
    for pattern in range_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            start_val = float(match.group(1))
            end_val = float(match.group(2))
            numeric_info['ranges'].append((start_val, end_val))
    
    return numeric_info

def extract_comparison_operators(query: str) -> List[Dict[str, str]]:
    """Extract comparison operators and their context"""
    comparisons = []
    
    # Define comparison patterns with their SQL equivalents
    comparison_patterns = [
        (r'greater\s+than\s+(\d+(?:\.\d+)?)', '>', 'greater_than'),
        (r'more\s+than\s+(\d+(?:\.\d+)?)', '>', 'greater_than'),
        (r'above\s+(\d+(?:\.\d+)?)', '>', 'greater_than'),
        (r'over\s+(\d+(?:\.\d+)?)', '>', 'greater_than'),
        (r'>\s*(\d+(?:\.\d+)?)', '>', 'greater_than'),
        
        (r'less\s+than\s+(\d+(?:\.\d+)?)', '<', 'less_than'),
        (r'fewer\s+than\s+(\d+(?:\.\d+)?)', '<', 'less_than'),
        (r'below\s+(\d+(?:\.\d+)?)', '<', 'less_than'),
        (r'under\s+(\d+(?:\.\d+)?)', '<', 'less_than'),
        (r'<\s*(\d+(?:\.\d+)?)', '<', 'less_than'),
        
        (r'at\s+least\s+(\d+(?:\.\d+)?)', '>=', 'greater_equal'),
        (r'minimum\s+of\s+(\d+(?:\.\d+)?)', '>=', 'greater_equal'),
        (r'>=\s*(\d+(?:\.\d+)?)', '>=', 'greater_equal'),
        
        (r'at\s+most\s+(\d+(?:\.\d+)?)', '<=', 'less_equal'),
        (r'maximum\s+of\s+(\d+(?:\.\d+)?)', '<=', 'less_equal'),
        (r'up\s+to\s+(\d+(?:\.\d+)?)', '<=', 'less_equal'),
        (r'<=\s*(\d+(?:\.\d+)?)', '<=', 'less_equal'),
        
        (r'equal\s+to\s+(\d+(?:\.\d+)?)', '=', 'equal'),
        (r'exactly\s+(\d+(?:\.\d+)?)', '=', 'equal'),
        (r'=\s*(\d+(?:\.\d+)?)', '=', 'equal'),
        
        (r'not\s+equal\s+to\s+(\d+(?:\.\d+)?)', '!=', 'not_equal'),
        (r'different\s+from\s+(\d+(?:\.\d+)?)', '!=', 'not_equal'),
        (r'!=\s*(\d+(?:\.\d+)?)', '!=', 'not_equal'),
    ]
    
    for pattern, operator, operator_type in comparison_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            value = float(match.group(1))
            comparisons.append({
                'operator': operator,
                'value': value,
                'type': operator_type,
                'original_text': match.group(0)
            })
    
    # Handle between ranges
    between_patterns = [
        r'between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)',
        r'from\s+(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)'
    ]
    
    for pattern in between_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            start_val = float(match.group(1))
            end_val = float(match.group(2))
            comparisons.append({
                'operator': 'BETWEEN',
                'value': [start_val, end_val],
                'type': 'between',
                'original_text': match.group(0)
            })
    
    return comparisons

def fuzzy_match_schema_elements(query: str, schema_metadata: List[Dict], vector_store=None, threshold: int = 70) -> Dict[str, List[Dict]]:
    """Improved table and column name fuzzy matching using vector similarity"""
    matches = {
        'tables': [],
        'columns': [],
        'combined_matches': []
    }
    
    if not schema_metadata:
        return matches
    
    # Extract all table and column names with metadata
    schema_elements = []
    for meta in schema_metadata:
        table_name = meta['table']
        schema_name = meta['schema']
        
        # Add table information
        schema_elements.append({
            'name': table_name,
            'type': 'table',
            'schema': schema_name,
            'full_name': f"{schema_name}.{table_name}",
            'description': meta.get('description', ''),
            'metadata': meta
        })
        
        # Add column information
        for col in meta['columns']:
            schema_elements.append({
                'name': col['name'],
                'type': 'column',
                'schema': schema_name,
                'table': table_name,
                'full_name': f"{schema_name}.{table_name}.{col['name']}",
                'data_type': col['type'],
                'description': col.get('description', ''),
                'metadata': col
            })
    
    # Use vector similarity if available
    if vector_store:
        try:
            # Search for similar schema elements
            similar_docs = vector_store.similarity_search(query, k=10)
            for doc in similar_docs:
                if doc.metadata.get('type') == 'schema':
                    table_info = doc.metadata
                    similarity_score = _calculate_text_similarity(query, doc.page_content)
                    
                    if similarity_score >= threshold:
                        matches['combined_matches'].append({
                            'element': table_info,
                            'similarity': similarity_score,
                            'match_type': 'vector_similarity'
                        })
        except Exception as e:
            print(f"Vector similarity search failed: {e}")
    
    # Fallback to fuzzy string matching
    query_words = query.lower().split()
    
    for element in schema_elements:
        # Calculate fuzzy match scores
        name_score = fuzz.partial_ratio(query.lower(), element['name'].lower())
        full_name_score = fuzz.partial_ratio(query.lower(), element['full_name'].lower())
        
        # Check for word matches
        word_matches = sum(1 for word in query_words if word in element['name'].lower())
        word_score = (word_matches / len(query_words)) * 100 if query_words else 0
        
        # Combined score with weights
        combined_score = max(name_score, full_name_score, word_score)
        
        if combined_score >= threshold:
            match_info = {
                'element': element,
                'similarity': combined_score,
                'match_type': 'fuzzy_string',
                'name_score': name_score,
                'full_name_score': full_name_score,
                'word_score': word_score
            }
            
            if element['type'] == 'table':
                matches['tables'].append(match_info)
            else:
                matches['columns'].append(match_info)
            
            matches['combined_matches'].append(match_info)
    
    # Sort by similarity score
    for key in matches:
        matches[key].sort(key=lambda x: x['similarity'], reverse=True)
    
    return matches

def _calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using multiple methods"""
    if not text1 or not text2:
        return 0.0
    
    # Use fuzzywuzzy for basic similarity
    basic_score = fuzz.ratio(text1.lower(), text2.lower())
    
    # Word overlap score
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if words1 and words2:
        overlap = len(words1.intersection(words2))
        union = len(words1.union(words2))
        overlap_score = (overlap / union) * 100
    else:
        overlap_score = 0
    
    # Return weighted average
    return (basic_score * 0.7) + (overlap_score * 0.3)

def _is_database_related_query(query_lower: str, schema_metadata: List[Dict], entities: Dict) -> bool:
    """
    Robust multi-layered approach to determine if a query is database-related.
    Uses semantic analysis, context scoring, and schema matching.
    """
    
    # Layer 1: Immediate rejection patterns (highest priority)
    immediate_reject_patterns = [
        # Personal statements
        r'\bmy\s+name\s+is\b', r'\bi\s+am\b', r'\bmy\s+\w+\s+is\b',
        r'\bi\s+have\b', r'\bi\s+like\b', r'\bi\s+want\b', r'\bi\s+need\b',
        
        # General knowledge/conversational
        r'\bweather\b', r'\bwhat\s+is\s+\d+\s*[\+\-\*\/]\s*\d+',
        r'\bhow\s+are\s+you\b', r'\bwho\s+are\s+you\b', r'\bwhat\s+are\s+you\b',
        r'\bthanks?\b', r'\bthank\s+you\b', r'\bgoodbye\b', r'\bbye\b',
        
        # Non-data operations
        r'\bdefine\b', r'\bexplain\s+(?:how|what|why)', r'\btell\s+me\s+about\b',
        r'\bwrite\s+(?:a|an|some)\b', r'\bcreate\s+(?:a|an|some)\b',
        r'\bgenerate\s+(?:a|an|some)\b', r'\bhow\s+do\s+i\b'
    ]
    
    for pattern in immediate_reject_patterns:
        if re.search(pattern, query_lower):
            return False
    
    # Layer 2: Context-based scoring system
    database_score = 0
    non_database_score = 0
    
    # Positive signals (database-related)
    database_signals = {
        # Strong database indicators (high weight)
        'explicit_db_terms': (['database', 'table', 'record', 'query', 'sql', 'schema'], 5),
        'data_operations': (['show', 'list', 'get', 'find', 'count', 'total', 'sum', 'average'], 3),
        'business_entities': (['employee', 'project', 'client', 'timesheet', 'activity'], 4),
        'aggregation_words': (['how many', 'number of', 'total', 'sum of', 'average'], 4),
        'filter_words': (['where', 'with', 'having', 'for', 'by'], 2),
        'comparison_words': (['greater', 'less', 'more', 'fewer', 'above', 'below', 'between'], 3)
    }
    
    # Negative signals (non-database)
    non_database_signals = {
        'general_knowledge': (['meaning', 'definition', 'explain', 'what does', 'how does'], 4),
        'personal_context': (['i am', 'my', 'me', 'myself', 'personal'], 3),
        'external_topics': (['weather', 'news', 'sports', 'politics', 'entertainment'], 5),
        'math_operations': (['calculate', 'solve', 'equation', 'formula'], 4),
        'creative_requests': (['write', 'create', 'generate', 'make'], 3)
    }
    
    # Calculate scores
    for signal_type, (terms, weight) in database_signals.items():
        matches = sum(1 for term in terms if term in query_lower)
        database_score += matches * weight
    
    for signal_type, (terms, weight) in non_database_signals.items():
        matches = sum(1 for term in terms if term in query_lower)
        non_database_score += matches * weight
    
    # Layer 3: Schema relevance check
    schema_relevance_score = 0
    if schema_metadata:
        # Extract schema terms
        schema_terms = set()
        for meta in schema_metadata:
            schema_terms.add(meta["table"].lower())
            for col in meta["columns"]:
                # Only add meaningful column names (not generic ones like 'id', 'name')
                col_name = col["name"].lower()
                if len(col_name) > 2 and col_name not in ['id', 'name', 'date', 'time']:
                    schema_terms.add(col_name)
        
        # Check for schema term matches with context
        query_words = query_lower.split()
        for term in schema_terms:
            if term in query_lower:
                # Higher score if schema term appears with data operation words
                context_words = ['show', 'list', 'get', 'find', 'count', 'total', 'how many']
                if any(ctx_word in query_lower for ctx_word in context_words):
                    schema_relevance_score += 3
                else:
                    schema_relevance_score += 1
    
    # Layer 4: Intent-based validation
    intent_validation_score = 0
    if entities.get("intent"):
        intent = entities["intent"]
        if intent in ["list", "count", "sum", "filter", "comparison", "sort", "group"]:
            # Only boost if there's business context
            business_context = ['employee', 'project', 'client', 'timesheet', 'work', 'hours']
            if any(ctx in query_lower for ctx in business_context):
                intent_validation_score += 3
    
    # Layer 5: Final decision logic
    total_database_score = database_score + schema_relevance_score + intent_validation_score
    
    # Strong rejection if non-database score is high
    if non_database_score >= 8:
        return False
    
    # Strong acceptance if database score is high
    if total_database_score >= 10:
        return True
    
    # Medium threshold with context consideration
    if total_database_score >= 5 and non_database_score <= 3:
        return True
    
    # Default: reject if no strong database signals
    return False
    
    # Signal 1: Direct schema matches (strongest signal)
    if entities.get("schema_matches"):
        schema_matches = entities["schema_matches"]
        if (schema_matches.get("tables") or 
            schema_matches.get("columns") or 
            schema_matches.get("combined_matches")):
            return True
    
    # Signal 2: Explicit database/data keywords
    explicit_db_keywords = [
        "database", "table", "record", "data", "query", "sql",
        "schema", "column", "row", "field", "index"
    ]
    if any(keyword in query_lower for keyword in explicit_db_keywords):
        return True
    
    # Signal 3: Schema-specific terms (dynamically extracted from actual schema)
    if schema_metadata:
        # Extract all table and column names from schema
        schema_terms = set()
        for meta in schema_metadata:
            schema_terms.add(meta["table"].lower())
            for col in meta["columns"]:
                schema_terms.add(col["name"].lower())
        
        # Check for direct matches with schema elements
        query_words = set(query_lower.split())
        if schema_terms.intersection(query_words):
            return True
        
        # Check for partial matches (fuzzy)
        for term in schema_terms:
            if term in query_lower or any(term in word for word in query_words):
                return True
    
    # Signal 4: Data operation patterns combined with business context
    data_operation_patterns = [
        r'\b(?:show|list|get|find|retrieve|fetch)\s+(?:all|the)?\s*\w+',
        r'\b(?:how many|count|number of)\s+\w+',
        r'\b(?:total|sum|average|avg)\s+\w+',
        r'\b(?:who|which|what)\s+\w+\s+(?:have|has|are|is)',
        r'\bemployees?\s+(?:who|that|with)',
        r'\bprojects?\s+(?:where|that|with)',
        r'\btimesheets?\s+(?:for|from|where)',
        r'\bclients?\s+(?:who|that|with)'
    ]
    
    for pattern in data_operation_patterns:
        if re.search(pattern, query_lower):
            return True
    
    # Signal 5: Business domain keywords (context-specific)
    business_keywords = [
        "employee", "employees", "worker", "workers", "staff", "personnel",
        "client", "clients", "customer", "customers", "project", "projects",
        "timesheet", "timesheets", "leave", "hours", "billable", "work", "worked",
        "forecast", "activity", "description", "processed", "information"
    ]
    
    if any(keyword in query_lower for keyword in business_keywords):
        # Additional check: must have data operation intent
        data_intents = ["list", "count", "sum", "filter", "comparison", "sort", "group"]
        if entities.get("intent") in data_intents:
            return True
    
    # Signal 6: Numeric/temporal queries with business context
    if (entities.get("numeric_values") or entities.get("dates") or entities.get("comparisons")):
        # Check if numeric/temporal query has business context
        context_indicators = ["hours", "days", "projects", "employees", "clients", "work"]
        if any(indicator in query_lower for indicator in context_indicators):
            return True
    
    # Signal 7: Aggregation patterns
    aggregation_patterns = [
        r'\btotal\s+\w+',
        r'\bsum\s+of\s+\w+',
        r'\baverage\s+\w+',
        r'\bcount\s+of\s+\w+',
        r'\bhow many\s+\w+',
        r'\bnumber\s+of\s+\w+'
    ]
    
    for pattern in aggregation_patterns:
        if re.search(pattern, query_lower):
            return True
    
    # Signal 8: Reject common non-database patterns (check this FIRST)
    non_database_patterns = [
        # Personal statements
        r'\bmy\s+name\s+is\b',
        r'\bi\s+am\b',
        r'\bmy\s+\w+\s+is\b',
        r'\bi\s+have\b',
        r'\bi\s+like\b',
        r'\bi\s+want\b',
        r'\bi\s+need\b',
        r'\bmy\s+favorite\b',
        
        # General knowledge questions
        r'\bweather\b',
        r'\btime\s+(?:is|now)\b',
        r'\bwhat\s+is\s+\d+\s*[\+\-\*\/]\s*\d+',
        r'\bcalculate\s+\d+',
        r'\bmath\b',
        r'\bsolve\b',
        r'\bdefine\b',
        r'\bexplain\s+(?:how|what|why)',
        r'\btell\s+me\s+about\b',
        r'\bwrite\s+(?:a|an|some)\b',
        r'\bcreate\s+(?:a|an|some)\b',
        r'\bgenerate\s+(?:a|an|some)\b',
        
        # Conversational patterns
        r'\bhow\s+are\s+you\b',
        r'\bwhat\s+are\s+you\b',
        r'\bwho\s+are\s+you\b',
        r'\bcan\s+you\s+help\b',
        r'\bthanks?\b',
        r'\bthank\s+you\b',
        r'\bgoodbye\b',
        r'\bbye\b',
        
        # Non-data questions
        r'\bwhat\s+is\s+the\s+meaning\b',
        r'\bhow\s+do\s+i\b',
        r'\bwhat\s+does\s+\w+\s+mean\b',
        r'\bwhat\s+is\s+\w+\s+(?:used\s+for|about)\b'
    ]
    
    # Check non-database patterns FIRST - if any match, immediately return False
    for pattern in non_database_patterns:
        if re.search(pattern, query_lower):
            return False
    
    # Default: if no strong signals, return False
    return False

def get_name_columns(schema_metadata: List[Dict]) -> List[str]:
    """Enhanced name column detection"""
    name_columns = []
    name_indicators = ['name', 'title', 'description', 'label', 'firstname', 'lastname', 'fullname']
    
    for meta in schema_metadata:
        for col in meta["columns"]:
            col_name_lower = col["name"].lower()
            col_type_lower = col["type"].lower()
            
            # Check if it's a text column and contains name indicators
            if (col_type_lower.startswith(("varchar", "nvarchar", "char", "text")) and 
                any(indicator in col_name_lower for indicator in name_indicators)):
                name_columns.append(f"{meta['schema']}.{meta['table']}.{col['name']}")
    
    return name_columns

def extract_entities(query: str, schema_metadata: List[Dict], execute_query_fn, vector_store=None) -> Dict:
    """Enhanced entity extraction with improved date parsing, numeric values, and fuzzy matching"""
    entities = {
        "names": [],
        "dates": [],
        "keywords": [],
        "intent": None,
        "suggested_tables": [],
        "is_database_related": False,
        "limit": None,
        "numeric_values": {},
        "comparisons": [],
        "schema_matches": {}
    }

    # Enhanced date extraction using improved normalize_date function
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
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            normalized = normalize_date(match.group(0))
            if normalized and normalized not in entities["dates"]:
                entities["dates"].append(normalized)

    # Enhanced numeric value extraction
    entities["numeric_values"] = extract_numeric_values(query)
    
    # Extract comparison operators
    entities["comparisons"] = extract_comparison_operators(query)
    
    # Enhanced schema matching using fuzzy matching and vector similarity
    if schema_metadata:
        entities["schema_matches"] = fuzzy_match_schema_elements(query, schema_metadata, vector_store)

    # Enhanced NLP entity extraction with spaCy
    if nlp is not None and schema_metadata:
        try:
            doc = nlp(query)
            if doc.ents:
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        entities["names"].append(ent.text)
                    elif ent.label_ == "DATE":
                        normalized = normalize_date(ent.text)
                        if normalized and normalized not in entities["dates"]:
                            entities["dates"].append(normalized)
                    elif ent.label_ in ["CARDINAL", "MONEY", "PERCENT", "QUANTITY"]:
                        # Enhanced numeric entity handling
                        try:
                            if "first" in query.lower() or "top" in query.lower():
                                num_match = re.search(r'\d+', ent.text)
                                if num_match:
                                    entities["limit"] = int(num_match.group())
                        except (ValueError, AttributeError):
                            pass
        except Exception as e:
            print(f"Error during NLP entity extraction: {e}")

    # Enhanced intent recognition with more patterns
    query_lower = query.lower()
    intent_keywords = {
        "greeting": ["hi", "hello", "hey", "good morning", "good afternoon", "how are you"],
        "list": ["show", "display", "list", "get", "find", "retrieve", "fetch", "what", "which"],
        "count": ["how many", "count", "number of", "total count"],
        "sum": ["total", "sum", "how many hours", "average", "avg", "mean", "aggregate"],
        "filter": ["where", "for", "in", "by", "with", "having"],
        "comparison": ["greater", "less", "more", "fewer", "above", "below", "between", "equal"],
        "sort": ["order by", "sort", "arrange", "rank", "top", "bottom", "highest", "lowest"],
        "group": ["group by", "grouped", "categorize", "breakdown", "per"]
    }
    
    # Determine primary intent
    intent_scores = {}
    for intent, keywords in intent_keywords.items():
        score = sum(1 for keyword in keywords if keyword in query_lower)
        if score > 0:
            intent_scores[intent] = score
            entities["keywords"].extend([k for k in keywords if k in query_lower])
    
    if intent_scores:
        entities["intent"] = max(intent_scores, key=intent_scores.get)
        if entities["intent"] == "greeting":
            return entities
    
    # Multi-signal approach to determine if query is database-related
    entities["is_database_related"] = _is_database_related_query(query_lower, schema_metadata, entities)
    
    # Enhanced table suggestion using schema matches
    if entities["is_database_related"] and entities["schema_matches"]:
        # Use fuzzy matching results to suggest tables
        table_suggestions = []
        
        # Prioritize tables from fuzzy matching
        for match in entities["schema_matches"]["tables"][:3]:  # Top 3 table matches
            table_element = match["element"]
            table_key = f"{table_element['schema']}.{table_element['name']}"
            if table_key not in table_suggestions:
                table_suggestions.append(table_key)
        
        # Add tables that contain relevant columns
        for match in entities["schema_matches"]["columns"][:5]:  # Top 5 column matches
            column_element = match["element"]
            table_key = f"{column_element['schema']}.{column_element['table']}"
            if table_key not in table_suggestions:
                table_suggestions.append(table_key)
        
        entities["suggested_tables"] = table_suggestions[:3]  # Limit to top 3 suggestions
    
    # Enhanced vector store fallback - try even if not initially database-related
    if vector_store and not entities["suggested_tables"]:
        try:
            schema_docs = vector_store.similarity_search(query, k=5)
            table_scores = {}
            
            for doc in schema_docs:
                table_info = doc.metadata
                if table_info.get("type") == "schema":
                    table_key = f"{table_info['schema']}.{table_info['table']}"
                    
                    # Enhanced scoring based on intent and content
                    score = 0
                    if entities["intent"] == "list" and "name" in table_info.get("description", "").lower():
                        score += 3
                    elif entities["intent"] == "sum":
                        score += 3
                    elif entities["intent"] == "count":
                        score += 2
                    
                    # Boost score for keyword matches in table description
                    for keyword in entities["keywords"]:
                        if keyword in table_info.get("description", "").lower():
                            score += 1
                    
                    # Additional semantic scoring for common database terms
                    query_words = query.lower().split()
                    description = table_info.get("description", "").lower()
                    for word in query_words:
                        if word in description:
                            score += 2
                    
                    # Base score for vector similarity (since it was retrieved)
                    score += 1
                    
                    table_scores[table_key] = score
            
            # Sort and take top suggestions
            sorted_tables = sorted(table_scores.items(), key=lambda x: x[1], reverse=True)
            high_score_tables = [table for table, score in sorted_tables[:3] if score >= 1]  # Include base score
            
            if high_score_tables:
                entities["suggested_tables"] = high_score_tables
                entities["is_database_related"] = True  # Override if vector store finds good matches
                print(f"Vector store override: Found {len(high_score_tables)} relevant tables")
            
        except Exception as e:
            print(f"Error during vector store table suggestion: {e}")
    
    # Final fallback: basic schema term matching
    if entities["is_database_related"] and not entities["suggested_tables"] and schema_metadata:
        schema_terms = set()
        table_term_map = {}
        
        for meta in schema_metadata:
            table_key = f"{meta['schema']}.{meta['table']}"
            schema_terms.add(meta["table"].lower())
            table_term_map[meta["table"].lower()] = table_key
            
            for col in meta["columns"]:
                schema_terms.add(col["name"].lower())
                table_term_map[col["name"].lower()] = table_key
        
        # Find matching tables based on term overlap
        matching_tables = set()
        for term in schema_terms:
            if term in query_lower:
                if term in table_term_map:
                    matching_tables.add(table_term_map[term])
        
        entities["suggested_tables"] = list(matching_tables)[:3]
        entities["is_database_related"] = bool(entities["suggested_tables"]) or bool(schema_terms.intersection(query_lower.split()))

    return entities