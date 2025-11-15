"""One-shot judge that evaluates team performance in a single LLM call."""

import re
from typing import Dict, Any, Optional

from agent_evo.llm.client import LLMClient
from agent_evo.prompts.judge import JUDGE_SYSTEM_PROMPT
from agent_evo.models.results import TeamResult


class OneShotJudge:
    """Evaluate team performance in a single LLM call."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the judge.
        
        Args:
            llm_client: LLM client to use for evaluation
        """
        self.llm_client = llm_client
    
    def judge_team(
        self,
        task: str,
        team_result: TeamResult,
        files: Dict[str, str],
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Evaluate how well a team completed a task.
        
        Args:
            task: The original task description
            team_result: Result from team execution
            files: Dictionary of filename -> content for output files
            temperature: LLM temperature (lower for more consistent scoring)
        
        Returns:
            Dictionary with 'score', 'reasoning', and 'raw_response' keys
        
        Raises:
            ValueError: If score cannot be parsed
            RuntimeError: If LLM call fails
        """
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(task, team_result, files)
        
        # Call LLM
        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_client.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        
        # Parse score and reasoning
        score, reasoning = self._parse_evaluation(response)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "raw_response": response
        }
    
    def _build_evaluation_prompt(
        self,
        task: str,
        team_result: TeamResult,
        files: Dict[str, str]
    ) -> str:
        """Build the evaluation prompt with all context."""
        
        # Format execution history
        execution_summary = self._format_execution_history(team_result)
        
        # Format files
        files_summary = self._format_files(files)
        
        # Format agent outputs
        outputs_summary = self._format_agent_outputs(team_result.agent_outputs)
        
        prompt = f"""
=== TASK ===
{task}

=== EXECUTION HISTORY ===
{execution_summary}

=== AGENT OUTPUTS ===
{outputs_summary}

=== OUTPUT FILES ===
{files_summary}

Please evaluate whether the team successfully completed the task. Provide a score from 0-10 and detailed reasoning for your evaluation.

Format your response as:

Score: X/10
Reasoning: [Your detailed evaluation explaining the score]
"""
        
        return prompt.strip()
    
    def _format_execution_history(self, team_result: TeamResult) -> str:
        """Format execution history for the prompt."""
        lines = []
        
        for entry in team_result.execution_history:
            lines.append(f"\nRound {entry.round}: {entry.agent_name}")
            lines.append(f"Task: {entry.task[:200]}...")
            
            # Add tool usage if any
            tool_calls = []
            for hist in entry.result.history:
                if hist.get("tool_calls"):
                    for tc in hist["tool_calls"]:
                        tool_calls.append(f"  - {tc['tool']}({tc.get('arguments', {})})")
            
            if tool_calls:
                lines.append("Tools used:")
                lines.extend(tool_calls)
            
            # Add delegation if any
            if entry.result.delegation:
                delegation = entry.result.delegation
                lines.append(f"Delegated to: {delegation['to_agent']}")
            
            lines.append(f"Iterations: {entry.result.iterations}")
            lines.append(f"Finished: {entry.result.finished}")
        
        return "\n".join(lines)
    
    def _format_files(self, files: Dict[str, str]) -> str:
        """Format output files for the prompt."""
        if not files:
            return "No files created"
        
        lines = []
        for filename, content in files.items():
            lines.append(f"\n**{filename}**")
            # Truncate large files
            if len(content) > 1000:
                lines.append(f"```\n{content[:500]}\n\n... [truncated {len(content) - 1000} characters] ...\n\n{content[-500:]}\n```")
            else:
                lines.append(f"```\n{content}\n```")
        
        return "\n".join(lines)
    
    def _format_agent_outputs(self, agent_outputs: Dict[str, str]) -> str:
        """Format agent outputs for the prompt."""
        lines = []
        
        for agent_id, output in agent_outputs.items():
            lines.append(f"\n**{agent_id}**:")
            # Truncate long outputs
            if len(output) > 500:
                lines.append(f"{output[:250]}...[truncated]...{output[-250:]}")
            else:
                lines.append(output)
        
        return "\n".join(lines)
    
    def _parse_evaluation(self, response: str) -> tuple[float, str]:
        """
        Parse score and reasoning from judge response.
        
        Args:
            response: Raw LLM response
        
        Returns:
            Tuple of (score, reasoning)
        
        Raises:
            ValueError: If score cannot be parsed
        """
        # Try multiple patterns for score
        patterns = [
            r'Score:\s*(\d+(?:\.\d+)?)\s*/\s*10',  # "Score: 8/10"
            r'Score:\s*(\d+(?:\.\d+)?)/10',         # "Score: 8/10" (no spaces)
            r'Score:\s*(\d+(?:\.\d+)?)',            # "Score: 8"
            r'(\d+(?:\.\d+)?)\s*/\s*10',            # "8/10"
        ]
        
        score = None
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                break
        
        if score is None:
            raise ValueError(
                f"Could not parse score from response. "
                f"Response: {response[:200]}"
            )
        
        # Validate score range
        if not (0 <= score <= 10):
            raise ValueError(f"Score {score} out of valid range 0-10")
        
        # Extract reasoning
        reasoning_match = re.search(
            r'Reasoning:\s*(.+)',
            response,
            re.IGNORECASE | re.DOTALL
        )
        
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        else:
            # If no explicit reasoning section, use everything after score
            reasoning = response.split('\n', 1)[-1].strip()
        
        return score, reasoning