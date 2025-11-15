import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import sys
from pathlib import Path

from agent_evo.llm.client import OpenAIClient
from agent_evo.core.merger import TeamMerger


def main():
    parser = argparse.ArgumentParser(
        description="Merge two AI agent teams into an improved combined team"
    )
    parser.add_argument(
        "--team1-dir", 
        required=True, 
        help="Directory containing first team's files (agents.json, team.json)"
    )
    parser.add_argument(
        "--team2-dir",
        required=True,
        help="Directory containing second team's files (agents.json, team.json)"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to save merged team files"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="LLM model to use for merging (default: gpt-4o)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        # Validate input directories
        team1_dir = Path(args.team1_dir)
        team2_dir = Path(args.team2_dir)
        output_dir = Path(args.output_dir)
        
        if not team1_dir.exists():
            raise FileNotFoundError(f"Team 1 directory not found: {team1_dir}")
        if not team2_dir.exists():
            raise FileNotFoundError(f"Team 2 directory not found: {team2_dir}")
        
        # Initialize LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        
        llm_client = OpenAIClient(api_key=api_key, model=args.model)
        
        # Create merger
        merger = TeamMerger(llm_client)
        
        # Merge teams
        result = merger.merge_teams(
            team1_dir=team1_dir,
            team2_dir=team2_dir,
            output_dir=output_dir,
            verbose=args.verbose
        )
        
        print("\n" + "="*60)
        print("MERGE COMPLETE")
        print("="*60)
        
        if result["validation"]["all_files_created"]:
            print("\n✓ Successfully merged teams")
            if result["validation"]["validation_errors"]:
                print("\n⚠ Validation warnings:")
                for error in result["validation"]["validation_errors"]:
                    print(f"  - {error}")
        else:
            print("\n⚠ Merge completed with issues")
            print(f"Created files: {', '.join(result['validation']['created_files'])}")
        
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()