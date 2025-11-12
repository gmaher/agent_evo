"""Example demonstrating file reading and writing with agents."""
import os
import sys
sys.path.append(os.path.abspath(".."))

from agent_evo.models.agent import Agent
from agent_evo.core.agent_runner import AgentRunner
from agent_evo.llm.client import OpenAIClient
import os

# Create an agent (no need to specify file tools in tool_ids)
file_agent = Agent(
    id="file_agent",
    name="File Handler",
    system_prompt="You are a helpful file management assistant.",
    tool_ids=[],  # Empty - will still have access to default file tools
    temperature=0.7
)

# Setup
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Please set OPENAI_API_KEY environment variable")

llm_client = OpenAIClient(api_key=api_key)
runner = AgentRunner(llm_client)

# Run agent with a file task
result = runner.run_agent(
    agent=file_agent,
    task="Please create a file called 'test_output.txt' with the content 'Hello from Agent!' and then read it back to verify it was created correctly.",
    tools={},  # No additional tools needed - defaults are included
)

print(f"\nAgent completed in {result['iterations']} iterations")
print(f"Final response: {result['final_response']}")