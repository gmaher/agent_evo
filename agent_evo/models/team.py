from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field

@dataclass
class TeamEdge:
    """Represents a directed edge in the team graph."""
    from_agent: str
    to_agent: str
    description: Optional[str] = None

@dataclass
class Team:
    """Represents a team of AI agents working together."""
    id: str
    name: str
    description: str
    agent_ids: List[str]
    edges: List[TeamEdge]
    entry_point: str  # ID of the agent that receives initial task
    
    def get_neighbors(self, agent_id: str) -> List[str]:
        """Get all agents that the given agent can communicate with."""
        return [edge.to_agent for edge in self.edges if edge.from_agent == agent_id]
    
    def validate(self) -> bool:
        """Validate team configuration."""
        if self.entry_point not in self.agent_ids:
            raise ValueError(f"Entry point {self.entry_point} not in agent list")
        
        # Check all edges reference valid agents
        for edge in self.edges:
            if edge.from_agent not in self.agent_ids:
                raise ValueError(f"Edge from_agent {edge.from_agent} not in agent list")
            if edge.to_agent not in self.agent_ids:
                raise ValueError(f"Edge to_agent {edge.to_agent} not in agent list")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert team to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_ids": self.agent_ids,
            "edges": [
                {
                    "from": edge.from_agent,
                    "to": edge.to_agent,
                    "description": edge.description
                }
                for edge in self.edges
            ],
            "entry_point": self.entry_point
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Team':
        """Create a Team from dictionary representation."""
        edges = [
            TeamEdge(
                from_agent=edge["from"],
                to_agent=edge["to"],
                description=edge.get("description")
            )
            for edge in data.get("edges", [])
        ]
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            agent_ids=data["agent_ids"],
            edges=edges,
            entry_point=data["entry_point"]
        )