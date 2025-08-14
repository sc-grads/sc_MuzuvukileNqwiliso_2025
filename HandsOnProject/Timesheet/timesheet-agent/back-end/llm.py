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
        self._cached_invoke = lru_cache(maxsize=self.cache_size)(self._execute_invoke)

    def _get_fallback_models(self) -> List[str]:
        if "mistral" in self.primary_model.lower():
            return ["llama2:7b", "codellama:7b"]
        elif "llama2" in self.primary_model.lower():
            return ["mistral:7b", "codellama:7b"]
        else:
            return ["mistral:7b", "llama2:7b"]

    def _initialize_llm(self):
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
        try:
            test_response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.current_model, "prompt": "SELECT 1", "stream": False},
                timeout=30
            )
            return test_response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def _attempt_model_fallback(self) -> bool:
        for fallback_model in self.fallback_models:
            logger.info(f"Attempting fallback to model: {fallback_model}")
            self.current_model = fallback_model
            self._initialize_llm()
            if self.llm_instance and self.check_ollama_health():
                logger.info(f"Switched to fallback model: {fallback_model}")
                return True
        self.current_model = self.primary_model
        self._initialize_llm()
        return False

    def _execute_invoke(self, prompt: str) -> str:
        if time.time() - self.last_health_check > self.health_check_interval:
            if not self.check_ollama_health():
                if not self._attempt_model_fallback():
                    raise ConnectionError("All models failed.")
            self.last_health_check = time.time()

        if not self.llm_instance:
            self._initialize_llm()
            if not self.llm_instance:
                raise ConnectionError("LLM instance unavailable.")

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.llm_instance.invoke(prompt)
                return response.content.strip()
            except Exception as e:
                if attempt < max_retries - 1:
                    self._attempt_model_fallback()
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"LLM failed: {e}")
        return ""

    def invoke(self, prompt: str, use_cache: bool = True) -> str:
        if use_cache:
            return self._cached_invoke(prompt)
        return self._execute_invoke(prompt)

    def get_model_info(self) -> Dict[str, any]:
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
        self._cached_invoke.cache_clear()


llm_manager = OllamaManager()


def _extract_sql_from_response(response: str) -> str:
    sql_block_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
    if sql_block_match:
        candidate = sql_block_match.group(1).strip()
    else:
        sql_section_match = re.search(r"\*\*SQL:\*\*", response, re.IGNORECASE)
        candidate = response[sql_section_match.end():].strip() if sql_section_match else response

    candidate = candidate.strip().strip("`").strip()
    match = re.search(r"((WITH\s+[\s\S]+?\)\s*)?SELECT\b[\s\S]+)", candidate, re.IGNORECASE)
    if match:
        return match.group(1).rstrip().rstrip(";")
    logger.warning("No valid SQL found in response.")
    return ""


# -------------------------
# Fully dynamic example generator
# -------------------------
def _create_dynamic_example(schema_metadata: List[Dict]) -> str:
    if not schema_metadata:
        return ""

    examples = []

    def find_table(min_cols=1, has_numeric=False, has_date=False, has_name=False):
        for t in schema_metadata:
            if len(t['columns']) >= min_cols:
                cols = t['columns']
                if has_numeric and not any(any(x in c['type'].lower() for x in ['int', 'decimal', 'numeric']) for c in cols):
                    continue
                if has_date and not any('date' in c['type'].lower() or 'time' in c['type'].lower() for c in cols):
                    continue
                if has_name and not any('name' in c['name'].lower() for c in cols):
                    continue
                return t
        return None

    tbl_simple = find_table(min_cols=2)
    if tbl_simple:
        c1, c2 = tbl_simple['columns'][0]['name'], tbl_simple['columns'][1]['name']
        examples.append(f"""User Request: "Show some rows from {tbl_simple['table']}."
Plan:
1. Select a sample of rows.
2. Return two representative columns.

**SQL:**
```sql
SELECT TOP 10
    [{c1}],
    [{c2}]
FROM
    [{tbl_simple['schema']}].[{tbl_simple['table']}];
```""")

    tbl_with_rel = next((t for t in schema_metadata if t.get('relationships')), None)
    if tbl_with_rel:
        rel = tbl_with_rel['relationships'][0]
        target_tbl = next((tt for tt in schema_metadata if f"{tt['schema']}.{tt['table']}" == rel['target_table']), None)
        if target_tbl:
            examples.append(f"""User Request: "Show related data between {tbl_with_rel['table']} and {target_tbl['table']}."
Plan:
1. Join the two tables using the defined relationship.

**SQL:**
```sql
SELECT TOP 10
    t1.*,
    t2.[{target_tbl['columns'][0]['name']}]
FROM
    [{tbl_with_rel['schema']}].[{tbl_with_rel['table']}] AS t1
JOIN
    [{target_tbl['schema']}].[{target_tbl['table']}] AS t2
    ON t1.[{rel['source_column']}] = t2.[{rel['target_column']}];
```""")

    tbl_with_num_date = find_table(min_cols=2, has_numeric=True, has_date=True)
    if tbl_with_num_date:
        date_col = next(c['name'] for c in tbl_with_num_date['columns'] if 'date' in c['type'].lower() or 'time' in c['type'].lower())
        num_col = next(c['name'] for c in tbl_with_num_date['columns'] if any(x in c['type'].lower() for x in ['int', 'decimal', 'numeric']))
        examples.append(f"""User Request: "Total {num_col} for April 2024."
Plan:
1. Filter by April 2024.
2. Sum the numeric column.

**SQL:**
```sql
SELECT
    SUM([{num_col}]) AS TotalValue
FROM
    [{tbl_with_num_date['schema']}].[{tbl_with_num_date['table']}]
WHERE
    [{date_col}] >= '2024-04-01'
    AND [{date_col}] <= '2024-04-30';
```""")

    tbl_name = find_table(has_name=True)
    if tbl_name and tbl_with_rel:
        name_col = next(c['name'] for c in tbl_name['columns'] if 'name' in c['name'].lower())
        examples.append(f"""User Request: "Show related rows for a specific name."
Plan:
1. Use a CTE to filter by name.
2. Join the CTE to another table.

**SQL:**
```sql
WITH filtered AS (
    SELECT [{tbl_name['columns'][0]['name']}] AS ID
    FROM [{tbl_name['schema']}].[{tbl_name['table']}]
    WHERE [{name_col}] = 'Example Name'
)
SELECT t.*
FROM [{tbl_with_rel['schema']}].[{tbl_with_rel['table']}] t
JOIN filtered f ON t.[{tbl_with_rel['columns'][0]['name']}] = f.ID;
```""")

    return "\n\n".join(examples)


def get_model_specific_prompt_template(dynamic_example: str) -> str:
    return f"""You are an expert SQL Server developer.
Your task: produce ONE correct, safe SQL query in T-SQL (SQL Server) 
that answers the user's request using the provided database schema.

## Rules:
1. Output two sections: **Plan:** (short reasoning) and **SQL:** (final query in code block).
2. Always use schema-qualified names: [Schema].[Table].
3. Only SELECT/ WITH + SELECT statements. No modifications.
4. Use TOP N for sampling.
5. Use YYYY-MM-DD for dates.
6. Match exact strings unless told otherwise.
7. Use explicit JOINs when combining tables.
8. Use columns from schema; if unsure, pick most likely.
9. Keep query readable.
10. Only one final query.

---

## Schema:
{{schema_text}}

---

## Example Queries:
{dynamic_example}

---

## User Request:
"{{nl_query}}"

Plan:
"""


def _prepare_llm_prompt(nl_query: str, schema_metadata: List[Dict], previous_sql: Optional[str] = None, error_feedback: Optional[str] = None) -> str:
    lowered = nl_query.lower()

    def is_relevant(tbl):
        if tbl['table'].lower() in lowered:
            return True
        if any(col['name'].lower() in lowered for col in tbl.get('columns', [])):
            return True
        return False

    relevant_tables = [t for t in schema_metadata if is_relevant(t)]
    if not relevant_tables:
        relevant_tables = schema_metadata

    schema_text_parts = []
    for m in relevant_tables:
        table_desc = m.get('description', f"Table {m['schema']}.{m['table']}")
        cols_text = ", ".join(f"[{col['name']}] ({col.get('type','')})" for col in m['columns'])
        table_text = f"Table [{m['schema']}].[{m['table']}]: {table_desc}\nColumns: {cols_text}"
        if m.get('relationships'):
            rel_lines = [f"  - Connects to [{rel['target_table']}] via {m['table']}.{rel['source_column']} = {rel['target_table']}.{rel['target_column']}" for rel in m['relationships']]
            table_text += "\nRelationships:\n" + "\n".join(rel_lines)
        schema_text_parts.append(table_text)

    schema_text = "\n\n".join(schema_text_parts)

    if previous_sql and error_feedback:
        nl_query += f"\n\nThe previous query failed. Fix it.\nPrevious SQL:\n{previous_sql}\nError:\n{error_feedback}"

    dynamic_example = _create_dynamic_example(relevant_tables)
    prompt_template = get_model_specific_prompt_template(dynamic_example)

    return prompt_template.format(schema_text=schema_text, nl_query=nl_query)


def generate_sql_query(nl_query: str, schema_metadata: List[Dict], **kwargs) -> str:
    if not kwargs.get("entities", {}).get("is_database_related", False):
        return "This query is not related to the database."

    prompt = _prepare_llm_prompt(
        nl_query,
        schema_metadata,
        kwargs.get("previous_sql_query"),
        kwargs.get("error_feedback")
    )

    try:
        llm_response = llm_manager.invoke(prompt, use_cache=True)
        sql_query = _extract_sql_from_response(llm_response)

        if not sql_query:
            return "Error: Failed to extract SQL."

        validation_result = comprehensive_validate_query(sql_query, schema_metadata)
        if validation_result["should_block"]:
            errors = "; ".join(validation_result["errors"])
            warnings = "; ".join(validation_result["warnings"])
            return f"Error: Query blocked. Errors: {errors}. Warnings: {warnings}"

        return validation_result["query"]

    except Exception as e:
        return f"Error: {e}"


def comprehensive_validate_query(sql_query: str, schema_metadata: List[Dict]) -> Dict[str, any]:
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
    is_high_or_critical_risk = validation_result.security_risk in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]
    return (
        not validation_result.is_valid or
        validation_result.complexity == QueryComplexity.DANGEROUS or
        is_high_or_critical_risk or
        validation_result.performance_risk == PerformanceRisk.CRITICAL
    )
