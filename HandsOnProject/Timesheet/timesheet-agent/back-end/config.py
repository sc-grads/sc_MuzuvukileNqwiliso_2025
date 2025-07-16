from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()

MSSQL_CONNECTION_BASE = os.getenv("MSSQL_CONNECTION")
if not MSSQL_CONNECTION_BASE:
    raise ValueError("MSSQL_CONNECTION environment variable is required")

MSSQL_CONNECTION = MSSQL_CONNECTION_BASE

def update_mssql_connection(database_name):
    global MSSQL_CONNECTION
    if not database_name:
        if 'DATABASE=' not in MSSQL_CONNECTION_BASE.upper():
            raise ValueError("No database specified in command-line or .env file.")
        MSSQL_CONNECTION = MSSQL_CONNECTION_BASE
        print(f"Using default database from .env file.")
        return

    parts = MSSQL_CONNECTION_BASE.split(';')
    new_parts = []
    database_found = False
    for part in parts:
        if part.strip().upper().startswith('DATABASE='):
            new_parts.append(f'DATABASE={database_name}')
            database_found = True
        elif part:
            new_parts.append(part)
    
    if not database_found:
        new_parts.append(f'DATABASE={database_name}')

    MSSQL_CONNECTION = ";".join(new_parts)
    print(f"Connection string updated to use database: {database_name}")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral:7b")
CHROMADB_DIR = os.getenv("CHROMADB_DIR", "./chroma_db")
CHROMADB_COLLECTION = os.getenv("CHROMADB_COLLECTION", "timesheet_schema")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
USE_LIVE_DB = os.getenv("USE_LIVE_DB", "False").lower() == "true"
EXCLUDE_TABLE_PATTERNS = [
    r"staging",
    r"audit",
    r"error",
    r"log",
    r"temp",
    r"backup"
]

SCHEMA_CACHE_FILE = "schema_cache.json"
COLUMN_MAP_FILE = "column_map.json"