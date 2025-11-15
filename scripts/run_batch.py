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
        help="Directory containing subdirectories with task.txt files"
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing tools.json, agents.json, and team.json"
    )
    parser.add_argument("--model", default="gpt-4o", help="LLM model to use")
    parser.add_argument("--max-rounds", type=int, default=10, help="Maximum rounds per task")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        tasks_dir = Path(args.tasks_dir)
        
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
        
        print(f"Found {len(task_dirs)} tasks to process")
        print("="*60)
        
        # Store results
        batch_results = {
            "start_time": datetime.now().isoformat(),
            "tasks_dir": str(tasks_dir),
            "input_dir": args.input_dir,
            "model": args.model,
            "tasks": []
        }
        
        # Process each task
        for i, task_dir in enumerate(task_dirs, 1):
            task_file = task_dir / "task.txt"
            
            print(f"\n[{i}/{len(task_dirs)}] Processing: {task_dir.name}")
            print("-"*60)
            
            task_result = {
                "task_dir": str(task_dir),
                "task_name": task_dir.name,
                "success": False,
                "error": None
            }
            
            try:
                # Initialize app with subdirectory as output
                app = AgentEvoApp(
                    model=args.model,
                    output_dir=str(task_dir)
                )
                
                # Change to task directory
                original_dir = os.getcwd()
                os.chdir(task_dir)
                
                if args.verbose:
                    print(f"Working directory: {task_dir.absolute()}")
                
                try:
                    # Run team
                    result = app.run_from_directory(
                        team_dir=args.input_dir,
                        task_path=str(task_file),
                        max_rounds=args.max_rounds,
                        verbose=args.verbose
                    )
                    
                    task_result["success"] = True
                    task_result["rounds"] = result.get("rounds")
                    task_result["agents_involved"] = len(result.get("agent_outputs", {}))
                    
                    print(f"✓ Completed in {result['rounds']} rounds")
                    
                finally:
                    # Always change back to original directory
                    os.chdir(original_dir)
                
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