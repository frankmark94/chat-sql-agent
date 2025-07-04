import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from config import settings


class SendEmailInput(BaseModel):
    report_path: str = Field(description="Path to the report file to send")
    to: str = Field(description="Recipient email address")
    subject: Optional[str] = Field(
        default="SQL Analysis Report", description="Email subject"
    )
    body: Optional[str] = Field(
        default="Please find the attached SQL analysis report.",
        description="Email body",
    )


class SendEmailTool(BaseTool):
    name: str = "send_email"
    description: str = "Send an email with an attached report file"
    args_schema: Type[BaseModel] = SendEmailInput

    def _run(
        self,
        report_path: str,
        to: str,
        subject: str = "SQL Analysis Report",
        body: str = "Please find the attached SQL analysis report.",
    ) -> str:
        try:
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
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        server.send_message(msg)
        server.quit()

        return f"Email sent successfully to {to}"

    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")


class QueryVisualizationInput(BaseModel):
    query_result: str = Field(description="SQL query result as a string or dataframe")
    chart_type: str = Field(
        description="Type of chart to create (bar, line, pie, scatter)"
    )
    title: Optional[str] = Field(
        default="Query Result Visualization", description="Chart title"
    )


class QueryVisualizationTool(BaseTool):
    name: str = "create_visualization"
    description: str = "Create a visualization from SQL query results"
    args_schema: Type[BaseModel] = QueryVisualizationInput

    def _run(
        self,
        query_result: str,
        chart_type: str,
        title: str = "Query Result Visualization",
    ) -> str:
        try:
            from reporting import create_chart_from_query_result

            chart_path = create_chart_from_query_result(query_result, chart_type, title)
            return f"Visualization created: {chart_path}"
        except Exception as e:
            return f"Failed to create visualization: {str(e)}"


def get_custom_tools(
    enable_reporting: bool = True, enable_email: bool = True
) -> List[BaseTool]:
    """
    Get list of custom tools for the SQL agent.

    Args:
        enable_reporting: Whether to include reporting tools
        enable_email: Whether to include email tools

    Returns:
        List of custom tools
    """
    tools = []

    if enable_email:
        tools.append(SendEmailTool())

    if enable_reporting:
        tools.append(QueryVisualizationTool())

    return tools
