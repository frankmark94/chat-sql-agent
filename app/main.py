import os
import sys
import tempfile

import pandas as pd
import streamlit as st
from openai import OpenAI
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../src")

from agents import create_sql_agent
from agents_enhanced import create_enhanced_sql_agent, run_agent_with_error_handling
from config import settings


# Model is now hardcoded to GPT-4o


st.set_page_config(page_title="Chat with SQL Agent", page_icon="🗣️", layout="wide")

st.title("🗣️ Chat with SQL Agent")
st.markdown("Ask questions about your database in natural language!")

if "messages" not in st.session_state:
    st.session_state.messages = []

# EMERGENCY: Clear messages if they contain too much data (base64 overflow)
if st.session_state.messages:
    total_chars = sum(len(msg["content"]) for msg in st.session_state.messages)
    if total_chars > 50000:  # If messages are too large, clear them
        st.session_state.messages = []
        st.warning("🚨 Conversation history was automatically cleared due to context overflow!")
        st.info("💡 You can now ask your question again.")

if "agent" not in st.session_state:
    st.session_state.agent = None

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gpt-4o"

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
        st.info("🤖 Using GPT-4o")
    with col3:
        col3a, col3b = st.columns(2)
        with col3a:
            if st.button("🔄 Reconnect"):
                st.session_state.db_connected = False
                st.session_state.agent = None
                st.rerun()
        with col3b:
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
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
    st.markdown("**Model:** 🤖 GPT-4o")
    
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
        
        # Model Selection - Fixed to GPT-4o
        st.markdown("**AI Model**")
        st.info("🤖 Using GPT-4o (Latest and most capable model)")
        st.session_state.selected_model = "gpt-4o"
        
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
        # Check for context overflow and manage conversation history
        total_tokens = sum(len(msg["content"]) for msg in st.session_state.messages) + len(prompt)
        
        # If context is getting too large, keep only the last few messages
        if total_tokens > 12000:  # Conservative limit to prevent overflow
            st.session_state.messages = st.session_state.messages[-4:]  # Keep last 4 messages
            st.info("🔄 Conversation history trimmed to prevent context overflow")
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get response with or without intermediate steps using error handling
                    if st.session_state.show_reasoning:
                        response = run_agent_with_error_handling(
                            st.session_state.agent, prompt
                        )
                        output = response["output"]
                        intermediate_steps = response.get("intermediate_steps", [])

                        # Display the output
                        st.markdown(output)
                        
                        # Check intermediate steps for visualization tool calls and parse JSON responses
                        import re
                        import json
                        images_displayed = False
                        
                        if intermediate_steps:
                            for i, (action, observation) in enumerate(intermediate_steps):
                                # Check if this step used a visualization tool
                                if hasattr(action, 'tool') and 'visualization' in action.tool.lower():
                                    try:
                                        # Try to parse JSON response from visualization tool
                                        chart_data = json.loads(str(observation))
                                        if chart_data.get("status") == "success" and "chart_path" in chart_data:
                                            chart_path = chart_data["chart_path"]
                                            chart_type = chart_data.get("chart_type", "visualization")
                                            message = chart_data.get("message", "Visualization created")
                                            
                                            if os.path.exists(chart_path):
                                                st.image(chart_path, caption=f"Generated {chart_type.title()} Chart", use_container_width=True)
                                                st.success(f"✅ {message}")
                                                images_displayed = True
                                    except (json.JSONDecodeError, KeyError):
                                        # Fallback to regex parsing if JSON fails
                                        image_patterns = [
                                            r'reports/chart_\d{8}_\d{6}\.png',
                                            r'reports/network_\d{8}_\d{6}\.png', 
                                            r'reports/table_relationships_\d{8}_\d{6}\.png'
                                        ]
                                        
                                        for pattern in image_patterns:
                                            matches = re.findall(pattern, str(observation))
                                            for match in matches:
                                                if os.path.exists(match):
                                                    st.image(match, caption="Generated Visualization", use_container_width=True)
                                                    images_displayed = True
                        
                        # Fallback: check final output and recent files if no images found in steps
                        if not images_displayed:
                            # Check final output for file paths
                            image_patterns = [
                                r'reports/chart_\d{8}_\d{6}\.png',
                                r'reports/network_\d{8}_\d{6}\.png', 
                                r'reports/table_relationships_\d{8}_\d{6}\.png'
                            ]
                            
                            for pattern in image_patterns:
                                matches = re.findall(pattern, output)
                                for match in matches:
                                    if os.path.exists(match):
                                        st.image(match, caption="Generated Visualization", use_container_width=True)
                                        images_displayed = True
                            
                            # Final fallback: automatically detect most recent chart if visualization keywords present
                            if not images_displayed and ("chart" in output.lower() or "visualization" in output.lower() or "created" in output.lower()):
                                import glob
                                chart_files = glob.glob("reports/chart_*.png")
                                network_files = glob.glob("reports/network_*.png") 
                                table_files = glob.glob("reports/table_relationships_*.png")
                                all_files = chart_files + network_files + table_files
                                
                                if all_files:
                                    latest_file = max(all_files, key=os.path.getctime)
                                    st.image(latest_file, caption="Generated Visualization", use_container_width=True)
                                    st.success(f"✅ Auto-detected and displayed: {os.path.basename(latest_file)}")
                        
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
                        response_data = run_agent_with_error_handling(
                            st.session_state.agent, prompt
                        )
                        response = response_data["output"]
                        
                        # Display the response
                        st.markdown(response)
                        
                        # Check for visualizations in the response
                        import re
                        import json
                        images_displayed = False
                        
                        # Check final output for file paths
                        image_patterns = [
                            r'reports/chart_\d{8}_\d{6}\.png',
                            r'reports/network_\d{8}_\d{6}\.png',
                            r'reports/table_relationships_\d{8}_\d{6}\.png'
                        ]
                        
                        for pattern in image_patterns:
                            matches = re.findall(pattern, response)
                            for match in matches:
                                if os.path.exists(match):
                                    st.image(match, caption="Generated Visualization", use_container_width=True)
                                    images_displayed = True
                        
                        # Fallback: automatically detect most recent chart if visualization keywords present
                        if not images_displayed and ("chart" in response.lower() or "visualization" in response.lower() or "created" in response.lower()):
                            import glob
                            chart_files = glob.glob("reports/chart_*.png")
                            network_files = glob.glob("reports/network_*.png") 
                            table_files = glob.glob("reports/table_relationships_*.png")
                            all_files = chart_files + network_files + table_files
                            
                            if all_files:
                                latest_file = max(all_files, key=os.path.getctime)
                                st.image(latest_file, caption="Generated Visualization", use_container_width=True)
                                st.success(f"✅ Auto-detected and displayed: {os.path.basename(latest_file)}")
                        
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )
