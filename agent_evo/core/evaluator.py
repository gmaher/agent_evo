import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from agent_evo.llm.client import LLMClient
from agent_evo.prompts.judge import JUDGE_SYSTEM_PROMPT


class TeamEvaluator:
    """Evaluates agent team task completion using an LLM judge."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the evaluator.
        
        Args:
            llm_client: LLM client to use for evaluation
        """
        self.llm_client = llm_client
    
    def evaluate(self, 
                 task: str,
                 result: Dict[str, Any],
                 additional_files: Optional[List[str]] = None,
                 verbose: bool = False) -> Dict[str, Any]:
        """
        Evaluate if a team successfully completed their task.
        
        Args:
            task: The original task description
            result: The execution result from TeamRunner
            additional_files: List of file paths to include in evaluation
            verbose: Whether to include verbose output
        
        Returns:
            Dictionary with score, reasoning, and evaluation details
        """
        # Build the evaluation prompt
        prompt = self._build_evaluation_prompt(task, result, additional_files)
        
        if verbose:
            print(f"\n{'='*60}")
            print("EVALUATION PROMPT")
            print(f"{'='*60}")
            print(prompt)
        
        # Get judge evaluation
        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_client.generate(
            messages=messages,
            temperature=0.3  # Lower temperature for more consistent evaluation
        )
        
        if verbose:
            print(f"\n{'='*60}")
            print("JUDGE RESPONSE")
            print(f"{'='*60}")
            print(response)
        
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