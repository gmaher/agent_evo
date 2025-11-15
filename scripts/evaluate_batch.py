import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from agent_evo.llm.client import OpenAIClient
from agent_evo.core.evaluator import TeamEvaluator


def find_files_to_evaluate(task_dir: Path) -> list[str]:
    """
    Find all files to include in evaluation.
    Includes files in task_dir and files 1 subdirectory deep.
    Excludes task.txt, output.json, and evaluation files.
    """
    excluded_files = {"task.txt", "output.json", "evaluation.json", "batch_summary.json"}
    files = []
    
    # Get files in the task directory
    for item in task_dir.iterdir():
        if item.is_file() and item.name not in excluded_files:
            files.append(str(item))
        elif item.is_dir():
            # Get files 1 level deeper
            for subitem in item.iterdir():
                if subitem.is_file():
                    files.append(str(subitem))
    
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate agent team results on multiple tasks in batch"
    )
    parser.add_argument(
        "--tasks-dir",
        required=True,
        help="Directory containing subdirectories with task.txt and output.json files"
    )
    parser.add_argument("--model", default="gpt-4o", help="LLM model to use for judging")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        tasks_dir = Path(args.tasks_dir)
        
        if not tasks_dir.exists():
            raise FileNotFoundError(f"Tasks directory not found: {tasks_dir}")
        
        # Find all subdirectories with task.txt and output.json
        task_dirs = []
        for subdir in tasks_dir.iterdir():
            if subdir.is_dir():
                task_file = subdir / "task.txt"
                output_file = subdir / "output.json"
                if task_file.exists() and output_file.exists():
                    task_dirs.append(subdir)
        
        if not task_dirs:
            print(f"No subdirectories with task.txt and output.json found in {tasks_dir}")
            return
        
        print(f"Found {len(task_dirs)} tasks to evaluate")
        print("="*60)
        
        # Initialize LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        
        llm_client = OpenAIClient(api_key=api_key, model=args.model)
        evaluator = TeamEvaluator(llm_client)
        
        # Store results
        batch_results = {
            "start_time": datetime.now().isoformat(),
            "tasks_dir": str(tasks_dir),
            "model": args.model,
            "evaluations": []
        }
        
        # Process each task
        for i, task_dir in enumerate(task_dirs, 1):
            task_file = task_dir / "task.txt"
            output_file = task_dir / "output.json"
            
            print(f"\n[{i}/{len(task_dirs)}] Evaluating: {task_dir.name}")
            print("-"*60)
            
            eval_result = {
                "task_dir": str(task_dir),
                "task_name": task_dir.name,
                "success": False,
                "score": None,
                "error": None
            }
            
            try:
                # Load task
                with open(task_file, 'r') as f:
                    task = f.read().strip()
                
                # Load result
                with open(output_file, 'r') as f:
                    result = json.load(f)
                
                # Find files to include
                additional_files = find_files_to_evaluate(task_dir)
                
                if args.verbose:
                    print(f"Task: {task[:100]}...")
                    print(f"Found {len(additional_files)} additional files to include")
                    for file in additional_files:
                        print(f"  - {file}")
                
                # Run evaluation
                evaluation = evaluator.evaluate(
                    task=task,
                    result=result,
                    additional_files=additional_files if additional_files else None,
                    verbose=args.verbose
                )
                
                # Save evaluation to subdirectory
                eval_path = task_dir / "evaluation.json"
                with open(eval_path, 'w') as f:
                    json.dump(evaluation, f, indent=2, default=str)
                
                eval_result["success"] = True
                eval_result["score"] = evaluation["score"]
                eval_result["reasoning"] = evaluation["reasoning"]
                eval_result["team_name"] = evaluation["result_summary"]["team_name"]
                eval_result["rounds"] = evaluation["result_summary"]["rounds"]
                eval_result["files_evaluated"] = len(additional_files)
                
                print(f"✓ Score: {evaluation['score']}/10")
                print(f"  Saved to: {eval_path}")
                
            except Exception as e:
                eval_result["error"] = str(e)
                print(f"✗ Failed: {e}")
                
                if args.verbose:
                    import traceback
                    traceback.print_exc()
            
            batch_results["evaluations"].append(eval_result)
        
        # Calculate statistics
        batch_results["end_time"] = datetime.now().isoformat()
        batch_results["total_tasks"] = len(task_dirs)
        batch_results["successful"] = sum(1 for e in batch_results["evaluations"] if e["success"])
        batch_results["failed"] = sum(1 for e in batch_results["evaluations"] if not e["success"])
        
        scores = [e["score"] for e in batch_results["evaluations"] if e["score"] is not None]
        if scores:
            batch_results["average_score"] = sum(scores) / len(scores)
            batch_results["min_score"] = min(scores)
            batch_results["max_score"] = max(scores)
        
        # Save batch summary
        summary_path = tasks_dir / "evaluation_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(batch_results, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("BATCH EVALUATION SUMMARY")
        print("="*60)
        print(f"Total tasks: {batch_results['total_tasks']}")
        print(f"Successfully evaluated: {batch_results['successful']}")
        print(f"Failed: {batch_results['failed']}")
        
        if scores:
            print(f"\nScore Statistics:")
            print(f"  Average: {batch_results['average_score']:.2f}/10")
            print(f"  Min: {batch_results['min_score']}/10")
            print(f"  Max: {batch_results['max_score']}/10")
            
            # Show individual scores
            print(f"\nIndividual Scores:")
            for eval_result in batch_results["evaluations"]:
                if eval_result["success"]:
                    print(f"  {eval_result['task_name']}: {eval_result['score']}/10")
        
        print(f"\nSummary saved to: {summary_path}")
        
        if batch_results["failed"] > 0:
            print("\nFailed evaluations:")
            for eval_result in batch_results["evaluations"]:
                if not eval_result["success"]:
                    print(f"  - {eval_result['task_name']}: {eval_result['error']}")
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()