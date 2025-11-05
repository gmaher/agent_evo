from typing import Dict, List, Any, Optional
from agent_evo.models.agent import Agent
from agent_evo.models.tool import Tool
from agent_evo.core.tool_executor import ToolExecutor
from agent_evo.utils.parser import ToolCallParser
from agent_evo.llm.client import LLMClient

class AgentRunner:
    """Runs an agent with tool execution capabilities."""
    
    BASE_SYSTEM_PROMPT = """You are an AI agent with access to various tools. When you need to use a tool, use the following syntax:

[TOOL: tool_name(arg1=value1, arg2=value2)]

For example:
[TOOL: calculate(expression="2 + 2")]
[TOOL: search(query="AI news", limit=5)]

You can use multiple tools in a single response. After using a tool, I will provide you with the result, and you can continue with your task.

Always think step by step about what tools you need to use to complete the task.

Available tools:
{tools_description}

{custom_prompt}"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.tool_executor = ToolExecutor()
        self.parser = ToolCallParser()
    
    def run_agent(self, 
                  agent: Agent, 
                  task: str, 
                  tools: Dict[str, Tool],
                  context: Optional[Dict[str, Any]] = None,
                  max_iterations: int = 10) -> Dict[str, Any]:
        """
        Run an agent on a task with available tools.
        Returns the final response and execution history.
        """
        # Filter tools available to this agent
        available_tools = {
            tool_id: tool 
            for tool_id, tool in tools.items() 
            if tool_id in agent.tool_ids
        }
        
        # Build tools description
        tools_description = self._build_tools_description(available_tools)
        
        # Build system prompt
        system_prompt = self.BASE_SYSTEM_PROMPT.format(
            tools_description=tools_description,
            custom_prompt=agent.system_prompt
        )
        
        # Initialize conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task}
        ]
        
        history = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get response from LLM
            response = self.llm_client.generate(
                messages=messages,
                temperature=agent.temperature
            )
            
            # Parse response for tool calls
            cleaned_response, tool_calls = self.parser.parse_response(response)
            
            history.append({
                "iteration": iteration,
                "response": response,
                "tool_calls": tool_calls
            })
            
            # If no tool calls, we're done
            if not tool_calls:
                messages.append({"role": "assistant", "content": response})
                break
            
            # Execute tool calls
            tool_results = []
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
            
            # Add tool results as user message
            results_message = self._format_tool_results(tool_results)
            messages.append({"role": "user", "content": results_message})
            
            # Check if all tools succeeded
            all_success = all(
                r.get("result", {}).get("success", False) 
                for r in tool_results
            )
            
            if not all_success and iteration <= agent.max_retries:
                # Let agent retry
                continue
        
        return {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "final_response": messages[-2]["content"] if len(messages) > 2 else "No response",
            "history": history,
            "messages": messages,
            "iterations": iteration
        }
    
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