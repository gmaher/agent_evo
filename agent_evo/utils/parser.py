import re
from typing import Dict, List, Any, Tuple

class ToolCallParser:
    """Parses tool calls from agent responses using structured format."""
    
    @classmethod
    def parse_response(cls, response: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse agent response to extract tool calls.
        Returns cleaned response and list of tool calls.
        
        Expected format:
        BEGIN_TOOL_CALL <tool_name>
        BEGIN_ARG <arg_name>
        <arg_value>
        END_ARG
        BEGIN_ARG <arg_name>
        <arg_value>
        END_ARG
        END_TOOL_CALL
        """
        tool_calls = []
        lines = response.split('\n')
        i = 0
        tool_call_positions = []
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for BEGIN_TOOL_CALL
            if line.startswith('BEGIN_TOOL_CALL'):
                start_line = i
                tool_name = line[len('BEGIN_TOOL_CALL'):].strip()
                
                if not tool_name:
                    i += 1
                    continue
                
                arguments = {}
                i += 1
                
                # Parse arguments until we hit END_TOOL_CALL
                current_arg_name = None
                current_arg_lines = []
                
                while i < len(lines):
                    line = lines[i]
                    stripped = line.strip()
                    
                    if stripped == 'END_TOOL_CALL':
                        # Save the last argument if any
                        if current_arg_name and current_arg_lines:
                            arguments[current_arg_name] = cls._process_arg_value(current_arg_lines)
                        
                        # Record the position for removal
                        tool_call_positions.append((start_line, i))
                        
                        tool_calls.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "raw": '\n'.join(lines[start_line:i+1])
                        })
                        i += 1
                        break
                    elif stripped == 'END_ARG':
                        # Save the current argument
                        if current_arg_name is not None:
                            arguments[current_arg_name] = cls._process_arg_value(current_arg_lines)
                            current_arg_name = None
                            current_arg_lines = []
                    elif stripped.startswith('BEGIN_ARG'):
                        # Start new argument
                        current_arg_name = stripped[len('BEGIN_ARG'):].strip()
                        current_arg_lines = []
                    else:
                        # This is part of the current argument value
                        if current_arg_name is not None:
                            current_arg_lines.append(line)
                    
                    i += 1
                
                # If we didn't find END_TOOL_CALL, skip this tool call
                continue
            
            i += 1
        
        # Remove tool calls from response
        cleaned_lines = lines.copy()
        for start, end in reversed(tool_call_positions):
            del cleaned_lines[start:end+1]
        
        cleaned_response = '\n'.join(cleaned_lines).strip()
        
        return cleaned_response, tool_calls
    
    @classmethod
    def _process_arg_value(cls, lines: List[str]) -> Any:
        """
        Process argument value lines into final value.
        Handles triple quotes and multi-line content.
        """
        if not lines:
            return ""
        
        # Join all lines
        value = '\n'.join(lines)
        
        # Check if it starts and ends with triple quotes (on separate lines)
        lines_stripped = [line.strip() for line in lines]
        
        # Check for triple quotes at start and end
        if len(lines) >= 2:
            first_line = lines_stripped[0]
            last_line = lines_stripped[-1]
            
            if first_line in ('"""', "'''") and last_line in ('"""', "'''"):
                # Remove first and last lines
                if len(lines) > 2:
                    value = '\n'.join(lines[1:-1])
                else:
                    value = ""
        
        # Try to parse as a simple type if it's a single line
        if '\n' not in value:
            stripped = value.strip()
            
            # Try to parse as number
            try:
                if '.' in stripped:
                    return float(stripped)
                return int(stripped)
            except ValueError:
                pass
            
            # Try to parse as boolean
            if stripped.lower() == 'true':
                return True
            if stripped.lower() == 'false':
                return False
            
            # Try to parse as None
            if stripped.lower() in ('none', 'null'):
                return None
        
        # Return as string (potentially multi-line)
        return value