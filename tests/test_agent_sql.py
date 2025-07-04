import os
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents import create_sql_agent
from config import Settings
from reporting import dataframe_to_pdf, dataframe_to_plot
from tools import get_custom_tools, send_email


class TestSQLAgent:
    """Test suite for SQL Agent functionality."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary SQLite database for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create test tables
        cursor.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                age INTEGER
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                product TEXT,
                amount REAL,
                order_date DATE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        # Insert test data
        users_data = [
            (1, "Alice", "alice@test.com", 25),
            (2, "Bob", "bob@test.com", 30),
            (3, "Charlie", "charlie@test.com", 35),
        ]
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", users_data)

        orders_data = [
            (1, 1, "Laptop", 999.99, "2023-01-01"),
            (2, 2, "Phone", 599.99, "2023-01-02"),
            (3, 1, "Mouse", 25.99, "2023-01-03"),
            (4, 3, "Keyboard", 75.50, "2023-01-04"),
        ]
        cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders_data)

        conn.commit()
        conn.close()

        yield f"sqlite:///{db_path}"

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("config.settings") as mock:
            mock.OPENAI_API_KEY = "test-key"
            mock.EMAIL_FROM = "test@example.com"
            mock.SMTP_SERVER = "smtp.test.com"
            mock.SMTP_PORT = 587
            mock.SMTP_USE_TLS = True
            mock.SMTP_USERNAME = "test_user"
            mock.SMTP_PASSWORD = "test_pass"
            yield mock

    def test_config_validation(self):
        """Test configuration validation."""
        from config import validate_config

        # This will fail without proper environment variables
        # but we're testing the validation logic
        result = validate_config()
        assert isinstance(result, bool)

    def test_database_url_generation(self):
        """Test database URL generation for different database types."""
        from config import get_database_url

        # Test SQLite
        sqlite_url = get_database_url("sqlite", path="test.db")
        assert sqlite_url == "sqlite:///test.db"

        # Test PostgreSQL
        pg_url = get_database_url(
            "postgresql",
            host="localhost",
            database="testdb",
            username="user",
            password="pass",
        )
        assert "postgresql://user:pass@localhost:5432/testdb" == pg_url

        # Test invalid database type
        with pytest.raises(ValueError):
            get_database_url("invalid_db_type")

    @patch("agents.ChatOpenAI")
    @patch("agents.SQLDatabase")
    def test_agent_creation(self, mock_db, mock_llm, test_db, mock_settings):
        """Test SQL agent creation."""
        # Mock the database and LLM
        mock_db_instance = MagicMock()
        mock_db.from_uri.return_value = mock_db_instance

        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        # This test verifies the agent creation process
        # Without full OpenAI integration, we can't test the actual functionality
        # but we can test that the function doesn't crash
        try:
            agent = create_sql_agent(test_db)
            # If we get here without exception, the basic setup works
            assert True
        except Exception as e:
            # Expected to fail without real OpenAI API key
            assert "openai" in str(e).lower() or "api" in str(e).lower()

    def test_custom_tools_creation(self):
        """Test custom tools creation."""
        tools = get_custom_tools(enable_reporting=True, enable_email=True)
        assert len(tools) >= 1

        tools_no_email = get_custom_tools(enable_reporting=True, enable_email=False)
        tools_no_reporting = get_custom_tools(enable_reporting=False, enable_email=True)

        assert len(tools_no_email) != len(tools)
        assert len(tools_no_reporting) != len(tools)

    def test_send_email_validation(self, mock_settings):
        """Test email sending validation."""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            send_email("non_existent_file.pdf", "test@example.com")

    def test_reporting_functions(self):
        """Test reporting functions with sample data."""
        import pandas as pd

        # Create sample DataFrame
        df = pd.DataFrame({"category": ["A", "B", "C"], "value": [10, 20, 15]})

        # Test plot creation (returns base64 string)
        plot_b64 = dataframe_to_plot(df, plot_type="bar", title="Test Plot")
        assert isinstance(plot_b64, str)
        assert len(plot_b64) > 0

        # Test PDF creation
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name

        try:
            result_path = dataframe_to_pdf(df, filename=pdf_path, title="Test Report")
            assert os.path.exists(result_path)
            assert result_path == pdf_path
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

    def test_database_queries(self, test_db):
        """Test basic database queries against test database."""
        import sqlite3

        # Extract the file path from the SQLite URL
        db_path = test_db.replace("sqlite:///", "")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        assert user_count == 3

        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]
        assert order_count == 4

        # Test join query
        cursor.execute(
            """
            SELECT u.name, SUM(o.amount) as total
            FROM users u
            JOIN orders o ON u.id = o.user_id
            GROUP BY u.name
            ORDER BY total DESC
        """
        )
        results = cursor.fetchall()
        assert len(results) == 3
        assert results[0][1] > 0  # Alice should have highest total

        conn.close()


@pytest.mark.integration
class TestIntegration:
    """Integration tests that require external services."""

    def test_full_agent_workflow(self):
        """Test full agent workflow (requires OpenAI API key)."""
        # Skip if no API key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        # This would test the full workflow but requires real API access
        # Implementation would depend on testing strategy for LLM-dependent code
        pass


def test_smoke_test():
    """Basic smoke test to ensure all imports work."""
    try:
        from agents import create_sql_agent
        from config import settings, validate_config
        from reporting import dataframe_to_plot
        from tools import get_custom_tools

        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
