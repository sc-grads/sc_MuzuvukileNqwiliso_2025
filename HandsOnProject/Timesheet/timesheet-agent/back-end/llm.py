from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from config import OLLAMA_BASE_URL, LLM_MODEL
import sqlparse
import re


def validate_sql(sql_query, schema_metadata):
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return False, "Invalid SQL: Unable to parse query."

    statement = parsed[0]
    statement_type = statement.get_type()
    if statement_type != 'SELECT':
        return False, f"Invalid SQL: Only SELECT statements are allowed, found '{statement_type}'."

    valid_tables = {re.search(r"Table: Timesheet\.(\w+)", meta).group(1).lower() for meta in schema_metadata if re.search(r"Table: Timesheet\.(\w+)", meta)}
    valid_columns = {}
    for meta in schema_metadata:
        table_match = re.search(r"Table: Timesheet\.(\w+)", meta)
        if table_match:
            table = table_match.group(1).lower()
            columns_match = re.search(r"Columns: (.+)", meta)
            if columns_match:
                valid_columns[table] = {col.split("(")[0].strip().lower() for col in columns_match.group(1).split(", ")}

    for token in statement.flatten():
        if token.ttype is None and token.value:
            raw = token.value.strip().lower()
            if raw in valid_tables:
                continue
            if '.' in raw:
                parts = raw.split('.')
                if len(parts) == 2:
                    t, c = parts
                    if t.lower() in valid_columns and c.lower() in valid_columns[t.lower()]:
                        continue
            if any(raw in cols for cols in valid_columns.values()):
                continue
            return False, f"Invalid column or table: {raw}"

    return True, sql_query


def generate_sql_query(nl_query, schema_metadata, entities, vector_store=None):
    llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.0, max_tokens=500)

    if vector_store:
        schema_text = "\n\n".join([doc.page_content for doc in vector_store.similarity_search(nl_query, k=5)])
    else:
        schema_text = "\n\n".join(schema_metadata)

    entity_context = []
    if entities.get("names"):
        entity_context.append(f"Names mentioned: {', '.join(entities['names'])}")
    if entities.get("dates"):
        entity_context.append(f"Dates mentioned: {', '.join(entities['dates'])}")
    if entities.get("keywords"):
        entity_context.append(f"Keywords: {', '.join(entities['keywords'])}")

    context_str = "\n".join(entity_context)

    prompt_template = PromptTemplate(
        input_variables=["schema", "query", "context"],
        template="""
        You are an expert SQL assistant for a SQL Server database named TimesheetDB with tables in the 'Timesheet' schema. 
        Your task is to generate a valid SQL SELECT query using only the tables, columns, and relationships provided in the schema section below.

        Strict rules:
        - Only use tables and columns from the schema.
        - Do not guess or invent column/table names.
        - Always use Timesheet.[TableName] format.
        - Use SQL Server syntax (NO MySQL-style backticks).
        - Use WHERE, JOIN, and functions like YEAR(), MONTH() as needed.
        - Return ONLY a valid raw SQL Server query.

        **Schema**:
        {schema}

        **Context from Query**:
        {context}

        **User Query**:
        {query}

        **SQL Query**:
        """
    )

    prompt = prompt_template.format(schema=schema_text, query=nl_query, context=context_str)
    sql_query = llm.invoke(prompt).content.strip()

    sql_query = sql_query.replace("`", "") 
    
    if sql_query:
        is_valid, result = validate_sql(sql_query, schema_metadata)
        if not is_valid:
            print(f"SQL validation failed: {result}")
            return ""
        return result
    return ""
