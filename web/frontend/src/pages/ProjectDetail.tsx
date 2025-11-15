import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Task, Project, File } from "../types";
import CreateTaskModal from "../components/CreateTaskModal";

const ProjectDetail: React.FC = () => {
  const { username, projectId } = useParams<{
    username: string;
    projectId: string;
  }>();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchTasks = async () => {
    try {
      const tasksResponse = await fetch(
        `http://localhost:8000/projects/${username}/${projectId}/tasks`
      );
      const tasksData = await tasksResponse.json();
      setTasks(tasksData);
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch project details
        const projectsResponse = await fetch(
          `http://localhost:8000/projects/${username}`
        );
        const projects = await projectsResponse.json();
        const currentProject = projects.find(
          (p: Project) => p.id === Number(projectId)
        );
        setProject(currentProject || null);

        // Fetch tasks
        await fetchTasks();
      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [username, projectId]);

  const handleCreateTask = async (description: string, files: File[]) => {
    try {
      const response = await fetch(
        `http://localhost:8000/projects/${username}/${projectId}/tasks`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ description, files }),
        }
      );

      if (response.ok) {
        await fetchTasks(); // Refresh the tasks list
        setIsModalOpen(false);
      }
    } catch (error) {
      console.error("Failed to create task:", error);
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    if (!confirm("Are you sure you want to delete this task?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/projects/${username}/${projectId}/tasks/${taskId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        await fetchTasks(); // Refresh the tasks list
      }
    } catch (error) {
      console.error("Failed to delete task:", error);
    }
  };

  if (loading) return <p>Loading project details...</p>;
  if (!project) return <p>Project not found</p>;

  return (
    <div>
      <Link
        to={`/projects/${username}`}
        style={{ textDecoration: "none", color: "#007bff" }}
      >
        ← Back to Projects
      </Link>

      <h1 style={{ marginTop: "1rem" }}>{project.name}</h1>
      <p style={{ color: "#666", marginBottom: "2rem" }}>
        {project.description}
      </p>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <h2 style={{ margin: 0 }}>Tasks</h2>
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
          Create Task
        </button>
      </div>

      {tasks.length === 0 ? (
        <p>No tasks yet for this project.</p>
      ) : (
        <div>
          {tasks.map((task) => (
            <div
              key={task.id}
              style={{
                border: "1px solid #ddd",
                borderRadius: "8px",
                padding: "1.5rem",
                marginBottom: "1rem",
                backgroundColor: "#f9f9f9",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  marginBottom: "0.5rem",
                }}
              >
                <h3 style={{ margin: 0 }}>Task #{task.id}</h3>
                <button
                  onClick={() => handleDeleteTask(task.id)}
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
              </div>
              <p style={{ marginBottom: "1rem" }}>{task.description}</p>

              {task.files.length > 0 && (
                <div>
                  <h4 style={{ marginBottom: "0.5rem" }}>Files:</h4>
                  {task.files.map((file, index) => (
                    <div
                      key={index}
                      style={{
                        marginBottom: "1rem",
                        backgroundColor: "white",
                        border: "1px solid #ddd",
                        borderRadius: "4px",
                        padding: "1rem",
                      }}
                    >
                      <div
                        style={{
                          fontWeight: "bold",
                          marginBottom: "0.5rem",
                          color: "#333",
                        }}
                      >
                        {file.filename}
                      </div>
                      <pre
                        style={{
                          backgroundColor: "#f5f5f5",
                          padding: "0.75rem",
                          borderRadius: "4px",
                          overflow: "auto",
                          margin: 0,
                        }}
                      >
                        <code>{file.content}</code>
                      </pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <CreateTaskModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateTask}
      />
    </div>
  );
};

export default ProjectDetail;
