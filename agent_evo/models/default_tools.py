"""Default tools available to all agents."""

from typing import Any, Dict, Callable, Optional
from dataclasses import dataclass
import subprocess
import json
import pandas as pd
from io import StringIO

READ_FILE = "read_file"
WRITE_FILE = "write_file"
HTTP_REQUEST = "http_request"
EXECUTE_SHELL = "execute_shell"
READ_CSV = "read_csv"
WRITE_CSV = "write_csv"
DATAFRAME_INFO = "dataframe_info"
DATAFRAME_QUERY = "dataframe_query"
DATAFRAME_TRANSFORM = "dataframe_transform"

@dataclass
class ToolDefinition:
    """Metadata for a predefined tool."""
    name: str
    description: str
    parameters: list  # List of dicts with name, type, description, required
    returns: Dict[str, str]
    function: Callable


def create_read_file_function(filesystem):
    """Create a read_file function bound to a filesystem."""
    def read_file(file_path: str, encoding: str = "utf-8") -> str:
        """Read the contents of a file."""
        return filesystem.read_file(file_path, encoding)
    return read_file


def create_write_file_function(filesystem):
    """Create a write_file function bound to a filesystem."""
    def write_file(file_path: str, content: str, mode: str = "w", encoding: str = "utf-8") -> str:
        """Write content to a file (creates file if it doesn't exist)."""
        return filesystem.write_file(file_path, content, mode, encoding)
    return write_file


def create_http_request_function():
    """Create an HTTP request function."""
    def http_request(
        url: str,
        method: str = "GET",
        headers: Optional[str] = None,
        body: Optional[str] = None,
        timeout: int = 30
    ) -> str:
        """
        Send an HTTP request and return the response.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: JSON string of headers (optional)
            body: Request body for POST/PUT (optional)
            timeout: Request timeout in seconds
        """
        try:
            import requests
            
            # Parse headers if provided
            headers_dict = {}
            if headers:
                try:
                    headers_dict = json.loads(headers)
                except json.JSONDecodeError:
                    return f"Error: Invalid JSON in headers: {headers}"
            
            # Make request
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers_dict,
                data=body,
                timeout=timeout
            )
            
            # Format response
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "url": response.url
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"Error making HTTP request: {type(e).__name__}: {str(e)}"
    
    return http_request


def create_execute_shell_function():
    """Create a shell command execution function."""
    def execute_shell(
        command: str,
        timeout: int = 30,
        capture_output: bool = True
    ) -> str:
        """
        Execute a shell command and return the output.
        
        WARNING: This can be dangerous. Only use with trusted commands.
        
        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            output = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            return json.dumps(output, indent=2)
            
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error executing command: {type(e).__name__}: {str(e)}"
    
    return execute_shell


def create_read_csv_function(filesystem):
    """Create a read_csv function bound to a filesystem."""
    def read_csv(
        file_path: str,
        max_rows: int = 100,
        show_info: bool = True
    ) -> str:
        """
        Read a CSV file and return summary information and preview.
        
        Args:
            file_path: Path to CSV file
            max_rows: Maximum rows to show in preview
            show_info: Whether to include DataFrame info
        """
        try:
            # Read file content
            content = filesystem.read_file(file_path)
            
            # Parse CSV
            df = pd.read_csv(StringIO(content))
            
            # Build output
            parts = []
            
            if show_info:
                parts.append("=== DataFrame Info ===")
                parts.append(f"Shape: {df.shape}")
                parts.append(f"Columns: {list(df.columns)}")
                parts.append(f"Dtypes:\n{df.dtypes.to_string()}")
                parts.append("")
            
            parts.append(f"=== Preview (first {min(max_rows, len(df))} rows) ===")
            parts.append(df.head(max_rows).to_string())
            
            return "\n".join(parts)
            
        except Exception as e:
            return f"Error reading CSV: {type(e).__name__}: {str(e)}"
    
    return read_csv


def create_write_csv_function(filesystem):
    """Create a write_csv function bound to a filesystem."""
    def write_csv(
        file_path: str,
        data: str,
        index: bool = False
    ) -> str:
        """
        Write data to a CSV file.
        
        Args:
            file_path: Path to output CSV file
            data: CSV data as string or JSON array of objects
            index: Whether to include index in output
        """
        try:
            # Try to parse as JSON first (array of objects)
            try:
                data_obj = json.loads(data)
                df = pd.DataFrame(data_obj)
                csv_content = df.to_csv(index=index)
            except (json.JSONDecodeError, ValueError):
                # Assume it's already CSV format
                csv_content = data
            
            # Write to filesystem
            result = filesystem.write_file(file_path, csv_content)
            return result
            
        except Exception as e:
            return f"Error writing CSV: {type(e).__name__}: {str(e)}"
    
    return write_csv


def create_dataframe_query_function(filesystem):
    """Create a dataframe query function."""
    def dataframe_query(
        file_path: str,
        query: str,
        max_rows: int = 100
    ) -> str:
        """
        Query a CSV file using pandas query syntax.
        
        Args:
            file_path: Path to CSV file
            query: Pandas query string (e.g., "age > 30 and city == 'NYC'")
            max_rows: Maximum rows to return
        """
        try:
            # Read file content
            content = filesystem.read_file(file_path)
            df = pd.read_csv(StringIO(content))
            
            # Execute query
            result_df = df.query(query)
            
            # Format output
            parts = [
                f"Query: {query}",
                f"Result shape: {result_df.shape}",
                "",
                f"=== Results (first {min(max_rows, len(result_df))} rows) ===",
                result_df.head(max_rows).to_string()
            ]
            
            return "\n".join(parts)
            
        except Exception as e:
            return f"Error querying DataFrame: {type(e).__name__}: {str(e)}"
    
    return dataframe_query


def create_dataframe_transform_function(filesystem):
    """Create a dataframe transformation function."""
    def dataframe_transform(
        input_path: str,
        output_path: str,
        operations: str
    ) -> str:
        """
        Apply transformations to a CSV file and save result.
        
        Args:
            input_path: Path to input CSV file
            output_path: Path to output CSV file
            operations: JSON string describing operations to apply
                       Example: [{"op": "filter", "query": "age > 30"},
                                {"op": "sort", "by": "name", "ascending": true},
                                {"op": "select", "columns": ["name", "age"]}]
        """
        try:
            # Read input file
            content = filesystem.read_file(input_path)
            df = pd.read_csv(StringIO(content))
            
            # Parse operations
            ops = json.loads(operations)
            
            # Apply operations
            for op in ops:
                op_type = op.get("op")
                
                if op_type == "filter":
                    df = df.query(op["query"])
                
                elif op_type == "sort":
                    df = df.sort_values(
                        by=op["by"],
                        ascending=op.get("ascending", True)
                    )
                
                elif op_type == "select":
                    df = df[op["columns"]]
                
                elif op_type == "drop":
                    df = df.drop(columns=op["columns"])
                
                elif op_type == "rename":
                    df = df.rename(columns=op["mapping"])
                
                elif op_type == "aggregate":
                    group_by = op.get("group_by")
                    agg_dict = op["aggregations"]
                    if group_by:
                        df = df.groupby(group_by).agg(agg_dict).reset_index()
                    else:
                        df = df.agg(agg_dict).to_frame().T
                
                else:
                    return f"Error: Unknown operation type: {op_type}"
            
            # Write result
            csv_content = df.to_csv(index=False)
            filesystem.write_file(output_path, csv_content)
            
            return f"Successfully transformed data and saved to {output_path}\nResult shape: {df.shape}"
            
        except Exception as e:
            return f"Error transforming DataFrame: {type(e).__name__}: {str(e)}"
    
    return dataframe_transform


def get_default_tools(filesystem) -> Dict[str, ToolDefinition]:
    """Get dictionary of default tools available to all agents."""
    return {
        "read_file": ToolDefinition(
            name="read_file",
            description="Read the contents of a file",
            parameters=[
                {
                    "name": "file_path",
                    "type": "str",
                    "description": "Path to the file to read",
                    "required": True
                },
                {
                    "name": "encoding",
                    "type": "str",
                    "description": "File encoding (default: utf-8)",
                    "required": False,
                    "default": "utf-8"
                }
            ],
            returns={
                "type": "str",
                "description": "The contents of the file"
            },
            function=create_read_file_function(filesystem)
        ),
        "write_file": ToolDefinition(
            name="write_file",
            description="Write content to a file (creates file if it doesn't exist)",
            parameters=[
                {
                    "name": "file_path",
                    "type": "str",
                    "description": "Path to the file to write",
                    "required": True
                },
                {
                    "name": "content",
                    "type": "str",
                    "description": "Content to write to the file",
                    "required": True
                },
                {
                    "name": "mode",
                    "type": "str",
                    "description": "Write mode: 'w' to overwrite, 'a' to append (default: 'w')",
                    "required": False,
                    "default": "w"
                },
                {
                    "name": "encoding",
                    "type": "str",
                    "description": "File encoding (default: utf-8)",
                    "required": False,
                    "default": "utf-8"
                }
            ],
            returns={
                "type": "str",
                "description": "Success message with bytes written"
            },
            function=create_write_file_function(filesystem)
        ),
        "http_request": ToolDefinition(
            name="http_request",
            description="Send an HTTP request and get the response",
            parameters=[
                {
                    "name": "url",
                    "type": "str",
                    "description": "The URL to request",
                    "required": True
                },
                {
                    "name": "method",
                    "type": "str",
                    "description": "HTTP method (GET, POST, PUT, DELETE, etc.)",
                    "required": False,
                    "default": "GET"
                },
                {
                    "name": "headers",
                    "type": "str",
                    "description": "JSON string of headers (optional)",
                    "required": False
                },
                {
                    "name": "body",
                    "type": "str",
                    "description": "Request body for POST/PUT (optional)",
                    "required": False
                },
                {
                    "name": "timeout",
                    "type": "int",
                    "description": "Request timeout in seconds (default: 30)",
                    "required": False,
                    "default": 30
                }
            ],
            returns={
                "type": "str",
                "description": "JSON string with status_code, headers, body, and url"
            },
            function=create_http_request_function()
        ),
        "execute_shell": ToolDefinition(
            name="execute_shell",
            description="Execute a shell command (USE WITH CAUTION - only for trusted commands)",
            parameters=[
                {
                    "name": "command",
                    "type": "str",
                    "description": "Shell command to execute",
                    "required": True
                },
                {
                    "name": "timeout",
                    "type": "int",
                    "description": "Command timeout in seconds (default: 30)",
                    "required": False,
                    "default": 30
                },
                {
                    "name": "capture_output",
                    "type": "bool",
                    "description": "Whether to capture stdout/stderr (default: true)",
                    "required": False,
                    "default": True
                }
            ],
            returns={
                "type": "str",
                "description": "JSON string with returncode, stdout, and stderr"
            },
            function=create_execute_shell_function()
        ),
        "read_csv": ToolDefinition(
            name="read_csv",
            description="Read a CSV file and return summary information and preview",
            parameters=[
                {
                    "name": "file_path",
                    "type": "str",
                    "description": "Path to CSV file",
                    "required": True
                },
                {
                    "name": "max_rows",
                    "type": "int",
                    "description": "Maximum rows to show in preview (default: 100)",
                    "required": False,
                    "default": 100
                },
                {
                    "name": "show_info",
                    "type": "bool",
                    "description": "Whether to include DataFrame info (default: true)",
                    "required": False,
                    "default": True
                }
            ],
            returns={
                "type": "str",
                "description": "DataFrame info and preview"
            },
            function=create_read_csv_function(filesystem)
        ),
        "write_csv": ToolDefinition(
            name="write_csv",
            description="Write data to a CSV file",
            parameters=[
                {
                    "name": "file_path",
                    "type": "str",
                    "description": "Path to output CSV file",
                    "required": True
                },
                {
                    "name": "data",
                    "type": "str",
                    "description": "CSV data as string or JSON array of objects",
                    "required": True
                },
                {
                    "name": "index",
                    "type": "bool",
                    "description": "Whether to include index in output (default: false)",
                    "required": False,
                    "default": False
                }
            ],
            returns={
                "type": "str",
                "description": "Success message"
            },
            function=create_write_csv_function(filesystem)
        ),
        "dataframe_query": ToolDefinition(
            name="dataframe_query",
            description="Query a CSV file using pandas query syntax",
            parameters=[
                {
                    "name": "file_path",
                    "type": "str",
                    "description": "Path to CSV file",
                    "required": True
                },
                {
                    "name": "query",
                    "type": "str",
                    "description": "Pandas query string (e.g., \"age > 30 and city == 'NYC'\")",
                    "required": True
                },
                {
                    "name": "max_rows",
                    "type": "int",
                    "description": "Maximum rows to return (default: 100)",
                    "required": False,
                    "default": 100
                }
            ],
            returns={
                "type": "str",
                "description": "Query results"
            },
            function=create_dataframe_query_function(filesystem)
        ),
        "dataframe_transform": ToolDefinition(
            name="dataframe_transform",
            description="Apply transformations to a CSV file and save result",
            parameters=[
                {
                    "name": "input_path",
                    "type": "str",
                    "description": "Path to input CSV file",
                    "required": True
                },
                {
                    "name": "output_path",
                    "type": "str",
                    "description": "Path to output CSV file",
                    "required": True
                },
                {
                    "name": "operations",
                    "type": "str",
                    "description": "JSON string of operations: filter, sort, select, drop, rename, aggregate",
                    "required": True
                }
            ],
            returns={
                "type": "str",
                "description": "Success message with result shape"
            },
            function=create_dataframe_transform_function(filesystem)
        )
    }


def get_tool_by_name(tools_dict: Dict[str, ToolDefinition], tool_name: str) -> Optional[ToolDefinition]:
    """Get a tool by its function name from the tools dictionary."""
    return tools_dict.get(tool_name)