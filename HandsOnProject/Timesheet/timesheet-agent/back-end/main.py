from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
import os
import urllib
import time
import logging

# Import fast RAG agent
from fast_rag_sql_agent import process_query_fast, get_fast_performance_stats

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_odbc_to_sqlalchemy_url(odbc_string):
    """Convert ODBC connection string to SQLAlchemy-compatible format using URL encoding."""
    encoded = urllib.parse.quote_plus(odbc_string)
    return f"mssql+pyodbc:///?odbc_connect={encoded}"

@app.route("/connect", methods=['POST'])
def connect_to_database():
    details = request.json
    try:
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={details['hostname']},{details['port']};"
            f"DATABASE={details['dbName']};"
            f"UID={details['username']};"
            f"PWD={details['password']}"
        )
        
        sqlalchemy_url = convert_odbc_to_sqlalchemy_url(connection_string)
        engine = create_engine(sqlalchemy_url)

        # Test the connection
        with engine.connect() as connection:
            pass

        # If connection is successful, update the environment for other parts of the app
        os.environ["DB_HOST"] = details['hostname']
        os.environ["DB_PORT"] = str(details['port'])
        os.environ["DB_NAME"] = details['dbName']
        os.environ["DB_USER"] = details['username']
        os.environ["DB_PASSWORD"] = details['password']
        os.environ["MSSQL_CONNECTION"] = connection_string


        return jsonify({"message": "Connection successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/query", methods=['POST'])
def process_natural_language_query():
    """Process natural language query using the fast RAG agent"""
    try:
        data = request.json
        nl_query = data.get('query', '').strip()
        
        if not nl_query:
            return jsonify({"error": "Query is required"}), 400
        
        logger.info(f"Processing query: {nl_query}")
        start_time = time.time()
        
        # Process query using fast agent
        result = process_query_fast(nl_query)
        
        processing_time = time.time() - start_time
        logger.info(f"Query processed in {processing_time:.2f} seconds")
        
        # Format response
        response = {
            "success": result.success,
            "sql_query": result.sql_query,
            "results": result.results,
            "columns": result.columns,
            "confidence": result.confidence,
            "processing_time": result.processing_time,
            "natural_language_response": result.natural_language_response,
            "performance_metrics": result.performance_metrics,
            "cache_hits": result.cache_hits
        }
        
        if not result.success:
            response["error"] = result.error_message
        
        return jsonify(response), 200 if result.success else 400
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/performance", methods=['GET'])
def get_performance_statistics():
    """Get performance statistics from the fast RAG agent"""
    try:
        stats = get_fast_performance_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Performance stats error: {e}")
        return jsonify({"error": f"Failed to get performance stats: {str(e)}"}), 500


@app.route("/health", methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "message": "Fast RAG SQL Agent is running"
    }), 200


if __name__ == '__main__':
    logger.info("Starting Fast RAG SQL Agent server...")
    app.run(port=5000, debug=False)
