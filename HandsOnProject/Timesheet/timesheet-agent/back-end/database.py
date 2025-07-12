from sqlalchemy import create_engine, inspect, text
from config import MSSQL_CONNECTION

def get_engine():
    return create_engine(MSSQL_CONNECTION)

def get_schema_metadata():
    engine = get_engine()
    try:
        with engine.connect() as conn:
            current_db = conn.execute(text("SELECT DB_NAME()")).scalar()
            print(f"Connected to DB: {current_db}")
            
            inspector = inspect(engine)
            table_names = inspector.get_table_names(schema="Timesheet")
            if not table_names:
                print("No tables found in Timesheet schema.")
                return []

            schema_metadata = []
            for table_name in table_names:
                columns = inspector.get_columns(table_name, schema="Timesheet")
                col_list = [f"{col['name']} ({col['type']})" for col in columns]
                
                fks = inspector.get_foreign_keys(table_name, schema="Timesheet")
                fk_list = [f"{fk['constrained_columns'][0]} -> {fk['referred_schema']}.{fk['referred_table']}({fk['referred_columns'][0]})" for fk in fks]
                
                check_constraints = []
                if table_name == "Timesheet":
                    check_constraints = [
                        "DayOfWeek IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')",
                        "BillableStatus IN ('Billable', 'Non-Billable')",
                        "TotalHours >= 0"
                    ]
                elif table_name == "LeaveRequest":
                    check_constraints = [
                        "Status IN ('Pending', 'Approved', 'Rejected')",
                        "DATEDIFF(DAY, StartDate, EndDate) BETWEEN 1 AND 10"
                    ]
                elif table_name in ["Employee", "Client", "Project", "LeaveType", "Activity"]:
                    check_constraints = [f"{col['name']} <> ''" for col in columns if col['name'].endswith('Name')]

                schema_text = (
                    f"Table: Timesheet.{table_name}\n"
                    f"Columns: {', '.join(col_list)}\n"
                    f"Foreign Keys: {', '.join(fk_list) if fk_list else 'None'}\n"
                    f"Constraints: {', '.join(check_constraints) if check_constraints else 'None'}"
                )
                schema_metadata.append(schema_text)
            
            return schema_metadata, None

    except Exception as e:
        print(f"Failed to retrieve schema: {e}")
        return [], None

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