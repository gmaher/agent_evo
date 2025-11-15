"""Default tools available to all agents."""

from typing import Any, Dict, Callable, Optional
from dataclasses import dataclass

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
        )
    }


def get_tool_by_name(tools_dict: Dict[str, ToolDefinition], tool_name: str) -> Optional[ToolDefinition]:
    """Get a tool by its function name from the tools dictionary."""
    return tools_dict.get(tool_name)