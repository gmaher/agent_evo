import re
import json
from typing import Dict, List, Any, Optional, Tuple

class ToolCallParser:
    """Parses tool calls from agent responses."""
    
    # Pattern to match tool calls in the format: [TOOL: tool_name(arg1=value1, arg2=value2)]
    TOOL_CALL_PATTERN = r'\[TOOL:\s*(\w+)\((.*?)\)\]'
    
    @classmethod
    def parse_response(cls, response: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse agent response to extract tool calls.
        Returns cleaned response and list of tool calls.
        """
        tool_calls = []
        
        # Find all tool calls in the response
        matches = re.finditer(cls.TOOL_CALL_PATTERN, response, re.DOTALL)
        
        for match in matches:
            tool_name = match.group(1)
            args_str = match.group(2).strip()
            
            # Parse arguments
            arguments = cls._parse_arguments(args_str)
            
            tool_calls.append({
                "tool": tool_name,
                "arguments": arguments,
                "raw": match.group(0)
            })
        
        # Remove tool calls from response
        cleaned_response = re.sub(cls.TOOL_CALL_PATTERN, '', response).strip()
        
        return cleaned_response, tool_calls
    
    @classmethod
    def _parse_arguments(cls, args_str: str) -> Dict[str, Any]:
        """Parse argument string into dictionary."""
        if not args_str:
            return {}
        
        arguments = {}
        
        # Try to parse as JSON-like format first
        try:
            # Convert Python-like syntax to JSON
            args_str = args_str.replace("'", '"')
            # Try to evaluate as a dict
            arguments = json.loads(f"{{{args_str}}}")
            return arguments
        except:
            pass
        
        # Fallback to simple parsing
        # Split by commas not inside quotes or brackets
        parts = cls._smart_split(args_str, ',')
        
        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Try to parse the value
                arguments[key] = cls._parse_value(value)
        
        return arguments
    
    @classmethod
    def _parse_value(cls, value_str: str) -> Any:
        """Parse a string value into appropriate Python type."""
        value_str = value_str.strip()
        
        # Remove quotes if present
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass
        
        # Try to parse as boolean
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # Try to parse as None
        if value_str.lower() == 'none':
            return None
        
        # Try to parse as list
        if value_str.startswith('[') and value_str.endswith(']'):
            try:
                return json.loads(value_str)
            except:
                pass
        
        # Return as string
        return value_str
    
    @classmethod
    def _smart_split(cls, text: str, delimiter: str) -> List[str]:
        """Split text by delimiter, respecting quotes and brackets."""
        parts = []
        current = []
        depth = 0
        in_quotes = False
        quote_char = None
        
        for char in text:
            if char in '"\'':
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
            elif not in_quotes:
                if char in '([{':
                    depth += 1
                elif char in ')]}':
                    depth -= 1
                elif char == delimiter and depth == 0:
                    parts.append(''.join(current))
                    current = []
                    continue
            
            current.append(char)
        
        if current:
            parts.append(''.join(current))
        
        return parts