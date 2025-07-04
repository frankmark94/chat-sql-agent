import os
import sys

import pandas as pd
import streamlit as st
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../src")

from agents import create_sql_agent
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

    st.divider()

    # Database Configuration
    st.subheader("🗄️ Database Configuration")

    db_type = st.selectbox(
        "Database Type", ["SQLite", "PostgreSQL", "MySQL", "SQL Server"]
    )

    if db_type == "SQLite":
        db_file = st.file_uploader(
            "Upload SQLite Database", type=["db", "sqlite", "sqlite3"]
        )
        if db_file:
            with open("temp_db.sqlite", "wb") as f:
                f.write(db_file.getbuffer())
            db_url = "sqlite:///temp_db.sqlite"
        else:
            db_url = None
    else:
        host = st.text_input("Host", value="localhost")
        port = st.number_input("Port", value=5432 if db_type == "PostgreSQL" else 3306)
        database = st.text_input("Database Name")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if all([host, port, database, username, password]):
            if db_type == "PostgreSQL":
                db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            elif db_type == "MySQL":
                db_url = f"mysql://{username}:{password}@{host}:{port}/{database}"
            else:
                db_url = f"mssql://{username}:{password}@{host}:{port}/{database}"
        else:
            db_url = None

    if db_url and st.button("Connect to Database"):
        try:
            with st.spinner(f"Connecting with {st.session_state.selected_model}..."):
                st.session_state.agent = create_sql_agent(
                    db_url, model_name=st.session_state.selected_model
                )
            st.success(
                f"✅ Connected successfully using {st.session_state.selected_model}!"
            )
            st.info(f"🎯 Ready to answer questions about your database")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)}")
            st.error("Please check your API key and database connection details")

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
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

if st.session_state.messages:
    if st.button("📧 Email Report"):
        with st.spinner("Generating and sending report..."):
            try:
                from reporting import create_report_from_messages
                from tools import send_email

                report_path = create_report_from_messages(st.session_state.messages)
                recipient = st.text_input("Recipient Email")
                if recipient:
                    send_email(report_path, recipient)
                    st.success("Report sent successfully!")
            except Exception as e:
                st.error(f"Failed to send report: {str(e)}")
