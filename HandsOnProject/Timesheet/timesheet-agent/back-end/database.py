from sqlalchemy import create_engine, inspect, text
from config import (
    CHROMADB_DIR, CHROMADB_COLLECTION, OLLAMA_BASE_URL, 
    LLM_MODEL, EXCLUDE_TABLE_PATTERNS, get_schema_cache_file, 
    get_column_map_file, get_enhanced_schema_cache_file, get_current_database
)
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
import os
import chromadb
import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
os.environ["CHROMA_API_IMPL"] = "chromadb.api.segment.SegmentAPI"

import urllib.parse

@dataclass
class BusinessPattern:
    """Represents a detected business pattern in database columns"""
    pattern_type: str  # 'name', 'date', 'amount', 'identifier', 'status', 'description'
    confidence: float  # 0.0 to 1.0
    column_name: str
    table_name: str
    schema_name: str
    semantic_meaning: str

@dataclass
class TableRelationship:
    """Enhanced relationship information between tables"""
    source_table: str
    target_table: str
    source_column: str
    target_column: str
    relationship_type: str  # 'one_to_many', 'many_to_one', 'many_to_many', 'one_to_one'
    confidence: float
    semantic_meaning: str

@dataclass
class TablePriority:
    """Table prioritization for query context"""
    table_name: str
    schema_name: str
    priority_score: float
    relevance_factors: List[str]
    business_importance: str  # 'high', 'medium', 'low'

class BusinessPatternDetector:
    """Detects common business patterns in database columns"""
    
    def __init__(self):
        # Pattern definitions for common business entities
        self.name_patterns = [
            r'.*name.*', r'.*title.*', r'.*label.*', r'.*description.*',
            r'first.*name', r'last.*name', r'full.*name', r'display.*name'
        ]
        
        self.date_patterns = [
            r'.*date.*', r'.*time.*', r'.*created.*', r'.*modified.*', r'.*updated.*',
            r'.*start.*', r'.*end.*', r'.*begin.*', r'.*finish.*', r'.*due.*',
            r'.*birth.*', r'.*hire.*', r'.*term.*', r'.*expire.*'
        ]
        
        self.amount_patterns = [
            r'.*amount.*', r'.*price.*', r'.*cost.*', r'.*total.*', r'.*sum.*',
            r'.*value.*', r'.*rate.*', r'.*salary.*', r'.*wage.*', r'.*fee.*',
            r'.*balance.*', r'.*payment.*', r'.*charge.*', r'.*revenue.*'
        ]
        
        self.identifier_patterns = [
            r'.*id$', r'.*key$', r'.*code.*', r'.*number.*', r'.*ref.*',
            r'.*guid.*', r'.*uuid.*', r'pk_.*', r'fk_.*'
        ]
        
        self.status_patterns = [
            r'.*status.*', r'.*state.*', r'.*flag.*', r'.*active.*',
            r'.*enabled.*', r'.*deleted.*', r'.*archived.*', r'is_.*'
        ]

    def detect_patterns(self, column_name: str, data_type: str, table_name: str, schema_name: str) -> List[BusinessPattern]:
        """Detect business patterns for a given column"""
        patterns = []
        col_lower = column_name.lower()
        type_lower = data_type.lower()
        
        # Name pattern detection
        if any(re.match(pattern, col_lower, re.IGNORECASE) for pattern in self.name_patterns):
            if 'varchar' in type_lower or 'nvarchar' in type_lower or 'text' in type_lower:
                confidence = 0.9 if 'name' in col_lower else 0.7
                patterns.append(BusinessPattern(
                    pattern_type='name',
                    confidence=confidence,
                    column_name=column_name,
                    table_name=table_name,
                    schema_name=schema_name,
                    semantic_meaning=f"Likely stores human-readable names or labels"
                ))
        
        # Date pattern detection
        if any(re.match(pattern, col_lower, re.IGNORECASE) for pattern in self.date_patterns):
            if 'date' in type_lower or 'time' in type_lower:
                confidence = 0.95
            elif 'varchar' in type_lower and ('date' in col_lower or 'time' in col_lower):
                confidence = 0.8
            else:
                confidence = 0.6
            
            patterns.append(BusinessPattern(
                pattern_type='date',
                confidence=confidence,
                column_name=column_name,
                table_name=table_name,
                schema_name=schema_name,
                semantic_meaning=f"Likely stores temporal information"
            ))
        
        # Amount pattern detection
        if any(re.match(pattern, col_lower, re.IGNORECASE) for pattern in self.amount_patterns):
            if 'decimal' in type_lower or 'money' in type_lower or 'float' in type_lower:
                confidence = 0.9
            elif 'int' in type_lower:
                confidence = 0.7
            else:
                confidence = 0.5
            
            patterns.append(BusinessPattern(
                pattern_type='amount',
                confidence=confidence,
                column_name=column_name,
                table_name=table_name,
                schema_name=schema_name,
                semantic_meaning=f"Likely stores monetary or numeric values"
            ))
        
        # Identifier pattern detection
        if any(re.match(pattern, col_lower, re.IGNORECASE) for pattern in self.identifier_patterns):
            if 'int' in type_lower or 'guid' in type_lower or 'uuid' in type_lower:
                confidence = 0.95
            else:
                confidence = 0.8
            
            patterns.append(BusinessPattern(
                pattern_type='identifier',
                confidence=confidence,
                column_name=column_name,
                table_name=table_name,
                schema_name=schema_name,
                semantic_meaning=f"Likely serves as a unique identifier or reference"
            ))
        
        # Status pattern detection
        if any(re.match(pattern, col_lower, re.IGNORECASE) for pattern in self.status_patterns):
            if 'bit' in type_lower or 'boolean' in type_lower:
                confidence = 0.9
            elif 'varchar' in type_lower or 'char' in type_lower:
                confidence = 0.8
            else:
                confidence = 0.6
            
            patterns.append(BusinessPattern(
                pattern_type='status',
                confidence=confidence,
                column_name=column_name,
                table_name=table_name,
                schema_name=schema_name,
                semantic_meaning=f"Likely indicates state or condition"
            ))
        
        return patterns

class RelationshipInferencer:
    """Infers relationships between tables beyond explicit foreign keys"""
    
    def __init__(self):
        self.common_join_patterns = [
            ('id', 'id'), ('key', 'key'), ('code', 'code'),
            ('number', 'number'), ('ref', 'ref')
        ]

    def infer_relationships(self, schema_metadata: List[Dict]) -> List[TableRelationship]:
        """Infer implicit relationships between tables"""
        relationships = []
        
        # Create lookup for tables and their columns
        table_columns = {}
        for table in schema_metadata:
            full_name = f"{table['schema']}.{table['table']}"
            table_columns[full_name] = {
                'columns': {col['name'].lower(): col for col in table['columns']},
                'metadata': table
            }
        
        # Look for naming pattern relationships
        for source_table, source_data in table_columns.items():
            for target_table, target_data in table_columns.items():
                if source_table == target_table:
                    continue
                
                # Check for common naming patterns
                for source_col_name, source_col in source_data['columns'].items():
                    for target_col_name, target_col in target_data['columns'].items():
                        
                        # Skip if already has explicit FK relationship
                        existing_fk = any(
                            fk['source_column'].lower() == source_col_name and 
                            fk['target_table'].lower() == target_table.lower()
                            for fk in source_data['metadata']['relationships']
                        )
                        if existing_fk:
                            continue
                        
                        # Check for naming pattern matches
                        confidence = self._calculate_relationship_confidence(
                            source_col_name, target_col_name,
                            source_col['type'], target_col['type'],
                            source_table, target_table
                        )
                        
                        if confidence > 0.6:
                            relationship_type = self._determine_relationship_type(
                                source_col, target_col, source_data, target_data
                            )
                            
                            relationships.append(TableRelationship(
                                source_table=source_table,
                                target_table=target_table,
                                source_column=source_col['name'],
                                target_column=target_col['name'],
                                relationship_type=relationship_type,
                                confidence=confidence,
                                semantic_meaning=f"Inferred relationship based on column naming patterns"
                            ))
        
        return relationships

    def _calculate_relationship_confidence(self, source_col: str, target_col: str, 
                                         source_type: str, target_type: str,
                                         source_table: str, target_table: str) -> float:
        """Calculate confidence score for potential relationship"""
        confidence = 0.0
        
        # Exact name match
        if source_col == target_col:
            confidence += 0.4
        
        # Similar naming patterns
        if source_col.endswith('_id') and target_col == 'id':
            confidence += 0.3
        elif source_col.endswith('_key') and target_col == 'key':
            confidence += 0.3
        elif source_col.replace('_', '') == target_col.replace('_', ''):
            confidence += 0.2
        
        # Type compatibility
        if source_type == target_type:
            confidence += 0.2
        elif ('int' in source_type and 'int' in target_type) or \
             ('varchar' in source_type and 'varchar' in target_type):
            confidence += 0.1
        
        # Table name hints
        source_table_name = source_table.split('.')[-1].lower()
        target_table_name = target_table.split('.')[-1].lower()
        
        if source_col.lower().startswith(target_table_name):
            confidence += 0.2
        elif target_col.lower().startswith(source_table_name):
            confidence += 0.2
        
        return min(confidence, 1.0)

    def _determine_relationship_type(self, source_col: Dict, target_col: Dict,
                                   source_data: Dict, target_data: Dict) -> str:
        """Determine the type of relationship"""
        # Check if source column is primary key
        source_is_pk = source_col.get('primary_key', False)
        target_is_pk = target_col.get('primary_key', False)
        
        if target_is_pk and not source_is_pk:
            return 'many_to_one'
        elif source_is_pk and not target_is_pk:
            return 'one_to_many'
        elif source_is_pk and target_is_pk:
            return 'one_to_one'
        else:
            return 'many_to_many'

class TablePrioritizer:
    """Prioritizes tables based on query context and business importance"""
    
    def __init__(self):
        # Common important table patterns
        self.high_priority_patterns = [
            r'.*user.*', r'.*customer.*', r'.*employee.*', r'.*person.*',
            r'.*order.*', r'.*transaction.*', r'.*payment.*', r'.*invoice.*',
            r'.*product.*', r'.*item.*', r'.*project.*', r'.*task.*'
        ]
        
        self.medium_priority_patterns = [
            r'.*detail.*', r'.*line.*', r'.*entry.*', r'.*record.*',
            r'.*log.*', r'.*history.*', r'.*audit.*'
        ]
        
        self.low_priority_patterns = [
            r'.*lookup.*', r'.*reference.*', r'.*config.*', r'.*setting.*',
            r'.*temp.*', r'.*staging.*', r'.*backup.*'
        ]

    def prioritize_tables(self, schema_metadata: List[Dict], 
                         business_patterns: List[BusinessPattern],
                         query_context: Optional[str] = None) -> List[TablePriority]:
        """Prioritize tables based on various factors"""
        priorities = []
        
        for table in schema_metadata:
            full_name = f"{table['schema']}.{table['table']}"
            table_name = table['table'].lower()
            
            # Base priority calculation
            priority_score = self._calculate_base_priority(table_name)
            relevance_factors = []
            
            # Adjust based on business patterns
            table_patterns = [p for p in business_patterns 
                            if p.table_name == table['table'] and p.schema_name == table['schema']]
            
            pattern_bonus = self._calculate_pattern_bonus(table_patterns)
            priority_score += pattern_bonus
            if pattern_bonus > 0:
                relevance_factors.append(f"Contains {len(table_patterns)} business patterns")
            
            # Adjust based on relationships
            relationship_bonus = len(table['relationships']) * 0.1
            priority_score += relationship_bonus
            if relationship_bonus > 0:
                relevance_factors.append(f"Has {len(table['relationships'])} relationships")
            
            # Adjust based on column count (more columns = more important)
            column_bonus = min(len(table['columns']) * 0.02, 0.2)
            priority_score += column_bonus
            
            # Query context relevance
            if query_context:
                context_bonus = self._calculate_context_relevance(table_name, query_context)
                priority_score += context_bonus
                if context_bonus > 0:
                    relevance_factors.append("Relevant to query context")
            
            # Determine business importance
            if priority_score >= 0.8:
                business_importance = 'high'
            elif priority_score >= 0.5:
                business_importance = 'medium'
            else:
                business_importance = 'low'
            
            priorities.append(TablePriority(
                table_name=table['table'],
                schema_name=table['schema'],
                priority_score=min(priority_score, 1.0),
                relevance_factors=relevance_factors,
                business_importance=business_importance
            ))
        
        return sorted(priorities, key=lambda x: x.priority_score, reverse=True)

    def _calculate_base_priority(self, table_name: str) -> float:
        """Calculate base priority based on table name patterns"""
        if any(re.match(pattern, table_name, re.IGNORECASE) for pattern in self.high_priority_patterns):
            return 0.7
        elif any(re.match(pattern, table_name, re.IGNORECASE) for pattern in self.medium_priority_patterns):
            return 0.5
        elif any(re.match(pattern, table_name, re.IGNORECASE) for pattern in self.low_priority_patterns):
            return 0.2
        else:
            return 0.4  # Default priority

    def _calculate_pattern_bonus(self, patterns: List[BusinessPattern]) -> float:
        """Calculate bonus based on business patterns"""
        if not patterns:
            return 0.0
        
        # Weight patterns by confidence and importance
        pattern_weights = {
            'identifier': 0.1,
            'name': 0.15,
            'date': 0.2,
            'amount': 0.25,
            'status': 0.1
        }
        
        total_bonus = 0.0
        for pattern in patterns:
            weight = pattern_weights.get(pattern.pattern_type, 0.1)
            total_bonus += weight * pattern.confidence
        
        return min(total_bonus, 0.3)  # Cap at 0.3

    def _calculate_context_relevance(self, table_name: str, query_context: str) -> float:
        """Calculate relevance based on query context"""
        if not query_context:
            return 0.0
        
        context_lower = query_context.lower()
        table_lower = table_name.lower()
        
        # Direct name match
        if table_lower in context_lower or any(word in context_lower for word in table_lower.split('_')):
            return 0.3
        
        # Semantic similarity (simplified)
        common_words = set(context_lower.split()) & set(table_lower.split('_'))
        if common_words:
            return len(common_words) * 0.1
        
        return 0.0

def convert_odbc_to_sqlalchemy_url(odbc_string):
    """Convert ODBC connection string to SQLAlchemy-compatible format using URL encoding."""
    encoded = urllib.parse.quote_plus(odbc_string)
    return f"mssql+pyodbc:///?odbc_connect={encoded}"


def get_engine():
    try:
        # Import connection string dynamically to get updated value
        from config import MSSQL_CONNECTION
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

def generate_column_description(column, relationships):
    try:
        llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.3)
        rel_summary = "\n".join([
            f"- {r['source_column']} → {r['target_table']}({r['target_column']})" for r in relationships
            if r['source_column'] == column['name']
        ]) if relationships else "None"

        prompt = f"""
        You are a database assistant. Given the following column information, generate a one-line human-readable description of its purpose.

        Column Name: {column['name']}
        Data Type: {column['type']}
        Relationships:
        {rel_summary}

        Description:
        """

        response = llm.invoke(prompt).content.strip()
        return response

    except Exception as e:
        print(f"Failed to generate description for column {column['name']}: {e}")
        return f"A column named {column['name']} of type {column['type']}."

def get_schema_metadata():
    # Use database-specific cache files
    cache_file = get_schema_cache_file()
    column_map_file = get_column_map_file()
    enhanced_cache_file = get_enhanced_schema_cache_file()
    
    current_db = get_current_database()
    print(f"📊 Using schema cache for database: {current_db}")
    
    # Import connection string dynamically to get updated value
    from config import MSSQL_CONNECTION
    cache_key = hash(MSSQL_CONNECTION)  

    if os.path.exists(cache_file) and os.path.exists(column_map_file) and os.path.exists(enhanced_cache_file):
        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)
            if cached_data.get("cache_key") == cache_key:
                print("Schema cache found and valid. Loading from cache...")
                with open(column_map_file, "r") as f:
                    column_map = json.load(f)
                with open(enhanced_cache_file, "r") as f:
                    enhanced_data = json.load(f)
                vector_store = initialize_vector_store()
                return cached_data["metadata"], column_map, vector_store, enhanced_data
            else:
                print("Schema cache found but invalid (connection string changed). Regenerating...")
        except Exception as e:
            print(f"Failed to load cache: {e}. Regenerating schema...")

    print("Generating enhanced schema metadata from database...")

    engine = get_engine()
    vector_store = initialize_vector_store()
    schema_metadata = []
    column_map = {}
    
    # Initialize enhanced analysis components
    pattern_detector = BusinessPatternDetector()
    relationship_inferencer = RelationshipInferencer()
    table_prioritizer = TablePrioritizer()

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
                            "primary_key": col['name'] in pks.get('constrained_columns', []),
                            "description": generate_column_description(
                                {"name": col['name'], "type": str(col["type"]).lower()},
                                [
                                    {
                                        "source_column": fk['constrained_columns'][0],
                                        "target_table": f"{fk['referred_schema']}.{fk['referred_table']}",
                                        "target_column": fk['referred_columns'][0]
                                    }
                                    for fk in fks if fk['constrained_columns'][0] == col['name']
                                ]
                            )
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

            # Perform enhanced analysis after collecting all schema metadata
            print("Performing enhanced schema analysis...")
            
            # Detect business patterns for all columns
            all_business_patterns = []
            for table in schema_metadata:
                for column in table['columns']:
                    patterns = pattern_detector.detect_patterns(
                        column['name'], 
                        column['type'], 
                        table['table'], 
                        table['schema']
                    )
                    all_business_patterns.extend(patterns)
                    
                    # Add pattern information to column metadata
                    column['business_patterns'] = [
                        {
                            'type': p.pattern_type,
                            'confidence': p.confidence,
                            'semantic_meaning': p.semantic_meaning
                        } for p in patterns
                    ]
            
            # Infer additional relationships
            inferred_relationships = relationship_inferencer.infer_relationships(schema_metadata)
            
            # Add inferred relationships to table metadata
            for table in schema_metadata:
                table_name = f"{table['schema']}.{table['table']}"
                table_inferred_rels = [
                    {
                        'source_column': rel.source_column,
                        'target_table': rel.target_table,
                        'target_column': rel.target_column,
                        'relationship_type': rel.relationship_type,
                        'confidence': rel.confidence,
                        'semantic_meaning': rel.semantic_meaning,
                        'inferred': True
                    }
                    for rel in inferred_relationships 
                    if rel.source_table == table_name
                ]
                table['inferred_relationships'] = table_inferred_rels
            
            # Calculate table priorities
            table_priorities = table_prioritizer.prioritize_tables(
                schema_metadata, 
                all_business_patterns
            )
            
            # Add priority information to table metadata
            priority_map = {f"{p.schema_name}.{p.table_name}": p for p in table_priorities}
            for table in schema_metadata:
                table_key = f"{table['schema']}.{table['table']}"
                if table_key in priority_map:
                    priority = priority_map[table_key]
                    table['priority'] = {
                        'score': priority.priority_score,
                        'business_importance': priority.business_importance,
                        'relevance_factors': priority.relevance_factors
                    }
                else:
                    table['priority'] = {
                        'score': 0.4,
                        'business_importance': 'medium',
                        'relevance_factors': []
                    }
            
            # Create enhanced data structure
            enhanced_data = {
                'business_patterns': [
                    {
                        'pattern_type': p.pattern_type,
                        'confidence': p.confidence,
                        'column_name': p.column_name,
                        'table_name': p.table_name,
                        'schema_name': p.schema_name,
                        'semantic_meaning': p.semantic_meaning
                    } for p in all_business_patterns
                ],
                'inferred_relationships': [
                    {
                        'source_table': rel.source_table,
                        'target_table': rel.target_table,
                        'source_column': rel.source_column,
                        'target_column': rel.target_column,
                        'relationship_type': rel.relationship_type,
                        'confidence': rel.confidence,
                        'semantic_meaning': rel.semantic_meaning
                    } for rel in inferred_relationships
                ],
                'table_priorities': [
                    {
                        'table_name': p.table_name,
                        'schema_name': p.schema_name,
                        'priority_score': p.priority_score,
                        'business_importance': p.business_importance,
                        'relevance_factors': p.relevance_factors
                    } for p in table_priorities
                ]
            }
            
            # Save all cache files
            with open(cache_file, "w") as f:
                json.dump({"cache_key": cache_key, "metadata": schema_metadata}, f, indent=2)
            with open(column_map_file, "w") as f:
                json.dump(column_map, f, indent=2)
            with open(enhanced_cache_file, "w") as f:
                json.dump(enhanced_data, f, indent=2)
            
            print(f"Enhanced schema analysis complete:")
            print(f"- Detected {len(all_business_patterns)} business patterns")
            print(f"- Inferred {len(inferred_relationships)} additional relationships")
            print(f"- Prioritized {len(table_priorities)} tables")

            return schema_metadata, column_map, vector_store, enhanced_data

    except Exception as e:
        print(f"Failed to retrieve schema: {e}")
        return [], {}, vector_store, {}

def get_contextual_table_priorities(query: str, schema_metadata: List[Dict], enhanced_data: Dict) -> List[TablePriority]:
    """Get table priorities based on query context"""
    prioritizer = TablePrioritizer()
    business_patterns = enhanced_data.get('business_patterns', [])
    return prioritizer.prioritize_tables(schema_metadata, business_patterns, query)

def execute_query(query):
    """Execute SQL query with enhanced error handling and reporting"""
    try:
        engine = get_engine()
        with engine.connect().execution_options(stream_results=True) as conn:
            result = conn.execute(text(query))
            if query.strip().upper().startswith("SELECT"):
                rows = result.fetchall()
                columns = result.keys()
                return rows, columns, None # No error
            return None, None, None # No error
    except Exception as e:
        # Enhanced error reporting with more specific error types
        error_str = str(e).lower()
        
        if "invalid object name" in error_str:
            enhanced_error = f"Table or view does not exist: {str(e)}"
        elif "invalid column name" in error_str:
            enhanced_error = f"Column does not exist: {str(e)}"
        elif "syntax error" in error_str or "incorrect syntax" in error_str:
            enhanced_error = f"SQL syntax error: {str(e)}"
        elif "timeout" in error_str:
            enhanced_error = f"Query execution timeout: {str(e)}"
        elif "permission denied" in error_str or "access denied" in error_str:
            enhanced_error = f"Access denied: {str(e)}"
        elif "login failed" in error_str:
            enhanced_error = f"Authentication failed: {str(e)}"
        elif "cannot open database" in error_str:
            enhanced_error = f"Database not accessible: {str(e)}"
        else:
            enhanced_error = f"Database error: {str(e)}"
        
        print(f"❌ Query execution failed: {enhanced_error}")
        return None, None, enhanced_error # Return enhanced error message

def refresh_schema_cache():
    """Refresh all database-specific schema cache files and regenerate enhanced metadata"""
    try:
        # Use database-specific cache files
        cache_files = [
            get_schema_cache_file(),
            get_column_map_file(),
            get_enhanced_schema_cache_file()
        ]
        
        current_db = get_current_database()
        print(f"🔄 Refreshing schema cache for database: {current_db}")
        
        for file in cache_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"   🗑️ Removed: {file}")
                
    except FileNotFoundError:
        pass
    
    return get_schema_metadata()

def get_business_patterns_for_table(schema_name: str, table_name: str, enhanced_data: Dict) -> List[Dict]:
    """Get business patterns detected for a specific table"""
    if not enhanced_data or 'business_patterns' not in enhanced_data:
        return []
    
    return [
        pattern for pattern in enhanced_data['business_patterns']
        if pattern['schema_name'] == schema_name and pattern['table_name'] == table_name
    ]

def get_high_priority_tables(enhanced_data: Dict, limit: int = 10) -> List[Dict]:
    """Get the highest priority tables for query processing"""
    if not enhanced_data or 'table_priorities' not in enhanced_data:
        return []
    
    priorities = enhanced_data['table_priorities']
    sorted_priorities = sorted(priorities, key=lambda x: x['priority_score'], reverse=True)
    return sorted_priorities[:limit]

def get_tables_by_business_importance(enhanced_data: Dict, importance: str = 'high') -> List[Dict]:
    """Get tables filtered by business importance level"""
    if not enhanced_data or 'table_priorities' not in enhanced_data:
        return []
    
    return [
        table for table in enhanced_data['table_priorities']
        if table['business_importance'] == importance
    ]

def get_inferred_relationships_for_table(schema_name: str, table_name: str, enhanced_data: Dict) -> List[Dict]:
    """Get inferred relationships for a specific table"""
    if not enhanced_data or 'inferred_relationships' not in enhanced_data:
        return []
    
    table_key = f"{schema_name}.{table_name}"
    return [
        rel for rel in enhanced_data['inferred_relationships']
        if rel['source_table'] == table_key or rel['target_table'] == table_key
    ]

def find_tables_with_pattern(pattern_type: str, enhanced_data: Dict, min_confidence: float = 0.7) -> List[str]:
    """Find tables that contain columns with specific business patterns"""
    if not enhanced_data or 'business_patterns' not in enhanced_data:
        return []
    
    matching_tables = set()
    for pattern in enhanced_data['business_patterns']:
        if (pattern['pattern_type'] == pattern_type and 
            pattern['confidence'] >= min_confidence):
            matching_tables.add(f"{pattern['schema_name']}.{pattern['table_name']}")
    
    return list(matching_tables)

def get_contextual_table_priorities(query_context: str, schema_metadata: List[Dict], 
                                  enhanced_data: Dict) -> List[TablePriority]:
    """Get table priorities adjusted for specific query context"""
    if not enhanced_data or 'business_patterns' not in enhanced_data:
        return []
    
    # Convert enhanced_data business patterns back to BusinessPattern objects
    business_patterns = [
        BusinessPattern(
            pattern_type=p['pattern_type'],
            confidence=p['confidence'],
            column_name=p['column_name'],
            table_name=p['table_name'],
            schema_name=p['schema_name'],
            semantic_meaning=p['semantic_meaning']
        ) for p in enhanced_data['business_patterns']
    ]
    
    # Use the table prioritizer with query context
    prioritizer = TablePrioritizer()
    return prioritizer.prioritize_tables(schema_metadata, business_patterns, query_context)