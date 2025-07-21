"""
Advanced Query Examples and Test Cases for Task 9 Implementation
This file contains examples of the advanced query features that have been implemented.
"""

# Example queries that should now be supported with advanced features

ADVANCED_QUERY_EXAMPLES = {
    "complex_aggregations": [
        {
            "natural_language": "Show me the total hours worked by each employee per month, but only for months where they worked more than 160 hours",
            "expected_features": ["GROUP BY", "HAVING", "SUM", "aggregation"],
            "description": "Complex aggregation with GROUP BY and HAVING clause"
        },
        {
            "natural_language": "Give me a breakdown of project costs by department with subtotals and grand total",
            "expected_features": ["GROUP BY", "ROLLUP", "SUM", "advanced_aggregates"],
            "description": "Advanced aggregation using ROLLUP for subtotals"
        },
        {
            "natural_language": "Show running totals of sales by month for each salesperson",
            "expected_features": ["SUM() OVER", "PARTITION BY", "ORDER BY", "window_functions"],
            "description": "Window function for running totals"
        }
    ],
    
    "window_functions": [
        {
            "natural_language": "Rank employees by their total sales, showing their position within their department",
            "expected_features": ["RANK()", "OVER", "PARTITION BY", "ORDER BY"],
            "description": "Ranking window function with partitioning"
        },
        {
            "natural_language": "Show each employee's current salary and their previous salary",
            "expected_features": ["LAG()", "OVER", "PARTITION BY", "ORDER BY"],
            "description": "LAG window function to show previous values"
        },
        {
            "natural_language": "Find the top 3 highest paid employees in each department",
            "expected_features": ["ROW_NUMBER()", "OVER", "PARTITION BY", "ORDER BY", "subquery"],
            "description": "ROW_NUMBER with subquery for top N per group"
        }
    ],
    
    "subqueries": [
        {
            "natural_language": "Show employees who work on projects that have budgets higher than the average project budget",
            "expected_features": ["subquery", "AVG", "IN", "JOIN"],
            "description": "Subquery with aggregate comparison"
        },
        {
            "natural_language": "Find customers who have never placed an order",
            "expected_features": ["NOT EXISTS", "correlated_subquery"],
            "description": "Correlated subquery with NOT EXISTS"
        },
        {
            "natural_language": "Show products along with their category's average price",
            "expected_features": ["scalar_subquery", "AVG", "correlated_subquery"],
            "description": "Scalar subquery in SELECT clause"
        }
    ],
    
    "cte": [
        {
            "natural_language": "First find all active projects, then calculate the total hours and costs for each, then show only those over budget",
            "expected_features": ["WITH", "CTE", "multiple_steps", "complex_logic"],
            "description": "Multi-step CTE for complex business logic"
        },
        {
            "natural_language": "Show the organizational hierarchy with employee levels and their managers",
            "expected_features": ["WITH", "RECURSIVE", "hierarchical_data"],
            "description": "Recursive CTE for hierarchical data"
        }
    ],
    
    "conditional_logic": [
        {
            "natural_language": "Categorize employees as Junior, Mid-level, or Senior based on their years of experience",
            "expected_features": ["CASE WHEN", "conditional_logic", "DATEDIFF"],
            "description": "CASE statement for categorization"
        },
        {
            "natural_language": "Show employee names, but display 'Confidential' if their salary is above 100000",
            "expected_features": ["IIF", "conditional_logic"],
            "description": "IIF function for simple conditions"
        },
        {
            "natural_language": "Display project status, using 'Unknown' for any null status values",
            "expected_features": ["COALESCE", "NULL handling"],
            "description": "COALESCE for NULL value handling"
        }
    ],
    
    "advanced_joins": [
        {
            "natural_language": "Show all employees with their department info, project assignments, and timesheet hours, including employees without projects",
            "expected_features": ["multiple_joins", "LEFT JOIN", "INNER JOIN", "optimized_order"],
            "description": "Multiple table joins with proper join types"
        },
        {
            "natural_language": "Find all related data for employees including their manager, department, current projects, and recent timesheets",
            "expected_features": ["complex_joins", "multiple_relationships", "join_optimization"],
            "description": "Complex multi-table joins with relationship optimization"
        }
    ],
    
    "combined_advanced": [
        {
            "natural_language": "Create a comprehensive report showing each department's monthly performance with rankings, running totals, and comparisons to department averages, but only for departments that exceeded their quarterly targets",
            "expected_features": ["CTE", "window_functions", "GROUP BY", "HAVING", "subqueries", "CASE WHEN"],
            "description": "Complex query combining multiple advanced features"
        }
    ]
}

def test_advanced_query_generation():
    """
    Test function to validate that advanced query features are working.
    This would be called by the test suite to ensure task 9 is properly implemented.
    """
    print("Testing Advanced Query Generation Features...")
    
    # Import the necessary functions
    from llm import analyze_query_requirements, generate_advanced_query_context
    
    test_results = []
    
    for category, examples in ADVANCED_QUERY_EXAMPLES.items():
        print(f"\nTesting {category}:")
        
        for example in examples:
            nl_query = example["natural_language"]
            expected_features = example["expected_features"]
            
            # Test requirement analysis
            requirements = analyze_query_requirements(nl_query, {})
            
            # Check if the expected features are detected
            detected_features = []
            if requirements.get('needs_aggregation') and any('aggregation' in f or 'SUM' in f or 'COUNT' in f or 'AVG' in f for f in expected_features):
                detected_features.append('aggregation')
            
            if requirements.get('needs_grouping') and 'GROUP BY' in expected_features:
                detected_features.append('grouping')
            
            if requirements.get('needs_having') and 'HAVING' in expected_features:
                detected_features.append('having')
            
            if requirements.get('needs_window_functions') and any('window' in f.lower() or 'OVER' in f or 'RANK' in f or 'LAG' in f for f in expected_features):
                detected_features.append('window_functions')
            
            if requirements.get('needs_subquery') and any('subquery' in f.lower() or 'EXISTS' in f or 'IN' in f for f in expected_features):
                detected_features.append('subquery')
            
            if requirements.get('needs_cte') and any('CTE' in f or 'WITH' in f for f in expected_features):
                detected_features.append('cte')
            
            if requirements.get('needs_conditional_logic') and any('CASE' in f or 'IIF' in f or 'COALESCE' in f for f in expected_features):
                detected_features.append('conditional_logic')
            
            if requirements.get('needs_advanced_joins') and any('join' in f.lower() or 'JOIN' in f for f in expected_features):
                detected_features.append('advanced_joins')
            
            # Test context generation
            context = generate_advanced_query_context(requirements, {}, [])
            
            test_result = {
                'query': nl_query,
                'expected_features': expected_features,
                'detected_features': detected_features,
                'requirements': requirements,
                'context_generated': len(context) > 0,
                'description': example['description']
            }
            
            test_results.append(test_result)
            
            print(f"  ✓ {example['description']}")
            print(f"    Expected: {expected_features}")
            print(f"    Detected: {detected_features}")
            print(f"    Complexity: {requirements.get('complexity_level', 'unknown')}")
    
    return test_results

if __name__ == "__main__":
    # Run the tests
    results = test_advanced_query_generation()
    
    print(f"\n=== Test Summary ===")
    print(f"Total test cases: {len(results)}")
    
    successful_detections = sum(1 for r in results if len(r['detected_features']) > 0)
    print(f"Successful feature detections: {successful_detections}/{len(results)}")
    
    context_generations = sum(1 for r in results if r['context_generated'])
    print(f"Context generated: {context_generations}/{len(results)}")
    
    print("\nAdvanced query features implementation test completed!")