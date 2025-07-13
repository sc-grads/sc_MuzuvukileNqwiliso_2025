from database import get_schema_metadata, execute_query, refresh_schema_cache
from llm import generate_sql_query
from nlp import extract_entities
from history import save_query, get_query_history
import time
import argparse
import os
from datetime import datetime

def main(refresh_schema=False, schemas=None):
    try:
        if refresh_schema:
            cache_files = ["schema_cache.json", "column_map.json"]
            for cache_file in cache_files:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    print(f"Cleared cache: {cache_file}")
            print("Schema cache invalidated.")

        schema_metadata, column_map, vector_store = get_schema_metadata(schemas=schemas)
        
        if not schema_metadata:
            print("No schema metadata available. Exiting.")
            return
        else:
            print(f"Loaded schema metadata for {len(schema_metadata)} tables in schemas: {', '.join(set(m['schema'] for m in schema_metadata))}")

    except Exception as e:
        print(f"Failed to initialize application: {e}")
        return

    print("\nWelcome to the SQL AI Agent!")
    print("Enter a natural language query about your database (or 'exit' to quit).")

    def no_exec_query(sql):
        return None, None

    while True:
        nl_query = input("\nYour query: ")
        if nl_query.lower() == "exit":
            break

        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            entities = extract_entities(nl_query, schema_metadata, no_exec_query)
            print(f"Extracted Entities: {entities}")

            sql_query = generate_sql_query(nl_query, schema_metadata, column_map, entities, vector_store)
            generation_time = time.time() - start_time
            print(f"SQL generation took {generation_time:.2f} seconds")
            
            success = not sql_query.startswith(("Failed", "Error"))
            error_message = sql_query if not success else None
            save_query(nl_query, sql_query if success else None, timestamp, success, error_message)

            if success:
                print("\nGenerated SQL Query:")
                print(sql_query)
            else:
                print(f"Could not generate a valid SQL query: {sql_query}")

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
        "--schemas",
        type=str,
        help="Comma-separated list of schemas to use (e.g., Timesheet,Sales). If not provided, all schemas are loaded."
    )
    args = parser.parse_args()
    
    schemas = args.schemas.split(",") if args.schemas else None
    main(refresh_schema=args.refresh_schema, schemas=schemas)
