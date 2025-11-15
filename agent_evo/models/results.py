from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ChatMessage:
    """A message in the team chat history."""
    agent_id: str
    agent_name: str
    role: str  # "user", "assistant", or "system"
    content: str

@dataclass
class ExecutionEntry:
    """An entry in the team execution history."""
    round: int
    agent_id: str
    agent_name: str
    task: str
    result: 'AgentResult'

@dataclass
class AgentResult:
    """Result from running a single agent."""
    agent_id: str
    agent_name: str
    final_response: str
    history: List[Dict[str, Any]]
    messages: List[Dict[str, str]]
    iterations: int
    delegation: Optional[Dict[str, str]] = None
    finished: bool = False

@dataclass
class TeamResult:
    """Result from running a team of agents."""
    team_id: str
    team_name: str
    execution_history: List[ExecutionEntry]
    chat_history: List[ChatMessage]
    agent_outputs: Dict[str, str]
    rounds: int