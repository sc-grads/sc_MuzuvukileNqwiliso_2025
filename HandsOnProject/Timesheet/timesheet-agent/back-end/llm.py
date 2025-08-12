# Standard library imports
import logging
import re
import time
from functools import lru_cache
from typing import Dict, List, Optional

# Third-party imports
import requests
import sqlparse
from langchain_core.caches import BaseCache
from langchain_ollama import ChatOllama

# Local application imports
from config import LLM_MODEL, OLLAMA_BASE_URL
from sql_validator import (ComprehensiveSQLValidator, QueryComplexity,
                           SecurityRisk, PerformanceRisk, create_validator_from_schema)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaManager:
    """
    Manages the connection to the Ollama service, including model initialization,
    health checks, model fallback, and performance optimizations like caching.
    """

    def __init__(self, health_check_interval: int = 300, cache_size: int = 128):
        self.primary_model = LLM_MODEL
        self.fallback_models = self._get_fallback_models()
        self.base_url = OLLAMA_BASE_URL
        self.current_model = self.primary_model
        self.llm_instance: Optional[ChatOllama] = None
        self.last_health_check = 0
        self.health_check_interval = health_check_interval
        self.cache_size = cache_size
        self._initialize_llm()

        # Decorate the _execute_invoke method with lru_cache
        self._cached_invoke = lru_cache(maxsize=self.cache_size)(self._execute_invoke)

    def _get_fallback_models(self) -> List[str]:
        """Defines a list of fallback models based on the primary model."""
        if "mistral" in self.primary_model.lower():
            return ["llama2:7b", "codellama:7b"]
        elif "llama2" in self.primary_model.lower():
            return ["mistral:7b", "codellama:7b"]
        else:
            return ["mistral:7b", "llama2:7b"]

    def _initialize_llm(self):
        """Initializes or re-initializes the ChatOllama instance."""
        try:
            ChatOllama.model_rebuild()
            self.llm_instance = ChatOllama(
                model=self.current_model,
                base_url=self.base_url,
                temperature=0.0,
                timeout=60
            )
            logger.info(f"Initialized LLM with model: {self.current_model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM with {self.current_model}: {e}")
            self.llm_instance = None

    def check_ollama_health(self) -> bool:
        """
        Checks if the Ollama service is healthy by sending a test generation request.
        """
        try:
            test_response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.current_model, "prompt": "SELECT 1", "stream": False},
                timeout=30
            )
            if test_response.status_code == 200:
                return True
            logger.warning(f"Ollama health check for model {self.current_model} failed with status {test_response.status_code}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def _attempt_model_fallback(self) -> bool:
        """Attempts to switch to a fallback model if the current one fails."""
        for fallback_model in self.fallback_models:
            logger.info(f"Attempting fallback to model: {fallback_model}")
            self.current_model = fallback_model
            self._initialize_llm()
            if self.llm_instance and self.check_ollama_health():
                logger.info(f"Successfully switched to fallback model: {fallback_model}")
                return True
        logger.error("All fallback models failed. Resetting to primary model.")
        self.current_model = self.primary_model
        self._initialize_llm()
        return False

    def _execute_invoke(self, prompt: str) -> str:
        """
        The core logic for invoking the LLM, including health checks and retries.
        This method is wrapped by the lru_cache for caching.
        """
        if time.time() - self.last_health_check > self.health_check_interval:
            if not self.check_ollama_health():
                logger.warning("Health check failed, attempting model fallback.")
                if not self._attempt_model_fallback():
                    raise ConnectionError("Ollama service is unavailable and all fallback models failed.")
            self.last_health_check = time.time()

        if not self.llm_instance:
            self._initialize_llm()
            if not self.llm_instance:
                raise ConnectionError("LLM instance is not available.")

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.llm_instance.invoke(prompt)
                return response.content.strip()
            except Exception as e:
                logger.error(f"LLM invocation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    if not self._attempt_model_fallback():
                        time.sleep(2 ** attempt)
                else:
                    raise Exception(f"All LLM invocation attempts failed. Last error: {e}")
        return ""

    def invoke(self, prompt: str, use_cache: bool = True) -> str:
        """Invokes the LLM with optional caching."""
        if use_cache:
            return self._cached_invoke(prompt)
        return self._execute_invoke(prompt)

    def get_model_info(self) -> Dict[str, any]:
        """Returns information about the current model and cache status."""
        cache_info = self._cached_invoke.cache_info()
        return {
            "current_model": self.current_model,
            "primary_model": self.primary_model,
            "fallback_models": self.fallback_models,
            "base_url": self.base_url,
            "health_status": "healthy" if self.check_ollama_health() else "unhealthy",
            "cache_info": {
                "hits": cache_info.hits,
                "misses": cache_info.misses,
                "max_size": cache_info.maxsize,
                "current_size": cache_info.currsize,
            },
            "last_health_check": self.last_health_check,
        }

    def clear_cache(self):
        """Clears the LRU cache."""
        logger.info("Clearing LLM prompt cache.")
        self._cached_invoke.cache_clear()


llm_manager = OllamaManager()


def _extract_sql_from_response(response: str) -> str:
    """
    Robustly extracts a SQL query from the LLM's response.
    """
    sql_section_match = re.search(r"\*\*SQL:\*\*", response, re.IGNORECASE)
    search_area = response[sql_section_match.end():] if sql_section_match else response
    
    sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", search_area, re.DOTALL)
    clean_sql = sql_match.group(1) if sql_match else search_area
    
    clean_sql = clean_sql.strip().replace("`", "").replace(";", "")
    
    parsed = sqlparse.parse(clean_sql)
    if not parsed:
        logger.warning("Could not parse any SQL from the LLM response.")
        return ""

    for statement in parsed:
        if statement.get_type() in ("SELECT", "WITH"):
            return str(statement).strip()

    logger.warning("No valid SELECT or WITH statement found in the LLM response.")
    return ""


def _create_dynamic_example(schema_metadata: List[Dict]) -> str:
    """
    Creates a realistic, dynamic few-shot example based on the relevant schema.
    """
    if not schema_metadata:
        return "" # No context to build an example

    # Prioritize tables with relationships for better JOIN examples
    schema_metadata.sort(key=lambda t: len(t.get('relationships', [])), reverse=True)

    # Scenario 1: A table with a relationship exists (ideal for a JOIN example)
    for table1 in schema_metadata:
        if table1.get('relationships'):
            rel = table1['relationships'][0]
            target_table_name = rel['target_table']
            
            table2 = next((t for t in schema_metadata if f"{t['schema']}.{t['table']}" == target_table_name), None)
            if not table2: continue

            s1, t1, c1 = table1['schema'], table1['table'], table1['columns'][0]['name']
            s2, t2, c2 = table2['schema'], table2['table'], table2['columns'][0]['name']
            source_join_key = rel['source_column']
            target_join_key = rel['target_column']

            return f"""User Request: "Find all `{t1}` records and their related `{t2}`."

Plan:
1. I need to join `[{s1}].[{t1}]` with `[{s2}].[{t2}]`.
2. The schema indicates they join on `[{s1}].[{t1}].[{source_join_key}]` and `[{s2}].[{t2}].[{target_join_key}]`.
3. I will select the first 10 results to keep the output small.

**SQL:**
```sql
SELECT TOP 10
    t1.*,
    t2.[{c2}]
FROM
    [{s1}].[{t1}] AS t1
JOIN
    [{s2}].[{t2}] AS t2 ON t1.[{source_join_key}] = t2.[{target_join_key}];
```"""

    # Scenario 2: No relationships, but multiple tables (less ideal JOIN)
    if len(schema_metadata) >= 2:
        table1, table2 = schema_metadata[0], schema_metadata[1]
        s1, t1, c1 = table1['schema'], table1['table'], table1['columns'][0]['name']
        s2, t2 = table2['schema'], table2['table']
        # Make a plausible guess for a join key, like 'ID' or the first column name
        join_key = next((c['name'] for c in table1['columns'] if 'ID' in c['name'].upper()), c1)

        return f"""User Request: "Find all `{t1}` records related to `{t2}`."

Plan:
1. I need to join `[{s1}].[{t1}]` with `[{s2}].[{t2}]`.
2. I will assume they join on a common key like `[{join_key}]`.
3. I will select the first 10 results.

**SQL:**
```sql
SELECT TOP 10
    t1.*
FROM
    [{s1}].[{t1}] AS t1
JOIN
    [{s2}].[{t2}] AS t2 ON t1.[{join_key}] = t2.[{join_key}];
```"""

    # Scenario 3: Only one table provided
    table1 = schema_metadata[0]
    schema, table_name = table1['schema'], table1['table']
    col1, col2 = table1['columns'][0]['name'], table1['columns'][1]['name']
    return f"""User Request: "Show me all records from `{table_name}`."

Plan:
1. I will select the first 10 records from the `[{schema}].[{table_name}]` table.
2. I will select the columns `[{col1}]` and `[{col2}]`.

**SQL:**
```sql
SELECT TOP 10
    [{col1}],
    [{col2}]
FROM
    [{schema}].[{table_name}];
```"""


def get_model_specific_prompt_template(dynamic_example: str) -> str:
    """
    Gets an advanced, robust prompt template that is dynamically customized
    with a relevant few-shot example.
    """
    return f"""You are an expert SQL Server developer. Your task is to write a single, correct SQL query based on the user's request and the provided database schema.

First, think step-by-step to create a plan.
Second, write the final SQL query based on your plan.

**IMPORTANT RULE: You MUST use the schema name provided for each table (e.g., `[SchemaName].[TableName]`).**

**Schema Information:**
{{schema_text}}

---

**Example of how to structure your response:**
{dynamic_example}

---

**User Request:**
"{{nl_query}}"

**Plan:**
"""


def _prepare_llm_prompt(nl_query: str, schema_metadata: List[Dict], previous_sql: Optional[str] = None, error_feedback: Optional[str] = None) -> str:
    """Prepares the full prompt for the LLM, including a dynamic few-shot example."""
    schema_text_parts = []
    relevant_tables = schema_metadata[:5]

    for m in relevant_tables:
        table_desc = m.get('description', f"Table {m['schema']}.{m['table']}")
        columns = [f"[{col['name']}] ({col.get('description', col['type'])})" for col in m['columns'][:7]]
        table_text = f"Table [{m['schema']}].[{m['table']}]: {table_desc}\nColumns: {', '.join(columns)}"
        
        relationships = m.get('relationships', [])
        if relationships:
            rel_texts = [f"  - Connects to [{rel['target_table']}] via {m['table']}.{rel['source_column']} = {rel['target_table']}.{rel['target_column']}" for rel in relationships]
            table_text += "\nRelationships:\n" + "\n".join(rel_texts)
        schema_text_parts.append(table_text)

    schema_text = "\n\n".join(schema_text_parts)

    if previous_sql and error_feedback:
        nl_query += f"\n\nThe previous query attempt failed. Please fix it.\nPrevious SQL: {previous_sql}\nError: {error_feedback}"

    # Generate a dynamic example based on the provided schema context
    dynamic_example = _create_dynamic_example(relevant_tables)
    prompt_template = get_model_specific_prompt_template(dynamic_example)
    
    return prompt_template.format(schema_text=schema_text, nl_query=nl_query)


def generate_sql_query(nl_query: str, schema_metadata: List[Dict], **kwargs) -> str:
    """
    Generates a SQL query from a natural language query, validates it, and returns it.
    """
    if not kwargs.get("entities", {}).get("is_database_related", False):
        return "This query is not related to the database. Please ask about data in the connected database."

    prompt = _prepare_llm_prompt(
        nl_query,
        schema_metadata,
        kwargs.get("previous_sql_query"),
        kwargs.get("error_feedback")
    )

    try:
        logger.info(f"Generating SQL for query: '{nl_query}' using model: {llm_manager.current_model}")
        llm_response = llm_manager.invoke(prompt, use_cache=True)
        sql_query = _extract_sql_from_response(llm_response)

        if not sql_query:
            logger.error("LLM failed to return a valid SQL query.")
            return "Error: Failed to generate a valid SQL query from the model's response."

        logger.info(f"Validating generated SQL: {sql_query}")
        validation_result = comprehensive_validate_query(sql_query, schema_metadata)

        if validation_result["should_block"]:
            errors = "; ".join(validation_result["errors"])
            warnings = "; ".join(validation_result["warnings"])
            error_message = f"Generated query is invalid or unsafe and was blocked. Errors: {errors}. Warnings: {warnings}"
            logger.error(error_message)
            return f"Error: {error_message}"

        if not validation_result["is_valid"]:
            warnings = "; ".join(validation_result["warnings"])
            logger.warning(f"Generated query has warnings: {warnings}")

        logger.info(f"Successfully generated and validated SQL: {validation_result['query']}")
        return validation_result["query"]

    except Exception as e:
        logger.error(f"An unexpected error occurred during SQL generation: {e}", exc_info=True)
        return f"Error: An unexpected error occurred: {e}"


def comprehensive_validate_query(sql_query: str, schema_metadata: List[Dict]) -> Dict[str, any]:
    """
    Performs comprehensive validation of a SQL query.
    """
    validator = create_validator_from_schema(schema_metadata)
    validation_result = validator.validate_query(sql_query)

    return {
        "is_valid": validation_result.is_valid,
        "query": validation_result.query,
        "errors": validation_result.errors,
        "warnings": validation_result.warnings,
        "complexity": {"level": validation_result.complexity.value},
        "security_risk": {"level": validation_result.security_risk.value},
        "performance_risk": {"level": validation_result.performance_risk.value},
        "should_block": _should_block_query(validation_result),
        "validation_summary": validator.get_validation_summary(validation_result)
    }


def _should_block_query(validation_result) -> bool:
    """Determines if a query should be blocked based on validation results."""
    is_high_or_critical_risk = validation_result.security_risk in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]
    return (
        not validation_result.is_valid or
        validation_result.complexity == QueryComplexity.DANGEROUS or
        is_high_or_critical_risk or
        validation_result.performance_risk == PerformanceRisk.CRITICAL
    )