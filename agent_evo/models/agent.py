from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Agent:
    """Represents an AI agent with tools and capabilities.
    
    All agents automatically have access to default tools (file_reader, file_writer).
    The tool_ids list specifies additional tools specific to this agent.
    """
    id: str
    name: str
    system_prompt: str
    tool_ids: List[str] = field(default_factory=list)  # Additional tools beyond defaults
    model: str = "gpt-4o"
    temperature: float = 1.0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "system_prompt": self.system_prompt,
            "tool_ids": self.tool_ids,
            "model": self.model,
            "temperature": self.temperature,
            "max_retries": self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """Create an Agent from dictionary representation."""
        return cls(
            id=data["id"],
            name=data["name"],
            system_prompt=data["system_prompt"],
            tool_ids=data.get("tool_ids", []),
            model=data.get("model", "gpt-5-mini"),
            temperature=data.get("temperature", 0.7),
            max_retries=data.get("max_retries", 3)
        )