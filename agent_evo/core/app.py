"""Main application class for running agent teams."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from agent_evo.loaders.json_loader import JSONLoader
from agent_evo.llm.client import OpenAIClient, LLMClient
from agent_evo.core.team_runner import TeamRunner
from agent_evo.models.agent import Agent
from agent_evo.models.tool import Tool
from agent_evo.models.team import Team


class AgentEvoApp:
    """Main application for running agent teams."""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        model: str = "gpt-4o",
        output_dir: str = "./output",
        ignored_files: Optional[List[str]] = None
    ):
        """
        Initialize the application.
        
        Args:
            llm_client: Custom LLM client (if None, will create OpenAIClient)
            model: Model name to use if creating default client
            output_dir: Directory for output files
            ignored_files: Files to ignore in directory structure
        """
        self.model = model
        self.output_dir = Path(output_dir)
        self.ignored_files = set(ignored_files or ["agents.json", "tools.json", "team.json"])
        
        # Initialize LLM client
        if llm_client is None:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("Missing OPENAI_API_KEY environment variable")
            self.llm_client = OpenAIClient(api_key=api_key, model=model)
        else:
            self.llm_client = llm_client
        
        # Initialize team runner (will be created per run with specific output_dir)
        self.team_runner = None
    
    def load_team_from_directory(self, directory: str) -> Dict[str, Any]:
        """
        Load team configuration from a directory.
        
        Args:
            directory: Path to directory containing tools.json, agents.json, team.json
        
        Returns:
            Dictionary with 'tools', 'agents', and 'team' keys
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        print("LOAD TEAM", dir_path)
        tools_path = dir_path / "tools.json"
        agents_path = dir_path / "agents.json"
        team_path = dir_path / "team.json"
        print(tools_path, agents_path, team_path)
        # Check required files exist
        missing = []
        if not tools_path.exists():
            missing.append("tools.json")
        if not agents_path.exists():
            missing.append("agents.json")
        if not team_path.exists():
            missing.append("team.json")
        print("MISSING ", [])
        if missing:
            print("MISSING CHECK TRUE")
            raise FileNotFoundError(
                f"Missing required files in {directory}: {', '.join(missing)}"
            )
        
        # Load configurations
        tools = JSONLoader.load_tools(str(tools_path))
        print(tools)
        agents = JSONLoader.load_agents(str(agents_path))
        print(agents)
        team = JSONLoader.load_team(str(team_path))
        print(team)

        return {
            "tools": tools,
            "agents": agents,
            "team": team
        }
    
    def load_task(self, task_path: str) -> str:
        """Load task from file."""
        return JSONLoader.load_task(task_path)
    
    def run_team(
        self,
        team: Team,
        task: str,
        agents: Dict[str, Agent],
        tools: Dict[str, Tool],
        max_rounds: int = 10,
        save_result: bool = True,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a team on a task.
        
        Args:
            team: Team configuration
            task: Task description
            agents: Dictionary of agents
            tools: Dictionary of tools
            max_rounds: Maximum number of delegation rounds
            save_result: Whether to save result to output.json
            output_dir: Override output directory for this run
        
        Returns:
            Execution result dictionary
        """
        # Use provided output_dir or default
        run_output_dir = Path(output_dir) if output_dir else self.output_dir
        run_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create team runner with specific output directory
        team_runner = TeamRunner(
            llm_client=self.llm_client,
            output_dir=str(run_output_dir),
            ignored_files=self.ignored_files
        )
        
        print(f"Output directory: {run_output_dir.absolute()}")
        print(f"\nRunning team: {team.name}")
        print("=" * 60)
        
        # Run the team
        result = team_runner.run_team(
            team=team,
            task=task,
            agents=agents,
            tools=tools,
            max_rounds=max_rounds
        )
        
        print(f"\nTeam execution completed in {result['rounds']} rounds")
        
        # Save result if requested
        if save_result:
            result_path = run_output_dir / "output.json"
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\nResults saved to {result_path}")
        
        return result
    
    def run_from_directory(
        self,
        team_dir: str,
        task_path: str,
        max_rounds: int = 10,
        verbose: bool = False,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load team from directory and run on task.
        
        Args:
            team_dir: Directory containing team configuration
            task_path: Path to task file
            max_rounds: Maximum number of rounds
            verbose: Enable verbose output
            output_dir: Override output directory for this run
        
        Returns:
            Execution result dictionary
        """
        # Load team configuration
        if verbose:
            print(f"Loading team from: {team_dir}")
        
        config = self.load_team_from_directory(team_dir)
        task = self.load_task(task_path)
        
        if verbose:
            print(f"Loaded {len(config['tools'])} tools")
            print(f"Loaded {len(config['agents'])} agents")
            print(f"Task: {task[:100]}...")
        
        # Run the team
        result = self.run_team(
            team=config['team'],
            task=task,
            agents=config['agents'],
            tools=config['tools'],
            max_rounds=max_rounds,
            output_dir=output_dir
        )
        
        # Print outputs
        if verbose:
            print("\nAgent outputs:")
            for agent_id, output in result['agent_outputs'].items():
                agent_name = config['agents'][agent_id].name
                print(f"\n{agent_name}:")
                print(output)
        
        return result
    
    def validate_team_files(self, directory: str) -> Dict[str, Any]:
        """
        Validate team configuration files.
        
        Args:
            directory: Directory containing team files
        
        Returns:
            Validation results with status and any errors
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        print("VALIDATION", directory)
        try:
            config = self.load_team_from_directory(directory)
            print(config)
            # Validate team structure
            try:
                config['team'].validate()
            except Exception as e:
                validation["valid"] = False
                validation["errors"].append(f"Team validation error: {e}")
            
            # Check all agent tools exist
            for agent_id, agent in config['agents'].items():
                for tool_id in agent.tool_ids:
                    if tool_id not in config['tools']:
                        validation["warnings"].append(
                            f"Agent {agent_id} references non-existent tool: {tool_id}"
                        )
            
            # Check all team agents exist
            for agent_id in config['team'].agent_ids:
                if agent_id not in config['agents']:
                    validation["valid"] = False
                    validation["errors"].append(
                        f"Team references non-existent agent: {agent_id}"
                    )
        
        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(str(e))
        
        return validation