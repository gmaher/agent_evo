from typing import Dict, List, Any, Optional
from agent_evo.models.team import Team
from agent_evo.models.agent import Agent
from agent_evo.models.tool import Tool
from agent_evo.core.agent_runner import AgentRunner
from agent_evo.llm.client import LLMClient

class TeamRunner:
    """Orchestrates a team of agents working together."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.agent_runner = AgentRunner(llm_client)
    
    def run_team(self, 
                 team: Team,
                 task: str,
                 agents: Dict[str, Agent],
                 tools: Dict[str, Tool],
                 max_rounds: int = 5) -> Dict[str, Any]:
        """
        Run a team of agents on a task.
        """
        # Validate team
        team.validate()
        
        # Check all agents exist
        for agent_id in team.agent_ids:
            if agent_id not in agents:
                raise ValueError(f"Agent {agent_id} not found")
        
        execution_history = []
        agent_outputs = {}
        
        # Start with entry point agent
        current_tasks = {team.entry_point: task}
        visited_agents = set()
        round_num = 0
        for round_num in range(max_rounds):
            if not current_tasks:
                break
            
            next_tasks = {}
            
            for agent_id, agent_task in current_tasks.items():
                if agent_id in visited_agents:
                    continue
                
                visited_agents.add(agent_id)
                agent = agents[agent_id]
                
                # Build context from previous agent outputs
                context = {
                    "round": round_num,
                    "team_id": team.id,
                    "previous_outputs": agent_outputs
                }
                
                # Run the agent
                result = self.agent_runner.run_agent(
                    agent=agent,
                    task=agent_task,
                    tools=tools,
                    context=context
                )
                
                agent_outputs[agent_id] = result["final_response"]
                execution_history.append({
                    "round": round_num,
                    "agent_id": agent_id,
                    "task": agent_task,
                    "result": result
                })
                
                # Check if this agent can delegate to others
                neighbors = team.get_neighbors(agent_id)
                
                if neighbors:
                    # For simplicity, pass the same task to all neighbors
                    # In practice, the agent could specify different tasks
                    delegation_prompt = f"""
Based on the following task and your response, delegate subtasks to your team members:

Original Task: {agent_task}

Your Response: {result["final_response"]}

Available team members: {', '.join(neighbors)}

For each team member you want to delegate to, specify their task.
Use format: [DELEGATE: agent_id] task description
"""
                    
                    delegation_messages = [
                        {"role": "system", "content": "You are coordinating a team. Delegate tasks as needed."},
                        {"role": "user", "content": delegation_prompt}
                    ]
                    
                    delegation_response = self.llm_client.generate(
                        messages=delegation_messages,
                        temperature=0.7
                    )
                    
                    # Parse delegations
                    delegations = self._parse_delegations(delegation_response, neighbors)
                    
                    for delegated_agent_id, delegated_task in delegations.items():
                        if delegated_agent_id not in visited_agents:
                            next_tasks[delegated_agent_id] = delegated_task
            
            current_tasks = next_tasks
        
        return {
            "team_id": team.id,
            "team_name": team.name,
            "execution_history": execution_history,
            "agent_outputs": agent_outputs,
            "rounds": round_num + 1
        }
    
    def _parse_delegations(self, response: str, valid_agents: List[str]) -> Dict[str, str]:
        """Parse delegation instructions from response."""
        import re
        
        delegations = {}
        pattern = r'\[DELEGATE:\s*(\w+)\]\s*(.+?)(?=\[DELEGATE:|$)'
        matches = re.finditer(pattern, response, re.DOTALL)
        
        for match in matches:
            agent_id = match.group(1)
            task = match.group(2).strip()
            
            if agent_id in valid_agents:
                delegations[agent_id] = task
        
        return delegations