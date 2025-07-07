import os
import sys
import tempfile

import pandas as pd
import streamlit as st
from openai import OpenAI
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../src")

from agents import create_sql_agent
from agents_enhanced import create_enhanced_sql_agent
from config import settings


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_available_models():
    """Fetch available OpenAI models."""
    try:
        if not settings.OPENAI_API_KEY:
            return ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        models = client.models.list()

        # Filter for relevant chat models
        chat_models = []
        for model in models.data:
            model_name = model.id
            # Only include GPT models suitable for chat
            if any(prefix in model_name.lower() for prefix in ["gpt-3.5", "gpt-4"]):
                chat_models.append(model_name)

        # Sort models with preferred ones first
        preferred_order = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        sorted_models = []

        # Add preferred models first (if available)
        for preferred in preferred_order:
            matching = [m for m in chat_models if preferred in m]
            if matching:
                sorted_models.extend(sorted(matching))

        # Add remaining models
        remaining = [
            m
            for m in chat_models
            if not any(preferred in m for preferred in preferred_order)
        ]
        sorted_models.extend(sorted(remaining))

        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in sorted_models:
            if model not in seen:
                seen.add(model)
                unique_models.append(model)

        return (
            unique_models
            if unique_models
            else ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
        )

    except Exception as e:
        st.warning(f"Could not fetch models from OpenAI: {str(e)}")
        # Return fallback models
        return ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]


st.set_page_config(page_title="Chat with SQL Agent", page_icon="🗣️", layout="wide")

st.title("🗣️ Chat with SQL Agent")
st.markdown("Ask questions about your database in natural language!")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gpt-3.5-turbo"

if "show_reasoning" not in st.session_state:
    st.session_state.show_reasoning = False

if "db_connected" not in st.session_state:
    st.session_state.db_connected = False

if "db_url" not in st.session_state:
    st.session_state.db_url = None

if "agent_type" not in st.session_state:
    st.session_state.agent_type = "Enhanced SQL Agent"

@st.dialog("Database Configuration")
def database_config_modal():
    """Modal dialog for database configuration"""
    st.markdown("### 🗄️ Connect to Your Database")
    st.markdown("Choose your database type and provide connection details.")
    
    # Database type selection
    db_type = st.selectbox(
        "Database Type", 
        ["SQLite", "PostgreSQL", "MySQL"],
        help="Select your database type"
    )
    
    db_url = None
    
    if db_type == "SQLite":
        st.markdown("**📁 Upload SQLite Database File**")
        db_file = st.file_uploader(
            "Choose a SQLite database file", 
            type=["db", "sqlite", "sqlite3"],
            help="Upload your .db, .sqlite, or .sqlite3 file"
        )
        
        if db_file:
            # Save uploaded file to data directory
            file_path = os.path.join(settings.DATA_DIR, f"uploaded_{db_file.name}")
            with open(file_path, "wb") as f:
                f.write(db_file.getbuffer())
            db_url = f"sqlite:///{file_path}"
            st.success(f"✅ File uploaded: {db_file.name}")
    
    else:
        st.markdown(f"**🔗 {db_type} Connection Details**")
        
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("Host", value="localhost", help="Database server hostname")
            database = st.text_input("Database Name", help="Name of the database")
        
        with col2:
            port = st.number_input(
                "Port", 
                value=5432 if db_type == "PostgreSQL" else 3306,
                min_value=1,
                max_value=65535,
                help="Database server port"
            )
            username = st.text_input("Username", help="Database username")
        
        password = st.text_input("Password", type="password", help="Database password")
        
        if all([host, port, database, username, password]):
            if db_type == "PostgreSQL":
                db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            elif db_type == "MySQL":
                db_url = f"mysql://{username}:{password}@{host}:{port}/{database}"
            
            st.info(f"🔗 Connection URL: {db_type.lower()}://{username}:***@{host}:{port}/{database}")
    
    st.divider()
    
    # Test Connection button
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Test Connection", type="primary", use_container_width=True):
            if not db_url:
                st.error("❌ Please provide all required connection details")
            else:
                test_connection(db_url)
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()

def test_connection(db_url):
    """Test database connection and initialize agent if successful"""
    try:
        with st.spinner("Testing database connection..."):
            # Test connection
            engine = create_engine(db_url)
            with engine.connect() as conn:
                # Test a simple query using text() for SQLAlchemy 2.0+
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
        
        st.success("✅ Database connection successful!")
        
        # Initialize agent
        with st.spinner(f"Initializing {st.session_state.agent_type} with {st.session_state.selected_model}..."):
            if st.session_state.agent_type == "Enhanced SQL Agent":
                agent = create_enhanced_sql_agent(
                    db_url, 
                    model_name=st.session_state.selected_model,
                    enable_reporting=True,
                    enable_email=True
                )
            else:
                agent = create_sql_agent(db_url, model_name=st.session_state.selected_model)
        
        # Store in session state
        st.session_state.db_url = db_url
        st.session_state.agent = agent
        st.session_state.db_connected = True
        
        st.success(f"🎉 {st.session_state.agent_type} initialized successfully!")
        st.info("You can now start asking questions about your database.")
        
        # Small delay to show success message
        import time
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")
        st.error("Please check your connection details and try again.")
        
        # Show detailed error info
        with st.expander("🔍 Error Details"):
            st.code(str(e))

# Check if database is connected, if not show modal
if not st.session_state.db_connected:
    database_config_modal()
    st.stop()

# Show current configuration
if st.session_state.agent:
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.success("🟢 Connected to database")
    with col2:
        st.info(f"🤖 Using {st.session_state.selected_model}")
    with col3:
        if st.button("🔄 Reconnect"):
            st.session_state.db_connected = False
            st.session_state.agent = None
            st.rerun()

with st.sidebar:
    st.header("🔧 Configuration")
    
    # ===========================
    # STATUS HEADER
    # ===========================
    def get_status_badge(connected, value=None):
        if connected:
            return f"🟢 {value}" if value else "🟢 Connected"
        else:
            return "🔴 Not Connected"
    
    def get_email_status():
        if settings.EMAIL_FROM and settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            tls_status = "TLS" if settings.SMTP_USE_TLS else "No TLS"
            return f"🟢 Configured | {tls_status}"
        elif settings.EMAIL_FROM:
            return "🟡 Partial Setup"
        else:
            return "🔴 Not Configured"
    
    # Status Overview
    st.markdown("### 📊 Status Overview")
    if st.session_state.db_connected:
        db_type = st.session_state.db_url.split("://")[0].upper()
        st.markdown(f"**Database:** {get_status_badge(True, f'{db_type} | {st.session_state.agent_type}')}")
    else:
        st.markdown(f"**Database:** {get_status_badge(False)}")
    
    st.markdown(f"**Email:** {get_email_status()}")
    st.markdown(f"**Model:** 🤖 {st.session_state.selected_model}")
    
    st.divider()
    
    # ===========================
    # 🔗 DATABASE SECTION
    # ===========================
    with st.expander("🔗 Database Settings", expanded=not st.session_state.db_connected):
        st.caption("Choose and configure your database connection")
        
        if st.session_state.db_connected:
            st.success("✅ Database connected")
            
            # Clean display of current connection
            db_type = st.session_state.db_url.split("://")[0].upper()
            if "sqlite" in st.session_state.db_url.lower():
                db_path = st.session_state.db_url.split("///")[-1]
                db_name = os.path.basename(db_path)
                st.info(f"📁 **File:** {db_name}")
            else:
                # Extract host and database name for other DB types
                try:
                    url_parts = st.session_state.db_url.split("://")[1]
                    if "@" in url_parts:
                        host_db = url_parts.split("@")[1]
                        host = host_db.split("/")[0].split(":")[0]
                        db_name = host_db.split("/")[1] if "/" in host_db else "Unknown"
                        st.info(f"🌐 **Host:** {host}")
                        st.info(f"🗄️ **Database:** {db_name}")
                except:
                    st.info(f"🔗 **URL:** {st.session_state.db_url[:50]}...")
            
            st.info(f"🤖 **Agent:** {st.session_state.agent_type}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reconnect", use_container_width=True):
                    st.session_state.db_connected = False
                    st.session_state.agent = None
                    st.rerun()
            with col2:
                if st.button("🔄 Change DB", use_container_width=True):
                    st.session_state.db_connected = False
                    st.session_state.agent = None
                    st.session_state.db_url = None
                    st.rerun()
        else:
            st.warning("⚠️ No database connected")
            st.info("Click here or restart the app to open the database configuration modal.")
            
            if st.button("🔗 Open Database Config", use_container_width=True, type="primary"):
                st.session_state.db_connected = False
                st.rerun()
    
    # ===========================
    # 🤖 AI AGENT & REASONING
    # ===========================
    with st.expander("🤖 AI Agent & Reasoning", expanded=False):
        st.caption("Configure your AI model and reasoning options")
        
        # Agent Type Selection
        st.markdown("**Agent Type**")
        agent_type = st.selectbox(
            "Select Agent Type",
            ["Enhanced SQL Agent", "Basic SQL Agent"],
            index=0 if st.session_state.agent_type == "Enhanced SQL Agent" else 1,
            help="Enhanced agent has advanced SQL execution, visualizations, and reporting tools",
            label_visibility="collapsed"
        )
        
        if agent_type != st.session_state.agent_type:
            st.session_state.agent_type = agent_type
            if st.session_state.db_connected:
                st.session_state.agent = None
                st.session_state.db_connected = False
                st.info("🔄 Agent type changed. Please reconnect to database.")
        
        st.divider()
        
        # Model Selection
        st.markdown("**AI Model**")
        available_models = get_available_models()
        
        model_descriptions = {
            "gpt-4o": "Latest and most capable (Recommended)",
            "gpt-4-turbo": "Fast and powerful",
            "gpt-4": "High quality responses", 
            "gpt-3.5-turbo": "Fast and cost-effective",
        }
        
        model_options = []
        for model in available_models:
            if model in model_descriptions:
                model_options.append(f"{model} - {model_descriptions[model]}")
            else:
                model_options.append(model)
        
        current_index = 0
        for i, model in enumerate(available_models):
            if model == st.session_state.selected_model:
                current_index = i
                break
        
        selected_model_display = st.selectbox(
            "Select OpenAI Model",
            model_options,
            index=current_index,
            help="Choose the AI model for SQL generation and analysis",
            label_visibility="collapsed"
        )
        
        selected_model = selected_model_display.split(" - ")[0]
        st.session_state.selected_model = selected_model
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            pass  # Keep for balance
        
        st.divider()
        
        # Reasoning Options
        st.markdown("**Reasoning Options**")
        show_reasoning = st.checkbox(
            "Show reasoning steps",
            value=st.session_state.show_reasoning,
            help="Display the AI's intermediate thinking steps and SQL queries"
        )
        st.session_state.show_reasoning = show_reasoning
        
        if show_reasoning:
            st.info("💡 Reasoning steps will appear below each response")
        
        # Enhanced Agent Features
        if st.session_state.agent_type == "Enhanced SQL Agent":
            with st.expander("📊 Visualization Examples", expanded=False):
                st.markdown("""
                **Available visualizations:**
                • Bar charts: "sales by region"
                • Pie charts: "order status distribution" 
                • Scatter plots: "price vs ratings"
                • Histograms: "customer age distribution"
                • Network diagrams: "table relationships"
                • Heatmaps: "correlation matrix"
                """)
                st.info("💡 Just ask in natural language - visualizations appear automatically!")
    
    # ===========================
    # 📬 EMAIL & NOTIFICATIONS
    # ===========================
    with st.expander("📬 Email & Notifications", expanded=False):
        st.caption("Configure email reporting and notifications")
        
        # Email Enable Toggle
        email_enabled = st.checkbox(
            "Enable Email Notifications",
            value=bool(settings.EMAIL_FROM),
            help="Enable email functionality for sending reports"
        )
        
        if email_enabled:
            # Basic Email Settings
            st.markdown("**Basic Settings**")
            email_from = st.text_input(
                "From Email", 
                value=settings.EMAIL_FROM if settings.EMAIL_FROM else "", 
                help="Email address to send reports from"
            )
            
            # Advanced SMTP Settings
            with st.expander("🔧 SMTP Settings", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    smtp_server = st.text_input(
                        "SMTP Server", 
                        value=settings.SMTP_SERVER, 
                        help="e.g., smtp.gmail.com"
                    )
                    smtp_username = st.text_input(
                        "Username", 
                        value=settings.SMTP_USERNAME if settings.SMTP_USERNAME else "", 
                        help="SMTP authentication username"
                    )
                
                with col2:
                    smtp_port = st.number_input(
                        "Port", 
                        value=settings.SMTP_PORT, 
                        min_value=1, 
                        max_value=65535,
                        help="Usually 587 or 465"
                    )
                    smtp_use_tls = st.checkbox(
                        "Use TLS", 
                        value=settings.SMTP_USE_TLS, 
                        help="Enable TLS encryption"
                    )
                
                smtp_password = st.text_input(
                    "Password", 
                    type="password", 
                    help="SMTP authentication password"
                )
            
            # Update settings
            settings.EMAIL_FROM = email_from
            settings.SMTP_SERVER = smtp_server
            settings.SMTP_PORT = smtp_port
            settings.SMTP_USE_TLS = smtp_use_tls
            if smtp_username:
                settings.SMTP_USERNAME = smtp_username
            if smtp_password:
                settings.SMTP_PASSWORD = smtp_password
            
            # Action Buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧪 Test Email", use_container_width=True):
                    if not email_from:
                        st.error("Please enter a 'From Email' address")
                    else:
                        try:
                            import smtplib
                            server = smtplib.SMTP(smtp_server, smtp_port)
                            if smtp_use_tls:
                                server.starttls()
                            
                            if smtp_username and smtp_password:
                                server.login(smtp_username, smtp_password)
                                st.success("✅ Email test successful!")
                            else:
                                st.success("✅ Server connection successful!")
                                st.info("💡 No authentication configured")
                            
                            server.quit()
                        except Exception as e:
                            st.error(f"❌ Email test failed: {str(e)}")
            
            with col2:
                pass  # Keep for balance
            
            # Send Report Section
            if st.session_state.messages:
                st.divider()
                st.markdown("**📤 Send Report**")
                recipient_email = st.text_input(
                    "Recipient Email", 
                    help="Email address to send the conversation report to"
                )
                
                if st.button("📧 Send Report", use_container_width=True, type="primary"):
                    if not recipient_email:
                        st.error("Please enter a recipient email address")
                    elif not email_from:
                        st.error("Please configure 'From Email' address first")
                    else:
                        with st.spinner("Generating and sending report..."):
                            try:
                                from tools import send_email
                                from reporting import create_report_from_messages
                                
                                report_path = create_report_from_messages(st.session_state.messages)
                                send_email(report_path, recipient_email)
                                st.success(f"✅ Report sent to {recipient_email}!")
                            except Exception as e:
                                st.error(f"❌ Failed to send report: {str(e)}")
        else:
            st.info("📧 Email notifications are disabled")
            st.caption("Enable email to send reports and get notifications")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about your data..."):
    if not st.session_state.db_connected or not st.session_state.agent:
        st.error("Please connect to a database first!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get response with or without intermediate steps
                    if st.session_state.show_reasoning:
                        response = st.session_state.agent.invoke(
                            {"input": prompt}, return_only_outputs=False
                        )
                        output = response["output"]
                        intermediate_steps = response.get("intermediate_steps", [])

                        st.markdown(output)
                        
                        # Check if any visualizations were created
                        if "chart_" in output or "network_" in output or "table_relationships_" in output:
                            # Extract image paths from response
                            import re
                            image_patterns = [
                                r'reports/chart_\d{8}_\d{6}\.png',
                                r'reports/network_\d{8}_\d{6}\.png',
                                r'reports/table_relationships_\d{8}_\d{6}\.png'
                            ]
                            
                            for pattern in image_patterns:
                                matches = re.findall(pattern, output)
                                for match in matches:
                                    if os.path.exists(match):
                                        st.image(match, caption="Generated Visualization", use_column_width=True)
                        
                        # Show reasoning steps if available
                        if intermediate_steps:
                            with st.expander("🧠 Reasoning Steps", expanded=False):
                                for i, (action, observation) in enumerate(
                                    intermediate_steps, 1
                                ):
                                    st.markdown(f"**Step {i}:**")
                                    st.markdown(f"*Action:* {action.tool}")
                                    if hasattr(action, "tool_input"):
                                        st.code(
                                            str(action.tool_input),
                                            language=(
                                                "sql"
                                                if "sql" in action.tool.lower()
                                                else None
                                            ),
                                        )
                                    st.markdown(f"*Observation:* {observation}")
                                    if i < len(intermediate_steps):
                                        st.divider()

                        st.session_state.messages.append(
                            {"role": "assistant", "content": output}
                        )
                    else:
                        response = st.session_state.agent.invoke({"input": prompt})[
                            "output"
                        ]
                        st.markdown(response)
                        
                        # Check if any visualizations were created
                        if "chart_" in response or "network_" in response or "table_relationships_" in response:
                            # Extract image paths from response
                            import re
                            image_patterns = [
                                r'reports/chart_\d{8}_\d{6}\.png',
                                r'reports/network_\d{8}_\d{6}\.png',
                                r'reports/table_relationships_\d{8}_\d{6}\.png'
                            ]
                            
                            for pattern in image_patterns:
                                matches = re.findall(pattern, response)
                                for match in matches:
                                    if os.path.exists(match):
                                        st.image(match, caption="Generated Visualization", use_column_width=True)
                        
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )
