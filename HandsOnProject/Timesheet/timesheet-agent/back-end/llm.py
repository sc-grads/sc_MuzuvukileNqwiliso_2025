from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from config import OLLAMA_BASE_URL, LLM_MODEL
import sqlparse
import re

# Initialize the LLM once when the module is loaded
llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.0)

def validate_sql(sql_query, schema_metadata, column_map):
    try:
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return False, "Invalid SQL: Could not parse."

        statement = parsed[0]
        if statement.get_type() not in ("SELECT", "UNION", "WITH"):
            return False, "Only SELECT, UNION, or WITH queries are allowed."

        all_table_keys = set(column_map.keys())  
        used_tables = set()
        alias_to_table = {}

        for token in statement.tokens:
            if isinstance(token, sqlparse.sql.Identifier):
                raw = str(token)
                match = re.search(r'\[?(\w+)\]?\.\[?(\w+)\]?(?:\s+AS\s+(\w+))?', raw, re.IGNORECASE)
                if match:
                    schema, table, alias = match.groups()
                    table_key = f"{schema}.{table}"
                    used_tables.add(table_key)
                    if alias:
                        alias_to_table[alias.strip()] = table_key
                    else:
                        alias_to_table[table] = table_key

        for token in statement.flatten():
            if token.ttype is None:
                identifier = token.value.strip("[]")
                if "." in identifier:
                    left, right = identifier.split(".", 1)
                    table_key = alias_to_table.get(left) or next((k for k in all_table_keys if k.endswith(f".{left}")), None)
                    if not table_key:
                        return False, f"Invalid alias or table '{left}' used in column reference '{identifier}'"
                    if right not in column_map.get(table_key, []):
                        return False, f"Column '{right}' not found in table '{table_key}'"
                else:
                    found = False
                    for t in used_tables:
                        if identifier in column_map.get(t, []):
                            found = True
                            break
                    if not found:
                        return False, f"Unqualified column '{identifier}' not found in any used table"

        return True, sql_query

    except Exception as e:
        return False, f"Validator error: {str(e)}"

def col_text(col):
    return f"{col['name']} ({col['type']}) - {col['description']}"

def relationships_text(rels):
    if not rels:
        return "None"
    return ", ".join([f"{fk['source_column']} -> {fk['target_table']}.{fk['target_column']}" for fk in rels])

def generate_sql_query(nl_query, schema_metadata, column_map, entities, vector_store=None, previous_sql_query=None, error_feedback=None):
    if not entities.get("is_database_related", False):
        return "This query is not related to the database. Please ask about data present in the connected database."

    # Provide full schema with detailed column descriptions
    schema_text = "\n\n".join([
        (
            f"Table: {m['schema']}.{m['table']}\n"
            f"Columns: {', '.join([col_text(c) for c in m['columns']])}\n"
            f"Relationships: {relationships_text(m['relationships'])}\n"
            f"Primary Keys: {', '.join(m['primary_keys']) if m['primary_keys'] else 'None'}\n"
            f"Description: {m.get('description', 'No description')}"
        )
        for m in schema_metadata
    ])

    context = []
    intent = entities.get("intent")
    if intent == "list":
        context.append("Return all relevant columns from the most relevant table, using joins only if relationships are required. Add ORDER BY for sorting if 'sort' or 'alphabetically' is implied.")
    elif intent == "count":
        context.append("Use COUNT(*) for counting rows, applying GROUP BY if implied by relationships or multiple entities.")
    elif intent == "sum":
        context.append("Use SUM(column), AVG(column), or other aggregations as implied, with GROUP BY if needed, prioritizing numeric columns from descriptions.")
    elif intent == "filter":
        context.append("Apply WHERE clauses for filtering using names or dates, leveraging column descriptions.")

    if entities.get("names"):
        context.append(f"Filter for names: {', '.join(entities['names'])} in appropriate name columns using LIKE '%[name]%' unless a primary key match is confirmed.")
    if entities.get("dates"):
        for date_range in entities["dates"]:
            if isinstance(date_range, tuple):
                context.append(f"Filter dates BETWEEN '{date_range[0]}' AND '{date_range[1]}' in date columns.")
            else:
                context.append(f"Filter date = '{date_range}' in date columns.")
    if entities.get("limit"):
        context.append(f"Limit results to {entities['limit']} rows using TOP.")
    if entities.get("suggested_tables"):
        context.append(f"Prioritize the most relevant table from: {', '.join(entities['suggested_tables'])}. Use relationships to determine joins only if multiple tables are essential to fulfill the query.")

    context_str = "\n".join(context) if context else "No specific filters or tables suggested."

    previous_sql_query_section = f"Previous SQL Attempt: {previous_sql_query}\n" if previous_sql_query else ""
    error_feedback_section = f"Error Feedback: {error_feedback}\n" if error_feedback else ""

    prompt_template = PromptTemplate(
        input_variables=["schema", "query", "context", "previous_sql_query_section", "error_feedback_section"],
        template="""
        You are a T-SQL expert for a SQL Server database. Generate a valid T-SQL SELECT query using the tables, columns, and relationships provided in the schema below. Follow these strict rules:
        1. Use exact table and column names in square brackets (e.g., [Schema].[Table]).
        2. Select the simplest valid query that fulfills the intent, prioritizing the most relevant table based on the query and schema description.
        3. Use JOINs with ON clauses only when relationships are required to connect tables relevant to the query, based on schema relationships.
        4. Apply WHERE clauses for filters as specified in the context (e.g., names with LIKE, dates in DATE/DATETIME columns).
        5. Use SQL Server date formats ('YYYY-MM-DD').
        6. For aggregations (COUNT, SUM, AVG), include GROUP BY if grouping is implied, and use HAVING for filtered aggregations if needed.
        7. Use UNION or UNION ALL only if the query explicitly implies comparing or consolidating distinct datasets (e.g., 'vs', 'compare', 'combine'), verified by relationships.
        8. Use WITH clauses for complex subqueries or common table expressions if simpler approaches are insufficient.
        9. Add ORDER BY if 'sort' or 'alphabetically' is implied, using relevant columns.
        10. Add TOP if a limit is specified in the context, e.g., 'first 5' or 'top 10'.
        11. Use CASE statements for conditional logic if implied by the query (e.g., 'if status is active').
        12. Return ONLY the raw SQL query. Do not include explanations, comments, or text beyond the SQL itself—any non-SQL content will invalidate the query.
        13. If error feedback indicates an invalid column or syntax, adjust the query to remove invalid references and simplify.

        Schema Information:
        {schema}

        Filter Context:
        {context}

        User Question:
        {query}

        {previous_sql_query_section}
        {error_feedback_section}

        SQL Query:
        """
    )

    try:
        sql_query = llm.invoke(prompt_template.format(
            schema=schema_text,
            query=nl_query,
            context=context_str,
            previous_sql_query_section=previous_sql_query_section,
            error_feedback_section=error_feedback_section
        )).content.strip()
        sql_query = sql_query.replace("`", "").strip()
        if sql_query.endswith(';'):
            sql_query = sql_query[:-1]

        is_valid, validated_query = validate_sql(sql_query, schema_metadata, column_map)
        if is_valid:
            return validated_query
        return f"Failed to generate valid SQL: {validated_query}"
    except Exception as e:
        return f"Error generating SQL: {str(e)}"

def col_text(col):
    return f"{col['name']} ({col['type']}) - {col['description']}"

def relationships_text(rels):
    if not rels:
        return "None"
    return ", ".join([f"{fk['source_column']} -> {fk['target_table']}.{fk['target_column']}" for fk in rels])