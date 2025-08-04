#!/usr/bin/env python3
"""
Simple Main Application - Simplified version for interactive testing.

This is a streamlined version of the main application that focuses on
interactive query testing without complex RAG integration.
"""

import time
import argparse
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from database import get_schema_metadata, execute_query, refresh_schema_cache
from llm import generate_sql_query
from nlp import extract_entities
from history import (
    save_query, get_query_history, get_conversation_context_for_query,
    resolve_context_references, find_similar_successful_queries
)
from error_handler import EnhancedErrorHandler, ErrorContext, ErrorType
from config import USE_LIVE_DB, update_mssql_connection

# Globals for application state
error_handler = EnhancedErrorHandler()
schema_metadata = None
column_map = None
vector_store = None
enhanced_data = None

def initialize_app(refresh: bool, db_name: Optional[str]):
    """Initializes database connection and loads schema."""
    global schema_metadata, column_map, vector_store, enhanced_data
    
    update_mssql_connection(db_name)

    try:
        if refresh:
            from config import get_schema_cache_file, get_column_map_file, get_enhanced_schema_cache_file, get_current_database
            
            cache_files = [
                get_schema_cache_file(),
                get_column_map_file(), 
                get_enhanced_schema_cache_file()
            ]
            
            current_db = get_current_database()
            print(f"Clearing schema cache for database: {current_db}")
            
            for cache_file in cache_files:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    print(f"   Cleared cache: {cache_file}")
            
            print(f"Schema cache invalidated for database: {current_db}")

        print("Loading database schema...")
        schema_metadata, column_map, vector_store, enhanced_data = get_schema_metadata()

        if not schema_metadata:
            print("❌ No schema metadata available. Please check your database connection.")
            print("\n🔧 Troubleshooting steps:")
            print("   1. Verify your database connection string in .env file")
            print("   2. Ensure the database is accessible and you have permissions")
            print("   3. Try using --refresh-schema to reload the schema")
            return False
        
        schemas = set(m['schema'] for m in schema_metadata)
        print(f"✅ Loaded schema metadata for {len(schema_metadata)} tables in schemas: {', '.join(schemas)}")
        return True

    except Exception as e:
        context = ErrorContext(user_query="Database initialization", error_message=str(e), error_type=ErrorType.SCHEMA_ERROR)
        error_response = error_handler.handle_error(e, context)
        print(error_handler.format_error_message(error_response, show_technical_details=True))
        return False

def display_results(rows: List, columns: List):
    """Prints query results in a formatted way."""
    print("\n📊 Query Results:")
    if columns:
        print(f"📋 Columns: {', '.join(columns)}")
    
    if rows:
        print(f"📈 Found {len(rows)} rows:")
        for i, row in enumerate(rows[:10]):  # Limit display to first 10 rows
            print(f"   {i+1}: {row}")
        if len(rows) > 10:
            print(f"   ... and {len(rows) - 10} more rows")
    else:
        print("   📭 No data returned")

def display_history():
    """Shows the last few queries from history."""
    history = get_query_history()
    if history:
        print("\n📜 Recent Queries:")
        for entry in history[-3:]:
            status_icon = "✅" if entry["success"] else "❌"
            status_text = "Success" if entry["success"] else f"Failed: {entry['error'][:50]}..."
            query_preview = entry['natural_language_query'][:60] + "..." if len(entry['natural_language_query']) > 60 else entry['natural_language_query']
            print(f"   {status_icon} {query_preview} ({status_text})")

def process_query(nl_query: str):
    """Handles the logic for processing a single natural language query."""
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    context = ErrorContext(user_query=nl_query, timestamp=datetime.now(), max_retries=3)
    query_fn = execute_query if USE_LIVE_DB else lambda sql: (None, None, None)

    try:
        print("🔄 Processing your query...")
        
        conversation_context = get_conversation_context_for_query(nl_query)
        if conversation_context.get('context_references'):
            resolved_query = resolve_context_references(nl_query, conversation_context)
            if resolved_query != nl_query:
                print(f"🔗 Resolved context: {resolved_query}")
                nl_query = resolved_query
        
        similar_queries = find_similar_successful_queries(nl_query)
        if similar_queries:
            print(f"📚 Found {len(similar_queries)} similar successful queries for reference")
        
        entities = extract_entities(nl_query, schema_metadata, query_fn, vector_store)
        print(f"🏷️  Extracted Entities: {entities}")

        if entities["intent"] == "greeting":
            print("👋 Hello! How can I assist you with your database?")
            save_query(nl_query, None, timestamp, False, "Non-database greeting", entities)
            return
        elif not entities["is_database_related"]:
            print("⛓️‍💥 I can only assist with database queries. Try asking about your data!")
            context.error_message = "Query not database-related"
            error_response = error_handler.handle_generation_error("😵 This query is not related to the database", context, schema_metadata)
            print(error_handler.format_error_message(error_response))
            save_query(nl_query, None, timestamp, False, "Non-database query", entities)
            return

        # --- Retry Loop ---
        generated_sql, execution_error, final_success = None, None, False
        for retry_count in range(context.max_retries):
            context.retry_count = retry_count
            print(f"🔄 Attempt {retry_count + 1}/{context.max_retries} to generate and execute SQL...")
            
            try:
                sql_query = generate_sql_query(
                    nl_query, schema_metadata, column_map, entities, vector_store,
                    previous_sql_query=generated_sql, error_feedback=execution_error,
                    enhanced_data=enhanced_data, conversation_context=conversation_context
                )
                
                generation_time = time.time() - start_time
                print(f"⚡ SQL generation took {generation_time:.2f} seconds")

                if not sql_query.startswith(("Failed", "Error", "This query is not related")):
                    print(f"\n📝 Generated SQL Query:\n   {sql_query}")
                    context.generated_sql = sql_query
                    
                    if USE_LIVE_DB:
                        rows, columns, db_error = execute_query(sql_query)
                        if db_error is None:
                            display_results(rows, columns)
                            results_summary = f"Retrieved {len(rows)} rows with {len(columns)} columns" if rows else "No data returned"
                            save_query(nl_query, sql_query, timestamp, True, None, entities, results_summary, retry_count)
                            final_success = True
                            break
                        else:
                            execution_error = str(db_error)
                            context.error_message = execution_error
                            error_response = error_handler.handle_error(Exception(db_error), context, schema_metadata)
                            print(f"\n❌ Database execution failed:\n{error_handler.format_error_message(error_response)}")
                            save_query(nl_query, sql_query, timestamp, False, execution_error, entities, None, retry_count)
                            if not error_handler.should_retry(context): break
                    else:
                        print("ℹ️  Live DB execution is DISABLED. SQL generated successfully.")
                        save_query(nl_query, sql_query, timestamp, True, "Live DB execution disabled", entities, "SQL generated (execution disabled)", retry_count)
                        final_success = True
                        break
                else:
                    execution_error = sql_query
                    context.error_message = execution_error
                    error_response = error_handler.handle_generation_error(sql_query, context, schema_metadata)
                    print(f"\n❌ SQL generation failed:\n{error_handler.format_error_message(error_response)}")
                    save_query(nl_query, None, timestamp, False, execution_error, entities, None, retry_count)
                    if not error_handler.should_retry(context): break
            
            except Exception as gen_exception:
                execution_error = str(gen_exception)
                context.error_message = execution_error
                error_response = error_handler.handle_error(gen_exception, context, schema_metadata)
                print(f"\n❌ Unexpected error during SQL generation:\n{error_handler.format_error_message(error_response)}")
                save_query(nl_query, None, timestamp, False, execution_error, entities, None, retry_count)
                if not error_handler.should_retry(context): break
        
        # --- Final Status Report ---
        if final_success:
            print(f"\n✅ Query completed successfully! (Total time: {time.time() - start_time:.2f}s)")
        else:
            print(f"\n❌ Query failed after {context.max_retries} attempts.")
            if execution_error: print(f"🔍 Last error: {execution_error}")
            final_suggestions = error_handler.suggestion_engine.generate_suggestions(context, schema_metadata)
            if final_suggestions:
                print("\n💡 Try these alternatives:")
                for i, suggestion in enumerate(final_suggestions[:3], 1):
                    print(f"   {i}. {suggestion.suggestion}")
                    if suggestion.example: print(f"      Example: {suggestion.example}")

    except Exception as e:
        context.error_message = str(e)
        error_response = error_handler.handle_error(e, context, schema_metadata)
        print(f"\n❌ Unexpected error processing query:\n{error_handler.format_error_message(error_response, show_technical_details=True)}")
        save_query(nl_query, None, timestamp, False, str(e), None, None, 0)

def main_loop():
    """The main interactive loop for the agent."""
    print(f"\n🔗 Live DB execution is {'ENABLED' if USE_LIVE_DB else 'DISABLED'}.")
    print("📊 Traditional SQL Agent is ACTIVE")
    print("\n🤖 Welcome to the Data Agent!")
    print("💬 Enter a natural language query about your database (or 'exit' to quit).")
    print("💡 Examples:")
    print("   - How many records are in [table_name]?")
    print("   - Show me all data from [table_name]")
    print("   - What is the average [column_name] by [group_column]?")

    while True:
        nl_query = input("\n🔍 Your query: ")
        if nl_query.lower() == "exit":
            print("👋 Goodbye!")
            break
        if not nl_query.strip():
            print("⚠️  Please enter a query.")
            continue
        
        process_query(nl_query)
        display_history()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple SQL AI Agent for interactive testing")
    parser.add_argument("--refresh-schema", action="store_true", help="Force a refresh of the database schema cache.")
    parser.add_argument("--database", type=str, help="Specify the database to connect to. Overrides the default database in MSSQL_CONNECTION.")
    args = parser.parse_args()

    if initialize_app(refresh=args.refresh_schema, db_name=args.database):
        main_loop()