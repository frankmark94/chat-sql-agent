#!/usr/bin/env python3
"""
Test script for the enhanced SQL agent
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/src')

from agents_enhanced import create_enhanced_sql_agent
from config import settings
import traceback

def test_enhanced_agent():
    """Test the enhanced SQL agent with a sample database"""
    try:
        print("Testing Enhanced SQL Agent...")
        
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
        
        # Test a simple query
        test_query = "What tables are in the database?"
        print(f"\nTesting query: {test_query}")
        
        result = agent.invoke({"input": test_query})
        print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced agent: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_agent()
    if success:
        print("\n✅ Enhanced SQL Agent test completed successfully!")
    else:
        print("\n❌ Enhanced SQL Agent test failed!")