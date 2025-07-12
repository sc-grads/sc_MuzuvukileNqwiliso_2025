from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()

MSSQL_CONNECTION_RAW = os.getenv("MSSQL_CONNECTION")
MSSQL_CONNECTION = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(MSSQL_CONNECTION_RAW)}"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
CHROMADB_DIR = os.getenv("CHROMADB_DIR")
CHROMADB_COLLECTION = os.getenv("CHROMADB_COLLECTION")
FLASK_PORT = int(os.getenv("FLASK_PORT"))