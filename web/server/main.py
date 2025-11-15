from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
from pymongo import MongoClient

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
class Project(BaseModel):
    id: int
    name: str
    description: str

class ProjectCreate(BaseModel):
    name: str
    description: str

class File(BaseModel):
    filename: str
    content: str

class Task(BaseModel):
    id: int
    project_id: int
    description: str
    files: List[File]

class TaskCreate(BaseModel):
    description: str
    files: List[File]

# Mongo
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)

db = client["evo_agents"]          # database name
projects_collection = db["projects"]  # collection name
tasks_collection = db["tasks"]  # tasks collection


######################
# Routes
######################
@app.get("/projects/{username}", response_model=List[Project])
def get_projects(username: str):
    # Find all docs for this username
    docs = list(projects_collection.find({"username": username}))

    if not docs:
        # Optional: return default projects if none exist in DB
        return [
            Project(
                id=1,
                name=f"{username}'s First Project",
                description="This is an example project for this demo.",
            ),
            Project(
                id=2,
                name="Second Project",
                description="Another sample project.",
            ),
        ]

    # Map MongoDB docs to Pydantic Project models
    projects = [
        Project(
            id=doc.get("id", 0),
            name=doc.get("name", ""),
            description=doc.get("description", ""),
        )
        for doc in docs
    ]
    return projects


@app.post("/projects/{username}", response_model=Project)
def create_project(username: str, project: ProjectCreate):
    # Get the highest existing ID for this user
    existing_projects = list(projects_collection.find({"username": username}))
    max_id = max([p.get("id", 0) for p in existing_projects], default=0)
    
    new_project = {
        "id": max_id + 1,
        "username": username,
        "name": project.name,
        "description": project.description,
    }
    
    projects_collection.insert_one(new_project)
    
    return Project(
        id=new_project["id"],
        name=new_project["name"],
        description=new_project["description"],
    )


@app.delete("/projects/{username}/{project_id}")
def delete_project(username: str, project_id: int):
    result = projects_collection.delete_one({
        "username": username,
        "id": project_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Also delete all tasks associated with this project
    tasks_collection.delete_many({
        "username": username,
        "project_id": project_id
    })
    
    return {"message": "Project deleted successfully"}


@app.get("/projects/{username}/{project_id}/tasks", response_model=List[Task])
def get_tasks(username: str, project_id: int):
    docs = list(tasks_collection.find({
        "username": username,
        "project_id": project_id
    }))
    
    tasks = [
        Task(
            id=doc.get("id", 0),
            project_id=doc.get("project_id", 0),
            description=doc.get("description", ""),
            files=[File(**f) for f in doc.get("files", [])],
        )
        for doc in docs
    ]
    return tasks


@app.post("/projects/{username}/{project_id}/tasks", response_model=Task)
def create_task(username: str, project_id: int, task: TaskCreate):
    # Get the highest existing task ID for this project
    existing_tasks = list(tasks_collection.find({
        "username": username,
        "project_id": project_id
    }))
    max_id = max([t.get("id", 0) for t in existing_tasks], default=0)
    
    new_task = {
        "id": max_id + 1,
        "username": username,
        "project_id": project_id,
        "description": task.description,
        "files": [f.dict() for f in task.files],
    }
    
    tasks_collection.insert_one(new_task)
    
    return Task(
        id=new_task["id"],
        project_id=new_task["project_id"],
        description=new_task["description"],
        files=task.files,
    )


@app.delete("/projects/{username}/{project_id}/tasks/{task_id}")
def delete_task(username: str, project_id: int, task_id: int):
    result = tasks_collection.delete_one({
        "username": username,
        "project_id": project_id,
        "id": task_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task deleted successfully"}


@app.put("/projects/{username}/{project_id}/tasks/{task_id}", response_model=Task)
def update_task(username: str, project_id: int, task_id: int, task: TaskCreate):
    result = tasks_collection.update_one(
        {
            "username": username,
            "project_id": project_id,
            "id": task_id
        },
        {
            "$set": {
                "description": task.description,
                "files": [f.dict() for f in task.files],
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return Task(
        id=task_id,
        project_id=project_id,
        description=task.description,
        files=task.files,
    )