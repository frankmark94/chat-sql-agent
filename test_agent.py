#!/usr/bin/env python3
"""
Test script to verify the SQL agent works with the sample database.
"""

import os
import sys

sys.path.append("src")

from agents import create_sql_agent
from config import settings


def test_agent():
    """Test the SQL agent with the sample database."""

    print("🧪 Testing SQL Agent...")

    # Check if API key is available
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment!")
        print("Please set your API key in the .env file")
        return False

    if settings.OPENAI_API_KEY.startswith("sk-proj-"):
        print("✅ OpenAI API key found")
    else:
        print("⚠️  API key format might be invalid")

    # Check if database exists
    db_path = "sample_ecommerce.db"
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("Please run create_sample_db.py first")
        return False

    print(f"✅ Database file found: {db_path}")

    try:
        # Create agent
        database_uri = f"sqlite:///{db_path}"
        print(f"🔗 Creating agent with URI: {database_uri}")

        agent = create_sql_agent(database_uri)
        print("✅ Agent created successfully!")

        # Test a simple query
        print("\n🔍 Testing simple query...")
        try:
            response = agent.run("How many customers are in the database?")
            print(f"📝 Response: {response}")
            return True
        except Exception as e:
            print(f"❌ Query failed: {str(e)}")
            return False

    except Exception as e:
        print(f"❌ Agent creation failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_agent()
    if success:
        print("\n🎉 All tests passed! Your Chat-with-SQL Agent is ready!")
    else:
        print("\n❌ Tests failed. Please check the errors above.")

    sys.exit(0 if success else 1)
