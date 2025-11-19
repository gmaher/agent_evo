"""Basic tests for the CLI commands."""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
import pytest

from agent_evo.cli.main import app
from agent_evo.models.database import ProjectDoc, AgentDoc, TeamDoc, RunDoc, EvolutionDoc

runner = CliRunner()

# Test data
TEST_USERNAME = "testuser"
TEST_PROJECT_ID = 1
TEST_AGENT_ID = "agent-123"
TEST_TEAM_ID = "team-456"
TEST_RUN_ID = "run-789"
TEST_EVOLUTION_ID = "evo-012"


class TestProjectCommands:
    """Test project-related CLI commands."""
    
    @patch('agent_evo.services.repository.list_projects')
    def test_list_projects(self, mock_list_projects):
        """Test listing projects."""
        mock_list_projects.return_value = [
            ProjectDoc(
                id=1,
                username=TEST_USERNAME,
                name="Test Project",
                description="A test project",
                files=[]
            )
        ]
        
        result = runner.invoke(app, ["projects", "list", "--username", TEST_USERNAME])
        assert result.exit_code == 0
        assert "Test Project" in result.stdout
        mock_list_projects.assert_called_once_with(TEST_USERNAME)
    
    @patch('agent_evo.services.repository.list_projects')
    def test_list_projects_empty(self, mock_list_projects):
        """Test listing projects when none exist."""
        mock_list_projects.return_value = []
        
        result = runner.invoke(app, ["projects", "list", "--username", TEST_USERNAME])
        assert result.exit_code == 0
        assert "No projects found" in result.stdout
    
    @patch('agent_evo.services.repository.get_project')
    def test_show_project(self, mock_get_project):
        """Test showing project details."""
        mock_get_project.return_value = ProjectDoc(
            id=TEST_PROJECT_ID,
            username=TEST_USERNAME,
            name="Test Project",
            description="A test project",
            files=[{"filename": "test.py", "content": "print('test')"}]
        )
        
        result = runner.invoke(app, [
            "projects", "show", 
            "--username", TEST_USERNAME, 
            "--project-id", str(TEST_PROJECT_ID)
        ])
        assert result.exit_code == 0
        assert "Test Project" in result.stdout
        assert "test.py" in result.stdout
    
    @patch('agent_evo.services.repository.create_project')
    def test_create_project(self, mock_create_project):
        """Test creating a project."""
        mock_create_project.return_value = ProjectDoc(
            id=2,
            username=TEST_USERNAME,
            name="New Project",
            description="A new test project",
            files=[]
        )
        
        result = runner.invoke(app, [
            "projects", "create",
            "--username", TEST_USERNAME,
            "--name", "New Project",
            "--description", "A new test project"
        ])
        assert result.exit_code == 0
        assert "Created project" in result.stdout
    
    @patch('agent_evo.services.repository.delete_project')
    def test_delete_project(self, mock_delete_project):
        """Test deleting a project."""
        mock_delete_project.return_value = True
        
        result = runner.invoke(app, [
            "projects", "delete",
            "--username", TEST_USERNAME,
            "--project-id", str(TEST_PROJECT_ID),
            "--yes"  # Skip confirmation
        ])
        assert result.exit_code == 0
        assert "Deleted project" in result.stdout


class TestAgentCommands:
    """Test agent-related CLI commands."""
    
    @patch('agent_evo.services.repository.list_agents')
    def test_list_agents(self, mock_list_agents):
        """Test listing agents."""
        mock_list_agents.return_value = [
            AgentDoc(
                id=TEST_AGENT_ID,
                username=TEST_USERNAME,
                name="Test Agent",
                system_prompt="You are a test agent",
                tool_names=["bash", "str_replace"],
                model="gpt-4o",
                temperature=0.7
            )
        ]
        
        result = runner.invoke(app, ["agents", "list", "--username", TEST_USERNAME])
        assert result.exit_code == 0
        assert "Test Agent" in result.stdout
        assert "gpt-4o" in result.stdout
    
    @patch('agent_evo.services.repository.get_agent')
    def test_show_agent(self, mock_get_agent):
        """Test showing agent details."""
        mock_get_agent.return_value = AgentDoc(
            id=TEST_AGENT_ID,
            username=TEST_USERNAME,
            name="Test Agent",
            system_prompt="You are a test agent",
            tool_names=["bash", "str_replace"],
            model="gpt-4o",
            temperature=0.7,
            max_retries=3
        )
        
        result = runner.invoke(app, [
            "agents", "show",
            "--username", TEST_USERNAME,
            "--agent-id", TEST_AGENT_ID
        ])
        assert result.exit_code == 0
        assert "Test Agent" in result.stdout
        assert "test agent" in result.stdout


class TestTeamCommands:
    """Test team-related CLI commands."""
    
    @patch('agent_evo.services.repository.list_teams')
    def test_list_teams(self, mock_list_teams):
        """Test listing teams."""
        mock_list_teams.return_value = [
            TeamDoc(
                id=TEST_TEAM_ID,
                username=TEST_USERNAME,
                name="Test Team",
                description="A test team",
                agent_ids=[TEST_AGENT_ID],
                edges=[],
                entry_point=TEST_AGENT_ID
            )
        ]
        
        result = runner.invoke(app, ["teams", "list", "--username", TEST_USERNAME])
        assert result.exit_code == 0
        assert "Test Team" in result.stdout
    
    @patch('agent_evo.services.repository.get_team')
    @patch('agent_evo.services.repository.get_agents_by_ids')
    def test_show_team(self, mock_get_agents, mock_get_team):
        """Test showing team details."""
        mock_get_team.return_value = TeamDoc(
            id=TEST_TEAM_ID,
            username=TEST_USERNAME,
            name="Test Team",
            description="A test team",
            agent_ids=[TEST_AGENT_ID],
            edges=[],
            entry_point=TEST_AGENT_ID
        )
        mock_get_agents.return_value = [
            AgentDoc(
                id=TEST_AGENT_ID,
                username=TEST_USERNAME,
                name="Test Agent",
                system_prompt="test",
                tool_names=[]
            )
        ]
        
        result = runner.invoke(app, [
            "teams", "show",
            "--username", TEST_USERNAME,
            "--team-id", TEST_TEAM_ID
        ])
        assert result.exit_code == 0
        assert "Test Team" in result.stdout
        assert "Test Agent" in result.stdout
    
    @patch('agent_evo.services.orchestration.build_team_for_project')
    def test_build_team(self, mock_build_team):
        """Test building a team for a project."""
        mock_build_team.return_value = {
            "team_id": TEST_TEAM_ID,
            "agent_ids": [TEST_AGENT_ID],
            "team_name": "Built Team"
        }
        
        result = runner.invoke(app, [
            "teams", "build",
            "--username", TEST_USERNAME,
            "--project-id", str(TEST_PROJECT_ID)
        ])
        assert result.exit_code == 0
        assert "Built team" in result.stdout


class TestRunCommands:
    """Test run-related CLI commands."""
    
    @patch('agent_evo.services.repository.list_runs')
    def test_list_runs(self, mock_list_runs):
        """Test listing runs."""
        mock_list_runs.return_value = [
            RunDoc(
                id=TEST_RUN_ID,
                username=TEST_USERNAME,
                team_id=TEST_TEAM_ID,
                project_id=TEST_PROJECT_ID,
                run_name="Test Run",
                timestamp="2024-01-01T00:00:00",
                status="completed",
                result={},
                score=8.5,
                score_reasoning="Good performance"
            )
        ]
        
        result = runner.invoke(app, ["runs", "list", "--username", TEST_USERNAME])
        assert result.exit_code == 0
        assert "Test Run" in result.stdout
        assert "8.5" in result.stdout
    
    @patch('agent_evo.services.repository.get_run')
    def test_show_run(self, mock_get_run):
        """Test showing run details."""
        mock_get_run.return_value = RunDoc(
            id=TEST_RUN_ID,
            username=TEST_USERNAME,
            team_id=TEST_TEAM_ID,
            project_id=TEST_PROJECT_ID,
            run_name="Test Run",
            timestamp="2024-01-01T00:00:00",
            status="completed",
            result={"rounds": 5, "modified_files": {}},
            score=8.5,
            score_reasoning="Good performance"
        )
        
        result = runner.invoke(app, [
            "runs", "show",
            "--username", TEST_USERNAME,
            "--run-id", TEST_RUN_ID
        ])
        assert result.exit_code == 0
        assert "Test Run" in result.stdout
        assert "8.50/10" in result.stdout
        assert "Good performance" in result.stdout
    
    @patch('agent_evo.services.orchestration.run_team_on_project')
    def test_create_run(self, mock_run_team):
        """Test creating and executing a run."""
        mock_run_team.return_value = {
            "id": TEST_RUN_ID,
            "status": "completed",
            "score": 9.0
        }
        
        result = runner.invoke(app, [
            "runs", "create",
            "--username", TEST_USERNAME,
            "--project-id", str(TEST_PROJECT_ID),
            "--team-id", TEST_TEAM_ID,
            "--name", "Test Run"
        ])
        assert result.exit_code == 0
        assert "Run completed" in result.stdout


class TestEvolutionCommands:
    """Test evolution-related CLI commands."""
    
    @patch('agent_evo.services.repository.list_evolutions')
    def test_list_evolutions(self, mock_list_evolutions):
        """Test listing evolutions."""
        mock_list_evolutions.return_value = [
            EvolutionDoc(
                id=TEST_EVOLUTION_ID,
                username=TEST_USERNAME,
                project_id=TEST_PROJECT_ID,
                team_ids=[TEST_TEAM_ID],
                run_ids=[TEST_RUN_ID],
                max_rounds=10,
                K=5,
                timestamp="2024-01-01T00:00:00",
                status="completed",
                generation=3
            )
        ]
        
        result = runner.invoke(app, ["evolutions", "list", "--username", TEST_USERNAME])
        assert result.exit_code == 0
        assert str(TEST_PROJECT_ID) in result.stdout
        assert "completed" in result.stdout
    
    @patch('agent_evo.services.repository.get_evolution')
    @patch('agent_evo.services.repository.get_run')
    @patch('agent_evo.services.repository.get_team')
    def test_show_evolution(self, mock_get_team, mock_get_run, mock_get_evolution):
        """Test showing evolution details."""
        mock_get_evolution.return_value = EvolutionDoc(
            id=TEST_EVOLUTION_ID,
            username=TEST_USERNAME,
            project_id=TEST_PROJECT_ID,
            team_ids=[TEST_TEAM_ID],
            run_ids=[TEST_RUN_ID],
            max_rounds=10,
            K=5,
            timestamp="2024-01-01T00:00:00",
            status="completed",
            generation=3
        )
        mock_get_run.return_value = RunDoc(
            id=TEST_RUN_ID,
            username=TEST_USERNAME,
            team_id=TEST_TEAM_ID,
            project_id=TEST_PROJECT_ID,
            run_name="Test Run",
            timestamp="2024-01-01T00:00:00",
            status="completed",
            result={},
            score=9.0
        )
        mock_get_team.return_value = TeamDoc(
            id=TEST_TEAM_ID,
            username=TEST_USERNAME,
            name="Test Team",
            description="A test team",
            agent_ids=[],
            edges=[],
            entry_point=TEST_AGENT_ID
        )
        
        result = runner.invoke(app, [
            "evolutions", "show",
            "--username", TEST_USERNAME,
            "--evolution-id", TEST_EVOLUTION_ID
        ])
        assert result.exit_code == 0
        assert "Evolution" in result.stdout
        assert "Test Team" in result.stdout
        assert "9.00/10" in result.stdout
    
    @patch('agent_evo.services.orchestration.create_evolution_and_run_generations')
    def test_create_evolution(self, mock_create_evolution):
        """Test creating and running an evolution."""
        mock_create_evolution.return_value = EvolutionDoc(
            id=TEST_EVOLUTION_ID,
            username=TEST_USERNAME,
            project_id=TEST_PROJECT_ID,
            team_ids=[TEST_TEAM_ID],
            run_ids=[TEST_RUN_ID],
            max_rounds=5,
            K=3,
            timestamp="2024-01-01T00:00:00",
            status="completed",
            generation=4
        )
        
        result = runner.invoke(app, [
            "evolutions", "create",
            "--username", TEST_USERNAME,
            "--project-id", str(TEST_PROJECT_ID),
            "--max-rounds", "5",
            "--k", "3"  # Changed from --K to --k
        ])
        assert result.exit_code == 0
        assert "Evolution completed" in result.stdout
        assert TEST_EVOLUTION_ID in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])