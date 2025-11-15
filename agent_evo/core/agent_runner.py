from typing import Dict, List, Any, Optional, Tuple
from agent_evo.models.agent import Agent
from agent_evo.models.default_tools import get_default_tools
from agent_evo.models.tool import Tool
from agent_evo.core.tool_executor import ToolExecutor
from agent_evo.prompts.agent import AGENT_SYSTEM_PROMPT, DELEGATION_INSTRUCTIONS
from agent_evo.utils.parser import ToolCallParser
from agent_evo.llm.client import LLMClient
import os


class AgentRunner:
    """Runs an agent with tool execution capabilities."""
    
    def __init__(self, llm_client: LLMClient, output_dir: str = ".", ignored_files:Optional[set]=None):
        self.llm_client = llm_client
        self.tool_executor = ToolExecutor()
        self.parser = ToolCallParser()
        self.default_tools = get_default_tools()  # Load default tools
        self.output_dir = output_dir
        self.ignored_files = ignored_files

    def _read_directory_structure(self, path: str = None, prefix: str = "") -> str:
        """Recursively read directory structure, ignoring specific files."""
        if path is None:
            path = self.output_dir
        
        if self.ignored_files is None:
            self.ignored_files = {"agents.json", "tools.json", "team.json"}
        
        structure_lines = []
        
        try:
            # Get all items in directory
            items = sorted(os.listdir(path))
            
            # Filter out ignored files
            items = [item for item in items if item not in self.ignored_files]
            
            for i, item in enumerate(items):
                item_path = os.path.join(path, item)
                is_last = i == len(items) - 1
                
                # Determine the prefix characters
                current_prefix = "└── " if is_last else "├── "
                next_prefix = "    " if is_last else "│   "
                
                if os.path.isdir(item_path):
                    structure_lines.append(f"{prefix}{current_prefix}{item}/")
                    # Recursively add subdirectory contents
                    sub_structure = self._read_directory_structure(
                        item_path, 
                        prefix + next_prefix,
                    )
                    if sub_structure:
                        structure_lines.append(sub_structure)
                else:
                    structure_lines.append(f"{prefix}{current_prefix}{item}")
            
            return "\n".join(structure_lines)
        
        except Exception as e:
            return f"Error reading directory: {str(e)}"
    
    def _build_directory_info(self) -> str:
        """Build the directory information section."""
        structure = self._read_directory_structure()
        
        return f"""=== Current Directory Structure ===
Working Directory: .

{structure}

================================"""
    
    def run_agent(self, 
                  agent: Agent, 
                  task: str, 
                  tools: Dict[str, Tool],
                  available_agents: Optional[List[str]] = None,
                  chat_history: Optional[List[Dict[str, Any]]] = None,
                  max_iterations: int = 10) -> Dict[str, Any]:
        """
        Run an agent on a task with available tools.
        Returns the final response, execution history, and delegation info.
        """
        # Start with default tools
        all_tools = dict(self.default_tools)
        
        # Add custom tools (these can override defaults if needed)
        all_tools.update(tools)
        
        # Filter tools available to this agent
        # Note: default tools are always available regardless of agent.tool_ids
        available_tools = dict(self.default_tools)  # Always include defaults
        
        # Add agent-specific tools
        for tool_id, tool in all_tools.items():
            if tool_id in agent.tool_ids and tool_id not in self.default_tools:
                available_tools[tool_id] = tool
        
        
        # Build tools description
        tools_description = self._build_tools_description(available_tools)
        
        # Build delegation instructions if agent can delegate
        delegation_instructions = ""
        if available_agents:
            agents_list = "\n".join([f"- {agent_id}" for agent_id in available_agents])
            delegation_instructions = DELEGATION_INSTRUCTIONS.format(
                available_agents=agents_list
            )
        
        # Build system prompt
        system_prompt = AGENT_SYSTEM_PROMPT.format(
            tools_description=tools_description,
            delegation_instructions=delegation_instructions,
            custom_prompt=agent.system_prompt
        )
        
        # Initialize conversation
        messages = [{"role": "system", "content": system_prompt}]
        
        # Build the user message with chat history and directory structure
        user_message = self._build_task_message(task, chat_history)
        messages.append({"role": "user", "content": user_message})

        print(f"\n{'='*60}")
        print(f"AGENT: {agent.name}")
        print(f"{'='*60}")
        print(f"SYSTEM:\n{system_prompt}\n")
        print(f"USER:\n{user_message}")

        history = []
        iteration = 0
        delegation = None
        is_finished = False
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get response from LLM
            response = self.llm_client.generate(
                messages=messages,
                temperature=agent.temperature
            )
            print(f"\nASSISTANT ({agent.name}):\n{response}")
            
            # Parse response for tool calls first
            cleaned_response, tool_calls = self.parser.parse_response(response)
            
            # Execute tool calls if any
            tool_results = []
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call["tool"]
                    arguments = tool_call["arguments"]
                    
                    # Find the tool
                    matching_tools = [
                        tool for tool in available_tools.values() 
                        if tool.name == tool_name
                    ]
                    
                    if not matching_tools:
                        tool_results.append({
                            "tool": tool_name,
                            "error": f"Tool '{tool_name}' not found"
                        })
                        continue
                    
                    tool = matching_tools[0]
                    
                    # Make file paths relative to output directory for file operations
                    if tool_name in ["read_file", "write_file"] and "file_path" in arguments:
                        file_path = arguments["file_path"]
                        
                        # If path is not absolute, make it relative to output_dir
                        if not os.path.isabs(file_path):
                            arguments["file_path"] = os.path.join(self.output_dir, file_path)
                    
                    # Validate arguments
                    error = self.tool_executor.validate_arguments(tool, arguments)
                    if error:
                        tool_results.append({
                            "tool": tool_name,
                            "error": error
                        })
                        continue
                    
                    # Execute tool
                    result = self.tool_executor.execute_tool(tool, arguments)
                    tool_results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result
                    })
                
                # Add assistant message with tool calls
                messages.append({"role": "assistant", "content": response})
                
                # Add tool results as user message (with updated directory structure)
                results_message = self._format_tool_results_with_directory(tool_results)
                print(f"\nUSER (tools): {results_message}")
                messages.append({"role": "user", "content": results_message})
                
                # Record this iteration with tool calls
                history.append({
                    "iteration": iteration,
                    "response": response,
                    "tool_calls": tool_calls,
                    "finished": False
                })
                
                # Check if all tools succeeded, otherwise let agent retry
                all_success = all(
                    r.get("result", {}).get("success", False) 
                    for r in tool_results
                )
                
                if not all_success and iteration <= agent.max_retries:
                    continue
                
                # Continue to next iteration after tool execution
                continue
            
            # No tool calls - check for delegation
            delegation = self._parse_delegation(response)
            if delegation:
                messages.append({"role": "assistant", "content": response})
                history.append({
                    "iteration": iteration,
                    "response": response,
                    "tool_calls": [],
                    "delegation": delegation,
                    "finished": False
                })
                break
            
            # Check if agent marked task as finished
            is_finished = self._is_finished(response)
            
            # Record this iteration
            history.append({
                "iteration": iteration,
                "response": response,
                "tool_calls": [],
                "finished": is_finished
            })
            
            # If marked as finished, we're done
            if is_finished:
                messages.append({"role": "assistant", "content": response})
                break
            
            # No tool calls, no delegation, not finished - prompt to continue
            messages.append({"role": "assistant", "content": response})
            continue_prompt = self._build_continue_prompt()
            print(f"\nUSER (continue prompt): {continue_prompt}")
            messages.append({"role": "user", "content": continue_prompt})
        
        return {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "final_response": messages[-2]["content"] if len(messages) > 2 else "No response",
            "history": history,
            "messages": messages[1:],  # Exclude system message
            "iterations": iteration,
            "delegation": delegation,
            "finished": is_finished
        }
    
    def _parse_delegation(self, response: str) -> Optional[Dict[str, str]]:
        """Parse delegation from agent response."""
        import re
        
        # Pattern: [DELEGATE: agent_id] followed by task description
        pattern = r'\[DELEGATE:\s*(\w+)\]\s*(.+?)(?=\[DELEGATE:|$)'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            return {
                "to_agent": match.group(1),
                "task": match.group(2).strip()
            }
        
        return None
    
    def _is_finished(self, response: str) -> bool:
        """Check if agent marked their work as finished."""
        return "<FINISHED>" in response
    
    def _build_tools_description(self, tools: Dict[str, Tool]) -> str:
        """Build a description of available tools."""
        descriptions = []
        for tool in tools.values():
            params = ", ".join([
                f"{p.name}: {p.type}" + 
                (" (optional)" if not p.required else "")
                for p in tool.parameters
            ])
            descriptions.append(
                f"- {tool.name}({params}): {tool.description}"
            )
        return "\n".join(descriptions)
    
    def _format_tool_results(self, results: List[Dict[str, Any]]) -> str:
        """Format tool execution results for the agent."""
        formatted = []
        for result in results:
            tool_name = result["tool"]
            if "error" in result:
                formatted.append(f"[TOOL RESULT: {tool_name}]\nError: {result['error']}")
            else:
                exec_result = result["result"]
                if exec_result["success"]:
                    formatted.append(
                        f"[TOOL RESULT: {tool_name}]\nSuccess: {exec_result['result']}"
                    )
                else:
                    formatted.append(
                        f"[TOOL RESULT: {tool_name}]\nError: {exec_result['error']}"
                    )
        return "\n\n".join(formatted)
    
    def _format_tool_results_with_directory(self, results: List[Dict[str, Any]]) -> str:
        """Format tool execution results with updated directory structure."""
        results_text = self._format_tool_results(results)
        directory_info = self._build_directory_info()
        
        return f"{results_text}\n\n{directory_info}"
    
    def _build_continue_prompt(self) -> str:
        """Build continue prompt with directory structure."""
        directory_info = self._build_directory_info()
        
        prompt = f"""{directory_info}

You must either:
1. Use the available tools to continue working on the task
2. Delegate to another team member using [DELEGATE: agent_id]
3. Mark your work as complete with <FINISHED>

Please continue or finish your turn."""
        
        return prompt
    
    def _build_task_message(self, task: str, chat_history: Optional[List[Dict[str, Any]]]) -> str:
        """Build the initial task message with full chat history and directory structure."""
        message_parts = []
        
        # Add directory structure first
        message_parts.append(self._build_directory_info())
        
        # Add chat history if provided
        if chat_history:
            message_parts.append("\n=== Team Chat History ===")
            for msg in chat_history:
                agent_name = msg.get("agent_name", "Unknown")
                content = msg.get("content", "")
                message_parts.append(f"\n[{agent_name}]:\n{content}")
            message_parts.append("\n=== Your Task ===")
        else:
            message_parts.append("\n=== Your Task ===")
        
        # Add the actual task
        message_parts.append(task)
        
        return "\n".join(message_parts)