import argparse
import os
import time
from datetime import datetime

from config import update_mssql_connection, USE_LIVE_DB
from rag_sql_agent import create_rag_agent, RAGQueryResult
from history import get_query_history, save_query, conversation_manager

def main(refresh_schema=False, database=None):
    update_mssql_connection(database)

    # Create and initialize the RAG SQL Agent
    print("Initializing RAG SQL Agent...")
    rag_agent = None # Initialize to None
    try:
        rag_agent = create_rag_agent()

        # Register shutdown hook for graceful cleanup
        import atexit
        atexit.register(rag_agent.shutdown)

        if refresh_schema:
            print("Refreshing RAG SQL Agent schema...")
            rag_agent.refresh_schema()
            print("RAG SQL Agent schema refreshed.")
        else:
            print("Loading RAG SQL Agent schema...")
            # The agent's __init__ already loads schema, so no explicit call needed here
            print("RAG SQL Agent schema loaded.")

    except Exception as e:
        print(f"\nError during RAG Agent initialization or schema loading: {e}")
        print("\n Troubleshooting steps:")
        print("   1. Verify your database connection string in .env file")
        print("   2. Ensure the database is accessible and you have permissions")
        print("   3. Try using --refresh-schema to reload the schema")
        return # Exit if agent fails to initialize


    print("\nWelcome to the RAG Data Agent!")
    print("Enter a natural language query about your database (or 'exit' to quit).")

    conversation_context = {}

    while True:
        nl_query = input("\nYour query: ")
        if nl_query.lower() == "exit":
            print("👋Goodbye!")
            break

        start_time = time.time()
        timestamp = datetime.now().isoformat()

        try:
            print(" Processing your query with RAG Agent...")

            # Process query using the RAG SQL Agent, now with context
            rag_result: RAGQueryResult = rag_agent.process_query(nl_query, conversation_context)

            processing_time = time.time() - start_time
            print(f"  RAG Agent processing took {processing_time:.2f} seconds")

            if rag_result.success:
                # Update context for the next turn
                conversation_context = {
                    'nl_query': nl_query,
                    'sql_query': rag_result.sql_query,
                    'tables_used': rag_result.metadata.get('tables_used', [])
                }

                # Display the tables the agent chose to use
                if rag_result.metadata and rag_result.metadata.get('tables_used'):
                    print("\n Agent selected the following tables:")
                    for table in rag_result.metadata['tables_used']:
                        print(f"   - {table}")

                print("\n Generated SQL Query:")
                print(f"   {rag_result.sql_query}")

                if USE_LIVE_DB:
                    print(" Executing query against live database...")
                    if rag_result.results is not None:
                        print("\n Query Results:")
                        if rag_result.columns:
                            print(f" Columns: {', '.join(rag_result.columns)}")

                        if rag_result.results:
                            for i, row in enumerate(rag_result.results[:10]):  # Limit display to first 10 rows
                                print(f"   {i+1}: {row}")
                            if len(rag_result.results) > 10:
                                print(f"   ... and {len(rag_result.results) - 10} more rows")
                        else:
                            print("   No data returned")

                        results_summary = f"Retrieved {len(rag_result.results)} rows with {len(rag_result.columns)} columns" if rag_result.results else "No data returned"
                        save_query(nl_query, rag_result.sql_query, timestamp, True, None, rag_result.metadata, results_summary, 0)
                    else:
                        print("   Query executed, but no results returned (e.g., DDL/DML or no rows).")
                        save_query(nl_query, rag_result.sql_query, timestamp, True, "No results returned (DDL/DML)", rag_result.metadata, "SQL executed (no rows/DDL/DML)", 0)
                else:
                    print("ℹLive DB execution is DISABLED. SQL generated successfully.")
                    save_query(nl_query, rag_result.sql_query, timestamp, True, "Live DB execution disabled", rag_result.metadata, "SQL generated (execution disabled)", 0)

                if rag_result.natural_language_response:
                    print("\n Agent's Response:")
                    print(f"   {rag_result.natural_language_response}")

                print(f"\n Query completed successfully! Confidence: {rag_result.confidence:.2f}")
            else:
                # Clear context on failure
                conversation_context = {}
                # Handle RAG Agent's internal failure
                print("\n RAG Agent failed to process query:")
                print(f"  Error: {rag_result.error_message}")

                if rag_result.recovery_plan:
                    print("\n Recovery Suggestions:")
                    for i, suggestion in enumerate(rag_result.recovery_plan.suggestions[:3], 1):
                        print(f"   {i}. {suggestion.description}")
                        if hasattr(suggestion, 'example') and suggestion.example:
                            print(f"      Example: {suggestion.example}")
                        if hasattr(suggestion, 'corrected_sql') and suggestion.corrected_sql:
                            print(f"      Corrected SQL: {suggestion.corrected_sql}")

                # Pass rag_result.metadata as entities to save_query
                save_query(nl_query, rag_result.sql_query, timestamp, False, rag_result.error_message, rag_result.metadata, None, 0)
                print(f" Query failed.")

        except Exception as e:
            # Clear context on unexpected error
            conversation_context = {}
            # Handle any unexpected errors in the main loop (e.g., agent crashes)
            print(f"\nUnexpected error processing query: {e}")
            # Save query with error, but no specific entities or metadata from RAG agent
            save_query(nl_query, None, timestamp, False, str(e), None, None, 0)

        # Show recent query history with better formatting
        history = get_query_history()
        if history:
            print("\nRecent Queries:")
            for entry in history[-3:]:
                status_icon = "[SUCCESS]" if entry["success"] else "[FAILED]"
                status_text = "Success" if entry["success"] else f"Failed: {entry['error'][:50]}..." if entry['error'] else "Failed"
                query_preview = entry['natural_language_query'][:60] + "..." if len(entry['natural_language_query']) > 60 else entry['natural_language_query']
                print(f"   {status_icon} {query_preview} ({status_text})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG SQL AI Agent for any database")
    parser.add_argument(
        "--refresh-schema",
        action="store_true",
        help="Force a refresh of the database schema cache for the RAG agent."
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Specify the database to connect to. Overrides the default database in MSSQL_CONNECTION."
    )
    args = parser.parse_args()

    main(refresh_schema=args.refresh_schema, database=args.database)