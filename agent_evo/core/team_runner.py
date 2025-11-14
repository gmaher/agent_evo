from typing import Dict, List, Any, Optional
from agent_evo.models.team import Team
from agent_evo.models.agent import Agent
from agent_evo.models.tool import Tool
from agent_evo.core.agent_runner import AgentRunner
from agent_evo.llm.client import LLMClient

class TeamRunner:
    """Orchestrates a team of agents working together."""
    
    def __init__(self, llm_client: LLMClient, output_dir: str = ".", ignored_files=None):
        self.llm_client = llm_client
        self.output_dir = output_dir
        self.ignored_files = ignored_files
        self.agent_runner = AgentRunner(llm_client, output_dir, ignored_files=ignored_files)
    
    def run_team(self, 
                 team: Team,
                 task: str,
                 agents: Dict[str, Agent],
                 tools: Dict[str, Tool],
                 max_rounds: int = 10) -> Dict[str, Any]:
        """
        Run a team of agents on a task.
        """
        # Validate team
        team.validate()
        
        # Check all agents exist
        for agent_id in team.agent_ids:
            if agent_id not in agents:
                raise ValueError(f"Agent {agent_id} not found")
        
        # Maintain full chat history across all agents
        chat_history = []
        execution_history = []
        
        # Start with entry point agent
        current_agent_id = team.entry_point
        current_task = task
        visited_agents = set()
        round_num = 0
        
        for round_num in range(max_rounds):
            if current_agent_id is None:
                break
            
            if current_agent_id in visited_agents:
                print(f"Warning: Agent {current_agent_id} already visited, breaking cycle")
                break
            
            visited_agents.add(current_agent_id)
            agent = agents[current_agent_id]
            
            # Get agents this agent can delegate to
            available_agents = team.get_neighbors(current_agent_id)
            
            # Run the agent with full chat history
            result = self.agent_runner.run_agent(
                agent=agent,
                task=current_task,
                tools=tools,
                available_agents=available_agents,
                chat_history=chat_history
            )
            
            # Add agent's messages to chat history
            for msg in result["messages"]:
                chat_history.append({
                    "agent_id": current_agent_id,
                    "agent_name": agent.name,
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            execution_history.append({
                "round": round_num,
                "agent_id": current_agent_id,
                "agent_name": agent.name,
                "task": current_task,
                "result": result
            })
            
            # Check if agent delegated to another agent
            delegation = result.get("delegation")
            if delegation:
                delegated_agent_id = delegation["to_agent"]
                
                # Verify delegation is valid
                if delegated_agent_id not in available_agents:
                    print(f"Warning: Agent {current_agent_id} tried to delegate to {delegated_agent_id}, but that's not a valid neighbor")
                    break
                
                if delegated_agent_id not in agents:
                    print(f"Warning: Delegated agent {delegated_agent_id} not found")
                    break
                
                print(f"\n{'='*60}")
                print(f"DELEGATION: {agent.name} -> {agents[delegated_agent_id].name}")
                print(f"Task: {delegation['task'][:100]}...")
                print(f"{'='*60}")
                
                # Continue with delegated agent
                current_agent_id = delegated_agent_id
                current_task = delegation["task"]
            else:
                # Agent finished without delegating
                print(f"\n{'='*60}")
                print(f"TEAM COMPLETED: {agent.name} finished the task")
                print(f"{'='*60}")
                break
        
        # Extract final outputs from chat history
        agent_outputs = {}
        for entry in execution_history:
            agent_id = entry["agent_id"]
            final_response = entry["result"]["final_response"]
            agent_outputs[agent_id] = final_response
        
        return {
            "team_id": team.id,
            "team_name": team.name,
            "execution_history": execution_history,
            "chat_history": chat_history,
            "agent_outputs": agent_outputs,
            "rounds": round_num + 1
        }