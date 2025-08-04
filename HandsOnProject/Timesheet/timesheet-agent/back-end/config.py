from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()

MSSQL_CONNECTION_BASE = os.getenv("MSSQL_CONNECTION")
DEFAULT_DATABASE = os.getenv("DEFAULT_DATABASE", "TimesheetDB")

if not MSSQL_CONNECTION_BASE:
    raise ValueError("MSSQL_CONNECTION environment variable is required")

# Initialize with default database
MSSQL_CONNECTION = f"{MSSQL_CONNECTION_BASE};DATABASE={DEFAULT_DATABASE}"
CURRENT_DATABASE = DEFAULT_DATABASE

def update_mssql_connection(database_name):
    global MSSQL_CONNECTION, CURRENT_DATABASE
    
    if not database_name:
        # Use default database
        database_name = DEFAULT_DATABASE
        print(f"Using default database: {database_name}")
    else:
        print(f"Switching to database: {database_name}")

    # Build new connection string
    parts = MSSQL_CONNECTION_BASE.split(';')
    new_parts = []
    database_found = False
    
    for part in parts:
        if part.strip().upper().startswith('DATABASE='):
            new_parts.append(f'DATABASE={database_name}')
            database_found = True
        elif part.strip():  # Only add non-empty parts
            new_parts.append(part.strip())
    
    if not database_found:
        new_parts.append(f'DATABASE={database_name}')

    MSSQL_CONNECTION = ";".join(new_parts)
    CURRENT_DATABASE = database_name
    
    print(f"Connection string updated for database: {database_name}")
    return MSSQL_CONNECTION

def get_current_database():
    """Get the currently configured database name"""
    return CURRENT_DATABASE

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral:7b")
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "../vector_data")
VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION", "schema_embeddings")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
USE_LIVE_DB = os.getenv("USE_LIVE_DB", "False").lower() == "true"
EXCLUDE_TABLE_PATTERNS = [
    r"staging",
    r"audit",
    r"error",
    r"log",
    r"temp",
    r"backup",
    r"sys"
]

def ensure_cache_dir():
    """Ensures that the cache directory exists."""
    os.makedirs('cache', exist_ok=True)

def get_schema_cache_file():
    """Get database-specific schema cache file name"""
    ensure_cache_dir()
    return f"cache/schema_cache_{CURRENT_DATABASE}.json"

def get_column_map_file():
    """Get database-specific column map file name"""
    ensure_cache_dir()
    return f"cache/column_map_{CURRENT_DATABASE}.json"

def get_enhanced_schema_cache_file():
    """Get database-specific enhanced schema cache file name"""
    ensure_cache_dir()
    return f"cache/enhanced_schema_cache_{CURRENT_DATABASE}.json"
