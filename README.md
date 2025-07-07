# 🗣️ Chat with SQL Agent

A powerful AI-driven natural language interface for database interaction using advanced LangChain agents and OpenAI. Transform complex SQL queries into simple conversations and get instant insights with automated visualizations.

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?style=for-the-badge&logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-green?style=for-the-badge&logo=chainlink&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-purple?style=for-the-badge&logo=openai&logoColor=white)

![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Multi-DB](https://img.shields.io/badge/Multi--DB-Support-lightblue?style=for-the-badge&logo=database&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7+-cyan?style=for-the-badge&logo=matplotlib&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.15+-darkblue?style=for-the-badge&logo=plotly&logoColor=white)

![Pandas](https://img.shields.io/badge/Pandas-2.0+-yellow?style=for-the-badge&logo=pandas&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.0+-pink?style=for-the-badge&logo=pydantic&logoColor=white)
![ReportLab](https://img.shields.io/badge/ReportLab-4.0+-brown?style=for-the-badge&logo=pdf&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen?style=for-the-badge&logo=docker&logoColor=white)

## ✨ Features

### 🤖 **Enhanced AI Agent**
- **Natural Language Processing**: Ask questions in plain English, get precise SQL results
- **Intelligent SQL Generation**: Advanced query optimization and error handling
- **Multi-step Reasoning**: Complex analytical questions resolved automatically
- **Context Awareness**: Understands database schema and relationships

### 📊 **Advanced Visualizations**
- **Automatic Chart Generation**: Bar charts, line plots, scatter plots, pie charts
- **Network Diagrams**: Database relationship mapping
- **Statistical Analysis**: Histograms, heatmaps, correlation matrices
- **Interactive Plots**: Powered by Matplotlib, Seaborn, and Plotly

### 🗄️ **Multi-Database Support**
- SQLite, PostgreSQL, MySQL, SQL Server
- Dynamic schema discovery and validation
- Connection pooling and optimization
- Secure parameterized queries

### 📧 **Reporting & Communication**
- **PDF Report Generation**: Professional formatted reports
- **Email Integration**: SMTP with secure authentication
- **Export Capabilities**: CSV, Excel, PDF formats
- **Automated Scheduling**: Configure recurring reports

### 🎨 **Modern Web Interface**
- **Streamlit UI**: Intuitive, responsive design
- **Real-time Chat**: Interactive conversation flow
- **Visualization Display**: Charts appear inline with responses
- **Configuration Management**: Easy setup and customization

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/frankmark94/chat-sql-agent.git
cd chat-sql-agent
pip install -r requirements.txt
```

### 2. Environment Setup

Create your environment configuration:

```bash
cp .env.example .env
```

Configure your `.env` file:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
EMAIL_FROM=your_email@example.com

# Optional SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Application Settings
OPENAI_MODEL=gpt-4
DEBUG=False
```

### 3. Launch Application

**Web Interface (Recommended)**
```bash
streamlit run app/main.py
```

**Python API**
```python
from src.agents_enhanced import create_enhanced_sql_agent

# Create agent
agent = create_enhanced_sql_agent("sqlite:///your_database.db")

# Ask questions
response = agent.invoke({"input": "What are our top 5 customers by revenue?"})
print(response["output"])
```

## 💡 Usage Examples

### Basic Analytics
```
"How many customers do we have?"
"What's our average order value?"
"Show me sales by month"
```

### Advanced Queries
```
"Find customers who haven't ordered in 6 months"
"What's the correlation between product price and ratings?"
"Calculate customer lifetime value by segment"
```

### Visualizations
```
"Create a bar chart of sales by region"
"Show me a pie chart of order status distribution"
"Generate a network diagram of table relationships"
"Make a scatter plot of price vs ratings"
```

### Reporting
```
"Create a monthly sales report and email it to manager@company.com"
"Generate a customer analysis report"
"Export top products data to Excel"
```

## 🏗️ Architecture

### Project Structure
```
chat-sql-agent/
├── app/
│   └── main.py                    # Streamlit web application
├── src/
│   ├── agents.py                  # Basic SQL agent
│   ├── agents_enhanced.py         # Enhanced agent with visualizations
│   ├── tools.py                   # Email and reporting tools
│   ├── visualization_tools.py     # Chart and graph generation
│   ├── reporting.py               # PDF and report generation
│   ├── config.py                  # Configuration management
│   ├── github_client.py           # GitHub API client
│   └── github_webhooks.py         # GitHub webhook handlers
├── config/
│   └── github-app.yml             # GitHub App configuration
├── data/
│   ├── sample_ecommerce.db        # Sample database
│   └── temp_db.sqlite             # Temporary database
├── docs/
│   ├── GITHUB_APP_SETUP.md        # GitHub App setup guide
│   └── LinkedInPost.md            # LinkedIn post content
├── examples/
│   └── notebooks/
│       └── demo.ipynb             # Example notebook
├── reports/                       # Generated reports and charts
├── scripts/
│   ├── create_sample_db.py        # Database creation script
│   ├── simple_agent.py            # Simple agent example
│   └── check_*.py                 # Utility scripts
├── tests/
│   └── unit/
│       ├── test_agent.py          # Agent tests
│       └── test_*.py              # Other unit tests
├── uploads/                       # Database file uploads
├── requirements.txt               # Python dependencies
└── .env.example                   # Environment template
```

### Technical Stack
- **AI/ML**: OpenAI GPT-4, LangChain Agents
- **Database**: SQLAlchemy with multi-DB support
- **Visualization**: Matplotlib, Seaborn, Plotly, NetworkX
- **Web Framework**: Streamlit
- **Email**: SMTP with TLS encryption
- **Reports**: ReportLab, FPDF
- **Security**: Environment-based secrets, parameterized queries

## ⚙️ Configuration

### Agent Types
- **Basic SQL Agent**: Standard query execution
- **Enhanced SQL Agent**: Advanced reasoning + visualizations (recommended)

### Visualization Options
| Chart Type | Use Case | Example Query |
|------------|----------|---------------|
| Bar Chart | Category comparisons | "Sales by product category" |
| Line Plot | Trends over time | "Monthly revenue trends" |
| Scatter Plot | Correlations | "Price vs rating correlation" |
| Pie Chart | Distributions | "Order status breakdown" |
| Histogram | Value distributions | "Customer age distribution" |
| Heatmap | Matrix correlations | "Feature correlation matrix" |
| Network | Relationships | "Table relationship diagram" |

### Email Configuration
```env
EMAIL_FROM=reports@yourcompany.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password
```

## 🛡️ Security & Best Practices

- **API Key Protection**: Never commit secrets to repository
- **SQL Injection Prevention**: Parameterized queries only
- **Secure Email**: TLS encryption for SMTP connections
- **Input Validation**: Schema-aware query validation
- **Access Control**: Environment-based configuration

## 🧪 Development

### Adding Custom Tools
```python
# src/custom_tools.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class CustomAnalyticsTool(BaseTool):
    name: str = "custom_analytics"
    description: str = "Perform custom analytics operations"
    
    def _run(self, query: str) -> str:
        # Your custom logic
        return "Analytics result"
```

### Database Extensions
```python
# src/config.py - Add new database type
def get_database_url(db_type: str, **kwargs) -> str:
    if db_type.lower() == "snowflake":
        return f"snowflake://{kwargs['user']}:{kwargs['password']}@{kwargs['account']}"
```

## 📊 Performance

- **Query Optimization**: Intelligent SQL generation and validation
- **Caching**: Database schema and query result caching
- **Connection Pooling**: Efficient database connection management
- **Async Processing**: Non-blocking report generation

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", "--server.address", "0.0.0.0"]
```

```bash
docker build -t chat-sql-agent .
docker run -p 8501:8501 --env-file .env chat-sql-agent
```

### Cloud Platforms
- **Streamlit Cloud**: Direct GitHub integration
- **AWS**: ECS, Lambda, or EC2 deployment
- **Google Cloud**: Cloud Run or App Engine
- **Azure**: Container Instances or App Service

## 📈 Roadmap

### Short-term
- [ ] Query caching and optimization
- [ ] Advanced statistical functions
- [ ] Multi-language support
- [ ] API endpoint creation

### Medium-term
- [ ] Integration with BI tools (Tableau, PowerBI)
- [ ] Advanced ML analytics (forecasting, clustering)
- [ ] Multi-tenant architecture
- [ ] Real-time data streaming

### Long-term
- [ ] Natural language data modeling
- [ ] Automated insight generation
- [ ] Voice interface integration
- [ ] Enterprise SSO integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Email**: For enterprise support and consulting

---

**Transform your data analysis workflow today!** 🚀

Made with ❤️ using OpenAI, LangChain, and modern Python technologies.