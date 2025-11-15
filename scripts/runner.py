import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import sys
from pathlib import Path

from agent_evo.core.app import AgentEvoApp



def main():
    parser = argparse.ArgumentParser(description="Run AI agent teams")
    parser.add_argument(
        "--input-dir", 
        required=True, 
        help="Directory containing agents.json and team.json"
    )
    parser.add_argument("--task", required=True, help="Path to task text file")
    parser.add_argument("--model", help="LLM model to use", default="gpt-4o")
    parser.add_argument(
        "--output-dir", 
        help="Directory to save generated files (default: ./output)", 
        default="./output"
    )
    parser.add_argument(
        "--context-dir",
        help="Directory containing initial context files to load into filesystem"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Initialize app
        app = AgentEvoApp(model=args.model)
        
        # Build exclude patterns (exclude team config files)
        exclude_patterns = ["agents.json", "team.json"]
        
        # Run team
        result = app.run_from_directory(
            team_dir=args.input_dir,
            task_path=args.task,
            verbose=args.verbose,
            context_dir=args.context_dir,
            exclude_patterns=exclude_patterns if args.context_dir else None
        )
        
        # Save files from in-memory filesystem to disk
        files_saved = app.save_filesystem_to_disk(args.output_dir)
        
        print(f"\n✓ Team execution completed successfully")
        print(f"✓ Saved {files_saved} files to {args.output_dir}")
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()