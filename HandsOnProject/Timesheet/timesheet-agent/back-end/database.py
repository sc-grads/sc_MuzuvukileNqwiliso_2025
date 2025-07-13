from sqlalchemy import create_engine, inspect, text
from config import MSSQL_CONNECTION, CHROMADB_DIR, CHROMADB_COLLECTION
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import os
import chromadb
import json


def get_engine():
    return create_engine(MSSQL_CONNECTION)


def initialize_vector_store():
    try:
        chromadb.config.Settings(anonymized_telemetry=False)
        embeddings = OllamaEmbeddings(model="mistral:7b", base_url=os.getenv("OLLAMA_BASE_URL"))
        vector_store = Chroma(
            collection_name=CHROMADB_COLLECTION,
            embedding_function=embeddings,
            persist_directory=CHROMADB_DIR
        )
        return vector_store
    except Exception as e:
        print(f"Failed to initialize vector store: {e}")
        return None


def get_schema_metadata():
    cache_file = "schema_cache.json"
    column_map_file = "column_map.json"

    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            schema_metadata = json.load(f)
        vector_store = initialize_vector_store()
        return schema_metadata, vector_store

    engine = get_engine()
    vector_store = initialize_vector_store()

    table_descriptions = {
        "Employee": "Contains employee records, including EmployeeID (PK) and EmployeeName.",
        "Client": "Stores client information such as ClientID (PK), ClientName, and contact details.",
        "Project": "Represents projects linked to clients, includes ProjectID (PK), ClientID (FK), and ProjectName.",
        "Timesheet": (
            "Main table for recording work logs. "
            "Includes Date (DATE), EmployeeID (FK), ClientID (FK), ProjectID (FK), "
            "DescriptionID (FK), TotalHours (decimal), BillableStatus ('Billable' or 'Non-Billable'), and FileName."
        ),
        "ProcessedFiles": (
            "Tracks uploaded or processed timesheet files. "
            "Includes FileName (PK or unique), EmployeeName (linked to Employee)."
        ),
        "LeaveRequest": (
            "Stores leave request information, including StartDate, EndDate, Status ('Pending', 'Approved', 'Rejected'), "
            "and EmployeeID (FK)."
        ),
        "LeaveType": "Defines different types of leave, such as Annual or Sick, using LeaveTypeID and LeaveTypeName.",
        "Activity": "Lists available work activities or task categories, referenced in Timesheet via DescriptionID.",
        "Description": (
            "Structured lookup table containing descriptive labels. "
            "Includes DescriptionID (PK), DescriptionType (e.g., 'Activity'), "
            "SourceID (link to another table), and DescriptionName (e.g., '.NET code')."
        ),
        "Forecast": (
            "Stores planned work hours or days per employee. "
            "Includes EmployeeID (FK), ForecastDate, ExpectedHours, and ExpectedDays."
        )
    }

    column_map = {}
    schema_metadata = []

    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            table_names = inspector.get_table_names(schema="Timesheet")
            exclude_tables = [
                "TimesheetStaging", "ProjectStaging", "ActivityLeaveStaging",
                "StagingLeaveRequest", "AuditLog", "ErrorLog"
            ]
            table_names = [t for t in table_names if t not in exclude_tables]

            if not table_names:
                print("No relevant tables found in Timesheet schema.")
                return [], vector_store

            for table_name in table_names:
                columns = inspector.get_columns(table_name, schema="Timesheet")
                fks = inspector.get_foreign_keys(table_name, schema="Timesheet")

                col_details = []
                for col in columns:
                    col_type = str(col["type"])
                    col_info = f"{col['name']} ({col_type})"
                    if not col.get("nullable", True):
                        col_info += " NOT NULL"
                    if col.get("default"):
                        default_val = str(col["default"]).strip("()")
                        col_info += f" DEFAULT {default_val}"
                    col_details.append(col_info)

                column_map[table_name] = [col["name"] for col in columns]

                fk_details = [
                    f"{fk['constrained_columns'][0]} -> {fk['referred_table']}({fk['referred_columns'][0]})"
                    for fk in fks
                ]

                schema_text = (
                    f"Table: Timesheet.{table_name}\n"
                    f"Description: {table_descriptions.get(table_name, 'No description available')}\n"
                    f"Columns: {', '.join(col_details)}\n"
                    f"Foreign Keys: {', '.join(fk_details) if fk_details else 'None'}\n"
                    f"Sample Query: SELECT TOP 5 * FROM [Timesheet].[{table_name}]"
                )

                schema_metadata.append(schema_text)

                if vector_store:
                    try:
                        vector_store.add_texts(
                            texts=[schema_text],
                            metadatas=[{"table": table_name}],
                            ids=[f"schema_{table_name}"]
                        )
                    except Exception as e:
                        print(f"Failed to store schema for {table_name} in vector store: {e}")

            with open(cache_file, "w") as f:
                json.dump(schema_metadata, f, indent=2)

            with open(column_map_file, "w") as f:
                json.dump(column_map, f, indent=2)

            return schema_metadata, vector_store

    except Exception as e:
        print(f"Failed to retrieve schema: {e}")
        return [], vector_store


def execute_query(query):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            conn.commit()
            if query.strip().upper().startswith("SELECT"):
                rows = result.fetchall()
                columns = result.keys()
                return rows, columns
            return None, None
    except Exception as e:
        print(f"Query execution failed: {e}")
        return None, None
