#!/usr/bin/env python3
"""
Schema Ingestion and Vectorization Engine

This module implements the schema metadata to vector conversion pipeline,
table and column embedding generation, relationship graph vectorization,
and business context embedding for schema elements.

Implements task 2.2: Implement schema ingestion and vectorization
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
import re

from vector_schema_store import (
    VectorSchemaStore, SchemaVector, TableMatch, ColumnMatch, 
    RelationshipEdge, RelationshipGraph
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Helper functions for intelligent description generation ---

def _split_camel_case(name: str) -> List[str]:
    """Splits camelCase or PascalCase into words."""
    # Handles cases like 'MyVariableName' -> ['My', 'Variable', 'Name']
    # and 'HTTPRequestHandler' -> ['HTTP', 'Request', 'Handler']
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).split()

def _generate_intelligent_description(name: str, element_type: str, context: Optional[Dict] = None) -> str:
    """Generates a more sophisticated, human-readable description for a schema element."""
    context = context or {}
    words = _split_camel_case(name)
    
    # Clean common suffixes from the base name for better descriptions
    base_name_for_desc = name.replace("ID", "").replace("Id", "").replace("Seq", "")
    readable_base = ' '.join(_split_camel_case(base_name_for_desc)).lower()

    if element_type == "table":
        plural_name = readable_base
        if not plural_name.endswith('s'):
            # Handle simple plurals, can be improved for irregular nouns if needed
            plural_name += 's'
        return f"Stores and represents information about {plural_name} within the system."

    if element_type == "column":
        table_name = context.get("table_name", "the table")
        table_readable_name = ' '.join(_split_camel_case(table_name)).lower()
        col_lower = name.lower()

        # --- Rule-based description generation for columns ---

        # 1. Primary Keys
        if col_lower in [pk.lower() for pk in context.get("pk_names", [])]:
            return f"A unique identifier for each {table_readable_name} record."

        # 2. Foreign Keys
        if context.get("is_fk"):
            target_table = context.get('target_table', 'another table').split('.')[-1]
            target_readable_name = ' '.join(_split_camel_case(target_table)).lower()
            return f"A foreign key that links this record to the '{target_table}' table, identifying the associated {target_readable_name}."

        # 3. Common Naming Patterns (more specific)
        if "name" in col_lower:
            return f"The name of the {readable_base}."
        if "description" in col_lower or "comment" in col_lower:
            return f"A textual description, comment, or note providing additional details about this record."
        if col_lower.startswith("is_") or col_lower.startswith("has_"):
            action = ' '.join(_split_camel_case(name.replace("is_", "").replace("has_", ""))).lower()
            return f"A boolean flag (true/false) indicating if the record {action}."
        if "status" in col_lower:
            return f"Indicates the current status or state of the {readable_base} (e.g., 'Active', 'Pending', 'Completed')."
        if "type" in col_lower:
            return f"Specifies the type or category of the {readable_base}."
        if "date" in col_lower or "time" in col_lower:
            if "start" in col_lower:
                return f"The date and/or time when the {readable_base} begins."
            if "end" in col_lower:
                return f"The date and/or time when the {readable_base} ends."
            if "created" in col_lower or "processed" in col_lower:
                return f"The timestamp when this record was created or processed."
            return f"A date and/or time value associated with the {readable_base}."
        if "hours" in col_lower or "total" in col_lower or "count" in col_lower or "number" in col_lower:
             return f"A numeric value representing the {readable_base}."
        if "amount" in col_lower or "billable" in col_lower:
            return f"A financial value representing the {readable_base}."
        if "path" in col_lower or "file" in col_lower:
            return f"The file path or name associated with this record."

        # 4. Default fallback
        return f"Stores data for the '{readable_base}' attribute of a {table_readable_name}."

    return f"Data element: {name}"


@dataclass
class BusinessPattern:
    """Represents a business pattern for context enhancement"""
    pattern_type: str  # 'domain_keyword', 'business_rule', 'priority_indicator'
    domain: str
    keywords: List[str]
    context: Dict[str, Any]
    priority: str = 'medium'


@dataclass
class SchemaIngestionResult:
    """Result of schema ingestion process"""
    tables_processed: int
    columns_processed: int
    relationships_discovered: int
    business_contexts_added: int
    vectors_created: int
    processing_time: float
    errors: List[str]


class SchemaIngestionEngine:
    """
    Enhanced schema ingestion engine that converts database schema metadata
    into rich vector embeddings with business context and relationship understanding.
    """
    
    def __init__(self, vector_store: VectorSchemaStore):
        """
        Initialize the schema ingestion engine.
        
        Args:
            vector_store: VectorSchemaStore instance for storing vectors
        """
        self.vector_store = vector_store
        self.business_patterns: List[BusinessPattern] = []
        self.domain_mappings = self._initialize_domain_mappings()
        
    def _initialize_domain_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize domain-specific mappings for business context."""
        return {
            'human_resources': {
                'keywords': ['employee', 'staff', 'person', 'user', 'hr', 'personnel'],
                'common_columns': ['employee_id', 'staff_id', 'hire_date', 'department_id', 'salary'],
                'priority': 'high',
                'sensitivity': 'high'
            },
            'project_management': {
                'keywords': ['project', 'task', 'milestone', 'sprint', 'deliverable'],
                'common_columns': ['project_id', 'task_id', 'start_date', 'end_date', 'status'],
                'priority': 'high',
                'sensitivity': 'medium'
            },
            'time_tracking': {
                'keywords': ['time', 'hour', 'log', 'entry', 'timesheet', 'attendance'],
                'common_columns': ['hours_worked', 'time_spent', 'work_date', 'clock_in', 'clock_out'],
                'priority': 'medium',
                'sensitivity': 'medium'
            },
            'financial': {
                'keywords': ['invoice', 'payment', 'billing', 'cost', 'budget', 'expense'],
                'common_columns': ['amount', 'cost', 'price', 'budget', 'invoice_id'],
                'priority': 'high',
                'sensitivity': 'high'
            },
            'client_management': {
                'keywords': ['client', 'customer', 'company', 'vendor', 'supplier'],
                'common_columns': ['client_id', 'customer_id', 'company_name', 'contact_info'],
                'priority': 'high',
                'sensitivity': 'medium'
            }
        }

    def _enrich_schema_with_descriptions(self, schema_metadata: List[Dict]) -> List[Dict]:
        """
        Pre-processes schema metadata to add intelligent descriptions if they are missing.
        This makes the schema more understandable for the LLM.
        """
        logger.info("Enriching schema with intelligent descriptions...")
        for table_info in schema_metadata:
            table_name = table_info.get("table")
            # Only generate if description is missing or a generic default
            if not table_info.get("description") or "Data table" in table_info.get("description") or "information table" in table_info.get("description"):
                table_info["description"] = _generate_intelligent_description(table_name, "table")

            pk_names = table_info.get("primary_keys", [])
            
            # Create a map of foreign keys for easy lookup
            fk_map = {}
            for rel in table_info.get("relationships", []):
                fk_map[rel["source_column"]] = rel.get("target_table", "unknown")

            for column in table_info.get("columns", []):
                # Only generate if description is missing or a generic default
                col_desc = column.get("description", "")
                if not col_desc or "Data field" in col_desc or "Name field" in col_desc or "description field" in col_desc:
                    col_name = column["name"]
                    context = {"table_name": table_name, "pk_names": pk_names}
                    
                    if col_name in fk_map:
                        context["is_fk"] = True
                        context["target_table"] = fk_map[col_name]
                    
                    column["description"] = _generate_intelligent_description(col_name, "column", context)
        
        return schema_metadata
    
    def ingest_schema_with_enhancement(self, 
                                     schema_metadata: List[Dict],
                                     business_patterns: List[BusinessPattern] = None) -> SchemaIngestionResult:
        """
        Enhanced schema ingestion with business context and relationship analysis.
        
        Args:
            schema_metadata: List of schema metadata dictionaries
            business_patterns: Optional business patterns for context enhancement
            
        Returns:
            SchemaIngestionResult with processing statistics
        """
        start_time = datetime.now()
        result = SchemaIngestionResult(
            tables_processed=0,
            columns_processed=0,
            relationships_discovered=0,
            business_contexts_added=0,
            vectors_created=0,
            processing_time=0.0,
            errors=[]
        )
        
        try:
            # First, enrich the raw schema with generated descriptions for better context
            schema_metadata = self._enrich_schema_with_descriptions(schema_metadata)

            logger.info(f"Starting enhanced schema ingestion for {len(schema_metadata)} tables")
            
            # Store business patterns
            if business_patterns:
                self.business_patterns = business_patterns
            
            # Phase 1: Create table vectors with business context
            table_vectors_created = self._create_enhanced_table_vectors(schema_metadata, result)
            
            # Phase 2: Create column vectors with business context
            column_vectors_created = self._create_enhanced_column_vectors(schema_metadata, result)
            
            # Phase 3: Build and vectorize relationship graph
            relationships_created = self._build_and_vectorize_relationships(schema_metadata, result)
            
            # Phase 4: Add cross-domain business context
            business_contexts_added = self._add_cross_domain_context(schema_metadata, result)
            
            # Update result statistics
            result.vectors_created = table_vectors_created + column_vectors_created + relationships_created
            result.business_contexts_added = business_contexts_added
            
            # Calculate processing time
            end_time = datetime.now()
            result.processing_time = (end_time - start_time).total_seconds()
            
            logger.info(f"Schema ingestion completed: {result.vectors_created} vectors created in {result.processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Schema ingestion failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return result
    
    def _create_enhanced_table_vectors(self, schema_metadata: List[Dict], result: SchemaIngestionResult) -> int:
        """Create enhanced table vectors with business context."""
        vectors_created = 0
        
        for table_metadata in schema_metadata:
            try:
                schema_name = table_metadata.get('schema', 'default')
                table_name = table_metadata.get('table', '') # Changed from table_name to table
                
                if not table_name:
                    continue
                
                # Extract business context
                business_context = self._extract_table_business_context(table_name, table_metadata)
                
                # Create enhanced embedding text
                embedding_text = self._create_enhanced_table_embedding_text(table_name, table_metadata, business_context)
                
                # Prepare enhanced metadata
                enhanced_metadata = table_metadata.copy()
                enhanced_metadata.update({
                    'business_domain': business_context['business_domain'],
                    'table_type': business_context['table_type'],
                    'business_priority': business_context['business_priority'],
                    'data_sensitivity': business_context['data_sensitivity'],
                    'usage_patterns': business_context['usage_patterns'],
                    'embedding_text': embedding_text
                })
                
                # Store enhanced table vector
                element_id = self.vector_store.store_schema_vector(
                    element_type="table",
                    schema_name=schema_name,
                    element_name=table_name,
                    metadata=enhanced_metadata,
                    semantic_tags=self._generate_table_semantic_tags(table_name, business_context),
                    business_context=business_context
                )
                
                if element_id:
                    vectors_created += 1
                    result.tables_processed += 1
                
            except Exception as e:
                error_msg = f"Failed to create table vector for {table_name}: {str(e)}"
                logger.warning(error_msg)
                result.errors.append(error_msg)
        
        return vectors_created
    
    def _create_enhanced_column_vectors(self, schema_metadata: List[Dict], result: SchemaIngestionResult) -> int:
        """Create enhanced column vectors with business context."""
        vectors_created = 0
        
        for table_metadata in schema_metadata:
            try:
                schema_name = table_metadata.get('schema', 'default')
                table_name = table_metadata.get('table', '') # Changed from table_name to table
                columns = table_metadata.get('columns', [])
                
                # Get table business context for column enhancement
                table_business_context = self._extract_table_business_context(table_name, table_metadata)
                
                for column in columns:
                    column_name = column.get('name', '')
                    if not column_name:
                        continue
                    
                    try:
                        # Extract column-specific business context
                        column_business_context = self._extract_column_business_context(
                            column, table_name, table_business_context
                        )
                        
                        # Create enhanced embedding text
                        embedding_text = self._create_enhanced_column_embedding_text(
                            column, table_name, column_business_context
                        )
                        
                        # Prepare enhanced metadata
                        enhanced_metadata = column.copy()
                        enhanced_metadata.update({
                            'table_name': table_name,
                            'schema_name': schema_name,
                            'business_meaning': column_business_context['business_meaning'],
                            'data_classification': column_business_context['data_classification'],
                            'business_importance': column_business_context['business_importance'],
                            'privacy_level': column_business_context['privacy_level'],
                            'validation_rules': column_business_context['validation_rules'],
                            'embedding_text': embedding_text
                        })
                        
                        # Store enhanced column vector
                        element_id = self.vector_store.store_schema_vector(
                            element_type="column",
                            schema_name=schema_name,
                            element_name=column_name,
                            metadata=enhanced_metadata,
                            semantic_tags=self._generate_column_semantic_tags(column, column_business_context),
                            business_context=column_business_context
                        )
                        
                        if element_id:
                            vectors_created += 1
                            result.columns_processed += 1
                    
                    except Exception as e:
                        error_msg = f"Failed to create column vector for {table_name}.{column_name}: {str(e)}"
                        logger.warning(error_msg)
                        result.errors.append(error_msg)
            
            except Exception as e:
                error_msg = f"Failed to process columns for table {table_name}: {str(e)}"
                logger.warning(error_msg)
                result.errors.append(error_msg)
        
        return vectors_created
    
    def _build_and_vectorize_relationships(self, schema_metadata: List[Dict], result: SchemaIngestionResult) -> int:
        """Build relationship graph and create relationship vectors."""
        try:
            # Build relationship graph using the vector store method
            self.vector_store._build_relationship_graph(schema_metadata)
            
            # Count relationships
            relationship_count = len(self.vector_store.relationship_graph.edges)
            result.relationships_discovered = relationship_count
            
            # Relationship vectors are created automatically in _build_relationship_graph
            # via _vectorize_relationships method
            return relationship_count
            
        except Exception as e:
            error_msg = f"Failed to build relationship graph: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return 0
    
    def _add_cross_domain_context(self, schema_metadata: List[Dict], result: SchemaIngestionResult) -> int:
        """Add cross-domain business context to enhance semantic understanding."""
        contexts_added = 0
        
        try:
            # Analyze cross-domain relationships
            domain_analysis = self._analyze_cross_domain_relationships(schema_metadata)
            
            # Enhance existing vectors with cross-domain context
            for table_metadata in schema_metadata:
                schema_name = table_metadata.get('schema', 'default')
                table_name = table_metadata.get('table', '') # Changed from table_name to table
                
                # Get existing table vector
                table_element_id = self.vector_store._generate_element_id("table", schema_name, table_name)
                table_vector = self.vector_store.retrieve_schema_vector(table_element_id)
                
                if table_vector:
                    # Add cross-domain context
                    cross_domain_context = domain_analysis.get(f"{schema_name}.{table_name}", {})
                    if cross_domain_context:
                        # Update business context with cross-domain information
                        enhanced_business_context = table_vector.business_context.copy()
                        enhanced_business_context.update({
                            'cross_domain_connections': cross_domain_context.get('connections', []),
                            'domain_influence_score': cross_domain_context.get('influence_score', 0.0),
                            'integration_patterns': cross_domain_context.get('patterns', [])
                        })
                        
                        # Update the vector
                        self.vector_store.update_schema_vector(
                            table_element_id,
                            business_context=enhanced_business_context
                        )
                        contexts_added += 1
            
        except Exception as e:
            error_msg = f"Failed to add cross-domain context: {str(e)}"
            logger.warning(error_msg)
            result.errors.append(error_msg)
        
        return contexts_added
    
    def _extract_table_business_context(self, table_name: str, table_metadata: Dict) -> Dict[str, Any]:
        """Extract comprehensive business context for a table."""
        return {
            'business_domain': self._infer_business_domain(table_name, table_metadata),
            'table_type': self._classify_table_type(table_name, table_metadata),
            'business_priority': self._assess_business_priority(table_name, table_metadata),
            'usage_patterns': self._infer_usage_patterns(table_name, table_metadata),
            'data_sensitivity': self._assess_data_sensitivity(table_metadata),
            'business_rules': self._extract_applicable_business_rules(table_name),
            'domain_keywords': self._extract_domain_keywords(table_name, table_metadata)
        }
    
    def _extract_column_business_context(self, column: Dict, table_name: str, table_context: Dict) -> Dict[str, Any]:
        """Extract comprehensive business context for a column."""
        column_name = column.get('name', '').lower()
        data_type = column.get('type', '').lower() # Changed from data_type to type
        
        return {
            'business_meaning': self._infer_column_business_meaning(column_name, data_type),
            'data_classification': self._classify_column_data(column_name, data_type),
            'business_importance': self._assess_column_importance(column, table_context),
            'privacy_level': self._assess_column_privacy(column_name, data_type),
            'validation_rules': self._infer_validation_rules(column_name, data_type),
            'business_domain': table_context.get('business_domain', 'general'),
            'semantic_relationships': self._find_column_semantic_relationships(column_name, table_name)
        }
    
    def _create_enhanced_table_embedding_text(self, table_name: str, table_metadata: Dict, business_context: Dict) -> str:
        """Create rich embedding text for table with business context."""
        text_parts = [
            f"Table: {table_name}",
            f"Business domain: {business_context.get('business_domain', 'general')}",
            f"Table type: {business_context.get('table_type', 'entity')}",
            f"Business priority: {business_context.get('business_priority', 'medium')}"
        ]
        
        # Add description if available
        if table_metadata.get('description'):
            text_parts.append(f"Description: {table_metadata['description']}")
        
        # Add column information
        columns = table_metadata.get('columns', [])
        if columns:
            column_names = [col.get('name', '') for col in columns[:10]]  # Limit to first 10
            text_parts.append(f"Key columns: {', '.join(column_names)}")
        
        # Add business context
        usage_patterns = business_context.get('usage_patterns', [])
        if usage_patterns:
            text_parts.append(f"Usage patterns: {', '.join(usage_patterns)}")
        
        domain_keywords = business_context.get('domain_keywords', [])
        if domain_keywords:
            text_parts.append(f"Domain keywords: {', '.join(domain_keywords)}")
        
        # Add relationship information
        relationships = table_metadata.get('relationships', [])
        if relationships:
            related_tables = [rel.get('target_table', '') for rel in relationships[:5]]
            text_parts.append(f"Related to: {', '.join(related_tables)}")
        
        return " | ".join(text_parts)
    
    def _create_enhanced_column_embedding_text(self, column: Dict, table_name: str, business_context: Dict) -> str:
        """Create rich embedding text for column with business context."""
        column_name = column.get('name', '')
        data_type = column.get('type', '') # Changed from data_type to type
        
        text_parts = [
            f"Column: {column_name}",
            f"Table: {table_name}",
            f"Data type: {data_type}",
            f"Business meaning: {business_context.get('business_meaning', 'data_field')}",
            f"Data classification: {business_context.get('data_classification', 'general_data')}",
            f"Business importance: {business_context.get('business_importance', 'medium')}",
            f"Privacy level: {business_context.get('privacy_level', 'none')}"
        ]
        
        # Add column-specific attributes
        if column.get('primary_key'):
            text_parts.append("Primary key field")
        
        if not column.get('nullable', True):
            text_parts.append("Required field")
        
        # Add validation rules
        validation_rules = business_context.get('validation_rules', [])
        if validation_rules:
            text_parts.append(f"Validation: {', '.join(validation_rules)}")
        
        # Add semantic relationships
        semantic_relationships = business_context.get('semantic_relationships', [])
        if semantic_relationships:
            text_parts.append(f"Related to: {', '.join(semantic_relationships)}")
        
        return " | ".join(text_parts)
    
    def _generate_table_semantic_tags(self, table_name: str, business_context: Dict) -> List[str]:
        """Generate semantic tags for table vectors."""
        tags = ['table', 'schema']
        
        # Add domain tags
        domain = business_context.get('business_domain', 'general')
        tags.append(domain)
        
        # Add type tags
        table_type = business_context.get('table_type', 'entity')
        tags.append(table_type)
        
        # Add priority tags
        priority = business_context.get('business_priority', 'medium')
        tags.append(f"priority_{priority}")
        
        # Add usage pattern tags
        usage_patterns = business_context.get('usage_patterns', [])
        tags.extend([f"usage_{pattern}" for pattern in usage_patterns])
        
        return list(set(tags))
    
    def _generate_column_semantic_tags(self, column: Dict, business_context: Dict) -> List[str]:
        """Generate semantic tags for column vectors."""
        tags = ['column', 'field']
        
        # Add meaning tags
        meaning = business_context.get('business_meaning', 'data_field')
        tags.append(meaning)
        
        # Add classification tags
        classification = business_context.get('data_classification', 'general_data')
        tags.append(classification)
        
        # Add importance tags
        importance = business_context.get('business_importance', 'medium')
        tags.append(f"importance_{importance}")
        
        # Add privacy tags
        privacy = business_context.get('privacy_level', 'none')
        if privacy != 'none':
            tags.append(f"privacy_{privacy}")
        
        # Add type-specific tags
        if column.get('primary_key'):
            tags.append('primary_key')
        
        if not column.get('nullable', True):
            tags.append('required')
        
        return list(set(tags))
    
    # Business context analysis methods
    def _infer_business_domain(self, table_name: str, table_metadata: Dict) -> str:
        """Infer business domain from table name and metadata."""
        table_lower = table_name.lower()
        description = table_metadata.get('description', '').lower()
        columns = [col.get('name', '').lower() for col in table_metadata.get('columns', [])]
        
        # Check against domain mappings
        for domain, mapping in self.domain_mappings.items():
            keywords = mapping['keywords']
            common_columns = mapping['common_columns']
            
            # Check table name and description
            if any(keyword in table_lower for keyword in keywords):
                return domain
            if any(keyword in description for keyword in keywords):
                return domain
            
            # Check column names
            if any(col_pattern in ' '.join(columns) for col_pattern in common_columns):
                return domain
        
        return 'general'
    
    def _classify_table_type(self, table_name: str, table_metadata: Dict) -> str:
        """Classify table type based on structure and naming."""
        table_lower = table_name.lower()
        columns = table_metadata.get('columns', [])
        column_names = [col.get('name', '').lower() for col in columns]
        
        # Junction/Bridge table (many-to-many relationships)
        id_columns = [col for col in column_names if col.endswith('_id') or col.endswith('id')]
        if len(id_columns) >= 2 and len(columns) <= 5:
            return 'junction'
        
        # Lookup/Reference table
        if len(columns) <= 3 and any(col in column_names for col in ['name', 'code', 'description', 'type']):
            return 'lookup'
        
        # Log/Audit table
        if any(pattern in table_lower for pattern in ['log', 'audit', 'history', 'track']):
            return 'log'
        
        # Transaction table
        if any(pattern in table_lower for pattern in ['transaction', 'entry', 'record', 'request']):
            return 'transaction'
        
        # Master/Entity table
        if any(pattern in table_lower for pattern in ['master', 'main']) or len(columns) > 5:
            return 'entity'
        
        return 'entity'  # Default
    
    def _assess_business_priority(self, table_name: str, table_metadata: Dict) -> str:
        """Assess business priority of a table."""
        table_lower = table_name.lower()
        
        # High priority patterns
        if any(pattern in table_lower for pattern in ['employee', 'customer', 'project', 'order', 'invoice', 'client']):
            return 'high'
        
        # Low priority patterns
        if any(pattern in table_lower for pattern in ['log', 'audit', 'temp', 'backup', 'cache', 'processedfiles']):
            return 'low'
        
        # Check domain priority
        domain = self._infer_business_domain(table_name, table_metadata)
        domain_priority = self.domain_mappings.get(domain, {}).get('priority', 'medium')
        
        return domain_priority
    
    def _infer_usage_patterns(self, table_name: str, table_metadata: Dict) -> List[str]:
        """Infer common usage patterns for a table."""
        patterns = []
        table_lower = table_name.lower()
        columns = [col.get('name', '').lower() for col in table_metadata.get('columns', [])]
        
        # OLTP patterns
        if any(col.endswith('_id') or col.endswith('id') for col in columns):
            patterns.append('transactional')
        
        # Reporting patterns
        if any(pattern in table_lower for pattern in ['report', 'summary', 'aggregate', 'forecast']):
            patterns.append('reporting')
        
        # Audit patterns
        if any(pattern in table_lower for pattern in ['audit', 'log', 'history']):
            patterns.append('audit')
        
        # Master data patterns
        if any(pattern in table_lower for pattern in ['master', 'reference', 'lookup', 'type']):
            patterns.append('master_data')
        
        # Time-series patterns
        if any(col in columns for col in ['created_date', 'updated_date', 'timestamp', 'date']):
            patterns.append('time_series')
        
        return list(set(patterns)) if patterns else ['general']
    
    def _assess_data_sensitivity(self, table_metadata: Dict) -> str:
        """Assess data sensitivity level of a table."""
        columns = [col.get('name', '').lower() for col in table_metadata.get('columns', [])]
        
        # High sensitivity indicators
        high_sensitivity_patterns = ['ssn', 'social_security', 'password', 'salary', 'credit_card', 'bank_account']
        if any(pattern in ' '.join(columns) for pattern in high_sensitivity_patterns):
            return 'high'
        
        # Medium sensitivity indicators
        medium_sensitivity_patterns = ['email', 'phone', 'address', 'birth_date', 'employee_id']
        if any(pattern in ' '.join(columns) for pattern in medium_sensitivity_patterns):
            return 'medium'
        
        return 'low'
    
    def _extract_applicable_business_rules(self, table_name: str) -> List[str]:
        """Extract applicable business rules for a table."""
        rules = []
        table_lower = table_name.lower()
        
        # Check business patterns for applicable rules
        for pattern in self.business_patterns:
            if pattern.pattern_type == 'business_rule':
                applicable_tables = pattern.context.get('applicable_tables', [])
                if any(table_pattern.lower() in table_lower for table_pattern in applicable_tables):
                    rules.append(pattern.domain)
        
        return rules
    
    def _extract_domain_keywords(self, table_name: str, table_metadata: Dict) -> List[str]:
        """Extract domain-specific keywords for a table."""
        domain = self._infer_business_domain(table_name, table_metadata)
        return self.domain_mappings.get(domain, {}).get('keywords', [])
    
    def _infer_column_business_meaning(self, column_name: str, data_type: str) -> str:
        """Infer business meaning of a column."""
        column_lower = column_name.lower()
        
        # Identity columns
        if column_lower.endswith('id'):
            return 'identifier'
        
        # Name columns
        if 'name' in column_lower:
            return 'name_field'
        
        # Date/time columns
        if any(pattern in column_lower for pattern in ['date', 'time', 'created', 'updated', 'modified']):
            return 'temporal_field'
        
        # Status/state columns
        if any(pattern in column_lower for pattern in ['status', 'state', 'flag', 'active', 'type']):
            return 'status_field'
        
        # Measurement columns
        if any(pattern in column_lower for pattern in ['amount', 'count', 'quantity', 'hours', 'rate', 'total', 'number']):
            return 'measurement_field'
        
        # Contact information
        if any(pattern in column_lower for pattern in ['email', 'phone', 'address']):
            return 'contact_field'
        
        return 'data_field'
    
    def _classify_column_data(self, column_name: str, data_type: str) -> str:
        """Classify the type of data stored in a column."""
        column_lower = column_name.lower()
        type_lower = data_type.lower()
        
        # Numeric data
        if any(type_pattern in type_lower for type_pattern in ['int', 'decimal', 'float', 'numeric']):
            if any(pattern in column_lower for pattern in ['amount', 'cost', 'price', 'salary']):
                return 'financial_numeric'
            elif any(pattern in column_lower for pattern in ['count', 'quantity', 'hours']):
                return 'measurement_numeric'
            else:
                return 'general_numeric'
        
        # Text data
        if any(type_pattern in type_lower for type_pattern in ['varchar', 'char', 'text', 'string']):
            if any(pattern in column_lower for pattern in ['name', 'title']):
                return 'name_text'
            elif any(pattern in column_lower for pattern in ['description', 'comment', 'note']):
                return 'descriptive_text'
            elif any(pattern in column_lower for pattern in ['email', 'phone', 'address']):
                return 'contact_text'
            else:
                return 'general_text'
        
        # Date/time data
        if any(type_pattern in type_lower for type_pattern in ['date', 'time', 'datetime', 'timestamp']):
            return 'temporal_data'
        
        # Boolean data
        if any(type_pattern in type_lower for type_pattern in ['bit', 'boolean', 'bool']):
            return 'boolean_data'
        
        return 'unknown_data'
    
    def _assess_column_importance(self, column: Dict, table_context: Dict) -> str:
        """Assess business importance of a column."""
        column_name = column.get('name', '').lower()
        is_primary_key = column.get('primary_key', False)
        is_nullable = column.get('nullable', True)
        
        # Primary keys are always high importance
        if is_primary_key:
            return 'high'
        
        # Non-nullable columns are generally more important
        if not is_nullable:
            if any(pattern in column_name for pattern in ['name', 'title', 'status', 'type']):
                return 'high'
            else:
                return 'medium'
        
        # Business-critical fields
        if any(pattern in column_name for pattern in ['employee_id', 'customer_id', 'project_id', 'amount']):
            return 'high'
        
        # Descriptive fields
        if any(pattern in column_name for pattern in ['description', 'comment', 'note']):
            return 'low'
        
        return 'medium'
    
    def _assess_column_privacy(self, column_name: str, data_type: str) -> str:
        """Assess privacy level of a column."""
        column_lower = column_name.lower()
        
        # High privacy fields
        if any(pattern in column_lower for pattern in ['ssn', 'social_security', 'password', 'salary', 'credit_card']):
            return 'high'
        
        # Medium privacy fields
        if any(pattern in column_lower for pattern in ['email', 'phone', 'address', 'birth_date']):
            return 'medium'
        
        # Low privacy fields
        if any(pattern in column_lower for pattern in ['name', 'title', 'department', 'status']):
            return 'low'
        
        return 'none'
    
    def _infer_validation_rules(self, column_name: str, data_type: str) -> List[str]:
        """Infer validation rules for a column."""
        rules = []
        column_lower = column_name.lower()
        type_lower = data_type.lower()
        
        # Email validation
        if 'email' in column_lower:
            rules.append('email_format')
        
        # Phone validation
        if 'phone' in column_lower:
            rules.append('phone_format')
        
        # Date validation
        if any(pattern in column_lower for pattern in ['date', 'time']) or 'date' in type_lower:
            rules.append('date_format')
        
        # Numeric validation
        if any(type_pattern in type_lower for type_pattern in ['int', 'decimal', 'float']):
            if any(pattern in column_lower for pattern in ['amount', 'cost', 'price']):
                rules.append('positive_number')
            elif 'count' in column_lower or 'quantity' in column_lower:
                rules.append('non_negative_number')
        
        # Required field validation
        if any(pattern in column_lower for pattern in ['name', 'title', 'status']) and 'id' not in column_lower:
            rules.append('required_field')
        
        return list(set(rules))
    
    def _find_column_semantic_relationships(self, column_name: str, table_name: str) -> List[str]:
        """Find semantic relationships for a column."""
        relationships = []
        column_lower = column_name.lower()
        
        # Foreign key relationships
        if column_lower.endswith('_id') and column_lower != 'id':
            referenced_table = column_lower[:-3]  # Remove '_id'
            relationships.append(f"references_{referenced_table}")
        
        # Common semantic relationships
        if 'name' in column_lower:
            relationships.append('naming_field')
        if 'date' in column_lower or 'time' in column_lower:
            relationships.append('temporal_field')
        if 'status' in column_lower or 'state' in column_lower:
            relationships.append('status_field')
        
        return list(set(relationships))
    
    def _analyze_cross_domain_relationships(self, schema_metadata: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Analyze cross-domain relationships between tables."""
        domain_analysis = {}
        
        # Build domain mapping for all tables
        table_domains = {}
        for table_metadata in schema_metadata:
            schema_name = table_metadata.get('schema', 'default')
            table_name = table_metadata.get('table', '') # Changed from table_name to table
            full_name = f"{schema_name}.{table_name}"
            domain = self._infer_business_domain(table_name, table_metadata)
            table_domains[full_name] = domain
        
        # Analyze relationships across domains
        for table_metadata in schema_metadata:
            schema_name = table_metadata.get('schema', 'default')
            table_name = table_metadata.get('table', '') # Changed from table_name to table
            full_name = f"{schema_name}.{table_name}"
            table_domain = table_domains.get(full_name, 'general')
            
            connections = []
            influence_score = 0.0
            patterns = []
            
            # Check relationships
            relationships = table_metadata.get('relationships', [])
            for rel in relationships:
                target_table = rel.get('target_table', '')
                target_domain = table_domains.get(target_table, 'general')
                
                if target_domain != table_domain:
                    connections.append({
                        'target_table': target_table,
                        'target_domain': target_domain,
                        'relationship_type': 'foreign_key'
                    })
                    influence_score += 0.3
                    patterns.append(f"cross_domain_{table_domain}_to_{target_domain}")
            
            if connections:
                domain_analysis[full_name] = {
                    'connections': connections,
                    'influence_score': min(1.0, influence_score),
                    'patterns': list(set(patterns))
                }
        
        return domain_analysis
    
    def get_ingestion_statistics(self) -> Dict[str, Any]:
        """Get statistics about the ingestion process."""
        stats = self.vector_store.get_schema_statistics()
        
        # Add ingestion-specific statistics
        stats.update({
            'business_patterns_loaded': len(self.business_patterns),
            'domain_mappings': len(self.domain_mappings),
            'relationship_graph_nodes': len(self.vector_store.relationship_graph.nodes),
            'relationship_graph_edges': len(self.vector_store.relationship_graph.edges)
        })
        
        return stats