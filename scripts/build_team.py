import sys
import os

sys.path.append(os.path.abspath(".."))
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from agent_evo.loaders.json_loader import JSONLoader
from agent_evo.llm.client import OpenAIClient
from agent_evo.core.team_runner import TeamRunner
from agent_evo.prompts.builder import BUILD_PROMPT

def main():
    parser = argparse.ArgumentParser(description="Use an AI builder team to create a new team for a task")
    parser.add_argument("--builder-dir", required=True, help="Directory containing builder team files (agents.json, tools.json, team.json)")
    parser.add_argument("--task", required=True, help="Path to task text file")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated team files")
    parser.add_argument("--model", help="LLM model to use", default="gpt-4o")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Validate builder directory and files exist
        builder_dir = Path(args.builder_dir)
        if not builder_dir.exists():
            raise FileNotFoundError(f"Builder directory does not exist: {builder_dir}")
        
        # Define expected file paths
        builder_tools_path = builder_dir / "tools.json"
        builder_agents_path = builder_dir / "agents.json"
        builder_team_path = builder_dir / "team.json"
        
        # Check if all required files exist
        missing_files = []
        if not builder_tools_path.exists():
            missing_files.append("tools.json")
        if not builder_agents_path.exists():
            missing_files.append("agents.json")
        if not builder_team_path.exists():
            missing_files.append("team.json")
        
        if missing_files:
            raise FileNotFoundError(f"Missing required files in {builder_dir}: {', '.join(missing_files)}")
        

        
        # Load builder configurations
        print(f"Loading builder team from: {builder_dir}")
        builder_tools = JSONLoader.load_tools(str(builder_tools_path))
        builder_agents = JSONLoader.load_agents(str(builder_agents_path))
        builder_team = JSONLoader.load_team(str(builder_team_path))
        original_task = JSONLoader.load_task(args.task)
        
        if args.verbose:
            print(f"Loaded {len(builder_tools)} builder tools")
            print(f"Loaded {len(builder_agents)} builder agents")
            print(f"Builder team: {builder_team.name}")
            print(f"Original task: {original_task[:200]}...")

        # Create output directory and change to it
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(output_dir)
        print(f"Working directory: {output_dir.absolute()}")

        # Initialize LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        
        llm_client = OpenAIClient(api_key=api_key, model=args.model)
        
        print(f"\nRunning builder team: {builder_team.name}")
        print("="*60)
        
        runner = TeamRunner(llm_client)
        result = runner.run_team(
            team=builder_team,
            task=BUILD_PROMPT.format(original_task=original_task),
            agents=builder_agents,
            tools=builder_tools
        )
        
        print(f"\nBuilder team execution completed in {result['rounds']} rounds")
        
        # Check if files were created
        tools_path = output_dir / "tools.json"
        agents_path = output_dir / "agents.json"
        team_path = output_dir / "team.json"
        
        files_created = []
        if tools_path.exists():
            files_created.append("tools.json")
        if agents_path.exists():
            files_created.append("agents.json")
        if team_path.exists():
            files_created.append("team.json")
        
        if files_created:
            print(f"\n✓ Successfully created: {', '.join(files_created)}")
            print(f"Files saved to: {output_dir}")
            
            # Validate the generated files
            try:
                if tools_path.exists():
                    JSONLoader.load_tools(str(tools_path))
                    print("✓ tools.json is valid")
                if agents_path.exists():
                    JSONLoader.load_agents(str(agents_path))
                    print("✓ agents.json is valid")
                if team_path.exists():
                    JSONLoader.load_team(str(team_path))
                    print("✓ team.json is valid")
            except Exception as e:
                print(f"⚠ Warning: Generated files have validation issues: {e}")
        else:
            print(f"\n⚠ Warning: No team files were created in {output_dir}")
            print("Check the agent outputs for any errors")
        
        # Save the builder execution result
        result_path = output_dir / "builder_result.json"
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nBuilder execution details saved to: {result_path}")
    
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()