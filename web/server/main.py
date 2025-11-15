from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


class Project(BaseModel):
    id: int
    name: str
    description: str


MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)

db = client["evo_agents"]          # database name
projects_collection = db["projects"]  # collection name



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
