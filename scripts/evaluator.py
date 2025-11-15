import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import json
import sys
from pathlib import Path

from agent_evo.llm.client import OpenAIClient
from agent_evo.core.evaluator import TeamEvaluator


def main():
    parser = argparse.ArgumentParser(description="Evaluate agent team task completion")
    parser.add_argument("--task", required=True, help="Path to task text file")
    parser.add_argument("--result", required=True, help="Path to result JSON file from runner")
    parser.add_argument("--files", nargs="*", help="Additional files to include in evaluation")
    parser.add_argument("--model", default="gpt-4o", help="LLM model to use for judging")
    parser.add_argument("--output", help="Output file for evaluation results")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Load task
        print("Loading task...")
        with open(args.task, 'r') as f:
            task = f.read().strip()
        
        # Load result
        print("Loading execution result...")
        with open(args.result, 'r') as f:
            result = json.load(f)
        
        # Initialize LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        
        llm_client = OpenAIClient(api_key=api_key, model=args.model)
        
        # Create evaluator
        evaluator = TeamEvaluator(llm_client)
        
        # Run evaluation
        print("\nEvaluating task completion...")
        evaluation = evaluator.evaluate(
            task=task,
            result=result,
            additional_files=args.files,
            verbose=args.verbose
        )
        
        # Print results
        print("\n" + "="*60)
        print("EVALUATION RESULTS")
        print("="*60)
        print(f"\nTask: {task[:100]}...")
        print(f"\nTeam: {evaluation['result_summary']['team_name']}")
        print(f"Rounds: {evaluation['result_summary']['rounds']}")
        print(f"Agents: {evaluation['result_summary']['agents_involved']}")
        print(f"\nScore: {evaluation['score']}/10")
        print(f"\nReasoning:\n{evaluation['reasoning']}")
        
        if args.verbose:
            print(f"\n{'-'*60}")
            print("Full Judge Response:")
            print(evaluation['full_response'])
        
        # Save output if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(evaluation, f, indent=2, default=str)
            print(f"\nEvaluation saved to {args.output}")
    
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()