import json
import os
from datetime import datetime

HISTORY_FILE = "query_history.json"

def save_query(nl_query, sql_query):
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "natural_language_query": nl_query,
        "sql_query": sql_query
    }
    
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    
    history.append(history_entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def get_query_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []