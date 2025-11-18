"""Command-line interface for agent_evo."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from agent_evo.services import orchestration, repository

app = typer.Typer(help="Agent Evolution CLI - Build and evolve AI agent teams")
console = Console()

# Subcommands
projects_app = typer.Typer(help="Manage projects")
agents_app = typer.Typer(help="Manage agents")
teams_app = typer.Typer(help="Manage teams")
runs_app = typer.Typer(help="Manage and execute runs")
evolutions_app = typer.Typer(help="Manage and execute evolutions")

app.add_typer(projects_app, name="projects")
app.add_typer(agents_app, name="agents")
app.add_typer(teams_app, name="teams")
app.add_typer(runs_app, name="runs")
app.add_typer(evolutions_app, name="evolutions")


# ==================
# Project Commands
# ==================

@projects_app.command("list")
def list_projects(username: str = typer.Option(..., help="Username")):
    """List all projects for a user."""
    projects = repository.list_projects(username)
    
    if not projects:
        console.print(f"[yellow]No projects found for user '{username}'[/yellow]")
        return
    
    table = Table(title=f"Projects for {username}")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")
    table.add_column("Files", style="blue")
    
    for project in projects:
        table.add_row(
            str(project["id"]),
            project["name"],
            project["description"][:50] + "..." if len(project["description"]) > 50 else project["description"],
            str(len(project.get("files", [])))
        )
    
    console.print(table)


@projects_app.command("show")
def show_project(
    username: str = typer.Option(..., help="Username"),
    project_id: int = typer.Option(..., help="Project ID")
):
    """Show details of a specific project."""
    project = repository.get_project(username, project_id)
    
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]Project: {project['name']}[/bold cyan]")
    console.print(f"[bold]ID:[/bold] {project['id']}")
    console.print(f"[bold]Description:[/bold] {project['description']}")
    console.print(f"\n[bold]Files ({len(project.get('files', []))}):[/bold]")
    
    for file in project.get("files", []):
        console.print(f"  • {file['filename']} ({len(file['content'])} bytes)")


@projects_app.command("create")
def create_project(
    username: str = typer.Option(..., help="Username"),
    name: str = typer.Option(..., help="Project name"),
    description: str = typer.Option(..., help="Project description"),
    file: list[str] = typer.Option([], help="File in format 'path=content' or 'path' to read from disk")
):
    """Create a new project."""
    files = []
    
    for file_spec in file:
        if "=" in file_spec:
            # Format: path=content
            path, content = file_spec.split("=", 1)
            files.append({"filename": path, "content": content})
        else:
            # Read from disk
            file_path = Path(file_spec)
            if not file_path.exists():
                console.print(f"[red]File not found: {file_spec}[/red]")
                raise typer.Exit(1)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            files.append({"filename": file_path.name, "content": content})
    
    project = repository.create_project(username, name, description, files)
    
    console.print(f"[green]✓ Created project '{name}' with ID {project['id']}[/green]")


@projects_app.command("delete")
def delete_project(
    username: str = typer.Option(..., help="Username"),
    project_id: int = typer.Option(..., help="Project ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Delete a project."""
    if not confirm:
        typer.confirm(f"Are you sure you want to delete project {project_id}?", abort=True)
    
    if repository.delete_project(username, project_id):
        console.print(f"[green]✓ Deleted project {project_id}[/green]")
    else:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)


# ==================
# Agent Commands
# ==================

@agents_app.command("list")
def list_agents(username: str = typer.Option(..., help="Username")):
    """List all agents for a user."""
    agents = repository.list_agents(username)
    
    if not agents:
        console.print(f"[yellow]No agents found for user '{username}'[/yellow]")
        return
    
    table = Table(title=f"Agents for {username}")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Model", style="blue")
    table.add_column("Temperature", style="yellow")
    table.add_column("Tools", style="magenta")
    
    for agent in agents:
        table.add_row(
            agent["id"][:8] + "...",
            agent["name"],
            agent.get("model", "gpt-4o"),
            str(agent.get("temperature", 1.0)),
            str(len(agent.get("tool_names", [])))
        )
    
    console.print(table)


@agents_app.command("show")
def show_agent(
    username: str = typer.Option(..., help="Username"),
    agent_id: str = typer.Option(..., help="Agent ID")
):
    """Show details of a specific agent."""
    agent = repository.get_agent(username, agent_id)
    
    if not agent:
        console.print(f"[red]Agent {agent_id} not found[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]Agent: {agent['name']}[/bold cyan]")
    console.print(f"[bold]ID:[/bold] {agent['id']}")
    console.print(f"[bold]Model:[/bold] {agent.get('model', 'gpt-4o')}")
    console.print(f"[bold]Temperature:[/bold] {agent.get('temperature', 1.0)}")
    console.print(f"[bold]Max Retries:[/bold] {agent.get('max_retries', 3)}")
    console.print(f"\n[bold]System Prompt:[/bold]")
    console.print(agent["system_prompt"])
    console.print(f"\n[bold]Tools:[/bold] {', '.join(agent.get('tool_names', []))}")


# ===============
# Team Commands
# ===============

@teams_app.command("list")
def list_teams(username: str = typer.Option(..., help="Username")):
    """List all teams for a user."""
    teams = repository.list_teams(username)
    
    if not teams:
        console.print(f"[yellow]No teams found for user '{username}'[/yellow]")
        return
    
    table = Table(title=f"Teams for {username}")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")
    table.add_column("Agents", style="blue")
    
    for team in teams:
        table.add_row(
            team["id"][:8] + "...",
            team["name"],
            team["description"][:40] + "..." if len(team["description"]) > 40 else team["description"],
            str(len(team.get("agent_ids", [])))
        )
    
    console.print(table)


@teams_app.command("show")
def show_team(
    username: str = typer.Option(..., help="Username"),
    team_id: str = typer.Option(..., help="Team ID")
):
    """Show details of a specific team."""
    team = repository.get_team(username, team_id)
    
    if not team:
        console.print(f"[red]Team {team_id} not found[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]Team: {team['name']}[/bold cyan]")
    console.print(f"[bold]ID:[/bold] {team['id']}")
    console.print(f"[bold]Description:[/bold] {team['description']}")
    console.print(f"[bold]Entry Point:[/bold] {team['entry_point']}")
    
    # Get agent details
    agents = repository.get_agents_by_ids(username, team.get("agent_ids", []))
    agent_map = {a["id"]: a["name"] for a in agents}
    
    console.print(f"\n[bold]Agents ({len(agents)}):[/bold]")
    for agent in agents:
        console.print(f"  • {agent['name']} ({agent['id'][:8]}...)")
    
    console.print(f"\n[bold]Edges ({len(team.get('edges', []))}):[/bold]")
    for edge in team.get("edges", []):
        from_name = agent_map.get(edge.get("from_agent") or edge.get("from"), "Unknown")
        to_name = agent_map.get(edge.get("to_agent") or edge.get("to"), "Unknown")
        desc = edge.get("description", "")
        console.print(f"  • {from_name} → {to_name}" + (f": {desc}" if desc else ""))


@teams_app.command("build")
def build_team(
    username: str = typer.Option(..., help="Username"),
    project_id: int = typer.Option(..., help="Project ID to build team for"),
    temperature: float = typer.Option(0.7, help="LLM temperature"),
    model: str = typer.Option("gpt-4o", help="LLM model")
):
    """Build a team for a project using AI."""
    console.print(f"[cyan]Building team for project {project_id}...[/cyan]")
    
    try:
        result = orchestration.build_team_for_project(
            username=username,
            project_id=project_id,
            temperature=temperature,
            model=model
        )
        
        console.print(f"[green]✓ Built team '{result['team_name']}'[/green]")
        console.print(f"[bold]Team ID:[/bold] {result['team_id']}")
        console.print(f"[bold]Agents:[/bold] {len(result['agent_ids'])}")
        
    except Exception as e:
        console.print(f"[red]Failed to build team: {e}[/red]")
        raise typer.Exit(1)


# ==============
# Run Commands
# ==============

@runs_app.command("list")
def list_runs(
    username: str = typer.Option(..., help="Username"),
    project_id: Optional[int] = typer.Option(None, help="Filter by project ID"),
    team_id: Optional[str] = typer.Option(None, help="Filter by team ID")
):
    """List runs."""
    runs = repository.list_runs(username, project_id=project_id, team_id=team_id)
    
    if not runs:
        console.print(f"[yellow]No runs found[/yellow]")
        return
    
    table = Table(title="Runs")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Score", style="magenta")
    table.add_column("Timestamp", style="white")
    
    for run in runs:
        status_color = {
            "completed": "green",
            "failed": "red",
            "running": "yellow"
        }.get(run.get("status", ""), "white")
        
        score = run.get("score")
        score_str = f"{score:.2f}/10" if score is not None else "N/A"
        
        table.add_row(
            run["id"][:8] + "...",
            run.get("run_name", "Untitled"),
            f"[{status_color}]{run.get('status', 'unknown')}[/{status_color}]",
            score_str,
            run.get("timestamp", "")[:19]
        )
    
    console.print(table)


@runs_app.command("show")
def show_run(
    username: str = typer.Option(..., help="Username"),
    run_id: str = typer.Option(..., help="Run ID")
):
    """Show details of a specific run."""
    run = repository.get_run(username, run_id)
    
    if not run:
        console.print(f"[red]Run {run_id} not found[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]Run: {run.get('run_name', 'Untitled')}[/bold cyan]")
    console.print(f"[bold]ID:[/bold] {run['id']}")
    console.print(f"[bold]Status:[/bold] {run.get('status', 'unknown')}")
    console.print(f"[bold]Team ID:[/bold] {run.get('team_id', 'N/A')}")
    console.print(f"[bold]Project ID:[/bold] {run.get('project_id', 'N/A')}")
    console.print(f"[bold]Timestamp:[/bold] {run.get('timestamp', 'N/A')}")
    
    if run.get("score") is not None:
        console.print(f"[bold]Score:[/bold] {run['score']:.2f}/10")
        if run.get("score_reasoning"):
            console.print(f"[bold]Reasoning:[/bold] {run['score_reasoning']}")
    
    result = run.get("result", {})
    if result.get("error"):
        console.print(f"\n[red]Error: {result['error']}[/red]")
    elif result:
        console.print(f"\n[bold]Rounds:[/bold] {result.get('rounds', 'N/A')}")
        console.print(f"[bold]Modified Files:[/bold] {len(result.get('modified_files', {}))}")


@runs_app.command("create")
def create_run(
    username: str = typer.Option(..., help="Username"),
    project_id: int = typer.Option(..., help="Project ID"),
    team_id: str = typer.Option(..., help="Team ID"),
    name: str = typer.Option("CLI Run", help="Run name"),
    max_rounds: int = typer.Option(10, help="Maximum delegation rounds"),
    model: str = typer.Option("gpt-4o", help="LLM model")
):
    """Create and execute a new run."""
    console.print(f"[cyan]Running team {team_id} on project {project_id}...[/cyan]")
    
    try:
        run = orchestration.run_team_on_project(
            username=username,
            project_id=project_id,
            team_id=team_id,
            run_name=name,
            max_rounds=max_rounds,
            model=model
        )
        
        console.print(f"[green]✓ Run completed[/green]")
        console.print(f"[bold]Run ID:[/bold] {run['id']}")
        console.print(f"[bold]Status:[/bold] {run['status']}")
        
        if run.get("score") is not None:
            console.print(f"[bold]Score:[/bold] {run['score']:.2f}/10")
        
    except Exception as e:
        console.print(f"[red]Run failed: {e}[/red]")
        raise typer.Exit(1)


# ====================
# Evolution Commands
# ====================

@evolutions_app.command("list")
def list_evolutions(
    username: str = typer.Option(..., help="Username"),
    project_id: Optional[int] = typer.Option(None, help="Filter by project ID")
):
    """List evolutions."""
    evolutions = repository.list_evolutions(username, project_id=project_id)
    
    if not evolutions:
        console.print(f"[yellow]No evolutions found[/yellow]")
        return
    
    table = Table(title="Evolutions")
    table.add_column("ID", style="cyan")
    table.add_column("Project", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Generation", style="blue")
    table.add_column("Teams", style="magenta")
    table.add_column("Timestamp", style="white")
    
    for evo in evolutions:
        status_color = {
            "completed": "green",
            "failed": "red",
            "generating": "yellow"
        }.get(evo.get("status", ""), "white")
        
        table.add_row(
            evo["id"][:8] + "...",
            str(evo.get("project_id", "N/A")),
            f"[{status_color}]{evo.get('status', 'unknown')}[/{status_color}]",
            str(evo.get("generation", 0)),
            str(len(evo.get("team_ids", []))),
            evo.get("timestamp", "")[:19]
        )
    
    console.print(table)


@evolutions_app.command("show")
def show_evolution(
    username: str = typer.Option(..., help="Username"),
    evolution_id: str = typer.Option(..., help="Evolution ID")
):
    """Show details of a specific evolution."""
    evolution = repository.get_evolution(username, evolution_id)
    
    if not evolution:
        console.print(f"[red]Evolution {evolution_id} not found[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]Evolution[/bold cyan]")
    console.print(f"[bold]ID:[/bold] {evolution['id']}")
    console.print(f"[bold]Project ID:[/bold] {evolution.get('project_id', 'N/A')}")
    console.print(f"[bold]Status:[/bold] {evolution.get('status', 'unknown')}")
    console.print(f"[bold]Generation:[/bold] {evolution.get('generation', 0)}")
    console.print(f"[bold]Max Rounds:[/bold] {evolution.get('max_rounds', 'N/A')}")
    console.print(f"[bold]K (initial teams):[/bold] {evolution.get('K', 'N/A')}")
    console.print(f"[bold]Teams Created:[/bold] {len(evolution.get('team_ids', []))}")
    console.print(f"[bold]Runs:[/bold] {len(evolution.get('run_ids', []))}")
    console.print(f"[bold]Timestamp:[/bold] {evolution.get('timestamp', 'N/A')}")
    
    # Show top scoring runs
    run_ids = evolution.get("run_ids", [])
    if run_ids:
        runs = [repository.get_run(username, rid) for rid in run_ids]
        runs = [r for r in runs if r and r.get("score") is not None]
        runs.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        console.print(f"\n[bold]Top 5 Runs:[/bold]")
        for i, run in enumerate(runs[:5], 1):
            team = repository.get_team(username, run.get("team_id", ""))
            team_name = team.get("name", "Unknown") if team else "Unknown"
            console.print(f"  {i}. {team_name}: {run['score']:.2f}/10")


@evolutions_app.command("create")
def create_evolution(
    username: str = typer.Option(..., help="Username"),
    project_id: int = typer.Option(..., help="Project ID"),
    max_rounds: int = typer.Option(10, help="Number of evolution generations"),
    K: int = typer.Option(5, help="Number of initial teams"),
    model: str = typer.Option("gpt-4o", help="LLM model")
):
    """Create and run an evolution."""
    console.print(f"[cyan]Starting evolution for project {project_id}...[/cyan]")
    console.print(f"[cyan]Generations: {max_rounds}, Initial teams: {K}[/cyan]")
    
    try:
        evolution = orchestration.create_evolution_and_run_generations(
            username=username,
            project_id=project_id,
            max_rounds=max_rounds,
            K=K,
            model=model
        )
        
        console.print(f"\n[green]✓ Evolution completed[/green]")
        console.print(f"[bold]Evolution ID:[/bold] {evolution['id']}")
        console.print(f"[bold]Teams Created:[/bold] {len(evolution['team_ids'])}")
        console.print(f"[bold]Generations:[/bold] {evolution['generation'] + 1}")
        
    except Exception as e:
        console.print(f"[red]Evolution failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()