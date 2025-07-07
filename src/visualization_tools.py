import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
from typing import List, Dict, Any, Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import io
import base64
import os
from datetime import datetime
import sqlite3

class DatabaseVisualizationInput(BaseModel):
    visualization_params: str = Field(description="Visualization parameters in format: 'query|chart_type|title|x_column|y_column' (title, x_column, y_column are optional)")

class DatabaseVisualizationTool(BaseTool):
    name: str = "create_database_visualization"
    description: str = "REQUIRED for chart/graph requests: Execute a SQL query and create a visualization (line chart, bar chart, etc.). Input format: 'query|chart_type|title|x_column|y_column'. Use this tool immediately after getting query results when user asks for charts, graphs, or plots."
    args_schema: Type[BaseModel] = DatabaseVisualizationInput
    db_path: str = ""
    
    def __init__(self, db_path: str = "temp_db.sqlite"):
        super().__init__()
        self.db_path = db_path
    
    def _run(self, visualization_params: str) -> str:
        try:
            # Parse visualization parameters
            parts = visualization_params.split("|")
            if len(parts) < 2:
                return "Error: Must provide at least query|chart_type"
            
            query = parts[0].strip()
            chart_type = parts[1].strip()
            title = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "Database Visualization"
            x_column = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
            y_column = parts[4].strip() if len(parts) > 4 and parts[4].strip() else None
            
            # Execute the query
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                return "No data returned from query"
            
            # Create visualization
            chart_path = self._create_chart(df, chart_type, title, x_column, y_column)
            return f"Visualization created successfully: {chart_path}"
            
        except Exception as e:
            return f"Error creating visualization: {str(e)}"
    
    def _create_chart(self, df: pd.DataFrame, chart_type: str, title: str, 
                     x_column: str = None, y_column: str = None) -> str:
        """Create a chart from the DataFrame"""
        plt.figure(figsize=(12, 8))
        
        # Auto-detect columns if not specified
        if x_column is None and len(df.columns) > 0:
            x_column = df.columns[0]
        if y_column is None and len(df.columns) > 1:
            # Find first numeric column
            numeric_cols = df.select_dtypes(include=['number']).columns
            y_column = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[1]
        
        try:
            if chart_type.lower() == "bar":
                if x_column and y_column:
                    plt.bar(df[x_column], df[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                else:
                    df.plot(kind='bar')
                    
            elif chart_type.lower() == "line":
                if x_column and y_column:
                    plt.plot(df[x_column], df[y_column], marker='o')
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                else:
                    df.plot(kind='line')
                    
            elif chart_type.lower() == "scatter":
                if x_column and y_column:
                    plt.scatter(df[x_column], df[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                else:
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) >= 2:
                        plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]])
                        plt.xlabel(numeric_cols[0])
                        plt.ylabel(numeric_cols[1])
                        
            elif chart_type.lower() == "pie":
                if x_column and y_column:
                    plt.pie(df[y_column], labels=df[x_column], autopct='%1.1f%%')
                else:
                    # Use first two columns
                    plt.pie(df.iloc[:, 1], labels=df.iloc[:, 0], autopct='%1.1f%%')
                    
            elif chart_type.lower() == "histogram":
                if y_column:
                    plt.hist(df[y_column], bins=20, alpha=0.7)
                    plt.xlabel(y_column)
                    plt.ylabel("Frequency")
                else:
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        plt.hist(df[numeric_cols[0]], bins=20, alpha=0.7)
                        plt.xlabel(numeric_cols[0])
                        plt.ylabel("Frequency")
                        
            elif chart_type.lower() == "heatmap":
                numeric_df = df.select_dtypes(include=['number'])
                if not numeric_df.empty:
                    correlation = numeric_df.corr()
                    sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
                    
            elif chart_type.lower() == "network":
                return self._create_network_graph(df, title)
                
            else:
                # Default to bar chart
                plt.bar(df.iloc[:, 0], df.iloc[:, 1] if len(df.columns) > 1 else range(len(df)))
                
            plt.title(title)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save chart
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_{timestamp}.png"
            filepath = os.path.join("reports", filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            plt.close()
            raise Exception(f"Error creating {chart_type} chart: {str(e)}")
    
    def _create_network_graph(self, df: pd.DataFrame, title: str) -> str:
        """Create a network graph from relationship data"""
        try:
            G = nx.Graph()
            
            # Assume first two columns are source and target
            if len(df.columns) >= 2:
                for _, row in df.iterrows():
                    source = str(row.iloc[0])
                    target = str(row.iloc[1])
                    weight = row.iloc[2] if len(row) > 2 else 1
                    G.add_edge(source, target, weight=weight)
            
            plt.figure(figsize=(15, 12))
            pos = nx.spring_layout(G, k=3, iterations=50)
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                 node_size=1000, alpha=0.7)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, alpha=0.5, edge_color='gray')
            
            # Draw labels
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
            
            plt.title(title)
            plt.axis('off')
            plt.tight_layout()
            
            # Save network graph
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_{timestamp}.png"
            filepath = os.path.join("reports", filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            plt.close()
            raise Exception(f"Error creating network graph: {str(e)}")

class TableRelationshipInput(BaseModel):
    request: str = Field(description="Request to create table relationship diagram")

class TableRelationshipTool(BaseTool):
    name: str = "create_table_relationship_diagram"
    description: str = "Create a visual diagram showing relationships between database tables"
    args_schema: Type[BaseModel] = TableRelationshipInput
    db_path: str = ""
    
    def __init__(self, db_path: str = "temp_db.sqlite"):
        super().__init__()
        self.db_path = db_path
    
    def _run(self, request: str) -> str:
        try:
            # Get table information
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Create network graph
            G = nx.Graph()
            
            # Add tables as nodes
            for table in tables:
                G.add_node(table)
            
            # Find relationships through foreign keys
            relationships = []
            for table in tables:
                cursor.execute(f"PRAGMA foreign_key_list({table});")
                fks = cursor.fetchall()
                for fk in fks:
                    referenced_table = fk[2]  # Referenced table
                    relationships.append((table, referenced_table))
                    G.add_edge(table, referenced_table)
            
            conn.close()
            
            # Create visualization
            plt.figure(figsize=(15, 12))
            pos = nx.spring_layout(G, k=3, iterations=50)
            
            # Draw nodes (tables)
            nx.draw_networkx_nodes(G, pos, node_color='lightcoral', 
                                 node_size=3000, alpha=0.8)
            
            # Draw edges (relationships)
            nx.draw_networkx_edges(G, pos, alpha=0.6, edge_color='blue', width=2)
            
            # Draw labels
            nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
            
            plt.title("Database Table Relationships", fontsize=16, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            
            # Save diagram
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"table_relationships_{timestamp}.png"
            filepath = os.path.join("reports", filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return f"Table relationship diagram created: {filepath}"
            
        except Exception as e:
            return f"Error creating table relationship diagram: {str(e)}"

def get_visualization_tools(db_path: str = "temp_db.sqlite") -> List[BaseTool]:
    """Get list of visualization tools"""
    return [
        DatabaseVisualizationTool(db_path=db_path),
        TableRelationshipTool(db_path=db_path)
    ]