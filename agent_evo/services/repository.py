"""Database access layer for agent_evo - fully typed."""

from typing import List, Optional
from pymongo import MongoClient

from agent_evo.models.database import (
    ProjectDoc,
    AgentDoc,
    TeamDoc,
    RunDoc,
    EvolutionDoc,
    FileDoc,
    TeamEdgeDoc
)

# Initialize MongoDB client
MONGO_URI = "mongodb://localhost:27017"
_client = None
_db = None

def get_db():
    """Get or create database connection."""
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db = _client["evo_agents"]
    return _db

# Collection accessors (unchanged)
def get_projects_collection():
    return get_db()["projects"]

def get_agents_collection():
    return get_db()["agents"]

def get_teams_collection():
    return get_db()["teams"]

def get_runs_collection():
    return get_db()["runs"]

def get_evolutions_collection():
    return get_db()["evolutions"]


# ==================
# Project Operations
# ==================

def get_project(username: str, project_id: int) -> Optional[ProjectDoc]:
    """Get a project by ID."""
    doc = get_projects_collection().find_one({
        "username": username,
        "id": project_id
    })
    
    if not doc:
        return None
    
    doc.pop("_id", None)  # Remove MongoDB internal ID
    return ProjectDoc(**doc)


def list_projects(username: str) -> List[ProjectDoc]:
    """List all projects for a user."""
    docs = list(get_projects_collection().find({"username": username}))
    
    for doc in docs:
        doc.pop("_id", None)
    
    return [ProjectDoc(**doc) for doc in docs]


def create_project(
    username: str,
    name: str,
    description: str,
    files: List[dict]
) -> ProjectDoc:
    """Create a new project."""
    collection = get_projects_collection()
    
    # Get next ID
    existing = list(collection.find({"username": username}))
    max_id = max([p.get("id", 0) for p in existing], default=0)
    
    # Create and validate document
    project = ProjectDoc(
        id=max_id + 1,
        username=username,
        name=name,
        description=description,
        files=[FileDoc(**f) for f in files]
    )
    
    # Insert into database
    collection.insert_one(project.model_dump())
    
    return project


def update_project(
    username: str,
    project_id: int,
    name: str,
    description: str,
    files: List[dict]
) -> bool:
    """Update a project. Returns True if updated."""
    # Validate files
    validated_files = [FileDoc(**f).model_dump() for f in files]
    
    result = get_projects_collection().update_one(
        {"username": username, "id": project_id},
        {"$set": {
            "name": name,
            "description": description,
            "files": validated_files
        }}
    )
    
    return result.matched_count > 0


def delete_project(username: str, project_id: int) -> bool:
    """Delete a project. Returns True if deleted."""
    result = get_projects_collection().delete_one({
        "username": username,
        "id": project_id
    })
    return result.deleted_count > 0


# ================
# Agent Operations
# ================

def get_agent(username: str, agent_id: str) -> Optional[AgentDoc]:
    """Get an agent by ID."""
    doc = get_agents_collection().find_one({
        "username": username,
        "id": agent_id
    })
    
    if not doc:
        return None
    
    doc.pop("_id", None)
    return AgentDoc(**doc)


def list_agents(username: str) -> List[AgentDoc]:
    """List all agents for a user."""
    docs = list(get_agents_collection().find({"username": username}))
    
    for doc in docs:
        doc.pop("_id", None)
    
    return [AgentDoc(**doc) for doc in docs]


def create_agent(username: str, agent_data: dict) -> AgentDoc:
    """Create a new agent."""
    # Validate and create agent document
    agent = AgentDoc(username=username, **agent_data)
    
    # Insert into database
    get_agents_collection().insert_one(agent.model_dump())
    
    return agent


def update_agent(username: str, agent_id: str, agent_data: dict) -> bool:
    """Update an agent. Returns True if updated."""
    # Validate data (without username/id)
    partial = AgentDoc(
        id=agent_id,
        username=username,
        **agent_data
    )
    
    # Extract only the updateable fields
    update_fields = {
        "name": partial.name,
        "system_prompt": partial.system_prompt,
        "tool_names": partial.tool_names,
        "model": partial.model,
        "temperature": partial.temperature,
        "max_retries": partial.max_retries
    }
    
    result = get_agents_collection().update_one(
        {"username": username, "id": agent_id},
        {"$set": update_fields}
    )
    
    return result.matched_count > 0


def delete_agent(username: str, agent_id: str) -> bool:
    """Delete an agent. Returns True if deleted."""
    result = get_agents_collection().delete_one({
        "username": username,
        "id": agent_id
    })
    return result.deleted_count > 0


def get_agents_by_ids(username: str, agent_ids: List[str]) -> List[AgentDoc]:
    """Get multiple agents by their IDs."""
    docs = list(get_agents_collection().find({
        "username": username,
        "id": {"$in": agent_ids}
    }))
    
    for doc in docs:
        doc.pop("_id", None)
    
    return [AgentDoc(**doc) for doc in docs]


# ===============
# Team Operations
# ===============

def get_team(username: str, team_id: str) -> Optional[TeamDoc]:
    """Get a team by ID."""
    doc = get_teams_collection().find_one({
        "username": username,
        "id": team_id
    })
    
    if not doc:
        return None
    
    doc.pop("_id", None)
    return TeamDoc(**doc)


def list_teams(username: str) -> List[TeamDoc]:
    """List all teams for a user."""
    docs = list(get_teams_collection().find({"username": username}))
    
    for doc in docs:
        doc.pop("_id", None)
    
    return [TeamDoc(**doc) for doc in docs]


def create_team(username: str, team_data: dict) -> TeamDoc:
    """Create a new team."""
    # Validate and create team document
    team = TeamDoc(username=username, **team_data)
    
    # Insert into database
    get_teams_collection().insert_one(team.model_dump(by_alias=True))
    
    return team


def update_team(username: str, team_id: str, team_data: dict) -> bool:
    """Update a team. Returns True if updated."""
    # Validate data
    partial = TeamDoc(
        id=team_id,
        username=username,
        **team_data
    )
    
    # Extract updateable fields
    update_fields = {
        "name": partial.name,
        "description": partial.description,
        "agent_ids": partial.agent_ids,
        "edges": [edge.model_dump(by_alias=True) for edge in partial.edges],
        "entry_point": partial.entry_point
    }
    
    result = get_teams_collection().update_one(
        {"username": username, "id": team_id},
        {"$set": update_fields}
    )
    
    return result.matched_count > 0


def delete_team(username: str, team_id: str) -> bool:
    """Delete a team. Returns True if deleted."""
    result = get_teams_collection().delete_one({
        "username": username,
        "id": team_id
    })
    return result.deleted_count > 0


# ==============
# Run Operations
# ==============

def get_run(username: str, run_id: str) -> Optional[RunDoc]:
    """Get a run by ID."""
    doc = get_runs_collection().find_one({
        "username": username,
        "id": run_id
    })
    
    if not doc:
        return None
    
    doc.pop("_id", None)
    return RunDoc(**doc)


def list_runs(
    username: str,
    project_id: Optional[int] = None,
    team_id: Optional[str] = None
) -> List[RunDoc]:
    """List runs, optionally filtered by project or team."""
    query = {"username": username}
    if project_id is not None:
        query["project_id"] = project_id
    if team_id is not None:
        query["team_id"] = team_id
    
    docs = list(get_runs_collection().find(query).sort("timestamp", -1))
    
    for doc in docs:
        doc.pop("_id", None)
    
    return [RunDoc(**doc) for doc in docs]


def create_run(run_data: dict) -> RunDoc:
    """Create a new run."""
    # Validate and create run document
    run = RunDoc(**run_data)
    
    # Insert into database
    get_runs_collection().insert_one(run.model_dump())
    
    return run


def update_run(run_id: str, updates: dict) -> bool:
    """Update a run. Returns True if updated."""
    result = get_runs_collection().update_one(
        {"id": run_id},
        {"$set": updates}
    )
    return result.matched_count > 0


def delete_run(username: str, run_id: str) -> bool:
    """Delete a run. Returns True if deleted."""
    result = get_runs_collection().delete_one({
        "username": username,
        "id": run_id
    })
    return result.deleted_count > 0


# ====================
# Evolution Operations
# ====================

def get_evolution(username: str, evolution_id: str) -> Optional[EvolutionDoc]:
    """Get an evolution by ID."""
    doc = get_evolutions_collection().find_one({
        "username": username,
        "id": evolution_id
    })
    
    if not doc:
        return None
    
    doc.pop("_id", None)
    return EvolutionDoc(**doc)


def list_evolutions(
    username: str,
    project_id: Optional[int] = None
) -> List[EvolutionDoc]:
    """List evolutions, optionally filtered by project."""
    query = {"username": username}
    if project_id is not None:
        query["project_id"] = project_id
    
    docs = list(get_evolutions_collection().find(query).sort("timestamp", -1))
    
    for doc in docs:
        doc.pop("_id", None)
    
    return [EvolutionDoc(**doc) for doc in docs]


def create_evolution(evolution_data: dict) -> EvolutionDoc:
    """Create a new evolution."""
    # Validate and create evolution document
    evolution = EvolutionDoc(**evolution_data)
    
    # Insert into database
    get_evolutions_collection().insert_one(evolution.model_dump())
    
    return evolution


def update_evolution(evolution_id: str, updates: dict) -> bool:
    """Update an evolution. Returns True if updated."""
    result = get_evolutions_collection().update_one(
        {"id": evolution_id},
        {"$set": updates}
    )
    return result.matched_count > 0


def delete_evolution(username: str, evolution_id: str) -> bool:
    """Delete an evolution. Returns True if deleted."""
    result = get_evolutions_collection().delete_one({
        "username": username,
        "id": evolution_id
    })
    return result.deleted_count > 0