"""Business logic layer for agent_evo operations - fully typed."""

import os
import uuid
import random
from typing import Dict, Any, List, Tuple
from datetime import datetime

from agent_evo.core.app import AgentEvoApp
from agent_evo.core.one_shot_builder import OneShotBuilder
from agent_evo.core.one_shot_merger import OneShotMerger
from agent_evo.core.one_shot_judge import OneShotJudge
from agent_evo.llm.client import OpenAIClient
from agent_evo.models.agent import Agent as EvoAgent
from agent_evo.models.team import Team as EvoTeam, TeamEdge as EvoTeamEdge
from agent_evo.models.results import TeamResult as EvoTeamResult
from agent_evo.models.database import (
    ProjectDoc,
    AgentDoc,
    TeamDoc,
    RunDoc,
    EvolutionDoc,
    FileDoc,
    TeamEdgeDoc
)

from . import repository


def _convert_team_result_to_dict(team_result: EvoTeamResult) -> Dict[str, Any]:
    """Convert TeamResult object to dictionary for storage."""
    return {
        "team_id": team_result.team_id,
        "team_name": team_result.team_name,
        "rounds": team_result.rounds,
        "agent_outputs": team_result.agent_outputs,
        "execution_history": [
            {
                "round": entry.round,
                "agent_id": entry.agent_id,
                "agent_name": entry.agent_name,
                "task": entry.task,
                "result": {
                    "agent_id": entry.result.agent_id,
                    "agent_name": entry.result.agent_name,
                    "final_response": entry.result.final_response,
                    "history": entry.result.history,
                    "messages": entry.result.messages,
                    "iterations": entry.result.iterations,
                    "delegation": entry.result.delegation,
                    "finished": entry.result.finished
                }
            }
            for entry in team_result.execution_history
        ],
        "chat_history": [
            {
                "agent_id": msg.agent_id,
                "agent_name": msg.agent_name,
                "role": msg.role,
                "content": msg.content
            }
            for msg in team_result.chat_history
        ]
    }


def _load_team_from_db(username: str, team_id: str) -> Tuple[Dict[str, EvoAgent], EvoTeam]:
    """
    Load a team and its agents from the database.
    
    Returns:
        Tuple of (agents_dict, team)
    """
    # Get team (returns TeamDoc)
    team_doc = repository.get_team(username, team_id)
    if not team_doc:
        raise ValueError(f"Team {team_id} not found")
    
    # Get agents (returns List[AgentDoc])
    agent_docs = repository.get_agents_by_ids(username, team_doc.agent_ids)
    
    if len(agent_docs) != len(team_doc.agent_ids):
        raise ValueError(f"Some agents not found for team {team_id}")
    
    # Convert to EvoAgent objects
    agents = {
        doc.id: EvoAgent(
            id=doc.id,
            name=doc.name,
            system_prompt=doc.system_prompt,
            tool_names=doc.tool_names,
            model=doc.model,
            temperature=doc.temperature,
            max_retries=doc.max_retries
        )
        for doc in agent_docs
    }
    
    # Convert to EvoTeam object
    team = EvoTeam(
        id=team_doc.id,
        name=team_doc.name,
        description=team_doc.description,
        agent_ids=team_doc.agent_ids,
        edges=[
            EvoTeamEdge(
                from_agent=edge.from_agent,
                to_agent=edge.to_agent,
                description=edge.description
            )
            for edge in team_doc.edges
        ],
        entry_point=team_doc.entry_point
    )
    
    return agents, team


def _store_and_run_team(
    username: str,
    project_id: int,
    project_doc: ProjectDoc,
    project_files: Dict[str, str],
    team_result: Dict[str, Any],
    team_name_prefix: str,
    app_instance: AgentEvoApp,
    judge: OneShotJudge,
    max_rounds: int
) -> Tuple[str, str]:
    """
    Store a team in the database, run it, score it, and return team_id and run_id.
    
    Returns:
        Tuple of (team_id, run_id)
    """
    # Create team ID
    team_id = str(uuid.uuid4())
    
    # Store agents and track ID mapping
    agent_id_mapping = {}
    agents_for_run = {}
    
    for old_id, agent in team_result["agents"].items():
        new_agent_id = str(uuid.uuid4())
        
        # Store in database (using typed create_agent)
        agent_doc = repository.create_agent(username, {
            "id": new_agent_id,
            "name": agent.name,
            "system_prompt": agent.system_prompt,
            "tool_names": agent.tool_names,
            "model": agent.model,
            "temperature": agent.temperature,
            "max_retries": agent.max_retries,
        })
        
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
    
    # Store team with updated agent IDs (using typed create_team)
    team = team_result["team"]
    team_doc = repository.create_team(username, {
        "id": team_id,
        "name": f"{team.name} ({team_name_prefix})",
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
    })
    
    # Create EvoTeam for running
    team_for_run = EvoTeam(
        id=team_doc.id,
        name=team_doc.name,
        description=team_doc.description,
        agent_ids=team_doc.agent_ids,
        edges=[
            EvoTeamEdge(
                from_agent=edge.from_agent,
                to_agent=edge.to_agent,
                description=edge.description
            )
            for edge in team_doc.edges
        ],
        entry_point=team_doc.entry_point
    )
    
    # Create run record (using typed create_run)
    run_id = str(uuid.uuid4())
    run_doc = repository.create_run({
        "id": run_id,
        "username": username,
        "team_id": team_id,
        "project_id": project_id,
        "run_name": f"{team.name} - Auto Run",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "running",
        "result": {},
        "score": None,
        "score_reasoning": None
    })
    
    try:
        # Run the team
        print(f"Running team: {team_doc.name}...")
        team_result_obj = app_instance.run_project(
            project_files=project_files,
            project_description=project_doc.description,
            team=team_for_run,
            agents=agents_for_run,
            max_rounds=max_rounds
        )
        
        # Convert to dict for storage
        result_dict = _convert_team_result_to_dict(team_result_obj)
        
        # Get modified files
        modified_files = app_instance.get_filesystem_files()
        result_dict["modified_files"] = modified_files
        
        # Judge the team performance
        judge_result = judge.judge_team(
            task=project_doc.description,
            team_result=team_result_obj,
            files=modified_files,
            temperature=0.3
        )
        
        # Update run with results and score
        repository.update_run(run_id, {
            "status": "completed",
            "result": result_dict,
            "score": judge_result["score"],
            "score_reasoning": judge_result["reasoning"]
        })
        
        print(f"Team run completed with score: {judge_result['score']}/10")
        
    except Exception as run_error:
        # Mark run as failed
        repository.update_run(run_id, {
            "status": "failed",
            "result": {"error": str(run_error)},
            "score": 0.0
        })
        print(f"Team run failed: {str(run_error)}")
    
    return team_id, run_id


# ==================
# Public API
# ==================

def run_team_on_project(
    username: str,
    project_id: int,
    team_id: str,
    run_name: str = "Untitled Run",
    max_rounds: int = 10,
    model: str = "gpt-4o"
) -> RunDoc:
    """
    Run a team on a project.
    
    Args:
        username: Username
        project_id: Project ID
        team_id: Team ID
        run_name: Name for this run
        max_rounds: Maximum number of delegation rounds
        model: LLM model to use
    
    Returns:
        Run document with results
    
    Raises:
        ValueError: If project or team not found
        RuntimeError: If run fails
    """
    # Get project (returns ProjectDoc)
    project_doc = repository.get_project(username, project_id)
    if not project_doc:
        raise ValueError(f"Project {project_id} not found")
    
    # Load team and agents (returns Dict[str, EvoAgent], EvoTeam)
    agents, team = _load_team_from_db(username, team_id)
    
    # Initialize LLM and app
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")
    
    llm_client = OpenAIClient(api_key=api_key, model=model)
    app_instance = AgentEvoApp(llm_client=llm_client)
    
    # Convert project files to dict
    project_files = {
        f.filename: f.content 
        for f in project_doc.files
    }
    
    # Create run record (returns RunDoc)
    run_id = str(uuid.uuid4())
    run_doc = repository.create_run({
        "id": run_id,
        "username": username,
        "team_id": team_id,
        "project_id": project_id,
        "run_name": run_name,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "running",
        "result": {},
        "score": None,
        "score_reasoning": None
    })
    
    try:
        # Run the team
        team_result = app_instance.run_project(
            project_files=project_files,
            project_description=project_doc.description,
            team=team,
            agents=agents,
            max_rounds=max_rounds
        )
        
        # Convert to dict for storage
        result_dict = _convert_team_result_to_dict(team_result)
        
        # Get modified files
        modified_files = app_instance.get_filesystem_files()
        result_dict["modified_files"] = modified_files
        
        # Judge the team performance
        judge = OneShotJudge(llm_client)
        judge_result = judge.judge_team(
            task=project_doc.description,
            team_result=team_result,
            files=modified_files,
            temperature=0.3
        )
        
        # Update run with results
        repository.update_run(run_id, {
            "status": "completed",
            "result": result_dict,
            "score": judge_result["score"],
            "score_reasoning": judge_result["reasoning"]
        })
        
        # Fetch updated run doc
        updated_run = repository.get_run(username, run_id)
        if not updated_run:
            raise RuntimeError("Failed to retrieve updated run")
        
        return updated_run
        
    except Exception as e:
        # Mark run as failed
        repository.update_run(run_id, {
            "status": "failed",
            "result": {"error": str(e)}
        })
        raise RuntimeError(f"Run failed: {str(e)}")


def build_team_for_project(
    username: str,
    project_id: int,
    temperature: float = 0.7,
    model: str = "gpt-4o"
) -> Dict[str, Any]:
    """
    Build a team for a project using one-shot builder.
    
    Args:
        username: Username
        project_id: Project ID
        temperature: LLM temperature
        model: LLM model to use
    
    Returns:
        Dictionary with team_id and agent_ids
    
    Raises:
        ValueError: If project not found
        RuntimeError: If build fails
    """
    # Get project (returns ProjectDoc)
    project_doc = repository.get_project(username, project_id)
    if not project_doc:
        raise ValueError(f"Project {project_id} not found")
    
    task = project_doc.description
    if not task:
        raise ValueError("Project must have a description to build a team")
    
    # Initialize LLM and builder
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")
    
    llm_client = OpenAIClient(api_key=api_key, model=model)
    builder = OneShotBuilder(llm_client)
    
    # Build team
    result = builder.build_team(task, temperature=temperature)
    
    # Store team and agents
    team_id = str(uuid.uuid4())
    agent_id_mapping = {}
    
    # Store agents (using typed create_agent)
    for old_id, agent in result["agents"].items():
        new_agent_id = str(uuid.uuid4())
        agent_doc = repository.create_agent(username, {
            "id": new_agent_id,
            "name": agent.name,
            "system_prompt": agent.system_prompt,
            "tool_names": agent.tool_names,
            "model": agent.model,
            "temperature": agent.temperature,
            "max_retries": agent.max_retries,
        })
        agent_id_mapping[old_id] = new_agent_id
    
    # Store team (using typed create_team)
    team = result["team"]
    team_doc = repository.create_team(username, {
        "id": team_id,
        "name": team.name,
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
    })
    
    return {
        "team_id": team_id,
        "agent_ids": list(agent_id_mapping.values()),
        "team_name": team.name
    }


def create_evolution_and_run_generations(
    username: str,
    project_id: int,
    max_rounds: int = 10,
    K: int = 5,
    model: str = "gpt-4o"
) -> EvolutionDoc:
    """
    Create an evolution and run all generations.
    
    Args:
        username: Username
        project_id: Project ID
        max_rounds: Number of evolution generations
        K: Number of initial teams to generate
        model: LLM model to use
    
    Returns:
        Evolution document
    
    Raises:
        ValueError: If project not found
        RuntimeError: If evolution fails
    """
    # Validate project (returns ProjectDoc)
    project_doc = repository.get_project(username, project_id)
    if not project_doc:
        raise ValueError(f"Project {project_id} not found")
    
    task = project_doc.description
    if not task:
        raise ValueError("Project must have a description to run evolution")
    
    # Create evolution record (returns EvolutionDoc)
    evolution_id = str(uuid.uuid4())
    evolution_doc = repository.create_evolution({
        "id": evolution_id,
        "username": username,
        "project_id": project_id,
        "team_ids": [],
        "run_ids": [],
        "max_rounds": max_rounds,
        "K": K,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "generating",
        "generation": 0
    })
    
    try:
        # Initialize LLM client and tools
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        
        llm_client = OpenAIClient(api_key=api_key, model=model)
        builder = OneShotBuilder(llm_client)
        merger = OneShotMerger(llm_client)
        judge = OneShotJudge(llm_client)
        app_instance = AgentEvoApp(llm_client=llm_client)
        
        # Convert project files to dict
        project_files = {
            f.filename: f.content 
            for f in project_doc.files
        }
        
        # Track all teams and runs
        all_team_ids = []
        all_run_ids = []
        
        # === GENERATION 0: Create K initial teams ===
        print(f"\n=== GENERATION 0: Creating {K} initial teams ===")
        
        for i in range(K):
            print(f"\nGenerating team {i+1}/{K}...")
            
            # Build team
            result = builder.build_team(task, temperature=0.8)
            
            # Store and run team
            team_id, run_id = _store_and_run_team(
                username=username,
                project_id=project_id,
                project_doc=project_doc,
                project_files=project_files,
                team_result=result,
                team_name_prefix=f"Gen 0 - Team {i+1}",
                app_instance=app_instance,
                judge=judge,
                max_rounds=10
            )
            
            all_team_ids.append(team_id)
            all_run_ids.append(run_id)
        
        # Update evolution after generation 0
        repository.update_evolution(evolution_id, {
            "team_ids": all_team_ids,
            "run_ids": all_run_ids,
            "generation": 0
        })
        
        print(f"\n=== Generation 0 complete: {len(all_team_ids)} teams created ===")
        
        # === GENERATIONS 1 to max_rounds: Merge and evolve ===
        for generation in range(1, max_rounds):
            print(f"\n=== GENERATION {generation}: Merging teams ===")
            
            # Get all runs with scores (returns List[RunDoc])
            run_docs = repository.list_runs(username, project_id=project_id)
            run_docs = [r for r in run_docs if r.score is not None]
            
            if len(run_docs) < 2:
                print(f"Not enough scored runs ({len(run_docs)}) to continue")
                break
            
            # Sort by score (descending)
            run_docs.sort(key=lambda x: x.score or 0, reverse=True)
            
            # Take top 50%
            top_half_count = max(2, len(run_docs) // 2)
            top_runs = run_docs[:top_half_count]
            
            print(f"Top 50% teams ({top_half_count} teams):")
            for i, run in enumerate(top_runs[:5]):
                team_doc = repository.get_team(username, run.team_id)
                if team_doc:
                    print(f"  {i+1}. {team_doc.name}: {run.score:.2f}/10")
            
            # Randomly select 2 teams from top 50%
            selected_runs = random.sample(top_runs, 2)
            parent1_run = selected_runs[0]
            parent2_run = selected_runs[1]
            
            print(f"\nSelected parents:")
            parent1_team_doc = repository.get_team(username, parent1_run.team_id)
            parent2_team_doc = repository.get_team(username, parent2_run.team_id)
            if parent1_team_doc and parent2_team_doc:
                print(f"  Parent 1: {parent1_team_doc.name} (score: {parent1_run.score:.2f})")
                print(f"  Parent 2: {parent2_team_doc.name} (score: {parent2_run.score:.2f})")
            
            # Load parent teams and agents
            parent1_agents, parent1_team = _load_team_from_db(
                username=username,
                team_id=parent1_run.team_id
            )
            parent2_agents, parent2_team = _load_team_from_db(
                username=username,
                team_id=parent2_run.team_id
            )
            
            # Merge teams
            print(f"\nMerging teams...")
            merge_result = merger.merge_teams(
                team1_agents=parent1_agents,
                team1_team=parent1_team,
                team2_agents=parent2_agents,
                team2_team=parent2_team,
                temperature=0.7
            )
            
            # Store merged team and run it
            team_id, run_id = _store_and_run_team(
                username=username,
                project_id=project_id,
                project_doc=project_doc,
                project_files=project_files,
                team_result=merge_result,
                team_name_prefix=f"Gen {generation} - Merged",
                app_instance=app_instance,
                judge=judge,
                max_rounds=10
            )
            
            all_team_ids.append(team_id)
            all_run_ids.append(run_id)
            
            # Update evolution with new generation
            repository.update_evolution(evolution_id, {
                "team_ids": all_team_ids,
                "run_ids": all_run_ids,
                "generation": generation
            })
            
            print(f"=== Generation {generation} complete ===")
        
        # Mark evolution as completed
        repository.update_evolution(evolution_id, {"status": "completed"})
        
        print(f"\n=== EVOLUTION COMPLETE ===")
        print(f"Total teams created: {len(all_team_ids)}")
        print(f"Total generations: {max_rounds}")
        
        # Print final rankings
        final_runs = repository.list_runs(username, project_id=project_id)
        final_runs = [r for r in final_runs if r.score is not None]
        final_runs.sort(key=lambda x: x.score or 0, reverse=True)
        
        print(f"\nFinal Top 5 Teams:")
        for i, run in enumerate(final_runs[:5]):
            team_doc = repository.get_team(username, run.team_id)
            if team_doc:
                print(f"  {i+1}. {team_doc.name}: {run.score:.2f}/10")
        
        # Return updated evolution doc
        updated_evolution = repository.get_evolution(username, evolution_id)
        if not updated_evolution:
            raise RuntimeError("Failed to retrieve updated evolution")
        
        return updated_evolution
        
    except Exception as e:
        # Mark evolution as failed
        repository.update_evolution(evolution_id, {"status": "failed"})
        raise RuntimeError(f"Evolution failed: {str(e)}")