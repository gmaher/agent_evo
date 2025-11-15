import traceback
from typing import Any, Dict, Optional
from agent_evo.models.default_tools import ToolDefinition


class ToolExecutor:
    """Executes predefined tools and returns results."""
    
    def execute_tool(self, tool: ToolDefinition, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a predefined tool with given arguments."""
        try:
            # Extract function arguments, using defaults for optional params
            func_args = {}
            for param in tool.parameters:
                param_name = param["name"]
                if param_name in arguments:
                    func_args[param_name] = arguments[param_name]
                elif not param["required"] and "default" in param:
                    func_args[param_name] = param["default"]
            
            # Call the tool function
            result = tool.function(**func_args)
            
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
    
    def validate_arguments(self, tool: ToolDefinition, arguments: Dict[str, Any]) -> Optional[str]:
        """Validate that all required arguments are provided."""
        missing = []
        for param in tool.parameters:
            if param["required"] and param["name"] not in arguments and "default" not in param:
                missing.append(param["name"])
        
        if missing:
            return f"Missing required arguments: {', '.join(missing)}"
        
        return None