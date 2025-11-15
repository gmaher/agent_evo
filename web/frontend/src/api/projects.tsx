import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Project } from "../types";
import CreateProjectModal from "../components/CreateProjectModal";

const Projects: React.FC = () => {
  const { username } = useParams<{ username: string }>();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    fetchProjects();
  }, [username]);

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
        await fetchProjects(); // Refresh the list
        setIsModalOpen(false);
      }
    } catch (error) {
      console.error("Failed to create project:", error);
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
        await fetchProjects(); // Refresh the list
      }
    } catch (error) {
      console.error("Failed to delete project:", error);
    }
  };

  if (loading) return <p>Loading projects...</p>;

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <h1>Projects for {username}</h1>
        <button
          onClick={() => setIsModalOpen(true)}
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

      {projects.length === 0 ? (
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
              <div>
                <h3 style={{ margin: "0 0 0.5rem 0" }}>{proj.name}</h3>
                <p style={{ margin: 0, color: "#666" }}>{proj.description}</p>
              </div>
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
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateProject}
      />
    </div>
  );
};

export default Projects;
