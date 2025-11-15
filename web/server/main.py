import sys
import os
sys.path.append(os.path.abspath("../.."))

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
from pymongo import MongoClient

# Convert agents to Agent objects
from agent_evo.models.agent import Agent as EvoAgent
from agent_evo.core.app import AgentEvoApp
from agent_evo.models.team import Team as EvoTeam, TeamEdge as EvoTeamEdge

app = FastAPI()

# Allow local frontend dev (Vite default port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class File(BaseModel):
    filename: str
    content: str

class Project(BaseModel):
    id: int
    name: str
    description: str
    files: List[File] = []

class ProjectCreate(BaseModel):
    name: str
    description: str
    files: List[File] = []

class Agent(BaseModel):
    id: str
    name: str
    system_prompt: str
    tool_names: List[str] = []
    model: str = "gpt-4o"
    temperature: float = 1.0
    max_retries: int = 3

class AgentCreate(BaseModel):
    name: str
    system_prompt: str
    tool_names: List[str] = []
    model: str = "gpt-4o"
    temperature: float = 1.0
    max_retries: int = 3

class TeamEdge(BaseModel):
    from_agent: str = None
    to_agent: str = None
    description: str = None
    
    class Config:
        fields = {
            'from_agent': 'from',
            'to_agent': 'to'
        }

class Team(BaseModel):
    id: str
    name: str
    description: str
    agent_ids: List[str]
    edges: List[TeamEdge]
    entry_point: str

class TeamCreate(BaseModel):
    name: str
    description: str
    agent_ids: List[str]
    edges: List[TeamEdge]
    entry_point: str

class TeamWithAgents(BaseModel):
    id: str
    name: str
    description: str
    agent_ids: List[str]
    edges: List[TeamEdge]
    entry_point: str
    agents: List[Agent]

# Run result models matching AgentEvo structure
class ChatMessage(BaseModel):
    agent_id: str
    agent_name: str
    role: str
    content: str

class Delegation(BaseModel):
    to_agent: str
    task: str

class AgentResult(BaseModel):
    agent_id: str
    agent_name: str
    final_response: str
    iterations: int
    delegation: Optional[Delegation] = None
    finished: bool = False

class ExecutionEntry(BaseModel):
    round: int
    agent_id: str
    agent_name: str
    task: str
    result: AgentResult

class TeamResult(BaseModel):
    team_id: str
    team_name: str
    rounds: int
    agent_outputs: Dict[str, str]
    execution_history: List[ExecutionEntry]
    chat_history: List[ChatMessage]
    modified_files: Optional[Dict[str, str]] = None

class Run(BaseModel):
    id: str
    username: str
    team_id: str
    project_id: int
    run_name: str
    timestamp: str
    status: str  # "running", "completed", "failed"
    result: Dict[str, Any] = {}  # Can be TeamResult or error dict

class RunCreate(BaseModel):
    team_id: str
    project_id: int
    run_name: str = "Untitled Run"

# Mongo
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)

db = client["evo_agents"]
projects_collection = db["projects"]
teams_collection = db["teams"]
agents_collection = db["agents"]
runs_collection = db["runs"]  # Add runs collection

######################
# Project Routes
######################
@app.get("/projects/{username}", response_model=List[Project])
def get_projects(username: str):
    docs = list(projects_collection.find({"username": username}))

    if not docs:
        return []

    projects = [
        Project(
            id=doc.get("id", 0),
            name=doc.get("name", ""),
            description=doc.get("description", ""),
            files=[File(**f) for f in doc.get("files", [])],
        )
        for doc in docs
    ]
    return projects


@app.get("/projects/{username}/{project_id}", response_model=Project)
def get_project(username: str, project_id: int):
    doc = projects_collection.find_one({
        "username": username,
        "id": project_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return Project(
        id=doc.get("id", 0),
        name=doc.get("name", ""),
        description=doc.get("description", ""),
        files=[File(**f) for f in doc.get("files", [])],
    )


@app.post("/projects/{username}", response_model=Project)
def create_project(username: str, project: ProjectCreate):
    existing_projects = list(projects_collection.find({"username": username}))
    max_id = max([p.get("id", 0) for p in existing_projects], default=0)
    
    new_project = {
        "id": max_id + 1,
        "username": username,
        "name": project.name,
        "description": project.description,
        "files": [f.dict() for f in project.files],
    }
    
    projects_collection.insert_one(new_project)
    
    return Project(
        id=new_project["id"],
        name=new_project["name"],
        description=new_project["description"],
        files=project.files,
    )


@app.put("/projects/{username}/{project_id}", response_model=Project)
def update_project(username: str, project_id: int, project: ProjectCreate):
    result = projects_collection.update_one(
        {
            "username": username,
            "id": project_id
        },
        {
            "$set": {
                "name": project.name,
                "description": project.description,
                "files": [f.dict() for f in project.files],
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return Project(
        id=project_id,
        name=project.name,
        description=project.description,
        files=project.files,
    )


@app.delete("/projects/{username}/{project_id}")
def delete_project(username: str, project_id: int):
    result = projects_collection.delete_one({
        "username": username,
        "id": project_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project deleted successfully"}

######################
# Agent Routes
######################

@app.get("/agents/{username}", response_model=List[Agent])
def get_agents(username: str):
    """Get all agents for a user."""
    docs = list(agents_collection.find({"username": username}))
    
    agents = [
        Agent(
            id=doc.get("id", ""),
            name=doc.get("name", ""),
            system_prompt=doc.get("system_prompt", ""),
            tool_names=doc.get("tool_names", []),
            model=doc.get("model", "gpt-4o"),
            temperature=doc.get("temperature", 1.0),
            max_retries=doc.get("max_retries", 3),
        )
        for doc in docs
    ]
    return agents


@app.post("/agents/{username}", response_model=Agent)
def create_agent(username: str, agent: AgentCreate):
    """Create a new agent."""
    import uuid
    
    new_agent = {
        "id": str(uuid.uuid4()),
        "username": username,
        "name": agent.name,
        "system_prompt": agent.system_prompt,
        "tool_names": agent.tool_names,
        "model": agent.model,
        "temperature": agent.temperature,
        "max_retries": agent.max_retries,
    }
    
    agents_collection.insert_one(new_agent)
    
    return Agent(
        id=new_agent["id"],
        name=new_agent["name"],
        system_prompt=new_agent["system_prompt"],
        tool_names=new_agent["tool_names"],
        model=new_agent["model"],
        temperature=new_agent["temperature"],
        max_retries=new_agent["max_retries"],
    )


@app.get("/agents/{username}/{agent_id}", response_model=Agent)
def get_agent(username: str, agent_id: str):
    """Get a specific agent."""
    doc = agents_collection.find_one({
        "username": username,
        "id": agent_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return Agent(
        id=doc.get("id", ""),
        name=doc.get("name", ""),
        system_prompt=doc.get("system_prompt", ""),
        tool_names=doc.get("tool_names", []),
        model=doc.get("model", "gpt-4o"),
        temperature=doc.get("temperature", 1.0),
        max_retries=doc.get("max_retries", 3),
    )


@app.put("/agents/{username}/{agent_id}", response_model=Agent)
def update_agent(username: str, agent_id: str, agent: AgentCreate):
    """Update an existing agent."""
    result = agents_collection.update_one(
        {
            "username": username,
            "id": agent_id
        },
        {
            "$set": {
                "name": agent.name,
                "system_prompt": agent.system_prompt,
                "tool_names": agent.tool_names,
                "model": agent.model,
                "temperature": agent.temperature,
                "max_retries": agent.max_retries,
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return Agent(
        id=agent_id,
        name=agent.name,
        system_prompt=agent.system_prompt,
        tool_names=agent.tool_names,
        model=agent.model,
        temperature=agent.temperature,
        max_retries=agent.max_retries,
    )


@app.delete("/agents/{username}/{agent_id}")
def delete_agent(username: str, agent_id: str):
    """Delete an agent."""
    result = agents_collection.delete_one({
        "username": username,
        "id": agent_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": "Agent deleted successfully"}

######################
# Team Routes
######################

@app.get("/teams/{username}", response_model=List[Team])
def get_teams(username: str):
    """Get all teams for a user."""
    docs = list(teams_collection.find({"username": username}))
    
    teams = [
        Team(
            id=doc.get("id", ""),
            name=doc.get("name", ""),
            description=doc.get("description", ""),
            agent_ids=doc.get("agent_ids", []),
            edges=[TeamEdge(**edge) for edge in doc.get("edges", [])],
            entry_point=doc.get("entry_point", ""),
        )
        for doc in docs
    ]
    return teams


@app.get("/teams/{username}/{team_id}", response_model=TeamWithAgents)
def get_team_with_agents(username: str, team_id: str):
    """Get a team with all its agents."""
    team_doc = teams_collection.find_one({
        "username": username,
        "id": team_id
    })
    
    if not team_doc:
        raise HTTPException(status_code=404, detail="Team not found")
    
    agent_ids = team_doc.get("agent_ids", [])
    agent_docs = list(agents_collection.find({
        "username": username,
        "id": {"$in": agent_ids}
    }))
    
    agents = [
        Agent(
            id=doc.get("id", ""),
            name=doc.get("name", ""),
            system_prompt=doc.get("system_prompt", ""),
            tool_names=doc.get("tool_names", []),
            model=doc.get("model", "gpt-4o"),
            temperature=doc.get("temperature", 1.0),
            max_retries=doc.get("max_retries", 3),
        )
        for doc in agent_docs
    ]
    
    return TeamWithAgents(
        id=team_doc.get("id", ""),
        name=team_doc.get("name", ""),
        description=team_doc.get("description", ""),
        agent_ids=agent_ids,
        edges=[TeamEdge(**edge) for edge in team_doc.get("edges", [])],
        entry_point=team_doc.get("entry_point", ""),
        agents=agents,
    )


@app.post("/teams/{username}", response_model=Team)
def create_team(username: str, team: TeamCreate):
    """Create a new team."""
    import uuid
    
    agent_docs = list(agents_collection.find({
        "username": username,
        "id": {"$in": team.agent_ids}
    }))
    
    if len(agent_docs) != len(team.agent_ids):
        raise HTTPException(status_code=400, detail="One or more agent IDs not found")
    
    new_team = {
        "id": str(uuid.uuid4()),
        "username": username,
        "name": team.name,
        "description": team.description,
        "agent_ids": team.agent_ids,
        "edges": [edge.dict() for edge in team.edges],
        "entry_point": team.entry_point,
    }
    
    teams_collection.insert_one(new_team)
    
    return Team(
        id=new_team["id"],
        name=new_team["name"],
        description=new_team["description"],
        agent_ids=new_team["agent_ids"],
        edges=team.edges,
        entry_point=new_team["entry_point"],
    )


@app.delete("/teams/{username}/{team_id}")
def delete_team(username: str, team_id: str):
    """Delete a team."""
    result = teams_collection.delete_one({
        "username": username,
        "id": team_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"message": "Team deleted successfully"}

@app.put("/teams/{username}/{team_id}", response_model=Team)
def update_team(username: str, team_id: str, team: TeamCreate):
    """Update an existing team."""
    result = teams_collection.update_one(
        {
            "username": username,
            "id": team_id
        },
        {
            "$set": {
                "name": team.name,
                "description": team.description,
                "agent_ids": team.agent_ids,
                "edges": [edge.dict() for edge in team.edges],
                "entry_point": team.entry_point,
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return Team(
        id=team_id,
        name=team.name,
        description=team.description,
        agent_ids=team.agent_ids,
        edges=team.edges,
        entry_point=team.entry_point,
    )

######################
# Run Routes
######################

@app.post("/runs/{username}", response_model=Run)
def create_run(username: str, run_request: RunCreate):
    """Create and execute a new run."""
    
    # Validate project exists
    project_doc = projects_collection.find_one({
        "username": username,
        "id": run_request.project_id
    })
    if not project_doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate team exists and get agents
    team_doc = teams_collection.find_one({
        "username": username,
        "id": run_request.team_id
    })
    if not team_doc:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get all agents for the team
    agent_ids = team_doc.get("agent_ids", [])
    agent_docs = list(agents_collection.find({
        "username": username,
        "id": {"$in": agent_ids}
    }))
    
    if len(agent_docs) != len(agent_ids):
        raise HTTPException(status_code=400, detail="One or more agents not found")
    
    # Create run record
    run_id = str(uuid.uuid4())
    run_doc = {
        "id": run_id,
        "username": username,
        "team_id": run_request.team_id,
        "project_id": run_request.project_id,
        "run_name": run_request.run_name,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "running",
        "result": {}
    }
    runs_collection.insert_one(run_doc)
    
    try:
        # Initialize AgentEvoApp
        app_instance = AgentEvoApp()
        
        # Convert project files to dict
        project_files = {
            f["filename"]: f["content"] 
            for f in project_doc.get("files", [])
        }
        
        
        agents = {
            doc["id"]: EvoAgent(
                id=doc["id"],
                name=doc["name"],
                system_prompt=doc["system_prompt"],
                tool_names=doc.get("tool_names", []),
                model=doc.get("model", "gpt-4o"),
                temperature=doc.get("temperature", 1.0),
                max_retries=doc.get("max_retries", 3)
            )
            for doc in agent_docs
        }
        
        # Convert team to Team object
        team = EvoTeam(
            id=team_doc["id"],
            name=team_doc["name"],
            description=team_doc["description"],
            agent_ids=team_doc["agent_ids"],
            edges=[
                EvoTeamEdge(
                    from_agent=edge.get("from_agent") or edge.get("from"),  # Handle both field names
                    to_agent=edge.get("to_agent") or edge.get("to"),
                    description=edge.get("description")
                )
                for edge in team_doc.get("edges", [])
            ],
            entry_point=team_doc["entry_point"]
        )
        
        # Run the team
        result = app_instance.run_project(
            project_files=project_files,
            project_description=project_doc.get("description", ""),
            team=team,
            agents=agents,
            max_rounds=10
        )
        
        # Update run with results
        runs_collection.update_one(
            {"id": run_id},
            {
                "$set": {
                    "status": "completed",
                    "result": result
                }
            }
        )
        
        run_doc["status"] = "completed"
        run_doc["result"] = result
        
    except Exception as e:
        # Mark run as failed
        runs_collection.update_one(
            {"id": run_id},
            {
                "$set": {
                    "status": "failed",
                    "result": {"error": str(e)}
                }
            }
        )
        raise HTTPException(status_code=500, detail=f"Run failed: {str(e)}")
    
    return Run(**run_doc)


@app.get("/runs/{username}", response_model=List[Run])
def get_runs(username: str, project_id: Optional[int] = None, team_id: Optional[str] = None):
    """Get all runs for a user, optionally filtered by project or team."""
    query = {"username": username}
    
    if project_id is not None:
        query["project_id"] = project_id
    if team_id is not None:
        query["team_id"] = team_id
    
    docs = list(runs_collection.find(query).sort("timestamp", -1))
    
    return [Run(**doc) for doc in docs]


@app.get("/runs/{username}/{run_id}", response_model=Run)
def get_run(username: str, run_id: str):
    """Get a specific run."""
    doc = runs_collection.find_one({
        "username": username,
        "id": run_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return Run(**doc)


@app.delete("/runs/{username}/{run_id}")
def delete_run(username: str, run_id: str):
    """Delete a run."""
    result = runs_collection.delete_one({
        "username": username,
        "id": run_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {"message": "Run deleted successfully"}