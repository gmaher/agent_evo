import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import sys
from pathlib import Path

from agent_evo.core.app import AgentEvoApp
from agent_evo.prompts.builder import BUILD_PROMPT
from agent_evo.prompts.builder import BUILD_PROMPT, format_available_tools


def main():
    parser = argparse.ArgumentParser(
        description="Use an AI builder team to create a new team for a task"
    )
    parser.add_argument(
        "--builder-dir", 
        required=True, 
        help="Directory containing builder team files"
    )
    parser.add_argument("--task", required=True, help="Path to task text file")
    parser.add_argument(
        "--output-dir", 
        required=True, 
        help="Directory to save generated team files"
    )
    parser.add_argument("--model", help="LLM model to use", default="gpt-4o")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Initialize app with no ignored files for builder
        app = AgentEvoApp(
            model=args.model,
            output_dir=args.output_dir,
            ignored_files=[]
        )
        
        # Load builder team
        if args.verbose:
            print(f"Loading builder team from: {args.builder_dir}")
        
        builder_config = app.load_team_from_directory(args.builder_dir)
        original_task = app.load_task(args.task)
        
        if args.verbose:
            print(f"Loaded {len(builder_config['agents'])} builder agents")
            print(f"Original task: {original_task[:200]}...")
        
        # Run builder team
        result = app.run_team(
            team=builder_config['team'],
            task=BUILD_PROMPT.format(
                original_task=original_task,
                available_tools=format_available_tools()
            ),
            agents=builder_config['agents']
        )
        
        # Validate generated files
        output_dir = Path(args.output_dir)
        agents_path = output_dir / "agents.json"
        team_path = output_dir / "team.json"
        
        files_created = []
        if agents_path.exists():
            files_created.append("agents.json")
        if team_path.exists():
            files_created.append("team.json")
        
        if files_created:
            print(f"\n✓ Successfully created: {', '.join(files_created)}")
            
            # Validate the generated files
            validation = app.validate_team_files(str(output_dir))
            if validation["valid"]:
                print("✓ All files are valid")
            else:
                print("⚠ Validation warnings/errors:")
                for error in validation["errors"]:
                    print(f"  ERROR: {error}")
                for warning in validation["warnings"]:
                    print(f"  WARNING: {warning}")
        else:
            print(f"\n⚠ Warning: No team files were created")
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()