import ast
import traceback
from typing import Any, Dict, Optional
from agent_evo.models.tool import Tool

class ToolExecutor:
    """Executes tool code safely and returns results."""
    
    def __init__(self):
        self.global_context = {}
        self.setup_safe_environment()
    
    def setup_safe_environment(self):
        """Setup a safe execution environment with common imports."""
        safe_imports = """
import os
import math
import json
import datetime
import re
import requests
from typing import *
"""
        exec(safe_imports, self.global_context)
    
    def execute_tool(self, tool: Tool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given arguments."""
        try:
            # Create a local context for this execution
            local_context = dict(arguments)
            
            # Execute the tool code
            exec(tool.code, self.global_context, local_context)
            
            # The tool code should define a function with the same name as the tool
            if tool.name not in local_context:
                raise ValueError(f"Tool code must define a function named '{tool.name}'")
            
            # Call the tool function
            tool_function = local_context[tool.name]
            
            # Extract only the required arguments
            func_args = {
                param.name: arguments.get(param.name, param.default)
                for param in tool.parameters
                if param.name in arguments or param.default is not None
            }
            
            result = tool_function(**func_args)
            
            return {
                "success": True,
                "result": result,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            }
    
    def validate_arguments(self, tool: Tool, arguments: Dict[str, Any]) -> Optional[str]:
        """Validate that all required arguments are provided."""
        missing = []
        for param in tool.parameters:
            if param.required and param.name not in arguments and param.default is None:
                missing.append(param.name)
        
        if missing:
            return f"Missing required arguments: {', '.join(missing)}"
        
        return None