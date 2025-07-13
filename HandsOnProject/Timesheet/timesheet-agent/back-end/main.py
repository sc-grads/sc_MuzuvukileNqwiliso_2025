from database import get_schema_metadata, execute_query
from llm import generate_sql_query
from nlp import process_query
from history import save_query, get_query_history
import time
import argparse
import os

def main(refresh_schema=False):
    if refresh_schema:
        # Invalidate the cache by deleting the cache file
        cache_file = "schema_cache.json"
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print("Schema cache has been invalidated.")

    schema_metadata, vector_store = get_schema_metadata()
    if not schema_metadata:
        print("No schema metadata available. Exiting.")
        return

    print("\nWelcome to the Timesheet AI Agent!")
    print("Enter a natural language query about Timesheets (or 'exit' to quit).")

    while True:
        nl_query = input("\nYour query: ")
        if nl_query.lower() == "exit":
            break

        start_time = time.time()
        
        entities = process_query(nl_query, schema_metadata)
        print(f"Extracted Entities: {entities}")

        sql_query = generate_sql_query(nl_query, schema_metadata, entities, vector_store)
        print(f"SQL generation took {time.time() - start_time:.2f} seconds")
        
        if sql_query:
            print("\nGenerated SQL Query:")
            print(sql_query)
            save_query(nl_query, sql_query)
            
            print("\nWould you like to execute this query? (y/n)")
            if input().lower() == "y":
                rows, columns = execute_query(sql_query)
                if rows and columns:
                    print("\nQuery Results:")
                    for row in rows:
                        print(dict(zip(columns, row)))
                else:
                    print("No results or query did not return data.")
        else:
            print("Could not generate a valid SQL query. Please clarify or try a different query.")

        history = get_query_history()
        if history:
            print("\nRecent Queries:")
            for entry in history[-3:]:
                print(f"- {entry['timestamp']}: {entry['natural_language_query']} -> {entry['sql_query']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TimesheetDB AI Agent")
    parser.add_argument(
        "--refresh-schema",
        action="store_true",
        help="Force a refresh of the database schema cache."
    )
    args = parser.parse_args()
    main(refresh_schema=args.refresh_schema)
