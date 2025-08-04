#!/usr/bin/env python3
"""
Vector Performance Optimizer - Efficient vector indexing and retrieval system.

This module implements optimized vector indexing strategies, efficient similarity search
with approximate methods, vector cache management, and batch processing capabilities.
"""

import numpy as np
import faiss
import time
import threading
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime, timedelta
import pickle
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IndexConfig:
    """Configuration for FAISS index optimization"""
    index_type: str = "hnsw"  # flat, ivf, hnsw, pq
    dimension: int = 384
    nlist: int = 100  # For IVF indices
    m_hnsw: int = 16  # For HNSW indices
    ef_construction: int = 200  # For HNSW indices
    ef_search: int = 50  # For HNSW indices
    pq_m: int = 8  # For PQ indices
    nbits: int = 8  # For PQ indices
    use_gpu: bool = False
    gpu_id: int = 0


@dataclass
class CacheConfig:
    """Configuration for vector cache management"""
    max_cache_size: int = 10000  # Maximum number of cached vectors
    cache_ttl_seconds: int = 3600  # Time to live for cache entries
    lru_cleanup_threshold: float = 0.8  # Cleanup when cache reaches this ratio
    enable_persistent_cache: bool = True
    cache_file_path: str = "vector_data/cache"


@dataclass
class CacheEntry:
    """Represents a cached vector entry"""
    vector_id: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """Enhanced search result with performance metrics"""
    vector_id: str
    similarity_score: float
    distance: float
    metadata: Dict[str, Any]
    search_time_ms: float = 0.0
    cache_hit: bool = False


@dataclass
class BatchSearchRequest:
    """Batch search request for multiple queries"""
    query_id: str
    query_vector: np.ndarray
    k: int = 5
    filter_metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for vector operations"""
    total_searches: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_search_time_ms: float = 0.0
    total_search_time_ms: float = 0.0
    index_build_time_ms: float = 0.0
    memory_usage_mb: float = 0.0


class VectorCache:
    """
    High-performance LRU cache for frequently accessed vectors with TTL support.
    """
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0
        }
        
        # Load persistent cache if enabled
        if config.enable_persistent_cache:
            self._load_persistent_cache()
    
    def get(self, vector_id: str) -> Optional[CacheEntry]:
        """Get vector from cache with LRU update"""
        with self.lock:
            if vector_id in self.cache:
                entry = self.cache[vector_id]
                
                # Check TTL
                if self._is_expired(entry):
                    del self.cache[vector_id]
                    self.stats['misses'] += 1
                    return None
                
                # Update access info and move to end (most recently used)
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self.cache.move_to_end(vector_id)
                
                self.stats['hits'] += 1
                return entry
            
            self.stats['misses'] += 1
            return None
    
    def put(self, vector_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> None:
        """Put vector in cache with automatic cleanup"""
        with self.lock:
            # Create cache entry
            entry = CacheEntry(
                vector_id=vector_id,
                embedding=embedding.copy(),
                metadata=metadata.copy()
            )
            
            # Add to cache
            self.cache[vector_id] = entry
            self.cache.move_to_end(vector_id)
            
            # Cleanup if needed
            if len(self.cache) > self.config.max_cache_size * self.config.lru_cleanup_threshold:
                self._cleanup_cache()
            
            self.stats['size'] = len(self.cache)
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry has expired"""
        if self.config.cache_ttl_seconds <= 0:
            return False
        
        age = (datetime.now() - entry.created_at).total_seconds()
        return age > self.config.cache_ttl_seconds
    
    def _cleanup_cache(self) -> None:
        """Remove expired and least recently used entries"""
        current_time = datetime.now()
        expired_keys = []
        
        # Find expired entries
        for vector_id, entry in self.cache.items():
            if self._is_expired(entry):
                expired_keys.append(vector_id)
        
        # Remove expired entries
        for key in expired_keys:
            del self.cache[key]
            self.stats['evictions'] += 1
        
        # Remove LRU entries if still over threshold
        target_size = int(self.config.max_cache_size * 0.7)  # Reduce to 70%
        while len(self.cache) > target_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats['evictions'] += 1
        
        self.stats['size'] = len(self.cache)
        logger.info(f"Cache cleanup: removed {len(expired_keys)} expired, "
                   f"evicted {self.stats['evictions']} LRU entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0.0
            
            return {
                'size': len(self.cache),
                'max_size': self.config.max_cache_size,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self.stats['evictions'],
                'memory_usage_mb': self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> float:
        """Estimate cache memory usage in MB"""
        if not self.cache:
            return 0.0
        
        # Sample a few entries to estimate average size
        sample_size = min(10, len(self.cache))
        sample_entries = list(self.cache.values())[:sample_size]
        
        total_size = 0
        for entry in sample_entries:
            # Embedding size
            total_size += entry.embedding.nbytes
            # Metadata size (rough estimate)
            total_size += len(str(entry.metadata).encode('utf-8'))
            # Object overhead
            total_size += 200  # Rough estimate for object overhead
        
        avg_entry_size = total_size / sample_size
        total_estimated_size = avg_entry_size * len(self.cache)
        
        return total_estimated_size / (1024 * 1024)  # Convert to MB
    
    def _save_persistent_cache(self) -> None:
        """Save cache to disk for persistence"""
        if not self.config.enable_persistent_cache:
            return
        
        try:
            cache_path = Path(self.config.cache_file_path)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Only save non-expired entries
            persistent_data = {}
            for vector_id, entry in self.cache.items():
                if not self._is_expired(entry):
                    persistent_data[vector_id] = {
                        'embedding': entry.embedding.tolist(),
                        'metadata': entry.metadata,
                        'access_count': entry.access_count,
                        'created_at': entry.created_at.isoformat()
                    }
            
            with open(f"{cache_path}.pkl", 'wb') as f:
                pickle.dump(persistent_data, f)
            
            logger.info(f"Saved {len(persistent_data)} cache entries to disk")
            
        except Exception as e:
            logger.error(f"Failed to save persistent cache: {e}")
    
    def _load_persistent_cache(self) -> None:
        """Load cache from disk"""
        try:
            cache_file = f"{self.config.cache_file_path}.pkl"
            if not os.path.exists(cache_file):
                return
            
            with open(cache_file, 'rb') as f:
                persistent_data = pickle.load(f)
            
            loaded_count = 0
            for vector_id, data in persistent_data.items():
                entry = CacheEntry(
                    vector_id=vector_id,
                    embedding=np.array(data['embedding']),
                    metadata=data['metadata'],
                    access_count=data['access_count'],
                    created_at=datetime.fromisoformat(data['created_at'])
                )
                
                # Only load non-expired entries
                if not self._is_expired(entry):
                    self.cache[vector_id] = entry
                    loaded_count += 1
            
            self.stats['size'] = len(self.cache)
            logger.info(f"Loaded {loaded_count} cache entries from disk")
            
        except Exception as e:
            logger.warning(f"Failed to load persistent cache: {e}")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.stats = {'hits': 0, 'misses': 0, 'evictions': 0, 'size': 0}
    
    def __del__(self):
        """Save cache on destruction"""
        if hasattr(self, 'config') and self.config.enable_persistent_cache:
            self._save_persistent_cache()


class OptimizedVectorIndex:
    """
    Optimized FAISS vector index with multiple indexing strategies and performance tuning.
    """
    
    def __init__(self, config: IndexConfig):
        self.config = config
        self.index = None
        self.is_trained = False
        self.vector_ids = []  # Maps FAISS index to vector ID
        self.id_to_index = {}  # Maps vector ID to FAISS index
        self.metrics = PerformanceMetrics()
        
        self._initialize_index()
    
    def _initialize_index(self) -> None:
        """Initialize FAISS index based on configuration"""
        start_time = time.time()
        
        try:
            if self.config.index_type == "flat":
                # Exact search using L2 distance
                self.index = faiss.IndexFlatL2(self.config.dimension)
                self.is_trained = True
                
            elif self.config.index_type == "ivf":
                # IVF (Inverted File) for approximate search
                quantizer = faiss.IndexFlatL2(self.config.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.config.dimension, self.config.nlist)
                
            elif self.config.index_type == "hnsw":
                # HNSW for very fast approximate search
                self.index = faiss.IndexHNSWFlat(self.config.dimension, self.config.m_hnsw)
                self.index.hnsw.efConstruction = self.config.ef_construction
                self.index.hnsw.efSearch = self.config.ef_search
                self.is_trained = True
                
            elif self.config.index_type == "pq":
                # Product Quantization for memory efficiency
                self.index = faiss.IndexPQ(self.config.dimension, self.config.pq_m, self.config.nbits)
                
            else:
                raise ValueError(f"Unsupported index type: {self.config.index_type}")
            
            # GPU support if requested
            if self.config.use_gpu and faiss.get_num_gpus() > 0:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, self.config.gpu_id, self.index)
                logger.info(f"Using GPU {self.config.gpu_id} for FAISS index")
            
            build_time = (time.time() - start_time) * 1000
            self.metrics.index_build_time_ms = build_time
            
            logger.info(f"Initialized {self.config.index_type} index in {build_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Failed to initialize index: {e}")
            raise
    
    def add_vectors(self, vectors: np.ndarray, vector_ids: List[str]) -> None:
        """Add vectors to the index with batch optimization"""
        if len(vectors) != len(vector_ids):
            raise ValueError("Number of vectors must match number of IDs")
        
        start_time = time.time()
        
        try:
            # Ensure vectors are float32 for FAISS
            vectors = vectors.astype(np.float32)
            
            # Train index if needed
            if not self.is_trained:
                logger.info("Training index...")
                self.index.train(vectors)
                self.is_trained = True
            
            # Add vectors to index
            start_idx = len(self.vector_ids)
            self.index.add(vectors)
            
            # Update mappings
            for i, vector_id in enumerate(vector_ids):
                faiss_idx = start_idx + i
                self.vector_ids.append(vector_id)
                self.id_to_index[vector_id] = faiss_idx
            
            add_time = (time.time() - start_time) * 1000
            logger.info(f"Added {len(vectors)} vectors in {add_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            raise
    
    def search(self, query_vectors: np.ndarray, k: int = 5) -> List[List[Tuple[str, float]]]:
        """Search for similar vectors with performance optimization"""
        if self.index.ntotal == 0:
            return [[] for _ in range(len(query_vectors))]
        
        start_time = time.time()
        
        try:
            # Ensure query vectors are float32
            query_vectors = query_vectors.astype(np.float32)
            
            # Perform search
            distances, indices = self.index.search(query_vectors, k)
            
            # Convert results
            results = []
            for i in range(len(query_vectors)):
                query_results = []
                for j in range(k):
                    idx = indices[i][j]
                    if idx >= 0 and idx < len(self.vector_ids):
                        vector_id = self.vector_ids[idx]
                        distance = float(distances[i][j])
                        # Convert distance to similarity score
                        similarity = 1.0 / (1.0 + distance)
                        query_results.append((vector_id, similarity))
                
                results.append(query_results)
            
            # Update metrics
            search_time = (time.time() - start_time) * 1000
            self.metrics.total_searches += len(query_vectors)
            self.metrics.total_search_time_ms += search_time
            self.metrics.avg_search_time_ms = (
                self.metrics.total_search_time_ms / self.metrics.total_searches
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            'index_type': self.config.index_type,
            'dimension': self.config.dimension,
            'total_vectors': self.index.ntotal if self.index else 0,
            'is_trained': self.is_trained,
            'metrics': {
                'total_searches': self.metrics.total_searches,
                'avg_search_time_ms': self.metrics.avg_search_time_ms,
                'index_build_time_ms': self.metrics.index_build_time_ms
            }
        }


class VectorPerformanceOptimizer:
    """
    Main performance optimizer that combines optimized indexing, caching, and batch processing.
    """
    
    def __init__(self, 
                 index_config: IndexConfig = None,
                 cache_config: CacheConfig = None):
        self.index_config = index_config or IndexConfig()
        self.cache_config = cache_config or CacheConfig()
        
        # Initialize components
        self.index = OptimizedVectorIndex(self.index_config)
        self.cache = VectorCache(self.cache_config)
        self.vector_metadata = {}  # vector_id -> metadata
        
        # Thread pool for batch processing
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        logger.info("VectorPerformanceOptimizer initialized")
    
    def add_vectors_batch(self, 
                         vectors: List[np.ndarray], 
                         vector_ids: List[str],
                         metadata_list: List[Dict[str, Any]]) -> None:
        """Add vectors in batch with caching"""
        if len(vectors) != len(vector_ids) or len(vectors) != len(metadata_list):
            raise ValueError("All input lists must have the same length")
        
        # Convert to numpy array for batch processing
        vector_array = np.vstack(vectors)
        
        # Add to index
        self.index.add_vectors(vector_array, vector_ids)
        
        # Add to cache and metadata
        for vector_id, vector, metadata in zip(vector_ids, vectors, metadata_list):
            self.cache.put(vector_id, vector, metadata)
            self.vector_metadata[vector_id] = metadata
        
        logger.info(f"Added {len(vectors)} vectors in batch")
    
    def search_single(self, 
                     query_vector: np.ndarray, 
                     k: int = 5,
                     use_cache: bool = True) -> List[SearchResult]:
        """Search for similar vectors with caching"""
        start_time = time.time()
        
        # Check cache first if enabled
        cached_results = []
        if use_cache:
            # Simple cache key based on query vector hash
            query_hash = str(hash(query_vector.tobytes()))
            cached_entry = self.cache.get(f"query_{query_hash}")
            if cached_entry:
                # Return cached results (simplified for demo)
                pass
        
        # Perform index search
        results = self.index.search(query_vector.reshape(1, -1), k)[0]
        
        # Convert to SearchResult objects
        search_results = []
        for vector_id, similarity in results:
            metadata = self.vector_metadata.get(vector_id, {})
            search_time = (time.time() - start_time) * 1000
            
            search_result = SearchResult(
                vector_id=vector_id,
                similarity_score=similarity,
                distance=1.0 - similarity,  # Approximate conversion
                metadata=metadata,
                search_time_ms=search_time,
                cache_hit=False
            )
            search_results.append(search_result)
        
        return search_results
    
    def search_batch(self, 
                    batch_requests: List[BatchSearchRequest]) -> Dict[str, List[SearchResult]]:
        """Process multiple search requests in batch"""
        if not batch_requests:
            return {}
        
        # Group requests by k value for efficient batch processing
        k_groups = defaultdict(list)
        for req in batch_requests:
            k_groups[req.k].append(req)
        
        all_results = {}
        
        # Process each k group
        for k, requests in k_groups.items():
            query_vectors = np.vstack([req.query_vector for req in requests])
            batch_results = self.index.search(query_vectors, k)
            
            # Convert results
            for i, req in enumerate(requests):
                search_results = []
                for vector_id, similarity in batch_results[i]:
                    metadata = self.vector_metadata.get(vector_id, {})
                    
                    # Apply metadata filters if specified
                    if req.filter_metadata:
                        if not self._matches_filter(metadata, req.filter_metadata):
                            continue
                    
                    search_result = SearchResult(
                        vector_id=vector_id,
                        similarity_score=similarity,
                        distance=1.0 - similarity,
                        metadata=metadata,
                        cache_hit=False
                    )
                    search_results.append(search_result)
                
                all_results[req.query_id] = search_results
        
        return all_results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            'index_stats': self.index.get_stats(),
            'cache_stats': self.cache.get_stats(),
            'total_vectors': len(self.vector_metadata),
            'memory_usage_estimate_mb': self._estimate_total_memory_usage()
        }
    
    def _estimate_total_memory_usage(self) -> float:
        """Estimate total memory usage in MB"""
        # Index memory (rough estimate)
        index_memory = self.index.config.dimension * self.index.index.ntotal * 4 / (1024 * 1024)
        
        # Cache memory
        cache_memory = self.cache.get_stats()['memory_usage_mb']
        
        # Metadata memory (rough estimate)
        metadata_memory = len(str(self.vector_metadata).encode('utf-8')) / (1024 * 1024)
        
        return index_memory + cache_memory + metadata_memory
    
    def optimize_index(self) -> None:
        """Perform index optimization operations"""
        logger.info("Starting index optimization...")
        
        # For HNSW indices, we can adjust search parameters
        if self.index_config.index_type == "hnsw" and hasattr(self.index.index, 'hnsw'):
            # Optimize search parameters based on current performance
            current_stats = self.index.get_stats()
            avg_search_time = current_stats['metrics']['avg_search_time_ms']
            
            if avg_search_time > 100:  # If searches are slow
                # Reduce efSearch for faster but less accurate searches
                self.index.index.hnsw.efSearch = max(10, self.index.index.hnsw.efSearch - 10)
                logger.info(f"Reduced efSearch to {self.index.index.hnsw.efSearch} for faster searches")
            elif avg_search_time < 10:  # If searches are very fast
                # Increase efSearch for better accuracy
                self.index.index.hnsw.efSearch = min(200, self.index.index.hnsw.efSearch + 10)
                logger.info(f"Increased efSearch to {self.index.index.hnsw.efSearch} for better accuracy")
        
        # Clean up cache
        self.cache._cleanup_cache()
        
        logger.info("Index optimization completed")
    
    def save_state(self, filepath: str) -> None:
        """Save optimizer state to disk"""
        try:
            state = {
                'index_config': self.index_config.__dict__,
                'cache_config': self.cache_config.__dict__,
                'vector_metadata': self.vector_metadata,
                'vector_ids': self.index.vector_ids,
                'id_to_index': self.index.id_to_index
            }
            
            with open(f"{filepath}_state.pkl", 'wb') as f:
                pickle.dump(state, f)
            
            # Save FAISS index
            if self.index.index:
                faiss.write_index(self.index.index, f"{filepath}_index.faiss")
            
            # Save cache
            self.cache._save_persistent_cache()
            
            logger.info(f"Optimizer state saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save optimizer state: {e}")
            raise
    
    def load_state(self, filepath: str) -> None:
        """Load optimizer state from disk"""
        try:
            # Load state
            with open(f"{filepath}_state.pkl", 'rb') as f:
                state = pickle.load(f)
            
            # Restore configurations
            self.index_config = IndexConfig(**state['index_config'])
            self.cache_config = CacheConfig(**state['cache_config'])
            
            # Restore metadata and mappings
            self.vector_metadata = state['vector_metadata']
            
            # Load FAISS index
            if os.path.exists(f"{filepath}_index.faiss"):
                self.index = OptimizedVectorIndex(self.index_config)
                self.index.index = faiss.read_index(f"{filepath}_index.faiss")
                self.index.vector_ids = state['vector_ids']
                self.index.id_to_index = state['id_to_index']
                self.index.is_trained = True
            
            # Reload cache
            self.cache = VectorCache(self.cache_config)
            
            logger.info(f"Optimizer state loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load optimizer state: {e}")
            raise
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=True)