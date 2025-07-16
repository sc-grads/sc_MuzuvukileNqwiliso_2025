import spacy
from fuzzywuzzy import process
from datetime import datetime, timedelta
import re
from typing import List, Dict, Tuple, Optional
from dateutil.parser import parse as parse_date

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
    date_str = date_str.strip()
    try:
        today = datetime.now()
        if "today" in date_str.lower():
            return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        if "yesterday" in date_str.lower():
            yesterday = today - timedelta(days=1)
            return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
        if "this week" in date_str.lower():
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")
        if "last week" in date_str.lower():
            end_of_last_week = today - timedelta(days=today.weekday() + 1)
            start_of_last_week = end_of_last_week - timedelta(days=6)
            return start_of_last_week.strftime("%Y-%m-%d"), end_of_last_week.strftime("%Y-%m-%d")
        if "this month" in date_str.lower():
            start_of_month = today.replace(day=1)
            next_month = start_of_month.replace(day=28) + timedelta(days=4)
            end_of_month = next_month - timedelta(days=next_month.day)
            return start_of_month.strftime("%Y-%m-%d"), end_of_month.strftime("%Y-%m-%d")
        if "last month" in date_str.lower():
            end_of_last_month = today.replace(day=1) - timedelta(days=1)
            start_of_last_month = end_of_last_month.replace(day=1)
            return start_of_last_month.strftime("%Y-%m-%d"), end_of_last_month.strftime("%Y-%m-%d")
        parsed_date = parse_date(date_str)
        return parsed_date.strftime("%Y-%m-%d"), parsed_date.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        return None

def get_name_columns(schema_metadata: List[Dict]) -> List[str]:
    name_columns = []
    for meta in schema_metadata:
        for col in meta["columns"]:
            if col["type"].lower().startswith(("varchar", "nvarchar")) and "name" in col["name"].lower():
                name_columns.append(f"{meta['schema']}.{meta['table']}.{col['name']}")
    return name_columns

def extract_entities(query: str, schema_metadata: List[Dict], execute_query_fn, vector_store=None) -> Dict:
    entities = {
        "names": [],
        "dates": [],
        "keywords": [],
        "intent": None,
        "suggested_tables": [],
        "is_database_related": False
    }

    if nlp is not None and schema_metadata:
        try:
            doc = nlp(query)
            if doc.ents:
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        entities["names"].append(ent.text)
                    elif ent.label_ == "DATE":
                        normalized = normalize_date(ent.text)
                        if normalized:
                            entities["dates"].append(normalized)
        except Exception as e:
            print(f"Error during NLP entity extraction: {e}")

    query_lower = query.lower()
    intent_keywords = {
        "greeting": ["hi", "hello", "hey", "good morning", "good afternoon"],
        "list": ["show", "display", "list", "get", "find"],
        "count": ["how many", "count"],
        "sum": ["total", "sum", "how many hours", "average", "avg"],
        "filter": ["where", "for", "in", "by"]
    }
    for intent, keywords in intent_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            entities["intent"] = intent
            entities["keywords"].extend([k for k in keywords if k in query_lower])
            if intent == "greeting":
                return entities
            entities["is_database_related"] = True
            break

    if entities["is_database_related"]:
        if vector_store:
            schema_docs = vector_store.similarity_search(query, k=3)
            for doc in schema_docs:
                table_info = doc.metadata
                if table_info.get("type") == "schema":
                    entities["suggested_tables"].append(f"{table_info['schema']}.{table_info['table']}")
                    entities["is_database_related"] = True
        else:
            schema_terms = set()
            for meta in schema_metadata:
                schema_terms.add(meta["table"].lower())
                schema_terms.update(col["name"].lower() for col in meta["columns"])
            if not any(term in query_lower for term in schema_terms):
                entities["is_database_related"] = False

    name_columns = get_name_columns(schema_metadata) if schema_metadata else []

    if entities["is_database_related"] and vector_store:
        schema_docs = vector_store.similarity_search(query, k=3)
        for doc in schema_docs:
            table_info = doc.metadata
            if table_info.get("type") == "schema":
                entities["suggested_tables"].append(f"{table_info['schema']}.{table_info['table']}")

    return entities
