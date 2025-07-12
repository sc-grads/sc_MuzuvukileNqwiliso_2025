from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from config import OLLAMA_BASE_URL, LLM_MODEL
import sqlparse
import re

def validate_sql(sql_query, schema_metadata):
    valid_tables = [re.search(r"Table: Timesheet\.(\w+)", meta).group(1) for meta in schema_metadata if re.search(r"Table: Timesheet\.(\w+)", meta)]
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return False, "Invalid SQL syntax"
    
    for token in parsed[0].tokens:
        if token.ttype is None and isinstance(token, sqlparse.sql.Identifier):
            table_name = str(token).split(".")[-1]
            if table_name not in valid_tables and not table_name.startswith("("):
                return False, f"Invalid table: {table_name}"
    
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT"]
    if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
        return False, "Query contains restricted keywords (DROP, DELETE, UPDATE, INSERT)"

    if re.search(r"Date\s*=\s*'\d{4}-\d{2}-\d{2}'\s*OR", sql_query, re.IGNORECASE):
        match = re.search(r"YEAR\s*\(\s*Date\s*\)\s*=\s*(\d{4})\s*AND\s*MONTH\s*\(\s*Date\s*\)\s*=\s*(\d+)", sql_query, re.IGNORECASE)
        if match:
            year, month = match.groups()
            sql_query = re.sub(
                r"Date\s*=\s*'\d{4}-\d{2}-\d{2}'\s*OR\s*Date\s*=\s*'\d{4}-\d{2}-\d{2}'",
                f"Date BETWEEN '{year}-{month:0>2}-01' AND '{year}-{month:0>2}-31'",
                sql_query,
                flags=re.IGNORECASE
            )

    return True, sql_query

def generate_sql_query(nl_query, schema_metadata, vector_store=None):
    llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.1)
    schema_text = "\n\n".join(schema_metadata)
    
    prompt_template = PromptTemplate(
        input_variables=["schema", "query"],
        template="""
        You are an expert SQL assistant for a SQL Server database named TimesheetDB with tables in the 'Timesheet' schema. Your task is to generate a valid SQL SELECT query based on the user's natural language query. The user is not expected to know the database schema, so you must infer the correct tables, columns, and relationships based on the query's intent and the provided schema metadata. Follow these rules:
        - Always prefix tables with 'Timesheet' (e.g., Timesheet.Timesheet).
        - Use joins to connect tables via foreign keys (e.g., Timesheet.Employee for EmployeeName).
        - Use SQL Server functions like YEAR(), MONTH(), or BETWEEN for date filtering.
        - Only generate SELECT queries; do not use DROP, DELETE, UPDATE, or INSERT.
        - If the query involves files or employee names, consider Timesheet.ProcessedFiles for FileName and EmployeeName.
        - For aggregations (e.g., total hours), use GROUP BY appropriately.
        - If the query is ambiguous, select the most relevant tables based on keywords (e.g., 'timesheet' -> Timesheet.Timesheet, 'employee' -> Timesheet.Employee).
        - Return only the SQL query, without explanations or comments.
        - If the query cannot be generated, return an empty string.

        **Relevant Schema**:
        {schema}

        **User Query**:
        {query}

        **SQL Query**:
        """
    )

    prompt = prompt_template.format(schema=schema_text, query=nl_query)
    sql_query = llm.invoke(prompt).content.strip()
    
    if sql_query:
        is_valid, result = validate_sql(sql_query, schema_metadata)
        if not is_valid:
            print(f"SQL validation failed: {result}")
            return ""
        return result
    return ""