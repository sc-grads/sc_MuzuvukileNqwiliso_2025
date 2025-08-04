from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
import os
import urllib

app = Flask(__name__)
CORS(app)

def convert_odbc_to_sqlalchemy_url(odbc_string):
    """Convert ODBC connection string to SQLAlchemy-compatible format using URL encoding."""
    encoded = urllib.parse.quote_plus(odbc_string)
    return f"mssql+pyodbc:///?odbc_connect={encoded}"

@app.route("/connect", methods=['POST'])
def connect_to_database():
    details = request.json
    try:
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={details['hostname']},{details['port']};"
            f"DATABASE={details['dbName']};"
            f"UID={details['username']};"
            f"PWD={details['password']}"
        )
        
        sqlalchemy_url = convert_odbc_to_sqlalchemy_url(connection_string)
        engine = create_engine(sqlalchemy_url)

        # Test the connection
        with engine.connect() as connection:
            pass

        # If connection is successful, update the environment for other parts of the app
        os.environ["DB_HOST"] = details['hostname']
        os.environ["DB_PORT"] = str(details['port'])
        os.environ["DB_NAME"] = details['dbName']
        os.environ["DB_USER"] = details['username']
        os.environ["DB_PASSWORD"] = details['password']
        os.environ["MSSQL_CONNECTION"] = connection_string


        return jsonify({"message": "Connection successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(port=5000)
