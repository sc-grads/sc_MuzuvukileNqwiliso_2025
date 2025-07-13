from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()

MSSQL_CONNECTION_RAW = os.getenv("MSSQL_CONNECTION")
if not MSSQL_CONNECTION_RAW:
    raise ValueError("MSSQL_CONNECTION environment variable is required")

MSSQL_CONNECTION = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(MSSQL_CONNECTION_RAW)}"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral:7b")
CHROMADB_DIR = os.getenv("CHROMADB_DIR", "./chroma_db")
CHROMADB_COLLECTION = os.getenv("CHROMADB_COLLECTION", "timesheet_schema")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

EXCLUDE_TABLE_PATTERNS = [
    r"staging",
    r"audit",
    r"error",
    r"log",
    r"temp",
    r"backup"
]