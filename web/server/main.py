from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


# Very simple in-memory "db" indexed by username
PROJECTS_BY_USER = {
    "alice": [
        Project(id=1, name="Website Redesign", description="Update landing page layout"),
        Project(id=2, name="Analytics Setup", description="Add tracking for user events"),
    ],
    "bob": [
        Project(id=1, name="Internal Tool", description="CLI to manage tasks"),
        Project(id=2, name="Docs Cleanup", description="Organize API documentation"),
    ],
}


@app.get("/projects/{username}", response_model=List[Project])
def get_projects(username: str):
    # For demo purposes: return some default projects if user not found
    projects = PROJECTS_BY_USER.get(
        username,
        [
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
        ],
    )
    return projects
