import os
import sys
from rag_sql_agent import create_rag_agent

def run_verification_test():
    """
    Initializes the RAG agent and tests a specific query that previously failed.
    """
    print("--- Starting verification test ---")
    
    # Add the current directory to the path to ensure modules are found
    sys.path.append(os.getcwd())

    try:
        print("Step 1: Initializing RAG SQL Agent...")
        # We set USE_LIVE_DB to False in the agent, so this won't hit the DB
        agent = create_rag_agent()
        print("Agent initialized successfully. Startup error is resolved.")
    except Exception as e:
        print(f"!!! Test Failed: Could not initialize RAG Agent.")
        print(f"Error: {e}")
        return

    test_query = "Show me all projects for the client 'C. Steinweg'."
    print(f"\nStep 2: Processing test query: '{test_query}'")

    try:
        # Disable live DB for this test to only validate SQL generation
        from config import USE_LIVE_DB
        original_db_setting = USE_LIVE_DB
        import config
        config.USE_LIVE_DB = False

        result = agent.process_query(test_query)
        
        # Restore original setting
        config.USE_LIVE_DB = original_db_setting

        if result.success:
            print("\n--- Verification Result: SUCCESS ---")
            print("The agent processed the query successfully.")
            print("\nGenerated SQL:")
            print(result.sql_query)
            
            # Basic check for correctness
            if result.sql_query and "JOIN" in result.sql_query.upper() and "CLIENT" in result.sql_query.upper() and "PROJECT" in result.sql_query.upper():
                 print("\nValidation: SQL contains expected JOIN between Client and Project tables.")
            else:
                 print("\nValidation WARNING: Generated SQL may not have the correct JOINs.")

        else:
            print("\n--- Verification Result: FAILED ---")
            print("The agent failed to process the query.")
            print(f"Error Message: {result.error_message}")
            if result.needs_clarification:
                print(f"Clarification Question: {result.clarification_question}")

    except Exception as e:
        print(f"\n!!! Test Failed: An unexpected error occurred during query processing.")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Verification test complete ---")

if __name__ == "__main__":
    run_verification_test()
