#!/usr/bin/env python3
"""
Core vector infrastructure for RAG-based SQL agent.
Provides FAISS-based vector storage, indexing, and retrieval operations.
"""

import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Represents a document stored in the vector database"""
    id: str
    text: str
    embedding: np.ndarray
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    """Represents a search result from vector similarity search"""
    document: VectorDocument
    similarity_score: float
    distance: float

class FAISSVectorStore:
    """
    Core FAISS vector store implementation for efficient similarity search.
    Handles vector storage, indexing, and retrieval operations.
    """
    
    def __init__(self, 
                 embedding_model: str = "all-MiniLM-L6-v2",
                 index_type: str = "flat",
                 dimension: Optional[int] = None):
        """
        Initialize FAISS vector store.
        
        Args:
            embedding_model: SentenceTransformer model name
            index_type: FAISS index type ('flat', 'ivf', 'hnsw')
            dimension: Vector dimension (auto-detected if None)
        """
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.index_type = index_type
        self.dimension = dimension
        self.index = None
        self.documents = {}  # id -> VectorDocument
        self.id_to_index = {}  # document_id -> faiss_index
        self.index_to_id = {}  # faiss_index -> document_id
        self.next_index = 0
        
        # Initialize embedding model
        self._initialize_embedding_model()
        
        # Initialize FAISS index
        if self.dimension:
            self._initialize_index()
    
    def _initialize_embedding_model(self):
        """Initialize the sentence transformer model"""
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            if not self.dimension:
                # Get dimension from model
                test_embedding = self.embedding_model.encode(["test"])
                self.dimension = test_embedding.shape[1]
            logger.info(f"Initialized embedding model: {self.embedding_model_name} (dim: {self.dimension})")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def _initialize_index(self):
        """Initialize FAISS index based on specified type"""
        try:
            if self.index_type == "flat":
                # L2 distance (Euclidean)
                self.index = faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "ivf":
                # IVF (Inverted File) index for faster search on large datasets
                quantizer = faiss.IndexFlatL2(self.dimension)
                nlist = 100  # number of clusters
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            elif self.index_type == "hnsw":
                # HNSW (Hierarchical Navigable Small World) for very fast approximate search
                M = 16  # number of connections
                self.index = faiss.IndexHNSWFlat(self.dimension, M)
            else:
                raise ValueError(f"Unsupported index type: {self.index_type}")
            
            logger.info(f"Initialized FAISS index: {self.index_type} (dim: {self.dimension})")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents with 'id', 'text', and 'metadata' keys
            
        Returns:
            List of document IDs that were added
        """
        if not self.index:
            self._initialize_index()
        
        added_ids = []
        texts = []
        doc_objects = []
        
        for doc in documents:
            doc_id = doc['id']
            text = doc['text']
            metadata = doc.get('metadata', {})
            
            # Skip if document already exists
            if doc_id in self.documents:
                logger.warning(f"Document {doc_id} already exists, skipping")
                continue
            
            texts.append(text)
            doc_objects.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })
        
        if not texts:
            return added_ids
        
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            
            # Add to FAISS index
            start_index = self.next_index
            self.index.add(embeddings.astype(np.float32))
            
            # Store documents and mappings
            for i, doc_obj in enumerate(doc_objects):
                doc_id = doc_obj['id']
                faiss_idx = start_index + i
                
                # Create VectorDocument
                vector_doc = VectorDocument(
                    id=doc_id,
                    text=doc_obj['text'],
                    embedding=embeddings[i],
                    metadata=doc_obj['metadata']
                )
                
                # Store mappings
                self.documents[doc_id] = vector_doc
                self.id_to_index[doc_id] = faiss_idx
                self.index_to_id[faiss_idx] = doc_id
                added_ids.append(doc_id)
            
            self.next_index += len(doc_objects)
            logger.info(f"Added {len(added_ids)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
        
        return added_ids
    
    def search(self, 
               query: str, 
               k: int = 5, 
               filter_metadata: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of SearchResult objects
        """
        if not self.index or self.index.ntotal == 0:
            logger.warning("Index is empty or not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            
            # Search FAISS index
            distances, indices = self.index.search(query_embedding.astype(np.float32), k)
            
            results = []
            for i in range(len(indices[0])):
                faiss_idx = indices[0][i]
                distance = distances[0][i]
                
                # Skip invalid indices
                if faiss_idx == -1:
                    continue
                
                # Get document
                doc_id = self.index_to_id.get(faiss_idx)
                if not doc_id:
                    continue
                
                document = self.documents.get(doc_id)
                if not document:
                    continue
                
                # Apply metadata filters if specified
                if filter_metadata:
                    if not self._matches_filter(document.metadata, filter_metadata):
                        continue
                
                # Convert distance to similarity score (higher is better)
                similarity_score = 1.0 / (1.0 + distance)
                
                results.append(SearchResult(
                    document=document,
                    similarity_score=similarity_score,
                    distance=distance
                ))
            
            # Sort by similarity score (descending)
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"Found {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """Check if document metadata matches filter criteria"""
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID"""
        return self.documents.get(doc_id)
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove document from vector store.
        Note: FAISS doesn't support efficient removal, so this marks as deleted.
        """
        if doc_id not in self.documents:
            return False
        
        # Remove from our mappings
        faiss_idx = self.id_to_index.get(doc_id)
        if faiss_idx is not None:
            del self.id_to_index[doc_id]
            del self.index_to_id[faiss_idx]
        
        del self.documents[doc_id]
        logger.info(f"Removed document: {doc_id}")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'embedding_model': self.embedding_model_name
        }
    
    def save(self, filepath: str):
        """Save vector store to disk"""
        try:
            # Create directory if it doesn't exist
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss_path = f"{filepath}.faiss"
            if self.index:
                faiss.write_index(self.index, faiss_path)
            
            # Save metadata
            metadata = {
                'documents': {doc_id: {
                    'id': doc.id,
                    'text': doc.text,
                    'embedding': doc.embedding.tolist(),
                    'metadata': doc.metadata
                } for doc_id, doc in self.documents.items()},
                'id_to_index': self.id_to_index,
                'index_to_id': self.index_to_id,
                'next_index': self.next_index,
                'dimension': self.dimension,
                'index_type': self.index_type,
                'embedding_model': self.embedding_model_name
            }
            
            metadata_path = f"{filepath}.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"Saved vector store to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
            raise
    
    def load(self, filepath: str):
        """Load vector store from disk"""
        try:
            faiss_path = f"{filepath}.faiss"
            metadata_path = f"{filepath}.pkl"
            
            # Check if files exist
            if not os.path.exists(faiss_path) or not os.path.exists(metadata_path):
                raise FileNotFoundError(f"Vector store files not found at {filepath}")
            
            # Load FAISS index
            self.index = faiss.read_index(faiss_path)
            
            # Load metadata
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            # Restore state
            self.dimension = metadata['dimension']
            self.index_type = metadata['index_type']
            self.embedding_model_name = metadata['embedding_model']
            self.id_to_index = metadata['id_to_index']
            self.index_to_id = metadata['index_to_id']
            self.next_index = metadata['next_index']
            
            # Restore documents
            self.documents = {}
            for doc_id, doc_data in metadata['documents'].items():
                self.documents[doc_id] = VectorDocument(
                    id=doc_data['id'],
                    text=doc_data['text'],
                    embedding=np.array(doc_data['embedding']),
                    metadata=doc_data['metadata']
                )
            
            # Initialize embedding model
            self._initialize_embedding_model()
            
            logger.info(f"Loaded vector store from {filepath}")
            logger.info(f"Stats: {self.get_stats()}")
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            raise

class VectorStoreManager:
    """
    High-level manager for vector store operations.
    Provides utilities for managing multiple vector stores and persistence.
    """
    
    def __init__(self, base_dir: str = "../vector_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.stores = {}  # name -> FAISSVectorStore
    
    def create_store(self, 
                     name: str, 
                     embedding_model: str = "all-MiniLM-L6-v2",
                     index_type: str = "flat") -> FAISSVectorStore:
        """Create a new vector store"""
        if name in self.stores:
            logger.warning(f"Store {name} already exists")
            return self.stores[name]
        
        store = FAISSVectorStore(
            embedding_model=embedding_model,
            index_type=index_type
        )
        self.stores[name] = store
        logger.info(f"Created vector store: {name}")
        return store
    
    def get_store(self, name: str) -> Optional[FAISSVectorStore]:
        """Get existing vector store"""
        return self.stores.get(name)
    
    def load_store(self, name: str) -> Optional[FAISSVectorStore]:
        """Load vector store from disk"""
        filepath = self.base_dir / name
        
        if name not in self.stores:
            self.stores[name] = FAISSVectorStore()
        
        try:
            self.stores[name].load(str(filepath))
            return self.stores[name]
        except Exception as e:
            logger.error(f"Failed to load store {name}: {e}")
            return None
    
    def save_store(self, name: str) -> bool:
        """Save vector store to disk"""
        if name not in self.stores:
            logger.error(f"Store {name} not found")
            return False
        
        filepath = self.base_dir / name
        
        try:
            self.stores[name].save(str(filepath))
            return True
        except Exception as e:
            logger.error(f"Failed to save store {name}: {e}")
            return False
    
    def list_stores(self) -> List[str]:
        """List available vector stores"""
        return list(self.stores.keys())
    
    def get_store_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a vector store"""
        store = self.stores.get(name)
        return store.get_stats() if store else None