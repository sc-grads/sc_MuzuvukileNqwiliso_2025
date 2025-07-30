#!/usr/bin/env python3
"""
RAG Configuration Management - Centralized configuration for the RAG-based SQL system.

This module provides comprehensive configuration management for all RAG components,
including vector settings, model configurations, and system parameters.
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from config import VECTOR_STORE_DIR, get_current_database

@dataclass
class VectorStoreConfig:
    """Configuration for vector store components"""
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_dimension: int = 384
    index_type: str = "flat"
    similarity_metric: str = "cosine"
    storage_path: str = "vector_data/rag_system"
    cache_size: int = 1000
    batch_size: int = 100


@dataclass
class IntentEngineConfig:
    """Configuration for semantic intent engine"""
    confidence_threshold: float = 0.3
    entity_confidence_threshold: float = 0.25
    max_entities_per_query: int = 10
    enable_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.6


@dataclass
class SQLGeneratorConfig:
    """Configuration for dynamic SQL generator"""
    max_query_complexity: str = "complex"
    enable_join_optimization: bool = True
    enable_aggregation_optimization: bool = True
    default_result_limit: int = 100
    enable_advanced_features: bool = True
    sql_dialect: str = "tsql"  # T-SQL for SQL Server


@dataclass
class LearningEngineConfig:
    """Configuration for adaptive learning engine"""
    enable_learning: bool = True
    pattern_confidence_threshold: float = 0.5
    max_patterns_stored: int = 10000
    learning_rate: float = 0.1
    pattern_expiry_days: int = 365
    auto_save_interval: int = 100  # Save every N queries


@dataclass
class ErrorHandlerConfig:
    """Configuration for semantic error handler"""
    enable_error_recovery: bool = True
    max_recovery_suggestions: int = 5
    recovery_confidence_threshold: float = 0.4
    enable_automatic_retry: bool = True
    max_retry_attempts: int = 3
    fuzzy_matching_threshold: float = 0.6


@dataclass
class SystemConfig:
    """Overall system configuration"""
    enable_monitoring: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    enable_metrics: bool = True
    metrics_collection_interval: int = 60


@dataclass
class RAGSystemConfig:
    """Complete RAG system configuration"""
    vector_store: VectorStoreConfig
    intent_engine: IntentEngineConfig
    sql_generator: SQLGeneratorConfig
    learning_engine: LearningEngineConfig
    error_handler: ErrorHandlerConfig
    system: SystemConfig
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'vector_store': asdict(self.vector_store),
            'intent_engine': asdict(self.intent_engine),
            'sql_generator': asdict(self.sql_generator),
            'learning_engine': asdict(self.learning_engine),
            'error_handler': asdict(self.error_handler),
            'system': asdict(self.system)
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RAGSystemConfig':
        """Create configuration from dictionary"""
        return cls(
            vector_store=VectorStoreConfig(**config_dict.get('vector_store', {})),
            intent_engine=IntentEngineConfig(**config_dict.get('intent_engine', {})),
            sql_generator=SQLGeneratorConfig(**config_dict.get('sql_generator', {})),
            learning_engine=LearningEngineConfig(**config_dict.get('learning_engine', {})),
            error_handler=ErrorHandlerConfig(**config_dict.get('error_handler', {})),
            system=SystemConfig(**config_dict.get('system', {}))
        )


class RAGConfigManager:
    """
    Configuration manager for the RAG system.
    
    Handles loading, saving, and managing configurations with support for
    environment variable overrides and database-specific configurations.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Default configuration
        self._default_config = self._create_default_config()
        
        # Current configuration
        self._current_config: Optional[RAGSystemConfig] = None
        
        # Database-specific configurations
        self._db_configs: Dict[str, RAGSystemConfig] = {}
    
    def _create_default_config(self) -> RAGSystemConfig:
        """Create default configuration"""
        return RAGSystemConfig(
            vector_store=VectorStoreConfig(),
            intent_engine=IntentEngineConfig(),
            sql_generator=SQLGeneratorConfig(),
            learning_engine=LearningEngineConfig(),
            error_handler=ErrorHandlerConfig(),
            system=SystemConfig()
        )
    
    def get_config(self, database_name: Optional[str] = None) -> RAGSystemConfig:
        """
        Get configuration for specified database or current database.
        
        Args:
            database_name: Database name (uses current database if None)
            
        Returns:
            RAGSystemConfig for the specified database
        """
        if database_name is None:
            database_name = get_current_database()
        
        # Check if we have a database-specific configuration
        if database_name in self._db_configs:
            return self._db_configs[database_name]
        
        # Load configuration from file if exists
        config_file = self.config_dir / f"rag_config_{database_name}.json"
        if config_file.exists():
            config = self._load_config_from_file(config_file)
            self._db_configs[database_name] = config
            return config
        
        # Return default configuration with environment overrides
        config = self._apply_environment_overrides(self._default_config)
        self._db_configs[database_name] = config
        return config
    
    def save_config(self, config: RAGSystemConfig, database_name: Optional[str] = None):
        """
        Save configuration for specified database.
        
        Args:
            config: Configuration to save
            database_name: Database name (uses current database if None)
        """
        if database_name is None:
            database_name = get_current_database()
        
        config_file = self.config_dir / f"rag_config_{database_name}.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            # Update cached configuration
            self._db_configs[database_name] = config
            
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration: {e}")
    
    def _load_config_from_file(self, config_file: Path) -> RAGSystemConfig:
        """Load configuration from file"""
        try:
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
            
            # Apply environment overrides
            config = RAGSystemConfig.from_dict(config_dict)
            return self._apply_environment_overrides(config)
            
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration from {config_file}: {e}")
    
    def _apply_environment_overrides(self, config: RAGSystemConfig) -> RAGSystemConfig:
        """Apply environment variable overrides to configuration"""
        
        # Vector store overrides
        if os.getenv("RAG_EMBEDDING_MODEL"):
            config.vector_store.embedding_model = os.getenv("RAG_EMBEDDING_MODEL")
        
        if os.getenv("RAG_INDEX_TYPE"):
            config.vector_store.index_type = os.getenv("RAG_INDEX_TYPE")
        
        if os.getenv("RAG_STORAGE_PATH"):
            config.vector_store.storage_path = os.getenv("RAG_STORAGE_PATH")
        
        # Intent engine overrides
        if os.getenv("RAG_CONFIDENCE_THRESHOLD"):
            config.intent_engine.confidence_threshold = float(os.getenv("RAG_CONFIDENCE_THRESHOLD"))
        
        # SQL generator overrides
        if os.getenv("RAG_MAX_COMPLEXITY"):
            config.sql_generator.max_query_complexity = os.getenv("RAG_MAX_COMPLEXITY")
        
        if os.getenv("RAG_RESULT_LIMIT"):
            config.sql_generator.default_result_limit = int(os.getenv("RAG_RESULT_LIMIT"))
        
        # Learning engine overrides
        if os.getenv("RAG_ENABLE_LEARNING"):
            config.learning_engine.enable_learning = os.getenv("RAG_ENABLE_LEARNING").lower() == "true"
        
        if os.getenv("RAG_MAX_PATTERNS"):
            config.learning_engine.max_patterns_stored = int(os.getenv("RAG_MAX_PATTERNS"))
        
        # Error handler overrides
        if os.getenv("RAG_ENABLE_ERROR_RECOVERY"):
            config.error_handler.enable_error_recovery = os.getenv("RAG_ENABLE_ERROR_RECOVERY").lower() == "true"
        
        if os.getenv("RAG_MAX_SUGGESTIONS"):
            config.error_handler.max_recovery_suggestions = int(os.getenv("RAG_MAX_SUGGESTIONS"))
        
        # System overrides
        if os.getenv("RAG_LOG_LEVEL"):
            config.system.log_level = os.getenv("RAG_LOG_LEVEL")
        
        if os.getenv("RAG_ENABLE_CACHING"):
            config.system.enable_caching = os.getenv("RAG_ENABLE_CACHING").lower() == "true"
        
        return config
    
    def create_database_config(self, 
                              database_name: str,
                              base_config: Optional[RAGSystemConfig] = None,
                              overrides: Dict[str, Any] = None) -> RAGSystemConfig:
        """
        Create a database-specific configuration.
        
        Args:
            database_name: Name of the database
            base_config: Base configuration (uses default if None)
            overrides: Configuration overrides
            
        Returns:
            Database-specific RAGSystemConfig
        """
        if base_config is None:
            base_config = self._default_config
        
        # Create a copy of the base configuration
        config_dict = base_config.to_dict()
        
        # Apply database-specific overrides
        if overrides:
            self._deep_update(config_dict, overrides)
        
        # Update storage paths to be database-specific
        config_dict['vector_store']['storage_path'] = f"vector_data/rag_system_{database_name}"
        
        # Create and save the configuration
        config = RAGSystemConfig.from_dict(config_dict)
        self.save_config(config, database_name)
        
        return config
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """Deep update dictionary with another dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def list_database_configs(self) -> List[str]:
        """List all available database configurations"""
        config_files = list(self.config_dir.glob("rag_config_*.json"))
        return [f.stem.replace("rag_config_", "") for f in config_files]
    
    def delete_database_config(self, database_name: str):
        """Delete configuration for specified database"""
        config_file = self.config_dir / f"rag_config_{database_name}.json"
        
        if config_file.exists():
            config_file.unlink()
        
        # Remove from cache
        if database_name in self._db_configs:
            del self._db_configs[database_name]
    
    def validate_config(self, config: RAGSystemConfig) -> List[str]:
        """
        Validate configuration and return list of issues.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Validate vector store configuration
        if config.vector_store.vector_dimension <= 0:
            issues.append("Vector dimension must be positive")
        
        if config.vector_store.cache_size <= 0:
            issues.append("Cache size must be positive")
        
        # Validate intent engine configuration
        if not (0.0 <= config.intent_engine.confidence_threshold <= 1.0):
            issues.append("Intent confidence threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= config.intent_engine.entity_confidence_threshold <= 1.0):
            issues.append("Entity confidence threshold must be between 0.0 and 1.0")
        
        # Validate SQL generator configuration
        valid_complexities = ["simple", "moderate", "complex", "very_complex"]
        if config.sql_generator.max_query_complexity not in valid_complexities:
            issues.append(f"Max query complexity must be one of: {valid_complexities}")
        
        if config.sql_generator.default_result_limit <= 0:
            issues.append("Default result limit must be positive")
        
        # Validate learning engine configuration
        if not (0.0 <= config.learning_engine.pattern_confidence_threshold <= 1.0):
            issues.append("Pattern confidence threshold must be between 0.0 and 1.0")
        
        if config.learning_engine.max_patterns_stored <= 0:
            issues.append("Max patterns stored must be positive")
        
        if not (0.0 <= config.learning_engine.learning_rate <= 1.0):
            issues.append("Learning rate must be between 0.0 and 1.0")
        
        # Validate error handler configuration
        if config.error_handler.max_recovery_suggestions <= 0:
            issues.append("Max recovery suggestions must be positive")
        
        if not (0.0 <= config.error_handler.recovery_confidence_threshold <= 1.0):
            issues.append("Recovery confidence threshold must be between 0.0 and 1.0")
        
        if config.error_handler.max_retry_attempts <= 0:
            issues.append("Max retry attempts must be positive")
        
        # Validate system configuration
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.system.log_level not in valid_log_levels:
            issues.append(f"Log level must be one of: {valid_log_levels}")
        
        if config.system.cache_ttl_seconds <= 0:
            issues.append("Cache TTL must be positive")
        
        return issues
    
    def get_config_summary(self, database_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.
        
        Args:
            database_name: Database name (uses current database if None)
            
        Returns:
            Configuration summary dictionary
        """
        config = self.get_config(database_name)
        
        return {
            'database': database_name or get_current_database(),
            'embedding_model': config.vector_store.embedding_model,
            'vector_dimension': config.vector_store.vector_dimension,
            'learning_enabled': config.learning_engine.enable_learning,
            'error_recovery_enabled': config.error_handler.enable_error_recovery,
            'max_patterns': config.learning_engine.max_patterns_stored,
            'confidence_threshold': config.intent_engine.confidence_threshold,
            'result_limit': config.sql_generator.default_result_limit,
            'storage_path': config.vector_store.storage_path,
            'log_level': config.system.log_level
        }


# Global configuration manager instance
_config_manager = None

def get_config_manager() -> RAGConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = RAGConfigManager()
    return _config_manager

def get_rag_config(database_name: Optional[str] = None) -> RAGSystemConfig:
    """Get RAG configuration for specified database"""
    return get_config_manager().get_config(database_name)

def save_rag_config(config: RAGSystemConfig, database_name: Optional[str] = None):
    """Save RAG configuration for specified database"""
    get_config_manager().save_config(config, database_name)


# Example usage and configuration templates
if __name__ == "__main__":
    # Create configuration manager
    config_manager = RAGConfigManager()
    
    # Get default configuration
    default_config = config_manager.get_config()
    print("Default Configuration:")
    print(json.dumps(default_config.to_dict(), indent=2))
    
    # Create a high-performance configuration
    high_perf_overrides = {
        'vector_store': {
            'embedding_model': 'all-mpnet-base-v2',
            'index_type': 'hnsw',
            'cache_size': 5000
        },
        'learning_engine': {
            'max_patterns_stored': 50000,
            'auto_save_interval': 50
        },
        'error_handler': {
            'max_recovery_suggestions': 10
        }
    }
    
    high_perf_config = config_manager.create_database_config(
        "HighPerformanceDB",
        overrides=high_perf_overrides
    )
    
    print("\nHigh Performance Configuration Created")
    
    # Validate configuration
    issues = config_manager.validate_config(high_perf_config)
    if issues:
        print(f"Configuration issues: {issues}")
    else:
        print("Configuration is valid")
    
    # Show configuration summary
    summary = config_manager.get_config_summary("HighPerformanceDB")
    print(f"\nConfiguration Summary: {summary}")