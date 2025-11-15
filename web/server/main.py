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
from agent_evo.core.one_shot_builder import OneShotBuilder
from agent_evo.llm.client import OpenAIClient
from agent_evo.core.one_shot_judge import OneShotJudge

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
    score: Optional[float] = None  # Add score field
    score_reasoning: Optional[str] = None  # Add reasoning field

class RunCreate(BaseModel):
    team_id: str
    project_id: int
    run_name: str = "Untitled Run"


class Evolution(BaseModel):
    id: str
    username: str
    project_id: int
    team_ids: List[str]
    run_ids: List[str] = []  # Add run_ids field
    max_rounds: int
    K: int
    timestamp: str
    status: str  # "generating", "completed", "failed"
    generation: int = 0  # Current generation number

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
    runs: List[Run] = []  # Add runs field


class EvolutionCreate(BaseModel):
    project_id: int
    max_rounds: int = 10
    K: int = 5  # Number of initial teams to generate


# Mongo
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)

db = client["evo_agents"]
projects_collection = db["projects"]
teams_collection = db["teams"]
agents_collection = db["agents"]
runs_collection = db["runs"]  # Add runs collection
evolutions_collection = db["evolutions"]

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
        "result": {},
        "score": None,
        "score_reasoning": None
    }
    runs_collection.insert_one(run_doc)
    
    try:
        # Initialize AgentEvoApp and LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")
        
        llm_client = OpenAIClient(api_key=api_key, model="gpt-4o")
        app_instance = AgentEvoApp(llm_client=llm_client)
        
        # Convert project files to dict
        project_files = {
            f["filename"]: f["content"] 
            for f in project_doc.get("files", [])
        }
        
        # Convert agents to Agent objects
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
                    from_agent=edge.get("from_agent") or edge.get("from"),
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
        
        # Score the run using OneShotJudge
        judge = OneShotJudge(llm_client)
        
        # Convert result to TeamResult for judge
        from agent_evo.models.results import TeamResult, ExecutionEntry, AgentResult, ChatMessage
        
        team_result = TeamResult(
            team_id=result["team_id"],
            team_name=result["team_name"],
            execution_history=[
                ExecutionEntry(
                    round=entry["round"],
                    agent_id=entry["agent_id"],
                    agent_name=entry["agent_name"],
                    task=entry["task"],
                    result=AgentResult(
                        agent_id=entry["result"]["agent_id"],
                        agent_name=entry["result"]["agent_name"],
                        final_response=entry["result"]["final_response"],
                        history=[],
                        messages=[],
                        iterations=entry["result"]["iterations"],
                        delegation=entry["result"].get("delegation"),
                        finished=entry["result"]["finished"]
                    )
                )
                for entry in result["execution_history"]
            ],
            chat_history=[
                ChatMessage(
                    agent_id=msg["agent_id"],
                    agent_name=msg["agent_name"],
                    role=msg["role"],
                    content=msg["content"]
                )
                for msg in result["chat_history"]
            ],
            agent_outputs=result["agent_outputs"],
            rounds=result["rounds"]
        )
        
        # Get modified files
        modified_files = result.get("modified_files", {})
        
        # Judge the team performance
        judge_result = judge.judge_team(
            task=project_doc.get("description", ""),
            team_result=team_result,
            files=modified_files,
            temperature=0.3
        )
        
        # Update run with results and score
        runs_collection.update_one(
            {"id": run_id},
            {
                "$set": {
                    "status": "completed",
                    "result": result,
                    "score": judge_result["score"],
                    "score_reasoning": judge_result["reasoning"]
                }
            }
        )
        
        run_doc["status"] = "completed"
        run_doc["result"] = result
        run_doc["score"] = judge_result["score"]
        run_doc["score_reasoning"] = judge_result["reasoning"]
        
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

######################
# Evolution Routes
######################

@app.get("/evolutions/{username}", response_model=List[Evolution])
def get_evolutions(username: str, project_id: Optional[int] = None):
    """Get all evolutions for a user, optionally filtered by project."""
    query = {"username": username}
    
    if project_id is not None:
        query["project_id"] = project_id
    
    docs = list(evolutions_collection.find(query).sort("timestamp", -1))
    
    return [Evolution(**doc) for doc in docs]


@app.get("/evolutions/{username}/{evolution_id}", response_model=EvolutionWithRuns)
def get_evolution(username: str, evolution_id: str):
    """Get a specific evolution with its runs."""
    doc = evolutions_collection.find_one({
        "username": username,
        "id": evolution_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Evolution not found")
    
    # Fetch all runs for this evolution
    run_ids = doc.get("run_ids", [])
    runs = []
    if run_ids:
        run_docs = list(runs_collection.find({
            "username": username,
            "id": {"$in": run_ids}
        }))
        runs = [Run(**run_doc) for run_doc in run_docs]
    
    return EvolutionWithRuns(
        id=doc["id"],
        username=doc["username"],
        project_id=doc["project_id"],
        team_ids=doc.get("team_ids", []),
        run_ids=doc.get("run_ids", []),
        max_rounds=doc["max_rounds"],
        K=doc["K"],
        timestamp=doc["timestamp"],
        status=doc["status"],
        generation=doc.get("generation", 0),
        runs=runs
    )


@app.post("/evolutions/{username}", response_model=Evolution)
def create_evolution(username: str, evolution_request: EvolutionCreate):
    """Create a new evolution and generate K initial teams."""
    
    # Validate project exists
    project_doc = projects_collection.find_one({
        "username": username,
        "id": evolution_request.project_id
    })
    if not project_doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create evolution record
    evolution_id = str(uuid.uuid4())
    evolution_doc = {
        "id": evolution_id,
        "username": username,
        "project_id": evolution_request.project_id,
        "team_ids": [],
        "run_ids": [],  # Initialize run_ids
        "max_rounds": evolution_request.max_rounds,
        "K": evolution_request.K,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "generating",
        "generation": 0
    }
    evolutions_collection.insert_one(evolution_doc)
    
    try:
        # Initialize LLM client and one-shot builder
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")
        
        llm_client = OpenAIClient(api_key=api_key, model="gpt-4o")
        builder = OneShotBuilder(llm_client)
        judge = OneShotJudge(llm_client)  # Initialize judge
        
        # Generate task from project description
        task = project_doc.get("description", "")
        if not task:
            raise HTTPException(
                status_code=400,
                detail="Project must have a description to generate teams"
            )
        
        # Initialize AgentEvoApp for running teams
        app_instance = AgentEvoApp(llm_client=llm_client)
        
        # Convert project files to dict
        project_files = {
            f["filename"]: f["content"] 
            for f in project_doc.get("files", [])
        }
        
        # Generate K teams and run each one
        generated_team_ids = []
        generated_run_ids = []  # Track run IDs
        
        for i in range(evolution_request.K):
            print(f"Generating team {i+1}/{evolution_request.K}...")
            
            # Build team using one-shot builder
            result = builder.build_team(task, temperature=0.8)
            
            # Create team ID
            team_id = str(uuid.uuid4())
            
            # Store agents and track ID mapping
            agent_id_mapping = {}
            agents_for_run = {}
            
            for old_id, agent in result["agents"].items():
                new_agent_id = str(uuid.uuid4())
                
                # Store in database
                agent_doc = {
                    "id": new_agent_id,
                    "username": username,
                    "name": agent.name,
                    "system_prompt": agent.system_prompt,
                    "tool_names": agent.tool_names,
                    "model": agent.model,
                    "temperature": agent.temperature,
                    "max_retries": agent.max_retries,
                }
                agents_collection.insert_one(agent_doc)
                
                # Track mapping and create EvoAgent for running
                agent_id_mapping[old_id] = new_agent_id
                agents_for_run[new_agent_id] = EvoAgent(
                    id=new_agent_id,
                    name=agent.name,
                    system_prompt=agent.system_prompt,
                    tool_names=agent.tool_names,
                    model=agent.model,
                    temperature=agent.temperature,
                    max_retries=agent.max_retries
                )
            
            # Store team with updated agent IDs
            team = result["team"]
            team_doc = {
                "id": team_id,
                "username": username,
                "name": f"{team.name} (Gen 0 - Team {i+1})",
                "description": team.description,
                "agent_ids": [agent_id_mapping[aid] for aid in team.agent_ids],
                "edges": [
                    {
                        "from_agent": agent_id_mapping[edge.from_agent],
                        "to_agent": agent_id_mapping[edge.to_agent],
                        "description": edge.description
                    }
                    for edge in team.edges
                ],
                "entry_point": agent_id_mapping[team.entry_point],
            }
            teams_collection.insert_one(team_doc)
            generated_team_ids.append(team_id)
            
            # Create EvoTeam for running
            team_for_run = EvoTeam(
                id=team_id,
                name=team_doc["name"],
                description=team_doc["description"],
                agent_ids=team_doc["agent_ids"],
                edges=[
                    EvoTeamEdge(
                        from_agent=edge["from_agent"],
                        to_agent=edge["to_agent"],
                        description=edge.get("description")
                    )
                    for edge in team_doc["edges"]
                ],
                entry_point=team_doc["entry_point"]
            )
            
            # Run the team against the project
            print(f"Running team {i+1}/{evolution_request.K}...")
            run_id = str(uuid.uuid4())
            run_doc = {
                "id": run_id,
                "username": username,
                "team_id": team_id,
                "project_id": evolution_request.project_id,
                "run_name": f"{team.name} - Initial Run",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "running",
                "result": {},
                "score": None,
                "score_reasoning": None
            }
            runs_collection.insert_one(run_doc)
            generated_run_ids.append(run_id)  # Track run ID
            
            try:
                # Run the team
                run_result = app_instance.run_project(
                    project_files=project_files,
                    project_description=project_doc.get("description", ""),
                    team=team_for_run,
                    agents=agents_for_run,
                    max_rounds=evolution_request.max_rounds
                )
                
                # Score the run using OneShotJudge
                from agent_evo.models.results import TeamResult, ExecutionEntry, AgentResult, ChatMessage
                
                team_result = TeamResult(
                    team_id=run_result["team_id"],
                    team_name=run_result["team_name"],
                    execution_history=[
                        ExecutionEntry(
                            round=entry["round"],
                            agent_id=entry["agent_id"],
                            agent_name=entry["agent_name"],
                            task=entry["task"],
                            result=AgentResult(
                                agent_id=entry["result"]["agent_id"],
                                agent_name=entry["result"]["agent_name"],
                                final_response=entry["result"]["final_response"],
                                history=[],
                                messages=[],
                                iterations=entry["result"]["iterations"],
                                delegation=entry["result"].get("delegation"),
                                finished=entry["result"]["finished"]
                            )
                        )
                        for entry in run_result["execution_history"]
                    ],
                    chat_history=[
                        ChatMessage(
                            agent_id=msg["agent_id"],
                            agent_name=msg["agent_name"],
                            role=msg["role"],
                            content=msg["content"]
                        )
                        for msg in run_result["chat_history"]
                    ],
                    agent_outputs=run_result["agent_outputs"],
                    rounds=run_result["rounds"]
                )
                
                # Get modified files
                modified_files = run_result.get("modified_files", {})
                
                # Judge the team performance
                judge_result = judge.judge_team(
                    task=project_doc.get("description", ""),
                    team_result=team_result,
                    files=modified_files,
                    temperature=0.3
                )
                
                # Update run with results and score
                runs_collection.update_one(
                    {"id": run_id},
                    {
                        "$set": {
                            "status": "completed",
                            "result": run_result,
                            "score": judge_result["score"],
                            "score_reasoning": judge_result["reasoning"]
                        }
                    }
                )
                print(f"Team {i+1}/{evolution_request.K} run completed with score: {judge_result['score']}/10")
                
            except Exception as run_error:
                # Mark run as failed but continue with other teams
                runs_collection.update_one(
                    {"id": run_id},
                    {
                        "$set": {
                            "status": "failed",
                            "result": {"error": str(run_error)}
                        }
                    }
                )
                print(f"Team {i+1}/{evolution_request.K} run failed: {str(run_error)}")
        
        # Update evolution with generated teams and runs
        evolutions_collection.update_one(
            {"id": evolution_id},
            {
                "$set": {
                    "team_ids": generated_team_ids,
                    "run_ids": generated_run_ids,  # Store run IDs
                    "status": "completed"
                }
            }
        )
        
        evolution_doc["team_ids"] = generated_team_ids
        evolution_doc["run_ids"] = generated_run_ids
        evolution_doc["status"] = "completed"
        
        print(f"\nEvolution created with {len(generated_team_ids)} teams")
        print(f"All teams have been run and scored against the project")
        
    except Exception as e:
        # Mark evolution as failed
        evolutions_collection.update_one(
            {"id": evolution_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create evolution: {str(e)}"
        )
    
    return Evolution(**evolution_doc)


@app.delete("/evolutions/{username}/{evolution_id}")
def delete_evolution(username: str, evolution_id: str):
    """Delete an evolution."""
    result = evolutions_collection.delete_one({
        "username": username,
        "id": evolution_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Evolution not found")
    
    return {"message": "Evolution deleted successfully"}