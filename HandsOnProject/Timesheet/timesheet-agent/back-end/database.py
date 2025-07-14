from sqlalchemy import create_engine, inspect, text
from config import MSSQL_CONNECTION, CHROMADB_DIR, CHROMADB_COLLECTION, OLLAMA_BASE_URL, LLM_MODEL, EXCLUDE_TABLE_PATTERNS
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import os
import chromadb
import json
import re

def get_engine():
    try:
        return create_engine(MSSQL_CONNECTION, echo=False)
    except Exception as e:
        print(f"Failed to create database engine: {e}")
        raise

def initialize_vector_store():
    try:
        chromadb.config.Settings(anonymized_telemetry=False)
        embeddings = OllamaEmbeddings(model=LLM_MODEL, base_url=OLLAMA_BASE_URL)
        return Chroma(
            collection_name=CHROMADB_COLLECTION,
            embedding_function=embeddings,
            persist_directory=CHROMADB_DIR
        )
    except Exception as e:
        print(f"Vector store initialization warning: {e}")
        return None

def should_exclude_table(table_name, exclude_patterns):
    return any(re.compile(pattern, re.IGNORECASE).search(table_name) for pattern in exclude_patterns)

def get_schema_metadata(schemas=None):
    cache_file = "schema_cache.json"
    column_map_file = "column_map.json"

    if os.path.exists(cache_file) and os.path.exists(column_map_file):
        try:
            with open(cache_file, "r") as f:
                schema_metadata = json.load(f)
            with open(column_map_file, "r") as f:
                column_map = json.load(f)
            vector_store = initialize_vector_store()
            return schema_metadata, column_map, vector_store
        except Exception as e:
            print(f"Failed to load cache: {e}")

    engine = get_engine()
    vector_store = initialize_vector_store()
    schema_metadata = []
    column_map = {}

    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            if schemas is None:
                schemas = [s.schema_name for s in inspector.get_schema_names() if s != "INFORMATION_SCHEMA"]

            for schema in schemas:
                table_names = [t for t in inspector.get_table_names(schema=schema) 
                             if not should_exclude_table(t, EXCLUDE_TABLE_PATTERNS)]
                view_names = inspector.get_view_names(schema=schema)
                table_names.extend(view_names)

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

                    table_metadata = {
                        "schema": schema,
                        "table": table_name,
                        "description": f"Contains data about {table_name.replace('_', ' ')}",
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
                                f"Description: {table_metadata['description']}\n"
                                f"Columns: {column_str}\n"
                                f"Relationships: {rel_str}\n"
                                f"Primary Keys: {pk_str}"
                            )
                            existing = vector_store.get(ids=[f"{schema}_{table_name}"])
                            if not existing['ids']:
                                vector_store.add_texts(
                                    texts=[schema_text],
                                    metadatas=[{
                                        "schema": schema,
                                        "table": table_name,
                                        "type": "schema",
                                        "primary_keys": pk_str
                                    }],
                                    ids=[f"{schema}_{table_name}"]
                                )
                        except Exception as e:
                            print(f"Failed to store schema for {schema}.{table_name}: {e}")

            with open(cache_file, "w") as f:
                json.dump(schema_metadata, f, indent=2)
            with open(column_map_file, "w") as f:
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

    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            conn.commit()
            if query.strip().upper().startswith("SELECT"):
                return result.fetchall(), result.keys()
            return None, None
    except Exception as e:
        print(f"Query execution failed: {e}")
        return None, None

def refresh_schema_cache(schemas=None):
    try:
        for file in ["schema_cache.json", "column_map.json"]:
            if os.path.exists(file):
                os.remove(file)
    except FileNotFoundError:
        pass
    return get_schema_metadata(schemas)
