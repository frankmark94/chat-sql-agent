from langchain.agents import AgentType, initialize_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from config import settings
from tools import get_custom_tools


def create_sql_agent(database_uri: str, model_name: str = "gpt-3.5-turbo"):
    """
    Create a SQL agent that can interact with a database using natural language.

    Args:
        database_uri: Database connection string (e.g., "sqlite:///path/to/db.sqlite")
        model_name: OpenAI model to use for the agent

    Returns:
        Configured SQL agent
    """
    db = SQLDatabase.from_uri(database_uri)

    llm = ChatOpenAI(model=model_name, temperature=0, api_key=settings.OPENAI_API_KEY)

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # Get SQL tools from toolkit
    sql_tools = toolkit.get_tools()

    agent = initialize_agent(
        sql_tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
        early_stopping_method="generate",
        return_intermediate_steps=True
    )

    return agent


def create_advanced_sql_agent(
    database_uri: str,
    model_name: str = "gpt-4",
    enable_reporting: bool = True,
    enable_email: bool = True,
):
    """
    Create an advanced SQL agent with additional capabilities.

    Args:
        database_uri: Database connection string
        model_name: OpenAI model to use
        enable_reporting: Whether to include reporting tools
        enable_email: Whether to include email tools

    Returns:
        Configured advanced SQL agent
    """
    db = SQLDatabase.from_uri(database_uri)

    llm = ChatOpenAI(model=model_name, temperature=0, api_key=settings.OPENAI_API_KEY)

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # Get SQL tools from toolkit
    sql_tools = toolkit.get_tools()
    # Add optional custom tools
    custom_tools = get_custom_tools(
        enable_reporting=enable_reporting,
        enable_email=enable_email,
    )

    agent = initialize_agent(
        sql_tools + custom_tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
        early_stopping_method="generate",
        return_intermediate_steps=True
    )

    return agent
