"""Refactored FastAPI server - thin HTTP layer over orchestration API."""

import sys
import os

sys.path.append(os.path.abspath("../.."))

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import database models
from agent_evo.models.database import (
    FileDoc as File,
    ProjectDoc as Project,
    AgentDoc as Agent,
    TeamEdgeDoc as TeamEdge,
    TeamDoc as Team,
    RunDoc as Run,
    EvolutionDoc as Evolution
)

# Import orchestration and repository
from agent_evo.services import orchestration, repository

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================
# Pydantic Models (only specialized ones)
# ==================

class ProjectCreate(BaseModel):
    name: str
    description: str
    files: List[File] = []

class AgentCreate(BaseModel):
    name: str
    system_prompt: str
    tool_names: List[str] = []
    model: str = "gpt-4o"
    temperature: float = 1.0
    max_retries: int = 3

class TeamCreate(BaseModel):
    name: str
    description: str
    agent_ids: List[str]
    edges: List[TeamEdge]
    entry_point: str

class TeamWithAgents(BaseModel):
    id: str
    username: str
    name: str
    description: str
    agent_ids: List[str]
    edges: List[TeamEdge]
    entry_point: str
    agents: List[Agent]

class RunCreate(BaseModel):
    team_id: str
    project_id: int
    run_name: str = "Untitled Run"

class EvolutionWithRuns(BaseModel):
    id: str
    username: str
    project_id: int
    team_ids: List[str]
    run_ids: List[str] = []
    max_rounds: int
    K: int
    timestamp: str
    status: str
    generation: int = 0
    runs: List[Run] = []

class EvolutionCreate(BaseModel):
    project_id: int
    max_rounds: int = 10
    K: int = 5

# ==================
# Project Routes
# ==================

@app.get("/projects/{username}", response_model=List[Project])
def get_projects(username: str):
    """Get all projects for a user."""
    docs = repository.list_projects(username)
    return docs

@app.get("/projects/{username}/{project_id}", response_model=Project)
def get_project(username: str, project_id: int):
    """Get a specific project."""
    doc = repository.get_project(username, project_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return doc

@app.post("/projects/{username}", response_model=Project)
def create_project(username: str, project: ProjectCreate):
    """Create a new project."""
    files = [f.model_dump() for f in project.files]
    
    doc = repository.create_project(
        username=username,
        name=project.name,
        description=project.description,
        files=files
    )
    
    return doc

@app.put("/projects/{username}/{project_id}", response_model=Project)
def update_project(username: str, project_id: int, project: ProjectCreate):
    """Update a project."""
    files = [f.model_dump() for f in project.files]
    
    success = repository.update_project(
        username=username,
        project_id=project_id,
        name=project.name,
        description=project.description,
        files=files
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Return updated project
    updated = repository.get_project(username, project_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found after update")
    
    return updated

@app.delete("/projects/{username}/{project_id}")
def delete_project(username: str, project_id: int):
    """Delete a project."""
    success = repository.delete_project(username, project_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project deleted successfully"}

# ==================
# Agent Routes
# ==================

@app.get("/agents/{username}", response_model=List[Agent])
def get_agents(username: str):
    """Get all agents for a user."""
    return repository.list_agents(username)

@app.post("/agents/{username}", response_model=Agent)
def create_agent(username: str, agent: AgentCreate):
    """Create a new agent."""
    import uuid
    
    agent_doc = {
        "id": str(uuid.uuid4()),
        "name": agent.name,
        "system_prompt": agent.system_prompt,
        "tool_names": agent.tool_names,
        "model": agent.model,
        "temperature": agent.temperature,
        "max_retries": agent.max_retries,
    }
    
    return repository.create_agent(username, agent_doc)

@app.get("/agents/{username}/{agent_id}", response_model=Agent)
def get_agent(username: str, agent_id: str):
    """Get a specific agent."""
    doc = repository.get_agent(username, agent_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return doc

@app.put("/agents/{username}/{agent_id}", response_model=Agent)
def update_agent(username: str, agent_id: str, agent: AgentCreate):
    """Update an agent."""
    agent_doc = {
        "name": agent.name,
        "system_prompt": agent.system_prompt,
        "tool_names": agent.tool_names,
        "model": agent.model,
        "temperature": agent.temperature,
        "max_retries": agent.max_retries,
    }
    
    success = repository.update_agent(username, agent_id, agent_doc)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Return updated agent
    updated = repository.get_agent(username, agent_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found after update")
    
    return updated

@app.delete("/agents/{username}/{agent_id}")
def delete_agent(username: str, agent_id: str):
    """Delete an agent."""
    success = repository.delete_agent(username, agent_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": "Agent deleted successfully"}

# ==================
# Team Routes
# ==================

@app.get("/teams/{username}", response_model=List[Team])
def get_teams(username: str):
    """Get all teams for a user."""
    return repository.list_teams(username)

@app.get("/teams/{username}/{team_id}", response_model=TeamWithAgents)
def get_team_with_agents(username: str, team_id: str):
    """Get a team with all its agents."""
    team_doc = repository.get_team(username, team_id)
    
    if not team_doc:
        raise HTTPException(status_code=404, detail="Team not found")
    
    agent_ids = team_doc.agent_ids
    agent_docs = repository.get_agents_by_ids(username, agent_ids)
    
    return TeamWithAgents(
        id=team_doc.id,
        username=team_doc.username,
        name=team_doc.name,
        description=team_doc.description,
        agent_ids=agent_ids,
        edges=team_doc.edges,
        entry_point=team_doc.entry_point,
        agents=agent_docs
    )

@app.post("/teams/{username}", response_model=Team)
def create_team(username: str, team: TeamCreate):
    """Create a new team."""
    import uuid
    
    # Validate agents exist
    agent_docs = repository.get_agents_by_ids(username, team.agent_ids)
    
    if len(agent_docs) != len(team.agent_ids):
        raise HTTPException(status_code=400, detail="One or more agent IDs not found")
    
    team_doc = {
        "id": str(uuid.uuid4()),
        "name": team.name,
        "description": team.description,
        "agent_ids": team.agent_ids,
        "edges": [edge.model_dump(by_alias=True) for edge in team.edges],
        "entry_point": team.entry_point,
    }
    
    return repository.create_team(username, team_doc)

@app.put("/teams/{username}/{team_id}", response_model=Team)
def update_team(username: str, team_id: str, team: TeamCreate):
    """Update a team."""
    team_doc = {
        "name": team.name,
        "description": team.description,
        "agent_ids": team.agent_ids,
        "edges": [edge.model_dump(by_alias=True) for edge in team.edges],
        "entry_point": team.entry_point,
    }
    
    success = repository.update_team(username, team_id, team_doc)
    
    if not success:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Return updated team
    updated = repository.get_team(username, team_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Team not found after update")
    
    return updated

@app.delete("/teams/{username}/{team_id}")
def delete_team(username: str, team_id: str):
    """Delete a team."""
    success = repository.delete_team(username, team_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"message": "Team deleted successfully"}

# ==================
# Run Routes
# ==================

@app.post("/runs/{username}", response_model=Run)
def create_run(username: str, run_request: RunCreate):
    """Create and execute a new run."""
    try:
        run_doc = orchestration.run_team_on_project(
            username=username,
            project_id=run_request.project_id,
            team_id=run_request.team_id,
            run_name=run_request.run_name,
            max_rounds=10
        )
        
        return run_doc
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Run failed: {str(e)}")

@app.get("/runs/{username}", response_model=List[Run])
def get_runs(
    username: str,
    project_id: Optional[int] = None,
    team_id: Optional[str] = None
):
    """Get all runs for a user."""
    return repository.list_runs(username, project_id=project_id, team_id=team_id)

@app.get("/runs/{username}/{run_id}", response_model=Run)
def get_run(username: str, run_id: str):
    """Get a specific run."""
    doc = repository.get_run(username, run_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return doc

@app.delete("/runs/{username}/{run_id}")
def delete_run(username: str, run_id: str):
    """Delete a run."""
    success = repository.delete_run(username, run_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {"message": "Run deleted successfully"}

# ==================
# Evolution Routes
# ==================

@app.get("/evolutions/{username}", response_model=List[Evolution])
def get_evolutions(username: str, project_id: Optional[int] = None):
    """Get all evolutions for a user."""
    return repository.list_evolutions(username, project_id=project_id)

@app.get("/evolutions/{username}/{evolution_id}", response_model=EvolutionWithRuns)
def get_evolution(username: str, evolution_id: str):
    """Get a specific evolution with its runs."""
    doc = repository.get_evolution(username, evolution_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Evolution not found")
    
    # Fetch all runs for this evolution
    run_ids = doc.run_ids
    runs = []
    if run_ids:
        run_docs = [repository.get_run(username, rid) for rid in run_ids]
        runs = [run_doc for run_doc in run_docs if run_doc]
    
    return EvolutionWithRuns(
        id=doc.id,
        username=doc.username,
        project_id=doc.project_id,
        team_ids=doc.team_ids,
        run_ids=doc.run_ids,
        max_rounds=doc.max_rounds,
        K=doc.K,
        timestamp=doc.timestamp,
        status=doc.status,
        generation=doc.generation,
        runs=runs
    )

@app.post("/evolutions/{username}", response_model=Evolution)
def create_evolution(username: str, evolution_request: EvolutionCreate):
    """Create and run an evolution."""
    try:
        evolution_doc = orchestration.create_evolution_and_run_generations(
            username=username,
            project_id=evolution_request.project_id,
            max_rounds=evolution_request.max_rounds,
            K=evolution_request.K
        )
        
        return evolution_doc
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create evolution: {str(e)}")

@app.delete("/evolutions/{username}/{evolution_id}")
def delete_evolution(username: str, evolution_id: str):
    """Delete an evolution."""
    success = repository.delete_evolution(username, evolution_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Evolution not found")
    
    return {"message": "Evolution deleted successfully"}