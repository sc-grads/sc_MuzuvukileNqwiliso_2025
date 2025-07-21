"""
Enhanced error handling and user feedback system for the CLI application.
Provides descriptive error messages, retry logic, and query suggestions.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Classification of different error types"""
    CONNECTION_ERROR = "connection_error"
    SQL_GENERATION_ERROR = "sql_generation_error"
    SQL_EXECUTION_ERROR = "sql_execution_error"
    VALIDATION_ERROR = "validation_error"
    OLLAMA_ERROR = "ollama_error"
    SCHEMA_ERROR = "schema_error"
    QUERY_PROCESSING_ERROR = "query_processing_error"
    UNKNOWN_ERROR = "unknown_error"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorContext:
    """Context information for error analysis"""
    user_query: str
    generated_sql: Optional[str] = None
    error_message: str = ""
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    timestamp: datetime = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class QuerySuggestion:
    """Suggested alternative query"""
    suggestion: str
    reason: str
    confidence: float
    example: Optional[str] = None

@dataclass
class ErrorResponse:
    """Structured error response with suggestions"""
    error_message: str
    user_friendly_message: str
    suggestions: List[QuerySuggestion]
    troubleshooting_steps: List[str]
    can_retry: bool
    retry_strategy: Optional[str] = None

class DatabaseErrorHandler:
    """Handles database connection and execution errors"""
    
    def __init__(self):
        self.connection_error_patterns = {
            r"Login failed": "Authentication failed - check username and password",
            r"Cannot open database": "Database not found or access denied",
            r"A network-related or instance-specific error": "Cannot connect to SQL Server - check server name and network",
            r"Timeout expired": "Connection timeout - server may be overloaded or unreachable",
            r"Invalid object name": "Table or view does not exist in the database",
            r"Invalid column name": "Column does not exist in the specified table",
            r"Syntax error": "SQL syntax is incorrect",
            r"Permission denied": "Insufficient permissions to access the resource"
        }
    
    def handle_connection_error(self, error: Exception, context: ErrorContext) -> ErrorResponse:
        """Handle database connection errors with specific guidance"""
        error_str = str(error).lower()
        
        # Identify specific connection issue
        user_message = "Database connection failed"
        troubleshooting = []
        suggestions = []
        
        if "login failed" in error_str:
            user_message = "Authentication failed - incorrect username or password"
            troubleshooting = [
                "Verify your username and password are correct",
                "Check if the account is locked or expired",
                "Ensure you have permission to access the database",
                "Try connecting with SQL Server Management Studio to test credentials"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Check your connection string credentials",
                reason="Authentication credentials appear to be invalid",
                confidence=0.9
            ))
        
        elif "cannot open database" in error_str:
            user_message = "Database not found or access denied"
            troubleshooting = [
                "Verify the database name is spelled correctly",
                "Check if the database exists on the server",
                "Ensure you have permission to access this specific database",
                "Try listing available databases first"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Use --database parameter to specify the correct database name",
                reason="The specified database may not exist or be accessible",
                confidence=0.8
            ))
        
        elif "network-related" in error_str or "instance-specific" in error_str:
            user_message = "Cannot connect to SQL Server - network or server issue"
            troubleshooting = [
                "Check if the server name/IP address is correct",
                "Verify the server is running and accessible",
                "Check firewall settings and network connectivity",
                "Ensure SQL Server is configured to accept remote connections",
                "Try pinging the server to test basic connectivity"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Test basic network connectivity to the server",
                reason="Network connectivity issues detected",
                confidence=0.8
            ))
        
        elif "timeout" in error_str:
            user_message = "Connection timeout - server may be overloaded"
            troubleshooting = [
                "Wait a moment and try again",
                "Check if the server is experiencing high load",
                "Verify network connectivity is stable",
                "Consider increasing connection timeout if this persists"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Retry the connection after a brief wait",
                reason="Server may be temporarily overloaded",
                confidence=0.7
            ))
        
        return ErrorResponse(
            error_message=str(error),
            user_friendly_message=user_message,
            suggestions=suggestions,
            troubleshooting_steps=troubleshooting,
            can_retry=True,
            retry_strategy="exponential_backoff"
        )
    
    def handle_execution_error(self, error: Exception, context: ErrorContext) -> ErrorResponse:
        """Handle SQL execution errors with specific guidance"""
        error_str = str(error).lower()
        
        suggestions = []
        troubleshooting = []
        user_message = "SQL query execution failed"
        
        if "invalid object name" in error_str:
            user_message = "Table or view does not exist"
            troubleshooting = [
                "Check if the table name is spelled correctly",
                "Verify the table exists in the current database",
                "Ensure you're using the correct schema name",
                "Use square brackets around table names with spaces or special characters"
            ]
            suggestions.extend(self._suggest_similar_tables(error_str, context))
        
        elif "invalid column name" in error_str:
            user_message = "Column does not exist in the table"
            troubleshooting = [
                "Check if the column name is spelled correctly",
                "Verify the column exists in the specified table",
                "Use square brackets around column names with spaces or special characters"
            ]
            suggestions.extend(self._suggest_similar_columns(error_str, context))
        
        elif "syntax error" in error_str or "incorrect syntax" in error_str:
            user_message = "SQL syntax error detected"
            troubleshooting = [
                "Check for missing commas, parentheses, or quotes",
                "Verify SQL Server T-SQL syntax is being used",
                "Ensure proper use of square brackets for identifiers",
                "Check for reserved word conflicts"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Try a simpler version of your query first",
                reason="Complex queries can have subtle syntax issues",
                confidence=0.6,
                example="SELECT TOP 10 * FROM [YourTable]"
            ))
        
        elif "permission denied" in error_str or "access denied" in error_str:
            user_message = "Insufficient permissions to access the data"
            troubleshooting = [
                "Contact your database administrator for access",
                "Verify you have SELECT permissions on the table",
                "Check if the table is in a restricted schema"
            ]
        
        elif "timeout" in error_str:
            user_message = "Query execution timeout - query may be too complex"
            troubleshooting = [
                "Try adding more specific WHERE clauses to limit results",
                "Consider breaking complex queries into smaller parts",
                "Add appropriate indexes if you have permission",
                "Use TOP clause to limit result set size"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Add TOP 100 to limit results and test the query",
                reason="Large result sets can cause timeouts",
                confidence=0.8,
                example="SELECT TOP 100 * FROM [YourTable] WHERE [condition]"
            ))
        
        return ErrorResponse(
            error_message=str(error),
            user_friendly_message=user_message,
            suggestions=suggestions,
            troubleshooting_steps=troubleshooting,
            can_retry=True,
            retry_strategy="modify_query"
        )
    
    def _suggest_similar_tables(self, error_str: str, context: ErrorContext) -> List[QuerySuggestion]:
        """Suggest similar table names when table not found"""
        suggestions = []
        
        # Extract table name from error message
        table_match = re.search(r"'([^']+)'", error_str)
        if table_match:
            missing_table = table_match.group(1)
            suggestions.append(QuerySuggestion(
                suggestion=f"Check if you meant a table similar to '{missing_table}'",
                reason="Table name may be misspelled or in a different schema",
                confidence=0.7,
                example="Try: SELECT * FROM [schema].[table_name]"
            ))
        
        return suggestions
    
    def _suggest_similar_columns(self, error_str: str, context: ErrorContext) -> List[QuerySuggestion]:
        """Suggest similar column names when column not found"""
        suggestions = []
        
        # Extract column name from error message
        column_match = re.search(r"'([^']+)'", error_str)
        if column_match:
            missing_column = column_match.group(1)
            suggestions.append(QuerySuggestion(
                suggestion=f"Check if you meant a column similar to '{missing_column}'",
                reason="Column name may be misspelled",
                confidence=0.7,
                example="Use: DESCRIBE [table_name] to see available columns"
            ))
        
        return suggestions

class LLMErrorHandler:
    """Handles LLM and SQL generation errors"""
    
    def __init__(self):
        self.common_generation_issues = {
            "no_tables_found": "Could not identify relevant tables for your query",
            "ambiguous_query": "Your query could refer to multiple things",
            "unsupported_operation": "The requested operation is not supported",
            "complex_query": "Query is too complex to generate automatically"
        }
    
    def handle_ollama_error(self, error: Exception, context: ErrorContext) -> ErrorResponse:
        """Handle Ollama connection and processing errors"""
        error_str = str(error).lower()
        
        suggestions = []
        troubleshooting = []
        user_message = "AI service error"
        
        if "connection" in error_str or "refused" in error_str:
            user_message = "Cannot connect to Ollama AI service"
            troubleshooting = [
                "Check if Ollama is running: ollama serve",
                "Verify Ollama is installed and accessible",
                "Check if the correct model is available: ollama list",
                "Ensure the OLLAMA_BASE_URL is correct in your .env file"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Start Ollama service and ensure the model is downloaded",
                reason="Ollama service appears to be unavailable",
                confidence=0.9,
                example="Run: ollama serve (in a separate terminal)"
            ))
        
        elif "model" in error_str:
            user_message = "AI model not available or not loaded"
            troubleshooting = [
                "Check if the specified model is downloaded: ollama list",
                "Download the model if missing: ollama pull mistral:7b",
                "Verify the LLM_MODEL setting in your .env file",
                "Try using a different model if available"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Download the required model: ollama pull mistral:7b",
                reason="The specified AI model may not be available",
                confidence=0.8
            ))
        
        elif "timeout" in error_str:
            user_message = "AI processing timeout - query may be too complex"
            troubleshooting = [
                "Try simplifying your query",
                "Break complex requests into smaller parts",
                "Wait a moment and try again",
                "Check if Ollama has sufficient resources"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Try asking a simpler, more specific question",
                reason="Complex queries can take longer to process",
                confidence=0.7
            ))
        
        return ErrorResponse(
            error_message=str(error),
            user_friendly_message=user_message,
            suggestions=suggestions,
            troubleshooting_steps=troubleshooting,
            can_retry=True,
            retry_strategy="simplify_query"
        )
    
    def handle_generation_error(self, error_message: str, context: ErrorContext) -> ErrorResponse:
        """Handle SQL generation failures with specific suggestions"""
        suggestions = []
        troubleshooting = []
        
        if "not related to the database" in error_message.lower():
            user_message = "Your question doesn't appear to be about the database"
            troubleshooting = [
                "Ask questions about data in your connected database",
                "Reference specific table or column names if known",
                "Try questions like 'Show me all records' or 'Count the rows'"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Ask about specific data in your database",
                reason="The AI needs database-related questions to generate SQL",
                confidence=0.9,
                example="How many employees are in the database?"
            ))
        
        elif "failed to generate" in error_message.lower():
            user_message = "Could not generate SQL for your request"
            troubleshooting = [
                "Try rephrasing your question more specifically",
                "Break complex requests into simpler parts",
                "Reference specific table or column names",
                "Use more common database terminology"
            ]
            suggestions.extend([
                QuerySuggestion(
                    suggestion="Try a simpler version of your question",
                    reason="Complex queries are harder to generate automatically",
                    confidence=0.8,
                    example="Show me the first 10 rows from [table_name]"
                ),
                QuerySuggestion(
                    suggestion="Be more specific about what data you want",
                    reason="Specific requests are easier to translate to SQL",
                    confidence=0.7,
                    example="Count how many records were created today"
                )
            ])
        
        elif "validation failed" in error_message.lower():
            user_message = "Generated SQL failed validation checks"
            troubleshooting = [
                "The AI generated SQL that doesn't match your database schema",
                "Try being more specific about table and column names",
                "Check if your database schema is properly loaded"
            ]
            suggestions.append(QuerySuggestion(
                suggestion="Try refreshing the database schema: --refresh-schema",
                reason="Schema information may be outdated",
                confidence=0.6
            ))
        
        return ErrorResponse(
            error_message=error_message,
            user_friendly_message=user_message,
            suggestions=suggestions,
            troubleshooting_steps=troubleshooting,
            can_retry=True,
            retry_strategy="rephrase_query"
        )

class QuerySuggestionEngine:
    """Generates helpful query suggestions based on context"""
    
    def __init__(self):
        self.common_patterns = {
            "count": ["How many", "Count", "Total number"],
            "list": ["Show me", "List", "Display", "Get"],
            "filter": ["Find", "Where", "With", "Having"],
            "aggregate": ["Sum", "Average", "Maximum", "Minimum", "Total"]
        }
    
    def generate_suggestions(self, context: ErrorContext, schema_metadata: List[Dict] = None) -> List[QuerySuggestion]:
        """Generate contextual query suggestions"""
        suggestions = []
        
        if schema_metadata:
            # Suggest queries based on available tables
            high_priority_tables = [
                table for table in schema_metadata 
                if table.get('priority', {}).get('business_importance') == 'high'
            ][:3]
            
            for table in high_priority_tables:
                table_name = f"[{table['schema']}].[{table['table']}]"
                suggestions.extend([
                    QuerySuggestion(
                        suggestion=f"Show me data from {table['table']}",
                        reason=f"Explore the {table['table']} table",
                        confidence=0.8,
                        example=f"SELECT TOP 10 * FROM {table_name}"
                    ),
                    QuerySuggestion(
                        suggestion=f"Count records in {table['table']}",
                        reason=f"Get an overview of {table['table']} data volume",
                        confidence=0.7,
                        example=f"SELECT COUNT(*) FROM {table_name}"
                    )
                ])
        
        # General suggestions based on query intent
        if context.user_query:
            query_lower = context.user_query.lower()
            
            if any(word in query_lower for word in ["show", "list", "display"]):
                suggestions.append(QuerySuggestion(
                    suggestion="Try: 'Show me the first 10 rows from [table_name]'",
                    reason="Simple listing queries are easier to generate",
                    confidence=0.8
                ))
            
            if any(word in query_lower for word in ["count", "how many", "total"]):
                suggestions.append(QuerySuggestion(
                    suggestion="Try: 'Count all records in [table_name]'",
                    reason="Counting queries are straightforward",
                    confidence=0.8
                ))
            
            if any(word in query_lower for word in ["find", "where", "filter"]):
                suggestions.append(QuerySuggestion(
                    suggestion="Try: 'Find records where [column] equals [value]'",
                    reason="Specific filtering criteria work better",
                    confidence=0.7
                ))
        
        return suggestions[:5]  # Limit to top 5 suggestions

class RetryStrategy:
    """Manages retry logic with different strategies"""
    
    def __init__(self):
        self.strategies = {
            "exponential_backoff": self._exponential_backoff,
            "modify_query": self._modify_query,
            "simplify_query": self._simplify_query,
            "rephrase_query": self._rephrase_query
        }
    
    def should_retry(self, context: ErrorContext) -> bool:
        """Determine if a retry should be attempted"""
        return context.retry_count < context.max_retries
    
    def get_retry_delay(self, context: ErrorContext, strategy: str = "exponential_backoff") -> float:
        """Calculate delay before retry"""
        if strategy == "exponential_backoff":
            return min(2 ** context.retry_count, 30)  # Max 30 seconds
        return 1.0  # Default 1 second delay
    
    def _exponential_backoff(self, context: ErrorContext) -> Dict[str, Any]:
        """Exponential backoff strategy for connection issues"""
        return {
            "delay": self.get_retry_delay(context, "exponential_backoff"),
            "modify_context": False
        }
    
    def _modify_query(self, context: ErrorContext) -> Dict[str, Any]:
        """Modify query strategy for execution errors"""
        modifications = []
        
        if context.generated_sql:
            # Add TOP clause if missing
            if "TOP" not in context.generated_sql.upper():
                modifications.append("Add TOP 100 to limit results")
            
            # Suggest simpler WHERE clauses
            if "WHERE" in context.generated_sql.upper():
                modifications.append("Simplify WHERE conditions")
        
        return {
            "delay": 1.0,
            "modify_context": True,
            "modifications": modifications
        }
    
    def _simplify_query(self, context: ErrorContext) -> Dict[str, Any]:
        """Simplify query strategy for complex queries"""
        return {
            "delay": 1.0,
            "modify_context": True,
            "simplification_hints": [
                "Focus on a single table",
                "Remove complex JOINs",
                "Use basic SELECT statements",
                "Avoid subqueries"
            ]
        }
    
    def _rephrase_query(self, context: ErrorContext) -> Dict[str, Any]:
        """Rephrase query strategy for generation errors"""
        return {
            "delay": 1.0,
            "modify_context": True,
            "rephrase_hints": [
                "Use simpler language",
                "Be more specific about data needed",
                "Reference table names directly",
                "Ask for basic operations first"
            ]
        }

class EnhancedErrorHandler:
    """Main error handler that coordinates all error handling components"""
    
    def __init__(self):
        self.db_handler = DatabaseErrorHandler()
        self.llm_handler = LLMErrorHandler()
        self.suggestion_engine = QuerySuggestionEngine()
        self.retry_strategy = RetryStrategy()
        self.error_history = []
    
    def handle_error(self, error: Exception, context: ErrorContext, 
                    schema_metadata: List[Dict] = None) -> ErrorResponse:
        """Main error handling entry point"""
        
        # Log the error for debugging
        logger.error(f"Error occurred: {str(error)}")
        logger.error(f"Context: {context}")
        
        # Store error in history
        self.error_history.append({
            "timestamp": context.timestamp,
            "error": str(error),
            "context": context,
            "retry_count": context.retry_count
        })
        
        # Determine error type and route to appropriate handler
        error_str = str(error).lower()
        
        if "connection" in error_str or "login" in error_str or "network" in error_str:
            context.error_type = ErrorType.CONNECTION_ERROR
            response = self.db_handler.handle_connection_error(error, context)
        
        elif "invalid object" in error_str or "invalid column" in error_str or "syntax error" in error_str:
            context.error_type = ErrorType.SQL_EXECUTION_ERROR
            response = self.db_handler.handle_execution_error(error, context)
        
        elif "ollama" in error_str or "model" in error_str:
            context.error_type = ErrorType.OLLAMA_ERROR
            response = self.llm_handler.handle_ollama_error(error, context)
        
        else:
            # Generic error handling
            context.error_type = ErrorType.UNKNOWN_ERROR
            response = ErrorResponse(
                error_message=str(error),
                user_friendly_message="An unexpected error occurred",
                suggestions=self.suggestion_engine.generate_suggestions(context, schema_metadata),
                troubleshooting_steps=[
                    "Try rephrasing your question",
                    "Check your database connection",
                    "Verify Ollama is running",
                    "Contact support if the issue persists"
                ],
                can_retry=True,
                retry_strategy="exponential_backoff"
            )
        
        # Add contextual suggestions
        if schema_metadata:
            additional_suggestions = self.suggestion_engine.generate_suggestions(context, schema_metadata)
            response.suggestions.extend(additional_suggestions)
        
        return response
    
    def handle_generation_error(self, error_message: str, context: ErrorContext,
                              schema_metadata: List[Dict] = None) -> ErrorResponse:
        """Handle SQL generation errors specifically"""
        context.error_type = ErrorType.SQL_GENERATION_ERROR
        response = self.llm_handler.handle_generation_error(error_message, context)
        
        # Add contextual suggestions
        if schema_metadata:
            additional_suggestions = self.suggestion_engine.generate_suggestions(context, schema_metadata)
            response.suggestions.extend(additional_suggestions)
        
        return response
    
    def should_retry(self, context: ErrorContext) -> bool:
        """Check if retry should be attempted"""
        return self.retry_strategy.should_retry(context)
    
    def get_retry_strategy_info(self, context: ErrorContext, strategy_name: str) -> Dict[str, Any]:
        """Get retry strategy information"""
        if strategy_name in self.retry_strategy.strategies:
            return self.retry_strategy.strategies[strategy_name](context)
        return {"delay": 1.0, "modify_context": False}
    
    def format_error_message(self, response: ErrorResponse, show_technical_details: bool = False) -> str:
        """Format error message for display to user"""
        message_parts = [
            f"❌ {response.user_friendly_message}",
            ""
        ]
        
        if response.suggestions:
            message_parts.append("💡 Suggestions:")
            for i, suggestion in enumerate(response.suggestions[:3], 1):
                message_parts.append(f"   {i}. {suggestion.suggestion}")
                if suggestion.example:
                    message_parts.append(f"      Example: {suggestion.example}")
            message_parts.append("")
        
        if response.troubleshooting_steps:
            message_parts.append("🔧 Troubleshooting steps:")
            for i, step in enumerate(response.troubleshooting_steps[:3], 1):
                message_parts.append(f"   {i}. {step}")
            message_parts.append("")
        
        if response.can_retry:
            message_parts.append("🔄 This error can be retried. The system will attempt to fix the issue automatically.")
        
        if show_technical_details:
            message_parts.extend([
                "",
                "🔍 Technical details:",
                f"   {response.error_message}"
            ])
        
        return "\n".join(message_parts)