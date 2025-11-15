import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Project, Team } from "../types";
import CreateProjectModal from "../components/CreateProjectModal";
import CreateTeamModal from "../components/CreateTeamModal";
import CreateAgentModal from "../components/CreateAgentModal";
import { Agent } from "../types";
import CreateRunModal from "../components/CreateRunModal";
import { Run } from "../types";
import CreateEvolutionModal from "../components/CreateEvolutionModal";
import { Evolution } from "../types";

type TabType = "projects" | "teams" | "agents" | "runs" | "evolutions";

const Dashboard: React.FC = () => {
  const { username } = useParams<{ username: string }>();
  const [activeTab, setActiveTab] = useState<TabType>("projects");
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isTeamModalOpen, setIsTeamModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false);
  const [runs, setRuns] = useState<Run[]>([]);
  const [isRunModalOpen, setIsRunModalOpen] = useState(false);
  const [evolutions, setEvolutions] = useState<Evolution[]>([]);
  const [isEvolutionModalOpen, setIsEvolutionModalOpen] = useState(false);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/projects/${username}`
      );
      const data = await response.json();
      setProjects(data);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeams = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/teams/${username}`);
      const data = await response.json();
      setTeams(data);
    } catch (error) {
      console.error("Failed to fetch teams:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/agents/${username}`);
      const data = await response.json();
      setAgents(data);
    } catch (error) {
      console.error("Failed to fetch agents:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/runs/${username}`);
      const data = await response.json();
      setRuns(data);
    } catch (error) {
      console.error("Failed to fetch runs:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvolutions = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/evolutions/${username}`
      );
      const data = await response.json();
      setEvolutions(data);
    } catch (error) {
      console.error("Failed to fetch evolutions:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "projects") {
      fetchProjects();
    } else if (activeTab === "teams") {
      fetchTeams();
    } else if (activeTab === "agents") {
      fetchAgents();
    } else if (activeTab === "runs") {
      fetchRuns();
    } else if (activeTab === "evolutions") {
      fetchEvolutions();
    }
  }, [username, activeTab]);

  const handleCreateProject = async (name: string, description: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/projects/${username}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, description }),
        }
      );

      if (response.ok) {
        await fetchProjects();
        setIsProjectModalOpen(false);
      }
    } catch (error) {
      console.error("Failed to create project:", error);
    }
  };

  const handleCreateTeam = async (name: string, description: string) => {
    try {
      const response = await fetch(`http://localhost:8000/teams/${username}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          agent_ids: [],
          edges: [],
          entry_point: "",
        }),
      });

      if (response.ok) {
        await fetchTeams();
        setIsTeamModalOpen(false);
      }
    } catch (error) {
      console.error("Failed to create team:", error);
    }
  };

  const handleDeleteProject = async (projectId: number) => {
    if (!confirm("Are you sure you want to delete this project?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/projects/${username}/${projectId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        await fetchProjects();
      }
    } catch (error) {
      console.error("Failed to delete project:", error);
    }
  };

  const handleDeleteTeam = async (teamId: string) => {
    if (!confirm("Are you sure you want to delete this team?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/teams/${username}/${teamId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        await fetchTeams();
      }
    } catch (error) {
      console.error("Failed to delete team:", error);
    }
  };

  const handleCreateAgent = async (agentData: {
    name: string;
    system_prompt: string;
    tool_names: string[];
    model: string;
    temperature: number;
    max_retries: number;
  }) => {
    try {
      const response = await fetch(`http://localhost:8000/agents/${username}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(agentData),
      });

      if (response.ok) {
        await fetchAgents();
        setIsAgentModalOpen(false);
      }
    } catch (error) {
      console.error("Failed to create agent:", error);
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm("Are you sure you want to delete this agent?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/agents/${username}/${agentId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        await fetchAgents();
      }
    } catch (error) {
      console.error("Failed to delete agent:", error);
    }
  };

  const handleCreateRun = async (
    teamId: string,
    projectId: number,
    runName: string
  ) => {
    try {
      const response = await fetch(`http://localhost:8000/runs/${username}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          team_id: teamId,
          project_id: projectId,
          run_name: runName,
        }),
      });

      if (response.ok) {
        await fetchRuns();
        setIsRunModalOpen(false);
        setActiveTab("runs");
      }
    } catch (error) {
      console.error("Failed to create run:", error);
    }
  };

  const handleDeleteRun = async (runId: string) => {
    if (!confirm("Are you sure you want to delete this run?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/runs/${username}/${runId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        await fetchRuns();
      }
    } catch (error) {
      console.error("Failed to delete run:", error);
    }
  };

  const handleCreateEvolution = async (
    projectId: number,
    maxRounds: number,
    K: number
  ) => {
    try {
      const response = await fetch(
        `http://localhost:8000/evolutions/${username}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: projectId,
            max_rounds: maxRounds,
            K: K,
          }),
        }
      );

      if (response.ok) {
        await fetchEvolutions();
        setIsEvolutionModalOpen(false);
        setActiveTab("evolutions");
      }
    } catch (error) {
      console.error("Failed to create evolution:", error);
    }
  };

  const handleDeleteEvolution = async (evolutionId: string) => {
    if (!confirm("Are you sure you want to delete this evolution?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/evolutions/${username}/${evolutionId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        await fetchEvolutions();
      }
    } catch (error) {
      console.error("Failed to delete evolution:", error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "#28a745";
      case "failed":
        return "#dc3545";
      case "running":
        return "#ffc107";
      default:
        return "#6c757d";
    }
  };

  const tabStyle = (tab: TabType) => ({
    padding: "0.75rem 1.5rem",
    backgroundColor: activeTab === tab ? "#007bff" : "#f8f9fa",
    color: activeTab === tab ? "white" : "#333",
    border: "none",
    borderBottom: activeTab === tab ? "none" : "2px solid #ddd",
    cursor: "pointer",
    fontSize: "1rem",
    fontWeight: activeTab === tab ? "bold" : "normal",
  });

  return (
    <div>
      <h1 style={{ marginBottom: "1.5rem" }}>Dashboard - {username}</h1>

      {/* Tab Navigation */}
      <div style={{ borderBottom: "2px solid #ddd", marginBottom: "1.5rem" }}>
        <button
          onClick={() => setActiveTab("projects")}
          style={tabStyle("projects")}
        >
          Projects
        </button>
        <button onClick={() => setActiveTab("teams")} style={tabStyle("teams")}>
          Agent Teams
        </button>
        <button
          onClick={() => setActiveTab("agents")}
          style={tabStyle("agents")}
        >
          Agents
        </button>
        <button onClick={() => setActiveTab("runs")} style={tabStyle("runs")}>
          Runs
        </button>
        <button
          onClick={() => setActiveTab("evolutions")}
          style={tabStyle("evolutions")}
        >
          Evolutions
        </button>
      </div>

      {/* Projects Tab */}
      {activeTab === "projects" && (
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ margin: 0 }}>Your Projects</h2>
            <button
              onClick={() => setIsProjectModalOpen(true)}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#007bff",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Create Project
            </button>
          </div>

          {loading ? (
            <p>Loading projects...</p>
          ) : projects.length === 0 ? (
            <p>No projects yet. Create your first project!</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {projects.map((proj) => (
                <li
                  key={proj.id}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    padding: "1rem",
                    marginBottom: "0.5rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Link
                    to={`/projects/${username}/${proj.id}`}
                    style={{
                      textDecoration: "none",
                      color: "inherit",
                      flex: 1,
                    }}
                  >
                    <div>
                      <h3 style={{ margin: "0 0 0.5rem 0" }}>{proj.name}</h3>
                      <p style={{ margin: 0, color: "#666" }}>
                        {proj.description}
                      </p>
                    </div>
                  </Link>
                  <button
                    onClick={() => handleDeleteProject(proj.id)}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#dc3545",
                      color: "white",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}

          <CreateProjectModal
            isOpen={isProjectModalOpen}
            onClose={() => setIsProjectModalOpen(false)}
            onSubmit={handleCreateProject}
          />
        </div>
      )}

      {/* Agent Teams Tab */}
      {activeTab === "teams" && (
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ margin: 0 }}>Your Agent Teams</h2>
            <button
              onClick={() => setIsTeamModalOpen(true)}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#28a745",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Create Team
            </button>
          </div>

          {loading ? (
            <p>Loading teams...</p>
          ) : teams.length === 0 ? (
            <p>No teams yet. Create your first team!</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {teams.map((team) => (
                <li
                  key={team.id}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    padding: "1rem",
                    marginBottom: "0.5rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Link
                    to={`/teams/${username}/${team.id}`}
                    style={{
                      textDecoration: "none",
                      color: "inherit",
                      flex: 1,
                    }}
                  >
                    <div>
                      <h3 style={{ margin: "0 0 0.5rem 0" }}>{team.name}</h3>
                      <p style={{ margin: "0 0 0.5rem 0", color: "#666" }}>
                        {team.description}
                      </p>
                      <p
                        style={{ margin: 0, fontSize: "0.9rem", color: "#999" }}
                      >
                        {team.agent_ids.length} agent
                        {team.agent_ids.length !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </Link>
                  <button
                    onClick={() => handleDeleteTeam(team.id)}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#dc3545",
                      color: "white",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}

          <CreateTeamModal
            isOpen={isTeamModalOpen}
            onClose={() => setIsTeamModalOpen(false)}
            onSubmit={handleCreateTeam}
          />
        </div>
      )}

      {/* Agents Tab */}
      {activeTab === "agents" && (
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ margin: 0 }}>Your Agents</h2>
            <button
              onClick={() => setIsAgentModalOpen(true)}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#28a745",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Create Agent
            </button>
          </div>

          {loading ? (
            <p>Loading agents...</p>
          ) : agents.length === 0 ? (
            <p>No agents yet. Create your first agent!</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {agents.map((agent) => (
                <li
                  key={agent.id}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    padding: "1rem",
                    marginBottom: "0.5rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Link
                    to={`/agents/${username}/${agent.id}`}
                    style={{
                      textDecoration: "none",
                      color: "inherit",
                      flex: 1,
                    }}
                  >
                    <div>
                      <h3 style={{ margin: "0 0 0.5rem 0" }}>{agent.name}</h3>
                      <p style={{ margin: "0 0 0.5rem 0", color: "#666" }}>
                        {agent.system_prompt.substring(0, 100)}...
                      </p>
                      <p
                        style={{ margin: 0, fontSize: "0.9rem", color: "#999" }}
                      >
                        Model: {agent.model || "gpt-4o"} | Tools:{" "}
                        {agent.tool_names.length > 0
                          ? agent.tool_names.join(", ")
                          : "None"}
                      </p>
                    </div>
                  </Link>
                  <button
                    onClick={() => handleDeleteAgent(agent.id)}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#dc3545",
                      color: "white",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}

          <CreateAgentModal
            isOpen={isAgentModalOpen}
            onClose={() => setIsAgentModalOpen(false)}
            onSubmit={handleCreateAgent}
          />
        </div>
      )}

      {/* Runs Tab */}
      {activeTab === "runs" && (
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ margin: 0 }}>Your Runs</h2>
            <button
              onClick={() => setIsRunModalOpen(true)}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#007bff",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Create Run
            </button>
          </div>

          {loading ? (
            <p>Loading runs...</p>
          ) : runs.length === 0 ? (
            <p>No runs yet. Create your first run!</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {runs.map((run) => (
                <li
                  key={run.id}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    padding: "1rem",
                    marginBottom: "0.5rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Link
                    to={`/runs/${username}/${run.id}`}
                    style={{
                      textDecoration: "none",
                      color: "inherit",
                      flex: 1,
                    }}
                  >
                    <div>
                      <h3 style={{ margin: "0 0 0.5rem 0" }}>
                        {run.run_name}
                        <span
                          style={{
                            marginLeft: "0.5rem",
                            padding: "0.25rem 0.5rem",
                            backgroundColor: getStatusColor(run.status),
                            color: "white",
                            fontSize: "0.75rem",
                            borderRadius: "4px",
                            textTransform: "uppercase",
                          }}
                        >
                          {run.status}
                        </span>
                      </h3>
                      <p
                        style={{ margin: 0, fontSize: "0.9rem", color: "#999" }}
                      >
                        {new Date(run.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </Link>
                  <button
                    onClick={() => handleDeleteRun(run.id)}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#dc3545",
                      color: "white",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}

          <CreateRunModal
            isOpen={isRunModalOpen}
            onClose={() => setIsRunModalOpen(false)}
            onSubmit={handleCreateRun}
            username={username!}
          />
        </div>
      )}

      {/* Evolutions Tab */}
      {activeTab === "evolutions" && (
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ margin: 0 }}>Your Evolutions</h2>
            <button
              onClick={() => setIsEvolutionModalOpen(true)}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#6f42c1",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Create Evolution
            </button>
          </div>

          {loading ? (
            <p>Loading evolutions...</p>
          ) : evolutions.length === 0 ? (
            <p>No evolutions yet. Create your first evolution!</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {evolutions.map((evolution) => (
                <li
                  key={evolution.id}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    padding: "1rem",
                    marginBottom: "0.5rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Link
                    to={`/evolutions/${username}/${evolution.id}`}
                    style={{
                      textDecoration: "none",
                      color: "inherit",
                      flex: 1,
                    }}
                  >
                    <div>
                      <h3 style={{ margin: "0 0 0.5rem 0" }}>
                        Evolution - Project #{evolution.project_id}
                        <span
                          style={{
                            marginLeft: "0.5rem",
                            padding: "0.25rem 0.5rem",
                            backgroundColor: getStatusColor(evolution.status),
                            color: "white",
                            fontSize: "0.75rem",
                            borderRadius: "4px",
                            textTransform: "uppercase",
                          }}
                        >
                          {evolution.status}
                        </span>
                      </h3>
                      <p
                        style={{ margin: 0, fontSize: "0.9rem", color: "#999" }}
                      >
                        {evolution.team_ids.length} teams | Generation{" "}
                        {evolution.generation} | Max Rounds:{" "}
                        {evolution.max_rounds}
                      </p>
                      <p
                        style={{
                          margin: "0.25rem 0 0 0",
                          fontSize: "0.85rem",
                          color: "#999",
                        }}
                      >
                        {new Date(evolution.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </Link>
                  <button
                    onClick={() => handleDeleteEvolution(evolution.id)}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#dc3545",
                      color: "white",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}

          <CreateEvolutionModal
            isOpen={isEvolutionModalOpen}
            onClose={() => setIsEvolutionModalOpen(false)}
            onSubmit={handleCreateEvolution}
            username={username!}
          />
        </div>
      )}
    </div>
  );
};

export default Dashboard;
