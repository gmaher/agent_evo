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

def main():
    parser = argparse.ArgumentParser(description="Use an AI builder team to create a new team for a task")
    parser.add_argument("--builder-tools", required=True, help="Path to builder tools JSON file")
    parser.add_argument("--builder-agents", required=True, help="Path to builder agents JSON file")
    parser.add_argument("--builder-team", required=True, help="Path to builder team JSON file")
    parser.add_argument("--task", required=True, help="Path to task text file")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated team files")
    parser.add_argument("--model", help="LLM model to use", default="gpt-4o")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load builder configurations
        print("Loading builder team configurations...")
        builder_tools = JSONLoader.load_tools(args.builder_tools)
        builder_agents = JSONLoader.load_agents(args.builder_agents)
        builder_team = JSONLoader.load_team(args.builder_team)
        original_task = JSONLoader.load_task(args.task)
        
        if args.verbose:
            print(f"Loaded {len(builder_tools)} builder tools")
            print(f"Loaded {len(builder_agents)} builder agents")
            print(f"Original task: {original_task[:200]}...")
        
        # Initialize LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        
        llm_client = OpenAIClient(api_key=api_key, model=args.model)
        
        # Create the meta-task for the builder
        build_task = f"""You are an AI team builder. Your job is to design and create a team of AI agents that can solve the following task:

=== ORIGINAL TASK ===
{original_task}

=== YOUR OBJECTIVE ===
You need to create:
1. A tools.json file containing any custom tools the agents might need
2. An agents.json file defining the agents with appropriate system prompts and tool access
3. A team.json file defining the team structure and delegation flow

Guidelines:
- Think carefully about what types of agents are needed (e.g., researcher, writer, coder, analyst)
- Design appropriate tools for the task (file operations, calculations, search, etc.)
- Create clear system prompts that give each agent a specific role and expertise
- Design the delegation flow logically - who should start, who should delegate to whom
- Keep the team as simple as possible while still being effective
- Each agent should have a clear, focused responsibility

The files should be created in the following paths:
- {output_dir}/tools.json
- {output_dir}/agents.json
- {output_dir}/team.json

Make sure the JSON files are properly formatted and follow the expected schema.

Example schemas:

tools.json:
{{
  "tools": [
    {{
      "id": "tool_1",
      "name": "search",
      "description": "Search for information",
      "parameters": [...],
      "returns": {{"type": "string", "description": "Search results"}},
      "code": "def search(query): ..."
    }}
  ]
}}

agents.json:
{{
  "agents": [
    {{
      "id": "agent_1",
      "name": "Researcher",
      "system_prompt": "You are a research specialist...",
      "tool_ids": ["tool_1"],
      "temperature": 0.7
    }}
  ]
}}

team.json:
{{
  "id": "team_1",
  "name": "Task Team",
  "description": "Team for solving the task",
  "agent_ids": ["agent_1", "agent_2"],
  "edges": [
    {{"from": "agent_1", "to": "agent_2", "description": "Pass findings"}}
  ],
  "entry_point": "agent_1"
}}
"""
        
        print(f"\nRunning builder team: {builder_team.name}")
        print("="*60)
        
        runner = TeamRunner(llm_client)
        result = runner.run_team(
            team=builder_team,
            task=build_task,
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