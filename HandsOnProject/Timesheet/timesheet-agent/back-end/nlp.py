import spacy
from fuzzywuzzy import process
from datetime import datetime, timedelta
import re
from typing import List, Dict, Tuple, Optional

try:
    nlp = spacy.load("en_core_web_md")  
except OSError:
    print("Warning: spaCy model 'en_core_web_md' not found.")
    nlp = None

def normalize_date(date_str: str) -> Optional[Tuple[str, str]]:
    date_str = date_str.strip()
    try:
        if re.match(r"^\d{4}$", date_str):
            return f"{date_str}-01-01", f"{date_str}-12-31"
        if re.match(r"^Q[1-4]\s+\d{4}$", date_str, re.IGNORECASE):
            year = int(date_str.split()[1])
            quarter = int(date_str[1])
            start_month = (quarter - 1) * 3 + 1
            end_month = start_month + 2
            start_date = f"{year}-{start_month:02d}-01"
            end_date = (datetime(year, end_month, 1) + timedelta(days=31)).replace(day=1).strftime("%Y-%m-%d")
            return start_date, end_date
        if re.match(r"^\w+\s+\d{4}$", date_str, re.IGNORECASE):
            parsed = datetime.strptime(date_str, "%B %Y")
            start_date = parsed.replace(day=1).strftime("%Y-%m-%d")
            end_date = (parsed.replace(day=28) + timedelta(days=4)).replace(day=1).strftime("%Y-%m-%d")
            return start_date, end_date
        parsed = datetime.strptime(date_str, "%B %d, %Y")
        return parsed.strftime("%Y-%m-%d"), parsed.strftime("%Y-%m-%d")
    except ValueError:
        return None

def get_name_columns(schema_metadata: List[Dict]) -> List[str]:
    name_columns = []
    for meta in schema_metadata:
        for col in meta["columns"]:
            if col["type"].lower().startswith(("varchar", "nvarchar")) and "name" in col["name"].lower():
                name_columns.append(f"{meta['schema']}.{meta['table']}.{col['name']}")
    return name_columns

def extract_entities(query: str, schema_metadata: List[Dict], execute_query_fn) -> Dict:
    entities = {
        "names": [],
        "dates": [],
        "keywords": [],
        "intent": None,
        "target_table": None
    }

    if nlp is None:
        return entities

    doc = nlp(query)

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["names"].append(ent.text)
        elif ent.label_ == "DATE":
            normalized = normalize_date(ent.text)
            if normalized:
                entities["dates"].append(normalized)

    name_columns = get_name_columns(schema_metadata)
    if name_columns and not entities["names"]:
        for col in name_columns:
            schema, table, col_name = col.split(".")
            try:
                rows, _ = execute_query_fn(f"SELECT DISTINCT [{col_name}] FROM [{schema}].[{table}]")
                if rows:
                    possible_names = [row[0] for row in rows if row and row[0]]
                    for word in query.split():
                        match = process.extractOne(word, possible_names, score_cutoff=85)
                        if match and match[0] not in entities["names"]:
                            entities["names"].append(match[0])
                # else:
                #     print(f"Skipping fuzzy match for {col} - no data")
            except Exception as e:
                print(f"Failed to query {schema}.{table}.{col_name}: {e}")

    intent_keywords = {
        "list": ["show", "display", "list", "get", "find"],
        "count": ["how many", "count"],
        "sum": ["total", "sum", "how many hours", "average", "avg"],
        "filter": ["where", "for", "in", "by"]
    }

    query_lower = query.lower()
    for intent, keywords in intent_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            entities["intent"] = intent
            entities["keywords"].extend([k for k in keywords if k in query_lower])
            break

    table_names = {meta["table"].lower() for meta in schema_metadata}
    table_aliases = {t: t for t in table_names}
    for meta in schema_metadata:
        table_aliases[meta["table"].lower()] = meta["table"]
        table_aliases[meta["table"].lower() + "s"] = meta["table"]

    for token in doc:
        token_text = token.text.lower()
        if token_text in table_aliases:
            entities["target_table"] = table_aliases[token_text]

    return entities
