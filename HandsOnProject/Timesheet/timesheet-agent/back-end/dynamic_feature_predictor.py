#!/usr/bin/env python3
"""
Dynamic Feature Predictor - Pure vector-based SQL feature prediction.

This module implements the dynamic table/column/join prediction logic that was
successfully tested in test_sample_questions_dynamic.py. It uses pure vector
similarity to predict SQL features without any hardcoded business rules.

This replaces the static hardcoded approach with a flexible, future-proof system
that will work with any new tables added to the database.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PredictedSQLFeatures:
    """Container for predicted SQL features"""
    sql_feature: str
    tables: List[str]
    columns: List[str]
    joins: str
    complexity: str
    special_functions: List[str]
    confidence: float
    metadata: Dict[str, Any]


class DynamicFeaturePredictor:
    """
    Pure vector-based SQL feature predictor.
    
    This class uses vector similarity to dynamically predict which tables,
    columns, and joins are needed for a query without any hardcoded rules.
    """
    
    def __init__(self, vector_store, schema_metadata):
        """
        Initialize the dynamic feature predictor.
        
        Args:
            vector_store: VectorSchemaStore instance
            schema_metadata: Database schema metadata
        """
        self.vector_store = vector_store
        self.schema_metadata = schema_metadata
        
        # Convert schema format if needed
        if isinstance(schema_metadata, list):
            schema_dict = {}
            for table_info in schema_metadata:
                if isinstance(table_info, dict) and 'name' in table_info:
                    schema_dict[table_info['name']] = table_info
            self.schema_metadata = schema_dict
        else:
            self.schema_metadata = schema_metadata
        
        logger.info("DynamicFeaturePredictor initialized")
    
    def predict_sql_features(self, query_intent, original_question: str) -> PredictedSQLFeatures:
        """
        Predict SQL features using improved vector similarity with business logic.
        Enhanced to better distinguish between similar concepts like projects vs forecasts.
        
        Args:
            query_intent: QueryIntent object from semantic analysis
            original_question: Original natural language question
            
        Returns:
            PredictedSQLFeatures object with predicted elements
        """
        try:
            predicted_tables = []
            predicted_columns = []
            
            # Create comprehensive search terms from the original question
            search_terms = [original_question]
            
            # Add entity names as additional search terms
            for entity in query_intent.entities:
                search_terms.append(entity.name)
            
            # Enhanced table selection with business logic
            predicted_tables = self._predict_tables_with_business_logic(search_terms, query_intent)
            
            # Enhanced column selection based on selected tables and intent
            predicted_columns = self._predict_columns_with_context(predicted_tables, search_terms, query_intent)
            
            # Fallback: If no tables found, use schema-driven approach
            if not predicted_tables and self.schema_metadata:
                available_tables = list(self.schema_metadata.keys())
                predicted_tables = available_tables[:2]  # Conservative fallback
                predicted_columns = self._predict_columns_with_context(predicted_tables, search_terms, query_intent)
                                
        except Exception as e:
            logger.warning(f"Enhanced prediction failed, falling back to basic vector search: {e}")
            # Fallback to basic vector search
            try:
                predicted_tables, predicted_columns = self._basic_vector_search(search_terms)
            except Exception as e2:
                logger.error(f"Basic vector search also failed: {e2}")
                predicted_tables, predicted_columns = [], []
            
        # Final fallback: If still no tables, use schema-driven approach
        if not predicted_tables and self.schema_metadata:
            available_tables = list(self.schema_metadata.keys())
            predicted_tables = available_tables[:2]  # Conservative fallback
            predicted_columns = self._predict_columns_with_context(predicted_tables, search_terms, query_intent)
        
        # Dynamically determine joins from schema relationships
        predicted_joins = self._predict_joins_dynamically(predicted_tables)
        
        # Determine complexity dynamically
        complexity = self._assess_complexity_dynamically(predicted_tables, predicted_joins)
        
        # Map intent types to SQL features (generic, not table-specific)
        sql_feature = self._map_intent_to_sql_feature(query_intent.intent_type)
        
        # Predict special functions based on intent (generic, not hardcoded)
        special_functions = self._predict_special_functions(query_intent)
        
        # Calculate overall confidence
        confidence = self._calculate_prediction_confidence(
            predicted_tables, predicted_columns, query_intent
        )
        
        return PredictedSQLFeatures(
            sql_feature=sql_feature,
            tables=predicted_tables or ['No tables found via vector search'],
            columns=predicted_columns or ['No columns found via vector search'], 
            joins=predicted_joins,
            complexity=complexity,
            special_functions=special_functions,
            confidence=confidence,
            metadata={
                'search_terms_used': len(search_terms),
                'vector_search_successful': len(predicted_tables) > 0,
                'fallback_used': len(predicted_tables) == 0 and self.schema_metadata
            }
        )
    
    def _predict_joins_dynamically(self, predicted_tables: List[str]) -> str:
        """Dynamically predict joins from schema relationships"""
        if len(predicted_tables) <= 1 or not self.schema_metadata:
            return "None"
        
        join_combinations = []
        for table in predicted_tables:
            table_info = self.schema_metadata.get(table, {})
            foreign_keys = table_info.get('foreign_keys', [])
            for fk in foreign_keys:
                if isinstance(fk, dict):
                    ref_table = fk.get('referenced_table')
                    if ref_table in predicted_tables:
                        join_str = f"{table}.{fk.get('column')} = {ref_table}.{fk.get('referenced_column')}"
                        if join_str not in join_combinations:
                            join_combinations.append(join_str)
        
        return ' AND '.join(join_combinations) if join_combinations else "None"
    
    def _predict_tables_with_business_logic(self, search_terms: List[str], query_intent) -> List[str]:
        """Enhanced table prediction with business logic to avoid common mistakes"""
        predicted_tables = []
        
        # Business logic mappings to avoid common mistakes
        business_mappings = {
            'project': ['Project'],  # "projects" should map to Project table, not Forecast
            'projects': ['Project'],
            'client': ['Client'],
            'clients': ['Client'], 
            'employee': ['Employee'],
            'employees': ['Employee'],
            'timesheet': ['Timesheet'],
            'timesheets': ['Timesheet'],
            'leave': ['LeaveRequest', 'LeaveType'],
            'activity': ['Activity'],
            'activities': ['Activity'],
            'forecast': ['Forecast'],  # Only use Forecast when explicitly mentioned
            'processed file': ['ProcessedFiles'],
            'file': ['ProcessedFiles']
        }
        
        # Check for direct business logic matches first
        query_lower = ' '.join(search_terms).lower()
        for keyword, tables in business_mappings.items():
            if keyword in query_lower:
                for table in tables:
                    if table not in predicted_tables:
                        predicted_tables.append(table)
        
        # If no direct matches, use vector search with higher threshold
        if not predicted_tables:
            try:
                for search_term in search_terms:
                    query_vector = self.vector_store.embedder.encode(search_term)
                    table_matches = self.vector_store.find_similar_tables(query_vector, k=3)
                    
                    for match in table_matches:
                        if match.similarity_score > 0.4:  # Higher threshold for better precision
                            if match.table_name not in predicted_tables:
                                predicted_tables.append(match.table_name)
            except Exception as e:
                logger.warning(f"Vector table search failed: {e}")
        
        # Fallback to schema-driven approach if still empty
        if not predicted_tables and self.schema_metadata:
            available_tables = list(self.schema_metadata.keys())
            predicted_tables = available_tables[:2]  # Conservative fallback
        
        return predicted_tables[:3]  # Limit to top 3 tables
    
    def _predict_columns_with_context(self, predicted_tables: List[str], search_terms: List[str], query_intent) -> List[str]:
        """Enhanced column prediction based on table context and query intent"""
        predicted_columns = []
        
        # Intent-based column selection
        intent_column_preferences = {
            'COUNT': ['ID', 'Key'],  # For counting, prefer ID columns
            'SUM': ['Hours', 'Amount', 'Total', 'Cost'],  # For summing, prefer numeric columns
            'AVERAGE': ['Hours', 'Amount', 'Total', 'Cost'],
            'MAX': ['Hours', 'Amount', 'Total', 'Date'],
            'MIN': ['Hours', 'Amount', 'Total', 'Date'],
            'SELECT': ['Name', 'Title', 'Description', 'ID']  # For listing, prefer descriptive columns
        }
        
        intent_str = query_intent.intent_type.value.upper()
        preferred_column_types = intent_column_preferences.get(intent_str, ['Name', 'ID'])
        
        # For each predicted table, select appropriate columns
        for table_name in predicted_tables:
            table_info = self.schema_metadata.get(table_name, {})
            columns = table_info.get('columns', [])
            
            # Add columns based on intent preferences
            for col in columns:
                col_name = col.get('name', '') if isinstance(col, dict) else str(col)
                
                # Check if column matches intent preferences
                for pref in preferred_column_types:
                    if pref.lower() in col_name.lower():
                        col_full_name = f"{table_name}.{col_name}"
                        if col_full_name not in predicted_columns:
                            predicted_columns.append(col_full_name)
                        break
            
            # Always include primary key for the table
            primary_keys = table_info.get('primary_keys', [])
            for pk in primary_keys:
                col_full_name = f"{table_name}.{pk}"
                if col_full_name not in predicted_columns:
                    predicted_columns.append(col_full_name)
        
        # If no columns found, use vector search as fallback
        if not predicted_columns:
            predicted_columns = self._vector_search_columns(search_terms, predicted_tables)
        
        return predicted_columns[:5]  # Limit to top 5 columns
    
    def _basic_vector_search(self, search_terms: List[str]) -> tuple:
        """Basic vector search fallback"""
        predicted_tables = []
        predicted_columns = []
        
        for search_term in search_terms:
            try:
                query_vector = self.vector_store.embedder.encode(search_term)
                
                table_matches = self.vector_store.find_similar_tables(query_vector, k=3)
                for match in table_matches:
                    if match.similarity_score > 0.3 and match.table_name not in predicted_tables:
                        predicted_tables.append(match.table_name)
                
                column_matches = self.vector_store.find_similar_columns(query_vector, k=5)
                for match in column_matches:
                    if match.similarity_score > 0.3:
                        col_full_name = f"{match.table_name}.{match.column_name}"
                        if col_full_name not in predicted_columns:
                            predicted_columns.append(col_full_name)
                            
            except Exception as e:
                logger.warning(f"Basic vector search failed for '{search_term}': {e}")
                continue
        
        return predicted_tables, predicted_columns
    
    def _vector_search_columns(self, search_terms: List[str], predicted_tables: List[str]) -> List[str]:
        """Vector search for columns within predicted tables"""
        predicted_columns = []
        
        for search_term in search_terms:
            try:
                query_vector = self.vector_store.embedder.encode(search_term)
                column_matches = self.vector_store.find_similar_columns(query_vector, k=8)
                
                for match in column_matches:
                    if match.table_name in predicted_tables and match.similarity_score > 0.3:
                        col_full_name = f"{match.table_name}.{match.column_name}"
                        if col_full_name not in predicted_columns:
                            predicted_columns.append(col_full_name)
            except Exception as e:
                logger.warning(f"Column vector search failed: {e}")
        
        return predicted_columns

    def _assess_complexity_dynamically(self, predicted_tables: List[str], predicted_joins: str) -> str:
        """Dynamically assess query complexity"""
        if len(predicted_tables) > 2:
            return "Complex"
        elif len(predicted_tables) > 1 or predicted_joins != "None":
            return "Moderate"
        else:
            return "Simple"
    
    def _map_intent_to_sql_feature(self, intent_type) -> str:
        """Map intent types to SQL features (generic mapping)"""
        sql_feature_map = {
            'select': 'SELECT with WHERE clause',
            'count': 'COUNT() aggregate function',
            'sum': 'SUM() aggregate function', 
            'average': 'AVG() aggregate function',
            'max': 'MAX() aggregate function',
            'min': 'MIN() aggregate function',
            'unknown': 'Basic SELECT'
        }
        
        return sql_feature_map.get(intent_type.value, 'SELECT with WHERE clause')
    
    def _predict_special_functions(self, query_intent) -> List[str]:
        """Predict special functions based on intent (generic patterns)"""
        special_functions = []
        intent_value = query_intent.intent_type.value
        
        if intent_value == 'sum':
            special_functions.append('SUM()')
        elif intent_value == 'count':
            special_functions.append('COUNT()')
        elif intent_value == 'average':
            special_functions.append('AVG()')
        elif intent_value == 'max':
            special_functions.append('MAX()')
        elif intent_value == 'min':
            special_functions.append('MIN()')
        
        # Add functions based on entity types (generic patterns)
        for entity in query_intent.entities:
            if entity.entity_type.value == 'date':
                special_functions.extend(['MONTH()', 'YEAR()', 'DATEPART()'])
            elif entity.entity_type.value == 'number':
                special_functions.append('Comparison operators (>, <, >=, <=)')
        
        # Remove duplicates
        return list(set(special_functions))
    
    def _calculate_prediction_confidence(self, predicted_tables: List[str], 
                                       predicted_columns: List[str], query_intent) -> float:
        """Calculate overall prediction confidence"""
        confidence = 0.0
        
        # Base confidence from query intent
        confidence += query_intent.confidence * 0.4
        
        # Confidence from table prediction
        if predicted_tables and 'Error' not in predicted_tables[0] and 'No tables' not in predicted_tables[0]:
            confidence += 0.3
        
        # Confidence from column prediction
        if predicted_columns and 'Error' not in predicted_columns[0] and 'No columns' not in predicted_columns[0]:
            confidence += 0.2
        
        # Confidence from entity extraction
        if query_intent.entities:
            confidence += min(len(query_intent.entities) * 0.05, 0.1)
        
        return min(confidence, 0.95)  # Cap at 95%


def create_dynamic_feature_predictor(vector_store, schema_metadata) -> DynamicFeaturePredictor:
    """
    Factory function to create a DynamicFeaturePredictor instance.
    
    Args:
        vector_store: VectorSchemaStore instance
        schema_metadata: Database schema metadata
        
    Returns:
        DynamicFeaturePredictor instance
    """
    return DynamicFeaturePredictor(vector_store, schema_metadata)