#!/usr/bin/env python3
"""
Simple working SQL agent implementation for testing
"""

import sys
import os
sys.path.append('src')

from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.agents import create_sql_agent, AgentType
from langchain.agents.agent_types import AgentType
from config import settings

def create_simple_sql_agent(database_uri: str):
    """Create a simple SQL agent that definitely works."""
    
    # Create database connection
    db = SQLDatabase.from_uri(database_uri)
    
    # Create LLM
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    )
    
    # Create toolkit
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    
    # Try different approaches
    try:
        # Approach 1: Use deprecated but working import
        from langchain.agents import create_sql_agent as old_create_sql_agent
        agent = old_create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True
        )
        print("✅ Used legacy create_sql_agent")
        return agent
    except:
        pass
    
    try:
        # Approach 2: Manual agent creation
        from langchain.agents import initialize_agent
        tools = toolkit.get_tools()
        agent = initialize_agent(
            tools, 
            llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True
        )
        print("✅ Used initialize_agent")
        return agent
    except:
        pass
    
    raise Exception("Could not create SQL agent with any method")

if __name__ == "__main__":
    try:
        database_uri = "sqlite:///sample_ecommerce.db"
        agent = create_simple_sql_agent(database_uri)
        
        # Test the agent
        response = agent.run("How many customers are in the database?")
        print(f"Response: {response}")
        
        print("🎉 Success!")
    except Exception as e:
        print(f"❌ Failed: {e}")