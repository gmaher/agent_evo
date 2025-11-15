import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import json
from pathlib import Path
from datetime import datetime

from agent_evo.core.app import AgentEvoApp
from agent_evo.prompts.builder import BUILD_PROMPT


def main():
    parser = argparse.ArgumentParser(
        description="Build agent teams for multiple tasks in batch using a builder team"
    )
    parser.add_argument(
        "--tasks-dir",
        required=True,
        help="Directory containing subdirectories with task.txt files"
    )
    parser.add_argument(
        "--builder-dir",
        required=True,
        help="Directory containing builder team files"
    )
    parser.add_argument("--model", default="gpt-4o", help="LLM model to use")
    parser.add_argument("--max-rounds", type=int, default=10, help="Maximum rounds per build")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        original_dir = os.getcwd()
        tasks_dir = Path(os.path.abspath(args.tasks_dir))
        
        if not tasks_dir.exists():
            raise FileNotFoundError(f"Tasks directory not found: {tasks_dir}")
        
        # Find all subdirectories with task.txt
        task_dirs = []
        for subdir in tasks_dir.iterdir():
            if subdir.is_dir():
                task_file = subdir / "task.txt"
                if task_file.exists():
                    task_dirs.append(subdir)
        
        if not task_dirs:
            print(f"No subdirectories with task.txt found in {tasks_dir}")
            return
        
        print(f"Found {len(task_dirs)} tasks to build teams for")
        print("="*60)
        
        # Store results
        batch_results = {
            "start_time": datetime.now().isoformat(),
            "tasks_dir": str(tasks_dir),
            "builder_dir": args.builder_dir,
            "model": args.model,
            "builds": []
        }
        
        # Process each task
        for i, task_dir in enumerate(task_dirs, 1):
            task_file = task_dir / "task.txt"
            output_dir = task_dir / "team"
            
            print(f"\n[{i}/{len(task_dirs)}] Building team for: {task_dir.name}")
            print("-"*60)
            
            build_result = {
                "task_dir": str(task_dir),
                "task_name": task_dir.name,
                "output_dir": str(output_dir),
                "success": False,
                "error": None
            }
            
            try:
                # Initialize app with team subdirectory as output
                app = AgentEvoApp(
                    model=args.model,
                    output_dir=str(output_dir),
                    ignored_files=[]
                )
                
                # Load builder team
                if args.verbose:
                    print(f"Loading builder team from: {args.builder_dir}")
                
                builder_config = app.load_team_from_directory(args.builder_dir)
                
                # Load task
                with open(task_file, 'r') as f:
                    original_task = f.read().strip()
                
                if args.verbose:
                    print(f"Task: {original_task[:200]}...")
                    print(f"Loaded {len(builder_config['tools'])} builder tools")
                    print(f"Loaded {len(builder_config['agents'])} builder agents")
                
                try:
                    # Run builder team
                    result = app.run_team(
                        team=builder_config['team'],
                        task=BUILD_PROMPT.format(original_task=original_task),
                        agents=builder_config['agents'],
                        tools=builder_config['tools'],
                        max_rounds=args.max_rounds,
                        save_result=True
                    )
                    
                    # Validate generated files
                    files_created = []
                    tools_path = output_dir / "tools.json"
                    agents_path = output_dir / "agents.json"
                    team_path = output_dir / "team.json"
                    
                    if tools_path.exists():
                        files_created.append("tools.json")
                    if agents_path.exists():
                        files_created.append("agents.json")
                    if team_path.exists():
                        files_created.append("team.json")
                    
                    if files_created:
                        build_result["files_created"] = files_created
                        
                        # Validate the generated files
                        validation = app.validate_team_files(str(output_dir))
                        build_result["validation"] = validation
                        
                        if validation["valid"]:
                            build_result["success"] = True
                            print(f"✓ Successfully created: {', '.join(files_created)}")
                            print(f"✓ All files are valid")
                        else:
                            print(f"⚠ Created files but validation failed:")
                            for error in validation["errors"]:
                                print(f"  ERROR: {error}")
                            for warning in validation["warnings"]:
                                print(f"  WARNING: {warning}")
                    else:
                        build_result["error"] = "No team files were created"
                        print(f"✗ No team files were created")
                    
                    build_result["rounds"] = result.get("rounds")
                    
                finally:
                    # Always change back to original directory
                    os.chdir(original_dir)
                
            except Exception as e:
                build_result["error"] = str(e)
                print(f"✗ Failed: {e}")
                
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                
                # Ensure we're back in original directory
                os.chdir(original_dir)
            
            batch_results["builds"].append(build_result)
        
        # Save batch summary
        batch_results["end_time"] = datetime.now().isoformat()
        batch_results["total_tasks"] = len(task_dirs)
        batch_results["successful"] = sum(1 for b in batch_results["builds"] if b["success"])
        batch_results["failed"] = sum(1 for b in batch_results["builds"] if not b["success"])
        
        summary_path = tasks_dir / "build_batch_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(batch_results, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("BATCH BUILD SUMMARY")
        print("="*60)
        print(f"Total tasks: {batch_results['total_tasks']}")
        print(f"Successful builds: {batch_results['successful']}")
        print(f"Failed builds: {batch_results['failed']}")
        print(f"\nSummary saved to: {summary_path}")
        
        if batch_results["failed"] > 0:
            print("\nFailed builds:")
            for build in batch_results["builds"]:
                if not build["success"]:
                    print(f"  - {build['task_name']}: {build['error']}")
        
        # Show where teams were created
        if batch_results["successful"] > 0:
            print("\nSuccessfully built teams:")
            for build in batch_results["builds"]:
                if build["success"]:
                    print(f"  - {build['task_name']}: {build['output_dir']}")
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()