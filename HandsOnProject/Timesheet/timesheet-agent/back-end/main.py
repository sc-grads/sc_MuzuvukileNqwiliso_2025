from database import get_schema_metadata, execute_query, refresh_schema_cache
from llm import generate_sql_query
from nlp import extract_entities
from history import save_query, get_query_history
import time
import argparse
import os
from datetime import datetime
from config import USE_LIVE_DB, update_mssql_connection

def main(refresh_schema=False, database=None):
    update_mssql_connection(database)

    try:
        if refresh_schema:
            cache_files = ["schema_cache.json", "column_map.json"]
            for cache_file in cache_files:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    print(f"Cleared cache: {cache_file}")
            print("Schema cache invalidated.")

        schema_metadata, column_map, vector_store = get_schema_metadata()

        if not schema_metadata:
            print("No schema metadata available. Exiting.")
            return
        else:
            print(f"Loaded schema metadata for {len(schema_metadata)} tables in schemas: {', '.join(set(m['schema'] for m in schema_metadata))}")

    except Exception as e:
        print(f"Failed to initialize application: {e}")
        return

    query_fn = execute_query if USE_LIVE_DB else lambda sql: (None, None)

    print(f"\nLive DB fuzzy name matching is {'ENABLED' if USE_LIVE_DB else 'DISABLED'}.")

    print("\nWelcome to the Data Agent 🤖!")
    print("Enter a natural language query about your database (or 'exit' to quit).")

    while True:
        nl_query = input("\nYour query: ")
        if nl_query.lower() == "exit":
            break

        start_time = time.time()
        timestamp = datetime.now().isoformat()

        try:
            entities = extract_entities(nl_query, schema_metadata, query_fn, vector_store)
            print(f"Extracted Entities: {entities}")

            # Intent-based filtering
            if entities["intent"] == "greeting":
                print("Hello! How can I assist you with your database?")
                save_query(nl_query, None, timestamp, False, "Non-database greeting")
                continue
            elif not entities["is_database_related"]:
                print("I can only assist with database queries. Try asking about your data!")
                save_query(nl_query, None, timestamp, False, "Non-database query")
                continue

            MAX_RETRIES = 3
            generated_sql = None
            execution_error = None
            
            for retry_count in range(MAX_RETRIES):
                print(f"Attempt {retry_count + 1}/{MAX_RETRIES} to generate and execute SQL...")
                
                sql_query = generate_sql_query(
                    nl_query, 
                    schema_metadata, 
                    column_map, 
                    entities, 
                    vector_store,
                    previous_sql_query=generated_sql, # Pass previous attempt
                    error_feedback=execution_error # Pass error feedback
                )
                
                generation_time = time.time() - start_time
                print(f"SQL generation took {generation_time:.2f} seconds")

                success = not sql_query.startswith(("Failed", "Error", "This query is not related"))
                
                if success:
                    print("\nGenerated SQL Query:")
                    print(sql_query)
                    
                    if USE_LIVE_DB:
                        print("Executing query against live database...")
                        rows, columns, db_error = execute_query(sql_query) # Capture db_error
                        if db_error is None: # Query executed successfully
                            print("\nQuery Results:")
                            if columns:
                                print(f"Columns: {', '.join(columns)}")
                            for row in rows:
                                print(row)
                            save_query(nl_query, sql_query, timestamp, True, None)
                            generated_sql = sql_query # Store successful query
                            break # Exit retry loop on success
                        else:
                            execution_error = f"Database execution error: {db_error}"
                            print(f"Execution failed. Retrying with feedback. Error: {execution_error}")
                            save_query(nl_query, sql_query, timestamp, False, execution_error)
                            generated_sql = sql_query # Store the query that failed execution
                    else:
                        print("Live DB execution is DISABLED. Skipping execution.")
                        save_query(nl_query, sql_query, timestamp, True, "Live DB execution disabled")
                        generated_sql = sql_query # Store successful query
                        break # Exit retry loop if live DB is disabled
                else:
                    execution_error = sql_query # The "Failed" or "Error" message from generate_sql_query
                    print(f"\nSQL generation failed. Retrying with feedback. Error: {execution_error}")
                    save_query(nl_query, None, timestamp, False, execution_error)
                    generated_sql = None # Reset generated_sql if generation itself failed
                
                if retry_count == MAX_RETRIES - 1 and not generated_sql:
                    print(f"\nFailed to generate a valid SQL query after {MAX_RETRIES} attempts.")
                    if execution_error:
                        print(f"Last error: {execution_error}")
                    break # All retries exhausted
            
            if generated_sql and success: # Only print if a successful query was generated and potentially executed
                pass # Already printed above
            elif not generated_sql and not success:
                print(f"\nFinal attempt failed. No valid SQL query could be generated.")
                if execution_error:
                    print(f"Last error: {execution_error}")

        except Exception as e:
            print(f"Error processing query: {e}")
            save_query(nl_query, None, timestamp, False, str(e))

        history = get_query_history()
        if history:
            print("\nRecent Queries:")
            for entry in history[-3:]:
                status = "Success" if entry["success"] else f"Failed: {entry['error']}"
                print(f"- {entry['timestamp']}: {entry['natural_language_query']} ({status})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQL AI Agent for any database")
    parser.add_argument(
        "--refresh-schema",
        action="store_true",
        help="Force a refresh of the database schema cache."
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Specify the database to connect to. Overrides the default database in MSSQL_CONNECTION."
    )
    args = parser.parse_args()

    main(refresh_schema=args.refresh_schema, database=args.database)