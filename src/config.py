import os
from typing import List, Optional, Union

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key for LLM access")
    OPENAI_MODEL: str = Field(
        default="gpt-3.5-turbo", description="OpenAI model to use"
    )

    # Database Configuration
    DEFAULT_DB_URL: Optional[str] = Field(
        default=None, description="Default database connection URL"
    )

    # Email Configuration
    EMAIL_FROM: str = Field(..., description="Sender email address")
    SMTP_SERVER: str = Field(
        default="smtp.gmail.com", description="SMTP server hostname"
    )
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    SMTP_USE_TLS: bool = Field(default=True, description="Use TLS for SMTP connection")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")

    # Application Configuration
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Streamlit Configuration
    STREAMLIT_SERVER_PORT: int = Field(
        default=8501, description="Streamlit server port"
    )
    STREAMLIT_SERVER_ADDRESS: str = Field(
        default="localhost", description="Streamlit server address"
    )

    # Security Configuration
    SECRET_KEY: Optional[str] = Field(
        default=None, description="Secret key for session management"
    )
    ALLOWED_HOSTS: Optional[List[str]] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"],
        description="Allowed host names",
    )

    # File Storage Configuration
    UPLOAD_DIR: str = Field(
        default="uploads", description="Directory for uploaded files"
    )
    REPORT_DIR: str = Field(
        default="reports", description="Directory for generated reports"
    )
    DATA_DIR: str = Field(
        default="data", description="Directory for database files"
    )
    MAX_FILE_SIZE: int = Field(
        default=100 * 1024 * 1024, description="Maximum file size in bytes (100MB)"
    )

    # Agent Configuration
    MAX_ITERATIONS: int = Field(
        default=10, description="Maximum iterations for agent execution"
    )
    AGENT_TIMEOUT: int = Field(default=300, description="Agent timeout in seconds")
    VERBOSE_AGENT: bool = Field(default=True, description="Enable verbose agent output")

    # Database Connection Pool Settings
    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(
        default=20, description="Database connection pool max overflow"
    )
    DB_POOL_TIMEOUT: int = Field(default=30, description="Database connection timeout")

    # GitHub App Configuration
    GITHUB_APP_ID: Optional[str] = Field(
        default=None, description="GitHub App ID for GitHub integration"
    )
    GITHUB_APP_PRIVATE_KEY: Optional[str] = Field(
        default=None, description="GitHub App private key (PEM format)"
    )
    GITHUB_APP_INSTALLATION_ID: Optional[str] = Field(
        default=None, description="GitHub App installation ID"
    )
    GITHUB_WEBHOOK_SECRET: Optional[str] = Field(
        default=None, description="GitHub webhook secret for signature validation"
    )

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if v is None or v == "":
            return ["localhost", "127.0.0.1"]
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # Ignore extra environment variables
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.REPORT_DIR, exist_ok=True)
        os.makedirs(self.DATA_DIR, exist_ok=True)


# Global settings instance
settings = Settings()


def get_database_url(db_type: str = "sqlite", **kwargs) -> str:
    """
    Generate database URL based on type and parameters.

    Args:
        db_type: Database type (sqlite, postgresql, mysql, etc.)
        **kwargs: Database connection parameters

    Returns:
        Database connection URL
    """
    if db_type.lower() == "sqlite":
        db_path = kwargs.get("path", "database.db")
        return f"sqlite:///{db_path}"

    elif db_type.lower() == "postgresql":
        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", 5432)
        database = kwargs.get("database", "postgres")
        username = kwargs.get("username", "postgres")
        password = kwargs.get("password", "")
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

    elif db_type.lower() == "mysql":
        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", 3306)
        database = kwargs.get("database", "mysql")
        username = kwargs.get("username", "root")
        password = kwargs.get("password", "")
        return f"mysql://{username}:{password}@{host}:{port}/{database}"

    elif db_type.lower() in ["mssql", "sqlserver"]:
        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", 1433)
        database = kwargs.get("database", "master")
        username = kwargs.get("username", "sa")
        password = kwargs.get("password", "")
        return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"

    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def validate_config() -> bool:
    """
    Validate the current configuration.

    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Check required fields
        if not settings.OPENAI_API_KEY:
            print("Error: OPENAI_API_KEY is required")
            return False

        if not settings.EMAIL_FROM:
            print("Error: EMAIL_FROM is required")
            return False

        # Check directories exist and are writable
        for directory in [settings.UPLOAD_DIR, settings.REPORT_DIR, settings.DATA_DIR]:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except OSError as e:
                    print(f"Error: Cannot create directory {directory}: {e}")
                    return False
            elif not os.access(directory, os.W_OK):
                print(f"Error: Directory {directory} is not writable")
                return False

        return True

    except Exception as e:
        print(f"Configuration validation error: {e}")
        return False
