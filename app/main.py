import os
import sys

import pandas as pd
import streamlit as st
from openai import OpenAI
from sqlalchemy import create_engine

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


@st.dialog("Database Configuration")
def database_config_dialog():
    """Modal dialog for database connection."""
    db_type = st.selectbox(
        "Database Type",
        ["SQLite", "PostgreSQL", "MySQL"],
        key="db_type_dialog",
    )

    db_url = None

    if db_type == "SQLite":
        db_file = st.file_uploader(
            "Upload SQLite Database",
            type=["db", "sqlite", "sqlite3"],
            key="sqlite_file",
        )
        if db_file:
            with open("temp_db.sqlite", "wb") as f:
                f.write(db_file.getbuffer())
            db_url = "sqlite:///temp_db.sqlite"
    else:
        host = st.text_input("Host", key="host")
        port_default = 5432 if db_type == "PostgreSQL" else 3306
        port = st.number_input("Port", value=port_default, step=1, key="port")
        database = st.text_input("DB Name", key="db_name")
        username = st.text_input("Username", key="db_user")
        password = st.text_input("Password", type="password", key="db_pass")

        if all([host, port, database, username, password]):
            if db_type == "PostgreSQL":
                db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            else:
                db_url = f"mysql://{username}:{password}@{host}:{port}/{database}"

    if st.button("Test Connection", key="test_conn"):
        if not db_url:
            st.error("Please provide all required fields")
        else:
            try:
                engine = create_engine(db_url)
                with engine.connect():
                    pass
                st.session_state.db_url = db_url
                st.session_state.db_connected = True
                if st.session_state.agent_type == "Enhanced SQL Agent":
                    st.session_state.agent = create_enhanced_sql_agent(
                        db_url,
                        model_name=st.session_state.selected_model,
                        enable_reporting=True,
                        enable_email=True,
                    )
                else:
                    st.session_state.agent = create_sql_agent(
                        db_url, model_name=st.session_state.selected_model
                    )
                st.success("Connected successfully!")
                st.rerun()
            except Exception as e:
                st.session_state.db_connected = False
                st.error(f"Connection failed: {e}")


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

if not st.session_state.db_connected:
    database_config_dialog()
    st.stop()

# Show current configuration
if st.session_state.agent:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success("🟢 Connected to database")
    with col2:
        st.info(f"🤖 Using {st.session_state.selected_model}")
else:
    st.info("👈 Configure your AI model and connect to a database to get started")

with st.sidebar:
    st.header("Configuration")

    # Model Selection
    st.subheader("🤖 AI Model")

    # Get available models
    available_models = get_available_models()

    # Model selection with helpful descriptions
    model_descriptions = {
        "gpt-4o": "GPT-4o - Latest and most capable (Recommended)",
        "gpt-4-turbo": "GPT-4 Turbo - Fast and powerful",
        "gpt-4": "GPT-4 - High quality responses",
        "gpt-3.5-turbo": "GPT-3.5 Turbo - Fast and cost-effective",
    }

    # Create display options with descriptions
    model_options = []
    for model in available_models:
        if model in model_descriptions:
            model_options.append(
                f"{model} - {model_descriptions[model].split(' - ')[1]}"
            )
        else:
            model_options.append(model)

    # Find the index of the current model
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
    )

    # Extract the actual model name and store in session state
    selected_model = selected_model_display.split(" - ")[0]
    st.session_state.selected_model = selected_model

    # Show model info
    if selected_model in model_descriptions:
        st.info(f"ℹ️ {model_descriptions[selected_model]}")

    # Add refresh button for models
    if st.button("🔄 Refresh Models"):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # Chain-of-Thought Settings
    st.subheader("🧠 Chain-of-Thought")

    show_reasoning = st.checkbox(
        "Show reasoning steps",
        value=st.session_state.show_reasoning,
        help="Display the AI's intermediate thinking steps and SQL queries",
    )
    st.session_state.show_reasoning = show_reasoning

    if show_reasoning:
        st.info("💡 Reasoning steps will be shown below responses")

    # Agent type selection
    st.subheader("🤖 Agent Type")
    agent_type = st.selectbox(
        "Select Agent Type",
        ["Enhanced SQL Agent", "Basic SQL Agent"],
        index=0,
        help="Enhanced agent has better SQL execution and additional tools",
    )

    if "agent_type" not in st.session_state:
        st.session_state.agent_type = "Enhanced SQL Agent"

    if agent_type != st.session_state.agent_type:
        st.session_state.agent_type = agent_type
        st.session_state.agent = None  # Reset agent when type changes

    # Visualization help
    if agent_type == "Enhanced SQL Agent":
        with st.expander("📊 Visualization Examples"):
            st.markdown(
                """
            **The Enhanced Agent can create visualizations! Try these examples:**
            
            • "Create a bar chart of customer segments"
            • "Show me a pie chart of order status distribution"
            • "Make a scatter plot of product prices vs ratings"
            • "Create a histogram of order amounts"
            • "Show table relationships as a network diagram"
            • "Visualize the correlation between product features"
            
            **Available chart types:** bar, line, scatter, pie, histogram, heatmap, network
            """
            )
            st.info(
                "💡 Visualizations will appear automatically below your query results!"
            )

    st.divider()

    # Email Configuration
    st.subheader("📧 Email Configuration")

    # Email settings input
    email_from = st.text_input(
        "From Email",
        value=settings.EMAIL_FROM if settings.EMAIL_FROM else "",
        help="Email address to send reports from",
    )
    smtp_server = st.text_input(
        "SMTP Server",
        value=settings.SMTP_SERVER,
        help="SMTP server hostname (e.g., smtp.gmail.com)",
    )
    smtp_port = st.number_input(
        "SMTP Port",
        value=settings.SMTP_PORT,
        min_value=1,
        max_value=65535,
        help="SMTP server port (usually 587 or 465)",
    )
    smtp_use_tls = st.checkbox(
        "Use TLS",
        value=settings.SMTP_USE_TLS,
        help="Use TLS encryption for secure email transmission",
    )
    smtp_username = st.text_input(
        "SMTP Username",
        value=settings.SMTP_USERNAME if settings.SMTP_USERNAME else "",
        help="Username for SMTP authentication",
    )
    smtp_password = st.text_input(
        "SMTP Password", type="password", help="Password for SMTP authentication"
    )

    # Update settings if values are provided
    if email_from:
        settings.EMAIL_FROM = email_from
    if smtp_username:
        settings.SMTP_USERNAME = smtp_username
    if smtp_password:
        settings.SMTP_PASSWORD = smtp_password
    settings.SMTP_SERVER = smtp_server
    settings.SMTP_PORT = smtp_port
    settings.SMTP_USE_TLS = smtp_use_tls

    # Test email configuration
    if st.button("📧 Test Email Configuration"):
        if not email_from:
            st.error("Please enter a 'From Email' address")
        else:
            try:
                import smtplib

                server = smtplib.SMTP(smtp_server, smtp_port)
                if smtp_use_tls:
                    server.starttls()

                # Only attempt login if username and password are provided
                if smtp_username and smtp_password:
                    server.login(smtp_username, smtp_password)
                    st.success(
                        "✅ Email configuration test successful with authentication!"
                    )
                else:
                    st.success(
                        "✅ Email server connection successful (no authentication required)!"
                    )
                    st.info(
                        "💡 Note: No username/password provided - using server without authentication"
                    )

                server.quit()
            except smtplib.SMTPAuthenticationError as e:
                st.error(f"❌ Authentication failed: {str(e)}")
                st.info("💡 Try using an app-specific password if using Gmail")
            except smtplib.SMTPException as e:
                st.error(f"❌ SMTP error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Email configuration test failed: {str(e)}")

    # Email report section
    if st.session_state.messages:
        st.subheader("📤 Send Report")
        recipient_email = st.text_input(
            "Recipient Email", help="Email address to send the report to"
        )

        if st.button("📧 Send Report via Email"):
            if not recipient_email:
                st.error("Please enter a recipient email address")
            elif not email_from:
                st.error("Please configure 'From Email' address first")
            else:
                with st.spinner("Generating and sending report..."):
                    try:
                        from tools import send_email
                        from reporting import create_report_from_messages

                        report_path = create_report_from_messages(
                            st.session_state.messages
                        )
                        send_email(report_path, recipient_email)
                        st.success(f"✅ Report sent successfully to {recipient_email}!")
                    except Exception as e:
                        st.error(f"❌ Failed to send report: {str(e)}")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about your data..."):
    if not st.session_state.agent:
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
                        if (
                            "chart_" in output
                            or "network_" in output
                            or "table_relationships_" in output
                        ):
                            # Extract image paths from response
                            import re

                            image_patterns = [
                                r"reports/chart_\d{8}_\d{6}\.png",
                                r"reports/network_\d{8}_\d{6}\.png",
                                r"reports/table_relationships_\d{8}_\d{6}\.png",
                            ]

                            for pattern in image_patterns:
                                matches = re.findall(pattern, output)
                                for match in matches:
                                    if os.path.exists(match):
                                        st.image(
                                            match,
                                            caption="Generated Visualization",
                                            use_column_width=True,
                                        )

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
                        if (
                            "chart_" in response
                            or "network_" in response
                            or "table_relationships_" in response
                        ):
                            # Extract image paths from response
                            import re

                            image_patterns = [
                                r"reports/chart_\d{8}_\d{6}\.png",
                                r"reports/network_\d{8}_\d{6}\.png",
                                r"reports/table_relationships_\d{8}_\d{6}\.png",
                            ]

                            for pattern in image_patterns:
                                matches = re.findall(pattern, response)
                                for match in matches:
                                    if os.path.exists(match):
                                        st.image(
                                            match,
                                            caption="Generated Visualization",
                                            use_column_width=True,
                                        )

                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )
