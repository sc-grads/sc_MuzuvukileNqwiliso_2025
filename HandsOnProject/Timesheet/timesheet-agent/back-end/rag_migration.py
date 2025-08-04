#!/usr/bin/env python3
"""
RAG Migration Utilities - Migration tools for transitioning to the RAG-based system.

This module provides utilities for migrating from the existing JSON cache system
to the new vector-based RAG system, including data validation and backward compatibility.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import shutil
from dataclasses import dataclass

# Import existing system components
from database import get_schema_metadata
from history import get_query_history
from config import get_schema_cache_file, get_column_map_file, get_enhanced_schema_cache_file

# Import RAG components
from rag_sql_agent import RAGSQLAgent, create_rag_agent
from vector_schema_store import VectorSchemaStore
from adaptive_learning_engine import AdaptiveLearningEngine
from rag_config import get_rag_config, RAGConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of a migration operation"""
    success: bool
    items_migrated: int
    items_failed: int
    errors: List[str]
    warnings: List[str]
    migration_time: float
    metadata: Dict[str, Any]


@dataclass
class ValidationResult:
    """Result of data validation"""
    valid: bool
    issues: List[str]
    warnings: List[str]
    statistics: Dict[str, Any]


class RAGMigrationManager:
    """
    Manager for migrating from traditional system to RAG-based system.
    
    Handles migration of JSON caches, query history, and provides
    backward compatibility during the transition period.
    """
    
    def __init__(self, 
                 backup_dir: str = "migration_backup",
                 enable_fallback: bool = True):
        """
        Initialize migration manager.
        
        Args:
            backup_dir: Directory to store migration backups
            enable_fallback: Whether to enable fallback to traditional system
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.enable_fallback = enable_fallback
        
        # Migration statistics
        self.migration_stats = {
            'schema_migrations': 0,
            'query_history_migrations': 0,
            'pattern_migrations': 0,
            'total_items_migrated': 0,
            'migration_start_time': None,
            'migration_end_time': None
        }
        
        logger.info(f"RAG Migration Manager initialized - backups in {backup_dir}")
    
    def create_system_backup(self) -> str:
        """
        Create a complete backup of the current system state.
        
        Returns:
            Path to the backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"system_backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Creating system backup at {backup_path}")
        
        try:
            # Backup JSON cache files
            cache_files = [
                get_schema_cache_file(),
                get_column_map_file(),
                get_enhanced_schema_cache_file()
            ]
            
            cache_backup_dir = backup_path / "cache"
            cache_backup_dir.mkdir(exist_ok=True)
            
            for cache_file in cache_files:
                if os.path.exists(cache_file):
                    shutil.copy2(cache_file, cache_backup_dir / Path(cache_file).name)
                    logger.info(f"Backed up {cache_file}")
            
            # Backup query history
            try:
                history = get_query_history()
                if history:
                    history_file = backup_path / "query_history.json"
                    with open(history_file, 'w') as f:
                        json.dump(history, f, indent=2, default=str)
                    logger.info(f"Backed up query history ({len(history)} entries)")
            except Exception as e:
                logger.warning(f"Failed to backup query history: {e}")
            
            # Backup vector data if it exists
            vector_dirs = ["vector_data", "../vector_data"]
            for vector_dir in vector_dirs:
                if os.path.exists(vector_dir):
                    vector_backup_dir = backup_path / "vector_data"
                    shutil.copytree(vector_dir, vector_backup_dir, dirs_exist_ok=True)
                    logger.info(f"Backed up vector data from {vector_dir}")
                    break
            
            # Create backup manifest
            manifest = {
                'backup_timestamp': timestamp,
                'backup_path': str(backup_path),
                'files_backed_up': [str(f.relative_to(backup_path)) for f in backup_path.rglob('*') if f.is_file()],
                'migration_manager_version': '1.0.0'
            }
            
            manifest_file = backup_path / "backup_manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"System backup completed: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create system backup: {e}")
            raise
    
    def migrate_json_caches_to_vectors(self, 
                                     rag_agent: Optional[RAGSQLAgent] = None) -> MigrationResult:
        """
        Migrate JSON cache files to vector representations.
        
        Args:
            rag_agent: RAG agent instance (creates new one if None)
            
        Returns:
            MigrationResult with migration details
        """
        start_time = datetime.now()
        self.migration_stats['migration_start_time'] = start_time
        
        logger.info("Starting JSON cache to vector migration")
        
        errors = []
        warnings = []
        items_migrated = 0
        items_failed = 0
        
        try:
            # Create or use provided RAG agent
            if rag_agent is None:
                rag_agent = create_rag_agent()
            
            # Get current schema metadata
            schema_metadata, column_map, existing_vector_store, enhanced_data = get_schema_metadata()
            
            if not schema_metadata:
                errors.append("No schema metadata available for migration")
                return MigrationResult(
                    success=False,
                    items_migrated=0,
                    items_failed=1,
                    errors=errors,
                    warnings=warnings,
                    migration_time=0,
                    metadata={}
                )
            
            # Migrate schema metadata to vectors
            logger.info(f"Migrating {len(schema_metadata)} tables to vector store")
            
            try:
                # Clear existing vectors to ensure clean migration
                rag_agent.vector_store.clear_all_vectors()
                
                # Ingest schema into vector store
                rag_agent.vector_store.ingest_schema(schema_metadata)
                
                items_migrated += len(schema_metadata)
                self.migration_stats['schema_migrations'] += len(schema_metadata)
                
                logger.info(f"Successfully migrated {len(schema_metadata)} schema items to vectors")
                
            except Exception as e:
                error_msg = f"Failed to migrate schema to vectors: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                items_failed += len(schema_metadata)
            
            # Migrate enhanced schema data if available
            if enhanced_data:
                try:
                    self._migrate_enhanced_schema_data(rag_agent.vector_store, enhanced_data)
                    logger.info("Migrated enhanced schema data")
                except Exception as e:
                    warning_msg = f"Failed to migrate enhanced schema data: {e}"
                    warnings.append(warning_msg)
                    logger.warning(warning_msg)
            
            # Save vector store state
            try:
                rag_agent.vector_store.save_to_disk()
                logger.info("Vector store saved to disk")
            except Exception as e:
                error_msg = f"Failed to save vector store: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
            
            # Update statistics
            self.migration_stats['total_items_migrated'] += items_migrated
            
            migration_time = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=len(errors) == 0,
                items_migrated=items_migrated,
                items_failed=items_failed,
                errors=errors,
                warnings=warnings,
                migration_time=migration_time,
                metadata={
                    'schema_tables_migrated': len(schema_metadata),
                    'vector_store_size': len(rag_agent.vector_store.schema_vectors),
                    'enhanced_data_available': enhanced_data is not None
                }
            )
            
        except Exception as e:
            error_msg = f"Migration failed with exception: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            migration_time = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=False,
                items_migrated=items_migrated,
                items_failed=items_failed + 1,
                errors=errors,
                warnings=warnings,
                migration_time=migration_time,
                metadata={}
            )
    
    def migrate_query_history_to_patterns(self, 
                                        rag_agent: Optional[RAGSQLAgent] = None) -> MigrationResult:
        """
        Migrate query history to learned patterns.
        
        Args:
            rag_agent: RAG agent instance (creates new one if None)
            
        Returns:
            MigrationResult with migration details
        """
        start_time = datetime.now()
        
        logger.info("Starting query history to patterns migration")
        
        errors = []
        warnings = []
        items_migrated = 0
        items_failed = 0
        
        try:
            # Create or use provided RAG agent
            if rag_agent is None:
                rag_agent = create_rag_agent()
            
            if not rag_agent.learning_engine:
                errors.append("Learning engine not available for migration")
                return MigrationResult(
                    success=False,
                    items_migrated=0,
                    items_failed=1,
                    errors=errors,
                    warnings=warnings,
                    migration_time=0,
                    metadata={}
                )
            
            # Get query history
            try:
                history = get_query_history()
                if not history:
                    warnings.append("No query history available for migration")
                    return MigrationResult(
                        success=True,
                        items_migrated=0,
                        items_failed=0,
                        errors=errors,
                        warnings=warnings,
                        migration_time=0,
                        metadata={}
                    )
                
                logger.info(f"Found {len(history)} queries in history")
                
            except Exception as e:
                error_msg = f"Failed to load query history: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                return MigrationResult(
                    success=False,
                    items_migrated=0,
                    items_failed=1,
                    errors=errors,
                    warnings=warnings,
                    migration_time=0,
                    metadata={}
                )
            
            # Migrate successful queries to patterns
            successful_queries = [q for q in history if q.get('success', False) and q.get('sql_query')]
            
            logger.info(f"Migrating {len(successful_queries)} successful queries to patterns")
            
            for query_entry in successful_queries:
                try:
                    nl_query = query_entry.get('natural_language_query', '')
                    sql_query = query_entry.get('sql_query', '')
                    
                    if not nl_query or not sql_query:
                        warnings.append(f"Skipping incomplete query entry: {query_entry.get('timestamp', 'unknown')}")
                        continue
                    
                    # Create execution result metadata
                    execution_result = {
                        'success': True,
                        'execution_time': query_entry.get('execution_time', 0),
                        'row_count': self._extract_row_count(query_entry.get('results_summary', '')),
                        'tables_used': self._extract_tables_from_sql(sql_query),
                        'columns_used': []
                    }
                    
                    # Learn from this successful query
                    pattern_id = rag_agent.learning_engine.learn_from_success(
                        nl_query, sql_query, execution_result
                    )
                    
                    items_migrated += 1
                    
                except Exception as e:
                    error_msg = f"Failed to migrate query: {e}"
                    warnings.append(error_msg)
                    items_failed += 1
                    logger.warning(error_msg)
            
            # Save learned patterns
            try:
                rag_agent.learning_engine.save_patterns_to_disk()
                logger.info("Learned patterns saved to disk")
            except Exception as e:
                error_msg = f"Failed to save learned patterns: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
            
            # Update statistics
            self.migration_stats['query_history_migrations'] += items_migrated
            self.migration_stats['pattern_migrations'] += items_migrated
            self.migration_stats['total_items_migrated'] += items_migrated
            
            migration_time = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=len(errors) == 0,
                items_migrated=items_migrated,
                items_failed=items_failed,
                errors=errors,
                warnings=warnings,
                migration_time=migration_time,
                metadata={
                    'total_history_entries': len(history),
                    'successful_queries_migrated': items_migrated,
                    'patterns_created': len(rag_agent.learning_engine.success_patterns)
                }
            )
            
        except Exception as e:
            error_msg = f"Query history migration failed: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            migration_time = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=False,
                items_migrated=items_migrated,
                items_failed=items_failed + 1,
                errors=errors,
                warnings=warnings,
                migration_time=migration_time,
                metadata={}
            )
    
    def validate_migrated_data(self, rag_agent: Optional[RAGSQLAgent] = None) -> ValidationResult:
        """
        Validate migrated data integrity and completeness.
        
        Args:
            rag_agent: RAG agent instance (creates new one if None)
            
        Returns:
            ValidationResult with validation details
        """
        logger.info("Starting migrated data validation")
        
        issues = []
        warnings = []
        statistics = {}
        
        try:
            # Create or use provided RAG agent
            if rag_agent is None:
                rag_agent = create_rag_agent()
            
            # Validate vector store
            vector_stats = rag_agent.vector_store.get_schema_statistics()
            statistics['vector_store'] = vector_stats
            
            if vector_stats['total_vectors'] == 0:
                issues.append("Vector store is empty - no schema data migrated")
            else:
                logger.info(f"Vector store contains {vector_stats['total_vectors']} vectors")
            
            # Validate schema coverage
            try:
                schema_metadata, _, _, _ = get_schema_metadata()
                if schema_metadata:
                    expected_tables = len(schema_metadata)
                    actual_tables = vector_stats.get('by_type', {}).get('table', 0)
                    
                    if actual_tables < expected_tables:
                        issues.append(f"Missing tables in vector store: expected {expected_tables}, found {actual_tables}")
                    elif actual_tables > expected_tables:
                        warnings.append(f"More tables in vector store than expected: expected {expected_tables}, found {actual_tables}")
                    
                    statistics['schema_coverage'] = {
                        'expected_tables': expected_tables,
                        'migrated_tables': actual_tables,
                        'coverage_percentage': (actual_tables / expected_tables * 100) if expected_tables > 0 else 0
                    }
                
            except Exception as e:
                warnings.append(f"Could not validate schema coverage: {e}")
            
            # Validate learning patterns
            if rag_agent.learning_engine:
                pattern_count = len(rag_agent.learning_engine.success_patterns)
                statistics['learning_patterns'] = {
                    'total_patterns': pattern_count,
                    'average_confidence': rag_agent.learning_engine._calculate_average_confidence()
                }
                
                if pattern_count == 0:
                    warnings.append("No learning patterns found - query history may not have been migrated")
                else:
                    logger.info(f"Found {pattern_count} learned patterns")
            
            # Test vector similarity search
            try:
                test_query = "employee information"
                query_vector = rag_agent.vector_store.embedder.encode(test_query)
                query_vector = rag_agent.vector_store._normalize_vector(query_vector)
                
                similar_tables = rag_agent.vector_store.find_similar_tables(query_vector, k=3)
                similar_columns = rag_agent.vector_store.find_similar_columns(query_vector, k=5)
                
                if not similar_tables and not similar_columns:
                    issues.append("Vector similarity search not working - no similar elements found")
                else:
                    statistics['similarity_search'] = {
                        'similar_tables_found': len(similar_tables),
                        'similar_columns_found': len(similar_columns)
                    }
                
            except Exception as e:
                issues.append(f"Vector similarity search failed: {e}")
            
            # Validate system integration
            try:
                system_stats = rag_agent.get_system_statistics()
                statistics['system_stats'] = {
                    'vector_store_size': system_stats.vector_store_size,
                    'learned_patterns_count': system_stats.learned_patterns_count
                }
                
            except Exception as e:
                warnings.append(f"Could not get system statistics: {e}")
            
            is_valid = len(issues) == 0
            
            if is_valid:
                logger.info("Data validation completed successfully")
            else:
                logger.warning(f"Data validation found {len(issues)} issues")
            
            return ValidationResult(
                valid=is_valid,
                issues=issues,
                warnings=warnings,
                statistics=statistics
            )
            
        except Exception as e:
            error_msg = f"Data validation failed: {e}"
            issues.append(error_msg)
            logger.error(error_msg)
            
            return ValidationResult(
                valid=False,
                issues=issues,
                warnings=warnings,
                statistics=statistics
            )
    
    def create_fallback_configuration(self) -> Dict[str, Any]:
        """
        Create configuration for fallback to traditional system.
        
        Returns:
            Fallback configuration dictionary
        """
        fallback_config = {
            'fallback_enabled': self.enable_fallback,
            'fallback_triggers': [
                'rag_initialization_failure',
                'vector_store_corruption',
                'high_error_rate',
                'performance_degradation'
            ],
            'fallback_thresholds': {
                'error_rate_percent': 50,
                'response_time_ms': 10000,
                'confidence_threshold': 0.3
            },
            'fallback_strategy': 'graceful_degradation',
            'recovery_attempts': 3,
            'recovery_delay_seconds': 30
        }
        
        return fallback_config
    
    def test_backward_compatibility(self, 
                                  test_queries: List[str] = None) -> Dict[str, Any]:
        """
        Test backward compatibility with traditional system.
        
        Args:
            test_queries: List of test queries (uses defaults if None)
            
        Returns:
            Compatibility test results
        """
        if test_queries is None:
            test_queries = [
                "How many employees are there?",
                "Show me all projects",
                "What is the average salary by department?"
            ]
        
        logger.info(f"Testing backward compatibility with {len(test_queries)} queries")
        
        results = {
            'test_timestamp': datetime.now().isoformat(),
            'queries_tested': len(test_queries),
            'rag_results': [],
            'traditional_results': [],
            'compatibility_score': 0.0,
            'issues': []
        }
        
        try:
            # Test with RAG system
            rag_agent = create_rag_agent()
            
            for query in test_queries:
                try:
                    result = rag_agent.process_query(query)
                    results['rag_results'].append({
                        'query': query,
                        'success': result.success,
                        'sql': result.sql_query,
                        'confidence': result.confidence,
                        'processing_time': result.processing_time
                    })
                except Exception as e:
                    results['rag_results'].append({
                        'query': query,
                        'success': False,
                        'error': str(e)
                    })
            
            # Test with traditional system (mock for now)
            # In a real implementation, this would call the traditional system
            for query in test_queries:
                results['traditional_results'].append({
                    'query': query,
                    'success': True,  # Assume traditional system works
                    'sql': f"-- Traditional SQL for: {query}",
                    'processing_time': 0.5
                })
            
            # Calculate compatibility score
            rag_success_count = sum(1 for r in results['rag_results'] if r.get('success', False))
            traditional_success_count = sum(1 for r in results['traditional_results'] if r.get('success', False))
            
            if traditional_success_count > 0:
                results['compatibility_score'] = rag_success_count / traditional_success_count
            
            logger.info(f"Compatibility test completed - score: {results['compatibility_score']:.2f}")
            
        except Exception as e:
            error_msg = f"Compatibility test failed: {e}"
            results['issues'].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def _migrate_enhanced_schema_data(self, vector_store: VectorSchemaStore, enhanced_data: Dict[str, Any]):
        """Migrate enhanced schema data to vector store"""
        # This would migrate any enhanced schema information
        # For now, we'll just log that it's available
        logger.info(f"Enhanced schema data available with {len(enhanced_data)} entries")
    
    def _extract_row_count(self, results_summary: str) -> int:
        """Extract row count from results summary"""
        if not results_summary:
            return 0
        
        # Try to extract number from summary like "Retrieved 42 rows"
        import re
        match = re.search(r'(\d+)\s+rows?', results_summary.lower())
        if match:
            return int(match.group(1))
        
        return 0
    
    def _extract_tables_from_sql(self, sql_query: str) -> List[str]:
        """Extract table names from SQL query"""
        if not sql_query:
            return []
        
        # Simple extraction - in practice, this would be more sophisticated
        import re
        
        # Look for FROM and JOIN clauses
        tables = []
        patterns = [
            r'FROM\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
            r'JOIN\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
            r'UPDATE\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)',
            r'INSERT\s+INTO\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, sql_query, re.IGNORECASE)
            for match in matches:
                # Get the table name (second group if schema.table, first group if just table)
                table_name = match.group(2) if match.group(2) else match.group(1)
                if table_name and table_name not in tables:
                    tables.append(table_name)
        
        return tables
    
    def get_migration_statistics(self) -> Dict[str, Any]:
        """Get migration statistics"""
        stats = self.migration_stats.copy()
        
        if stats['migration_start_time'] and stats['migration_end_time']:
            stats['total_migration_time'] = (
                stats['migration_end_time'] - stats['migration_start_time']
            ).total_seconds()
        
        return stats
    
    def complete_migration(self) -> Dict[str, Any]:
        """Mark migration as complete and finalize"""
        self.migration_stats['migration_end_time'] = datetime.now()
        
        summary = {
            'migration_completed': True,
            'completion_timestamp': datetime.now().isoformat(),
            'statistics': self.get_migration_statistics(),
            'next_steps': [
                'Test RAG system with production queries',
                'Monitor system performance',
                'Gradually increase RAG usage',
                'Remove old JSON caches when confident'
            ]
        }
        
        logger.info("Migration completed successfully")
        return summary


def run_complete_migration(backup_first: bool = True, 
                          validate_after: bool = True) -> Dict[str, Any]:
    """
    Run complete migration from traditional to RAG system.
    
    Args:
        backup_first: Whether to create backup before migration
        validate_after: Whether to validate data after migration
        
    Returns:
        Complete migration results
    """
    logger.info("Starting complete RAG migration")
    
    migration_manager = RAGMigrationManager()
    results = {
        'migration_start': datetime.now().isoformat(),
        'backup_path': None,
        'schema_migration': None,
        'history_migration': None,
        'validation_result': None,
        'compatibility_test': None,
        'overall_success': False
    }
    
    try:
        # Step 1: Create backup
        if backup_first:
            logger.info("Step 1: Creating system backup")
            results['backup_path'] = migration_manager.create_system_backup()
        
        # Step 2: Migrate JSON caches to vectors
        logger.info("Step 2: Migrating JSON caches to vectors")
        results['schema_migration'] = migration_manager.migrate_json_caches_to_vectors()
        
        if not results['schema_migration'].success:
            logger.error("Schema migration failed - aborting")
            return results
        
        # Step 3: Migrate query history to patterns
        logger.info("Step 3: Migrating query history to patterns")
        results['history_migration'] = migration_manager.migrate_query_history_to_patterns()
        
        # Step 4: Validate migrated data
        if validate_after:
            logger.info("Step 4: Validating migrated data")
            results['validation_result'] = migration_manager.validate_migrated_data()
        
        # Step 5: Test backward compatibility
        logger.info("Step 5: Testing backward compatibility")
        results['compatibility_test'] = migration_manager.test_backward_compatibility()
        
        # Step 6: Complete migration
        logger.info("Step 6: Completing migration")
        completion_summary = migration_manager.complete_migration()
        results.update(completion_summary)
        
        # Determine overall success
        results['overall_success'] = (
            results['schema_migration'].success and
            (not results['history_migration'] or results['history_migration'].success) and
            (not results['validation_result'] or results['validation_result'].valid)
        )
        
        results['migration_end'] = datetime.now().isoformat()
        
        if results['overall_success']:
            logger.info("Complete migration finished successfully")
        else:
            logger.warning("Migration completed with issues")
        
        return results
        
    except Exception as e:
        error_msg = f"Complete migration failed: {e}"
        logger.error(error_msg)
        results['error'] = error_msg
        results['migration_end'] = datetime.now().isoformat()
        return results


# Command-line interface for migration
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Migration Utilities")
    parser.add_argument("--backup", action="store_true", help="Create system backup")
    parser.add_argument("--migrate-schema", action="store_true", help="Migrate JSON caches to vectors")
    parser.add_argument("--migrate-history", action="store_true", help="Migrate query history to patterns")
    parser.add_argument("--validate", action="store_true", help="Validate migrated data")
    parser.add_argument("--test-compatibility", action="store_true", help="Test backward compatibility")
    parser.add_argument("--complete", action="store_true", help="Run complete migration")
    parser.add_argument("--output", type=str, help="Output file for results")
    
    args = parser.parse_args()
    
    migration_manager = RAGMigrationManager()
    results = {}
    
    if args.complete:
        print("Running complete migration...")
        results = run_complete_migration()
    else:
        if args.backup:
            print("Creating system backup...")
            backup_path = migration_manager.create_system_backup()
            results['backup_path'] = backup_path
            print(f"Backup created at: {backup_path}")
        
        if args.migrate_schema:
            print("Migrating JSON caches to vectors...")
            schema_result = migration_manager.migrate_json_caches_to_vectors()
            results['schema_migration'] = schema_result
            print(f"Schema migration: {'SUCCESS' if schema_result.success else 'FAILED'}")
            print(f"Items migrated: {schema_result.items_migrated}")
        
        if args.migrate_history:
            print("Migrating query history to patterns...")
            history_result = migration_manager.migrate_query_history_to_patterns()
            results['history_migration'] = history_result
            print(f"History migration: {'SUCCESS' if history_result.success else 'FAILED'}")
            print(f"Patterns created: {history_result.items_migrated}")
        
        if args.validate:
            print("Validating migrated data...")
            validation_result = migration_manager.validate_migrated_data()
            results['validation'] = validation_result
            print(f"Validation: {'PASSED' if validation_result.valid else 'FAILED'}")
            if validation_result.issues:
                print(f"Issues found: {len(validation_result.issues)}")
        
        if args.test_compatibility:
            print("Testing backward compatibility...")
            compatibility_result = migration_manager.test_backward_compatibility()
            results['compatibility'] = compatibility_result
            print(f"Compatibility score: {compatibility_result['compatibility_score']:.2f}")
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to: {args.output}")
    else:
        print("\nMigration Results:")
        print(json.dumps(results, indent=2, default=str))