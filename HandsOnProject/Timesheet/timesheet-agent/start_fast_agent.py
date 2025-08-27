#!/usr/bin/env python3
"""
Fast RAG SQL Agent Startup Script

This script demonstrates the performance improvements by starting the optimized agent
and running a sample query to show the dramatic speed improvement.
"""

import sys
import os
import time

# Add back-end to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'back-end'))

def main():
    """Main startup function"""
    
    print("🚀 Fast RAG SQL Agent Startup")
    print("=" * 50)
    
    try:
        # Import and initialize the fast agent
        print("📦 Loading optimized components...")
        from fast_rag_sql_agent import FastRAGSQLAgent
        from fast_config import get_performance_config
        
        # Create agent with maximum speed configuration
        print("⚡ Initializing Fast RAG Agent (Maximum Speed Mode)...")
        config = get_performance_config('maximum_speed')
        agent = FastRAGSQLAgent(performance_config=config, performance_level='maximum_speed')
        
        print("✅ Fast RAG Agent initialized successfully!")
        print(f"   • Cache TTL: {config.cache_ttl_seconds} seconds")
        print(f"   • Max Workers: {config.max_workers}")
        print(f"   • LLM Timeout: {config.llm_timeout} seconds")
        print(f"   • Aggressive Caching: {config.enable_aggressive_caching}")
        
        # Demonstrate performance with a sample query
        print("\n🔍 Testing Performance with Sample Query")
        print("-" * 40)
        
        sample_query = "Show me all projects for client 'C. Steinweg'"
        print(f"Query: {sample_query}")
        
        # Measure processing time
        print("⏱️  Processing query...")
        start_time = time.time()
        
        result = agent.process_query_fast(sample_query)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Display results
        print(f"\n📊 Results:")
        print(f"   ✅ Success: {result.success}")
        print(f"   ⚡ Processing Time: {processing_time:.2f} seconds")
        print(f"   🎯 Confidence: {result.confidence:.2f}")
        
        if result.sql_query:
            print(f"   📝 Generated SQL:")
            print(f"      {result.sql_query}")
        
        if result.results:
            print(f"   📈 Results Found: {len(result.results)} rows")
            if result.columns:
                print(f"   📋 Columns: {', '.join(result.columns)}")
        
        if result.natural_language_response:
            print(f"   💬 Response: {result.natural_language_response}")
        
        # Show performance breakdown
        if result.performance_metrics:
            print(f"\n⚡ Performance Breakdown:")
            for metric, value in result.performance_metrics.items():
                if isinstance(value, (int, float)) and 'time' in metric:
                    print(f"      {metric.replace('_', ' ').title()}: {value:.1f}ms")
        
        # Show cache performance
        if result.cache_hits:
            print(f"\n🎯 Cache Performance:")
            for cache_type, hit in result.cache_hits.items():
                status = "🟢 HIT" if hit else "🔴 MISS"
                print(f"      {cache_type.title()}: {status}")
        
        # Show overall statistics
        stats = agent.get_performance_statistics()
        print(f"\n📊 Agent Statistics:")
        print(f"   Total Queries: {stats['query_stats']['total_queries']}")
        print(f"   Fast Queries: {stats['query_stats']['fast_queries']}")
        print(f"   Success Rate: {stats['query_stats']['fast_success_rate']:.1%}")
        
        # Performance comparison
        print(f"\n🏆 Performance Improvement:")
        print(f"   Original Agent: ~120+ seconds")
        print(f"   Fast Agent: {processing_time:.2f} seconds")
        if processing_time > 0:
            improvement = (120 - processing_time) / 120 * 100
            speedup = 120 / processing_time
            print(f"   Improvement: {improvement:.1f}% faster")
            print(f"   Speedup: {speedup:.1f}x")
        
        # Test cache performance with repeat query
        print(f"\n🔄 Testing Cache Performance (Repeat Query)...")
        start_time = time.time()
        result2 = agent.process_query_fast(sample_query)
        cached_time = time.time() - start_time
        
        print(f"   Cached Query Time: {cached_time:.2f} seconds")
        if cached_time > 0 and processing_time > 0:
            cache_speedup = processing_time / cached_time
            print(f"   Cache Speedup: {cache_speedup:.1f}x")
        
        print(f"\n🎉 Fast RAG SQL Agent is ready!")
        print(f"   • Average response time: {processing_time:.2f}s")
        print(f"   • Cache-enabled for even faster subsequent queries")
        print(f"   • Fallback to original agent if needed")
        
        # Show how to use the agent
        print(f"\n📚 Usage Examples:")
        print(f"   # Python API")
        print(f"   from fast_rag_sql_agent import process_query_fast")
        print(f"   result = process_query_fast('Your query here')")
        print(f"")
        print(f"   # REST API (start server with: python back-end/main.py)")
        print(f"   curl -X POST http://localhost:5000/query \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"query\": \"Your query here\"}}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n✅ Startup completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Startup failed!")
        sys.exit(1)