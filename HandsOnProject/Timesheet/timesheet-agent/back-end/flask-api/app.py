from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, InternalServerError
import sys
import os

# Add the parent directory to the Python path to allow module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_schema_metadata, execute_query
from llm import generate_sql_query
from nlp import process_query
from config import FLASK_PORT

app = Flask(__name__)

# Initialize schema and vector store on startup
schema_metadata, vector_store = None, None

def initialize_app():
    """Initialize schema and vector store."""
    global schema_metadata, vector_store
    print("Initializing schema and vector store...")
    schema_metadata, column_map, vector_store = get_schema_metadata()
    if not schema_metadata:
        print("Warning: Schema metadata could not be loaded.")
    else:
        print("Initialization complete.")

@app.route('/query', methods=['POST'])
def handle_query():
    """
    Handle natural language queries to generate and execute SQL.
    """
    if not request.json or 'query' not in request.json:
        raise BadRequest("Invalid request: JSON payload with 'query' key is required.")

    nl_query = request.json['query']
    
    if not schema_metadata:
        raise InternalServerError("Application is not initialized. Schema metadata is missing.")

    # Process query to get entities
    entities = process_query(nl_query, schema_metadata)
    
    # Generate SQL query
    sql_query = generate_sql_query(nl_query, schema_metadata, entities, vector_store)
    
    if not sql_query:
        return jsonify({"error": "Could not generate a valid SQL query."}), 400

    # Execute query
    rows, columns = execute_query(sql_query)
    
    if rows is not None and columns is not None:
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify({
            "natural_language_query": nl_query,
            "sql_query": sql_query,
            "results": results
        })
    
    # Handle cases where the query is valid but returns no data (e.g., non-SELECT statements)
    return jsonify({
        "natural_language_query": nl_query,
        "sql_query": sql_query,
        "message": "Query executed successfully, but it did not return any data."
    })

@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify(error=str(e)), 400

@app.errorhandler(InternalServerError)
def handle_internal_error(e):
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=True)
