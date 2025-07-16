from sqlalchemy import create_engine, inspect, text
from config import (
    MSSQL_CONNECTION, CHROMADB_DIR, CHROMADB_COLLECTION, 
    OLLAMA_BASE_URL, LLM_MODEL, EXCLUDE_TABLE_PATTERNS,
    SCHEMA_CACHE_FILE, COLUMN_MAP_FILE
)
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
import os
import chromadb
import json
import re
import urllib.parse

os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

def convert_odbc_to_sqlalchemy_url(odbc_string):
    encoded = urllib.parse.quote_plus(odbc_string)
    return f"mssql+pyodbc:///?odbc_connect={encoded}"

def get_engine():
    try:
        sqlalchemy_url = convert_odbc_to_sqlalchemy_url(MSSQL_CONNECTION)
        return create_engine(sqlalchemy_url, echo=False)
    except Exception as e:
        print(f"Failed to create database engine: {e}")
        raise

def initialize_vector_store():
    try:
        settings = chromadb.Settings(allow_reset=True, is_persistent=True, anonymized_telemetry=False)
        embeddings = OllamaEmbeddings(model=LLM_MODEL, base_url=OLLAMA_BASE_URL)
        return Chroma(
            collection_name=CHROMADB_COLLECTION,
            embedding_function=embeddings,
            persist_directory=CHROMADB_DIR,
            client_settings=settings
        )
    except Exception as e:
        print(f"Vector store initialization warning: {e}")
        return None

def should_exclude_table(table_name, exclude_patterns):
    return any(re.compile(pattern, re.IGNORECASE).search(table_name) for pattern in exclude_patterns)

def generate_llm_description(schema, table, columns, relationships=None):
    try:
        llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.3)
        col_summary = "\n".join([f"- {col['name']} ({col['type']})" for col in columns])
        rel_summary = "\n".join([
            f"- {r['source_column']} → {r['target_table']}({r['target_column']})" for r in relationships
        ]) if relationships else "None"
        prompt = f"""
        You are a helpful database assistant. Given the following table and column information, generate a one-line human-readable description of what this table likely stores.

        Schema: {schema}
        Table: {table}
        Columns:
        {col_summary}
        Foreign Keys:
        {rel_summary}

        Description:
        """
        response = llm.invoke(prompt).content.strip()
        return response
    except Exception as e:
        print(f"Failed to generate LLM description for {schema}.{table}: {e}")
        return f"A table named {table} with fields like {', '.join([c['name'] for c in columns[:3]])}."

def get_schema_metadata():
    cache_key = hash(MSSQL_CONNECTION)
    if os.path.exists(SCHEMA_CACHE_FILE) and os.path.exists(COLUMN_MAP_FILE):
        try:
            with open(SCHEMA_CACHE_FILE, "r") as f:
                cached_data = json.load(f)
            if cached_data.get("cache_key") == cache_key:
                with open(COLUMN_MAP_FILE, "r") as f:
                    column_map = json.load(f)
                vector_store = initialize_vector_store()
                return cached_data["metadata"], column_map, vector_store
        except Exception as e:
            print(f"Failed to load cache: {e}")

    engine = get_engine()
    vector_store = initialize_vector_store()
    schema_metadata = []
    column_map = {}

    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            excluded_schemas = ["INFORMATION_SCHEMA", "guest", "sys", "db_owner", "db_accessadmin", 
                                "db_securityadmin", "db_ddladmin", "db_backupoperator", 
                                "db_datareader", "db_datawriter", "db_denydatareader", "db_denydatawriter"]
            schemas = [s for s in inspector.get_schema_names() if s not in excluded_schemas]
            for schema in schemas:
                table_names = [t for t in inspector.get_table_names(schema=schema)
                               if not should_exclude_table(t, EXCLUDE_TABLE_PATTERNS)]
                for table_name in table_names:
                    columns = inspector.get_columns(table_name, schema=schema)
                    fks = inspector.get_foreign_keys(table_name, schema=schema)
                    pks = inspector.get_pk_constraint(table_name, schema=schema)
                    col_details = [
                        {
                            "name": col['name'],
                            "type": str(col["type"]).lower(),
                            "nullable": col.get("nullable", True),
                            "default": str(col["default"]).strip("()") if col.get("default") else None,
                            "primary_key": col['name'] in pks.get('constrained_columns', [])
                        } for col in columns
                    ]
                    column_map[f"{schema}.{table_name}"] = [col["name"] for col in columns]
                    fk_info = [
                        {
                            "source_column": fk['constrained_columns'][0],
                            "target_table": f"{fk['referred_schema']}.{fk['referred_table']}",
                            "target_column": fk['referred_columns'][0]
                        } for fk in fks
                    ]
                    description = generate_llm_description(schema, table_name, col_details, fk_info)
                    table_metadata = {
                        "schema": schema,
                        "table": table_name,
                        "description": description,
                        "columns": col_details,
                        "relationships": fk_info,
                        "primary_keys": pks.get('constrained_columns', []),
                        "sample_query": f"SELECT TOP 5 * FROM [{schema}].[{table_name}]"
                    }
                    schema_metadata.append(table_metadata)
                    if vector_store:
                        try:
                            column_str = ', '.join([f"{c['name']} ({c['type']})" for c in col_details])
                            rel_str = ', '.join([f"{fk['source_column']} -> {fk['target_table']}.{fk['target_column']}" for fk in fk_info]) or 'None'
                            pk_str = ', '.join(pks.get('constrained_columns', [])) or 'None'
                            schema_text = (
                                f"Schema: {schema}\n"
                                f"Table: {table_name}\n"
                                f"Description: {description}\n"
                                f"Columns: {column_str}\n"
                                f"Relationships: {rel_str}\n"
                                f"Primary Keys: {pk_str}"
                            )
                            existing = vector_store.get(ids=[f"{schema}_{table_name}"])
                            if not existing['ids']:
                                vector_store.add_texts(
                                    texts=[schema_text],
                                    metadatas=[
                                        {
                                            "schema": schema,
                                            "table": table_name,
                                            "type": "schema",
                                            "primary_keys": pk_str
                                        }
                                    ],
                                    ids=[f"{schema}_{table_name}"]
                                )
                        except Exception as e:
                            print(f"Failed to store schema for {schema}.{table_name}: {e}")
            with open(SCHEMA_CACHE_FILE, "w") as f:
                json.dump({"cache_key": cache_key, "metadata": schema_metadata}, f, indent=2)
            with open(COLUMN_MAP_FILE, "w") as f:
                json.dump(column_map, f, indent=2)
            return schema_metadata, column_map, vector_store
    except Exception as e:
        print(f"Failed to retrieve schema: {e}")
        return [], {}, vector_store

def execute_query(query):
    try:
        engine = get_engine()
        with engine.connect().execution_options(stream_results=True) as conn:
            result = conn.execute(text(query))
            if query.strip().upper().startswith("SELECT"):
                rows = result.fetchall()
                columns = result.keys()
                return rows, columns
            return None, None
    except Exception as e:
        print(f"Query execution failed: {e}")
        return None, None

def refresh_schema_cache():
    try:
        for file in [SCHEMA_CACHE_FILE, COLUMN_MAP_FILE]:
            if os.path.exists(file):
                os.remove(file)
    except FileNotFoundError as e:
        print(f"Warning: Cache file not found during refresh: {e}")
    return get_schema_metadata()