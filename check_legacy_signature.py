#!/usr/bin/env python3
"""
Check the legacy create_sql_agent function signature
"""

from langchain.agents import create_sql_agent
import inspect

print("🔍 Checking legacy create_sql_agent function signature...")
print("=" * 50)

# Get function signature
sig = inspect.signature(create_sql_agent)
print(f"Function signature: {sig}")

# Get parameter details
print("\nParameters:")
for name, param in sig.parameters.items():
    print(f"  {name}: {param}")

# Get docstring
print(f"\nDocstring (first 500 chars):")
doc = create_sql_agent.__doc__
if doc:
    print(doc[:500] + "..." if len(doc) > 500 else doc)
else:
    print("No docstring available")