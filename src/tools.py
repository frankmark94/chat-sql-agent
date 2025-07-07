import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from config import settings
from visualization_tools import get_visualization_tools


class SendEmailInput(BaseModel):
    email_details: str = Field(description="Email details in format: 'report_path|recipient@email.com|subject|body' (subject and body are optional)")

class SendEmailTool(BaseTool):
    name: str = "send_email"
    description: str = "Send an email with an attached report file"
    args_schema: Type[BaseModel] = SendEmailInput

    def _run(self, email_details: str) -> str:
        try:
            # Parse email details
            parts = email_details.split("|")
            if len(parts) < 2:
                return "Error: Email details must include at least report_path|recipient@email.com"
            
            report_path = parts[0].strip()
            to = parts[1].strip()
            subject = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "SQL Analysis Report"
            body = parts[3].strip() if len(parts) > 3 and parts[3].strip() else "Please find the attached SQL analysis report."
            
            return send_email(report_path, to, subject, body)
        except Exception as e:
            return f"Failed to send email: {str(e)}"


def send_email(
    report_path: str,
    to: str,
    subject: str = "SQL Analysis Report",
    body: str = "Please find the attached SQL analysis report.",
) -> str:
    """
    Send an email with an attached report file.

    Args:
        report_path: Path to the report file to attach
        to: Recipient email address
        subject: Email subject line
        body: Email body text

    Returns:
        Success or error message
    """
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Report file not found: {report_path}")

    msg = MIMEMultipart()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with open(report_path, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(report_path)
        )
        msg.attach(attach)

    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        if settings.SMTP_USE_TLS:
            server.starttls()
        
        # Only authenticate if credentials are provided
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        server.send_message(msg)
        server.quit()

        return f"Email sent successfully to {to}"
        
    except smtplib.SMTPAuthenticationError as e:
        raise Exception(f"SMTP authentication failed: {str(e)}. Try using an app-specific password if using Gmail.")
    except smtplib.SMTPException as e:
        raise Exception(f"SMTP error: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")


class QueryVisualizationInput(BaseModel):
    visualization_request: str = Field(description="Visualization request in format: 'query_result|chart_type|title|x_field|y_field' (title, x_field, y_field are optional)")

class QueryVisualizationTool(BaseTool):
    name: str = "create_visualization"
    description: str = "Create a visualization from SQL query results. Input format: 'query_result|chart_type|title|x_field|y_field' where only query_result and chart_type are required. Example: 'data|bar|Chart Title|month|sales'"
    args_schema: Type[BaseModel] = QueryVisualizationInput

    def _run(self, visualization_request: str) -> str:
        try:
            # Parse visualization request
            parts = visualization_request.split("|")
            if len(parts) < 2:
                return "Error: Visualization request must include at least query_result|chart_type"
            
            query_result = parts[0].strip()
            chart_type = parts[1].strip()
            title = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "Query Result Visualization"
            x_field = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
            y_field = parts[4].strip() if len(parts) > 4 and parts[4].strip() else None
            
            from reporting import create_chart_from_query_result

            chart_path = create_chart_from_query_result(query_result, chart_type, title, x_field, y_field)
            return f"Visualization created: {chart_path}"
        except Exception as e:
            return f"Failed to create visualization: {str(e)}"

def get_custom_tools(enable_reporting: bool = True, enable_email: bool = True, db_path: str = "temp_db.sqlite") -> List[BaseTool]:
    """
    Get list of custom tools for the SQL agent.

    Args:
        enable_reporting: Whether to include reporting tools
        enable_email: Whether to include email tools
        db_path: Path to the database file for visualization tools
    
    Returns:
        List of custom tools
    """
    tools = []

    if enable_email:
        tools.append(SendEmailTool())

    if enable_reporting:
        # Only add the database visualization tools (not the duplicate QueryVisualizationTool)
        tools.extend(get_visualization_tools(db_path))
    
    return tools
