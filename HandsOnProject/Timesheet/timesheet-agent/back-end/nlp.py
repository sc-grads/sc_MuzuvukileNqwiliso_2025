import spacy
from fuzzywuzzy import process
from datetime import datetime, timedelta
import re
from typing import List, Dict, Tuple, Optional

def initialize_nlp():
    global nlp
    try:
        print("Attempting to load spaCy model 'en_core_web_md'...")
        nlp = spacy.load("en_core_web_md")
        print("spaCy model loaded successfully. Checking capabilities...")
        # Test the model with a sample text
        test_doc = nlp("John Smith works at Google")
        if hasattr(test_doc, 'ents') and test_doc.ents:
            print("Model supports entity recognition.")
        else:
            print("Warning: Model does not support entity recognition. Falling back to keyword-based extraction.")
        return True
    except OSError as e:
        print(f"Warning: spaCy model 'en_core_web_md' not found or corrupted: {e}")
        print("Attempting to download the model...")
        import subprocess
        try:
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"], check=True)
            nlp = spacy.load("en_core_web_md")
            print("Model downloaded and loaded successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to download spaCy model: {e}")
            return False
    except Exception as e:
        print(f"Unexpected error loading spaCy model: {e}")
        return False

# Initialize nlp at module load
if not initialize_nlp():
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

def extract_entities(query: str, schema_metadata: List[Dict], execute_query_fn, vector_store=None) -> Dict:
    entities = {
        "names": [],
        "dates": [],
        "keywords": [],
        "intent": None,
        "suggested_tables": [],
        "is_database_related": False
    }

    if nlp is None or not schema_metadata:
        print("Warning: NLP model not available or no schema metadata. Using keyword-based extraction.")
    else:
        try:
            doc = nlp(query)
            print(f"Processed query: '{query}' into Doc object with {len(doc)} tokens. Entities found: {len(doc.ents)}")
            if doc.ents:
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        entities["names"].append(ent.text)
                    elif ent.label_ == "DATE":
                        normalized = normalize_date(ent.text)
                        if normalized:
                            entities["dates"].append(normalized)
            else:
                print("No entities detected by NER. Relying on keyword and database-based extraction.")
        except Exception as e:
            print(f"Error processing query with spaCy: {e}. Falling back to keyword-based extraction.")

    # Keyword-based intent detection (primary method)
    query_lower = query.lower()
    intent_keywords = {
        "list": ["show", "display", "list", "get", "find"],
        "count": ["how many", "count"],
        "sum": ["total", "sum", "how many hours", "average", "avg"],
        "filter": ["where", "for", "in", "by"]
    }
    for intent, keywords in intent_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            entities["intent"] = intent
            entities["keywords"].extend([k for k in keywords if k in query_lower])
            entities["is_database_related"] = True
            break

    # Database-based name extraction
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
            except Exception as e:
                print(f"Failed to query {schema}.{table}.{col_name}: {e}")

    # Vector store suggestions
    if vector_store:
        schema_docs = vector_store.similarity_search(query, k=3)
        for doc in schema_docs:
            table_info = doc.metadata
            if table_info.get("type") == "schema":
                entities["suggested_tables"].append(f"{table_info['schema']}.{table_info['table']}")
                entities["is_database_related"] = True

    return entities