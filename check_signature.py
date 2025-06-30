#!/usr/bin/env python3
"""
Check the actual function signature of create_sql_agent
"""

from langchain_community.agent_toolkits.sql.base import create_sql_agent
import inspect

print("🔍 Checking create_sql_agent function signature...")
print("=" * 50)

# Get function signature
sig = inspect.signature(create_sql_agent)
print(f"Function signature: {sig}")

# Get parameter details
print("\nParameters:")
for name, param in sig.parameters.items():
    print(f"  {name}: {param}")

# Get docstring
print(f"\nDocstring:")
print(create_sql_agent.__doc__)