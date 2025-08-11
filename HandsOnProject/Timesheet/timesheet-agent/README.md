# Dynamic SQL Agent

A dynamic, database-agnostic SQL generation agent that can connect to multiple database types and generate SQL queries using natural language understanding.

## Features

- **Multi-Database Support**: Connect to SQL Server, PostgreSQL, MySQL, and Oracle databases
- **Dynamic SQL Generation**: Uses semantic understanding and vector-based schema matching
- **Adaptive Learning**: Learns from user interactions to improve query generation
- **Real-time Schema Analysis**: Automatically discovers and understands database schemas
- **Natural Language Processing**: Converts natural language questions to SQL queries
- **Performance Optimization**: Includes caching, query optimization, and performance monitoring

## Architecture

The system consists of several key components:

### Backend Components

- **Database Connector** (`main.py`): Handles connections to different database types
- **Dynamic SQL Generator** (`dynamic_sql_generator.py`): Core SQL generation engine
- **Semantic Intent Engine** (`improved_semantic_intent_engine.py`): Analyzes query intent
- **Vector Schema Store** (`vector_schema_store.py`): Stores and retrieves schema embeddings
- **Adaptive Learning Engine** (`adaptive_learning_engine.py`): Learns from user interactions
- **Performance Monitor** (`performance_monitor.py`): Monitors query performance

### Frontend Components

- **Database Connection Modal**: Supports multiple database types
- **Chat Interface**: Natural language query input
- **Database Status**: Shows connection and schema information
- **History Management**: Tracks conversation history

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- Database drivers (automatically installed)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd back-end
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   python main.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd front-end
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Usage

### Connecting to a Database

1. Open the application in your browser
2. Click "Add Database" in the sidebar
3. Select your database type from the dropdown
4. Enter connection details:
   - **Hostname/IP**: Database server address
   - **Port**: Database port (auto-filled based on type)
   - **Database Name**: Name of the database
   - **Username**: Database username
   - **Password**: Database password
5. Click "Connect"

### Supported Database Types

| Database | Default Port | Driver |
|----------|--------------|---------|
| SQL Server | 1433 | ODBC Driver 17 |
| PostgreSQL | 5432 | psycopg2 |
| MySQL | 3306 | PyMySQL |
| Oracle | 1521 | cx_Oracle |

### Asking Questions

Once connected, you can ask natural language questions like:

- **Simple**: "How many employees are in the system?"
- **Medium**: "Show me the total hours Karabo Tsaoane worked in April"
- **Complex**: "What is the average number of billable hours per employee for the last month?"

The agent will:
1. Analyze your question's intent
2. Identify relevant tables and columns
3. Generate appropriate SQL
4. Execute the query and return results

## Testing

### Run the Test Suite

To test the dynamic agent with 5 selected questions:

```bash
cd back-end
python test_dynamic_agent.py
```

This will test:
- Database configuration
- Vector store initialization
- Semantic intent engine
- Dynamic SQL generation
- Individual question processing

### Test Questions

The test suite uses these 5 questions:

1. **Basic Lookup**: "How many employees are in the system?"
2. **List Data**: "List all available clients."
3. **Filtering with Joins**: "Show me the total hours Karabo Tsaoane worked in April."
4. **Aggregation with Filtering**: "What are the total billable hours logged for the 'Graduate Program' project?"
5. **Complex Analysis**: "What is the average number of billable hours per employee for the last month?"

## Configuration

### Environment Variables

The system uses these environment variables:

- `DB_TYPE`: Database type (mssql, postgresql, mysql, oracle)
- `DB_HOST`: Database hostname
- `DB_PORT`: Database port
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `OLLAMA_BASE_URL`: Ollama server URL for LLM
- `LLM_MODEL`: LLM model to use
- `VECTOR_STORE_DIR`: Directory for vector storage

### Database-Specific Settings

Each database type has its own configuration in `config.py`:

- Connection string templates
- Default ports
- Driver specifications
- Exclusion patterns for system tables

## Advanced Features

### Adaptive Learning

The system learns from user interactions:
- Tracks successful query patterns
- Adapts to user preferences
- Improves accuracy over time

### Performance Optimization

- SQL query caching
- Join optimization
- Query execution monitoring
- Performance metrics collection

### Schema Discovery

- Automatic table and column detection
- Relationship inference
- Vector-based similarity matching
- Dynamic schema updates

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check database credentials and network connectivity
2. **Driver Not Found**: Ensure appropriate database driver is installed
3. **Schema Discovery Issues**: Verify database permissions
4. **SQL Generation Errors**: Check if the question is clear and specific

### Debug Mode

Enable debug logging by setting the log level in the backend:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

Check system health via the API endpoint:

```bash
curl http://localhost:5000/health
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the test examples
- Examine the code comments
- Create an issue in the repository
