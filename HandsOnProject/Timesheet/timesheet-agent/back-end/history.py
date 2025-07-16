import json
import os
from datetime import datetime
from typing import List, Dict, Optional

HISTORY_FILE = "query_history.json"

def save_query(nl_query: str, sql_query: Optional[str], timestamp: str, success: bool, error: Optional[str] = None):
    history = get_query_history()
    entry = {
        "timestamp": timestamp,
        "natural_language_query": nl_query,
        "sql_query": sql_query,
        "success": success,
        "error": error
    }
    history.append(entry)
    
    if len(history) > 100:
        history = history[-100:]
    
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving query history: {e}")

def get_query_history() -> List[Dict]:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading query history: {e}")
    return []
