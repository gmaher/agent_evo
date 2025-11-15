
"""One-shot team builder that generates team configuration in a single LLM call."""

import json
import re
from typing import Dict, Any, List, Optional

from agent_evo.llm.client import LLMClient
from agent_evo.models.agent import Agent
from agent_evo.models.default_tools import READ_FILE, WRITE_FILE
from agent_evo.models.team import Team
from agent_evo.prompts.builder import ONE_SHOT_BUILD_PROMPT, format_available_tools
from agent_evo.loaders.json_loader import JSONLoader
from agent_evo.models.default_tools import READ_FILE, WRITE_FILE


class OneShotBuilder:
    """Build a team configuration in a single LLM call."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the builder.
        
        Args:
            llm_client: LLM client to use for generation
        """
        self.llm_client = llm_client
    
    
    def build_team(self, task: str, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Build a team configuration for the given task.
        
        Args:
            task: The task description to build a team for
            temperature: LLM temperature for generation
        
        Returns:
            Dictionary with 'agents' and 'team' keys containing parsed configurations
        
        Raises:
            ValueError: If JSON parsing fails
            RuntimeError: If LLM call fails
        """
        # Format available tools
        tools_description = format_available_tools()
        
        # Build prompt
        prompt = ONE_SHOT_BUILD_PROMPT.format(
            task=task,
            available_tools=tools_description
        )
        print(prompt)
        # Call LLM
        messages = [{"role": "user", "content": prompt}]
        response = self.llm_client.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=8000
        )
        print(response)
        # Parse response
        agents_json, team_json = self._parse_response(response)
        
        # Parse JSON strings into objects
        try:
            agents_data = json.loads(agents_json)
            team_data = json.loads(team_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}\nResponse: {response}")
        
        # Convert to Agent and Team objects
        agents = self._parse_agents(agents_data)
        team = self._parse_team(team_data)
        
        return {
            "agents": agents,
            "team": team,
            "raw_response": response
        }
    
    def _parse_agents(self, agents_data: Dict[str, Any]) -> Dict[str, Agent]:
        """Parse agents data into Agent objects."""
        agents = {}
        for agent_data in agents_data.get("agents", []):
            agent = Agent.from_dict(agent_data)
            # Add default tools like JSONLoader does
            agent.tool_names = list(set(agent.tool_names + [READ_FILE, WRITE_FILE]))
            agents[agent.id] = agent
        return agents
    
    def _parse_team(self, team_data: Dict[str, Any]) -> Team:
        """Parse team data into Team object."""
        # Handle case where team data might be nested under "team" key
        if "team" in team_data:
            team_data = team_data["team"]
        return Team.from_dict(team_data)
    
    def _parse_response(self, response: str) -> tuple[str, str]:
        """
        Parse the LLM response to extract agents.json and team.json.
        
        Args:
            response: Raw LLM response
        
        Returns:
            Tuple of (agents_json_string, team_json_string)
        
        Raises:
            ValueError: If JSON blocks cannot be found
        """
        # Pattern to match ```json filename blocks
        pattern = r'```json\s+(\S+)\s*\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if len(matches) < 2:
            raise ValueError(
                f"Expected 2 JSON code blocks, found {len(matches)}. "
                f"Response: {response[:500]}"
            )
        
        agents_json = None
        team_json = None
        
        for filename, content in matches:
            if 'agents' in filename.lower():
                agents_json = content.strip()
            elif 'team' in filename.lower():
                team_json = content.strip()
        
        if not agents_json or not team_json:
            raise ValueError(
                f"Could not find both agents.json and team.json blocks. "
                f"Found: {[m[0] for m in matches]}"
            )
        
        return agents_json, team_json
    
    def build_and_save(
        self,
        task: str,
        output_dir: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Build a team and save the configuration to files.
        
        Args:
            task: The task description to build a team for
            output_dir: Directory to save agents.json and team.json
            temperature: LLM temperature for generation
        
        Returns:
            Dictionary with 'agents' and 'team' keys
        """
        from pathlib import Path
        
        result = self.build_team(task, temperature)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save agents.json
        agents_path = output_path / "agents.json"
        agents_data = {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "system_prompt": agent.system_prompt,
                    "tool_names": agent.tool_names,
                    "temperature": agent.temperature,
                    "max_retries": agent.max_retries
                }
                for agent in result["agents"].values()
            ]
        }
        with open(agents_path, 'w', encoding='utf-8') as f:
            json.dump(agents_data, f, indent=2)
        
        # Save team.json
        team_path = output_path / "team.json"
        team = result["team"]
        team_data = {
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "agent_ids": team.agent_ids,
            "edges": [
                {
                    "from": edge.from_agent,
                    "to": edge.to_agent,
                    "description": edge.description
                }
                for edge in team.edges
            ],
            "entry_point": team.entry_point
        }
        with open(team_path, 'w', encoding='utf-8') as f:
            json.dump(team_data, f, indent=2)
        
        print(f"\nTeam configuration saved to {output_dir}/")
        print(f"- agents.json: {len(result['agents'])} agents")
        print(f"- team.json: {team.name}")
        
        return result