from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import PromptTemplate
from config import settings
from tools import get_custom_tools

def create_enhanced_sql_agent(
    database_uri: str, 
    model_name: str = "gpt-4",
    enable_reporting: bool = True,
    enable_email: bool = True
):
    """
    Create an enhanced SQL agent with better prompting and tool integration.
    
    Args:
        database_uri: Database connection string
        model_name: OpenAI model to use
        enable_reporting: Whether to include reporting tools
        enable_email: Whether to include email tools
    
    Returns:
        Configured enhanced SQL agent
    """
    db = SQLDatabase.from_uri(database_uri)
    
    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    )
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    sql_tools = toolkit.get_tools()
    
    # Add custom tools with database path
    db_path = database_uri.replace("sqlite:///", "")  # Extract path from URI
    custom_tools = get_custom_tools(enable_reporting, enable_email, db_path)
    all_tools = sql_tools + custom_tools
    
    # Create agent with custom prompt
    agent_kwargs = {
        "prefix": """You are an expert SQL analyst with visualization capabilities. You have access to a database and powerful tools to analyze data and create visualizations.

When users ask questions:
1. First examine the database schema to understand the structure
2. Write and execute SQL queries to get the required data
3. For data analysis questions, always execute queries and provide actual results
4. When users ask for charts, graphs, or visualizations, use the visualization tools
5. For relationship questions, consider using the table relationship diagram tool

Key visualization guidelines:
- Use "create_database_visualization" for data-based charts (bar, line, scatter, pie, histogram, heatmap)
- Use "create_table_relationship_diagram" to show how database tables are connected
- Always execute SQL queries first to get the data, then visualize if requested
- Provide clear, actionable insights from the data

Available tools:""",
        "format_instructions": """Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Remember: Always execute queries to get actual data. Don't just describe what you would do - actually do it!""",
        "suffix": """Begin!

Question: {input}
Thought: {agent_scratchpad}"""
    }
    
    agent = initialize_agent(
        all_tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=15,
        early_stopping_method="generate",
        return_intermediate_steps=True,
        agent_kwargs=agent_kwargs
    )
    
    return agent