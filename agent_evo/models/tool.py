from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class ToolParameter:
    """Represents a parameter for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None

@dataclass
class Tool:
    """Represents a tool that agents can use."""
    id: str
    name: str
    description: str
    parameters: List[ToolParameter]
    returns: Dict[str, str]  # {"type": "string", "description": "..."}
    code: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in self.parameters
            ],
            "returns": self.returns,
            "code": self.code
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tool':
        """Create a Tool from dictionary representation."""
        parameters = [
            ToolParameter(
                name=p["name"],
                type=p["type"],
                description=p["description"],
                required=p.get("required", True),
                default=p.get("default")
            )
            for p in data.get("parameters", [])
        ]
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            parameters=parameters,
            returns=data["returns"],
            code=data["code"]
        )