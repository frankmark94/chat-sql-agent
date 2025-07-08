import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain import hub
from config import settings
from tools import get_custom_tools

def custom_parsing_error_handler(error):
    """Custom error handler for parsing errors."""
    error_message = str(error)
    
    # Check if it's a format error
    if "Could not parse LLM output" in error_message:
        # Extract the problematic output
        if "`" in error_message:
            llm_output = error_message.split("`")[1]
            # If output doesn't start with "Final Answer:", add it
            if not llm_output.startswith("Final Answer:"):
                return f"Final Answer: {llm_output}"
    
    # Default error message
    return "I apologize, but I encountered a format error. Let me try again with the correct format. Please rephrase your question if needed."

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
        api_key=settings.OPENAI_API_KEY,
        model_kwargs={"top_p": 0.1}  # Reduce randomness for better format adherence
    )
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    sql_tools = toolkit.get_tools()
    
    # Add custom tools with database path
    db_path = database_uri.replace("sqlite:///", "")  # Extract path from URI
    custom_tools = get_custom_tools(enable_reporting, enable_email, db_path)
    all_tools = sql_tools + custom_tools
    
    # Enhanced prompt template with stricter format rules
    enhanced_prompt = PromptTemplate.from_template("""You are an expert SQL analyst. Follow the format rules EXACTLY.

DATABASE SCHEMA:
- categories: product categories (category_id, category_name)
- products: product details (product_id, category_id, price)
- orders: order information (order_id, customer_id, order_date, total_amount)
- order_items: individual items in orders (order_id, product_id, quantity, unit_price, line_total)
- customers: customer information (customer_id, registration_date, customer_segment)
- reviews: product reviews (product_id, customer_id, rating)

TOOLS AVAILABLE: {tool_names}

{tools}

FORMAT RULES (MUST FOLLOW EXACTLY):
1. Every response must follow: Question → Thought → Action → Action Input → Observation → Thought → Final Answer
2. NEVER skip the "Thought:" prefix
3. NEVER provide text without "Thought:" or "Final Answer:" prefix
4. NEVER provide both Action and Final Answer in the same response
5. ALWAYS wait for Observation before next Thought
6. After tool execution, ALWAYS provide: "Thought: [analysis]" then "Final Answer: [result]"

EXAMPLE FORMAT:
Question: Create a bar chart of sales by category
Thought: I need to query sales data by category first.
Action: sql_db_query
Action Input: SELECT categories.category_name, SUM(order_items.line_total) as total_sales FROM order_items JOIN orders ON order_items.order_id = orders.order_id JOIN products ON order_items.product_id = products.product_id JOIN categories ON products.category_id = categories.category_id GROUP BY categories.category_name
Observation: [('Electronics', 500000), ('Clothing', 300000), ...]
Thought: Now I will create a bar chart with this data.
Action: create_database_visualization
Action Input: SELECT categories.category_name, SUM(order_items.line_total) as total_sales FROM order_items JOIN orders ON order_items.order_id = orders.order_id JOIN products ON order_items.product_id = products.product_id JOIN categories ON products.category_id = categories.category_id GROUP BY categories.category_name|bar|Sales by Category|category_name|total_sales
Observation: Visualization created successfully: reports/chart_20250708_123456.png
Thought: The bar chart has been created successfully and saved to the reports folder.
Final Answer: I have created a bar chart showing sales by category. The chart has been generated and saved to reports/chart_20250708_123456.png.

CRITICAL: After every tool execution, you MUST provide a "Thought:" followed by "Final Answer:". Never just provide text without these prefixes.

Question: {input}
{agent_scratchpad}""")
    
    # Create the ReAct agent
    agent = create_react_agent(
        llm=llm,
        tools=all_tools,
        prompt=enhanced_prompt
    )
    
    # Create agent executor with improved error handling
    agent_executor = AgentExecutor(
        agent=agent,
        tools=all_tools,
        verbose=True,
        handle_parsing_errors=custom_parsing_error_handler,  # Use custom error handler
        max_iterations=8,  # Reduce iterations to prevent loops
        early_stopping_method="force",
        return_intermediate_steps=True,
        max_execution_time=180  # 3 minutes timeout
    )
    
    return agent_executor

def run_agent_with_error_handling(agent, query: str, max_retries: int = 2):
    """
    Run the agent with enhanced error handling and retry logic.
    
    Args:
        agent: The agent executor
        query: The query to run
        max_retries: Maximum number of retries on parsing errors
    
    Returns:
        Agent response or error message
    """
    for attempt in range(max_retries + 1):
        try:
            # Run the agent
            response = agent.invoke({"input": query})
            return response
            
        except Exception as e:
            error_str = str(e)
            
            # Handle parsing errors specifically
            if "Could not parse LLM output" in error_str and attempt < max_retries:
                print(f"Parsing error on attempt {attempt + 1}, retrying...")
                continue
            
            # Handle other errors
            if "timeout" in error_str.lower():
                return {
                    "input": query,
                    "output": "The query timed out. Please try a simpler question or check your database connection.",
                    "intermediate_steps": []
                }
            
            elif "api" in error_str.lower() or "openai" in error_str.lower():
                return {
                    "input": query,
                    "output": "There was an issue with the OpenAI API. Please check your API key and try again.",
                    "intermediate_steps": []
                }
            
            else:
                return {
                    "input": query,
                    "output": f"An error occurred: {error_str}. Please try rephrasing your question.",
                    "intermediate_steps": []
                }
    
    # If all retries failed
    return {
        "input": query,
        "output": "Multiple parsing errors occurred. Please try rephrasing your question more clearly.",
        "intermediate_steps": []
    }