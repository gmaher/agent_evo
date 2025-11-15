import React, { useState, useEffect } from "react";
import { Project } from "../types";

interface CreateEvolutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (projectId: number, maxRounds: number, K: number) => void;
  username: string;
}

const CreateEvolutionModal: React.FC<CreateEvolutionModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  username,
}) => {
  const [selectedProject, setSelectedProject] = useState<number | "">("");
  const [maxRounds, setMaxRounds] = useState(10);
  const [K, setK] = useState(5);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchProjects();
    }
  }, [isOpen, username]);

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

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedProject !== "") {
      onSubmit(selectedProject as number, maxRounds, K);
      setSelectedProject("");
      setMaxRounds(10);
      setK(5);
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
        <h2 style={{ marginTop: 0 }}>Create New Evolution</h2>
        <p style={{ color: "#666", marginBottom: "1.5rem" }}>
          Generate K initial teams for evolutionary optimization
        </p>

        {loading ? (
          <p>Loading...</p>
        ) : (
          <form onSubmit={handleSubmit}>
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
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "#666",
                  marginTop: "0.25rem",
                }}
              >
                The project description will be used as the task for team
                generation
              </p>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                Number of Initial Teams (K) *
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={K}
                onChange={(e) => setK(Number(e.target.value))}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                }}
                required
              />
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "#666",
                  marginTop: "0.25rem",
                }}
              >
                Number of teams to generate (1-20)
              </p>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                Max Rounds *
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={maxRounds}
                onChange={(e) => setMaxRounds(Number(e.target.value))}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                }}
                required
              />
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "#666",
                  marginTop: "0.25rem",
                }}
              >
                Maximum rounds for evolution (1-50)
              </p>
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
                disabled={selectedProject === ""}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: selectedProject !== "" ? "#007bff" : "#ccc",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: selectedProject !== "" ? "pointer" : "not-allowed",
                }}
              >
                Generate Teams
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default CreateEvolutionModal;
