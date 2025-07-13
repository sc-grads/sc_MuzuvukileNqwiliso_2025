from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from config import OLLAMA_BASE_URL, LLM_MODEL
import sqlparse
import re

def validate_sql(sql_query, schema_metadata, column_map):
    try:
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return False, "Invalid SQL: Unable to parse query."

        statement = parsed[0]
        if statement.get_type() != 'SELECT':
            return False, "Only SELECT queries are allowed."

        mentioned_tables = set()
        from_seen = False
        for token in statement.tokens:
            if token.is_keyword and token.value.upper() == 'FROM':
                from_seen = True
                continue
            if from_seen and not token.is_keyword:
                table_matches = re.finditer(r'\[?(\w+)\]?\.\[?(\w+)\]?', str(token))
                for match in table_matches:
                    schema, table = match.groups()
                    mentioned_tables.add(f"{schema}.{table}")

        valid_tables = set(column_map.keys())
        if mentioned_tables - valid_tables:
            return False, f"Invalid table(s): {', '.join(mentioned_tables - valid_tables)}"

        for token in statement.tokens:
            if isinstance(token, sqlparse.sql.Identifier):
                parts = [p.value for p in token.tokens if not p.is_whitespace]
                if len(parts) >= 2:
                    table_part, column_part = parts[0], parts[-1]
                    table_key = next((t for t in mentioned_tables if t.endswith(f".{table_part}")), None)
                    if table_key and column_part.lower() not in [c.lower() for c in column_map.get(table_key, [])]:
                        return False, f"Column '{column_part}' not found in table '{table_key}'"

        return True, sql_query
    except Exception as e:
        return False, f"SQL validation error: {str(e)}"

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