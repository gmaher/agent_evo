import React, { useState, useEffect } from "react";
import { Project, Team } from "../types";

interface CreateRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (teamId: string, projectId: number, runName: string) => void;
  username: string;
}

const CreateRunModal: React.FC<CreateRunModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  username,
}) => {
  const [runName, setRunName] = useState("");
  const [selectedTeam, setSelectedTeam] = useState("");
  const [selectedProject, setSelectedProject] = useState<number | "">("");
  const [teams, setTeams] = useState<Team[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchTeamsAndProjects();
    }
  }, [isOpen, username]);

  const fetchTeamsAndProjects = async () => {
    setLoading(true);
    try {
      const [teamsRes, projectsRes] = await Promise.all([
        fetch(`http://localhost:8000/teams/${username}`),
        fetch(`http://localhost:8000/projects/${username}`),
      ]);
      const teamsData = await teamsRes.json();
      const projectsData = await projectsRes.json();
      setTeams(teamsData);
      setProjects(projectsData);
    } catch (error) {
      console.error("Failed to fetch teams and projects:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedTeam && selectedProject !== "") {
      onSubmit(
        selectedTeam,
        selectedProject as number,
        runName || "Untitled Run"
      );
      setRunName("");
      setSelectedTeam("");
      setSelectedProject("");
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "white",
          padding: "2rem",
          borderRadius: "8px",
          width: "90%",
          maxWidth: "500px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ marginTop: 0 }}>Create New Run</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                Run Name (optional)
              </label>
              <input
                type="text"
                value={runName}
                onChange={(e) => setRunName(e.target.value)}
                placeholder="Untitled Run"
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                }}
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                Select Team *
              </label>
              <select
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                }}
                required
              >
                <option value="">
                  {teams.length === 0
                    ? "No teams available"
                    : "Select a team..."}
                </option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name} ({team.agent_ids.length} agents)
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                Select Project *
              </label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(Number(e.target.value))}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                }}
                required
              >
                <option value="">
                  {projects.length === 0
                    ? "No projects available"
                    : "Select a project..."}
                </option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>

            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                justifyContent: "flex-end",
              }}
            >
              <button
                type="button"
                onClick={onClose}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!selectedTeam || selectedProject === ""}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor:
                    selectedTeam && selectedProject !== "" ? "#007bff" : "#ccc",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor:
                    selectedTeam && selectedProject !== ""
                      ? "pointer"
                      : "not-allowed",
                }}
              >
                Create Run
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default CreateRunModal;
