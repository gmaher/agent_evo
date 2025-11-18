"""Database document models for MongoDB collections."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class FileDoc(BaseModel):
    """File within a project."""
    filename: str
    content: str


class ProjectDoc(BaseModel):
    """Project document in MongoDB."""
    id: int
    username: str
    name: str
    description: str
    files: List[FileDoc] = []


class AgentDoc(BaseModel):
    """Agent document in MongoDB."""
    id: str
    username: str
    name: str
    system_prompt: str
    tool_names: List[str] = []
    model: str = "gpt-4o"
    temperature: float = 1.0
    max_retries: int = 3


class TeamEdgeDoc(BaseModel):
    """Team edge document."""
    from_agent: Optional[str] = Field(None, alias="from")
    to_agent: Optional[str] = Field(None, alias="to")
    description: Optional[str] = None
    
    class Config:
        populate_by_name = True


class TeamDoc(BaseModel):
    """Team document in MongoDB."""
    id: str
    username: str
    name: str
    description: str
    agent_ids: List[str]
    edges: List[TeamEdgeDoc]
    entry_point: str


class RunDoc(BaseModel):
    """Run document in MongoDB."""
    id: str
    username: str
    team_id: str
    project_id: int
    run_name: str
    timestamp: str
    status: str  # "running", "completed", "failed"
    result: Dict[str, Any] = {}
    score: Optional[float] = None
    score_reasoning: Optional[str] = None


class EvolutionDoc(BaseModel):
    """Evolution document in MongoDB."""
    id: str
    username: str
    project_id: int
    team_ids: List[str] = []
    run_ids: List[str] = []
    max_rounds: int
    K: int
    timestamp: str
    status: str  # "generating", "completed", "failed"
    generation: int = 0