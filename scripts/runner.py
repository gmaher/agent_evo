import sys
import os
sys.path.append(os.path.abspath(".."))
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from agent_evo.loaders.json_loader import JSONLoader
from agent_evo.llm.client import OpenAIClient, MockLLMClient
from agent_evo.core.agent_runner import AgentRunner
from agent_evo.core.team_runner import TeamRunner

def main():
    parser = argparse.ArgumentParser(description="Run AI agent teams")
    parser.add_argument("--tools", required=True, help="Path to tools JSON file")
    parser.add_argument("--agents", required=True, help="Path to agents JSON file")
    parser.add_argument("--team", required=True, help="Path to team JSON file (for team mode)")
    parser.add_argument("--task", required=True, help="Path to task text file")
    parser.add_argument("--model", help="LLM model to use", default="gpt-4o")

    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Load configurations
        print("Loading configurations...")
        tools = JSONLoader.load_tools(args.tools)
        agents = JSONLoader.load_agents(args.agents)
        task = JSONLoader.load_task(args.task)
        
        if args.verbose:
            print(f"Loaded {len(tools)} tools")
            print(f"Loaded {len(agents)} agents")
            print(f"Task: {task[:100]}...")
        
        # Initialize LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        
        llm_client = OpenAIClient(api_key=api_key, model=args.model)
        

        # Team mode
        team = JSONLoader.load_team(args.team)
        print(f"Running team: {team.name}")
        
        runner = TeamRunner(llm_client)
        result = runner.run_team(
            team=team,
            task=task,
            agents=agents,
            tools=tools
        )
        
        print(f"\nTeam execution completed in {result['rounds']} rounds")
        print("\nAgent outputs:")
        for agent_id, output in result['agent_outputs'].items():
            print(f"\n{agents[agent_id].name}:")
            print(output)
        
        
        # Save output if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\nResults saved to {args.output}")
    
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()