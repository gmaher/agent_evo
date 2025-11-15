from typing import Dict, List, Any, Optional
from pathlib import Path
from agent_evo.models.team import Team
from agent_evo.models.agent import Agent
from agent_evo.core.agent_runner import AgentRunner
from agent_evo.core.filesystem import FileSystem
from agent_evo.llm.client import LLMClient

class TeamRunner:
    """Orchestrates a team of agents working together."""
    
    def __init__(self, llm_client: LLMClient, filesystem: FileSystem, ignored_files=None):
        self.llm_client = llm_client
        self.filesystem = filesystem
        self.ignored_files = ignored_files or set()
        self.agent_runner = AgentRunner(
            llm_client, 
            filesystem,
            ignored_files=self.ignored_files
        )
    
    def run_team(self, 
                 team: Team,
                 task: str,
                 agents: Dict[str, Agent],
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
            
            # Run the agent with full chat history (no tools parameter needed)
            result = self.agent_runner.run_agent(
                agent=agent,
                task=current_task,
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
                # Check if there are unvisited team members available
                unvisited_neighbors = [aid for aid in available_agents if aid not in visited_agents]
                
                if unvisited_neighbors:
                    # Auto-delegate to first unvisited team member
                    next_agent_id = unvisited_neighbors[0]
                    next_agent = agents[next_agent_id]
                    
                    print(f"\n{'='*60}")
                    print(f"AUTO-DELEGATION: {agent.name} -> {next_agent.name}")
                    print(f"Reason: Unvisited team members remain")
                    print(f"{'='*60}")
                    
                    # Continue with next agent, passing along the current context
                    current_agent_id = next_agent_id
                    current_task = f"Continue the work from {agent.name}. Previous output: {result['final_response'][:200]}..."
                else:
                    # All neighbors visited or no neighbors left
                    print(f"\n{'='*60}")
                    print(f"TEAM COMPLETED: {agent.name} finished the task")
                    print(f"All available team members have been utilized")
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