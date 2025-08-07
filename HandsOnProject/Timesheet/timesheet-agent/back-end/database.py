#!/usr/bin/env python3
"""
Hybrid database module: Fast loading + ChromaDB vectorization + Lazy LLM descriptions
"""

from sqlalchemy import create_engine, inspect, text
from config import (
    VECTOR_STORE_DIR, VECTOR_COLLECTION, OLLAMA_BASE_URL, 
    LLM_MODEL, EXCLUDE_TABLE_PATTERNS, get_schema_cache_file, 
    get_column_map_file, get_enhanced_schema_cache_file, get_current_database
)
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, ChatOllama
import os
import pickle
import json
import re
from typing import Dict, List, Tuple, Optional
import urllib.parse
from collections import defaultdict
import threading
import time

# Disable ChromaDB telemetry
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
os.environ["CHROMA_API_IMPL"] = "chromadb.api.segment.SegmentAPI"

def convert_odbc_to_sqlalchemy_url(odbc_string):
    """Convert ODBC connection string to SQLAlchemy-compatible format using URL encoding."""
    encoded = urllib.parse.quote_plus(odbc_string)
    return f"mssql+pyodbc:///?odbc_connect={encoded}"

def get_engine():
    try:
        from config import MSSQL_CONNECTION
        sqlalchemy_url = convert_odbc_to_sqlalchemy_url(MSSQL_CONNECTION)
        return create_engine(sqlalchemy_url, echo=False)
    except Exception as e:
        print(f"Failed to create database engine: {e}")
        raise

def should_exclude_table(table_name, exclude_patterns):
    return any(re.compile(pattern, re.IGNORECASE).search(table_name) for pattern in exclude_patterns)

def initialize_vector_store():
    """Initialize FAISS vector store with memory-efficient approach"""
    try:
        # Try with a smaller embedding model first
        try:
            embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)
            print(f"Using nomic-embed-text for embeddings (memory efficient)")
        except:
            # Fallback to the main model
            embeddings = OllamaEmbeddings(model=LLM_MODEL, base_url=OLLAMA_BASE_URL)
            print(f"Using {LLM_MODEL} for embeddings")
        
        # Check if existing FAISS index exists
        faiss_index_path = os.path.join(VECTOR_STORE_DIR, "faiss_index")
        
        if os.path.exists(f"{faiss_index_path}.faiss") and os.path.exists(f"{faiss_index_path}.pkl"):
            # Load existing FAISS index
            vector_store = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
            print(f"Existing FAISS vector store loaded")
            return vector_store
        else:
            # Create new FAISS index with dummy data (will be populated later)
            dummy_texts = ["Initializing vector store"]
            dummy_metadatas = [{"type": "init"}]
            
            vector_store = FAISS.from_texts(
                texts=dummy_texts,
                embedding=embeddings,
                metadatas=dummy_metadatas
            )
            
            # Ensure directory exists
            os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
            
            # Save the index
            vector_store.save_local(faiss_index_path)
            print(f"New FAISS vector store created")
            return vector_store
        
    except Exception as e:
        print(f"FAISS vector store initialization failed: {e}")
        print(f"Suggestion: Try using a smaller embedding model or increase system memory")
        return None

def generate_fast_description(schema, table, columns):
    """Generate fast rule-based description without LLM"""
    # Smart pattern recognition for common table types
    table_lower = table.lower()
    col_names = [col['name'].lower() for col in columns]
    
    # Common patterns
    if any(word in table_lower for word in ['employee', 'staff', 'worker', 'person']):
        return f"Employee/staff information table containing {len(columns)} fields including personnel data"
    elif any(word in table_lower for word in ['project', 'task', 'work']):
        return f"Project/task management table with {len(columns)} fields for tracking work activities"
    elif any(word in table_lower for word in ['time', 'hour', 'log', 'entry']):
        return f"Time tracking table with {len(columns)} fields for recording work hours and activities"
    elif any(word in table_lower for word in ['client', 'customer', 'company']):
        return f"Client/customer information table containing {len(columns)} fields for business relationships"
    elif 'id' in col_names and any(word in col_names for word in ['name', 'title', 'description']):
        return f"Reference/lookup table with {len(columns)} fields for {table} data"
    else:
        key_cols = [col['name'] for col in columns[:3]]
        return f"Data table '{table}' in schema '{schema}' with {len(columns)} columns including {', '.join(key_cols)}"

def generate_fast_column_description(column):
    """Generate fast rule-based column description"""
    name = column['name'].lower()
    col_type = column['type'].lower()
    
    # Common patterns
    if name.endswith('_id') or name == 'id':
        return f"Unique identifier for {name.replace('_id', '').replace('id', 'record')}"
    elif 'name' in name:
        return f"Name field storing {col_type} values"
    elif 'date' in name or 'time' in name:
        return f"Date/time field tracking {name.replace('_', ' ')}"
    elif 'email' in name:
        return f"Email address field"
    elif 'phone' in name:
        return f"Phone number field"
    elif 'amount' in name or 'cost' in name or 'price' in name:
        return f"Monetary value field for {name.replace('_', ' ')}"
    elif 'status' in name or 'state' in name:
        return f"Status indicator field"
    elif 'description' in name or 'comment' in name:
        return f"Text description field"
    else:
        return f"Data field '{column['name']}' of type {col_type}"

class LazyLLMDescriptionGenerator:
    """Background LLM description generator that doesn't block schema loading"""
    
    def __init__(self):
        self.pending_descriptions = {}
        self.completed_descriptions = {}
        self.worker_thread = None
        self.running = False
    
    def queue_description(self, key, schema, table, columns, relationships=None):
        """Queue a description for background generation"""
        self.pending_descriptions[key] = {
            'schema': schema,
            'table': table,
            'columns': columns,
            'relationships': relationships
        }
        
        if not self.running:
            self.start_worker()
    
    def start_worker(self):
        """Start background worker thread"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """Background worker that generates descriptions"""
        while self.running and self.pending_descriptions:
            try:
                key, data = next(iter(self.pending_descriptions.items()))
                del self.pending_descriptions[key]
                
                # Generate LLM description
                description = self._generate_llm_description(
                    data['schema'], data['table'], data['columns'], data['relationships']
                )
                self.completed_descriptions[key] = description
                
                # Small delay to prevent overwhelming the LLM
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Background description generation error: {e}")
                time.sleep(1)
        
        self.running = False
    
    def _generate_llm_description(self, schema, table, columns, relationships=None):
        """Generate LLM description (runs in background)"""
        try:
            # Fix LangChain compatibility issue
            from langchain_ollama import ChatOllama
            ChatOllama.model_rebuild()
            llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.3)
            
            col_summary = "\n".join([f"- {col['name']} ({col['type']})" for col in columns[:10]])  # Limit to 10 cols
            rel_summary = "\n".join([
                f"- {r['source_column']} → {r['target_table']}({r['target_column']})" for r in relationships[:5]
            ]) if relationships else "None"

            prompt = f"""Generate a concise one-line description for this database table:

Schema: {schema}
Table: {table}
Key Columns: {col_summary}
Relationships: {rel_summary}

Description:"""

            response = llm.invoke(prompt).content.strip()
            return response

        except Exception as e:
            print(f"LLM description failed for {schema}.{table}: {e}")
            return generate_fast_description(schema, table, columns)
    
    def get_description(self, key, fallback):
        """Get description if ready, otherwise return fallback"""
        return self.completed_descriptions.get(key, fallback)

    def stop(self):
        """Stop the background worker thread"""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5) # Give it some time to finish
            if self.worker_thread.is_alive():
                print("Warning: LazyLLMDescriptionGenerator worker thread did not stop gracefully.")

# Global lazy description generator
lazy_generator = LazyLLMDescriptionGenerator()

def _generate_schema_signature(engine):
    """Generates a unique signature based on the current DB schema."""
    try:
        inspector = inspect(engine)
        schema_elements = []
        excluded_schemas = ["INFORMATION_SCHEMA", "guest", "sys", "db_owner", "db_accessadmin", 
                            "db_securityadmin", "db_ddladmin", "db_backupoperator", 
                            "db_datareader", "db_datawriter", "db_denydatareader", "db_denydatawriter"]
        
        schemas = [s for s in inspector.get_schema_names() if s not in excluded_schemas]
        
        for schema in sorted(schemas):
            for table_name in sorted(inspector.get_table_names(schema=schema)):
                if should_exclude_table(table_name, EXCLUDE_TABLE_PATTERNS):
                    continue
                schema_elements.append(f"{schema}.{table_name}")
                columns = inspector.get_columns(table_name, schema=schema)
                for col in sorted(columns, key=lambda x: x['name']):
                    schema_elements.append(f"{schema}.{table_name}.{col['name']}:{str(col['type'])}")
        
        return str(hash("".join(schema_elements)))
    except Exception as e:
        print(f"Warning: Could not generate schema signature. Cache validation may be incomplete. Error: {e}")
        return None

def get_schema_metadata():
    """Fast schema loading with ChromaDB vectorization and lazy LLM descriptions"""
    cache_file = get_schema_cache_file()
    column_map_file = get_column_map_file()
    enhanced_cache_file = get_enhanced_schema_cache_file()
    business_patterns_file = 'business_patterns.json'
    
    current_db = get_current_database()
    print(f"Using hybrid schema cache for database: {current_db}")
    
    engine = get_engine()
    live_signature = _generate_schema_signature(engine)

    # Load business patterns if available
    business_patterns = {}
    if os.path.exists(business_patterns_file):
        try:
            with open(business_patterns_file, "r") as f:
                patterns_data = json.load(f)
                for pattern in patterns_data.get("patterns", []):
                    business_patterns[pattern['maps_to']] = pattern
            print(f"Loaded {len(business_patterns)} business patterns.")
        except Exception as e:
            print(f"Warning: Could not load business patterns file: {e}")

    # Check cache validity
    if os.path.exists(cache_file) and os.path.exists(column_map_file):
        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)
            
            cached_signature = cached_data.get("schema_signature")

            if live_signature and cached_signature and live_signature == cached_signature:
                print("Schema cache found and valid. Loading from cache...")
                with open(column_map_file, "r") as f:
                    column_map = json.load(f)
                
                if os.path.exists(enhanced_cache_file):
                    with open(enhanced_cache_file, "r") as f:
                        enhanced_data = json.load(f)
                else:
                    enhanced_data = {'business_patterns': [], 'table_priorities': [], 'inferred_relationships': []}
                
                vector_store = initialize_vector_store()
                
                for table in cached_data["metadata"]:
                    key = f"{table['schema']}.{table['table']}"
                    lazy_generator.queue_description(key, table['schema'], table['table'], table['columns'])
                
                return cached_data["metadata"], column_map, vector_store, enhanced_data
            else:
                print("Schema has changed or cache is invalid. Forcing a refresh...")
        except Exception as e:
            print(f"Cache load failed: {e}. Regenerating...")

    print("Fast schema generation with FAISS vectorization...")
    
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
                    print(f"  Processing table: {schema}.{table_name}")
                    
                    columns = inspector.get_columns(table_name, schema=schema)
                    fks = inspector.get_foreign_keys(table_name, schema=schema)
                    pks = inspector.get_pk_constraint(table_name, schema=schema)
                    
                    full_table_name = f"{schema}.{table_name}"
                    table_pattern = business_patterns.get(full_table_name, {})
                    table_business_desc = f"Business context: {table_pattern['term']} - {table_pattern['description']}" if table_pattern else ""

                    col_details = []
                    for col in columns:
                        full_col_name = f"{full_table_name}.{col['name']}"
                        col_pattern = business_patterns.get(full_col_name, {})
                        business_desc = f"Business context: {col_pattern['term']} - {col_pattern['description']}" if col_pattern else ""
                        
                        col_info = {
                            "name": col['name'],
                            "type": str(col["type"]).lower(),
                            "nullable": col.get("nullable", True),
                            "default": str(col["default"]).strip("()") if col.get("default") else None,
                            "primary_key": col['name'] in pks.get('constrained_columns', []),
                            "description": generate_fast_column_description({
                                "name": col['name'], 
                                "type": str(col["type"]).lower()
                            }),
                            "business_description": business_desc
                        }
                        col_details.append(col_info)

                    column_map[full_table_name] = [col["name"] for col in columns]

                    fk_info = []
                    for fk in fks:
                        fk_info.append({
                            "source_column": fk['constrained_columns'][0],
                            "target_table": f"{fk['referred_schema']}.{fk['referred_table']}",
                            "target_column": fk['referred_columns'][0]
                        })

                    fast_description = generate_fast_description(schema, table_name, col_details)
                    
                    table_key = full_table_name
                    lazy_generator.queue_description(table_key, schema, table_name, col_details, fk_info)

                    table_metadata = {
                        "schema": schema,
                        "table": table_name,
                        "description": f"{fast_description} {table_business_desc}".strip(),
                        "columns": col_details,
                        "relationships": fk_info,
                        "primary_keys": pks.get('constrained_columns', []),
                        "sample_query": f"SELECT TOP 5 * FROM [{schema}].[{table_name}]",
                        "inferred_relationships": [],
                        "priority": {
                            "score": 0.5,
                            "business_importance": "medium",
                            "relevance_factors": []
                        }
                    }
                    schema_metadata.append(table_metadata)

                    if vector_store:
                        try:
                            column_str = ', '.join([f"{c['name']} ({c['type']}) - {c.get('business_description', '')}" for c in col_details])
                            pk_str = ', '.join(pks.get('constrained_columns', []))
                            fk_str = ', '.join([f"{fk['source_column']} -> {fk['target_table']}" for fk in fk_info])
                            
                            schema_text = (
                                f"Table: {full_table_name}\n"
                                f"Description: {table_metadata['description']}\n"
                                f"Columns: {column_str}\n"
                                f"Primary Keys: {pk_str}\n"
                                f"Foreign Keys: {fk_str}"
                            )
                            
                            vector_store.add_texts(
                                texts=[schema_text],
                                metadatas=[{
                                    'type': 'schema',
                                    'schema': schema,
                                    'table': table_name,
                                    'full_name': full_table_name
                                }]
                            )
                            
                        except Exception as e:
                            print(f"   Vector store add failed for {full_table_name}: {e}")

        # Enhanced data structure
        enhanced_data = {
            'business_patterns': [],
            'table_priorities': [
                {
                    'table_name': table['table'],
                    'schema_name': table['schema'],
                    'priority_score': 0.5,
                    'business_importance': 'medium',
                    'relevance_factors': []
                }
                for table in schema_metadata
            ],
            'inferred_relationships': []
        }

        # Save cache
        cache_data = {"schema_signature": live_signature, "metadata": schema_metadata}
        
        try:
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            with open(column_map_file, "w") as f:
                json.dump(column_map, f, indent=2)
            # with open(enhanced_cache_file, "w") as f:
            #     json.dump(enhanced_data, f, indent=2)
            
            print(f"Hybrid cache saved successfully")
            
        except Exception as e:
            print(f"Cache save failed: {e}")

        # Save the updated FAISS vector store
        if vector_store:
            try:
                faiss_index_path = os.path.join(VECTOR_STORE_DIR, "faiss_index")
                vector_store.save_local(faiss_index_path)
                print(f"FAISS vector store saved with {len(schema_metadata)} tables")
            except Exception as e:
                print(f"Failed to save FAISS index: {e}")

        print(f"Schema loaded: {len(schema_metadata)} tables with FAISS vectorization")
        return schema_metadata, column_map, vector_store, enhanced_data

    except Exception as e:
        print(f"Schema generation error: {e}")
        return [], {}, vector_store, {'business_patterns': [], 'table_priorities': [], 'inferred_relationships': []}

def execute_query(query):
    """Execute SQL query and return results in expected format: (rows, columns, error)"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(query))
            
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())
                
                data = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    data.append(row_dict)
                
                return data, columns, None
            else:
                return [], [], None
                
    except Exception as e:
        return [], [], str(e)

def refresh_schema_cache():
    """Refresh schema cache and regenerate enhanced metadata"""
    try:
        cache_files = [
            get_schema_cache_file(),
            get_column_map_file(),
            get_enhanced_schema_cache_file()
        ]
        
        current_db = get_current_database()
        print(f"Refreshing hybrid cache for database: {current_db}")
        
        for file in cache_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"   Removed: {file}")
                
    except FileNotFoundError:
        pass
    
    return get_schema_metadata()

def get_enhanced_description(schema, table):
    """Get enhanced LLM description if available, otherwise return fast description"""
    key = f"{schema}.{table}"
    # This will be populated by the background thread
    return lazy_generator.get_description(key, None)