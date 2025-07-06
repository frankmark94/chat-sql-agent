import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

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
    
    # Use standard agent initialization without custom prompt
    agent_kwargs = {}
    
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