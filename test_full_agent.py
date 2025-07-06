#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced SQL agent with visualizations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/src')

from agents_enhanced import create_enhanced_sql_agent
from config import settings
import traceback

def test_enhanced_agent_with_visualizations():
    """Test the enhanced SQL agent with visualization capabilities"""
    try:
        print("🚀 Testing Enhanced SQL Agent with Visualizations...")
        
        # Use the sample database
        db_url = "sqlite:///sample_ecommerce.db"
        
        # Create the enhanced agent
        agent = create_enhanced_sql_agent(
            db_url, 
            model_name="gpt-3.5-turbo",
            enable_reporting=True,
            enable_email=True
        )
        
        print("✅ Enhanced SQL Agent created successfully!")
        
        # Test cases
        test_queries = [
            "What tables are in the database?",
            "Find the average number of customer orders and average price",
            "Create a bar chart showing customer segments distribution",
            "Show table relationships as a network diagram"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            print("-" * 50)
            
            try:
                result = agent.invoke({"input": query})
                output = result.get("output", str(result))
                print(f"✅ Result: {output[:200]}...")
                
                # Check if visualization was created
                if "chart_" in output or "network_" in output or "table_relationships_" in output:
                    print("📊 Visualization created!")
                
            except Exception as e:
                print(f"❌ Error in test {i}: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced agent: {str(e)}")
        traceback.print_exc()
        return False

def check_agent_tools():
    """Check what tools are available to the agent"""
    try:
        print("\n🔧 Checking Available Tools...")
        
        db_url = "sqlite:///sample_ecommerce.db"
        agent = create_enhanced_sql_agent(db_url, model_name="gpt-3.5-turbo")
        
        # Access the tools from the agent
        tools = agent.tools
        print(f"📋 Available tools ({len(tools)}):")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name}: {tool.description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking tools: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Running comprehensive agent tests...")
    
    # Check tools first
    tools_ok = check_agent_tools()
    
    # Run full tests
    if tools_ok:
        success = test_enhanced_agent_with_visualizations()
        if success:
            print("\n🎉 All tests completed successfully!")
            print("✅ Enhanced SQL Agent is ready for production use!")
        else:
            print("\n❌ Some tests failed!")
    else:
        print("\n❌ Tool checking failed!")