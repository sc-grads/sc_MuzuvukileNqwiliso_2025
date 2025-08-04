#!/usr/bin/env python3
"""
Configuration utilities for vector infrastructure integration.
Provides configuration management and integration with existing system.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from config import VECTOR_STORE_DIR

class VectorConfig:
    """Configuration management for vector infrastructure"""
    
    # Default configurations for different use cases
    DEFAULT_CONFIGS = {
        'schema_store': {
            'embedding_model': 'all-MiniLM-L6-v2',
            'index_type': 'flat',
            'store_name': 'schema_embeddings'
        },
        'query_store': {
            'embedding_model': 'all-MiniLM-L6-v2', 
            'index_type': 'flat',
            'store_name': 'query_patterns'
        },
        'learning_store': {
            'embedding_model': 'all-MiniLM-L6-v2',
            'index_type': 'hnsw',  # Better for large-scale learning
            'store_name': 'learning_patterns'
        }
    }
    
    @classmethod
    def get_config(cls, config_type: str = 'schema_store') -> Dict[str, Any]:
        """Get configuration for specific vector store type"""
        if config_type not in cls.DEFAULT_CONFIGS:
            raise ValueError(f"Unknown config type: {config_type}")
        
        config = cls.DEFAULT_CONFIGS[config_type].copy()
        
        # Override with environment variables if available
        env_prefix = f"VECTOR_{config_type.upper()}_"
        
        if os.getenv(f"{env_prefix}EMBEDDING_MODEL"):
            config['embedding_model'] = os.getenv(f"{env_prefix}EMBEDDING_MODEL")
        
        if os.getenv(f"{env_prefix}INDEX_TYPE"):
            config['index_type'] = os.getenv(f"{env_prefix}INDEX_TYPE")
        
        if os.getenv(f"{env_prefix}STORE_NAME"):
            config['store_name'] = os.getenv(f"{env_prefix}STORE_NAME")
        
        return config
    
    @classmethod
    def get_store_path(cls, store_name: str) -> str:
        """Get full path for vector store"""
        return str(Path(VECTOR_STORE_DIR) / store_name)
    
    @classmethod
    def ensure_vector_dir(cls) -> None:
        """Ensure vector storage directory exists"""
        Path(VECTOR_STORE_DIR).mkdir(parents=True, exist_ok=True)

def get_embedding_model_info() -> Dict[str, Any]:
    """Get information about available embedding models"""
    return {
        'all-MiniLM-L6-v2': {
            'dimension': 384,
            'description': 'Fast and efficient, good for general use',
            'memory_usage': 'Low',
            'performance': 'Fast'
        },
        'all-mpnet-base-v2': {
            'dimension': 768,
            'description': 'Higher quality embeddings, slower',
            'memory_usage': 'Medium',
            'performance': 'Medium'
        },
        'all-MiniLM-L12-v2': {
            'dimension': 384,
            'description': 'Better quality than L6, still fast',
            'memory_usage': 'Low-Medium',
            'performance': 'Medium-Fast'
        }
    }

def get_index_type_info() -> Dict[str, Any]:
    """Get information about FAISS index types"""
    return {
        'flat': {
            'description': 'Exact search, best for small to medium datasets',
            'search_speed': 'Medium',
            'memory_usage': 'Medium',
            'accuracy': 'Perfect'
        },
        'ivf': {
            'description': 'Approximate search with clustering, good for large datasets',
            'search_speed': 'Fast',
            'memory_usage': 'Medium',
            'accuracy': 'High'
        },
        'hnsw': {
            'description': 'Hierarchical graph-based, very fast approximate search',
            'search_speed': 'Very Fast',
            'memory_usage': 'High',
            'accuracy': 'High'
        }
    }

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate vector store configuration"""
    required_keys = ['embedding_model', 'index_type', 'store_name']
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    # Validate embedding model
    available_models = get_embedding_model_info()
    if config['embedding_model'] not in available_models:
        print(f"Warning: Unknown embedding model {config['embedding_model']}")
    
    # Validate index type
    available_indices = get_index_type_info()
    if config['index_type'] not in available_indices:
        raise ValueError(f"Unknown index type: {config['index_type']}")
    
    return True

def print_config_info():
    """Print information about available configurations"""
    print("=== Vector Infrastructure Configuration ===\n")
    
    print("Available Embedding Models:")
    for model, info in get_embedding_model_info().items():
        print(f"  {model}:")
        print(f"    Dimension: {info['dimension']}")
        print(f"    Description: {info['description']}")
        print(f"    Memory: {info['memory_usage']}, Performance: {info['performance']}")
        print()
    
    print("Available Index Types:")
    for index_type, info in get_index_type_info().items():
        print(f"  {index_type}:")
        print(f"    Description: {info['description']}")
        print(f"    Speed: {info['search_speed']}, Memory: {info['memory_usage']}, Accuracy: {info['accuracy']}")
        print()
    
    print("Default Configurations:")
    for config_name, config in VectorConfig.DEFAULT_CONFIGS.items():
        print(f"  {config_name}: {config}")
    print()

if __name__ == '__main__':
    print_config_info()