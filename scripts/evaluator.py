import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from agent_evo.llm.client import OpenAIClient

class TaskEvaluator:
    """Evaluates agent team task completion using an LLM judge."""
    
    JUDGE_SYSTEM_PROMPT = """You are an expert evaluator assessing whether an AI agent team successfully completed their assigned task.

Your job is to:
1. Carefully read the original task requirements
2. Review the team's execution history and outputs
3. Check any relevant artifacts or files produced
4. Determine if the task was completed successfully
5. Provide a score from 0-10 and detailed reasoning

Scoring Guidelines:
- 10: Perfect completion, all requirements met excellently
- 8-9: Excellent completion, minor issues or areas for improvement
- 6-7: Good completion, task done but with notable gaps or errors
- 4-5: Partial completion, some requirements met but significant issues
- 2-3: Poor completion, major requirements missed
- 0-1: Failed, task not completed or severely incorrect

Consider:
- Did the team address all parts of the task?
- Are the outputs correct and complete?
- Was the approach reasonable and efficient?
- Were tools used appropriately?
- Were delegations between agents logical?
- Is the final deliverable usable?

IMPORTANT: Be strict but fair. A task is only "successful" if it truly meets the requirements.

Here are some examples:

---
EXAMPLE 1: SUCCESSFUL TASK

Task:
"Create a Python function that calculates the Fibonacci sequence up to n terms and save it to fib.py"

Execution History:
- Agent: CodeWriter
- Used tool: write_file(path="fib.py", content="def fibonacci(n):\\n    if n <= 0:\\n        return []\\n    elif n == 1:\\n        return [0]\\n    elif n == 2:\\n        return [0, 1]\\n    \\n    fib = [0, 1]\\n    for i in range(2, n):\\n        fib.append(fib[i-1] + fib[i-2])\\n    return fib")
- Result: File created successfully

Agent Output:
"I've created a Python function that calculates the Fibonacci sequence up to n terms. The function handles edge cases for n <= 0, n = 1, and n = 2, then uses iteration to compute the sequence efficiently. The code has been saved to fib.py."

Files:
fib.py exists and contains correct implementation

Evaluation:
Score: 10/10
Reasoning: Task completed perfectly. The agent created a correct Fibonacci function with proper edge case handling, saved it to the specified file, and provided clear documentation. All requirements met.

---
EXAMPLE 2: UNSUCCESSFUL TASK

Task:
"Research the current weather in Tokyo and London, compare them, and write a summary report to weather_report.txt"

Execution History:
- Agent: Researcher
- Used tool: search(query="Tokyo weather")
- Result: "Tokyo weather is typically mild..."
- Agent Output: "I found some general information about Tokyo's weather patterns."

Agent Output:
"Tokyo generally has a temperate climate with four distinct seasons. The weather varies throughout the year."

Files:
No weather_report.txt file created

Evaluation:
Score: 2/10
Reasoning: Task failed. The agent only searched for general Tokyo weather information, didn't get current weather data, didn't research London at all, didn't compare the cities, and never created the required report file. The output is generic and doesn't address the specific requirements.

---
EXAMPLE 3: PARTIAL SUCCESS

Task:
"Analyze the numbers in data.txt, calculate their mean and median, create a visualization, and save results to analysis_report.json"

Execution History:
- Agent: DataAnalyst
- Used tool: read_file(path="data.txt")
- Result: "10, 20, 30, 40, 50"
- Used tool: calculate(expression="(10+20+30+40+50)/5")
- Result: 30
- Agent: DataAnalyst
- Delegated to: Statistician
- Statistician Output: "The median of [10, 20, 30, 40, 50] is 30"
- Used tool: write_file(path="analysis_report.json", content='{"mean": 30, "median": 30}')

Agent Output:
"Analysis complete. Mean is 30, median is 30. Results saved to analysis_report.json"

Files:
analysis_report.json exists with correct mean and median

Evaluation:
Score: 6/10
Reasoning: Task partially completed. The agents correctly calculated mean and median and saved results to JSON. However, they failed to create any visualization as required. The team showed good delegation and tool use, but missed a key requirement, preventing full success.

---
EXAMPLE 4: SUCCESSFUL COMPLEX TASK

Task:
"Find information about Python 3.12 new features, summarize the top 3 features, have them reviewed by a senior developer, and create a blog post in blog_post.md"

Execution History:
- Agent: Researcher
- Used tool: search(query="Python 3.12 new features")
- Result: [detailed search results about Python 3.12]
- Agent: Researcher
- Delegated to: SeniorDev with summary of top 3 features
- Agent: SeniorDev  
- Output: "Reviewed the features. The summary is accurate. Top features are: 1) PEP 701 f-strings, 2) Per-interpreter GIL, 3) Improved error messages. Good choices."
- Delegated to: Writer
- Agent: Writer
- Used tool: write_file(path="blog_post.md", content=[blog post with intro, 3 features explained, conclusion])

Agent Output:
"Blog post created successfully with the top 3 Python 3.12 features reviewed and approved by the senior developer."

Files:
blog_post.md exists with well-structured content covering the 3 features

Evaluation:
Score: 9/10
Reasoning: Excellent task completion. The team successfully researched Python 3.12 features, identified top 3, got senior review as required, and created a proper blog post. The delegation flow was logical and efficient. Minor point deduction only because the blog post could have included code examples to be perfect, but all core requirements were met.

---

Now evaluate the following task:"""

    def __init__(self, llm_client: OpenAIClient):
        self.llm_client = llm_client
    
    def evaluate(self, 
                 task: str,
                 result: Dict[str, Any],
                 additional_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Evaluate if a team successfully completed their task.
        
        Args:
            task: The original task description
            result: The execution result from TeamRunner
            additional_files: List of file paths to include in evaluation
        
        Returns:
            Dictionary with score, reasoning, and evaluation details
        """
        # Build the evaluation prompt
        prompt = self._build_evaluation_prompt(task, result, additional_files)
        
        # Get judge evaluation
        messages = [
            {"role": "system", "content": self.JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_client.generate(
            messages=messages,
            temperature=0.3  # Lower temperature for more consistent evaluation
        )
        
        # Parse the response
        score, reasoning = self._parse_judge_response(response)
        
        return {
            "task": task,
            "score": score,
            "reasoning": reasoning,
            "full_response": response,
            "result_summary": {
                "team_name": result.get("team_name"),
                "rounds": result.get("rounds"),
                "agents_involved": len(result.get("agent_outputs", {}))
            }
        }
    
    def _build_evaluation_prompt(self, 
                                  task: str, 
                                  result: Dict[str, Any],
                                  additional_files: Optional[List[str]] = None) -> str:
        """Build the evaluation prompt for the judge."""
        prompt_parts = []
        
        # Add the task
        prompt_parts.append("=== TASK ===")
        prompt_parts.append(task)
        prompt_parts.append("")
        
        # Add execution summary
        prompt_parts.append("=== EXECUTION SUMMARY ===")
        prompt_parts.append(f"Team: {result.get('team_name', 'Unknown')}")
        prompt_parts.append(f"Rounds: {result.get('rounds', 0)}")
        prompt_parts.append(f"Agents involved: {len(result.get('agent_outputs', {}))}")
        prompt_parts.append("")
        
        # Add execution history
        prompt_parts.append("=== EXECUTION HISTORY ===")
        for entry in result.get("execution_history", []):
            agent_name = entry.get("agent_name", "Unknown")
            round_num = entry.get("round", 0)
            task_given = entry.get("task", "")
            
            prompt_parts.append(f"\nRound {round_num}: {agent_name}")
            prompt_parts.append(f"Task: {task_given[:200]}..." if len(task_given) > 200 else f"Task: {task_given}")
            
            # Add tool usage
            agent_result = entry.get("result", {})
            history = agent_result.get("history", [])
            for iteration in history:
                tool_calls = iteration.get("tool_calls", [])
                if tool_calls:
                    prompt_parts.append(f"  Tools used: {', '.join([tc['tool'] for tc in tool_calls])}")
            
            # Add delegation
            delegation = agent_result.get("delegation")
            if delegation:
                prompt_parts.append(f"  Delegated to: {delegation['to_agent']}")
        
        prompt_parts.append("")
        
        # Add agent outputs
        prompt_parts.append("=== AGENT OUTPUTS ===")
        for agent_id, output in result.get("agent_outputs", {}).items():
            # Find agent name
            agent_name = agent_id
            for entry in result.get("execution_history", []):
                if entry.get("agent_id") == agent_id:
                    agent_name = entry.get("agent_name", agent_id)
                    break
            
            prompt_parts.append(f"\n{agent_name}:")
            prompt_parts.append(output[:500] + "..." if len(output) > 500 else output)
        
        prompt_parts.append("")
        
        # Add additional files if provided
        if additional_files:
            prompt_parts.append("=== ADDITIONAL FILES ===")
            for file_path in additional_files:
                if os.path.exists(file_path):
                    prompt_parts.append(f"\nFile: {file_path}")
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            prompt_parts.append(content[:1000] + "..." if len(content) > 1000 else content)
                    except Exception as e:
                        prompt_parts.append(f"Error reading file: {e}")
                else:
                    prompt_parts.append(f"\nFile: {file_path} (NOT FOUND)")
            prompt_parts.append("")
        
        # Add evaluation instruction
        prompt_parts.append("=== YOUR EVALUATION ===")
        prompt_parts.append("Based on the task requirements and execution details above, provide:")
        prompt_parts.append("1. A score from 0-10")
        prompt_parts.append("2. Detailed reasoning for your score")
        prompt_parts.append("3. What was done well and what was missing")
        prompt_parts.append("")
        prompt_parts.append("Format your response as:")
        prompt_parts.append("Score: X/10")
        prompt_parts.append("Reasoning: [your detailed analysis]")
        
        return "\n".join(prompt_parts)
    
    def _parse_judge_response(self, response: str) -> tuple[float, str]:
        """Parse score and reasoning from judge response."""
        import re
        
        # Try to find score
        score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)\s*/\s*10', response, re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))
        else:
            # Try alternative formats
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', response)
            score = float(score_match.group(1)) if score_match else 5.0
        
        # Extract reasoning
        reasoning_match = re.search(r'Reasoning:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else response
        
        return score, reasoning


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
        evaluator = TaskEvaluator(llm_client)
        
        # Run evaluation
        print("\nEvaluating task completion...")
        evaluation = evaluator.evaluate(
            task=task,
            result=result,
            additional_files=args.files
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