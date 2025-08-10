#!/usr/bin/env python3
"""
Dynamic Schema Guidance System - Database Agnostic
Automatically learns schema patterns and provides guidance without hardcoding.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class SchemaPattern:
    """Represents a discovered schema pattern"""
    pattern_type: str
    confidence: float
    tables: List[str]
    columns: List[str]
    relationships: List[Dict]
    guidance: str

@dataclass
class TablePurpose:
    """Represents the inferred purpose of a table"""
    table_name: str
    purpose_type: str  # 'transactional', 'lookup', 'fact', 'dimension', 'bridge'
    confidence: float
    key_indicators: List[str]
    related_tables: List[str]

class DynamicSchemaAnalyzer:
    """
    Analyzes any database schema dynamically to provide intelligent guidance.
    No hardcoded business logic - learns from the actual schema structure.
    """
    
    def __init__(self):
        self.table_purposes = {}
        self.common_patterns = {}
        self.relationship_graph = {}
        self.column_patterns = {}
        
    def analyze_schema(self, schema_metadata: List[Dict]) -> Dict[str, Any]:
        """
        Dynamically analyze any database schema to understand its structure.
        
        Args:
            schema_metadata: Raw schema metadata from get_schema_metadata()
            
        Returns:
            Dictionary with discovered patterns and guidance
        """
        logger.info("Dynamic Schema Analyzer: Starting analysis of database schema")
        
        analysis_result = {
            'table_purposes': {},
            'relationship_patterns': {},
            'column_patterns': {},
            'query_guidance': {},
            'common_joins': {},
            'data_flow_patterns': {}
        }
        
        # Step 1: Analyze table purposes
        analysis_result['table_purposes'] = self._analyze_table_purposes(schema_metadata)
        
        # Step 2: Analyze relationship patterns
        analysis_result['relationship_patterns'] = self._analyze_relationship_patterns(schema_metadata)
        
        # Step 3: Analyze column patterns
        analysis_result['column_patterns'] = self._analyze_column_patterns(schema_metadata)
        
        # Step 4: Generate query guidance
        analysis_result['query_guidance'] = self._generate_dynamic_query_guidance(
            analysis_result['table_purposes'],
            analysis_result['relationship_patterns'],
            analysis_result['column_patterns']
        )
        
        # Step 5: Identify common join patterns
        analysis_result['common_joins'] = self._identify_common_join_patterns(schema_metadata)
        
        logger.info(f"Dynamic Schema Analyzer: Analysis complete for {len(schema_metadata)} tables")
        return analysis_result
    
    def _analyze_table_purposes(self, schema_metadata: List[Dict]) -> Dict[str, TablePurpose]:
        """
        Dynamically infer the purpose of each table based on its structure.
        """
        table_purposes = {}
        
        for table_info in schema_metadata:
            table_name = table_info['table']
            columns = table_info.get('columns', [])
            relationships = table_info.get('relationships', [])
            
            # Analyze column patterns to infer purpose
            column_names = [col['name'].lower() for col in columns]
            column_types = [col.get('type', '').lower() for col in columns]
            
            purpose_indicators = {
                'transactional': 0,  # Main business data (orders, transactions, timesheets)
                'lookup': 0,         # Reference data (clients, employees, categories)
                'fact': 0,           # Metrics/measurements (sales, hours, quantities)
                'dimension': 0,      # Descriptive attributes (time, geography, products)
                'bridge': 0          # Many-to-many relationships
            }
            
            # Analyze column patterns
            for col_name in column_names:
                # Transactional indicators
                if any(word in col_name for word in ['date', 'time', 'created', 'modified', 'status']):
                    purpose_indicators['transactional'] += 2
                if any(word in col_name for word in ['total', 'amount', 'quantity', 'hours', 'count']):
                    purpose_indicators['transactional'] += 3
                    purpose_indicators['fact'] += 2
                
                # Lookup table indicators
                if col_name.endswith('name') or col_name.endswith('title') or col_name.endswith('description'):
                    purpose_indicators['lookup'] += 2
                if col_name.endswith('id') and col_name != f"{table_name.lower()}id":
                    purpose_indicators['transactional'] += 1  # Foreign keys suggest transactional
                
                # Dimension indicators
                if any(word in col_name for word in ['category', 'type', 'group', 'class']):
                    purpose_indicators['dimension'] += 2
            
            # Analyze relationships
            if len(relationships) > 3:
                purpose_indicators['transactional'] += 2  # Central tables have many relationships
            elif len(relationships) == 0:
                purpose_indicators['lookup'] += 1  # Standalone tables often lookup
            
            # Determine primary purpose
            primary_purpose = max(purpose_indicators, key=purpose_indicators.get)
            confidence = purpose_indicators[primary_purpose] / max(sum(purpose_indicators.values()), 1)
            
            # Generate key indicators
            key_indicators = []
            if purpose_indicators['transactional'] > 0:
                key_indicators.extend([col for col in column_names if any(word in col for word in ['date', 'time', 'total', 'amount'])])
            if purpose_indicators['lookup'] > 0:
                key_indicators.extend([col for col in column_names if col.endswith('name')])
            
            table_purposes[table_name] = TablePurpose(
                table_name=table_name,
                purpose_type=primary_purpose,
                confidence=confidence,
                key_indicators=key_indicators[:3],  # Top 3 indicators
                related_tables=[rel.get('target_table', '').split('.')[-1] for rel in relationships]
            )
        
        return table_purposes
    
    def _analyze_relationship_patterns(self, schema_metadata: List[Dict]) -> Dict[str, Any]:
        """
        Analyze relationship patterns to understand data flow.
        """
        relationship_patterns = {
            'hub_tables': [],      # Tables with many outgoing relationships
            'leaf_tables': [],     # Tables with few/no relationships
            'bridge_tables': [],   # Tables that connect other tables
            'common_paths': []     # Most common relationship paths
        }
        
        # Count relationships per table
        relationship_counts = {}
        all_relationships = []
        
        for table_info in schema_metadata:
            table_name = table_info['table']
            relationships = table_info.get('relationships', [])
            relationship_counts[table_name] = len(relationships)
            all_relationships.extend(relationships)
        
        # Identify hub tables (many relationships)
        avg_relationships = sum(relationship_counts.values()) / len(relationship_counts) if relationship_counts else 0
        for table_name, count in relationship_counts.items():
            if count > avg_relationships * 1.5:
                relationship_patterns['hub_tables'].append(table_name)
            elif count == 0:
                relationship_patterns['leaf_tables'].append(table_name)
        
        # Identify common relationship paths
        target_counts = defaultdict(int)
        for rel in all_relationships:
            target_table = rel.get('target_table', '').split('.')[-1]
            if target_table:
                target_counts[target_table] += 1
        
        # Most referenced tables are likely central to queries
        relationship_patterns['common_paths'] = sorted(target_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return relationship_patterns
    
    def _analyze_column_patterns(self, schema_metadata: List[Dict]) -> Dict[str, Any]:
        """
        Analyze column patterns across tables to identify common data types and purposes.
        """
        column_patterns = {
            'id_columns': {},      # Primary/Foreign key patterns
            'name_columns': {},    # Name/description columns
            'date_columns': {},    # Date/time columns
            'numeric_columns': {}, # Numeric/measurement columns
            'status_columns': {}   # Status/category columns
        }
        
        for table_info in schema_metadata:
            table_name = table_info['table']
            columns = table_info.get('columns', [])
            
            for col in columns:
                col_name = col['name']
                col_type = col.get('type', '').lower()
                col_name_lower = col_name.lower()
                
                # Categorize columns
                if col_name_lower.endswith('id'):
                    column_patterns['id_columns'][f"{table_name}.{col_name}"] = {
                        'is_primary': col.get('primary_key', False),
                        'type': col_type
                    }
                
                elif any(word in col_name_lower for word in ['name', 'title', 'description']):
                    column_patterns['name_columns'][f"{table_name}.{col_name}"] = col_type
                
                elif any(word in col_name_lower for word in ['date', 'time', 'created', 'modified']):
                    column_patterns['date_columns'][f"{table_name}.{col_name}"] = col_type
                
                elif any(word in col_type for word in ['int', 'decimal', 'float', 'numeric']) and not col_name_lower.endswith('id'):
                    column_patterns['numeric_columns'][f"{table_name}.{col_name}"] = col_type
                
                elif any(word in col_name_lower for word in ['status', 'type', 'category', 'group']):
                    column_patterns['status_columns'][f"{table_name}.{col_name}"] = col_type
        
        return column_patterns
    
    def _generate_dynamic_query_guidance(self, table_purposes: Dict, relationship_patterns: Dict, column_patterns: Dict) -> Dict[str, Any]:
        """
        Generate dynamic query guidance based on discovered patterns.
        """
        guidance = {
            'table_selection_rules': [],
            'join_recommendations': [],
            'column_usage_tips': [],
            'common_query_patterns': []
        }
        
        # Table selection rules based on purposes
        transactional_tables = [name for name, purpose in table_purposes.items() if purpose.purpose_type == 'transactional']
        lookup_tables = [name for name, purpose in table_purposes.items() if purpose.purpose_type == 'lookup']
        
        if transactional_tables:
            guidance['table_selection_rules'].append({
                'rule': 'For actual data queries (worked, logged, recorded)',
                'recommended_tables': transactional_tables,
                'confidence': 0.8
            })
        
        if lookup_tables:
            guidance['table_selection_rules'].append({
                'rule': 'For reference data queries (names, categories, types)',
                'recommended_tables': lookup_tables,
                'confidence': 0.7
            })
        
        # Join recommendations based on hub tables
        hub_tables = relationship_patterns.get('hub_tables', [])
        if hub_tables:
            guidance['join_recommendations'].append({
                'rule': 'Central tables for complex queries',
                'tables': hub_tables,
                'note': 'These tables are well-connected and good for multi-table queries'
            })
        
        # Column usage tips
        numeric_columns = list(column_patterns.get('numeric_columns', {}).keys())
        if numeric_columns:
            guidance['column_usage_tips'].append({
                'rule': 'For aggregation queries (SUM, AVG, COUNT)',
                'columns': numeric_columns[:5],  # Top 5
                'functions': ['SUM', 'AVG', 'COUNT', 'MAX', 'MIN']
            })
        
        return guidance
    
    def _identify_common_join_patterns(self, schema_metadata: List[Dict]) -> Dict[str, List[str]]:
        """
        Identify the most common JOIN patterns in the schema.
        """
        join_patterns = {}
        
        for table_info in schema_metadata:
            table_name = table_info['table']
            relationships = table_info.get('relationships', [])
            
            if relationships:
                join_patterns[table_name] = []
                for rel in relationships:
                    target_table = rel.get('target_table', '').split('.')[-1]
                    source_col = rel.get('source_column')
                    target_col = rel.get('target_column')
                    
                    if target_table and source_col and target_col:
                        join_pattern = f"{table_name}.{source_col} = {target_table}.{target_col}"
                        join_patterns[table_name].append(join_pattern)
        
        return join_patterns
    
    def get_query_specific_guidance(self, query: str, schema_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get specific guidance for a query based on dynamic schema analysis.
        """
        query_lower = query.lower()
        guidance = {
            'recommended_tables': [],
            'recommended_joins': [],
            'recommended_columns': [],
            'warnings': []
        }
        
        # Analyze query intent
        if any(word in query_lower for word in ['total', 'sum', 'count', 'average']):
            # Aggregation query - recommend transactional tables and numeric columns
            transactional_tables = [
                name for name, purpose in schema_analysis['table_purposes'].items() 
                if purpose.purpose_type == 'transactional'
            ]
            guidance['recommended_tables'].extend(transactional_tables)
            
            numeric_columns = list(schema_analysis['column_patterns'].get('numeric_columns', {}).keys())
            guidance['recommended_columns'].extend(numeric_columns[:3])
        
        if any(word in query_lower for word in ['name', 'list', 'show', 'display']):
            # Display query - recommend lookup tables and name columns
            lookup_tables = [
                name for name, purpose in schema_analysis['table_purposes'].items() 
                if purpose.purpose_type == 'lookup'
            ]
            guidance['recommended_tables'].extend(lookup_tables)
            
            name_columns = list(schema_analysis['column_patterns'].get('name_columns', {}).keys())
            guidance['recommended_columns'].extend(name_columns[:3])
        
        # Remove duplicates
        guidance['recommended_tables'] = list(set(guidance['recommended_tables']))
        guidance['recommended_columns'] = list(set(guidance['recommended_columns']))
        
        return guidance

def create_dynamic_schema_guidance(schema_metadata: List[Dict]) -> Dict[str, Any]:
    """
    Main function to create dynamic schema guidance for any database.
    
    Args:
        schema_metadata: Raw schema metadata from get_schema_metadata()
        
    Returns:
        Dynamic guidance dictionary
    """
    analyzer = DynamicSchemaAnalyzer()
    return analyzer.analyze_schema(schema_metadata)

if __name__ == "__main__":
    # Test with actual schema
    from database import get_schema_metadata
    
    print("🔍 DYNAMIC SCHEMA GUIDANCE SYSTEM TEST")
    print("=" * 50)
    
    try:
        schema_metadata, _, _, _ = get_schema_metadata()
        
        print(f"Analyzing schema with {len(schema_metadata)} tables...")
        
        guidance = create_dynamic_schema_guidance(schema_metadata)
        
        print("\n📊 DISCOVERED TABLE PURPOSES:")
        for table_name, purpose in guidance['table_purposes'].items():
            print(f"  {table_name}: {purpose.purpose_type} (confidence: {purpose.confidence:.2f})")
            if purpose.key_indicators:
                print(f"    Key indicators: {purpose.key_indicators}")
        
        print("\n🔗 RELATIONSHIP PATTERNS:")
        patterns = guidance['relationship_patterns']
        if patterns['hub_tables']:
            print(f"  Hub tables (central): {patterns['hub_tables']}")
        if patterns['leaf_tables']:
            print(f"  Leaf tables (standalone): {patterns['leaf_tables']}")
        
        print("\n📋 COLUMN PATTERNS:")
        col_patterns = guidance['column_patterns']
        print(f"  ID columns: {len(col_patterns['id_columns'])}")
        print(f"  Name columns: {len(col_patterns['name_columns'])}")
        print(f"  Date columns: {len(col_patterns['date_columns'])}")
        print(f"  Numeric columns: {len(col_patterns['numeric_columns'])}")
        
        print("\n🎯 QUERY GUIDANCE RULES:")
        for rule in guidance['query_guidance']['table_selection_rules']:
            print(f"  {rule['rule']}: {rule['recommended_tables']}")
        
        print("\n✅ Dynamic analysis complete - No hardcoded rules!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()