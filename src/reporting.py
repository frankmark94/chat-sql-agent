import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import io
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def dataframe_to_plot(df: pd.DataFrame, plot_type: str = "bar", title: str = "Data Visualization", 
                     x_col: str = None, y_col: str = None) -> str:
    """
    Convert a pandas DataFrame to a plot and return the base64 encoded image.
    
    Args:
        df: DataFrame to plot
        plot_type: Type of plot (bar, line, scatter, pie, histogram)
        title: Plot title
        x_col: Column name for x-axis (if None, uses index)
        y_col: Column name for y-axis (if None, uses first numeric column)
    
    Returns:
        Base64 encoded plot image
    """
    plt.figure(figsize=(10, 6))
    
    if x_col is None:
        x_data = df.index
    else:
        x_data = df[x_col]
    
    if y_col is None:
        numeric_cols = df.select_dtypes(include=['number']).columns
        y_data = df[numeric_cols[0]] if len(numeric_cols) > 0 else df.iloc[:, 0]
    else:
        y_data = df[y_col]
    
    if plot_type == "bar":
        plt.bar(x_data, y_data)
    elif plot_type == "line":
        plt.plot(x_data, y_data, marker='o')
    elif plot_type == "scatter":
        plt.scatter(x_data, y_data)
    elif plot_type == "pie":
        plt.pie(y_data, labels=x_data, autopct='%1.1f%%')
    elif plot_type == "histogram":
        plt.hist(y_data, bins=20, alpha=0.7)
    else:
        plt.bar(x_data, y_data)
    
    plt.title(title)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return img_base64

def create_interactive_plot(df: pd.DataFrame, plot_type: str = "bar", title: str = "Interactive Plot",
                          x_col: str = None, y_col: str = None) -> str:
    """
    Create an interactive plot using Plotly.
    
    Args:
        df: DataFrame to plot
        plot_type: Type of plot (bar, line, scatter, pie)
        title: Plot title
        x_col: Column name for x-axis
        y_col: Column name for y-axis
    
    Returns:
        HTML string of the interactive plot
    """
    if x_col is None:
        x_col = df.columns[0]
    if y_col is None:
        numeric_cols = df.select_dtypes(include=['number']).columns
        y_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[1]
    
    if plot_type == "bar":
        fig = px.bar(df, x=x_col, y=y_col, title=title)
    elif plot_type == "line":
        fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)
    elif plot_type == "scatter":
        fig = px.scatter(df, x=x_col, y=y_col, title=title)
    elif plot_type == "pie":
        fig = px.pie(df, values=y_col, names=x_col, title=title)
    else:
        fig = px.bar(df, x=x_col, y=y_col, title=title)
    
    return fig.to_html(include_plotlyjs='cdn')

def dataframe_to_pdf(df: pd.DataFrame, filename: str = "report.pdf", title: str = "Data Report",
                    include_plots: bool = True) -> str:
    """
    Convert a DataFrame to a PDF report.
    
    Args:
        df: DataFrame to convert
        filename: Output filename
        title: Report title
        include_plots: Whether to include visualizations
    
    Returns:
        Path to the created PDF file
    """
    with PdfPages(filename) as pdf:
        # Title page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.text(0.5, 0.8, title, transform=ax.transAxes, fontsize=24, 
                ha='center', va='center', weight='bold')
        ax.text(0.5, 0.7, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                transform=ax.transAxes, fontsize=12, ha='center', va='center')
        ax.text(0.5, 0.6, f"Total Records: {len(df)}", 
                transform=ax.transAxes, fontsize=14, ha='center', va='center')
        ax.axis('off')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Data summary
        if not df.empty:
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.text(0.1, 0.9, "Data Summary", transform=ax.transAxes, fontsize=18, weight='bold')
            
            summary_text = []
            summary_text.append(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n")
            summary_text.append("Column Information:")
            for col in df.columns:
                dtype = str(df[col].dtype)
                null_count = df[col].isnull().sum()
                summary_text.append(f"  • {col}: {dtype} ({null_count} nulls)")
            
            ax.text(0.1, 0.8, '\n'.join(summary_text), transform=ax.transAxes, 
                   fontsize=10, va='top', fontfamily='monospace')
            ax.axis('off')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Include plots if requested
            if include_plots:
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                        fig, ax = plt.subplots(figsize=(8.5, 6))
                        df[col].hist(bins=20, ax=ax, alpha=0.7)
                        ax.set_title(f"Distribution of {col}")
                        ax.set_xlabel(col)
                        ax.set_ylabel("Frequency")
                        pdf.savefig(fig, bbox_inches='tight')
                        plt.close()
    
    return filename

def create_report_from_messages(messages: List[Dict[str, str]], filename: str = "chat_report.pdf") -> str:
    """
    Create a PDF report from chat messages.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        filename: Output filename
    
    Returns:
        Path to the created PDF file
    """
    with PdfPages(filename) as pdf:
        # Title page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.text(0.5, 0.8, "SQL Chat Analysis Report", transform=ax.transAxes, 
                fontsize=24, ha='center', va='center', weight='bold')
        ax.text(0.5, 0.7, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                transform=ax.transAxes, fontsize=12, ha='center', va='center')
        ax.text(0.5, 0.6, f"Total Messages: {len(messages)}", 
                transform=ax.transAxes, fontsize=14, ha='center', va='center')
        ax.axis('off')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Chat messages
        messages_per_page = 10
        for i in range(0, len(messages), messages_per_page):
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.text(0.1, 0.95, f"Chat Messages (Page {i//messages_per_page + 1})", 
                   transform=ax.transAxes, fontsize=16, weight='bold')
            
            y_pos = 0.9
            for msg in messages[i:i+messages_per_page]:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:500]  # Truncate long messages
                
                ax.text(0.1, y_pos, f"{role.upper()}:", transform=ax.transAxes, 
                       fontsize=12, weight='bold', color='blue' if role == 'user' else 'green')
                ax.text(0.1, y_pos-0.03, content, transform=ax.transAxes, 
                       fontsize=10, wrap=True, va='top')
                y_pos -= 0.08
                
                if y_pos < 0.1:
                    break
            
            ax.axis('off')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
    
    return filename

def create_chart_from_query_result(query_result: str, chart_type: str, title: str) -> str:
    """
    Create a chart from query result string.
    
    Args:
        query_result: Query result as string
        chart_type: Type of chart to create
        title: Chart title
    
    Returns:
        Path to the created chart file
    """
    try:
        # Try to parse the query result as a DataFrame
        lines = query_result.strip().split('\n')
        if len(lines) < 2:
            raise ValueError("Insufficient data for visualization")
        
        # Simple parsing - assumes tab or space separated values
        data = []
        headers = lines[0].split()
        for line in lines[1:]:
            row = line.split()
            if len(row) == len(headers):
                data.append(row)
        
        df = pd.DataFrame(data, columns=headers)
        
        # Convert numeric columns
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass
        
        filename = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        dataframe_to_plot(df, chart_type, title)
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filename
        
    except Exception as e:
        raise ValueError(f"Could not create chart from query result: {str(e)}")

def export_to_excel(df: pd.DataFrame, filename: str = "data_export.xlsx") -> str:
    """
    Export DataFrame to Excel file.
    
    Args:
        df: DataFrame to export
        filename: Output filename
    
    Returns:
        Path to the created Excel file
    """
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # Add a summary sheet
        summary_df = pd.DataFrame({
            'Metric': ['Total Rows', 'Total Columns', 'Memory Usage (MB)'],
            'Value': [len(df), len(df.columns), df.memory_usage(deep=True).sum() / 1024**2]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    return filename