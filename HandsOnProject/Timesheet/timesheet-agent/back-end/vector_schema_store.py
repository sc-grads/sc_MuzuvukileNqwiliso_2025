"""
VectorSchemaStore - Primary knowledge base using vector embeddings for database schema representation.

This module implements the core vector-based schema storage and retrieval system that replaces
static JSON caches with dynamic, semantic understanding of database structures.
"""

import numpy as np
import faiss
import pickle
import os
import json
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TableMatch:
    """Represents a semantic table match result"""
    table_name: str
    schema_name: str
    similarity_score: float
    context_relevance: float
    business_priority: float
    metadata: Dict[str, Any]


@dataclass
class ColumnMatch:
    """Represents a semantic column match result"""
    column_name: str
    table_name: str
    schema_name: str
    similarity_score: float
    data_type: str
    context_relevance: float
    metadata: Dict[str, Any]


@dataclass
class RelationshipEdge:
    """Represents a relationship between schema elements"""
    source_table: str
    target_table: str
    relationship_type: str
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class RelationshipGraph:
    """Dynamic relationship understanding between schema elements"""
    nodes: List[str]  # Table names
    edges: List[RelationshipEdge]
    semantic_context: Dict[str, Any]


@dataclass
class SchemaVector:
    """Vector representation of schema elements"""
    element_id: str
    element_type: str  # 'table', 'column', 'relationship'
    element_name: str
    schema_name: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    semantic_tags: List[str]
    business_context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class VectorSchemaStore:
    """
    Primary knowledge base using vector embeddings for schema representation.
    
    This class replaces JSON caches with vector-based schema understanding,
    enabling semantic search and dynamic adaptation to database structures.
    """
    
    def __init__(self, 
                 vector_db_path: str = "vector_data/schema_vectors",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 dimension: int = 384):
        """
        Initialize the VectorSchemaStore.
        
        Args:
            vector_db_path: Path to store FAISS index and metadata
            embedding_model: Sentence transformer model name
            dimension: Vector dimension (must match embedding model)
        """
        self.vector_db_path = vector_db_path
        self.dimension = dimension
        self.embedding_model_name = embedding_model
        
        # Initialize embedding model
        self.embedder = SentenceTransformer(embedding_model)
        
        # Initialize FAISS index with ID mapping for efficient updates/deletions
        index = faiss.IndexFlatIP(dimension)
        self.index = faiss.IndexIDMap(index)
        
        # Storage for metadata and mappings
        self.schema_vectors: Dict[str, SchemaVector] = {}
        self.faiss_id_to_element_id: Dict[int, str] = {}  # FAISS index ID to element ID
        self.element_id_to_faiss_id: Dict[str, int] = {}  # Element ID to FAISS index ID
        self.table_embeddings: Dict[str, np.ndarray] = {}
        self.column_embeddings: Dict[str, np.ndarray] = {}
        self.relationship_graph: RelationshipGraph = RelationshipGraph([], [], {})
        
        # Ensure storage directory exists
        os.makedirs(vector_db_path, exist_ok=True)
        
        # Load existing data if available
        self._load_from_disk()
        
        logger.info(f"VectorSchemaStore initialized with {self.index.ntotal} vectors")
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector for cosine similarity using inner product."""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def _generate_element_id(self, element_type: str, schema_name: str, element_name: str) -> str:
        """Generate unique ID for schema element."""
        return f"{element_type}:{schema_name}.{element_name}"
    
    def _create_embedding_text(self, element_type: str, element_name: str, metadata: Dict[str, Any]) -> str:
        """
        Create text representation for embedding generation.
        
        This method combines element name with contextual information to create
        rich embeddings that capture semantic meaning.
        """
        text_parts = [element_name]
        
        if element_type == "table":
            # Add table-specific context
            if "description" in metadata:
                text_parts.append(metadata["description"])
            if "business_context" in metadata:
                text_parts.append(metadata["business_context"])
            # Add column names for table context
            if "columns" in metadata:
                column_names = [col.get("name", "") for col in metadata["columns"]]
                text_parts.append(" ".join(column_names))
        
        elif element_type == "column":
            # Add column-specific context
            if "data_type" in metadata:
                text_parts.append(f"type {metadata['data_type']}")
            if "description" in metadata:
                text_parts.append(metadata["description"])
            if "table_name" in metadata:
                text_parts.append(f"in table {metadata['table_name']}")
        
        return " ".join(text_parts)
    
    def store_schema_vector(self, 
                           element_type: str,
                           schema_name: str, 
                           element_name: str,
                           metadata: Dict[str, Any],
                           semantic_tags: List[str] = None,
                           business_context: Dict[str, Any] = None) -> str:
        """
        Store a schema element as a vector embedding.
        
        Args:
            element_type: Type of element ('table', 'column', 'relationship')
            schema_name: Database schema name
            element_name: Name of the element
            metadata: Additional metadata about the element
            semantic_tags: Optional semantic tags
            business_context: Optional business context information
            
        Returns:
            Element ID of the stored vector
        """
        element_id = self._generate_element_id(element_type, schema_name, element_name)
        
        # Create embedding text
        embedding_text = self._create_embedding_text(element_type, element_name, metadata)
        
        # Generate embedding
        embedding = self.embedder.encode(embedding_text)
        normalized_embedding = self._normalize_vector(embedding)
        
        # Create schema vector object
        schema_vector = SchemaVector(
            element_id=element_id,
            element_type=element_type,
            element_name=element_name,
            schema_name=schema_name,
            embedding=normalized_embedding,
            metadata=metadata or {},
            semantic_tags=semantic_tags or [],
            business_context=business_context or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store in memory
        self.schema_vectors[element_id] = schema_vector
        
        # Add to FAISS index with a unique ID
        faiss_id = hash(element_id) & (2**63 - 1)
        self.index.add_with_ids(normalized_embedding.reshape(1, -1), np.array([faiss_id]))
        
        # Update mappings
        self.faiss_id_to_element_id[faiss_id] = element_id
        self.element_id_to_faiss_id[element_id] = faiss_id
        
        # Update type-specific storage
        if element_type == "table":
            table_key = f"{schema_name}.{element_name}"
            self.table_embeddings[table_key] = normalized_embedding
        elif element_type == "column":
            column_key = f"{schema_name}.{metadata.get('table_name', '')}.{element_name}"
            self.column_embeddings[column_key] = normalized_embedding
        
        logger.debug(f"Stored {element_type} vector: {element_id}")
        return element_id
    
    def retrieve_schema_vector(self, element_id: str) -> Optional[SchemaVector]:
        """
        Retrieve a schema vector by its element ID.
        
        Args:
            element_id: Unique identifier for the schema element
            
        Returns:
            SchemaVector object or None if not found
        """
        return self.schema_vectors.get(element_id)
    
    def update_schema_vector(self, 
                           element_id: str,
                           metadata: Dict[str, Any] = None,
                           semantic_tags: List[str] = None,
                           business_context: Dict[str, Any] = None) -> bool:
        """
        Update an existing schema vector.
        
        Args:
            element_id: Unique identifier for the schema element
            metadata: Updated metadata
            semantic_tags: Updated semantic tags
            business_context: Updated business context
            
        Returns:
            True if update was successful, False otherwise
        """
        if element_id not in self.schema_vectors:
            logger.warning(f"Schema vector not found for update: {element_id}")
            return False
        
        schema_vector = self.schema_vectors[element_id]
        
        # Update fields if provided
        if metadata is not None:
            schema_vector.metadata.update(metadata)
        if semantic_tags is not None:
            schema_vector.semantic_tags = semantic_tags
        if business_context is not None:
            schema_vector.business_context.update(business_context)
        
        schema_vector.updated_at = datetime.now()
        
        # Regenerate embedding if metadata changed significantly
        if metadata is not None:
            embedding_text = self._create_embedding_text(
                schema_vector.element_type, 
                schema_vector.element_name, 
                schema_vector.metadata
            )
            new_embedding = self.embedder.encode(embedding_text)
            normalized_embedding = self._normalize_vector(new_embedding)
            schema_vector.embedding = normalized_embedding
            
            # Update in FAISS index
            faiss_id = self.element_id_to_faiss_id[element_id]
            self.index.remove_ids(np.array([faiss_id]))
            self.index.add_with_ids(normalized_embedding.reshape(1, -1), np.array([faiss_id]))
        
        logger.debug(f"Updated schema vector: {element_id}")
        return True
    
    def delete_schema_vector(self, element_id: str) -> bool:
        """
        Delete a schema vector.
        
        Args:
            element_id: Unique identifier for the schema element
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if element_id not in self.schema_vectors:
            logger.warning(f"Schema vector not found for deletion: {element_id}")
            return False
        
        # Remove from memory storage
        schema_vector = self.schema_vectors.pop(element_id)
        
        # Remove from FAISS index
        faiss_id = self.element_id_to_faiss_id.pop(element_id)
        self.faiss_id_to_element_id.pop(faiss_id)
        self.index.remove_ids(np.array([faiss_id]))
        
        # Remove from type-specific storage
        if schema_vector.element_type == "table":
            table_key = f"{schema_vector.schema_name}.{schema_vector.element_name}"
            self.table_embeddings.pop(table_key, None)
        elif schema_vector.element_type == "column":
            table_name = schema_vector.metadata.get('table_name', '')
            column_key = f"{schema_vector.schema_name}.{table_name}.{schema_vector.element_name}"
            self.column_embeddings.pop(column_key, None)
        
        logger.debug(f"Deleted schema vector: {element_id}")
        return True
    
    def _rebuild_faiss_index(self):
        """Rebuild FAISS index from current schema vectors."""
        # Create new index
        index = faiss.IndexFlatIP(self.dimension)
        self.index = faiss.IndexIDMap(index)
        self.faiss_id_to_element_id.clear()
        self.element_id_to_faiss_id.clear()
        
        # Re-add all vectors
        for element_id, schema_vector in self.schema_vectors.items():
            faiss_id = hash(element_id) & (2**63 - 1)
            self.index.add_with_ids(schema_vector.embedding.reshape(1, -1), np.array([faiss_id]))
            self.faiss_id_to_element_id[faiss_id] = element_id
            self.element_id_to_faiss_id[element_id] = faiss_id
    
    def find_similar_vectors(self, 
                           query_vector: np.ndarray, 
                           k: int = 5,
                           element_type: str = None) -> List[Tuple[str, float]]:
        """
        Find vectors similar to the query vector.
        
        Args:
            query_vector: Query vector for similarity search
            k: Number of similar vectors to return
            element_type: Optional filter by element type
            
        Returns:
            List of tuples (element_id, similarity_score)
        """
        if self.index.ntotal == 0:
            return []
        
        # Normalize query vector
        normalized_query = self._normalize_vector(query_vector)
        
        # Search in FAISS index
        scores, indices = self.index.search(normalized_query.reshape(1, -1), min(k * 2, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Invalid index
                continue
                
            element_id = self.faiss_id_to_element_id.get(idx)
            if element_id and element_id in self.schema_vectors:
                schema_vector = self.schema_vectors[element_id]
                
                # Apply element type filter if specified
                if element_type is None or schema_vector.element_type == element_type:
                    results.append((element_id, float(score)))
        
        # Sort by similarity score (descending) and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def find_similar_tables(self, query_vector: np.ndarray, k: int = 5) -> List[TableMatch]:
        """
        Find tables semantically similar to the query vector.
        
        Args:
            query_vector: Query vector for similarity search
            k: Number of similar tables to return
            
        Returns:
            List of TableMatch objects sorted by similarity
        """
        similar_vectors = self.find_similar_vectors(query_vector, k=k*2, element_type="table")
        
        table_matches = []
        for element_id, similarity_score in similar_vectors:
            schema_vector = self.schema_vectors.get(element_id)
            if schema_vector:
                # Calculate context relevance and business priority
                context_relevance = self._calculate_context_relevance(schema_vector, query_vector)
                business_priority = self._calculate_business_priority(schema_vector)
                
                table_match = TableMatch(
                    table_name=schema_vector.element_name,
                    schema_name=schema_vector.schema_name,
                    similarity_score=similarity_score,
                    context_relevance=context_relevance,
                    business_priority=business_priority,
                    metadata=schema_vector.metadata
                )
                table_matches.append(table_match)
        
        # Sort by combined score (similarity + context + business priority)
        table_matches.sort(
            key=lambda x: (x.similarity_score * 0.5 + x.context_relevance * 0.3 + x.business_priority * 0.2),
            reverse=True
        )
        
        return table_matches[:k]
    
    def find_similar_columns(self, query_vector: np.ndarray, table_context: str = None, k: int = 5) -> List[ColumnMatch]:
        """
        Find columns semantically relevant to the query vector.
        
        Args:
            query_vector: Query vector for similarity search
            table_context: Optional table context to filter results
            k: Number of similar columns to return
            
        Returns:
            List of ColumnMatch objects sorted by similarity
        """
        similar_vectors = self.find_similar_vectors(query_vector, k=k*3, element_type="column")
        
        column_matches = []
        for element_id, similarity_score in similar_vectors:
            schema_vector = self.schema_vectors.get(element_id)
            if schema_vector:
                # Apply table context filter if specified
                if table_context and schema_vector.metadata.get('table_name') != table_context:
                    continue
                
                context_relevance = self._calculate_context_relevance(schema_vector, query_vector)
                
                column_match = ColumnMatch(
                    column_name=schema_vector.element_name,
                    table_name=schema_vector.metadata.get('table_name', ''),
                    schema_name=schema_vector.schema_name,
                    similarity_score=similarity_score,
                    data_type=schema_vector.metadata.get('data_type', 'unknown'),
                    context_relevance=context_relevance,
                    metadata=schema_vector.metadata
                )
                column_matches.append(column_match)
        
        # Sort by combined score
        column_matches.sort(
            key=lambda x: (x.similarity_score * 0.7 + x.context_relevance * 0.3),
            reverse=True
        )
        
        return column_matches[:k]
    
    def get_relationship_context(self, tables: List[str]) -> RelationshipGraph:
        """
        Get semantic relationships between the specified tables.
        
        Args:
            tables: List of table names to get relationships for
            
        Returns:
            RelationshipGraph containing relevant relationships
        """
        # Filter relationships that involve the specified tables
        relevant_edges = []
        for edge in self.relationship_graph.edges:
            if edge.source_table in tables or edge.target_table in tables:
                relevant_edges.append(edge)
        
        # Get all nodes involved in the relationships
        relevant_nodes = set(tables)
        for edge in relevant_edges:
            relevant_nodes.add(edge.source_table)
            relevant_nodes.add(edge.target_table)
        
        return RelationshipGraph(
            nodes=list(relevant_nodes),
            edges=relevant_edges,
            semantic_context=self.relationship_graph.semantic_context
        )
    
    def _calculate_context_relevance(self, schema_vector: SchemaVector, query_vector: np.ndarray) -> float:
        """Calculate context relevance score for a schema vector."""
        # Simple cosine similarity as base relevance
        base_similarity = np.dot(schema_vector.embedding, query_vector)
        
        # Boost score based on semantic tags
        tag_boost = 0.0
        if "primary" in schema_vector.semantic_tags:
            tag_boost += 0.1
        if "important" in schema_vector.semantic_tags:
            tag_boost += 0.05
        
        return min(1.0, base_similarity + tag_boost)
    
    def _calculate_business_priority(self, schema_vector: SchemaVector) -> float:
        """Calculate business priority score for a schema vector."""
        # Default priority
        priority = 0.5
        
        # Boost for commonly used tables/columns
        if schema_vector.business_context.get("usage_frequency", 0) > 0.7:
            priority += 0.2
        
        # Boost for core business entities
        core_entities = ["employee", "project", "customer", "order", "user"]
        element_name_lower = schema_vector.element_name.lower()
        if any(entity in element_name_lower for entity in core_entities):
            priority += 0.3
        
        return min(1.0, priority)

    def get_all_vectors_by_type(self, element_type: str) -> List[SchemaVector]:
        """
        Get all vectors of a specific type.
        
        Args:
            element_type: Type of elements to retrieve
            
        Returns:
            List of SchemaVector objects
        """
        return [
            vector for vector in self.schema_vectors.values()
            if vector.element_type == element_type
        ]
    
    def get_schema_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the stored schema vectors.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_vectors": len(self.schema_vectors),
            "faiss_index_size": self.index.ntotal,
            "by_type": {},
            "by_schema": {}
        }
        
        # Count by type
        for vector in self.schema_vectors.values():
            element_type = vector.element_type
            schema_name = vector.schema_name
            
            stats["by_type"][element_type] = stats["by_type"].get(element_type, 0) + 1
            stats["by_schema"][schema_name] = stats["by_schema"].get(schema_name, 0) + 1
        
        return stats
    
    def save_to_disk(self):
        """Save the vector store to disk."""
        try:
            # Save FAISS index
            faiss_path = os.path.join(self.vector_db_path, "schema.index")
            faiss.write_index(self.index, faiss_path)
            
            # Save metadata
            metadata = {
                "schema_vectors": {
                    element_id: {
                        "element_id": vector.element_id,
                        "element_type": vector.element_type,
                        "element_name": vector.element_name,
                        "schema_name": vector.schema_name,
                        "embedding": vector.embedding.tolist(),
                        "metadata": vector.metadata,
                        "semantic_tags": vector.semantic_tags,
                        "business_context": vector.business_context,
                        "created_at": vector.created_at.isoformat(),
                        "updated_at": vector.updated_at.isoformat()
                    }
                    for element_id, vector in self.schema_vectors.items()
                },
                "faiss_id_to_element_id": self.faiss_id_to_element_id,
                "element_id_to_faiss_id": self.element_id_to_faiss_id,
                "table_embeddings": {k: v.tolist() for k, v in self.table_embeddings.items()},
                "column_embeddings": {k: v.tolist() for k, v in self.column_embeddings.items()},
                "relationship_graph": {
                    "nodes": self.relationship_graph.nodes,
                    "edges": [
                        {
                            "source_table": edge.source_table,
                            "target_table": edge.target_table,
                            "relationship_type": edge.relationship_type,
                            "confidence": edge.confidence,
                            "metadata": edge.metadata
                        }
                        for edge in self.relationship_graph.edges
                    ],
                    "semantic_context": self.relationship_graph.semantic_context
                }
            }
            
            metadata_path = os.path.join(self.vector_db_path, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Vector store saved to {self.vector_db_path}")
            
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise
    
    def _load_from_disk(self):
        """Load the vector store from disk."""
        try:
            faiss_path = os.path.join(self.vector_db_path, "schema.index")
            metadata_path = os.path.join(self.vector_db_path, "metadata.json")
            
            if os.path.exists(faiss_path) and os.path.exists(metadata_path):
                # Load FAISS index
                self.index = faiss.read_index(faiss_path)
                
                # Load metadata
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Restore schema vectors
                self.schema_vectors = {}
                for element_id, vector_data in metadata["schema_vectors"].items():
                    self.schema_vectors[element_id] = SchemaVector(
                        element_id=vector_data["element_id"],
                        element_type=vector_data["element_type"],
                        element_name=vector_data["element_name"],
                        schema_name=vector_data["schema_name"],
                        embedding=np.array(vector_data["embedding"]),
                        metadata=vector_data["metadata"],
                        semantic_tags=vector_data["semantic_tags"],
                        business_context=vector_data["business_context"],
                        created_at=datetime.fromisoformat(vector_data["created_at"]),
                        updated_at=datetime.fromisoformat(vector_data["updated_at"])
                    )
                
                # Restore mappings
                self.faiss_id_to_element_id = {int(k): v for k, v in metadata["faiss_id_to_element_id"].items()}
                self.element_id_to_faiss_id = metadata["element_id_to_faiss_id"]
                self.table_embeddings = {k: np.array(v) for k, v in metadata["table_embeddings"].items()}
                self.column_embeddings = {k: np.array(v) for k, v in metadata["column_embeddings"].items()}
                
                # Restore relationship graph
                graph_data = metadata["relationship_graph"]
                edges = [
                    RelationshipEdge(
                        source_table=edge["source_table"],
                        target_table=edge["target_table"],
                        relationship_type=edge["relationship_type"],
                        confidence=edge["confidence"],
                        metadata=edge["metadata"]
                    )
                    for edge in graph_data["edges"]
                ]
                self.relationship_graph = RelationshipGraph(
                    nodes=graph_data["nodes"],
                    edges=edges,
                    semantic_context=graph_data["semantic_context"]
                )
                
                logger.info(f"Vector store loaded from {self.vector_db_path}")
            
        except Exception as e:
            logger.warning(f"Could not load vector store from disk: {e}")
            # Initialize empty structures
            index = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIDMap(index)
            self.schema_vectors = {}
            self.faiss_id_to_element_id = {}
            self.element_id_to_faiss_id = {}
            self.table_embeddings = {}
            self.column_embeddings = {}
            self.relationship_graph = RelationshipGraph([], [], {})
    
    def clear_all_vectors(self):
        """Clear all stored vectors and reset the store."""
        index = faiss.IndexFlatIP(self.dimension)
        self.index = faiss.IndexIDMap(index)
        self.schema_vectors.clear()
        self.faiss_id_to_element_id.clear()
        self.element_id_to_faiss_id.clear()
        self.table_embeddings.clear()
        self.column_embeddings.clear()
        self.relationship_graph = RelationshipGraph([], [], {})
        
        logger.info("All vectors cleared from store")
    
    def ingest_schema(self, schema_metadata: List[Dict]) -> None:
        """
        Convert schema metadata to vector embeddings and store them.
        
        Args:
            schema_metadata: List of schema metadata dictionaries containing table and column information
        """
        logger.info(f"Ingesting schema metadata for {len(schema_metadata)} tables")
        
        for table_metadata in schema_metadata:
            schema_name = table_metadata.get('schema', 'default')
            table_name = table_metadata.get('table_name', '')
            
            # Store table vector
            table_metadata_copy = table_metadata.copy()
            self.store_schema_vector(
                element_type="table",
                schema_name=schema_name,
                element_name=table_name,
                metadata=table_metadata_copy,
                semantic_tags=["table", "schema"],
                business_context={"source": "schema_ingestion"}
            )
            
            # Store column vectors
            columns = table_metadata.get('columns', [])
            for column in columns:
                column_name = column.get('name', '')
                if column_name:
                    column_metadata = column.copy()
                    column_metadata['table_name'] = table_name
                    column_metadata['schema_name'] = schema_name
                    
                    self.store_schema_vector(
                        element_type="column",
                        schema_name=schema_name,
                        element_name=column_name,
                        metadata=column_metadata,
                        semantic_tags=["column", "field"],
                        business_context={"table": table_name, "source": "schema_ingestion"}
                    )
        
        # Update relationship graph
        self._build_relationship_graph(schema_metadata)
        logger.info(f"Schema ingestion completed. Total vectors: {len(self.schema_vectors)}")
    
    def learn_from_query(self, nl_query: str, sql_query: str, success: bool) -> None:
        """
        Learn from query execution results to improve future performance.
        
        Args:
            nl_query: Natural language query
            sql_query: Generated SQL query
            success: Whether the query was successful
        """
        # Create a learning vector from the natural language query
        query_embedding = self.embedder.encode(nl_query)
        normalized_query = self._normalize_vector(query_embedding)
        
        # Store successful query patterns
        if success:
            learning_metadata = {
                "natural_language": nl_query,
                "sql_query": sql_query,
                "success": success,
                "learned_at": datetime.now().isoformat(),
                "query_type": self._classify_query_type(sql_query)
            }
            
            # Store as a learning pattern
            pattern_id = f"pattern_{len(self.schema_vectors)}"
            self.store_schema_vector(
                element_type="pattern",
                schema_name="learned",
                element_name=pattern_id,
                metadata=learning_metadata,
                semantic_tags=["pattern", "successful", "learned"],
                business_context={"source": "query_learning", "success": True}
            )
        
        logger.debug(f"Learned from query: {nl_query[:50]}... (success: {success})")
    
    def _classify_query_type(self, sql_query: str) -> str:
        """Classify the type of SQL query."""
        sql_upper = sql_query.upper().strip()
        
        if sql_upper.startswith("SELECT"):
            if "JOIN" in sql_upper:
                return "select_join"
            elif "GROUP BY" in sql_upper:
                return "select_aggregate"
            else:
                return "select_simple"
        elif sql_upper.startswith("INSERT"):
            return "insert"
        elif sql_upper.startswith("UPDATE"):
            return "update"
        elif sql_upper.startswith("DELETE"):
            return "delete"
        else:
            return "unknown"
            
    def _build_relationship_graph(self, schema_metadata):
        """
        Build relationship graph from schema metadata.
        
        This method analyzes foreign key relationships and creates a semantic
        relationship graph that can be used for join optimization and context understanding.
        """
        nodes = set()
        edges = []
        semantic_context = {}
        
        # First pass: collect all tables as nodes
        for table_metadata in schema_metadata:
            schema_name = table_metadata.get('schema', 'default')
            table_name = table_metadata.get('table_name', '')
            full_table_name = f"{schema_name}.{table_name}"
            nodes.add(full_table_name)
            
            # Store table context for semantic understanding
            semantic_context[full_table_name] = {
                'description': table_metadata.get('description', ''),
                'column_count': len(table_metadata.get('columns', [])),
                'business_domain': self._infer_business_domain(table_name, table_metadata),
                'table_type': self._classify_table_type(table_name, table_metadata)
            }
        
        # Second pass: build relationships from foreign keys
        for table_metadata in schema_metadata:
            schema_name = table_metadata.get('schema', 'default')
            table_name = table_metadata.get('table_name', '')
            source_table = f"{schema_name}.{table_name}"
            
            # Process explicit foreign key relationships
            relationships = table_metadata.get('relationships', [])
            for rel in relationships:
                target_table = rel.get('target_table', '')
                if not target_table.startswith(schema_name + '.'):
                    # Add schema prefix if not present
                    target_table = f"{schema_name}.{target_table}"
                
                # Create relationship edge
                edge = RelationshipEdge(
                    source_table=source_table,
                    target_table=target_table,
                    relationship_type='foreign_key',
                    confidence=0.9,  # High confidence for explicit FKs
                    metadata={
                        'source_column': rel.get('source_column', ''),
                        'target_column': rel.get('target_column', ''),
                        'relationship_strength': 'strong'
                    }
                )
                edges.append(edge)
            
            # Infer implicit relationships based on naming patterns
            implicit_relationships = self._infer_implicit_relationships(
                source_table, table_metadata, schema_metadata
            )
            edges.extend(implicit_relationships)
        
        # Create relationship graph
        self.relationship_graph = RelationshipGraph(
            nodes=list(nodes),
            edges=edges,
            semantic_context=semantic_context
        )
        
        # Store relationship vectors for semantic search
        self._vectorize_relationships()
        
        logger.info(f"Built relationship graph with {len(nodes)} nodes and {len(edges)} edges")

    def _infer_business_domain(self, table_name, table_metadata):
        """Infer business domain from table name and metadata."""
        table_lower = table_name.lower()
        description = table_metadata.get('description', '').lower()
        columns = [col.get('name', '').lower() for col in table_metadata.get('columns', [])]
        
        # HR domain patterns
        if any(pattern in table_lower for pattern in ['employee', 'staff', 'person', 'user', 'hr']):
            return 'human_resources'
        if any(pattern in ' '.join(columns) for pattern in ['employee_id', 'staff_id', 'hire_date']):
            return 'human_resources'
        
        # Project management domain
        if any(pattern in table_lower for pattern in ['project', 'task', 'milestone', 'sprint']):
            return 'project_management'
        if any(pattern in ' '.join(columns) for pattern in ['project_id', 'task_id', 'start_date', 'end_date']):
            return 'project_management'
        
        # Time tracking domain
        if any(pattern in table_lower for pattern in ['time', 'hour', 'log', 'entry', 'timesheet']):
            return 'time_tracking'
        if any(pattern in ' '.join(columns) for pattern in ['hours_worked', 'time_spent', 'work_date']):
            return 'time_tracking'
        
        # Financial domain
        if any(pattern in table_lower for pattern in ['invoice', 'payment', 'billing', 'cost', 'budget']):
            return 'financial'
        if any(pattern in ' '.join(columns) for pattern in ['amount', 'cost', 'price', 'budget']):
            return 'financial'
        
        # Client/Customer domain
        if any(pattern in table_lower for pattern in ['client', 'customer', 'company', 'vendor']):
            return 'client_management'
        
        return 'general'

    def _classify_table_type(self, table_name, table_metadata):
        """Classify table type based on structure and naming."""
        table_lower = table_name.lower()
        columns = table_metadata.get('columns', [])
        column_names = [col.get('name', '').lower() for col in columns]
        
        # Junction/Bridge table (many-to-many relationships)
        if len([col for col in column_names if col.endswith('_id')]) >= 2:
            if len(columns) <= 4:  # Typically just IDs and maybe timestamps
                return 'junction'
        
        # Lookup/Reference table
        if len(columns) <= 3 and any(col in column_names for col in ['name', 'code', 'description']):
            return 'lookup'
        
        # Log/Audit table
        if any(pattern in table_lower for pattern in ['log', 'audit', 'history', 'track']):
            return 'log'
        
        # Transaction table
        if any(pattern in table_lower for pattern in ['transaction', 'entry', 'record']):
            return 'transaction'
        
        # Master/Entity table
        if any(pattern in table_lower for pattern in ['master', 'main']) or len(columns) > 5:
            return 'entity'
        
        return 'entity'  # Default

    def _infer_implicit_relationships(self, source_table, table_metadata, all_schema_metadata):
        """Infer implicit relationships based on naming patterns and business logic."""
        edges = []
        source_columns = [col.get('name', '').lower() for col in table_metadata.get('columns', [])]
        
        # Look for potential foreign key columns (ending with _id)
        potential_fk_columns = [col for col in source_columns if col.endswith('_id') and col != 'id']
        
        for fk_column in potential_fk_columns:
            # Extract referenced table name (remove _id suffix)
            referenced_table_name = fk_column[:-3]  # Remove '_id'
            
            # Look for matching tables in schema metadata
            for target_metadata in all_schema_metadata:
                target_table_name = target_metadata.get('table_name', '').lower()
                target_schema = target_metadata.get('schema', 'default')
                target_full_name = f"{target_schema}.{target_table_name}"
                
                # Check for name similarity
                if (referenced_table_name in target_table_name or 
                    target_table_name in referenced_table_name or
                    self._calculate_name_similarity(referenced_table_name, target_table_name) > 0.7):
                    
                    # Create implicit relationship
                    edge = RelationshipEdge(
                        source_table=source_table,
                        target_table=target_full_name,
                        relationship_type='inferred_foreign_key',
                        confidence=0.6,  # Lower confidence for inferred relationships
                        metadata={
                            'source_column': fk_column,
                            'target_column': 'id',  # Assume primary key is 'id'
                            'relationship_strength': 'medium',
                            'inference_method': 'naming_pattern'
                        }
                    )
                    edges.append(edge)
                    break
        
        return edges

    def _calculate_name_similarity(self, name1, name2):
        """Calculate similarity between two names using simple string matching."""
        if name1 == name2:
            return 1.0
        
        # Check if one is contained in the other
        if name1 in name2 or name2 in name1:
            return 0.8
        
        # Simple character overlap ratio
        set1 = set(name1)
        set2 = set(name2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def _vectorize_relationships(self):
        """Create vector embeddings for relationships to enable semantic relationship search."""
        for edge in self.relationship_graph.edges:
            # Create relationship description for embedding
            relationship_text = self._create_relationship_text(edge)
            
            # Generate relationship ID
            relationship_id = f"rel:{edge.source_table}->{edge.target_table}"
            
            # Store relationship as vector
            self.store_schema_vector(
                element_type="relationship",
                schema_name="relationships",
                element_name=relationship_id,
                metadata={
                    'source_table': edge.source_table,
                    'target_table': edge.target_table,
                    'relationship_type': edge.relationship_type,
                    'confidence': edge.confidence,
                    'source_column': edge.metadata.get('source_column', ''),
                    'target_column': edge.metadata.get('target_column', ''),
                    'relationship_strength': edge.metadata.get('relationship_strength', 'medium')
                },
                semantic_tags=['relationship', edge.relationship_type],
                business_context={
                    'domain_connection': self._analyze_domain_connection(edge),
                    'join_frequency': 'unknown',  # Could be learned over time
                    'business_importance': self._assess_relationship_importance(edge)
                }
            )

    def _create_relationship_text(self, edge):
        """Create descriptive text for relationship embedding."""
        source_parts = edge.source_table.split('.')
        target_parts = edge.target_table.split('.')
        
        source_context = self.relationship_graph.semantic_context.get(edge.source_table, {})
        target_context = self.relationship_graph.semantic_context.get(edge.target_table, {})
        
        relationship_text = (
            f"Relationship from {source_parts[-1]} table to {target_parts[-1]} table. "
            f"Type: {edge.relationship_type}. "
            f"Source domain: {source_context.get('business_domain', 'unknown')}. "
            f"Target domain: {target_context.get('business_domain', 'unknown')}. "
            f"Connection: {edge.metadata.get('source_column', '')} references {edge.metadata.get('target_column', '')}."
        )
        
        return relationship_text

    def _analyze_domain_connection(self, edge):
        """Analyze the business domain connection between related tables."""
        source_context = self.relationship_graph.semantic_context.get(edge.source_table, {})
        target_context = self.relationship_graph.semantic_context.get(edge.target_table, {})
        
        source_domain = source_context.get('business_domain', 'unknown')
        target_domain = target_context.get('business_domain', 'unknown')
        
        if source_domain == target_domain:
            return f"same_domain_{source_domain}"
        else:
            return f"cross_domain_{source_domain}_to_{target_domain}"

    def _assess_relationship_importance(self, edge):
        """Assess the business importance of a relationship."""
        # High importance for explicit foreign keys
        if edge.relationship_type == 'foreign_key':
            return 'high'
        
        # Medium importance for inferred relationships with high confidence
        if edge.relationship_type == 'inferred_foreign_key' and edge.confidence > 0.7:
            return 'medium'
        
        # Lower importance for low-confidence inferred relationships
        return 'low'