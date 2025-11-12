import json
from pathlib import Path
from typing import Dict, Any, List
from agent_evo.models.tool import Tool
from agent_evo.models.agent import Agent
from agent_evo.models.team import Team

class JSONLoader:
    """Loads agents, tools, and teams from JSON files."""
    
    @staticmethod
    def load_tools(file_path: str) -> Dict[str, Tool]:
        """Load tools from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Tools file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        tools = {}
        for tool_data in data.get("tools", []):
            tool = Tool.from_dict(tool_data)
            if tool.id == "file_writer" or tool.id == "file_reader": continue
            tools[tool.id] = tool
        
        return tools
    
    @staticmethod
    def load_agents(file_path: str) -> Dict[str, Agent]:
        """Load agents from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Agents file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        agents = {}
        for agent_data in data.get("agents", []):
            agent = Agent.from_dict(agent_data)
            agents[agent.id] = agent
        
        return agents
    
    @staticmethod
    def load_team(file_path: str) -> Team:
        """Load a team from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Team file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return Team.from_dict(data)
    
    @staticmethod
    def load_task(file_path: str) -> str:
        """Load a task from a text file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Task file not found: {file_path}")
        
        with open(path, 'r') as f:
            return f.read().strip()