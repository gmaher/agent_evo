"""One-shot team merger that combines two teams in a single LLM call."""

import json
import re
from typing import Dict, Any

from agent_evo.llm.client import LLMClient
from agent_evo.models.agent import Agent
from agent_evo.models.team import Team
from agent_evo.models.default_tools import READ_FILE, WRITE_FILE
from agent_evo.prompts.merge import MERGE_PROMPT_ONE_SHOT


class OneShotMerger:
    """Merge and improve two team configurations in a single LLM call."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the merger.
        
        Args:
            llm_client: LLM client to use for generation
        """
        self.llm_client = llm_client
    
    def merge_teams(
        self,
        team1_agents: Dict[str, Agent],
        team1_team: Team,
        team2_agents: Dict[str, Agent],
        team2_team: Team,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Merge two teams into an improved single team.
        
        Args:
            team1_agents: Dictionary of agent_id -> Agent for team 1
            team1_team: Team configuration for team 1
            team2_agents: Dictionary of agent_id -> Agent for team 2
            team2_team: Team configuration for team 2
            temperature: LLM temperature for generation
        
        Returns:
            Dictionary with 'agents' and 'team' keys containing merged configurations
        
        Raises:
            ValueError: If JSON parsing fails
            RuntimeError: If LLM call fails
        """
        # Convert teams to JSON strings for the prompt
        team1_agents_json = self._agents_to_json(team1_agents)
        team1_team_json = self._team_to_json(team1_team)
        team2_agents_json = self._agents_to_json(team2_agents)
        team2_team_json = self._team_to_json(team2_team)
        
        # Build prompt
        prompt = MERGE_PROMPT_ONE_SHOT.format(
            team1_tools="[Default tools: read_file, write_file]",
            team1_agents=team1_agents_json,
            team1_team=team1_team_json,
            team2_tools="[Default tools: read_file, write_file]",
            team2_agents=team2_agents_json,
            team2_team=team2_team_json
        )
        
        print("=== MERGE PROMPT ===")
        print(prompt)
        print("=== END PROMPT ===\n")
        
        # Call LLM
        messages = [{"role": "user", "content": prompt}]
        response = self.llm_client.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=8000
        )
        
        print("=== LLM RESPONSE ===")
        print(response)
        print("=== END RESPONSE ===\n")
        
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
    
    def _agents_to_json(self, agents: Dict[str, Agent]) -> str:
        """Convert agents dictionary to JSON string."""
        agents_list = [agent.to_dict() for agent in agents.values()]
        return json.dumps({"agents": agents_list}, indent=2)
    
    def _team_to_json(self, team: Team) -> str:
        """Convert team to JSON string."""
        return json.dumps(team.to_dict(), indent=2)
    
    def _parse_agents(self, agents_data: Dict[str, Any]) -> Dict[str, Agent]:
        """Parse agents data into Agent objects."""
        agents = {}
        for agent_data in agents_data.get("agents", []):
            agent = Agent.from_dict(agent_data)
            # Add default tools
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
    
    def merge_and_save(
        self,
        team1_agents: Dict[str, Agent],
        team1_team: Team,
        team2_agents: Dict[str, Agent],
        team2_team: Team,
        output_dir: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Merge two teams and save the merged configuration to files.
        
        Args:
            team1_agents: Dictionary of agent_id -> Agent for team 1
            team1_team: Team configuration for team 1
            team2_agents: Dictionary of agent_id -> Agent for team 2
            team2_team: Team configuration for team 2
            output_dir: Directory to save merged agents.json and team.json
            temperature: LLM temperature for generation
        
        Returns:
            Dictionary with 'agents' and 'team' keys
        """
        from pathlib import Path
        
        result = self.merge_teams(
            team1_agents, team1_team,
            team2_agents, team2_team,
            temperature
        )
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save agents.json
        agents_path = output_path / "agents.json"
        agents_data = {
            "agents": [agent.to_dict() for agent in result["agents"].values()]
        }
        with open(agents_path, 'w', encoding='utf-8') as f:
            json.dump(agents_data, f, indent=2)
        
        # Save team.json
        team_path = output_path / "team.json"
        team_data = result["team"].to_dict()
        with open(team_path, 'w', encoding='utf-8') as f:
            json.dump(team_data, f, indent=2)
        
        print(f"\nMerged team configuration saved to {output_dir}/")
        print(f"- agents.json: {len(result['agents'])} agents")
        print(f"- team.json: {result['team'].name}")
        
        return result