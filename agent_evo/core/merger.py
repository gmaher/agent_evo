import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from agent_evo.llm.client import LLMClient
from agent_evo.loaders.json_loader import JSONLoader
from agent_evo.utils.parser import ToolCallParser
from agent_evo.core.tool_executor import ToolExecutor
from agent_evo.models.default_tools import create_file_writer_tool
from agent_evo.prompts.merge import MERGE_PROMPT

class TeamMerger:
    """Merges two agent teams into an improved combined team using LLM."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the team merger.
        
        Args:
            llm_client: LLM client to use for merging
        """
        self.llm_client = llm_client
        self.parser = ToolCallParser()
        self.executor = ToolExecutor()
        self.file_writer = create_file_writer_tool()
    
    def load_team_files(self, directory: Path) -> Dict[str, Any]:
        """Load all team files from a directory."""
        tools_path = directory / "tools.json"
        agents_path = directory / "agents.json"
        team_path = directory / "team.json"
        
        # Check all files exist
        missing = []
        if not tools_path.exists():
            missing.append("tools.json")
        if not agents_path.exists():
            missing.append("agents.json")
        if not team_path.exists():
            missing.append("team.json")
        
        if missing:
            raise FileNotFoundError(f"Missing files in {directory}: {', '.join(missing)}")
        
        # Load the files
        with open(tools_path, 'r') as f:
            tools = json.load(f)
        with open(agents_path, 'r') as f:
            agents = json.load(f)
        with open(team_path, 'r') as f:
            team = json.load(f)
        
        return {
            "tools": tools,
            "agents": agents,
            "team": team
        }
    
    def merge_teams(self,
                   team1_dir: Path,
                   team2_dir: Path,
                   output_dir: Path,
                   verbose: bool = False) -> Dict[str, Any]:
        """
        Merge two teams into an improved version.
        
        Args:
            team1_dir: Directory containing first team's files
            team2_dir: Directory containing second team's files
            output_dir: Directory to save merged team files
            verbose: Whether to include verbose output
            
        Returns:
            Dictionary with merge results and metadata
        """
        # Load both teams
        if verbose:
            print(f"Loading Team 1 from: {team1_dir}")
        team1 = self.load_team_files(team1_dir)
        
        if verbose:
            print(f"Loading Team 2 from: {team2_dir}")
        team2 = self.load_team_files(team2_dir)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if verbose:
            print(f"\nOutput directory: {output_dir.absolute()}")
            print("\n" + "="*60)
            print("MERGING TEAMS")
            print("="*60)
        
        # Format the prompt
        prompt = MERGE_PROMPT.format(
            team1_tools=json.dumps(team1["tools"], indent=2),
            team1_agents=json.dumps(team1["agents"], indent=2),
            team1_team=json.dumps(team1["team"], indent=2),
            team2_tools=json.dumps(team2["tools"], indent=2),
            team2_agents=json.dumps(team2["agents"], indent=2),
            team2_team=json.dumps(team2["team"], indent=2)
        )
        
        # Create system prompt
        system_prompt = """You are an expert AI team architect. You have access to a write_file tool to create the merged team files.

Available tool:
- write_file(file_path: string, content: string): Write content to a file

Use the tool to create tools.json, agents.json, and team.json with the improved merged team."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        if verbose:
            print("\nSending merge request to LLM...")
            print(f"Prompt length: {len(prompt)} characters")
        
        # Get LLM response
        response = self.llm_client.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=8000
        )
        
        if verbose:
            print(f"\nLLM Response:\n{response}")
        
        # Parse tool calls from response
        _, tool_calls = self.parser.parse_response(response)
        
        if not tool_calls:
            if verbose:
                print("\nWarning: LLM did not generate tool calls. Attempting to extract JSON directly...")
            self._extract_json_fallback(response, output_dir, verbose)
        else:
            # Execute tool calls
            if verbose:
                print(f"\nExecuting {len(tool_calls)} tool calls...")
            
            # Change to output directory before executing tools
            original_dir = os.getcwd()
            os.chdir(output_dir)
            
            try:
                for tool_call in tool_calls:
                    if tool_call["tool"] == "write_file":
                        result = self.executor.execute_tool(self.file_writer, tool_call["arguments"])
                        if result["success"]:
                            if verbose:
                                print(f"✓ Created: {tool_call['arguments']['file_path']}")
                        else:
                            if verbose:
                                print(f"✗ Failed to create {tool_call['arguments']['file_path']}: {result['error']}")
            finally:
                os.chdir(original_dir)
        
        # Validate created files
        validation = self._validate_created_files(output_dir, verbose)
        
        # Save merge log
        merge_log_path = output_dir / "merge_log.json"
        with open(merge_log_path, 'w') as f:
            json.dump({
                "team1_dir": str(team1_dir),
                "team2_dir": str(team2_dir),
                "team1_name": team1['team'].get('name'),
                "team2_name": team2['team'].get('name'),
                "llm_response": response,
                "validation": validation
            }, f, indent=2)
        
        if verbose:
            print(f"\nMerge log saved to: {merge_log_path}")
        
        return {
            "response": response,
            "tool_calls": tool_calls,
            "validation": validation,
            "team1": team1,
            "team2": team2
        }
    
    def _extract_json_fallback(self, response: str, output_dir: Path, verbose: bool = False):
        """Attempt to extract JSON directly from response when tool calls fail."""
        import re
        
        # Look for JSON blocks for each file
        for filename in ["tools.json", "agents.json", "team.json"]:
            pattern = rf'```json.*?{filename}.*?\n(.*?)```'
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if not match:
                # Try without filename in header
                pattern = r'```json\s*\n(\{.*?\})\s*```'
                matches = re.findall(pattern, response, re.DOTALL)
                if matches and verbose:
                    print(f"Warning: Could not automatically extract {filename}")
            else:
                content = match.group(1).strip()
                output_path = output_dir / filename
                with open(output_path, 'w') as f:
                    f.write(content)
                if verbose:
                    print(f"Extracted {filename}")
    
    def _validate_created_files(self, output_dir: Path, verbose: bool = False) -> Dict[str, Any]:
        """Validate the created team files."""
        tools_path = output_dir / "tools.json"
        agents_path = output_dir / "agents.json"
        team_path = output_dir / "team.json"
        
        created_files = []
        if tools_path.exists():
            created_files.append("tools.json")
        if agents_path.exists():
            created_files.append("agents.json")
        if team_path.exists():
            created_files.append("team.json")
        
        validation = {
            "all_files_created": len(created_files) == 3,
            "created_files": created_files,
            "validation_errors": []
        }
        
        if verbose:
            print("\n" + "="*60)
            print("VALIDATION")
            print("="*60)
        
        if len(created_files) == 3:
            if verbose:
                print("\n✓ All files created successfully:")
                for f in created_files:
                    print(f"  - {f}")
            
            # Validate JSON
            try:
                JSONLoader.load_tools(str(tools_path))
                if verbose:
                    print("\n✓ tools.json is valid")
            except Exception as e:
                validation["validation_errors"].append(f"tools.json: {e}")
                if verbose:
                    print(f"\n⚠ tools.json validation warning: {e}")
            
            try:
                JSONLoader.load_agents(str(agents_path))
                if verbose:
                    print("✓ agents.json is valid")
            except Exception as e:
                validation["validation_errors"].append(f"agents.json: {e}")
                if verbose:
                    print(f"⚠ agents.json validation warning: {e}")
            
            try:
                JSONLoader.load_team(str(team_path))
                if verbose:
                    print("✓ team.json is valid")
            except Exception as e:
                validation["validation_errors"].append(f"team.json: {e}")
                if verbose:
                    print(f"⚠ team.json validation warning: {e}")
        else:
            if verbose:
                print(f"\n⚠ Warning: Only created {len(created_files)} of 3 files: {', '.join(created_files)}")
        
        return validation