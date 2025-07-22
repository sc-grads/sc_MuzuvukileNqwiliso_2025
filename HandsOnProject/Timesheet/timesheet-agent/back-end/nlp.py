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
    
    # Database-related keywords that indicate database queries
    database_keywords = [
        "employee", "employees", "client", "clients", "project", "projects", 
        "timesheet", "timesheets", "leave", "hours", "billable", "work", "worked",
        "database", "table", "record", "data", "show", "list", "count", "total",
        "forecast", "activity", "description", "file", "processed"
    ]
    
    # Check if query contains database-related terms
    has_database_terms = any(keyword in query_lower for keyword in database_keywords)
    
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
    
    # Mark as database-related if has intent OR database terms
    entities["is_database_related"] = bool(intent_scores) or has_database_terms
    
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
    
    # Fallback table suggestion using vector store
    if entities["is_database_related"] and vector_store and not entities["suggested_tables"]:
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
                    elif entities["intent"] == "sum" and any(col["type"].startswith(("decimal", "int", "float")) 
                                                           for col in schema_metadata[0]["columns"] 
                                                           if col["name"].lower() in ["hours", "amount", "total", "sum"]):
                        score += 3
                    elif entities["intent"] == "count":
                        score += 2
                    
                    # Boost score for keyword matches in table description
                    for keyword in entities["keywords"]:
                        if keyword in table_info.get("description", "").lower():
                            score += 1
                    
                    table_scores[table_key] = score
            
            # Sort and take top suggestions
            sorted_tables = sorted(table_scores.items(), key=lambda x: x[1], reverse=True)
            entities["suggested_tables"] = [table for table, score in sorted_tables[:3] if score > 0]
            entities["is_database_related"] = bool(entities["suggested_tables"])
            
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