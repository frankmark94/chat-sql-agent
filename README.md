# 🗣️ Chat with SQL Agent

A powerful natural language interface for interacting with databases using LangChain and OpenAI. Ask questions in plain English and get instant insights from your data!

## ✨ Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Multi-Database Support**: Works with SQLite, PostgreSQL, MySQL, SQL Server, and more
- **Web Interface**: Beautiful Streamlit UI for easy interaction
- **Report Generation**: Create PDF reports and visualizations from your queries
- **Email Integration**: Send reports directly via email
- **Jupyter Notebook Demo**: 5-minute quick start in Google Colab
- **Comprehensive Testing**: Full test suite with CI/CD pipeline

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone <repository-url>
cd chat-sql-agent
pip install -r requirements.txt
```

### 2. Set Up Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your API keys and configuration:

```env
OPENAI_API_KEY=your_openai_api_key_here
EMAIL_FROM=your_email@example.com
# ... other settings
```

### 3. Run the Application

**Option A: Streamlit Web App**
```bash
streamlit run app/main.py
```

**Option B: Jupyter Notebook Demo**
```bash
jupyter notebook notebooks/demo.ipynb
```

**Option C: Python Script**
```python
from src.agents import create_sql_agent

agent = create_sql_agent("sqlite:///your_database.db")
response = agent.run("How many customers do we have?")
print(response)
```

## 📁 Project Structure

```
chat-sql-agent/
├─ app/
│  └─ main.py                 # Streamlit web interface
├─ src/
│  ├─ agents.py              # SQL agent factory functions
│  ├─ tools.py               # Custom tools (email, visualization)
│  ├─ reporting.py           # PDF and chart generation
│  └─ config.py              # Configuration management
├─ notebooks/
│  └─ demo.ipynb             # Interactive demo notebook
├─ tests/
│  └─ test_agent_sql.py      # Comprehensive test suite
├─ .github/workflows/
│  └─ ci.yml                 # CI/CD pipeline
├─ requirements.txt          # Python dependencies
├─ .env.example             # Environment variables template
└─ README.md                # This file
```

## 🎯 Usage Examples

### Basic Queries
```python
# Simple counting
agent.run("How many users are in the database?")

# Aggregations
agent.run("What's the total revenue for this month?")

# Filtering
agent.run("Show me customers from California")
```

### Advanced Analytics
```python
# Time series analysis
agent.run("Show me monthly sales trends for the last year")

# Customer segmentation
agent.run("Which customers haven't made a purchase in 90 days?")

# Product performance
agent.run("What are the top 5 products by revenue?")
```

### Visualization and Reporting
```python
# Generate charts
agent.run("Create a bar chart of sales by region")

# Create reports
agent.run("Generate a monthly sales report and email it to manager@company.com")
```

## 🗄️ Supported Databases

- **SQLite**: `sqlite:///path/to/database.db`
- **PostgreSQL**: `postgresql://user:pass@host:port/database`
- **MySQL**: `mysql://user:pass@host:port/database`
- **SQL Server**: `mssql://user:pass@host:port/database`
- **Oracle**: `oracle://user:pass@host:port/database`
- **And more!**

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key | ✅ | - |
| `EMAIL_FROM` | Sender email address | ✅ | - |
| `SMTP_SERVER` | SMTP server hostname | ❌ | smtp.gmail.com |
| `SMTP_PORT` | SMTP server port | ❌ | 587 |
| `SMTP_USERNAME` | SMTP username | ❌ | - |
| `SMTP_PASSWORD` | SMTP password | ❌ | - |
| `DEBUG` | Enable debug mode | ❌ | False |

### Custom Configuration

```python
from src.config import Settings

# Override default settings
custom_settings = Settings(
    OPENAI_MODEL="gpt-4",
    MAX_ITERATIONS=15,
    VERBOSE_AGENT=True
)
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m "not integration"  # Skip integration tests
pytest tests/test_agent_sql.py -v  # Specific test file
```

## 🔧 Development

### Setting up Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black .
flake8 .
isort .
```

### Adding Custom Tools

```python
# src/tools.py
from langchain.tools import BaseTool

class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "Description of what this tool does"
    
    def _run(self, query: str) -> str:
        # Your custom logic here
        return "Custom tool result"

# Add to get_custom_tools() function
```

### Extending Database Support

```python
# src/config.py
def get_database_url(db_type: str, **kwargs) -> str:
    if db_type.lower() == "my_database":
        # Handle your custom database type
        return f"my_database://{kwargs['connection_string']}"
```

## 📊 Example Notebook

Check out `notebooks/demo.ipynb` for a complete 5-minute walkthrough that includes:

1. Setting up the environment
2. Creating a sample database
3. Running natural language queries
4. Generating visualizations
5. Creating reports

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/your-repo/chat-sql-agent/blob/main/notebooks/demo.ipynb)

## 🛡️ Security

- Never commit API keys or sensitive credentials
- Use environment variables for configuration
- The application includes security scanning with Bandit
- Database connections use parameterized queries to prevent SQL injection
- Email functionality uses secure SMTP connections

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**OpenAI API Key Error**
```bash
Error: OPENAI_API_KEY is required
```
Solution: Set your OpenAI API key in the `.env` file.

**Database Connection Error**
```bash
Error: Could not connect to database
```
Solution: Check your database URL format and credentials.

**Email Sending Error**
```bash
Error: Failed to send email
```
Solution: Verify SMTP settings and credentials in your `.env` file.

### Getting Help

- Check the [Issues](../../issues) page for known problems
- Read through the test files for usage examples
- Review the demo notebook for step-by-step guidance

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app/main.py"]
```

```bash
docker build -t chat-sql-agent .
docker run -p 8501:8501 --env-file .env chat-sql-agent
```

### Cloud Deployment

The application is ready for deployment on:
- **Streamlit Cloud**: Push to GitHub and connect your repository
- **Heroku**: Includes Procfile and requirements.txt
- **AWS/GCP/Azure**: Use the Docker container or serverless functions

## 📈 Roadmap

- [ ] Support for more database types
- [ ] Advanced visualization options
- [ ] Query caching and optimization
- [ ] Multi-language support
- [ ] REST API interface
- [ ] Integration with BI tools

---

Made with ❤️ using LangChain and OpenAI