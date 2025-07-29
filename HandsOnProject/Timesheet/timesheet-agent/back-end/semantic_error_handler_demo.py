#!/usr/bin/env python3
"""
SemanticErrorHandler Demo - Demonstration of intelligent error recovery capabilities.

This script demonstrates how the SemanticErrorHandler uses vector similarity and
semantic understanding to provide intelligent error recovery suggestions.
"""

import sys
import os
import tempfile
from typing import Dict, Any

# Add the back-end directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from semantic_error_handler import SemanticErrorHandler, ErrorType
from vector_schema_store import VectorSchemaStore
from semantic_intent_engine import SemanticIntentEngine
from adaptive_learning_engine import AdaptiveLearningEngine


def create_sample_schema_data():
    """Create sample schema data for demonstration"""
    return [
        {
            'schema': 'dbo',
            'table': 'Employees',
            'columns': [
                {'name': 'EmployeeID', 'data_type': 'int', 'description': 'Employee identifier'},
                {'name': 'FirstName', 'data_type': 'varchar', 'description': 'Employee first name'},
                {'name': 'LastName', 'data_type': 'varchar', 'description': 'Employee last name'},
                {'name': 'Email', 'data_type': 'varchar', 'description': 'Employee email address'},
                {'name': 'DepartmentID', 'data_type': 'int', 'description': 'Department identifier'},
                {'name': 'HireDate', 'data_type': 'datetime', 'description': 'Employee hire date'},
                {'name': 'Salary', 'data_type': 'decimal', 'description': 'Employee salary'}
            ],
            'description': 'Employee information table',
            'business_context': 'Core HR data'
        },
        {
            'schema': 'dbo',
            'table': 'Projects',
            'columns': [
                {'name': 'ProjectID', 'data_type': 'int', 'description': 'Project identifier'},
                {'name': 'ProjectName', 'data_type': 'varchar', 'description': 'Project name'},
                {'name': 'Description', 'data_type': 'text', 'description': 'Project description'},
                {'name': 'StartDate', 'data_type': 'datetime', 'description': 'Project start date'},
                {'name': 'EndDate', 'data_type': 'datetime', 'description': 'Project end date'},
                {'name': 'Status', 'data_type': 'varchar', 'description': 'Project status'}
            ],
            'description': 'Project information table',
            'business_context': 'Project management data'
        },
        {
            'schema': 'dbo',
            'table': 'Departments',
            'columns': [
                {'name': 'DepartmentID', 'data_type': 'int', 'description': 'Department identifier'},
                {'name': 'DepartmentName', 'data_type': 'varchar', 'description': 'Department name'},
                {'name': 'ManagerID', 'data_type': 'int', 'description': 'Department manager ID'},
                {'name': 'Budget', 'data_type': 'decimal', 'description': 'Department budget'}
            ],
            'description': 'Department information table',
            'business_context': 'Organizational structure data'
        }
    ]


def setup_demo_environment():
    """Set up the demo environment with sample data"""
    print("🔧 Setting up demo environment...")
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    vector_data_path = os.path.join(temp_dir, "vector_data")
    error_data_path = os.path.join(temp_dir, "error_data")
    learning_data_path = os.path.join(temp_dir, "learning_data")
    
    os.makedirs(vector_data_path, exist_ok=True)
    os.makedirs(error_data_path, exist_ok=True)
    os.makedirs(learning_data_path, exist_ok=True)
    
    # Initialize components
    print("   📊 Initializing VectorSchemaStore...")
    vector_store = VectorSchemaStore(vector_db_path=vector_data_path)
    
    print("   🧠 Initializing SemanticIntentEngine...")
    intent_engine = SemanticIntentEngine(vector_store)
    
    print("   📚 Initializing AdaptiveLearningEngine...")
    learning_engine = AdaptiveLearningEngine(vector_store, learning_data_path)
    
    print("   🛠️ Initializing SemanticErrorHandler...")
    error_handler = SemanticErrorHandler(
        vector_store=vector_store,
        intent_engine=intent_engine,
        learning_engine=learning_engine,
        error_data_path=error_data_path
    )
    
    # Load sample schema data
    print("   📋 Loading sample schema data...")
    schema_data = create_sample_schema_data()
    vector_store.ingest_schema(schema_data)
    
    print("✅ Demo environment setup complete!\n")
    
    return error_handler, temp_dir


def demonstrate_schema_error_recovery(error_handler: SemanticErrorHandler):
    """Demonstrate schema error recovery capabilities"""
    print("🔍 SCHEMA ERROR RECOVERY DEMONSTRATION")
    print("=" * 50)
    
    # Test case 1: Invalid table name (typo)
    print("\n📋 Test Case 1: Invalid Table Name (Typo)")
    print("-" * 40)
    
    error = Exception("Invalid object name 'Employes'")
    query_context = {
        'original_query': 'Show me all employees',
        'failed_sql': 'SELECT * FROM Employes',
        'error_type': 'schema_error'
    }
    
    print(f"❌ Error: {error}")
    print(f"🔤 Original Query: {query_context['original_query']}")
    print(f"💻 Failed SQL: {query_context['failed_sql']}")
    
    recovery_plan = error_handler.handle_schema_error(error, query_context)
    
    print(f"\n🎯 Recovery Strategy: {recovery_plan.strategy.value}")
    print(f"📊 Confidence: {recovery_plan.confidence:.3f}")
    print(f"🔄 Automatic Retry: {recovery_plan.automatic_retry}")
    print(f"📈 Estimated Success Rate: {recovery_plan.estimated_success_rate:.3f}")
    
    print(f"\n💡 Top Suggestions ({len(recovery_plan.suggestions)}):")
    for i, suggestion in enumerate(recovery_plan.suggestions[:3], 1):
        print(f"   {i}. {suggestion.description}")
        print(f"      Confidence: {suggestion.confidence:.3f}")
        print(f"      Reasoning: {suggestion.reasoning}")
        if suggestion.corrected_sql:
            print(f"      Corrected SQL: {suggestion.corrected_sql}")
        print()
    
    # Test case 2: Invalid column name
    print("\n📋 Test Case 2: Invalid Column Name")
    print("-" * 40)
    
    error = Exception("Invalid column name 'EmpID'")
    query_context = {
        'original_query': 'Show me employee IDs and names',
        'failed_sql': 'SELECT EmpID, FirstName FROM Employees',
        'error_type': 'schema_error'
    }
    
    print(f"❌ Error: {error}")
    print(f"🔤 Original Query: {query_context['original_query']}")
    print(f"💻 Failed SQL: {query_context['failed_sql']}")
    
    recovery_plan = error_handler.handle_schema_error(error, query_context)
    
    print(f"\n🎯 Recovery Strategy: {recovery_plan.strategy.value}")
    print(f"📊 Confidence: {recovery_plan.confidence:.3f}")
    
    print(f"\n💡 Top Suggestions:")
    for i, suggestion in enumerate(recovery_plan.suggestions[:2], 1):
        print(f"   {i}. {suggestion.description}")
        print(f"      Confidence: {suggestion.confidence:.3f}")
        if suggestion.corrected_sql:
            print(f"      Corrected SQL: {suggestion.corrected_sql}")
        print()


def demonstrate_syntax_error_recovery(error_handler: SemanticErrorHandler):
    """Demonstrate syntax error recovery capabilities"""
    print("\n🔧 SYNTAX ERROR RECOVERY DEMONSTRATION")
    print("=" * 50)
    
    # Test case 1: Missing closing parenthesis
    print("\n📋 Test Case 1: Missing Closing Parenthesis")
    print("-" * 40)
    
    error = Exception("Incorrect syntax near ')'")
    query_context = {
        'original_query': 'Show me employees named John',
        'failed_sql': "SELECT * FROM Employees WHERE (FirstName = 'John'",
        'error_type': 'syntax_error'
    }
    
    print(f"❌ Error: {error}")
    print(f"🔤 Original Query: {query_context['original_query']}")
    print(f"💻 Failed SQL: {query_context['failed_sql']}")
    
    recovery_plan = error_handler.handle_syntax_error(error, query_context)
    
    print(f"\n🎯 Recovery Strategy: {recovery_plan.strategy.value}")
    print(f"📊 Confidence: {recovery_plan.confidence:.3f}")
    print(f"🔄 Automatic Retry: {recovery_plan.automatic_retry}")
    
    print(f"\n💡 Top Suggestions:")
    for i, suggestion in enumerate(recovery_plan.suggestions[:3], 1):
        print(f"   {i}. {suggestion.description}")
        print(f"      Confidence: {suggestion.confidence:.3f}")
        if suggestion.corrected_sql:
            print(f"      Corrected SQL: {suggestion.corrected_sql}")
        print()
    
    # Test case 2: Complex query simplification
    print("\n📋 Test Case 2: Complex Query Simplification")
    print("-" * 40)
    
    error = Exception("Incorrect syntax near 'SELECT'")
    query_context = {
        'original_query': 'Show me employees with their projects and departments',
        'failed_sql': '''SELECT e.FirstName, e.LastName, p.ProjectName, d.DepartmentName 
                        FROM Employees e 
                        JOIN Projects p ON e.EmployeeID = p.EmployeeID 
                        JOIN Departments d ON e.DepartmentID = d.DepartmentID
                        WHERE e.HireDate > '2020-01-01' AND''',
        'error_type': 'syntax_error'
    }
    
    print(f"❌ Error: {error}")
    print(f"🔤 Original Query: {query_context['original_query']}")
    print(f"💻 Failed SQL: {query_context['failed_sql'][:100]}...")
    
    recovery_plan = error_handler.handle_syntax_error(error, query_context)
    
    print(f"\n🎯 Recovery Strategy: {recovery_plan.strategy.value}")
    print(f"📊 Confidence: {recovery_plan.confidence:.3f}")
    
    print(f"\n💡 Top Suggestions:")
    for i, suggestion in enumerate(recovery_plan.suggestions[:2], 1):
        print(f"   {i}. {suggestion.description}")
        print(f"      Confidence: {suggestion.confidence:.3f}")
        if suggestion.corrected_sql:
            print(f"      Corrected SQL: {suggestion.corrected_sql[:100]}...")
        print()


def demonstrate_execution_error_recovery(error_handler: SemanticErrorHandler):
    """Demonstrate execution error recovery capabilities"""
    print("\n⚡ EXECUTION ERROR RECOVERY DEMONSTRATION")
    print("=" * 50)
    
    # Test case 1: Query timeout
    print("\n📋 Test Case 1: Query Timeout")
    print("-" * 40)
    
    error = Exception("Query timeout expired. The timeout period elapsed prior to completion of the operation")
    query_context = {
        'original_query': 'Show me all employees with their complete project history',
        'failed_sql': '''SELECT e.*, p.*, d.* 
                        FROM Employees e 
                        JOIN Projects p ON e.EmployeeID = p.EmployeeID 
                        JOIN Departments d ON e.DepartmentID = d.DepartmentID
                        ORDER BY e.LastName, e.FirstName''',
        'error_type': 'execution_error'
    }
    
    print(f"❌ Error: {error}")
    print(f"🔤 Original Query: {query_context['original_query']}")
    print(f"💻 Failed SQL: {query_context['failed_sql'][:100]}...")
    
    recovery_plan = error_handler.handle_execution_error(error, query_context)
    
    print(f"\n🎯 Recovery Strategy: {recovery_plan.strategy.value}")
    print(f"📊 Confidence: {recovery_plan.confidence:.3f}")
    print(f"🔄 Automatic Retry: {recovery_plan.automatic_retry}")
    
    print(f"\n💡 Top Suggestions:")
    for i, suggestion in enumerate(recovery_plan.suggestions[:3], 1):
        print(f"   {i}. {suggestion.description}")
        print(f"      Confidence: {suggestion.confidence:.3f}")
        if suggestion.corrected_sql:
            print(f"      Corrected SQL: {suggestion.corrected_sql[:100]}...")
        print()
    
    # Test case 2: Permission error
    print("\n📋 Test Case 2: Permission Error")
    print("-" * 40)
    
    error = Exception("The SELECT permission was denied on the object 'Employees', database 'CompanyDB'")
    query_context = {
        'original_query': 'Show me employee salaries',
        'failed_sql': 'SELECT EmployeeID, FirstName, LastName, Salary FROM Employees',
        'error_type': 'execution_error'
    }
    
    print(f"❌ Error: {error}")
    print(f"🔤 Original Query: {query_context['original_query']}")
    print(f"💻 Failed SQL: {query_context['failed_sql']}")
    
    recovery_plan = error_handler.handle_execution_error(error, query_context)
    
    print(f"\n🎯 Recovery Strategy: {recovery_plan.strategy.value}")
    print(f"📊 Confidence: {recovery_plan.confidence:.3f}")
    
    print(f"\n💡 Top Suggestions:")
    for i, suggestion in enumerate(recovery_plan.suggestions[:2], 1):
        print(f"   {i}. {suggestion.description}")
        print(f"      Confidence: {suggestion.confidence:.3f}")
        print(f"      Reasoning: {suggestion.reasoning}")
        print()


def demonstrate_error_statistics(error_handler: SemanticErrorHandler):
    """Demonstrate error statistics and learning capabilities"""
    print("\n📊 ERROR STATISTICS AND LEARNING")
    print("=" * 50)
    
    stats = error_handler.get_error_statistics()
    
    print(f"📈 Total Errors Handled: {stats['total_errors_handled']}")
    print(f"✅ Successful Recoveries: {stats['successful_recoveries']}")
    print(f"❌ Failed Recoveries: {stats['failed_recoveries']}")
    print(f"🤖 Automatic Corrections: {stats['automatic_corrections']}")
    print(f"👤 Manual Interventions: {stats['manual_interventions']}")
    print(f"📋 Error Patterns Learned: {stats['error_patterns_count']}")
    print(f"🔄 Recovery Plans Created: {stats['recovery_plans_count']}")
    print(f"💾 Cached Alternatives: {stats['cached_alternatives_count']}")
    
    if stats['total_errors_handled'] > 0:
        print(f"📊 Success Rate: {stats['success_rate']:.1%}")
        print(f"🤖 Automatic Correction Rate: {stats['automatic_correction_rate']:.1%}")
    
    print(f"\n🕒 Last Error Session: {stats.get('last_error_session', 'None')}")


def main():
    """Main demonstration function"""
    print("🚀 SEMANTIC ERROR HANDLER DEMONSTRATION")
    print("=" * 60)
    print("This demo shows how the SemanticErrorHandler uses vector")
    print("similarity and semantic understanding for intelligent error recovery.")
    print()
    
    try:
        # Set up demo environment
        error_handler, temp_dir = setup_demo_environment()
        
        # Demonstrate different types of error recovery
        demonstrate_schema_error_recovery(error_handler)
        demonstrate_syntax_error_recovery(error_handler)
        demonstrate_execution_error_recovery(error_handler)
        demonstrate_error_statistics(error_handler)
        
        print("\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("The SemanticErrorHandler successfully demonstrated:")
        print("✅ Schema error recovery using vector similarity")
        print("✅ Syntax error detection and correction")
        print("✅ Execution error analysis and optimization")
        print("✅ Confidence-based recovery strategies")
        print("✅ Automatic retry capabilities")
        print("✅ Error pattern learning and statistics")
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary directory: {temp_dir}")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()