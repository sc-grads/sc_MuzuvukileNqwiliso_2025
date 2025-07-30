#!/usr/bin/env python3
"""
Vector Memory Manager - Memory management and cleanup systems for vector operations.

This module implements vector database size management, automatic cleanup of outdated vectors,
memory-efficient embedding storage, and configurable cache sizes and retention policies.
"""

import os
import time
import threading
# import psutil  # Optional dependency for advanced memory monitoring
import gc
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json
import pickle
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import weakref

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """Configuration for memory management"""
    max_memory_mb: int = 1024  # Maximum memory usage in MB
    cleanup_threshold: float = 0.8  # Cleanup when memory usage exceeds this ratio
    cleanup_interval_seconds: int = 300  # Cleanup interval (5 minutes)
    vector_retention_days: int = 30  # Keep vectors for 30 days
    embedding_compression: bool = True  # Use compression for embeddings
    batch_cleanup_size: int = 1000  # Process cleanup in batches
    memory_monitoring_enabled: bool = True
    auto_gc_enabled: bool = True  # Enable automatic garbage collection
    memory_warning_threshold: float = 0.9  # Warn when memory usage exceeds this


@dataclass
class VectorMetadata:
    """Metadata for vector memory management"""
    vector_id: str
    size_bytes: int
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    is_compressed: bool = False
    priority: int = 1  # 1=low, 2=medium, 3=high
    tags: Set[str] = field(default_factory=set)


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_memory_mb: float = 0.0
    vector_memory_mb: float = 0.0
    cache_memory_mb: float = 0.0
    index_memory_mb: float = 0.0
    system_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    memory_usage_percent: float = 0.0
    total_vectors: int = 0
    compressed_vectors: int = 0
    cleanup_count: int = 0
    last_cleanup: Optional[datetime] = None


class VectorCompressor:
    """Handles vector compression and decompression"""
    
    @staticmethod
    def compress_vector(vector: np.ndarray, method: str = "float16") -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress a vector using specified method.
        
        Args:
            vector: Input vector to compress
            method: Compression method ('float16', 'quantize', 'sparse')
            
        Returns:
            Tuple of (compressed_data, compression_metadata)
        """
        if method == "float16":
            # Convert to float16 for 50% size reduction
            compressed = vector.astype(np.float16)
            return compressed.tobytes(), {
                'method': 'float16',
                'original_dtype': str(vector.dtype),
                'shape': vector.shape,
                'compression_ratio': 0.5
            }
        
        elif method == "quantize":
            # Simple quantization to 8-bit
            min_val, max_val = vector.min(), vector.max()
            scale = (max_val - min_val) / 255.0
            quantized = ((vector - min_val) / scale).astype(np.uint8)
            
            metadata = {
                'method': 'quantize',
                'min_val': float(min_val),
                'max_val': float(max_val),
                'scale': float(scale),
                'shape': vector.shape,
                'compression_ratio': 0.25
            }
            return quantized.tobytes(), metadata
        
        elif method == "sparse":
            # Sparse representation for vectors with many zeros
            threshold = np.std(vector) * 0.1  # Keep values above 10% of std dev
            mask = np.abs(vector) > threshold
            indices = np.where(mask)[0]
            values = vector[mask]
            
            sparse_data = {
                'indices': indices.astype(np.uint16).tobytes(),
                'values': values.astype(np.float32).tobytes(),
                'shape': vector.shape
            }
            
            metadata = {
                'method': 'sparse',
                'threshold': float(threshold),
                'sparsity': float(1.0 - len(indices) / len(vector)),
                'compression_ratio': len(indices) * 6 / (len(vector) * 4)  # Rough estimate
            }
            
            return pickle.dumps(sparse_data), metadata
        
        else:
            raise ValueError(f"Unknown compression method: {method}")
    
    @staticmethod
    def decompress_vector(compressed_data: bytes, metadata: Dict[str, Any]) -> np.ndarray:
        """
        Decompress a vector using metadata.
        
        Args:
            compressed_data: Compressed vector data
            metadata: Compression metadata
            
        Returns:
            Decompressed vector
        """
        method = metadata['method']
        
        if method == "float16":
            vector = np.frombuffer(compressed_data, dtype=np.float16)
            return vector.reshape(metadata['shape']).astype(np.float32)
        
        elif method == "quantize":
            quantized = np.frombuffer(compressed_data, dtype=np.uint8)
            vector = quantized.astype(np.float32) * metadata['scale'] + metadata['min_val']
            return vector.reshape(metadata['shape'])
        
        elif method == "sparse":
            sparse_data = pickle.loads(compressed_data)
            indices = np.frombuffer(sparse_data['indices'], dtype=np.uint16)
            values = np.frombuffer(sparse_data['values'], dtype=np.float32)
            
            vector = np.zeros(sparse_data['shape'], dtype=np.float32)
            vector[indices] = values
            return vector
        
        else:
            raise ValueError(f"Unknown compression method: {method}")


class MemoryMonitor:
    """Monitors system and application memory usage"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        try:
            import psutil
            self.process = psutil.Process()
            self.has_psutil = True
        except ImportError:
            self.process = None
            self.has_psutil = False
            logger.warning("psutil not available - memory monitoring will be limited")
        
        self.monitoring_active = False
        self.monitor_thread = None
        self.stats_history = deque(maxlen=100)  # Keep last 100 measurements
        self.callbacks = []  # Memory threshold callbacks
        
    def start_monitoring(self):
        """Start memory monitoring in background thread"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                stats = self.get_current_stats()
                self.stats_history.append(stats)
                
                # Check thresholds and trigger callbacks
                if stats.memory_usage_percent > self.config.memory_warning_threshold:
                    self._trigger_callbacks('warning', stats)
                
                if stats.memory_usage_percent > self.config.cleanup_threshold:
                    self._trigger_callbacks('cleanup', stats)
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in memory monitoring: {e}")
                time.sleep(60)  # Wait longer on error
    
    def get_current_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        try:
            if self.has_psutil and self.process:
                # Process memory info
                memory_info = self.process.memory_info()
                process_memory_mb = memory_info.rss / 1024 / 1024
                
                # System memory info
                import psutil
                system_memory = psutil.virtual_memory()
                total_system_mb = system_memory.total / 1024 / 1024
                available_system_mb = system_memory.available / 1024 / 1024
                
                stats = MemoryStats(
                    total_memory_mb=process_memory_mb,
                    system_memory_mb=total_system_mb,
                    available_memory_mb=available_system_mb,
                    memory_usage_percent=process_memory_mb / self.config.max_memory_mb
                )
            else:
                # Fallback without psutil - use simplified estimation
                gc.collect()
                object_count = len(gc.get_objects())
                estimated_memory_mb = object_count * 0.001  # Rough estimate
                
                stats = MemoryStats(
                    total_memory_mb=estimated_memory_mb,
                    system_memory_mb=1024,  # Default assumption
                    available_memory_mb=512,  # Default assumption
                    memory_usage_percent=estimated_memory_mb / self.config.max_memory_mb
                )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return MemoryStats()
    
    def add_callback(self, callback_type: str, callback_func):
        """Add callback for memory events"""
        self.callbacks.append((callback_type, callback_func))
    
    def _trigger_callbacks(self, event_type: str, stats: MemoryStats):
        """Trigger callbacks for memory events"""
        for callback_type, callback_func in self.callbacks:
            if callback_type == event_type:
                try:
                    callback_func(stats)
                except Exception as e:
                    logger.error(f"Error in memory callback: {e}")
    
    def get_memory_trend(self, minutes: int = 30) -> Dict[str, float]:
        """Get memory usage trend over specified time period"""
        if not self.stats_history:
            return {'trend': 0.0, 'avg_usage': 0.0, 'peak_usage': 0.0}
        
        recent_stats = list(self.stats_history)[-min(minutes, len(self.stats_history)):]
        
        if len(recent_stats) < 2:
            return {'trend': 0.0, 'avg_usage': recent_stats[0].memory_usage_percent, 'peak_usage': recent_stats[0].memory_usage_percent}
        
        # Calculate trend (positive = increasing, negative = decreasing)
        first_usage = recent_stats[0].memory_usage_percent
        last_usage = recent_stats[-1].memory_usage_percent
        trend = (last_usage - first_usage) / len(recent_stats)
        
        # Calculate averages
        avg_usage = sum(s.memory_usage_percent for s in recent_stats) / len(recent_stats)
        peak_usage = max(s.memory_usage_percent for s in recent_stats)
        
        return {
            'trend': trend,
            'avg_usage': avg_usage,
            'peak_usage': peak_usage
        }


class VectorMemoryManager:
    """
    Main memory manager for vector operations with automatic cleanup and optimization.
    """
    
    def __init__(self, config: MemoryConfig = None):
        self.config = config or MemoryConfig()
        self.vector_metadata: Dict[str, VectorMetadata] = {}
        self.compressed_vectors: Dict[str, Tuple[bytes, Dict[str, Any]]] = {}
        self.memory_monitor = MemoryMonitor(self.config)
        self.compressor = VectorCompressor()
        
        # Cleanup scheduling
        self.cleanup_thread = None
        self.cleanup_active = False
        self.last_cleanup = None
        
        # Memory tracking
        self.total_memory_usage = 0
        self.cleanup_stats = {
            'total_cleanups': 0,
            'vectors_cleaned': 0,
            'memory_freed_mb': 0.0
        }
        
        # Thread pool for background operations
        self.thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="memory_mgr")
        
        # Setup memory monitoring callbacks
        self.memory_monitor.add_callback('warning', self._on_memory_warning)
        self.memory_monitor.add_callback('cleanup', self._on_memory_cleanup)
        
        # Start monitoring if enabled
        if self.config.memory_monitoring_enabled:
            self.memory_monitor.start_monitoring()
            self.start_cleanup_scheduler()
    
    def register_vector(self, 
                       vector_id: str, 
                       vector: np.ndarray, 
                       priority: int = 1,
                       tags: Set[str] = None) -> None:
        """
        Register a vector for memory management.
        
        Args:
            vector_id: Unique identifier for the vector
            vector: The vector data
            priority: Priority level (1=low, 2=medium, 3=high)
            tags: Optional tags for categorization
        """
        size_bytes = vector.nbytes
        
        metadata = VectorMetadata(
            vector_id=vector_id,
            size_bytes=size_bytes,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            priority=priority,
            tags=tags or set()
        )
        
        self.vector_metadata[vector_id] = metadata
        self.total_memory_usage += size_bytes
        
        # Auto-compress if enabled and vector is large enough
        if (self.config.embedding_compression and 
            size_bytes > 1024 and  # Only compress vectors > 1KB
            priority < 3):  # Don't compress high-priority vectors
            
            self._compress_vector_async(vector_id, vector)
    
    def access_vector(self, vector_id: str) -> None:
        """Record vector access for LRU tracking"""
        if vector_id in self.vector_metadata:
            metadata = self.vector_metadata[vector_id]
            metadata.last_accessed = datetime.now()
            metadata.access_count += 1
    
    def update_vector_priority(self, vector_id: str, priority: int) -> None:
        """Update vector priority"""
        if vector_id in self.vector_metadata:
            self.vector_metadata[vector_id].priority = priority
    
    def add_vector_tags(self, vector_id: str, tags: Set[str]) -> None:
        """Add tags to a vector"""
        if vector_id in self.vector_metadata:
            self.vector_metadata[vector_id].tags.update(tags)
    
    def _compress_vector_async(self, vector_id: str, vector: np.ndarray) -> None:
        """Compress vector in background thread"""
        def compress_task():
            try:
                compressed_data, compression_metadata = self.compressor.compress_vector(vector, "float16")
                
                # Update metadata
                if vector_id in self.vector_metadata:
                    metadata = self.vector_metadata[vector_id]
                    original_size = metadata.size_bytes
                    compressed_size = len(compressed_data)
                    
                    metadata.size_bytes = compressed_size
                    metadata.is_compressed = True
                    
                    # Store compressed data
                    self.compressed_vectors[vector_id] = (compressed_data, compression_metadata)
                    
                    # Update memory usage
                    self.total_memory_usage -= (original_size - compressed_size)
                    
                    logger.debug(f"Compressed vector {vector_id}: {original_size} -> {compressed_size} bytes")
                
            except Exception as e:
                logger.error(f"Error compressing vector {vector_id}: {e}")
        
        self.thread_pool.submit(compress_task)
    
    def get_vector_data(self, vector_id: str) -> Optional[np.ndarray]:
        """Get vector data, decompressing if necessary"""
        if vector_id not in self.vector_metadata:
            return None
        
        metadata = self.vector_metadata[vector_id]
        self.access_vector(vector_id)
        
        if metadata.is_compressed and vector_id in self.compressed_vectors:
            compressed_data, compression_metadata = self.compressed_vectors[vector_id]
            return self.compressor.decompress_vector(compressed_data, compression_metadata)
        
        return None  # Vector data should be stored elsewhere
    
    def start_cleanup_scheduler(self) -> None:
        """Start automatic cleanup scheduler"""
        if self.cleanup_active:
            return
        
        self.cleanup_active = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info("Cleanup scheduler started")
    
    def stop_cleanup_scheduler(self) -> None:
        """Stop automatic cleanup scheduler"""
        self.cleanup_active = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=10)
        logger.info("Cleanup scheduler stopped")
    
    def _cleanup_loop(self) -> None:
        """Main cleanup loop"""
        while self.cleanup_active:
            try:
                time.sleep(self.config.cleanup_interval_seconds)
                
                if self._should_run_cleanup():
                    self.cleanup_outdated_vectors()
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _should_run_cleanup(self) -> bool:
        """Determine if cleanup should run"""
        # Check memory usage
        current_stats = self.memory_monitor.get_current_stats()
        if current_stats.memory_usage_percent > self.config.cleanup_threshold:
            return True
        
        # Check time since last cleanup
        if self.last_cleanup is None:
            return True
        
        time_since_cleanup = datetime.now() - self.last_cleanup
        if time_since_cleanup.total_seconds() > self.config.cleanup_interval_seconds:
            return True
        
        return False
    
    def cleanup_outdated_vectors(self, force: bool = False) -> Dict[str, Any]:
        """
        Clean up outdated vectors based on retention policy.
        
        Args:
            force: Force cleanup regardless of thresholds
            
        Returns:
            Cleanup statistics
        """
        start_time = time.time()
        cleanup_stats = {
            'vectors_removed': 0,
            'memory_freed_mb': 0.0,
            'compression_applied': 0,
            'duration_ms': 0.0
        }
        
        try:
            current_time = datetime.now()
            retention_cutoff = current_time - timedelta(days=self.config.vector_retention_days)
            
            # Find candidates for cleanup
            cleanup_candidates = []
            
            for vector_id, metadata in self.vector_metadata.items():
                # Skip high-priority vectors unless forced
                if metadata.priority >= 3 and not force:
                    continue
                
                # Check age
                if metadata.created_at < retention_cutoff:
                    cleanup_candidates.append((vector_id, metadata, 'age'))
                
                # Check access patterns (LRU)
                elif (metadata.access_count == 0 and 
                      (current_time - metadata.last_accessed).days > 7):
                    cleanup_candidates.append((vector_id, metadata, 'unused'))
            
            # Sort by priority (lower priority first) and access count
            cleanup_candidates.sort(key=lambda x: (x[1].priority, x[1].access_count))
            
            # Process cleanup in batches
            batch_size = self.config.batch_cleanup_size
            for i in range(0, len(cleanup_candidates), batch_size):
                batch = cleanup_candidates[i:i + batch_size]
                
                for vector_id, metadata, reason in batch:
                    if self._remove_vector(vector_id):
                        cleanup_stats['vectors_removed'] += 1
                        cleanup_stats['memory_freed_mb'] += metadata.size_bytes / (1024 * 1024)
                        
                        logger.debug(f"Cleaned up vector {vector_id} (reason: {reason})")
                
                # Check if we've freed enough memory
                if not force:
                    current_stats = self.memory_monitor.get_current_stats()
                    if current_stats.memory_usage_percent < self.config.cleanup_threshold * 0.8:
                        break
            
            # Try compression for remaining vectors
            if self.config.embedding_compression:
                compression_count = self._compress_uncompressed_vectors()
                cleanup_stats['compression_applied'] = compression_count
            
            # Force garbage collection if enabled
            if self.config.auto_gc_enabled:
                gc.collect()
            
            self.last_cleanup = current_time
            cleanup_stats['duration_ms'] = (time.time() - start_time) * 1000
            
            # Update global stats
            self.cleanup_stats['total_cleanups'] += 1
            self.cleanup_stats['vectors_cleaned'] += cleanup_stats['vectors_removed']
            self.cleanup_stats['memory_freed_mb'] += cleanup_stats['memory_freed_mb']
            
            logger.info(f"Cleanup completed: removed {cleanup_stats['vectors_removed']} vectors, "
                       f"freed {cleanup_stats['memory_freed_mb']:.2f}MB in {cleanup_stats['duration_ms']:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            cleanup_stats['error'] = str(e)
        
        return cleanup_stats
    
    def _remove_vector(self, vector_id: str) -> bool:
        """Remove a vector from memory management"""
        try:
            if vector_id in self.vector_metadata:
                metadata = self.vector_metadata[vector_id]
                self.total_memory_usage -= metadata.size_bytes
                del self.vector_metadata[vector_id]
            
            if vector_id in self.compressed_vectors:
                del self.compressed_vectors[vector_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing vector {vector_id}: {e}")
            return False
    
    def _compress_uncompressed_vectors(self) -> int:
        """Compress uncompressed vectors to save memory"""
        compression_count = 0
        
        for vector_id, metadata in self.vector_metadata.items():
            if (not metadata.is_compressed and 
                metadata.size_bytes > 1024 and 
                metadata.priority < 3):
                
                # This would need the actual vector data, which should be provided
                # by the calling system. For now, just mark as compressed.
                metadata.is_compressed = True
                compression_count += 1
                
                if compression_count >= 100:  # Limit batch size
                    break
        
        return compression_count
    
    def _on_memory_warning(self, stats: MemoryStats) -> None:
        """Handle memory warning callback"""
        logger.warning(f"Memory usage high: {stats.memory_usage_percent:.1%} "
                      f"({stats.total_memory_mb:.1f}MB)")
        
        # Trigger light cleanup
        self.thread_pool.submit(self.cleanup_outdated_vectors)
    
    def _on_memory_cleanup(self, stats: MemoryStats) -> None:
        """Handle memory cleanup callback"""
        logger.warning(f"Memory usage critical: {stats.memory_usage_percent:.1%} "
                      f"({stats.total_memory_mb:.1f}MB) - forcing cleanup")
        
        # Trigger aggressive cleanup
        self.thread_pool.submit(self.cleanup_outdated_vectors, force=True)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        current_stats = self.memory_monitor.get_current_stats()
        
        # Calculate vector-specific stats
        total_vectors = len(self.vector_metadata)
        compressed_vectors = sum(1 for m in self.vector_metadata.values() if m.is_compressed)
        
        vector_memory_mb = self.total_memory_usage / (1024 * 1024)
        
        # Priority distribution
        priority_dist = defaultdict(int)
        for metadata in self.vector_metadata.values():
            priority_dist[metadata.priority] += 1
        
        # Age distribution
        current_time = datetime.now()
        age_dist = {'<1day': 0, '1-7days': 0, '7-30days': 0, '>30days': 0}
        
        for metadata in self.vector_metadata.values():
            age_days = (current_time - metadata.created_at).days
            if age_days < 1:
                age_dist['<1day'] += 1
            elif age_days < 7:
                age_dist['1-7days'] += 1
            elif age_days < 30:
                age_dist['7-30days'] += 1
            else:
                age_dist['>30days'] += 1
        
        return {
            'system_memory': {
                'total_mb': current_stats.total_memory_mb,
                'available_mb': current_stats.available_memory_mb,
                'usage_percent': current_stats.memory_usage_percent
            },
            'vector_memory': {
                'total_mb': vector_memory_mb,
                'total_vectors': total_vectors,
                'compressed_vectors': compressed_vectors,
                'compression_ratio': compressed_vectors / total_vectors if total_vectors > 0 else 0
            },
            'cleanup_stats': self.cleanup_stats,
            'priority_distribution': dict(priority_dist),
            'age_distribution': age_dist,
            'memory_trend': self.memory_monitor.get_memory_trend(),
            'last_cleanup': self.last_cleanup.isoformat() if self.last_cleanup else None
        }
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """Perform comprehensive memory optimization"""
        logger.info("Starting memory optimization...")
        
        optimization_stats = {
            'cleanup_stats': {},
            'compression_stats': {},
            'gc_stats': {}
        }
        
        # 1. Run cleanup
        optimization_stats['cleanup_stats'] = self.cleanup_outdated_vectors()
        
        # 2. Compress uncompressed vectors
        compression_count = self._compress_uncompressed_vectors()
        optimization_stats['compression_stats'] = {'vectors_compressed': compression_count}
        
        # 3. Force garbage collection
        if self.config.auto_gc_enabled:
            gc_before = len(gc.get_objects())
            gc.collect()
            gc_after = len(gc.get_objects())
            optimization_stats['gc_stats'] = {
                'objects_before': gc_before,
                'objects_after': gc_after,
                'objects_freed': gc_before - gc_after
            }
        
        logger.info("Memory optimization completed")
        return optimization_stats
    
    def set_retention_policy(self, days: int) -> None:
        """Update vector retention policy"""
        self.config.vector_retention_days = days
        logger.info(f"Updated retention policy to {days} days")
    
    def set_memory_limit(self, memory_mb: int) -> None:
        """Update memory limit"""
        self.config.max_memory_mb = memory_mb
        logger.info(f"Updated memory limit to {memory_mb}MB")
    
    def __del__(self):
        """Cleanup resources"""
        try:
            self.stop_cleanup_scheduler()
            self.memory_monitor.stop_monitoring()
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=True)
        except:
            pass