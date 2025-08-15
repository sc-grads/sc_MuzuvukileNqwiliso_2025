

import logging
from typing import List, Any, Dict, Optional

from llm import llm_manager

# Configure logging
logger = logging.getLogger(__name__)

def generate_natural_language_response(
    natural_language_query: str,
    sql_query: str,
    results: List[Dict[str, Any]],
    columns: List[str]
) -> Optional[str]:
    """
    Generates a natural language response from SQL query results.

    Args:
        natural_language_query: The original user query.
        sql_query: The executed SQL query.
        results: The data returned from the query.
        columns: The column names of the results.

    Returns:
        A natural language summary of the results, or None if generation fails.
    """
    if not results:
        return "The query executed successfully, but there are no results to display."

    # Create a summary of the results to pass to the LLM
    results_summary = f"The query returned {len(results)} rows. The columns are: {', '.join(columns)}."
    if len(results) > 5:
        results_summary += " Here are the first 5 rows:\n"
        sample_results = results[:5]
    else:
        results_summary += " Here are the results:\n"
        sample_results = results

    for row in sample_results:
        results_summary += f"- {dict(zip(columns, row))}\n"

    # Construct the prompt for the LLM
    prompt = (
        f"The user asked: '{natural_language_query}'\n"
        f"We executed the SQL query: '{sql_query}'\n"
        f"The results are summarized as follows:\n{results_summary}\n\n"
        f"Please provide a concise, natural language response to the user's original question based on these results."
    )

    try:
        # Call the LLM to generate the response
        response = llm_manager.invoke(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating natural language response: {e}")
        return None

