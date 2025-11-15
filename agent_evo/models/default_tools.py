"""Default tools available to all agents."""

from typing import Any, Dict, Callable, Optional
from dataclasses import dataclass
import os

READ_FILE = "read_file"
WRITE_FILE = "write_file"

@dataclass
class ToolDefinition:
    """Metadata for a predefined tool."""
    name: str
    description: str
    parameters: list  # List of dicts with name, type, description, required
    returns: Dict[str, str]
    function: Callable


def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """Read the contents of a file."""
    # Expand user home directory if present
    file_path = os.path.expanduser(file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check if it's a file (not a directory)
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Read the file
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        return f"Successfully read {len(content)} characters from {file_path}\n\nContent:\n{content}"
    except Exception as e:
        raise RuntimeError(f"Failed to read file: {str(e)}")


def write_file(file_path: str, content: str, mode: str = "w", encoding: str = "utf-8") -> str:
    """Write content to a file (creates file if it doesn't exist)."""
    # Expand user home directory if present
    file_path = os.path.expanduser(file_path)
    
    # Validate mode
    if mode not in ['w', 'a']:
        raise ValueError(f"Invalid mode: {mode}. Use 'w' for write or 'a' for append")
    
    # Create directory if it doesn't exist
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    # Write the file
    try:
        with open(file_path, mode, encoding=encoding) as f:
            bytes_written = f.write(content)
        
        action = "overwrote" if mode == 'w' else "appended to"
        return f"Successfully {action} {file_path}. Wrote {bytes_written} characters."
    except Exception as e:
        raise RuntimeError(f"Failed to write file: {str(e)}")


# Define all available tools
PREDEFINED_TOOLS = {
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
        function=read_file
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
        function=write_file
    )
}


def get_default_tools() -> Dict[str, ToolDefinition]:
    """Get dictionary of default tools available to all agents."""
    return PREDEFINED_TOOLS


def get_tool_by_name(tool_name: str) -> Optional[ToolDefinition]:
    """Get a tool by its function name."""
    for tool in PREDEFINED_TOOLS.values():
        if tool.name == tool_name:
            return tool
    return None