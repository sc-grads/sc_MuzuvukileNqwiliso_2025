from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from config import OLLAMA_BASE_URL, LLM_MODEL
import sqlparse
import re

def validate_sql(sql_query, schema_metadata, column_map):
    try:
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return False, "Invalid SQL: Could not parse."

        statement = parsed[0]
        if statement.get_type() != "SELECT":
            return False, "Only SELECT queries are allowed."

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
    return f"{col['name']} ({col['type']})"

def relationships_text(rels):
    if not rels:
        return "None"
    return ", ".join([f"{fk['source_column']} -> {fk['target_table']}.{fk['target_column']}" for fk in rels])

def generate_sql_query(nl_query, schema_metadata, column_map, entities, vector_store=None):
    llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.0)

    target_table = entities.get("target_table")
    relevant_schemas = []

    if target_table:
        relevant_schemas = [m for m in schema_metadata if m["table"].lower() == target_table.lower()]
        for meta in schema_metadata:
            for fk in meta["relationships"]:
                if fk["target_table"].split(".")[-1].lower() == target_table.lower():
                    relevant_schemas.append(meta)
    elif vector_store:
        schema_docs = vector_store.similarity_search(nl_query, k=3)
        relevant_schemas = [m for m in schema_metadata if any(m["table"] in doc.page_content for doc in schema_docs)]
    else:
        relevant_schemas = schema_metadata

    relevant_schemas = list({m["table"]: m for m in relevant_schemas}.values())

    schema_text = "\n\n".join([
        (
            f"Table: {m['schema']}.{m['table']}\n"
            f"Columns: {', '.join([col_text(c) for c in m['columns']])}\n"
            f"Relationships: {relationships_text(m['relationships'])}\n"
            f"Primary Keys: {', '.join(m['primary_keys']) if m['primary_keys'] else 'None'}"
        )
        for m in relevant_schemas
    ])

    context = []
    intent = entities.get("intent")
    if intent == "list":
        context.append("Return all relevant columns from the target table.")
    elif intent == "count":
        context.append("Use COUNT(*) for counting rows, with GROUP BY if needed.")
    elif intent == "sum":
        context.append("Use SUM(column) or AVG(column) for aggregations, with GROUP BY if needed.")
    elif intent == "filter":
        context.append("Apply WHERE clauses for filtering.")

    if entities.get("names"):
        name_columns = [
            c for m in schema_metadata for c in m["columns"]
            if "name" in c["name"].lower() and c["type"].lower().startswith(("varchar", "nvarchar"))
        ]
        if name_columns:
            context.append(
                f"Filter for names: {', '.join(entities['names'])} in columns like " +
                ", ".join([
                    f"[{m['schema']}].[{m['table']}].[{c['name']}]"
                    for m in schema_metadata for c in m["columns"] if c in name_columns
                ])
            )

    if entities.get("dates"):
        date_columns = [
            c for m in schema_metadata for c in m["columns"]
            if c["type"].lower().startswith(("date", "datetime"))
        ]
        for date_range in entities["dates"]:
            if isinstance(date_range, tuple):
                context.append(
                    f"Filter dates BETWEEN '{date_range[0]}' AND '{date_range[1]}' in columns like " +
                    ", ".join([
                        f"[{m['schema']}].[{m['table']}].[{c['name']}]"
                        for m in schema_metadata for c in m["columns"] if c in date_columns
                    ])
                )
            else:
                context.append(
                    f"Filter date = '{date_range}' in columns like " +
                    ", ".join([
                        f"[{m['schema']}].[{m['table']}].[{c['name']}]"
                        for m in schema_metadata for c in m["columns"] if c in date_columns
                    ])
                )

    context_str = "\n".join(context) if context else "No specific filters"

    prompt_template = PromptTemplate(
        input_variables=["schema", "query", "context"],
        template="""
        You are a SQL expert for a SQL Server database. Generate a valid SQL SELECT query using ONLY the tables, columns, and relationships provided in the schema below. Follow these rules:
        1. Use exact table and column names, enclosed in square brackets (e.g., [Schema].[Table]).
        2. Use JOINs with ON clauses based on schema relationships for multi-table queries.
        3. Apply WHERE clauses for filters specified in the context (e.g., names in VARCHAR/NVARCHAR columns, dates in DATE/DATETIME columns).
        4. Use SQL Server date formats ('YYYY-MM-DD').
        5. For aggregations (COUNT, SUM, AVG), include GROUP BY if grouping by non-aggregated columns.
        6. If the target table is unclear, select the most relevant table based on the query and context.
        7. Return ONLY the raw SQL query without explanations or backticks.

        Schema Information:
        {schema}

        Filter Context:
        {context}

        User Question:
        {query}

        SQL Query:
        """
    )

    try:
        sql_query = llm.invoke(prompt_template.format(schema=schema_text, query=nl_query, context=context_str)).content.strip()
        sql_query = sql_query.replace("`", "").strip()
        if sql_query.endswith(';'):
            sql_query = sql_query[:-1]

        is_valid, validated_query = validate_sql(sql_query, schema_metadata, column_map)
        if is_valid:
            return validated_query
        return f"Failed to generate valid SQL: {validated_query}"
    except Exception as e:
        return f"Error generating SQL: {str(e)}"