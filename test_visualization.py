#!/usr/bin/env python3
"""
Test script for visualization tools
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/src')

from visualization_tools import DatabaseVisualizationTool, TableRelationshipTool
import traceback

def test_visualization_tools():
    """Test the visualization tools"""
    try:
        print("Testing Visualization Tools...")
        
        # Test database visualization tool
        viz_tool = DatabaseVisualizationTool(db_path="sample_ecommerce.db")
        
        # Test simple bar chart
        query = "SELECT customer_segment, COUNT(*) as count FROM customers GROUP BY customer_segment"
        result = viz_tool._run(query, "bar", "Customer Segments Distribution")
        print(f"Bar chart result: {result}")
        
        # Test table relationship diagram
        rel_tool = TableRelationshipTool(db_path="sample_ecommerce.db")
        result = rel_tool._run()
        print(f"Relationship diagram result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing visualization tools: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_visualization_tools()
    if success:
        print("\n✅ Visualization tools test completed successfully!")
    else:
        print("\n❌ Visualization tools test failed!")