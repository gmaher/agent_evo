"""Main application class for running agent teams."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from agent_evo.core.filesystem import FileSystem
from agent_evo.loaders.json_loader import JSONLoader
from agent_evo.llm.client import OpenAIClient, LLMClient
from agent_evo.core.team_runner import TeamRunner
from agent_evo.models.agent import Agent
from agent_evo.models.team import Team


class AgentEvoApp:
    """Main application for running agent teams."""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        model: str = "gpt-4o",
        ignored_files: Optional[List[str]] = None
    ):
        """
        Initialize the application.
        
        Args:
            llm_client: Custom LLM client (if None, will create OpenAIClient)
            model: Model name to use if creating default client
            ignored_files: Files to ignore in directory structure
        """
        self.model = model
        self.ignored_files = set(ignored_files or ["agents.json", "team.json"])
        
        # Initialize LLM client
        if llm_client is None:
            import os
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("Missing OPENAI_API_KEY environment variable")
            self.llm_client = OpenAIClient(api_key=api_key, model=model)
        else:
            self.llm_client = llm_client
        
        # Initialize in-memory filesystem
        self.filesystem = FileSystem()
    
    def load_team_from_directory(self, directory: str) -> Dict[str, Any]:
        """
        Load team configuration from a directory.
        
        Args:
            directory: Path to directory containing agents.json and team.json
        
        Returns:
            Dictionary with 'agents' and 'team' keys
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        agents_path = dir_path / "agents.json"
        team_path = dir_path / "team.json"
        
        # Check required files exist
        missing = []
        if not agents_path.exists():
            missing.append("agents.json")
        if not team_path.exists():
            missing.append("team.json")
        
        if missing:
            raise FileNotFoundError(
                f"Missing required files in {directory}: {', '.join(missing)}"
            )
        
        # Load configurations
        agents = JSONLoader.load_agents(str(agents_path))
        team = JSONLoader.load_team(str(team_path))

        return {
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
        max_rounds: int = 10,
        save_result: bool = True
    ) -> Dict[str, Any]:
        """
        Run a team on a task.
        
        Args:
            team: Team configuration
            task: Task description
            agents: Dictionary of agents
            max_rounds: Maximum number of delegation rounds
            save_result: Whether to save result to filesystem
        
        Returns:
            Execution result dictionary
        """
        # Create team runner with filesystem
        team_runner = TeamRunner(
            llm_client=self.llm_client,
            filesystem=self.filesystem,
            ignored_files=self.ignored_files
        )
        
        print(f"\nRunning team: {team.name}")
        print("=" * 60)
        
        # Run the team
        result = team_runner.run_team(
            team=team,
            task=task,
            agents=agents,
            max_rounds=max_rounds
        )
        
        print(f"\nTeam execution completed in {result['rounds']} rounds")
        
        # Save result to filesystem if requested
        if save_result:
            result_json = json.dumps(result, indent=2, default=str)
            self.filesystem.write_file("output.json", result_json)
            print(f"\nResults saved to output.json in filesystem")
        
        return result
    
    def get_filesystem_files(self) -> Dict[str, str]:
        """Get all files from the in-memory filesystem."""
        return self.filesystem.files.copy()
    
    def clear_filesystem(self):
        """Clear all files from the filesystem."""
        self.filesystem.clear()
    
    def run_from_directory(
        self,
        team_dir: str,
        task_path: str,
        max_rounds: int = 10,
        verbose: bool = False,
        context_dir: Optional[str] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Load team from directory and run on task.
        
        Args:
            team_dir: Directory containing team configuration
            task_path: Path to task file
            max_rounds: Maximum number of rounds
            verbose: Enable verbose output
            context_dir: Optional directory to load initial files from
            exclude_patterns: Patterns to exclude when loading context_dir
        
        Returns:
            Execution result dictionary
        """
        # Load initial context files if specified
        if context_dir:
            if verbose:
                print(f"Loading context files from: {context_dir}")
            
            files_loaded = self.load_directory_into_filesystem(
                context_dir,
                exclude_patterns=exclude_patterns
            )
            
            if verbose:
                print(f"Loaded {files_loaded} initial files into filesystem")
        
        # Load team configuration
        if verbose:
            print(f"Loading team from: {team_dir}")
        
        config = self.load_team_from_directory(team_dir)
        task = self.load_task(task_path)
        
        if verbose:
            print(f"Loaded {len(config['agents'])} agents")
            print(f"Task: {task[:100]}...")
        
        # Run the team
        result = self.run_team(
            team=config['team'],
            task=task,
            agents=config['agents'],
            max_rounds=max_rounds,
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
        
        try:
            config = self.load_team_from_directory(directory)
            
            # Validate team structure
            try:
                config['team'].validate()
            except Exception as e:
                validation["valid"] = False
                validation["errors"].append(f"Team validation error: {e}")
            
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
    

    def save_filesystem_to_disk(self, output_dir: str):
        """
        Save all files from in-memory filesystem to disk.
        
        Args:
            output_dir: Directory to save files to
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        files_saved = 0
        for file_path, content in self.filesystem.files.items():
            # Create full path
            full_path = output_path / file_path
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            files_saved += 1
        
        return files_saved
    
    def load_directory_into_filesystem(
        self,
        directory: str,
        exclude_patterns: Optional[List[str]] = None
    ) -> int:
        """
        Recursively load all files from a directory into the in-memory filesystem.
        
        Args:
            directory: Path to directory to load
            exclude_patterns: List of patterns to exclude (glob-style)
        
        Returns:
            Number of files loaded
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        exclude_patterns = exclude_patterns or []
        files_loaded = 0
        
        # Recursively find all files
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Get relative path from directory
            relative_path = file_path.relative_to(dir_path)
            relative_str = str(relative_path)
            
            # Check if should be excluded
            should_exclude = False
            for pattern in exclude_patterns:
                if pattern in relative_str:
                    should_exclude = True
                    break
            
            if should_exclude:
                continue
            
            # Read and add to filesystem
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.filesystem.write_file(relative_str, content)
                files_loaded += 1
            except Exception as e:
                print(f"Warning: Could not load {relative_str}: {e}")
        
        return files_loaded