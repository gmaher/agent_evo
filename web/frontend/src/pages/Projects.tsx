import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import type { Project } from "../types";

const API_BASE_URL = "http://localhost:8000";

const Projects: React.FC = () => {
  const { username } = useParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username) return;

    const fetchProjects = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await fetch(`${API_BASE_URL}/projects/${username}`);
        if (!res.ok) {
          throw new Error(`Request failed with status ${res.status}`);
        }
        const data: Project[] = await res.json();
        setProjects(data);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Unknown error occurred";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [username]);

  if (!username) {
    return (
      <main>
        <p>No username provided.</p>
        <Link to="/">Go back</Link>
      </main>
    );
  }

  return (
    <main>
      <h1>Projects for {decodeURIComponent(username)}</h1>
      <p>
        <Link to="/">← Back to login</Link>
      </p>

      {loading && <p>Loading projects...</p>}
      {error && <p style={{ color: "red" }}>Error loading projects: {error}</p>}

      {!loading && !error && projects.length === 0 && <p>No projects found.</p>}

      {!loading && !error && projects.length > 0 && (
        <ul style={{ marginTop: "1rem", paddingLeft: "1.2rem" }}>
          {projects.map((project) => (
            <li key={project.id} style={{ marginBottom: "0.5rem" }}>
              <strong>{project.name}</strong>
              <div style={{ fontSize: "0.9rem" }}>{project.description}</div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
};

export default Projects;
