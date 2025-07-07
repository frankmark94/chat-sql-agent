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
    
    # Enhanced prompt template for better SQL understanding
    enhanced_prompt = PromptTemplate(
        input_variables=["input", "agent_scratchpad", "tool_names", "tools"],
        template="""You are an expert SQL analyst with deep understanding of e-commerce databases. 

DATABASE SCHEMA UNDERSTANDING:
This database contains these key tables and relationships:
- categories: stores product categories (category_id, category_name)
- products: product details (product_id, category_id, price, created_at)
- orders: order information (order_id, customer_id, order_date, total_amount)
- order_items: individual items in orders (order_id, product_id, quantity, unit_price, line_total)
- customers: customer information (customer_id, registration_date, customer_segment)
- reviews: product reviews (product_id, customer_id, rating, review_date)

SALES DATA PATTERNS:
- Sales data comes from joining orders + order_items + products + categories
- For sales by category: JOIN products.category_id = categories.category_id
- For sales over time: Use orders.order_date for time filtering
- For sales amounts: Use order_items.line_total or order_items.quantity * order_items.unit_price

COMMON QUERY PATTERNS:
1. Category Sales: SELECT categories.category_name, SUM(order_items.line_total) FROM order_items 
   JOIN orders ON order_items.order_id = orders.order_id 
   JOIN products ON order_items.product_id = products.product_id 
   JOIN categories ON products.category_id = categories.category_id

2. Time-based Sales: Use DATE() functions for SQLite:
   - Last 6 months: WHERE orders.order_date >= DATE('now', '-6 months')
   - Monthly grouping: GROUP BY strftime('%Y-%m', orders.order_date)

3. Visualization Data: Always include time/category dimensions and aggregated values

IMPORTANT RULES:
1. ALWAYS check table structure first with sql_db_schema before writing queries
2. Use proper JOINs to connect related tables
3. For "Toys & Games" category, look for category_name = 'Toys & Games' 
4. Date filtering should use orders.order_date, not products.created_at
5. Sales amounts should come from order_items.line_total
6. When creating visualizations, ensure data has proper time series or categorical grouping

CRITICAL VISUALIZATION WORKFLOW:
When user requests ANY chart/graph/plot, you MUST follow this EXACT sequence:

STEP 1: Build and test the SQL query
STEP 2: Run sql_db_query to verify the query works and get results  
STEP 3: IMMEDIATELY call create_database_visualization tool with the working query
STEP 4: Do NOT provide "Final Answer" until AFTER creating the visualization

VISUALIZATION TOOL FORMAT:
Action: create_database_visualization
Action Input: [COMPLETE_WORKING_SQL_QUERY]|[CHART_TYPE]|[TITLE]|[X_COLUMN]|[Y_COLUMN]

EXAMPLE WORKFLOW for "bar chart of average order amount by category":
1. Action: sql_db_query
   Input: SELECT AVG(o.total_amount) as avg_order_amount, c.category_name as category FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id JOIN categories c ON p.category_id = c.category_id GROUP BY c.category_name
2. Action: create_database_visualization  
   Input: SELECT AVG(o.total_amount) as avg_order_amount, c.category_name as category FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id JOIN categories c ON p.category_id = c.category_id GROUP BY c.category_name|bar|Average Order Amount by Category|category|avg_order_amount

MANDATORY RULES:
- NEVER end with "Final Answer" for visualization requests without calling create_database_visualization
- Chart types: line, bar, scatter, pie, histogram, heatmap, network
- Column names in visualization tool must match query SELECT aliases exactly

You have access to these tools: {tool_names}

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

CRITICAL: For visualization requests (charts/graphs/plots), you MUST call create_database_visualization before providing Final Answer. Do NOT end with "Final Answer" until you have successfully created the visualization!

Question: {input}
{agent_scratchpad}"""
    )
    
    agent_kwargs = {
        "prompt": enhanced_prompt
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