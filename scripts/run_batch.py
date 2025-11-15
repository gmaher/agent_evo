import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

from agent_evo.core.app import AgentEvoApp


def main():
    parser = argparse.ArgumentParser(
        description="Run agent team on multiple tasks in batch"
    )
    parser.add_argument(
        "--tasks-dir",
        required=True,
        help="Directory containing subdirectories with task.txt files and team/ folders"
    )
    parser.add_argument("--model", default="gpt-4o", help="LLM model to use")
    parser.add_argument("--max-rounds", type=int, default=10, help="Maximum rounds per task")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--load-context",
        action="store_true",
        help="Load all files from task directory as initial context"
    )
    
    args = parser.parse_args()
    
    try:
        tasks_dir = Path(args.tasks_dir).absolute()
        
        if not tasks_dir.exists():
            raise FileNotFoundError(f"Tasks directory not found: {tasks_dir}")
    
        
        # Find all subdirectories with task.txt and team/ folder
        task_dirs = []
        for subdir in tasks_dir.iterdir():
            if subdir.is_dir():
                task_file = subdir / "task.txt"
                team_dir = subdir / "team"
                if task_file.exists() and team_dir.exists() and team_dir.is_dir():
                    task_dirs.append(subdir)
        
        if not task_dirs:
            print(f"No subdirectories with task.txt and team/ folder found in {tasks_dir}")
            return
        
        print(f"Found {len(task_dirs)} tasks to process")
        print("="*60)
        
        # Store results
        batch_results = {
            "start_time": datetime.now().isoformat(),
            "tasks_dir": str(tasks_dir),
            "model": args.model,
            "tasks": []
        }
        
        # Process each task
        for i, task_dir in enumerate(task_dirs, 1):
            task_file = task_dir / "task.txt"
            team_dir = task_dir / "team"
            output_dir = task_dir / "output"
            
            print(f"\n[{i}/{len(task_dirs)}] Processing: {task_dir.name}")
            print("-"*60)
            
            task_result = {
                "task_dir": str(task_dir),
                "task_name": task_dir.name,
                "team_dir": str(team_dir),
                "output_dir": str(output_dir),
                "success": False,
                "error": None
            }
            
            try:
                # Initialize app (creates fresh in-memory filesystem)
                app = AgentEvoApp(model=args.model)
                
                # Determine context directory and exclude patterns
                context_dir = None
                exclude_patterns = None
                
                if args.load_context:
                    context_dir = str(task_dir)
                    # Exclude task.txt, team/ folder, and output/ folder
                    exclude_patterns = ["task.txt", "team/", "output/"]
                    
                    if args.verbose:
                        print(f"Loading context from: {context_dir}")
                
                # Run team
                result = app.run_from_directory(
                    team_dir=str(team_dir),
                    task_path=str(task_file),
                    max_rounds=args.max_rounds,
                    verbose=args.verbose,
                    context_dir=context_dir,
                    exclude_patterns=exclude_patterns
                )
                
                # Save files from in-memory filesystem to disk
                files_saved = app.save_filesystem_to_disk(str(output_dir))
                
                task_result["success"] = True
                task_result["rounds"] = result.get("rounds")
                task_result["agents_involved"] = len(result.get("agent_outputs", {}))
                task_result["files_saved"] = files_saved
                
                print(f"✓ Completed in {result['rounds']} rounds")
                print(f"✓ Saved {files_saved} files to {output_dir}")
                
            except Exception as e:
                task_result["error"] = str(e)
                print(f"✗ Failed: {e}")
                
                if args.verbose:
                    import traceback
                    traceback.print_exc()
            
            batch_results["tasks"].append(task_result)
        
        
        # Save batch summary
        batch_results["end_time"] = datetime.now().isoformat()
        batch_results["total_tasks"] = len(task_dirs)
        batch_results["successful"] = sum(1 for t in batch_results["tasks"] if t["success"])
        batch_results["failed"] = sum(1 for t in batch_results["tasks"] if not t["success"])
        
        summary_path = tasks_dir / "batch_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(batch_results, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("BATCH EXECUTION SUMMARY")
        print("="*60)
        print(f"Total tasks: {batch_results['total_tasks']}")
        print(f"Successful: {batch_results['successful']}")
        print(f"Failed: {batch_results['failed']}")
        print(f"\nSummary saved to: {summary_path}")
        
        if batch_results["failed"] > 0:
            print("\nFailed tasks:")
            for task in batch_results["tasks"]:
                if not task["success"]:
                    print(f"  - {task['task_name']}: {task['error']}")
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()