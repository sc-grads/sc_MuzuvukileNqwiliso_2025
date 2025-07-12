from database import get_schema_metadata, execute_query
from llm import generate_sql_query
from nlp import process_query
from history import save_query, get_query_history

def main():
    schema_metadata, vector_store = get_schema_metadata()
    if not schema_metadata:
        print("No schema metadata available. Exiting.")
        return

    print("\nWelcome to the TimesheetDB AI Agent!")
    print("Enter a natural language query about TimesheetDB (or 'exit' to quit).")
    print("Example: 'Show all timesheets for employee Karabo in May 2025'")

    while True:
        nl_query = input("\nYour query: ")
        if nl_query.lower() == "exit":
            break

        processed_query = process_query(nl_query, schema_metadata)
        print(f"Processed query: {processed_query}")
        sql_query = generate_sql_query(processed_query, schema_metadata, vector_store)
        
        if sql_query:
            print("\nGenerated SQL Query:")
            print(sql_query)
            save_query(nl_query, sql_query)
            
            print("\nWould you like to execute this query? (y/n)")
            if input().lower() == "y":
                rows, columns = execute_query(sql_query)
                if rows and columns:
                    print("\nQuery Results:")
                    print(columns)
                    for row in rows:
                        print(row)
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
    main()
    
    