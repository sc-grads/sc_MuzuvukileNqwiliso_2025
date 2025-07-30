#!/usr/bin/env python3
"""
RAG API Endpoints - REST API for the RAG-based SQL system.

This module provides comprehensive API endpoints for interacting with the
RAG-based SQL agent, including query processing, system management, and monitoring.
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import traceback

# Import RAG components
from rag_sql_agent import RAGSQLAgent, create_rag_agent
from rag_config import get_rag_config, save_rag_config, get_config_manager
from config import FLASK_PORT, get_current_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Global RAG agent instance
_rag_agent: Optional[RAGSQLAgent] = None

def get_rag_agent() -> RAGSQLAgent:
    """Get or create RAG agent instance"""
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = create_rag_agent()
    return _rag_agent

def reset_rag_agent():
    """Reset RAG agent instance (for configuration changes)"""
    global _rag_agent
    if _rag_agent:
        try:
            _rag_agent.save_system_state()
        except Exception as e:
            logger.warning(f"Failed to save system state during reset: {e}")
    _rag_agent = None

@app.before_request
def before_request():
    """Set up request context"""
    g.start_time = time.time()
    g.request_id = f"req_{int(time.time() * 1000)}"

@app.after_request
def after_request(response):
    """Log request completion"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info(f"Request {g.request_id} completed in {duration:.3f}s - Status: {response.status_code}")
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler"""
    logger.error(f"Unhandled exception in request {getattr(g, 'request_id', 'unknown')}: {str(e)}")
    logger.error(traceback.format_exc())
    
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(e),
        'request_id': getattr(g, 'request_id', 'unknown')
    }), 500

# === Query Processing Endpoints ===

@app.route('/api/v1/query', methods=['POST'])
def process_query():
    """
    Process a natural language query using the RAG system.
    
    Request body:
    {
        "query": "natural language query",
        "options": {
            "explain": false,
            "include_similar": false,
            "max_results": 100
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: query'
            }), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400
        
        options = data.get('options', {})
        
        # Process query
        agent = get_rag_agent()
        result = agent.process_query(query)
        
        # Build response
        response = {
            'success': result.success,
            'query': query,
            'sql': result.sql_query,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'metadata': result.metadata,
            'request_id': g.request_id
        }
        
        if result.success:
            response.update({
                'results': result.results,
                'columns': result.columns,
                'row_count': len(result.results) if result.results else 0
            })
        else:
            response.update({
                'error': result.error_message,
                'recovery_suggestions': []
            })
            
            if result.recovery_plan:
                response['recovery_suggestions'] = [
                    {
                        'description': suggestion.description,
                        'corrected_query': suggestion.corrected_query,
                        'corrected_sql': suggestion.corrected_sql,
                        'confidence': suggestion.confidence,
                        'reasoning': suggestion.reasoning,
                        'example': suggestion.example
                    }
                    for suggestion in result.recovery_plan.suggestions
                ]
        
        # Add explanation if requested
        if options.get('explain', False):
            explanation = agent.explain_query_processing(query)
            response['explanation'] = explanation
        
        # Add similar queries if requested
        if options.get('include_similar', False):
            similar_queries = agent.get_similar_queries(query, k=3)
            response['similar_queries'] = [
                {
                    'query': nl_query,
                    'sql': sql_query,
                    'similarity': similarity
                }
                for nl_query, sql_query, similarity in similar_queries
            ]
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process query',
            'message': str(e),
            'request_id': g.request_id
        }), 500

@app.route('/api/v1/explain', methods=['POST'])
def explain_query():
    """
    Explain how a query would be processed without executing it.
    
    Request body:
    {
        "query": "natural language query"
    }
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: query'
            }), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400
        
        agent = get_rag_agent()
        explanation = agent.explain_query_processing(query)
        
        return jsonify({
            'success': True,
            'explanation': explanation,
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error explaining query: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to explain query',
            'message': str(e),
            'request_id': g.request_id
        }), 500

@app.route('/api/v1/similar', methods=['POST'])
def get_similar_queries():
    """
    Get similar queries from learned patterns.
    
    Request body:
    {
        "query": "natural language query",
        "limit": 5
    }
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: query'
            }), 400
        
        query = data['query'].strip()
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400
        
        agent = get_rag_agent()
        similar_queries = agent.get_similar_queries(query, k=limit)
        
        return jsonify({
            'success': True,
            'query': query,
            'similar_queries': [
                {
                    'natural_language': nl_query,
                    'sql': sql_query,
                    'similarity_score': similarity
                }
                for nl_query, sql_query, similarity in similar_queries
            ],
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error getting similar queries: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get similar queries',
            'message': str(e),
            'request_id': g.request_id
        }), 500

# === System Management Endpoints ===

@app.route('/api/v1/system/status', methods=['GET'])
def get_system_status():
    """Get system status and statistics"""
    try:
        agent = get_rag_agent()
        stats = agent.get_system_statistics()
        
        return jsonify({
            'success': True,
            'status': 'running',
            'database': get_current_database(),
            'statistics': {
                'total_queries_processed': stats.total_queries_processed,
                'successful_queries': stats.successful_queries,
                'failed_queries': stats.failed_queries,
                'success_rate': (stats.successful_queries / max(stats.total_queries_processed, 1)) * 100,
                'average_confidence': stats.average_confidence,
                'average_processing_time': stats.average_processing_time,
                'vector_store_size': stats.vector_store_size,
                'learned_patterns_count': stats.learned_patterns_count,
                'error_recovery_rate': stats.error_recovery_rate,
                'last_updated': stats.last_updated.isoformat()
            },
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get system status',
            'message': str(e),
            'request_id': g.request_id
        }), 500

@app.route('/api/v1/system/refresh-schema', methods=['POST'])
def refresh_schema():
    """Refresh database schema in vector store"""
    try:
        agent = get_rag_agent()
        agent.refresh_schema()
        
        return jsonify({
            'success': True,
            'message': 'Schema refreshed successfully',
            'database': get_current_database(),
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error refreshing schema: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to refresh schema',
            'message': str(e),
            'request_id': g.request_id
        }), 500

@app.route('/api/v1/system/save-state', methods=['POST'])
def save_system_state():
    """Save system state to disk"""
    try:
        agent = get_rag_agent()
        agent.save_system_state()
        
        return jsonify({
            'success': True,
            'message': 'System state saved successfully',
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error saving system state: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save system state',
            'message': str(e),
            'request_id': g.request_id
        }), 500

# === Configuration Management Endpoints ===

@app.route('/api/v1/config', methods=['GET'])
def get_configuration():
    """Get current system configuration"""
    try:
        config_manager = get_config_manager()
        database = request.args.get('database', get_current_database())
        
        config = config_manager.get_config(database)
        summary = config_manager.get_config_summary(database)
        
        return jsonify({
            'success': True,
            'database': database,
            'configuration': config.to_dict(),
            'summary': summary,
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get configuration',
            'message': str(e),
            'request_id': g.request_id
        }), 500

@app.route('/api/v1/config', methods=['POST'])
def update_configuration():
    """
    Update system configuration.
    
    Request body:
    {
        "database": "optional_database_name",
        "configuration": {
            "vector_store": {...},
            "intent_engine": {...},
            ...
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'configuration' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: configuration'
            }), 400
        
        database = data.get('database', get_current_database())
        config_dict = data['configuration']
        
        config_manager = get_config_manager()
        
        # Create configuration from dictionary
        from rag_config import RAGSystemConfig
        config = RAGSystemConfig.from_dict(config_dict)
        
        # Validate configuration
        issues = config_manager.validate_config(config)
        if issues:
            return jsonify({
                'success': False,
                'error': 'Configuration validation failed',
                'issues': issues,
                'request_id': g.request_id
            }), 400
        
        # Save configuration
        config_manager.save_config(config, database)
        
        # Reset RAG agent to apply new configuration
        reset_rag_agent()
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully',
            'database': database,
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update configuration',
            'message': str(e),
            'request_id': g.request_id
        }), 500

@app.route('/api/v1/config/databases', methods=['GET'])
def list_database_configs():
    """List all available database configurations"""
    try:
        config_manager = get_config_manager()
        databases = config_manager.list_database_configs()
        
        return jsonify({
            'success': True,
            'databases': databases,
            'current_database': get_current_database(),
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error listing database configs: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list database configurations',
            'message': str(e),
            'request_id': g.request_id
        }), 500

# === Monitoring and Analytics Endpoints ===

@app.route('/api/v1/monitoring/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics and performance data"""
    try:
        agent = get_rag_agent()
        stats = agent.get_system_statistics()
        
        # Calculate additional metrics
        success_rate = (stats.successful_queries / max(stats.total_queries_processed, 1)) * 100
        failure_rate = 100 - success_rate
        
        metrics = {
            'query_metrics': {
                'total_processed': stats.total_queries_processed,
                'successful': stats.successful_queries,
                'failed': stats.failed_queries,
                'success_rate_percent': success_rate,
                'failure_rate_percent': failure_rate
            },
            'performance_metrics': {
                'average_confidence': stats.average_confidence,
                'average_processing_time_ms': stats.average_processing_time * 1000,
                'error_recovery_rate_percent': stats.error_recovery_rate * 100
            },
            'system_metrics': {
                'vector_store_size': stats.vector_store_size,
                'learned_patterns_count': stats.learned_patterns_count,
                'database': get_current_database(),
                'last_updated': stats.last_updated.isoformat()
            }
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get metrics',
            'message': str(e),
            'request_id': g.request_id
        }), 500

@app.route('/api/v1/monitoring/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        agent = get_rag_agent()
        stats = agent.get_system_statistics()
        
        # Determine health status
        health_status = 'healthy'
        issues = []
        
        # Check if system is processing queries
        if stats.total_queries_processed == 0:
            health_status = 'warning'
            issues.append('No queries processed yet')
        
        # Check success rate
        if stats.total_queries_processed > 0:
            success_rate = stats.successful_queries / stats.total_queries_processed
            if success_rate < 0.5:
                health_status = 'unhealthy'
                issues.append(f'Low success rate: {success_rate:.1%}')
            elif success_rate < 0.8:
                health_status = 'warning'
                issues.append(f'Moderate success rate: {success_rate:.1%}')
        
        # Check vector store
        if stats.vector_store_size == 0:
            health_status = 'unhealthy'
            issues.append('Vector store is empty')
        
        return jsonify({
            'success': True,
            'health_status': health_status,
            'issues': issues,
            'timestamp': datetime.now().isoformat(),
            'database': get_current_database(),
            'request_id': g.request_id
        })
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'success': False,
            'health_status': 'unhealthy',
            'error': 'Health check failed',
            'message': str(e),
            'request_id': g.request_id
        }), 500

# === Utility Endpoints ===

@app.route('/api/v1/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    return jsonify({
        'success': True,
        'system': 'RAG-based SQL Agent',
        'version': '1.0.0',
        'database': get_current_database(),
        'features': {
            'vector_embeddings': True,
            'semantic_intent_analysis': True,
            'dynamic_sql_generation': True,
            'adaptive_learning': True,
            'error_recovery': True,
            'multi_database_support': True
        },
        'api_version': 'v1',
        'timestamp': datetime.now().isoformat(),
        'request_id': g.request_id
    })

@app.route('/api/v1/test', methods=['GET'])
def test_endpoint():
    """Test endpoint for connectivity"""
    return jsonify({
        'success': True,
        'message': 'RAG API is running',
        'timestamp': datetime.now().isoformat(),
        'request_id': g.request_id
    })

# === Error Handlers ===

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist',
        'request_id': getattr(g, 'request_id', 'unknown')
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'message': 'The HTTP method is not allowed for this endpoint',
        'request_id': getattr(g, 'request_id', 'unknown')
    }), 405

if __name__ == '__main__':
    logger.info(f"Starting RAG API server on port {FLASK_PORT}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)